from __future__ import annotations

import hashlib
from pathlib import Path

import numpy as np
import pandas as pd


RANDOM_SEED = 20260523
PROJECT_ROOT = Path(__file__).resolve().parents[1]
INPUT_CSV = PROJECT_ROOT / "data" / "processed" / "trees_with_favorites_live.csv"
OUTPUT_CSV = PROJECT_ROOT / "data" / "processed" / "primary_tree_care_providers.csv"


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

FALLBACK_SPECIALTY_WEIGHTS = [
    ("Family Medicine", 18),
    ("Internal Medicine", 16),
    ("Preventive Medicine", 11),
    ("Pediatrics", 8),
    ("Geriatrics", 8),
    ("Dermatology", 7),
    ("Cardiology", 7),
    ("Pulmonology", 6),
    ("Gastroenterology", 6),
    ("Endocrinology", 5),
    ("Psychiatry", 5),
    ("Sports Medicine", 4),
    ("Allergy/Immunology", 4),
    ("Women's Health", 4),
]


def stable_seed(*parts: object) -> int:
    text = "|".join(str(part) for part in parts)
    digest = hashlib.sha256(f"{RANDOM_SEED}|{text}".encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "little", signed=False)


def rng_for(*parts: object) -> np.random.Generator:
    return np.random.default_rng(stable_seed(*parts))


def stable_choice(options: list[str], *parts: object) -> str:
    rng = rng_for(*parts)
    return options[int(rng.integers(0, len(options)))]


def stable_weighted_choice(weighted_options: list[tuple[str, int]], *parts: object) -> str:
    choices = [item[0] for item in weighted_options]
    weights = np.array([item[1] for item in weighted_options], dtype=float)
    weights = weights / weights.sum()
    rng = rng_for(*parts)
    return str(rng.choice(choices, p=weights))


def stable_normal(mean: float, sd: float, *parts: object) -> float:
    return float(rng_for(*parts).normal(mean, sd))


def normalize_text(value: object) -> str:
    if pd.isna(value):
        return ""
    return str(value).strip()


def title_text(value: object) -> str:
    text = normalize_text(value)
    return text.title() if text else ""


def species_key(row: pd.Series) -> str:
    common = normalize_text(row.get("common_name")).lower()
    scientific = normalize_text(row.get("scientific_name")).lower()
    return f"{common}|{scientific}"


def assign_specialty(common_name: str, scientific_name: str) -> str:
    common_text = normalize_text(common_name).lower()
    scientific_text = normalize_text(scientific_name).lower()
    text = f"{common_text} {scientific_text}"

    if "ginkgo" in text:
        return "Neurology"
    if any(term in text for term in ["hawthorn", "crataegus"]):
        return "Cardiology"
    if any(term in text for term in ["linden", "tilia"]):
        return "Psychiatry"
    if any(term in text for term in ["oak", "quercus", "beech", "fagus", "redwood", "sequoia", "metasequoia"]):
        return "Geriatrics"
    if (
        any(term in text for term in ["honeylocust", "gleditsia", "planetree"])
        or scientific_text.startswith("platanus")
    ):
        return "Internal Medicine"
    if any(term in text for term in ["maple", "acer", "blackgum", "nyssa"]):
        return "Endocrinology"
    if any(term in text for term in ["willow", "salix", "ash", "fraxinus", "hornbeam", "carpinus", "ostrya"]):
        return "Sports Medicine"
    if any(term in text for term in ["pine", "spruce", "fir", "juniper", "cedar", "arborvitae", "cypress", "pinus", "picea", "abies", "juniperus", "thuja", "chamaecyparis", "sweetgum", "liquidambar", "catalpa"]):
        return "Pulmonology"
    if any(term in text for term in ["zelkova", "elm", "ulmus", "birch", "betula", "sycamore", "paperbark"]):
        return "Dermatology"
    if any(term in text for term in ["pear", "pyrus", "magnolia", "tulip"]):
        return "Women's Health"
    if any(term in text for term in ["cherry", "plum", "prunus", "serviceberry", "amelanchier", "dogwood", "cornus"]):
        return "Pediatrics"
    if any(term in text for term in ["apple", "malus", "hackberry", "celtis", "mulberry", "morus", "chestnut", "castanea", "coffeetree", "gymnocladus"]):
        return "Gastroenterology"
    if any(term in text for term in ["sophora", "styphnolobium", "pagoda", "locust", "robinia"]):
        return "Allergy/Immunology"
    if any(term in text for term in ["holly", "ilex", "snowbell", "styrax", "maackia", "katsura", "cercidiphyllum"]):
        return "Preventive Medicine"
    if any(term in text for term in ["ailanthus", "tree of heaven"]):
        return "Family Medicine"

    return stable_weighted_choice(FALLBACK_SPECIALTY_WEIGHTS, "specialty", text)


