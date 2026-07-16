# VQ-Fountain Anchor Security Probe

Date: 2026-07-15

## Purpose

Check whether synchronization anchors remain keyed and distribution-shaped
rather than becoming a trivially detectable fixed token pattern.

## Design

Anchors are:

- keyed by the shared seed and image index;
- placed through the same keyed schedule as payload slots;
- sampled through `PriorBinCodec.sample_token`, not written as fixed token ids;
- measured separately with anchor token leakage and Jensen-Shannon divergence to
  the learned token prior.

## Probe

Payload: 1024 B, 256 generated token-grid images, clean channel.

| Binning | Anchor slots | Mean anchor leakage | Anchor JSD to prior | Payload JSD to prior | Exact recovery |
|---|---:|---:|---:|---:|---:|
| projection | 2304 | 0.00000000 | 0.01041678 | 0.00073516 | yes |
| naive | 2304 | 0.03112697 | 0.01351906 | 0.00152866 | yes |

Outputs:

- `05_artifacts/results/tables/vq_fountain_anchor_security_projection_256.csv`
- `05_artifacts/results/raw/vq_fountain_anchor_security_projection_256.json`
- `05_artifacts/results/tables/vq_fountain_anchor_security_naive_256.csv`
- `05_artifacts/results/raw/vq_fountain_anchor_security_naive_256.json`

## Interpretation

Projection binning keeps anchor leakage below the naive mapping and produces a
lower anchor-token divergence to the prior. Anchors are not fixed visible token
ids in this implementation.
