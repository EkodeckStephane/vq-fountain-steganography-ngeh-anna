# First Five Milestones Execution Status

Date: 2026-07-15

Scope: only the first five requested items.

## 1. Real Tokenizer / Generator

Status: executed for local readiness.

Completed:

- Installed real-model dependencies: `diffusers`, `transformers`,
  `accelerate`, and `safetensors`.
- Added `run_real_diffusion_smoke.py`.
- Generated a local image with `diffusers/tiny-stable-diffusion-torch` on CPU.
- Added `run_real_vqmodel_smoke.py`.
- Loaded a public `diffusers.VQModel` and completed an encode/decode round trip
  with `fusing/vqgan-dummy`.
- Smoke evidence:
  - `05_artifacts/results/raw/vq_fountain_real_diffusion_smoke.png`
  - `05_artifacts/results/raw/vq_fountain_real_diffusion_smoke.json`
  - `05_artifacts/results/raw/vq_fountain_real_vqmodel_smoke.png`
  - `05_artifacts/results/raw/vq_fountain_real_vqmodel_smoke.json`

Stage 2 update:

- Converted public VQGAN f4-8192 weights to a modern `diffusers.VQModel`
  layout with 205/205 target tensors loaded.
- Added `run_real_vqgan_payload_probe.py`.
- Recovered conservative in-band payloads through generated VQGAN images:
  - 4 B exactly under clean, JPEG85, resize075, blur1, noise002, crop090,
    drop25, and crop090+jpeg85+drop25;
  - 8 B exactly under clean and crop090+jpeg85+drop25.
- Stage 2 evidence:
  - `04_experiments/results/vq_fountain_real_vqgan_stage2_payload_2026-07-15.md`
  - `05_artifacts/results/tables/vq_fountain_real_vqgan_payload_probe.csv`
  - `05_artifacts/results/tables/vq_fountain_real_vqgan_payload_probe_hard_attacks.csv`
  - `05_artifacts/results/tables/vq_fountain_real_vqgan_payload_probe_drop_attacks.csv`
  - `05_artifacts/results/tables/vq_fountain_real_vqgan_payload_probe_payload8.csv`

## 2. Geometry Synchronization

Status: executed for the current centered-crop probe.

Completed:

- Added `--geometry-search anchors2d`.
- Added `--crop-offsets`.
- The receiver now searches crop ratio plus row/column offsets using anchor
  agreement.
- Added tests for offset mapping and geometry candidate generation.
- Re-ran crop0.90 with spatial block anchors:
  - `05_artifacts/results/tables/vq_fountain_distribution_sampler_probe_k128_crop_anchors2d.csv`
  - `05_artifacts/results/raw/vq_fountain_distribution_sampler_probe_k128_crop_anchors2d.json`

Result:

- The 2D synchronizer selected `(ratio=0.90, row_offset=0, col_offset=0)`.
- 64 B recovered with 16 images in the centered crop probe.
- A direct non-centered crop probe `crop090_r02_c-02` was also executed.
- The 2D synchronizer selected `(row_offset=0.02, col_offset=-0.02)` and
  recovered 64 B with 16 images.

Remaining issue:

- The current search is discrete. Continuous or multi-scale geometry estimation
  is still not implemented.

## 3. 1000-Image / Multi-Seed Evaluation

Status: executed.

Completed:

- Added `run_scale_quality_security_probe.py`.
- Ran 1000 generated token-grid images x 3 seeds for 512 B and 4096 B payloads.
- Built a sanitized external dataset manifest.
- Ran learned patch-VQ stability checks on 1000 images from `bossbase` and
  1000 images from `local_raw`.
- Results:
  - `05_artifacts/results/tables/vq_fountain_scale_quality_security_probe_1000x3.csv`
  - `05_artifacts/results/raw/vq_fountain_scale_quality_security_probe_1000x3.json`

Result summary:

- 512 B uses about 69 images.
- 4096 B uses about 536 images.
- Token Jensen-Shannon divergence is about `0.00014` to `0.00021`.
- Proxy detector AUC stays near chance: about `0.48` to `0.51`.
- No capacity exhaustion in the tested settings.

## 4. Public Baselines

Status: executed for reproducibility triage.

Completed:

- Added public baseline registry:
  - `01_references/public_baselines_vq_fountain.md`
- Registered GSN, Cs-FNNS, CMSteg, MIDAS, latent iterative optimization,
  HiDDeN, and StegaStamp as public-only comparators.
- GitHub searches found clear public repositories for HiDDeN and StegaStamp.
- HiDDeN and StegaStamp were cloned locally with shallow filtered clones.
- Local baseline status:
  - `05_artifacts/baselines/baseline_reproducibility_status.json`

Remaining non-blocking note:

- Direct GitHub searches did not identify clear repositories for GSN, Cs-FNNS,
  CMSteg, or MIDAS by title/arXiv identifier.

## 5. Realism / Security Metrics

Status: executed for current feature-level evaluation.

Completed:

- Added NumPy-only quality/security metrics:
  - token-distribution Jensen-Shannon divergence;
  - diagonal Frechet feature distance;
  - NumPy Frechet feature distance;
  - polynomial-kernel MMD/KID proxy;
  - logistic proxy detector AUC/accuracy.
- Added tests for JSD, Frechet, KID/MMD, and AUC.
- Re-ran the 1000x3 scale probe with these columns.
- Installed `scipy` and `scikit-learn`.
- Added SciPy Frechet distance and scikit-learn logistic detector columns.

## Gate Result

The readiness gate now passes for the first five milestones.

Command:

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
python tools\check_vq_fountain_readiness.py
```
