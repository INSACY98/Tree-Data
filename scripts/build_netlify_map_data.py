from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = PROJECT_ROOT / "data" / "processed" / "primary_tree_care_providers.csv"
DEFAULT_OUTPUT = PROJECT_ROOT / "site" / "assets" / "trees_map.geojson"


MAP_COLUMNS = [
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
    "root_cause_analysis_score",
    "follow_up_watering_score",
    "primary_care_services",
    "signature_prescription",
    "waiting_room_feature",
    "condition_summary",
    "problem_burden_level",
    "tree_problem_count",
    "root_problem_count",
    "trunk_problem_count",
    "branch_problem_count",
    "clinic_name",
    "clinic_address",
    "clinic_zipcode",
    "clinic_city",
    "clinic_neighborhood",
    "clinic_state",
    "clinic_latitude",
    "clinic_longitude",
]


def as_bool(value: object) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"true", "1", "yes"}


def clean_text(value: object) -> str:
    if pd.isna(value):
        return "Unknown"
    return str(value)


def clean_int(value: object, default: int = 0) -> int:
    if pd.isna(value):
        return default
    return int(value)


def clean_float(value: object, default: float = 0.0, digits: int = 2) -> float:
    if pd.isna(value):
        return default
    return round(float(value), digits)


def quality_bucket(row: pd.Series) -> str:
    burden = clean_text(row["problem_burden_level"]).lower()
    rating = clean_float(row["care_rating"])
    problems = clean_int(row["tree_problem_count"])

    if burden == "high" or rating < 3.0 or problems >= 4:
        return "Needs review"
    if burden == "medium" or rating < 3.7 or problems >= 2:
        return "Watchlist"
    if as_bool(row["star_doctor"]):
        return "Star quality"
    return "Looks stable"


def quality_notes(row: pd.Series, bucket: str) -> str:
    problems = clean_int(row["tree_problem_count"])
    burden = clean_text(row["problem_burden_level"])
    rating = clean_float(row["care_rating"], digits=1)

    if bucket == "Needs review":
        return f"Check this record closely: {problems} tree issue(s), {burden.lower()} burden, rating {rating}."
    if bucket == "Watchlist":
        return f"Good for spot-checking: {problems} issue(s), {burden.lower()} burden, rating {rating}."
    if bucket == "Star quality":
        return "Favorite tree with strong provider signals."
    return "Stable-looking record for baseline comparison."


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


def feature_from_row(row: pd.Series) -> dict[str, Any]:
    bucket = quality_bucket(row)
    properties = {
        "provider_id": clean_int(row["provider_id"]),
        "species_common": clean_text(row["species_common"]),
        "species_scientific": clean_text(row["species_scientific"]),
        "medical_specialty": clean_text(row["medical_specialty"]),
        "provider_type": clean_text(row["provider_type"]),
        "years_of_practice": clean_int(row["years_of_practice"]),
        "care_rating": clean_float(row["care_rating"], digits=1),
        "review_count": clean_int(row["review_count"]),
        "star_doctor": as_bool(row["star_doctor"]),
        "popularity_badge": clean_text(row["popularity_badge"]),
        "next_available_visit_days": clean_int(row["next_available_visit_days"]),
        "weekend_availability": as_bool(row["weekend_availability"]),
        "care_accessibility_score": clean_int(row["care_accessibility_score"]),
        "shade_side_manner_score": clean_float(row["shade_side_manner_score"], digits=1),
        "root_cause_analysis_score": clean_float(row["root_cause_analysis_score"], digits=1),
        "follow_up_watering_score": clean_float(row["follow_up_watering_score"], digits=1),
        "primary_care_services": clean_text(row["primary_care_services"]),
        "signature_prescription": clean_text(row["signature_prescription"]),
        "waiting_room_feature": clean_text(row["waiting_room_feature"]),
        "condition_summary": clean_text(row["condition_summary"]),
        "problem_burden_level": clean_text(row["problem_burden_level"]),
        "tree_problem_count": clean_int(row["tree_problem_count"]),
        "root_problem_count": clean_int(row["root_problem_count"]),
        "trunk_problem_count": clean_int(row["trunk_problem_count"]),
        "branch_problem_count": clean_int(row["branch_problem_count"]),
        "clinic_name": clean_text(row["clinic_name"]),
        "clinic_address": clean_text(row["clinic_address"]),
        "clinic_zipcode": clean_text(row["clinic_zipcode"]),
        "clinic_city": clean_text(row["clinic_city"]),
        "clinic_neighborhood": clean_text(row["clinic_neighborhood"]),
        "clinic_state": clean_text(row["clinic_state"]),
        "quality_bucket": bucket,
        "quality_notes": quality_notes(row, bucket),
    }
    return {
        "type": "Feature",
        "id": properties["provider_id"],
        "geometry": {
            "type": "Point",
            "coordinates": [
                clean_float(row["clinic_longitude"], digits=6),
                clean_float(row["clinic_latitude"], digits=6),
            ],
        },
        "properties": properties,
    }


def build_geojson(input_csv: Path) -> dict[str, Any]:
    df = pd.read_csv(input_csv, usecols=MAP_COLUMNS)
    row_count = len(df)
    df["clinic_latitude"] = pd.to_numeric(df["clinic_latitude"], errors="coerce")
    df["clinic_longitude"] = pd.to_numeric(df["clinic_longitude"], errors="coerce")
    mapped = df.dropna(subset=["clinic_latitude", "clinic_longitude"]).copy()

    features = [feature_from_row(row) for _index, row in mapped.iterrows()]
    buckets = mapped.apply(quality_bucket, axis=1)

    return {
        "type": "FeatureCollection",
        "metadata": {
            "source_file": str(input_csv.relative_to(PROJECT_ROOT)),
            "row_count": int(row_count),
            "mapped_count": int(len(mapped)),
            "missing_coordinate_count": int(row_count - len(mapped)),
            "specialties": sorted(clean_text(value) for value in mapped["medical_specialty"].dropna().unique()),
            "provider_types": sorted(clean_text(value) for value in mapped["provider_type"].dropna().unique()),
            "quality_buckets": value_counts(buckets),
            "numeric_summary": numeric_summary(
                mapped,
                [
                    "care_rating",
                    "years_of_practice",
                    "tree_problem_count",
                    "care_accessibility_score",
                    "next_available_visit_days",
                ],
            ),
        },
        "features": features,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Export lean tree provider GeoJSON for the Netlify map.")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT, help="Input provider CSV.")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="Output GeoJSON path.")
    args = parser.parse_args()

    geojson = build_geojson(args.input)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(geojson, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(
        f"Wrote {args.output} with {geojson['metadata']['mapped_count']:,} trees "
        f"({args.output.stat().st_size / 1024 / 1024:.2f} MB)"
    )


if __name__ == "__main__":
    main()
