# Model Training Report

Generated on host: `scan-12`

## Environment

- hostname: `scan-12`
- exact Python executable: `/home/nvidia/gridflex-compute/.venv-dgx/bin/python`
- whether training ran on DGX: `True`
- whether cuML was used: `No`
- why cuML was not used: `unavailable in current DGX venv`
- whether sklearn was used: `Yes`
- whether CuPy GPU test passed: `True`

## Regression Metrics

- MAE: `0.0369882115503678`
- RMSE: `0.0526039269045957`
- R2: `0.7847183183455926`

## Classification Metrics

- accuracy: `0.8512163892445582`
- confusion matrix labels: `['low', 'medium', 'high']`
- confusion matrix: `[[5007, 293, 0], [808, 1631, 9], [28, 24, 10]]`
- class distribution: `{'low': 5300, 'medium': 2448, 'high': 62}`

## Generated Output Paths

- `/home/nvidia/gridflex-compute/apps/dgx_pipeline/outputs/model_metrics.json`
- `/home/nvidia/gridflex-compute/apps/dgx_pipeline/outputs/model_training_report.md`
- `/home/nvidia/gridflex-compute/apps/dgx_pipeline/outputs/cupy_gpu_training_evidence.json`
- `/home/nvidia/gridflex-compute/data/processed/grid_stress_predictions.csv`

## Exact Command Used

```bash
python apps/dgx_pipeline/src/train_stress_model.py --input data/processed/grid_stress_features.csv --output-dir data/processed
```
