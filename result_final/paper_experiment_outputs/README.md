# Paper experiment outputs

Generated from existing verified result files. Fields with unavailable ranking metrics are left blank and documented in `source_note`.

## Files

- `ablation_study.csv`
- `dataset_statistics.csv`
- `downstream_dispatch_utility.csv`
- `experiment_completion_status.csv`
- `graph_structure_analysis.csv`
- `main_prediction_comparison.csv`
- `multi_window_evaluation.csv`
- `risk_label_distribution.csv`
- `runtime_scalability.csv`
- `topk_risk_identification.csv`

## Remaining true rerun gaps

- `main_prediction_comparison.csv`: `recall_at_10` and `hit_at_10` need saved model predictions or a Stage6 rerun with ranking metrics.
- `ablation_study.csv`: A0-A3 MAE/RMSE/high-risk MAE are available, but Recall@10 was not logged.
- `graph_structure_analysis.csv`: current file is an encoder proxy; random graph and fully connected graph variants still need dedicated runs.
- `downstream_dispatch_utility.csv`: current file compares dispatch formulations under final warning context; no-warning/prior-only warning ablation still needs a dedicated run.
- `multi_window_evaluation.csv`: current file has two existing snapshots; a formal multi-window table should add more windows.
