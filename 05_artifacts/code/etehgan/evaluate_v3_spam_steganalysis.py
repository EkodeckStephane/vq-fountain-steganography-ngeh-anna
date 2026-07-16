import argparse
import csv
import json
import random
from pathlib import Path

import numpy as np
import torch

from evaluate_v2_random import IMAGE_EXTENSIONS, build_encoder, load_image, seed_everything, to_uint8_array
from evaluate_v3_simple_steganalysis import auc_score, build_payload_tensor, train_logistic_regression
from packet_v3 import capacity_plan


def collect_images(roots, max_images=None, offset_images=0):
    paths = []
    for root in roots:
        paths.extend(sorted(p for p in Path(root).rglob("*") if p.suffix.lower() in IMAGE_EXTENSIONS))
    paths = sorted(paths)
    if offset_images:
        paths = paths[offset_images:]
    if max_images:
        paths = paths[:max_images]
    if not paths:
        raise ValueError(f"No images found under {roots}")
    return paths


def random_payload(length, seed):
    return random.Random(int(seed)).randbytes(length)


def quantized_residuals(channel, truncation):
    residuals = [
        np.diff(channel, axis=1),
        np.diff(channel, axis=0),
        channel[1:, 1:] - channel[:-1, :-1],
        channel[1:, :-1] - channel[:-1, 1:],
    ]
    return [np.clip(np.rint(r * 255.0), -truncation, truncation).astype(np.int16) for r in residuals]


def cooc2_features(residual, truncation):
    bins = 2 * truncation + 1
    shifted = residual + truncation
    pairs = []
    if residual.shape[1] > 1:
        pairs.append((shifted[:, :-1], shifted[:, 1:]))
    if residual.shape[0] > 1:
        pairs.append((shifted[:-1, :], shifted[1:, :]))
    feats = []
    for first, second in pairs:
        hist = np.zeros((bins, bins), dtype=np.float64)
        np.add.at(hist, (first.reshape(-1), second.reshape(-1)), 1.0)
        total = hist.sum()
        if total > 0:
            hist /= total
        feats.extend(hist.reshape(-1).tolist())
    return feats


def extract_spam_features(uint8_rgb, truncation=3):
    arr = uint8_rgb.astype(np.float32) / 255.0
    luma = 0.299 * arr[:, :, 0] + 0.587 * arr[:, :, 1] + 0.114 * arr[:, :, 2]
    channels = [arr[:, :, 0], arr[:, :, 1], arr[:, :, 2], luma]
    feats = []
    for channel in channels:
        for residual in quantized_residuals(channel, truncation):
            feats.extend(cooc2_features(residual, truncation))
    return np.asarray(feats, dtype=np.float32)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--image-root", required=True, nargs="+")
    parser.add_argument("--checkpoint", required=True)
    parser.add_argument("--payload-bpp", type=float, required=True)
    parser.add_argument("--payload-fraction", type=float, default=1.0)
    parser.add_argument("--ecc-bytes", type=int, default=64)
    parser.add_argument("--nsize", type=int, default=255)
    parser.add_argument("--packet-seed", type=int, default=7)
    parser.add_argument("--max-images", type=int, default=100)
    parser.add_argument("--offset-images", type=int, default=20)
    parser.add_argument("--train-ratio", type=float, default=0.5)
    parser.add_argument("--epochs", type=int, default=700)
    parser.add_argument("--truncation", type=int, default=3)
    parser.add_argument("--out-csv", required=True)
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--seed", type=int, default=3030)
    args = parser.parse_args()

    seed_everything(args.seed)
    useful_bits = int(round(512 * 512 * args.payload_bpp))
    plan = capacity_plan(useful_bits, ecc_bytes=args.ecc_bytes, nsize=args.nsize)
    payload_bytes = max(1, int(plan.max_payload_bytes * args.payload_fraction))

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    checkpoint = torch.load(args.checkpoint, map_location=device)
    encoder = build_encoder(checkpoint.get("config", {})).to(device).eval()
    encoder.load_state_dict(checkpoint["en"], strict=True)

    paths = collect_images(args.image_root, max_images=args.max_images, offset_images=args.offset_images)
    features = []
    labels = []
    groups = []
    rows = []
    with torch.no_grad():
        for image_index, path in enumerate(paths):
            cover_image, cover_tensor = load_image(path)
            cover_arr = np.asarray(cover_image.convert("RGB"), dtype=np.uint8)
            payload = random_payload(payload_bytes, args.seed + image_index * 1297)
            payload_tensor, _ = build_payload_tensor(
                payload,
                useful_bits=useful_bits,
                ecc_bytes=args.ecc_bytes,
                nsize=args.nsize,
                packet_seed=args.packet_seed,
                device=device,
            )
            stego = encoder(cover_tensor.unsqueeze(0).to(device), payload_tensor)
            stego_arr = to_uint8_array(stego)

            for label, kind, arr in [(0, "cover", cover_arr), (1, "stego", stego_arr)]:
                features.append(extract_spam_features(arr, truncation=args.truncation))
                labels.append(label)
                groups.append(image_index)
                rows.append({"image": str(path), "group": image_index, "kind": kind, "label": label})

    x = np.vstack(features)
    y = np.asarray(labels, dtype=np.int64)
    groups = np.asarray(groups)
    unique_groups = np.arange(len(paths))
    random.Random(args.seed).shuffle(unique_groups)
    train_count = max(1, min(len(unique_groups) - 1, int(round(len(unique_groups) * args.train_ratio))))
    train_groups = set(unique_groups[:train_count].tolist())
    train_mask = np.asarray([g in train_groups for g in groups])
    test_mask = ~train_mask

    mean = x[train_mask].mean(axis=0, keepdims=True)
    std = x[train_mask].std(axis=0, keepdims=True)
    std[std < 1e-8] = 1.0
    x_norm = (x - mean) / std

    metrics = train_logistic_regression(
        x_norm[train_mask],
        y[train_mask],
        x_norm[test_mask],
        y[test_mask],
        epochs=args.epochs,
        seed=args.seed,
    )
    test_scores = metrics.pop("test_scores")
    score_index = 0
    for row, is_test in zip(rows, test_mask):
        row["split"] = "test" if is_test else "train"
        row["score"] = ""
        if is_test:
            row["score"] = float(test_scores[score_index])
            score_index += 1

    summary = {
        "checkpoint": args.checkpoint,
        "payload_bpp_requested": args.payload_bpp,
        "nominal_bpp_used": plan.nominal_bpp_used,
        "effective_user_bpp": (payload_bytes * 8) / float(512 * 512),
        "payload_bytes": payload_bytes,
        "images": len(paths),
        "train_images": train_count,
        "test_images": len(paths) - train_count,
        "feature_count": int(x.shape[1]),
        "detector": f"SPAM-style quantized residual co-occurrence, truncation={args.truncation}",
        "sanity_auc_check": float(auc_score(y[test_mask], test_scores)),
        **metrics,
    }

    Path(args.out_csv).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out_json).parent.mkdir(parents=True, exist_ok=True)
    with open(args.out_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    Path(args.out_json).write_text(json.dumps({"summary": summary, "rows": rows}, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
