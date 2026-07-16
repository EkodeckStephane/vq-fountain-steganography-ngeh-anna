from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser(description="Readiness gate for the first five VQ-Fountain milestones.")
    parser.add_argument("--baseline-dir", default=str(REPO_ROOT / "05_artifacts" / "baselines"))
    parser.add_argument(
        "--scale-results",
        default=str(REPO_ROOT / "05_artifacts" / "results" / "tables" / "vq_fountain_scale_quality_security_probe_1000x3.csv"),
    )
    parser.add_argument(
        "--anchors2d-results",
        default=str(REPO_ROOT / "05_artifacts" / "results" / "tables" / "vq_fountain_distribution_sampler_probe_k128_crop_anchors2d.csv"),
    )
    parser.add_argument(
        "--anchors2d-offset-results",
        default=str(REPO_ROOT / "05_artifacts" / "results" / "tables" / "vq_fountain_distribution_sampler_probe_k128_crop_anchors2d_offset.csv"),
    )
    parser.add_argument(
        "--real-generator-smoke",
        default=str(REPO_ROOT / "05_artifacts" / "results" / "raw" / "vq_fountain_real_diffusion_smoke.json"),
    )
    parser.add_argument(
        "--real-vqmodel-smoke",
        default=str(REPO_ROOT / "05_artifacts" / "results" / "raw" / "vq_fountain_real_vqmodel_smoke.json"),
    )
    parser.add_argument(
        "--external-dataset-manifest",
        default=str(REPO_ROOT / "05_artifacts" / "data" / "external_dataset_manifest.json"),
    )
    parser.add_argument(
        "--bossbase-stability",
        default=str(REPO_ROOT / "05_artifacts" / "results" / "tables" / "vq_fountain_token_stability_bossbase_1000.csv"),
    )
    parser.add_argument(
        "--localraw-stability",
        default=str(REPO_ROOT / "05_artifacts" / "results" / "tables" / "vq_fountain_token_stability_localraw_1000.csv"),
    )
    parser.add_argument(
        "--baseline-registry",
        default=str(REPO_ROOT / "01_references" / "public_baselines_vq_fountain.md"),
    )
    parser.add_argument(
        "--out-json",
        default=str(REPO_ROOT / "05_artifacts" / "results" / "raw" / "vq_fountain_readiness_gate_first5.json"),
    )
    args = parser.parse_args()

    checks = [
        check_imports(["torch", "diffusers", "transformers", "accelerate", "safetensors"], "real_model_dependencies"),
        check_file(Path(args.real_generator_smoke), "real_generator_smoke"),
        check_file(Path(args.real_vqmodel_smoke), "real_vqmodel_smoke"),
        check_file(Path(args.external_dataset_manifest), "external_dataset_manifest"),
        check_file(Path(args.bossbase_stability), "bossbase_1000_stability"),
        check_file(Path(args.localraw_stability), "localraw_1000_stability"),
        check_file(Path(args.baseline_registry), "public_baseline_registry"),
        check_path_has_files(Path(args.baseline_dir), "baseline_code"),
        check_file(Path(args.scale_results), "scale_1000x3_results"),
        check_file(Path(args.anchors2d_results), "anchors2d_geometry_results"),
        check_file(Path(args.anchors2d_offset_results), "anchors2d_offset_geometry_results"),
        check_scale_columns(Path(args.scale_results), "numpy_quality_security_metrics"),
        check_imports(["scipy", "sklearn"], "standard_fid_kid_and_detector_dependencies"),
    ]
    payload = {
        "all_passed": all(item["passed"] for item in checks),
        "checks": checks,
    }
    out_path = Path(args.out_json)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if payload["all_passed"] else 1


def check_imports(modules: list[str], name: str) -> dict[str, object]:
    missing = [module for module in modules if importlib.util.find_spec(module) is None]
    return {
        "name": name,
        "passed": not missing,
        "missing": missing,
    }


def check_path_has_files(path: Path, name: str) -> dict[str, object]:
    files = []
    if path.exists():
        files = [str(item.relative_to(REPO_ROOT)) for item in path.rglob("*") if item.is_file()]
    return {
        "name": name,
        "passed": bool(files),
        "path": display_path(path),
        "file_count": len(files),
    }


def check_file(path: Path, name: str) -> dict[str, object]:
    return {
        "name": name,
        "passed": path.exists() and path.stat().st_size > 0,
        "path": display_path(path),
        "size_bytes": path.stat().st_size if path.exists() else 0,
    }


def display_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def check_scale_columns(path: Path, name: str) -> dict[str, object]:
    required = {
        "feature_fid_numpy",
        "feature_fid_scipy",
        "feature_kid_polynomial",
        "proxy_detector_auc",
        "proxy_detector_accuracy",
        "sklearn_detector_auc",
        "sklearn_detector_accuracy",
        "token_jsd_stego_cover",
    }
    if not path.exists():
        return {
            "name": name,
            "passed": False,
            "missing_columns": sorted(required),
        }
    header = path.read_text(encoding="utf-8").splitlines()[0].split(",")
    missing = sorted(required - set(header))
    return {
        "name": name,
        "passed": not missing,
        "missing_columns": missing,
    }


if __name__ == "__main__":
    raise SystemExit(main())
