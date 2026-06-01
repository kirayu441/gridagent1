from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


def project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def ensure_columns(df: pd.DataFrame, required: list[str], path: Path) -> None:
    miss = [c for c in required if c not in df.columns]
    if miss:
        raise ValueError(f"missing columns in {path}: {miss}")


def calc_priority_indicator(policy_row: pd.Series) -> float:
    v = float(policy_row.get("critical_served_ratio", np.nan))
    if np.isnan(v):
        return 0.0
    return float(np.clip(v, 0.0, 1.0))


def calc_robustness_indicator(policy_row: pd.Series) -> float:
    v = float(policy_row.get("rr", np.nan))
    if np.isnan(v):
        return 0.0
    return float(np.clip(v, 0.0, 1.0))


def calc_time_series_indicators(worst_df: pd.DataFrame) -> tuple[float, float]:
    # Based on worst-scenario load shedding trajectory.
    # Robustness captures peak impact resistance, sustainability captures average service level.
    by_t = worst_df.groupby("timestamp", as_index=False).agg(
        demand_total=("demand", "sum"),
        shed_total=("shed", "sum"),
    )
    by_t = by_t.sort_values("timestamp")
    demand = by_t["demand_total"].to_numpy(dtype=float)
    shed = by_t["shed_total"].to_numpy(dtype=float)
    with np.errstate(divide="ignore", invalid="ignore"):
        shed_ratio = np.divide(shed, demand, out=np.zeros_like(shed), where=demand > 1e-12)
    shed_ratio = np.clip(shed_ratio, 0.0, 1.0)
    sustainability = float(np.clip(1.0 - float(shed_ratio.mean()), 0.0, 1.0))
    peak = float(shed_ratio.max(initial=0.0))

    peak_idx = int(np.argmax(shed_ratio)) if len(shed_ratio) > 0 else 0
    if peak <= 1e-9 or len(shed_ratio) <= 1:
        rapidity = 1.0
    else:
        target = 0.20 * peak
        rec_idx = None
        for i in range(peak_idx, len(shed_ratio)):
            if shed_ratio[i] <= target:
                rec_idx = i
                break
        if rec_idx is None:
            # no recovery observed in horizon
            rec_hours = float(len(shed_ratio))
        else:
            rec_hours = float(rec_idx - peak_idx)
        tau = max(len(shed_ratio) / 3.0, 1.0)
        rapidity = float(np.exp(-rec_hours / tau))
    return sustainability, rapidity


def minmax_forward(matrix: np.ndarray, benefit_flags: np.ndarray) -> np.ndarray:
    x = np.array(matrix, dtype=float)
    out = np.zeros_like(x)
    for j in range(x.shape[1]):
        col = x[:, j]
        cmin = float(col.min())
        cmax = float(col.max())
        span = cmax - cmin
        if span < 1e-12:
            out[:, j] = 1.0
        elif benefit_flags[j]:
            out[:, j] = (col - cmin) / span
        else:
            out[:, j] = (cmax - col) / span
    return out


