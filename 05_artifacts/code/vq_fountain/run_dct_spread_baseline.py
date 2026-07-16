from __future__ import annotations

import argparse
import csv
import json
import random
from pathlib import Path
import sys

import numpy as np
from PIL import Image
from scipy.fftpack import dct, idct

ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parents[2]
sys.path.insert(0, str(ROOT))

from vq_fountain.image_attacks import apply_attack


def main() -> int:
    parser = argparse.ArgumentParser(description="Executable classical DCT spread-spectrum image-hiding baseline.")
    parser.add_argument(
        "--source-image",
        default=str(REPO_ROOT / "05_artifacts" / "results" / "raw" / "vq_fountain_real_vqgan_payload_sample_128px.png"),
    )
    parser.add_argument("--message-bits", type=int, default=32)
    parser.add_argument("--repetition", type=int, default=7)
    parser.add_argument("--strength", type=float, default=28.0)
    parser.add_argument("--seed", default="dct-spread-baseline")
    parser.add_argument("--attacks", nargs="+", default=["clean", "jpeg85", "resize075", "blur1", "crop090"])
    parser.add_argument(
        "--out-image",
        default=str(REPO_ROOT / "05_artifacts" / "results" / "raw" / "dct_spread_baseline_encoded.png"),
    )
    parser.add_argument(
        "--out-csv",
        default=str(REPO_ROOT / "05_artifacts" / "results" / "tables" / "dct_spread_baseline.csv"),
    )
    parser.add_argument(
        "--out-json",
        default=str(REPO_ROOT / "05_artifacts" / "results" / "raw" / "dct_spread_baseline.json"),
    )
    args = parser.parse_args()

    image = Image.open(args.source_image).convert("RGB").resize((128, 128), Image.Resampling.BICUBIC)
    bits = deterministic_bits(args.message_bits, args.seed)
    encoded = embed_bits(image, bits, repetition=args.repetition, strength=args.strength, seed=args.seed)
    out_image = Path(args.out_image)
    out_image.parent.mkdir(parents=True, exist_ok=True)
    encoded.save(out_image)

    rows = []
    for attack in args.attacks:
        attacked = apply_attack(encoded, attack, seed=f"{args.seed}:{attack}")
        decoded = decode_bits(attacked, args.message_bits, repetition=args.repetition, seed=args.seed)
        errors = sum(int(left != right) for left, right in zip(bits, decoded))
        rows.append(
            {
                "baseline": "DCT-spread",
                "source_image": display_path(Path(args.source_image)),
                "encoded_image": display_path(out_image),
                "attack": attack,
                "message_bits": args.message_bits,
                "repetition": args.repetition,
                "strength": args.strength,
                "bit_errors": errors,
                "bit_error_rate": round(errors / args.message_bits, 8),
                "exact_recovery": errors == 0,
                "psnr_db": round(psnr(image, encoded), 6),
            }
        )
    payload = {"bits": bits, "rows": rows}
    write_csv(Path(args.out_csv), rows)
    write_json(Path(args.out_json), payload)
    print(json.dumps({"csv": display_path(Path(args.out_csv)), "json": display_path(Path(args.out_json)), "rows": len(rows)}, indent=2))
    return 0


def embed_bits(image: Image.Image, bits: list[int], repetition: int, strength: float, seed: str) -> Image.Image:
    ycbcr = image.convert("YCbCr")
    array = np.asarray(ycbcr, dtype=np.float32)
    y = array[:, :, 0].copy()
    blocks = block_positions(y.shape[0], y.shape[1])
    required = len(bits) * repetition
    if required > len(blocks):
        raise ValueError("message does not fit")
    order = keyed_order(blocks, seed)
    for bit_index, bit in enumerate(bits):
        for rep in range(repetition):
            row, col = order[bit_index * repetition + rep]
            block = y[row : row + 8, col : col + 8]
            coeff = dct2(block - 128.0)
            magnitude = max(abs(float(coeff[3, 2])), strength)
            coeff[3, 2] = magnitude if bit else -magnitude
            y[row : row + 8, col : col + 8] = idct2(coeff) + 128.0
    out = array.copy()
    out[:, :, 0] = np.clip(y, 0, 255)
    return Image.fromarray(out.round().astype(np.uint8), mode="YCbCr").convert("RGB")


def decode_bits(image: Image.Image, message_bits: int, repetition: int, seed: str) -> list[int]:
    y = np.asarray(image.convert("YCbCr"), dtype=np.float32)[:, :, 0]
    blocks = block_positions(y.shape[0], y.shape[1])
    order = keyed_order(blocks, seed)
    decoded = []
    for bit_index in range(message_bits):
        votes = 0
        for rep in range(repetition):
            row, col = order[bit_index * repetition + rep]
            coeff = dct2(y[row : row + 8, col : col + 8] - 128.0)
            votes += 1 if coeff[3, 2] >= 0 else -1
        decoded.append(1 if votes >= 0 else 0)
    return decoded


def dct2(block: np.ndarray) -> np.ndarray:
    return dct(dct(block.T, norm="ortho").T, norm="ortho")


def idct2(coeff: np.ndarray) -> np.ndarray:
    return idct(idct(coeff.T, norm="ortho").T, norm="ortho")


def block_positions(height: int, width: int) -> list[tuple[int, int]]:
    return [(row, col) for row in range(0, height - 7, 8) for col in range(0, width - 7, 8)]


def keyed_order(items: list[tuple[int, int]], seed: str) -> list[tuple[int, int]]:
    rng = random.Random(seed)
    ordered = list(items)
    rng.shuffle(ordered)
    return ordered


def deterministic_bits(count: int, seed: str) -> list[int]:
    rng = random.Random(seed)
    return [rng.randrange(2) for _ in range(count)]


def psnr(left: Image.Image, right: Image.Image) -> float:
    a = np.asarray(left, dtype=np.float32)
    b = np.asarray(right, dtype=np.float32)
    mse = float(np.mean((a - b) ** 2))
    if mse <= 1e-12:
        return 99.0
    return 20.0 * float(np.log10(255.0 / np.sqrt(mse)))


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
