# Anti-"Lack of Novelty" Strategy

Status: historical ETHEGAN strategy. Reuse only the claim-discipline rules;
the active method is VQ-Fountain Stega.

## What Editors May Reject

Editors may reject the article for insufficient novelty if it is presented as:

- another GAN steganography model;
- a SteganoGAN-like encoder-decoder with different wording;
- a coverless method that still needs a cover image;
- a high-capacity claim supported only by one image and one payload;
- a WYSAWIS extension without a concrete replacement of the cloud channel;
- a paper that ignores recent generative and invertible steganography work.

## Required Defensive Moves

### 1. Narrow the Claim

Do not compete on "first GAN." Compete on:

- removal of WYSAWIS auxiliary channel;
- global payload encoding;
- repeated-segment leakage removal;
- benchmark rigor.

### 2. Build a Gap Table

The introduction must include a table with columns:

- Method
- Cover modification / cover selection / cover synthesis / neural embedding
- Requires auxiliary metadata channel
- Handles repeated segments without observable repetition
- Effective bpp
- Robustness tested
- Deep steganalysis tested
- Public reproducible artifacts

The row for ETEHGAN must be true and experimentally supported.

### 3. Add Ablations

Minimum ablations:

- with vs without ECC
- with vs without robustness/noise layer
- different payload rates
- different cover datasets
- repeated vs random payloads
- model trained on one dataset and tested on another

### 4. Separate Nominal and Effective Capacity

A Q1 reviewer will reject "2 bpp" if ECC, delimiter, padding, or failures reduce practical payload.

Report:

- nominal capacity
- user payload capacity
- ECC overhead
- delimiter/metadata overhead
- exact recovery rate

### 5. Include Steganalysis

PSNR and SSIM are not security metrics.

At least one modern detector must be evaluated. If a strong detector is not implemented, the claim must be downgraded from "secure" to "visually imperceptible under distortion metrics."

### 6. Make the Artifact Complete

The current prototype is incomplete because `models.py` is absent.

Before submission:

- include full architecture code;
- include weights or training recipe;
- include deterministic evaluation scripts;
- include data split files;
- include commands that regenerate every table.
