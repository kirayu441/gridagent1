# GridAgent Stage3 Package

This folder is the cleaned upload package for Stage3.

## Purpose

Stage3 converts line-level failure probabilities from Stage2 into spatio-temporal contingency scenarios.

The current implementation supports:

- `wang_qmc`
- `wang_mc`
- `c3po_ref`
- `trim_ref`

For the cleaned package run, the default formal output uses:

- `c3po_ref`

## Structure

| Path | Purpose |
|---|---|
| `scripts/spatiotemporal_contingency_generator.py` | Stage3 execution script. |
| `inputs/grid_topology.ieee118_full.json` | IEEE 118 full grid topology used for graph connectivity and bus roles. |
| `inputs/line_failure_timeseries_schloemer.csv` | Stage2 line failure probability timeseries used as Stage3 input. |
| `outputs/` | Output folder for Stage3 results. |
| `requirements_stage3.txt` | Minimal Python dependencies. |

## Method Summary

1. Read Stage2 line failure probability timeseries.
2. Pivot hourly line failure probabilities into a `time x line` matrix.
3. Build outage tensors using the selected contingency generation method.
4. Evaluate high-risk coverage, outage rates, disconnected loads, and diversity.
5. Export the contingency tensor, scenario table, method comparison, and summary report.

## Reproduction Command

```powershell
python scripts\spatiotemporal_contingency_generator.py --failure-csv inputs\line_failure_timeseries_schloemer.csv --grid inputs\grid_topology.ieee118_full.json --output-dir outputs --methods c3po_ref --n-scenarios 256 --seed 42 --repair-hours 12 --high-risk-quantile 0.90
```

## Note

This package mirrors the organization style of `gridagent_final/stage1`, but it contains the Stage3 spatio-temporal contingency generation module.
