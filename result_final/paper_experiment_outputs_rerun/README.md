# Paper experiment rerun outputs

This directory contains rerun-backed experiment tables for the ICDE paper package.

## Core files

- `dataset_statistics.csv`
- `main_prediction_comparison.csv`
- `topk_risk_identification.csv`
- `ablation_study.csv`
- `ablation_study_runs.csv`
- `graph_structure_analysis.csv`
- `downstream_dispatch_utility.csv`
- `multi_window_evaluation.csv`
- `risk_label_distribution.csv`
- `runtime_scalability.csv`
- `experiment_completion_status.csv`

## Run manifests

- `run_manifest.json`: E8/E9 model reruns.
- `ablation_run_manifest.json`: E10 full-grid ablation reruns.
- `dispatch_run_manifest.json`: E12/E13 dispatch reruns.

All CSV files are also synced to `paper_submission_package/results/paper_experiments_rerun`.
