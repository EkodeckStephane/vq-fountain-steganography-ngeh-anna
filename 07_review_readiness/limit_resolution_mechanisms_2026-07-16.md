# Mechanisms to Lift Remaining Limits - 2026-07-16

Scope: ETHEGAN manuscript in `paper/main.tex`.

## Executive Position

The remaining limits cannot all be removed by wording. They require new
experiments and, for robustness/security/coverless claims, likely method-level
changes. The safest target is a two-track strategy:

1. strengthen ETHEGAN as a clean-channel auxiliary-channel-free method;
2. develop a second robust/coverless variant if the paper must claim robustness
   or coverless steganography.

## Limit Closure Table

| Limit | Mechanism | Experiment to run | Acceptance gate | Claim unlocked |
|---|---|---|---|---|
| No reproduced SOTA baseline | Reproduce at least HiDDeN, StegaStamp, and one generative/fixed-network method under equal effective payload where possible. | Run baselines on the same Caltech/COCO splits, attacks, PSNR/SSIM, exact recovery. | Table includes success/failure, effective bpp, quality, robustness, and code status for each baseline. | Fair comparative positioning; not necessarily SOTA superiority. |
| No security proof | Add stronger steganalysis: SRM/SPAM-style features, small CNN, and if feasible SRNet/Ye-Net-style detector. | Train/test detectors with grouped image splits, multiple seeds, and held-out datasets. | AUC near 0.5 for weak claim, or explicit failure if AUC remains high. | Only bounded resistance to tested detectors. |
| JPEG/blur/resize failure | Add attack-channel training plus synchronization-aware decoding. Use differentiable JPEG, blur, resize, random crop, and spatial jitter during training. | Evaluate clean, JPEG95/90/80, blur1, resize0.75, crop0.90, and combined attacks. | Exact recovery above a predefined threshold, e.g. >=95/100, at stated effective bpp. | Robustness only for tested attacks and payload. |
| Decoder desynchronization | Add image-space synchronization markers or block-level packet repetition with local coordinate recovery. Alternative: embed in DCT/wavelet blocks aligned to compression. | Test resize/crop/blur with and without synchronization module. | Synchronization module improves exact recovery under resize/crop without unacceptable detectability. | Robust-channel packet recovery. |
| COCO failures at high payload | Use adaptive ECC and reliability-aware rate selection per image. Select ECC-64/ECC-128/ECC-192 based on predicted reliability. | Evaluate per-image predicted reliability versus exact recovery on larger COCO subset. | No CRC failures at selected effective bpp; report realized average effective bpp. | Reliable clean-channel recovery with adaptive capacity. |
| Detectability remains high | Use distortion-adaptive embedding: texture masks, residual-cost maps, adversarial detector ensemble, and residual-statistics losses. | Compare residual 0.18 stat/adv against texture-aware/adaptive masks. | Lower AUC without loss of exact recovery; ideally AUC reduction across both Caltech and COCO. | Artifact-reduction claim, possibly detector-bounded security if strong detectors pass. |
| Generalization limited | Expand datasets and splits. Use COCO train/val, BOSSBase/BOWS2 or ALASKA-style image sets if available, and multiple random seeds. | At least 3 model training seeds and 3 split seeds. | Mean + confidence intervals for exact recovery, BER, PSNR, SSIM, AUC. | Generalization across tested datasets. |
| No multi-seed training | Make training deterministic and run 3 independent seeds. | Train final checkpoint 3 times with fixed config. | Confidence intervals reported; no seed collapses. | Stability of method. |
| Not coverless | Either stop trying to claim coverless, or pivot to a generative/token method. Candidate mechanisms: diffusion coverless, VQ-token in-band recovery, or VQ-Fountain style multi-image generation. | Separate coverless experiment using generated images only, no cover image at sender. | Receiver recovers payload from generated image(s) without original cover and without external metadata. | Coverless claim for the new variant only. |
| No confidentiality | Add authenticated encryption before packetization: XChaCha20-Poly1305 or AES-GCM. Keep ECC outside encryption if needed for channel correction. | Round-trip encrypted payload; wrong key fails authentication. | Correct key recovers exact plaintext; wrong key yields authenticated failure. | Confidential payload transport, separate from steganographic security. |
| Model sharing assumption | Package public model weights and derive packet interleaving/key schedule from a shared secret. | Test extraction with public weights + correct/incorrect key. | Correct key succeeds; incorrect key fails CRC/AEAD. | Clear deployment model. |
| No public artifact | Freeze code, data split manifests, hashes, model checkpoints, and scripts; archive on Zenodo/OSF/GitHub release. | One-command regeneration of all paper tables. | Independent rerun regenerates CSV tables within tolerance. | Reproducibility claim. |

