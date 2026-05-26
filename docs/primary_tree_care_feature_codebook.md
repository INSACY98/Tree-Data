# Primary Tree Care Data Description

Source file: `data/processed/trees_with_favorites_live2.csv`
Output file: `data/processed/primary_tree_care_providers2.csv`
Transformation script: `scripts/primary_tree_care_transform.py`
Rows: 96,950
Columns: 38
Random seed: `20260523`

## Concept

Each row is one living NYC tree reimagined as a public primary-care provider. The original `tree_id` becomes `provider_id`; the tree remains the provider, so the dataset does not create human names, insurance fields, referrals, telehealth, languages, medical schools, or hospital affiliations. Care is assumed to be open to everyone.

Most generated fields are deterministic functions of species, tree diameter, health, sidewalk condition, problem indicators, stewardship, guard status, favorite status, and location. Controlled randomness is seeded by `provider_id`, feature name, and the project seed so the same input creates the same output every time.

## Current Output Summary

| Metric | Value |
| --- | --- |
| Input rows read | 96,950 |
| Provider rows written | 96,950 |
| Unique provider IDs | 96,950 |
| Unique tree kinds | 132 |
| Unique specialties | 30 |
| Star doctors | 9,695 (10.00%) |
| Target star-doctor share | 10% |
| Average rating | 4.25 |
| Median rating | 4.3 |
| Average wait days | 6.07 |
| Map neighborhood groups | 263 |

## Local Map

The local interactive map is generated from the current provider CSV and saved here:

[Open `primary_tree_care_map.html`](primary_tree_care_map.html)

Regenerate it with:

```bash
python scripts/build_primary_tree_care_map.py
```

The current map aggregates individual trees into neighborhood circles for speed. It covers 263 neighborhood groups and 96,950 tree providers.

## Transformation Strategy

| Feature Area | Mapping Strategy |
| --- | --- |
| `provider_id` | Uses the original `tree_id`; no new human identity is created. |
| `medical_specialty` | Assigned once per species using common and scientific names. The same species always receives the same specialty. |
| `star_doctor` | Keeps all source favorites, then adds reproducible random stars until about 10% of all rows are stars. |
| Ratings and wait days | Derived from health, sidewalk condition, problem burden, stewardship, guard status, specialty demand, and star status. Stars get rating support and shorter waits. |
| `searchable_conditions` | Draws realistic health concerns from the assigned specialty, not from arbitrary row-level randomness. |
| Descriptive text | Uses specialty, species, health, neighborhood, star status, rating, wait time, and problem burden to create varied profile text. |
| Location fields | Renames tree address, ZIP, city, neighborhood, state, latitude, and longitude into clinic fields. |
| Removed fields | `doctor_tagline`, `condition_summary`, `problem_burden_level`, internal problem-count columns, and extra score columns are not exported. |

## Star Doctor Logic

`star_doctor` is designed to be popular but not rare. The script keeps every existing favorite tree as a star doctor, then selects additional trees using a deterministic seeded score until the total reaches approximately 10% of the dataset. In this output, the target is exact: 9,695 of 96,950 providers are star doctors.

Star doctors receive stronger profile attributes: higher minimum rating support, shorter appointment waits, larger review counts, a small accessibility boost, and more polished wording in bio, philosophy, clinic description, and reviews.

## Specialty Mapping Rules

Specialty mapping is the core transformation. The script joins `common_name` and `scientific_name` into lowercase species text and evaluates the rules below in order. The first match wins. If a species does not match any symbolic rule, it receives a deterministic weighted fallback specialty. If the dataset has at least 30 species and a specialty is missing, rare species are reassigned first so all 30 specialties are represented while common symbolic mappings remain dominant.

