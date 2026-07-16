# Preliminary Literature Map From Semantic Scholar

Generated from `semantic_scholar_search_results.csv`.

Status: preliminary. These entries were discovered through Semantic Scholar and still require verification from publisher pages, DOI resolution, Crossref, or official repositories before citation.

## Direct Novelty Threats

| Work | Year | Venue | DOI | Why It Matters |
|---|---:|---|---|---|
| Generative Steganography Network | 2022 | ACM Multimedia | 10.1145/3503161.3548217 | Directly challenges any broad claim that generative steganography itself is new. |
| Coverless Image Steganography Based on Generative Adversarial Network | 2020 | Mathematics | 10.3390/math8091394 | Directly challenges GAN-based coverless novelty. |
| IDGAN: Information-Driven Generative Adversarial Network of Coverless Image Steganography | 2023 | Electronics | 10.3390/electronics12132881 | Directly challenges "information-driven GAN for coverless steganography" framing. |
| Leveraging coverless image steganography to hide secret information by generating anime characters using GAN | 2024 | Expert Systems with Applications | 10.1016/j.eswa.2024.123420 | Challenges image-synthesis-based coverless claims. |
| Robust Generative Steganography Based on Image Mapping | 2024 | IEEE TCSVT | 10.1109/TCSVT.2024.3451620 | Directly relevant to robust generative steganography and likely a strong Q1 baseline. |
| Cover-separable Fixed Neural Network Steganography via Deep Generative Models | 2024 | ACM Multimedia | 10.1145/3664647.3680824 | Directly relevant to using generative models while separating cover behavior. |
| High-accuracy image steganography with invertible neural network and generative adversarial network | 2025 | Signal Processing | 10.1016/j.sigpro.2025.109988 | Strong threat for extraction accuracy and invertible/GAN comparison. |
| Highly Robust and Diverse Coverless Image Steganography Against Passive and Active Steganalysis | 2025 | IEEE TDSC | 10.1109/TDSC.2024.3521424 | Strong threat for robustness and steganalysis claims. |
| A Universal Framework for Improving the Robustness of Coverless Image Steganography Based on Image Restoration | 2025 | IEEE TCSVT | 10.1109/TCSVT.2024.3454457 | Strong threat for robustness claims. |
| StyleStego: a novel paradigm for high-capacity steganography using per layer noise maps in StyleGAN for cross-domain robustness | 2026 | Multimedia Tools and Applications | 10.1007/s11042-026-21718-4 | Very recent high-capacity StyleGAN steganography threat. |

## Implication

The article must not claim novelty as:

- "first GAN-based image steganography";
- "first coverless GAN steganography";
- "first generative steganography";
- "first high-capacity neural steganography";
- "first robust GAN-based steganography".

Those claims are unsafe against the discovered literature.

## Defensible Gap

The defensible gap is narrower and should be tied to WYSAWIS:

> Existing high-capacity coverless/indexing methods such as WYSAWIS still depend on observable auxiliary metadata channels, while existing neural/generative methods rarely evaluate the operational replacement of such channels under a common capacity-quality-robustness-security protocol. The proposed work targets auxiliary-channel elimination and repeated-segment leakage with a reproducible high-capacity neural pipeline and a reviewer-grade benchmark against both WYSAWIS and neural baselines.

