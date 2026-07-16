import argparse
import csv
import json
import random
from pathlib import Path

import numpy as np
import torch

from evaluate_v2_random import (
    IMAGE_EXTENSIONS,
    build_encoder,
    global_ssim,
    load_image,
    psnr,
    seed_everything,
    to_uint8_array,
)
from evaluate_v3_simple_steganalysis import (
    build_payload_tensor,
    extract_features as extract_simple_features,
    train_logistic_regression,
)
from evaluate_v3_spam_steganalysis import extract_spam_features
from models import DenseDecoder512
from packet_v3 import bits_to_bytes, decode_packet


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


def feature_distance(cover_feat, stego_feat):
    denom = np.maximum(np.abs(cover_feat), 1e-6)
    return float(np.mean(np.abs(stego_feat - cover_feat) / denom))


def detector_metrics(rows, feature_key, seed, train_ratio, epochs):
    accepted = [row for row in rows if row["accepted"]]
    features = []
    labels = []
    groups = []
    for group, row in enumerate(accepted):
        features.append(row[f"cover_{feature_key}"])
        labels.append(0)
        groups.append(group)
        features.append(row[f"stego_{feature_key}"])
        labels.append(1)
        groups.append(group)

    if len(accepted) < 4:
        return {"accepted_images": len(accepted), "test_auc": float("nan"), "test_accuracy": float("nan")}

    x = np.vstack(features)
    y = np.asarray(labels, dtype=np.int64)
    groups = np.asarray(groups)
    unique_groups = list(range(len(accepted)))
    random.Random(seed).shuffle(unique_groups)
    train_count = max(1, min(len(unique_groups) - 1, int(round(len(unique_groups) * train_ratio))))
    train_groups = set(unique_groups[:train_count])
    train_mask = np.asarray([g in train_groups for g in groups])
    test_mask = ~train_mask
    mean = x[train_mask].mean(axis=0, keepdims=True)
    std = x[train_mask].std(axis=0, keepdims=True)
    std[std < 1e-8] = 1.0
    metrics = train_logistic_regression(
        (x[train_mask] - mean) / std,
        y[train_mask],
        (x[test_mask] - mean) / std,
        y[test_mask],
        epochs=epochs,
        seed=seed,
    )
    metrics.pop("test_scores", None)
    metrics["accepted_images"] = len(accepted)
    metrics["train_images"] = train_count
    metrics["test_images"] = len(accepted) - train_count
    return metrics