| Order | Species Text Match | Assigned Specialty | Rationale |
| --- | --- | --- | --- |
| 1 | `ginkgo` | Neurology | Ginkgo has a long cultural association with memory, attention, and cognition. |
| 2 | `hawthorn`, `crataegus` | Cardiology | Hawthorn is traditionally linked to heart and circulation support. |
| 3 | `horse chestnut`, `aesculus`, `buckeye` | Vascular Medicine | Horse chestnut and buckeye references suggest circulation, veins, and flow. |
| 4 | `red maple`, `red oak`, `redcedar`, `scarlet oak`, `crimson king` | Hematology | Red-colored species names are translated into blood and hematology associations. |
| 5 | `linden`, `tilia` | Psychiatry | Linden and similar calming species suggest rest, mood, and nervous-system care. |
| 6 | `hemlock`, `tsuga`, `douglas-fir`, `pseudotsuga`, `drooping`, `cedar of lebanon` | Sleep Medicine | Weeping or drooping forms read as quiet, rest-oriented, and sleep-adjacent. |
| 7 | `oak`, `quercus`, `beech`, `fagus`, `redwood`, `sequoia`, `metasequoia` | Geriatrics | Long-lived and elder-like trees become longevity and aging specialists. |
| 8 | `honeylocust`, `gleditsia`, `planetree`, `platanus`, `london planetree` | Internal Medicine | Common NYC street-tree generalists become broad adult-care providers. |
| 9 | `shantung` | Occupational Medicine | Place-named species become workaday, commute-aware occupational health trees. |
| 10 | `maple`, `acer`, `sweetgum`, `liquidambar`, `blackgum`, `nyssa` | Endocrinology | Sap, sugar, and seasonal energy associations map to metabolism and hormones. |
| 11 | `willow`, `salix` | Pain Management | Willow's salicin association maps naturally to pain relief and symptom control. |
| 12 | `ash`, `fraxinus`, `hornbeam`, `carpinus`, `ostrya`, `ironwood`, `parrotia` | Orthopedics | Hard, structural woods become bone, joint, posture, and movement specialists. |
| 13 | `black pine`, `pinus nigra` | Emergency Medicine | Black pine becomes a rapid-access triage tree because it is tough, compact, and visibly street-ready. |
| 14 | `pine`, `pinus`, `spruce`, `picea`, `fir`, `abies`, `cedar`, `juniper`, `juniperus`, `arborvitae`, `thuja`, `cypress`, `chamaecyparis`, `catalpa` | Pulmonology | Evergreen, resinous, aromatic, and breezy species map to lungs and airways. |
| 15 | `river birch` | Urology | River and water names suggest urinary and fluid-system care. |
| 16 | `zelkova`, `elm`, `ulmus`, `birch`, `betula`, `paperbark`, `sycamore` | Dermatology | Bark, surface texture, peeling, and visible skin-like layers map to dermatology. |
| 17 | `magnolia`, `tulip`, `liriodendron` | Women's Health | Flowering and bloom-centered species become supportive life-stage care. |
| 18 | `cherry`, `plum`, `prunus`, `serviceberry`, `amelanchier`, `dogwood`, `cornus`, `redbud`, `cercis`, `silverbell`, `halesia`, `snowbell`, `styrax` | Pediatrics | Blossom, fruit, and sapling associations become child and adolescent care. |
| 19 | `apple`, `malus`, `hackberry`, `celtis`, `coffeetree`, `gymnocladus` | Gastroenterology | Fruit, food, beans, and post-lunch associations map to digestive care. |
| 20 | `walnut`, `juglans`, `chestnut`, `castanea`, `hazelnut`, `corylus`, `mulberry`, `morus`, `pear`, `pyrus` | Nutrition and Weight Management | Fruit and nut species become food, metabolism, and sustainable habit specialists. |
| 21 | `sophora`, `styphnolobium`, `pagoda`, `locust`, `robinia`, `mimosa`, `albizia` | Allergy and Immunology | Flowering, pollen, and immune-response associations map to allergy care. |
| 22 | `holly`, `ilex`, `maackia`, `katsura`, `cercidiphyllum`, `hardy rubber` | Preventive Medicine | Hardy ornamental species become maintenance, screening, and prevention specialists. |
| 23 | `amur cork`, `phellodendron`, `sassafras`, `ailanthus`, `tree of heaven` | Infectious Disease | Medicinal, hardy, and invasive-survivor associations become infection specialists. |
| 24 | `alder`, `alnus`, `cottonwood`, `populus deltoides`, `taxodium`, `bald cypress`, `pond cypress` | Nephrology | Wetland and water-filtering associations map to kidney and fluid balance care. |
| 25 | `lilac`, `syringa`, `fringetree`, `chionanthus` | ENT / Otolaryngology | Fragrant flowering species suggest nose, throat, sinus, and voice care. |
| 26 | `empress`, `paulownia`, `golden rain`, `koelreuteria` | Ophthalmology | Large leaves, bright crowns, and light-filtering canopies map to vision care. |
| 27 | `eucommia`, `rubber tree`, `yellowwood`, `cladrastis` | Rheumatology | Flexible or traditionally medicinal woods suggest connective tissue and inflammation. |
| 28 | `smoketree`, `cotinus` | Oncology | Smoke and abnormal-growth imagery becomes a careful, serious screening specialty. |
| 29 | `aspen`, `populus tremuloides`, `larch`, `larix` | Sports Medicine | Quaking, flexible, and trail-associated species map to activity and recovery. |
| 30 | `kentucky`, `turkish`, `persian`, `american`, `european`, `chinese`, `japanese` | Occupational Medicine | Place-named species become workaday, commute-aware occupational health trees. |
| 31 | `silver`, `green`, `black`, `white` | Emergency Medicine | Broad color-name groups become practical rapid-access fallback clinicians. |
| 32 | `crepe myrtle`, `lagerstroemia`, `mimosa`, `goldenrain` | Family Medicine | Hardy everyday ornamental trees become neighborhood primary-care generalists. |
| Fallback | No keyword match | Weighted across all 30 specialties | Keeps uncommon species varied while remaining reproducible. |

## Specialties And Searchable Conditions

