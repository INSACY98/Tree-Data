# Primary Tree Care

Creative data transformation project that reimagines living NYC street trees as public primary-care providers.

## Repository Contents

- `scripts/primary_tree_care_transform.py` - reproducible pandas transformation script.
- `scripts/build_primary_tree_care_map.py` - local interactive Leaflet map builder.
- `scripts/build_netlify_map_data.py` - exports a lean tree-level GeoJSON for the hosted quality map.
- `site/` - Netlify-ready static map app.
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

Create the local interactive map:

```bash
source .venv/bin/activate
python scripts/build_primary_tree_care_map.py
```

Then open the generated local file. The script prints a `file://...` URL you can paste into your browser.

For browser speed, the map aggregates the 21,739 tree providers into 233 neighborhood circles. Specialty, provider type, rating, star doctor, weekend, and search filters recalculate the matching neighborhood totals without drawing one marker for every tree.

You can also serve it from the project root:

```bash
python3 -m http.server 8000
```

Then open:

```text
http://localhost:8000/docs/primary_tree_care_map.html
```

The generated HTML map is local-only because it embeds the provider data.

## Tree-Level Hosted Map

Build the tree-level map data:

```bash
source .venv/bin/activate
python scripts/build_netlify_map_data.py
```

Preview the Netlify site locally:

```bash
python3 -m http.server 8010 --directory site
```

Then open:

```text
http://localhost:8010/
```

Deploy to Netlify from the local generated site:

```bash
netlify login
netlify deploy --dir site --prod
```

The generated `site/assets/trees_map.geojson` file is intentionally ignored by Git. A manual Netlify deploy uploads it to the hosted site without committing the data to GitHub.
