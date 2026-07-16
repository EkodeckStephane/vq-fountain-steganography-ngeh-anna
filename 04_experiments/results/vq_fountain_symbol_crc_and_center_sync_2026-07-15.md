# VQ-Fountain Symbol CRC and Center-Schedule Probe

Date: 2026-07-15

## Purpose

Address two limits from the distribution-aware sampler probe:

1. corrupted symbols could contaminate GF(2) decoding;
2. crop0.90 destroyed token synchronization.

## Implemented Changes

Symbol-level CRC:

- each generated `FountainSymbol` now carries `data_crc`;
- `decode_symbols()` filters CRC-invalid symbols before GF(2) elimination;
- corrupted symbols are treated as erasures rather than equations.

Center-position scheduling:

- `run_distribution_sampler_probe.py` now supports `--position-mode center`;
- payload positions are restricted to a central token window controlled by
  `--margin`;
- receiver extracts from the same deterministic central schedule.

## Symbol CRC Stress Result

Command shape:

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
python 05_artifacts\code\vq_fountain\run_distribution_sampler_probe.py `
  --payload-bytes 64 128 `
  --bits-per-token 1 2 `
  --overheads 0.5 0.8 1.2 `
  --image-copies 2 4 8 12 16 `
  --attacks clean jpeg85 resize075 blur1 noise002 crop090 `
  --out-csv 05_artifacts\results\tables\vq_fountain_distribution_sampler_probe_k128_symbolcrc_stress.csv `
  --out-json 05_artifacts\results\raw\vq_fountain_distribution_sampler_probe_k128_symbolcrc_stress.json
```

Result:

| Attack | Exact recovery | Mean value match | Mean CRC-valid symbols | Mean CRC-rejected symbols |
|---|---:|---:|---:|---:|
| clean | 48 / 60 | 1.000000 | 42.350 | 0.000 |
| JPEG85 | 48 / 60 | 1.000000 | 42.350 | 0.000 |
| resize0.75 | 48 / 60 | 1.000000 | 42.350 | 0.000 |
| blur1 | 48 / 60 | 0.998471 | 41.483 | 0.867 |
| noise0.02 | 48 / 60 | 1.000000 | 42.350 | 0.000 |
| crop0.90 | 0 / 60 | 0.550701 | 0.000 | 42.350 |

Effect:

- blur1 improves from 30 / 60 exact recoveries to 48 / 60 because corrupted
  symbols are discarded instead of poisoning the decoder;
- crop0.90 remains fully broken because all recovered symbols fail CRC.

## Center-Schedule Crop Probe

Command shape:

```powershell
python 05_artifacts\code\vq_fountain\run_distribution_sampler_probe.py `
  --payload-bytes 64 128 `
  --bits-per-token 1 2 `
  --overheads 0.5 0.8 `
  --image-copies 4 8 12 16 24 `
  --attacks clean jpeg85 resize075 blur1 noise002 crop090 `
  --position-mode center `
  --margin 2 `
  --out-csv 05_artifacts\results\tables\vq_fountain_distribution_sampler_probe_k128_center_margin2.csv `
  --out-json 05_artifacts\results\raw\vq_fountain_distribution_sampler_probe_k128_center_margin2.json
```

Result:

| Attack | Exact recovery | Mean value match | Mean CRC-valid symbols | Mean CRC-rejected symbols |
|---|---:|---:|---:|---:|
| clean | 36 / 40 | 1.000000 | 39.875 | 0.000 |
| JPEG85 | 36 / 40 | 1.000000 | 39.875 | 0.000 |
| resize0.75 | 36 / 40 | 1.000000 | 39.875 | 0.000 |
| blur1 | 34 / 40 | 0.998939 | 39.000 | 0.875 |
| noise0.02 | 36 / 40 | 1.000000 | 39.875 | 0.000 |
| crop0.90 | 0 / 40 | 0.665523 | 0.000 | 39.875 |

Interpretation:

- center scheduling improves crop value match from roughly 0.55 to 0.67;
- it still produces zero CRC-valid symbols under crop0.90;
- it reduces available positions, so non-crop payloads need more image copies.

## Current Status

Lifted:

- corrupted symbol contamination is fixed for the current fountain decoder;
- blur robustness improves materially under the patch-token probe.

Still open:

- crop/geometric synchronization is not solved by a simple center window;
- the next solution must use explicit geometric synchronization, redundant
  anchors, local block registration, or a crop-invariant token layout.

Update: a later high-redundancy crop-ratio search achieved the first crop0.90
exact recovery in `vq_fountain_crop_geometry_breakthrough_2026-07-15.md`.
