# VQ-Fountain Real Model Smoke Tests

Date: 2026-07-15

## Purpose

Verify that the local environment can run public real-model components beyond
the lightweight learned patch-VQ baseline.

## Diffusion Generator

Model: `diffusers/tiny-stable-diffusion-torch`

Result:

- CPU generation succeeds.
- Output image: `05_artifacts/results/raw/vq_fountain_real_diffusion_smoke.png`
- Manifest: `05_artifacts/results/raw/vq_fountain_real_diffusion_smoke.json`

## VQ Encoder / Decoder

Model: `fusing/vqgan-dummy`

Result:

- `diffusers.VQModel` loads locally.
- Encode/decode round trip succeeds.
- Latent shape: `1 x 3 x 32 x 32`
- Output image: `05_artifacts/results/raw/vq_fountain_real_vqmodel_smoke.png`
- Manifest: `05_artifacts/results/raw/vq_fountain_real_vqmodel_smoke.json`

## Interpretation

The environment can now run both a public diffusion generator and a public VQ
encoder/decoder. This removes the previous local dependency/model availability
blocker for Stage 2 engineering.
