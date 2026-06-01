# GridAgent Stage6 Package

This folder is the cleaned upload package for Stage6.

## Purpose

Stage6 performs line-level early warning and risk prediction on the IEEE 118 full-node grid.

The current cleaned package uses the selected formal Stage6 scheme:

- `A2_metapath_adaptive_global`
- supervision label: `c3po_ref`
- training enhancement: `warmup + gate_reg + risk_weight + lower lr`

## Structure

| Path | Purpose |
|---|---|
| `scripts/gnn_warning_module.py` | Stage6 execution script. |
| `inputs/grid_topology.ieee118_full.json` | IEEE 118 full grid topology used for node, line, and generator structure. |
| `inputs/aligned_merged.guangdong2024.csv` | Guangdong 2024 aligned wind/PV/load/weather time series used to build node temporal features. |
| `inputs/line_failure_timeseries_schloemer.csv` | Stage2 line failure time series used for edge dynamic features. |
| `inputs/contingency_tensor_c3po_ref.npy` | Stage3 `c3po_ref` contingency tensor used as supervision labels. |
| `inputs/load_bus_priority_profile.csv` | Stage4 load-priority profile used to define critical-load attributes. |
| `outputs/` | Output folder for Stage6 results. |
| `requirements_stage6.txt` | Minimal Python dependencies. |

## Method Summary

1. Read the IEEE 118 full-node grid, Guangdong aligned time series, Stage2 line failure table, Stage3 contingency tensor, and Stage4 load-priority profile.
2. Build node features, edge dynamic/static features, and line outage probability labels.
3. Train the selected `MetaPath V1` warning model with `adaptive_global` semantic attention.
4. Enable the selected training enhancements:
   lower learning rate, risk-weighted objective, MetaPath warmup, and gate regularization.
5. Predict hourly line risk and derive downstream warning outputs:
   calibrated line probability, line warning table, N-k risk, and critical-load risk.
6. Export the warning report and model comparison outputs.

## Reproduction Command

```powershell
python scripts\gnn_warning_module.py --grid inputs\grid_topology.ieee118_full.json --aligned inputs\aligned_merged.guangdong2024.csv --failure-csv inputs\line_failure_timeseries_schloemer.csv --contingency-tensor inputs\contingency_tensor_c3po_ref.npy --load-priority-csv inputs\load_bus_priority_profile.csv --output-dir outputs\formal_ieee118_full_a2_c3po_ref --horizon-hours 24 --horizon-start-index 24 --train-ratio 0.7 --hidden-dim 80 --epochs 700 --lr 0.00315 --weight-decay 0.00015 --mc-scenarios 3000 --metapath-v1-enabled --metapath-attention-mode adaptive_global --metapath-topk 3 --run-baseline-comparison --risk-weight-alpha 1.0 --risk-weight-beta 2.0 --risk-weight-threshold 0.10 --risk-weight-on-metapath-only --metapath-gate-reg-lambda 0.0002 --metapath-attention-entropy-reg-lambda 0.0 --metapath-warmup-epochs 12 --high-risk-threshold 0.10 --top-risk-quantile 0.90 --seed 42
```

## Note

This package mirrors the organization style of `gridagent_final/stage1`, but it contains the Stage6 GNN early-warning module.
