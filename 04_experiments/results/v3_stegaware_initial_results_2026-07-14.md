# V3 Steganalysis-Aware Initial Results - 2026-07-14

## Objective

Add two training terms to reduce obvious statistical detectability while keeping
the V3 packet and exact-recovery protocol unchanged:

1. differentiable residual-statistics regularization;
2. adversarial cover/stego loss against a small residual-domain discriminator.

## Implemented Code

Added:

- `05_artifacts/code/etehgan/steg_losses.py`
- `ResidualStegoDiscriminator` in `05_artifacts/code/etehgan/models.py`
- `05_artifacts/code/etehgan/train_v3_stegaware.py`

The statistical loss matches differentiable first-order residual statistics
between cover and stego. The adversarial loss trains a small discriminator to
separate cover/stego images while the encoder learns to make stego images look
like cover images to that discriminator.

## Trained Checkpoint

`05_artifacts/models/etehgan_v3_stegaware018_stat05_adv001_e3.pt`

Training setup:

- initialized from `etehgan_v3_residual018_img16_caltech20_coco20_e5.pt`;
- residual strength: 0.18;
- payload: 0.25 nominal bpp;
- V3 effective user payload: 0.185546875 bpp;
- lambda image: 16.0;
- lambda stat: 0.5;
- lambda adversarial: 0.01;
- discriminator steps: 1;
- epochs: 3;
- training images: 20 Caltech101 + 20 COCO.

Final training metrics:

- useful BER: 0.0034492493;
- stat loss: 0.0027228378;
- adversarial loss: 0.6846680939;
- discriminator accuracy: 0.5375.

## Clean-Channel Exact Recovery

| Checkpoint | Dataset | Images | Exact recovery | Mean raw BER | Mean PSNR | Mean global SSIM |
|---|---|---:|---:|---:|---:|---:|
| residual 0.2 baseline | Caltech101 offset 20 | 50 | 50/50 | 0.0007910156 | 36.8149 dB | 0.9984265 |
| residual 0.2 baseline | COCO val2017 offset 20 | 50 | 50/50 | 0.0035113525 | 36.1305 dB | 0.9979151 |
| residual 0.18 image-16 | Caltech101 offset 20 | 50 | 50/50 | 0.0007458496 | 38.3645 dB | 0.9988853 |
| residual 0.18 image-16 | COCO val2017 offset 20 | 50 | 50/50 | 0.0032171631 | 37.3305 dB | 0.9983871 |
| stegaware 0.18 stat0.5 adv0.01 | Caltech101 offset 20 | 50 | 50/50 | 0.0007705688 | 38.7663 dB | 0.9989831 |
| stegaware 0.18 stat0.5 adv0.01 | COCO val2017 offset 20 | 50 | 50/50 | 0.0030282593 | 37.5780 dB | 0.9984748 |

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
| residual 0.18 image-16 | COCO val2017 offset 20 | 0.8875 | 0.936250 |
| residual 0.18 image-16 | Caltech101 offset 20 | 0.9625 | 0.961250 |
| stegaware 0.18 stat0.5 adv0.01 | COCO val2017 offset 20 | 0.9250 | 0.918125 |
| stegaware 0.18 stat0.5 adv0.01 | Caltech101 offset 20 | 0.9500 | 0.963750 |

## Interpretation

The new losses produce the first useful improvement that preserves exact
recovery:

- Caltech50 exact recovery remains 50/50;
- COCO50 exact recovery remains 50/50;
- PSNR improves over residual 0.18;
- COCO simple detector AUC improves from 0.936250 to 0.918125.

The improvement is modest and not universal:

- Caltech AUC remains very high at 0.963750;
- the detector is lightweight, not a contemporary deep steganalyzer;
- no security or undetectability claim is justified.

Reviewer-safe conclusion:

> Statistical residual regularization and adversarial steganalysis-aware
> training improve the clean-channel quality/detectability trade-off on COCO
> while preserving exact V3 packet recovery, but the current model remains
> detectable and requires stronger steganalysis evaluation.

## Decision

Use `etehgan_v3_stegaware018_stat05_adv001_e3.pt` as the current best
quality-recovery-detectability checkpoint.

Do not claim steganographic security. The next step is to tune the adversarial
loss and evaluate against stronger detectors.
