# VQ-Fountain Second Model, Baseline, and Deep Detector Audit

Date: 2026-07-15

## Second Public VQModel

Added support for Hugging Face model IDs plus subfolders in the Stage 2 probes.

Second public checkpoint tested:

- `CompVis/ldm-celebahq-256`, subfolder `vqvae`;
- public `diffusers.VQModel`;
- code path: same calibrated value-channel and fountain recovery stack.

Results:

| Model | Payload | Attack | Images | CRC-valid symbols | Exact recovery |
|---|---:|---|---:|---:|---|
| CompVis/ldm-celebahq-256/vqvae | 2 B | clean | 14 | 14 | true |
| CompVis/ldm-celebahq-256/vqvae | 2 B | jpeg85 | 14 | 14 | true |
| CompVis/ldm-celebahq-256/vqvae | 16 B | clean | 14 | 111 | true |
| CompVis/ldm-celebahq-256/vqvae | 16 B | crop090+jpeg85+drop25 | 14 | 37 | true |

Evidence:

- `05_artifacts/results/tables/vq_fountain_real_vqgan_payload_probe_compvis_smoke.csv`
- `05_artifacts/results/tables/vq_fountain_real_vqgan_payload_probe_compvis_payload16.csv`

Decision: the "single public checkpoint only" limitation is lifted for a
second VQModel feasibility setting.

## Public Baseline Execution Audit

Added `tools/audit_public_baselines.py`.

Audit output:

- `05_artifacts/baselines/baseline_execution_audit.json`
- `04_experiments/results/vq_fountain_public_baseline_execution_audit_2026-07-15.md`

Result:

| Baseline | Accounted | Executable now | Local result |
|---|---:|---:|---|
| HiDDeN | true | true | five-trial smoke run, 30-bit message, mean BER 0.31333333, 0/5 exact recoveries |
| DCT-spread | true | true | 32-bit DCT-spread baseline exact under clean/JPEG85/resize075/blur1, crop090 BER 0.5 |
| StegaStamp | true | false | no pretrained SavedModel; TensorFlow 1.x/BCH runtime unavailable |

Artifacts:

- `05_artifacts/results/tables/hidden_baseline_smoke.csv`
- `05_artifacts/results/raw/hidden_baseline_smoke.json`
- `05_artifacts/results/tables/dct_spread_baseline.csv`
- `05_artifacts/results/raw/dct_spread_baseline.json`

Decision: the local executable-baseline gap is lifted with two runnable
non-coverless baselines. StegaStamp remains a public paper/code comparator only;
no local StegaStamp recovery score is claimed.

## Local Deep Steganalysis Probe

Added `run_real_vqgan_deep_steganalysis_probe.py`, a small CNN detector trained
and tested on Stage 2 VQGAN payload images versus same-family reference images.

Protocol:

- payload: 32 B;
- payload images: 88;
- reference images: 88;
- train samples: 114;
- test samples: 62;
- epochs: 12;
- detector: `SmallSteganalysisCNN`.

Result:

| Detector | AUC | Accuracy |
|---|---:|---:|
| Small CNN | 0.51092612 | 0.50000000 |

Evidence:

- `05_artifacts/results/tables/vq_fountain_real_vqgan_deep_steganalysis.csv`
- `05_artifacts/results/raw/vq_fountain_real_vqgan_deep_steganalysis.json`

Decision: the "no local deep detector" limitation is lifted for a controlled
small-CNN probe. This is still not a substitute for standard external
steganalysis suites.

## Classical SPAM-Style Steganalysis Probe

Added `run_real_vqgan_spam_steganalysis_probe.py`, a classical residual
cooccurrence detector inspired by SPAM/rich-model steganalysis.

Protocol:

- payload: 32 B;
- payload images: 88;
- reference images: 88;
- features: 1388 residual cooccurrence and residual-statistic features;
- classifier: standardized logistic regression;
- train/test split: stratified 65/35.

Result:

| Detector | AUC | Accuracy |
|---|---:|---:|
| SPAM-style residual cooccurrence | 0.56919875 | 0.56451613 |

Evidence:

- `05_artifacts/results/tables/vq_fountain_real_vqgan_spam_steganalysis.csv`
- `05_artifacts/results/raw/vq_fountain_real_vqgan_spam_steganalysis.json`

Decision: the "standard-style classical steganalysis" gap is lifted for a
local SPAM-style probe. This does not replace a full external SRM/SRNet suite.

## Remaining Items

- Full external steganalysis suites such as SRM/SRNet are still future work.
- StegaStamp remains paper/code-only locally until a SavedModel and compatible
  runtime are available.
- The full manuscript and final SOTA table must be kept synchronized with these
  evidence boundaries.
