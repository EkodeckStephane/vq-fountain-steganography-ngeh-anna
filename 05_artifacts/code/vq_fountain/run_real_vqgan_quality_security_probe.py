from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import sys

import numpy as np
from PIL import Image
import torch

ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parents[2]
sys.path.insert(0, str(ROOT))

from run_real_vqgan_payload_probe import (
    calibrate_tokens,
    decode_token_grids_to_images,
    generate_payload_images,
    stable_random,
)
from vq_fountain.token_sampler import PriorBinCodec


def main() -> int:
    parser = argparse.ArgumentParser(description="Feature-level quality/security probe for real VQGAN payload images.")
    parser.add_argument("--model-dir", default=str(REPO_ROOT / "05_artifacts" / "models" / "vqgan_f4_8192_diffusers_converted"))
    parser.add_argument("--model-subfolder", default=None)
    parser.add_argument("--allow-download", action="store_true")
    parser.add_argument("--payload-bytes", type=int, default=32)
    parser.add_argument("--block-size", type=int, default=1)
    parser.add_argument("--overhead", type=float, default=3.0)
    parser.add_argument("--latent-side", type=int, default=16)
    parser.add_argument("--macro-cell-size", type=int, default=2)
    parser.add_argument("--symbols-per-image", type=int, default=8)
    parser.add_argument("--payload-seeds", nargs="+", default=["quality-a", "quality-b", "quality-c", "quality-d"])
    parser.add_argument("--calibration-seed", default="real-vqgan-calibration-v1")
    parser.add_argument("--calibration-count", type=int, default=256)
    parser.add_argument("--calibration-threshold", type=float, default=0.90)
    parser.add_argument("--calibration-batch-size", type=int, default=8)
    parser.add_argument("--batch-size", type=int, default=4)
    parser.add_argument("--device", default="cpu")
    parser.add_argument(
        "--out-csv",
        default=str(REPO_ROOT / "05_artifacts" / "results" / "tables" / "vq_fountain_real_vqgan_quality_security.csv"),
    )
    parser.add_argument(
        "--out-json",
        default=str(REPO_ROOT / "05_artifacts" / "results" / "raw" / "vq_fountain_real_vqgan_quality_security.json"),
    )
    args = parser.parse_args()

    try:
        from diffusers import VQModel
    except Exception as exc:  # pragma: no cover - optional dependency
        raise SystemExit(f"diffusers VQModel is unavailable: {exc}") from exc

    device = torch.device(args.device)
    model = VQModel.from_pretrained(
        args.model_dir,
        subfolder=args.model_subfolder,
        local_files_only=not args.allow_download,
        use_safetensors=False,
    ).to(device)
    model.eval()

    codebook = model.quantize.embedding.weight.detach().cpu().numpy()
    prior = np.ones(model.config.num_vq_embeddings, dtype=np.float64) / float(model.config.num_vq_embeddings)
    codec = PriorBinCodec(prior=prior, capacity_bits=1, codebook=codebook, mode="projection")
    calibration = calibrate_tokens(
        model=model,
        codec=codec,
        latent_side=args.latent_side,
        count=args.calibration_count,
        threshold=args.calibration_threshold,
        batch_size=args.calibration_batch_size,
        seed=args.calibration_seed,
        device=device,
    )
    pools = {
        value: [item for item in calibration if item.received_value == value and item.majority_fraction >= args.calibration_threshold]
        for value in range(2)
    }
    if not pools[0] or not pools[1]:
        raise SystemExit("calibration did not produce stable pools for both values")

    payload_images = []
    generated_image_counts = []
    for seed in args.payload_seeds:
        generated = generate_payload_images(
            model=model,
            codec=codec,
            pools=pools,
            payload_bytes=args.payload_bytes,
            bits_per_token=1,
            block_size=args.block_size,
            overhead=args.overhead,
            latent_side=args.latent_side,
            macro_cell_size=args.macro_cell_size,
            symbols_per_image=args.symbols_per_image,
            batch_size=args.batch_size,
            seed=seed,
            device=device,
        )
        payload_images.extend(generated["images"])
        generated_image_counts.append(len(generated["images"]))

    reference_images = generate_reference_images(
        model=model,
        pools=pools,
        count=len(payload_images),
        latent_side=args.latent_side,
        macro_cell_size=args.macro_cell_size,
        batch_size=args.batch_size,
        seed=f"{args.calibration_seed}:reference",
        device=device,
    )

    payload_features = image_features(payload_images)
    reference_features = image_features(reference_images)
    row = {
        "model_dir": model_reference(args.model_dir),
        "model_subfolder": args.model_subfolder or "",
        "payload_bytes": args.payload_bytes,
        "block_size": args.block_size,
        "overhead": args.overhead,
        "macro_cell_size": args.macro_cell_size,
        "symbols_per_image": args.symbols_per_image,
        "payload_seed_count": len(args.payload_seeds),
        "payload_images": len(payload_images),
        "reference_images": len(reference_images),
        "stable_pool_0": len(pools[0]),
        "stable_pool_1": len(pools[1]),
        "mean_abs_feature_delta": round(float(np.mean(np.abs(payload_features.mean(axis=0) - reference_features.mean(axis=0)))), 8),
        "feature_fid_scipy": round(frechet_distance(payload_features, reference_features), 8),
        "feature_kid_polynomial": round(polynomial_mmd(payload_features, reference_features), 8),
        **detector_metrics(payload_features, reference_features),
    }
    raw = {
        "row": row,
        "payload_seeds": args.payload_seeds,
        "generated_image_counts": generated_image_counts,
        "calibration_seed": args.calibration_seed,
        "calibration_count": args.calibration_count,
        "calibration_threshold": args.calibration_threshold,
    }
    write_csv(Path(args.out_csv), [row])
    write_json(Path(args.out_json), raw)
    print(json.dumps({"csv": display_path(Path(args.out_csv)), "json": display_path(Path(args.out_json)), "rows": 1}, indent=2))
    return 0