| Specialty | Care Focus | Tree Style | Searchable Conditions Pool |
| --- | --- | --- | --- |
| Family Medicine | whole-person care | whole-block | annual physical, cold and flu, preventive care, vaccinations, minor injuries, routine checkups, high blood pressure screening |
| Internal Medicine | adult primary care | root-to-canopy | chronic disease care, fatigue, medication review, high blood pressure, high cholesterol, diabetes follow-up, adult wellness visits |
| Pediatrics | child and adolescent care | sapling-friendly | childhood fever, growth concerns, school physicals, routine vaccinations, seasonal allergies, ear infections, well-child visits |
| Geriatrics | older-adult care | long-view | memory concerns, fall risk, medication management, mobility changes, chronic disease care, caregiver planning, frailty screening |
| Preventive Medicine | prevention-first care | maintenance-minded | annual screenings, vaccination planning, healthy aging, risk reduction, lifestyle counseling, cancer screening reminders, blood pressure checks |
| Dermatology | skin and surface care | bark-aware | acne, eczema, psoriasis, skin rash, sun damage, mole checks, dry skin |
| Cardiology | heart and circulation care | steady-pulse | high blood pressure, chest pain, high cholesterol, heart palpitations, shortness of breath, heart disease prevention, irregular heartbeat |
| Pulmonology | breathing care | breeze-assisted | asthma, chronic cough, shortness of breath, bronchitis, COPD, wheezing, post-viral breathing symptoms |
| Gastroenterology | digestive care | gut-calm | acid reflux, IBS, stomach pain, constipation, diarrhea, bloating, colon cancer screening |
| Endocrinology | metabolic care | sap-balanced | diabetes, thyroid disorder, weight changes, prediabetes, hormone imbalance, fatigue, metabolic syndrome |
| Allergy and Immunology | immune and allergy care | pollen-diplomatic | seasonal allergies, food allergies, hives, asthma triggers, immune concerns, sinus congestion, eczema flares |
| Psychiatry | mental health care | calm-canopy | anxiety, depression, insomnia, stress management, burnout, panic symptoms, mood changes |
| Sports Medicine | movement care | stretch-friendly | sprains, running injuries, knee pain, shoulder pain, overuse injuries, return-to-activity planning, muscle strains |
| Women's Health | life-stage care | bloom-aware | well-woman visit, menstrual concerns, menopause symptoms, contraception counseling, pelvic pain, breast health, pregnancy planning |
| Neurology | brain and nerve care | focus-restoring | migraine, memory changes, headache, dizziness, numbness and tingling, brain fog, tremor |
| Rheumatology | inflammation care | flexible-branch | joint pain, arthritis, autoimmune concerns, inflammation, morning stiffness, lupus monitoring, gout |
| Pain Management | pain-focused care | willow-calm | chronic pain, back pain, neck pain, nerve pain, joint pain, pain flares, non-opioid pain planning |
| Sleep Medicine | sleep and rest care | quiet-hour | insomnia, sleep apnea, snoring, daytime sleepiness, restless sleep, sleep schedule problems, fatigue |
| Nutrition and Weight Management | nutrition care | fruit-and-nut | weight changes, cholesterol nutrition, prediabetes nutrition, heart-healthy eating, digestive nutrition, meal planning, metabolic health |
| Infectious Disease | infection care | hardy-defense | recurrent infections, fever evaluation, travel health, tick-borne illness concerns, wound infection, antibiotic questions, immune suppression concerns |
| Nephrology | kidney and fluid care | water-wise | kidney disease, high blood pressure, protein in urine, electrolyte imbalance, fluid retention, kidney stone prevention, chronic kidney monitoring |
| ENT / Otolaryngology | ear, nose, and throat care | fragrant-airway | sinus infection, ear pain, sore throat, hearing concerns, voice changes, nasal congestion, tonsil concerns |
| Ophthalmology | eye and vision care | light-filtering | vision changes, dry eyes, eye irritation, glaucoma screening, cataract concerns, red eye, diabetic eye screening |
| Orthopedics | bone and joint care | strong-limb | joint injury, fracture follow-up, back pain, hip pain, shoulder pain, arthritis, mobility problems |
| Urology | urinary care | flow-focused | urinary tract infection, urinary frequency, kidney stones, prostate concerns, bladder pain, incontinence, pelvic discomfort |
| Hematology | blood health care | red-leaf | anemia, easy bruising, blood clot history, low iron, abnormal blood counts, bleeding concerns, fatigue from anemia |
| Oncology | cancer screening and survivorship care | watchful-growth | cancer screening, lump evaluation, survivorship care, family cancer risk, abnormal imaging follow-up, unexplained weight loss, screening reminders |
| Occupational Medicine | work and city-life care | commute-aware | work injury, ergonomic strain, return-to-work visit, commute stress, repetitive motion pain, workplace exposure questions, job physicals |
| Emergency Medicine | same-day urgent care | rapid-shade | urgent symptoms, minor injuries, sudden pain, fever triage, cuts and scrapes, dizziness, same-day assessment |
| Vascular Medicine | vessel and circulation care | flow-steady | leg swelling, varicose veins, poor circulation, blood clot concerns, cold feet, leg pain when walking, vascular risk review |

## All Tree Kinds And Assigned Specialties

