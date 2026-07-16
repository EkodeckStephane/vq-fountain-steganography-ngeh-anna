# V3 Residual 0.15 Iteration Results - 2026-07-14

## Objective

Try an intermediate residual strength between:

- residual 0.2: strong exact recovery but high detectability;
- residual 0.1: better fidelity/detectability but insufficient COCO recovery.

The gate was strict:

> A candidate can replace the residual 0.2 baseline only if it keeps 50/50 exact
> recovery on COCO50 at 0.25 nominal bpp with the same V3 packet.

## Candidate A: Residual 0.15, Image Weight 20

Checkpoint:

`05_artifacts/models/etehgan_v3_residual015_img20_caltech20_coco20_e5.pt`

Training:

- initialized from residual 0.2 baseline;
- residual strength: 0.15;
- lambda image: 20.0;
- learning rate: 5e-5;
- epochs: 5;
- final training useful BER: 0.0048530579.

### Exact Recovery

| Dataset | Images | Exact recovery | Mean raw BER | Mean PSNR | Mean global SSIM |
|---|---:|---:|---:|---:|---:|
| Caltech101 offset 20 | 50 | 50/50 | 0.0009884644 | 39.2491 dB | 0.9990990 |
| COCO val2017 offset 20 | 50 | 48/50 | 0.0045501709 | 38.1728 dB | 0.9986821 |

### Simple Steganalysis

| Dataset | Images | Test accuracy | Test AUC |
|---|---:|---:|---:|
| COCO val2017 offset 20 | 80 | 0.8250 | 0.888125 |
| Caltech101 offset 20 | 80 | 0.9500 | 0.947500 |

## Candidate B: Residual 0.15, Recovery Fine-Tune

Checkpoint:

`05_artifacts/models/etehgan_v3_residual015_img12_ft3.pt`

Training:

- initialized from Candidate A;
- residual strength: 0.15;
- lambda image: 12.0;
- learning rate: 3e-5;
- epochs: 3;
- final training useful BER: 0.0036781311.

### Exact Recovery

| Dataset | Images | Exact recovery | Mean raw BER | Mean PSNR | Mean global SSIM |
|---|---:|---:|---:|---:|---:|
| Caltech101 offset 20 | 50 | 50/50 | 0.0009301758 | 38.9726 dB | 0.9990471 |
| COCO val2017 offset 20 | 50 | 48/50 | 0.0040902710 | 37.9345 dB | 0.9986112 |

Reliability-aware erasures with 8 erasures per RS chunk did not improve COCO50:

- hard exact recovery: 48/50;
- erasure exact recovery: 48/50.

## Comparison to Current Main Baseline

| Checkpoint | COCO50 exact recovery | COCO PSNR | COCO simple detector AUC |
|---|---:|---:|---:|
| residual 0.2 baseline | 50/50 | 36.1305 dB | 0.930625 |
| residual 0.15 image-20 | 48/50 | 38.1728 dB | 0.888125 |
| residual 0.15 image-12 fine-tune | 48/50 | 37.9345 dB | not rerun because recovery gate failed |

## Decision

Residual 0.15 is not yet an acceptable replacement for the residual 0.2
baseline. It improves fidelity and lowers simple detectability, but it misses
the exact-recovery gate on COCO50.

Keep:

- residual 0.2 as the main clean-channel exact-recovery baseline;
- residual 0.15 as evidence that detectability can be reduced, but only at a
  reliability cost.

Next viable direction:

1. train a residual 0.16-0.18 variant rather than pushing 0.15 further;
2. or train with a curriculum: start from residual 0.2 exact recovery, then
   gradually anneal image penalty/residual strength while monitoring COCO exact
   recovery;
3. add a recovery gate during training rather than relying only on training BER.