def ewm_topsis(matrix: np.ndarray, indicators: list[str], benefit_flags: list[bool]) -> dict[str, Any]:
    x = np.array(matrix, dtype=float)
    benefit = np.array(benefit_flags, dtype=bool)
    x_forward = minmax_forward(x, benefit)

    # Entropy weights
    p = x_forward / np.clip(x_forward.sum(axis=0, keepdims=True), 1e-12, None)
    n_case = x.shape[0]
    k = 1.0 / np.log(max(n_case, 2))
    safe_p = np.clip(p, 1e-12, 1.0)
    entropy = -k * np.sum(p * np.log(safe_p), axis=0)
    divergence = 1.0 - entropy
    if float(divergence.sum()) <= 1e-12:
        weights = np.full(x.shape[1], 1.0 / x.shape[1], dtype=float)
    else:
        weights = divergence / divergence.sum()

    # TOPSIS
    r = x_forward / np.clip(np.sqrt((x_forward**2).sum(axis=0, keepdims=True)), 1e-12, None)
    v = r * weights
    ideal_best = v.max(axis=0)
    ideal_worst = v.min(axis=0)
    d_plus = np.sqrt(((v - ideal_best) ** 2).sum(axis=1))
    d_minus = np.sqrt(((v - ideal_worst) ** 2).sum(axis=1))
    score = d_minus / np.clip(d_plus + d_minus, 1e-12, None)

    return {
        "weights": {indicators[i]: float(weights[i]) for i in range(len(indicators))},
        "score": score,
        "x_forward": x_forward,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Multi-criteria resilience assessment (Priority/Robustness/Rapidity/Sustainability) with EWM+TOPSIS."
    )
    parser.add_argument(
        "--policy-comparison",
        default="results/load_prioritization_scheduling/formal2024/policy_comparison.csv",
        help="Policy comparison csv from load prioritization stage.",
    )
    parser.add_argument(
        "--worst-detail",
        default="results/load_prioritization_scheduling/formal2024/worst_scenario_shedding_detail.csv",
        help="Worst scenario per-time shedding detail csv.",
    )
    parser.add_argument(
        "--output-dir",
        default="results/multi_criteria_resilience/formal2024",
        help="Output directory.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    root = project_root()
    policy_path = (root / args.policy_comparison).resolve()
    worst_path = (root / args.worst_detail).resolve()
    output_dir = (root / args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    policy_df = pd.read_csv(policy_path)
    worst_df = pd.read_csv(worst_path)
    ensure_columns(policy_df, ["policy", "rr", "critical_served_ratio"], policy_path)
    ensure_columns(worst_df, ["policy", "timestamp", "demand", "shed"], worst_path)

    indicator_rows: list[dict[str, Any]] = []
    for _, row in policy_df.iterrows():
        policy = str(row["policy"])
        block = worst_df[worst_df["policy"] == policy].copy()
        if block.empty:
            raise ValueError(f"policy {policy} not found in worst-detail table")
        sustainability, rapidity = calc_time_series_indicators(block)
        record = {
            "policy": policy,
            "Priority": calc_priority_indicator(row),
            "Robustness": calc_robustness_indicator(row),
            "Rapidity": rapidity,
            "Sustainability": sustainability,
        }
        indicator_rows.append(record)

    indicator_df = pd.DataFrame(indicator_rows)
    indicators = ["Priority", "Robustness", "Rapidity", "Sustainability"]
    matrix = indicator_df[indicators].to_numpy(dtype=float)
    benefit_flags = [True, True, True, True]

    topsis = ewm_topsis(matrix=matrix, indicators=indicators, benefit_flags=benefit_flags)
    indicator_df["TOPSIS_Score"] = topsis["score"]
    indicator_df = indicator_df.sort_values("TOPSIS_Score", ascending=False).reset_index(drop=True)
    indicator_df["TOPSIS_Rank"] = np.arange(1, len(indicator_df) + 1)

    # single-indicator rankings
    single_rows: list[dict[str, Any]] = []
    for ind in indicators:
        ranked = indicator_df[["policy", ind]].sort_values(ind, ascending=False).reset_index(drop=True)
        for i, r in ranked.iterrows():
            single_rows.append(
                {
                    "indicator": ind,
                    "rank": int(i + 1),
                    "policy": str(r["policy"]),
                    "value": float(r[ind]),
                }
            )
    single_df = pd.DataFrame(single_rows)

    # Output
    indicator_csv = output_dir / "indicator_table.csv"
    single_csv = output_dir / "single_indicator_ranking.csv"
    topsis_csv = output_dir / "ewm_topsis_result.csv"

    indicator_df.to_csv(indicator_csv, index=False, encoding="utf-8")
    single_df.to_csv(single_csv, index=False, encoding="utf-8")
    indicator_df[["policy", "TOPSIS_Score", "TOPSIS_Rank"]].to_csv(
        topsis_csv, index=False, encoding="utf-8"
    )

    report = {
        "input": {
            "policy_comparison_csv": str(policy_path),
            "worst_detail_csv": str(worst_path),
        },
        "indicator_definition": {
            "Priority": "critical_served_ratio (higher is better)",
            "Robustness": "Rr served-ratio metric from scheduling stage (higher is better)",
            "Rapidity": "exp(-recovery_time/tau) based on worst-scenario shedding trajectory",
            "Sustainability": "1 - mean(shed_ratio_t) over worst-scenario trajectory",
        },
        "ewm_weights": topsis["weights"],
        "output_files": {
            "indicator_table_csv": str(indicator_csv),
            "single_indicator_ranking_csv": str(single_csv),
            "ewm_topsis_result_csv": str(topsis_csv),
        },
    }
    report_path = output_dir / "multi_criteria_report.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    print("Done.")
    print(f"indicator table -> {indicator_csv}")
    print(f"single ranking -> {single_csv}")
    print(f"topsis result -> {topsis_csv}")
    print(f"report -> {report_path}")


if __name__ == "__main__":
    main()

