from pathlib import Path
import json
import pandas as pd

ROOT = Path(__file__).resolve().parent
V2 = ROOT


def test_primary_schema_and_count():
    df = pd.read_csv(V2 / 'AkkadNMT_75K_primary.csv', dtype=str)
    assert list(df.columns) == ['row_id', 'source_transliteration', 'target_translation']
    assert len(df) == 75562
    assert df['row_id'].is_unique
    assert df['source_transliteration'].notna().all()
    assert df['target_translation'].notna().all()


def test_metadata_alignment():
    primary = pd.read_csv(V2 / 'AkkadNMT_75K_primary.csv', dtype=str)
    metadata = pd.read_csv(V2 / 'AkkadNMT_75K_metadata.csv', dtype=str)
    assert list(metadata.columns) == [
        'row_id', 'source_characters', 'target_characters', 'source_words',
        'target_words', 'target_source_character_ratio', 'source_length_bin',
        'validation_flags', 'validation_status', 'historical_provenance_status'
    ]
    assert len(metadata) == len(primary)
    assert metadata['row_id'].tolist() == primary['row_id'].tolist()


def test_report_contract():
    report = json.loads((V2 / 'validation_report.json').read_text())
    assert report['rows'] == 75562
    assert report['exact_duplicate_rows'] == 0
    assert report['primary_columns'] == ['row_id', 'source_transliteration', 'target_translation']
    assert report['metadata_columns'][0] == 'row_id'


if __name__ == '__main__':
    test_primary_schema_and_count()
    test_metadata_alignment()
    test_report_contract()
    print('All release tests passed.')