## Method-Level Mechanisms

### 1. Robust Channel Layer

Implement a channel simulator during training:

- differentiable JPEG approximation;
- Gaussian blur;
- resize down/up;
- crop and pad;
- mild noise;
- color quantization.

The decoder should train on both clean and attacked images. HiDDeN is the
closest classical learned reference for this idea; it reports robustness by
training with differentiable approximations for non-differentiable JPEG.

### 2. Synchronization-Aware Packet Recovery

Add redundancy at block level:

- repeat packet header in multiple spatial regions;
- use block CRC so valid blocks can be selected independently;
- add local coordinate markers or learned anchor maps;
- interleave bytes across blocks so a local failure does not destroy a whole
  Reed--Solomon chunk.

This directly targets resize/crop/blur failures, which are currently
desynchronization problems as much as bit-error problems.

### 3. Adaptive ECC and Rate Control

The current ECC-128 result already shows that reliability can be bought with
capacity. Turn this into a method:

- estimate per-image reliability from decoder logit margins;
- choose ECC parity bytes per image;
- report realized effective bpp, not requested bpp;
- reject images predicted to be unreliable.

This can remove clean-channel CRC failures without pretending all images carry
the same usable payload.

### 4. Steganalysis-Aware Training

The existing stat/adv run is a first step. Strengthen it with:

- texture-aware embedding masks;
- residual-cost maps;
- a detector ensemble in training;
- explicit penalty on LSB and residual co-occurrence shift;
- validation gate on grouped-detector AUC, not just BER.

RFNNS is relevant here because it uses texture-aware localization for quality
and robustness. DiffStega/MIDAS are relevant if the strategy pivots toward
coverless generative carriers.

### 5. Baseline Reproduction

Minimum baseline ladder:

1. HiDDeN: learned robust hiding baseline.
2. StegaStamp: robust low-payload learned watermark/steganography baseline.
3. DCT-spread or another classical transform-domain baseline.
4. One recent generative/fixed-network method if executable code is available.

For each baseline, report:

- effective bpp;
- payload bytes;
- exact recovery;
- BER;
- PSNR/SSIM;
- attacks;
- detector AUC;
- whether code/checkpoints are public and executable.

## Acceptance Gates Before Upgrading Claims

- **Clean reliability**: >=95/100 exact recovery on both datasets at the stated
  effective bpp, or 100/100 if claiming exact reliability.
- **Robustness**: >=95/100 exact recovery under each named transformation.
- **Detector-bounded security**: AUC close to chance on at least one classical
  and one neural detector, across grouped splits.
- **Generalization**: at least three training seeds and larger held-out subsets.
- **SOTA comparison**: at least one reproduced public baseline under equal or
  clearly normalized effective payload.
- **Coverless**: no cover image used at sender; otherwise do not use the claim.

## Sources Used For Mechanism Selection

- HiDDeN: https://arxiv.org/abs/1807.09937
- StegaStamp: https://arxiv.org/abs/1904.05343
- Cross-modal robust steganography: https://arxiv.org/abs/2412.12206
- RFNNS: https://arxiv.org/abs/2505.04116
- DiffStega: https://arxiv.org/abs/2407.10459
- MIDAS: https://arxiv.org/abs/2603.09390
- CNN steganalysis reference: https://arxiv.org/abs/1807.11428
