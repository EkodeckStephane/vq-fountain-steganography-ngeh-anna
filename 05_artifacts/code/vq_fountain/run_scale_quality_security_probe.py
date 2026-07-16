from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import random
import sys

import numpy as np

ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parents[2]
sys.path.insert(0, str(ROOT))

from run_distribution_sampler_probe import generate_payload_images
from vq_fountain.token_sampler import PriorBinCodec, sample_prior_token
from vq_fountain.tokenizer_adapter import TokenGrid, build_tokenizer


def main() -> int:
    parser = argparse.ArgumentParser(description="Scale, distribution, and lightweight security probe.")
    parser.add_argument("--tokenizer", default="learned-patch-vq")
    parser.add_argument("--codebook", default=str(REPO_ROOT / "05_artifacts" / "models" / "learned_patch_vq_stage1_k128.npz"))
    parser.add_argument("--payload-bytes", type=int, nargs="+", default=[512, 4096])
    parser.add_argument("--seeds", nargs="+", default=["scale-a", "scale-b", "scale-c"])
    parser.add_argument("--image-copies", type=int, default=1000)
    parser.add_argument("--bits-per-token", type=int, default=1)
    parser.add_argument("--overhead", type=float, default=1.2)
    parser.add_argument("--block-size", type=int, default=4)
    parser.add_argument("--binning", choices=["projection", "mass"], default="projection")
    parser.add_argument("--position-mode", choices=["raster", "center"], default="center")
    parser.add_argument("--margin", type=int, default=2)
    parser.add_argument("--anchor-scope", choices=["global", "block"], default="block")
    parser.add_argument("--token-block-size", type=int, default=4)
    parser.add_argument("--anchor-count", type=int, default=1)
    parser.add_argument(
        "--out-csv",
        default=str(REPO_ROOT / "05_artifacts" / "results" / "tables" / "vq_fountain_scale_quality_security_probe.csv"),
    )
    parser.add_argument(
        "--out-json",
        default=str(REPO_ROOT / "05_artifacts" / "results" / "raw" / "vq_fountain_scale_quality_security_probe.json"),
    )
    args = parser.parse_args()

    tokenizer = build_tokenizer(args.tokenizer, codebook_path=args.codebook)
    if not hasattr(tokenizer, "token_prior") or not hasattr(tokenizer, "codebook"):
        raise SystemExit("scale probe requires a tokenizer with token_prior and codebook")

    codec = PriorBinCodec(
        prior=tokenizer.token_prior,
        capacity_bits=args.bits_per_token,
        codebook=tokenizer.codebook,
        mode=args.binning,
    )

    rows: list[dict[str, object]] = []
    for payload_bytes in args.payload_bytes:
        for seed in args.seeds:
            generated = generate_payload_images(
                tokenizer=tokenizer,
                codec=codec,
                payload_bytes=payload_bytes,
                bits_per_token=args.bits_per_token,
                overhead=args.overhead,
                block_size=args.block_size,
                image_copies=args.image_copies,
                position_mode=args.position_mode,
                margin=args.margin,
                anchor_count=args.anchor_count,
                anchor_scope=args.anchor_scope,
                token_block_size=args.token_block_size,
                seed=seed,
            )
            cover_grids = generate_cover_grids(tokenizer=tokenizer, image_copies=args.image_copies, seed=f"{seed}:cover")
            stego_grids = generated["grids"]
            if not isinstance(stego_grids, list):
                raise ValueError("invalid generated grids")

            cover_hist = token_histogram(cover_grids, tokenizer.codebook_size)
            stego_hist = token_histogram(stego_grids, tokenizer.codebook_size)
            prior = np.asarray(tokenizer.token_prior, dtype=np.float64)
            cover_features = image_features(cover_grids, tokenizer.codebook)
            stego_features = image_features(stego_grids, tokenizer.codebook)
            detector = logistic_detection_metrics(cover_features, stego_features, seed=seed)
            sklearn_detector = sklearn_detection_metrics(cover_features, stego_features, seed=seed)
            kid = polynomial_mmd(cover_features, stego_features)

            payload_slots_per_image = int(np.mean([len(positions) for positions in generated["position_schedules"]]))
            used_images = int(np.ceil(int(generated["used_token_slots"]) / max(1, payload_slots_per_image)))
            row = {
                "tokenizer": args.tokenizer,
                "payload_bytes": payload_bytes,
                "seed": seed,
                "image_copies": args.image_copies,
                "estimated_used_images": used_images,
                "packet_bytes": generated["packet_bytes"],
                "source_symbols": generated["source_symbols"],
                "encoded_symbols": generated["encoded_symbols"],
                "used_token_slots": generated["used_token_slots"],
                "payload_slots_per_image": payload_slots_per_image,
                "nominal_user_bits_per_generated_image": round(payload_bytes * 8 / args.image_copies, 6),
                "nominal_user_bits_per_used_image": round(payload_bytes * 8 / max(1, used_images), 6),
                "token_jsd_cover_prior": round(jensen_shannon_divergence(cover_hist, prior), 8),
                "token_jsd_stego_prior": round(jensen_shannon_divergence(stego_hist, prior), 8),
                "token_jsd_stego_cover": round(jensen_shannon_divergence(stego_hist, cover_hist), 8),
                "feature_frechet_diag": round(diagonal_frechet_distance(cover_features, stego_features), 8),
                "feature_fid_numpy": round(frechet_distance_numpy(cover_features, stego_features), 8),
                "feature_fid_scipy": round(frechet_distance_scipy(cover_features, stego_features), 8),
                "feature_kid_polynomial": round(kid, 8),
                "proxy_detector_auc": round(detector["auc"], 6),
                "proxy_detector_accuracy": round(detector["accuracy"], 6),
                "sklearn_detector_auc": round(sklearn_detector["auc"], 6),
                "sklearn_detector_accuracy": round(sklearn_detector["accuracy"], 6),
                "capacity_exhausted": bool(generated["capacity_exhausted"]),
            }
            rows.append(row)

    write_csv(Path(args.out_csv), rows)
    write_json(Path(args.out_json), rows)
    print(json.dumps({"csv": args.out_csv, "json": args.out_json, "rows": len(rows)}, indent=2))
    return 0


