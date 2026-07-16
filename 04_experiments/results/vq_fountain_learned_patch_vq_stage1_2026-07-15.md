# VQ-Fountain Stage 1 Learned Patch-VQ Results

Date: 2026-07-15

## Purpose

Move from the fixed `patch-vq` baseline to a learned local VQ codebook while
keeping the experiment dependency-light.

This is still not a VQGAN or autoregressive image tokenizer. It is a learned
patch-vector codebook trained with NumPy k-means, used to validate the Stage 1
token stability and recovery protocol on 100 images.

## Codebook Training

Command shape:

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
python 05_artifacts\code\vq_fountain\train_patch_vq_codebook.py `
  --image-root <CALTECH101_IMAGES_DIR> <COCO_VAL2017_DIR> `
  --max-images 120 `
  --max-patches 8000 `
  --codebook-size 128 `
  --iterations 6 `
  --out 05_artifacts\models\learned_patch_vq_stage1_k128.npz `
  --metadata-out 05_artifacts\models\learned_patch_vq_stage1_k128_metadata.json
```

Training summary:

- used images: 120
- used patches: 8000
- codebook size: 128
- patch size: 16
- image size: 256
- k-means iterations: 6
- mean squared distortion: 0.01388178 -> 0.01274997

## Token Stability on 100 Images

Command shape:

```powershell
python 05_artifacts\code\vq_fountain\measure_token_stability.py `
  --image-root <COCO_VAL2017_DIR> `
  --max-images 100 `
  --tokenizer learned-patch-vq `
  --codebook 05_artifacts\models\learned_patch_vq_stage1_k128.npz `
  --attacks clean jpeg85 resize075 blur1 noise002 `
  --out-csv 05_artifacts\results\tables\vq_fountain_learned_patch_vq_k128_stability_100.csv `
  --out-json 05_artifacts\results\raw\vq_fountain_learned_patch_vq_k128_stability_100.json
```

Mean token stability:

| Attack | Mean changed tokens / 256 | Mean token match rate |
|---|---:|---:|
| clean | 0.00 | 1.000000 |
| resize0.75 | 0.89 | 0.996524 |
| JPEG85 | 2.19 | 0.991445 |
| noise0.02 | 2.85 | 0.988867 |
| blur1 | 6.71 | 0.973789 |

Separate crop diagnostic:

| Attack | Mean changed tokens / 256 | Mean token match rate |
|---|---:|---:|
| crop0.90 | 154.34 | 0.397109 |

## Recovery Probe on 100 Images

Command shape:

```powershell
python 05_artifacts\code\vq_fountain\run_token_recovery_probe.py `
  --image-root <COCO_VAL2017_DIR> `
  --max-images 100 `
  --tokenizer learned-patch-vq `
  --codebook 05_artifacts\models\learned_patch_vq_stage1_k128.npz `
  --attacks jpeg85 resize075 blur1 noise002 `
  --out-csv 05_artifacts\results\tables\vq_fountain_learned_patch_vq_k128_recovery_100.csv `
  --out-json 05_artifacts\results\raw\vq_fountain_learned_patch_vq_k128_recovery_100.json
```

Ablation:

```powershell
python 05_artifacts\code\vq_fountain\run_token_recovery_probe.py `
  --image-root <COCO_VAL2017_DIR> `
  --max-images 100 `
  --tokenizer learned-patch-vq `
  --codebook 05_artifacts\models\learned_patch_vq_stage1_k128.npz `
  --attacks jpeg85 resize075 blur1 noise002 `
  --schedule random `
  --out-csv 05_artifacts\results\tables\vq_fountain_learned_patch_vq_k128_recovery_100_random.csv `
  --out-json 05_artifacts\results\raw\vq_fountain_learned_patch_vq_k128_recovery_100_random.json
```

Main thresholds with stability scheduling:

| Payload | Bits/token | Overhead | Minimum simulated images for exact recovery |
|---:|---:|---:|---:|
| 32 B | 1 | 0.5 | 4 |
| 32 B | 2 | 0.5 | 2 |
| 64 B | 1 | 0.5 | 4 |
| 64 B | 2 | 0.5 | 2 |
| 128 B | 1 | 0.5 | 8 |
| 128 B | 2 | 0.5 | 4 |
| 128 B | 2 | 0.8 | 8 |

Scheduling ablation:

- stability schedule: 49 / 72 exact-recovery conditions
- random schedule: 0 / 72 exact-recovery conditions

## Interpretation

The learned patch-VQ Stage 1 result strengthens the direction:

1. token stability remains high under JPEG85, resize0.75, mild noise, and blur1;
2. stability scheduling is not cosmetic; it is the difference between many
   exact-recovery conditions and none in this probe;
3. multi-image rateless recovery is the plausible operating point for 128-byte
   payloads at this token density;
4. crop/geometric desynchronization remains the hard problem.

## Limits

- The tokenizer is learned but still patch-based, not VQGAN.
- The recovery probe is token-space and uses a stability oracle from measured
  attacks.
- No distribution-aware token sampling is evaluated yet.
- No generated coverless image pipeline is connected yet.
- Security against image steganalysis is not tested at this stage.
