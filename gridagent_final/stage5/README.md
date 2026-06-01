# GridAgent Stage5 Package

This folder is the cleaned upload package for Stage5.

## Purpose

Stage5 performs multi-criteria resilience assessment on the policy results produced by Stage4.

The current cleaned package uses:

- Stage4 policy comparison results
- Stage4 worst-scenario shedding detail results
- EWM + TOPSIS multi-indicator aggregation

## Structure

| Path | Purpose |
|---|---|
| `scripts/multi_criteria_resilience_assessment.py` | Stage5 execution script. |
| `inputs/policy_comparison.csv` | Stage4 policy-level resilience summary used as the primary policy input. |
| `inputs/worst_scenario_shedding_detail.csv` | Stage4 worst-scenario shedding time-series detail used to derive rapidity and sustainability indicators. |
| `outputs/` | Output folder for Stage5 results. |
| `requirements_stage5.txt` | Minimal Python dependencies. |

## Method Summary

1. Read Stage4 policy comparison results.
2. Read Stage4 worst-scenario shedding detail for each policy.
3. Compute four resilience indicators:
   `Priority`, `Robustness`, `Rapidity`, and `Sustainability`.
4. Apply entropy weight method (EWM) to obtain data-driven indicator weights.
5. Apply TOPSIS to produce the final resilience ranking of Stage4 policies.
6. Export the indicator table, single-indicator rankings, TOPSIS results, and the Stage5 report.

## Reproduction Command

```powershell
python scripts\multi_criteria_resilience_assessment.py --policy-comparison inputs\policy_comparison.csv --worst-detail inputs\worst_scenario_shedding_detail.csv --output-dir outputs\formal_ieee118_full_candidate_rr0p30
```

## Note

This package mirrors the organization style of `gridagent_final/stage1`, but it contains the Stage5 multi-criteria resilience assessment module.
