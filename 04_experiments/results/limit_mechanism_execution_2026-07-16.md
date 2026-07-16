# ETHEGAN Limit-Mechanism Execution Report - 2026-07-16

Scope: local NGEH ANNA article workspace only.

This report records mechanisms that were added or audited after the final
defect table. It separates what is now operational from what remains blocked.

## Executed Mechanisms

| Limit from final review | Mechanism added or audited | Artifact | Local result | Status |
|---|---|---|---|---|
| Clean-channel COCO failures at high payload | Adaptive ECC/rate-control evaluator over ECC-64/96/128/160 | `05_artifacts/code/etehgan/evaluate_v3_adaptive_ecc.py` | On the two bundled sample images, clean recovery is 2/2 for all ECC settings; oracle adaptive rate selects ECC-64 and keeps 6080 bytes, 0.185546875 bpp | Mechanism operational; needs external-dataset rerun |
| JPEG/blur/resize failure | Same evaluator tested attacks during ECC selection | `05_artifacts/results/raw/adaptive_ecc_sample_025.json` | JPEG95, blur1, and resize0.75 remain 0/2 even with ECC-160 | Limit not lifted; requires synchronization/robust-channel training |
| Weak passive-security evidence | SPAM-style quantized residual co-occurrence detector added | `05_artifacts/code/etehgan/evaluate_v3_spam_steganalysis.py` | Two-image smoke test: 1568 features, 1 train image, 1 test image, test AUC 0.5 | Pipeline operational only; not security evidence |
| Passive security not proven | Low-payload detectability-gated operating mode | `05_artifacts/results/raw/ethegan_detectability_gate_40_00075_n128e32_accept25.json` | 10/40 accepted images; accepted exact recovery 10/10; simple AUC 0.58; SPAM AUC 0.52 | Lifted only for accepted low-payload images against tested classical detectors |
| No reproduced/public baseline gate | Baseline executability audit rerun and renamed for ETHEGAN | `04_experiments/results/ethegan_public_baseline_execution_audit_2026-07-16.md` | HiDDeN and DCT-spread executable locally with run artifacts; StegaStamp blocked by missing SavedModel/TensorFlow/bchlib | Partially lifted |
| No confidentiality support | AES-256-GCM pre-packet wrapper and AEAD audit | `05_artifacts/code/etehgan/secure_payload.py` and `tools/audit_confidentiality_support.py` | correct-key recovery true; wrong-key failure true; wrong-AAD failure true | Lifted for payload confidentiality before packetization |
| No equal-effective-bpp benchmark | Equal-bpp benchmark against ETHEGAN gated/ungated, DCT-spread, HiDDeN local checkpoint | `04_experiments/results/equal_bpp_benchmark_2026-07-16.md` | ETHEGAN gated: 0.001953125 bpp, 10/10 clean accepted, PSNR 46.3759, AUC 0.58/0.52; DCT: 40/40 clean, PSNR 34.7398, AUC 0.73/0.95, better active robustness | Clean-channel/fidelity superiority lifted; universal SOTA superiority not claimed |
| No artifact integrity lock | SHA256 manifest generated | `04_experiments/results/ethegan_reproducibility_manifest_2026-07-16.md` | 166 files frozen after README/report update | Partially lifted; not a DOI |

## What Can Now Be Claimed More Safely

- The artifact contains an adaptive ECC evaluator for reliability-aware rate
  selection.
- The artifact contains a stronger classical residual co-occurrence detector
  gate in addition to the lightweight residual/LSB detector.
- The artifact contains a low-payload detectability gate that supports a
  bounded passive-security claim for accepted images.
- The artifact contains AES-256-GCM pre-packet encryption with correct-key and
  wrong-key authentication tests.
- The artifact has a baseline audit that distinguishes executable local
  comparators from blocked comparators.
- The artifact has an equal-effective-bpp benchmark against locally executable
  baselines.
- The artifact has a local SHA256 integrity mechanism for manuscript, code,
  checkpoints, and result tables.

## What Still Cannot Be Claimed

- Robustness to JPEG, blur, resize, or crop is still not supported.
- Passive steganographic security is not supported for the default high-payload
  mode; it is supported only for the low-payload accepted-image gate and only
  against the tested classical detectors.
- Payload confidentiality is supported only when AES-GCM pre-packet encryption
  is used.
- Universal SOTA superiority is still not supported; the equal-bpp benchmark
  supports clean-channel/fidelity superiority over local baselines but shows
  DCT-spread is stronger under JPEG/blur/resize.
- Public archival reproducibility is still not complete until the package is
  released with a stable public URL or archive DOI.

## Practical Next Gates

1. Rerun adaptive ECC on the same Caltech101 and COCO subsets used in the
   manuscript, then report realized average effective bpp and CRC failures.
2. Rerun the low-payload detectability gate on larger grouped splits and add a
   neural detector before broadening the passive-security claim.
3. Integrate AES-GCM as an optional CLI flag in the embed/extract scripts, not
   only as a tested pre-packet wrapper.
4. Add synchronization-aware packet repetition or block-local CRC before
   repeating JPEG/blur/resize/crop robustness claims.
5. Add StegaStamp or another recent learned robust baseline once compatible
   weights and runtime are available.
6. Publish or archive the frozen artifact after final compilation.
