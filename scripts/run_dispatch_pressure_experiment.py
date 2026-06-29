from __future__ import annotations

import argparse
import csv
import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "result_final" / "paper_experiment_outputs_rerun"
PKG_OUT = ROOT / "paper_submission_package" / "results" / "paper_experiments_rerun"
STAGE7 = ROOT / "gridagent_final" / "stage7"

BASE_GRID = STAGE7 / "inputs" / "grid_topology.ieee118_full.json"
BASE_TRIM = STAGE7 / "inputs" / "TRIM_input.guangdong2024.csv"
FAILURE = STAGE7 / "inputs" / "line_failure_timeseries_schloemer.csv"
UNCERTAINTY = STAGE7 / "inputs" / "stage1_formal_output"
PRIORITY = STAGE7 / "inputs" / "load_bus_priority_profile.csv"

RUN_ROOT = OUT / "stage7_dispatch_pressure_runs"
INPUT_ROOT = OUT / "dispatch_pressure_inputs"
LOG_ROOT = OUT / "logs_dispatch_pressure"


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def ensure_dirs() -> None:
    for path in [RUN_ROOT, INPUT_ROOT, LOG_ROOT, PKG_OUT]:
        path.mkdir(parents=True, exist_ok=True)


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    fields: list[str] = []
    for row in rows:
        for key in row:
            if key not in fields:
                fields.append(key)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def risk_level(x: float) -> str:
    if x >= 0.7:
        return "HIGH"
    if x >= 0.4:
        return "MEDIUM"
    return "LOW"


def build_pressure_grid(line_capacity: float) -> Path:
    payload = json.loads(BASE_GRID.read_text(encoding="utf-8"))
    for line in payload.get("lines", []):
        line["capacity_original"] = line.get("capacity")
        line["capacity"] = float(line_capacity)
    path = INPUT_ROOT / f"grid_pressure_linecap_{str(line_capacity).replace('.', 'p')}.json"
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path


def build_pressure_trim(load_scale: float) -> Path:
    df = pd.read_csv(BASE_TRIM)
    load_cols = [c for c in df.columns if c.startswith("load_")]
    for col in load_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0) * float(load_scale)
    path = INPUT_ROOT / f"TRIM_pressure_loadx_{str(load_scale).replace('.', 'p')}.csv"
    df.to_csv(path, index=False)
    return path


def build_zero_failure_timeline() -> Path:
    df = pd.read_csv(FAILURE)
    for col in ["p_line", "v_surface"]:
        if col in df.columns:
            df[col] = 0.0
    path = INPUT_ROOT / "line_failure_timeseries_zero_warning.csv"
    df.to_csv(path, index=False)
    return path


def build_prior_only() -> Path:
    df = pd.read_csv(FAILURE)
    ts = sorted(df["timestamp"].astype(str).unique())[24:48]
    h = df[df["timestamp"].astype(str).isin(ts)]
    scores = h.groupby("line_id")["p_line"].max().reset_index()
    scores = scores.rename(columns={"p_line": "risk_prob"})
    scores["risk_level"] = scores["risk_prob"].map(risk_level)
    scores["predicted_fail_hour"] = "-"
    scores = scores.sort_values("risk_prob", ascending=False)
    path = INPUT_ROOT / "failure_prior_only_line_risk_prediction.csv"
    scores.to_csv(path, index=False)
    return path


def build_from_ranking(model: str, out_name: str) -> Path:
    rank_path = OUT / "stage6_model_runs" / model / "line_ranking_validation.csv"
    df = pd.read_csv(rank_path)
    out = pd.DataFrame({"line_id": df["line_id"], "risk_prob": df["predicted_max_risk"]})
    out["risk_level"] = out["risk_prob"].map(risk_level)
    out["predicted_fail_hour"] = "-"
    out = out.sort_values("risk_prob", ascending=False)
    path = INPUT_ROOT / out_name
    out.to_csv(path, index=False)
    return path


