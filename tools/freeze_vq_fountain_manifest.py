from __future__ import annotations

import hashlib
import importlib.metadata
import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]

DEFAULT_GLOBS = [
    "paper_vq_fountain/references.bib",
    "paper_vq_fountain/highlights.txt",
    "paper_vq_fountain/figures/*.pdf",
    "paper_vq_fountain/Elsevier/README_JISA.md",
    "paper_vq_fountain/Elsevier/highlights.txt",
    "paper_vq_fountain/Elsevier/manifest.txt",
    "paper_vq_fountain/Elsevier/references.bib",
    "paper_vq_fountain/Elsevier/cas-dc.cls",
    "paper_vq_fountain/Elsevier/cas-common.sty",
    "paper_vq_fountain/Elsevier/cas-model2-names.bst",
    "paper_vq_fountain/Elsevier/figures/*.pdf",
    "paper_vq_fountain/Elsevier/thumbnails/*.jpeg",
    "05_artifacts/code/vq_fountain/**/*.py",
    "05_artifacts/code/vq_fountain/README.md",
    "05_artifacts/code/vq_fountain/requirements-real-model.txt",
    "05_artifacts/models/vqgan_f4_8192_diffusers_converted/**/*",
    "05_artifacts/results/tables/vq_fountain*.csv",
    "05_artifacts/results/raw/vq_fountain*.json",
    "05_artifacts/results/raw/vq_fountain*.png",
    "05_artifacts/results/tables/hidden_baseline_smoke.csv",
    "05_artifacts/results/raw/hidden_baseline_smoke.json",
    "05_artifacts/results/tables/dct_spread_baseline.csv",
    "05_artifacts/results/raw/dct_spread_baseline.json",
    "05_artifacts/baselines/baseline_execution_audit.json",
    "04_experiments/results/vq_fountain*.md",
    "01_references/public_baselines_vq_fountain.md",
    "01_references/primary/verified_references.md",
    "tools/audit_public_baselines.py",
    "tools/check_vq_fountain_*.py",
    "tools/convert_vqgan_f4_checkpoint.py",
    "tools/freeze_vq_fountain_manifest.py",
]

DEPENDENCIES = [
    "diffusers",
    "torch",
    "numpy",
    "pillow",
    "scikit-learn",
    "scipy",
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


def dependency_versions() -> dict[str, str]:
    versions: dict[str, str] = {}
    for name in DEPENDENCIES:
        try:
            versions[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            versions[name] = "<not installed>"
    return versions


def main() -> int:
    files = collect_files(DEFAULT_GLOBS)
    manifest = {
        "artifact": "VQ-Fountain manuscript package",
        "date": "2026-07-16",
        "root": str(REPO_ROOT),
        "file_count": len(files),
        "patterns": DEFAULT_GLOBS,
        "dependency_versions": dependency_versions(),
        "files": [
            {
                "path": display_path(path),
                "bytes": path.stat().st_size,
                "sha256": sha256_file(path),
            }
            for path in files
        ],
    }

    out_json = REPO_ROOT / "05_artifacts" / "results" / "raw" / "vq_fountain_reproducibility_manifest.json"
    out_md = REPO_ROOT / "04_experiments" / "results" / "vq_fountain_reproducibility_manifest_2026-07-16.md"
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    out_md.write_text(render_markdown(manifest), encoding="utf-8")
    print(
        json.dumps(
            {
                "out_json": display_path(out_json),
                "out_md": display_path(out_md),
                "file_count": len(files),
            },
            indent=2,
        )
    )
    return 0


def render_markdown(manifest: dict[str, object]) -> str:
    lines = [
        "# VQ-Fountain Reproducibility Manifest",
        "",
        f"Date: {manifest['date']}",
        "",
        f"Frozen files: {manifest['file_count']}",
        "",
        "## Dependency Versions",
        "",
        "| Package | Version |",
        "|---|---|",
    ]
    for name, version in manifest["dependency_versions"].items():
        lines.append(f"| `{name}` | `{version}` |")
    lines.extend(
        [
            "",
            "## Files",
            "",
            "| Path | Bytes | SHA256 |",
            "|---|---:|---|",
        ]
    )
    for item in manifest["files"]:
        lines.append(f"| `{item['path']}` | {item['bytes']} | `{item['sha256']}` |")
    lines.append("")
    return "\n".join(lines)


if __name__ == "__main__":
    raise SystemExit(main())