def build_species_specialty_map(df: pd.DataFrame) -> dict[str, str]:
    unique_species = df[["common_name", "scientific_name"]].drop_duplicates()
    return {
        species_key(row): assign_specialty(row["common_name"], row["scientific_name"])
        for _, row in unique_species.iterrows()
    }


def neighborhood_short(value: object) -> str:
    text = normalize_text(value)
    if not text:
        return "Neighborhood"
    return text.split("-")[0].strip()[:42]


def make_clinic_name(row: pd.Series) -> str:
    suffixes = [
        "Canopy Care Stop",
        "Root Check Station",
        "Shade Practice",
        "Leafside Primary Care",
        "Neighborhood Tree Clinic",
        "Branch Office",
        "Bark Desk",
    ]
    area = neighborhood_short(row["neighborhood"])
    suffix = stable_choice(suffixes, row["tree_id"], row["neighborhood"], "clinic_name")
    return f"{area} {suffix}"


def years_of_practice(row: pd.Series) -> int:
    years = 2 + 1.35 * row["tree_diameter"] + stable_normal(0, 1.5, row["tree_id"], "experience")
    return int(np.clip(round(years), 1, 45))


def experience_level(years: int) -> str:
    if years >= 30:
        return "Ancient attending"
    if years >= 18:
        return "Seasoned canopy clinician"
    if years >= 8:
        return "Established neighborhood healer"
    return "Newly rooted resident"


def tree_provider_type(row: pd.Series) -> str:
    if int(row["star_doctor"]) == 1:
        return "Star tree doctor"
    if row["tree_problem_count"] >= 5 or row["tree_health"] == "Poor":
        return "Urgent shade provider"
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


def patient_age_focus(specialty: str) -> str:
    mapping = {
        "Pediatrics": "Saplings and younger visitors",
        "Geriatrics": "Older adults and long-walk thinkers",
        "Women's Health": "Adolescents and adults",
        "Family Medicine": "Everyone",
        "Internal Medicine": "Adults",
        "Sports Medicine": "Walkers, runners, and stretchers",
        "Preventive Medicine": "Everyone",
    }
    return mapping.get(specialty, "Adults and curious passersby")


def problem_burden_level(problem_count: int) -> str:
    if problem_count >= 5:
        return "High"
    if problem_count >= 3:
        return "Moderate"
    if problem_count >= 1:
        return "Low"
    return "None noted"


