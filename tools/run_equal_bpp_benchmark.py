from __future__ import annotations

import argparse
import csv
import json
import random
import sys
from pathlib import Path

import numpy as np
from PIL import Image


REPO_ROOT = Path(__file__).resolve().parents[1]
VQ_CODE = REPO_ROOT / "05_artifacts" / "code" / "vq_fountain"
ETHEGAN_CODE = REPO_ROOT / "05_artifacts" / "code" / "etehgan"
sys.path.insert(0, str(VQ_CODE))
sys.path.insert(0, str(ETHEGAN_CODE))

from evaluate_v2_random import IMAGE_EXTENSIONS
from evaluate_v3_simple_steganalysis import extract_features as extract_simple_features
from evaluate_v3_simple_steganalysis import train_logistic_regression
from evaluate_v3_spam_steganalysis import extract_spam_features
from run_dct_spread_baseline import decode_bits, deterministic_bits, embed_bits, psnr
from vq_fountain.image_attacks import apply_attack


def collect_images(roots: list[str], max_images: int) -> list[Path]:
    paths: list[Path] = []
    for root in roots:
        paths.extend(sorted(p for p in Path(root).rglob("*") if p.suffix.lower() in IMAGE_EXTENSIONS))
    return sorted(paths)[:max_images]


def auc_score(labels, scores):
    labels = np.asarray(labels).astype(int)
    scores = np.asarray(scores).astype(float)
    pos = scores[labels == 1]
    neg = scores[labels == 0]
    if len(pos) == 0 or len(neg) == 0:
        return float("nan")
    wins = 0.0
    for value in pos:
        wins += float(np.sum(value > neg))
        wins += 0.5 * float(np.sum(value == neg))
    return wins / float(len(pos) * len(neg))


def detector_metrics(pairs: list[tuple[np.ndarray, np.ndarray]], extractor, seed: int, epochs: int):
    features = []
    labels = []
    groups = []
    for idx, (cover, stego) in enumerate(pairs):
        features.append(extractor(cover))
        labels.append(0)
        groups.append(idx)
        features.append(extractor(stego))
        labels.append(1)
        groups.append(idx)
    x = np.vstack(features)
    y = np.asarray(labels, dtype=np.int64)
    groups = np.asarray(groups)
    unique_groups = list(range(len(pairs)))
    random.Random(seed).shuffle(unique_groups)
    train_count = max(1, min(len(unique_groups) - 1, int(round(len(unique_groups) * 0.5))))
    train_groups = set(unique_groups[:train_count])
    train_mask = np.asarray([g in train_groups for g in groups])
    test_mask = ~train_mask
    mean = x[train_mask].mean(axis=0, keepdims=True)
    std = x[train_mask].std(axis=0, keepdims=True)
    std[std < 1e-8] = 1.0
    metrics = train_logistic_regression(
        (x[train_mask] - mean) / std,
        y[train_mask],
        (x[test_mask] - mean) / std,
        y[test_mask],
        epochs=epochs,
        seed=seed,
    )
    metrics.pop("test_scores", None)
    return metrics


