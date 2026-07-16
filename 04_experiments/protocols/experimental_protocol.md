# Experimental Protocol

Status: active protocol for VQ-Fountain Stega.

## Research Questions

RQ1. Can payloads be recovered from generated images without a cover image or
auxiliary recovery channel?

RQ2. How much effective payload can be recovered per image after packet headers,
CRC, fountain overhead, channel losses, and decoding failures?

RQ3. Does entropy-stability token scheduling improve recovery under JPEG,
resize, blur, noise, crop, and image loss?

RQ4. Does distribution-aware token sampling reduce steganalysis detectability
relative to naive token-bit mapping?

RQ5. How does the method compare to public coverless/generative/robust hiding
baselines under equal-payload and equal-quality conditions?

## Development Stages

Stage 0: synthetic token channel.

- No image generator.
- Simulate token distributions, token erasures, token flips, and image drops.
- Validate packet, fountain, scheduling, and accounting code.

Stage 1: fixed tokenizer path.

- Use a VQ tokenizer/re-tokenizer.
- Measure token stability after image transformations.
- Evaluate extraction from tokenized images before full generation.
- Current local baseline: `patch-vq`, a fixed patch quantizer used only to
  validate accounting before a learned VQ tokenizer is available.

Stage 2: generative path.

- Connect an autoregressive or VQ-based image generator.
- Embed bits during token sampling.
- Generate and evaluate stego images.

Stage 3: full SOTA evaluation.

- Compare against public baselines.
- Run modern steganalysis.
- Produce ablations and confidence intervals.

## Datasets

Minimum:

- COCO or equivalent natural-image distribution for prompts/conditioning and
  evaluator calibration;
- BOSSBase/BOWS2 or equivalent where steganalysis comparison is meaningful;
- at least one out-of-distribution prompt/image set.

Document source, license, version, splits, preprocessing, and duplicates.

## Payload Conditions

Report at least:

- short payload: 128 to 512 bytes;
- medium payload: 1 to 4 KB;
- stress payload: highest reliable payload found by search.

For every condition, report both nominal and effective payload.

## Transformations

Clean channel:

- no modification after generation.

Lossy channel:

- JPEG quality 95, 90, 85, 75;
- resize 0.75 and 0.50 followed by restoration to decoder size;
- Gaussian blur radius 1 and 2;
- mild Gaussian noise;
- center crop and resize;
- image drop rates 10%, 25%, 40% for multi-image payloads.

## Metrics

Recovery:

- exact payload recovery rate;
- CRC pass rate;
- raw bit error rate;
- source-symbol recovery rate;
- images needed for successful decoding;
- failure causes.

Capacity:

- nominal bits per image;
- effective user bits per image;
- overhead ratio;
- redundancy ratio.

Realism/security:

- FID/KID or equivalent generative realism metric;
- CLIP/prompt consistency if prompt conditioning is used;
- steganalysis AUC and accuracy;
- token-distribution divergence or sampler leakage score.

Efficiency:

- encode time;
- decode time;
- generator calls;
- GPU/CPU and memory.

## Baselines

Public baselines to track:

- GSN-style generative steganography;
- Cs-FNNS-style cover-separable generative steganography;
- CMSteg-style robust cross-modal correction;
- MIDAS-style diffusion coverless multi-image hiding;
- latent iterative optimization for robust provably secure generated-image
  steganography;
- HiDDeN and StegaStamp as robust learned hiding references;
- Tree-Ring-style diffusion watermarking as a robustness/security reference.

Only use baselines that can be described from public sources or reproduced from
public code/papers.

Public baseline registry: `01_references/public_baselines_vq_fountain.md`.

## Ablations

Required:

- naive token mapping vs distribution-aware sampling;
- random token positions vs entropy-only vs entropy-stability scheduling;
- no anchors vs global anchors vs spatial block anchors for crop synchronization;
- fixed ECC only vs fountain coding;
- single-image vs multi-image recovery;
- with and without image-drop redundancy.

## Statistics

- at least 3 seeds for synthetic and model-based stochastic results;
- mean, standard deviation, and confidence interval for key metrics;
- paired comparisons where the same prompts/images are used;
- all failures included in aggregate tables.
