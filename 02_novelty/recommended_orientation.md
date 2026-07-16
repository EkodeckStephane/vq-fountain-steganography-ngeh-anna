# Recommended Article Orientation

Status: active after the July 2026 pivot.

## Core Position

Build the article around the following contribution:

> VQ-Fountain Steganography: a coverless generative image steganography
> framework that embeds payloads through distribution-aware VQ token choices and
> recovers them with an in-band rateless fountain layer across one or more
> generated images.

This is stronger than the previous clean-channel ETHEGAN framing because it
attacks the three critical weaknesses directly:

1. no cover image is required by the sender;
2. payload recovery is designed for lossy channels through rateless redundancy;
3. security is linked to token-distribution preservation rather than only small
   pixel residuals.

## Working Title

Preferred:

> VQ-Fountain Steganography: Distribution-Preserving Coverless Image Generation
> with In-Band Rateless Recovery

Short variant:

> VQ-Fountain Stega: Robust Coverless Generative Image Steganography with
> Rateless Token Recovery

## Main Scientific Gap

Recent generative, coverless, robust, and watermark-like image hiding methods
show that the field is active. The still defensible gap is:

> No established method simultaneously provides coverless generative image
> synthesis, distribution-aware token-level embedding, no auxiliary recovery
> channel, and rateless multi-image recovery under realistic image processing.

The paper must not claim to be the first generative steganography method, the
first robust hiding method, or the first diffusion/VQ watermarking method.

## Proposed Contributions

Use precise claims:

1. We formulate coverless VQ-token steganography as a constrained sampling
   problem where payload bits are carried by key-conditioned choices among
   high-probability token alternatives.
2. We introduce an in-band fountain packet layer that spreads recoverable coded
   symbols across token positions and images without an auxiliary stego text or
   location channel.
3. We define entropy-stability token scheduling: candidate positions are chosen
   by combining model entropy with empirical re-tokenization stability under
   JPEG, resize, blur, noise, and crop.
4. We evaluate exact message recovery, effective bits per image, realism,
   robustness, and steganalysis detectability under equal-payload and
   equal-quality constraints.

## Avoid

- "undetectable"
- "perfect security"
- "robust to all transformations"
- "first generative steganography"
- "infinite capacity"
- "secure because PSNR/SSIM is high"
- citations to unpublished internal manuscripts

## Minimum Q1 Standard

The approach is competitive only if it demonstrates:

1. exact recovery near 99% under at least JPEG85 plus resize0.75 for short and
   medium messages;
2. detector AUC close to chance against at least one modern deep steganalysis
   setup, with the adversary model stated clearly;
3. effective capacity reported after headers, CRC, fountain overhead, dropped
   images, and decoding failures;
4. ablations for distribution-aware sampling, stability scheduling, and the
   rateless layer;
5. fair comparison to public baselines.
