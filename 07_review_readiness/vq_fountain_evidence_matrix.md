# VQ-Fountain Promises-Evidence Matrix

Status: active matrix. Fill with experiment identifiers as work progresses.

| Promise | Where It May Appear | Evidence Required | Current Status | Decision |
|---|---|---|---|---|
| P1: The method is coverless. | Title, abstract, method | Sender does not use a cover image; generation starts from model conditioning, key, and payload. | Real diffusion and VQModel smoke tests pass with public models; Stage 2 real VQGAN payload probe recovers 4 B, 8 B, 16 B at 128x128, 32 B grouped payloads, and 64 B grouped payloads from generated images. A second public VQModel, `CompVis/ldm-celebahq-256/vqvae`, recovers 16 B. | Claim for the tested real-VQGAN settings; do not generalize to all generators. |
| P2: No auxiliary recovery channel is needed. | Abstract, contributions | Receiver recovers from generated images, shared key/model, and public packet parameters only. | Synthetic packet/fountain layer, token-space probes, and Stage 2 real VQGAN payload probe recover in-band without an auxiliary channel. | Claim for measured settings. |
| P3: Fountain coding improves recovery. | Method, ablation | Fixed ECC/baseline vs fountain under erasures and image drops. | Synthetic Stage 0 sweep and learned Patch-VQ token-space probe added; symbol CRC turns corrupted symbols into erasures; final ablation shows fountain recovers under crop-offset where fixed repetition fails. Stage 2 VQGAN probe recovers with 25% image drops. | Stage 1 ablation supported; Stage 2 drop recovery supported, but fixed-code comparison still needs replication on VQGAN. |
| P4: Token scheduling improves robustness. | Method, results | Random vs entropy-only vs entropy-stability schedule under transformations. | Learned Patch-VQ 100-image probe: stability schedule has 49/72 successful conditions; random schedule has 0/72. | Local-tokenizer claim only until VQGAN/AR tokenizer is connected. |
| P5: Sampling limits distribution shift. | Method, security | Leakage score, token-distribution divergence, and steganalysis results. | Distribution-aware prior-bin sampler added; projection binning outperforms mass binning for resize/blur in patch-token probe. 1000x3 scale probe shows low token JSD, low feature-level FID/KID, and near-chance scikit-learn detector AUC. Stage 2 64 B VQGAN probes report feature detector AUC 0.48862745, small-CNN AUC 0.5332, SPAM-style AUC 0.52627451, and SRM-style residual cooccurrence mean AUC 0.49521569. | Local detector claim allowed for the reported detectors; no undetectability claim. |
| P6: Competitive robustness. | Abstract, results | Exact recovery under JPEG/resize/blur/noise/crop at stated payloads. | Patch-token sampler recovers under JPEG85/resize0.75/noise0.02 and blur1 after symbol CRC. `anchors2d` recovers 64 B with overhead 2.5 and 16 images for offset crop; crop+JPEG+drop25 needs overhead 4.0 and 24 images. Stage 2 VQGAN probe recovers 64 B with grouped 2x2 macro-cells across three seeds under clean and crop090+jpeg85+drop25, using 48 images. A 128x128 probe recovers 16 B under clean and crop090+jpeg85+drop25. Baselines now include executable HiDDeN and DCT-spread runs. | Robustness claim allowed only with exact payload/image counts; do not claim final SOTA superiority. |
| P7: Competitive steganographic security. | Abstract, results | Modern detector AUC/accuracy under fair splits. | Stage 2 64 B probes use 144 payload and 144 reference VQGAN images. Feature-level logistic detector gives AUC 0.48862745. A local small-CNN detector gives AUC 0.5332 and accuracy 0.57. A SPAM-style residual cooccurrence detector gives AUC 0.52627451 and accuracy 0.5049505. A local SRM-style residual cooccurrence detector gives mean AUC 0.49521569 across five splits. | Local detector evidence only; do not claim resistance to official external SRNet or third-party steganalysis suites. |
| P8: Effective capacity is auditable. | Results, tables | User bits per image after all overhead and failures. | Packet/fountain metadata available. | Ready for synthetic accounting. |

## Deferred Extensions

These are no longer prerequisites for the bounded feasibility paper, but they
remain useful for a later SOTA-superiority submission.

1. Replace discrete crop search with continuous or multi-scale geometry estimation.
2. Add official external SRNet or third-party steganalysis suites when runtime/code is available.
3. Add broader public-generator coverage beyond the two substantive VQModel checkpoints.
4. Obtain a StegaStamp SavedModel/runtime only if a local StegaStamp score is required.
5. Replace naive block rejection with a coded local synchronization layer or drop it if it remains inferior.
