# Reliability-Aware Auxiliary-Channel-Free Neural Image Steganography with Self-Contained Payload Recovery

Status: legacy draft. Do not submit or cite as the active VQ-Fountain Stega
manuscript without a full rewrite.

Authors: to be completed

Manuscript status: technical draft v1, prepared from the current reproducible
artifact and experimental logs. This draft intentionally avoids claims that are
not yet supported by the available experiments.

## Abstract

Recent coverless and generative image steganography methods have reduced the
need to directly modify classical cover images, but operational side channels
remain a practical source of leakage in some high-capacity schemes. WYSAWIS, a
recent high-capacity coverless approach based on block-level hash encoding and
sequence category mapping, avoids pixel modification but relies on
cloud-carried location information for extraction. This paper studies a
different operating point: reliable payload recovery from a single transmitted
image without WYSAWIS-style folder positions, block index lists, or external
location metadata. We propose ETEHGAN v3, an auxiliary-channel-free neural image
steganography framework with a self-contained packet layer containing payload
length, CRC32 validation, Reed-Solomon parity, deterministic interleaving, and
optional reliability-aware erasure decoding. To reduce visible and statistical
embedding artifacts, we further introduce residual-statistics regularization
and a lightweight adversarial residual-domain discriminator during training.
Using fixed Caltech101 and COCO val2017 subsets, the current best checkpoint
recovers all evaluated payloads exactly on 50/50 Caltech101 and 50/50 COCO
clean-channel test images at 0.25 nominal bpp, corresponding to 0.185546875
effective user bpp after packet and ECC overhead. It reaches mean PSNR of
38.77 dB on Caltech101 and 37.58 dB on COCO under this setting. A lightweight
residual/LSB detector remains effective, with test AUC 0.963750 on Caltech101
and 0.918125 on COCO, and common transformations such as JPEG compression,
blur, and resizing still break recovery. The results therefore support
clean-channel, auxiliary-channel-free payload recovery with effective-capacity
accounting as the current contribution, but
do not support claims of steganographic security or robustness to image
processing.

Keywords: image steganography; neural steganography; auxiliary-channel-free
communication; exact payload recovery; error correction; steganalysis-aware
training.

## 1. Introduction

Image steganography is often evaluated through payload size, visual quality,
bit recovery, and detectability. In practice, however, the communication
protocol surrounding an image can be as important as the image itself. A method
may avoid modifying a cover image and still rely on auxiliary information such
as cloud folder positions, sequence indices, file ordering, or block-location
metadata. Such auxiliary channels can become operational leakage points when an
adversary observes the storage environment, repeated uploads, or metadata
needed by the receiver.

WYSAWIS is a useful example of this issue. It provides a high-capacity
coverless image steganography mechanism based on block-level hash encoding and
sequence category mapping [1]. Its strength is that it avoids direct image
modification. Its operational limitation is that recovery depends on
cloud-carried location information, and repeated message segments can induce
repeated observable artifacts in the stego-file organization. This paper does
not attempt to relabel such a system as insecure. Instead, it isolates a
specific open problem: can the receiver recover the payload from one transmitted
image without a WYSAWIS-style auxiliary location channel?

The literature already contains multiple GAN-based, generative, invertible, and
coverless steganography systems [2]-[12]. Therefore, the novelty of the present
work is not "using a GAN for steganography" or "being the first coverless
method." The current prototype also uses a cover image at the sender, so it is
not a strict coverless generator. The contribution is narrower: a neural image
steganography pipeline that replaces external location metadata with a
self-contained packet recovered from the stego image itself, and evaluates this
claim using exact payload recovery rather than only raw bit error rate.

ETEHGAN v3 combines a residual neural
embedding network, a learned extractor, a packet layer, Reed-Solomon error
correction, deterministic interleaving, CRC-based validation, and
steganalysis-aware training. The receiver uses the stego image, the shared model
checkpoint, public packet parameters, and an optional shared seed. It does not
need the original cover image, cloud folder positions, or an external sequence
of block indices.

The present draft reports a preliminary but reproducible experimental state. On
small held-out Caltech101 and COCO val2017 subsets, the best current checkpoint
achieves exact clean-channel recovery at 0.25 nominal bpp. However, the method
is still detectable by a lightweight statistical classifier and is not robust to
JPEG compression, blur, or resizing. These limitations are central to the
paper's claim boundary.

