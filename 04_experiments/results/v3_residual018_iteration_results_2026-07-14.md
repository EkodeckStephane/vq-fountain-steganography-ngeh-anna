# V3 Residual 0.18 Iteration Results - 2026-07-14

## Objective

Test whether residual strength 0.18 can preserve the residual 0.2 exact-recovery
gate while improving image fidelity and lowering simple steganalysis
detectability.

Replacement gate:

> 50/50 exact recovery on both Caltech50 and COCO50 at 0.25 nominal bpp, using
> the unchanged V3 packet.

## Candidate

Checkpoint:

`05_artifacts/models/etehgan_v3_residual018_img16_caltech20_coco20_e5.pt`

Training:

- initialized from residual 0.2 baseline;
- residual strength: 0.18;
- lambda image: 16.0;
- learning rate: 5e-5;
- epochs: 5;
- training images: 20 Caltech101 + 20 COCO;
- final training useful BER: 0.0038936615.

## Clean-Channel Exact Recovery

| Checkpoint | Dataset | Images | Exact recovery | Mean raw BER | Mean PSNR | Mean global SSIM |
|---|---|---:|---:|---:|---:|---:|
| residual 0.2 baseline | Caltech101 offset 20 | 50 | 50/50 | 0.0007910156 | 36.8149 dB | 0.9984265 |
| residual 0.2 baseline | COCO val2017 offset 20 | 50 | 50/50 | 0.0035113525 | 36.1305 dB | 0.9979151 |
| residual 0.18 image-16 | Caltech101 offset 20 | 50 | 50/50 | 0.0007458496 | 38.3645 dB | 0.9988853 |
| residual 0.18 image-16 | COCO val2017 offset 20 | 50 | 50/50 | 0.0032171631 | 37.3305 dB | 0.9983871 |

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

## Interpretation

Residual 0.18 passes the exact-recovery gate and improves PSNR:

- Caltech: +1.55 dB over residual 0.2;
- COCO: +1.20 dB over residual 0.2.

However, it does not improve the simple steganalysis AUC in a reliable way:

- COCO AUC is slightly worse than the baseline;
- Caltech AUC is slightly lower than the baseline, but still very high.

Reviewer-safe conclusion:

> Residual 0.18 is a better visual-fidelity baseline than residual 0.2 while
> preserving exact recovery, but it does not solve detectability.

## Decision

Residual 0.18 can replace residual 0.2 only for the clean-channel
capacity-quality-recovery table. It cannot be claimed as a security improvement.

Next scientific direction:

1. stop searching residual strength alone as the main security fix;
2. add an explicit residual/statistical regularization term or adversarial
   steganalysis-aware loss;
3. keep residual 0.18 as the current best exact-recovery quality checkpoint.
