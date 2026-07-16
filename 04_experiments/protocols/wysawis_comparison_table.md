# WYSAWIS Comparison Table

Status: working version. Values must be completed and rechecked before manuscript submission.

| Criterion | WYSAWIS | ETEHGAN Target | Evidence Needed |
|---|---|---|---|
| Method family | Coverless image steganography by block-level hash encoding and sequence category mapping | Neural image steganography with global payload encoding | Method section and algorithm. |
| Cover image modification | No image modification in WYSAWIS | Yes if current prototype remains cover-image neural embedding | Be explicit; do not claim coverless if image is modified. |
| Auxiliary channel | Required: cloud storage carries location information | Target: not required | Receiver command must use stego image + shared model/key only. |
| Location metadata | Block and sequence positions are hidden in cloud files | Target: no external location metadata | Protocol description and artifact commands. |
| Repeated segment behavior | WYSAWIS discussion reports repeated segments can duplicate stego-files | Target: repeated segments are encoded in one global image bitstream | Repeated-payload stress test. |
| Nominal capacity | WYSAWIS reports minimum 491,520 bits/image and theoretical upper bound limited by cloud operations | Current smoke test nominal capacity: 524,288 bits/image on 512x512 | Effective bpp and failure rate across datasets. |
| Effective user payload | Depends on message and cloud representation | Smoke test: 458,480 user bits, 1.7490 effective bpp | Full payload accounting. |
| Extraction input | Stego image + cloud positions + shared dataset/keys | Stego image + shared model/weights | Threat model and command line. |
| Robustness | WYSAWIS tests BER/ER under image attacks | Must test JPEG/noise/blur/resize/crop | Robustness table. |
| Security basis | Unmodified image plus encrypted/cloud-hidden location information | Must be image-level imperceptibility + steganalysis evidence | Detector experiments; PSNR/SSIM alone insufficient. |
| Current reproduced status | Published baseline verified locally | Smoke test exact payload recovery, but low PSNR/SSIM and visible artifacts | Requires model recovery or retraining before Q1 claims. |

## Manuscript Implication

The article should not claim to dominate WYSAWIS on all axes.

The defensible claim is narrower:

> ETEHGAN targets the operational channel-dependence and repeated-cloud-artifact limitations of WYSAWIS, at the cost of moving the security burden to image-level imperceptibility and neural steganalysis resistance.

