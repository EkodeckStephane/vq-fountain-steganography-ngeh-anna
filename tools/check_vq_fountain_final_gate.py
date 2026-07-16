from __future__ import annotations

import csv
import json
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    checks: list[dict[str, object]] = []
    first_gate = subprocess.run(
        [sys.executable, str(REPO_ROOT / "tools" / "check_vq_fountain_readiness.py")],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    checks.append({"name": "first5_readiness_gate", "passed": first_gate.returncode == 0})

    ablation = REPO_ROOT / "05_artifacts" / "results" / "tables" / "vq_fountain_final_ablation_suite.csv"
    cost = REPO_ROOT / "05_artifacts" / "results" / "tables" / "vq_fountain_cost_search_crop_offset.csv"
    combined = REPO_ROOT / "05_artifacts" / "results" / "tables" / "vq_fountain_combined_attacks.csv"
    drop_cost = REPO_ROOT / "05_artifacts" / "results" / "tables" / "vq_fountain_combined_drop25_cost_search.csv"
    anchor_projection = REPO_ROOT / "05_artifacts" / "results" / "tables" / "vq_fountain_anchor_security_projection_256.csv"
    anchor_naive = REPO_ROOT / "05_artifacts" / "results" / "tables" / "vq_fountain_anchor_security_naive_256.csv"
    real_vqgan_conversion = (
        REPO_ROOT
        / "05_artifacts"
        / "models"
        / "vqgan_f4_8192_diffusers_converted"
        / "conversion_report.json"
    )
    real_vqgan_primary = REPO_ROOT / "05_artifacts" / "results" / "tables" / "vq_fountain_real_vqgan_payload_probe.csv"
    real_vqgan_hard = REPO_ROOT / "05_artifacts" / "results" / "tables" / "vq_fountain_real_vqgan_payload_probe_hard_attacks.csv"
    real_vqgan_drop = REPO_ROOT / "05_artifacts" / "results" / "tables" / "vq_fountain_real_vqgan_payload_probe_drop_attacks.csv"
    real_vqgan_payload8 = REPO_ROOT / "05_artifacts" / "results" / "tables" / "vq_fountain_real_vqgan_payload_probe_payload8.csv"
    real_vqgan_payload32_multiseed = (
        REPO_ROOT / "05_artifacts" / "results" / "tables" / "vq_fountain_real_vqgan_payload_probe_payload32_multiseed.csv"
    )
    real_vqgan_payload64_multiseed = (
        REPO_ROOT / "05_artifacts" / "results" / "tables" / "vq_fountain_real_vqgan_payload_probe_payload64_multiseed.csv"
    )
    real_vqgan_payload128_multiseed = (
        REPO_ROOT / "05_artifacts" / "results" / "tables" / "vq_fountain_real_vqgan_payload_probe_payload128_multiseed.csv"
    )
    real_vqgan_quality_security = REPO_ROOT / "05_artifacts" / "results" / "tables" / "vq_fountain_real_vqgan_quality_security.csv"
    real_vqgan_quality_security64 = (
        REPO_ROOT / "05_artifacts" / "results" / "tables" / "vq_fountain_real_vqgan_quality_security_payload64.csv"
    )
    real_vqgan_quality_security128 = (
        REPO_ROOT / "05_artifacts" / "results" / "tables" / "vq_fountain_real_vqgan_quality_security_payload128.csv"
    )
    real_vqgan_128px = REPO_ROOT / "05_artifacts" / "results" / "tables" / "vq_fountain_real_vqgan_payload_probe_128px.csv"
    real_vqgan_compvis = REPO_ROOT / "05_artifacts" / "results" / "tables" / "vq_fountain_real_vqgan_payload_probe_compvis_payload16.csv"
    real_vqgan_deep = REPO_ROOT / "05_artifacts" / "results" / "tables" / "vq_fountain_real_vqgan_deep_steganalysis.csv"
    real_vqgan_deep64 = (
        REPO_ROOT / "05_artifacts" / "results" / "tables" / "vq_fountain_real_vqgan_deep_steganalysis_payload64.csv"
    )
    real_vqgan_deep128 = (
        REPO_ROOT / "05_artifacts" / "results" / "tables" / "vq_fountain_real_vqgan_deep_steganalysis_payload128.csv"
    )
    real_vqgan_spam = REPO_ROOT / "05_artifacts" / "results" / "tables" / "vq_fountain_real_vqgan_spam_steganalysis.csv"
    real_vqgan_spam64 = (
        REPO_ROOT / "05_artifacts" / "results" / "tables" / "vq_fountain_real_vqgan_spam_steganalysis_payload64.csv"
    )
    real_vqgan_srm64 = (
        REPO_ROOT / "05_artifacts" / "results" / "tables" / "vq_fountain_real_vqgan_srm_steganalysis_payload64.csv"
    )
    real_vqgan_spam128_seed1 = (
        REPO_ROOT / "05_artifacts" / "results" / "tables" / "vq_fountain_real_vqgan_spam_steganalysis_payload128_seed1.csv"
    )
    hidden_baseline = REPO_ROOT / "05_artifacts" / "results" / "tables" / "hidden_baseline_smoke.csv"
    dct_baseline = REPO_ROOT / "05_artifacts" / "results" / "tables" / "dct_spread_baseline.csv"
    baseline_audit = REPO_ROOT / "05_artifacts" / "baselines" / "baseline_execution_audit.json"

    for name, path in [
        ("final_ablation_suite", ablation),
        ("cost_search", cost),
        ("combined_attacks", combined),
        ("combined_drop25_cost_search", drop_cost),
        ("anchor_security_projection", anchor_projection),
        ("anchor_security_naive", anchor_naive),
        ("real_vqgan_conversion", real_vqgan_conversion),
        ("real_vqgan_primary_payload", real_vqgan_primary),
        ("real_vqgan_hard_attacks", real_vqgan_hard),
        ("real_vqgan_drop_attacks", real_vqgan_drop),
        ("real_vqgan_payload8", real_vqgan_payload8),
        ("real_vqgan_payload32_multiseed", real_vqgan_payload32_multiseed),
        ("real_vqgan_payload64_multiseed", real_vqgan_payload64_multiseed),
        ("real_vqgan_payload128_multiseed", real_vqgan_payload128_multiseed),
        ("real_vqgan_quality_security", real_vqgan_quality_security),
        ("real_vqgan_quality_security64", real_vqgan_quality_security64),
        ("real_vqgan_quality_security128", real_vqgan_quality_security128),
        ("real_vqgan_128px", real_vqgan_128px),
        ("real_vqgan_compvis_payload16", real_vqgan_compvis),
        ("real_vqgan_deep_steganalysis", real_vqgan_deep),
        ("real_vqgan_deep_steganalysis64", real_vqgan_deep64),
        ("real_vqgan_deep_steganalysis128", real_vqgan_deep128),
        ("real_vqgan_spam_steganalysis", real_vqgan_spam),
        ("real_vqgan_spam_steganalysis64", real_vqgan_spam64),
        ("real_vqgan_spam_steganalysis128_seed1", real_vqgan_spam128_seed1),
        ("real_vqgan_srm_steganalysis64", real_vqgan_srm64),
        ("hidden_baseline_smoke", hidden_baseline),
        ("dct_spread_baseline", dct_baseline),
        ("baseline_execution_audit", baseline_audit),
    ]:
        checks.append(check_file(name, path))

    if ablation.exists():
        rows = read_rows(ablation)
        checks.extend(
            [
                check_ablation(rows, "coding", "fountain", True),
                check_ablation(rows, "coding", "repetition", False),
                check_ablation(rows, "sampling", "naive", False),
                check_ablation(rows, "schedule", "random", False),
            ]
        )

    if cost.exists():
        rows = read_rows(cost)
        checks.append(check_exact_under(rows, "cost_32B_overhead2_images8", payload=32, max_overhead=2.0, max_images=8))
        checks.append(check_exact_under(rows, "cost_64B_overhead2_5_images16", payload=64, max_overhead=2.5, max_images=16))

    if combined.exists():
        rows = read_rows(combined)
        checks.append(check_all_non_drop_combined(rows))

    if drop_cost.exists():
        rows = read_rows(drop_cost)
        checks.append(check_exact_under(rows, "drop25_32B_overhead4_images16", payload=32, max_overhead=4.0, max_images=16))
        checks.append(check_exact_under(rows, "drop25_64B_overhead4_images24", payload=64, max_overhead=4.0, max_images=24))

    if anchor_projection.exists() and anchor_naive.exists():
        projection = read_rows(anchor_projection)[0]
        naive = read_rows(anchor_naive)[0]
        checks.append(
            {
                "name": "projection_anchor_leakage_below_naive",
                "passed": float(projection["mean_anchor_leakage"]) <= float(naive["mean_anchor_leakage"]),
                "projection": projection["mean_anchor_leakage"],
                "naive": naive["mean_anchor_leakage"],
            }
        )
        checks.append(
            {
                "name": "projection_anchor_jsd_below_naive",
                "passed": float(projection["anchor_token_jsd_to_prior"]) <= float(naive["anchor_token_jsd_to_prior"]),
                "projection": projection["anchor_token_jsd_to_prior"],
                "naive": naive["anchor_token_jsd_to_prior"],
            }
        )

    if real_vqgan_conversion.exists():
        report = json.loads(real_vqgan_conversion.read_text(encoding="utf-8"))
        checks.append(
            {
                "name": "real_vqgan_conversion_complete",
                "passed": (
                    int(report["converted_tensor_count"]) == int(report["target_tensor_count"])
                    and not report["missing_target_keys"]
                    and not report["shape_mismatches"]
                    and not report["duplicate_targets"]
                ),
                "converted_tensor_count": report.get("converted_tensor_count"),
                "target_tensor_count": report.get("target_tensor_count"),
            }
        )

    if real_vqgan_primary.exists():
        rows = read_rows(real_vqgan_primary)
        checks.append(
            check_attacks_exact(
                rows,
                "real_vqgan_primary_4B_exact",
                payload=4,
                attacks=["clean", "jpeg85", "resize075"],
            )
        )

    if real_vqgan_hard.exists():
        rows = read_rows(real_vqgan_hard)
        checks.append(
            check_attacks_exact(
                rows,
                "real_vqgan_hard_4B_exact",
                payload=4,
                attacks=["blur1", "noise002", "crop090"],
            )
        )

    if real_vqgan_drop.exists():
        rows = read_rows(real_vqgan_drop)
        checks.append(
            check_attacks_exact(
                rows,
                "real_vqgan_drop_4B_exact",
                payload=4,
                attacks=["drop25", "crop090+jpeg85+drop25"],
            )
        )

    if real_vqgan_payload8.exists():
        rows = read_rows(real_vqgan_payload8)
        checks.append(
            check_attacks_exact(
                rows,
                "real_vqgan_payload8_exact",
                payload=8,
                attacks=["clean", "crop090+jpeg85+drop25"],
            )
        )

    if real_vqgan_payload32_multiseed.exists():
        rows = read_rows(real_vqgan_payload32_multiseed)
        checks.append(check_all_rows_exact(rows, "real_vqgan_payload32_multiseed_all_exact"))
        checks.append(
            {
                "name": "real_vqgan_payload32_has_three_test_seeds",
                "passed": len({row["payload_seed"] for row in rows}) >= 3,
                "seed_count": len({row["payload_seed"] for row in rows}),
            }
        )

    if real_vqgan_payload64_multiseed.exists():
        rows = read_rows(real_vqgan_payload64_multiseed)
        checks.append(check_all_rows_exact(rows, "real_vqgan_payload64_multiseed_all_exact"))
        checks.append(
            {
                "name": "real_vqgan_payload64_has_three_test_seeds",
                "passed": len({row["payload_seed"] for row in rows}) >= 3,
                "seed_count": len({row["payload_seed"] for row in rows}),
            }
        )
        checks.append(
            {
                "name": "real_vqgan_payload64_has_clean_and_hard_attacks",
                "passed": {"clean", "crop090+jpeg85+drop25"}.issubset({row["attack"] for row in rows}),
                "attacks": sorted({row["attack"] for row in rows}),
            }
        )

    if real_vqgan_payload128_multiseed.exists():
        rows = read_rows(real_vqgan_payload128_multiseed)
        checks.append(check_all_rows_exact(rows, "real_vqgan_payload128_multiseed_all_exact"))
        checks.append(
            {
                "name": "real_vqgan_payload128_has_three_test_seeds",
                "passed": len({row["payload_seed"] for row in rows}) >= 3,
                "seed_count": len({row["payload_seed"] for row in rows}),
            }
        )
        checks.append(
            {
                "name": "real_vqgan_payload128_has_clean_and_hard_attacks",
                "passed": {"clean", "crop090+jpeg85+drop25"}.issubset({row["attack"] for row in rows}),
                "attacks": sorted({row["attack"] for row in rows}),
            }
        )

    if real_vqgan_quality_security.exists():
        row = read_rows(real_vqgan_quality_security)[0]
        auc = float(row["sklearn_detector_auc"])
        checks.append(
            {
                "name": "real_vqgan_feature_detector_near_chance",
                "passed": 0.4 <= auc <= 0.6,
                "sklearn_detector_auc": row["sklearn_detector_auc"],
                "sklearn_detector_accuracy": row["sklearn_detector_accuracy"],
            }
        )

    if real_vqgan_quality_security64.exists():
        row = read_rows(real_vqgan_quality_security64)[0]
        auc = float(row["sklearn_detector_auc"])
        checks.append(
            {
                "name": "real_vqgan_feature_detector64_near_chance",
                "passed": 0.4 <= auc <= 0.6,
                "sklearn_detector_auc": row["sklearn_detector_auc"],
                "sklearn_detector_accuracy": row["sklearn_detector_accuracy"],
            }
        )

    if real_vqgan_quality_security128.exists():
        row = read_rows(real_vqgan_quality_security128)[0]
        auc = float(row["sklearn_detector_auc"])
        checks.append(
            {
                "name": "real_vqgan_feature_detector128_near_chance",
                "passed": 0.4 <= auc <= 0.6,
                "sklearn_detector_auc": row["sklearn_detector_auc"],
                "sklearn_detector_accuracy": row["sklearn_detector_accuracy"],
            }
        )

    if real_vqgan_128px.exists():
        rows = read_rows(real_vqgan_128px)
        checks.append(check_all_rows_exact(rows, "real_vqgan_128px_all_exact"))

    if real_vqgan_compvis.exists():
        rows = read_rows(real_vqgan_compvis)
        checks.append(check_all_rows_exact(rows, "real_vqgan_second_model_compvis_all_exact"))

    if real_vqgan_deep.exists():
        row = read_rows(real_vqgan_deep)[0]
        auc = float(row["cnn_detector_auc"])
        checks.append(
            {
                "name": "real_vqgan_cnn_detector_near_chance",
                "passed": 0.4 <= auc <= 0.6,
                "cnn_detector_auc": row["cnn_detector_auc"],
                "cnn_detector_accuracy": row["cnn_detector_accuracy"],
            }
        )

    if real_vqgan_deep64.exists():
        row = read_rows(real_vqgan_deep64)[0]
        auc = float(row["cnn_detector_auc"])
        checks.append(
            {
                "name": "real_vqgan_cnn_detector64_near_chance",
                "passed": 0.4 <= auc <= 0.6,
                "cnn_detector_auc": row["cnn_detector_auc"],
                "cnn_detector_accuracy": row["cnn_detector_accuracy"],
            }
        )

    if real_vqgan_deep128.exists():
        row = read_rows(real_vqgan_deep128)[0]
        auc = float(row["cnn_detector_auc"])
        checks.append(
            {
                "name": "real_vqgan_cnn_detector128_near_chance",
                "passed": 0.4 <= auc <= 0.6,
                "cnn_detector_auc": row["cnn_detector_auc"],
                "cnn_detector_accuracy": row["cnn_detector_accuracy"],
            }
        )

    if real_vqgan_spam.exists():
        row = read_rows(real_vqgan_spam)[0]
        auc = float(row["spam_detector_auc"])
        checks.append(
            {
                "name": "real_vqgan_spam_detector_below_alert_threshold",
                "passed": 0.4 <= auc <= 0.6,
                "spam_detector_auc": row["spam_detector_auc"],
                "spam_detector_accuracy": row["spam_detector_accuracy"],
                "threshold": "0.4 <= AUC <= 0.6",
            }
        )

    if real_vqgan_spam64.exists():
        row = read_rows(real_vqgan_spam64)[0]
        auc = float(row["spam_detector_auc"])
        checks.append(
            {
                "name": "real_vqgan_spam_detector64_below_alert_threshold",
                "passed": 0.4 <= auc <= 0.6,
                "spam_detector_auc": row["spam_detector_auc"],
                "spam_detector_accuracy": row["spam_detector_accuracy"],
                "threshold": "0.4 <= AUC <= 0.6",
            }
        )

    if real_vqgan_srm64.exists():
        row = read_rows(real_vqgan_srm64)[0]
        auc = float(row["srm_detector_auc_mean"])
        checks.append(
            {
                "name": "real_vqgan_srm_detector64_below_alert_threshold",
                "passed": 0.4 <= auc <= 0.6,
                "srm_detector_auc_mean": row["srm_detector_auc_mean"],
                "srm_detector_auc_std": row["srm_detector_auc_std"],
                "srm_detector_accuracy_mean": row["srm_detector_accuracy_mean"],
                "threshold": "0.4 <= mean AUC <= 0.6",
            }
        )

    if real_vqgan_spam128_seed1.exists():
        row = read_rows(real_vqgan_spam128_seed1)[0]
        auc = float(row["spam_detector_auc"])
        checks.append(
            {
                "name": "real_vqgan_spam_detector128_single_seed_smoke",
                "passed": 0.35 <= auc <= 0.65,
                "spam_detector_auc": row["spam_detector_auc"],
                "spam_detector_accuracy": row["spam_detector_accuracy"],
                "payload_seed_count": row["payload_seed_count"],
                "threshold": "0.35 <= AUC <= 0.65 for single-seed smoke only",
            }
        )

    if hidden_baseline.exists():
        rows = read_rows(hidden_baseline)
        checks.append(check_hidden_baseline_rows(rows))

    if dct_baseline.exists():
        rows = read_rows(dct_baseline)
        checks.append(check_dct_baseline_expected_attacks(rows))

    if baseline_audit.exists():
        audit = json.loads(baseline_audit.read_text(encoding="utf-8"))
        checks.append(
            {
                "name": "public_baselines_accounted_and_required_executables_ready",
                "passed": bool(audit.get("all_public_baselines_accounted"))
                and bool(audit.get("required_executable_baselines_ready")),
                "all_public_baselines_accounted": bool(audit.get("all_public_baselines_accounted")),
                "required_executable_baselines_ready": bool(audit.get("required_executable_baselines_ready")),
                "executable_baseline_count": int(audit.get("executable_baseline_count", 0)),
            }
        )

    payload = {"all_passed": all(bool(item["passed"]) for item in checks), "checks": checks}
    out = REPO_ROOT / "05_artifacts" / "results" / "raw" / "vq_fountain_final_gate.json"
    alias_out = REPO_ROOT / "05_artifacts" / "results" / "raw" / "vq_fountain_verification_report.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    alias_out.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if payload["all_passed"] else 1


def check_file(name: str, path: Path) -> dict[str, object]:
    return {
        "name": name,
        "passed": path.exists() and path.stat().st_size > 0,
        "path": display_path(path),
        "size_bytes": path.stat().st_size if path.exists() else 0,
    }


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def check_ablation(rows: list[dict[str, str]], ablation: str, variant: str, expected_exact: bool) -> dict[str, object]:
    matches = [row for row in rows if row["ablation"] == ablation and row["variant"] == variant]
    passed = bool(matches) and (matches[0]["exact_recovery"] == str(expected_exact))
    return {
        "name": f"ablation_{ablation}_{variant}",
        "passed": passed,
        "expected_exact": expected_exact,
        "actual_exact": matches[0]["exact_recovery"] if matches else "<missing>",
    }


def check_exact_under(rows: list[dict[str, str]], name: str, payload: int, max_overhead: float, max_images: int) -> dict[str, object]:
    matches = [
        row
        for row in rows
        if int(row["payload_bytes"]) == payload
        and float(row["overhead"]) <= max_overhead
        and int(row["image_copies"]) <= max_images
        and row["exact_recovery"] == "True"
    ]
    return {
        "name": name,
        "passed": bool(matches),
        "matches": len(matches),
    }


def check_all_non_drop_combined(rows: list[dict[str, str]]) -> dict[str, object]:
    subset = [
        row
        for row in rows
        if "drop25" not in row["attack"]
        and float(row["overhead"]) == 2.5
        and row["exact_recovery"] != "True"
    ]
    return {
        "name": "combined_non_drop_attacks_overhead2_5_all_exact",
        "passed": not subset,
        "failures": len(subset),
    }


def check_attacks_exact(rows: list[dict[str, str]], name: str, payload: int, attacks: list[str]) -> dict[str, object]:
    missing = []
    failures = []
    for attack in attacks:
        matches = [row for row in rows if row["attack"] == attack and int(row["payload_bytes"]) == payload]
        if not matches:
            missing.append(attack)
            continue
        if matches[0]["exact_recovery"] != "True":
            failures.append(attack)
    return {
        "name": name,
        "passed": not missing and not failures,
        "payload_bytes": payload,
        "missing": missing,
        "failures": failures,
    }


def check_all_rows_exact(rows: list[dict[str, str]], name: str) -> dict[str, object]:
    failures = [
        {"attack": row.get("attack", ""), "payload_seed": row.get("payload_seed", ""), "payload_bytes": row.get("payload_bytes", "")}
        for row in rows
        if row.get("exact_recovery") != "True"
    ]
    return {
        "name": name,
        "passed": bool(rows) and not failures,
        "rows": len(rows),
        "failures": failures,
    }


def check_hidden_baseline_rows(rows: list[dict[str, str]]) -> dict[str, object]:
    bit_error_rates = [float(row["bit_error_rate"]) for row in rows]
    return {
        "name": "hidden_baseline_run_is_measured",
        "passed": bool(rows)
        and all(row["baseline"] == "HiDDeN" for row in rows)
        and all(int(row["message_bits"]) == 30 for row in rows)
        and all(0.0 <= value <= 1.0 for value in bit_error_rates),
        "rows": len(rows),
        "mean_bit_error_rate": sum(bit_error_rates) / len(bit_error_rates) if bit_error_rates else None,
    }


def check_dct_baseline_expected_attacks(rows: list[dict[str, str]]) -> dict[str, object]:
    expected_attacks = ["clean", "jpeg85", "resize075", "blur1"]
    missing = []
    failures = []
    for attack in expected_attacks:
        matches = [row for row in rows if row["attack"] == attack and int(row["message_bits"]) == 32]
        if not matches:
            missing.append(attack)
            continue
        if matches[0]["exact_recovery"] != "True":
            failures.append(attack)
    crop_rows = [row for row in rows if row["attack"] == "crop090" and int(row["message_bits"]) == 32]
    return {
        "name": "dct_spread_baseline_expected_attacks_exact",
        "passed": not missing and not failures and bool(crop_rows),
        "payload_bits": 32,
        "expected_exact_attacks": expected_attacks,
        "missing": missing,
        "failures": failures,
        "crop090_recorded": bool(crop_rows),
        "crop090_exact_recovery": crop_rows[0]["exact_recovery"] if crop_rows else "<missing>",
    }


def display_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


if __name__ == "__main__":
    raise SystemExit(main())
