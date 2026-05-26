from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = PROJECT_ROOT / "data" / "processed" / "primary_tree_care_providers2.csv"
DEFAULT_OUTPUT = PROJECT_ROOT / "site_v2" / "assets" / "trees_map.json"

TEXT_COLUMNS = [
    "species_common",
    "species_scientific",
    "medical_specialty",
    "provider_type",
    "popularity_badge",
    "searchable_conditions",
    "care_philosophy",
    "patient_review_summary",
    "primary_care_services",
    "signature_prescription",
    "waiting_room_feature",
    "leaf_paperwork_level",
    "branch_office_status",
    "clinic_name",
    "clinic_address",
    "clinic_zipcode",
    "clinic_city",
    "clinic_neighborhood",
]

NUMERIC_COLUMNS = [
    "provider_id",
    "years_of_practice",
    "care_rating",
    "review_count",
    "star_doctor",
    "next_available_visit_days",
    "weekend_availability",
    "care_accessibility_score",
    "shade_side_manner_score",
    "clinic_latitude",
    "clinic_longitude",
]

INPUT_COLUMNS = TEXT_COLUMNS + NUMERIC_COLUMNS

ROW_FIELDS = [
    "lng",
    "lat",
    "provider_id",
    "species_common",
    "species_scientific",
    "medical_specialty",
    "provider_type",
    "years_of_practice",
    "care_rating",
    "review_count",
    "star_doctor",
    "popularity_badge",
    "next_available_visit_days",
    "weekend_availability",
    "care_accessibility_score",
    "shade_side_manner_score",
    "searchable_conditions",
    "care_philosophy",
    "patient_review_summary",
    "primary_care_services",
    "signature_prescription",
    "waiting_room_feature",
    "leaf_paperwork_level",
    "branch_office_status",
    "clinic_name",
    "clinic_address",
    "clinic_zipcode",
    "clinic_city",
    "clinic_neighborhood",
]


def clean_text(value: object) -> str:
    if pd.isna(value):
        return "Unknown"
    text = str(value).strip()
    return text if text else "Unknown"


def as_bool_int(value: object) -> int:
    if isinstance(value, bool):
        return int(value)
    return int(str(value).strip().lower() in {"1", "true", "yes", "y"})


def numeric_summary(df: pd.DataFrame, columns: list[str]) -> dict[str, dict[str, float]]:
    summary: dict[str, dict[str, float]] = {}
    for column in columns:
        series = pd.to_numeric(df[column], errors="coerce").dropna()
        summary[column] = {
            "min": round(float(series.min()), 2),
            "mean": round(float(series.mean()), 2),
            "median": round(float(series.median()), 2),
            "max": round(float(series.max()), 2),
        }
    return summary


def value_counts(series: pd.Series) -> dict[str, int]:
    return {str(key): int(value) for key, value in series.value_counts(dropna=False).items()}


def build_dictionary(series: pd.Series) -> tuple[list[str], dict[str, int]]:
    values = sorted(series.map(clean_text).unique())
    index = {value: position for position, value in enumerate(values)}
    return values, index


