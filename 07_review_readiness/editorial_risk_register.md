# Editorial Risk Register

| ID | Risk | Severity | Why It Matters | Mitigation |
|---|---|---|---|---|
| R1 | The method is called coverless although it uses a cover image. | Critical | Reviewers will treat this as a conceptual contradiction. | Use "neural image steganography" unless final method removes cover input. |
| R2 | Novelty is framed as GAN-based steganography. | Critical | Prior GAN/generative/coverless methods exist. | Frame novelty around WYSAWIS auxiliary-channel elimination and reproducible protocol. |
| R3 | `models.py` is missing from artifacts. | Critical | Results cannot be reproduced. | Add full architecture code and evaluation scripts. |
| R4 | Capacity is reported as nominal 2 bpp only. | Major | Effective payload may be lower due to ECC, delimiter, padding, and failures. | Report effective bpp and exact recovery rate. |
| R5 | Security is inferred from PSNR/SSIM. | Major | Image quality metrics do not measure steganographic security. | Add steganalysis detector experiments. |
| R6 | Only one or two images are tested. | Major | No generalization evidence. | Evaluate on fixed test sets across datasets. |
| R7 | WYSAWIS comparison is qualitative only. | Major | Q1 reviewers expect fair baseline analysis. | Compare operational assumptions, capacity, repeated-segment behavior, robustness, and metadata channels. |
| R8 | Claims of robustness lack attack matrix. | Major | Robustness must be attack-specific. | Add JPEG/noise/blur/resize/crop tests. |
| R9 | Literature omits recent 2024-2026 papers. | Major | Editors may desk reject for weak positioning. | Verify and cite the direct novelty threats from Semantic Scholar. |
| R10 | Reproduced stego image has visible artifacts and low PSNR/SSIM. | Critical | Q1 reviewers will reject imperceptibility/security claims if the reproduced artifact is visually degraded. | Recover exact original encoder forward function or retrain/fine-tune with image-fidelity and steganalysis-aware losses; report the current smoke test honestly. |
| R11 | Current checkpoint fails on the second provided image. | Critical | A one-image success cannot support generalization, robustness, or high-capacity claims. | Build dataset-level training/evaluation; report failure rates; improve model before manuscript drafting. |
| R12 | V3 stego images are detectable by a simple residual/LSB classifier. | Critical | Even a lightweight detector reached test AUC above 0.93 on COCO80 and above 0.96 on Caltech80, so security/undetectability claims would be invalid. | Treat steganalysis as a primary loss/evaluation target; do not claim security until strong detectors are near chance under fair splits. |
| R13 | The current V3 model is not robust to JPEG, blur, or resizing. | Major | COCO30 exact recovery is 0/30 under JPEG95, blur1, and resize0.75 at 0.25 nominal bpp. | Either limit the paper to clean-channel recovery or add robust/synchronization-aware training and coding. |
