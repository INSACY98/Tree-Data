# Primary Tree Care

Creative data transformation project that reimagines living NYC street trees as public primary-care providers.

## Repository Contents

- `scripts/primary_tree_care_transform.py` - reproducible pandas transformation script.
- `scripts/build_primary_tree_care_map.py` - local interactive Leaflet map builder.
- `docs/primary_tree_care_feature_codebook.md` - current data description, specialty mapping rules, species-to-specialty table, and validation summaries.
- `requirements.txt` - Python dependencies used for the analysis workflow.

## Local Data Layout

Data files are intentionally not tracked in GitHub.

Expected local structure:

```text
data/
  raw/
    2015_Street_Tree_Census_-_Tree_Data_20260522.csv
    favorite-trees.json
    FavoriteTreesDataDictionary_vF.xlsx
    StreetTreeCensus2015TreesDataDictionary20161102.pdf
  processed/
    trees_with_favorites_live.csv
    trees_with_favorites_dead.csv
    trees_with_favorites_stump.csv
    primary_tree_care_providers.csv
```

The raw NYC tree census CSV is larger than GitHub's normal file-size limit, so data stays local.

## Run

```bash
source .venv/bin/activate
python scripts/primary_tree_care_transform.py
```

The script reads `data/processed/trees_with_favorites_live.csv` and writes `data/processed/primary_tree_care_providers.csv`.

## Interactive Map

GitHub Markdown does not run interactive JavaScript maps directly. To view the local map:

```bash
source .venv/bin/activate
python scripts/build_primary_tree_care_map.py
```

Then open:

```text
docs/primary_tree_care_map.html
```

The generated HTML map is ignored by Git because it embeds local data.
