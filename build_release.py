#!/usr/bin/env python3
"""Build the AkkadNMT-75K reproducibility release from the supplied CSV.

This script is intentionally conservative: it normalizes Unicode to NFC and
recomputes derived metadata, but it does not silently alter scholarly text.
Potentially problematic rows are flagged for review and retained in the raw
source-of-truth artifact.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
import unicodedata
from pathlib import Path

import pandas as pd

EXPECTED_INPUT = [
    "transliteration", "translation", "trans_len", "transl_len",
    "trans_words", "transl_words", "len_bin", "ratio"
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def normalize_text(value: object) -> str:
    if pd.isna(value):
        return ""
    return unicodedata.normalize("NFC", str(value)).replace("\ufeff", "")


def word_count(value: str) -> int:
    return len(value.split()) if value else 0


def length_bin(n: int) -> str:
    if n <= 10:
        return "0-10"
    if n <= 25:
        return "11-25"
    if n <= 50:
        return "26-50"
    if n <= 100:
        return "51-100"
    if n <= 250:
        return "101-250"
    return "251+"


def flags_for(source: str, target: str) -> list[str]:
    flags: list[str] = []
    joined = f"{source}\n{target}"
    if "\ufffd" in joined:
        flags.append("replacement_character")
    if re.search(r"[\u0590-\u05ff]", joined):
        flags.append("hebrew_script")
    if re.search(r"[\u0600-\u06ff]", joined):
        flags.append("arabic_script")
    if re.search(r"[\u0400-\u04ff]", joined):
        flags.append("cyrillic_script")
    if re.search(r"[\u0900-\u097f]", joined):
        flags.append("devanagari_script")
    if re.search(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", joined):
        flags.append("control_character")
    if re.search(r"[ \t]+$", source) or re.search(r"[ \t]+$", target):
        flags.append("trailing_whitespace")
    if re.search(r'\.\s*""$', target):
        flags.append("doubled_terminal_quote_candidate")
    if not source.strip():
        flags.append("empty_source")
    if not target.strip():
        flags.append("empty_target")
    if len(source.strip()) < 2 or len(target.strip()) < 2:
        flags.append("very_short_record")
    return sorted(set(flags))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--outdir", type=Path, required=True)
    args = parser.parse_args()
    args.outdir.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(args.input, dtype=str, keep_default_na=False, quoting=csv.QUOTE_MINIMAL)
    if list(df.columns) != EXPECTED_INPUT:
        raise ValueError(f"Unexpected input schema: {list(df.columns)!r}")

    source = df["transliteration"].map(normalize_text)
    target = df["translation"].map(normalize_text)
    primary = pd.DataFrame({
        "row_id": [f"akkadnmt_v2_{i:06d}" for i in range(len(df))],
        "source_transliteration": source,
        "target_translation": target,
    })

    flags = [flags_for(a, b) for a, b in zip(source, target)]
    recomputed_source_len = source.str.len()
    recomputed_target_len = target.str.len()
    recomputed_source_words = source.map(word_count)
    recomputed_target_words = target.map(word_count)
    ratios = (recomputed_target_len / recomputed_source_len.replace(0, pd.NA)).astype("Float64")
    metadata = pd.DataFrame({
        "row_id": primary["row_id"],
        "source_characters": recomputed_source_len,
        "target_characters": recomputed_target_len,
        "source_words": recomputed_source_words,
        "target_words": recomputed_target_words,
        "target_source_character_ratio": ratios,
        "source_length_bin": recomputed_source_len.map(length_bin),
        "validation_flags": [";".join(x) for x in flags],
        "validation_status": ["review_required" if x else "passed" for x in flags],
        "historical_provenance_status": "unreconstructed",
    })

    primary.to_csv(args.outdir / "AkkadNMT_75K_primary.csv", index=False, encoding="utf-8", lineterminator="\n")
    metadata.to_csv(args.outdir / "AkkadNMT_75K_metadata.csv", index=False, encoding="utf-8", lineterminator="\n")

    audit = {
        "input_file": "AkkadNMT_75K_original_eight_column.csv",
        "input_sha256": sha256(args.input),
        "rows": int(len(df)),
        "input_columns": list(df.columns),
        "primary_columns": list(primary.columns),
        "metadata_columns": list(metadata.columns),
        "flagged_rows": int((metadata["validation_status"] == "review_required").sum()),
        "flag_counts": {},
        "exact_duplicate_rows": int(df.duplicated().sum()),
        "unique_source_transliterations": int(source.nunique()),
        "unique_target_translations": int(target.nunique()),
        "recomputed_field_disagreements": {},
        "notes": [
            "The primary release preserves text content after NFC normalization and BOM removal only.",
            "Potential issues are flagged, not silently deleted, because the historical source context is unavailable.",
            "Row-level upstream provenance is marked unreconstructed unless source identifiers are supplied separately.",
        ],
    }
    counts: dict[str, int] = {}
    for row_flags in flags:
        for flag in row_flags:
            counts[flag] = counts.get(flag, 0) + 1
    audit["flag_counts"] = counts
    comparisons = {
        "trans_len": int((recomputed_source_len != pd.to_numeric(df["trans_len"], errors="coerce")).sum()),
        "transl_len": int((recomputed_target_len != pd.to_numeric(df["transl_len"], errors="coerce")).sum()),
        "trans_words": int((recomputed_source_words != pd.to_numeric(df["trans_words"], errors="coerce")).sum()),
        "transl_words": int((recomputed_target_words != pd.to_numeric(df["transl_words"], errors="coerce")).sum()),
        "len_bin": int((recomputed_source_len.map(length_bin) != df["len_bin"]).sum()),
    }
    audit["recomputed_field_disagreements"] = comparisons
    (args.outdir / "validation_report.json").write_text(json.dumps(audit, indent=2, ensure_ascii=False), encoding="utf-8")

    print(json.dumps(audit, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
