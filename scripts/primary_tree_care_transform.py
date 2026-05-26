from __future__ import annotations

import hashlib
from pathlib import Path

import numpy as np
import pandas as pd


RANDOM_SEED = 20260523
STAR_DOCTOR_TARGET_SHARE = 0.10
PROJECT_ROOT = Path(__file__).resolve().parents[1]
INPUT_CSV = PROJECT_ROOT / "data" / "processed" / "trees_with_favorites_live2.csv"
OUTPUT_CSV = PROJECT_ROOT / "data" / "processed" / "primary_tree_care_providers2.csv"


PROBLEM_COLUMNS = [
    "root_problem_paving_stones",
    "root_problem_metal_grates",
    "root_problem_other",
    "trunk_problem_wires",
    "trunk_problem_lights",
    "trunk_problem_other",
    "branch_problem_lights_wires",
    "branch_problem_shoes",
    "branch_problem_other",
]

REMOVED_OUTPUT_COLUMNS = [
    "root_cause_analysis_score",
    "follow_up_watering_score",
    "tree_problem_count",
    "root_problem_count",
    "trunk_problem_count",
    "branch_problem_count",
    "doctor_tagline",
    "condition_summary",
    "problem_burden_level",
]

ALL_SPECIALTIES = [
    "Family Medicine",
    "Internal Medicine",
    "Pediatrics",
    "Geriatrics",
    "Preventive Medicine",
    "Dermatology",
    "Cardiology",
    "Pulmonology",
    "Gastroenterology",
    "Endocrinology",
    "Allergy and Immunology",
    "Psychiatry",
    "Sports Medicine",
    "Women's Health",
    "Neurology",
    "Rheumatology",
    "Pain Management",
    "Sleep Medicine",
    "Nutrition and Weight Management",
    "Infectious Disease",
    "Nephrology",
    "ENT / Otolaryngology",
    "Ophthalmology",
    "Orthopedics",
    "Urology",
    "Hematology",
    "Oncology",
    "Occupational Medicine",
    "Emergency Medicine",
    "Vascular Medicine",
]

SPECIALTY_RULES = [
    (
        "Neurology",
        ("ginkgo",),
        "Ginkgo has a long cultural association with memory, attention, and cognition.",
    ),
    (
        "Cardiology",
        ("hawthorn", "crataegus"),
        "Hawthorn is traditionally linked to heart and circulation support.",
    ),
    (
        "Vascular Medicine",
        ("horse chestnut", "aesculus", "buckeye"),
        "Horse chestnut and buckeye references suggest circulation, veins, and flow.",
    ),
    (
        "Hematology",
        ("red maple", "red oak", "redcedar", "scarlet oak", "crimson king"),
        "Red-colored species names are translated into blood and hematology associations.",
    ),
    (
        "Psychiatry",
        ("linden", "tilia"),
        "Linden and similar calming species suggest rest, mood, and nervous-system care.",
    ),
    (
        "Sleep Medicine",
        ("hemlock", "tsuga", "douglas-fir", "pseudotsuga", "drooping", "cedar of lebanon"),
        "Weeping or drooping forms read as quiet, rest-oriented, and sleep-adjacent.",
    ),
    (
        "Geriatrics",
        ("oak", "quercus", "beech", "fagus", "redwood", "sequoia", "metasequoia"),
        "Long-lived and elder-like trees become longevity and aging specialists.",
    ),
    (
        "Internal Medicine",
        ("honeylocust", "gleditsia", "planetree", "platanus", "london planetree"),
        "Common NYC street-tree generalists become broad adult-care providers.",
    ),
    (
        "Occupational Medicine",
        ("shantung",),
        "Place-named species become workaday, commute-aware occupational health trees.",
    ),
    (
        "Endocrinology",
        ("maple", "acer", "sweetgum", "liquidambar", "blackgum", "nyssa"),
        "Sap, sugar, and seasonal energy associations map to metabolism and hormones.",
    ),
    (
        "Pain Management",
        ("willow", "salix"),
        "Willow's salicin association maps naturally to pain relief and symptom control.",
    ),
    (
        "Orthopedics",
        ("ash", "fraxinus", "hornbeam", "carpinus", "ostrya", "ironwood", "parrotia"),
        "Hard, structural woods become bone, joint, posture, and movement specialists.",
    ),
    (
        "Emergency Medicine",
        ("black pine", "pinus nigra"),
        "Black pine becomes a rapid-access triage tree because it is tough, compact, and visibly street-ready.",
    ),
    (
        "Pulmonology",
        (
            "pine",
            "pinus",
            "spruce",
            "picea",
            "fir",
            "abies",
            "cedar",
            "juniper",
            "juniperus",
            "arborvitae",
            "thuja",
            "cypress",
            "chamaecyparis",
            "catalpa",
        ),
        "Evergreen, resinous, aromatic, and breezy species map to lungs and airways.",
    ),
    (
        "Urology",
        ("river birch",),
        "River and water names suggest urinary and fluid-system care.",
    ),
    (
        "Dermatology",
        ("zelkova", "elm", "ulmus", "birch", "betula", "paperbark", "sycamore"),
        "Bark, surface texture, peeling, and visible skin-like layers map to dermatology.",
    ),
    (
        "Women's Health",
        ("magnolia", "tulip", "liriodendron"),
        "Flowering and bloom-centered species become supportive life-stage care.",
    ),
    (
        "Pediatrics",
        (
            "cherry",
            "plum",
            "prunus",
            "serviceberry",
            "amelanchier",
            "dogwood",
            "cornus",
            "redbud",
            "cercis",
            "silverbell",
            "halesia",
            "snowbell",
            "styrax",
        ),
        "Blossom, fruit, and sapling associations become child and adolescent care.",
    ),
    (
        "Gastroenterology",
        ("apple", "malus", "hackberry", "celtis", "coffeetree", "gymnocladus"),
        "Fruit, food, beans, and post-lunch associations map to digestive care.",
    ),
    (
        "Nutrition and Weight Management",
        ("walnut", "juglans", "chestnut", "castanea", "hazelnut", "corylus", "mulberry", "morus", "pear", "pyrus"),
        "Fruit and nut species become food, metabolism, and sustainable habit specialists.",
    ),
    (
        "Allergy and Immunology",
        ("sophora", "styphnolobium", "pagoda", "locust", "robinia", "mimosa", "albizia"),
        "Flowering, pollen, and immune-response associations map to allergy care.",
    ),
    (
        "Preventive Medicine",
        ("holly", "ilex", "maackia", "katsura", "cercidiphyllum", "hardy rubber"),
        "Hardy ornamental species become maintenance, screening, and prevention specialists.",
    ),
    (
        "Infectious Disease",
        ("amur cork", "phellodendron", "sassafras", "ailanthus", "tree of heaven"),
        "Medicinal, hardy, and invasive-survivor associations become infection specialists.",
    ),
    (
        "Nephrology",
        ("alder", "alnus", "cottonwood", "populus deltoides", "taxodium", "bald cypress", "pond cypress"),
        "Wetland and water-filtering associations map to kidney and fluid balance care.",
    ),
    (
        "ENT / Otolaryngology",
        ("lilac", "syringa", "fringetree", "chionanthus"),
        "Fragrant flowering species suggest nose, throat, sinus, and voice care.",
    ),
    (
        "Ophthalmology",
        ("empress", "paulownia", "golden rain", "koelreuteria"),
        "Large leaves, bright crowns, and light-filtering canopies map to vision care.",
    ),
    (
        "Rheumatology",
        ("eucommia", "rubber tree", "yellowwood", "cladrastis"),
        "Flexible or traditionally medicinal woods suggest connective tissue and inflammation.",
    ),
    (
        "Oncology",
        ("smoketree", "cotinus"),
        "Smoke and abnormal-growth imagery becomes a careful, serious screening specialty.",
    ),
    (
        "Sports Medicine",
        ("aspen", "populus tremuloides", "larch", "larix"),
        "Quaking, flexible, and trail-associated species map to activity and recovery.",
    ),
    (
        "Occupational Medicine",
        ("kentucky", "turkish", "persian", "american", "european", "chinese", "japanese"),
        "Place-named species become workaday, commute-aware occupational health trees.",
    ),
    (
        "Emergency Medicine",
        ("silver", "green", "black", "white"),
        "Broad color-name groups become practical rapid-access fallback clinicians.",
    ),
    (
        "Family Medicine",
        ("crepe myrtle", "lagerstroemia", "mimosa", "goldenrain"),
        "Hardy everyday ornamental trees become neighborhood primary-care generalists.",
    ),
]

