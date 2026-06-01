# Result Final

This folder is the final delivery-facing result bundle for the current GridAgent IEEE118 formal experiment chain.

## Included Content

| Path | Purpose |
|---|---|
| `FINAL_EXPERIMENT_REPORT.md` | Final overall report for the Stage1-Stage8 chain. |
| `standardized_results/` | Standardized export package copied from Stage8. |

## Final Selected Chain

- Grid topology: IEEE 118 full-node grid
- Weather/load data: Guangdong 2024
- Stage1 uncertainty source for final dispatch chain: original `stage1` formal output
- Stage2 failure model: `schloemer`
- Stage3 contingency method: `c3po_ref`
- Stage4 reserve ratio: `0.3`
- Stage6 warning model: `A2_metapath_adaptive_global`
- Stage6 warning label: `c3po_ref`
- Stage7 dispatch mode: contextual adaptive

## Important Note

The enhanced Stage1 output was successfully developed and evaluated, but in the current Stage7 UC formulation it led to infeasible `Stochastic_UC` runs. Therefore, the final operational chain keeps:

- enhanced Stage1 as an improved Stage1 research result
- original Stage1 formal output as the stable uncertainty source for the final Stage7-Stage8 dispatch chain

