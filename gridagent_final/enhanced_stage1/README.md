# GridAgent Enhanced Stage1 Package

This folder is the cleaned upload package for the enhanced Stage1 method.

## Purpose

Enhanced Stage1 replaces hour-wise independent Rolling DPGMM with:

- Conditional Rolling DPGMM
- KMeans scenario reduction

The main idea is to learn the transition relation between consecutive hours:

- previous hour: `[wind_(t-1), pv_(t-1)]`
- current hour: `[wind_t, pv_t]`

and then generate annual trajectories sequentially with conditional sampling.
The current cleaned version also adds practical constraints for formal experiments:

- robust absolute/relative path resolution
- per-variable normalization before DPGMM fitting and sampling
- first-hour initialization from the early local window instead of the whole year
- output clipping to historical upper bounds
- night-hour PV reset to zero
- lower default iteration count (`max_iter=150`) for faster formal runs

## Structure

| Path | Purpose |
|---|---|
| `scripts/conditional_wind_pv_uncertainty_modeling.py` | Enhanced Stage1 execution script. |
| `inputs/DPGMM_input.guangdong2024.csv` | Wind/PV feature table used by the enhanced Stage1. |
| `inputs/TRIM_input.guangdong2024.csv` | Timestamp-aligned table used to provide the time axis. |
| `outputs/` | Output folder for the enhanced Stage1 results. |
| `requirements_enhanced_stage1.txt` | Minimal Python dependencies. |

## Method Summary

1. Read wind/PV historical series.
2. Build 4D transition samples:
   `[wind_(t-1), pv_(t-1), wind_t, pv_t]`.
3. Normalize wind and PV using historical per-variable maxima.
4. Fit a rolling DPGMM over transition windows for hour-by-hour conditional sampling.
5. Generate annual trajectories sequentially:
   `x_1 -> x_2 -> x_3 -> ... -> x_T`.
6. Restore MW scale, apply upper-bound and night-PV constraints.
7. Reduce sampled trajectories to 10 representative scenarios using KMeans.

## Reproduction Command

```powershell
python scripts\conditional_wind_pv_uncertainty_modeling.py --dataset formal2024 --dpgmm-input inputs\DPGMM_input.guangdong2024.csv --trim-input inputs\TRIM_input.guangdong2024.csv --output-dir outputs --window-radius 24 --max-components 8 --max-iter 150 --shared-block-hours 1 --n-sampled-scenarios 200 --n-typical-scenarios 10 --seed 42
```

## Note

This package mirrors the organization style of `gridagent_final/stage1`, but it contains the enhanced method implementation rather than the original Rolling DPGMM script.
