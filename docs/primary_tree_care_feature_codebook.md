# Primary Tree Care Data Description

Source file: `data/processed/trees_with_favorites_live.csv`  
Output file: `data/processed/primary_tree_care_providers.csv`  
Transformation script: `scripts/primary_tree_care_transform.py`  
Rows: 21,739  
Columns: 41  
Random seed: `20260523`

## Concept

Each row represents one living NYC tree reimagined as a primary-care tree. The tree itself is the provider. The original `tree_id` is reused as `provider_id`.

Care is assumed to be public and open to everyone, so the dataset does not include insurance, referral, cost, language, hospital, medical-school, telehealth, or human-name fields.

The generated data is reproducible. Most features are derived from tree species, tree diameter, tree condition, tree problems, stewardship, guard status, favorite status, and physical location. Controlled randomness is seeded by `tree_id` and feature names.

## Interactive Map

GitHub Markdown does not execute JavaScript or render embedded interactive maps directly. The interactive Primary Tree Care map is generated as a local HTML file from the local CSV data.

Build the map:

```bash
python scripts/build_primary_tree_care_map.py
```

Open the generated map:

[Open local interactive map](primary_tree_care_map.html)

The generated file is `docs/primary_tree_care_map.html`. It is intentionally ignored by Git because it embeds local provider data, so the link above only works in your local folder after you run the map builder. It will not work from GitHub.

If double-clicking the HTML file does not work, serve the project folder locally:

```bash
python3 -m http.server 8000
```

Then open:

```text
http://localhost:8000/docs/primary_tree_care_map.html
```

The map uses Leaflet and OpenStreetMap tiles from the web, so it needs internet access for the basemap and map library.

For Markdown viewers that allow iframes, the map can be displayed with:

```html
<iframe
  src="primary_tree_care_map.html"
  width="100%"
  height="720"
  style="border: 1px solid #d9e1dc; border-radius: 8px;"
></iframe>
```

## Specialty Mapping Method

`medical_specialty` is the most important fictional transformation. It is assigned at the species level, not row by row. This means every tree with the same `species_common` + `species_scientific` receives the same specialty.

The script combines the common name and scientific name into lowercase text, then checks the rules below in order. The first matching rule wins. If no rule matches, the species receives a deterministic weighted fallback specialty using the fixed random seed.

| Rule Order | Species Text Match | Assigned Specialty | Rationale |
|---:|---|---|---|
| 1 | `ginkgo` | Neurology | Ginkgo is culturally associated with memory and cognition. |
| 2 | `hawthorn`, `crataegus` | Cardiology | Hawthorn has traditional associations with heart and circulation. |
| 3 | `linden`, `tilia` | Psychiatry | Linden is associated with calming teas, rest, and nervous-system soothing. |
| 4 | `oak`, `quercus`, `beech`, `fagus`, `redwood`, `sequoia`, `metasequoia` | Geriatrics | Long-lived, strong, elder-like trees become longevity specialists. |
| 5 | `honeylocust`, `gleditsia`, `planetree`, or scientific names starting with `platanus` | Internal Medicine | Common NYC street-tree generalists become broad adult-care providers. |
| 6 | `maple`, `acer`, `blackgum`, `nyssa` | Endocrinology | Sap and sugar associations translate into metabolism and endocrine care. |
| 7 | `willow`, `salix`, `ash`, `fraxinus`, `hornbeam`, `carpinus`, `ostrya` | Sports Medicine | Flexible, resilient, or structural trees map to movement and recovery. |
| 8 | `pine`, `spruce`, `fir`, `juniper`, `cedar`, `arborvitae`, `cypress`, `pinus`, `picea`, `abies`, `juniperus`, `thuja`, `chamaecyparis`, `sweetgum`, `liquidambar`, `catalpa` | Pulmonology | Evergreen/resin/aromatic/breathing associations map to lungs and air. |
| 9 | `zelkova`, `elm`, `ulmus`, `birch`, `betula`, `sycamore`, `paperbark` | Dermatology | Bark, surface, and skin-like texture associations map to dermatology. |
| 10 | `pear`, `pyrus`, `magnolia`, `tulip` | Women's Health | Blooming and flowering associations become supportive reproductive/life-stage care. |
| 11 | `cherry`, `plum`, `prunus`, `serviceberry`, `amelanchier`, `dogwood`, `cornus` | Pediatrics | Fruit/blossom/sapling associations become child and adolescent care. |
| 12 | `apple`, `malus`, `hackberry`, `celtis`, `mulberry`, `morus`, `chestnut`, `castanea`, `coffeetree`, `gymnocladus` | Gastroenterology | Food, fruit, nut, and digestion associations map to GI care. |
| 13 | `sophora`, `styphnolobium`, `pagoda`, `locust`, `robinia` | Allergy/Immunology | Flowering/pollen and immune-response associations map to allergy/immunology. |
| 14 | `holly`, `ilex`, `snowbell`, `styrax`, `maackia`, `katsura`, `cercidiphyllum` | Preventive Medicine | Hardy ornamental species become prevention and maintenance specialists. |
| 15 | `ailanthus`, `tree of heaven` | Family Medicine | Tough, everyday urban survivorship maps to general neighborhood care. |
| 16 | No match | Weighted fallback | Rare species are assigned deterministically across common specialties so the dataset stays varied. |

