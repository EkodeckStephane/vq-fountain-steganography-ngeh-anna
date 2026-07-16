# ETEHGAN Minimal Artifact

This is the current reproducible prototype package.

## Current Scope

This code implements neural image steganography with:

- cover image input;
- secret text payload input;
- learned encoder;
- learned decoder;
- Reed-Solomon error correction;
- extraction from the stego image using the shared model weights.

Because the sender currently provides a cover image, this artifact must not be described as strictly coverless unless the method is later changed.

## Smoke Test Commands

From the repository root:

```powershell
python 05_artifacts\code\etehgan\embed_payload.py `
  05_artifacts\data\sample_images\000000001503.jpg `
  05_artifacts\data\payloads\numbered_story.txt `
  05_artifacts\results\raw\stego_000000001503.png `
  05_artifacts\models\ETEHGAN.pt

python 05_artifacts\code\etehgan\extract_payload.py `
  05_artifacts\results\raw\stego_000000001503.png `
  05_artifacts\results\raw\recovered_numbered_story.txt `
  05_artifacts\models\ETEHGAN.pt
```

## Required Before Submission

- training script;
- evaluation scripts;
- dataset split files;
- raw result tables;
- steganalysis scripts;
- robustness scripts.

## V2 Training Prototype

`train_v2.py` is a minimal training/fine-tuning script for extraction and image-fidelity losses. It is not yet the final experimental pipeline.

Example:

```powershell
python 05_artifacts\code\etehgan\train_v2.py `
  --image-root 05_artifacts\data\sample_images `
  --output 05_artifacts\models\etehgan_v2_smoke.pt `
  --init-checkpoint 05_artifacts\models\ETEHGAN.pt `
  --epochs 1 `
  --payload-bpp 0.25 `
  --lambda-image 10
```

Evaluate random-payload behavior:

```powershell
python 05_artifacts\code\etehgan\evaluate_v2_random.py `
  --image-root 05_artifacts\data\sample_images `
  --checkpoint 05_artifacts\models\etehgan_v2_smoke.pt `
  --payload-bpp 0.25 `
  --trials-per-image 1 `
  --out-csv 05_artifacts\results\tables\v2_smoke_random.csv `
  --out-json 05_artifacts\results\raw\v2_smoke_random.json
```

## V3 Reliability-Aware Packet Layer

The V3 scripts add a self-contained packet format:

- magic/version header;
- payload length;
- CRC32;
- Reed-Solomon parity;
- deterministic interleaving;
- optional erasure decoding from decoder-logit reliability.

End-to-end example:

```powershell
python 05_artifacts\code\etehgan\embed_payload_v3.py `
  --cover 05_artifacts\data\sample_images\000000001503.jpg `
  --payload 05_artifacts\data\payloads\short_readme_payload.txt `
  --checkpoint 05_artifacts\models\etehgan_v2_residual02_025_caltech20_coco20_e3.pt `
  --output 05_artifacts\results\raw\v3_stego_000000001503_025.png `
  --payload-bpp 0.25 `
  --ecc-bytes 64 `
  --packet-seed 7

python 05_artifacts\code\etehgan\extract_payload_v3.py `
  --stego 05_artifacts\results\raw\v3_stego_000000001503_025.png `
  --checkpoint 05_artifacts\models\etehgan_v2_residual02_025_caltech20_coco20_e3.pt `
  --output 05_artifacts\results\raw\v3_recovered_short_readme_payload.txt `
  --payload-bpp 0.25 `
  --ecc-bytes 64 `
  --packet-seed 7
```

Packet-level evaluation:

```powershell
python 05_artifacts\code\etehgan\evaluate_v3_packet.py `
  --image-root 05_artifacts\data\sample_images `
  --checkpoint 05_artifacts\models\etehgan_v2_residual02_025_caltech20_coco20_e3.pt `
  --payload-bpp 0.25 `
  --payload-fraction 1.0 `
  --ecc-bytes 64 `
  --packet-seed 7 `
  --trials-per-image 1 `
  --attacks clean `
  --out-csv 05_artifacts\results\tables\v3_packet_sample_025_clean.csv `
  --out-json 05_artifacts\results\raw\v3_packet_sample_025_clean.json
```

Simple steganalysis sanity check:

```powershell
python 05_artifacts\code\etehgan\evaluate_v3_simple_steganalysis.py `
  --image-root <COCO_VAL2017_DIR> `
  --checkpoint 05_artifacts\models\etehgan_v2_residual02_025_caltech20_coco20_e3.pt `
  --payload-bpp 0.25 `
  --payload-fraction 1.0 `
  --ecc-bytes 64 `
  --packet-seed 7 `
  --max-images 80 `
  --offset-images 20 `
  --out-csv 05_artifacts\results\tables\v3_simple_steganalysis_coco80_025.csv `
  --out-json 05_artifacts\results\raw\v3_simple_steganalysis_coco80_025.json
```

This detector is intentionally lightweight. It is a sanity check, not a
replacement for contemporary deep steganalysis.

SPAM-style residual co-occurrence detector smoke test:

```powershell
python 05_artifacts\code\etehgan\evaluate_v3_spam_steganalysis.py `
  --image-root 05_artifacts\data\sample_images `
  --checkpoint 05_artifacts\models\etehgan_v3_stegaware018_stat05_adv001_e3.pt `
  --payload-bpp 0.25 `
  --payload-fraction 1.0 `
  --ecc-bytes 64 `
  --packet-seed 7 `
  --max-images 2 `
  --offset-images 0 `
  --out-csv 05_artifacts\results\tables\spam_steganalysis_sample_025.csv `
  --out-json 05_artifacts\results\raw\spam_steganalysis_sample_025.json `
  --epochs 100
