# V3 Scaled Clean-Channel and Security Sanity Results - 2026-07-14

## Purpose

This file extends the initial V3 pivot test from 20-image subsets to 50-image
clean-channel subsets and adds a lightweight steganalysis sanity check.

The results should be treated as preliminary evidence, not as final Q1 evidence.
The checkpoint was trained on only 40 images and strong steganalysis baselines
are still missing.

## Checkpoint

`05_artifacts/models/etehgan_v2_residual02_025_caltech20_coco20_e3.pt`

## Clean-Channel Payload Curve

All experiments use:

- Reed-Solomon: 64 parity bytes per 255-byte chunk;
- packet seed: 7;
- one random payload per image;
- held-out offset: 20;
- exact recovery checked by ECC and CRC validation.

| Dataset | Images | Nominal bpp | Effective user bpp | Payload bytes | Exact recovery | Mean raw bit BER | Max raw bit BER | Mean PSNR | Mean global SSIM |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Caltech101 offset 20 | 50 | 0.05 | 0.0339965820 | 1114 | 50/50 | 0.0011736874 | 0.0067155067 | 39.5597 dB | 0.9991897 |
| COCO val2017 offset 20 | 50 | 0.05 | 0.0339965820 | 1114 | 47/50 | 0.0058913309 | 0.0521978022 | 38.5133 dB | 0.9987974 |
| Caltech101 offset 20 | 50 | 0.10 | 0.0689697266 | 2260 | 50/50 | 0.0009554335 | 0.0049603175 | 38.7317 dB | 0.9990114 |
| COCO val2017 offset 20 | 50 | 0.10 | 0.0689697266 | 2260 | 47/50 | 0.0048878205 | 0.0343025031 | 37.8042 dB | 0.9985878 |
| Caltech101 offset 20 | 50 | 0.25 | 0.1855468750 | 6080 | 50/50 | 0.0007910156 | 0.0044860840 | 36.8149 dB | 0.9984265 |
| COCO val2017 offset 20 | 50 | 0.25 | 0.1855468750 | 6080 | 50/50 | 0.0035113525 | 0.0138549805 | 36.1305 dB | 0.9979151 |

## Interpretation of Payload Curve

The current checkpoint performs best at 0.25 bpp nominal, the rate used during
V2 training. The lower nominal rates do not monotonically improve reliability on
COCO; the same three COCO images failed at 0.05 and 0.10 bpp.

Reviewer-safe conclusion:

> Payload-rate adaptation cannot be claimed from these results alone. The
> current evidence supports a trained operating point at 0.25 bpp nominal, with
> effective user payload of 0.185546875 bpp, on small held-out subsets.

## Attack Stress Test

Dataset:

- COCO val2017 offset 20;
- 30 images;
- nominal bpp: 0.25;
- effective user bpp: 0.185546875.

| Attack | Exact recovery | Mean raw bit BER | Max raw bit BER |
|---|---:|---:|---:|
| clean | 30/30 | 0.0036005656 | 0.0138549805 |
| jpeg95 | 0/30 | 0.4382308960 | 0.4566955566 |
| noise2 | 23/30 | 0.0103378296 | 0.0250396729 |
| blur1 | 0/30 | 0.3269129435 | 0.4140777588 |
| resize0.75 | 0/30 | 0.1956034342 | 0.2213897705 |

Reviewer-safe conclusion:

> The current V3 system is not robust to JPEG, blur, or resizing. It has partial
> tolerance to mild additive noise under this limited test.

## Simple Steganalysis Sanity Check

Implemented:

`05_artifacts/code/etehgan/evaluate_v3_simple_steganalysis.py`

Detector:

- logistic regression;
- 86 handcrafted residual and LSB summary features;
- train/test split by image group, not by individual cover/stego samples.

This is not a strong modern steganalysis baseline. It is a sanity check showing
whether the generated stego images are easily separable by simple statistics.

| Dataset | Images | Train images | Test images | Test accuracy | Test AUC |
|---|---:|---:|---:|---:|---:|
| COCO val2017 offset 20 | 80 | 40 | 40 | 0.900 | 0.930625 |
| Caltech101 offset 20 | 80 | 40 | 40 | 0.925 | 0.965625 |

Reviewer-safe conclusion:

> The current V3 stego images are detectable by a simple residual/LSB classifier.
> The method cannot claim steganographic security or undetectability.

## Current Article Direction

Promising:

- clean-channel exact recovery without WYSAWIS-style location metadata;
- explicit separation between nominal bpp and effective user bpp;
- reproducible packet-level evaluation with effective-payload accounting.

Not yet promising:

- robustness to common image processing attacks;
- security against steganalysis;
- Q1-level comparison against strong baselines;
- final novelty proof without a completed related-work table.

## Immediate Technical Consequence

The next model-training iteration should not simply maximize BER recovery. It
must reduce detectable residual artifacts while preserving exact recovery.

Minimum next experiments:

1. train with lower residual strength or perceptual/residual regularization;
2. evaluate detectability after each training variant;
3. keep the packet/ECC layer fixed so that improvements are attributable to the
   neural embedding model;
4. add a stronger steganalysis baseline once dependencies or code are available.
