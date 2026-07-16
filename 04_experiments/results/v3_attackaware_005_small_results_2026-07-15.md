# V3 Attack-Aware 0.05 Small Results - 2026-07-15

## Objective

Test whether a small attack-aware fine-tune can improve active-transformation
recovery by training the extractor on clean, JPEG-like, blur, and resize
surrogates.

This is a robustness experiment, not a manuscript-ready replacement for the
0.25 bpp clean-channel operating point.

## Implemented Code

Added:

- `05_artifacts/code/etehgan/train_attack_aware.py`

The script fine-tunes the encoder and decoder with:

- clean extraction loss;
- attacked-image extraction loss;
- image MSE loss;
- residual-statistics loss.

It also supports `--resume-checkpoint`, so interrupted epoch checkpoints can be
continued without overwriting earlier epoch outputs.

## Trained Checkpoint

`05_artifacts/models/ethegan_attackaware_005_small_e2.pt`

Training setup:

- initialized from `etehgan_v3_stegaware018_stat05_adv001_e3.pt`;
- resumed from `ethegan_attackaware_005_small_e2_epoch1.pt`;
- target epochs: 2;
- residual strength: 0.18;
- payload: 0.05 nominal bpp;
- ECC: 128 bytes for evaluation;
- lambda clean: 0.5;
- lambda attack: 1.5;
- lambda image: 18.0;
- lambda stat: 0.2;
- attacks sampled during training: clean, JPEG95 surrogate, blur, resize;
- training images: 4 Caltech101 + 4 COCO.

Final epoch metrics:

- clean BER: 0.0026989396;
- attack BER: 0.1588178081;
- clean extraction loss: 0.1111889547;
- attack extraction loss: 0.3715308914;
- image loss: 0.0004729746;
- stat loss: 0.0017036982.

## Held-Out Packet Evaluation

Evaluation uses:

- nominal payload: 0.05 bpp;
- effective user payload: 0.0222778320 bpp;
- payload bytes: 730;
- ECC: 128 bytes;
- packet seed: 7;
- held-out offset: 20;
- 20 images per dataset.

| Dataset | Attack | Exact recovery | Mean raw BER | Max raw BER | Mean PSNR | Mean global SSIM |
|---|---|---:|---:|---:|---:|---:|
| Caltech101 | clean | 20/20 | 0.0018391331 | 0.0067155067 | 41.8746 dB | 0.9995717 |
| Caltech101 | jpeg95 | 0/20 | 0.4455433455 | 0.4698565324 | 41.8746 dB | 0.9995717 |
| Caltech101 | blur1 | 0/20 | 0.2744429182 | 0.3679792430 | 41.8746 dB | 0.9995717 |
| Caltech101 | resize0.75 | 0/20 | 0.1821619353 | 0.2224511600 | 41.8746 dB | 0.9995717 |
| COCO val2017 | clean | 20/20 | 0.0062347375 | 0.0204517705 | 40.6681 dB | 0.9992122 |
| COCO val2017 | jpeg95 | 0/20 | 0.4376984127 | 0.4543650794 | 40.6681 dB | 0.9992122 |
| COCO val2017 | blur1 | 0/20 | 0.2740117521 | 0.3182997558 | 40.6681 dB | 0.9992122 |
| COCO val2017 | resize0.75 | 0/20 | 0.1785027473 | 0.2019993895 | 40.6681 dB | 0.9992122 |

Raw result files:

- `05_artifacts/results/raw/attackaware_005_small_e2_caltech20_005_ecc128_attacks.json`
- `05_artifacts/results/raw/attackaware_005_small_e2_coco20_005_ecc128_attacks.json`

## Interpretation

The small attack-aware run preserves clean-channel recovery at a lower payload
rate and improves visual quality because the effective user payload is much
smaller. It does not solve active-transformation recovery: JPEG95, blur1, and
resize0.75 all remain 0/20 exact recoveries on both held-out datasets.

Reviewer-safe conclusion:

> A two-epoch, eight-image attack-aware fine-tune at 0.05 nominal bpp does not
> establish robustness. Robust-channel claims must remain excluded until a
> stronger synchronization-aware or transformation-aware method is developed.

## Decision

Do not replace the current manuscript checkpoint with
`ethegan_attackaware_005_small_e2.pt`.

The next robustness attempt should change the method, not only repeat this
small surrogate fine-tune. Candidate directions:

1. train on larger data with explicit validation gates;
2. add synchronization-aware decoding for resize/blur;
3. evaluate differentiable JPEG surrogates against real JPEG at every epoch;
4. lower the payload further only if the claim is explicitly low-capacity
   robust recovery.