FALLBACK_SPECIALTY_WEIGHTS = [
    ("Family Medicine", 18),
    ("Internal Medicine", 16),
    ("Preventive Medicine", 12),
    ("Pediatrics", 10),
    ("Geriatrics", 10),
    ("Dermatology", 8),
    ("Cardiology", 8),
    ("Pulmonology", 8),
    ("Gastroenterology", 7),
    ("Endocrinology", 7),
    ("Allergy and Immunology", 6),
    ("Psychiatry", 6),
    ("Sports Medicine", 6),
    ("Women's Health", 5),
    ("Neurology", 5),
    ("Orthopedics", 5),
    ("Nutrition and Weight Management", 5),
    ("ENT / Otolaryngology", 4),
    ("Ophthalmology", 4),
    ("Rheumatology", 4),
    ("Pain Management", 4),
    ("Sleep Medicine", 4),
    ("Infectious Disease", 3),
    ("Nephrology", 3),
    ("Urology", 3),
    ("Hematology", 3),
    ("Vascular Medicine", 3),
    ("Occupational Medicine", 3),
    ("Emergency Medicine", 3),
    ("Oncology", 2),
]

SPECIALTY_CONDITIONS = {
    "Family Medicine": ["annual physical", "cold and flu", "preventive care", "vaccinations", "minor injuries", "routine checkups", "high blood pressure screening"],
    "Internal Medicine": ["chronic disease care", "fatigue", "medication review", "high blood pressure", "high cholesterol", "diabetes follow-up", "adult wellness visits"],
    "Pediatrics": ["childhood fever", "growth concerns", "school physicals", "routine vaccinations", "seasonal allergies", "ear infections", "well-child visits"],
    "Geriatrics": ["memory concerns", "fall risk", "medication management", "mobility changes", "chronic disease care", "caregiver planning", "frailty screening"],
    "Preventive Medicine": ["annual screenings", "vaccination planning", "healthy aging", "risk reduction", "lifestyle counseling", "cancer screening reminders", "blood pressure checks"],
    "Dermatology": ["acne", "eczema", "psoriasis", "skin rash", "sun damage", "mole checks", "dry skin"],
    "Cardiology": ["high blood pressure", "chest pain", "high cholesterol", "heart palpitations", "shortness of breath", "heart disease prevention", "irregular heartbeat"],
    "Pulmonology": ["asthma", "chronic cough", "shortness of breath", "bronchitis", "COPD", "wheezing", "post-viral breathing symptoms"],
    "Gastroenterology": ["acid reflux", "IBS", "stomach pain", "constipation", "diarrhea", "bloating", "colon cancer screening"],
    "Endocrinology": ["diabetes", "thyroid disorder", "weight changes", "prediabetes", "hormone imbalance", "fatigue", "metabolic syndrome"],
    "Allergy and Immunology": ["seasonal allergies", "food allergies", "hives", "asthma triggers", "immune concerns", "sinus congestion", "eczema flares"],
    "Psychiatry": ["anxiety", "depression", "insomnia", "stress management", "burnout", "panic symptoms", "mood changes"],
    "Sports Medicine": ["sprains", "running injuries", "knee pain", "shoulder pain", "overuse injuries", "return-to-activity planning", "muscle strains"],
    "Women's Health": ["well-woman visit", "menstrual concerns", "menopause symptoms", "contraception counseling", "pelvic pain", "breast health", "pregnancy planning"],
    "Neurology": ["migraine", "memory changes", "headache", "dizziness", "numbness and tingling", "brain fog", "tremor"],
    "Rheumatology": ["joint pain", "arthritis", "autoimmune concerns", "inflammation", "morning stiffness", "lupus monitoring", "gout"],
    "Pain Management": ["chronic pain", "back pain", "neck pain", "nerve pain", "joint pain", "pain flares", "non-opioid pain planning"],
    "Sleep Medicine": ["insomnia", "sleep apnea", "snoring", "daytime sleepiness", "restless sleep", "sleep schedule problems", "fatigue"],
    "Nutrition and Weight Management": ["weight changes", "cholesterol nutrition", "prediabetes nutrition", "heart-healthy eating", "digestive nutrition", "meal planning", "metabolic health"],
    "Infectious Disease": ["recurrent infections", "fever evaluation", "travel health", "tick-borne illness concerns", "wound infection", "antibiotic questions", "immune suppression concerns"],
    "Nephrology": ["kidney disease", "high blood pressure", "protein in urine", "electrolyte imbalance", "fluid retention", "kidney stone prevention", "chronic kidney monitoring"],
    "ENT / Otolaryngology": ["sinus infection", "ear pain", "sore throat", "hearing concerns", "voice changes", "nasal congestion", "tonsil concerns"],
    "Ophthalmology": ["vision changes", "dry eyes", "eye irritation", "glaucoma screening", "cataract concerns", "red eye", "diabetic eye screening"],
    "Orthopedics": ["joint injury", "fracture follow-up", "back pain", "hip pain", "shoulder pain", "arthritis", "mobility problems"],
    "Urology": ["urinary tract infection", "urinary frequency", "kidney stones", "prostate concerns", "bladder pain", "incontinence", "pelvic discomfort"],
    "Hematology": ["anemia", "easy bruising", "blood clot history", "low iron", "abnormal blood counts", "bleeding concerns", "fatigue from anemia"],
    "Oncology": ["cancer screening", "lump evaluation", "survivorship care", "family cancer risk", "abnormal imaging follow-up", "unexplained weight loss", "screening reminders"],
    "Occupational Medicine": ["work injury", "ergonomic strain", "return-to-work visit", "commute stress", "repetitive motion pain", "workplace exposure questions", "job physicals"],
    "Emergency Medicine": ["urgent symptoms", "minor injuries", "sudden pain", "fever triage", "cuts and scrapes", "dizziness", "same-day assessment"],
    "Vascular Medicine": ["leg swelling", "varicose veins", "poor circulation", "blood clot concerns", "cold feet", "leg pain when walking", "vascular risk review"],
}

