from __future__ import annotations

import argparse
import csv
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


EXPECTED_COLUMNS = {
    "LCLid",
    "stdorToU",
    "DateTime",
}

KWH_COLUMN_CANDIDATES = (
    "KWH/hh (per half hour)",
    "KWH/hh (per half hour) ",
)


def log(message: str) -> None:
    print(f"[gridflex-lcl] {message}", flush=True)


def repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Process LCL smart-meter half-hour data into GridFlex grid-stress profiles."
    )
    parser.add_argument("--input", required=True, help="Path to raw LCL .txt or .csv input file.")
    parser.add_argument(
        "--output-dir",
        default="data/processed",
        help="Directory for processed CSV outputs. Defaults to data/processed.",
    )
    return parser.parse_args()


def resolve_path(path_value: str) -> Path:
    path = Path(path_value)
    if not path.is_absolute():
        path = repo_root() / path
    return path.resolve()


def load_backend() -> tuple[str, Any]:
    try:
        import cudf  # type: ignore

        return "cudf", cudf
    except Exception as cudf_error:
        log(f"cuDF unavailable; falling back to pandas ({type(cudf_error).__name__}: {cudf_error}).")

    try:
        import pandas as pd  # type: ignore

        return "pandas", pd
    except Exception as pandas_error:
        log(
            "pandas unavailable; using standard-library fallback "
            f"({type(pandas_error).__name__}: {pandas_error})."
        )
        return "stdlib", None


def delimiter_for(input_path: Path) -> str:
    if input_path.name.lower() == "lclstdortou.txt" or input_path.suffix.lower() == ".txt":
        return "\t"
    return ","


def validate_columns(columns: list[str]) -> str:
    stripped = {column.strip(): column for column in columns}
    missing = sorted(EXPECTED_COLUMNS - set(stripped.keys()))
    if missing:
        raise ValueError(f"Input is missing expected columns: {', '.join(missing)}")

    for candidate in KWH_COLUMN_CANDIDATES:
        if candidate in columns:
            return candidate
        if candidate.strip() in stripped:
            return stripped[candidate.strip()]

    raise ValueError(
        "Input is missing expected kWh column. Expected one of: "
        + ", ".join(repr(column) for column in KWH_COLUMN_CANDIDATES)
    )


def stress_band(score: float) -> str:
    if score < 0.35:
        return "low"
    if score <= 0.70:
        return "medium"
    return "high"


def parse_datetime(value: str) -> datetime | None:
    text = value.strip()
    if not text:
        return None

    if "." in text:
        prefix, fraction = text.split(".", 1)
        if fraction.isdigit() and len(fraction) > 6:
            text = f"{prefix}.{fraction[:6]}"

    formats = (
        "%Y-%m-%d %H:%M:%S.%f",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S.%f",
        "%Y-%m-%dT%H:%M:%S",
    )
    for date_format in formats:
        try:
            return datetime.strptime(text, date_format)
        except ValueError:
            continue
    return None