Fallback specialty weights are: Family Medicine 18, Internal Medicine 16, Preventive Medicine 11, Pediatrics 8, Geriatrics 8, Dermatology 7, Cardiology 7, Pulmonology 6, Gastroenterology 6, Endocrinology 5, Psychiatry 5, Sports Medicine 4, Allergy/Immunology 4, Women's Health 4.

## All Tree Kinds And Assigned Specialties

| Common Name | Scientific Name | Specialty | Count |
|---|---|---|---:|
| 'Schubert' Chokecherry | Prunus virginiana | Pediatrics | 184 |
| American Beech | Fagus grandifolia | Geriatrics | 9 |
| American Elm | Ulmus americana | Dermatology | 209 |
| American Hophornbeam | Ostrya virginiana | Sports Medicine | 27 |
| American Hornbeam | Carpinus caroliniana | Sports Medicine | 27 |
| American Larch | Larix laricina | Internal Medicine | 1 |
| American Linden | Tilia americana | Psychiatry | 484 |
| Amur Cork Tree | Phellodendron amurense | Allergy/Immunology | 6 |
| Amur Maackia | Maackia amurensis | Preventive Medicine | 43 |
| Amur Maple | Acer ginnala | Endocrinology | 50 |
| Arborvitae | Thuja occidentalis | Pulmonology | 6 |
| Ash | Fraxinus | Sports Medicine | 30 |
| Atlantic White Cedar | Chamaecyparis thyoides | Pulmonology | 5 |
| Bald Cypress | Taxodium distichum | Pulmonology | 28 |
| Bigtooth Aspen | Populus grandidentata | Preventive Medicine | 2 |
| Black Cherry | Prunus serotina | Pediatrics | 17 |
| Black Locust | Robinia pseudoacacia | Allergy/Immunology | 85 |
| Black Maple | Acer nigrum | Endocrinology | 1 |
| Black Oak | Quercus velutina | Geriatrics | 44 |
| Black Walnut | Juglans nigra | Family Medicine | 9 |
| Blackgum | Nyssa sylvatica | Endocrinology | 9 |
| Boxelder | Acer negundo | Endocrinology | 2 |
| Bur Oak | Quercus macrocarpa | Geriatrics | 7 |
| Callery Pear | Pyrus calleryana | Women's Health | 2,647 |
| Catalpa | Catalpa | Pulmonology | 18 |
| Cherry | Prunus | Pediatrics | 578 |
| Chinese Chestnut | Castanea mollissima | Gastroenterology | 3 |
| Chinese Elm | Ulmus parvifolia | Dermatology | 210 |
| Chinese Fringetree | Chionanthus retusus | Pulmonology | 3 |
| Chinese Tree Lilac | Syringa pekinensis | Internal Medicine | 6 |
| Cockspur Hawthorn | Crataegus crusgalli var. inermis | Cardiology | 13 |
| Common Hackberry | Celtis occidentalis | Gastroenterology | 36 |
| Cornelian Cherry | Cornus mas | Pediatrics | 20 |
| Crab Apple | Malus | Gastroenterology | 59 |
| Crepe Myrtle | Lagerstroemia | Family Medicine | 15 |
| Crimson King Maple | Acer platanoides 'Crimson King' | Endocrinology | 137 |
| Cucumber Magnolia | Magnolia acuminata | Women's Health | 3 |
| Dawn Redwood | Metasequoia glyptostroboides | Geriatrics | 61 |
| Eastern Cottonwood | Populus deltoides | Endocrinology | 5 |
| Eastern Hemlock | Tsuga canadensis | Psychiatry | 5 |
| Eastern Redbud | Cercis canadensis | Family Medicine | 55 |
| Eastern Redcedar | Juniperus virginiana | Pulmonology | 16 |
| Empress Tree | Paulownia tomentosa | Women's Health | 12 |
| English Oak | Quercus robur | Geriatrics | 49 |
| European Alder | Alnus glutinosa | Pediatrics | 1 |
| European Beech | Fagus sylvatica | Geriatrics | 3 |
| European Hornbeam | Carpinus betulus | Sports Medicine | 39 |
| False Cypress | Chamaecyparis pisifera | Pulmonology | 1 |
| Flowering Dogwood | Cornus florida | Pediatrics | 47 |
| Ginkgo | Ginkgo biloba | Neurology | 1,395 |
| Golden Raintree | Koelreuteria paniculata | Family Medicine | 84 |
| Green Ash | Fraxinus pennsylvanica | Sports Medicine | 614 |
| Hardy Rubber Tree | Eucommia ulmoides | Internal Medicine | 12 |
| Hawthorn | Crataegus | Cardiology | 38 |
| Hedge Maple | Acer campestre | Endocrinology | 59 |
| Holly | Ilex | Preventive Medicine | 6 |
| Honeylocust | Gleditsia triacanthos var. inermis | Internal Medicine | 3,539 |
| Horse Chestnut | Aesculus hippocastanum | Gastroenterology | 19 |
| Japanese Hornbeam | Carpinus japonica | Sports Medicine | 25 |
| Japanese Maple | Acer palmatum | Endocrinology | 21 |
| Japanese Snowbell | Styrax japonicus | Preventive Medicine | 5 |
| Japanese Tree Lilac | Syringa reticulata | Pediatrics | 89 |
| Japanese Zelkova | Zelkova serrata | Dermatology | 897 |
| Katsura Tree | Cercidiphyllum japonicum | Preventive Medicine | 24 |
| Kentucky Coffeetree | Gymnocladus dioicus | Gastroenterology | 71 |
| Kentucky Yellowwood | Cladrastis kentukea | Pulmonology | 14 |
| Kousa Dogwood | Cornus kousa | Pediatrics | 7 |
| Littleleaf Linden | Tilia cordata | Psychiatry | 1,308 |
| London Planetree | Platanus x acerifolia | Internal Medicine | 2,397 |
| Magnolia | Magnolia | Women's Health | 8 |
| Maple | Acer | Endocrinology | 91 |
| Mimosa | Albizia julibrissin | Family Medicine | 10 |
| Mulberry | Morus | Gastroenterology | 28 |
| Northern Red Oak | Quercus rubra | Geriatrics | 269 |
| Norway Maple | Acer platanoides | Endocrinology | 877 |
| Norway Spruce | Picea abies | Pulmonology | 6 |
| Ohio Buckeye | Aesculus glabra | Endocrinology | 6 |
| Oklahoma Redbud | Cercis reniformis | Internal Medicine | 5 |
| Pagoda Dogwood | Cornus alternifolia | Pediatrics | 6 |
| Paper Birch | Betula papyrifera | Dermatology | 22 |
| Paperbark Maple | Acer griseum | Endocrinology | 5 |
| Persian Ironwood | Parrotia persica | Preventive Medicine | 6 |
| Pignut Hickory | Carya glabra | Pediatrics | 2 |
| Pin Oak | Quercus palustris | Geriatrics | 1,341 |
| Pine | Pinus | Pulmonology | 6 |
| Pitch Pine | Pinus rigida | Pulmonology | 2 |
| Pond Cypress | Taxodium ascendens | Pulmonology | 3 |
| Purple-Leaf Plum | Prunus cerasifera | Pediatrics | 150 |
| Quaking Aspen | Populus tremuloides | Pulmonology | 4 |
| Red Maple | Acer rubrum | Endocrinology | 324 |
| Red Pine | Pinus resinosa | Pulmonology | 1 |
| River Birch | Betula nigra | Dermatology | 6 |
| Sassafras | Sassafras albidum | Cardiology | 4 |
| Sawtooth Oak | Quercus acutissima | Geriatrics | 53 |
| Scarlet Oak | Quercus coccinea | Geriatrics | 11 |
| Schumard'S Oak | Quercus shumardii | Geriatrics | 42 |
| Serviceberry | Amelanchier | Pediatrics | 38 |
| Shingle Oak | Quercus imbricaria | Geriatrics | 12 |
| Siberian Elm | Ulmus pumila | Dermatology | 41 |
| Silver Birch | Betula pendula | Dermatology | 13 |
| Silver Linden | Tilia tomentosa | Psychiatry | 260 |
| Silver Maple | Acer saccharinum | Endocrinology | 144 |
| Smoketree | Cotinus coggygria | Pediatrics | 1 |
| Sophora | Styphnolobium japonicum | Allergy/Immunology | 1,203 |
| Southern Magnolia | Magnolia grandiflora | Women's Health | 9 |
| Southern Red Oak | Quercus falcata | Geriatrics | 4 |
| Spruce | Picea | Pulmonology | 1 |
| Sugar Maple | Acer saccharum | Endocrinology | 96 |
| Swamp White Oak | Quercus bicolor | Geriatrics | 157 |
| Sweetgum | Liquidambar styraciflua | Pulmonology | 159 |
| Sycamore Maple | Acer pseudoplatanus | Endocrinology | 69 |
| Tartar Maple | Acer tataricum | Endocrinology | 7 |
| Tree Of Heaven | Ailanthus altissima | Family Medicine | 27 |
| Tulip-Poplar | Liriodendron tulipifera | Women's Health | 7 |
| Turkish Hazelnut | Corylus colurna | Pediatrics | 11 |
| Two-Winged Silverbell | Halesia diptera | Preventive Medicine | 11 |
| Weeping Willow | Salix babylonica | Sports Medicine | 5 |
| White Ash | Fraxinus americana | Sports Medicine | 18 |
| White Oak | Quercus alba | Geriatrics | 34 |
| White Pine | Pinus strobus | Pulmonology | 4 |
| Willow Oak | Quercus phellos | Geriatrics | 169 |

