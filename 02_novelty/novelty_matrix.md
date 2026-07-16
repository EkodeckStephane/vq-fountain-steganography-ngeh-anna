# Novelty Matrix

Status: legacy ETHEGAN matrix. Use
`02_novelty/recommended_orientation.md` as the active novelty framing.

Target article direction:

> Reliability-aware auxiliary-channel-free neural image steganography, with a
> self-contained packet layer and verified exact extraction from the stego image
> alone under a reproducible evaluation protocol.

The contribution must be positioned against WYSAWIS and recent deep-learning steganography without overclaiming coverless generation unless the implementation actually synthesizes images from message and noise alone.

## Candidate Novelty Claims

| Claim ID | Candidate Claim | Competing Work | Why It May Be Novel | Evidence Required | Risk If Unsupported |
|---|---|---|---|---|---|
| N1 | Removes WYSAWIS auxiliary cloud channel by embedding the location/payload information into a single transmitted image. | WYSAWIS2025 | WYSAWIS still requires cloud-based location information; the proposed system must require only the stego image and shared model/key. | End-to-end extraction with no cloud, no side metadata, no original cover transmitted to receiver. | Rejected as incremental or falsely positioned. |
| N2 | Replaces external location metadata with a self-contained packet containing length, CRC, ECC, and deterministic interleaving. | WYSAWIS2025; neural steganography with raw bit reporting | The receiver obtains the recovery-critical packet fields from the image bitstream itself rather than relying on an external sequence of locations. | End-to-end exact recovery, CRC validation, and image-only packet decoding across images. | Weak novelty if the packet is treated as ordinary engineering and not tied to the WYSAWIS gap. |
| N3 | Reports effective user payload rather than nominal neural bitstream capacity. | High-capacity steganography papers with uneven accounting | Separates payload bytes from header/ECC/padding/failures, making capacity claims auditable. | Tables with nominal bpp, effective bpp, overhead, exact recovery, and failures. | "Lack of sufficient novelty" if no fair comparison or if capacity is too low. |
| N4 | Uses decoder-logit reliability for optional erasure-assisted Reed-Solomon recovery. | Deep image steganography methods | Potential method-level novelty only if it improves exact recovery under controlled ablations. | Hard-decoding vs erasure-decoding ablation across payload rates and attacks. | Must be downgraded if erasures do not improve results. |
| N5 | Establishes a reviewer-grade benchmark protocol for auxiliary-channel-free reliable image payload recovery. | Existing papers with uneven protocols | A strong benchmark contribution can compensate for moderate algorithmic novelty. | Public code, datasets, scripts, fixed splits, steganalysis baselines, repeated runs. | Not enough for Q1 if no new method or no strong empirical finding. |

## Preferred Novelty Position

The safest Q1-oriented novelty is not "we invented GAN steganography." That claim is already crowded.

The stronger angle is:

> A reproducible auxiliary-channel-free neural steganography framework that
> directly targets WYSAWIS's external metadata dependency through a
> self-contained packet layer, and evaluates the exact-recovery, capacity,
> fidelity, robustness, and security frontier under a fair protocol.

This should be supported by a method that is technically modest but rigorously validated.
