# VQ-Fountain External Dataset Stability

Date: 2026-07-15

## Purpose

Replace sample-only token stability checks with external dataset measurements.
The source folders are recorded only through sanitized aliases.

## Datasets

| Alias | Image files | Sampled images | Main formats |
|---|---:|---:|---|
| bossbase | 10000 | 1000 | PGM |
| local_raw | 21452 | 1000 | PGM, JPG |

Manifest:

- `05_artifacts/data/external_dataset_manifest.json`

## Results

Tokenizer: `learned-patch-vq`

| Dataset | Attack | Mean token match |
|---|---|---:|
| bossbase | clean | 1.000000 |
| bossbase | jpeg85 | 0.995223 |
| bossbase | resize075 | 0.996117 |
| bossbase | noise002 | 0.988297 |
| bossbase | blur1 | 0.975586 |
| bossbase | crop090 | 0.471012 |
| bossbase | crop090_r02_c-02 | 0.445676 |
| local_raw | clean | 1.000000 |
| local_raw | jpeg85 | 0.990992 |
| local_raw | resize075 | 0.994844 |
| local_raw | noise002 | 0.985504 |
| local_raw | blur1 | 0.966414 |
| local_raw | crop090 | 0.448480 |
| local_raw | crop090_r02_c-02 | 0.430004 |

Outputs:

- `05_artifacts/results/tables/vq_fountain_token_stability_bossbase_1000.csv`
- `05_artifacts/results/raw/vq_fountain_token_stability_bossbase_1000.json`
- `05_artifacts/results/tables/vq_fountain_token_stability_localraw_1000.csv`
- `05_artifacts/results/raw/vq_fountain_token_stability_localraw_1000.json`

## Interpretation

The external datasets confirm the earlier local observation:

- JPEG, resize, mild noise, and blur preserve most learned patch-VQ tokens.
- Crop destroys direct token alignment, which justifies the anchor-based
  geometry layer.
- Offset crop is slightly harder than centered crop, but the `anchors2d`
  recovery probe already restores exact payload recovery for the tested payloads.