| Common Name | Scientific Name | Specialty | Count |
| --- | --- | --- | --- |
| 'Schubert' Chokecherry | Prunus virginiana | Pediatrics | 867 |
| American Beech | Fagus grandifolia | Geriatrics | 36 |
| American Elm | Ulmus americana | Dermatology | 1,178 |
| American Hophornbeam | Ostrya virginiana | Orthopedics | 198 |
| American Hornbeam | Carpinus caroliniana | Orthopedics | 222 |
| American Larch | Larix laricina | Sports Medicine | 10 |
| American Linden | Tilia americana | Psychiatry | 2,321 |
| Amur Cork Tree | Phellodendron amurense | Infectious Disease | 21 |
| Amur Maackia | Maackia amurensis | Preventive Medicine | 279 |
| Amur Maple | Acer ginnala | Endocrinology | 255 |
| Arborvitae | Thuja occidentalis | Pulmonology | 50 |
| Ash | Fraxinus | Orthopedics | 168 |
| Atlantic White Cedar | Chamaecyparis thyoides | Pulmonology | 49 |
| Atlas Cedar | Cedrus atlantica | Pulmonology | 8 |
| Bald Cypress | Taxodium distichum | Pulmonology | 211 |
| Bigtooth Aspen | Populus grandidentata | Sports Medicine | 12 |
| Black Cherry | Prunus serotina | Pediatrics | 87 |
| Black Locust | Robinia pseudoacacia | Allergy and Immunology | 331 |
| Black Maple | Acer nigrum | Endocrinology | 15 |
| Black Oak | Quercus velutina | Geriatrics | 250 |
| Black Pine | Pinus nigra | Emergency Medicine | 5 |
| Black Walnut | Juglans nigra | Nutrition and Weight Management | 67 |
| Blackgum | Nyssa sylvatica | Endocrinology | 60 |
| Blue Spruce | Picea pungens | Pulmonology | 11 |
| Boxelder | Acer negundo | Endocrinology | 12 |
| Bur Oak | Quercus macrocarpa | Geriatrics | 70 |
| Callery Pear | Pyrus calleryana | Nutrition and Weight Management | 11,107 |
| Catalpa | Catalpa | Pulmonology | 67 |
| Cherry | Prunus | Pediatrics | 3,777 |
| Chinese Chestnut | Castanea mollissima | Nutrition and Weight Management | 27 |
| Chinese Elm | Ulmus parvifolia | Dermatology | 1,000 |
| Chinese Fringetree | Chionanthus retusus | ENT / Otolaryngology | 25 |
| Chinese Tree Lilac | Syringa pekinensis | ENT / Otolaryngology | 40 |
| Cockspur Hawthorn | Crataegus crusgalli var. inermis | Cardiology | 37 |
| Common Hackberry | Celtis occidentalis | Gastroenterology | 239 |
| Cornelian Cherry | Cornus mas | Pediatrics | 169 |
| Crab Apple | Malus | Gastroenterology | 346 |
| Crepe Myrtle | Lagerstroemia | Family Medicine | 75 |
| Crimson King Maple | Acer platanoides 'Crimson King' | Hematology | 653 |
| Cucumber Magnolia | Magnolia acuminata | Women's Health | 21 |
| Dawn Redwood | Metasequoia glyptostroboides | Geriatrics | 451 |
| Douglas-Fir | Pseudotsuga menziesii | Sleep Medicine | 13 |
| Eastern Cottonwood | Populus deltoides | Nephrology | 29 |
| Eastern Hemlock | Tsuga canadensis | Sleep Medicine | 19 |
| Eastern Redbud | Cercis canadensis | Pediatrics | 423 |
| Eastern Redcedar | Juniperus virginiana | Hematology | 135 |
| Empress Tree | Paulownia tomentosa | Ophthalmology | 39 |
| English Oak | Quercus robur | Geriatrics | 228 |
| European Alder | Alnus glutinosa | Nephrology | 6 |
| European Beech | Fagus sylvatica | Geriatrics | 15 |
| European Hornbeam | Carpinus betulus | Orthopedics | 324 |
| False Cypress | Chamaecyparis pisifera | Pulmonology | 24 |
| Flowering Dogwood | Cornus florida | Pediatrics | 262 |
| Ginkgo | Ginkgo biloba | Neurology | 5,532 |
| Golden Raintree | Koelreuteria paniculata | Ophthalmology | 567 |
| Green Ash | Fraxinus pennsylvanica | Orthopedics | 2,355 |
| Hardy Rubber Tree | Eucommia ulmoides | Preventive Medicine | 127 |
| Hawthorn | Crataegus | Cardiology | 309 |
| Hedge Maple | Acer campestre | Endocrinology | 280 |
| Himalayan Cedar | Cedrus deodara | Pulmonology | 7 |
| Holly | Ilex | Preventive Medicine | 25 |
| Honeylocust | Gleditsia triacanthos var. inermis | Internal Medicine | 12,770 |
| Horse Chestnut | Aesculus hippocastanum | Vascular Medicine | 84 |
| Japanese Hornbeam | Carpinus japonica | Orthopedics | 110 |
| Japanese Maple | Acer palmatum | Endocrinology | 178 |
| Japanese Snowbell | Styrax japonicus | Pediatrics | 35 |
| Japanese Tree Lilac | Syringa reticulata | ENT / Otolaryngology | 568 |
| Japanese Zelkova | Zelkova serrata | Dermatology | 4,783 |
| Katsura Tree | Cercidiphyllum japonicum | Preventive Medicine | 126 |
| Kentucky Coffeetree | Gymnocladus dioicus | Gastroenterology | 541 |
| Kentucky Yellowwood | Cladrastis kentukea | Rheumatology | 53 |
| Kousa Dogwood | Cornus kousa | Pediatrics | 61 |
| Littleleaf Linden | Tilia cordata | Psychiatry | 5,279 |
| London Planetree | Platanus x acerifolia | Internal Medicine | 9,698 |
| Magnolia | Magnolia | Women's Health | 87 |
| Maple | Acer | Endocrinology | 556 |
| Mimosa | Albizia julibrissin | Allergy and Immunology | 27 |
| Mulberry | Morus | Nutrition and Weight Management | 121 |
| Northern Red Oak | Quercus rubra | Hematology | 1,268 |
| Norway Maple | Acer platanoides | Endocrinology | 3,364 |
| Norway Spruce | Picea abies | Pulmonology | 41 |
| Ohio Buckeye | Aesculus glabra | Vascular Medicine | 21 |
| Oklahoma Redbud | Cercis reniformis | Pediatrics | 27 |
| Osage-Orange | Maclura pomifera | Preventive Medicine | 10 |
| Pagoda Dogwood | Cornus alternifolia | Pediatrics | 38 |
| Paper Birch | Betula papyrifera | Dermatology | 112 |
| Paperbark Maple | Acer griseum | Endocrinology | 33 |
| Persian Ironwood | Parrotia persica | Orthopedics | 27 |
| Pignut Hickory | Carya glabra | Pulmonology | 11 |
| Pin Oak | Quercus palustris | Geriatrics | 6,247 |
| Pine | Pinus | Pulmonology | 17 |
| Pitch Pine | Pinus rigida | Pulmonology | 6 |
| Pond Cypress | Taxodium ascendens | Pulmonology | 44 |
| Purple-Leaf Plum | Prunus cerasifera | Pediatrics | 934 |
| Quaking Aspen | Populus tremuloides | Sports Medicine | 9 |
| Red Horse Chestnut | Aesculus x carnea | Vascular Medicine | 11 |
| Red Maple | Acer rubrum | Hematology | 1,687 |
| Red Pine | Pinus resinosa | Pulmonology | 7 |
| River Birch | Betula nigra | Urology | 54 |
| Sassafras | Sassafras albidum | Infectious Disease | 21 |
| Sawtooth Oak | Quercus acutissima | Geriatrics | 386 |
| Scarlet Oak | Quercus coccinea | Hematology | 120 |
| Schumard'S Oak | Quercus shumardii | Geriatrics | 226 |
| Scots Pine | Pinus sylvestris | Pulmonology | 5 |
| Serviceberry | Amelanchier | Pediatrics | 281 |
| Shantung Maple | Acer truncatum | Occupational Medicine | 5 |
| Shingle Oak | Quercus imbricaria | Geriatrics | 161 |
| Siberian Elm | Ulmus pumila | Dermatology | 247 |
| Silver Birch | Betula pendula | Dermatology | 56 |
| Silver Linden | Tilia tomentosa | Psychiatry | 1,198 |
| Silver Maple | Acer saccharinum | Endocrinology | 779 |
| Smoketree | Cotinus coggygria | Oncology | 9 |
| Sophora | Styphnolobium japonicum | Allergy and Immunology | 4,531 |
| Southern Magnolia | Magnolia grandiflora | Women's Health | 30 |
| Southern Red Oak | Quercus falcata | Hematology | 9 |
| Spruce | Picea | Pulmonology | 14 |
| Sugar Maple | Acer saccharum | Endocrinology | 408 |
| Swamp White Oak | Quercus bicolor | Geriatrics | 1,137 |
| Sweetgum | Liquidambar styraciflua | Endocrinology | 1,086 |
| Sycamore Maple | Acer pseudoplatanus | Internal Medicine | 242 |
| Tartar Maple | Acer tataricum | Endocrinology | 34 |
| Tree Of Heaven | Ailanthus altissima | Infectious Disease | 83 |
| Trident Maple | Acer buergerianum | Endocrinology | 8 |
| Tulip-Poplar | Liriodendron tulipifera | Women's Health | 81 |
| Turkish Hazelnut | Corylus colurna | Nutrition and Weight Management | 53 |
| Two-Winged Silverbell | Halesia diptera | Pediatrics | 37 |
| Virginia Pine | Pinus virginiana | Pulmonology | 3 |
| Weeping Willow | Salix babylonica | Pain Management | 34 |
| White Ash | Fraxinus americana | Orthopedics | 108 |
| White Oak | Quercus alba | Geriatrics | 202 |
| White Pine | Pinus strobus | Pulmonology | 28 |
| Willow Oak | Quercus phellos | Geriatrics | 737 |

