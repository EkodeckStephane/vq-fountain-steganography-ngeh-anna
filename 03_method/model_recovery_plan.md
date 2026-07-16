# Model Recovery and V2 Training Plan

Status: legacy ETHEGAN recovery plan. Do not use as the active work plan unless
explicitly reviving ETHEGAN.

## Current Finding

The checkpoint `ETEHGAN.pt` loads successfully with the reconstructed `DenseEncoder512` and `DenseDecoder512` architecture.

Verified:

- all encoder keys match;
- all decoder keys match;
- payload extraction succeeds on `000000001503.jpg`;
- payload extraction fails on `dog_0031.jpg`;
- reproduced stego images have visible artifacts and low PSNR/SSIM.

This means the current artifact is not Q1-ready.

## Hypotheses

H1. The exact original forward function is still missing.

- Evidence: checkpoint stores `psnr ~= 29.92`, but reproduced forward pass gives much lower PSNR.
- Action: search for original training code, notebooks, or model definition.

H2. The checkpoint is optimized primarily for extraction, not image quality.

- Evidence: exact recovery on one sample but visible artifacts.
- Action: fine-tune with stronger image fidelity and steganalysis-aware losses.

H3. The reported PSNR was computed under a different protocol.

- Evidence: no original evaluation script is present.
- Action: require reproducible metric scripts before using any README metric.

## Recovery Attempts Already Performed

1. Reconstructed state_dict-compatible architecture.
2. Tested direct output variants:
   - `tanh(raw)`;
   - `raw.clamp(-1, 1)`;
   - `cover + raw`;
   - scaled residual variants.
3. Tested activation variants:
   - ReLU;
   - LeakyReLU;
   - ELU;
   - SELU;
   - Tanh.

None recovered both high PSNR and reliable extraction.

## V2 Training Direction

If original code cannot be recovered, train a new version with explicit objectives:

```text
L_total =
  lambda_extract * BCEWithLogits(decoded_bits, payload_bits)
  + lambda_image * MSE(stego, cover)
  + lambda_perceptual * LPIPS/VGG_loss(stego, cover)        [optional]
  + lambda_robust * BCEWithLogits(decoder(attack(stego)), payload_bits)
  + lambda_adv * adversarial_loss                           [optional]
```

Start without adversarial loss. A stable extractor-quality baseline is more important than a complex GAN claim.

## Minimum V2 Milestones

M1. Train/evaluate at 0.25 bpp with exact recovery and PSNR > 35 dB on held-out images.

M2. Train/evaluate at 0.5 bpp with exact recovery and PSNR > 32 dB.

M3. Train/evaluate at 1.0 bpp with quantified trade-off.

M4. Attempt 2.0 bpp only after lower rates are stable.

M5. Add robustness layer after the clean-channel baseline is stable.

## V2 Progress

Implemented:

- residual encoder mode;
- useful-bit weighted loss;
- random, mixed, and zero-tail payload modes;
- multi-root local dataset loading;
- random-payload evaluation;
- robustness evaluation;
- fixed-size text packet embedding/extraction with chunked Reed-Solomon.

Best current clean-channel checkpoint:

`05_artifacts/models/etehgan_v2_residual02_025_caltech20_coco20_e3.pt`

Current limitation:

Clean-channel low-payload results are promising, but JPEG/blur/resize robustness is poor and exact text recovery is not yet general across images.

## Manuscript Consequence

Do not draft the abstract or claim high imperceptibility until M1-M3 are supported on a real test set.
