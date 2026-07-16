from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
import random
import sys

ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parents[2]
sys.path.insert(0, str(ROOT))

from PIL import Image

from vq_fountain.bitstream import PayloadDecodeError, pack_payload, unpack_payload
from vq_fountain.fountain import FountainDecodeError, FountainSymbol, decode_symbols, encode_symbols
from vq_fountain.image_attacks import apply_attack
from vq_fountain.scheduler import keyed_order
from vq_fountain.tokenizer_adapter import build_tokenizer, stable_position_mask

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


def main() -> int:
    parser = argparse.ArgumentParser(description="Probe payload recovery from measured token stability.")
    parser.add_argument("--image-root", default=str(REPO_ROOT / "05_artifacts" / "data" / "sample_images"))
    parser.add_argument("--tokenizer", default="patch-vq")
    parser.add_argument("--codebook", default=None)
    parser.add_argument("--image-size", type=int, default=256)
    parser.add_argument("--patch-size", type=int, default=16)
    parser.add_argument("--levels", type=int, default=8)
    parser.add_argument("--payload-bytes", type=int, nargs="+", default=[32, 64, 128])
    parser.add_argument("--bits-per-token", type=int, nargs="+", default=[1, 2])
    parser.add_argument("--overheads", type=float, nargs="+", default=[0.5, 0.8, 1.2])
    parser.add_argument("--block-size", type=int, default=8)
    parser.add_argument("--image-copies", type=int, nargs="+", default=[2, 4, 8, 12])
    parser.add_argument("--attacks", nargs="+", default=["jpeg85", "resize075", "blur1", "noise002"])
    parser.add_argument("--schedule", choices=["random", "stability"], default="stability")
    parser.add_argument("--max-images", type=int, default=None)
    parser.add_argument("--seed", default="token-probe")
    parser.add_argument(
        "--out-csv",
        default=str(REPO_ROOT / "05_artifacts" / "results" / "tables" / "vq_fountain_token_recovery_probe.csv"),
    )
    parser.add_argument(
        "--out-json",
        default=str(REPO_ROOT / "05_artifacts" / "results" / "raw" / "vq_fountain_token_recovery_probe.json"),
    )
    args = parser.parse_args()

    tokenizer = build_tokenizer(
        args.tokenizer,
        image_size=args.image_size,
        patch_size=args.patch_size,
        levels=args.levels,
        codebook_path=args.codebook,
    )
    profiles = build_profiles(
        image_root=Path(args.image_root),
        tokenizer=tokenizer,
        attacks=args.attacks,
        max_images=args.max_images,
        seed=args.seed,
    )
    if not profiles:
        raise SystemExit(f"no images found under {args.image_root}")

    rows: list[dict[str, object]] = []
    raw: list[dict[str, object]] = []
    for payload_bytes in args.payload_bytes:
        for bits_per_token in args.bits_per_token:
            for overhead in args.overheads:
                for image_copies in args.image_copies:
                    result = run_condition(
                        profiles=profiles,
                        payload_bytes=payload_bytes,
                        bits_per_token=bits_per_token,
                        overhead=overhead,
                        block_size=args.block_size,
                        image_copies=image_copies,
                        schedule=args.schedule,
                        seed=args.seed,
                    )
                    rows.append(result["row"])
                    raw.append(result["raw"])

    write_csv(Path(args.out_csv), rows)
    write_json(Path(args.out_json), raw)
    print(json.dumps({"csv": args.out_csv, "json": args.out_json, "rows": len(rows)}, indent=2))
    return 0


def build_profiles(
    image_root: Path,
    tokenizer,
    attacks: list[str],
    max_images: int | None,
    seed: int | str,
) -> list[dict[str, object]]:
    profiles: list[dict[str, object]] = []
    for path in collect_images(image_root, max_images=max_images, seed=seed):
        with Image.open(path) as image:
            reference = tokenizer.encode_image(image)
            grids = []
            for attack in attacks:
                attacked = apply_attack(image, attack, seed=f"{seed}:{path}:{attack}")
                grids.append(tokenizer.encode_image(attacked))
            stable_mask = stable_position_mask([reference] + grids).reshape(-1)
            profiles.append(
                {
                    "image": normalize_path(path),
                    "token_count": int(reference.flat.size),
                    "stable_mask": stable_mask,
                    "stable_positions": int(stable_mask.sum()),
                    "stable_rate": float(stable_mask.mean()),
                }
            )
    return profiles