## Column Schema

| Column | Type | Description |
|---|---|---|
| `provider_id` | integer | Original tree ID; unique provider identifier. |
| `species_common` | text | Common tree species name. |
| `species_scientific` | text | Scientific tree species name. |
| `medical_specialty` | categorical text | Species-based specialty. Same species always receives the same specialty. |
| `provider_type` | categorical text | Tree-care provider style based on favorite status, health, problems, curb location, stewardship, guard status, specialty, and experience. |
| `tree_experience_level` | categorical text | Experience band derived from `years_of_practice`. |
| `years_of_practice` | integer | Experience proxy from tree diameter, with small seeded variation. |
| `years_at_current_spot` | integer | Estimated years at current practice location, derived from experience and site context. |
| `care_rating` | float | 1.5-5.0 rating based on health, sidewalk condition, problem burden, guard, stewardship, favorite status, and seeded variation. |
| `review_count` | integer | Fictional review count based on experience, diameter, favorite status, and seeded variation. |
| `star_doctor` | binary integer | 1 if the tree was marked favorite in the source data; otherwise 0. |
| `popularity_badge` | categorical text | `Star doctor` for favorite trees; otherwise `Neighborhood regular`. |
| `next_available_visit_days` | integer | Deterministic wait estimate based on specialty, popularity, rating, urgent-shade status, and seeded variation. |
| `weekend_availability` | boolean | Whether the tree is available on weekends. Trees can take breaks. |
| `storm_response_readiness` | categorical text | Standard/Medium/High readiness based on provider type and problem burden. |
| `care_accessibility_score` | integer | 25-100 score using problem count, sidewalk damage, curb location, and helpful guard status. |
| `shade_side_manner_score` | float | Tree version of bedside manner, based on rating, stewardship, guard, and seeded variation. |
| `root_cause_analysis_score` | float | Tree diagnostic score based on rating, experience, root problems, and seeded variation. |
| `follow_up_watering_score` | float | Follow-up quality score based on rating, guard, sidewalk condition, and seeded variation. |
| `care_philosophy` | text | Specialty-matched humorous care philosophy. |
| `care_audience` | categorical text | Specialty-driven audience description. |
| `primary_care_services` | text | Specialty-matched tree-care services. |
| `signature_prescription` | text | Specialty-matched humorous prescription. |
| `office_vibe` | text | Specialty/site-context description of the care setting. |
| `waiting_room_feature` | text | Specialty/site-context waiting-room feature. |
| `leaf_paperwork_level` | text | Humorous admin-workload description. |
| `branch_office_status` | text | Branch-network status based on branch problems and diameter. |
| `condition_summary` | text | Descriptive tree-health summary with contextual variation. |
| `problem_burden_level` | categorical text | Low/Moderate/High based on total tree problem count. |
| `tree_problem_count` | integer | Count of all tree problem indicators. |
| `root_problem_count` | integer | Count of root problem indicators. |
| `trunk_problem_count` | integer | Count of trunk problem indicators. |
| `branch_problem_count` | integer | Count of branch problem indicators. |
| `clinic_name` | text | Neighborhood-based fictional tree clinic name. |
| `clinic_address` | text | Tree address interpreted as clinic address. |
| `clinic_zipcode` | text/integer | Tree postcode interpreted as clinic ZIP code. |
| `clinic_city` | text | Tree city interpreted as clinic city. |
| `clinic_neighborhood` | text | Tree neighborhood interpreted as clinic neighborhood. |
| `clinic_state` | text | State. All rows are New York. |
| `clinic_latitude` | float | Tree latitude interpreted as clinic latitude. |
| `clinic_longitude` | float | Tree longitude interpreted as clinic longitude. |