def generate_cover_grids(tokenizer, image_copies: int, seed: int | str) -> list[TokenGrid]:
    token_count = tokenizer.tokens_per_side * tokenizer.tokens_per_side
    grids: list[TokenGrid] = []
    for image_index in range(image_copies):
        flat_tokens = np.empty(token_count, dtype=np.int32)
        for position in range(token_count):
            global_position = image_index * token_count + position
            flat_tokens[position] = sample_prior_token(tokenizer.token_prior, key=seed, position=global_position)
        grids.append(
            TokenGrid(
                tokens=flat_tokens.reshape(tokenizer.tokens_per_side, tokenizer.tokens_per_side),
                image_size=tokenizer.image_size,
                patch_size=tokenizer.patch_size,
                levels=tokenizer.codebook_size,
            )
        )
    return grids


def token_histogram(grids: list[TokenGrid], codebook_size: int) -> np.ndarray:
    counts = np.zeros(codebook_size, dtype=np.float64)
    for grid in grids:
        counts += np.bincount(grid.flat.astype(np.int32), minlength=codebook_size)
    total = float(counts.sum())
    if total <= 0:
        raise ValueError("empty token histogram")
    return counts / total


def image_features(grids: list[TokenGrid], codebook: np.ndarray) -> np.ndarray:
    patch_means = codebook.reshape(codebook.shape[0], -1, 3).mean(axis=1)
    luminance = 0.2126 * patch_means[:, 0] + 0.7152 * patch_means[:, 1] + 0.0722 * patch_means[:, 2]
    features = np.empty((len(grids), 10), dtype=np.float64)
    for index, grid in enumerate(grids):
        tokens = grid.flat.astype(np.int32)
        rgb = patch_means[tokens]
        lum = luminance[tokens]
        hist = np.bincount(tokens, minlength=codebook.shape[0]).astype(np.float64)
        hist = hist / max(1.0, float(hist.sum()))
        entropy = -float(np.sum(hist[hist > 0] * np.log2(hist[hist > 0])))
        features[index, 0:3] = rgb.mean(axis=0)
        features[index, 3:6] = rgb.std(axis=0)
        features[index, 6] = float(lum.mean())
        features[index, 7] = float(lum.std())
        features[index, 8] = entropy
        features[index, 9] = float(np.max(hist))
    return features


