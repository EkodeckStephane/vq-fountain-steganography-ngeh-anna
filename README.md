# VQ-Fountain Steganography - Reproducibility Workspace

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.21400722.svg)](https://doi.org/10.5281/zenodo.21400722)

This workspace contains the local article package and the reproducibility
artifacts for the NGEH Anna VQ-Fountain paper:

> VQ-Fountain Steganography: Distribution-Preserving Coverless VQ Image
> Generation with In-Band Rateless Payload Recovery

The active manuscript is in `paper_vq_fountain/`. The repository intended for
GitHub is an artifact repository, not the article repository: the article
source file and compiled PDF must not be uploaded.

Artifact repository URL used in the paper:

`https://github.com/EkodeckStephane/vq-fountain-steganography-ngeh-anna`

Archived artifact release DOI used in the paper:

`https://doi.org/10.5281/zenodo.21400722`

## Upload Policy

Allowed in the GitHub artifact repository:

- VQ-Fountain source code.
- Test suite.
- Result tables and raw JSON records.
- Generated figures used by the article.
- Verification scripts.
- Figure-generation scripts.
- Experiment notes.
- Reference discovery notes.
- README documentation.
- SHA256 reproducibility manifests.

Explicitly excluded from GitHub:

- `paper_vq_fountain/main.tex`
- `paper_vq_fountain/main.pdf`
- `paper_vq_fountain/Elsevier/*.tex`
- `paper_vq_fountain/Elsevier/*.pdf`

Technically large binary artifacts above normal GitHub limits are also not
committed directly. They remain local and are recorded through manifests and
documentation.

## What Was Done

The previous ETHEGAN line was kept as a legacy branch and the active article
was pivoted to VQ-Fountain, a coverless generated-image method. The current
paper is not a residual cover-image embedding article. It targets generated
VQ images with in-band payload recovery.

The manuscript was expanded from a short 9-page draft into a Q1-oriented
article structure with:

- full motivation against auxiliary-channel dependencies;
- explicit WYSAWIS comparison;
- SOTA positioning against GSN, CISGAN, IDGAN, Cs-FNNS, CMSteg, MIDAS,
  robust/diverse coverless methods, restoration-based coverless methods,
  HiDDeN, DCT-spread, and StegaStamp;
- a threat and channel model;
- a TikZ pipeline diagram;
- packet/fountain/value-channel method sections;
- token-channel ablations;
- public VQGAN recovery results;
- 128-byte capacity extension;
- 128x128 feasibility probe;
- second public VQModel probe;
- passive detector analysis;
- cost and attack-family analysis;
- executable non-coverless baseline discussion;
- a reproducibility and data-availability section with the GitHub artifact
  link, without embedding local command traces in the article;
- claim boundary and limitations;
- appendices with per-seed and ablation traces;
- expanded bibliography with more than twenty cited references.

The active article was also prepared locally as a potential Elsevier/JISA
submission package under `paper_vq_fountain/Elsevier/`. That local package uses
the Elsevier CAS double-column class (`cas-dc`) and includes highlights,
figures, local references, CAS support files, and a JISA preparation README.
The JISA manuscript source and compiled PDF remain local-only and are excluded
from the GitHub artifact repository.

## Main Supported Claim

VQ-Fountain is an auxiliary-channel-free, in-band, coverless VQ steganography
protocol under the measured public-VQModel settings.

The receiver does not require:

- original cover image;
- regenerated cover;
- cloud location index;
- text side channel;
- image-specific metadata;
- private side file.

Recovery-critical information is carried by the generated image sequence and
validated through symbol CRCs and fountain decoding.

## Evidence Summary

### Verification Gate

`tools/check_vq_fountain_final_gate.py` currently reports:

- `69/69` checks passed;
- `all_passed: true`.

The neutral report path used by the article is:

- `05_artifacts/results/raw/vq_fountain_verification_report.json`

The legacy/internal alias is still produced for compatibility:

- `05_artifacts/results/raw/vq_fountain_final_gate.json`

### Reproducibility Manifest

`tools/freeze_vq_fountain_manifest.py` records:

- 250 files;
- SHA256 hashes;
- dependency versions for core Python packages.

Manifest path:

- `05_artifacts/results/raw/vq_fountain_reproducibility_manifest.json`

### Unit Tests

The VQ-Fountain package test suite passed:

```powershell
python -m unittest discover 05_artifacts\code\vq_fountain\tests
```

Recorded result:

- 33 tests;
- OK.

### Public VQGAN 64-Byte Recovery

Artifact:

- `05_artifacts/results/tables/vq_fountain_real_vqgan_payload_probe_payload64_multiseed.csv`

Setting:

- model: converted public VQGAN f4-8192 `diffusers.VQModel`;
- payload: 64 bytes;
- packet: 76 bytes;
- source symbols: 76;
- encoded symbols: 380;
- images: 48;
- payload seeds: 3.

Results:

| Attack | CRC-valid range | Exact recovery |
|---|---:|---:|
| clean | 371-373 | 3/3 |
| crop090+jpeg85+drop25 | 97-111 | 3/3 |

### Public VQGAN 128-Byte Recovery

Artifact:

- `05_artifacts/results/tables/vq_fountain_real_vqgan_payload_probe_payload128_multiseed.csv`

Setting:

- payload: 128 bytes;
- packet: 140 bytes;
- source symbols: 140;
- encoded symbols: 700;
- images: 88;
- payload seeds: 3.

Results:

| Attack | CRC-valid range | Exact recovery |
|---|---:|---:|
| clean | 680-682 | 3/3 |
| crop090+jpeg85+drop25 | 200-222 | 3/3 |

The 128-byte hard-channel result is central because the minimum CRC-valid
count, 200, remains above the 140 source-symbol requirement.

### Token Identity vs Value Channel

The public VQGAN results show that token identity is not preserved. In the
128-byte hard-channel rows:

- token identity match: `0.000170` to `0.000841`;
- value match: `0.885417` to `0.887318`;
- exact payload recovery: 3/3.

This supports the value-channel design: the receiver recovers stable values,
not the exact original token IDs.

### 128x128 Feasibility Probe

Artifact:

- `05_artifacts/results/tables/vq_fountain_real_vqgan_payload_probe_128px.csv`

Result:

- payload: 16 bytes;
- clean: exact recovery;
- crop090+jpeg85+drop25: exact recovery;
- hard-channel CRC-valid symbols: 49.

### Second Public VQModel

Artifact:

- `05_artifacts/results/tables/vq_fountain_real_vqgan_payload_probe_compvis_payload16.csv`

Model:

- `CompVis/ldm-celebahq-256/vqvae`

Result:

- payload: 16 bytes;
- clean: exact recovery, 111 CRC-valid symbols;
- crop090+jpeg85+drop25: exact recovery, 37 CRC-valid symbols.

### Main Ablation Suite

Artifact:

- `05_artifacts/results/tables/vq_fountain_final_ablation_suite.csv`

Key rows:

| Ablation | Variant | CRC-valid | Exact recovery | Interpretation |
|---|---:|---:|---:|---|
| coding | fountain | 119 | yes | rateless coding works |
| coding | repetition | 109 | no | 12 missing source blocks |
| sampling | projection | 119 | yes | distribution-aware mapping works |
| sampling | naive | 7 | no | 69 missing source blocks |
| anchors | block 1 per 4x4 | 119 | yes | best crop-offset row |
| anchors | global 9 | 96 | yes | lower margin |
| schedule | center | 96 | yes | robust under crop-offset geometry |
| schedule | random | 71 | no | 5 missing source blocks |

These ablations justify the use of fountain coding, projection binning,
spatial anchors, and structured scheduling.

### Cost and Attack-Family Analysis

Artifacts:

- `05_artifacts/results/tables/vq_fountain_cost_search_crop_offset.csv`
- `05_artifacts/results/tables/vq_fountain_combined_drop25_cost_search.csv`
- `05_artifacts/results/tables/vq_fountain_combined_attacks.csv`

Key conclusion:

- 32 bytes under offset crop can recover with overhead 2.0 and 8 images.
- 64 bytes under crop090+jpeg85+drop25 fails at 16 images but succeeds at
  24 images with overhead 4.0.
- Crop and image drops are the dominant sources of symbol loss.

### Passive Detector Evidence

64-byte setting, 144 payload images and 144 reference images:

| Detector | AUC | Accuracy |
|---|---:|---:|
| feature-level logistic detector | 0.48862745 | 0.53465347 |
| small CNN | 0.53320000 | 0.57000000 |
| SPAM-style residual cooccurrence | 0.52627451 | 0.50495050 |
| SRM-style residual cooccurrence | 0.49521569 | 0.49702970 |

128-byte setting:

| Detector | AUC | Accuracy |
|---|---:|---:|
| feature-level logistic detector | 0.56077606 | 0.53513514 |
| small CNN | 0.48653119 | 0.52173913 |
| SPAM-style one-seed smoke | 0.39958377 | 0.33870968 |

These are detector-bounded passive results, not a proof of undetectability.

### Executable Non-Coverless Baselines

HiDDeN:

- artifact: `05_artifacts/results/tables/hidden_baseline_smoke.csv`;
- payload: 30 bits;
- five trials;
- mean BER: 0.31333333;
- exact recoveries: 0/5.

DCT-spread:

- artifact: `05_artifacts/results/tables/dct_spread_baseline.csv`;
- payload: 32 bits;
- PSNR: 37.916521 dB;
- exact under clean, JPEG85, resize075, blur1;
- fails under crop090 with BER 0.5.

StegaStamp:

- source/audit accounted for;
- no local score claimed because compatible SavedModel, TensorFlow, and BCH
  runtime are absent.

## Figures Generated for the Article

Figure-generation script:

```powershell
python tools\build_vq_fountain_paper_figures.py
```

Output directory:

- `paper_vq_fountain/figures/`

Generated figures:

- `fig_recovery_margin.pdf`
- `fig_ablation_crc.pdf`
- `fig_detector_auc.pdf`
- `fig_hard_channel_cost.pdf`
- `fig_attack_family.pdf`
- `fig_generated_samples.pdf`

These figures are derived from frozen CSV/PNG artifacts and do not require
rerunning the VQGAN experiments.

## Manuscript State

Local files:

- `paper_vq_fountain/main.tex`
- `paper_vq_fountain/main.pdf`
- `paper_vq_fountain/references.bib`
- `paper_vq_fountain/figures/`

The manuscript currently contains:

- author list with consistent proper-name formatting:
  EKODECK, EBELE, MVEH-ABIA, NGEH, EWANE, NDOUNDAM;
- EWANE placed after NGEH Anna;
- a GitHub artifact link in the reproducibility section;
- explicit statement that article `.tex` and PDF are excluded from the
  artifact repository;
- no claim that the article itself is hosted on GitHub.

## Current Claim Boundary

Supported:

- coverless generated-image setting under tested public VQModel conditions;
- in-band recovery without auxiliary cloud/text/location channel;
- exact 64-byte and 128-byte public VQGAN recovery under clean and
  crop090+jpeg85+drop25;
- second public VQModel feasibility;
- 128x128 feasibility;
- local detector-bounded passive evidence;
- executable local baseline context;
- reproducibility through scripts, CSV/JSON records, figures, tests, and
  manifest.

Not supported:

- universal undetectability;
- universal robustness;
- global SOTA dominance;
- higher capacity than WYSAWIS;
- official SRNet/SRNet-family external benchmark;
- local StegaStamp score;
- full equal-effective-bpp reproduction of every recent public SOTA method.

## Better Than Whom, Worse Than Whom

VQ-Fountain is better than WYSAWIS on:

- removal of the auxiliary cloud/location channel;
- in-band recovery from generated images only.

WYSAWIS is stronger than VQ-Fountain on:

- raw published capacity.

VQ-Fountain is better than the local HiDDeN smoke artifact on:

- exact local recovery under the measured artifact protocol.

DCT-spread is better than VQ-Fountain on:

- the tested non-coverless JPEG85, resize075, and blur1 transform-domain
  robustness rows.

VQ-Fountain is not claimed to dominate:

- CMSteg;
- MIDAS;
- robust diverse coverless steganography;
- restoration-based coverless steganography;
- StegaStamp;
- official deep steganalysis benchmarks.

A global SOTA-superiority claim would require official public-code
re-execution under equal effective payload, equal image budget, equal attack
matrix, equal detector protocol, and equal auxiliary-channel assumptions.

## Important Commands

Run unit tests:

```powershell
python -m unittest discover 05_artifacts\code\vq_fountain\tests
```

Generate article figures:

```powershell
python tools\build_vq_fountain_paper_figures.py
```

Run verification gate:

```powershell
python tools\check_vq_fountain_final_gate.py
```

Freeze manifest:

```powershell
python tools\freeze_vq_fountain_manifest.py
```

Compile local article:

```powershell
cd paper_vq_fountain
pdflatex -interaction=nonstopmode main.tex
bibtex main
pdflatex -interaction=nonstopmode main.tex
pdflatex -interaction=nonstopmode main.tex
```

Compile local Elsevier/JISA CAS draft:

```powershell
cd paper_vq_fountain\Elsevier
pdflatex -interaction=nonstopmode main_jisa_casdc.tex
bibtex main_jisa_casdc
pdflatex -interaction=nonstopmode main_jisa_casdc.tex
pdflatex -interaction=nonstopmode main_jisa_casdc.tex
```

Check LaTeX log:

```powershell
rg -n "undefined|Citation.*undefined|Reference.*undefined|Rerun to|LaTeX Warning|Overfull|Underfull|Fatal error|Emergency stop" paper_vq_fountain\main.log
```

## Folder Map

| Folder | Purpose |
|---|---|
| `00_brainstorming/` | Historical idea sources; not final claims. |
| `01_references/` | Public references and literature discovery outputs. |
| `02_novelty/` | SOTA positioning and novelty guardrails. |
| `03_method/` | VQ-Fountain method specification and legacy ETHEGAN notes. |
| `04_experiments/` | Experimental protocols and result notes. |
| `05_artifacts/` | Code, data, models, results, baselines, and reproducibility artifacts. |
| `06_manuscript/` | Manuscript blueprints and drafts. |
| `07_review_readiness/` | Acceptance gates, closure notes, and risk registers. |
| `ETEHGAN/` | Legacy prototype preserved for traceability. |
| `paper/` | Legacy ETHEGAN LaTeX draft. |
| `paper_vq_fountain/` | Active local VQ-Fountain article. |
| `paper_vq_fountain/Elsevier/` | Local Elsevier/JISA CAS preparation package; manuscript `.tex` and PDF are excluded from GitHub. |
| `tools/` | Verification, conversion, figure, and manifest scripts. |

## GitHub Artifact Preparation Rule

Before pushing artifacts, ensure `.gitignore` excludes:

```gitignore
paper_vq_fountain/main.tex
paper_vq_fountain/main.pdf
paper_vq_fountain/Elsevier/*.tex
paper_vq_fountain/Elsevier/*.pdf
*.abs
```

The GitHub artifact repository may include the README, code, results, scripts,
figures, manifests, and notes, but not the article source or compiled PDF.

## Guardrails

- Do not claim "undetectable" without stronger external steganalysis evidence.
- Do not claim "perfectly secure".
- Do not claim universal robustness.
- Do not claim SOTA dominance without equal-effective-bpp reproduction.
- Do not cite unpublished internal manuscripts as public SOTA.
- Keep WYSAWIS comparison precise: VQ-Fountain removes the auxiliary channel;
  WYSAWIS remains stronger in raw published capacity.
