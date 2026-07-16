# VQ-Fountain Steganography: Distribution-Preserving Coverless Image Generation with In-Band Rateless Recovery

## Abstract

Coverless image steganography aims to transmit hidden messages through images
that are generated rather than modified from a pre-existing cover. Recent
generative, diffusion, and VQ-based methods show that this setting is feasible,
but the most useful operating point remains difficult: the receiver should
recover a multi-byte payload from the received images alone, without a
regenerated cover, cloud index, text side channel, or image-specific metadata,
while preserving robustness under lossy image processing. This paper introduces
VQ-Fountain, a coverless steganographic framework that embeds packetized
payload symbols through key-conditioned VQ value-channel choices and recovers
them with an in-band rateless layer. The method combines distribution-aware
projection binning, calibrated stable token pools, spatial synchronization
anchors, symbol CRCs, and fountain coding across generated images. On a public
VQGAN f4-8192 checkpoint, VQ-Fountain recovers 64 B exactly across three
independent payload seeds under both clean transmission and
crop090+jpeg85+drop25, using 48 generated images. A 128x128 feasibility probe
recovers 16 B exactly under the same hard combined channel, and a second public
VQModel, `CompVis/ldm-celebahq-256/vqvae`, recovers 16 B exactly under clean
and crop090+jpeg85+drop25. Local steganalysis probes on 144 payload and 144
reference VQGAN images report feature-detector AUC 0.48862745, small-CNN AUC
0.53320000, SPAM-style residual AUC 0.52627451, and SRM-style residual
cooccurrence mean AUC 0.49521569 across five splits. The evidence supports a
bounded feasibility claim for in-band, auxiliary-channel-free, coverless VQ
steganography under the tested public VQModel settings.

Keywords: coverless steganography, VQGAN, image generation, fountain coding,
robust payload recovery, steganalysis.

## 1. Introduction

Image steganography traditionally hides a message by modifying a cover image.
That paradigm gives the sender a concrete carrier, but it also creates a
statistical comparison problem: the stego image must remain close enough to the
cover distribution to avoid detection. Coverless image steganography changes
the premise. Instead of modifying an existing cover, the sender generates an
image whose generation process encodes the secret. The observer sees a
generated image, and the receiver decodes the message using shared model and
key assumptions.

This coverless setting is attractive, but it introduces a difficult reliability
problem. Generated images are commonly transmitted through lossy channels:
JPEG compression, resizing, blur, noise, cropping, and partial image loss.
Token identities inside a VQ generator are not preserved after decoding,
processing, and re-encoding. A practical coverless method therefore cannot
assume exact token-ID preservation. It must recover a robust value channel from
images and must tolerate erasures and corrupted observations.

Several public works have advanced the area. GSN showed that generated images
can directly carry secret data. Cs-FNNS uses generated covers and cover
separation. CMSteg uses VQ/AR generation and cross-modal error correction.
MIDAS uses diffusion generation for multi-image coverless hiding with access
control. Robust watermarking methods such as Tree-Ring Watermarks and Stable
Signature demonstrate that generative image pipelines can carry persistent
signals. These systems make broad novelty claims unsafe. The useful gap is more
specific: in-band, auxiliary-channel-free payload recovery from generated
images, with explicit effective-capacity accounting and robustness under lossy
image processing.

VQ-Fountain targets this gap. It treats the VQ generation process as a
payload-bearing value channel rather than a token-ID channel. A secret payload
is packetized, split into small source blocks, encoded as rateless symbols, and
embedded into generated images through calibrated token choices. The receiver
extracts noisy value observations from the received images, validates symbols
with CRCs, treats invalid observations as erasures, and solves the fountain
decoding problem when enough valid symbols are available.

The main contributions are:

1. A coverless VQ steganography formulation based on distribution-aware value
   sampling rather than cover modification.
2. An in-band packet, symbol-CRC, anchor, and fountain recovery layer that does
   not require a text side channel, regenerated cover, cloud index, or
   per-image metadata.
3. A calibrated real-VQGAN value-channel implementation that does not rely on
   token-ID preservation.
4. A reproducible evaluation protocol reporting exact recovery, effective
   payload, image count, attack setting, detector metrics, and non-coverless
   executable baselines.

The paper deliberately avoids stronger claims. It does not claim
undetectability, universal robustness, or final state-of-the-art superiority.
It reports the measured operating points and the current limits.

## 2. Related Work

Generative Steganography Network introduced direct image generation from secret
data and showed that coverless generative steganography is a credible research
direction. Its generator/extractor formulation establishes an important
baseline, but it also means that a new method must be positioned more narrowly
than "first generative steganography."

