# Public Baselines for VQ-Fountain Evaluation

Status: active public-only baseline registry.

Do not include unpublished internal manuscripts in this file.

## Primary Baselines

| Baseline | Public Source | Relevance | Required Comparison |
|---|---|---|---|
| GSN: Generative Steganography Network | https://arxiv.org/abs/2207.13867 | Coverless generative steganography; generates stego images directly from secret data. | Payload recovery, image quality, steganalysis resistance, no-cover setting. |
| Cs-FNNS | https://arxiv.org/abs/2407.11405 | Uses deep generative models with cover-separable perturbation recovery. | Image quality, detectability, generated-cover assumption, whether receiver needs cover regeneration. |
| CMSteg / cross-modal error correction | https://arxiv.org/abs/2412.12206 | Robust steganography with AR/VQ image generation and auxiliary cross-modal correction. | Robustness under JPEG/social-channel processing, capacity, and whether auxiliary stego text is needed. |
| MIDAS | https://arxiv.org/abs/2603.09390 | Training-free diffusion coverless multi-image hiding with access control. | Multi-image capacity, robustness, access-control setting, steganalysis resistance. |
| Latent iterative optimization | https://arxiv.org/abs/2603.09348 | Robust provably secure latent-space refinement for lossy image channels. | Compression robustness and compute cost against iterative decoding/refinement. |
| HiDDeN | https://arxiv.org/abs/1807.09937 | Robust learned image hiding reference, not coverless. | Robustness and recovery under image transformations as a non-coverless baseline. |
| StegaStamp | https://arxiv.org/abs/1904.05343 | Robust learned watermark/steganography reference, not coverless. | JPEG/crop/print-like robustness and capacity under robust learned embedding. |
| DCT-spread | local runner | Classical transform-domain spread-spectrum hiding reference, not coverless. | Executable sanity baseline for clean/JPEG/resize/blur/crop robustness under a simple non-coverless embedder. |

## Current Reproducibility Status

| Baseline | Code Status | Local Status | Action |
|---|---|---|---|
| GSN | Not yet verified locally. | Not installed. | Search for public implementation or reimplement minimal reported protocol only if code is unavailable. |
| Cs-FNNS | Not yet verified locally. | Not installed. | Verify whether authors released code; otherwise mark as paper-only comparator. |
| CMSteg | Not yet verified locally. | Not installed. | Verify code and auxiliary-channel assumptions before fair comparison. |
| MIDAS | Not yet verified locally. | Not installed. | Verify code/model release and access-control setup. |
| Latent iterative optimization | Not yet verified locally. | Not installed. | Track as 2026 robustness comparator; verify whether code is public. |
| HiDDeN | Public implementation cloned locally. | Executable via compatibility runner with public checkpoint. | Report the measured smoke baseline only with its narrow protocol and artifact path. |
| DCT-spread | Local executable implementation. | Executable; CSV and JSON artifacts produced. | Report as a classical non-coverless transform baseline, not as a public SOTA method. |
| StegaStamp | Public implementation cloned locally. | Source present; local SavedModel/dependency audit blocks execution. | Keep as robust non-coverless paper/code comparator until SavedModel, TensorFlow, and `bchlib` are available. |

## Fairness Rules

- Report coverless and non-coverless baselines separately.
- Report whether a baseline requires an auxiliary recovery channel, regenerated
  cover, text side channel, cloud index, or image-specific metadata.
- Use equal payload first, then equal quality, then maximum reliable payload.
- Always report effective user bits per image after packet, redundancy, anchors,
  and failures.
- Separate exact payload recovery from partial bit accuracy.
- Include detector AUC/accuracy, not only image-quality scores.

## Executable Baseline Results

The current local audit records two executable non-coverless baselines:

- HiDDeN public checkpoint smoke run:
  `05_artifacts/results/tables/hidden_baseline_smoke.csv`.
  The run used a 30-bit message across five trials and produced mean bit error
  rate 0.31333333 with 0/5 exact recoveries on the selected VQGAN sample.
- DCT-spread local baseline:
  `05_artifacts/results/tables/dct_spread_baseline.csv`.
  The run used a 32-bit message, repetition 7, strength 28, and PSNR
  37.916521 dB. It recovered exactly under clean, JPEG85, resize075, and blur1,
  and failed under crop090 with bit error rate 0.5.

StegaStamp remains blocked for local scoring because the cloned public source
does not include a pretrained SavedModel and the compatible TensorFlow/BCH
runtime is not installed.

- `05_artifacts/baselines/baseline_execution_audit.json`
- `04_experiments/results/vq_fountain_public_baseline_execution_audit_2026-07-15.md`

GSN, Cs-FNNS, CMSteg, MIDAS, and latent iterative optimization remain
paper-first comparators unless public code is identified and installed.