def run_condition(
    profiles: list[dict[str, object]],
    payload_bytes: int,
    bits_per_token: int,
    overhead: float,
    block_size: int,
    image_copies: int,
    schedule: str,
    seed: int | str,
) -> dict[str, object]:
    payload = deterministic_payload(payload_bytes, seed=seed)
    packet = pack_payload(payload)
    symbols = encode_symbols(packet, block_size=block_size, overhead=overhead, seed=seed)
    slots_per_symbol = math.ceil((block_size * 8) / bits_per_token)

    placements = place_symbols(
        profiles=profiles,
        symbol_count=len(symbols),
        slots_per_symbol=slots_per_symbol,
        image_copies=image_copies,
        schedule=schedule,
        seed=seed,
    )
    delivered_symbols = [symbols[index] for index, delivered in enumerate(placements["delivered"]) if delivered]
    exact = False
    failure = ""
    try:
        recovered_payload = unpack_payload(decode_symbols(delivered_symbols))
        exact = recovered_payload == payload
    except (FountainDecodeError, PayloadDecodeError, IndexError) as exc:
        failure = str(exc)

    delivered_count = len(delivered_symbols)
    total_token_slots = int(placements["used_slots"])
    raw_capacity_bits = total_token_slots * bits_per_token
    row = {
        "payload_bytes": payload_bytes,
        "packet_bytes": len(packet),
        "block_size": block_size,
        "bits_per_token": bits_per_token,
        "overhead": overhead,
        "image_copies": image_copies,
        "schedule": schedule,
        "source_symbols": symbols[0].source_count,
        "encoded_symbols": len(symbols),
        "delivered_symbols": delivered_count,
        "slots_per_symbol": slots_per_symbol,
        "used_token_slots": total_token_slots,
        "raw_capacity_bits": raw_capacity_bits,
        "exact_recovery": exact,
        "failure": failure,
    }
    return {"row": row, "raw": {**row, "profiles": profile_summary(profiles)}}


def place_symbols(
    profiles: list[dict[str, object]],
    symbol_count: int,
    slots_per_symbol: int,
    image_copies: int,
    schedule: str,
    seed: int | str,
) -> dict[str, object]:
    slots: list[bool] = []
    for copy_index in range(image_copies):
        profile = profiles[copy_index % len(profiles)]
        stable_mask = profile["stable_mask"]
        if not hasattr(stable_mask, "tolist"):
            raise ValueError("profile stable_mask is invalid")
        stabilities = [bool(value) for value in stable_mask.tolist()]
        positions = order_positions(stabilities, schedule=schedule, seed=f"{seed}:{copy_index}")
        slots.extend(stabilities[index] for index in positions)

    required_slots = symbol_count * slots_per_symbol
    if len(slots) < required_slots:
        delivered = [False] * symbol_count
        return {"delivered": delivered, "used_slots": len(slots)}

    delivered: list[bool] = []
    for symbol_index in range(symbol_count):
        start = symbol_index * slots_per_symbol
        end = start + slots_per_symbol
        delivered.append(all(slots[start:end]))
    return {"delivered": delivered, "used_slots": required_slots}


def order_positions(stabilities: list[bool], schedule: str, seed: int | str) -> list[int]:
    positions = list(range(len(stabilities)))
    if schedule == "random":
        return keyed_order(positions, key=seed, context="token-probe")
    stable = [index for index in positions if stabilities[index]]
    unstable = [index for index in positions if not stabilities[index]]
    return keyed_order(stable, key=seed, context="stable") + keyed_order(unstable, key=seed, context="unstable")


def collect_images(root: Path, max_images: int | None = None, seed: int | str = "token-probe") -> list[Path]:
    if root.is_file() and root.suffix.lower() in IMAGE_EXTENSIONS:
        return [root]
    paths = sorted(path for path in root.rglob("*") if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS)
    if max_images is None:
        return paths
    rng = random.Random(str(seed))
    rng.shuffle(paths)
    return paths[:max_images]


def deterministic_payload(size: int, seed: int | str) -> bytes:
    rng = random.Random(f"{seed}:{size}")
    return bytes(rng.randrange(0, 256) for _ in range(size))


def profile_summary(profiles: list[dict[str, object]]) -> list[dict[str, object]]:
    return [
        {
            "image": str(profile["image"]),
            "token_count": int(profile["token_count"]),
            "stable_positions": int(profile["stable_positions"]),
            "stable_rate": round(float(profile["stable_rate"]), 6),
        }
        for profile in profiles
    ]


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(rows[0].keys())
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, payload: list[dict[str, object]]) -> None:
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
