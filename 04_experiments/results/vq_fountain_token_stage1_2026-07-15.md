# VQ-Fountain Stage 1 Token Stability and Recovery Probe

Date: 2026-07-15

## Purpose

Start the transition from a synthetic symbol-erasure channel to a measured token
channel.

Because no learned VQ tokenizer is installed locally, this run uses `patch-vq`:
a fixed patch color quantizer with a 512-token codebook. It validates the
measurement and recovery protocol, but it is not yet a learned VQGAN/AR image
tokenizer result.

## Commands

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
python 05_artifacts\code\vq_fountain\measure_token_stability.py
python 05_artifacts\code\vq_fountain\run_token_recovery_probe.py
python 05_artifacts\code\vq_fountain\run_token_recovery_probe.py --schedule random --out-csv 05_artifacts\results\tables\vq_fountain_token_recovery_probe_random.csv --out-json 05_artifacts\results\raw\vq_fountain_token_recovery_probe_random.json
```

Outputs:

- `05_artifacts/results/tables/vq_fountain_token_stability_stage1.csv`
- `05_artifacts/results/raw/vq_fountain_token_stability_stage1.json`
- `05_artifacts/results/tables/vq_fountain_token_recovery_probe.csv`
- `05_artifacts/results/raw/vq_fountain_token_recovery_probe.json`
- `05_artifacts/results/tables/vq_fountain_token_recovery_probe_random.csv`
- `05_artifacts/results/raw/vq_fountain_token_recovery_probe_random.json`

## Token Stability

Setup:

- images: 2 local sample images
- tokenizer: `patch-vq`
- image size: 256
- patch size: 16
- token grid: 16 x 16
- token count: 256 per image
- codebook size: 512

Mean token match rate:

| Attack | Mean changed tokens | Mean token match rate |
|---|---:|---:|
| clean | 0.0 | 1.000000 |
| JPEG95 | 0.5 | 0.998047 |
| JPEG85 | 2.0 | 0.992188 |
| resize0.75 | 2.0 | 0.992188 |
| blur1 | 6.5 | 0.974609 |
| noise0.02 | 1.5 | 0.994141 |
| crop0.90 | 157.5 | 0.384765 |

Stable positions across all listed attacks including crop0.90:

- image `000000001503.jpg`: 99 / 256
- image `dog_0031.jpg`: 95 / 256

## Recovery Probe

The recovery probe maps each fountain symbol to a group of token positions.
A symbol is delivered only when all assigned token positions remain stable under
the measured attacks. This is a token-space upper-bound probe, not generated
image steganography.

Default recovery attacks:

- JPEG85
- resize0.75
- blur1
- noise0.02

Main thresholds with stability scheduling:

| Payload | Bits/token | Overhead | Minimum simulated images for exact recovery |
|---:|---:|---:|---:|
| 32 B | 1 | 0.5 | 4 |
| 32 B | 2 | 0.5 | 2 |
| 64 B | 1 | 0.5 | 4 |
| 64 B | 2 | 0.5 | 2 |
| 128 B | 1 | 0.5 | 8 |
| 128 B | 2 | 0.5 | 4 |
| 128 B | 2 | 0.8 | 8 |

Scheduling ablation:

- stability schedule: multiple exact-recovery conditions pass;
- random schedule: 0 / 72 exact-recovery conditions pass.

## Interpretation

The first concrete direction is supported:

1. token stability is attack-dependent and must be measured, not assumed;
2. crop-like geometric shift is the immediate hard case;
3. stability-aware scheduling is necessary under grouped symbol placement;
4. rateless multi-image recovery is a plausible operating mode for short and
   medium payloads.

## Limits

- `patch-vq` is not a learned tokenizer.
- Only two images were used.
- The recovery probe uses an upper-bound stability schedule.
- The probe assumes fixed bits/token and does not yet implement
  distribution-aware token sampling.
- No generated coverless image pipeline is connected yet.
