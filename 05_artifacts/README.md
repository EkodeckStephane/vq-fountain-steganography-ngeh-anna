# Artifacts

This folder contains code, data, models, and results for the article.

## Active Package

```text
05_artifacts/
  code/
    vq_fountain/
      vq_fountain/
      tests/
      README.md
```

The active package starts with model-independent infrastructure:

- payload bit packing and CRC;
- sparse rateless fountain coding;
- keyed token scheduling;
- synthetic token-channel evaluation.

The first milestone is a passing synthetic benchmark before adding a real VQ
tokenizer or image generator.

Stage 1 now includes a local `patch-vq` tokenizer baseline for measuring token
stability and token-space recovery. This is a protocol scaffold, not the final
learned VQ tokenizer.

Stage 1 also includes a learned patch-VQ codebook and distribution-aware token
sampler probe. It removes the stability oracle but still produces patch-token
mosaics, not natural generated images.

Stage 2 now includes a public VQGAN f4-8192 path. The old checkpoint is
converted to a modern `diffusers.VQModel`, then
`run_real_vqgan_payload_probe.py` tests conservative calibrated macro-cell
payload recovery through generated VQGAN images. The current grouped setting
packs multiple short fountain symbols per image and recovers 32 B across
multiple payload/test seeds.

## Legacy Package

```text
05_artifacts/code/etehgan/
```

ETEHGAN code and results are preserved for traceability and negative evidence.
They are not the active Q1 method.

## Data Policy

- Keep raw experimental outputs that support reported results.
- Keep checkpoints only when they are referenced by result notes or reproduce a
  table.
- Remove generated caches and temporary build outputs.
- Do not put API keys, unpublished manuscript text, or private side-channel data
  into public artifacts.
