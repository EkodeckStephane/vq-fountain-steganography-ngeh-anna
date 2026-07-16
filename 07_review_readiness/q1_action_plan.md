# Q1 Action Plan

Status: legacy ETHEGAN action plan. Use
`07_review_readiness/q1_acceptance_gate.md` for the active VQ-Fountain gate.

Objective:

Prepare a manuscript that can withstand a senior Q1/rank-A review by ensuring that every major claim is novel, precisely scoped, experimentally supported, reproducible, and aligned with the literature.

Target decision:

- realistic target: major revision reduced to minor revision after strong pre-submission hardening;
- aspirational target: minor revision at first submission;
- do not assume acceptance without full evidence.

## Phase 1 - Freeze the Scientific Position

Goal:

Prevent desk rejection or "lack of novelty".

Actions:

1. Use the working positioning:
   > Reliability-aware auxiliary-channel-free neural image steganography addressing WYSAWIS auxiliary-channel and repeated-segment artifact limitations through self-contained packet recovery.
2. Avoid unsafe wording until proven:
   - first;
   - coverless;
   - undetectable;
   - perfect extraction;
   - robust to JPEG;
   - maximum security;
   - infinite capacity.
3. Define exactly what is shared between sender and receiver:
   - model weights;
   - optional key/seed if used;
   - no cloud metadata;
   - no external location channel.
4. Decide whether the final method is:
   - neural cover-image steganography; or
   - true coverless/generative steganography.

Deliverables:

- `02_novelty/recommended_orientation.md`
- `02_novelty/decision_log.md`
- final title and contribution wording

Reviewer risk addressed:

- lack of novelty;
- overclaiming;
- conceptual contradiction between "coverless" and cover-image input.

Acceptance gate:

- A reviewer must be able to state the novelty in one sentence without comparing it to generic GAN steganography.

## Phase 2 - Audit the Literature Before Writing

Goal:

Make the related work strong enough that editors cannot say the article ignores recent competitors.

Actions:

1. Verify the direct novelty threats found through Semantic Scholar:
   - Generative Steganography Network, ACM MM 2022;
   - Coverless Image Steganography Based on GAN, 2020;
   - IDGAN, 2023;
   - GAN anime coverless steganography, 2024;
   - Robust Generative Steganography Based on Image Mapping, IEEE TCSVT 2024;
   - Cover-separable Fixed Neural Network Steganography, ACM MM 2024;
   - invertible neural network + GAN steganography, Signal Processing 2025;
   - robust/diverse coverless steganography against passive and active steganalysis, IEEE TDSC 2025;
   - StyleStego, 2026.
2. For each paper, record:
   - DOI;
   - venue;
   - method type;
   - payload/capacity;
   - robustness tests;
   - steganalysis tests;
   - need for auxiliary information;
   - reproducibility status.
3. Build the gap table for the introduction.
4. Separate papers into:
   - direct baselines;
   - related but not comparable;
   - steganalysis tools;
   - datasets/protocol references.

Deliverables:

- `01_references/primary/verified_references.md`
- gap table for manuscript
- baseline selection memo

Reviewer risk addressed:

- selective citation;
- obsolete baselines;
- false novelty claim;
- unsupported "to the best of our knowledge".

Acceptance gate:

- Every novelty claim must cite the closest competing work and explain the exact difference.

## Phase 3 - Rebuild the Method as a Precise System

Goal:

Make the method auditable and avoid ambiguity between idea, specification, prototype, and validation.

Actions:

1. Recover or implement the missing `models.py`.
2. Document the exact architecture:
   - hiding network;
   - extractor network;
   - discriminator if used;
   - ECC layer;
   - payload length handling;
   - image preprocessing.
3. Define formal inputs/outputs:
   - sender input;
   - receiver input;
   - transmitted object;
   - shared assumptions.
4. Separate:
   - nominal payload;
   - effective user payload;
   - ECC overhead;
   - delimiter/metadata overhead.
5. Define failure modes:
   - payload too large;
   - extraction error;
   - ECC failure;
   - image transformation failure.

Deliverables:

- `03_method/method_specification.md`
- complete code under `05_artifacts/code/`
- architecture diagram
- algorithm pseudocode

Reviewer risk addressed:

- method only specified, not implemented;
- hidden assumptions;
- unclear capacity;
- irreproducible architecture.

Acceptance gate:

- A reviewer can reproduce the sender and receiver pipeline from the paper and artifact without asking for missing code.

## Phase 4 - Build a Q1 Experimental Protocol

Goal:

Generate evidence that directly answers the manuscript claims.

Actions:

1. Evaluate multiple payload rates:
   - 0.25 bpp;
   - 0.5 bpp;
   - 1.0 bpp;
   - 2.0 bpp if stable.
2. Use multiple datasets:
   - natural image dataset;
   - steganography-oriented dataset if available;
   - out-of-distribution dataset.
3. Report core metrics:
   - effective bpp;
   - raw BER;
   - corrected BER;
   - BCR;
   - exact-message recovery rate;
   - PSNR;
   - SSIM;
   - LPIPS;
   - encoding/decoding time.