def strip_features(row):
    return {
        key: value
        for key, value in row.items()
        if key
        not in {
            "cover_simple",
            "stego_simple",
            "cover_spam",
            "stego_spam",
        }
    }


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
    parser.add_argument("--offset-images", type=int, default=0)
    parser.add_argument("--accept-fraction", type=float, default=0.5)
    parser.add_argument("--train-ratio", type=float, default=0.5)
    parser.add_argument("--epochs", type=int, default=300)
    parser.add_argument("--seed", type=int, default=4401)
    parser.add_argument("--out-csv", required=True)
    parser.add_argument("--out-json", required=True)
    args = parser.parse_args()

    seed_everything(args.seed)
    useful_bits = int(round(512 * 512 * args.payload_bpp))

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    checkpoint = torch.load(args.checkpoint, map_location=device)
    encoder = build_encoder(checkpoint.get("config", {})).to(device).eval()
    decoder = DenseDecoder512().to(device).eval()
    encoder.load_state_dict(checkpoint["en"], strict=True)
    decoder.load_state_dict(checkpoint["de"], strict=True)

    rows = []
    paths = collect_images(args.image_root, max_images=args.max_images, offset_images=args.offset_images)
    with torch.no_grad():
        for image_index, path in enumerate(paths):
            cover_image, cover_tensor = load_image(path)
            cover_arr = np.asarray(cover_image.convert("RGB"), dtype=np.uint8)
            payload_probe = random_payload(1, args.seed + image_index * 1297)
            payload_tensor, plan = build_payload_tensor(
                payload_probe,
                useful_bits=useful_bits,
                ecc_bytes=args.ecc_bytes,
                nsize=args.nsize,
                packet_seed=args.packet_seed,
                device=device,
            )
            payload_bytes = max(1, int(plan.max_payload_bytes * args.payload_fraction))
            payload = random_payload(payload_bytes, args.seed + image_index * 1297)
            payload_tensor, packet_plan = build_payload_tensor(
                payload,
                useful_bits=useful_bits,
                ecc_bytes=args.ecc_bytes,
                nsize=args.nsize,
                packet_seed=args.packet_seed,
                device=device,
            )
            cover_batch = cover_tensor.unsqueeze(0).to(device)
            stego = encoder(cover_batch, payload_tensor)
            stego_arr = to_uint8_array(stego)
            logits = decoder(stego).detach().cpu().numpy().reshape(-1)
            pred_bits = (logits[: packet_plan.useful_bits_used] >= 0.0).astype(np.uint8)
            try:
                recovered, _ = decode_packet(
                    bits_to_bytes(pred_bits),
                    useful_bits=useful_bits,
                    ecc_bytes=args.ecc_bytes,
                    nsize=args.nsize,
                    seed=args.packet_seed,
                )
                exact = recovered == payload
            except Exception:
                exact = False

            cover_simple = extract_simple_features(cover_arr)
            stego_simple = extract_simple_features(stego_arr)
            cover_spam = extract_spam_features(cover_arr)
            stego_spam = extract_spam_features(stego_arr)
            rows.append(
                {
                    "image": str(path),
                    "image_index": image_index,
                    "payload_bytes": payload_bytes,
                    "effective_user_bpp": (payload_bytes * 8) / float(512 * 512),
                    "exact_recovery": exact,
                    "psnr_db": psnr(cover_arr, stego_arr),
                    "global_ssim": float(global_ssim(cover_arr, stego_arr)),
                    "simple_distance": feature_distance(cover_simple, stego_simple),
                    "spam_distance": feature_distance(cover_spam, stego_spam),
                    "cover_simple": cover_simple,
                    "stego_simple": stego_simple,
                    "cover_spam": cover_spam,
                    "stego_spam": stego_spam,
                }
            )

    simple_values = np.asarray([row["simple_distance"] for row in rows], dtype=np.float64)
    spam_values = np.asarray([row["spam_distance"] for row in rows], dtype=np.float64)
    simple_z = (simple_values - simple_values.mean()) / max(simple_values.std(), 1e-12)
    spam_z = (spam_values - spam_values.mean()) / max(spam_values.std(), 1e-12)
    for row, score in zip(rows, simple_z + spam_z):
        row["gate_score"] = float(score)

    exact_rows = [row for row in rows if row["exact_recovery"]]
    accept_count = max(4, int(round(len(rows) * args.accept_fraction)))
    accepted_ids = {
        row["image_index"]
        for row in sorted(exact_rows, key=lambda item: item["gate_score"])[: min(accept_count, len(exact_rows))]
    }
    for row in rows:
        row["accepted"] = row["image_index"] in accepted_ids

    simple_metrics = detector_metrics(rows, "simple", args.seed, args.train_ratio, args.epochs)
    spam_metrics = detector_metrics(rows, "spam", args.seed, args.train_ratio, args.epochs)
    accepted = [row for row in rows if row["accepted"]]
    summary = {
        "checkpoint": args.checkpoint,
        "payload_bpp_requested": args.payload_bpp,
        "nominal_bpp_used": plan.nominal_bpp_used,
        "ecc_bytes": args.ecc_bytes,
        "nsize": args.nsize,
        "payload_bytes": int(np.mean([row["payload_bytes"] for row in rows])),
        "effective_user_bpp": float(np.mean([row["effective_user_bpp"] for row in rows])),
        "images_tested": len(rows),
        "accept_fraction_requested": args.accept_fraction,
        "accepted_images": len(accepted),
        "acceptance_rate": 0.0 if not rows else len(accepted) / float(len(rows)),
        "exact_recovery_all_rate": float(np.mean([row["exact_recovery"] for row in rows])),
        "exact_recovery_accepted_rate": 0.0 if not accepted else float(np.mean([row["exact_recovery"] for row in accepted])),
        "mean_psnr_accepted": 0.0 if not accepted else float(np.mean([row["psnr_db"] for row in accepted])),
        "mean_ssim_accepted": 0.0 if not accepted else float(np.mean([row["global_ssim"] for row in accepted])),
        "simple_detector_on_accepted": simple_metrics,
        "spam_detector_on_accepted": spam_metrics,
        "gate_rule": "accept exact-recovery images with lowest combined simple/SPAM cover-stego feature-distance score",
    }

    out_rows = [strip_features(row) for row in rows]
    Path(args.out_csv).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out_json).parent.mkdir(parents=True, exist_ok=True)
    with open(args.out_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(out_rows[0].keys()))
        writer.writeheader()
        writer.writerows(out_rows)
    Path(args.out_json).write_text(json.dumps({"summary": summary, "rows": out_rows}, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