def copy_warning_line(src: Path, out_name: str) -> Path:
    path = INPUT_ROOT / out_name
    pd.read_csv(src).to_csv(path, index=False)
    return path


def build_warning_inputs() -> dict[str, Path | None]:
    inputs: dict[str, Path | None] = {
        "no_warning": None,
        "failure_prior_only": build_prior_only(),
    }
    mlp_rank = OUT / "stage6_model_runs" / "mlp" / "line_ranking_validation.csv"
    if mlp_rank.exists():
        inputs["mlp_warning"] = build_from_ranking("mlp", "mlp_warning_line_risk_prediction.csv")
    gridagent_line = OUT / "stage6_ablation_runs" / "A3_full_training_enhanced_seed_42" / "line_risk_prediction.csv"
    if gridagent_line.exists():
        inputs["gridagent_risk_warning"] = copy_warning_line(
            gridagent_line,
            "gridagent_risk_warning_line_risk_prediction.csv",
        )
    baseline_line = OUT / "stage6_ablation_runs" / "A0_baseline_no_metapath_seed_42" / "line_risk_prediction.csv"
    if baseline_line.exists():
        inputs["baseline_gnn_warning"] = copy_warning_line(
            baseline_line,
            "baseline_gnn_warning_line_risk_prediction.csv",
        )
    return inputs


def run_dispatch(
    strategy: str,
    line_risk: Path | None,
    grid: Path,
    trim: Path,
    failure_csv: Path,
    args: argparse.Namespace,
) -> dict[str, Any]:
    out_dir = RUN_ROOT / args.scenario_name / strategy
    log_path = LOG_ROOT / f"{args.scenario_name}_{strategy}.log"
    cmd = [
        sys.executable,
        str(STAGE7 / "scripts" / "dispatch_optimization_module.py"),
        "--strategy-mode",
        "contextual",
        "--export-diagnostics",
        "--grid",
        str(grid),
        "--trim-input",
        str(trim),
        "--failure-csv",
        str(failure_csv),
        "--uncertainty-dir",
        str(UNCERTAINTY),
        "--load-priority-csv",
        str(PRIORITY),
        "--output-dir",
        str(out_dir),
        "--horizon-hours",
        "24",
        "--horizon-start-index",
        "24",
        "--reserve-ratio",
        str(args.reserve_ratio),
        "--line-derate-coeff",
        str(args.line_derate_coeff),
        "--robust-line-factor",
        str(args.robust_line_factor),
        "--robust-load-high",
        str(args.robust_load_high),
        "--robust-wind-low",
        str(args.robust_wind_low),
        "--time-limit-sec",
        str(args.time_limit_sec),
        "--seed",
        str(args.seed),
    ]
    if line_risk is not None:
        cmd.extend(["--line-risk-csv", str(line_risk)])
    start = time.time()
    with log_path.open("w", encoding="utf-8") as log:
        proc = subprocess.run(cmd, cwd=STAGE7, stdout=log, stderr=subprocess.STDOUT, text=True)
    return {
        "pressure_scenario": args.scenario_name,
        "warning_strategy": strategy,
        "returncode": proc.returncode,
        "runtime_sec": time.time() - start,
        "run_dir": rel(out_dir),
        "line_risk_csv": rel(line_risk) if line_risk else "",
        "failure_csv": rel(failure_csv),
        "log": rel(log_path),
    }


