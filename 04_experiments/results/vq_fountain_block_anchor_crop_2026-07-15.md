# VQ-Fountain Block-Anchor Crop Synchronization

Date: 2026-07-15

## Purpose

Test whether spatially distributed synchronization anchors improve crop
recovery compared with a single global anchor prefix.

The probe partitions the usable token grid into local blocks. For the learned
patch-VQ tokenizer with a 16x16 token grid, center scheduling with margin 2
leaves a 12x12 region. With 4x4 token blocks this gives 9 local blocks per
image.

## Implementation

Added experimental options to
`05_artifacts/code/vq_fountain/run_distribution_sampler_probe.py`:

- `--anchor-scope global|block`;
- `--token-block-size`;
- `--block-anchor-threshold`.

For `--anchor-scope block`, each token block reserves a small number of keyed
anchor positions before payload positions. The receiver can select the crop
ratio by anchor agreement. It can also reject blocks whose anchor agreement
falls below a threshold, although the current probe shows this rejection is not
yet beneficial.

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
  --anchor-scope block `
  --token-block-size 4 `
  --anchor-count 1 `
  --block-anchor-threshold 0.0 `
  --crop-ratios 0.94 0.92 0.90 0.88 0.86
```

## Results

All runs use crop0.90, center schedule, margin 2, fountain block size 1,
overhead 4.0, and 1 bit/token.

| Anchor layout | Anchors/image | Local block rejection | 32 B exact | 32 B min images | 64 B exact | 64 B min images |
|---|---:|---:|---:|---:|---:|---:|
| Global prefix | 9 | no | 3 / 3 | 16 | 2 / 3 | 24 |
| Global prefix | 16 | no | 3 / 3 | 16 | 2 / 3 | 24 |
| Block 4x4 | 9 | no | 3 / 3 | 16 | 3 / 3 | 16 |
| Block 4x4 | 18 | no | 3 / 3 | 16 | 2 / 3 | 24 |
| Block 4x4 | 18 | threshold 0.5 | 3 / 3 | 16 | 2 / 3 | 24 |
| Block 4x4 | 27 | threshold 0.67 | 0 / 3 | none | 0 / 3 | none |

Representative block-anchor results:

| Anchor layout | Payload | Images | Selected ratio | Anchor match | CRC-valid symbols | Exact recovery |
|---|---:|---:|---:|---:|---:|---:|
| Global 9 | 64 B | 16 | 0.88 | 0.888889 | 60 | no |
| Global 9 | 64 B | 24 | 0.88 | 0.879630 | 86 | yes |
| Block 4x4, 1 anchor/block | 64 B | 16 | 0.90 | 0.854167 | 77 | yes |
| Block 4x4, 1 anchor/block | 64 B | 24 | 0.90 | 0.847222 | 105 | yes |
| Block 4x4, 2 anchors/block | 64 B | 16 | 0.88 | 0.833333 | 67 | no |
| Block 4x4, 2 anchors/block | 64 B | 24 | 0.88 | 0.837963 | 102 | yes |

## Interpretation

The best current crop setting is spatially distributed anchors with one anchor
per 4x4 token block and no local block rejection. This setting selects the true
crop-ratio hypothesis in this centered crop probe and recovers 64 B with 16
images.

The improvement is not just lower anchor cost. A global 9-anchor layout still
needs 24 images for 64 B, while the spatial 9-anchor layout succeeds with 16
images.

Local block rejection is not ready. With 2 anchors/block and threshold 0.5 it
rejects few blocks and does not improve exact recovery. With 3 anchors/block and
threshold 0.67 it rejects too many useful payload slots and all tested recovery
conditions fail.

## Limits

- This is still a learned patch-VQ probe, not a real VQGAN/autoregressive
  generator.
- Crop synchronization still uses a small crop-ratio grid; anchors select among
  hypotheses rather than estimating continuous geometry.
- The crop is centered; offset, rotation, perspective, local warps, and
  combined attacks are not covered.
- Results use one deterministic payload/key setting and small image-count
  sweeps; they need seeds and confidence intervals.
- Anchor sequences must be keyed and distribution-shaped in the final system to
  avoid detectable structure.