def care_philosophy(row: pd.Series) -> str:
    if int(row["star_doctor"]) == 1:
        return stable_choice(
            [
                "Popular open-air care with a loyal neighborhood following",
                "High-demand shade with a surprisingly calm fan base",
                "Beloved block medicine, mostly delivered by standing there beautifully",
            ],
            row["tree_id"],
            "star_philosophy",
        )
    if row["provider_type"] == "Urgent shade provider":
        return stable_choice(
            [
                "Triage first, photosynthesis later",
                "Quick shade, quick assessment, minimal leaf paperwork",
                "Problem-focused care for sidewalks having a complicated week",
            ],
            row["tree_id"],
            row["medical_specialty"],
            "urgent_philosophy",
        )

    specialty_philosophies = {
        "Allergy/Immunology": [
            "Negotiate gently with pollen instead of declaring war on spring",
            "Teach the immune system that not every blossom is an emergency",
            "Seasonal care with boundaries, tissues, and diplomatic shade",
        ],
        "Cardiology": [
            "Slow the block down until the heart finds a walkable rhythm",
            "Treat urgency as a modifiable risk factor",
            "Support circulation with shade, strolling, and less honking",
        ],
        "Dermatology": [
            "Protect the surface while respecting the bark underneath",
            "Offer shade as the oldest skincare technology in the city",
            "Keep the sun useful, not personal",
        ],
        "Endocrinology": [
            "Balance sap, sugar, and the emotional weather of the afternoon",
            "Treat energy crashes with steady shade and fewer dramatic snacks",
            "Respect cycles, seasons, and whatever maple is doing",
        ],
        "Family Medicine": [
            "Care for the whole block without making anyone feel late",
            "Solve ordinary problems with shade, patience, and practical calm",
            "Keep everyday care close enough to pass on a walk",
        ],
        "Gastroenterology": [
            "Let digestion move at walking speed",
            "Honor gut feelings, but ask them to sit in shade first",
            "Use gentle pacing for complicated lunches and complicated feelings",
        ],
        "Geriatrics": [
            "Practice the medicine of long memory and unhurried shade",
            "Make room for slower walks and better stories",
            "Treat longevity as a neighborhood resource",
        ],
        "Internal Medicine": [
            "Review the whole canopy before treating one leaf",
            "Look for root causes without blaming the branches",
            "Manage complexity with stillness, shade, and a suspiciously thorough trunk",
        ],
        "Neurology": [
            "Quiet the nervous system one rustle at a time",
            "Make focus feel less like a meeting and more like a breeze",
            "Treat overstimulation with patterned leaves and fewer notifications",
        ],
        "Pediatrics": [
            "Let small worries sit in small shade before they become large worries",
            "Care for saplings, snack breaks, and after-school weather systems",
            "Keep growth spurts grounded and lightly supervised",
        ],
        "Preventive Medicine": [
            "Offer shade before symptoms become paperwork",
            "Catch small sidewalk problems before they learn public speaking",
            "Practice maintenance medicine with hydration and fewer emergencies",
        ],
        "Psychiatry": [
            "Stand still together until the nervous system remembers the breeze",
            "Compost rumination into something quieter",
            "Treat mood weather with patience, rustling, and no push notifications",
        ],
        "Pulmonology": [
            "Make breathing feel less like a task and more like weather",
            "Use the breeze as a co-provider",
            "Support lungs with clean pauses and shade-filtered air",
        ],
        "Sports Medicine": [
            "Protect knees from ambition and calves from bad decisions",
            "Treat recovery as part of the route, not a failure of speed",
            "Offer cool-down care for runners, walkers, and heroic errand-doers",
        ],
        "Women's Health": [
            "Support cycles, seasons, and bodies that keep their own calendars",
            "Make room for bloom, rest, and no-rush listening",
            "Practice supportive care without asking the patient to justify the weather",
        ],
    }
    if row["medical_specialty"] in specialty_philosophies:
        return stable_choice(
            specialty_philosophies[row["medical_specialty"]],
            row["tree_id"],
            row["medical_specialty"],
            "care_philosophy_specialty",
        )
    if row["tree_guard"] == "Helpful" and row["stewardship_signs"] in {"3or4", "4orMore"}:
        return stable_choice(
            [
                "Community-supported care with excellent root boundaries",
                "Neighborhood medicine held together by stewardship and shade",
                "A curbside practice with help, boundaries, and surprisingly good follow-through",
            ],
            row["tree_id"],
            "community_philosophy",
        )
    return stable_choice(
        [
            "Practical curbside care, delivered without a clipboard",
            "Everyday shade care for urban systems under pressure",
            "Quiet primary care with bark-level patience",
        ],
        row["tree_id"],
        "fallback_philosophy",
    )


