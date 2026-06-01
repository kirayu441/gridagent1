# GridAgent Stage8 Package

This folder is the cleaned upload package for Stage8.

## Purpose

Stage8 is the standardized export layer for the final experiment chain.

It reorganizes the selected Stage1-Stage7 outputs into a final delivery structure:

- `scenario/`
- `warning/`
- `dispatch/`
- `resilience/`
- `summary/`

## Structure

| Path | Purpose |
|---|---|
| `scripts/export_standard_results.py` | Standardized export script. |
| `inputs/framework_run/framework_report.json` | Final selected-chain manifest used as the export input. |
| `outputs/` | Final standardized Stage8 result package. |
| `requirements_stage8.txt` | Minimal Python dependencies. |

## Selected Final Chain

- Stage1 uncertainty: `gridagent_final/stage1/outputs`
- Stage2 failure: `gridagent_final/stage2/outputs/formal_ieee118_full_candidate_ds0p03_it3p5`
- Stage3 contingency: `gridagent_final/stage3/outputs`
- Stage4 scheduling: `gridagent_final/stage4/outputs/formal_ieee118_full_candidate_rr0p30`
- Stage5 assessment: `gridagent_final/stage5/outputs/formal_ieee118_full_candidate_rr0p30`
- Stage6 warning: `gridagent_final/stage6/outputs/formal_ieee118_full_a2_c3po_ref`
- Stage7 dispatch: `gridagent_final/stage7/outputs/formal_ieee118_full_contextual_stage1baseline_a2_c3po_ref_h24`

## Reproduction Command

```powershell
python scripts\export_standard_results.py --run-root inputs\framework_run --output-root outputs\formal_ieee118_full_standard
```

## Note

This package mirrors the organization style of `gridagent_final/stage1`, but it contains the Stage8 standardized export layer rather than a new physical simulation module.