Cs-FNNS improves fixed neural network steganography by separating a generated
cover from a perturbation recovered by the receiver. This gives strong visual
quality but uses a different assumption: the receiver reproduces or separates
the cover. VQ-Fountain instead recovers from the transmitted images and shared
model/key assumptions without regenerating a cover image for subtraction.

CMSteg is a strong VQ/AR generated-image robustness comparator. It uses
cross-modal error correction, generating stego text from stego images to aid
restoration after lossy social-network processing. VQ-Fountain differs in the
recovery contract: all recovery-critical information is in-band in the image
sequence.

MIDAS studies training-free diffusion coverless multi-image hiding with access
control. It is a strong 2026 multi-image comparator, especially for user
authorization. VQ-Fountain does not claim access-control novelty; its focus is
rateless in-band recovery from VQ value observations.

Latent iterative optimization methods improve robustness under lossy channels
by refining latent variables during decoding. This is an important robustness
reference, but it makes a different compute and decoding trade-off. VQ-Fountain
uses packet redundancy, CRC filtering, and fountain decoding rather than
iterative latent refinement.

Robust learned hiding methods such as HiDDeN and StegaStamp remain important,
but they are not coverless. They modify or watermark cover images and therefore
must be reported separately. In this work, HiDDeN is included as an executable
public-checkpoint smoke baseline, DCT-spread is included as a classical
transform-domain executable baseline, and StegaStamp is kept as a paper/code
comparator until a compatible SavedModel runtime is available.

## 3. Problem and Threat Model

The sender and receiver share:

- the public generative VQ model;
- a secret key controlling symbol placement and token selection;
- public packet parameters such as block size, redundancy, and attack
  synchronization assumptions.

The sender does not use a cover image. The receiver does not receive the
original latent grid, token sequence, text side channel, cloud lookup index, or
per-image metadata. The transmitted object is a sequence of generated images.

The channel may apply:

- JPEG compression;
- resizing;
- blur;
- additive noise;
- cropping with offset;
- partial image drops;
- selected combinations of the above.

The adversary is passive and sees the transmitted images. The current
evaluation measures detector separability using local feature-level,
small-CNN, and SPAM-style probes. It does not claim security against all
possible steganalyzers.

## 4. Method

### 4.1 Payload Packet

The user message is converted into a packet containing the payload length,
payload bytes, integrity checks, and decoding-critical fields. The packet is
split into source blocks. This accounting distinguishes user payload from
header, CRC, redundancy, anchors, and erasures.

### 4.2 Fountain Encoding

The source blocks are encoded into a larger set of rateless symbols. Each
symbol carries:

- a symbol identifier generated from the shared key;
- a small payload block or XOR combination of source blocks;
- a symbol CRC.

At the receiver, symbols that fail the CRC are discarded. The decoder solves
the source block system once enough valid symbols have survived the channel.
This makes corrupted observations behave like erasures rather than silently
poisoning the recovered payload.

### 4.3 VQ Value Channel

A naive design would map payload bits directly to VQ token IDs. Real VQGAN
experiments show that this is not reliable: token identity match is near zero
after image decoding and re-encoding. VQ-Fountain instead uses a value channel.
Tokens are assigned to value bins, and the receiver extracts the value of a
received token rather than requiring the original token ID.

For the real VQGAN probes, the implemented value channel uses one bit per
macro-cell. Tokens are calibrated into stable pools for value 0 and value 1.
The generator fills macro-cells with tokens from the appropriate stable pool.
After attack and re-encoding, each macro-cell votes on the received value.

### 4.4 Distribution-Aware Projection Binning

Payload-bearing token choices must not create an obvious distribution shift.
VQ-Fountain therefore uses projection-based binning over codebook vectors. The
goal is to choose token sets that preserve a plausible token distribution while
still giving the receiver a decodable value channel.

In the final ablation suite, projection binning recovers the 64 B Stage 1
crop-offset case, while naive token modulo mapping fails with only 7 exact
symbols and 69 missing source blocks.

### 4.5 Spatial Synchronization

Cropping changes spatial alignment. VQ-Fountain uses spatial anchors to
estimate crop ratio and 2D offset, then decodes macro-cells in the corrected
coordinate system. Block anchors and global anchors are both evaluated. The
final Stage 1 crop-offset setting uses block anchors and center scheduling for
robust recovery.

### 4.6 Receiver

The receiver:

