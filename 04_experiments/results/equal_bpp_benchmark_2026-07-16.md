# Equal-Effective-BPP Benchmark

Date: 2026-07-16

| Method | Effective bpp | Images | Clean exact | PSNR | Simple AUC | SPAM AUC | Active-channel result | Scope |
|---|---:|---:|---:|---:|---:|---:|---|---|
| ETHEGAN gated low-payload | 0.001953125 | 10 | 1.0 | 46.37585768321092 | 0.58 | 0.52 | 0.0 under JPEG95/blur1/resize0.75 on ungated 40-image check | clean-channel accepted images only |
| ETHEGAN ungated low-payload | 0.001953125 | 40 | 0.95 | 45.28213034374153 |  |  | 0.0 under JPEG95/blur1/resize0.75 | clean-channel all images, no passive-security claim |
| DCT-spread | 0.001953125 | 40 | 1.0 | 34.73979491168076 | 0.73 | 0.95 | jpeg85=1.0, resize075=1.0, blur1=1.0, crop090=0.0 | classical transform baseline |
| HiDDeN local public checkpoint | 0.0018310546875 | 5 | 0.0 |  |  |  | not rerun in this compatibility smoke | local checkpoint compatibility smoke |

## Decision

ETHEGAN shows clean-channel superiority over the local HiDDeN compatibility run and higher clean PSNR than DCT-spread at matched effective bpp, but DCT-spread is superior under the tested active transformations. Do not claim universal SOTA superiority.
