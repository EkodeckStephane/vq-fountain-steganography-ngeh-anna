# VQ-Fountain SPAM-Style Steganalysis Probe

Date: 2026-07-15

## Purpose

Add a classical residual-cooccurrence steganalysis probe alongside the existing
feature-level detector and small-CNN detector.

This is a local SPAM-style probe, not a complete external SRM/SRNet benchmark.

## Protocol

- Model: converted public VQGAN f4-8192 checkpoint.
- Payload: 32 B.
- Payload images: 88.
- Reference images: 88.
- Payload generation: grouped 2x2 macro-cell value coding with overhead 3.0.
- Features: 1388 residual cooccurrence and residual-statistic features.
- Classifier: standardized logistic regression.
- Split: stratified 65/35 train/test.

## Result

| Detector | AUC | Accuracy |
|---|---:|---:|
| SPAM-style residual cooccurrence | 0.56919875 | 0.56451613 |

## Evidence

- `05_artifacts/code/vq_fountain/run_real_vqgan_spam_steganalysis_probe.py`
- `05_artifacts/results/tables/vq_fountain_real_vqgan_spam_steganalysis.csv`
- `05_artifacts/results/raw/vq_fountain_real_vqgan_spam_steganalysis.json`

## Decision

The previous lack of standard-style local steganalysis evidence is lifted for a
classical residual-cooccurrence detector. The manuscript may report this as
local SPAM-style evidence only. It must not claim resistance to full external
SRM/SRNet suites until those suites are run.
