from __future__ import annotations

import argparse
import json
import socket
import sys
from pathlib import Path
from typing import Any


def log(message: str) -> None:
    print(f"[gridflex-train] {message}", flush=True)


def repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def resolve_path(path_value: str) -> Path:
    path = Path(path_value)
    if not path.is_absolute():
        path = repo_root() / path
    return path.resolve()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Train GridFlex stress prediction models from processed 30-minute features."
    )
    parser.add_argument(
        "--input",
        required=True,
        help="Path to grid_stress_features.csv.",
    )
    parser.add_argument(
        "--output-dir",
        default="data/processed",
        help="Directory where prediction CSV output will be written.",
    )
    return parser.parse_args()


def run_cupy_evidence(outputs_dir: Path) -> dict[str, Any]:
    evidence: dict[str, Any] = {
        "hostname": socket.gethostname(),
        "python_executable": sys.executable,
        "cupy_version": None,
        "gpu_test_status": "FAIL",
        "gpu_array_size": 1_000_000,
        "gpu_sum_result": None,
        "note": "The ML model used sklearn; DGX GPU availability was verified separately through CuPy.",
        "error": None,
    }

    try:
        import cupy as cp  # type: ignore

        evidence["cupy_version"] = cp.__version__
        gpu_array = cp.arange(evidence["gpu_array_size"], dtype=cp.float32)
        evidence["gpu_sum_result"] = float(gpu_array.sum().get())
        evidence["gpu_test_status"] = "PASS"
    except Exception as exc:
        evidence["error"] = f"{type(exc).__name__}: {exc}"

    evidence_path = outputs_dir / "cupy_gpu_training_evidence.json"
    evidence_path.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    log(f"Saved CuPy GPU evidence: {evidence_path}")
    return evidence


def validate_columns(df: Any, required_columns: list[str]) -> None:
    missing_columns = [column for column in required_columns if column not in df.columns]
    if missing_columns:
        raise ValueError(f"Input is missing required columns: {', '.join(missing_columns)}")