def primary_care_services(row: pd.Series) -> str:
    specialty_services = {
        "Allergy/Immunology": [
            "pollen diplomacy; sneeze-season strategy; immune-system pep talks",
            "allergen boundary setting; springtime resilience coaching; gentle decongestion shade",
            "histamine calming sessions; bloom exposure planning; low-drama pollen interpretation",
        ],
        "Cardiology": [
            "heartwood checks; circulation strolls; pulse-slowing shade",
            "blood-pressure bench breaks; rhythm-of-the-block monitoring; calm-route planning",
            "vascular walk consults; stress pruning; slow-breath canopy care",
        ],
        "Dermatology": [
            "bark inspection; skin barrier counseling; sun-filtered shade",
            "shade-as-SPF coaching; texture checks; irritation-free sidewalk pacing",
            "canopy cover assessments; sensitive-skin strolls; rough-patch reassurance",
        ],
        "Endocrinology": [
            "sap balance review; sugar-season counseling; steady-energy shade",
            "metabolism pacing; maple-syrup restraint counseling; afternoon-crash prevention",
            "hormone-weather tracking; energy-cycle checkups; glucose-friendly walking pauses",
        ],
        "Family Medicine": [
            "whole-block checkups; everyday shade; general reassurance",
            "multi-generation curbside care; common-worry triage; practical shade prescriptions",
            "routine wellness pauses; neighborhood continuity; everybody-gets-a-branch care",
        ],
        "Gastroenterology": [
            "digestive walks; apple-adjacent advice; gentle gut pauses",
            "stomach-settling shade; fiber-forward pep talks; post-lunch stroll planning",
            "gut-feeling interpretation; slow-snack recovery; low-acid sidewalk counsel",
        ],
        "Geriatrics": [
            "longevity consults; slow-walk support; memory-of-the-block care",
            "fall-pace checkups; bench-adjacent counseling; long-view medicine",
            "wisdom rounds; balance-friendly shade; continuity care for patient walkers",
        ],
        "Internal Medicine": [
            "general adult care; chronic-condition shade; root-cause listening",
            "multi-symptom sorting; calm diagnostics; practical branch-by-branch planning",
            "longitudinal shade care; everyday complexity management; root-to-canopy review",
        ],
        "Neurology": [
            "memory walks; focus breaks; quiet nervous-system resets",
            "migraine-friendly shade; attention restoration; gentle sensory filtering",
            "brain-fog clearing; quiet-route consults; leaf-pattern meditation",
        ],
        "Pediatrics": [
            "sapling checkups; after-school shade; small-worry triage",
            "playground recovery; backpack-weight sympathy; tiny patient reassurance",
            "growth-spurt shade; snack-break coordination; recess-adjacent care",
        ],
        "Preventive Medicine": [
            "screening reminders; hydration nudges; shade before symptoms",
            "risk-factor pruning; early-warning leaf checks; sustainable habit planning",
            "annual wellness shade; sidewalk safety counseling; before-it-becomes-a-thing care",
        ],
        "Psychiatry": [
            "calming canopy sessions; quiet reflection; mood-weather tracking",
            "anxiety unbranching; stillness practice; nervous-system shade",
            "rumination composting; soft-focus sessions; emotionally available rustling",
        ],
        "Pulmonology": [
            "deep-breath coaching; cleaner-air pauses; breeze-assisted checkups",
            "lung-friendly walking breaks; inhale-exhale timing; shade-filtered recovery",
            "respiratory reset visits; pollen-aware breathing plans; fresh-air triage",
        ],
        "Sports Medicine": [
            "stretch-stop consults; ankle-friendly shade; recovery benches",
            "runner cool-downs; calf-negotiation visits; low-impact victory laps",
            "stride checks; hydration scolding; post-errand recovery protocols",
        ],
        "Women's Health": [
            "seasonal-cycle care; bloom-aware checkups; supportive shade",
            "life-stage listening; hormonal-weather notes; calm reproductive health pauses",
            "wellness check-ins; cycle-sensitive shade; no-rush support under blossoms",
        ],
    }
    options = specialty_services.get(row["medical_specialty"], ["shade; listening; suspiciously good stillness"])
    return stable_choice(options, row["tree_id"], row["medical_specialty"], "services")


def signature_prescription(row: pd.Series) -> str:
    options_by_specialty = {
        "Allergy/Immunology": [
            "Avoid arguing with pollen before breakfast.",
            "One shaded sneeze break, repeat through peak bloom.",
            "Carry tissues and lower your expectations of spring.",
        ],
        "Cardiology": [
            "Walk slower until your pulse remembers it has manners.",
            "Sit under the canopy until the heartwood sets the rhythm.",
            "Reduce urgency by one branch per day.",
        ],
        "Endocrinology": [
            "Stabilize the afternoon with shade before snacks.",
            "Do not let maple season make all decisions.",
            "Check sap levels emotionally, not literally.",
        ],
        "Gastroenterology": [
            "Take the scenic route after lunch and blame digestion.",
            "Prescribe one gentle walk, no competitive chewing.",
            "Let the gut feeling speak, but give it shade first.",
        ],
        "Neurology": [
            "For brain fog: watch leaves move until thoughts form a line.",
            "Reduce input; increase rustling.",
            "Take one quiet block and avoid fluorescent opinions.",
        ],
        "Pediatrics": [
            "After-school shade before dramatic snack negotiations.",
            "Growth spurts require snacks, water, and one excellent stick.",
            "Small worries may be parked under the lowest branch.",
        ],
        "Preventive Medicine": [
            "Apply shade before symptoms become a calendar event.",
            "Hydrate early; catastrophize late, if at all.",
            "Schedule maintenance before the sidewalk files a complaint.",
        ],
        "Pulmonology": [
            "Take 3 deep breaths and call back after the next breeze.",
            "One slow inhale under the canopy, repeated as needed.",
            "Exhale twice before answering city noise.",
        ],
        "Psychiatry": [
            "Stand here for 4 minutes; let the leaves handle the meeting.",
            "A quiet pause, no scrolling, refill weekly.",
            "Compost one worry and return next season.",
        ],
        "Sports Medicine": [
            "Stretch calves at curbside; hydrate before making heroic decisions.",
            "Walk one block slower than usual and pretend it was intentional.",
            "Cool down in shade; do not sprint for unnecessary trains.",
        ],
        "Dermatology": [
            "Apply shade generously to exposed plans.",
            "Avoid harsh noon sun; consult bark for boundaries.",
            "Reapply canopy every two blocks.",
        ],
        "Geriatrics": [
            "Return annually for perspective and respectable shade.",
            "Take the long view with a short walk.",
            "Pause often; wisdom has a slower appointment schedule.",
        ],
        "Internal Medicine": [
            "Investigate the root cause before blaming the branches.",
            "Daily shade, moderate water, and fewer rushed conclusions.",
            "Review the whole canopy before treating one leaf.",
        ],
        "Women's Health": [
            "Honor the season you are in, even if the calendar is rude.",
            "Bloom on your own schedule; hydrate meanwhile.",
            "Take supportive shade without explaining why.",
        ],
    }
    options = options_by_specialty.get(
        row["medical_specialty"],
        [
            "Two minutes of shade, repeat when urban life gets loud.",
            "Sit nearby until the sidewalk stops arguing.",
        ],
    )
    return stable_choice(options, row["tree_id"], row["medical_specialty"], "prescription")