def build_payload(input_csv: Path) -> dict[str, Any]:
    available_columns = pd.read_csv(input_csv, nrows=0).columns
    missing = [column for column in INPUT_COLUMNS if column not in available_columns]
    if missing:
        raise ValueError(f"Input CSV is missing required map columns: {missing}")

    df = pd.read_csv(input_csv, usecols=INPUT_COLUMNS)
    row_count = len(df)
    df["clinic_latitude"] = pd.to_numeric(df["clinic_latitude"], errors="coerce")
    df["clinic_longitude"] = pd.to_numeric(df["clinic_longitude"], errors="coerce")
    df = df.dropna(subset=["clinic_latitude", "clinic_longitude"]).copy()

    for column in TEXT_COLUMNS:
        df[column] = df[column].map(clean_text)

    for column in ["star_doctor", "weekend_availability"]:
        df[column] = df[column].map(as_bool_int)

    for column in [
        "provider_id",
        "years_of_practice",
        "review_count",
        "next_available_visit_days",
        "care_accessibility_score",
    ]:
        df[column] = pd.to_numeric(df[column], errors="coerce").fillna(0).round().astype(int)

    for column in ["care_rating", "shade_side_manner_score"]:
        df[column] = pd.to_numeric(df[column], errors="coerce").fillna(0).round(1)

    dictionaries: dict[str, list[str]] = {}
    dictionary_index: dict[str, dict[str, int]] = {}
    for column in TEXT_COLUMNS:
        dictionaries[column], dictionary_index[column] = build_dictionary(df[column])

    rows: list[list[Any]] = []
    for row in df.itertuples(index=False):
        values = row._asdict()
        rows.append(
            [
                round(float(values["clinic_longitude"]), 6),
                round(float(values["clinic_latitude"]), 6),
                int(values["provider_id"]),
                dictionary_index["species_common"][values["species_common"]],
                dictionary_index["species_scientific"][values["species_scientific"]],
                dictionary_index["medical_specialty"][values["medical_specialty"]],
                dictionary_index["provider_type"][values["provider_type"]],
                int(values["years_of_practice"]),
                round(float(values["care_rating"]), 1),
                int(values["review_count"]),
                int(values["star_doctor"]),
                dictionary_index["popularity_badge"][values["popularity_badge"]],
                int(values["next_available_visit_days"]),
                int(values["weekend_availability"]),
                int(values["care_accessibility_score"]),
                round(float(values["shade_side_manner_score"]), 1),
                dictionary_index["searchable_conditions"][values["searchable_conditions"]],
                dictionary_index["care_philosophy"][values["care_philosophy"]],
                dictionary_index["patient_review_summary"][values["patient_review_summary"]],
                dictionary_index["primary_care_services"][values["primary_care_services"]],
                dictionary_index["signature_prescription"][values["signature_prescription"]],
                dictionary_index["waiting_room_feature"][values["waiting_room_feature"]],
                dictionary_index["leaf_paperwork_level"][values["leaf_paperwork_level"]],
                dictionary_index["branch_office_status"][values["branch_office_status"]],
                dictionary_index["clinic_name"][values["clinic_name"]],
                dictionary_index["clinic_address"][values["clinic_address"]],
                dictionary_index["clinic_zipcode"][values["clinic_zipcode"]],
                dictionary_index["clinic_city"][values["clinic_city"]],
                dictionary_index["clinic_neighborhood"][values["clinic_neighborhood"]],
            ]
        )

    return {
        "version": 2,
        "metadata": {
            "source_file": str(input_csv.relative_to(PROJECT_ROOT)),
            "row_count": int(row_count),
            "mapped_count": int(len(df)),
            "missing_coordinate_count": int(row_count - len(df)),
            "fields": ROW_FIELDS,
            "specialties": dictionaries["medical_specialty"],
            "provider_types": dictionaries["provider_type"],
            "cities": dictionaries["clinic_city"],
            "star_count": int(df["star_doctor"].sum()),
            "rating_counts": value_counts(pd.cut(df["care_rating"], bins=[0, 3.5, 4.0, 4.5, 5.0], include_lowest=True)),
            "numeric_summary": numeric_summary(
                df,
                [
                    "care_rating",
                    "years_of_practice",
                    "care_accessibility_score",
                    "shade_side_manner_score",
                    "next_available_visit_days",
                ],
            ),
        },
        "dicts": dictionaries,
        "rows": rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Export compact map JSON for the second Netlify site.")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT, help="Input provider CSV.")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="Output compact JSON path.")
    args = parser.parse_args()

    payload = build_payload(args.input)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(
        f"Wrote {args.output} with {payload['metadata']['mapped_count']:,} trees "
        f"({args.output.stat().st_size / 1024 / 1024:.2f} MB)"
    )


if __name__ == "__main__":
    main()