def build_features(df: Any) -> tuple[Any, list[str]]:
    import pandas as pd  # type: ignore

    validate_columns(
        df,
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

    working = df.copy()
    working["timestamp"] = pd.to_datetime(working["timestamp"], errors="coerce")
    working = working.dropna(subset=["timestamp"])
    working = working.sort_values("timestamp").reset_index(drop=True)

    numeric_columns = [
        "total_kwh",
        "mean_kwh",
        "household_count",
        "hour",
        "minute",
        "day_of_week",
        "is_weekend",
        "settlement_period",
        "grid_stress_score",
    ]
    for column in numeric_columns:
        working[column] = pd.to_numeric(working[column], errors="coerce")

    lag_sources = ["total_kwh", "grid_stress_score"]
    lag_periods = [1, 2, 48]
    for source in lag_sources:
        for lag in lag_periods:
            working[f"{source}_lag_{lag}"] = working[source].shift(lag)

    rolling_windows = [3, 6, 48]
    for window in rolling_windows:
        working[f"rolling_mean_{window}"] = working["total_kwh"].rolling(window=window).mean()

    working["next_grid_stress_score"] = working["grid_stress_score"].shift(-1)
    working["next_stress_band"] = working["stress_band"].shift(-1)

    feature_columns = [
        "total_kwh",
        "mean_kwh",
        "household_count",
        "hour",
        "minute",
        "day_of_week",
        "is_weekend",
        "settlement_period",
        "grid_stress_score",
        "total_kwh_lag_1",
        "total_kwh_lag_2",
        "total_kwh_lag_48",
        "grid_stress_score_lag_1",
        "grid_stress_score_lag_2",
        "grid_stress_score_lag_48",
        "rolling_mean_3",
        "rolling_mean_6",
        "rolling_mean_48",
    ]

    working = working.dropna(subset=feature_columns + ["next_grid_stress_score", "next_stress_band"]).reset_index(drop=True)
    if len(working) < 10:
        raise ValueError("Not enough rows remain after feature engineering to train/test the model.")

    return working, feature_columns


def train_models(engineered: Any, feature_columns: list[str]) -> tuple[dict[str, Any], Any]:
    import pandas as pd  # type: ignore
    from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor  # type: ignore
    from sklearn.metrics import (  # type: ignore
        accuracy_score,
        confusion_matrix,
        mean_absolute_error,
        mean_squared_error,
        r2_score,
    )

    split_index = int(len(engineered) * 0.8)
    if split_index <= 0 or split_index >= len(engineered):
        raise ValueError("Time-based split produced an empty train or test partition.")

    train_df = engineered.iloc[:split_index].copy()
    test_df = engineered.iloc[split_index:].copy()

    X_train = train_df[feature_columns]
    X_test = test_df[feature_columns]
    y_reg_train = train_df["next_grid_stress_score"]
    y_reg_test = test_df["next_grid_stress_score"]
    y_cls_train = train_df["next_stress_band"]
    y_cls_test = test_df["next_stress_band"]

    regressor = RandomForestRegressor(
        n_estimators=200,
        max_depth=12,
        min_samples_leaf=2,
        random_state=42,
        n_jobs=-1,
    )
    classifier = RandomForestClassifier(
        n_estimators=200,
        max_depth=12,
        min_samples_leaf=2,
        random_state=42,
        n_jobs=-1,
    )

    log("Training regression model with sklearn RandomForestRegressor.")
    regressor.fit(X_train, y_reg_train)
    log("Training classification model with sklearn RandomForestClassifier.")
    classifier.fit(X_train, y_cls_train)

    reg_predictions = regressor.predict(X_test)
    cls_predictions = classifier.predict(X_test)

    mae = float(mean_absolute_error(y_reg_test, reg_predictions))
    rmse = float(mean_squared_error(y_reg_test, reg_predictions) ** 0.5)
    r2 = float(r2_score(y_reg_test, reg_predictions))

    labels = ["low", "medium", "high"]
    confusion = confusion_matrix(y_cls_test, cls_predictions, labels=labels)
    class_distribution = {
        label: int((y_cls_test == label).sum())
        for label in labels
    }

    predictions_df = pd.DataFrame(
        {
            "timestamp": test_df["timestamp"].dt.strftime("%Y-%m-%d %H:%M:%S"),
            "actual_next_grid_stress_score": y_reg_test.to_numpy(),
            "predicted_next_grid_stress_score": reg_predictions,
            "actual_next_stress_band": y_cls_test.to_numpy(),
            "predicted_next_stress_band": cls_predictions,
            "split": "test",
        }
    )

    metrics = {
        "hostname": socket.gethostname(),
        "python_executable": sys.executable,
        "training_ran_on_dgx": socket.gethostname() == "scan-12",
        "used_cuml": False,
        "used_sklearn": True,
        "regression_model": "RandomForestRegressor",
        "classification_model": "RandomForestClassifier",
        "train_rows": int(len(train_df)),
        "test_rows": int(len(test_df)),
        "feature_count": len(feature_columns),
        "regression_metrics": {
            "mae": mae,
            "rmse": rmse,
            "r2": r2,
        },
        "classification_metrics": {
            "accuracy": float(accuracy_score(y_cls_test, cls_predictions)),
            "confusion_matrix_labels": labels,
            "confusion_matrix": confusion.tolist(),
            "class_distribution": class_distribution,
        },
    }
    return metrics, predictions_df


def write_outputs(
    metrics: dict[str, Any],
    predictions_df: Any,
    output_dir: Path,
    outputs_dir: Path,
    cupy_evidence: dict[str, Any],
    command_text: str,
) -> tuple[Path, Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    outputs_dir.mkdir(parents=True, exist_ok=True)

    predictions_path = output_dir / "grid_stress_predictions.csv"
    metrics_path = outputs_dir / "model_metrics.json"
    report_path = outputs_dir / "model_training_report.md"

    predictions_df.to_csv(predictions_path, index=False)
    metrics_path.write_text(json.dumps(metrics, indent=2) + "\n", encoding="utf-8")

    regression = metrics["regression_metrics"]
    classification = metrics["classification_metrics"]
    report = f"""# Model Training Report

Generated on host: `{metrics['hostname']}`

## Environment

- hostname: `{metrics['hostname']}`
- exact Python executable: `{metrics['python_executable']}`
- whether training ran on DGX: `{metrics['training_ran_on_dgx']}`
- whether cuML was used: `No`
- why cuML was not used: `unavailable in current DGX venv`
- whether sklearn was used: `Yes`
- whether CuPy GPU test passed: `{cupy_evidence['gpu_test_status'] == 'PASS'}`

## Regression Metrics

- MAE: `{regression['mae']}`
- RMSE: `{regression['rmse']}`
- R2: `{regression['r2']}`

## Classification Metrics

- accuracy: `{classification['accuracy']}`
- confusion matrix labels: `{classification['confusion_matrix_labels']}`
- confusion matrix: `{classification['confusion_matrix']}`
- class distribution: `{classification['class_distribution']}`

## Generated Output Paths

- `{metrics_path}`
- `{report_path}`
- `{outputs_dir / 'cupy_gpu_training_evidence.json'}`
- `{predictions_path}`

## Exact Command Used

```bash
{command_text}
```
"""
    report_path.write_text(report, encoding="utf-8")

    log(f"Saved metrics JSON: {metrics_path}")
    log(f"Saved training report: {report_path}")
    log(f"Saved prediction CSV: {predictions_path}")
    return metrics_path, report_path, predictions_path


def main() -> int:
    try:
        import pandas as pd  # type: ignore

        args = parse_args()
        input_path = resolve_path(args.input)
        output_dir = resolve_path(args.output_dir)
        outputs_dir = repo_root() / "apps" / "dgx_pipeline" / "outputs"

        if not input_path.exists():
            raise FileNotFoundError(f"Input file does not exist: {input_path}")

        command_text = "python " + " ".join(sys.argv)
        log(f"Loading processed features: {input_path}")
        raw_df = pd.read_csv(input_path)
        engineered, feature_columns = build_features(raw_df)
        log(f"Engineered {len(feature_columns)} model features across {len(engineered):,} rows.")

        cupy_evidence = run_cupy_evidence(outputs_dir)
        metrics, predictions_df = train_models(engineered, feature_columns)
        metrics["cupy_gpu_test_passed"] = cupy_evidence["gpu_test_status"] == "PASS"
        metrics["cupy_gpu_evidence_path"] = str(outputs_dir / "cupy_gpu_training_evidence.json")

        metrics_path, report_path, predictions_path = write_outputs(
            metrics,
            predictions_df,
            output_dir,
            outputs_dir,
            cupy_evidence,
            command_text,
        )

        summary = {
            "metrics_path": str(metrics_path),
            "report_path": str(report_path),
            "predictions_path": str(predictions_path),
            "regression_metrics": metrics["regression_metrics"],
            "classification_metrics": metrics["classification_metrics"],
            "first_prediction_rows": predictions_df.head(10).to_dict(orient="records"),
        }
        print(json.dumps(summary, indent=2), flush=True)
        return 0
    except Exception as exc:
        print(f"[gridflex-train] ERROR: {exc}", file=sys.stderr, flush=True)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())