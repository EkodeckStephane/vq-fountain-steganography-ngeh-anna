# VQ-Fountain Stega Prototype

This package contains the model-independent core for VQ-Fountain Stega.

Current scope:

- payload packing with length and CRC32;
- deterministic XOR fountain coding with GF(2) decoding;
- synthetic symbol erasure/bit-flip channel;
- entropy/stability token scheduling helpers;
- unit tests that run without external dependencies.

The first implementation milestone is not image quality. It is reliable
accounting: every decoded payload must pass length and CRC checks, and
unsuccessful decodes must be retained in the tables.

## Run Tests

```powershell
python -m unittest discover 05_artifacts\code\vq_fountain\tests
```

## Synthetic Smoke Test

```powershell
python 05_artifacts\code\vq_fountain\run_synthetic_smoke.py --message "VQ-Fountain smoke test" --erasure-rate 0.2 --overhead 0.8
```

Expected result: `exact_recovery` should be `true` for moderate erasure rates
when enough redundancy is provided.

## Synthetic Sweep

```powershell
python 05_artifacts\code\vq_fountain\run_synthetic_sweep.py --trials 20
```

Outputs:

- `05_artifacts/results/tables/vq_fountain_synthetic_stage0.csv`
- `05_artifacts/results/raw/vq_fountain_synthetic_stage0.json`

## Token Stability Baseline

```powershell
python 05_artifacts\code\vq_fountain\measure_token_stability.py
```

The default tokenizer is `patch-vq`, a fixed patch quantizer that runs without
external model dependencies. It is a Stage 1 baseline for validating token
stability accounting, not the final learned VQ tokenizer.

## Learned Patch-VQ Codebook

```powershell
python 05_artifacts\code\vq_fountain\train_patch_vq_codebook.py --image-root <IMAGE_DIR> --max-images 200 --codebook-size 256
python 05_artifacts\code\vq_fountain\measure_token_stability.py --tokenizer learned-patch-vq --codebook 05_artifacts\models\learned_patch_vq_stage1.npz --image-root <IMAGE_DIR> --max-images 100
```

This is a learned local tokenizer baseline. It is stronger than `patch-vq`, but
still not a VQGAN or autoregressive image tokenizer.

Outputs:

- `05_artifacts/results/tables/vq_fountain_token_stability_stage1.csv`
- `05_artifacts/results/raw/vq_fountain_token_stability_stage1.json`

## Token Recovery Probe

```powershell
python 05_artifacts\code\vq_fountain\run_token_recovery_probe.py
```

This probe maps fountain symbols onto measured stable token positions. It is an
upper-bound token-space test for local scheduling and capacity accounting; it is
not yet a real generated-image steganography experiment.

Outputs:

- `05_artifacts/results/tables/vq_fountain_token_recovery_probe.csv`
- `05_artifacts/results/raw/vq_fountain_token_recovery_probe.json`

## Distribution-Aware Sampler Probe

```powershell
python 05_artifacts\code\vq_fountain\run_distribution_sampler_probe.py
```

This probe generates token grids from the learned token prior, embeds payload
values through balanced codebook bins, reconstructs images, applies attacks, and
re-tokenizes for extraction. It removes the measured-stability oracle, but it is
still a patch-token baseline rather than a full VQGAN/AR generator.

Outputs:

- `05_artifacts/results/tables/vq_fountain_distribution_sampler_probe.csv`
- `05_artifacts/results/raw/vq_fountain_distribution_sampler_probe.json`

Useful options:

- `--position-mode center --margin 2` restricts payload tokens to a central
  schedule. This is an experimental synchronization probe; it does not solve
  crop robustness by itself.
- `--geometry-search crop --crop-ratios ...` tests crop-ratio hypotheses at the
  receiver. It is a probe for geometric synchronization, not a final anchor
  estimator.
- `--geometry-search anchors --anchor-count 16` chooses the crop-ratio
  hypothesis from embedded anchor agreement instead of payload recovery.

## Real VQGAN Payload Probe

```powershell
python 05_artifacts\code\vq_fountain\run_real_vqgan_payload_probe.py
```

This probe uses a converted public VQGAN f4-8192 `diffusers.VQModel`, calibrates
stable token-value classes, generates VQGAN images from payload-bearing latent
macro-cells, and recovers the payload from received images. It is a conservative
Stage 2 real-generator proof, not yet a high-rate or steganalysis-complete
result.

The grouped Stage 2 setting uses `--macro-cell-size 2 --symbols-per-image 8`
with 1 B fountain symbols. This preserves 64 coded value bits per image while
keeping CRC granularity small enough for erasure recovery under combined
attacks.

Outputs:

- `05_artifacts/results/tables/vq_fountain_real_vqgan_payload_probe.csv`
- `05_artifacts/results/raw/vq_fountain_real_vqgan_payload_probe.json`

## Real VQGAN Quality/Security Probe

```powershell
python 05_artifacts\code\vq_fountain\run_real_vqgan_quality_security_probe.py
```

This probe compares payload-bearing VQGAN images with reference VQGAN images
from the same calibrated token family using feature distance, KID proxy, and a
logistic detector.

## Current Evidence Status

Completed local evidence includes:

1. Main public VQGAN f4-8192 payload recovery up to 128 B under clean and
   crop090+jpeg85+drop25 across three payload seeds.
2. A second public VQModel checkpoint, `CompVis/ldm-celebahq-256/vqvae`, at
   16 B under clean and crop090+jpeg85+drop25.
3. Feature-level, small-CNN, SPAM-style, and SRM-style local detector probes.
4. Executable HiDDeN and DCT-spread non-coverless baseline runs.
5. A verification report with 69/69 checks passed and a 226-file SHA256
   reproducibility manifest.

Deferred extensions are broader public-generator coverage, official external
SRNet-style suites, and local StegaStamp scoring if a compatible SavedModel and
runtime become available.
