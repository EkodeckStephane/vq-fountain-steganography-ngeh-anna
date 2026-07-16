# JISA / Elsevier CAS Preparation Notes

This directory contains a local Elsevier CAS double-column preparation of the
VQ-Fountain manuscript for a potential submission to the Journal of Information
Security and Applications (JISA).

Artifact DOI: `https://doi.org/10.5281/zenodo.21400722`

## Source Files

- `main_jisa_casdc.tex`: local CAS double-column manuscript source.
- `references.bib`: BibTeX database copied from the VQ-Fountain manuscript.
- `figures/`: PDF figures generated from the reproducibility artifacts.
- `highlights.txt`: separate Elsevier-style highlights file.
- `cas-dc.cls`, `cas-common.sty`, `cas-model2-names.bst`,
  `cas-dc-template.tex`, `manifest.txt`: CAS files downloaded from CTAN.

The manuscript `.tex` and compiled PDF are intentionally local-only and are
ignored by the repository rules so they are not pushed to the GitHub artifact
repository.

## JISA Alignment Checks Applied

- JISA scope fit: the manuscript is positioned as multimedia security and
  information hiding, which falls under JISA information security applications
  and multimedia security scope.
- CAS format: converted to Elsevier `cas-dc` double-column LaTeX format.
- Front matter: title, author order, affiliations, corresponding author, CRediT
  contributions, abstract, and keywords are included.
- Abstract: shortened for journal submission style.
- Tables: wide tables use editable LaTeX tables with fixed-width columns and
  explicit line breaks where needed.
- References: SOTA positioning table includes citations for the named external
  comparators.
- Data availability: the article contains the GitHub artifact link while keeping
  article `.tex` and PDF outside the repository; it also contains the Zenodo
  DOI for the archived artifact release.
- Declarations: competing interest, funding, acknowledgements, CRediT, and
  generative-AI-use declaration sections are included for author review.

## Manual Items Before Real Submission

- Confirm the corresponding author and email addresses.
- Confirm whether the generative-AI declaration text reflects the authors'
  intended disclosure.
- Check that all author CRediT roles are approved by the authors.
- Upload editable source files, figures, highlights, and declaration files in
  the Elsevier submission system according to the current JISA instructions.
