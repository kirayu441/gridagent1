# IEEE118 Full + Guangdong 2024 Paper Dataset

This directory is the formal paper dataset package for GridAgent final experiments.

## Dataset Definition

- Grid topology: IEEE 118 full topology (`118` nodes, `186` lines, `54` generators).
- Weather / wind / PV / load time series: Guangdong 2024 formal dataset (`8784` hourly records).
- Time range: `2024-01-01 00:00:00` to `2024-12-31 23:00:00`.

## Files

| Path | Description |
|---|---|
| `inputs/grid_topology.ieee118_full.json` | IEEE118 full grid topology. |
| `inputs/aligned_merged.guangdong2024.csv` | Aligned Guangdong 2024 weather, wind/PV and load series. |
| `inputs/DPGMM_input.guangdong2024.csv` | Stage1 wind/PV uncertainty input. |
| `inputs/TRIM_input.guangdong2024.csv` | Stage3/Stage7 time-series input with calendar features. |
| `metadata/dataset_integrity_report.json` | Dataset package integrity and source summary. |
| `configs/gridagent_framework.ieee118_full_guangdong2024.json` | Stage1-8 framework config using this dataset package and writing runs under `final_results`. |

## Intended Pipeline

Use the config below for formal Stage1-8 runs:

```powershell
python scripts\gridagent_framework.py --config final_results\dataset_ieee118_full_guangdong2024\configs\gridagent_framework.ieee118_full_guangdong2024.json --mode baseline --run-tag ieee118_full_guangdong2024_formal
```
