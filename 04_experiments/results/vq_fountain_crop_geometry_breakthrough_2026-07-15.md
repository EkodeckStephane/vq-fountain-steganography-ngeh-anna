# VQ-Fountain Crop Geometry Breakthrough

Date: 2026-07-15

## Purpose

Move crop0.90 from total failure to at least one exact-recovery operating
point in the learned patch-token probe.

The previous center-schedule attempt improved value match under crop0.90 but
still produced zero CRC-valid symbols. The new probe combines:

1. center token scheduling;
2. crop-ratio search at the receiver;
3. symbol-level CRC erasure filtering;
4. short fountain symbols (`block_size=1`);
5. high fountain redundancy.

## Geometry Search

The receiver tests several candidate crop ratios and keeps the result that
either decodes exactly or maximizes CRC-valid symbols and value match.

Command shape:

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
python 05_artifacts\code\vq_fountain\run_distribution_sampler_probe.py `
  --payload-bytes 32 64 `
  --bits-per-token 1 `
  --block-size 1 `
  --overheads 3.0 4.0 6.0 `
  --image-copies 16 24 32 48 64 `
  --attacks crop090 `
  --position-mode center `
  --margin 2 `
  --geometry-search crop `
  --crop-ratios 0.94 0.92 0.90 0.88 0.86 `
  --out-csv 05_artifacts\results\tables\vq_fountain_distribution_sampler_probe_k128_crop_geometry_block1_highred.csv `
  --out-json 05_artifacts\results\raw\vq_fountain_distribution_sampler_probe_k128_crop_geometry_block1_highred.json
```

## Results

| Payload | Bits/token | Block size | Overhead | Minimum images | Selected ratio | Exact recovery |
|---:|---:|---:|---:|---:|---:|---:|
| 32 B | 1 | 1 | 3.0 | none | 0.88 | 0 / 5 |
| 32 B | 1 | 1 | 4.0 | 16 | 0.90 | 5 / 5 |
| 32 B | 1 | 1 | 6.0 | 16 | 0.94 | 5 / 5 |
| 64 B | 1 | 1 | 3.0 | none | 0.88 | 0 / 5 |
| 64 B | 1 | 1 | 4.0 | 24 | 0.88 | 4 / 5 |
| 64 B | 1 | 1 | 6.0 | 24 | 0.90 | 4 / 5 |

Representative successful cases:

| Payload | Overhead | Images | CRC-valid symbols | Recovered symbols | Value match |
|---:|---:|---:|---:|---:|---:|
| 32 B | 4.0 | 16 | 54 | 220 | 0.835795 |
| 64 B | 4.0 | 24 | 78 | 380 | 0.833224 |
| 64 B | 6.0 | 24 | 90 | 432 | 0.829572 |

## Interpretation

This is the first crop0.90 exact-recovery result in the local patch-token
pipeline.

The important technical point is not the current efficiency. It is that crop can
be converted from catastrophic symbol corruption into a high-erasure channel
that fountain decoding can survive, provided symbols are short enough and
redundancy is high enough.

## Limits

Critical limits still remain:

1. overhead is very high: 4.0 or more for the first successful crop cases;
2. image count is high: 16 images for 32 B and 24 images for 64 B;
3. the pipeline is still learned patch-token, not natural-image VQGAN/AR
   generation;
4. the receiver tests a known candidate crop-ratio grid rather than estimating
   geometry from embedded anchors.

## Next Step

Replace brute-force ratio search with explicit anchors:

- reserve a small anchor pattern in central token blocks;
- estimate crop ratio and offset from anchor agreement;
- decode only blocks whose anchors pass CRC or Hamming checks;
- keep short-symbol fountain coding for crop-heavy channels.

Update: anchor-based ratio selection is implemented and evaluated in
`vq_fountain_anchor_sync_crop_2026-07-15.md`. The best tested default is
16 anchors per image.
