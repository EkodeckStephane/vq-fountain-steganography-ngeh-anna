from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import random
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


class SmallSteganalysisCNN(torch.nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.net = torch.nn.Sequential(
            torch.nn.Conv2d(3, 16, kernel_size=3, padding=1),
            torch.nn.ReLU(),
            torch.nn.AvgPool2d(2),
            torch.nn.Conv2d(16, 32, kernel_size=3, padding=1),
            torch.nn.ReLU(),
            torch.nn.AvgPool2d(2),
            torch.nn.Conv2d(32, 64, kernel_size=3, padding=1),
            torch.nn.ReLU(),
            torch.nn.AdaptiveAvgPool2d((1, 1)),
            torch.nn.Flatten(),
            torch.nn.Linear(64, 1),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x).squeeze(1)


def main() -> int:
    parser = argparse.ArgumentParser(description="Small CNN steganalysis probe for real VQGAN payload images.")
    parser.add_argument("--model-dir", default=str(REPO_ROOT / "05_artifacts" / "models" / "vqgan_f4_8192_diffusers_converted"))
    parser.add_argument("--model-subfolder", default=None)
    parser.add_argument("--allow-download", action="store_true")
    parser.add_argument("--payload-bytes", type=int, default=32)
    parser.add_argument("--block-size", type=int, default=1)
    parser.add_argument("--overhead", type=float, default=3.0)
    parser.add_argument("--latent-side", type=int, default=16)
    parser.add_argument("--macro-cell-size", type=int, default=2)
    parser.add_argument("--symbols-per-image", type=int, default=8)
    parser.add_argument("--payload-seeds", nargs="+", default=["deep-a", "deep-b", "deep-c", "deep-d"])
    parser.add_argument("--calibration-seed", default="real-vqgan-calibration-v1")
    parser.add_argument("--calibration-count", type=int, default=256)
    parser.add_argument("--calibration-threshold", type=float, default=0.90)
    parser.add_argument("--calibration-batch-size", type=int, default=8)
    parser.add_argument("--batch-size", type=int, default=4)
    parser.add_argument("--epochs", type=int, default=20)
    parser.add_argument("--device", default="cpu")
    parser.add_argument(
        "--out-csv",
        default=str(REPO_ROOT / "05_artifacts" / "results" / "tables" / "vq_fountain_real_vqgan_deep_steganalysis.csv"),
    )
    parser.add_argument(
        "--out-json",
        default=str(REPO_ROOT / "05_artifacts" / "results" / "raw" / "vq_fountain_real_vqgan_deep_steganalysis.json"),
    )
    args = parser.parse_args()

    from diffusers import VQModel

    set_deterministic(1234)
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

    reference_images = generate_reference_images(
        model=vq_model,
        pools=pools,
        count=len(payload_images),
        latent_side=args.latent_side,
        macro_cell_size=args.macro_cell_size,
        batch_size=args.batch_size,
        seed=f"{args.calibration_seed}:deep-reference",
        device=device,
    )
    x = torch.stack([image_tensor(image) for image in payload_images + reference_images])
    y = torch.tensor([1.0] * len(payload_images) + [0.0] * len(reference_images))
    train_idx, test_idx = stratified_split(len(payload_images), len(reference_images), test_fraction=0.35, seed=1234)

    detector = SmallSteganalysisCNN().to(device)
    optimizer = torch.optim.Adam(detector.parameters(), lr=1e-3, weight_decay=1e-4)
    loss_fn = torch.nn.BCEWithLogitsLoss()
    x_train = x[train_idx].to(device)
    y_train = y[train_idx].to(device)
    x_test = x[test_idx].to(device)
    y_test = y[test_idx].to(device)
    for _epoch in range(args.epochs):
        detector.train()
        permutation = torch.randperm(x_train.shape[0], device=device)
        for start in range(0, x_train.shape[0], 16):
            batch_idx = permutation[start : start + 16]
            logits = detector(x_train[batch_idx])
            loss = loss_fn(logits, y_train[batch_idx])
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

    detector.eval()
    with torch.no_grad():
        scores = torch.sigmoid(detector(x_test)).detach().cpu().numpy()
    y_true = y_test.detach().cpu().numpy()
    auc = roc_auc(y_true, scores)
    accuracy = float(((scores >= 0.5).astype(np.float32) == y_true).mean())
    row = {
        "model_dir": model_reference(args.model_dir),
        "model_subfolder": args.model_subfolder or "",
        "payload_bytes": args.payload_bytes,
        "payload_images": len(payload_images),
        "reference_images": len(reference_images),
        "train_samples": len(train_idx),
        "test_samples": len(test_idx),
        "epochs": args.epochs,
        "stable_pool_0": len(pools[0]),
        "stable_pool_1": len(pools[1]),
        "cnn_detector_auc": round(auc, 8),
        "cnn_detector_accuracy": round(accuracy, 8),
    }
    payload = {
        "row": row,
        "payload_seeds": args.payload_seeds,
        "calibration_seed": args.calibration_seed,
        "detector": "SmallSteganalysisCNN",
    }
    write_csv(Path(args.out_csv), [row])
    write_json(Path(args.out_json), payload)
    print(json.dumps({"csv": display_path(Path(args.out_csv)), "json": display_path(Path(args.out_json)), "rows": 1}, indent=2))
    return 0


def image_tensor(image: Image.Image) -> torch.Tensor:
    array = np.asarray(image.convert("RGB"), dtype=np.float32) / 255.0
    array = (array - 0.5) / 0.5
    return torch.from_numpy(array).permute(2, 0, 1)


def stratified_split(payload_count: int, reference_count: int, test_fraction: float, seed: int) -> tuple[list[int], list[int]]:
    rng = random.Random(seed)
    payload_indices = list(range(payload_count))
    reference_indices = list(range(payload_count, payload_count + reference_count))
    rng.shuffle(payload_indices)
    rng.shuffle(reference_indices)
    payload_test = max(1, round(payload_count * test_fraction))
    reference_test = max(1, round(reference_count * test_fraction))
    test = payload_indices[:payload_test] + reference_indices[:reference_test]
    train = payload_indices[payload_test:] + reference_indices[reference_test:]
    rng.shuffle(train)
    rng.shuffle(test)
    return train, test


def roc_auc(y_true: np.ndarray, scores: np.ndarray) -> float:
    try:
        from sklearn.metrics import roc_auc_score

        return float(roc_auc_score(y_true, scores))
    except Exception:
        positives = scores[y_true == 1]
        negatives = scores[y_true == 0]
        wins = 0.0
        total = 0
        for positive in positives:
            for negative in negatives:
                wins += 1.0 if positive > negative else 0.5 if positive == negative else 0.0
                total += 1
        return wins / max(1, total)


def set_deterministic(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)


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