The contributions are:

1. We formalize an auxiliary-channel-free recovery objective motivated by the
   operational metadata dependency of WYSAWIS-style indexing.
2. We propose ETEHGAN v3, a neural image steganography pipeline with a
   self-contained packet layer that includes payload length, CRC32, ECC,
   interleaving, and receiver-side recovery from the stego image.
3. We introduce a training extension combining residual-statistics
   regularization and a lightweight adversarial residual-domain discriminator.
4. We provide a reproducible evaluation that separates nominal bpp from
   effective user bpp and reports exact recovery, raw BER, quality metrics,
   attack failures, and simple steganalysis results.

## 2. Related Work

### 2.1 WYSAWIS and auxiliary location metadata

WYSAWIS maps secret data to image blocks using hash-based category sequences
and cloud-carried location information [1]. This design is attractive because
it avoids modifying image pixels. Its operational cost is that the receiver
needs auxiliary metadata or cloud-position information to reconstruct the
message. In settings where the storage channel is monitored, compromised, or
auditable, this external information can itself become a signal. The present
paper targets this specific limitation by embedding a recoverable packet inside
one stego image.

The comparison is not one-to-one: WYSAWIS is coverless/indexing-based, while
ETEHGAN v3 modifies a cover image through a neural residual encoder. The fair
claim is therefore not that ETEHGAN v3 dominates WYSAWIS. The fair claim is
that ETEHGAN v3 removes the WYSAWIS-style auxiliary location channel in the
tested clean-channel setting.

### 2.2 Generative and neural image steganography

Generative Steganography Network (GSN) demonstrated that generative models can
be used for steganographic communication [2]. Coverless image steganography
based on GANs [3], IDGAN [4], and GAN-based anime-character generation [5]
show that GAN and coverless framing are already established. More recent work
addresses robustness and quality, including robust generative steganography
based on image mapping [6], cover-separable fixed neural network steganography
via deep generative models [7], invertible neural network plus GAN
steganography [8], robust and diverse coverless image steganography against
passive and active steganalysis [9], restoration-based robustness for coverless
steganography [10], StyleGAN noise-map steganography [11], and wavelet-GAN
high-invisibility steganography [12].

These works are direct novelty threats to any broad claim of being a first
GAN-based, first generative, or first coverless steganography system. The
present work is positioned differently. It focuses on the packet-level recovery
problem that arises when an indexing-based scheme requires external location
metadata, and on reporting the difference between nominal embedding capacity and
effective user payload after packet overhead and failures.

### 2.3 Steganalysis and robustness

Visual metrics such as PSNR and SSIM are not security proofs. A stego image can
have high visual fidelity while remaining statistically detectable. For this
reason, the current artifact includes a simple sanity-check detector based on
residual and least-significant-bit summary features. This detector is not a
replacement for contemporary deep steganalysis. Its role is to prevent
unsupported claims of security from being inferred from PSNR or exact recovery
alone.

Robustness is similarly attack-specific. The present results show that clean
transmission can be reliable, but JPEG compression, blur, and resizing destroy
recovery under the tested model. Robust steganography is therefore outside the
supported claim boundary of the current checkpoint.

## 3. Problem Definition and Threat Model

The system has three main parties:

- a sender, who owns a cover image and a secret payload;
- a receiver, who obtains the stego image and uses shared extraction material;
- an adversary, who may passively inspect images and, in the active case, apply
  image transformations.

The sender and receiver may share:

- model architecture;
- trained model weights;
- packet parameters;
- an optional seed or key for deterministic packet interleaving.

The receiver must not require:

- the original cover image;
- WYSAWIS-style cloud folder positions;
- block-location lists;
- external sequence metadata.

The core goal is exact payload recovery from the stego image in the tested
channel. Payload confidentiality is not provided by the steganographic layer
unless the payload is encrypted before embedding. Steganographic security is
not assumed; it must be evaluated through detectors. Robustness is not assumed;
it must be reported per transformation.

## 4. Method

### 4.1 Overview

ETEHGAN v3 contains four layers:

1. a packet layer that converts a byte payload into a self-contained protected
   bitstream;
2. a residual neural encoder that embeds the packet bitstream into a cover
   image;
3. a neural decoder that outputs bit logits from the stego image;
4. a recovery layer that thresholds logits, optionally uses reliability scores,
   applies ECC decoding, and validates the CRC.

The transmitted object is one stego image.

### 4.2 Packet layer

For a 512 by 512 RGB image, the current neural payload tensor has two bit
planes, giving a maximum carrier tensor of 524,288 positions. The paper does
not report this value as user capacity. Instead, capacity is counted after
header, ECC, interleaving, padding, and failures.

The V3 packet contains:

- magic bytes and version;
- header length;
- packet configuration identifier;
- payload length;
- payload CRC32;
- useful bit count;
- ECC parameters;
- seed identifier;
- payload bytes;
- padding;
- chunked Reed-Solomon parity;
- deterministic byte interleaving.

The reported operating point uses 0.25 nominal bpp:

```text
useful_bits = 512 * 512 * 0.25 = 65,536 bits
useful_bytes = 8,192 bytes
RS chunk size = 255 bytes
parity bytes per chunk = 64
data bytes per chunk = 191
number of full RS chunks = 32
raw RS data capacity = 32 * 191 = 6,112 bytes
header size = 32 bytes
effective user payload = 6,080 bytes = 0.185546875 bpp
```

The receiver validates exact recovery by checking that Reed-Solomon decoding
succeeds and that the decoded payload matches the CRC32 stored in the packet.

### 4.3 Neural encoder and extractor

The encoder is a dense convolutional residual network. It takes a normalized
cover image and two payload bit planes as input. Let \(C\) be the cover image
and \(P\) be the payload tensor. The residual encoder computes:

```text
S = clamp(C + alpha * tanh(E_raw(C, P)), -1, 1)
```

where \(S\) is the stego image and \(\alpha\) is the residual strength. Earlier
iterations tested \(\alpha = 0.2\), \(0.18\), \(0.15\), and \(0.1\). The
current best checkpoint uses \(\alpha = 0.18\).

The decoder is a dense convolutional extractor with a spatial attention block.
It outputs two logit planes. The sign of each logit gives the hard bit
prediction. The magnitude of the logit can be used as a reliability score for
optional erasure decoding, although the present experiments did not show a
consistent gain from erasures.

### 4.4 Training losses

The clean-channel baseline uses:

```text
L_base = lambda_extract * BCEWithLogits(D(S), P)
       + lambda_image * MSE(S, C)
```

The steganalysis-aware training variant adds two terms:

```text
L_total = L_base
        + lambda_stat * ||phi(S) - phi(C)||_1
        + lambda_adv * BCE(A(S), cover_label)
```

Here, \(\phi(\cdot)\) is a differentiable residual-statistics feature vector
computed from horizontal, vertical, diagonal, and anti-diagonal residuals. The
adversarial term uses a small residual-domain discriminator \(A\), trained to
separate cover images from stego images. The discriminator loss is:

```text
L_D = 0.5 * BCE(A(C), cover_label)
    + 0.5 * BCE(A(S_detached), stego_label)
```

This adversarial loss is a training regularizer, not a security proof. The
external simple detector used in evaluation is trained separately.

## 5. Experimental Protocol

### 5.1 Data and splits

Experiments use local subsets of Caltech101 and COCO val2017. Images are
center-cropped to a square and resized to 512 by 512 pixels. The training runs
reported here use 20 Caltech101 images and 20 COCO images. Evaluation uses
offset test subsets beginning after the first 20 sorted images, preventing the
reported 50-image and 80-image evaluations from reusing the training images
under this deterministic split.

The dataset citations and license statements should be completed before
submission. COCO is the Microsoft Common Objects in Context dataset [13].
Caltech101 is referenced here as the standard 101-category Caltech dataset; its
formal citation must be verified in the final bibliography.

### 5.2 Metrics

Capacity metrics:

- nominal bpp;
- effective user bpp;
- payload bytes;
- ECC overhead.

Recovery metrics:

- raw bit error rate before ECC;
- exact recovery rate after ECC and CRC validation;
- failure rate.

Quality metrics:

- PSNR;
- global SSIM.

Security sanity metric:

- accuracy and AUC of a lightweight logistic detector using 86 residual and
  LSB summary features.

Robustness metrics:

- exact recovery and raw BER under JPEG, additive noise, blur, and resize.

### 5.3 Claim boundaries

The current experiments are preliminary. The training set is small, the
steganalysis detector is lightweight, and no strong external baselines have
been reproduced. The results are therefore suitable for method development and
claim calibration, but not yet sufficient for final Q1 submission without
additional evaluation.

## 6. Results

### 6.1 Payload accounting and clean-channel recovery

Table 1 reports the payload curve for the residual 0.2 baseline. Lower nominal
rates do not monotonically improve COCO reliability because the checkpoint was
trained at 0.25 bpp.

**Table 1. Clean-channel payload curve for residual 0.2 baseline.**

| Dataset | Images | Nominal bpp | Effective bpp | Payload bytes | Exact recovery | Mean BER | Mean PSNR | Mean SSIM |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Caltech101 | 50 | 0.05 | 0.0339965820 | 1114 | 50/50 | 0.0011736874 | 39.5597 | 0.9991897 |
| COCO | 50 | 0.05 | 0.0339965820 | 1114 | 47/50 | 0.0058913309 | 38.5133 | 0.9987974 |
| Caltech101 | 50 | 0.10 | 0.0689697266 | 2260 | 50/50 | 0.0009554335 | 38.7317 | 0.9990114 |
| COCO | 50 | 0.10 | 0.0689697266 | 2260 | 47/50 | 0.0048878205 | 37.8042 | 0.9985878 |
| Caltech101 | 50 | 0.25 | 0.1855468750 | 6080 | 50/50 | 0.0007910156 | 36.8149 | 0.9984265 |
| COCO | 50 | 0.25 | 0.1855468750 | 6080 | 50/50 | 0.0035113525 | 36.1305 | 0.9979151 |

The supported operating point is therefore 0.25 nominal bpp, corresponding to
0.185546875 effective user bpp after packet and ECC overhead.

### 6.2 Residual-strength trade-off

Table 2 compares residual strength variants. Residual 0.15 reduces simple COCO
detectability but fails the COCO50 exact-recovery gate. Residual 0.18 preserves
exact recovery and improves PSNR, but does not reliably improve detector AUC.

**Table 2. Residual-strength trade-off at 0.25 nominal bpp.**

| Checkpoint | Dataset | Exact recovery | Mean BER | PSNR | Simple detector AUC |
|---|---|---:|---:|---:|---:|
| residual 0.2 | Caltech101 | 50/50 | 0.0007910156 | 36.8149 | 0.965625 |
| residual 0.2 | COCO | 50/50 | 0.0035113525 | 36.1305 | 0.930625 |
| residual 0.15 | Caltech101 | 50/50 | 0.0009884644 | 39.2491 | 0.947500 |
| residual 0.15 | COCO | 48/50 | 0.0045501709 | 38.1728 | 0.888125 |
| residual 0.18 | Caltech101 | 50/50 | 0.0007458496 | 38.3645 | 0.961250 |
| residual 0.18 | COCO | 50/50 | 0.0032171631 | 37.3305 | 0.936250 |

Residual strength alone is therefore not a sufficient security mechanism.

### 6.3 Effect of steganalysis-aware training

Table 3 reports the current best checkpoint, trained with residual-statistics
regularization and an adversarial residual-domain discriminator.

**Table 3. Current best quality-recovery-detectability checkpoint.**

| Checkpoint | Dataset | Exact recovery | Mean BER | PSNR | SSIM | Detector accuracy | Detector AUC |
|---|---|---:|---:|---:|---:|---:|---:|
| residual 0.2 | Caltech101 | 50/50 | 0.0007910156 | 36.8149 | 0.9984265 | 0.9250 | 0.965625 |
| residual 0.2 | COCO | 50/50 | 0.0035113525 | 36.1305 | 0.9979151 | 0.9000 | 0.930625 |
| residual 0.18 | Caltech101 | 50/50 | 0.0007458496 | 38.3645 | 0.9988853 | 0.9625 | 0.961250 |
| residual 0.18 | COCO | 50/50 | 0.0032171631 | 37.3305 | 0.9983871 | 0.8875 | 0.936250 |
| stegaware 0.18 | Caltech101 | 50/50 | 0.0007705688 | 38.7663 | 0.9989831 | 0.9500 | 0.963750 |
| stegaware 0.18 | COCO | 50/50 | 0.0030282593 | 37.5780 | 0.9984748 | 0.9250 | 0.918125 |

