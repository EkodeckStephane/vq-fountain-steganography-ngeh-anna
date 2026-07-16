# VQ-Fountain 2D Anchor Geometry Search

Date: 2026-07-15

## Purpose

Validate that anchor-based crop synchronization can select both crop ratio and
2D crop offset, not only a centered crop ratio.

## Implementation

Added:

- `--geometry-search anchors2d`;
- `--crop-offsets`;
- attack syntax `crop090_r02_c-02` for non-centered crop tests.

The receiver evaluates `(ratio, row_offset, col_offset)` hypotheses and selects
the one with the highest anchor agreement.

## Probe

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
python 05_artifacts\code\vq_fountain\run_distribution_sampler_probe.py `
  --payload-bytes 32 64 `
  --bits-per-token 1 `
  --block-size 1 `
  --overheads 4.0 `
  --image-copies 16 24 `
  --attacks crop090_r02_c-02 `
  --position-mode center `
  --margin 2 `
  --geometry-search anchors2d `
  --anchor-scope block `
  --token-block-size 4 `
  --anchor-count 1 `
  --block-anchor-threshold 0.0 `
  --crop-ratios 0.94 0.92 0.90 0.88 0.86 `
  --crop-offsets -0.02 0.0 0.02
```

## Results

| Payload | Images | Selected ratio | Selected row offset | Selected col offset | Anchor match | CRC-valid symbols | Exact recovery |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 32 B | 16 | 0.90 | 0.02 | -0.02 | 0.895833 | 87 | yes |
| 32 B | 24 | 0.90 | 0.02 | -0.02 | 0.907407 | 87 | yes |
| 64 B | 16 | 0.90 | 0.02 | -0.02 | 0.895833 | 99 | yes |
| 64 B | 24 | 0.92 | 0.02 | -0.02 | 0.893519 | 135 | yes |

## Interpretation

The synchronizer correctly recovers the imposed crop offset for the 16-image
conditions and keeps exact payload recovery. The 64 B / 24-image condition
selects the correct offset but a neighboring ratio; this still recovers exactly,
which suggests the anchor score has a small ratio ambiguity at higher redundancy.

## Remaining Issue

The current search is still discrete. A continuous estimator or multi-scale
search is needed before claiming general geometric synchronization.
