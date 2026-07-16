# V2 Training Progress - 2026-07-13

## Summary

The original checkpoint was not Q1-ready. A residual V2 training path was implemented and tested at 0.25 bpp.

## Best Current Clean-Channel Checkpoint

Checkpoint:

`05_artifacts/models/etehgan_v2_residual02_025_caltech20_coco20_e3.pt`

Training data:

- 20 Caltech101 images
- 20 COCO val2017 images
- payload: random useful bits
- payload rate: 0.25 bpp
- residual strength: 0.2
- epochs: 3

## Clean Evaluation

| Evaluation set | Images | Payload | Mean useful BER | Mean PSNR | Mean global SSIM |
|---|---:|---:|---:|---:|---:|
| Caltech101 offset 20 | 20 | 0.25 bpp | 0.0008201599 | 36.5812 dB | 0.9985458 |
| COCO val2017 offset 20 | 20 | 0.25 bpp | 0.0024406433 | 35.9593 dB | 0.9977689 |

## Robustness on COCO Val Subset

Checkpoint:

`05_artifacts/models/etehgan_v2_residual02_025_caltech20_coco20_e3.pt`

Evaluation:

- COCO val2017 offset 20
- 10 images
- 0.25 bpp

| Attack | Mean useful BER | Max useful BER |
|---|---:|---:|
| clean | 0.0023941040 | 0.0065917969 |
| jpeg95 | 0.4425094604 | 0.4640350342 |
| jpeg90 | 0.4980682373 | 0.5061798096 |
| jpeg80 | 0.5005477905 | 0.5054626465 |
| noise2 | 0.0091247559 | 0.0159149170 |
| blur1 | 0.3207839966 | 0.3427886963 |
| resize0.75 | 0.1931076050 | 0.2060546875 |

## Short Text Payload Test

Checkpoint:

`05_artifacts/models/etehgan_v2_residual02_025_zerotail_e105.pt`

Payload:

`05_artifacts/data/payloads/short_readme_payload.txt`

Result:

- exact recovery on `000000001503.jpg`: true
- exact recovery on `dog_0031.jpg`: false

## Scientific Interpretation

The V2 direction is viable for clean-channel low-payload embedding, but it is not yet robust and not yet ready for Q1 claims.

Allowed current claim:

> A residual neural embedding variant improves the clean-channel capacity-quality trade-off at 0.25 bpp on small local Caltech/COCO subsets.

Not allowed yet:

- robust steganography;
- JPEG-resistant extraction;
- high-capacity 2 bpp performance;
- generalization across large datasets;
- steganographic security.

## Next Technical Steps

1. Train on larger Caltech/COCO subsets.
2. Add explicit differentiable noise/blur/resize training.
3. Add a stronger ECC/interleaving layer for structured packets.
4. Evaluate at 0.5 bpp only after 0.25 bpp reaches lower clean BER.
5. Add real steganalysis detection experiments.

