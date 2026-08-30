from pathlib import Path
import json
import pandas as pd
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
V2 = ROOT / 'zenodo_v2'
OUT = ROOT / 'latex_manuscript'
IMG = OUT / 'figures'
OUT.mkdir(exist_ok=True)
IMG.mkdir(exist_ok=True)

primary = pd.read_csv(V2 / 'AkkadNMT_75K_primary.csv', dtype=str)
meta = pd.read_csv(V2 / 'AkkadNMT_75K_metadata.csv', low_memory=False)

# Exact release statistics for manuscript tables.
summary = {
    'rows': int(len(primary)),
    'unique_source_transliterations': int(primary['source_transliteration'].nunique()),
    'unique_target_translations': int(primary['target_translation'].nunique()),
    'duplicate_rows': int(primary.duplicated().sum()),
    'review_required_rows': int((meta['validation_status'] == 'review_required').sum()),
    'mean_source_characters': float(meta['source_characters'].mean()),
    'median_source_characters': float(meta['source_characters'].median()),
    'mean_target_characters': float(meta['target_characters'].mean()),
    'median_target_characters': float(meta['target_characters'].median()),
    'source_length_bins': {str(k): int(v) for k, v in meta['source_length_bin'].value_counts().sort_index().items()},
}
(OUT / 'release_statistics.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')

# Table-ready CSVs.
source_bin = meta['source_length_bin'].value_counts().rename_axis('source_length_bin').reset_index(name='rows')
source_bin.to_csv(OUT / 'table_source_length_bins.csv', index=False)
validation = meta['validation_flags'].replace('', 'none').value_counts().rename_axis('validation_flags').reset_index(name='rows')
validation.to_csv(OUT / 'table_validation_flags.csv', index=False)

# Length distribution.
plt.figure(figsize=(7.2, 4.2))
plt.hist(meta['source_characters'], bins=50, color='#2b7a9a', alpha=0.9, edgecolor='white')
plt.xlabel('Source transliteration length (Unicode characters)')
plt.ylabel('Number of records')
plt.title('Distribution of source transliteration lengths')
plt.tight_layout()
plt.savefig(IMG / 'source_length_distribution.png', dpi=300)
plt.close()

# Pipeline figure using matplotlib for exact counts; approximate historical stages are labelled.
fig, ax = plt.subplots(figsize=(9, 4.8))
ax.axis('off')
boxes = [
    (0.03, 0.62, 0.25, 0.18, 'Kültepe PDF\n~40,000 reported', '#d9edf7'),
    (0.37, 0.62, 0.25, 0.18, 'ORACC/CuneiML/EvaCun\n~50,000 initial; ~37,000 retained', '#dff0d8'),
    (0.20, 0.25, 0.25, 0.18, 'Additional dictionaries\nCAD/eSAD reported', '#fcf8e3'),
    (0.65, 0.34, 0.28, 0.22, 'Candidate pool\n~77,000 reported', '#f2dede'),
    (0.65, 0.70, 0.28, 0.18, 'new dataset final release\n75,562 rows', '#d9edf7'),
]
for x, y, w, h, text, color in boxes:
    ax.add_patch(plt.Rectangle((x, y), w, h, facecolor=color, edgecolor='#2f4f4f', linewidth=1.2))
    ax.text(x + w/2, y + h/2, text, ha='center', va='center', fontsize=10)
for x1, y1, x2, y2 in [(0.28,0.71,0.65,0.45),(0.62,0.71,0.65,0.45),(0.45,0.34,0.65,0.45),(0.79,0.56,0.79,0.70)]:
    ax.annotate('', xy=(x2, y2), xytext=(x1, y1), arrowprops=dict(arrowstyle='->', lw=1.4, color='#333333'))
ax.text(0.5, 0.06, 'Historical approximate stages are shown separately from exact new dataset counts.', ha='center', fontsize=9, style='italic')
fig.tight_layout()
fig.savefig(IMG / 'source_to_release_pipeline.png', dpi=300)
plt.close(fig)

print(json.dumps(summary, indent=2))
