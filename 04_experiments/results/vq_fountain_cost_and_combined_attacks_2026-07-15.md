# VQ-Fountain Cost Reduction and Combined Attacks

Date: 2026-07-15

## Cost Search

Attack: `crop090_r02_c-02`

Best exact-recovery points found:

| Payload | Minimum tested setting |
|---:|---|
| 32 B | overhead 2.0, 8 images |
| 64 B | overhead 2.5, 16 images |

Previous crop experiments used overhead 4.0. The current anchor/geometry stack
therefore reduces the tested 64 B crop setting from overhead 4.0 to 2.5 while
keeping 16 images.

Outputs:

- `05_artifacts/results/tables/vq_fountain_cost_search_crop_offset.csv`
- `05_artifacts/results/raw/vq_fountain_cost_search_crop_offset.json`

## Combined Attacks

Tested attacks:

- `jpeg85+blur1`
- `jpeg85+noise002`
- `crop090_r02_c-02+jpeg85`
- `crop090_r02_c-02+resize075`
- `crop090_r02_c-02+jpeg85+noise002`
- `drop25`
- `crop090_r02_c-02+jpeg85+drop25`

At overhead 2.5, all non-drop-combined attacks recover exactly for both 32 B
and 64 B at 16 and 24 images.

The hard combined setting `crop090_r02_c-02+jpeg85+drop25` needs more
redundancy:

| Payload | Minimum tested exact-recovery setting |
|---:|---|
| 32 B | overhead 4.0, 16 images |
| 64 B | overhead 4.0, 24 images |

Outputs:

- `05_artifacts/results/tables/vq_fountain_combined_attacks.csv`
- `05_artifacts/results/raw/vq_fountain_combined_attacks.json`
- `05_artifacts/results/tables/vq_fountain_combined_drop25_cost_search.csv`
- `05_artifacts/results/raw/vq_fountain_combined_drop25_cost_search.json`

## Interpretation

The current default operating point should be:

- overhead 2.5, 16 images for 64 B under crop/JPEG/resize/noise/blur without
  image drops;
- overhead 4.0, 24 images for 64 B under crop + JPEG + 25% image drop.
