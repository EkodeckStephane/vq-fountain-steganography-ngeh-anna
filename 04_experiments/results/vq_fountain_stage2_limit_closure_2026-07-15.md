# VQ-Fountain Stage 2 Limit Closure

Date: 2026-07-15

## Purpose

Close the main limits left after the first real VQGAN payload proof:

1. payload capacity was too small;
2. calibration and test seeds were not formally separated;
3. feature-level realism/security had not been measured on real VQGAN payload
   images;
4. the real-generator result was restricted to 64x64 images.

## Changes

- Added grouped symbol packing to
  `05_artifacts/code/vq_fountain/run_real_vqgan_payload_probe.py`.
- Added `--symbols-per-image`, `--calibration-seed`, and `--test-seeds`.
- Added
  `05_artifacts/code/vq_fountain/run_real_vqgan_quality_security_probe.py`.
- Extended the final gate with Stage 2 high-capacity, multi-seed,
  feature-security, and 128px checks.

## Capacity Closure

Previous conservative Stage 2 setting:

- macro-cell: 4x4 latent tokens;
- capacity: 16 payload-value bits/image;
- demonstrated payload: 8 B.

New grouped setting:

- macro-cell: 2x2 latent tokens;
- macro-cells/image: 64;
- block size: 1 B;
- symbols/image: 8;
- effective coded payload-value budget: 64 bits/image.

Primary result:

| Payload | Attack | Images | Recovered symbols | CRC-valid symbols | Exact recovery |
|---:|---|---:|---:|---:|---|
| 32 B | clean | 22 | 176/176 | 172-176 | true |
| 32 B | crop090+jpeg85+drop25 | 22 | 120-136/176 | 53 | true |

Evidence:

- `05_artifacts/results/tables/vq_fountain_real_vqgan_payload_probe_payload32_grouped_overhead3.csv`
- `05_artifacts/results/tables/vq_fountain_real_vqgan_payload_probe_payload32_multiseed.csv`

## Calibration/Test Split Closure

A fixed calibration seed was used:

- `real-vqgan-calibration-v1`

Three independent payload/test seeds were then evaluated:

- `real-vqgan-test-a`
- `real-vqgan-test-b`
- `real-vqgan-test-c`

All six rows are exact:

- three clean rows;
- three `crop090+jpeg85+drop25` rows.

This closes the previous deterministic-single-seed limitation for the measured
32 B setting.

## Stage 2 Feature-Level Security/Quality Closure

Feature-level comparison was run on:

- 88 payload images;
- 88 reference images generated from the same calibrated VQGAN token family;
- payload: 32 B;
- grouped 2x2 macro-cell setting.

Results:

| Metric | Value |
|---|---:|
| Mean absolute feature delta | 0.04024327 |
| SciPy Frechet feature distance | 2.49162368 |
| Polynomial KID proxy | -0.00260754 |
| Logistic detector AUC | 0.49115505 |
| Logistic detector accuracy | 0.54838710 |

Evidence:

- `05_artifacts/results/tables/vq_fountain_real_vqgan_quality_security.csv`
- `05_artifacts/results/raw/vq_fountain_real_vqgan_quality_security.json`

Decision: the Stage 2 feature-level detector limitation is lifted for the
current proxy. This is still not a deep-steganalysis claim.

## Resolution Closure

The real VQGAN probe was rerun with:

- latent grid: 32x32;
- output image size: 128x128;
- macro-cell: 4x4 latent tokens;
- payload: 16 B;
- symbols/image: 8;
- overhead: 3.0.

Results:

| Attack | Images | Recovered symbols | CRC-valid symbols | Exact recovery |
|---|---:|---:|---:|---|
| clean | 14 | 112/112 | 108 | true |
| crop090+jpeg85+drop25 | 14 | 72/112 | 49 | true |

Evidence:

- `05_artifacts/results/tables/vq_fountain_real_vqgan_payload_probe_128px.csv`
- `05_artifacts/results/raw/vq_fountain_real_vqgan_payload_probe_128px.json`

Decision: the strict 64x64-only limitation is lifted as a feasibility result.

## Remaining Limits

- Full external SRM/SRNet-style steganalysis suites are still not run.
- Public generator coverage is limited to two VQModel checkpoints.
- StegaStamp is not locally scored because a pretrained SavedModel and
  compatible runtime are unavailable.
- The manuscript must remain explicit that the Stage 2 result is value-channel
  recovery, not token-ID preservation.

## Claim Boundary

Allowed:

- real VQGAN in-band recovery at 32 B under the measured grouped setting;
- multi-seed exact recovery for three test seeds;
- feature-level detector AUC near chance on the measured Stage 2 image set;
- local small-CNN detector AUC 0.51092612 and SPAM-style detector AUC
  0.56919875 on the measured Stage 2 image set;
- 128x128 feasibility.
- executable HiDDeN and DCT-spread non-coverless baseline results under their
  recorded local protocols.

Not allowed:

- final SOTA superiority;
- undetectability;
- robustness beyond the tested attacks, checkpoint, resolution, and payloads;
- full external steganalysis-suite resistance;
- local StegaStamp recovery scores.
