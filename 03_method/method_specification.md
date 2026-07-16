# Method Specification

Working name: VQ-Fountain Stega.

## Objective

Build a coverless generative image steganography method that hides a message in
the token choices of a VQ/autoregressive image generator and recovers it through
an in-band rateless fountain layer.

The sender should not require a cover image. The receiver should not require an
auxiliary stego text, cloud location map, external index file, or private
unpublished artifact.

## System Model

Inputs:

- secret payload bytes;
- shared key or seed;
- public generator/tokenizer configuration;
- optional prompt or public conditioning signal;
- target number of images or target recovery probability.

Sender:

1. Compress or normalize the payload if enabled.
2. Add payload length, version, CRC, and experiment metadata.
3. Split the payload into source blocks.
4. Generate rateless coded symbols.
5. Select token positions by entropy and channel-stability scores.
6. Embed coded bits by key-conditioned distribution-aware token sampling.
7. Generate one or more stego images.

Receiver:

1. Tokenize or invert each received image into VQ tokens.
2. Recompute the keyed schedule from public metadata and shared key.
3. Extract coded-symbol bits from selected token choices.
4. Use the fountain decoder to recover the payload.
5. Validate CRC and payload length.

## Core Components

1. Packet layer
   - version field
   - payload length
   - CRC32
   - source block size
   - symbol id
   - image id
   - optional experiment id

2. Fountain layer
   - rateless encoded symbols from source blocks
   - GF(2) decoder for XOR equations
   - configurable redundancy target
   - recorded decode status and CRC result
   - symbol-level CRC so corrupted equations can be converted to erasures

3. Token scheduler
   - entropy threshold from model logits
   - empirical stability score under transformations
   - keyed pseudo-random ordering
   - forbidden-token and prompt-safety masks where needed
   - current local baseline uses learned patch-VQ stability until a VQGAN/AR
     tokenizer is connected
   - simple center scheduling was tested for crop, but crop0.90 still requires
     stronger geometric synchronization; high-redundancy crop-ratio search
     provides a first patch-token exact-recovery proof of concept, global
     anchors provide non-payload ratio selection, and spatial block anchors
     with 2D ratio/offset search improve the current crop operating point

4. Distribution-aware sampler
   - candidate set from high-probability VQ tokens
   - keyed partition or arithmetic-style coding interface
   - payload bits mapped to token alternatives with bounded distribution shift
   - leakage score recorded for each token decision
   - current local sampler uses balanced global prior bins and projection-based
     grouping as a patch-token baseline

5. Channel simulator
   - JPEG
   - resize
   - blur
   - noise
   - crop
   - image drop
   - token erasure/flip synthetic mode for early testing

## Non-Negotiable Reporting

- nominal bits per image;
- effective user bits per image after all overhead and failures;
- raw symbol error/erasure rate;
- exact payload recovery after CRC;
- number of images needed for recovery;
- image realism or fidelity metrics appropriate to generative images;
- steganalysis detector AUC/accuracy;
- robustness matrix under each transformation;
- compute cost.

## Claim Boundaries

Do not claim:

- perfect security;
- universal robustness;
- undetectability;
- robustness to transformations not tested;
- coverless operation if a cover image is introduced later;
- auxiliary-channel-free operation if recovery needs external side metadata.