## Column Schema

| Column | Type | Unique Values | Description |
| --- | --- | --- | --- |
| `provider_id` | int64 | 96,950 | Original tree ID used as the fictional provider ID. |
| `species_common` | str | 132 | Common tree species name. |
| `species_scientific` | str | 132 | Scientific tree species name. |
| `medical_specialty` | str | 30 | Species-based medical specialty; stable for each species. |
| `specialty_description` | str | 132 | Readable explanation of why the species maps to the specialty. |
| `searchable_conditions` | str | 32,206 | Comma-separated human conditions users might search for, selected from the specialty pool. |
| `provider_type` | str | 11 | Practice style inferred from star status, problems, health, location, stewardship, specialty, and experience. |
| `tree_experience_level` | str | 4 | Experience label derived from years of practice. |
| `years_of_practice` | int64 | 45 | Experience proxy based mainly on tree diameter with small seeded variation. |
| `years_at_current_spot` | int64 | 38 | Estimated years at this location based on experience, stewardship, sidewalk condition, and seeded variation. |
| `care_rating` | float64 | 33 | 1.2-5.0 review score; most ratings stay high, with penalties for problems and boosts for support/star status. |
| `review_count` | int64 | 243 | Fictional review volume based on experience, diameter, star status, and seeded variation. |
| `star_doctor` | int64 | 2 | Binary popularity marker: source favorites plus seeded additions to reach about 10%. |
| `popularity_badge` | str | 2 | Readable badge for star doctors vs neighborhood regulars. |
| `next_available_visit_days` | int64 | 20 | Estimated wait time using specialty demand, star priority, urgent style, rating demand, and seeded variation. |
| `weekend_availability` | bool | 2 | Whether weekend shade is available; many trees still take weekends off. |
| `storm_response_readiness` | str | 3 | Standard, Medium, or High readiness based on urgent/elder provider style and internal problem burden. |
| `care_accessibility_score` | int64 | 37 | 25-100 access score based on problems, sidewalk damage, curb location, guard status, and star boost. |
| `shade_side_manner_score` | float64 | 35 | 1.0-5.0 bedside-manner parody score using rating, stewardship, guard status, star status, and seeded variation. |
| `care_philosophy` | str | 2,495 | Varied natural-language care philosophy tied to specialty, health, star status, and location. |
| `provider_bio` | str | 17,342 | Short profile bio for the tree provider. |
| `clinic_description` | str | 50,146 | Description of the tree-as-clinic location and access context. |
| `patient_review_summary` | str | 95 | Rating-aware fictional review summary. |
| `care_audience` | str | 9 | Likely audience focus derived from specialty. |
| `primary_care_services` | str | 2,647 | Humorous service list derived from specialty and searchable conditions. |
| `signature_prescription` | str | 25 | Humorous advice line matched to specialty where possible. |
| `office_vibe` | str | 64 | Tone of the tree practice, using specialty and site condition. |
| `waiting_room_feature` | str | 66 | Humorous waiting-room feature for the sidewalk practice. |
| `leaf_paperwork_level` | str | 16 | Humorous workload/profile-admin indicator based on problems and star status. |
| `branch_office_status` | str | 13 | Humorous branch-network availability based on branch problems and diameter. |
| `clinic_name` | str | 1,660 | Generated clinic name using neighborhood and seeded suffix. |
| `clinic_address` | str | 72,709 | Tree address reused as clinic address. |
| `clinic_zipcode` | int64 | 183 | Tree postcode reused as clinic ZIP code. |
| `clinic_city` | str | 47 | Tree city reused as clinic city. |
| `clinic_neighborhood` | str | 188 | Tree neighborhood reused as clinic neighborhood. |
| `clinic_state` | str | 1 | Tree state reused as clinic state. |
| `clinic_latitude` | float64 | 96,721 | Tree latitude reused as clinic latitude. |
| `clinic_longitude` | float64 | 96,663 | Tree longitude reused as clinic longitude. |

