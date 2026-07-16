# Execution Status - 2026-07-13

## Completed

1. Workspace reorganized into article-oriented folders.
2. WYSAWIS copied into verified primary references.
3. Semantic Scholar queried with the provided API key; 60 results collected, 34 unique titles.
4. Critical novelty-threat papers verified via Crossref.
5. First gap table created.
6. `models.py` reconstructed from `ETEHGAN.pt`.
7. Original scripts patched to remove `torchvision` dependency.
8. Console logs made Windows-safe by removing non-ASCII status icons.
9. Exact newline preservation added for byte-perfect payload recovery.
10. Minimal reproducible artifact packaged under `05_artifacts/`.
11. Smoke test on `000000001503.jpg` completed:
    - exact payload recovery: true;
    - effective user payload: 1.7490 bpp;
    - raw BER before ECC: 0.00048828125;
    - PSNR: 14.1911 dB;
    - global SSIM: 0.3504.
12. Smoke test on `dog_0031.jpg` completed:
    - exact payload recovery: false;
    - raw BER before ECC: 0.0020790100;
    - PSNR: 12.7822 dB;
    - global SSIM: 0.3014.
13. Threat model drafted.
14. WYSAWIS comparison table drafted.
15. V2 training smoke script implemented and executed.
16. Residual V2 encoder path added.
17. V2 random-payload and robustness evaluation scripts added.
18. V2 text payload embed/extract scripts added with fixed chunked Reed-Solomon packets.
19. Local Caltech101 and COCO val2017 image folders discovered and used without copying data.
20. Mixed Caltech20+COCO20 V2 checkpoint trained and evaluated.
21. Pivot to ETEHGAN v3 reliability-aware packet layer accepted.
22. V3 packet code implemented:
    - header with magic/version, payload length, CRC32, configuration ID;
    - chunked Reed-Solomon coding;
    - deterministic interleaving;
    - optional erasure decoding from decoder-logit reliability.
23. V3 end-to-end embed/extract scripts added and tested.
24. Initial V3 clean-channel packet experiments completed on sample images, Caltech101 offset 20, and COCO val2017 offset 20.
25. V3 clean-channel curves extended to 50-image Caltech101 and COCO subsets at 0.05, 0.10, and 0.25 nominal bpp.
26. V3 COCO30 attack matrix completed at 0.25 nominal bpp.
27. Simple residual/LSB steganalysis sanity detector implemented and run on Caltech80 and COCO80.
28. Residual-strength 0.1 variant trained with stronger image penalty.
29. Residual 0.1 variant evaluated for exact recovery and simple steganalysis.
30. Residual-strength 0.15 variant trained and evaluated.
31. Residual 0.15 recovery fine-tune trained and evaluated.
32. Reliability-aware erasure decoding tested on residual 0.15 fine-tune COCO50; no improvement observed.
33. Residual-strength 0.18 variant trained and evaluated.
34. Residual 0.18 passed Caltech50/COCO50 exact-recovery gate but did not improve simple steganalysis AUC.
35. Statistical residual regularization implemented in `steg_losses.py`.
36. Residual-domain adversarial discriminator implemented in `models.py`.
37. Steganalysis-aware training script implemented in `train_v3_stegaware.py`.
38. First steganalysis-aware 0.18 checkpoint trained and evaluated.
39. Attack-aware training script implemented in `train_attack_aware.py` with
    resumable checkpoint support.
40. Interrupted attack-aware 0.05 bpp run resumed to epoch 2 and evaluated on
    held-out Caltech20/COCO20 attack checks.

## Critical Findings

The original checkpoint is not Q1-ready.

It demonstrates that payload extraction can work on one sample, but it does not support claims of:

- generalization;
- imperceptibility;
- robustness;
- steganographic security;
- publication-grade high-capacity performance.

The V2 residual direction is more promising but still preliminary. At 0.25 bpp, a mixed Caltech20+COCO20 checkpoint reached clean-channel useful BER below 0.25% on small held-out subsets with PSNR around 36 dB. Robustness remains poor under JPEG, blur, and resizing.