SPECIALTY_CONTEXT = {
    "Family Medicine": ("whole-person care", "everyday symptoms, prevention, and checkups", "whole-block"),
    "Internal Medicine": ("adult primary care", "complex symptoms and long-term conditions", "root-to-canopy"),
    "Pediatrics": ("child and adolescent care", "growth, fevers, school forms, and small worries", "sapling-friendly"),
    "Geriatrics": ("older-adult care", "mobility, memory, medicines, and longevity", "long-view"),
    "Preventive Medicine": ("prevention-first care", "screening, habits, risk reduction, and early warnings", "maintenance-minded"),
    "Dermatology": ("skin and surface care", "rashes, irritation, sun exposure, and texture checks", "bark-aware"),
    "Cardiology": ("heart and circulation care", "blood pressure, rhythm, and cardiovascular risk", "steady-pulse"),
    "Pulmonology": ("breathing care", "cough, asthma, airways, and recovery after respiratory illness", "breeze-assisted"),
    "Gastroenterology": ("digestive care", "reflux, bowel patterns, belly pain, and screening", "gut-calm"),
    "Endocrinology": ("metabolic care", "diabetes, thyroid questions, energy shifts, and hormones", "sap-balanced"),
    "Allergy and Immunology": ("immune and allergy care", "pollen, hives, triggers, and immune concerns", "pollen-diplomatic"),
    "Psychiatry": ("mental health care", "anxiety, depression, stress, sleep, and overwhelm", "calm-canopy"),
    "Sports Medicine": ("movement care", "sprains, recovery, overuse, and return to activity", "stretch-friendly"),
    "Women's Health": ("life-stage care", "cycle concerns, menopause, pelvic health, and prevention", "bloom-aware"),
    "Neurology": ("brain and nerve care", "migraine, memory, dizziness, and sensory symptoms", "focus-restoring"),
    "Rheumatology": ("inflammation care", "joint pain, autoimmune questions, stiffness, and flares", "flexible-branch"),
    "Pain Management": ("pain-focused care", "back pain, nerve pain, flare plans, and function", "willow-calm"),
    "Sleep Medicine": ("sleep and rest care", "insomnia, fatigue, snoring, and sleep rhythm", "quiet-hour"),
    "Nutrition and Weight Management": ("nutrition care", "metabolic health, eating patterns, and sustainable goals", "fruit-and-nut"),
    "Infectious Disease": ("infection care", "fever, recurrent infections, travel health, and antibiotic questions", "hardy-defense"),
    "Nephrology": ("kidney and fluid care", "blood pressure, kidney monitoring, and fluid balance", "water-wise"),
    "ENT / Otolaryngology": ("ear, nose, and throat care", "sinus, ear, voice, congestion, and throat concerns", "fragrant-airway"),
    "Ophthalmology": ("eye and vision care", "vision changes, irritation, dry eyes, and screenings", "light-filtering"),
    "Orthopedics": ("bone and joint care", "injuries, arthritis, posture, and mobility", "strong-limb"),
    "Urology": ("urinary care", "bladder symptoms, stones, frequency, and pelvic discomfort", "flow-focused"),
    "Hematology": ("blood health care", "anemia, bruising, clot history, and blood counts", "red-leaf"),
    "Oncology": ("cancer screening and survivorship care", "screenings, risk, lumps, and careful follow-up", "watchful-growth"),
    "Occupational Medicine": ("work and city-life care", "ergonomics, work injuries, exposure questions, and return-to-work", "commute-aware"),
    "Emergency Medicine": ("same-day urgent care", "sudden symptoms, minor injuries, and triage", "rapid-shade"),
    "Vascular Medicine": ("vessel and circulation care", "leg swelling, circulation, clot risk, and walking pain", "flow-steady"),
}

SPECIALTY_TAGLINES = {
    "Family Medicine": ["Everyday shade for everyday care.", "Whole-block checkups, no appointment desk required."],
    "Internal Medicine": ["Complex symptoms, calm roots.", "Adult care from root cause to canopy."],
    "Pediatrics": ["Small worries welcome under the lower branches.", "Sapling care with snack-break energy."],
    "Geriatrics": ["Long-view medicine from a tree that understands time.", "Slow walks, steady shade, excellent perspective."],
    "Preventive Medicine": ["Shade before symptoms become paperwork.", "Maintenance care with a very leafy calendar."],
    "Dermatology": ["Bark-level wisdom for skin-level concerns.", "Dappled-light care for sensitive surfaces."],
    "Cardiology": ["A slower block for a steadier pulse.", "Heartwood care with low-drama rhythm."],
    "Pulmonology": ["Breathe easier where the canopy does its best work.", "Airway care with breeze privileges."],
    "Gastroenterology": ["Digest the day at walking speed.", "Gentle gut care near the curb."],
    "Endocrinology": ["Seasonal balance for sap, sugar, and energy.", "Metabolic calm under a steady canopy."],
    "Allergy and Immunology": ["Pollen diplomacy starts here.", "Immune care that does not overreact to spring."],
    "Psychiatry": ["Quiet enough for thoughts to sit down.", "Mood weather welcomed without judgment."],
    "Sports Medicine": ["Recovery shade for ambitious calves.", "Movement care for walkers, runners, and errand athletes."],
    "Women's Health": ["Supportive care for every season.", "Bloom-aware care without rushing the calendar."],
    "Neurology": ["Leaf-pattern focus for busy nervous systems.", "Memory, migraine, and calm attention care."],
    "Rheumatology": ["Flexible care for stiff mornings.", "Inflammation support with branch-level patience."],
    "Pain Management": ["Function first, flare plans second, shade always.", "Calm pain care with willow logic."],
    "Sleep Medicine": ["Restorative shade for restless nights.", "Sleep rhythm support from a quiet canopy."],
    "Nutrition and Weight Management": ["Sustainable habits, fruit-and-nut common sense.", "Food care without moralizing the snacks."],
    "Infectious Disease": ["Hardy care for fevers and stubborn bugs.", "Careful infection guidance with strong urban roots."],
    "Nephrology": ["Water-wise care for kidneys and pressure.", "Fluid balance with wetland imagination."],
    "ENT / Otolaryngology": ["Sinus, throat, and voice care with fragrant shade.", "Clearer passages, quieter complaints."],
    "Ophthalmology": ["Vision care through filtered city light.", "Eye checks with excellent shade angles."],
    "Orthopedics": ["Strong-limb care for joints and bones.", "Mobility support from a structurally serious tree."],
    "Urology": ["Flow-focused care without awkward waiting-room energy.", "Bladder and stone concerns, handled calmly."],
    "Hematology": ["Blood-count care with red-leaf symbolism.", "Anemia, bruising, and clot questions under steady shade."],
    "Oncology": ["Careful screening, watchful follow-up.", "Serious care delivered with a gentle canopy."],
    "Occupational Medicine": ["Workday care for city bodies.", "Commute stress and sidewalk ergonomics, reviewed outdoors."],
    "Emergency Medicine": ["Same-day shade for sudden symptoms.", "Rapid-access curbside triage."],
    "Vascular Medicine": ["Circulation care for long walks.", "Flow, vessels, and leg symptoms with steady shade."],
}


def stable_seed(*parts: object) -> int:
    text = "|".join(str(part) for part in parts)
    digest = hashlib.sha256(f"{RANDOM_SEED}|{text}".encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "little", signed=False)


