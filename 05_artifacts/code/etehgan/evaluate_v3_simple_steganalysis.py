import argparse
import csv
import json
import random
from pathlib import Path

import numpy as np
import torch

from evaluate_v2_random import IMAGE_EXTENSIONS, build_encoder, load_image, seed_everything, to_uint8_array
from packet_v3 import bytes_to_bits, build_packet, capacity_plan


TOTAL_BITS = 2 * 512 * 512


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


def build_payload_tensor(payload_bytes, useful_bits, ecc_bytes, nsize, packet_seed, device):
    packet, plan = build_packet(
        payload_bytes,
        useful_bits=useful_bits,
        ecc_bytes=ecc_bytes,
        nsize=nsize,
        seed=packet_seed,
    )
    packet_bits = bytes_to_bits(packet)
    full = np.zeros(TOTAL_BITS, dtype=np.float32)
    full[: len(packet_bits)] = packet_bits
    return torch.from_numpy(full).view(1, 2, 512, 512).to(device), plan


def channel_features(channel):
    feats = []
    arrays = [
        np.diff(channel, axis=0),
        np.diff(channel, axis=1),
        channel[1:, 1:] - channel[:-1, :-1],
        channel[1:, :-1] - channel[:-1, 1:],
    ]
    for residual in arrays:
        abs_res = np.abs(residual)
        feats.extend(
            [
                float(abs_res.mean()),
                float(abs_res.std()),
                float(np.percentile(abs_res, 50)),
                float(np.percentile(abs_res, 90)),
                float(np.percentile(abs_res, 99)),
            ]
        )
    return feats


def extract_features(uint8_rgb):
    arr = uint8_rgb.astype(np.float32) / 255.0
    luma = 0.299 * arr[:, :, 0] + 0.587 * arr[:, :, 1] + 0.114 * arr[:, :, 2]
    feats = []
    for c in range(3):
        feats.extend(channel_features(arr[:, :, c]))
    feats.extend(channel_features(luma))

    lsb = uint8_rgb & 1
    feats.extend(lsb.reshape(-1, 3).mean(axis=0).astype(float).tolist())
    feats.extend(lsb.reshape(-1, 3).std(axis=0).astype(float).tolist())
    return np.asarray(feats, dtype=np.float32)


def auc_score(labels, scores):
    labels = np.asarray(labels).astype(int)
    scores = np.asarray(scores).astype(float)
    pos = scores[labels == 1]
    neg = scores[labels == 0]
    if len(pos) == 0 or len(neg) == 0:
        return float("nan")
    wins = 0.0
    for value in pos:
        wins += float(np.sum(value > neg))
        wins += 0.5 * float(np.sum(value == neg))
    return wins / float(len(pos) * len(neg))


def train_logistic_regression(train_x, train_y, test_x, test_y, epochs=500, lr=0.05, seed=0):
    torch.manual_seed(seed)
    x_train = torch.from_numpy(train_x.astype(np.float32))
    y_train = torch.from_numpy(train_y.astype(np.float32)).view(-1, 1)
    model = torch.nn.Linear(train_x.shape[1], 1)
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    loss_fn = torch.nn.BCEWithLogitsLoss()
    for _ in range(epochs):
        optimizer.zero_grad()
        loss = loss_fn(model(x_train), y_train)
        loss.backward()
        optimizer.step()

    with torch.no_grad():
        train_scores = torch.sigmoid(model(x_train)).numpy().reshape(-1)
        test_scores = torch.sigmoid(model(torch.from_numpy(test_x.astype(np.float32)))).numpy().reshape(-1)
    train_pred = train_scores >= 0.5
    test_pred = test_scores >= 0.5
    return {
        "train_accuracy": float(np.mean(train_pred == train_y)),
        "test_accuracy": float(np.mean(test_pred == test_y)),
        "train_auc": float(auc_score(train_y, train_scores)),
        "test_auc": float(auc_score(test_y, test_scores)),
        "test_scores": test_scores,
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
    parser.add_argument("--offset-images", type=int, default=20)
    parser.add_argument("--train-ratio", type=float, default=0.5)
    parser.add_argument("--epochs", type=int, default=500)
    parser.add_argument("--out-csv", required=True)
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--seed", type=int, default=2026)
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
            payload_tensor, packet_plan = build_payload_tensor(
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
                feat = extract_features(arr)
                features.append(feat)
                labels.append(label)
                groups.append(image_index)
                rows.append(
                    {
                        "image": str(path),
                        "group": image_index,
                        "kind": kind,
                        "label": label,
                    }
                )

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
        "detector": "logistic regression on simple residual and LSB summary features",
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
