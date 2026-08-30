# AkkadNMT-75K reproducibility package

This repository contains the deterministic release-builder and validation code for the AkkadNMT-75K data package. It does not claim to reconstruct the deleted historical February extraction scripts exactly. Instead, it provides an auditable pipeline that starts from the supplied eight-column CSV, creates the public two-column primary release and derived metadata, and reports potential issues without silently changing scholarly text.

## Repository structure

```text
build_release.py       Build primary release, metadata, and validation report
requirements.txt       Minimal runtime dependencies
test_release.py         Automated schema and output checks
README.md               Reproducibility instructions
LICENSE_PENDING.md      Licensing placeholder pending source-rights review
```

## Reproduce the release

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
python build_release.py --input /path/to/AkkadNMT_75K_original_eight_column.csv --outdir /path/to/output
```

The output contains `AkkadNMT_75K_primary.csv`, `AkkadNMT_75K_metadata.csv`, and `validation_report.json`. The input file is the exact supplied source-of-truth artifact. The audited release contains 75,562 rows, 74,420 unique source transliterations, 47,633 unique target translations, zero exact duplicate aligned pairs, 1,986 repeated-source rows, and 51,171 rows in repeated-target groups. Source lengths range from 2 to 2,982 Unicode characters and target lengths from 3 to 3,895 characters. The script performs Unicode NFC normalization and BOM removal, recomputes derived fields, and adds validation flags. It does not silently delete records or apply unverified linguistic corrections.

## Validation philosophy

The validation report separates automated detection from scholarly adjudication. A flag means that a row requires review; it does not establish that the text is wrong. In particular, legitimate Akkadian diacritics, determinatives, logograms, damaged-text markers, proper names, and quotation marks must not be removed by a generic text-cleaning rule.

## Comparison with the official Deep Past archive

The official archive contains 1,561 training pairs, 4 test rows, 7,953 published-text records, 878 bibliography records, and 292 resource records, in addition to dictionary, lexicon, publication, and alignment files. A named-column comparison found 310 unique exact pair matches between its training file and the AkkadNMT release. This demonstrates overlap but does not reconstruct complete row-level provenance for the aggregate corpus.

## Provenance limitation

The final CSV does not preserve complete upstream row-level source identifiers. The repository marks historical row-level source identifiers as `unreconstructed` unless a separate manifest is later added by the authors. The manuscript must report this limitation plainly.

## Historical AI-assisted step

The historical workflow used Manus for limited duplicate screening and removal of corrupted or non-meaningful English records. The original prompts and logs were not retained. This repository does not present that historical step as reproducible agentic-AI processing; it provides a new deterministic audit instead.

## Data and licensing

The data package contains materials assembled from multiple upstream sources. Do not add a blanket repository license until the source-by-source redistribution audit is complete. Source-specific rights and attribution requirements take precedence.