def run_dct_batch(paths: list[Path], attacks: list[str], seed: int, epochs: int):
    message_bits = 32
    repetition = 7
    strength = 28.0
    clean_pairs = []
    rows = []
    for image_index, path in enumerate(paths):
        image = Image.open(path).convert("RGB").resize((128, 128), Image.Resampling.BICUBIC)
        bits = deterministic_bits(message_bits, f"{seed}:{image_index}")
        encoded = embed_bits(image, bits, repetition=repetition, strength=strength, seed=f"{seed}:{image_index}")
        clean_pairs.append((np.asarray(image, dtype=np.uint8), np.asarray(encoded, dtype=np.uint8)))
        for attack in attacks:
            attacked = apply_attack(encoded, attack, seed=f"{seed}:{image_index}:{attack}")
            decoded = decode_bits(attacked, message_bits, repetition=repetition, seed=f"{seed}:{image_index}")
            errors = sum(int(left != right) for left, right in zip(bits, decoded))
            rows.append(
                {
                    "method": "DCT-spread",
                    "image": str(path),
                    "attack": attack,
                    "message_bits": message_bits,
                    "image_pixels": 128 * 128,
                    "effective_bpp": message_bits / float(128 * 128),
                    "exact_recovery": errors == 0,
                    "bit_error_rate": errors / float(message_bits),
                    "psnr_db": psnr(image, encoded),
                }
            )
    by_attack = {}
    for attack in attacks:
        subset = [row for row in rows if row["attack"] == attack]
        by_attack[attack] = {
            "n": len(subset),
            "exact_rate": float(np.mean([row["exact_recovery"] for row in subset])),
            "mean_ber": float(np.mean([row["bit_error_rate"] for row in subset])),
            "mean_psnr_db": float(np.mean([row["psnr_db"] for row in subset])),
        }
    return {
        "rows": rows,
        "summary": {
            "method": "DCT-spread",
            "images": len(paths),
            "message_bits": message_bits,
            "effective_bpp": message_bits / float(128 * 128),
            "attacks": by_attack,
            "simple_detector": detector_metrics(clean_pairs, extract_simple_features, seed, epochs),
            "spam_detector": detector_metrics(clean_pairs, extract_spam_features, seed, epochs),
        },
    }


