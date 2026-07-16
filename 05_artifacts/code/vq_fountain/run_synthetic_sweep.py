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

from vq_fountain.bitstream import PayloadDecodeError, pack_payload, unpack_payload
from vq_fountain.fountain import FountainDecodeError, decode_symbols, encode_symbols
from vq_fountain.synthetic_channel import SyntheticChannelConfig, transmit_symbols


def main() -> int:
    parser = argparse.ArgumentParser(description="Sweep synthetic VQ-Fountain channel conditions.")
    parser.add_argument("--payload-bytes", type=int, nargs="+", default=[128, 1024])
    parser.add_argument("--block-size", type=int, default=32)
    parser.add_argument("--overheads", type=float, nargs="+", default=[0.25, 0.5, 0.8, 1.2])
    parser.add_argument("--erasure-rates", type=float, nargs="+", default=[0.0, 0.1, 0.2, 0.3, 0.4, 0.5])
    parser.add_argument("--trials", type=int, default=20)
    parser.add_argument("--seed", default="stage0")
    parser.add_argument(
        "--out-csv",
        default=str(REPO_ROOT / "05_artifacts" / "results" / "tables" / "vq_fountain_synthetic_stage0.csv"),
    )
    parser.add_argument(
        "--out-json",
        default=str(REPO_ROOT / "05_artifacts" / "results" / "raw" / "vq_fountain_synthetic_stage0.json"),
    )
    args = parser.parse_args()

    rows: list[dict[str, object]] = []
    raw: list[dict[str, object]] = []
    for payload_bytes in args.payload_bytes:
        for overhead in args.overheads:
            for erasure_rate in args.erasure_rates:
                summary = run_condition(
                    payload_bytes=payload_bytes,
                    block_size=args.block_size,
                    overhead=overhead,
                    erasure_rate=erasure_rate,
                    trials=args.trials,
                    seed=args.seed,
                )
                rows.append(summary["row"])
                raw.extend(summary["trials"])

    write_csv(Path(args.out_csv), rows)
    write_json(Path(args.out_json), raw)
    print(json.dumps({"csv": args.out_csv, "json": args.out_json, "rows": len(rows), "trials": len(raw)}, indent=2))
    return 0


def run_condition(
    payload_bytes: int,
    block_size: int,
    overhead: float,
    erasure_rate: float,
    trials: int,
    seed: int | str,
) -> dict[str, object]:
    successes = 0
    delivered_total = 0
    encoded_symbols = 0
    source_symbols = 0
    trial_rows: list[dict[str, object]] = []

    for trial in range(trials):
        payload = deterministic_payload(payload_bytes, seed=seed, trial=trial)
        packet = pack_payload(payload)
        trial_seed = f"{seed}:{payload_bytes}:{overhead}:{erasure_rate}:{trial}"
        symbols = encode_symbols(packet, block_size=block_size, overhead=overhead, seed=trial_seed)
        delivered = transmit_symbols(
            symbols,
            SyntheticChannelConfig(symbol_erasure_rate=erasure_rate, bit_flip_rate=0.0, seed=trial_seed),
        )

        exact = False
        failure = ""
        try:
            recovered = unpack_payload(decode_symbols(delivered))
            exact = recovered == payload
        except (FountainDecodeError, PayloadDecodeError) as exc:
            failure = str(exc)

        successes += int(exact)
        delivered_total += len(delivered)
        encoded_symbols = len(symbols)
        source_symbols = symbols[0].source_count
        trial_rows.append(
            {
                "payload_bytes": payload_bytes,
                "block_size": block_size,
                "overhead": overhead,
                "erasure_rate": erasure_rate,
                "trial": trial,
                "source_symbols": source_symbols,
                "encoded_symbols": encoded_symbols,
                "delivered_symbols": len(delivered),
                "exact_recovery": exact,
                "failure": failure,
            }
        )

    row = {
        "payload_bytes": payload_bytes,
        "block_size": block_size,
        "overhead": overhead,
        "erasure_rate": erasure_rate,
        "trials": trials,
        "source_symbols": source_symbols,
        "encoded_symbols": encoded_symbols,
        "mean_delivered_symbols": round(delivered_total / trials, 3),
        "exact_recovery_rate": round(successes / trials, 3),
    }
    return {"row": row, "trials": trial_rows}


def deterministic_payload(size: int, seed: int | str, trial: int) -> bytes:
    rng = random.Random(f"{seed}:{trial}:{size}")
    return bytes(rng.randrange(0, 256) for _ in range(size))


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(rows, handle, indent=2, sort_keys=True)


if __name__ == "__main__":
    raise SystemExit(main())
