# GridAgent Stage2 Package

This folder is the cleaned upload package for Stage2.

## Purpose

Stage2 computes hourly transmission-line failure probabilities under a parameterized typhoon process.

The current implementation includes:

- Batts wind-field model
- Schloemer wind-field model
- stress-strength failure probability calculation
- line-level aggregation from span and tower failures

## Structure

| Path | Purpose |
|---|---|
| `scripts/component_failure_probability.py` | Stage2 execution script. |
| `inputs/grid_topology.ieee118_full.json` | IEEE 118 full grid topology used by Stage2. |
| `outputs/` | Output folder for Stage2 results. |
| `requirements_stage2.txt` | Minimal Python dependencies. |

## Method Summary

1. Read the grid topology and derive line assets.
2. Build a 72-hour parameterized typhoon track.
3. Compute local wind speeds on each line midpoint using Batts or Schloemer.
4. Convert wind speed into tower and span loads.
5. Use stress-strength probability to compute component failure probabilities.
6. Aggregate tower/span failures into line failure probabilities over time.

## Reproduction Command

```powershell
python scripts\component_failure_probability.py --grid inputs\grid_topology.ieee118_full.json --output-dir outputs --model both --start-time "2024-09-01 00:00:00" --hours 72 --center-lat 23.1291 --center-lon 113.2644 --intensity-scale 1.0 --move-dir-deg 300.0 --move-speed-ms 6.0 --design-scale 1.0
```

## Note

This package mirrors the organization style of `gridagent_final/stage1`, but it contains the Stage2 transmission-component failure probability module.
