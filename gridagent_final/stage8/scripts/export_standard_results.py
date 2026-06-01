from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


def project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def copy_csv(src: Path, dst: Path) -> None:
    df = pd.read_csv(src)
    df.to_csv(dst, index=False, encoding="utf-8")


def build_generation_schedule(unit_df: pd.DataFrame) -> pd.DataFrame:
    power_col = "p_selected" if "p_selected" in unit_df.columns else ("p" if "p" in unit_df.columns else "p_base")
    out = (
        unit_df.pivot_table(index="timestamp", columns="unit_id", values=power_col, aggfunc="sum")
        .sort_index()
        .reset_index()
    )
    out.columns = [str(c) for c in out.columns]
    return out


def build_reserve_schedule(unit_df: pd.DataFrame) -> pd.DataFrame:
    reserve_up = unit_df.groupby("timestamp", as_index=False)["reserve"].sum()
    reserve_up = reserve_up.rename(columns={"reserve": "reserve_up"})
    reserve_up["reserve_down"] = 0.0
    return reserve_up[["timestamp", "reserve_up", "reserve_down"]]


def build_load_shedding(load_df: pd.DataFrame) -> pd.DataFrame:
    level_map = {1: "primary", 2: "secondary", 3: "tertiary"}
    out = load_df.copy()
    out["node"] = out["load_bus"].apply(lambda x: f"load_bus_{int(x)}")
    out["load_type"] = out["priority_level"].map(level_map).fillna("tertiary")
    out["shed_MW"] = out["shed"].astype(float)
    return out[["timestamp", "node", "load_type", "shed_MW"]]


def build_wind_solar_scenarios(wind_df: pd.DataFrame) -> pd.DataFrame:
    ts = pd.DataFrame({"timestamp": sorted(wind_df["timestamp"].astype(str).unique())})
    wind_w = wind_df.pivot_table(index="timestamp", columns="scenario_id", values="wind", aggfunc="mean").reset_index()
    pv_w = wind_df.pivot_table(index="timestamp", columns="scenario_id", values="pv", aggfunc="mean").reset_index()
    wind_w.columns = ["timestamp"] + [f"wind_s{int(c)}" for c in wind_w.columns[1:]]
    pv_w.columns = ["timestamp"] + [f"solar_s{int(c)}" for c in pv_w.columns[1:]]
    out = ts.merge(wind_w, on="timestamp", how="left").merge(pv_w, on="timestamp", how="left")
    return out.sort_values("timestamp").reset_index(drop=True)


def build_component_failure(failure_df: pd.DataFrame) -> pd.DataFrame:
    out = failure_df.copy()
    out = out.rename(columns={"line_id": "line", "timestamp": "hour", "p_line": "failure_prob"})
    cols = ["line", "hour", "failure_prob"]
    return out[cols]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export GridAgent run results into standardized results/* structure.")
    parser.add_argument("--run-root", required=True, help="GridAgent framework run root.")
    parser.add_argument("--output-root", default="results", help="Output root directory.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    root = project_root()
    run_root = (root / args.run_root).resolve()
    output_root = (root / args.output_root).resolve()

    report_path = run_root / "framework_report.json"
    if not report_path.exists():
        raise FileNotFoundError(f"missing framework report: {report_path}")

    report = read_json(report_path)
    details = report.get("details", {})
    outputs = details.get("outputs", {})

    summary_dir = ensure_dir(output_root / "summary")
    warning_dir = ensure_dir(output_root / "warning")
    dispatch_dir = ensure_dir(output_root / "dispatch")
    resilience_dir = ensure_dir(output_root / "resilience")
    scenario_dir = ensure_dir(output_root / "scenario")

    # warning/
    copy_csv(Path(outputs["line_risk_prediction_csv"]), warning_dir / "line_risk_prediction.csv")
    copy_csv(Path(outputs["nk_failure_risk_csv"]), warning_dir / "nk_failure_risk.csv")
    copy_csv(Path(outputs["critical_load_risk_csv"]), warning_dir / "critical_load_risk.csv")

    # dispatch/
    unit_sched = pd.read_csv(Path(outputs["contextual_dispatch_unit_schedule_csv"]))
    load_sched = pd.read_csv(Path(outputs["contextual_dispatch_load_shedding_csv"]))
    build_generation_schedule(unit_sched).to_csv(dispatch_dir / "generation_schedule.csv", index=False, encoding="utf-8")
    build_reserve_schedule(unit_sched).to_csv(dispatch_dir / "reserve_schedule.csv", index=False, encoding="utf-8")
    build_load_shedding(load_sched).to_csv(dispatch_dir / "load_shedding.csv", index=False, encoding="utf-8")
    copy_csv(Path(outputs["dispatch_line_flow_csv"]), dispatch_dir / "line_flow.csv")

    # resilience/
    indicator_src = Path(outputs.get("assessment_dir", outputs.get("best_assessment_dir", ""))) / "indicator_table.csv"
    if not indicator_src.exists():
        raise FileNotFoundError(f"missing indicator table: {indicator_src}")
    indicator_df = pd.read_csv(indicator_src)
    indicator_df[["policy", "Priority", "Robustness", "Rapidity", "Sustainability"]].to_csv(
        resilience_dir / "resilience_metrics.csv", index=False, encoding="utf-8"
    )

    topsis_src = Path(outputs.get("assessment_topsis_csv", outputs.get("best_assessment_topsis_csv", "")))
    topsis_df = pd.read_csv(topsis_src).rename(columns={"TOPSIS_Score": "score", "TOPSIS_Rank": "rank"})
    keep_cols = [c for c in ["policy", "score", "rank"] if c in topsis_df.columns]
    topsis_df[keep_cols].to_csv(resilience_dir / "topsis_ranking.csv", index=False, encoding="utf-8")

    # scenario/
    wind_solar_src = Path(outputs["uncertainty_dir"]) / "typical_scenarios_long.csv"
    wind_df = pd.read_csv(wind_solar_src)
    build_wind_solar_scenarios(wind_df).to_csv(scenario_dir / "wind_solar_scenarios.csv", index=False, encoding="utf-8")

    failure_src = Path(outputs["failure_csv"])
    failure_df = pd.read_csv(failure_src)
    build_component_failure(failure_df).to_csv(scenario_dir / "component_failure_prob.csv", index=False, encoding="utf-8")

    contingency_src = Path(outputs["contingency_scenarios_csv"])
    copy_csv(contingency_src, scenario_dir / "contingency_scenarios.csv")

    # summary/
    indicator_df.to_csv(summary_dir / "indicator_table.csv", index=False, encoding="utf-8")
    quick_summary = {
        "framework": report.get("framework"),
        "mode": report.get("mode"),
        "run_root": str(run_root),
        "timestamp": report.get("timestamp"),
        "selected_chain": details.get("selected_chain"),
        "best_candidate": details.get("best_candidate"),
        "standard_outputs": {
            "summary": str(summary_dir),
            "warning": str(warning_dir),
            "dispatch": str(dispatch_dir),
            "resilience": str(resilience_dir),
            "scenario": str(scenario_dir),
        },
    }
    (summary_dir / "experiment_summary.json").write_text(json.dumps(quick_summary, ensure_ascii=False, indent=2), encoding="utf-8")

    print("Done.")
    print(f"run_root -> {run_root}")
    print(f"standard_root -> {output_root}")


if __name__ == "__main__":
    main()