## Numeric Distributions

| Column | Count | Mean | Std | Min | P25 | Median | P75 | Max |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `years_of_practice` | 21,739 | 16.94 | 8.77 | 1.0 | 10.0 | 16.0 | 21.0 | 45.0 |
| `years_at_current_spot` | 21,739 | 10.21 | 5.40 | 1.0 | 6.0 | 9.0 | 13.0 | 36.0 |
| `care_rating` | 21,739 | 3.88 | 0.58 | 1.5 | 3.5 | 3.9 | 4.3 | 5.0 |
| `review_count` | 21,739 | 45.14 | 24.16 | 1.0 | 28.0 | 42.0 | 58.0 | 257.0 |
| `next_available_visit_days` | 21,739 | 5.89 | 3.23 | 0.0 | 4.0 | 6.0 | 8.0 | 18.0 |
| `care_accessibility_score` | 21,739 | 82.71 | 12.04 | 28.0 | 73.0 | 82.0 | 91.0 | 97.0 |
| `shade_side_manner_score` | 21,739 | 3.95 | 0.63 | 1.3 | 3.5 | 4.0 | 4.4 | 5.0 |
| `root_cause_analysis_score` | 21,739 | 3.91 | 0.59 | 1.4 | 3.5 | 4.0 | 4.3 | 5.0 |
| `follow_up_watering_score` | 21,739 | 3.94 | 0.65 | 1.3 | 3.5 | 4.0 | 4.4 | 5.0 |
| `tree_problem_count` | 21,739 | 1.42 | 0.69 | 1.0 | 1.0 | 1.0 | 2.0 | 6.0 |
| `root_problem_count` | 21,739 | 0.67 | 0.59 | 0.0 | 0.0 | 1.0 | 1.0 | 3.0 |
| `trunk_problem_count` | 21,739 | 0.32 | 0.49 | 0.0 | 0.0 | 0.0 | 1.0 | 3.0 |
| `branch_problem_count` | 21,739 | 0.43 | 0.52 | 0.0 | 0.0 | 0.0 | 1.0 | 3.0 |