def generate_reference_images(
    model,
    pools,
    count: int,
    latent_side: int,
    macro_cell_size: int,
    batch_size: int,
    seed: str,
    device: torch.device,
) -> list[Image.Image]:
    macro_cells = [
        (row, col)
        for row in range(0, latent_side, macro_cell_size)
        for col in range(0, latent_side, macro_cell_size)
    ]
    grids = []
    for image_index in range(count):
        grid = np.zeros((latent_side, latent_side), dtype=np.int64)
        for cell_index, (row_start, col_start) in enumerate(macro_cells):
            value = int(stable_random(f"{seed}:{image_index}:{cell_index}:value") % 2)
            pool = sorted(pools[value], key=lambda item: (-item.majority_fraction, item.token_id))
            token = pool[stable_random(f"{seed}:{image_index}:{cell_index}:token") % len(pool)].token_id
            grid[row_start : row_start + macro_cell_size, col_start : col_start + macro_cell_size] = token
        grids.append(grid)
    return decode_token_grids_to_images(
        model=model,
        token_grids=np.asarray(grids, dtype=np.int64),
        batch_size=batch_size,
        device=device,
    )


def image_features(images: list[Image.Image]) -> np.ndarray:
    features = []
    for image in images:
        small = image.convert("RGB").resize((16, 16), Image.Resampling.BICUBIC)
        array = np.asarray(small, dtype=np.float32) / 255.0
        flat = array.reshape(-1, 3)
        hist_parts = []
        for channel in range(3):
            hist, _ = np.histogram(flat[:, channel], bins=16, range=(0.0, 1.0), density=True)
            hist_parts.append(hist.astype(np.float32))
        feature = np.concatenate(
            [
                flat.mean(axis=0),
                flat.std(axis=0),
                np.percentile(flat, [10, 50, 90], axis=0).reshape(-1),
                *hist_parts,
            ]
        )
        features.append(feature)
    return np.asarray(features, dtype=np.float64)


def frechet_distance(left: np.ndarray, right: np.ndarray) -> float:
    mu_left = left.mean(axis=0)
    mu_right = right.mean(axis=0)
    cov_left = np.cov(left, rowvar=False)
    cov_right = np.cov(right, rowvar=False)
    try:
        from scipy.linalg import sqrtm

        covmean = sqrtm(cov_left @ cov_right)
        if np.iscomplexobj(covmean):
            covmean = covmean.real
        return float(np.sum((mu_left - mu_right) ** 2) + np.trace(cov_left + cov_right - 2.0 * covmean))
    except Exception:
        return float(np.sum((mu_left - mu_right) ** 2) + np.sum((np.sqrt(np.diag(cov_left)) - np.sqrt(np.diag(cov_right))) ** 2))


def polynomial_mmd(left: np.ndarray, right: np.ndarray) -> float:
    gamma = 1.0 / left.shape[1]
    k_xx = (gamma * left @ left.T + 1.0) ** 3
    k_yy = (gamma * right @ right.T + 1.0) ** 3
    k_xy = (gamma * left @ right.T + 1.0) ** 3
    n = left.shape[0]
    m = right.shape[0]
    xx = (k_xx.sum() - np.trace(k_xx)) / max(1, n * (n - 1))
    yy = (k_yy.sum() - np.trace(k_yy)) / max(1, m * (m - 1))
    xy = k_xy.mean()
    return float(xx + yy - 2.0 * xy)


def detector_metrics(payload_features: np.ndarray, reference_features: np.ndarray) -> dict[str, float]:
    try:
        from sklearn.linear_model import LogisticRegression
        from sklearn.metrics import accuracy_score, roc_auc_score
        from sklearn.model_selection import train_test_split
        from sklearn.preprocessing import StandardScaler
        from sklearn.pipeline import make_pipeline

        x = np.vstack([payload_features, reference_features])
        y = np.asarray([1] * len(payload_features) + [0] * len(reference_features), dtype=np.int32)
        x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=0.35, random_state=1234, stratify=y)
        model = make_pipeline(StandardScaler(), LogisticRegression(max_iter=1000, random_state=1234))
        model.fit(x_train, y_train)
        scores = model.predict_proba(x_test)[:, 1]
        predictions = (scores >= 0.5).astype(np.int32)
        return {
            "sklearn_detector_auc": round(float(roc_auc_score(y_test, scores)), 8),
            "sklearn_detector_accuracy": round(float(accuracy_score(y_test, predictions)), 8),
        }
    except Exception:
        return {"sklearn_detector_auc": -1.0, "sklearn_detector_accuracy": -1.0}


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")


def display_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def model_reference(model_dir: str) -> str:
    path = Path(model_dir)
    if path.exists() or "\\" in model_dir or "/" in model_dir and model_dir.startswith("."):
        return display_path(path)
    return model_dir


if __name__ == "__main__":
    raise SystemExit(main())
