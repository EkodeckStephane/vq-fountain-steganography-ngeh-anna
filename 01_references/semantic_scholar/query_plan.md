# Semantic Scholar Query Plan

API key use policy:

- The key is used only from the runtime environment.
- The key must not be committed to any file.
- Respect the approved rate limit: at most 1 request per second.

Core queries:

1. `coverless image steganography generative adversarial network high capacity`
2. `coverless image steganography image synthesis GAN`
3. `deep learning image steganography high capacity robust extraction`
4. `neural image steganography high capacity robustness steganalysis`
5. `generative steganography without cover image extraction network`
6. `image steganography steganalysis deep learning high payload`

Fields to collect:

- title
- authors
- year
- venue
- DOI
- URL
- abstract
- citation count
- influential citation count
- open access PDF

Screening criteria:

- Keep papers directly related to image steganography, coverless steganography, GAN/diffusion/flow-based generation, high-capacity payload extraction, and steganalysis.
- Exclude unrelated audio/video/text-only methods unless used to justify taxonomy.
- Mark papers as `primary baseline`, `related baseline`, `state-of-the-art detector`, `dataset/protocol`, or `background`.

