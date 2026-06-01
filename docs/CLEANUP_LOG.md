# Cleanup Log

- Timestamp: 2026-03-10T19:50:59
- Rule: remove smoke caches, heavy runtime intermediates, and obsolete raw/processed data; keep final deliverables.

## Deleted
- `__pycache__/`
- `scripts/__pycache__/`
- `configs/gridagent_framework.formal2024.smoke.json`
- `data_raw/`
- `data_processed/`
- `results/gridagent_framework/`
- `results/wind_pv_uncertainty/demo2020/sampled_scenarios.npy`
- `results/wind_pv_uncertainty/formal2024/sampled_scenarios.npy`
- `results/wind_pv_uncertainty/demo2020/typical_scenarios_long.csv`
- `results/wind_pv_uncertainty/formal2024/typical_scenarios_long.csv`
- `results/wind_pv_uncertainty_smoke/`
- `results/component_failure_probability/formal2024_smoke/`
- `results/spatiotemporal_contingency/formal2024_schloemer_smoke/`
- `results/load_prioritization_scheduling/formal2024_schloemer_smoke/`
- `results/multi_criteria_resilience/formal2024_schloemer_smoke/`
- `results/module_sensitivity/formal2024/runs/`
- `results/multiscenario_fusion/phase1_design/edge_eval_pilot/`
- `results/multiscenario_fusion/phase1_design/edge_eval_v2/`
- `results/multiscenario_fusion/phase1_design/cloud_eval_v1/runtime/`
- `results/multiscenario_fusion/phase1_design/prepared/`

## Moved For Organization
- `DATASET_PIPELINE.md` -> `docs/DATASET_PIPELINE.md`
- `paper745.txt` -> `docs/paper745.txt`
- `run_matpower_resilience_batch.m` -> `scripts/legacy/run_matpower_resilience_batch.m`
- `typhoon_grid_resilience_demo.py` -> `scripts/legacy/typhoon_grid_resilience_demo.py`

## Retained (Core)
- `data_final/`
- `configs/`
- `scripts/`
- `results/*` summary outputs and final deliverables