def floor_to_30_minutes(value: datetime) -> datetime:
    minute = 0 if value.minute < 30 else 30
    return value.replace(minute=minute, second=0, microsecond=0)


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as output_file:
        writer = csv.DictWriter(output_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def process_with_stdlib(input_path: Path, output_dir: Path) -> dict[str, Any]:
    delimiter = delimiter_for(input_path)
    log(f"Loading raw dataset with standard-library CSV reader: {input_path}")

    rows_before = 0
    invalid_or_null_rows = 0
    duplicate_rows_removed = 0
    seen_rows: set[tuple[str, str, datetime, float]] = set()
    households: set[str] = set()
    date_min: datetime | None = None
    date_max: datetime | None = None
    aggregates: dict[datetime, dict[str, Any]] = {}

    with input_path.open("r", encoding="utf-8-sig", newline="") as input_file:
        reader = csv.DictReader(input_file, delimiter=delimiter)
        if reader.fieldnames is None:
            raise ValueError("Input file has no header row.")

        normalized_fieldnames = [field.strip() for field in reader.fieldnames]
        kwh_column = validate_columns(normalized_fieldnames)
        rename_map = dict(zip(reader.fieldnames, normalized_fieldnames))

        for raw_row in reader:
            rows_before += 1
            row = {rename_map[key]: value for key, value in raw_row.items() if key in rename_map}
            lcl_id = row.get("LCLid", "").strip()
            tariff = row.get("stdorToU", "").strip()
            parsed_datetime = parse_datetime(row.get("DateTime", ""))

            try:
                kwh_hh = float(row.get(kwh_column, ""))
            except (TypeError, ValueError):
                invalid_or_null_rows += 1
                continue

            if parsed_datetime is None:
                invalid_or_null_rows += 1
                continue

            normalized_row = (lcl_id, tariff, parsed_datetime, kwh_hh)
            if normalized_row in seen_rows:
                duplicate_rows_removed += 1
                continue
            seen_rows.add(normalized_row)

            households.add(lcl_id)
            date_min = parsed_datetime if date_min is None else min(date_min, parsed_datetime)
            date_max = parsed_datetime if date_max is None else max(date_max, parsed_datetime)

            timestamp = floor_to_30_minutes(parsed_datetime)
            bucket = aggregates.setdefault(
                timestamp,
                {"total_kwh": 0.0, "row_count": 0, "households": set()},
            )
            bucket["total_kwh"] += kwh_hh
            bucket["row_count"] += 1
            bucket["households"].add(lcl_id)

    rows_after_cleaning = rows_before - invalid_or_null_rows
    rows_after_dedup = rows_after_cleaning - duplicate_rows_removed
    if not aggregates or date_min is None or date_max is None:
        raise ValueError("No valid rows remain after cleaning; cannot build grid-stress profile.")

    log(f"Loaded {rows_before:,} raw rows.")
    log(f"Dropped {invalid_or_null_rows:,} rows with invalid/null kWh or DateTime values.")
    log(f"Removed {duplicate_rows_removed:,} duplicate rows.")
    log(f"Aggregating {rows_after_dedup:,} cleaned rows into 30-minute windows.")

    total_values = [float(bucket["total_kwh"]) for bucket in aggregates.values()]
    min_kwh = min(total_values)
    max_kwh = max(total_values)
    window_rows: list[dict[str, Any]] = []

    for timestamp in sorted(aggregates.keys()):
        bucket = aggregates[timestamp]
        total_kwh = float(bucket["total_kwh"])
        mean_kwh = total_kwh / int(bucket["row_count"])
        grid_stress_score = 0.0 if max_kwh == min_kwh else (total_kwh - min_kwh) / (max_kwh - min_kwh)
        window_rows.append(
            {
                "timestamp": timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                "total_kwh": round(total_kwh, 6),
                "mean_kwh": round(mean_kwh, 6),
                "household_count": len(bucket["households"]),
                "hour": timestamp.hour,
                "minute": timestamp.minute,
                "day_of_week": timestamp.weekday(),
                "is_weekend": 1 if timestamp.weekday() in (5, 6) else 0,
                "settlement_period": timestamp.hour * 2 + (timestamp.minute // 30) + 1,
                "grid_stress_score": round(grid_stress_score, 6),
                "stress_band": stress_band(grid_stress_score),
            }
        )

    output_dir.mkdir(parents=True, exist_ok=True)
    grid_stress_path = output_dir / "grid_stress_30min.csv"
    features_path = output_dir / "grid_stress_features.csv"
    write_csv(
        grid_stress_path,
        [
            {
                "timestamp": row["timestamp"],
                "total_kwh": row["total_kwh"],
                "mean_kwh": row["mean_kwh"],
                "household_count": row["household_count"],
                "grid_stress_score": row["grid_stress_score"],
                "stress_band": row["stress_band"],
            }
            for row in window_rows
        ],
        ["timestamp", "total_kwh", "mean_kwh", "household_count", "grid_stress_score", "stress_band"],
    )
    write_csv(
        features_path,
        window_rows,
        [
            "timestamp",
            "total_kwh",
            "mean_kwh",
            "household_count",
            "hour",
            "minute",
            "day_of_week",
            "is_weekend",
            "settlement_period",
            "grid_stress_score",
            "stress_band",
        ],
    )
    log(f"Saved 30-minute stress profile: {grid_stress_path}")
    log(f"Saved feature table: {features_path}")

    stress_counts: dict[str, int] = {"low": 0, "medium": 0, "high": 0}
    for row in window_rows:
        stress_counts[row["stress_band"]] += 1

    window_count = len(window_rows)
    stress_percentages = {
        band: round((stress_counts[band] / window_count) * 100, 2) if window_count else 0.0
        for band in ("low", "medium", "high")
    }

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "input_path": str(input_path),
        "backend": "stdlib",
        "gpu_acceleration_used": False,
        "rows_before_cleaning": rows_before,
        "rows_after_cleaning": rows_after_cleaning,
        "rows_after_deduplication": rows_after_dedup,
        "invalid_or_null_rows_dropped": invalid_or_null_rows,
        "duplicate_rows_removed": duplicate_rows_removed,
        "date_min": date_min.isoformat(),
        "date_max": date_max.isoformat(),
        "unique_households": len(households),
        "window_count_30min": window_count,
        "total_kwh_min": min_kwh,
        "total_kwh_max": max_kwh,
        "stress_band_counts": stress_counts,
        "stress_band_percentages": stress_percentages,
        "outputs": {
            "grid_stress_30min": str(grid_stress_path),
            "grid_stress_features": str(features_path),
        },
    }


def process_with_pandas(input_path: Path, output_dir: Path, pd: Any, backend_name: str) -> dict[str, Any]:
    delimiter = delimiter_for(input_path)
    log(f"Loading raw dataset with {backend_name}: {input_path}")
    raw = pd.read_csv(input_path, sep=delimiter)
    rows_before = int(len(raw))
    log(f"Loaded {rows_before:,} raw rows.")

    raw.columns = [str(column).strip() for column in raw.columns]
    kwh_column = validate_columns(list(raw.columns))
    data = raw.rename(columns={kwh_column: "kwh_hh"})

    before_kwh_clean = int(len(data))
    data["kwh_hh"] = pd.to_numeric(data["kwh_hh"], errors="coerce")
    data["DateTime"] = pd.to_datetime(data["DateTime"], errors="coerce")
    data = data.dropna(subset=["kwh_hh", "DateTime"])
    rows_after_cleaning = int(len(data))
    invalid_or_null_rows = before_kwh_clean - rows_after_cleaning
    log(f"Dropped {invalid_or_null_rows:,} rows with invalid/null kWh or DateTime values.")

    rows_before_dedup = int(len(data))
    data = data.drop_duplicates()
    duplicate_rows_removed = rows_before_dedup - int(len(data))
    rows_after_dedup = int(len(data))
    log(f"Removed {duplicate_rows_removed:,} duplicate rows.")

    if data.empty:
        raise ValueError("No valid rows remain after cleaning; cannot build grid-stress profile.")

    unique_households = int(data["LCLid"].nunique())
    date_min = data["DateTime"].min()
    date_max = data["DateTime"].max()
    log(f"Aggregating {rows_after_dedup:,} cleaned rows into 30-minute windows.")

    data["timestamp"] = data["DateTime"].dt.floor("30min")
    aggregate = (
        data.groupby("timestamp", as_index=False)
        .agg(
            total_kwh=("kwh_hh", "sum"),
            mean_kwh=("kwh_hh", "mean"),
            household_count=("LCLid", "nunique"),
        )
        .sort_values("timestamp")
        .reset_index(drop=True)
    )

    aggregate["hour"] = aggregate["timestamp"].dt.hour.astype("int64")
    aggregate["minute"] = aggregate["timestamp"].dt.minute.astype("int64")
    aggregate["day_of_week"] = aggregate["timestamp"].dt.dayofweek.astype("int64")
    aggregate["is_weekend"] = aggregate["day_of_week"].isin([5, 6]).astype("int64")
    aggregate["settlement_period"] = (
        aggregate["hour"] * 2 + (aggregate["minute"] // 30) + 1
    ).astype("int64")

    min_kwh = float(aggregate["total_kwh"].min())
    max_kwh = float(aggregate["total_kwh"].max())
    if max_kwh == min_kwh:
        aggregate["grid_stress_score"] = 0.0
    else:
        aggregate["grid_stress_score"] = (aggregate["total_kwh"] - min_kwh) / (max_kwh - min_kwh)

    aggregate["stress_band"] = aggregate["grid_stress_score"].apply(stress_band)

    grid_stress = aggregate[["timestamp", "total_kwh", "mean_kwh", "household_count", "grid_stress_score", "stress_band"]]
    features = aggregate[
        [
            "timestamp",
            "total_kwh",
            "mean_kwh",
            "household_count",
            "hour",
            "minute",
            "day_of_week",
            "is_weekend",
            "settlement_period",
            "grid_stress_score",
            "stress_band",
        ]
    ]

    output_dir.mkdir(parents=True, exist_ok=True)
    grid_stress_path = output_dir / "grid_stress_30min.csv"
    features_path = output_dir / "grid_stress_features.csv"
    grid_stress.to_csv(grid_stress_path, index=False)
    features.to_csv(features_path, index=False)
    log(f"Saved 30-minute stress profile: {grid_stress_path}")
    log(f"Saved feature table: {features_path}")

    stress_counts = aggregate["stress_band"].value_counts().to_dict()
    window_count = int(len(aggregate))
    stress_percentages = {
        band: round((int(stress_counts.get(band, 0)) / window_count) * 100, 2) if window_count else 0.0
        for band in ("low", "medium", "high")
    }

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "input_path": str(input_path),
        "backend": backend_name,
        "gpu_acceleration_used": backend_name == "cudf",
        "rows_before_cleaning": rows_before,
        "rows_after_cleaning": rows_after_cleaning,
        "rows_after_deduplication": rows_after_dedup,
        "invalid_or_null_rows_dropped": invalid_or_null_rows,
        "duplicate_rows_removed": duplicate_rows_removed,
        "date_min": date_min.isoformat(),
        "date_max": date_max.isoformat(),
        "unique_households": unique_households,
        "window_count_30min": window_count,
        "total_kwh_min": min_kwh,
        "total_kwh_max": max_kwh,
        "stress_band_counts": {band: int(stress_counts.get(band, 0)) for band in ("low", "medium", "high")},
        "stress_band_percentages": stress_percentages,
        "outputs": {
            "grid_stress_30min": str(grid_stress_path),
            "grid_stress_features": str(features_path),
        },
    }


def write_profile_and_report(profile: dict[str, Any]) -> None:
    root = repo_root()
    outputs_dir = root / "apps" / "dgx_pipeline" / "outputs"
    outputs_dir.mkdir(parents=True, exist_ok=True)

    profile_path = outputs_dir / "data_profile.json"
    profile_path.write_text(json.dumps(profile, indent=2) + "\n", encoding="utf-8")
    log(f"Saved data profile: {profile_path}")

    percentages = profile["stress_band_percentages"]
    report = f"""# Data Processing Report

Generated: {profile['generated_at']}

## Input

- Raw dataset: `{profile['input_path']}`
- Processing backend: `{profile['backend']}`
- GPU/cuDF used: `{profile['gpu_acceleration_used']}`

## Cleaning Summary

- Rows before cleaning: `{profile['rows_before_cleaning']}`
- Rows after kWh/DateTime cleaning: `{profile['rows_after_cleaning']}`
- Rows after duplicate removal: `{profile['rows_after_deduplication']}`
- Invalid/null rows dropped: `{profile['invalid_or_null_rows_dropped']}`
- Duplicate rows removed: `{profile['duplicate_rows_removed']}`

## Dataset Summary

- Date range: `{profile['date_min']}` to `{profile['date_max']}`
- Unique households: `{profile['unique_households']}`
- Number of 30-minute windows: `{profile['window_count_30min']}`

## Stress Band Distribution

- Low: `{percentages['low']}%`
- Medium: `{percentages['medium']}%`
- High: `{percentages['high']}%`

## Outputs

- `{profile['outputs']['grid_stress_30min']}`
- `{profile['outputs']['grid_stress_features']}`
- `{profile_path}`
"""
    report_path = outputs_dir / "data_processing_report.md"
    report_path.write_text(report, encoding="utf-8")
    log(f"Saved data processing report: {report_path}")


def main() -> int:
    try:
        args = parse_args()
        input_path = resolve_path(args.input)
        output_dir = resolve_path(args.output_dir)

        if not input_path.exists():
            raise FileNotFoundError(f"Input file does not exist: {input_path}")
        if input_path.suffix.lower() not in {".txt", ".csv"}:
            raise ValueError(f"Expected .txt or .csv input, got: {input_path.suffix}")

        backend_name, backend_module = load_backend()
        log(f"Using processing backend: {backend_name}")

        if backend_name == "stdlib":
            profile = process_with_stdlib(input_path, output_dir)
        else:
            profile = process_with_pandas(input_path, output_dir, backend_module, backend_name)
        write_profile_and_report(profile)

        log("Processing complete.")
        print(json.dumps(profile, indent=2), flush=True)
        return 0
    except Exception as exc:
        print(f"[gridflex-lcl] ERROR: {exc}", file=sys.stderr, flush=True)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())