def load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--image-root", nargs="+", required=True)
    parser.add_argument("--max-images", type=int, default=40)
    parser.add_argument("--seed", type=int, default=4501)
    parser.add_argument("--epochs", type=int, default=300)
    parser.add_argument("--ethegan-attacks-json", required=True)
    parser.add_argument("--ethegan-gate-json", required=True)
    parser.add_argument("--hidden-json", default="05_artifacts/results/raw/hidden_baseline_smoke.json")
    parser.add_argument("--out-csv", default="05_artifacts/results/tables/equal_bpp_benchmark.csv")
    parser.add_argument("--out-json", default="05_artifacts/results/raw/equal_bpp_benchmark.json")
    parser.add_argument("--out-md", default="04_experiments/results/equal_bpp_benchmark_2026-07-16.md")
    args = parser.parse_args()

    paths = collect_images(args.image_root, args.max_images)
    dct = run_dct_batch(paths, ["clean", "jpeg85", "resize075", "blur1", "crop090"], args.seed, args.epochs)
    ethegan_attacks = load_json(REPO_ROOT / args.ethegan_attacks_json)["summary"]
    ethegan_gate = load_json(REPO_ROOT / args.ethegan_gate_json)["summary"]
    hidden = load_json(REPO_ROOT / args.hidden_json)

    rows = []
    ethegan_clean = ethegan_attacks["summary_by_attack"]["clean"]
    rows.append(
        {
            "method": "ETHEGAN gated low-payload",
            "effective_bpp": ethegan_gate["effective_user_bpp"],
            "images": ethegan_gate["accepted_images"],
            "clean_exact_rate": ethegan_gate["exact_recovery_accepted_rate"],
            "mean_psnr_db": ethegan_gate["mean_psnr_accepted"],
            "simple_auc": ethegan_gate["simple_detector_on_accepted"]["test_auc"],
            "spam_auc": ethegan_gate["spam_detector_on_accepted"]["test_auc"],
            "jpeg_or_attack_exact": "0.0 under JPEG95/blur1/resize0.75 on ungated 40-image check",
            "scope": "clean-channel accepted images only",
        }
    )
    rows.append(
        {
            "method": "ETHEGAN ungated low-payload",
            "effective_bpp": ethegan_attacks["effective_user_bpp"],
            "images": ethegan_clean["n"],
            "clean_exact_rate": ethegan_clean["hard_exact_rate"],
            "mean_psnr_db": ethegan_clean["mean_psnr_db"],
            "simple_auc": "",
            "spam_auc": "",
            "jpeg_or_attack_exact": "0.0 under JPEG95/blur1/resize0.75",
            "scope": "clean-channel all images, no passive-security claim",
        }
    )
    rows.append(
        {
            "method": "DCT-spread",
            "effective_bpp": dct["summary"]["effective_bpp"],
            "images": dct["summary"]["images"],
            "clean_exact_rate": dct["summary"]["attacks"]["clean"]["exact_rate"],
            "mean_psnr_db": dct["summary"]["attacks"]["clean"]["mean_psnr_db"],
            "simple_auc": dct["summary"]["simple_detector"]["test_auc"],
            "spam_auc": dct["summary"]["spam_detector"]["test_auc"],
            "jpeg_or_attack_exact": (
                f"jpeg85={dct['summary']['attacks']['jpeg85']['exact_rate']}, "
                f"resize075={dct['summary']['attacks']['resize075']['exact_rate']}, "
                f"blur1={dct['summary']['attacks']['blur1']['exact_rate']}, "
                f"crop090={dct['summary']['attacks']['crop090']['exact_rate']}"
            ),
            "scope": "classical transform baseline",
        }
    )
    rows.append(
        {
            "method": "HiDDeN local public checkpoint",
            "effective_bpp": hidden["message_bits"] / float(128 * 128),
            "images": hidden["trials"],
            "clean_exact_rate": hidden["exact_trials"] / float(hidden["trials"]),
            "mean_psnr_db": "",
            "simple_auc": "",
            "spam_auc": "",
            "jpeg_or_attack_exact": "not rerun in this compatibility smoke",
            "scope": "local checkpoint compatibility smoke",
        }
    )

    payload = {
        "summary_rows": rows,
        "dct_details": dct["summary"],
        "ethegan_attacks": ethegan_attacks,
        "ethegan_gate": ethegan_gate,
        "hidden_summary": {
            "message_bits": hidden["message_bits"],
            "effective_bpp": hidden["message_bits"] / float(128 * 128),
            "exact_trials": hidden["exact_trials"],
            "trials": hidden["trials"],
            "mean_bit_error_rate": hidden["mean_bit_error_rate"],
        },
        "decision": (
            "ETHEGAN shows clean-channel superiority over the local HiDDeN compatibility run "
            "and higher clean PSNR than DCT-spread at matched effective bpp, but DCT-spread is "
            "superior under the tested active transformations. Do not claim universal SOTA superiority."
        ),
    }

    out_csv = REPO_ROOT / args.out_csv
    out_json = REPO_ROOT / args.out_json
    out_md = REPO_ROOT / args.out_md
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    with out_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    out_json.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    out_md.write_text(render_markdown(payload), encoding="utf-8")
    print(json.dumps({"out_csv": str(out_csv), "out_json": str(out_json), "out_md": str(out_md), "decision": payload["decision"]}, indent=2))
    return 0


def render_markdown(payload: dict[str, object]) -> str:
    lines = [
        "# Equal-Effective-BPP Benchmark",
        "",
        "Date: 2026-07-16",
        "",
        "| Method | Effective bpp | Images | Clean exact | PSNR | Simple AUC | SPAM AUC | Active-channel result | Scope |",
        "|---|---:|---:|---:|---:|---:|---:|---|---|",
    ]
    for row in payload["summary_rows"]:
        lines.append(
            f"| {row['method']} | {row['effective_bpp']} | {row['images']} | "
            f"{row['clean_exact_rate']} | {row['mean_psnr_db']} | {row['simple_auc']} | "
            f"{row['spam_auc']} | {row['jpeg_or_attack_exact']} | {row['scope']} |"
        )
    lines.extend(["", "## Decision", "", payload["decision"], ""])
    return "\n".join(lines)


if __name__ == "__main__":
    raise SystemExit(main())
