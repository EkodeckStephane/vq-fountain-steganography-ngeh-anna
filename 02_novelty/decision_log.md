# Decision Log

Status: historical ETHEGAN decision log. The active July 2026 decision is the
VQ-Fountain Stega pivot documented in `02_novelty/recommended_orientation.md`.

## D1 - Article Positioning

Date: 2026-07-13

Decision:

The article will not be positioned as a generic GAN steganography paper.

Accepted positioning:

> Auxiliary-channel-free high-capacity neural image steganography, motivated by the operational limitations of WYSAWIS and evaluated with a reproducible capacity-quality-robustness-security protocol.

Reason:

Semantic Scholar discovery found multiple direct novelty threats:

- GAN-based coverless image steganography
- generative steganography networks
- image-synthesis-based coverless methods
- robust generative steganography based on image mapping
- invertible neural network + GAN steganography
- StyleGAN-based high-capacity steganography

Therefore, novelty must come from the WYSAWIS-specific operational gap, global payload encoding, absence of auxiliary cloud metadata, and rigorous evaluation.

Consequence:

The words "first", "coverless", "undetectable", "perfect", and "maximum security" require explicit proof before use.

## D2 - Current Prototype Framing

Date: 2026-07-13

Decision:

The current prototype must be described as neural image steganography, not coverless generative steganography, until the implementation proves otherwise.

Reason:

The current `ETEHGAN/` scripts take a cover image as input. A method that requires a cover image is not coverless in the strict sense.

Consequence:

If the final paper keeps this architecture, the title and abstract must avoid "coverless" and focus on "auxiliary-channel-free".

## D3 - Minimal Novelty Test

Date: 2026-07-13

Decision:

Before manuscript drafting, every proposed contribution must pass this test:

1. Which specific paper does it improve on?
2. What exact limitation is addressed?
3. What experiment proves it?
4. What table or figure will show it?
5. What claim is no longer allowed if the experiment fails?

## D4 - Pivot to Reliability-Aware ETEHGAN v3

Date: 2026-07-14

Decision:

The article pivots away from high-capacity 2 bpp GAN-style framing.

Accepted new positioning:

> Reliability-aware auxiliary-channel-free neural image steganography that replaces WYSAWIS-style external location metadata with a self-contained robust packet layer.

Reason:

The current checkpoint and V2 experiments do not support Q1-level claims of 2 bpp robust, imperceptible, general image steganography. However, the operational WYSAWIS gap remains strong: external location metadata and repeated cloud artifacts can be replaced by a self-contained image-only communication layer.

Consequence:

The next experiments must prioritize exact recovery at low payload rates before capacity escalation.