def jensen_shannon_divergence(p: np.ndarray, q: np.ndarray) -> float:
    p = normalize_distribution(p)
    q = normalize_distribution(q)
    m = 0.5 * (p + q)
    return 0.5 * kl_divergence(p, m) + 0.5 * kl_divergence(q, m)


def normalize_distribution(values: np.ndarray) -> np.ndarray:
    values = np.asarray(values, dtype=np.float64)
    total = float(values.sum())
    if total <= 0:
        raise ValueError("distribution has no mass")
    return values / total


def kl_divergence(p: np.ndarray, q: np.ndarray) -> float:
    mask = p > 0
    return float(np.sum(p[mask] * np.log2(p[mask] / np.maximum(q[mask], 1e-15))))


def diagonal_frechet_distance(a: np.ndarray, b: np.ndarray) -> float:
    mean_a = a.mean(axis=0)
    mean_b = b.mean(axis=0)
    var_a = a.var(axis=0)
    var_b = b.var(axis=0)
    mean_term = float(np.sum((mean_a - mean_b) ** 2))
    var_term = float(np.sum(var_a + var_b - 2.0 * np.sqrt(np.maximum(var_a * var_b, 0.0))))
    return mean_term + var_term


def frechet_distance_numpy(a: np.ndarray, b: np.ndarray) -> float:
    mean_a = a.mean(axis=0)
    mean_b = b.mean(axis=0)
    cov_a = np.cov(a, rowvar=False)
    cov_b = np.cov(b, rowvar=False)
    sqrt_cov_a = symmetric_matrix_sqrt(cov_a)
    middle = sqrt_cov_a @ cov_b @ sqrt_cov_a
    cov_mean = symmetric_matrix_sqrt(middle)
    value = float(np.sum((mean_a - mean_b) ** 2) + np.trace(cov_a + cov_b - 2.0 * cov_mean))
    return max(0.0, value)


def frechet_distance_scipy(a: np.ndarray, b: np.ndarray) -> float:
    from scipy.linalg import sqrtm

    mean_a = a.mean(axis=0)
    mean_b = b.mean(axis=0)
    cov_a = np.cov(a, rowvar=False)
    cov_b = np.cov(b, rowvar=False)
    cov_mean = sqrtm(cov_a @ cov_b)
    if np.iscomplexobj(cov_mean):
        cov_mean = cov_mean.real
    value = float(np.sum((mean_a - mean_b) ** 2) + np.trace(cov_a + cov_b - 2.0 * cov_mean))
    return max(0.0, value)


def symmetric_matrix_sqrt(matrix: np.ndarray) -> np.ndarray:
    matrix = 0.5 * (matrix + matrix.T)
    values, vectors = np.linalg.eigh(matrix)
    values = np.maximum(values, 0.0)
    return (vectors * np.sqrt(values)) @ vectors.T


