from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]

DEFAULT_GLOBS = [
    "paper/main.tex",
    "paper/references.bib",
    "paper/highlights.txt",
    "05_artifacts/code/etehgan/*.py",
    "05_artifacts/code/etehgan/README.md",
    "05_artifacts/models/etehgan_v3_stegaware018_stat05_adv001_e3.pt",
    "05_artifacts/models/ethegan_attackaware_005_small_e2.pt",
    "05_artifacts/results/tables/ethegan_*.csv",
    "05_artifacts/results/tables/equal_bpp_*.csv",
    "05_artifacts/results/tables/v3_*.csv",
    "05_artifacts/results/tables/adaptive_ecc_*.csv",
    "05_artifacts/results/tables/spam_steganalysis_*.csv",
    "05_artifacts/results/raw/ethegan_*.json",
    "05_artifacts/results/raw/equal_bpp_*.json",
    "05_artifacts/results/raw/aead_self_test.json",
    "05_artifacts/results/raw/v3_*.json",
    "05_artifacts/results/raw/adaptive_ecc_*.json",
    "05_artifacts/results/raw/spam_steganalysis_*.json",
    "05_artifacts/data/security_gate/**/*",
    "05_artifacts/baselines/baseline_execution_audit.json",
    "tools/audit_*.py",
    "tools/run_*.py",
    "tools/freeze_reproducibility_manifest.py",
    "07_review_readiness/*.md",
    "04_experiments/results/*ethegan*.md",
    "04_experiments/results/*v3*.md",
    "04_experiments/results/confidentiality_support_audit_*.md",
    "04_experiments/results/equal_bpp_*.md",
    "04_experiments/results/limit_mechanism_execution_*.md",
]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def display_path(path: Path) -> str:
    return str(path.resolve().relative_to(REPO_ROOT))


def collect_files(patterns: list[str]) -> list[Path]:
    files: set[Path] = set()
    for pattern in patterns:
        for path in REPO_ROOT.glob(pattern):
            if path.is_file():
                files.add(path.resolve())
    return sorted(files, key=lambda item: display_path(item))


def main() -> int:
    parser = argparse.ArgumentParser(description="Freeze a SHA256 manifest for the ETHEGAN artifact.")
    parser.add_argument("--out-json", default="05_artifacts/results/raw/ethegan_reproducibility_manifest.json")
    parser.add_argument("--out-md", default="04_experiments/results/ethegan_reproducibility_manifest_2026-07-16.md")
    parser.add_argument("--extra-glob", action="append", default=[])
    args = parser.parse_args()

    patterns = DEFAULT_GLOBS + list(args.extra_glob)
    files = collect_files(patterns)
    manifest = {
        "artifact": "ETHEGAN NGEH ANNA manuscript package",
        "date": "2026-07-16",
        "root": str(REPO_ROOT),
        "file_count": len(files),
        "patterns": patterns,
        "files": [
            {
                "path": display_path(path),
                "bytes": path.stat().st_size,
                "sha256": sha256_file(path),
            }
            for path in files
        ],
    }

    out_json = REPO_ROOT / args.out_json
    out_md = REPO_ROOT / args.out_md
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    out_md.write_text(render_markdown(manifest), encoding="utf-8")
    print(json.dumps({"out_json": display_path(out_json), "out_md": display_path(out_md), "file_count": len(files)}, indent=2))
    return 0


def render_markdown(manifest: dict[str, object]) -> str:
    lines = [
        "# ETHEGAN Reproducibility Manifest",
        "",
        f"Date: {manifest['date']}",
        "",
        f"Frozen files: {manifest['file_count']}",
        "",
        "This manifest records SHA256 hashes for the manuscript source, ETHEGAN code,",
        "selected checkpoints, result tables, raw result JSON files, baseline audits,",
        "and review-readiness documents available inside this local artifact.",
        "",
        "It is not a public archive DOI. It is a local integrity lock that makes later",
        "changes detectable before repository or Zenodo/OSF release.",
        "",
        "| Path | Bytes | SHA256 |",
        "|---|---:|---|",
    ]
    for item in manifest["files"]:
        lines.append(f"| `{item['path']}` | {item['bytes']} | `{item['sha256']}` |")
    lines.append("")
    return "\n".join(lines)


if __name__ == "__main__":
    raise SystemExit(main())