4. Run robustness tests:
   - JPEG compression;
   - Gaussian noise;
   - salt-and-pepper noise;
   - blur;
   - resizing;
   - cropping.
5. Run repeated-payload stress tests:
   - random payload;
   - repeated 15-bit segments;
   - repeated long text;
   - structured text payload.
6. Compare with baselines:
   - WYSAWIS for operational assumptions and capacity;
   - at least one neural/deep steganography baseline;
   - one recent generative/coverless baseline if reproducible.

Deliverables:

- `04_experiments/protocols/experimental_protocol.md`
- raw result CSV files
- scripts generating tables and figures

Reviewer risk addressed:

- insufficient experiments;
- unfair baselines;
- single-image demonstration;
- unsupported robustness;
- capacity overclaim.

Acceptance gate:

- Each table must answer one research question and support one manuscript claim.

## Phase 5 - Add Security and Steganalysis Evidence

Goal:

Avoid the common fatal flaw: treating PSNR/SSIM as security proof.

Actions:

1. Define the adversary:
   - passive observer;
   - active image transformer;
   - access/no access to model;
   - access/no access to cover image;
   - access/no access to payload distribution.
2. Define what security is not claimed.
3. Evaluate detectability:
   - at least one modern deep steganalysis detector if feasible;
   - detector AUC/accuracy/FPR/FNR;
   - train/test separation by image.
4. Compare random payloads and repeated payloads.
5. Discuss leakage:
   - image distortion;
   - file size;
   - payload length;
   - model sharing;
   - ECC structure.

Deliverables:

- threat model section
- steganalysis result table
- limitations section

Reviewer risk addressed:

- "secure" without security model;
- overclaiming undetectability;
- no steganalysis baseline.

Acceptance gate:

- The paper never uses visual quality as a substitute for security.

## Phase 6 - Make the Artifact Reproducible

Goal:

Prevent reproducibility rejection.

Actions:

1. Package code:
   - training;
   - embedding;
   - extraction;
   - evaluation;
   - plotting.
2. Fix dependencies:
   - Python version;
   - PyTorch version;
   - CUDA/CPU notes;
   - requirements file.
3. Publish or prepare archive:
   - code;
   - weights;
   - fixed splits;
   - payload examples;
   - raw results;
   - scripts to regenerate tables.
4. Record:
   - seeds;
   - hardware;
   - runtime;
   - dataset versions.

Deliverables:

- `05_artifacts/code/`
- `requirements.txt`
- artifact README
- reproducibility checklist

Reviewer risk addressed:

- code unavailable;
- private/incomplete artifact;
- results not regenerable;
- missing dependencies.

Acceptance gate:

- A third party can run one command per experiment group and regenerate the tables.

## Phase 7 - Draft With the Promises-Evidence Matrix

Goal:

Ensure the paper says only what it proves.

Actions:

1. Fill `07_review_readiness/promises_evidence_matrix.md` before writing the abstract.
2. Write the title last, after results.
3. For every contribution, identify:
   - closest prior work;
   - exact limitation;
   - evidence table/figure;
   - limitation.
4. Keep limitations explicit:
   - image transformations that break extraction;
   - payload rates where BER rises;
   - detector conditions;
   - compute cost;
   - model-sharing assumptions.

Deliverables:

- final promises-evidence matrix
- manuscript draft
- limitations section

Reviewer risk addressed:

- conclusion stronger than results;
- abstract overclaim;
- missing limitations;
- decorative theory.

Acceptance gate:

- No sentence in title, abstract, contributions, or conclusion is unsupported by a table, figure, proof, or explicit limitation.

## Phase 8 - Run an Internal Senior Reviewer Simulation

Goal:

Apply the provided reviewer prompt before submission.

Actions:

1. Review the complete paper as if recommending reject.
2. Fill:
   - calibration;
   - promises-evidence matrix;
   - coherence check;
   - math/algorithm check;
   - experimental validity;
   - statistics;
   - reproducibility;
   - bibliography audit;
   - novelty audit.
3. Classify every defect:
   - critical;
   - major;
   - minor;
   - clarification.
4. Fix all critical and major issues before submission.

Deliverables:

- internal review report
- final defect table
- response-ready correction log

Reviewer risk addressed:

- discovering fatal weaknesses after submission.

Acceptance gate:

- Internal recommendation must be at least "minor revision" before external submission.

## Immediate Next Tasks

1. Verify the top 10 direct novelty-threat papers from Semantic Scholar.
2. Decide final terminology: "neural image steganography" unless cover input is removed.
3. Recover or rebuild missing `models.py`.
4. Package current prototype under `05_artifacts/code/`.
5. Run a small smoke test: embed/extract on the provided image and payload.
6. Build the first evaluation script for BER, PSNR, SSIM, effective bpp.
7. Create a WYSAWIS comparison table focused on auxiliary channel, redundancy, capacity, and robustness.
8. Fill the first version of the gap table.
9. Draft the threat model.
10. Only then draft the abstract.
