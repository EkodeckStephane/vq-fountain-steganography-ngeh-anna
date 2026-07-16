# V3 Pivot Initial Results - 2026-07-14

## Purpose

The pivot tests whether the project has a stronger path as reliability-aware
auxiliary-channel-free neural image steganography, rather than as a generic
high-capacity GAN steganography paper.

The key question is no longer only raw BER:

> Can a receiver recover the exact payload from one stego image without
> WYSAWIS-style external location metadata?

## Implemented Artifact

Added:

- `05_artifacts/code/etehgan/packet_v3.py`
- `05_artifacts/code/etehgan/evaluate_v3_packet.py`
- `05_artifacts/code/etehgan/embed_payload_v3.py`
- `05_artifacts/code/etehgan/extract_payload_v3.py`

The V3 packet contains:

- magic/version header;
- payload length;
- CRC32;
- Reed-Solomon parity;
- deterministic byte interleaving;
- optional byte erasures from decoder-logit reliability.

## Checkpoint Used

`05_artifacts/models/etehgan_v2_residual02_025_caltech20_coco20_e3.pt`

This checkpoint remains preliminary. It was trained only on 40 images
(20 Caltech101 + 20 COCO val2017) for 3 epochs.

## End-to-End V3 Payload Test

Command family:

- embed: `embed_payload_v3.py`
- extract: `extract_payload_v3.py`

Result on `000000001503.jpg` with `short_readme_payload.txt`:

- payload bytes: 1181;
- requested nominal payload: 0.25 bpp;
- exact byte recovery: true;
- output: `05_artifacts/results/raw/v3_recovered_short_readme_payload.txt`.

## Clean-Channel Packet Recovery

All results below use:

- nominal payload requested: 0.25 bpp;
- nominal bpp used after byte alignment: 0.25;
- effective user payload after packet/ECC overhead: 0.185546875 bpp;
- payload bytes per image: 6080;
- Reed-Solomon: 64 parity bytes per 255-byte chunk;
- packet seed: 7.

| Evaluation set | Images | Hard exact recovery | Mean raw bit BER | Max raw bit BER | Mean PSNR | Mean global SSIM |
|---|---:|---:|---:|---:|---:|---:|
| Sample images | 2 | 2/2 | 0.0002822876 | 0.0003204346 | 37.5911 dB | 0.9983878 |
| Caltech101 offset 20 | 20 | 20/20 | 0.0008438110 | 0.0044860840 | 36.5892 dB | 0.9985487 |
| COCO val2017 offset 20 | 20 | 20/20 | 0.0024093628 | 0.0100402832 | 35.9664 dB | 0.9977730 |

## Lower Payload Sanity Checks on Sample Images

| Nominal payload | Effective user payload | Images | Exact recovery | Mean raw bit BER | Mean PSNR |
|---:|---:|---:|---:|---:|---:|
| 0.05 bpp | 0.0339965820 bpp | 2 | 2/2 | 0.0004578755 | 41.3228 dB |
| 0.10 bpp | 0.0689697266 bpp | 2 | 2/2 | 0.0007249695 | 40.0826 dB |
| 0.25 bpp | 0.1855468750 bpp | 2 | 2/2 | 0.0002822876 | 37.5911 dB |

## Attack Results on COCO Subset

Evaluation:

- COCO val2017 offset 20;
- 10 images;
- nominal payload: 0.25 bpp;
- effective user payload: 0.185546875 bpp.

| Attack | Hard exact recovery | Mean raw bit BER | Max raw bit BER |
|---|---:|---:|---:|
| clean | 10/10 | 0.0024520874 | 0.0068206787 |
| jpeg95 | 0/10 | 0.4380661011 | 0.4559631348 |
| jpeg90 | 0/10 | 0.4936553955 | 0.5024871826 |
| noise2 | 8/10 | 0.0093719482 | 0.0160522461 |
| blur1 | 0/10 | 0.3173400879 | 0.3416595459 |
| resize0.75 | 0/10 | 0.1922897339 | 0.2064819336 |

Erasures based on decoder-logit reliability with 8 erasures per RS chunk did
not improve the noise2 result on this subset.

## Reviewer-Safe Interpretation

Supported by current evidence:

> The V3 packet layer turns low raw BER into exact clean-channel payload
> recovery on small held-out Caltech101 and COCO subsets, without external
> WYSAWIS-style location metadata.

Not supported:

- robustness to JPEG;
- robustness to blur or resizing;
- steganographic security;
- Q1-ready generalization;
- superiority over contemporary neural steganography baselines;
- a demonstrated benefit from reliability-aware erasures.

## Consequence for the Article

The pivot is promising for a clean-channel, auxiliary-channel-free reliable
payload recovery contribution. It is not yet promising as a robust
steganography paper unless robust training or synchronization-resistant coding
is added.