## Numeric Distributions

| Column | Count | Mean | Std | Min | 25% | Median | 75% | Max |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `provider_id` | 96,950 | 290,155.34 | 195,895.03 | 16.00 | 129,249.50 | 252,418.00 | 417,850.25 | 722,674.00 |
| `years_of_practice` | 96,950 | 15.41 | 9.17 | 1.00 | 8.00 | 14.00 | 20.00 | 45.00 |
| `years_at_current_spot` | 96,950 | 9.31 | 5.56 | 1.00 | 5.00 | 8.00 | 12.00 | 38.00 |
| `care_rating` | 96,950 | 4.25 | 0.52 | 1.80 | 3.90 | 4.30 | 4.60 | 5.00 |
| `review_count` | 96,950 | 51.24 | 37.81 | 1.00 | 25.00 | 41.00 | 64.00 | 379.00 |
| `star_doctor` | 96,950 | 0.10 | 0.30 | 0.00 | 0.00 | 0.00 | 0.00 | 1.00 |
| `next_available_visit_days` | 96,950 | 6.07 | 3.32 | 0.00 | 4.00 | 6.00 | 8.00 | 19.00 |
| `care_accessibility_score` | 96,950 | 88.75 | 12.27 | 28.00 | 82.00 | 91.00 | 100.00 | 100.00 |
| `shade_side_manner_score` | 96,950 | 4.31 | 0.56 | 1.60 | 3.90 | 4.40 | 4.80 | 5.00 |
| `clinic_zipcode` | 96,950 | 10,760.16 | 762.63 | 83.00 | 10,065.00 | 11,203.00 | 11,233.00 | 11,694.00 |
| `clinic_latitude` | 96,950 | 40.72 | 0.08 | 40.50 | 40.67 | 40.72 | 40.77 | 40.91 |
| `clinic_longitude` | 96,950 | -73.95 | 0.09 | -74.25 | -73.98 | -73.95 | -73.90 | -73.70 |