## Binary Fields

| Column | Value | Count | Percent |
|---|---|---:|---:|
| `star_doctor` | 0 | 21,730 | 99.96% |
| `star_doctor` | 1 | 9 | 0.04% |
| `weekend_availability` | True | 11,999 | 55.20% |
| `weekend_availability` | False | 9,740 | 44.80% |

## Categorical Value Distributions

### `medical_specialty`

| Value | Count | Percent |
|---|---:|---:|
| Internal Medicine | 5,960 | 27.42% |
| Women's Health | 2,686 | 12.36% |
| Geriatrics | 2,265 | 10.42% |
| Psychiatry | 2,057 | 9.46% |
| Endocrinology | 1,903 | 8.75% |
| Dermatology | 1,398 | 6.43% |
| Neurology | 1,395 | 6.42% |
| Allergy/Immunology | 1,294 | 5.95% |
| Pediatrics | 1,151 | 5.29% |
| Sports Medicine | 785 | 3.61% |
| Pulmonology | 277 | 1.27% |
| Gastroenterology | 216 | 0.99% |
| Family Medicine | 200 | 0.92% |
| Preventive Medicine | 97 | 0.45% |
| Cardiology | 55 | 0.25% |

### `provider_type`

| Value | Count | Percent |
|---|---:|---:|
| Neighborhood care tree | 8,256 | 37.98% |
| Friendly curbside generalist | 4,962 | 22.83% |
| Elder shade practitioner | 4,192 | 19.28% |
| Community-rooted care tree | 2,354 | 10.83% |
| Urgent shade provider | 1,466 | 6.74% |
| Quiet courtyard specialist | 269 | 1.24% |
| Preventive canopy specialist | 231 | 1.06% |
| Star tree doctor | 9 | 0.04% |

