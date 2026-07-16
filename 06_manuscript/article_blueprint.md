# Article Blueprint

Status: legacy ETHEGAN blueprint. A VQ-Fountain manuscript blueprint must be
written before drafting the active paper.

## Abstract Logic

1. State the WYSAWIS problem: high-capacity coverless indexing still requires auxiliary cloud-carried location information and can expose repeated-segment artifacts.
2. State the proposed answer: auxiliary-channel-free neural embedding with a self-contained packet layer and learned extraction.
3. State what is evaluated: exact recovery, effective user payload, fidelity, robustness limits, steganalysis, repeated payloads, and reproducibility.
4. State measured results only after experiments are complete.

## Section Plan

1. Introduction
   - problem
   - WYSAWIS limitations
   - why generic GAN steganography is not enough
   - contributions

2. Related Work
   - cover modification steganography
   - cover selection and coverless steganography
   - WYSAWIS and indexing-based high capacity
   - generative/neural image steganography
   - steganalysis and robustness

3. Threat Model and Problem Definition
   - sender/receiver assumptions
   - adversary capabilities
   - what is shared
   - what is transmitted
   - what is not claimed

4. Proposed Method
   - payload preparation
   - V3 packet header, CRC, ECC, and interleaving
   - neural hiding network
   - extraction network
   - exact recovery and effective-payload accounting
   - training losses
   - inference protocol

5. Experimental Protocol
   - datasets
   - baselines
   - payload rates
   - attacks
   - metrics
   - statistics

6. Results
   - main comparison
   - effective-payload-quality curve
   - exact recovery curve
   - robustness
   - steganalysis
   - repeated payload stress test
   - ablations
   - efficiency

7. Discussion
   - what is solved relative to WYSAWIS
   - what remains unsolved
   - security limits
   - deployment assumptions

8. Reproducibility
   - code
   - data
   - commands
   - seeds

9. Conclusion

## Contribution Template

Use this template only after experiments support it:

1. We formalize the operational leakage introduced by auxiliary location channels in WYSAWIS-style high-capacity coverless steganography.
2. We propose ETEHGAN v3, an auxiliary-channel-free neural image steganography pipeline with a self-contained packet layer recoverable from the stego image.
3. We introduce a reproducible evaluation protocol for reliable neural image payload recovery, reporting nominal payload, effective payload, raw BER, exact recovery after ECC/CRC, perceptual quality, robustness limits, steganalysis detectability, and repeated-payload behavior.
4. We provide code, models, fixed data splits, and scripts to regenerate the reported tables and figures.