The V3 packet pivot is more promising than the earlier high-capacity framing.
At 0.25 bpp nominal, the current packet layer obtained 20/20 exact clean-channel
recoveries on Caltech101 offset 20 and 20/20 on COCO val2017 offset 20, with
0.185546875 bpp effective user payload after packet/ECC overhead. This is still
not a Q1-ready result because the subsets are small, baselines are missing, and
JPEG/blur/resize robustness is not achieved.

Scaled V3 testing strengthens and narrows this conclusion. At 0.25 bpp nominal,
the system reached 50/50 exact clean-channel recovery on Caltech101 offset 20
and 50/50 on COCO val2017 offset 20. However, it failed under JPEG95, blur1, and
resize0.75 on COCO30, and a simple residual/LSB detector reached test AUC
0.930625 on COCO80 and 0.965625 on Caltech80. Therefore, clean-channel exact
recovery is promising, but security and robustness are not demonstrated.

## Next Required Work

1. Expand V3 packet experiments to larger held-out Caltech101/COCO subsets.
2. Add equal-payload/equal-quality comparisons against strong baselines.
3. Add standard SSIM/LPIPS and steganalysis evaluation.
4. Decide whether the article will include robust training or explicitly limit claims to clean-channel exact recovery.
5. Run dataset-level experiments with train/validation/test splits and fixed seeds.
6. Complete full-paper audits of the direct novelty-threat references.

Immediate model-development priority:

Reduce detectable residual artifacts while preserving V3 exact recovery. The
next training run should include lower residual strength and/or residual-domain
regularization, then rerun exact recovery and steganalysis before adding any
new claims.

Residual 0.1 follow-up:

The residual 0.1, lambda-image 30 variant improved PSNR by roughly 3.7-4.0 dB
and lowered simple steganalysis AUC, but reduced COCO50 exact recovery from
50/50 to 41/50. It should not replace the residual 0.2 baseline. The next
training point should target residual strength 0.12-0.15 or use a curriculum
that preserves exact recovery before lowering detectability.

Residual 0.15 follow-up:

Residual 0.15 improved the trade-off but still failed the replacement gate.
The image-20 variant reached 48/50 exact recovery on COCO50, with COCO simple
detector AUC reduced from 0.930625 to 0.888125. A recovery fine-tune reduced raw
BER but still remained at 48/50, and reliability-aware erasures did not recover
the failed images. Residual 0.2 remains the current main baseline.

Residual 0.18 follow-up:

Residual 0.18 passed the exact-recovery gate with 50/50 on Caltech50 and 50/50
on COCO50. It improved PSNR over residual 0.2 by about 1.55 dB on Caltech and
1.20 dB on COCO. However, simple steganalysis AUC did not improve reliably
(COCO AUC 0.936250 vs 0.930625 baseline; Caltech AUC 0.961250 vs 0.965625).
Residual 0.18 is the current best quality-fiability checkpoint, but not a
security improvement.

Steganalysis-aware follow-up:

The first `stegaware` checkpoint preserves exact recovery with 50/50 on
Caltech50 and 50/50 on COCO50. It improves PSNR relative to residual 0.18 and
reduces COCO simple-detector AUC from 0.936250 to 0.918125. Caltech AUC remains
high at 0.963750. This is the current best quality-recovery-detectability
checkpoint, but it still does not support security or undetectability claims.

Attack-aware follow-up:

The small `attackaware` checkpoint at 0.05 nominal bpp and ECC-128 preserves
20/20 clean-channel recovery on held-out Caltech20 and COCO20, with higher PSNR
because the effective user payload falls to 0.0222778320 bpp. It still obtains
0/20 exact recovery under JPEG95, blur1, and resize0.75 on both datasets.
Therefore, the attack-aware surrogate fine-tune does not support robustness
claims and should not replace the current manuscript checkpoint.