```

This SPAM-style evaluator is a stronger classical-detector gate than the
simple residual/LSB sanity check. The bundled two-image run is only a pipeline
smoke test; a manuscript security claim requires larger grouped splits.

Adaptive ECC/rate-control smoke test:

```powershell
python 05_artifacts\code\etehgan\evaluate_v3_adaptive_ecc.py `
  --image-root 05_artifacts\data\sample_images `
  --checkpoint 05_artifacts\models\etehgan_v3_stegaware018_stat05_adv001_e3.pt `
  --payload-bpp 0.25 `
  --ecc-candidates 64 96 128 160 `
  --packet-seed 7 `
  --trials-per-image 1 `
  --attacks clean jpeg95 blur1 resize0.75 `
  --max-images 2 `
  --out-csv 05_artifacts\results\tables\adaptive_ecc_sample_025.csv `
  --out-json 05_artifacts\results\raw\adaptive_ecc_sample_025.json
```

The adaptive ECC evaluator reports fixed-ECC recovery and an oracle adaptive
upper bound. It can support clean-channel rate control, but it does not solve
JPEG, blur, resize, or crop desynchronization.

Low-payload detectability-gated passive-security check:

```powershell
python 05_artifacts\code\etehgan\evaluate_v3_detectability_gate.py `
  --image-root 05_artifacts\data\security_gate\caltech20_diverse `
               <COCO_VAL2017_DIR> `
  --checkpoint 05_artifacts\models\etehgan_v3_stegaware018_stat05_adv001_e3.pt `
  --payload-bpp 0.0075 `
  --payload-fraction 1.0 `
  --ecc-bytes 32 `
  --nsize 128 `
  --packet-seed 7 `
  --max-images 40 `
  --accept-fraction 0.25 `
  --out-csv 05_artifacts\results\tables\ethegan_detectability_gate_40_00075_n128e32_accept25.csv `
  --out-json 05_artifacts\results\raw\ethegan_detectability_gate_40_00075_n128e32_accept25.json
```

This mode accepts only images with the lowest cover-stego feature displacement.
In the recorded 40-image run it accepts 10 images, recovers all accepted
payloads, and reports test AUC 0.58 for the simple detector and 0.52 for the
SPAM-style detector. This supports only a low-payload, accepted-image,
detector-bounded passive-security claim.

## V3 Steganalysis-Aware Training

`train_v3_stegaware.py` adds:

- differentiable residual-statistics regularization;
- a small residual-domain cover/stego discriminator;
- adversarial encoder loss against that discriminator.

Example:

```powershell
python 05_artifacts\code\etehgan\train_v3_stegaware.py `
  --image-root <CALTECH101_IMAGES_DIR> `
               <COCO_VAL2017_DIR> `
  --output 05_artifacts\models\etehgan_v3_stegaware018_stat05_adv001_e3.pt `
  --init-checkpoint 05_artifacts\models\etehgan_v3_residual018_img16_caltech20_coco20_e5.pt `
  --epochs 3 `
  --payload-bpp 0.25 `
  --lambda-image 16.0 `
  --lambda-stat 0.5 `
  --lambda-adv 0.01 `
  --disc-steps 1 `
  --encoder-mode residual `
  --residual-strength 0.18 `
  --max-images-per-root 20
```

This loss improves the first simple-detector result but does not establish
steganographic security.

## V3 Attack-Aware Robustness Probe

`train_attack_aware.py` fine-tunes the encoder and decoder with clean
extraction, attacked-image extraction, image-fidelity, and residual-statistics
losses. It supports `--resume-checkpoint` for interrupted runs.

Example resume command:

```powershell
python 05_artifacts\code\etehgan\train_attack_aware.py `
  --image-root <CALTECH101_IMAGES_DIR> `
               <COCO_VAL2017_DIR> `
  --output 05_artifacts\models\ethegan_attackaware_005_small_e2.pt `
  --resume-checkpoint 05_artifacts\models\ethegan_attackaware_005_small_e2_epoch1.pt `
  --epochs 2 `
  --payload-bpp 0.05 `
  --lambda-clean 0.5 `
  --lambda-attack 1.5 `
  --lambda-image 18.0 `
  --lambda-stat 0.2 `
  --encoder-mode residual `
  --residual-strength 0.18 `
  --attacks clean jpeg95 blur resize `
  --max-images-per-root 4
```

The first small run preserved clean-channel recovery but did not recover any
held-out payloads after JPEG95, blur1, or resize0.75. Treat it as negative
robustness evidence, not as a manuscript checkpoint.

## Claim-Gating Audits

Public baseline executability audit:

```powershell
python tools\audit_public_baselines.py
```

Confidentiality mechanism audit:

```powershell
python tools\audit_confidentiality_support.py
```

Local reproducibility manifest with SHA256 hashes:

```powershell
python tools\freeze_reproducibility_manifest.py
```

AES-GCM confidentiality self-test:

```powershell
python 05_artifacts\code\etehgan\secure_payload.py `
  --out-json 05_artifacts\results\raw\aead_self_test.json
```

Equal-effective-bpp benchmark:

```powershell
python tools\run_equal_bpp_benchmark.py `
  --image-root 05_artifacts\data\security_gate\caltech20_diverse `
               <COCO_VAL2017_DIR> `
  --ethegan-attacks-json 05_artifacts\results\raw\ethegan_equalbpp_40_00075_n128e32_attacks.json `
  --ethegan-gate-json 05_artifacts\results\raw\ethegan_detectability_gate_40_00075_n128e32_accept25.json
```

The confidentiality audit supports confidentiality only when AEAD self-tests
pass. Payload confidentiality requires AES-GCM encryption before packetization
and wrong-key authentication failure.
