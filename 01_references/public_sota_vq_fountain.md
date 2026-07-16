# Public SOTA Map for VQ-Fountain Stega

Status: public-source-only working table. Do not cite unpublished internal
manuscripts here.

## Positioning Sentence

VQ-Fountain Stega targets the gap between generative/coverless steganography,
robust learned hiding, and watermark-like diffusion methods: payload bits are
embedded in distribution-aware VQ token choices, while recovery is handled by an
in-band rateless layer across one or more generated images.

## Public Baselines

| Work | Public link | Relevant strength | Limit for our positioning |
|---|---|---|---|
| Generative Steganography Network (GSN), ACM MM 2022 | https://arxiv.org/abs/2207.13867 | Generates stego images without conventional covers and includes a generator, discriminator, steganalyzer, and extractor. | Establishes that broad "first generative steganography" claims are unsafe; robustness and exact effective-capacity accounting must be checked separately. |
| Cs-FNNS, ACM MM 2024 | https://arxiv.org/abs/2407.11405 | Uses a shared generative model and perturbation strategy for cover-separable hiding. | Reported JPEG sensitivity makes robustness a differentiator; side assumptions and exact recovery accounting need careful comparison. |
| CMSteg, 2024/2025 | https://arxiv.org/abs/2412.12206 | Uses robust token-oriented generation and cross-modal error correction for social-network-like lossy processing. | Strong robustness comparator; VQ-Fountain must differentiate by avoiding auxiliary cross-modal stego text and by using in-band rateless recovery. |
| MIDAS, ICML 2026 | https://arxiv.org/abs/2603.09390 | Diffusion-based coverless multi-image hiding with access control and robustness/security evaluation. | Strong multi-image competitor; VQ-Fountain must show clearer token-level distribution control, effective capacity, or simpler recovery assumptions. |
| Diffusion steganography trade-off work, 2025 | https://arxiv.org/abs/2510.07219 | Frames the security/robustness trade-off between pixel-space diffusion and VAE/latent-space methods. | Helps motivate entropy-stability scheduling; also warns that robustness can amplify detectable artifacts. |
| Tree-Ring Watermarks, NeurIPS 2023 | https://arxiv.org/abs/2305.20030 | Embeds robust signals in diffusion initial noise without post-hoc image modification. | Watermarking rather than message steganography; useful robustness/security reference but not a direct high-payload baseline. |
| Stable Signature, ICCV 2023 | https://arxiv.org/abs/2303.15435 | Fine-tunes latent diffusion decoders to add detectable signatures. | Signature watermarking, not arbitrary payload recovery; useful for detector and robustness framing. |
| HiDDeN, ECCV 2018 | https://arxiv.org/abs/1807.09937 | Learned robust data hiding under differentiable distortions. | Cover-modification method, not coverless generation; still a robustness baseline. |
| StegaStamp, CVPR 2020 | https://arxiv.org/abs/1904.05343 | Robust invisible hyperlinks for physical/image transformations. | Low payload and cover-modification setting; useful as a practical robustness reference. |

## Competitive Claim Boundary

The paper should claim novelty only at the intersection of:

1. coverless generative image production;
2. payload-bearing VQ token sampling with measured distribution shift;
3. no auxiliary recovery channel;
4. rateless in-band recovery across generated images;
5. robustness/effective-capacity accounting under common transformations.

Any one of these items alone is not enough for a Q1 novelty claim.
