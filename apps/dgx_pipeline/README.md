# DGX Pipeline

Use DGX for:
- cuDF ingestion of the large LCL smart-meter file.
- GPU aggregation to 30-minute grid stress proxy.
- cuML regression/classification to forecast next stress band.
- Optional NIM/Triton/Nemo-based explanation endpoint.

Do not block the demo on full modelling. Export grid_stress_profile_from_lcl.csv first.