def rng_for(*parts: object) -> np.random.Generator:
    return np.random.default_rng(stable_seed(*parts))


def stable_choice(options: list[str], *parts: object) -> str:
    if not options:
        return ""
    rng = rng_for(*parts)
    return options[int(rng.integers(0, len(options)))]


def stable_weighted_choice(weighted_options: list[tuple[str, int]], *parts: object) -> str:
    choices = [item[0] for item in weighted_options]
    weights = np.array([item[1] for item in weighted_options], dtype=float)
    weights = weights / weights.sum()
    return str(rng_for(*parts).choice(choices, p=weights))


def stable_normal(mean: float, sd: float, *parts: object) -> float:
    return float(rng_for(*parts).normal(mean, sd))


def stable_uniform(*parts: object) -> float:
    return float(rng_for(*parts).random())


def normalize_text(value: object) -> str:
    if pd.isna(value):
        return ""
    return str(value).strip()


def title_text(value: object) -> str:
    text = normalize_text(value)
    return text.title() if text else ""


def normalize_category(value: object, default: str = "Unknown") -> str:
    text = normalize_text(value)
    return text if text else default


def clean_yes_no(value: object) -> bool:
    return normalize_text(value).lower() in {"yes", "true", "1", "y"}


def normalize_favorite(value: object) -> int:
    text = normalize_text(value).lower()
    if text in {"1", "true", "yes", "y", "favorite", "star"}:
        return 1
    if text in {"0", "false", "no", "n", ""}:
        return 0
    numeric = pd.to_numeric(pd.Series([value]), errors="coerce").iloc[0]
    return int(not pd.isna(numeric) and numeric > 0)


def species_key_from_values(common_name: object, scientific_name: object) -> str:
    return f"{normalize_text(common_name).lower()}|{normalize_text(scientific_name).lower()}"


def neighborhood_short(value: object) -> str:
    text = normalize_text(value)
    if not text:
        return "Neighborhood"
    return text.split("-")[0].strip()[:42]


def assign_specialty(common_name: object, scientific_name: object) -> str:
    common_text = normalize_text(common_name).lower()
    scientific_text = normalize_text(scientific_name).lower()
    text = f"{common_text} {scientific_text}"

    for specialty, keywords, _rationale in SPECIALTY_RULES:
        if any(keyword in text for keyword in keywords):
            return specialty

    return stable_weighted_choice(FALLBACK_SPECIALTY_WEIGHTS, "specialty", text)


def ensure_specialty_variety(species_specialty_map: dict[str, str], species_counts: pd.Series) -> dict[str, str]:
    if len(species_specialty_map) < len(ALL_SPECIALTIES):
        return species_specialty_map

    missing = [specialty for specialty in ALL_SPECIALTIES if specialty not in set(species_specialty_map.values())]
    if not missing:
        return species_specialty_map

    # Assign missing specialties to rare species first so the main symbolic rules still dominate the dataset.
    ordered_species = sorted(
        species_specialty_map,
        key=lambda key: (int(species_counts.get(key, 0)), stable_seed("specialty_variety", key)),
    )
    used: set[str] = set()
    for specialty in missing:
        for key in ordered_species:
            if key in used:
                continue
            species_specialty_map[key] = specialty
            used.add(key)
            break
    return species_specialty_map


def build_species_specialty_map(df: pd.DataFrame) -> dict[str, str]:
    unique_species = df[["_species_key", "common_name", "scientific_name"]].drop_duplicates("_species_key")
    specialty_map = {
        species_key: assign_specialty(common_name, scientific_name)
        for species_key, common_name, scientific_name in unique_species.itertuples(index=False, name=None)
    }
    species_counts = df["_species_key"].value_counts()
    return ensure_specialty_variety(specialty_map, species_counts)


def assign_star_doctors(df: pd.DataFrame) -> pd.Series:
    favorite_mask = df["favorite"].fillna(0).astype(int).eq(1)
    target = int(round(len(df) * STAR_DOCTOR_TARGET_SHARE))
    target = max(target, int(favorite_mask.sum()))

    star_doctor = favorite_mask.copy()
    extra_needed = target - int(star_doctor.sum())
    if extra_needed <= 0:
        return star_doctor.astype(int)

    candidate_scores = (
        df.loc[~star_doctor, "tree_id"]
        .map(lambda tree_id: stable_uniform(tree_id, "star_doctor_assignment"))
        .sort_values(kind="mergesort")
    )
    star_doctor.loc[candidate_scores.index[:extra_needed]] = True
    return star_doctor.astype(int)


def years_of_practice(tree_id: object, diameter: float) -> int:
    years = 2 + 1.35 * diameter + stable_normal(0, 1.5, tree_id, "experience")
    return int(np.clip(round(years), 1, 45))


def experience_level(years: int) -> str:
    if years >= 30:
        return "Ancient attending"
    if years >= 18:
        return "Seasoned canopy clinician"
    if years >= 8:
        return "Established neighborhood healer"
    return "Newly rooted resident"


def problem_burden_level(problem_count: int) -> str:
    if problem_count >= 5:
        return "High"
    if problem_count >= 3:
        return "Moderate"
    if problem_count >= 1:
        return "Low"
    return "None noted"


def patient_age_focus(specialty: str) -> str:
    mapping = {
        "Pediatrics": "Children, teens, and sapling-sized concerns",
        "Geriatrics": "Older adults and long-walk thinkers",
        "Women's Health": "Adolescents and adults",
        "Family Medicine": "Everyone",
        "Internal Medicine": "Adults",
        "Sports Medicine": "Walkers, runners, and stretchers",
        "Preventive Medicine": "Everyone",
        "Occupational Medicine": "Workers, commuters, and city bodies",
        "Emergency Medicine": "Anyone with a same-day concern",
    }
    return mapping.get(specialty, "Adults and curious passersby")


def tree_provider_type(row: pd.Series) -> str:
    if int(row["star_doctor"]) == 1:
        return stable_choice(
            ["Star tree doctor", "Popular canopy clinician", "Highly rated shade specialist"],
            row["tree_id"],
            "provider_type_star",
        )
    if row["tree_problem_count"] >= 5 or row["tree_health"] == "Poor":
        return "Urgent shade provider"
    if row["medical_specialty"] in {"Emergency Medicine", "Pain Management"}:
        return "Fast-access curbside clinician"
    if row["curb_location"] == "OffsetFromCurb":
        return "Quiet courtyard specialist"
    if row["stewardship_signs"] == "4orMore" and row["tree_guard"] == "Helpful":
        return "Preventive canopy specialist"
    if row["medical_specialty"] == "Geriatrics" or row["years_of_practice"] >= 28:
        return "Elder shade practitioner"
    if row["tree_guard"] == "Helpful" and row["sidewalk_condition"] == "NoDamage":
        return "Friendly curbside generalist"
    if row["stewardship_signs"] in {"3or4", "4orMore"}:
        return "Community-rooted care tree"
    return "Neighborhood care tree"


