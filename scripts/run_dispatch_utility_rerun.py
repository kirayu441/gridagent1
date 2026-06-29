from __future__ import annotations

import csv
import json
import subprocess
import sys
import time
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "result_final" / "paper_experiment_outputs_rerun"
PKG_OUT = ROOT / "paper_submission_package" / "results" / "paper_experiments_rerun"
RUN_ROOT = OUT / "stage7_dispatch_warning_runs"
INPUT_ROOT = OUT / "dispatch_warning_inputs"
LOG_ROOT = OUT / "logs_dispatch"

STAGE7 = ROOT / "gridagent_final" / "stage7"
GRID = STAGE7 / "inputs" / "grid_topology.ieee118_full.json"
TRIM = STAGE7 / "inputs" / "TRIM_input.guangdong2024.csv"
FAILURE = STAGE7 / "inputs" / "line_failure_timeseries_schloemer.csv"
UNCERTAINTY = STAGE7 / "inputs" / "stage1_formal_output"
PRIORITY = STAGE7 / "inputs" / "load_bus_priority_profile.csv"


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def ensure_dirs() -> None:
    RUN_ROOT.mkdir(parents=True, exist_ok=True)
    INPUT_ROOT.mkdir(parents=True, exist_ok=True)
    LOG_ROOT.mkdir(parents=True, exist_ok=True)
    PKG_OUT.mkdir(parents=True, exist_ok=True)


def risk_level(x: float) -> str:
    if x >= 0.7:
        return "HIGH"
    if x >= 0.4:
        return "MEDIUM"
    return "LOW"


def build_prior_only() -> Path:
    df = pd.read_csv(FAILURE)
    # Match the Stage7 horizon: rows 24:48 by timestamp.
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
    out = pd.DataFrame(
        {
            "line_id": df["line_id"],
            "risk_prob": df["predicted_max_risk"],
        }
    )
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
    prior = build_prior_only()
    mlp = build_from_ranking("mlp", "mlp_warning_line_risk_prediction.csv")
    baseline = copy_warning_line(
        OUT / "stage6_ablation_runs" / "A0_baseline_no_metapath_seed_42" / "line_risk_prediction.csv",
        "baseline_gnn_warning_line_risk_prediction.csv",
    )
    gridagent = copy_warning_line(
        OUT / "stage6_ablation_runs" / "A3_full_training_enhanced_seed_42" / "line_risk_prediction.csv",
        "gridagent_risk_warning_line_risk_prediction.csv",
    )
    return {
        "no_warning": None,
        "failure_prior_only": prior,
        "mlp_warning": mlp,
        "baseline_gnn_warning": baseline,
        "gridagent_risk_warning": gridagent,
    }


def run_dispatch(strategy: str, line_risk: Path | None) -> dict:
    out_dir = RUN_ROOT / strategy
    log_path = LOG_ROOT / f"{strategy}.log"
    cmd = [
        sys.executable,
        str(STAGE7 / "scripts" / "dispatch_optimization_module.py"),
        "--strategy-mode",
        "contextual",
        "--export-diagnostics",
        "--grid",
        str(GRID),
        "--trim-input",
        str(TRIM),
        "--failure-csv",
        str(FAILURE),
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
        "--seed",
        "3042",
    ]
    if line_risk is not None:
        cmd.extend(["--line-risk-csv", str(line_risk)])
    start = time.time()
    with log_path.open("w", encoding="utf-8") as log:
        proc = subprocess.run(cmd, cwd=STAGE7, stdout=log, stderr=subprocess.STDOUT, text=True)
    return {
        "warning_strategy": strategy,
        "returncode": proc.returncode,
        "runtime_sec": time.time() - start,
        "run_dir": rel(out_dir),
        "line_risk_csv": rel(line_risk) if line_risk else "",
        "log": rel(log_path),
    }


def write_csv(path: Path, rows: list[dict]) -> None:
    fields: list[str] = []
    for row in rows:
        for key in row:
            if key not in fields:
                fields.append(key)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def collect_dispatch() -> None:
    rows = []
    for run_dir in sorted(RUN_ROOT.iterdir()):
        if not run_dir.is_dir():
            continue
        strategy = run_dir.name
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
                "warning_strategy": strategy,
                "dispatch_cost": r["total_cost"],
                "eens": r["EENS"],
                "critical_load_supply_rate": r["critical_load_supply_rate"],
                "overload_count": r["overload_count"],
                "max_line_loading": r["max_line_loading"],
                "runtime_sec": r["runtime_sec"],
                "source": rel(comp),
            }
        )
    write_csv(OUT / "downstream_dispatch_utility.csv", rows)

    # Also expose multi-window strategy selections from each dispatch run.
    multi_rows = []
    for run_dir in sorted(RUN_ROOT.iterdir()):
        sel = run_dir / "dispatch_strategy_selection.csv"
        if not sel.exists():
            continue
        df = pd.read_csv(sel)
        for _, r in df.iterrows():
            multi_rows.append(
                {
                    "warning_strategy": run_dir.name,
                    "timestamp": r.get("timestamp", ""),
                    "selected_strategy": r.get("selected_strategy", ""),
                    "hourly_line_risk": r.get("hourly_line_risk", ""),
                    "hourly_uncertainty": r.get("hourly_uncertainty", ""),
                    "reason": r.get("reason", ""),
                    "source": rel(sel),
                }
            )
    write_csv(OUT / "multi_window_evaluation.csv", multi_rows)


def sync_outputs() -> None:
    import shutil

    for path in [OUT / "downstream_dispatch_utility.csv", OUT / "multi_window_evaluation.csv"]:
        if path.exists():
            shutil.copy2(path, PKG_OUT / path.name)


def main() -> None:
    ensure_dirs()
    inputs = build_warning_inputs()
    manifest = {"started_at": time.strftime("%Y-%m-%dT%H:%M:%S"), "runs": []}
    for strategy, line_risk in inputs.items():
        info = run_dispatch(strategy, line_risk)
        manifest["runs"].append(info)
        (OUT / "dispatch_run_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        if info["returncode"] != 0:
            raise SystemExit(info["returncode"])
    manifest["finished_at"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    (OUT / "dispatch_run_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    collect_dispatch()
    sync_outputs()


if __name__ == "__main__":
    main()