def office_vibe(row: pd.Series) -> str:
    specialty_vibes = {
        "Psychiatry": ["soft rustling, low judgment, excellent pauses", "quiet enough for thoughts to sit down"],
        "Pulmonology": ["airy, breezy, professionally oxygen-adjacent", "fresh-air forward with minimal indoor energy"],
        "Dermatology": ["shade-balanced, texture-aware, suspicious of noon", "sun-smart with bark-level boundaries"],
        "Sports Medicine": ["stretch-friendly, hydration-forward, ready for cool-downs", "runner-approved but bench-curious"],
        "Pediatrics": ["after-school friendly, snack-tolerant, low branch energy", "gentle, playful, leaf-litter optional"],
        "Geriatrics": ["slow-paced, perspective-rich, bench compatible", "old-school calm with excellent shade memory"],
        "Cardiology": ["unhurried, pulse-aware, quietly steady", "rhythm-conscious with low-drama wind chimes"],
        "Endocrinology": ["steady-energy, sap-balanced, no sugar judgment", "metabolically calm with seasonal awareness"],
        "Gastroenterology": ["post-lunch friendly, gentle, not too spicy", "digestive-walk adjacent with soft shade"],
        "Allergy/Immunology": ["pollen-aware, tissue-friendly, cautiously blooming", "immune-curious with springtime boundaries"],
        "Women's Health": ["supportive, bloom-aware, no-rush listening", "cycle-sensitive with generous shade"],
        "Preventive Medicine": ["organized, early, and lightly smug about hydration", "maintenance-minded with a tidy canopy"],
        "Internal Medicine": ["practical, thorough, root-cause oriented", "generalist calm with diagnostic shade"],
        "Family Medicine": ["neighborly, flexible, everybody welcome", "block-friendly with multi-generation shade"],
    }
    specialty_options = specialty_vibes.get(row["medical_specialty"], [])
    if specialty_options and stable_normal(0, 1, row["tree_id"], "specialty_vibe_gate") > -0.35:
        return stable_choice(specialty_options, row["tree_id"], row["medical_specialty"], "office_vibe_specialty").capitalize()
    if row["tree_guard"] == "Helpful" and row["sidewalk_condition"] == "NoDamage":
        return "Orderly, welcoming, excellent curb manners"
    if row["tree_guard"] == "Harmful":
        return "A little intense, but committed to growth"
    if row["sidewalk_condition"] == "Damage":
        return "Textured floor plan; bring flexible expectations"
    if row["stewardship_signs"] == "4orMore":
        return "Very loved, slightly overbooked"
    return "Low-key sidewalk wisdom"


