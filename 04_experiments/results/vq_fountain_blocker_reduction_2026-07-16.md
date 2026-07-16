# VQ-Fountain Blocker Reduction Pass

Date: 2026-07-16

Purpose: address the main readiness blockers identified after the first
compiled VQ-Fountain draft.

## Payload Scale

The main public VQGAN f4-8192 Stage 2 setting was extended from 32 B to 64 B.

Configuration:

- payload: 64 B;
- packet: 76 B;
- block size: 1 B;
- overhead: 4.0;
- macro-cells: 2x2;
- symbols per image: 8;
- generated images: 48;
- payload/test seeds: `real-vqgan-64-a`, `real-vqgan-64-b`,
  `real-vqgan-64-c`;
- attacks: `clean`, `crop090+jpeg85+drop25`.

Result:

| Attack | Seeds | Images | CRC-valid symbols | Exact recovery |
|---|---:|---:|---|---|
| clean | 3 | 48 | 371-373 | true |
| crop090+jpeg85+drop25 | 3 | 48 | 97-111 | true |

Evidence:

- `05_artifacts/results/tables/vq_fountain_real_vqgan_payload_probe_payload64_multiseed.csv`
- `05_artifacts/results/raw/vq_fountain_real_vqgan_payload_probe_payload64_multiseed.json`

Decision: the "main real-model payload is only 32 B" blocker is lifted for the
bounded feasibility claim. Do not generalize beyond the tested 64 B setting.

## Steganalysis

A stronger local SRM-style residual cooccurrence detector was added and run on
the same 64 B VQGAN setting. The older feature-level, small-CNN, and SPAM-style
detectors were also rerun at 64 B so the detector evidence matches the main
payload scale.

| Detector | Payload/ref images | AUC | Accuracy |
|---|---:|---:|---:|
| Feature-level logistic | 144 / 144 | 0.48862745 | 0.53465347 |
| Small CNN | 144 / 144 | 0.53320000 | 0.57000000 |
| SPAM-style residual cooccurrence | 144 / 144 | 0.52627451 | 0.50495050 |
| SRM-style residual cooccurrence | 144 / 144 | 0.49521569 mean | 0.49702970 mean |

Evidence:

- `05_artifacts/code/vq_fountain/run_real_vqgan_srm_steganalysis_probe.py`
- `05_artifacts/results/tables/vq_fountain_real_vqgan_quality_security_payload64.csv`
- `05_artifacts/results/tables/vq_fountain_real_vqgan_deep_steganalysis_payload64.csv`
- `05_artifacts/results/tables/vq_fountain_real_vqgan_spam_steganalysis_payload64.csv`
- `05_artifacts/results/tables/vq_fountain_real_vqgan_srm_steganalysis_payload64.csv`

Decision: the detector evidence is no longer limited to the earlier 32 B / 88
image setting. The paper may claim bounded local detector evidence, but it must
not claim undetectability or official external SRNet resistance.

## Baselines and StegaStamp

The existing baseline audit remains the governing rule:

- HiDDeN has a local compatibility run artifact.
- DCT-spread has a local run artifact.
- StegaStamp source is present but no local score is claimed because the
  pretrained SavedModel, TensorFlow runtime, and BCH dependency are unavailable.

Decision: StegaStamp is not a blocker for the bounded feasibility paper because
no claim depends on a local StegaStamp score. It remains a paper/code comparator.

## Third Public VQModel Attempt

A third cached Hugging Face candidate, `thomwolf/vqgan_imagenet_f16_1024`, was
found, but only `config.json` was cached locally. A download attempt for
`pytorch_model.bin` failed with DNS resolution error (`getaddrinfo failed`).

Decision: broader generator coverage remains a deferred extension. It is not a
blocker for the current bounded feasibility claim because the paper no longer
claims broad generator generality or final SOTA superiority.
