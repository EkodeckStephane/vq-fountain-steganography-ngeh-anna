# VQ-Fountain Stage 2 Real VQGAN Payload Probe

Date: 2026-07-15

## Objective

Test whether VQ-Fountain can carry an in-band payload through a public, non-dummy
VQGAN VQModel path, instead of stopping at learned patch-token simulations.

## Implementation

- Added `tools/convert_vqgan_f4_checkpoint.py`.
- Converted the old `fusing/vqgan-f4-8192` checkpoint into a modern
  `diffusers.VQModel` layout.
- Conversion result:
  - source tensors: 209;
  - target tensors: 205;
  - converted tensors: 205;
  - missing target tensors: 0;
  - dropped source tensors: 4 legacy `qkv` tensors superseded by explicit
    `q/k/v` tensors.
- Added `05_artifacts/code/vq_fountain/run_real_vqgan_payload_probe.py`.

The probe uses a calibrated token-value channel:

- latent grid: 16x16 for 64x64 images;
- macro-cell size: 4x4 latent tokens;
- capacity: 1 bit per macro-cell, 16 bits per generated image;
- fountain block size: 2 B;
- overhead: 2.0;
- clean-channel calibration: 256 candidate codebook tokens;
- stable pools at threshold 0.90:
  - value 0: 44 tokens;
  - value 1: 26 tokens.

The measured token identity match remains near zero. Recovery succeeds because
the receiver decodes calibrated value classes by macro-cell majority, not
because transmitted token IDs survive.

## Results

Primary 4 B payload, 24 generated images:

| Attack | Recovered symbols | CRC-valid symbols | Value match | Exact recovery |
|---|---:|---:|---:|---|
| clean | 24/24 | 24 | 1.000 | true |
| jpeg85 | 24/24 | 24 | 1.000 | true |
| resize075 | 24/24 | 24 | 1.000 | true |
| blur1 | 24/24 | 24 | 1.000 | true |
| noise002 | 24/24 | 24 | 1.000 | true |
| crop090 | 24/24 | 24 | 1.000 | true |
| drop25 | 18/24 | 18 | 1.000 | true |
| crop090+jpeg85+drop25 | 16/24 | 16 | 1.000 | true |

Payload scaling check, 8 B payload, 30 generated images:

| Attack | Recovered symbols | CRC-valid symbols | Dropped images | Value match | Exact recovery |
|---|---:|---:|---:|---:|---|
| clean | 30/30 | 30 | 0 | 1.000 | true |
| crop090+jpeg85+drop25 | 20/30 | 20 | 10 | 1.000 | true |

Evidence files:

- `05_artifacts/models/vqgan_f4_8192_diffusers_converted/conversion_report.json`
- `05_artifacts/results/tables/vq_fountain_real_vqgan_payload_probe.csv`
- `05_artifacts/results/tables/vq_fountain_real_vqgan_payload_probe_hard_attacks.csv`
- `05_artifacts/results/tables/vq_fountain_real_vqgan_payload_probe_drop_attacks.csv`
- `05_artifacts/results/tables/vq_fountain_real_vqgan_payload_probe_payload8.csv`
- `05_artifacts/results/raw/vq_fountain_real_vqgan_payload_probe.json`
- `05_artifacts/results/raw/vq_fountain_real_vqgan_payload_probe_hard_attacks.json`
- `05_artifacts/results/raw/vq_fountain_real_vqgan_payload_probe_drop_attacks.json`
- `05_artifacts/results/raw/vq_fountain_real_vqgan_payload_probe_payload8.json`

## Limits

- Capacity is intentionally conservative: 16 bits/image in this probe. This
  lifts the real-generator payload blocker, but it is not yet a competitive
  payload-rate result.
- The probe uses one public VQGAN checkpoint and 64x64 images. A paper result
  still needs more generators, resolutions, and seeds.
- Calibration and evaluation are deterministic but not yet separated into a
  formal train/calibration/test protocol.
- Visual quality and modern steganalysis have not yet been rerun on these real
  VQGAN payload images.
- The method should be described as calibrated value recovery through a VQGAN
  channel, not as token-ID preservation.

## Decision

The major Stage 2 blocker "payload does not pass through a real public
VQ/tokenizer path" is lifted for a conservative payload setting. Remaining work
is now capacity, breadth, security, and manuscript integration.