def care_rating(df: pd.DataFrame) -> pd.Series:
    health_penalty = df["tree_health"].map({"Good": 0.08, "Fair": 0.60, "Poor": 1.10}).fillna(0.35)
    sidewalk_penalty = np.where(df["sidewalk_condition"].eq("Damage"), 0.32, 0.0)
    guard_adjust = df["tree_guard"].map({"Helpful": 0.18, "Unsure": -0.06, "Harmful": -0.22}).fillna(0.0)
    stewardship_adjust = df["stewardship_signs"].map({"1or2": 0.00, "3or4": 0.14, "4orMore": 0.26}).fillna(0.0)
    star_adjust = np.where(df["star_doctor"].eq(1), 0.42, 0.0)
    problem_penalty = 0.15 * df["tree_problem_count"]
    noise = df["tree_id"].map(lambda tree_id: stable_normal(0, 0.30, tree_id, "rating_v3"))
    rating = 4.58 - health_penalty - sidewalk_penalty - problem_penalty + guard_adjust + stewardship_adjust + star_adjust + noise
    star_floor = df["tree_id"].map(lambda tree_id: 4.15 + stable_uniform(tree_id, "star_rating_floor") * 0.55)
    rating = np.where(df["star_doctor"].eq(1), np.maximum(rating, star_floor), rating)
    return np.clip(rating, 1.2, 5.0).round(1)


def appointment_wait_days(row: pd.Series) -> int:
    specialty_adjust = {
        "Dermatology": 9,
        "Neurology": 8,
        "Psychiatry": 8,
        "Cardiology": 7,
        "Gastroenterology": 7,
        "Endocrinology": 6,
        "Women's Health": 5,
        "Pulmonology": 5,
        "Ophthalmology": 5,
        "ENT / Otolaryngology": 5,
        "Rheumatology": 5,
        "Vascular Medicine": 5,
        "Geriatrics": 4,
        "Pediatrics": 3,
        "Allergy and Immunology": 3,
        "Orthopedics": 3,
        "Pain Management": 3,
        "Internal Medicine": 2,
        "Sports Medicine": 2,
        "Preventive Medicine": 1,
        "Family Medicine": 1,
        "Emergency Medicine": -1,
    }
    base = 2 + specialty_adjust.get(row["medical_specialty"], 3)
    star_relief = -4 if int(row["star_doctor"]) == 1 else 0
    urgent_relief = -3 if row["provider_type"] in {"Urgent shade provider", "Fast-access curbside clinician"} else 0
    high_rating_demand = max(0.0, float(row["care_rating"]) - 4.5) * 2.0
    noise = stable_normal(0, 2.0, row["tree_id"], "wait_days_v3")
    return int(np.clip(round(base + star_relief + urgent_relief + high_rating_demand + noise), 0, 45))


def weekend_availability(row: pd.Series) -> bool:
    probability = 0.34
    if int(row["star_doctor"]) == 1:
        probability += 0.18
    if row["provider_type"] in {"Urgent shade provider", "Community-rooted care tree", "Fast-access curbside clinician"}:
        probability += 0.09
    if row["tree_health"] == "Poor":
        probability -= 0.16
    if row["tree_problem_count"] >= 4:
        probability -= 0.12
    if row["stewardship_signs"] == "4orMore":
        probability += 0.08
    if row["tree_guard"] == "Harmful":
        probability -= 0.07
    probability = float(np.clip(probability, 0.08, 0.72))
    return bool(stable_uniform(row["tree_id"], row["medical_specialty"], "weekend_v3") < probability)


def make_clinic_name(row: pd.Series) -> str:
    suffixes = [
        "Canopy Care Stop",
        "Root Check Station",
        "Shade Practice",
        "Leafside Primary Care",
        "Neighborhood Tree Clinic",
        "Branch Office",
        "Bark Desk",
        "Open-Air Clinic",
        "Curbside Care Point",
    ]
    area = neighborhood_short(row["neighborhood"])
    suffix = stable_choice(suffixes, row["tree_id"], row["neighborhood"], "clinic_name")
    return f"{area} {suffix}"


def searchable_conditions(row: pd.Series) -> str:
    options = SPECIALTY_CONDITIONS[row["medical_specialty"]]
    count = 5 if int(row["star_doctor"]) == 1 or float(row["care_rating"]) >= 4.5 else 4
    count = min(count, len(options))
    rng = rng_for(row["tree_id"], row["medical_specialty"], "conditions")
    selected = list(rng.choice(options, size=count, replace=False))
    return ", ".join(selected)


def specialty_description(row: pd.Series) -> str:
    focus, concerns, style = SPECIALTY_CONTEXT[row["medical_specialty"]]
    common = title_text(row["common_name"]) or "This tree"
    return (
        f"{row['medical_specialty']} is assigned from the {common} species profile: "
        f"a {style} association with {concerns}."
    )


def care_philosophy(row: pd.Series) -> str:
    focus, concerns, style = SPECIALTY_CONTEXT[row["medical_specialty"]]
    health = normalize_text(row["tree_health"]).lower() or "steady"
    neighborhood = neighborhood_short(row["neighborhood"])
    common = title_text(row["common_name"]) or "tree"

    templates = [
        f"This {common} practices {focus} with a practical, {style} rhythm: listen first, shade generously, and keep {concerns} understandable.",
        f"Care here is preventive and long-term, using {health} canopy habits to make {concerns} feel less intimidating.",
        f"The approach is calm and supportive, with street-level advice for {concerns} and enough patience for a full sidewalk pause.",
        f"This practice favors clear explanations, manageable next steps, and a little humor around {concerns}.",
        f"In {neighborhood}, this tree keeps care accessible: no velvet rope, just {style} attention and steady follow-through.",
        f"The philosophy is holistic without drifting away from reality: watch the seasons, respect the data, and respond to {concerns}.",
        f"This tree treats {concerns} like a neighborhood pattern, not a personal failure, and builds care plans at walking speed.",
        f"The work is community-health focused, balancing {focus} with shade, patience, and the limits of urban soil.",
    ]

    if int(row["star_doctor"]) == 1:
        templates.extend(
            [
                f"As a star doctor, this {common} keeps the tone polished and reassuring: quick access, clear explanations, and {style} confidence.",
                f"Popular but not precious, this tree turns its strong rating into practical care for {concerns} and a smoother visit.",
                f"This star canopy has a loyal following because the advice is specific, calm, and unusually easy to remember after the walk home.",
            ]
        )
    if row["tree_problem_count"] >= 4 or row["tree_health"] == "Poor":
        templates.extend(
            [
                f"Because the chart is a little complicated, the philosophy is triage-forward: stabilize the block, then work through {concerns} one branch at a time.",
                f"This tree knows stress firsthand, so the care style is direct, kind, and realistic about what can improve this season.",
            ]
        )
    if row["medical_specialty"] in {"Pediatrics", "Family Medicine", "Geriatrics"}:
        templates.append(
            f"Family-centered care is the default here, with space for multiple generations to ask about {concerns} without feeling rushed."
        )
    if row["medical_specialty"] in {"Emergency Medicine", "Sports Medicine", "Pain Management"}:
        templates.append(
            f"The style is fast-access and function-focused: help people move through sudden symptoms, pain, or recovery without overcomplicating the visit."
        )

    return stable_choice(templates, row["tree_id"], row["medical_specialty"], row["star_doctor"], "care_philosophy")


