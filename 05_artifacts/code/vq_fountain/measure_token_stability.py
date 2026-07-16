from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import random
import sys

ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parents[2]
sys.path.insert(0, str(ROOT))

from PIL import Image

from vq_fountain.image_attacks import apply_attack
from vq_fountain.tokenizer_adapter import build_tokenizer, stable_position_mask, token_match_rate

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp", ".pgm", ".ppm", ".tif", ".tiff"}


def main() -> int:
    parser = argparse.ArgumentParser(description="Measure token stability under image transformations.")
    parser.add_argument("--image-root", default=str(REPO_ROOT / "05_artifacts" / "data" / "sample_images"))
    parser.add_argument("--tokenizer", default="patch-vq")
    parser.add_argument("--codebook", default=None)
    parser.add_argument("--image-size", type=int, default=256)
    parser.add_argument("--patch-size", type=int, default=16)
    parser.add_argument("--levels", type=int, default=8)
    parser.add_argument(
        "--attacks",
        nargs="+",
        default=["clean", "jpeg95", "jpeg85", "resize075", "blur1", "noise002", "crop090"],
    )
    parser.add_argument("--max-images", type=int, default=None)
    parser.add_argument("--seed", default="token-stability")
    parser.add_argument(
        "--out-csv",
        default=str(REPO_ROOT / "05_artifacts" / "results" / "tables" / "vq_fountain_token_stability_stage1.csv"),
    )
    parser.add_argument(
        "--out-json",
        default=str(REPO_ROOT / "05_artifacts" / "results" / "raw" / "vq_fountain_token_stability_stage1.json"),
    )
    args = parser.parse_args()

    tokenizer = build_tokenizer(
        args.tokenizer,
        image_size=args.image_size,
        patch_size=args.patch_size,
        levels=args.levels,
        codebook_path=args.codebook,
    )
    image_paths = collect_images(Path(args.image_root), max_images=args.max_images, seed=args.seed)
    if not image_paths:
        raise SystemExit(f"no images found under {args.image_root}")

    rows: list[dict[str, object]] = []
    raw: list[dict[str, object]] = []
    for image_path in image_paths:
        with Image.open(image_path) as image:
            reference = tokenizer.encode_image(image)
            attack_grids = []
            for attack in args.attacks:
                attacked = apply_attack(image, attack, seed=str(image_path))
                grid = tokenizer.encode_image(attacked)
                attack_grids.append(grid)
                match_rate = token_match_rate(reference, grid)
                changed = int(reference.flat.size - (reference.flat == grid.flat).sum())
                raw.append(
                    {
                        "image": normalize_path(image_path),
                        "tokenizer": tokenizer.name,
                        "attack": attack,
                        "token_count": int(reference.flat.size),
                        "changed_tokens": changed,
                        "token_match_rate": round(match_rate, 6),
                    }
                )

            stable_mask = stable_position_mask([reference] + attack_grids)
            rows.append(
                {
                    "image": normalize_path(image_path),
                    "tokenizer": tokenizer.name,
                    "image_size": args.image_size,
                    "patch_size": args.patch_size,
                    "levels": args.levels,
                    "codebook_size": tokenizer.codebook_size,
                    "token_grid": f"{reference.shape[0]}x{reference.shape[1]}",
                    "token_count": int(reference.flat.size),
                    "attacks": " ".join(args.attacks),
                    "stable_positions_all_attacks": int(stable_mask.sum()),
                    "stable_position_rate_all_attacks": round(float(stable_mask.mean()), 6),
                }
            )

    aggregate = aggregate_by_attack(raw)
    write_csv(Path(args.out_csv), rows + aggregate)
    write_json(Path(args.out_json), {"images": rows, "attacks": raw, "aggregate": aggregate})
    print(
        json.dumps(
            {
                "images": len(image_paths),
                "tokenizer": tokenizer.name,
                "csv": args.out_csv,
                "json": args.out_json,
                "aggregate": aggregate,
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


def collect_images(root: Path, max_images: int | None = None, seed: int | str = "token-stability") -> list[Path]:
    if root.is_file() and root.suffix.lower() in IMAGE_EXTENSIONS:
        return [root]
    paths = sorted(path for path in root.rglob("*") if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS)
    if max_images is None:
        return paths
    rng = random.Random(str(seed))
    rng.shuffle(paths)
    return paths[:max_images]


def aggregate_by_attack(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    attacks = sorted({str(row["attack"]) for row in rows})
    aggregate: list[dict[str, object]] = []
    for attack in attacks:
        subset = [row for row in rows if row["attack"] == attack]
        mean_match = sum(float(row["token_match_rate"]) for row in subset) / len(subset)
        mean_changed = sum(int(row["changed_tokens"]) for row in subset) / len(subset)
        aggregate.append(
            {
                "image": "<aggregate>",
                "tokenizer": str(subset[0]["tokenizer"]),
                "image_size": "",
                "patch_size": "",
                "levels": "",
                "codebook_size": "",
                "token_grid": "",
                "token_count": int(subset[0]["token_count"]),
                "attacks": attack,
                "stable_positions_all_attacks": "",
                "stable_position_rate_all_attacks": "",
                "mean_changed_tokens": round(mean_changed, 3),
                "mean_token_match_rate": round(mean_match, 6),
            }
        )
    return aggregate


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "image",
        "tokenizer",
        "image_size",
        "patch_size",
        "levels",
        "codebook_size",
        "token_grid",
        "token_count",
        "attacks",
        "stable_positions_all_attacks",
        "stable_position_rate_all_attacks",
        "mean_changed_tokens",
        "mean_token_match_rate",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)


def normalize_path(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT)).replace("\\", "/")
    except ValueError:
        return path.name


if __name__ == "__main__":
    raise SystemExit(main())