def collect_pressure_results(scenario_name: str) -> None:
    rows: list[dict[str, Any]] = []
    scenario_root = RUN_ROOT / scenario_name
    for run_dir in sorted(scenario_root.iterdir()):
        if not run_dir.is_dir():
            continue
        comp = run_dir / "dispatch_model_comparison.csv"
        if not comp.exists():
            continue
        df = pd.read_csv(comp)
        contextual = df[df["model"] == "Contextual_Adaptive"]
        if contextual.empty:
            contextual = df.head(1)
        r = contextual.iloc[0]
        rows.append(
            {
                "pressure_scenario": scenario_name,
                "warning_strategy": run_dir.name,
                "dispatch_cost": r["total_cost"],
                "eens": r["EENS"],
                "critical_load_supply_rate": r["critical_load_supply_rate"],
                "overload_count": r["overload_count"],
                "max_line_loading": r["max_line_loading"],
                "runtime_sec": r["runtime_sec"],
                "source": rel(comp),
            }
        )
    out = OUT / f"downstream_dispatch_pressure_{scenario_name}.csv"
    write_csv(out, rows)
    if rows:
        base = next((r for r in rows if r["warning_strategy"] == "no_warning"), rows[0])
        compare_rows = []
        for r in rows:
            compare_rows.append(
                {
                    **r,
                    "delta_eens_vs_no_warning": float(r["eens"]) - float(base["eens"]),
                    "delta_overload_vs_no_warning": int(r["overload_count"]) - int(base["overload_count"]),
                    "delta_critical_supply_vs_no_warning": float(r["critical_load_supply_rate"])
                    - float(base["critical_load_supply_rate"]),
                }
            )
        write_csv(OUT / f"downstream_dispatch_pressure_{scenario_name}_delta.csv", compare_rows)
    for path in OUT.glob(f"downstream_dispatch_pressure_{scenario_name}*.csv"):
        import shutil

        shutil.copy2(path, PKG_OUT / path.name)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Stage7 pressure scenario warning utility experiments.")
    parser.add_argument("--scenario-name", default="stress_load1p35_linecap0p75")
    parser.add_argument("--load-scale", type=float, default=1.35)
    parser.add_argument("--line-capacity", type=float, default=0.75)
    parser.add_argument("--reserve-ratio", type=float, default=0.10)
    parser.add_argument("--line-derate-coeff", type=float, default=0.80)
    parser.add_argument("--robust-line-factor", type=float, default=0.75)
    parser.add_argument("--robust-load-high", type=float, default=1.35)
    parser.add_argument("--robust-wind-low", type=float, default=0.55)
    parser.add_argument("--time-limit-sec", type=float, default=45.0)
    parser.add_argument("--seed", type=int, default=4042)
    parser.add_argument(
        "--strategies",
        default="no_warning,failure_prior_only,mlp_warning,gridagent_risk_warning,baseline_gnn_warning",
    )
    args = parser.parse_args()

    ensure_dirs()
    grid = build_pressure_grid(args.line_capacity)
    trim = build_pressure_trim(args.load_scale)
    zero_failure = build_zero_failure_timeline()
    inputs = build_warning_inputs()
    requested = [s.strip() for s in str(args.strategies).split(",") if s.strip()]

    manifest = {
        "started_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "pressure_scenario": args.scenario_name,
        "parameters": {
            "load_scale": float(args.load_scale),
            "line_capacity": float(args.line_capacity),
            "reserve_ratio": float(args.reserve_ratio),
            "line_derate_coeff": float(args.line_derate_coeff),
            "robust_line_factor": float(args.robust_line_factor),
            "robust_load_high": float(args.robust_load_high),
            "robust_wind_low": float(args.robust_wind_low),
        },
        "inputs": {"grid": rel(grid), "trim": rel(trim)},
        "runs": [],
    }
    for strategy in requested:
        if strategy not in inputs:
            continue
        failure_csv = zero_failure if strategy == "no_warning" else FAILURE
        info = run_dispatch(strategy, inputs[strategy], grid, trim, failure_csv, args)
        manifest["runs"].append(info)
        manifest_path = OUT / f"dispatch_pressure_manifest_{args.scenario_name}.json"
        manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        if info["returncode"] != 0:
            raise SystemExit(info["returncode"])
    manifest["finished_at"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    manifest_path = OUT / f"dispatch_pressure_manifest_{args.scenario_name}.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    import shutil

    shutil.copy2(manifest_path, PKG_OUT / manifest_path.name)
    collect_pressure_results(args.scenario_name)


if __name__ == "__main__":
    main()