def provider_bio(row: pd.Series) -> str:
    common = title_text(row["common_name"]) or "Neighborhood tree"
    scientific = normalize_text(row["scientific_name"])
    neighborhood = neighborhood_short(row["neighborhood"])
    focus, concerns, style = SPECIALTY_CONTEXT[row["medical_specialty"]]
    star_note = " It is a star doctor, so the profile reads as especially trusted and easy to choose." if int(row["star_doctor"]) == 1 else ""
    health_note = {
        "Good": "with a steady canopy and low-drama chart",
        "Fair": "with a few urban stories in the chart",
        "Poor": "while managing a more complicated street-side chart",
    }.get(row["tree_health"], "with a practical open-air chart")
    templates = [
        f"{common} offers {focus} in {neighborhood}, translating {style} tree logic into care for {concerns} {health_note}.{star_note}",
        f"This {common} has {int(row['years_of_practice'])} years of fictional practice and a specialty shaped by species symbolism, site condition, and neighborhood context.{star_note}",
        f"{common} ({scientific}) works like a public sidewalk clinician: rooted in place, open to everyone, and focused on {concerns}.{star_note}",
        f"In {neighborhood}, this {common} turns shade, seasonality, and a {style} temperament into an accessible {row['medical_specialty']} profile.{star_note}",
    ]
    return stable_choice(templates, row["tree_id"], row["medical_specialty"], "provider_bio")


def clinic_description(row: pd.Series) -> str:
    neighborhood = neighborhood_short(row["neighborhood"])
    address = title_text(row["tree_address"]) or "an address pending curbside spot"
    wait = int(row["next_available_visit_days"])
    access = int(row["care_accessibility_score"])
    weekend = "weekend shade is sometimes available" if bool(row["weekend_availability"]) else "weekends are reserved for tree rest"
    templates = [
        f"Located near {address} in {neighborhood}, this open-air practice has an accessibility score of {access} and a typical wait of {wait} days.",
        f"The clinic is the tree itself: curbside, public, and rooted in {neighborhood}. Current wait is about {wait} days; {weekend}.",
        f"This spot keeps care close to the block, with {row['provider_type'].lower()} energy and an access score of {access}.",
        f"Patients find this practice by walking to {address}; the waiting room is shade, sidewalk, and whatever the weather contributes.",
    ]
    if int(row["star_doctor"]) == 1:
        templates.append(
            f"This star practice is easy to notice in {neighborhood}: higher reputation, shorter wait, and a polished curbside presence."
        )
    return stable_choice(templates, row["tree_id"], row["medical_specialty"], "clinic_description")


def patient_review_summary(row: pd.Series) -> str:
    rating = float(row["care_rating"])
    focus, concerns, style = SPECIALTY_CONTEXT[row["medical_specialty"]]
    templates: list[str]
    if rating >= 4.6:
        templates = [
            f"Patients praise the {style} calm, the clear advice about {concerns}, and the shade that makes waiting feel intentional.",
            f"Reviews describe this tree as reassuring, specific, and unusually good at making {row['medical_specialty']} feel approachable.",
            f"Visitors mention strong follow-through, a polished canopy presence, and advice that still makes sense after leaving the block.",
        ]
    elif rating >= 4.0:
        templates = [
            f"Reviews are positive overall, especially for practical explanations and a grounded approach to {concerns}.",
            f"Patients like the steady shade and realistic guidance, though busy days can make the visit feel brisk.",
            f"The summary reads as dependable: useful care, calm presence, and enough personality to remember the appointment.",
        ]
    elif rating >= 3.0:
        templates = [
            f"Patients appreciate the public access and shade, but mention a more uneven chart and occasional sidewalk complications.",
            f"Reviews are mixed but fair: the care is useful, the setting is real, and the tree is doing its best with urban conditions.",
            f"People come for accessible care and leave with practical notes, even when the canopy has a complicated week.",
        ]
    else:
        templates = [
            f"Reviews note a stressed chart and limited polish, but the tree remains available for basic, open-air care.",
            f"Patients value the access, while also noticing that this provider needs extra support from the block.",
        ]
    if int(row["star_doctor"]) == 1:
        templates.append(
            f"Star reviews highlight the strong reputation, short wait, and a visit that feels more thoughtful than a sidewalk appointment has any right to be."
        )
    return stable_choice(templates, row["tree_id"], row["medical_specialty"], "review_summary")


def doctor_tagline(row: pd.Series) -> str:
    options = list(SPECIALTY_TAGLINES[row["medical_specialty"]])
    if int(row["star_doctor"]) == 1:
        options.extend(
            [
                "Star-rated shade with a loyal block following.",
                "Popular, polished, and still rooted in public care.",
            ]
        )
    if row["tree_problem_count"] >= 4:
        options.append("A complicated chart, handled one branch at a time.")
    return stable_choice(options, row["tree_id"], row["medical_specialty"], "tagline")


def primary_care_services(row: pd.Series) -> str:
    conditions = searchable_conditions(row).split(", ")
    focus, _concerns, style = SPECIALTY_CONTEXT[row["medical_specialty"]]
    options = [
        f"{focus}; {conditions[0]}; {conditions[1]}; practical follow-up",
        f"{style} consults; {conditions[0]}; {conditions[2]}; prevention planning",
        f"walk-up shade visits; {conditions[1]}; {conditions[3]}; clear next steps",
    ]
    return stable_choice(options, row["tree_id"], row["medical_specialty"], "services")


def signature_prescription(row: pd.Series) -> str:
    prescriptions = {
        "Cardiology": ["Walk slower until your pulse remembers it has manners.", "Reduce urgency by one branch per day."],
        "Pulmonology": ["Take three deep breaths and call back after the next breeze.", "Exhale twice before answering city noise."],
        "Dermatology": ["Apply shade generously to exposed plans.", "Reapply canopy every two blocks."],
        "Psychiatry": ["Stand here for four minutes; let the leaves handle the meeting.", "Compost one worry and return next season."],
        "Sleep Medicine": ["Dim the sidewalk, lower the noise, and let the canopy close the tabs.", "One quiet block before bed, no scrolling under the branches."],
        "Pain Management": ["Function first; heroics can wait until after shade.", "Treat the flare like weather: plan, pace, and hydrate."],
        "Nutrition and Weight Management": ["No moral judgment for snacks; just add a walk and some shade.", "Balance the plate, then balance the afternoon."],
        "Emergency Medicine": ["If it is sudden, start with shade and then escalate responsibly.", "Same-day concern, same-curb calm."],
        "Pediatrics": ["After-school shade before dramatic snack negotiations.", "Small worries may park under the lowest branch."],
        "Geriatrics": ["Take the long view with a short walk.", "Pause often; wisdom has a slower appointment schedule."],
        "Family Medicine": ["Two minutes of shade, repeat when urban life gets loud.", "Routine care is allowed to be ordinary."],
    }
    fallback = [
        "Two minutes of shade, repeat when urban life gets loud.",
        "Sit nearby until the sidewalk stops arguing.",
        "Hydrate early; catastrophize late, if at all.",
        "Bring the symptom, leave with a plan and one leaf of perspective.",
    ]
    options = prescriptions.get(row["medical_specialty"], fallback)
    return stable_choice(options, row["tree_id"], row["medical_specialty"], "prescription")