The steganalysis-aware checkpoint preserves exact recovery and improves the
COCO detector AUC relative to both the residual 0.2 and residual 0.18
checkpoints. The improvement is modest and not universal: Caltech AUC remains
high.

### 6.4 Robustness stress test

Table 4 reports the attack stress test performed on the earlier residual 0.2
baseline. These results define a limitation rather than a strength.

**Table 4. COCO30 attack stress test at 0.25 nominal bpp.**

| Attack | Exact recovery | Mean raw BER | Max raw BER |
|---|---:|---:|---:|
| clean | 30/30 | 0.0036005656 | 0.0138549805 |
| JPEG95 | 0/30 | 0.4382308960 | 0.4566955566 |
| noise2 | 23/30 | 0.0103378296 | 0.0250396729 |
| blur1 | 0/30 | 0.3269129435 | 0.4140777588 |
| resize0.75 | 0/30 | 0.1956034342 | 0.2213897705 |

The current method is not robust to JPEG compression, blur, or resizing. Mild
additive noise shows partial tolerance in this limited test.

## 7. Discussion

### 7.1 What is demonstrated

The current experiments demonstrate that ETEHGAN v3 can recover a
self-contained packet from a single stego image in the clean channel, without
the auxiliary cloud-location metadata required by WYSAWIS-style indexing. The
receiver obtains payload length and validates exact recovery from the decoded
packet itself. This directly supports the auxiliary-channel-free recovery
claim, within the small evaluated subsets.

The packet layer also makes capacity accounting auditable. At 0.25 nominal bpp,
the effective user payload is not 0.25 bpp; it is 0.185546875 bpp after header
and ECC overhead. This distinction is important for avoiding inflated capacity
claims.

### 7.2 What is not demonstrated

The method is not proven secure. A lightweight residual/LSB detector still
detects stego images above chance. The method is not robust to common image
processing. It is also not coverless in the strict sense, because the sender
uses a cover image. Finally, the training and evaluation subsets are too small
to support broad generalization claims.

### 7.3 Implications for novelty

The strongest novelty claim is not a broad generative-steganography claim. The
strongest current claim is a protocol-level and evaluation-level contribution:
self-contained exact recovery without an auxiliary location channel, with
explicit accounting of effective payload and failure modes. This gap is
meaningful relative to WYSAWIS, but it must be positioned carefully against the
larger neural and generative steganography literature.

## 8. Reproducibility

The artifact is organized under:

```text
05_artifacts/code/etehgan/
05_artifacts/models/
05_artifacts/results/
```

Core scripts:

- `packet_v3.py`: packet construction, ECC, interleaving, decoding;
- `embed_payload_v3.py`: end-to-end payload embedding;
- `extract_payload_v3.py`: end-to-end payload extraction;
- `evaluate_v3_packet.py`: exact-recovery evaluation;
- `evaluate_v3_simple_steganalysis.py`: lightweight detector evaluation;
- `train_v3_stegaware.py`: residual-statistics and adversarial training.

Current best checkpoint:

```text
05_artifacts/models/etehgan_v3_stegaware018_stat05_adv001_e3.pt
```

The current experiments use fixed sorted offsets and fixed seeds. Final
submission should include full split files, dataset license statements, and
stronger baseline code.

## 9. Limitations and Future Work

The current artifact is not submission-ready for a Q1 journal without further
experiments. The highest-priority missing elements are:

1. larger train, validation, and test splits;
2. repeated seeds and confidence intervals;
3. LPIPS or another perceptual metric beyond global SSIM;
4. contemporary deep steganalysis baselines;
5. fair comparisons against at least one reproducible neural or generative
   steganography baseline;
6. robust training or synchronization-aware coding if robustness is to be
   claimed;
7. a complete related-work audit of all cited competitors.