def waiting_room_feature(row: pd.Series) -> str:
    options_by_specialty = {
        "Allergy/Immunology": ["Pollen forecast board", "Tissue-friendly breeze zone", "Low-histamine shade"],
        "Cardiology": ["Slow-pulse bench", "Heartwood listening corner", "No-rush walking loop"],
        "Dermatology": ["SPF-by-canopy seating", "Dappled-light waiting area", "Bark texture gallery"],
        "Endocrinology": ["Steady-energy shade patch", "Sap-balance check-in stump", "Low-crash afternoon corner"],
        "Gastroenterology": ["Post-lunch pacing lane", "Gentle digestion bench", "Fiber-friendly leaf pile"],
        "Geriatrics": ["Long-view bench", "Memory-of-the-block plaque", "Extra-patient shade"],
        "Internal Medicine": ["Root-cause intake nook", "General symptoms sorting branch", "Whole-canopy chart board"],
        "Neurology": ["Quiet focus canopy", "Migraine-soft shade", "Leaf-pattern meditation spot"],
        "Pediatrics": ["Sapling-height shade", "Tiny acorn check-in desk", "After-school snack shadow"],
        "Preventive Medicine": ["Hydration reminder sign", "Early-warning leaf display", "Wellness walk starting line"],
        "Psychiatry": ["No-scroll stillness zone", "Rumination compost bin", "Feelings-friendly rustle corner"],
        "Pulmonology": ["Deep-breath breeze lane", "Fresh-air intake window", "Exhale-friendly canopy"],
        "Sports Medicine": ["Stretching curb", "Cool-down shade lane", "Hydration scolding station"],
        "Women's Health": ["Bloom-aware seating", "Supportive shade circle", "No-rush listening branch"],
        "Family Medicine": ["Whole-block check-in bench", "Everybody-fits shade patch", "Practical reassurance desk"],
    }
    options = list(options_by_specialty.get(row["medical_specialty"], []))
    options.extend(
        [
            "Complimentary shade",
            "Seasonal leaf reading material",
            "Curbside standing room",
            "Breeze-based check-in system",
            "Sun-dappled waiting area",
            "A very patient trunk",
            "No forms, only photosynthesis",
        ]
    )
    if row["tree_diameter"] >= 20:
        options.extend(["Extra-wide shade coverage", "Big-canopy calm zone"])
    if row["sidewalk_condition"] == "Damage":
        options.append("Uneven-floor mindfulness practice")
    return stable_choice(options, row["tree_id"], "waiting_room")


def leaf_paperwork_level(row: pd.Series) -> str:
    if row["tree_problem_count"] >= 5:
        return stable_choice(
            [
                "High: many leaves in the inbox",
                "High: inbox currently photosynthesizing stress",
                "High: paperwork has entered the canopy",
            ],
            row["tree_id"],
            "leafwork_high",
        )
    if int(row["star_doctor"]) == 1:
        return stable_choice(
            [
                "Celebrity backlog",
                "Fan mail mixed with leaf litter",
                "Popular enough to need a rake assistant",
            ],
            row["tree_id"],
            "leafwork_star",
        )
    if row["stewardship_signs"] == "4orMore":
        return stable_choice(
            [
                "Well-raked",
                "Tidy chart, tidy mulch",
                "Beautifully maintained leaf inbox",
            ],
            row["tree_id"],
            "leafwork_tidy",
        )
    if row["tree_problem_count"] == 0:
        return stable_choice(
            [
                "Almost suspiciously tidy",
                "No loose leaves on file",
                "Paperwork so clean it feels staged",
            ],
            row["tree_id"],
            "leafwork_none",
        )
    return stable_choice(
        [
            "Manageable leaf pile",
            "A few forms under the mulch",
            "Normal seasonal paperwork drift",
            "Leaf inbox under control",
            "Slightly rustly but functional",
            "Enough paperwork to prove it is real",
        ],
        row["tree_id"],
        "leafwork_manageable",
    )


def weekend_availability(row: pd.Series) -> bool:
    probability = 0.58
    if int(row["star_doctor"]) == 1:
        probability += 0.16
    if row["provider_type"] in {"Urgent shade provider", "Community-rooted care tree"}:
        probability += 0.10
    if row["tree_health"] == "Poor":
        probability -= 0.20
    if row["tree_problem_count"] >= 4:
        probability -= 0.14
    if row["stewardship_signs"] == "4orMore":
        probability += 0.08
    if row["tree_guard"] == "Harmful":
        probability -= 0.07
    probability = float(np.clip(probability, 0.15, 0.88))
    return bool(rng_for(row["tree_id"], row["medical_specialty"], "weekend_v2").random() < probability)


def branch_office_status(row: pd.Series) -> str:
    if row["branch_problem_count"] >= 2:
        return stable_choice(
            [
                "Branch office under review",
                "Upper branch desk temporarily complicated",
                "Branch network requesting a maintenance meeting",
            ],
            row["tree_id"],
            "branch_under_review",
        )
    if row["branch_problem_count"] == 1:
        return stable_choice(
            [
                "Branch office open with notes",
                "Branch office operating with a small caveat",
                "One branch desk needs a follow-up memo",
            ],
            row["tree_id"],
            "branch_notes",
        )
    if row["tree_diameter"] >= 18:
        return stable_choice(
            [
                "Multiple branch offices available",
                "Expanded canopy practice",
                "Several branch desks taking walk-ins",
            ],
            row["tree_id"],
            "branch_multi",
        )
    return stable_choice(
        [
            "Main trunk office",
            "Single-trunk practice",
            "Compact branch schedule",
            "Primary trunk desk",
        ],
        row["tree_id"],
        "branch_main",
    )


