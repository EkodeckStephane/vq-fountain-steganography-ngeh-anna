from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parents[2]
sys.path.insert(0, str(ROOT))

from run_distribution_sampler_probe import generate_payload_images, recover_from_images
from vq_fountain.token_sampler import PriorBinCodec
from vq_fountain.tokenizer_adapter import build_tokenizer


def main() -> int:
    parser = argparse.ArgumentParser(description="Run final ablations for VQ-Fountain Stage 1.")
    parser.add_argument("--tokenizer", default="learned-patch-vq")
    parser.add_argument("--codebook", default=str(REPO_ROOT / "05_artifacts" / "models" / "learned_patch_vq_stage1_k128.npz"))
    parser.add_argument("--payload-bytes", type=int, default=64)
    parser.add_argument("--bits-per-token", type=int, default=1)
    parser.add_argument("--block-size", type=int, default=1)
    parser.add_argument("--overhead", type=float, default=4.0)
    parser.add_argument("--image-copies", type=int, default=16)
    parser.add_argument("--attack", default="crop090_r02_c-02")
    parser.add_argument("--seed", default="final-ablation")
    parser.add_argument(
        "--out-csv",
        default=str(REPO_ROOT / "05_artifacts" / "results" / "tables" / "vq_fountain_final_ablation_suite.csv"),
    )
    parser.add_argument(
        "--out-json",
        default=str(REPO_ROOT / "05_artifacts" / "results" / "raw" / "vq_fountain_final_ablation_suite.json"),
    )
    args = parser.parse_args()

    tokenizer = build_tokenizer(args.tokenizer, codebook_path=args.codebook)
    variants = [
        ("coding", "fountain", {"coding": "fountain"}),
        ("coding", "repetition", {"coding": "repetition"}),
        ("sampling", "projection", {"binning": "projection"}),
        ("sampling", "naive", {"binning": "naive"}),
        ("anchors", "block_1_per_4x4", {"anchor_scope": "block", "anchor_count": 1}),
        ("anchors", "global_9", {"anchor_scope": "global", "anchor_count": 9}),
        ("schedule", "center", {"position_mode": "center", "anchor_scope": "global", "anchor_count": 9}),
        ("schedule", "random", {"position_mode": "random", "anchor_scope": "global", "anchor_count": 9}),
        ("block_rejection", "off", {"anchor_scope": "block", "anchor_count": 2, "block_anchor_threshold": 0.0}),
        ("block_rejection", "threshold_0_5", {"anchor_scope": "block", "anchor_count": 2, "block_anchor_threshold": 0.5}),
    ]

    rows: list[dict[str, object]] = []
    for ablation, variant, overrides in variants:
        config = {
            "coding": "fountain",
            "binning": "projection",
            "position_mode": "center",
            "anchor_scope": "block",
            "anchor_count": 1,
            "token_block_size": 4,
            "block_anchor_threshold": 0.0,
            **overrides,
        }
        codec = PriorBinCodec(
            prior=tokenizer.token_prior,
            capacity_bits=args.bits_per_token,
            codebook=tokenizer.codebook,
            mode=str(config["binning"]),
        )
        generated = generate_payload_images(
            tokenizer=tokenizer,
            codec=codec,
            payload_bytes=args.payload_bytes,
            bits_per_token=args.bits_per_token,
            overhead=args.overhead,
            block_size=args.block_size,
            coding=str(config["coding"]),
            image_copies=args.image_copies,
            position_mode=str(config["position_mode"]),
            margin=2,
            anchor_count=int(config["anchor_count"]),
            anchor_scope=str(config["anchor_scope"]),
            token_block_size=int(config["token_block_size"]),
            seed=args.seed,
        )
        result = recover_from_images(
            tokenizer=tokenizer,
            codec=codec,
            generated=generated,
            attack=args.attack,
            bits_per_token=args.bits_per_token,
            block_size=args.block_size,
            geometry_search="anchors2d",
            crop_ratios=[0.94, 0.92, 0.90, 0.88, 0.86],
            crop_offsets=[-0.02, 0.0, 0.02],
            block_anchor_threshold=float(config["block_anchor_threshold"]),
            seed=args.seed,
        )
        rows.append(
            {
                "ablation": ablation,
                "variant": variant,
                "payload_bytes": args.payload_bytes,
                "image_copies": args.image_copies,
                "attack": args.attack,
                **config,
                "source_symbols": generated["source_symbols"],
                "encoded_symbols": generated["encoded_symbols"],
                "used_token_slots": generated["used_token_slots"],
                "payload_token_slots": generated["payload_token_slots"],
                "anchor_token_slots": generated["anchor_token_slots"],
                "mean_payload_leakage": generated["mean_payload_leakage"],
                "mean_anchor_leakage": generated["mean_anchor_leakage"],
                **result,
            }
        )

    write_csv(Path(args.out_csv), rows)
    write_json(Path(args.out_json), rows)
    print(json.dumps({"csv": args.out_csv, "json": args.out_json, "rows": len(rows)}, indent=2))
    return 0


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