Future technical work should integrate stronger steganalysis-aware objectives
and test whether the simple-detector AUC reduction transfers to deeper
detectors. Robustness should be treated as a separate objective because the
current clean-channel model fails under JPEG, blur, and resizing.

## 10. Conclusion

This paper presented ETEHGAN v3, a reliability-aware auxiliary-channel-free
neural image steganography framework with self-contained packet recovery. The
method replaces WYSAWIS-style external location metadata with a packet that
contains payload length, CRC32, ECC, and interleaving information recoverable
from the stego image. The best current checkpoint achieves exact clean-channel
recovery on the evaluated Caltech101 and COCO subsets at 0.25 nominal bpp,
corresponding to 0.185546875 effective user bpp. Statistical regularization and
adversarial residual-domain training improve the quality/detectability
trade-off on COCO while preserving exact recovery. However, the method remains
detectable by a lightweight classifier and is not robust to common image
transformations. The present contribution should therefore be understood as a
clean-channel, auxiliary-channel-free exact-recovery step, not as a complete
solution to secure or robust image steganography.

## References

[1] E. Fotso, Ebele, Ekodeck, and M. Ndoundam, "A high-capacity coverless image
steganography approach using block-level hash encoding and sequence category
mapping: WYSAWIS," Multimedia Tools and Applications, 2025.
https://doi.org/10.1007/s11042-025-21128-y

[2] "Generative Steganography Network," Proceedings of the 30th ACM
International Conference on Multimedia, 2022.
https://doi.org/10.1145/3503161.3548217

[3] "Coverless Image Steganography Based on Generative Adversarial Network,"
Mathematics, 2020. https://doi.org/10.3390/math8091394

[4] "IDGAN: Information-Driven Generative Adversarial Network of Coverless Image
Steganography," Electronics, 2023. https://doi.org/10.3390/electronics12132881

[5] "Leveraging coverless image steganography to hide secret information by
generating anime characters using GAN," Expert Systems with Applications, 2024.
https://doi.org/10.1016/j.eswa.2024.123420

[6] "Robust Generative Steganography Based on Image Mapping," IEEE Transactions
on Circuits and Systems for Video Technology, 2024.
https://doi.org/10.1109/TCSVT.2024.3451620

[7] "Cover-separable Fixed Neural Network Steganography via Deep Generative
Models," Proceedings of the 32nd ACM International Conference on Multimedia,
2024. https://doi.org/10.1145/3664647.3680824

[8] "High-accuracy image steganography with invertible neural network and
generative adversarial network," Signal Processing, 2025.
https://doi.org/10.1016/j.sigpro.2025.109988

[9] "Highly Robust and Diverse Coverless Image Steganography Against Passive and
Active Steganalysis," IEEE Transactions on Dependable and Secure Computing,
2025. https://doi.org/10.1109/TDSC.2024.3521424

[10] "A Universal Framework for Improving the Robustness of Coverless Image
Steganography Based on Image Restoration," IEEE Transactions on Circuits and
Systems for Video Technology, 2025.
https://doi.org/10.1109/TCSVT.2024.3454457

[11] "StyleStego: a novel paradigm for high-capacity steganography using per
layer noise maps in StyleGAN for cross-domain robustness," Multimedia Tools and
Applications, 2026. https://doi.org/10.1007/s11042-026-21718-4

[12] "High invisibility image steganography with wavelet transform and generative
adversarial network," Expert Systems with Applications, 2024.
https://doi.org/10.1016/j.eswa.2024.123540

[13] T.-Y. Lin, M. Maire, S. Belongie, L. Bourdev, R. Girshick, J. Hays,
P. Perona, D. Ramanan, C. L. Zitnick, and P. Dollar, "Microsoft COCO: Common
Objects in Context," 2014. https://arxiv.org/abs/1405.0312

## Pre-submission Actions Outside the Article Body

1. Verify all author names for references [2]-[12] from publisher pages before
   journal submission.
2. Add the formal Caltech101 dataset citation after primary-source
   verification.
3. Replace the lightweight detector-only security evaluation with contemporary
   steganalysis baselines.
4. Add confidence intervals and repeated seeds.
5. Add at least one reproduced baseline comparison under equal effective bpp.
