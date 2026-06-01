# Results Cleanup Suggestions (2026-04-07)

## Current Snapshot

- `results/` files: 1414
- `results/` total size: **378.37 MB** (~0.37 GB)
- Latest framework run pointer: `results\gridagent_framework\ieee118_n60_stagewise_20260324_195044`

| Top Directory | Files | Size (MB) |
|---|---:|---:|
| `ablation` | 89 | 189.72 |
| `gridagent_framework` | 320 | 91.88 |
| `component_failure_probability` | 169 | 61.02 |
| `spatiotemporal_contingency` | 42 | 20.08 |
| `formal2024_full_baseline_20260310_233109_standard` | 14 | 4.54 |
| `early_warning` | 483 | 3.92 |
| `wind_pv_uncertainty` | 8 | 3.58 |
| `paper_comparison` | 120 | 1.07 |
| `load_prioritization_scheduling` | 6 | 0.38 |
| `dispatch_optimization` | 72 | 0.22 |
| `multiscenario_fusion` | 27 | 0.11 |
| `timepoint_snapshots_formal2024_20240901_0000_1700` | 19 | 0.06 |

| File Type | Count | Size (MB) |
|---|---:|---:|
| `.npy` | 41 | 207.01 |
| `.csv` | 1083 | 167.39 |
| `.json` | 249 | 2.2 |
| `.zip` | 1 | 1.56 |
| `.txt` | 3 | 0.11 |
| `.md` | 12 | 0.05 |
| `.log` | 25 | 0.04 |

## Keep Baseline (Recommended)

- Keep `results/gridagent_framework/latest_run.json` and the pointed latest run directory.
- Keep one historical full baseline run for reproducibility (`formal2024_full_baseline_20260310_233109`).
- Keep summary/report files (`*_report.json`, `*_summary.csv`, `comparison_*.md/json`, `framework_report.json`).

## Cleanup Plan A (Low Risk)

- Remove `dryrun/smoke/tmp` directories in `results/`: **~2.19 MB**
- Remove `.log` files in `results/`: **~0.04 MB**
- Optional: keep either the folder or the zip for `formal2024_full_baseline_20260310_233109_standard` to avoid duplicate packaging.

## Cleanup Plan B (Recommended, Medium Risk)

1. Prune Stage2 tuning grids, keep only sweep summaries + 1 representative run per grid family.
   Estimated reclaim: **~57.12 MB**
   Keep examples:
   - `results\component_failure_probability\ieee118_n60_stage2_calib\ds0p030_it3p5`
   - `results\component_failure_probability\ieee118_n60_stagewise_tune\ds1p00_it2p80`
   - `results\component_failure_probability\ieee118_n60_tune\ds1p00_it1p40`
   - `results\component_failure_probability\ieee118_n60_stage2_calib\sweep_summary.json`
   - `results\component_failure_probability\ieee118_n60_tune\sweep_summary.json`
2. Prune duplicated `sampled_scenarios.npy` (keep 2 canonical files).
   Estimated reclaim: **~134.08 MB**
   Candidate files to drop:
   - `results\ablation\stage123_comparison\stage1_uncertainty\dpgmm\formal2024\sampled_scenarios.npy`
   - `results\ablation\stage1_comparison\arima\sampled_scenarios.npy`
   - `results\ablation\stage1_comparison\copula\sampled_scenarios.npy`
   - `results\ablation\stage1_comparison\dpgmm\sampled_scenarios.npy`
   - `results\ablation\stage1_comparison\lstm\sampled_scenarios.npy`
   - `results\gridagent_framework\dispatch_opt_integration_smoke\stage1_wind_pv\formal2024\sampled_scenarios.npy`
   - `results\gridagent_framework\formal2024_quick_std\stage1_wind_pv\formal2024\sampled_scenarios.npy`
   - `results\gridagent_framework\warning_integration_smoke\stage1_wind_pv\formal2024\sampled_scenarios.npy`
3. Optional: prune duplicated `typical_scenarios_long.csv` (keep 2 canonical files).
   Estimated reclaim: **~31.77 MB**

- Plan B total reclaim (without long CSV pruning): **~193.39 MB**
- Plan B total reclaim (with long CSV pruning): **~225.16 MB**

## Cleanup Plan C (Aggressive Archive)

- Archive raw folders under:
  - `results/ablation/stage1_comparison/`
  - `results/ablation/stage123_comparison/`
- Keep only top-level summary docs/json in those folders.
- Estimated reclaim: **~189.43 MB** (overlaps with Plan B `sampled_scenarios` pruning).

## Notes

- Estimates are measured on current workspace state (2026-04-07) and may shift if files change.
- Plans are suggestions only; no files were deleted in this step.
- If you want, I can execute Plan A now, or generate a one-click PowerShell cleanup script for Plan B/C.