def condition_summary(row: pd.Series) -> str:
    health = normalize_text(row["tree_health"])
    if health == "Good":
        options = [
            "Good canopy condition",
            "Good condition with confident leaf posture",
            "Healthy-looking canopy, minimal drama",
            "Good condition and accepting compliments",
        ]
    elif health == "Fair":
        options = [
            "Fair canopy condition",
            "Fair condition with a few urban stories",
            "Stable but asking for a little patience",
            "Fair condition, still showing up for the block",
        ]
    else:
        options = [
            "Poor canopy condition",
            "Poor condition but still holding office hours",
            "Stressed canopy, generous spirit",
            "Needs support, still offering shade",
        ]

    if row["tree_problem_count"] >= 4:
        options.append(f"{health} condition with a complicated chart")
    if row["tree_guard"] == "Helpful":
        options.append(f"{health} condition with good support nearby")
    if row["sidewalk_condition"] == "Damage":
        options.append(f"{health} condition with sidewalk tension")

    return stable_choice(options, row["tree_id"], health, "condition_summary")


def care_rating(df: pd.DataFrame) -> pd.Series:
    health_penalty = df["tree_health"].map({"Good": 0.10, "Fair": 0.70, "Poor": 1.25}).fillna(0.35)
    sidewalk_penalty = np.where(df["sidewalk_condition"].eq("Damage"), 0.35, 0.0)
    guard_adjust = df["tree_guard"].map({"Helpful": 0.18, "Unsure": -0.08, "Harmful": -0.24}).fillna(0.0)
    stewardship_adjust = df["stewardship_signs"].map({"1or2": 0.00, "3or4": 0.14, "4orMore": 0.26}).fillna(0.0)
    favorite_adjust = np.where(df["favorite"].eq(1), 0.35, 0.0)
    problem_penalty = 0.17 * df["tree_problem_count"]
    noise = df["tree_id"].map(lambda tree_id: stable_normal(0, 0.32, tree_id, "rating_v2"))
    rating = 4.55 - health_penalty - sidewalk_penalty - problem_penalty + guard_adjust + stewardship_adjust + favorite_adjust + noise
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
        "Geriatrics": 4,
        "Pediatrics": 3,
        "Allergy/Immunology": 3,
        "Internal Medicine": 2,
        "Sports Medicine": 2,
        "Preventive Medicine": 1,
        "Family Medicine": 1,
    }
    base = 1 + specialty_adjust.get(row["medical_specialty"], 3)
    popularity = 6 if int(row["star_doctor"]) == 1 else max(0, row["care_rating"] - 4.0) * 3
    condition_relief = -2 if row["provider_type"] == "Urgent shade provider" else 0
    noise = stable_normal(0, 2.0, row["tree_id"], "wait_days_v2")
    return int(np.clip(round(base + popularity + condition_relief + noise), 0, 45))


