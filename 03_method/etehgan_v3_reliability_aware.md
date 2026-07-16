# ETEHGAN v3 Reliability-Aware Method

Status: legacy method note. The active method specification is
`03_method/method_specification.md` for VQ-Fountain Stega.

## System Definition

ETEHGAN v3 is a neural image steganography system with a self-contained packet layer.

Sender input:

- cover image;
- secret payload;
- shared model checkpoint;
- packet parameters;
- optional seed/key.

Transmitted object:

- one stego image.

Receiver input:

- stego image;
- shared model checkpoint;
- packet parameters;
- optional seed/key.

No WYSAWIS-style cloud, folder index, block sequence position list, or external location metadata is used.

## Packet Layer

The bitstream contains:

1. magic bytes;
2. version;
3. payload length;
4. payload CRC32;
5. packet configuration identifier;
6. payload bytes;
7. padding;
8. chunked Reed-Solomon parity;
9. deterministic interleaving.

The header is ECC-protected so that the receiver can infer payload size from
the decoded image bitstream itself.

Current implementation:

- `packet_v3.py` implements a single ECC-protected header rather than a repeated
  header;
- payload length and CRC32 are self-contained in the decoded packet;
- the receiver still needs the public extraction configuration
  (`payload-bpp`, `ecc-bytes`, `nsize`) and the shared packet seed;
- automatic configuration scanning is not implemented yet.

## Reliability Layer

The receiver computes bit logits from the neural decoder. Reliability is derived from logit magnitude:

```text
reliability(bit_i) = abs(logit_i)
```

For byte-level ECC, the byte reliability is the minimum or mean reliability of its 8 bits. Low-confidence bytes can be treated as erasures when supported by the ECC decoder.

Current evidence:

- erasure decoding is implemented;
- an initial COCO noise2 test with 8 erasures per RS chunk did not improve exact
  recovery over hard decoding;
- therefore, the reliability-aware component is currently an implemented
  mechanism, not yet a demonstrated empirical advantage.

## Adaptive Capacity

Instead of claiming fixed high capacity, ETEHGAN v3 reports:

- nominal carrier bitstream;
- packet capacity;
- ECC overhead;
- interleaving overhead;
- effective payload bytes;
- exact recovery rate;
- failure rate.

Capacity is selected by a reliability policy:

```text
choose highest payload rate r such that exact_recovery_rate(r) >= target
```

Candidate rates:

- 0.05 bpp;
- 0.10 bpp;
- 0.25 bpp;
- 0.50 bpp only after lower rates are stable.

## Training Objective

Clean-channel baseline:

```text
L = lambda_extract * BCEWithLogits(decoded_bits, target_bits)
  + lambda_image * MSE(stego, cover)
```

Robust training extension:

```text
L_robust = BCEWithLogits(decoder(attack(stego)), target_bits)
```

Attacks for training:

- mild noise;
- JPEG-like differentiable approximation or compression simulation;
- blur;
- resize/downsample-upsample.

## Reviewer-Safe Claim Boundary

Allowed after current evidence:

> The V3 packet layer turns low raw BER into exact clean-channel payload recovery
> on small held-out Caltech101 and COCO subsets, without WYSAWIS-style external
> location metadata.

Not allowed yet:

- robust to JPEG;
- Q1-ready;
- secure against steganalysis;
- high-capacity at 2 bpp.
- demonstrated improvement from reliability-aware erasures.