def office_vibe(row: pd.Series) -> str:
    focus, _concerns, style = SPECIALTY_CONTEXT[row["medical_specialty"]]
    options = [
        f"{style.capitalize()}, practical, and open-air",
        f"Quietly focused on {focus}",
        "Low-key sidewalk wisdom",
        "Sun-dappled, public, and more organized than expected",
    ]
    if row["tree_guard"] == "Helpful" and row["sidewalk_condition"] == "NoDamage":
        options.append("Orderly, welcoming, excellent curb manners")
    if row["tree_guard"] == "Harmful":
        options.append("A little intense, but committed to growth")
    if row["sidewalk_condition"] == "Damage":
        options.append("Textured floor plan; bring flexible expectations")
    if int(row["star_doctor"]) == 1:
        options.append("Popular enough to seem booked, calm enough not to show it")
    return stable_choice(options, row["tree_id"], row["medical_specialty"], "office_vibe")


def waiting_room_feature(row: pd.Series) -> str:
    focus, _concerns, style = SPECIALTY_CONTEXT[row["medical_specialty"]]
    options = [
        "Complimentary shade",
        "Seasonal leaf reading material",
        "Curbside standing room",
        "Breeze-based check-in system",
        f"{style.capitalize()} waiting patch",
        f"{focus.capitalize()} conversation bench",
        "No forms, only photosynthesis",
    ]
    if row["tree_diameter"] >= 20:
        options.extend(["Extra-wide shade coverage", "Big-canopy calm zone"])
    if row["sidewalk_condition"] == "Damage":
        options.append("Uneven-floor mindfulness practice")
    if int(row["star_doctor"]) == 1:
        options.append("Star-doctor fan mail tucked into the leaf pile")
    return stable_choice(options, row["tree_id"], row["medical_specialty"], "waiting_room")


def leaf_paperwork_level(row: pd.Series) -> str:
    if row["tree_problem_count"] >= 5:
        options = [
            "High: many leaves in the inbox",
            "High: paperwork has entered the canopy",
            "High: the chart rustles when opened",
        ]
    elif int(row["star_doctor"]) == 1:
        options = [
            "Celebrity backlog",
            "Fan mail mixed with leaf litter",
            "Popular enough to need a rake assistant",
        ]
    elif row["stewardship_signs"] == "4orMore":
        options = [
            "Well-raked",
            "Tidy chart, tidy mulch",
            "Beautifully maintained leaf inbox",
        ]
    elif row["tree_problem_count"] == 0:
        options = [
            "Almost suspiciously tidy",
            "No loose leaves on file",
            "Paperwork so clean it feels staged",
        ]
    else:
        options = [
            "Manageable leaf pile",
            "Normal seasonal paperwork drift",
            "Slightly rustly but functional",
            "Enough paperwork to prove it is real",
        ]
    return stable_choice(options, row["tree_id"], "leafwork")


def branch_office_status(row: pd.Series) -> str:
    if row["branch_problem_count"] >= 2:
        options = [
            "Branch office under review",
            "Upper branch desk temporarily complicated",
            "Branch network requesting a maintenance meeting",
        ]
    elif row["branch_problem_count"] == 1:
        options = [
            "Branch office open with notes",
            "Branch office operating with a small caveat",
            "One branch desk needs a follow-up memo",
        ]
    elif row["tree_diameter"] >= 18:
        options = [
            "Multiple branch offices available",
            "Expanded canopy practice",
            "Several branch desks taking walk-ins",
        ]
    else:
        options = [
            "Main trunk office",
            "Single-trunk practice",
            "Compact branch schedule",
            "Primary trunk desk",
        ]
    return stable_choice(options, row["tree_id"], "branch_status")


def condition_summary(row: pd.Series) -> str:
    health = normalize_text(row["tree_health"])
    if health == "Good":
        options = [
            "Good canopy condition",
            "Healthy-looking canopy, minimal drama",
            "Good condition and accepting compliments",
        ]
    elif health == "Fair":
        options = [
            "Fair canopy condition",
            "Fair condition with a few urban stories",
            "Stable but asking for a little patience",
        ]
    else:
        options = [
            "Poor canopy condition",
            "Stressed canopy, generous spirit",
            "Needs support, still offering shade",
        ]

    if row["tree_problem_count"] >= 4:
        options.append(f"{health or 'Unknown'} condition with a complicated chart")
    if row["tree_guard"] == "Helpful":
        options.append(f"{health or 'Unknown'} condition with good support nearby")
    if row["sidewalk_condition"] == "Damage":
        options.append(f"{health or 'Unknown'} condition with sidewalk tension")
    if int(row["star_doctor"]) == 1:
        options.append(f"{health or 'Unknown'} condition with unusually loyal reviews")
    return stable_choice(options, row["tree_id"], health, "condition_summary")


def prepare_input(df: pd.DataFrame) -> pd.DataFrame:
    working = df.copy()
    defaults = {
        "tree_id": range(1, len(working) + 1),
        "tree_diameter": 0,
        "curb_location": "Unknown",
        "tree_health": "Unknown",
        "scientific_name": "",
        "common_name": "",
        "stewardship_signs": "None",
        "tree_guard": "Unsure",
        "sidewalk_condition": "Unknown",
        "tree_address": "",
        "postcode": "",
        "city": "",
        "neighborhood": "",
        "state": "",
        "latitude": np.nan,
        "longitude": np.nan,
        "favorite": 0,
    }
    for column, default in defaults.items():
        if column not in working.columns:
            working[column] = default
    for column in PROBLEM_COLUMNS:
        if column not in working.columns:
            working[column] = "No"

    fallback_ids = pd.Series(range(1, len(working) + 1), index=working.index)
    working["tree_id"] = pd.to_numeric(working["tree_id"], errors="coerce").fillna(fallback_ids).astype(int)
    working["tree_diameter"] = pd.to_numeric(working["tree_diameter"], errors="coerce").fillna(0).clip(lower=0)
    working["latitude"] = pd.to_numeric(working["latitude"], errors="coerce")
    working["longitude"] = pd.to_numeric(working["longitude"], errors="coerce")
    working["favorite"] = working["favorite"].map(normalize_favorite).astype(int)

    for column in [
        "curb_location",
        "tree_health",
        "scientific_name",
        "common_name",
        "stewardship_signs",
        "tree_guard",
        "sidewalk_condition",
        "tree_address",
        "postcode",
        "city",
        "neighborhood",
        "state",
    ]:
        working[column] = working[column].map(normalize_category)

    working["_species_key"] = [
        species_key_from_values(common, scientific)
        for common, scientific in zip(working["common_name"], working["scientific_name"])
    ]
    return working


