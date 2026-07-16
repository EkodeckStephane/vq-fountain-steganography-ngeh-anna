from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import sys

import numpy as np
import torch
from PIL import Image

ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parents[2]
sys.path.insert(0, str(ROOT))

from run_real_vqgan_payload_probe import calibrate_tokens, generate_payload_images
from run_real_vqgan_quality_security_probe import generate_reference_images, model_reference
from vq_fountain.token_sampler import PriorBinCodec


def main() -> int:
    parser = argparse.ArgumentParser(description="SPAM-style residual steganalysis probe for real VQGAN payload images.")
    parser.add_argument("--model-dir", default=str(REPO_ROOT / "05_artifacts" / "models" / "vqgan_f4_8192_diffusers_converted"))
    parser.add_argument("--model-subfolder", default=None)
    parser.add_argument("--allow-download", action="store_true")
    parser.add_argument("--payload-bytes", type=int, default=32)
    parser.add_argument("--block-size", type=int, default=1)
    parser.add_argument("--overhead", type=float, default=3.0)
    parser.add_argument("--latent-side", type=int, default=16)
    parser.add_argument("--macro-cell-size", type=int, default=2)
    parser.add_argument("--symbols-per-image", type=int, default=8)
    parser.add_argument("--payload-seeds", nargs="+", default=["spam-a", "spam-b", "spam-c", "spam-d"])
    parser.add_argument("--calibration-seed", default="real-vqgan-calibration-v1")
    parser.add_argument("--calibration-count", type=int, default=256)
    parser.add_argument("--calibration-threshold", type=float, default=0.90)
    parser.add_argument("--calibration-batch-size", type=int, default=8)
    parser.add_argument("--batch-size", type=int, default=4)
    parser.add_argument("--residual-truncation", type=int, default=3)
    parser.add_argument("--device", default="cpu")
    parser.add_argument(
        "--out-csv",
        default=str(REPO_ROOT / "05_artifacts" / "results" / "tables" / "vq_fountain_real_vqgan_spam_steganalysis.csv"),
    )
    parser.add_argument(
        "--out-json",
        default=str(REPO_ROOT / "05_artifacts" / "results" / "raw" / "vq_fountain_real_vqgan_spam_steganalysis.json"),
    )
    args = parser.parse_args()

    from diffusers import VQModel

    device = torch.device(args.device)
    vq_model = VQModel.from_pretrained(
        args.model_dir,
        subfolder=args.model_subfolder,
        local_files_only=not args.allow_download,
        use_safetensors=False,
    ).to(device)
    vq_model.eval()

    codebook = vq_model.quantize.embedding.weight.detach().cpu().numpy()
    prior = np.ones(vq_model.config.num_vq_embeddings, dtype=np.float64) / float(vq_model.config.num_vq_embeddings)
    codec = PriorBinCodec(prior=prior, capacity_bits=1, codebook=codebook, mode="projection")
    calibration = calibrate_tokens(
        model=vq_model,
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
            model=vq_model,
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
        model=vq_model,
        pools=pools,
        count=len(payload_images),
        latent_side=args.latent_side,
        macro_cell_size=args.macro_cell_size,
        batch_size=args.batch_size,
        seed=f"{args.calibration_seed}:spam-reference",
        device=device,
    )

    payload_features = spam_features(payload_images, truncation=args.residual_truncation)
    reference_features = spam_features(reference_images, truncation=args.residual_truncation)
    metrics = detector_metrics(payload_features, reference_features)
    row = {
        "model_dir": model_reference(args.model_dir),
        "model_subfolder": args.model_subfolder or "",
        "detector": "SPAM-style residual cooccurrence + logistic regression",
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
        "residual_truncation": args.residual_truncation,
        "feature_dim": payload_features.shape[1],
        **metrics,
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


def spam_features(images: list[Image.Image], truncation: int = 3) -> np.ndarray:
    return np.asarray([spam_feature(image, truncation=truncation) for image in images], dtype=np.float64)


def spam_feature(image: Image.Image, truncation: int = 3) -> np.ndarray:
    gray = np.asarray(image.convert("L"), dtype=np.float32)
    parts = []
    for residual, direction in residuals(gray):
        clipped = np.clip(np.rint(residual), -truncation, truncation).astype(np.int16) + truncation
        parts.append(cooccurrence_hist(clipped, truncation=truncation, direction=direction))
        values = residual.reshape(-1)
        parts.append(
            np.asarray(
                [
                    float(np.mean(np.abs(values))),
                    float(np.std(values)),
                    float(np.mean(values > 0.0)),
                    float(np.mean(values < 0.0)),
                ],
                dtype=np.float64,
            )
        )
    return np.concatenate(parts)


def residuals(gray: np.ndarray) -> list[tuple[np.ndarray, str]]:
    return [
        (gray[:, 1:] - gray[:, :-1], "h"),
        (gray[1:, :] - gray[:-1, :], "v"),
        (gray[1:, 1:] - gray[:-1, :-1], "d"),
        (gray[1:, :-1] - gray[:-1, 1:], "a"),
    ]


def cooccurrence_hist(values: np.ndarray, truncation: int, direction: str) -> np.ndarray:
    cardinality = 2 * truncation + 1
    if direction == "h":
        triplets = [values[:, :-2], values[:, 1:-1], values[:, 2:]]
    elif direction == "v":
        triplets = [values[:-2, :], values[1:-1, :], values[2:, :]]
    elif direction == "d":
        triplets = [values[:-2, :-2], values[1:-1, 1:-1], values[2:, 2:]]
    else:
        triplets = [values[:-2, 2:], values[1:-1, 1:-1], values[2:, :-2]]
    if triplets[0].size == 0:
        return np.zeros(cardinality**3, dtype=np.float64)
    codes = np.ravel_multi_index([part.reshape(-1) for part in triplets], dims=(cardinality, cardinality, cardinality))
    hist = np.bincount(codes, minlength=cardinality**3).astype(np.float64)
    total = hist.sum()
    return hist / total if total else hist


def detector_metrics(payload_features: np.ndarray, reference_features: np.ndarray) -> dict[str, float]:
    try:
        from sklearn.linear_model import LogisticRegression
        from sklearn.metrics import accuracy_score, roc_auc_score
        from sklearn.model_selection import train_test_split
        from sklearn.pipeline import make_pipeline
        from sklearn.preprocessing import StandardScaler

        x = np.vstack([payload_features, reference_features])
        y = np.asarray([1] * len(payload_features) + [0] * len(reference_features), dtype=np.int32)
        x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=0.35, random_state=1234, stratify=y)
        model = make_pipeline(StandardScaler(), LogisticRegression(max_iter=2000, random_state=1234))
        model.fit(x_train, y_train)
        scores = model.predict_proba(x_test)[:, 1]
        predictions = (scores >= 0.5).astype(np.int32)
        return {
            "spam_detector_auc": round(float(roc_auc_score(y_test, scores)), 8),
            "spam_detector_accuracy": round(float(accuracy_score(y_test, predictions)), 8),
        }
    except Exception:
        return {"spam_detector_auc": -1.0, "spam_detector_accuracy": -1.0}


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


if __name__ == "__main__":
    raise SystemExit(main())
