# VQ-Fountain Locked Claims

Date: 2026-07-16

## Claims Allowed By Current Evidence

- The method design is coverless: it does not require a cover image.
- The implemented recovery layer is in-band: packet, symbol CRC, anchors, and
  fountain symbols are recovered from received images and shared key/model
  assumptions.
- Fountain coding outperforms fixed repetition in the tested crop-offset
  channel.
- Distribution-aware projection binning outperforms naive token modulo mapping.
- Spatial block anchors support crop-ratio and 2D offset synchronization.
- On the learned patch-VQ Stage 1 channel, 64 B payload recovery is exact under
  crop0.90 with offset, JPEG, resize, blur, noise, and selected combined attacks.
- Under the hardest tested combined channel, crop + JPEG + 25% image drop, 64 B
  needs overhead 4.0 and 24 images.
- In the Stage 2 public VQGAN f4-8192 probe, conservative calibrated
  macro-cell value coding recovers:
  - 4 B exactly under clean, JPEG85, resize075, blur1, noise002, crop090,
    drop25, and crop090+jpeg85+drop25;
  - 8 B exactly under clean and crop090+jpeg85+drop25.
- With grouped 2x2 macro-cells, the Stage 2 VQGAN probe recovers 32 B exactly
  across three independent payload/test seeds under both clean and
  crop090+jpeg85+drop25 attacks.
- The 32 B grouped Stage 2 setting uses 64 coded value bits per generated
  image and 22 images at overhead 3.0.
- With grouped 2x2 macro-cells and overhead 4.0, the Stage 2 VQGAN probe
  recovers 64 B exactly across three independent payload/test seeds under both
  clean and crop090+jpeg85+drop25 attacks.
- The 64 B grouped Stage 2 setting uses 64 coded value bits per generated
  image, 48 images, and 76 packet/source symbols.
- A feature-level Stage 2 detector trained on 144 payload and 144 reference
  VQGAN images from the 64 B setting reports AUC 0.48862745 and accuracy
  0.53465347.
- A 128x128 feasibility probe recovers 16 B exactly under clean and
  crop090+jpeg85+drop25.
- A second public VQModel, `CompVis/ldm-celebahq-256/vqvae`, recovers 16 B
  exactly under clean and crop090+jpeg85+drop25.
- A local small-CNN steganalysis probe on 144 payload and 144 reference VQGAN
  images from the 64 B setting reports AUC 0.5332 and accuracy 0.57.
- A local SPAM-style residual cooccurrence steganalysis probe on 144 payload
  and 144 reference VQGAN images from the 64 B setting reports AUC 0.52627451
  and accuracy 0.5049505.
- A local SRM-style residual cooccurrence steganalysis probe on 144 payload and
  144 reference VQGAN images from the 64 B setting reports mean AUC 0.49521569
  and mean accuracy 0.49702970 across five splits.
- A HiDDeN public-checkpoint compatibility smoke run is executable locally; on
  the selected VQGAN sample it gives mean bit error rate 0.31333333 over five
  30-bit trials and 0/5 exact recoveries.
- A local DCT-spread non-coverless baseline is executable; with a 32-bit
  payload it is exact under clean, JPEG85, resize075, and blur1, but fails
  crop090 with bit error rate 0.5.
- The Stage 2 real VQGAN result is value-channel recovery, not token-ID
  preservation; token identity match is near zero.

## Claims Not Allowed Yet

- Do not claim undetectability.
- Do not claim universal robustness.
- Do not claim final SOTA superiority.
- Do not claim high payload rate beyond the measured 64 B grouped VQGAN
  setting.
- Do not claim the Stage 2 result generalizes beyond the tested public VQGAN
  checkpoints, image sizes, payload sizes, and attacks.
- Do not claim resistance to official external SRNet or third-party
  steganalysis suites; the current SRM-style result is a local
  residual-cooccurrence probe.
- Do not claim a local StegaStamp score; the current audit says its SavedModel
  and compatible runtime are unavailable.

## Manuscript Rule

Use measured numbers only. If a result is from learned patch-VQ, label it as a
Stage 1 token-channel result. If a result is from the public VQGAN f4-8192
payload probe, label it as a Stage 2 conservative real-VQGAN result.
