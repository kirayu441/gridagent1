# Stage1 Performance Package

This package strengthens the evidence for the current Stage1 method:

- Rolling DPGMM
- 200 sampled annual trajectories
- KMeans reduction to 10 representative scenarios

It reuses existing artifacts whenever possible, so it avoids expensive reruns of Stage4-Stage7.

## Structure

| Path | Purpose |
|---|---|
| `scripts/evaluate_stage1_performance.py` | Evaluation script for Stage1 performance. |
| `results/` | Generated metrics tables, plots, and markdown report. |

## Evaluation Dimensions

The script evaluates:

1. Distribution fit
2. Wind-PV joint relation
3. Time continuity
4. Extreme coverage
5. Downstream scheduling / resilience snapshot

## Reproduction

```powershell
python gridagent_final\stage1_performance\scripts\evaluate_stage1_performance.py
```
