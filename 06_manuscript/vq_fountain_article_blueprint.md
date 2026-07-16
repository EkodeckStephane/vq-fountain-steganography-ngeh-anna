# VQ-Fountain Article Blueprint

Status: active blueprint.

## Provisional Title

VQ-Fountain Steganography: Distribution-Preserving Coverless Image Generation
with In-Band Rateless Recovery

## Abstract Logic

1. State the gap: existing generative, robust, and watermark-like methods do not
   jointly provide coverless generation, distribution-aware token embedding,
   no auxiliary recovery channel, and rateless multi-image recovery.
2. State the method: VQ-Fountain embeds fountain-coded payload symbols through
   key-conditioned VQ token choices selected by entropy and channel stability.
3. State the evaluation: exact recovery, effective bits per image, robustness,
   realism, steganalysis, and ablations.
4. State measured results only after experiments are complete.

## Section Plan

1. Introduction
   - operational problem;
   - public SOTA gap;
   - contributions and claim boundaries.

2. Related Work
   - generative and coverless steganography;
   - robust learned data hiding;
   - diffusion/VQ watermarking;
   - steganalysis and distribution preservation;
   - rateless and error-correcting payload recovery.

3. Threat and Channel Model
   - passive observer;
   - image-processing channel;
   - no auxiliary recovery channel;
   - shared key/model assumptions.

4. Method
   - payload packet;
   - fountain coding;
   - entropy-stability token scheduling;
   - distribution-aware token sampling;
   - receiver and decoding.

5. Experiments
   - synthetic token channel;
   - tokenizer stability;
   - external dataset token stability;
   - ablations: fountain vs repetition, projection vs naive mapping, global vs
     block anchors, center vs random scheduling;
   - real generative model;
   - robustness matrix;
   - combined attacks and image drops;
   - steganalysis;
   - ablations.

6. Results
   - exact recovery and effective capacity;
   - robustness;
   - security/detectability;
   - realism and compute;
   - failure analysis.

7. Limitations
   - tested generator/tokenizer only;
   - bounded transformations;
   - detector coverage;
   - payload/quality trade-off;
   - compute and model availability.

## Contribution Wording

Use:

1. We formulate payload-bearing VQ generation as distribution-aware constrained
   sampling.
2. We introduce an in-band fountain recovery layer for coverless generative
   steganography.
3. We propose entropy-stability token scheduling for lossy image channels.
4. We provide a reproducible effective-capacity and exact-recovery evaluation.

Current claim lock: `06_manuscript/vq_fountain_claims_locked_2026-07-15.md`.

Avoid:

- "undetectable";
- "perfectly secure";
- "first generative steganography";
- "robust to any transformation";
- citations to unpublished internal manuscripts.
