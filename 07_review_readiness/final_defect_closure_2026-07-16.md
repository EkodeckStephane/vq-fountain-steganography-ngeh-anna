# Final Defect Closure Log - 2026-07-16

Scope: `paper/main.tex` and `paper/references.bib` in the NGEH ANNA article.

| ID | Defect | Closure status | Manuscript action |
|---|---|---|---|
| R1 | Method could be misread as coverless although it uses a cover image. | Closed by wording. | Title, abstract, method, discussion, and conclusion use auxiliary-channel-free neural image steganography; strict coverless status is explicitly denied. |
| R2 | Novelty could be framed as GAN/neural steganography. | Closed by wording. | Novelty is now framed as protocol-level self-contained recovery without WYSAWIS-style auxiliary metadata. |
| R3 | Architecture code availability risk. | Closed in artifact statement. | Reproducibility text now explicitly mentions model architecture, packet codec, scripts, weights, and result tables. |
| R4 | Nominal capacity could be confused with usable payload. | Closed in manuscript. | Abstract, packet section, results, discussion, and conclusion report effective user bpp and exact recovery. |
| R5 | Security could be inferred from PSNR/SSIM. | Closed by limitation. | Detectability is reported as an explicit negative result; passive security is not claimed. |
| R6 | Too few images. | Partially closed. | The paper reports 100-image clean-channel checks, 80-image detectability checks, and 20-image attack checks; larger datasets remain future work. |
| R7 | WYSAWIS comparison too qualitative. | Partially closed. | Positioning table now separates metadata channel, carrier model, and ETHEGAN boundary; no dominance claim is made. |
| R8 | Robustness claims unsupported. | Closed by negative evidence. | Attack matrix reports JPEG, blur, and resize failures; robustness is excluded from claims. |
| R9 | Recent 2024-2026 literature risk. | Partially closed. | Added RFNNS, cross-modal error correction, and MIDAS references to the related-work discussion and positioning table. |
| R10 | Visible artifact / imperceptibility risk. | Bounded, not solved. | PSNR/SSIM are reported as quality metrics only; security and imperceptibility claims remain limited. |
| R11 | Generalization risk from failures. | Bounded, not solved. | COCO failures are explicitly counted; universal exact recovery is not claimed. |
| R12 | Simple detector still detects stego images. | Bounded, not solved. | Detectability is presented as a limitation and future validation gap. |
| R13 | No JPEG/blur/resize robustness. | Bounded, not solved. | Active transformations remain outside the contribution; robust-channel training is listed as required future work. |

Residual submission risks:

- No equal-effective-bpp reproduction of a public SOTA method.
- No full training repetition over independent seeds with confidence intervals.
- No stronger contemporary deep steganalysis benchmark.
- No public repository or archive DOI yet.

## Results Integrated After Lightness Review

- Added 50-image payload operating-point curve at 0.05, 0.10, and 0.25 nominal bpp.
- Added 100-image ECC-64 versus ECC-128 capacity/reliability trade-off.
- Added residual-strength and steganalysis-aware training ablation table.
- Added COCO mild-noise stress-test note and low-payload attack-aware fine-tune table.
- Updated abstract, discussion, limitations, conclusion, and highlights accordingly.
