# Smoke Test - dog_0031

Date: 2026-07-13

Artifact:

- cover: `05_artifacts/data/sample_images/dog_0031.jpg`
- payload: `05_artifacts/data/payloads/numbered_story.txt`
- stego: `05_artifacts/results/raw/stego_dog_0031.png`
- recovered payload: `05_artifacts/results/raw/recovered_dog_0031.txt`
- metrics JSON: `05_artifacts/results/raw/smoke_metrics_dog_0031.json`
- metrics CSV: `05_artifacts/results/tables/smoke_metrics_dog_0031.csv`

## Results

| Metric | Value |
|---|---:|
| Image size after preprocessing | 512 x 512 |
| Payload bytes | 57,310 |
| Payload bits | 458,480 |
| Nominal capacity | 2.0000 bpp |
| Effective user payload | 1.7490 bpp |
| Raw prefix BER before ECC | 0.0020790100 |
| Raw prefix bit errors before ECC | 1,090 / 524,288 |
| Exact recovered payload | false |
| Recovered bytes | 66 |
| PSNR | 12.7822 dB |
| Global SSIM | 0.3014 |

## Interpretation

The current prototype does not generalize reliably to this second provided image. The embed script's loopback verification flagged uncorrectable bit errors, and the recovered file is not the original payload.

## Consequence

This result strengthens the conclusion that the current checkpoint cannot support Q1 claims. The next technical step must be model recovery, retraining, or architectural redesign before manuscript claims about robustness or generalization are allowed.

