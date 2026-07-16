# VQ-Fountain Limit Closure

Date: 2026-07-16

## Closed Items

| Prior issue | Closure mechanism | Evidence |
|---|---|---|
| WYSAWIS comparison absent | Added explicit WYSAWIS related-work discussion, positioning table, and bibliography entry. | `paper_vq_fountain/main.tex`, `paper_vq_fountain/references.bib` |
| Main real-VQGAN capacity only 64 bytes | Added 128-byte real-VQGAN run across three payload seeds under clean and crop090+jpeg85+drop25. | `vq_fountain_real_vqgan_payload_probe_payload128_multiseed.csv` |
| 128-byte security not checked | Added feature-level and small-CNN detector checks for 128-byte mode; added one-seed SPAM smoke check. | `vq_fountain_real_vqgan_quality_security_payload128.csv`, `vq_fountain_real_vqgan_deep_steganalysis_payload128.csv`, `vq_fountain_real_vqgan_spam_steganalysis_payload128_seed1.csv` |
| Results not fully surfaced in article | Added artifact-coverage and 69-check verification table. | `paper_vq_fountain/main.tex`, `vq_fountain_verification_report.json` |
| SOTA positioning too generic | Added table separating WYSAWIS, public coverless/generative comparators, and non-coverless executable baselines. | `paper_vq_fountain/main.tex` |
| Package not frozen | Added VQ-Fountain SHA256 manifest with dependency versions. | `vq_fountain_reproducibility_manifest.json` |

## Bound Claim

The article now claims auxiliary-channel-free, in-band, coverless VQ steganography with exact 128-byte public-VQGAN recovery under clean and crop090+jpeg85+drop25, second-model feasibility, local detector-bounded passive evidence, executable baseline accounting, and a reproducibility manifest.

The article does not claim universal SOTA dominance. This is deliberate: WYSAWIS remains stronger in raw published capacity, and StegaStamp is accounted for as paper/code comparator without unsupported local scoring.
