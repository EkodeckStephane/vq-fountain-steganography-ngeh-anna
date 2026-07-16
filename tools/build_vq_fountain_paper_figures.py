"""Build publication figures for the VQ-Fountain manuscript.

The script intentionally reads only frozen CSV/PNG artifacts and writes figures
under ``paper_vq_fountain/figures`` so the manuscript can be rebuilt without
rerunning expensive model evaluations.
"""

from __future__ import annotations

import csv
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
TABLES = ROOT / "05_artifacts" / "results" / "tables"
RAW = ROOT / "05_artifacts" / "results" / "raw"
OUT = ROOT / "paper_vq_fountain" / "figures"


def rows(name: str) -> list[dict[str, str]]:
    with (TABLES / name).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def as_float(value: str) -> float:
    return float(value)


def as_int(value: str) -> int:
    return int(float(value))


def save(fig: plt.Figure, name: str) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(OUT / name, bbox_inches="tight")
    plt.close(fig)


def style_axes(ax: plt.Axes) -> None:
    ax.grid(axis="y", color="#d7dce2", linewidth=0.8, alpha=0.8)
    ax.set_axisbelow(True)
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)


def recovery_margin() -> None:
    data = []
    for filename in [
        "vq_fountain_real_vqgan_payload_probe_payload64_multiseed.csv",
        "vq_fountain_real_vqgan_payload_probe_payload128_multiseed.csv",
    ]:
        for row in rows(filename):
            attack = row["attack"].replace("crop090+jpeg85+drop25", "hard")
            payload = row["payload_bytes"]
            label = f"{payload} B / {attack}"
            data.append(
                {
                    "label": label,
                    "crc": as_int(row["crc_valid_symbols"]),
                    "source": as_int(row["source_symbols"]),
                }
            )

    labels = []
    crc_values = []
    source_values = []
    for label in ["64 B / clean", "64 B / hard", "128 B / clean", "128 B / hard"]:
        subset = [d for d in data if d["label"] == label]
        labels.append(label)
        crc_values.append(min(d["crc"] for d in subset))
        source_values.append(max(d["source"] for d in subset))

    fig, ax = plt.subplots(figsize=(7.0, 4.0))
    x = range(len(labels))
    ax.bar([i - 0.18 for i in x], source_values, width=0.36, label="required source symbols", color="#596b7a")
    ax.bar([i + 0.18 for i in x], crc_values, width=0.36, label="min CRC-valid symbols", color="#2f8f83")
    ax.set_xticks(list(x), labels, rotation=18, ha="right")
    ax.set_ylabel("symbol count")
    ax.set_title("Exact recovery margin on the public VQGAN checkpoint")
    ax.legend(frameon=False)
    style_axes(ax)
    save(fig, "fig_recovery_margin.pdf")


def ablation_crc() -> None:
    selected = [
        ("fountain", "coding", "fountain"),
        ("repetition", "coding", "repetition"),
        ("projection", "sampling", "projection"),
        ("naive", "sampling", "naive"),
        ("block anchors", "anchors", "block_1_per_4x4"),
        ("global anchors", "anchors", "global_9"),
        ("center", "schedule", "center"),
        ("random", "schedule", "random"),
    ]
    table = rows("vq_fountain_final_ablation_suite.csv")
    values = []
    colors = []
    labels = []
    for label, ablation, variant in selected:
        row = next(r for r in table if r["ablation"] == ablation and r["variant"] == variant)
        labels.append(label)
        values.append(as_int(row["crc_valid_symbols"]))
        colors.append("#2f8f83" if row["exact_recovery"] == "True" else "#b65353")

    fig, ax = plt.subplots(figsize=(7.2, 4.0))
    ax.bar(range(len(labels)), values, color=colors)
    ax.axhline(76, color="#333333", linestyle="--", linewidth=1.0, label="64 B source-symbol target")
    ax.set_xticks(range(len(labels)), labels, rotation=25, ha="right")
    ax.set_ylabel("CRC-valid symbols")
    ax.set_title("Component ablations under offset crop")
    ax.legend(frameon=False)
    style_axes(ax)
    save(fig, "fig_ablation_crc.pdf")


def detector_auc() -> None:
    metrics = [
        ("Feature 64 B", "vq_fountain_real_vqgan_quality_security_payload64.csv", "sklearn_detector_auc"),
        ("CNN 64 B", "vq_fountain_real_vqgan_deep_steganalysis_payload64.csv", "cnn_detector_auc"),
        ("SPAM 64 B", "vq_fountain_real_vqgan_spam_steganalysis_payload64.csv", "spam_detector_auc"),
        ("SRM 64 B", "vq_fountain_real_vqgan_srm_steganalysis_payload64.csv", "srm_detector_auc_mean"),
        ("Feature 128 B", "vq_fountain_real_vqgan_quality_security_payload128.csv", "sklearn_detector_auc"),
        ("CNN 128 B", "vq_fountain_real_vqgan_deep_steganalysis_payload128.csv", "cnn_detector_auc"),
        ("SPAM 128 B smoke", "vq_fountain_real_vqgan_spam_steganalysis_payload128_seed1.csv", "spam_detector_auc"),
    ]
    labels = []
    values = []
    for label, filename, key in metrics:
        row = rows(filename)[0]
        labels.append(label)
        values.append(as_float(row[key]))

    fig, ax = plt.subplots(figsize=(7.4, 4.2))
    ax.bar(range(len(labels)), values, color="#647ca1")
    ax.axhline(0.5, color="#333333", linestyle="--", linewidth=1.0, label="chance AUC")
    ax.set_xticks(range(len(labels)), labels, rotation=25, ha="right")
    ax.set_ylim(0.30, 0.65)
    ax.set_ylabel("AUC")
    ax.set_title("Local passive-detector separability")
    ax.legend(frameon=False)
    style_axes(ax)
    save(fig, "fig_detector_auc.pdf")