def build_provider_dataset(df: pd.DataFrame) -> pd.DataFrame:
    working = prepare_input(df)

    problem_flags = pd.DataFrame(
        {column: working[column].map(clean_yes_no) for column in PROBLEM_COLUMNS},
        index=working.index,
    )
    working["tree_problem_count"] = problem_flags.sum(axis=1).astype(int)
    working["root_problem_count"] = problem_flags[[column for column in PROBLEM_COLUMNS if column.startswith("root_")]].sum(axis=1).astype(int)
    working["trunk_problem_count"] = problem_flags[[column for column in PROBLEM_COLUMNS if column.startswith("trunk_")]].sum(axis=1).astype(int)
    working["branch_problem_count"] = problem_flags[[column for column in PROBLEM_COLUMNS if column.startswith("branch_")]].sum(axis=1).astype(int)

    species_specialty_map = build_species_specialty_map(working)
    working["medical_specialty"] = working["_species_key"].map(species_specialty_map)
    working["years_of_practice"] = [
        years_of_practice(tree_id, diameter)
        for tree_id, diameter in zip(working["tree_id"], working["tree_diameter"])
    ]
    working["years_at_current_spot"] = np.clip(
        (
            working["years_of_practice"]
            * np.clip(
                0.62
                + working["stewardship_signs"].map({"1or2": 0.00, "3or4": 0.08, "4orMore": 0.16}).fillna(0.0)
                - np.where(working["sidewalk_condition"].eq("Damage"), 0.08, 0.0)
                + working["tree_id"].map(lambda tree_id: stable_normal(0, 0.06, tree_id, "current_spot")),
                0.25,
                0.98,
            )
        ).round(),
        1,
        working["years_of_practice"],
    ).astype(int)

    working["star_doctor"] = assign_star_doctors(working)
    working["care_rating"] = care_rating(working)
    working["provider_type"] = working.apply(tree_provider_type, axis=1)
    working["care_accessibility_score"] = np.clip(
        100
        - 9 * working["tree_problem_count"]
        - np.where(working["sidewalk_condition"].eq("Damage"), 18, 0)
        - np.where(working["curb_location"].eq("OffsetFromCurb"), 4, 0)
        + np.where(working["tree_guard"].eq("Helpful"), 6, 0)
        + np.where(working["star_doctor"].eq(1), 5, 0),
        25,
        100,
    ).round(0).astype(int)

    working["shade_side_manner_score"] = np.clip(
        working["care_rating"]
        + working["stewardship_signs"].map({"1or2": 0.00, "3or4": 0.15, "4orMore": 0.25}).fillna(0.0)
        + np.where(working["tree_guard"].eq("Helpful"), 0.12, -0.04)
        + np.where(working["star_doctor"].eq(1), 0.14, 0.0)
        + working["tree_id"].map(lambda tree_id: stable_normal(0, 0.12, tree_id, "shade_side")),
        1.0,
        5.0,
    ).round(1)

    review_count = (
        4
        + working["years_of_practice"] * 1.7
        + working["tree_diameter"] * 1.15
        + np.where(working["star_doctor"].eq(1), 95, 0)
        + working["tree_id"].map(lambda tree_id: stable_normal(0, 8, tree_id, "review_count_v3"))
    )
    working["review_count"] = np.clip(review_count.round(), 1, 600).astype(int)
    working["next_available_visit_days"] = working.apply(appointment_wait_days, axis=1)
    working["weekend_availability"] = working.apply(weekend_availability, axis=1)
    working["searchable_conditions"] = working.apply(searchable_conditions, axis=1)

    output = pd.DataFrame(
        {
            "provider_id": working["tree_id"].astype(int),
            "species_common": working["common_name"].map(title_text).replace("Unknown", "Unknown Species"),
            "species_scientific": working["scientific_name"].map(normalize_text).replace("Unknown", ""),
            "medical_specialty": working["medical_specialty"],
            "specialty_description": working.apply(specialty_description, axis=1),
            "searchable_conditions": working["searchable_conditions"],
            "provider_type": working["provider_type"],
            "tree_experience_level": working["years_of_practice"].map(experience_level),
            "years_of_practice": working["years_of_practice"],
            "years_at_current_spot": working["years_at_current_spot"],
            "care_rating": working["care_rating"],
            "review_count": working["review_count"],
            "star_doctor": working["star_doctor"],
            "popularity_badge": np.where(working["star_doctor"].eq(1), "Star doctor", "Neighborhood regular"),
            "next_available_visit_days": working["next_available_visit_days"],
            "weekend_availability": working["weekend_availability"],
            "storm_response_readiness": np.where(
                working["provider_type"].isin(["Urgent shade provider", "Elder shade practitioner", "Fast-access curbside clinician"]),
                "High",
                np.where(working["tree_problem_count"].ge(4), "Medium", "Standard"),
            ),
            "care_accessibility_score": working["care_accessibility_score"],
            "shade_side_manner_score": working["shade_side_manner_score"],
            "care_philosophy": working.apply(care_philosophy, axis=1),
            "provider_bio": working.apply(provider_bio, axis=1),
            "clinic_description": working.apply(clinic_description, axis=1),
            "patient_review_summary": working.apply(patient_review_summary, axis=1),
            "care_audience": working["medical_specialty"].map(patient_age_focus),
            "primary_care_services": working.apply(primary_care_services, axis=1),
            "signature_prescription": working.apply(signature_prescription, axis=1),
            "office_vibe": working.apply(office_vibe, axis=1),
            "waiting_room_feature": working.apply(waiting_room_feature, axis=1),
            "leaf_paperwork_level": working.apply(leaf_paperwork_level, axis=1),
            "branch_office_status": working.apply(branch_office_status, axis=1),
            "clinic_name": working.apply(make_clinic_name, axis=1),
            "clinic_address": working["tree_address"].map(title_text).replace("", "Address Pending"),
            "clinic_zipcode": working["postcode"].astype(str).str.replace(r"\.0$", "", regex=True).str.zfill(5),
            "clinic_city": working["city"].map(normalize_text),
            "clinic_neighborhood": working["neighborhood"].map(normalize_text),
            "clinic_state": working["state"].map(normalize_text),
            "clinic_latitude": working["latitude"],
            "clinic_longitude": working["longitude"],
        }
    )

    return output.drop(columns=[column for column in REMOVED_OUTPUT_COLUMNS if column in output.columns])


def validate_provider_dataset(provider_df: pd.DataFrame) -> None:
    new_columns = [
        "care_philosophy",
        "provider_bio",
        "clinic_description",
        "patient_review_summary",
        "specialty_description",
        "searchable_conditions",
    ]
    star_share = provider_df["star_doctor"].mean()
    missing_removed = [column for column in REMOVED_OUTPUT_COLUMNS if column in provider_df.columns]
    null_counts = provider_df[new_columns].isna().sum()

    print("\nValidation checks:")
    print(f"- Star doctors: {provider_df['star_doctor'].sum():,} ({star_share:.2%})")
    print(f"- Unique specialties: {provider_df['medical_specialty'].nunique():,}")
    print(f"- Removed columns still present: {missing_removed if missing_removed else 'none'}")
    print("- Nulls in new descriptive/search columns:")
    print(null_counts.to_string())
    print("\nSample generated profiles:")
    sample_columns = [
        "provider_id",
        "species_common",
        "medical_specialty",
        "star_doctor",
        "care_rating",
        "next_available_visit_days",
        "searchable_conditions",
    ]
    print(provider_df[sample_columns].sample(min(5, len(provider_df)), random_state=RANDOM_SEED).to_string(index=False))


def main() -> None:
    df = pd.read_csv(INPUT_CSV)
    provider_df = build_provider_dataset(df)
    provider_df.to_csv(OUTPUT_CSV, index=False)

    print(f"Read {INPUT_CSV}: {df.shape[0]:,} rows x {df.shape[1]:,} columns")
    print(f"Wrote {OUTPUT_CSV}: {provider_df.shape[0]:,} rows x {provider_df.shape[1]:,} columns")
    print("\nSpecialty counts:")
    print(provider_df["medical_specialty"].value_counts().to_string())
    print("\nCare rating summary:")
    print(provider_df["care_rating"].describe().to_string())
    print(f"\nShare of care ratings >= 4.0: {(provider_df['care_rating'] >= 4.0).mean():.1%}")
    validate_provider_dataset(provider_df)


if __name__ == "__main__":
    main()