def build_provider_dataset(df: pd.DataFrame) -> pd.DataFrame:
    working = df.copy()

    problem_flags = working[PROBLEM_COLUMNS].astype(str).apply(lambda col: col.str.strip().str.lower().eq("yes"))
    working["tree_problem_count"] = problem_flags.sum(axis=1).astype(int)
    working["root_problem_count"] = problem_flags[[col for col in PROBLEM_COLUMNS if col.startswith("root_")]].sum(axis=1).astype(int)
    working["trunk_problem_count"] = problem_flags[[col for col in PROBLEM_COLUMNS if col.startswith("trunk_")]].sum(axis=1).astype(int)
    working["branch_problem_count"] = problem_flags[[col for col in PROBLEM_COLUMNS if col.startswith("branch_")]].sum(axis=1).astype(int)

    species_specialty_map = build_species_specialty_map(working)
    working["medical_specialty"] = working.apply(lambda row: species_specialty_map[species_key(row)], axis=1)
    working["years_of_practice"] = working.apply(years_of_practice, axis=1)
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

    working["star_doctor"] = working["favorite"].astype(int)
    working["care_rating"] = care_rating(working)
    working["provider_type"] = working.apply(tree_provider_type, axis=1)
    working["care_accessibility_score"] = np.clip(
        100
        - 9 * working["tree_problem_count"]
        - np.where(working["sidewalk_condition"].eq("Damage"), 18, 0)
        - np.where(working["curb_location"].eq("OffsetFromCurb"), 4, 0)
        + np.where(working["tree_guard"].eq("Helpful"), 6, 0),
        25,
        100,
    ).round(0).astype(int)

    working["shade_side_manner_score"] = np.clip(
        working["care_rating"]
        + working["stewardship_signs"].map({"1or2": 0.00, "3or4": 0.15, "4orMore": 0.25}).fillna(0.0)
        + np.where(working["tree_guard"].eq("Helpful"), 0.12, -0.04)
        + working["tree_id"].map(lambda tree_id: stable_normal(0, 0.12, tree_id, "shade_side")),
        1.0,
        5.0,
    ).round(1)

    working["root_cause_analysis_score"] = np.clip(
        working["care_rating"]
        + np.where(working["years_of_practice"] >= 15, 0.15, 0.0)
        - 0.08 * working["root_problem_count"]
        + working["tree_id"].map(lambda tree_id: stable_normal(0, 0.10, tree_id, "root_cause")),
        1.0,
        5.0,
    ).round(1)

    working["follow_up_watering_score"] = np.clip(
        working["care_rating"]
        + np.where(working["tree_guard"].eq("Helpful"), 0.14, -0.04)
        + np.where(working["sidewalk_condition"].eq("NoDamage"), 0.10, -0.10)
        + working["tree_id"].map(lambda tree_id: stable_normal(0, 0.11, tree_id, "watering")),
        1.0,
        5.0,
    ).round(1)

    review_count = (
        3
        + working["years_of_practice"] * 1.7
        + working["tree_diameter"] * 1.2
        + np.where(working["star_doctor"].eq(1), 85, 0)
        + working["tree_id"].map(lambda tree_id: stable_normal(0, 8, tree_id, "review_count_v2"))
    )
    working["review_count"] = np.clip(review_count.round(), 1, 500).astype(int)
    working["next_available_visit_days"] = working.apply(appointment_wait_days, axis=1)

    output = pd.DataFrame(
        {
            "provider_id": working["tree_id"].astype(int),
            "species_common": working["common_name"].map(title_text),
            "species_scientific": working["scientific_name"].map(normalize_text),
            "medical_specialty": working["medical_specialty"],
            "provider_type": working["provider_type"],
            "tree_experience_level": working["years_of_practice"].map(experience_level),
            "years_of_practice": working["years_of_practice"],
            "years_at_current_spot": working["years_at_current_spot"],
            "care_rating": working["care_rating"],
            "review_count": working["review_count"],
            "star_doctor": working["star_doctor"],
            "popularity_badge": np.where(working["star_doctor"].eq(1), "Star doctor", "Neighborhood regular"),
            "next_available_visit_days": working["next_available_visit_days"],
            "weekend_availability": working.apply(weekend_availability, axis=1),
            "storm_response_readiness": np.where(
                working["provider_type"].isin(["Urgent shade provider", "Elder shade practitioner"]),
                "High",
                np.where(working["tree_problem_count"].ge(4), "Medium", "Standard"),
            ),
            "care_accessibility_score": working["care_accessibility_score"],
            "shade_side_manner_score": working["shade_side_manner_score"],
            "root_cause_analysis_score": working["root_cause_analysis_score"],
            "follow_up_watering_score": working["follow_up_watering_score"],
            "care_philosophy": working.apply(care_philosophy, axis=1),
            "care_audience": working["medical_specialty"].map(patient_age_focus),
            "primary_care_services": working.apply(primary_care_services, axis=1),
            "signature_prescription": working.apply(signature_prescription, axis=1),
            "office_vibe": working.apply(office_vibe, axis=1),
            "waiting_room_feature": working.apply(waiting_room_feature, axis=1),
            "leaf_paperwork_level": working.apply(leaf_paperwork_level, axis=1),
            "branch_office_status": working.apply(branch_office_status, axis=1),
            "condition_summary": working.apply(condition_summary, axis=1),
            "problem_burden_level": working["tree_problem_count"].map(problem_burden_level),
            "tree_problem_count": working["tree_problem_count"],
            "root_problem_count": working["root_problem_count"],
            "trunk_problem_count": working["trunk_problem_count"],
            "branch_problem_count": working["branch_problem_count"],
            "clinic_name": working.apply(make_clinic_name, axis=1),
            "clinic_address": working["tree_address"].map(title_text).replace("", "Address Pending"),
            "clinic_zipcode": working["postcode"].astype(str).str.zfill(5),
            "clinic_city": working["city"].map(normalize_text),
            "clinic_neighborhood": working["neighborhood"].map(normalize_text),
            "clinic_state": working["state"].map(normalize_text),
            "clinic_latitude": working["latitude"],
            "clinic_longitude": working["longitude"],
        }
    )

    return output


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


if __name__ == "__main__":
    main()