def hard_channel_cost() -> None:
    table = rows("vq_fountain_combined_drop25_cost_search.csv")
    selected = [
        r
        for r in table
        if r["payload_bytes"] == "64" and r["attack"] == "crop090_r02_c-02+jpeg85+drop25"
    ]
    selected.sort(key=lambda r: (as_float(r["overhead"]), as_int(r["image_copies"])))

    labels = [f"{r['overhead']}x/{r['image_copies']} img" for r in selected]
    crc = [as_int(r["crc_valid_symbols"]) for r in selected]
    success = [r["exact_recovery"] == "True" for r in selected]
    colors = ["#2f8f83" if ok else "#b65353" for ok in success]

    fig, ax = plt.subplots(figsize=(7.4, 4.2))
    ax.bar(range(len(labels)), crc, color=colors)
    ax.axhline(76, color="#333333", linestyle="--", linewidth=1.0, label="64 B source-symbol target")
    ax.set_xticks(range(len(labels)), labels, rotation=25, ha="right")
    ax.set_ylabel("CRC-valid symbols")
    ax.set_title("Cost search under crop090+jpeg85+drop25")
    ax.legend(frameon=False)
    style_axes(ax)
    save(fig, "fig_hard_channel_cost.pdf")


def sample_montage() -> None:
    samples = [
        ("32 B", "vq_fountain_real_vqgan_payload_sample_payload32_multiseed_00_real-vqgan-test-a.png"),
        ("64 B", "vq_fountain_real_vqgan_payload_sample_payload64_multiseed_00_real-vqgan-64-a.png"),
        ("128 B", "vq_fountain_real_vqgan_payload_sample_payload128_multiseed_00_real-vqgan-128-a.png"),
        ("128 px", "vq_fountain_real_vqgan_payload_sample_128px.png"),
        ("CompVis", "vq_fountain_real_vqgan_payload_sample_compvis_payload16.png"),
    ]
    fig, axes = plt.subplots(1, len(samples), figsize=(8.4, 2.1))
    for ax, (label, filename) in zip(axes, samples):
        image = Image.open(RAW / filename).convert("RGB")
        ax.imshow(image)
        ax.set_title(label, fontsize=9)
        ax.axis("off")
    save(fig, "fig_generated_samples.pdf")


def attack_matrix() -> None:
    table = rows("vq_fountain_combined_attacks.csv")
    selected = [
        r
        for r in table
        if r["payload_bytes"] == "64"
        and r["overhead"] == "4.0"
        and r["image_copies"] == "24"
    ]
    order = [
        "jpeg85+blur1",
        "jpeg85+noise002",
        "crop090_r02_c-02+jpeg85",
        "crop090_r02_c-02+resize075",
        "crop090_r02_c-02+jpeg85+noise002",
        "drop25",
        "crop090_r02_c-02+jpeg85+drop25",
    ]
    selected_by_attack = {r["attack"]: r for r in selected}
    labels = [a.replace("crop090_r02_c-02", "crop090") for a in order]
    crc = [as_int(selected_by_attack[a]["crc_valid_symbols"]) for a in order]
    colors = ["#2f8f83" if selected_by_attack[a]["exact_recovery"] == "True" else "#b65353" for a in order]

    fig, ax = plt.subplots(figsize=(7.6, 4.2))
    ax.bar(range(len(labels)), crc, color=colors)
    ax.axhline(76, color="#333333", linestyle="--", linewidth=1.0, label="64 B source-symbol target")
    ax.set_xticks(range(len(labels)), labels, rotation=25, ha="right")
    ax.set_ylabel("CRC-valid symbols")
    ax.set_title("Attack-family recovery at 64 B, overhead 4.0, 24 images")
    ax.legend(frameon=False)
    style_axes(ax)
    save(fig, "fig_attack_family.pdf")


def main() -> None:
    plt.rcParams.update(
        {
            "font.size": 9,
            "axes.titlesize": 10,
            "axes.labelsize": 9,
            "legend.fontsize": 8,
            "figure.dpi": 160,
        }
    )
    recovery_margin()
    ablation_crc()
    detector_auc()
    hard_channel_cost()
    attack_matrix()
    sample_montage()
    print(f"Wrote figures to {OUT}")


if __name__ == "__main__":
    main()
