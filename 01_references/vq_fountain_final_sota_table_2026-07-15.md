# VQ-Fountain Final Public SOTA Table

Date: 2026-07-15

Scope: public-source positioning only. Do not cite unpublished internal
manuscripts.

## Coverless and Generative Steganography

| Work | Public source | Coverless | Auxiliary recovery channel | Main reported strength | Limit for VQ-Fountain positioning |
|---|---|---:|---:|---|---|
| GSN | https://arxiv.org/abs/2207.13867 | yes | no explicit auxiliary channel | Generative stego images are produced directly from secret data with generator, discriminator, steganalyzer, and extractor. | Establishes that broad "first generative steganography" claims are not defensible. VQ-Fountain must position on in-band rateless recovery and audited effective capacity. |
| DiffStega | https://arxiv.org/abs/2407.10459 | yes | password/reference-image assumptions | Training-free diffusion CIS with password-dependent reference image and noise flipping. | Strong training-free diffusion comparator; VQ-Fountain differs by VQ value-channel sampling and packet/fountain recovery. |
| Cs-FNNS | https://arxiv.org/abs/2407.11405 | partial / cover-separable | regenerated cover required | Uses a shared generative model to reproduce the cover and decode perturbations. | Not the same channel assumption: receiver must reproduce/separate a cover. VQ-Fountain can claim no regenerated cover in the tested protocol. |
| CMSteg | https://arxiv.org/abs/2412.12206 | generated-image setting | yes, cross-modal stego text | Robust VQ/AR generated-image steganography with cross-modal error correction for lossy channels. | Strong robustness comparator. VQ-Fountain must emphasize that recovery is in-band from images, without cross-modal stego text. |
| MIDAS | https://arxiv.org/abs/2603.09390 | yes | access-control latent/key assumptions | Training-free diffusion multi-image CIS with user-specific access control. | Strong 2026 multi-image comparator. VQ-Fountain is not positioned as access control; it is positioned as in-band rateless VQ recovery. |
| Latent iterative optimization | https://arxiv.org/abs/2603.09348 | no / robust steganography | no text channel | Iterative latent refinement improves robustness while preserving provable-security framing. | Strong lossy-channel robustness comparator, but compute/iterative decoding differs from VQ-Fountain's packet/fountain design. |
| VQ-Fountain | local implementation | yes in tested VQGAN settings | no auxiliary recovery channel | 32 B exact recovery across three seeds under clean and crop090+jpeg85+drop25 with 22 images; second public VQModel recovers 16 B under clean and crop090+jpeg85+drop25. | Claim only for measured public VQModel settings. Do not claim final SOTA superiority or universal robustness. |

## Watermarking and Robust Generated-Image References

| Work | Public source | Direct arbitrary payload? | Main relevance | Limit for direct comparison |
|---|---|---:|---|---|
| Tree-Ring Watermarks | https://arxiv.org/abs/2305.20030 | no | Robust diffusion watermark signal embedded through initial noise. | Watermark detection/fingerprinting, not multi-byte arbitrary message recovery. |
| Stable Signature | https://arxiv.org/abs/2303.15435 | limited signature | Decoder fine-tuning for robust latent-diffusion signatures. | Signature watermarking, not coverless arbitrary-payload steganography. |

## Non-Coverless Executable Baselines

| Baseline | Public/local source | Coverless | Executable locally | Measured local result | Use in manuscript |
|---|---|---:|---:|---|---|
| HiDDeN | https://arxiv.org/abs/1807.09937 and local public checkpoint | no | yes | 30-bit five-trial smoke run, mean BER 0.31333333, 0/5 exact recoveries on the selected VQGAN sample. | Report separately as a non-coverless robust learned hiding baseline. Do not present as same-assumption coverless SOTA. |
| DCT-spread | local runner | no | yes | 32-bit payload exact under clean, JPEG85, resize075, and blur1; crop090 fails with BER 0.5. | Report as a classical transform-domain sanity baseline. |
| StegaStamp | https://arxiv.org/abs/1904.05343 | no | no | No local score: pretrained SavedModel and compatible TensorFlow/BCH runtime unavailable. | Paper/code comparator only until runtime/checkpoint is available. |

## Competitive Position

VQ-Fountain has an original contribution if framed narrowly:

1. payload-bearing VQ value-channel sampling for coverless image generation;
2. distribution-aware projection binning to limit token-distribution shift;
3. in-band packet, CRC, anchors, and fountain recovery without text or cloud
   metadata;
4. exact-recovery accounting under lossy image channels and image drops;
5. local detector evidence from feature, CNN, and SPAM-style probes.

The current evidence is competitive but not a final SOTA win. The manuscript
should use the phrase "competitive feasibility evidence" rather than
"state-of-the-art superiority" unless public SOTA code is reproduced under the
same protocol.
