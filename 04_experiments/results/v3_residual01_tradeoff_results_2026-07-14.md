# V3 Residual 0.1 Trade-Off Results - 2026-07-14

## Objective

Test whether reducing the residual embedding strength improves image fidelity
and lowers simple steganalysis detectability while preserving V3 exact payload
recovery.

## Variant

Checkpoint:

`05_artifacts/models/etehgan_v3_residual01_img30_caltech20_coco20_e5.pt`

Training command summary:

- initialized from `etehgan_v2_residual02_025_caltech20_coco20_e3.pt`;
- residual strength: 0.1;
- payload: 0.25 nominal bpp;
- effective V3 user payload: 0.185546875 bpp;
- lambda image: 30.0;
- learning rate: 5e-5;
- epochs: 5;
- training images: 20 Caltech101 + 20 COCO.

Final training useful BER:

- epoch 5: 0.0077362061.

## Clean-Channel Exact Recovery

| Checkpoint | Dataset | Images | Exact recovery | Mean raw BER | Mean PSNR | Mean global SSIM |
|---|---|---:|---:|---:|---:|---:|
| residual 0.2 baseline | Caltech101 offset 20 | 50 | 50/50 | 0.0007910156 | 36.8149 dB | 0.9984265 |
| residual 0.2 baseline | COCO val2017 offset 20 | 50 | 50/50 | 0.0035113525 | 36.1305 dB | 0.9979151 |
| residual 0.1 image-30 | Caltech101 offset 20 | 50 | 50/50 | 0.0022451782 | 40.8337 dB | 0.9993825 |
| residual 0.1 image-30 | COCO val2017 offset 20 | 50 | 41/50 | 0.0085617065 | 39.8127 dB | 0.9991134 |

## Simple Steganalysis Sanity Check

Detector:

- logistic regression;
- 86 residual and LSB summary features;
- image-group split;
- 80 images per dataset, 40 train and 40 test.

| Checkpoint | Dataset | Test accuracy | Test AUC |
|---|---|---:|---:|
| residual 0.2 baseline | COCO val2017 offset 20 | 0.9000 | 0.930625 |
| residual 0.2 baseline | Caltech101 offset 20 | 0.9250 | 0.965625 |
| residual 0.1 image-30 | COCO val2017 offset 20 | 0.7750 | 0.842500 |
| residual 0.1 image-30 | Caltech101 offset 20 | 0.8875 | 0.933750 |

## Interpretation

The residual 0.1 variant improves visual fidelity by roughly 3.7-4.0 dB PSNR
and reduces simple detector AUC, especially on COCO.

However, it damages COCO exact recovery at the current training budget:

- baseline residual 0.2: 50/50 exact COCO recovery;
- residual 0.1 image-30: 41/50 exact COCO recovery.

Reviewer-safe conclusion:

> Lower residual strength is a promising direction for reducing detectability,
> but the current residual 0.1 checkpoint is not an acceptable replacement for
> the residual 0.2 clean-channel reliability baseline.

## Decision

Do not use the residual 0.1 checkpoint as the main reported method yet.

Keep:

- residual 0.2 checkpoint as the current exact-recovery baseline;
- residual 0.1 checkpoint as evidence for the fidelity/detectability trade-off.

Next training target:

- residual strength between 0.12 and 0.15, or a curriculum that starts with
  residual 0.2 for recovery and anneals toward lower residual strength;
- preserve V3 exact recovery at 50/50 on COCO50 before claiming improvement;
- rerun simple steganalysis after exact recovery is restored.