### `tree_experience_level`

| Value | Count | Percent |
|---|---:|---:|
| Established neighborhood healer | 10,473 | 48.18% |
| Seasoned canopy clinician | 6,711 | 30.87% |
| Newly rooted resident | 2,540 | 11.68% |
| Ancient attending | 2,015 | 9.27% |

### Other Categorical Fields

| Column | Unique Values | Most Common Value | Count | Percent |
|---|---:|---|---:|---:|
| `popularity_badge` | 2 | Neighborhood regular | 21,730 | 99.96% |
| `storm_response_readiness` | 3 | Standard | 15,895 | 73.12% |
| `care_audience` | 7 | Adults and curious passersby | 8,595 | 39.54% |
| `problem_burden_level` | 3 | Low | 19,976 | 91.89% |
| `clinic_state` | 1 | New York | 21,739 | 100.00% |

## Descriptive Text Diversity

| Column | Unique Values | Most Common Value | Count | Percent |
|---|---:|---|---:|---:|
| `care_philosophy` | 51 | Review the whole canopy before treating one leaf | 1,937 | 8.91% |
| `primary_care_services` | 45 | multi-symptom sorting; calm diagnostics; practical branch-by-branch planning | 2,051 | 9.43% |
| `signature_prescription` | 44 | Review the whole canopy before treating one leaf. | 2,051 | 9.43% |
| `office_vibe` | 33 | A little intense, but committed to growth | 3,424 | 15.75% |
| `waiting_room_feature` | 55 | Sun-dappled waiting area | 2,124 | 9.77% |
| `leaf_paperwork_level` | 15 | Slightly rustly but functional | 3,593 | 16.53% |
| `branch_office_status` | 13 | Branch office open with notes | 3,027 | 13.92% |
| `condition_summary` | 21 | Healthy-looking canopy, minimal drama | 3,280 | 15.09% |