1. re-encodes each received image through the VQ tokenizer;
2. estimates geometric synchronization where needed;
3. extracts macro-cell value observations;
4. reconstructs candidate symbols;
5. discards CRC-invalid symbols;
6. fountain-decodes the packet;
7. verifies payload integrity.

## 5. Experimental Protocol

The evaluation is split into two layers.

Stage 1 uses a learned patch-VQ token channel. It is useful for stress testing
packet coding, scheduling, binning, anchors, image drops, and attack
combinations at larger scale. Stage 1 results are not presented as final
real-generator claims.

Stage 2 uses public VQModel checkpoints. It tests whether the value-channel
formulation works when images are decoded from VQ tokens and later re-encoded.
The main public checkpoint is a converted VQGAN f4-8192 model. A second public
checkpoint, `CompVis/ldm-celebahq-256/vqvae`, is used to test that the result
is not restricted to one VQModel.

The main metrics are:

- exact payload recovery;
- payload bytes and packet bytes;
- encoded symbols and valid CRC symbols;
- image count;
- attack condition;
- token-match rate and value-match rate;
- detector AUC and accuracy;
- baseline recovery metrics.

## 6. Results

### 6.1 Stage 1 Ablations

The final Stage 1 ablation suite evaluates a 64 B payload under offset crop
with crop ratio 0.90 and offsets 0.02, -0.02.

| Ablation | Variant | Exact recovery | Key observation |
|---|---|---:|---|
| Coding | fountain | true | Recovers despite CRC rejections and crop-offset loss. |
| Coding | repetition | false | Stops with 12 missing source blocks. |
| Sampling | projection | true | Distribution-aware value mapping is sufficient. |
| Sampling | naive | false | Stops with 69 missing source blocks. |
| Schedule | center | true | More robust under crop-offset geometry. |
| Schedule | random | false | Stops with 5 missing source blocks. |

These results support the use of fountain coding, projection binning, and
structured scheduling. They are Stage 1 token-channel evidence, not final
public-generator evidence.

### 6.2 Stage 1 Robustness and Cost

For 32 B in the Stage 1 crop-offset setting, exact recovery is obtained with
overhead 2.0 and 8 images. For 64 B under the hardest crop+jpeg+drop25
condition, exact recovery requires overhead 4.0 and 24 images.

The combined-attack table shows exact recovery under JPEG85+blur1,
JPEG85+noise002, crop090+JPEG85, crop090+resize075, crop090+JPEG85+noise002,
and drop25 for the measured settings. The hardest crop090+JPEG85+drop25
condition requires additional redundancy.

### 6.3 Real VQGAN 64 B Payload

The main Stage 2 public VQGAN setting uses:

- payload: 64 B;
- packet: 76 B;
- one value bit per macro-cell;
- 2x2 macro-cells;
- 64 macro-cells per image;
- 8 symbols per image;
- overhead: 4.0;
- images: 48;
- calibration seed separated from three payload/test seeds.

| Attack | Test seeds | Image count | CRC-valid symbols | Exact recovery |
|---|---:|---:|---:|---:|
| clean | 3 | 48 | 371-373 | true for all seeds |
| crop090+jpeg85+drop25 | 3 | 48 | 97-111 | true for all seeds |

Token identity match is approximately zero, while value match remains high
enough for CRC-filtered fountain recovery. This supports the central design
choice: the method recovers a value channel, not exact token IDs. A smaller
32 B setting also recovers exactly across three seeds with overhead 3.0 and 22
images.

### 6.4 128x128 Feasibility

A 128x128 public VQGAN feasibility probe uses a 32x32 latent grid, 4x4
macro-cells, 16 B payload, overhead 3.0, and 14 images.

| Attack | Recovered symbols | CRC-valid symbols | Exact recovery |
|---|---:|---:|---:|
| clean | 112 | 108 | true |
| crop090+jpeg85+drop25 | 72 | 49 | true |

This lifts the strict 64x64-only limitation for a measured feasibility setting.

### 6.5 Second Public VQModel

The second public checkpoint is `CompVis/ldm-celebahq-256/vqvae`. It uses the
same recovery stack.

| Attack | Payload | Images | CRC-valid symbols | Exact recovery |
|---|---:|---:|---:|---:|
| clean | 16 B | 14 | 111 | true |
| crop090+jpeg85+drop25 | 16 B | 14 | 37 | true |

This lifts the single-checkpoint limitation for a second measured VQModel
setting.

### 6.6 Steganalysis Probes

Four local detectors compare 144 payload images against 144 reference images
generated from the same calibrated VQGAN token family.

