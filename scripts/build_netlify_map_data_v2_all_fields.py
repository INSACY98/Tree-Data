from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = PROJECT_ROOT / "data" / "processed" / "primary_tree_care_providers2.csv"
DEFAULT_OUTPUT = PROJECT_ROOT / "site_v2" / "assets" / "trees_map_all_fields.json"

INTEGER_COLUMNS = {
    "provider_id",
    "years_of_practice",
    "years_at_current_spot",
    "review_count",
    "star_doctor",
    "next_available_visit_days",
    "care_accessibility_score",
    "clinic_zipcode",
}

FLOAT_COLUMNS = {
    "care_rating",
    "shade_side_manner_score",
    "clinic_latitude",
    "clinic_longitude",
}

BOOLEAN_COLUMNS = {
    "weekend_availability",
}


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
        if series.empty:
            continue
        summary[column] = {
            "min": round(float(series.min()), 4),
            "mean": round(float(series.mean()), 4),
            "median": round(float(series.median()), 4),
            "max": round(float(series.max()), 4),
        }
    return summary


def value_counts(series: pd.Series) -> dict[str, int]:
    return {str(key): int(value) for key, value in series.value_counts(dropna=False).items()}


def build_dictionary(series: pd.Series) -> tuple[list[str], dict[str, int]]:
    values = sorted(series.map(clean_text).unique())
    index = {value: position for position, value in enumerate(values)}
    return values, index


def build_payload(input_csv: Path) -> dict[str, Any]:
    df = pd.read_csv(input_csv)
    fields = list(df.columns)
    row_count = len(df)

    text_columns = [
        column
        for column in fields
        if column not in INTEGER_COLUMNS and column not in FLOAT_COLUMNS and column not in BOOLEAN_COLUMNS
    ]
    numeric_columns = [column for column in fields if column in INTEGER_COLUMNS or column in FLOAT_COLUMNS]
    boolean_columns = [column for column in fields if column in BOOLEAN_COLUMNS]

    for column in text_columns:
        df[column] = df[column].map(clean_text)

    for column in boolean_columns:
        df[column] = df[column].map(as_bool_int).astype(int)

    for column in numeric_columns:
        df[column] = pd.to_numeric(df[column], errors="coerce")

    for column in INTEGER_COLUMNS:
        if column in df.columns:
            df[column] = df[column].fillna(0).round().astype(int)

    for column in FLOAT_COLUMNS:
        if column in df.columns:
            df[column] = df[column].round(6)

    dictionaries: dict[str, list[str]] = {}
    dictionary_index: dict[str, dict[str, int]] = {}
    for column in text_columns:
        dictionaries[column], dictionary_index[column] = build_dictionary(df[column])

    rows: list[list[Any]] = []
    for row in df.itertuples(index=False, name=None):
        encoded_row: list[Any] = []
        for column, value in zip(fields, row):
            if column in text_columns:
                encoded_row.append(dictionary_index[column][value])
            elif pd.isna(value):
                encoded_row.append(None)
            elif column in FLOAT_COLUMNS:
                encoded_row.append(round(float(value), 6))
            else:
                encoded_row.append(int(value) if column in INTEGER_COLUMNS or column in BOOLEAN_COLUMNS else value)
        rows.append(encoded_row)

    metadata = {
        "source_file": str(input_csv.relative_to(PROJECT_ROOT)),
        "row_count": int(row_count),
        "fields": fields,
        "text_fields": text_columns,
        "numeric_fields": numeric_columns,
        "boolean_fields": boolean_columns,
        "coordinate_fields": ["clinic_latitude", "clinic_longitude"],
        "specialties": dictionaries.get("medical_specialty", []),
        "provider_types": dictionaries.get("provider_type", []),
        "cities": dictionaries.get("clinic_city", []),
        "star_count": int(df["star_doctor"].sum()) if "star_doctor" in df.columns else 0,
        "numeric_summary": numeric_summary(df, numeric_columns),
    }
    if "medical_specialty" in df.columns:
        metadata["specialty_counts"] = value_counts(df["medical_specialty"])

    return {
        "version": 2,
        "metadata": metadata,
        "dicts": dictionaries,
        "rows": rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Export a site_v2-style compact JSON with all provider fields.")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT, help="Input provider CSV.")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="Output compact JSON path.")
    args = parser.parse_args()

    payload = build_payload(args.input)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(
        f"Wrote {args.output} with {payload['metadata']['row_count']:,} rows "
        f"({args.output.stat().st_size / 1024 / 1024:.2f} MB)"
    )


if __name__ == "__main__":
    main()