## Categorical Unique Values And Counts

### `medical_specialty`
| Value | Count | Share |
| --- | --- | --- |
| Internal Medicine | 22,710 | 23.42% |
| Nutrition and Weight Management | 11,375 | 11.73% |
| Geriatrics | 10,146 | 10.47% |
| Psychiatry | 8,798 | 9.07% |
| Dermatology | 7,376 | 7.61% |
| Endocrinology | 7,068 | 7.29% |
| Pediatrics | 6,998 | 7.22% |
| Neurology | 5,532 | 5.71% |
| Allergy and Immunology | 4,889 | 5.04% |
| Hematology | 3,872 | 3.99% |
| Orthopedics | 3,512 | 3.62% |
| Gastroenterology | 1,126 | 1.16% |
| ENT / Otolaryngology | 633 | 0.65% |
| Ophthalmology | 606 | 0.63% |
| Pulmonology | 603 | 0.62% |
| Preventive Medicine | 567 | 0.58% |
| Cardiology | 346 | 0.36% |
| Women's Health | 219 | 0.23% |
| Infectious Disease | 125 | 0.13% |
| Vascular Medicine | 116 | 0.12% |
| Family Medicine | 75 | 0.08% |
| Urology | 54 | 0.06% |
| Rheumatology | 53 | 0.05% |
| Nephrology | 35 | 0.04% |
| Pain Management | 34 | 0.04% |
| Sleep Medicine | 32 | 0.03% |
| Sports Medicine | 31 | 0.03% |
| Oncology | 9 | 0.01% |
| Emergency Medicine | 5 | 0.01% |
| Occupational Medicine | 5 | 0.01% |

### `provider_type`
| Value | Count | Share |
| --- | --- | --- |
| Neighborhood care tree | 35,008 | 36.11% |
| Friendly curbside generalist | 23,745 | 24.49% |
| Elder shade practitioner | 15,554 | 16.04% |
| Community-rooted care tree | 5,650 | 5.83% |
| Urgent shade provider | 4,190 | 4.32% |
| Highly rated shade specialist | 3,275 | 3.38% |
| Star tree doctor | 3,257 | 3.36% |
| Popular canopy clinician | 3,163 | 3.26% |
| Quiet courtyard specialist | 2,295 | 2.37% |
| Preventive canopy specialist | 778 | 0.80% |
| Fast-access curbside clinician | 35 | 0.04% |

### `tree_experience_level`
| Value | Count | Share |
| --- | --- | --- |
| Established neighborhood healer | 45,029 | 46.45% |
| Seasoned canopy clinician | 24,190 | 24.95% |
| Newly rooted resident | 19,563 | 20.18% |
| Ancient attending | 8,168 | 8.42% |

### `star_doctor`
| Value | Count | Share |
| --- | --- | --- |
| 0 | 87,255 | 90.00% |
| 1 | 9,695 | 10.00% |

### `popularity_badge`
| Value | Count | Share |
| --- | --- | --- |
| Neighborhood regular | 87,255 | 90.00% |
| Star doctor | 9,695 | 10.00% |

### `weekend_availability`
| Value | Count | Share |
| --- | --- | --- |
| False | 63,305 | 65.30% |
| True | 33,645 | 34.70% |

### `storm_response_readiness`
| Value | Count | Share |
| --- | --- | --- |
| Standard | 76,638 | 79.05% |
| High | 19,779 | 20.40% |
| Medium | 533 | 0.55% |

