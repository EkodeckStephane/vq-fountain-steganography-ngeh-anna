# Q1 Acceptance Gate

Status: active gate for VQ-Fountain Stega.

Before submission, every accepted claim must pass the matching gate below.

## Novelty

- The paper states a specific public SOTA gap: coverless generative image
  hiding with distribution-aware token sampling and in-band rateless recovery.
- The method does not rely on a cover image.
- Recovery does not require auxiliary stego text, cloud maps, location files, or
  unpublished side artifacts.
- The paper avoids "first" claims unless directly proven from public sources.
- The contribution is not merely "using a GAN", "using diffusion", or "using
  deep learning".

## Evidence

- Synthetic token-channel tests pass before real-model claims are made.
- Real-model experiments report exact recovery, not only BER.
- Effective payload is reported after headers, CRC, fountain overhead, image
  losses, and failures.
- Equal-payload and equal-quality comparisons are included where possible.
- Ablations isolate distribution-aware sampling, entropy-stability scheduling,
  and fountain coding.

## Robustness

- JPEG85 plus resize0.75 is treated as the first robustness gate.
- The method reports clean, JPEG, resize, blur, noise, crop, and image-drop
  results.
- Failures are included in aggregate metrics.
- Robustness claims are limited to tested transformations and payload ranges.

## Security

- The adversary model is explicit.
- PSNR/SSIM are not used as security proof.
- At least one modern steganalysis setup is reported.
- Token-distribution shift or sampler leakage is measured.
- Security claims are bounded by the tested detectors.

## Reproducibility

- Code runs from documented commands.
- Dependencies and versions are fixed.
- Seeds are recorded.
- Data splits are published or exactly reconstructible.
- Scripts regenerate tables from raw outputs.

## Writing

- No claim of "perfect", "maximum", "undetectable", or "universal" without
  formal proof and experiments.
- Internal unpublished manuscripts are not cited.
- Limitations are explicit and placed before reviewer objection would force
  them into the discussion.
