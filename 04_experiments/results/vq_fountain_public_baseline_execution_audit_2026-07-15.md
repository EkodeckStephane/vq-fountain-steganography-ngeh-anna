# Public Baseline Execution Audit

Date: 2026-07-15

This audit records local executability of public non-coverless baselines.
It prevents unsupported baseline claims when dependencies or checkpoints are absent.

| Baseline | Accounted | Executable now | Main blockers |
|---|---:|---:|---|
| HiDDeN | true | true | none |
| DCT-spread | true | true | none |
| StegaStamp | true | false | pretrained SavedModel is not present in the local sparse checkout; TensorFlow is not installed; bchlib is not installed |

## Decision

2 executable non-coverless baselines are available locally.
HiDDeN and DCT-spread have local run artifacts and can be reported with their measured scores.
StegaStamp remains a valid public non-coverless comparator, but no local recovery score may be claimed
until a pretrained SavedModel and compatible TensorFlow 1.x/BCH runtime are available.