## Species And Location Summary

| Column | Unique Values | Most Common Value | Count | Percent |
|---|---:|---|---:|---:|
| `species_common` | 121 | Honeylocust | 3,539 | 16.28% |
| `species_scientific` | 121 | Gleditsia triacanthos var. inermis | 3,539 | 16.28% |
| `clinic_name` | 1,216 | Upper East Side Branch Office | 169 | 0.78% |
| `clinic_address` | 17,994 | 292 Greenwich Street | 12 | 0.06% |
| `clinic_zipcode` | 177 | 11385 | 1,328 | 6.11% |
| `clinic_city` | 45 | New York | 7,925 | 36.46% |
| `clinic_neighborhood` | 186 | Upper East Side-Carnegie Hill | 1,080 | 4.97% |
| `clinic_latitude` | 21,722 | 40.76092549 | 3 | 0.01% |
| `clinic_longitude` | 21,712 | -73.98654114 | 3 | 0.01% |

### Top Species

| Species | Count | Percent |
|---|---:|---:|
| Honeylocust | 3,539 | 16.28% |
| Callery Pear | 2,647 | 12.18% |
| London Planetree | 2,397 | 11.03% |
| Ginkgo | 1,395 | 6.42% |
| Pin Oak | 1,341 | 6.17% |
| Littleleaf Linden | 1,308 | 6.02% |
| Sophora | 1,203 | 5.53% |
| Japanese Zelkova | 897 | 4.13% |
| Norway Maple | 877 | 4.03% |
| Green Ash | 614 | 2.82% |

### Top Cities

| City | Count | Percent |
|---|---:|---:|
| New York | 7,925 | 36.46% |
| Brooklyn | 7,455 | 34.29% |
| Ridgewood | 1,328 | 6.11% |
| Bronx | 1,205 | 5.54% |
| Staten Island | 850 | 3.91% |
| Astoria | 383 | 1.76% |
| Jackson Heights | 213 | 0.98% |
| Middle Village | 183 | 0.84% |
| Flushing | 171 | 0.79% |
| Maspeth | 165 | 0.76% |

## Current Validation Checks

| Check | Result |
|---|---:|
| Output rows | 21,739 |
| Output columns | 41 |
| `provider_id` unique count | 21,739 |
| `provider_id` equals original `tree_id` | True |
| Species with inconsistent specialties | 0 |
| Diameter-to-years correlation | 0.974 |
| Care rating range | 1.5 to 5.0 |
| Share of care ratings >= 4.0 | 48.2% |
| Weekend availability true share | 55.2% |

## Suggested Notebook Checks

```python
ptc = pd.read_csv("data/processed/primary_tree_care_providers.csv")

ptc.shape
ptc.head()
ptc["medical_specialty"].value_counts()
ptc["provider_type"].value_counts()
ptc["care_rating"].describe()
(ptc["care_rating"] >= 4).mean()
ptc["weekend_availability"].value_counts(normalize=True)
ptc.groupby(["species_common", "species_scientific"])["medical_specialty"].nunique().max()
```