### `clinic_city`
| Value | Count | Share |
| --- | --- | --- |
| Brooklyn | 32,769 | 33.80% |
| New York | 27,780 | 28.65% |
| Bronx | 7,403 | 7.64% |
| Staten Island | 7,094 | 7.32% |
| Ridgewood | 3,204 | 3.30% |
| Astoria | 2,296 | 2.37% |
| Flushing | 1,171 | 1.21% |
| Jamaica | 877 | 0.90% |
| Woodside | 874 | 0.90% |
| Forest Hills | 806 | 0.83% |
| Middle Village | 697 | 0.72% |
| Maspeth | 691 | 0.71% |
| Long Island City | 681 | 0.70% |
| Bayside | 675 | 0.70% |
| Jackson Heights | 673 | 0.69% |
| Queens Village | 648 | 0.67% |
| East Elmhurst | 561 | 0.58% |
| Elmhurst | 540 | 0.56% |
| Ozone Park | 525 | 0.54% |
| Corona | 509 | 0.53% |
| Richmond Hill | 454 | 0.47% |
| Sunnyside | 442 | 0.46% |
| Rego Park | 419 | 0.43% |
| College Point | 367 | 0.38% |
| Whitestone | 360 | 0.37% |
| Fresh Meadows | 343 | 0.35% |
| South Ozone Park | 338 | 0.35% |
| Hollis | 316 | 0.33% |
| Rockaway Park | 311 | 0.32% |
| Far Rockaway | 305 | 0.31% |
| Howard Beach | 304 | 0.31% |
| Arverne | 276 | 0.28% |
| Little Neck | 258 | 0.27% |
| Woodhaven | 251 | 0.26% |
| Bellerose | 230 | 0.24% |
| Central Park | 217 | 0.22% |
| Springfield Gardens | 207 | 0.21% |
| South Richmond Hill | 189 | 0.19% |
| Rosedale | 186 | 0.19% |
| Kew Gardens | 185 | 0.19% |
| Saint Albans | 150 | 0.15% |
| Oakland Gardens | 120 | 0.12% |
| Glen Oaks | 118 | 0.12% |
| Cambria Heights | 76 | 0.08% |
| Floral Park | 40 | 0.04% |
| New Hyde Park | 13 | 0.01% |
| Inwood | 1 | 0.00% |

## Descriptive Text Diversity

| Column | Unique Values | Example |
| --- | --- | --- |
| `care_philosophy` | 2,495 | The work is community-health focused, balancing blood health care with shade, patience, and the limits of urban soil. |
| `provider_bio` | 17,342 | In Midwood, this Scarlet Oak turns shade, seasonality, and a red-leaf temperament into an accessible Hematology profile. |
| `clinic_description` | 50,146 | Patients find this practice by walking to 1921 Avenue K; the waiting room is shade, sidewalk, and whatever the weather contributes. |
| `patient_review_summary` | 95 | Reviews are mixed but fair: the care is useful, the setting is real, and the tree is doing its best with urban conditions. |
| `specialty_description` | 132 | Hematology is assigned from the Scarlet Oak species profile: a red-leaf association with anemia, bruising, clot history, and blood counts. |
| `searchable_conditions` | 32,206 | blood clot history, anemia, easy bruising, low iron |

## Missing Values

No columns in the current output contain missing values.

## Removed Columns

| Column | Status |
| --- | --- |
| `root_cause_analysis_score` | Not present in final output |
| `follow_up_watering_score` | Not present in final output |
| `tree_problem_count` | Not present in final output |
| `root_problem_count` | Not present in final output |
| `trunk_problem_count` | Not present in final output |
| `branch_problem_count` | Not present in final output |
| `doctor_tagline` | Not present in final output |
| `condition_summary` | Not present in final output |
| `problem_burden_level` | Not present in final output |

## Validation Checks

| Check | Current Value | Interpretation |
| --- | --- | --- |
| Star-doctor share | 10.00% | Target is about 10% while preserving source favorites. |
| Unique specialties | 30 | Expected 30. |
| New searchable condition nulls | 0 | Expected 0. |
| Descriptive column nulls | 0 | Expected 0. |
| Removed columns present | none | Expected none. |
| Provider ID uniqueness | 96,950 unique IDs | Should match row count for one row per tree. |

## Sample Profiles

| `provider_id` | `species_common` | `medical_specialty` | `star_doctor` | `care_rating` | `next_available_visit_days` | `searchable_conditions` |
| --- | --- | --- | --- | --- | --- | --- |
| 181988 | Scarlet Oak | Hematology | 0 | 3.7 | 8 | blood clot history, anemia, easy bruising, low iron |
| 110153 | Japanese Zelkova | Dermatology | 0 | 4.1 | 14 | skin rash, eczema, acne, dry skin |
| 583615 | Sweetgum | Endocrinology | 0 | 4.4 | 9 | metabolic syndrome, diabetes, weight changes, hormone imbalance |
| 239868 | Ginkgo | Neurology | 0 | 5.0 | 11 | memory changes, migraine, tremor, headache, dizziness |
| 499220 | Littleleaf Linden | Psychiatry | 0 | 4.4 | 10 | stress management, panic symptoms, depression, burnout |
| 186329 | Sophora | Allergy and Immunology | 0 | 4.3 | 7 | food allergies, hives, asthma triggers, immune concerns |
| 206415 | Silver Linden | Psychiatry | 0 | 4.6 | 9 | depression, insomnia, mood changes, anxiety, burnout |
| 203799 | Pin Oak | Geriatrics | 0 | 4.5 | 4 | medication management, caregiver planning, frailty screening, fall risk, mobility changes |
