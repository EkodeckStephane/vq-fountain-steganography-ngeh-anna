# VQ-Fountain Final Ablation Suite

Date: 2026-07-15

## Purpose

Run the mandatory ablations for the active Stage 1 configuration.

Common setting: 64 B payload, 16 images, 1 bit/token, block size 1, crop0.90
with row offset `0.02`, column offset `-0.02`, and anchor-driven 2D geometry
search.

## Results

| Ablation | Variant | Exact recovery | CRC-valid symbols | Value match |
|---|---|---:|---:|---:|
| coding | fountain | yes | 119 | 0.895370 |
| coding | repetition | no | 109 | 0.884259 |
| sampling | projection | yes | 119 | 0.895370 |
| sampling | naive | no | 7 | 0.636574 |
| anchors | block 1 per 4x4 | yes | 119 | 0.895370 |
| anchors | global 9 | yes | 96 | 0.882407 |
| schedule | center | yes | 96 | 0.882407 |
| schedule | random | no | 71 | 0.818750 |
| block rejection | off | yes | 85 | 0.876488 |
| block rejection | threshold 0.5 | yes | 83 | 0.867560 |

Outputs:

- `05_artifacts/results/tables/vq_fountain_final_ablation_suite.csv`
- `05_artifacts/results/raw/vq_fountain_final_ablation_suite.json`

## Interpretation

- The rateless fountain layer is necessary under the tested lossy crop channel:
  repetition fails where fountain recovers exactly.
- Distribution-aware projection binning is necessary: naive token modulo
  mapping collapses recovery.
- Spatial block anchors improve CRC-valid symbol count relative to a global
  9-anchor prefix at the same anchor budget.
- Center scheduling is necessary for crop; random scheduling fails.
- Local block rejection is no longer catastrophic at threshold 0.5, but it does
  not improve recovery and is not the default.
