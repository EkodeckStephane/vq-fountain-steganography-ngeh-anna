from __future__ import annotations

import argparse
import json
from pathlib import Path
import random
import sys

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parents[2]
sys.path.insert(0, str(ROOT))

from vq_fountain.tokenizer_adapter import image_to_patch_matrix, nearest_codebook_indices

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp", ".pgm", ".ppm", ".tif", ".tiff"}


def main() -> int:
    parser = argparse.ArgumentParser(description="Train a lightweight learned patch VQ codebook.")
    parser.add_argument("--image-root", nargs="+", required=True)
    parser.add_argument("--image-size", type=int, default=256)
    parser.add_argument("--patch-size", type=int, default=16)
    parser.add_argument("--codebook-size", type=int, default=256)
    parser.add_argument("--max-images", type=int, default=200)
    parser.add_argument("--max-patches", type=int, default=30000)
    parser.add_argument("--iterations", type=int, default=10)
    parser.add_argument("--seed", default="learned-patch-vq")
    parser.add_argument(
        "--out",
        default=str(REPO_ROOT / "05_artifacts" / "models" / "learned_patch_vq_stage1.npz"),
    )
    parser.add_argument(
        "--metadata-out",
        default=str(REPO_ROOT / "05_artifacts" / "models" / "learned_patch_vq_stage1_metadata.json"),
    )
    args = parser.parse_args()

    image_paths = collect_images([Path(root) for root in args.image_root], max_images=args.max_images, seed=args.seed)
    if not image_paths:
        raise SystemExit("no training images found")

    patches = sample_patches(
        image_paths=image_paths,
        image_size=args.image_size,
        patch_size=args.patch_size,
        max_patches=args.max_patches,
        seed=args.seed,
    )
    codebook, token_prior, history = train_kmeans(
        patches=patches,
        codebook_size=args.codebook_size,
        iterations=args.iterations,
        seed=args.seed,
    )

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        out_path,
        codebook=codebook.astype(np.float32),
        token_prior=token_prior.astype(np.float64),
        image_size=np.array(args.image_size, dtype=np.int32),
        patch_size=np.array(args.patch_size, dtype=np.int32),
    )

    metadata = {
        "tokenizer": "learned-patch-vq",
        "image_size": args.image_size,
        "patch_size": args.patch_size,
        "codebook_size": args.codebook_size,
        "max_images": args.max_images,
        "used_images": len(image_paths),
        "max_patches": args.max_patches,
        "used_patches": int(patches.shape[0]),
        "iterations": args.iterations,
        "prior_min": round(float(token_prior.min()), 8),
        "prior_max": round(float(token_prior.max()), 8),
        "history": history,
        "source_roots": [f"root_{index}" for index, _ in enumerate(args.image_root)],
    }
    metadata_path = Path(args.metadata_out)
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    with metadata_path.open("w", encoding="utf-8") as handle:
        json.dump(metadata, handle, indent=2, sort_keys=True)

    print(json.dumps({"codebook": str(out_path), "metadata": str(metadata_path), **metadata}, indent=2))
    return 0


def collect_images(roots: list[Path], max_images: int, seed: int | str) -> list[Path]:
    paths: list[Path] = []
    for root in roots:
        if root.is_file() and root.suffix.lower() in IMAGE_EXTENSIONS:
            paths.append(root)
        elif root.exists():
            paths.extend(
                path for path in root.rglob("*") if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS
            )
    paths = sorted(set(paths))
    rng = random.Random(str(seed))
    rng.shuffle(paths)
    return paths[:max_images]


def sample_patches(
    image_paths: list[Path],
    image_size: int,
    patch_size: int,
    max_patches: int,
    seed: int | str,
) -> np.ndarray:
    matrices: list[np.ndarray] = []
    for path in image_paths:
        try:
            with Image.open(path) as image:
                matrices.append(image_to_patch_matrix(image, image_size=image_size, patch_size=patch_size))
        except OSError:
            continue
    if not matrices:
        raise SystemExit("no readable training images")
    patches = np.concatenate(matrices, axis=0)
    if patches.shape[0] > max_patches:
        rng = np.random.default_rng(seed_to_uint64(seed))
        indices = rng.choice(patches.shape[0], size=max_patches, replace=False)
        patches = patches[indices]
    return patches.astype(np.float32)


def train_kmeans(
    patches: np.ndarray,
    codebook_size: int,
    iterations: int,
    seed: int | str,
) -> tuple[np.ndarray, np.ndarray, list[dict[str, float]]]:
    if patches.shape[0] < codebook_size:
        raise ValueError("not enough patches for requested codebook_size")
    rng = np.random.default_rng(seed_to_uint64(seed))
    centers = patches[rng.choice(patches.shape[0], size=codebook_size, replace=False)].copy()
    history: list[dict[str, float]] = []

    counts = np.zeros(codebook_size, dtype=np.int64)
    for iteration in range(iterations):
        assignments = nearest_codebook_indices(patches, centers, chunk_size=2048)
        counts = np.bincount(assignments, minlength=codebook_size).astype(np.int64)
        new_centers = np.zeros_like(centers)
        np.add.at(new_centers, assignments, patches)
        empty = counts == 0
        non_empty = ~empty
        new_centers[non_empty] /= counts[non_empty, None]
        if empty.any():
            replacement_indices = rng.choice(patches.shape[0], size=int(empty.sum()), replace=False)
            new_centers[empty] = patches[replacement_indices]

        distortion = mean_squared_distortion(patches, new_centers, chunk_size=2048)
        centers = new_centers
        history.append(
            {
                "iteration": float(iteration + 1),
                "mean_squared_distortion": round(float(distortion), 8),
                "empty_clusters": float(empty.sum()),
            }
        )
    final_assignments = nearest_codebook_indices(patches, centers, chunk_size=2048)
    final_counts = np.bincount(final_assignments, minlength=codebook_size).astype(np.float64)
    token_prior = (final_counts + 1.0) / (final_counts.sum() + codebook_size)
    return centers.astype(np.float32), token_prior.astype(np.float64), history


def mean_squared_distortion(patches: np.ndarray, centers: np.ndarray, chunk_size: int) -> float:
    total = 0.0
    count = 0
    for start in range(0, patches.shape[0], chunk_size):
        chunk = patches[start : start + chunk_size]
        assignments = nearest_codebook_indices(chunk, centers, chunk_size=chunk_size)
        residual = chunk - centers[assignments]
        total += float(np.sum(residual * residual))
        count += int(np.prod(residual.shape))
    return total / count


def seed_to_uint64(seed: int | str) -> int:
    if isinstance(seed, int):
        return seed & ((1 << 64) - 1)
    import hashlib

    digest = hashlib.sha256(str(seed).encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "big")


if __name__ == "__main__":
    raise SystemExit(main())
