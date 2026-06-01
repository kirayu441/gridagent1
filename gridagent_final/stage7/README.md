# GridAgent Stage7 Package

This folder is the cleaned upload package for Stage7.

## Purpose

Stage7 performs contextual dispatch optimization on the IEEE 118 full-node grid.

The current cleaned package uses:

- IEEE 118 full-node topology
- Guangdong 2024 load and renewable input
- Stage2 formal candidate failure timeline
- Stage1 formal uncertainty scenarios
- Stage4 load-priority profile
- Stage6 formal warning context

## Structure

| Path | Purpose |
|---|---|
| `scripts/dispatch_optimization_module.py` | Stage7 execution script. |
| `inputs/grid_topology.ieee118_full.json` | IEEE 118 full grid topology used for buses, lines, and units. |
| `inputs/TRIM_input.guangdong2024.csv` | Guangdong 2024 trimmed load and renewable time series used as the deterministic backbone. |
| `inputs/line_failure_timeseries_schloemer.csv` | Stage2 line failure time series used for the timeline and hourly line-risk proxy. |
| `inputs/load_bus_priority_profile.csv` | Stage4 load-priority profile used for load class and VOLL weighting. |
| `inputs/stage1_formal_output/` | Stage1 uncertainty outputs used for stochastic and robust renewable/load scenario construction. |
| `inputs/stage6_warning_formal_ieee118_full_a2_c3po_ref/` | Stage6 warning outputs used for contextual strategy routing. |
| `outputs/` | Output folder for Stage7 results. |
| `requirements_stage7.txt` | Minimal Python dependencies. |

## Method Summary

1. Read the IEEE 118 full grid, Guangdong 2024 TRIM input, Stage2 failure timeline, Stage1 uncertainty scenarios, Stage4 load-priority profile, and Stage6 warning outputs.
2. Build three dispatch candidates:
   `SCUC`, `Stochastic_UC`, and `Robust_UC`.
3. Use Stage6 warning context plus hourly uncertainty/risk signals to route each hour to an active strategy.
4. Merge the selected hourly schedules into the contextual dispatch result.
5. Export strategy selection, contextual unit schedule, load shedding, line flow, and the Stage7 report.

## Reproduction Command

```powershell
python scripts\dispatch_optimization_module.py --strategy-mode contextual --export-diagnostics --grid inputs\grid_topology.ieee118_full.json --trim-input inputs\TRIM_input.guangdong2024.csv --failure-csv inputs\line_failure_timeseries_schloemer.csv --uncertainty-dir inputs\stage1_formal_output --line-risk-csv inputs\stage6_warning_formal_ieee118_full_a2_c3po_ref\line_risk_prediction.csv --load-priority-csv inputs\load_bus_priority_profile.csv --output-dir outputs\formal_ieee118_full_contextual_stage1baseline_a2_c3po_ref_h24 --horizon-hours 24 --horizon-start-index 24 --seed 3042
```

## Note

This package mirrors the organization style of `gridagent_final/stage1`, but it contains the Stage7 contextual dispatch optimization module.
