# Threat Model

Status: working version for manuscript development.

## System Roles

- Sender: owns the secret payload and generates one stego image.
- Receiver: receives the stego image and uses the shared extraction model to recover the payload.
- Passive adversary: observes transmitted image files and may run visual inspection, statistical tests, or steganalysis detectors.
- Active adversary: can additionally apply common image transformations such as compression, resizing, blur, noise, or cropping.

## Shared Material

Allowed shared material:

- model architecture;
- trained model weights;
- optional key or random seed if later added;
- payload/ECC specification.

Not allowed for the core claim:

- WYSAWIS-style cloud folder positions;
- external location metadata;
- side channel carrying block or sequence indices;
- original cover image at receiver, unless explicitly declared as part of a weaker scenario.

## Core Security Goal

The core operational goal is not formal cryptographic secrecy.

The core goal is:

> The receiver can extract the payload from the transmitted stego image without an auxiliary location channel, while the transmitted image remains hard to distinguish from normal images under the evaluated adversary model.

## Claims That Require Evidence

| Claim | Required Evidence |
|---|---|
| No auxiliary channel | Receiver-side extraction command uses only stego image and shared model/key. |
| Payload confidentiality | Either encrypted payload before embedding or explicit statement that confidentiality is outside scope. |
| Steganographic security | Detection rates/AUC from contemporary steganalysis baselines. |
| Robustness | BER/BCR/exact recovery after named transformations. |
| Imperceptibility | PSNR, SSIM, LPIPS, visual examples, and detector results. |

## Non-Claims

Until proven, the paper must not claim:

- unconditional undetectability;
- cryptographic security;
- security against a white-box adversary with model weights unless tested;
- robustness to arbitrary social media recompression;
- coverless operation if a cover image is used by the sender.

## WYSAWIS-Specific Adversary Contrast

In WYSAWIS, an adversary may observe:

- the unchanged stego image;
- the shared cloud account activity if compromised or monitored;
- repeated files in the stego-folder for repeated message segments.

The target ETEHGAN contribution removes the cloud-observable artifact from the transmission path. This does not automatically prove image-level undetectability; that must be tested separately.

