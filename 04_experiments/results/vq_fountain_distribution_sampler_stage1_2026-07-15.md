# VQ-Fountain Distribution-Aware Sampler Probe

Date: 2026-07-15

## Purpose

Replace the previous measured-stability oracle with a real token-sampling
round-trip:

1. sample token grids from the learned token prior;
2. encode payload values through balanced global codebook bins;
3. reconstruct images from tokens;
4. apply image transformations;
5. re-tokenize transformed images;
6. decode token-bin values and run fountain recovery.

This is still a learned patch-token baseline, not a VQGAN/AR generator.

## Code

- `05_artifacts/code/vq_fountain/vq_fountain/token_sampler.py`
- `05_artifacts/code/vq_fountain/run_distribution_sampler_probe.py`

## Main Probe

Command shape:

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
python 05_artifacts\code\vq_fountain\run_distribution_sampler_probe.py `
  --payload-bytes 8 16 32 `
  --bits-per-token 1 2 `
  --overheads 0.5 0.8 1.2 `
  --image-copies 2 4 8 12 `
  --attacks clean jpeg85 resize075 blur1 noise002 `
  --out-csv 05_artifacts\results\tables\vq_fountain_distribution_sampler_probe_k128.csv `
  --out-json 05_artifacts\results\raw\vq_fountain_distribution_sampler_probe_k128.json
```

Results over 360 conditions:

| Attack | Exact recovery | Mean value match | Mean token match |
|---|---:|---:|---:|
| clean | 72 / 72 | 1.000000 | 1.000000 |
| JPEG85 | 72 / 72 | 1.000000 | 0.999272 |
| resize0.75 | 72 / 72 | 1.000000 | 0.957924 |
| blur1 | 68 / 72 | 0.999861 | 0.881947 |
| noise0.02 | 72 / 72 | 1.000000 | 1.000000 |

## Stress Probe

Command shape:

```powershell
python 05_artifacts\code\vq_fountain\run_distribution_sampler_probe.py `
  --payload-bytes 64 128 `
  --bits-per-token 1 2 `
  --overheads 0.5 0.8 1.2 `
  --image-copies 2 4 8 12 16 `
  --attacks clean jpeg85 resize075 blur1 noise002 crop090 `
  --out-csv 05_artifacts\results\tables\vq_fountain_distribution_sampler_probe_k128_stress.csv `
  --out-json 05_artifacts\results\raw\vq_fountain_distribution_sampler_probe_k128_stress.json
```

Results over 360 conditions:

| Attack | Exact recovery | Mean value match | Mean token match |
|---|---:|---:|---:|
| clean | 48 / 60 | 1.000000 | 1.000000 |
| JPEG85 | 48 / 60 | 1.000000 | 1.000000 |
| resize0.75 | 48 / 60 | 1.000000 | 0.958331 |
| blur1 | 30 / 60 | 0.998471 | 0.879712 |
| noise0.02 | 48 / 60 | 1.000000 | 1.000000 |
| crop0.90 | 0 / 60 | 0.550701 | 0.077860 |

Useful thresholds:

| Payload | Bits/token | Attack set excluding crop | Minimum images |
|---:|---:|---|---:|
| 64 B | 1 | clean/JPEG85/resize0.75/blur1/noise0.02 | 4 |
| 64 B | 2 | clean/JPEG85/resize0.75/noise0.02 | 2 |
| 128 B | 1 | clean/JPEG85/resize0.75/blur1/noise0.02 | 8 |
| 128 B | 2 | clean/JPEG85/resize0.75/blur1/noise0.02 | 4 |

## Binning Ablation

Projection binning groups tokens by codebook luminance projection and balances
prior mass. Mass binning ignores geometry and balances prior mass directly.

Matched subset: payloads 64/128 B, overhead 0.5, image copies 4/8.

| Binning | JPEG85 | resize0.75 | blur1 | noise0.02 | crop0.90 |
|---|---:|---:|---:|---:|---:|
| projection | 7/8 | 7/8 | 5/8 | 7/8 | 0/8 |
| mass | 7/8 | 0/8 | 0/8 | 7/8 | 0/8 |

Projection binning is the better default because nearby visual tokens are more
likely to decode to the same payload value after resize and blur.

## Current Limits

Critical:

1. crop/geometric desynchronization still fails completely;
2. generated images are patch-codebook mosaics, not natural images;
3. no VQGAN/AR generator is connected yet;
4. no steganalysis or realism score is meaningful on these patch images.

Major:

1. symbol-level corruption is not yet protected by a symbol checksum;
2. binning is based on luminance projection, not learned generator logits;
3. capacity is still small: useful thresholds are 64-128 B across multiple
   generated images;
4. the current codebook has only 128 tokens and 16x16 positions per image.

## Next Technical Lock

The next useful step is synchronization:

- add block anchors or crop-invariant token scheduling;
- add symbol-level CRC/erasure handling;
- then connect a learned VQGAN/AR tokenizer or generator.

Update: symbol-level CRC/erasure handling has been implemented and evaluated in
`vq_fountain_symbol_crc_and_center_sync_2026-07-15.md`. It improves blur1, but
crop0.90 remains unsolved.