def polynomial_mmd(a: np.ndarray, b: np.ndarray) -> float:
    degree = 3
    gamma = 1.0 / a.shape[1]
    coef = 1.0
    k_aa = (gamma * (a @ a.T) + coef) ** degree
    k_bb = (gamma * (b @ b.T) + coef) ** degree
    k_ab = (gamma * (a @ b.T) + coef) ** degree
    n = a.shape[0]
    m = b.shape[0]
    if n < 2 or m < 2:
        return 0.0
    aa = (float(k_aa.sum()) - float(np.trace(k_aa))) / (n * (n - 1))
    bb = (float(k_bb.sum()) - float(np.trace(k_bb))) / (m * (m - 1))
    ab = float(k_ab.mean())
    return max(0.0, aa + bb - 2.0 * ab)


def logistic_detection_metrics(cover_features: np.ndarray, stego_features: np.ndarray, seed: int | str) -> dict[str, float]:
    x = np.vstack([cover_features, stego_features]).astype(np.float64)
    y = np.concatenate([np.zeros(len(cover_features)), np.ones(len(stego_features))]).astype(np.float64)
    indices = list(range(len(y)))
    random.Random(str(seed)).shuffle(indices)
    split = int(0.7 * len(indices))
    train = np.asarray(indices[:split], dtype=np.int32)
    test = np.asarray(indices[split:], dtype=np.int32)
    mean = x[train].mean(axis=0)
    std = x[train].std(axis=0) + 1e-8
    x_train = (x[train] - mean) / std
    x_test = (x[test] - mean) / std
    y_train = y[train]
    y_test = y[test]

    weights = np.zeros(x_train.shape[1], dtype=np.float64)
    bias = 0.0
    lr = 0.05
    l2 = 1e-3
    for _ in range(300):
        scores = x_train @ weights + bias
        probs = sigmoid(scores)
        error = probs - y_train
        weights -= lr * ((x_train.T @ error) / len(y_train) + l2 * weights)
        bias -= lr * float(error.mean())

    scores = x_test @ weights + bias
    probs = sigmoid(scores)
    predictions = (probs >= 0.5).astype(np.float64)
    return {
        "accuracy": float((predictions == y_test).mean()),
        "auc": binary_auc(y_test, probs),
    }


def sklearn_detection_metrics(cover_features: np.ndarray, stego_features: np.ndarray, seed: int | str) -> dict[str, float]:
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import accuracy_score, roc_auc_score
    from sklearn.model_selection import train_test_split
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler

    x = np.vstack([cover_features, stego_features]).astype(np.float64)
    y = np.concatenate([np.zeros(len(cover_features)), np.ones(len(stego_features))]).astype(np.int32)
    random_state = abs(hash(str(seed))) % (2**32)
    x_train, x_test, y_train, y_test = train_test_split(
        x,
        y,
        test_size=0.3,
        random_state=random_state,
        stratify=y,
    )
    model = make_pipeline(
        StandardScaler(),
        LogisticRegression(max_iter=1000, solver="lbfgs"),
    )
    model.fit(x_train, y_train)
    probabilities = model.predict_proba(x_test)[:, 1]
    predictions = (probabilities >= 0.5).astype(np.int32)
    return {
        "accuracy": float(accuracy_score(y_test, predictions)),
        "auc": float(roc_auc_score(y_test, probabilities)),
    }


def sigmoid(values: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-np.clip(values, -60.0, 60.0)))


def binary_auc(labels: np.ndarray, scores: np.ndarray) -> float:
    order = np.argsort(scores)
    ranks = np.empty_like(order, dtype=np.float64)
    ranks[order] = np.arange(1, len(scores) + 1)
    positive = labels == 1
    negative = labels == 0
    positive_count = int(positive.sum())
    negative_count = int(negative.sum())
    if positive_count == 0 or negative_count == 0:
        return 0.5
    rank_sum = float(ranks[positive].sum())
    return (rank_sum - positive_count * (positive_count + 1) / 2.0) / (positive_count * negative_count)


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(rows[0].keys())
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(rows, handle, indent=2, sort_keys=True)


if __name__ == "__main__":
    raise SystemExit(main())
