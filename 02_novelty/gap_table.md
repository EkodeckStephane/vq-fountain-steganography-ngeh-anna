# Gap Table

Status: legacy ETHEGAN gap table. Replace with a public VQ-Fountain SOTA table
before manuscript drafting.

Status: first working version. Detailed values for capacity, robustness, and steganalysis must be completed from the full papers before manuscript submission.

| Method | Type | Auxiliary Channel / Side Metadata | Repeated-Segment Leakage | Robustness / Security Focus | Relevance to Our Novelty |
|---|---|---|---|---|---|
| WYSAWIS2025 | Coverless/indexing with block-level hash categories | Yes: cloud-carried location information is central to extraction | Yes: repeated message segments can create repeated stego-files, according to WYSAWIS discussion | Robustness tested with image attacks; security argued through unchanged image and cloud assumptions | Main operational baseline. Our work must show extraction without cloud metadata and no repeated external artifacts. |
| GSN2022 | Generative steganography | To verify from full paper | To verify | Generative steganography baseline | Prevents broad "first generative steganography" claim. |
| CISGAN2020 | GAN-based coverless image steganography | To verify | To verify | GAN coverless baseline | Prevents broad "first GAN coverless" claim. |
| IDGAN2023 | Information-driven GAN coverless steganography | To verify | To verify | Coverless GAN framing | Must be positioned as prior work, not ignored. |
| AnimeGAN2024 | Coverless image generation using GAN | To verify | To verify | Image synthesis as carrier | Challenges any generated-image novelty claim. |
| RGSIM2024 | Robust generative steganography based on image mapping | To verify | To verify | Robust generative steganography | Strong Q1 comparator for robustness. |
| CsFNNS2024 | Fixed neural network steganography with deep generative models | Uses shared generative model/key according to S2 abstract; exact side information to verify | To verify | Visual quality and undetectability | Strong neural/generative comparator; code availability makes it a likely baseline. |
| INNGAN2025 | Invertible neural network + GAN steganography | To verify | To verify | High extraction accuracy | Strong comparator for BER/extraction reliability. |
| RobustDiverseCIS2025 | Robust and diverse coverless steganography against passive/active steganalysis | To verify | To verify | Passive and active steganalysis | Strong comparator for security claims. |
| RestorationCIS2025 | Robustness framework for coverless steganography using restoration | To verify | To verify | Robustness under image restoration | Important comparator for robustness. |
| StyleStego2026 | StyleGAN per-layer noise maps for high-capacity cross-domain robustness | To verify | To verify | High capacity and cross-domain robustness | Very recent competitor; must be acknowledged. |
| ETEHGAN v3 target | Reliability-aware auxiliary-channel-free neural image steganography | No cloud/file-position metadata; receiver uses stego image, shared model, public packet parameters, and optional shared seed/key only | Target: no repeated external metadata artifacts because payload is encoded as one self-contained packet | Must report nominal bpp, effective user bpp, exact recovery, failures, quality, robustness, and steganalysis | Defensible novelty only if exact-recovery and comparison experiments prove these points. |

## Working Novelty Sentence

Existing generative and neural steganography methods already address image
synthesis, learned embedding, or robust extraction; the unresolved operational
gap targeted here is the replacement of WYSAWIS-style auxiliary cloud-carried
location metadata by a reproducible image-only recovery pipeline with
self-contained payload recovery and explicit effective-payload accounting.
