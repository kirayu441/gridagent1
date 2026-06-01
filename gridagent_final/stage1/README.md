# GridAgent Final Stage1 Package

This folder is the cleaned upload package for Stage1 only.

## Purpose

Stage1 performs wind-PV uncertainty modeling on the Guangdong 2024 hourly series and compresses the original yearly sequence into a small set of representative scenarios with probabilities.

## Structure

| Path | Purpose |
|---|---|
| `scripts/wind_pv_uncertainty_modeling.py` | Stage1 execution script. |
| `inputs/DPGMM_input.guangdong2024.csv` | Wind/PV feature table used by Stage1. |
| `inputs/TRIM_input.guangdong2024.csv` | Timestamp-aligned table used by Stage1 to provide the time axis. |
| `outputs/history_series.csv` | Historical wind/PV series used for modeling. |
| `outputs/scenario_probabilities.csv` | Probabilities of the 10 representative scenarios. |
| `outputs/typical_scenarios.npy` | Core scenario tensor, shape `(10, 8784, 2)`. |
| `outputs/typical_scenarios_long.csv` | CSV view of the representative scenarios. |
| `outputs/uncertainty_report.json` | Stage1 report with parameters and quality metrics. |
| `requirements_stage1.txt` | Minimal Python dependencies for Stage1. |

## Why Some Files Are Not Included

- `sampled_scenarios.npy` is not included because it is a large intermediate artifact used before scenario reduction.
- Grid topology files are not included because Stage1 does not read the power grid topology.

## File Meaning

1. `DPGMM_input.guangdong2024.csv`
   Contains the wind and PV columns used to fit the rolling DPGMM.
2. `TRIM_input.guangdong2024.csv`
   Contains the hourly timestamps and auxiliary columns; Stage1 mainly uses the timestamp column to align the scenario time axis.
3. `history_series.csv`
   A compact export of the final historical wind/PV series actually modeled by Stage1.
4. `typical_scenarios.npy`
   The main Stage1 result. Each scenario is a full-year wind/PV trajectory.
5. `scenario_probabilities.csv`
   Gives the probability weight of each representative scenario.
6. `typical_scenarios_long.csv`
   Converts the scenario tensor into a table format for checking, plotting, and paper use.
7. `uncertainty_report.json`
   Records input paths, model parameters, summary statistics, and coverage metrics.

## Reproduction Command

```powershell
python scripts\wind_pv_uncertainty_modeling.py --dataset formal2024 --dpgmm-input inputs\DPGMM_input.guangdong2024.csv --trim-input inputs\TRIM_input.guangdong2024.csv --output-dir outputs --window-radius 6 --max-components 8 --max-iter 400 --n-sampled-scenarios 200 --n-typical-scenarios 10 --seed 42
```
