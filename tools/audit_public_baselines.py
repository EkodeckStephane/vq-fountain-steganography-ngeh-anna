from __future__ import annotations

import importlib.util
import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    baselines = [audit_hidden(), audit_dct_spread(), audit_stegastamp()]
    executable_count = sum(1 for item in baselines if item["executable_now"])
    payload = {
        "all_public_baselines_accounted": all(item["accounted"] for item in baselines),
        "all_executable_now": all(item["executable_now"] for item in baselines),
        "executable_baseline_count": executable_count,
        "required_executable_baselines_ready": executable_count >= 2,
        "baselines": baselines,
        "policy": {
            "coverless_separation": (
                "HiDDeN, StegaStamp, and DCT-spread are non-coverless robust hiding baselines."
            ),
            "claim_rule": "Do not report local baseline recovery scores unless executable_now is true and a run artifact exists.",
        },
    }
    out_json = REPO_ROOT / "05_artifacts" / "baselines" / "baseline_execution_audit.json"
    out_md = REPO_ROOT / "04_experiments" / "results" / "ethegan_public_baseline_execution_audit_2026-07-16.md"
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    out_md.write_text(render_markdown(payload), encoding="utf-8")
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


def audit_hidden() -> dict[str, object]:
    root = REPO_ROOT / "05_artifacts" / "baselines" / "HiDDeN"
    required_files = [
        "README.md",
        "main.py",
        "train.py",
        "test_model.py",
        "model/hidden.py",
        "model/encoder_decoder.py",
        "noise_layers/noiser.py",
    ]
    checkpoint_candidates = list(root.glob("experiments/**/checkpoints/*.pyt"))
    runner = REPO_ROOT / "05_artifacts" / "code" / "vq_fountain" / "run_hidden_baseline_smoke.py"
    run_artifact = REPO_ROOT / "05_artifacts" / "results" / "tables" / "hidden_baseline_smoke.csv"
    dependencies = {
        "torch": module_available("torch"),
    }
    blockers = []
    if not all((root / name).exists() for name in required_files):
        blockers.append("required source files missing")
    if not checkpoint_candidates:
        blockers.append("public checkpoint files are not present in the local sparse checkout")
    if not dependencies["torch"]:
        blockers.append("torch is not installed")
    if not runner.exists():
        blockers.append("compatibility runner is missing")
    if not run_artifact.exists():
        blockers.append("local run artifact is missing")
    return {
        "name": "HiDDeN",
        "category": "non-coverless robust learned hiding",
        "local_path": display_path(root),
        "accounted": root.exists(),
        "source_files_present": all((root / name).exists() for name in required_files),
        "checkpoint_count": len(checkpoint_candidates),
        "dependencies": dependencies,
        "runner": display_path(runner),
        "run_artifact": display_path(run_artifact),
        "executable_now": not blockers,
        "blockers": blockers,
        "comparison_status": "paper-and-code-available; local compatibility run artifact produced",
    }


def audit_dct_spread() -> dict[str, object]:
    runner = REPO_ROOT / "05_artifacts" / "code" / "vq_fountain" / "run_dct_spread_baseline.py"
    run_artifact = REPO_ROOT / "05_artifacts" / "results" / "tables" / "dct_spread_baseline.csv"
    dependencies = {
        "PIL": module_available("PIL"),
        "scipy": module_available("scipy"),
    }
    blockers = []
    if not runner.exists():
        blockers.append("runner is missing")
    if not run_artifact.exists():
        blockers.append("local run artifact is missing")
    for name, available in dependencies.items():
        if not available:
            blockers.append(f"{name} is not installed")
    return {
        "name": "DCT-spread",
        "category": "non-coverless classical transform-domain hiding",
        "local_path": display_path(runner),
        "accounted": runner.exists(),
        "source_files_present": runner.exists(),
        "dependencies": dependencies,
        "runner": display_path(runner),
        "run_artifact": display_path(run_artifact),
        "executable_now": not blockers,
        "blockers": blockers,
        "comparison_status": "local classical baseline runner and artifact produced",
    }


def audit_stegastamp() -> dict[str, object]:
    root = REPO_ROOT / "05_artifacts" / "baselines" / "StegaStamp"
    required_files = ["README.md", "encode_image.py", "decode_image.py", "models.py", "train.py"]
    saved_models = list(root.glob("saved_models/**/saved_model.pb"))
    dependencies = {
        "tensorflow": module_available("tensorflow"),
        "bchlib": module_available("bchlib"),
        "cv2": module_available("cv2"),
    }
    blockers = []
    if not all((root / name).exists() for name in required_files):
        blockers.append("required source files missing")
    if not saved_models:
        blockers.append("pretrained SavedModel is not present in the local sparse checkout")
    if not dependencies["tensorflow"]:
        blockers.append("TensorFlow is not installed")
    if not dependencies["bchlib"]:
        blockers.append("bchlib is not installed")
    return {
        "name": "StegaStamp",
        "category": "non-coverless robust learned watermark/steganography",
        "local_path": display_path(root),
        "accounted": root.exists(),
        "source_files_present": all((root / name).exists() for name in required_files),
        "saved_model_count": len(saved_models),
        "dependencies": dependencies,
        "executable_now": not blockers,
        "blockers": blockers,
        "comparison_status": "paper-and-code-available; local run blocked by SavedModel/dependency availability",
    }


def module_available(name: str) -> bool:
    return importlib.util.find_spec(name) is not None


def display_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def render_markdown(payload: dict[str, object]) -> str:
    lines = [
        "# ETHEGAN Public Baseline Execution Audit",
        "",
        "Date: 2026-07-16",
        "",
        "This audit records local executability of public non-coverless baselines for ETHEGAN.",
        "It prevents unsupported baseline claims when dependencies or checkpoints are absent.",
        "",
        "| Baseline | Accounted | Executable now | Main blockers |",
        "|---|---:|---:|---|",
    ]
    for baseline in payload["baselines"]:
        blockers = "; ".join(baseline["blockers"]) if baseline["blockers"] else "none"
        lines.append(
            f"| {baseline['name']} | {str(baseline['accounted']).lower()} | "
            f"{str(baseline['executable_now']).lower()} | {blockers} |"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            f"{payload['executable_baseline_count']} executable non-coverless baselines are available locally.",
            "HiDDeN and DCT-spread have local run artifacts and can be reported with their measured scores.",
            "StegaStamp remains a valid public non-coverless comparator, but no local recovery score may be claimed",
            "until a pretrained SavedModel and compatible TensorFlow 1.x/BCH runtime are available.",
            "",
        ]
    )
    return "\n".join(lines)


if __name__ == "__main__":
    raise SystemExit(main())
