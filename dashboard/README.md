# GridAgent1 Visual Dashboard (Streamlit)

## 1. Install

```powershell
pip install -r dashboard/requirements-visualization.txt
```

## 2. Run

```powershell
streamlit run dashboard/gridagent_dashboard.py
```

## 3. What It Includes

- 9 pages:
  - `Overview`
  - `Pipeline View`
  - `Scenario & Failure`
  - `Warning`
  - `Node Weather`
  - `MetaPath`
  - `Dispatch`
  - `Resilience`
  - `Export`
- Global filters in sidebar:
  - scenario
  - policy
  - 24h dispatch hour
  - 72h typhoon hour
  - risk threshold
  - Top-K

## 4. Data Source Priority

1. Standardized run package:
   - `results/*_standard`
2. Framework stagewise run package:
   - `results/gridagent_framework/*`
3. Extra stage-level data (if available):
   - `run_root/stage6_warning/*`
   - `run_root/stage7_dispatch_optimization/*`
   - `run_root/stage5_assessment/*`

The default run is:

`formal2024_full_baseline_20260310_233109_standard`
