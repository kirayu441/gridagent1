# GridAgent Stage4 Package

This folder is the cleaned upload package for Stage4.

## Purpose

Stage4 performs pre-disaster scheduling and load-priority-aware post-disaster shedding evaluation on the IEEE 118 full-node grid.

The current cleaned package uses:

- IEEE 118 full-node topology
- Guangdong 2024 TRIM load input
- Stage3 `c3po_ref` contingency tensor
- enhanced Stage1 formal wind/PV typical scenarios

## Structure

| Path | Purpose |
|---|---|
| `scripts/load_prioritization_scheduling.py` | Stage4 execution script. |
| `inputs/grid_topology.ieee118_full.json` | IEEE 118 full grid topology used for bus, line, and generator definitions. |
| `inputs/TRIM_input.guangdong2024.csv` | Guangdong 2024 load time series used to build total hourly demand. |
| `inputs/line_failure_timeseries_schloemer.csv` | Stage2 line failure probability time series used for timestamp and line ordering alignment. |
| `inputs/contingency_tensor_c3po_ref.npy` | Stage3 spatio-temporal outage tensor used for scenario simulation. |
| `inputs/enhanced_stage1_formal_Guangdong_full_semidecoupled_w15_p30/` | Stage1 wind/PV uncertainty outputs used to map renewable supply into Stage4 scenarios. |
| `outputs/` | Output folder for Stage4 results. |
| `requirements_stage4.txt` | Minimal Python dependencies. |

## Method Summary

1. Read the IEEE 118 full-node grid, Stage3 contingency tensor, Stage2 failure table, Guangdong 2024 load input, and enhanced Stage1 renewable scenarios.
2. Split load buses into three priority levels and assign priority weights.
3. Build hourly load demand shares across load buses from the TRIM total load series.
4. Map Stage1 wind/PV typical scenarios onto the grid's renewable generator buses.
5. Solve the pre-disaster linear scheduling problem for base dispatch and reserve allocation.
6. Simulate post-disaster optimal shedding under the outage tensor for different policy baselines.
7. Export policy comparison, scenario metrics, worst-scenario shedding details, dispatch schedule, and the Stage4 report.

## Reproduction Command

```powershell
python scripts\load_prioritization_scheduling.py --grid inputs\grid_topology.ieee118_full.json --trim-input inputs\TRIM_input.guangdong2024.csv --contingency-tensor inputs\contingency_tensor_c3po_ref.npy --failure-csv inputs\line_failure_timeseries_schloemer.csv --uncertainty-dir inputs\enhanced_stage1_formal_Guangdong_full_semidecoupled_w15_p30 --output-dir outputs\formal_ieee118_full_candidate --reserve-ratio 0.30 --policy-set all --seed 42
```

## Note

This package mirrors the organization style of `gridagent_final/stage1`, but it contains the Stage4 load prioritization and scheduling module.
