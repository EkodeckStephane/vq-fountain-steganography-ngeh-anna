# VQ-Fountain Anchor-Based Crop Synchronization

Date: 2026-07-15

## Purpose

Replace payload-driven crop-ratio selection with embedded synchronization
anchors.

Previous crop recovery used a brute-force crop-ratio search and selected the
best ratio using payload recovery quality. This was useful as a feasibility
probe, but too close to an oracle. The new probe reserves a small set of token
positions for a known anchor sequence. The receiver selects the crop-ratio
hypothesis that maximizes anchor agreement, then decodes the payload.

## Command Shape

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
python 05_artifacts\code\vq_fountain\run_distribution_sampler_probe.py `
  --payload-bytes 32 64 `
  --bits-per-token 1 `
  --block-size 1 `
  --overheads 4.0 `
  --image-copies 16 24 32 `
  --attacks crop090 `
  --position-mode center `
  --margin 2 `
  --geometry-search anchors `
  --anchor-count 16 `
  --crop-ratios 0.94 0.92 0.90 0.88 0.86 `
  --out-csv 05_artifacts\results\tables\vq_fountain_distribution_sampler_probe_k128_crop_anchors16.csv `
  --out-json 05_artifacts\results\raw\vq_fountain_distribution_sampler_probe_k128_crop_anchors16.json
```

## Anchor Count Ablation

All runs use crop0.90, center schedule, margin 2, block size 1, overhead 4.0,
and 1 bit/token.

| Anchors/image | Payload | Exact recovery | Minimum images | Mean anchor match |
|---:|---:|---:|---:|---:|
| 8 | 32 B | 2 / 3 | 16 | 0.878906 |
| 8 | 64 B | 2 / 3 | 24 | 0.875000 |
| 16 | 32 B | 3 / 3 | 16 | 0.856988 |
| 16 | 64 B | 2 / 3 | 24 | 0.847439 |
| 32 | 32 B | 3 / 3 | 16 | 0.836697 |
| 32 | 64 B | 2 / 3 | 24 | 0.859918 |

Representative 16-anchor results:

| Payload | Images | Selected ratio | Anchor match | CRC-valid symbols | Exact recovery |
|---:|---:|---:|---:|---:|---:|
| 32 B | 16 | 0.88 | 0.851562 | 48 | yes |
| 32 B | 24 | 0.88 | 0.854167 | 48 | yes |
| 32 B | 32 | 0.88 | 0.865234 | 48 | yes |
| 64 B | 16 | 0.88 | 0.859375 | 59 | no |
| 64 B | 24 | 0.88 | 0.833333 | 78 | yes |
| 64 B | 32 | 0.88 | 0.849609 | 78 | yes |

## Interpretation

The crop pipeline no longer needs payload-CRC search to choose the geometry.
Anchors alone are sufficient to select a usable crop-ratio hypothesis in this
patch-token probe.

The practical operating point is still costly:

- 32 B needs 16 images;
- 64 B needs 24 images;
- block size must be 1 byte;
- overhead is 4.0;
- anchor count 16 is the current best default among tested values.

## Limits

- Ratio selection is still grid search; it is now anchor-driven, not fully
  estimated analytically.
- Offset is not independently estimated; this assumes centered crop.
- The method is still patch-token, not VQGAN/AR.
- Anchor patterns are known and may create detectable structure unless later
  keyed and distribution-shaped.

## Next Step

Move from global anchors to local block anchors:

1. split token grid into blocks;
2. put small keyed anchors in each block;
3. reject blocks whose anchors fail;
4. let fountain coding recover from rejected blocks.
