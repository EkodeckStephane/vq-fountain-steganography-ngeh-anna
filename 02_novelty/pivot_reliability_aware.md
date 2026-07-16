# Pivot: Reliability-Aware Auxiliary-Channel-Free Neural Steganography

Status: legacy pivot superseded by `02_novelty/recommended_orientation.md`
and `03_method/method_specification.md` for VQ-Fountain Stega.

Date: 2026-07-14

## Why Pivot

The previous line attempted to rescue a high-capacity 2 bpp neural embedding checkpoint. Smoke tests showed:

- one-image exact recovery is possible;
- generalization is weak;
- image quality is poor for the original checkpoint;
- V2 improves clean-channel quality at 0.25 bpp but remains weak under JPEG/blur/resize;
- the "2 bpp high-capacity robust imperceptible" claim is not currently defensible.

Continuing to optimize this as a generic GAN/high-capacity steganography paper is likely to trigger:

- lack of novelty;
- insufficient experimental evidence;
- overclaiming;
- weak robustness;
- weak security evaluation.

## New Scientific Position

The article will target:

> Reliability-aware auxiliary-channel-free neural image steganography for replacing WYSAWIS-style external location metadata.

The novelty is not "another GAN." The novelty is an operational replacement of an external location channel by an image-internal, self-contained, reliability-aware communication layer.

## Core Idea

WYSAWIS needs external cloud-carried location information. ETEHGAN v3 should instead transmit a self-contained bitstream in one image:

1. robust header;
2. payload length;
3. payload CRC;
4. chunked ECC;
5. deterministic interleaving;
6. confidence/reliability-aware extraction;
7. adaptive payload rate selected from measured reliability.

The receiver uses only:

- stego image;
- shared model/checkpoint;
- public packet format;
- optional shared seed/key.

No cloud folder positions or side metadata are required.

## What Becomes Novel

| Component | Novelty Role |
|---|---|
| Auxiliary-channel-free framing | Directly addresses WYSAWIS's core operational limitation. |
| Reliability-aware packet layer | Replaces external location metadata with self-contained robust packet recovery. |
| Adaptive capacity | Avoids unsafe fixed "2 bpp" overclaim; capacity is reported as effective reliable payload. |
| Reviewer-grade evidence | Capacity-quality-reliability-security frontier replaces isolated PSNR/BER values. |

## Revised Contributions

1. We formalize the auxiliary-channel dependency and repeated-artifact risks of WYSAWIS-style high-capacity coverless indexing.
2. We propose ETEHGAN v3, an auxiliary-channel-free neural steganography framework with a self-contained reliability-aware packet layer.
3. We introduce adaptive payload accounting that separates nominal bitstream size, ECC/interleaving overhead, and effective user payload.
4. We evaluate clean-channel recovery, degradation under attacks, and image-level detectability under explicit adversary assumptions.

## Claims We Will Not Make

- first GAN steganography;
- first coverless GAN;
- 2 bpp robust payload;
- undetectable steganography;
- cryptographic confidentiality unless the payload is encrypted before embedding;
- coverless if a cover image is used.

## Immediate Technical Goal

Show reliable exact recovery at low payload:

- 0.05 bpp;
- 0.10 bpp;
- 0.25 bpp only if stable.

The target is exact recovery first, then capacity scaling.
