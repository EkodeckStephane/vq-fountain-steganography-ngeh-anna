# VQ-Fountain Stage 0 Synthetic Results

Date: 2026-07-15

## Purpose

Validate the model-independent recovery layer before connecting an image
tokenizer or generator.

This is not an image-steganography result. It tests only packet packing, CRC,
XOR fountain coding, GF(2) decoding, and synthetic symbol erasures.

## Command

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
python 05_artifacts\code\vq_fountain\run_synthetic_sweep.py --trials 20
```

Outputs:

- `05_artifacts/results/tables/vq_fountain_synthetic_stage0.csv`
- `05_artifacts/results/raw/vq_fountain_synthetic_stage0.json`

## Setup

- payload sizes: 128 bytes and 1024 bytes
- block size: 32 bytes
- overheads: 0.25, 0.50, 0.80, 1.20
- symbol erasure rates: 0.0 to 0.5
- trials per condition: 20
- bit flips: 0.0

## Key Findings

For 1024-byte payloads:

| Overhead | 10% erasure | 20% erasure | 30% erasure | 40% erasure | 50% erasure |
|---:|---:|---:|---:|---:|---:|
| 0.25 | 0.95 | 0.50 | 0.00 | 0.00 | 0.00 |
| 0.50 | 1.00 | 1.00 | 0.50 | 0.10 | 0.00 |
| 0.80 | 1.00 | 1.00 | 0.95 | 0.90 | 0.15 |
| 1.20 | 1.00 | 1.00 | 1.00 | 1.00 | 0.65 |

For 128-byte payloads, results are more volatile because the source-block count
is only 5. This needs separate short-payload tuning rather than assuming the
same code parameters are optimal across all payload sizes.

## Interpretation

The recovery core is viable for the next stage:

1. medium payloads can tolerate substantial symbol erasure when overhead is
   high enough;
2. exact recovery is measured by CRC-validated payload equality, not raw BER;
3. unsuccessful decodes are retained in the aggregate table.

## Limits

- Synthetic symbol erasure is not JPEG, resize, blur, or tokenizer drift.
- No token-distribution security is tested here.
- No image generator is connected yet.
- Dense parity symbols improve recovery but may increase scheduling pressure in
  the real token channel.
- Short payloads need a dedicated parameter regime.