| Detector | AUC | Accuracy |
|---|---:|---:|
| Feature-level logistic detector | 0.48862745 | 0.53465347 |
| Small CNN | 0.53320000 | 0.57000000 |
| SPAM-style residual cooccurrence | 0.52627451 | 0.50495050 |
| SRM-style residual cooccurrence | 0.49521569 | 0.49702970 |

The results do not show a strong local detector separation in these measured
settings. They do not prove undetectability. The SRM-style row is a local
residual-cooccurrence implementation, not an official external SRNet result, so
the security claim is bounded to the reported detectors.

### 6.7 Executable Non-Coverless Baselines

HiDDeN is evaluated via a public checkpoint and a compatibility runner.

| Baseline | Payload | Trials | Mean BER | Exact recoveries |
|---|---:|---:|---:|---:|
| HiDDeN | 30 bits | 5 | 0.31333333 | 0/5 |

DCT-spread is evaluated as a classical transform-domain baseline.

| Attack | Payload | PSNR | Exact recovery | BER |
|---|---:|---:|---:|---:|
| clean | 32 bits | 37.916521 | true | 0.0 |
| JPEG85 | 32 bits | 37.916521 | true | 0.0 |
| resize075 | 32 bits | 37.916521 | true | 0.0 |
| blur1 | 32 bits | 37.916521 | true | 0.0 |
| crop090 | 32 bits | 37.916521 | false | 0.5 |

These baselines are not coverless and are not used to claim same-assumption
superiority. They are used to provide executable robustness references.

## 7. SOTA Positioning

VQ-Fountain is original at the intersection of four constraints:

1. the image is generated rather than modified from a cover;
2. the embedded message is recovered in-band from the received images;
3. VQ token choices are distribution-aware and calibrated for a robust value
   channel;
4. recovery uses packet validation and rateless decoding across image sequences.

No single component is individually unique. VQ generators, coverless
steganography, robust watermarking, and fountain codes are established ideas.
The contribution is their combination into an auxiliary-channel-free VQ
generation protocol with exact-recovery accounting and measured real-VQGAN
evidence.

The current evidence is competitive as a feasibility result because it
demonstrates exact multi-byte payload recovery under severe combined processing
and image drops, includes two public VQModel checkpoints, reports four local
detector families, and adds executable non-coverless baselines. It is not
presented as a final SOTA-superiority result. Public SOTA code can be
reproduced later under a shared payload, quality, attack, and detector protocol
without changing the central claim of this paper.

## 8. Limitations

The main limitations are:

- public-generator coverage is limited to two substantive VQModel checkpoints;
- official external SRNet-style steganalysis and a local StegaStamp score are
  not claimed;
- real-VQGAN capacity is measured up to 64 B in the main grouped setting;
- token-ID preservation is not achieved and is not claimed;
- the geometry model uses discrete crop/offset assumptions;
- the current implementation is a research prototype rather than an optimized
  communication system.

These limits should appear explicitly in any submission draft.

## 9. Conclusion

VQ-Fountain provides a measured route to coverless VQ steganography with
in-band rateless recovery. The key empirical result is that exact payload
recovery can be achieved even when token IDs are not preserved, provided the
system uses calibrated value channels, CRC-based erasure filtering, spatial
synchronization, and fountain decoding. On public VQModel checkpoints, the
method recovers 64 B across three seeds under clean and crop090+jpeg85+drop25
for the main VQGAN setting, and 16 B on a second public VQModel. Local
feature, CNN, SPAM-style, and SRM-style steganalysis probes do not show strong
separation, and executable baselines are now available for comparison. Broader
public SOTA reproduction and official external steganalysis remain useful
follow-up work, but the present claim is already bounded to the measured
feasibility setting.

## References

- Generative Steganography Network: https://arxiv.org/abs/2207.13867
- DiffStega: https://arxiv.org/abs/2407.10459
- Cover-separable Fixed Neural Network Steganography: https://arxiv.org/abs/2407.11405
- Provably Secure Robust Image Steganography via Cross-Modal Error Correction: https://arxiv.org/abs/2412.12206
- Training-Free Coverless Multi-Image Steganography with Access Control: https://arxiv.org/abs/2603.09390
- Robust Provably Secure Image Steganography via Latent Iterative Optimization: https://arxiv.org/abs/2603.09348
- Tree-Ring Watermarks: https://arxiv.org/abs/2305.20030
- The Stable Signature: https://arxiv.org/abs/2303.15435
- HiDDeN: https://arxiv.org/abs/1807.09937
- StegaStamp: https://arxiv.org/abs/1904.05343
