from __future__ import annotations

import argparse
import itertools
import json
import math
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd


def project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def parse_int_list(raw: str) -> list[int]:
    vals = [x.strip() for x in str(raw).split(",") if x.strip()]
    if not vals:
        raise ValueError("empty integer list")
    return [int(v) for v in vals]


def parse_float_list(raw: str) -> list[float]:
    vals = [x.strip() for x in str(raw).split(",") if x.strip()]
    if not vals:
        raise ValueError("empty float list")
    return [float(v) for v in vals]


def run_cmd(cmd: list[str], cwd: Path, log_path: Path, dry_run: bool) -> int:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    if dry_run:
        log_path.write_text("DRY RUN\n" + " ".join(cmd) + "\n", encoding="utf-8")
        print("[dry-run]", " ".join(cmd))
        return 0

    print(">>", " ".join(cmd))
    proc = subprocess.run(cmd, cwd=str(cwd), text=True, capture_output=True, check=False)
    content = []
    content.append("CMD: " + " ".join(cmd))
    content.append("")
    content.append("STDOUT:")
    content.append(proc.stdout or "")
    content.append("")
    content.append("STDERR:")
    content.append(proc.stderr or "")
    content.append("")
    content.append(f"RETURNCODE: {proc.returncode}")
    log_path.write_text("\n".join(content), encoding="utf-8")
    return int(proc.returncode)


def can_import_warning_deps(python_exe: str) -> bool:
    probe = [
        python_exe,
        "-c",
        "import numpy,pandas,networkx,torch; print('ok')",
    ]
    proc = subprocess.run(probe, text=True, capture_output=True, check=False)
    return int(proc.returncode) == 0


def pick_python_exe(user_input: str) -> str:
    preferred = str(user_input).strip()
    if preferred:
        return preferred
    candidates = [sys.executable, "python"]
    for exe in candidates:
        if can_import_warning_deps(exe):
            return exe
    raise RuntimeError(
        "No usable Python interpreter found for warning experiments. "
        "Please install numpy/pandas/networkx/torch in your active environment, "
        "or pass --python-exe explicitly."
    )


def safe_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def pick_metric(df: pd.DataFrame, model: str, col: str) -> float:
    if df.empty or "model" not in df.columns or col not in df.columns:
        return math.nan
    row = df[df["model"].astype(str) == str(model)]
    if row.empty:
        return math.nan
    val = pd.to_numeric(row.iloc[0][col], errors="coerce")
    return float(val) if pd.notna(val) else math.nan


def aggregate_rows(df: pd.DataFrame, out_dir: Path) -> None:
    if df.empty:
        return
    group_cols = ["metapath_topk", "hidden_dim", "epochs", "lr", "weight_decay", "train_ratio"]
    stat_df = (
        df.groupby(group_cols, dropna=False, as_index=False)
        .agg(
            runs=("run_name", "count"),
            success_runs=("status", lambda s: int((s == "ok").sum())),
            delta_val_mae_mean=("delta_val_mae", "mean"),
            delta_val_mae_std=("delta_val_mae", "std"),
            delta_horizon_mae_mean=("delta_horizon_mae", "mean"),
            delta_horizon_mae_std=("delta_horizon_mae", "std"),
            delta_best_val_mse_mean=("delta_best_val_mse", "mean"),
            delta_best_val_mse_std=("delta_best_val_mse", "std"),
            metapath_val_mae_mean=("metapath_val_mae", "mean"),
            baseline_val_mae_mean=("baseline_val_mae", "mean"),
            metapath_horizon_mae_mean=("metapath_horizon_mae", "mean"),
            baseline_horizon_mae_mean=("baseline_horizon_mae", "mean"),
        )
    )
    stat_df["val_mae_win_rate"] = (
        df.groupby(group_cols, dropna=False)["delta_val_mae"].apply(lambda s: float((pd.to_numeric(s, errors="coerce") > 0).mean())).reset_index(drop=True)
    )
    stat_df["horizon_mae_win_rate"] = (
        df.groupby(group_cols, dropna=False)["delta_horizon_mae"].apply(lambda s: float((pd.to_numeric(s, errors="coerce") > 0).mean())).reset_index(drop=True)
    )
    stat_df = stat_df.sort_values(["delta_val_mae_mean", "delta_horizon_mae_mean"], ascending=[False, False]).reset_index(drop=True)
    stat_df.to_csv(out_dir / "summary_by_setting.csv", index=False, encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Scale-out experiments for MetaPath warning module.")
    parser.add_argument("--grid", default="data_final/formal_guangdong_2024/grid_topology.json")
    parser.add_argument("--aligned", default="data_final/formal_guangdong_2024/aligned_merged.csv")
    parser.add_argument("--failure-csv", default="results/component_failure_probability/formal2024/line_failure_timeseries_schloemer.csv")
    parser.add_argument("--contingency-tensor", default="results/spatiotemporal_contingency/formal2024_schloemer72h/contingency_tensor_wang_qmc.npy")
    parser.add_argument("--load-priority-csv", default="results/load_prioritization_scheduling/formal2024/load_bus_priority_profile.csv")
    parser.add_argument("--output-root", default="results/early_warning")
    parser.add_argument("--tag", default="metapath_scale")
    parser.add_argument("--python-exe", default="", help="Python executable for invoking gnn_warning_module.py. Empty means auto-detect.")
    parser.add_argument("--seeds", default="42,43,44,45,46")
    parser.add_argument("--metapath-topk-list", default="3,4,5")
    parser.add_argument("--hidden-dim-list", default="64,80,96")
    parser.add_argument("--epochs-list", default="700,900")
    parser.add_argument("--lr-list", default="0.006,0.005")
    parser.add_argument("--weight-decay-list", default="0.0001")
    parser.add_argument("--train-ratio-list", default="0.7")
    parser.add_argument("--risk-weight-alpha", type=float, default=2.0)
    parser.add_argument("--risk-weight-beta", type=float, default=4.0)
    parser.add_argument("--risk-weight-threshold", type=float, default=0.10)
    parser.add_argument("--risk-weight-on-metapath-only", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--metapath-gate-reg-lambda", type=float, default=8e-4)
    parser.add_argument("--metapath-attention-entropy-reg-lambda", type=float, default=0.0)
    parser.add_argument("--metapath-warmup-epochs", type=int, default=35)
    parser.add_argument("--high-risk-threshold", type=float, default=0.10)
    parser.add_argument("--top-risk-quantile", type=float, default=0.90)
    parser.add_argument("--horizon-hours", type=int, default=24)
    parser.add_argument("--horizon-start-index", type=int, default=0)
    parser.add_argument("--mc-scenarios", type=int, default=3000)
    parser.add_argument("--risk-high-threshold", type=float, default=0.70)
    parser.add_argument("--risk-medium-threshold", type=float, default=0.40)
    parser.add_argument("--hour-trigger-threshold", type=float, default=0.35)
    parser.add_argument("--risk-mean-floor", type=float, default=0.18)
    parser.add_argument("--risk-mean-cap", type=float, default=0.55)
    parser.add_argument("--scenario-intensity-alpha", type=float, default=2.0)
    parser.add_argument("--scenario-intensity-beta", type=float, default=6.0)
    parser.add_argument("--metapath-v1-enabled", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--run-baseline-comparison", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--reuse-existing", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--max-runs", type=int, default=0, help="Limit total run count. 0 means no limit.")
    parser.add_argument("--dry-run", action=argparse.BooleanOptionalAction, default=False)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    root = project_root()
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    exp_dir = (root / args.output_root / f"{args.tag}_{ts}").resolve()
    exp_dir.mkdir(parents=True, exist_ok=True)
    python_exe = pick_python_exe(args.python_exe)

    seeds = parse_int_list(args.seeds)
    k_list = parse_int_list(args.metapath_topk_list)
    h_list = parse_int_list(args.hidden_dim_list)
    ep_list = parse_int_list(args.epochs_list)
    lr_list = parse_float_list(args.lr_list)
    wd_list = parse_float_list(args.weight_decay_list)
    tr_list = parse_float_list(args.train_ratio_list)

    grid = (root / args.grid).resolve()
    aligned = (root / args.aligned).resolve()
    failure_csv = (root / args.failure_csv).resolve()
    contingency_tensor = (root / args.contingency_tensor).resolve()
    load_priority_csv = (root / args.load_priority_csv).resolve()

    run_items: list[dict[str, Any]] = []
    combinations = list(itertools.product(k_list, h_list, ep_list, lr_list, wd_list, tr_list, seeds))
    if args.max_runs > 0:
        combinations = combinations[: int(args.max_runs)]

    print(f"experiment_dir={exp_dir}")
    print(f"total_runs={len(combinations)}")
    print(f"python_exe={python_exe}")
    config_manifest = {
        "python_exe": python_exe,
        "seeds": seeds,
        "metapath_topk_list": k_list,
        "hidden_dim_list": h_list,
        "epochs_list": ep_list,
        "lr_list": lr_list,
        "weight_decay_list": wd_list,
        "train_ratio_list": tr_list,
        "risk_weight_alpha": float(args.risk_weight_alpha),
        "risk_weight_beta": float(args.risk_weight_beta),
        "risk_weight_threshold": float(args.risk_weight_threshold),
        "risk_weight_on_metapath_only": bool(args.risk_weight_on_metapath_only),
        "metapath_gate_reg_lambda": float(args.metapath_gate_reg_lambda),
        "metapath_attention_entropy_reg_lambda": float(args.metapath_attention_entropy_reg_lambda),
        "metapath_warmup_epochs": int(args.metapath_warmup_epochs),
        "high_risk_threshold": float(args.high_risk_threshold),
        "top_risk_quantile": float(args.top_risk_quantile),
        "horizon_hours": int(args.horizon_hours),
        "horizon_start_index": int(args.horizon_start_index),
        "mc_scenarios": int(args.mc_scenarios),
        "metapath_v1_enabled": bool(args.metapath_v1_enabled),
        "run_baseline_comparison": bool(args.run_baseline_comparison),
        "reuse_existing": bool(args.reuse_existing),
        "dry_run": bool(args.dry_run),
        "max_runs": int(args.max_runs),
    }
    (exp_dir / "experiment_config.json").write_text(json.dumps(config_manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    for idx, (topk, hidden_dim, epochs, lr, weight_decay, train_ratio, seed) in enumerate(combinations, start=1):
        run_name = (
            f"r{idx:03d}_k{int(topk)}_h{int(hidden_dim)}_ep{int(epochs)}"
            f"_lr{float(lr):.6g}_wd{float(weight_decay):.6g}_tr{float(train_ratio):.3f}_s{int(seed)}"
        )
        run_dir = exp_dir / run_name
        run_dir.mkdir(parents=True, exist_ok=True)

        report_path = run_dir / "warning_report.json"
        cmp_path = run_dir / "model_comparison.csv"
        log_path = run_dir / "train.log"

        status = "ok"
        return_code = 0
        skipped = False
        if args.reuse_existing and report_path.exists():
            skipped = True
            print(f"[skip-existing] {run_name}")
        else:
            cmd = [
                python_exe,
                str(root / "scripts" / "gnn_warning_module.py"),
                "--grid",
                str(grid),
                "--aligned",
                str(aligned),
                "--failure-csv",
                str(failure_csv),
                "--contingency-tensor",
                str(contingency_tensor),
                "--load-priority-csv",
                str(load_priority_csv),
                "--output-dir",
                str(run_dir),
                "--horizon-hours",
                str(int(args.horizon_hours)),
                "--horizon-start-index",
                str(int(args.horizon_start_index)),
                "--train-ratio",
                str(float(train_ratio)),
                "--hidden-dim",
                str(int(hidden_dim)),
                "--epochs",
                str(int(epochs)),
                "--lr",
                str(float(lr)),
                "--weight-decay",
                str(float(weight_decay)),
                "--risk-weight-alpha",
                str(float(args.risk_weight_alpha)),
                "--risk-weight-beta",
                str(float(args.risk_weight_beta)),
                "--risk-weight-threshold",
                str(float(args.risk_weight_threshold)),
                "--metapath-gate-reg-lambda",
                str(float(args.metapath_gate_reg_lambda)),
                "--metapath-attention-entropy-reg-lambda",
                str(float(args.metapath_attention_entropy_reg_lambda)),
                "--metapath-warmup-epochs",
                str(int(args.metapath_warmup_epochs)),
                "--high-risk-threshold",
                str(float(args.high_risk_threshold)),
                "--top-risk-quantile",
                str(float(args.top_risk_quantile)),
                "--mc-scenarios",
                str(int(args.mc_scenarios)),
                "--risk-high-threshold",
                str(float(args.risk_high_threshold)),
                "--risk-medium-threshold",
                str(float(args.risk_medium_threshold)),
                "--hour-trigger-threshold",
                str(float(args.hour_trigger_threshold)),
                "--risk-mean-floor",
                str(float(args.risk_mean_floor)),
                "--risk-mean-cap",
                str(float(args.risk_mean_cap)),
                "--scenario-intensity-alpha",
                str(float(args.scenario_intensity_alpha)),
                "--scenario-intensity-beta",
                str(float(args.scenario_intensity_beta)),
                "--metapath-topk",
                str(int(topk)),
                "--seed",
                str(int(seed)),
            ]
            if bool(args.metapath_v1_enabled):
                cmd.append("--metapath-v1-enabled")
            else:
                cmd.append("--no-metapath-v1-enabled")
            if bool(args.risk_weight_on_metapath_only):
                cmd.append("--risk-weight-on-metapath-only")
            else:
                cmd.append("--no-risk-weight-on-metapath-only")
            if bool(args.run_baseline_comparison):
                cmd.append("--run-baseline-comparison")
            else:
                cmd.append("--no-run-baseline-comparison")

            return_code = run_cmd(cmd=cmd, cwd=root, log_path=log_path, dry_run=bool(args.dry_run))
            if return_code != 0:
                status = "failed"

        report = safe_json(report_path)
        train = report.get("training", {}) if isinstance(report, dict) else {}
        val_metrics = train.get("val_metrics", {}) if isinstance(train, dict) else {}

        comparison_df = pd.read_csv(cmp_path) if cmp_path.exists() else pd.DataFrame()
        metapath_val_mae = pick_metric(comparison_df, "metapath_v1", "val_mae")
        baseline_val_mae = pick_metric(comparison_df, "baseline_gnn", "val_mae")
        metapath_horizon_mae = pick_metric(comparison_df, "metapath_v1", "horizon_mae")
        baseline_horizon_mae = pick_metric(comparison_df, "baseline_gnn", "horizon_mae")
        metapath_best_val_mse = pick_metric(comparison_df, "metapath_v1", "best_val_mse")
        baseline_best_val_mse = pick_metric(comparison_df, "baseline_gnn", "best_val_mse")

        row = {
            "run_name": run_name,
            "run_dir": str(run_dir),
            "status": status,
            "return_code": int(return_code),
            "skipped": bool(skipped),
            "metapath_topk": int(topk),
            "hidden_dim": int(hidden_dim),
            "epochs": int(epochs),
            "lr": float(lr),
            "weight_decay": float(weight_decay),
            "train_ratio": float(train_ratio),
            "seed": int(seed),
            "train_model_variant": train.get("model_variant"),
            "train_best_val_mse": train.get("best_val_mse"),
            "train_val_mae": val_metrics.get("mae") if isinstance(val_metrics, dict) else math.nan,
            "metapath_gate_mean": train.get("metapath_gate_mean"),
            "metapath_val_mae": metapath_val_mae,
            "baseline_val_mae": baseline_val_mae,
            "metapath_horizon_mae": metapath_horizon_mae,
            "baseline_horizon_mae": baseline_horizon_mae,
            "metapath_best_val_mse": metapath_best_val_mse,
            "baseline_best_val_mse": baseline_best_val_mse,
            "delta_val_mae": baseline_val_mae - metapath_val_mae if pd.notna(baseline_val_mae) and pd.notna(metapath_val_mae) else math.nan,
            "delta_horizon_mae": baseline_horizon_mae - metapath_horizon_mae if pd.notna(baseline_horizon_mae) and pd.notna(metapath_horizon_mae) else math.nan,
            "delta_best_val_mse": baseline_best_val_mse - metapath_best_val_mse if pd.notna(baseline_best_val_mse) and pd.notna(metapath_best_val_mse) else math.nan,
        }
        run_items.append(row)

        pd.DataFrame(run_items).to_csv(exp_dir / "all_runs.csv", index=False, encoding="utf-8")
        print(f"[{idx}/{len(combinations)}] {run_name} status={status}")

    all_df = pd.DataFrame(run_items)
    all_df.to_csv(exp_dir / "all_runs.csv", index=False, encoding="utf-8")
    aggregate_rows(all_df, exp_dir)

    done = {
        "python_exe": python_exe,
        "experiment_dir": str(exp_dir),
        "all_runs_csv": str(exp_dir / "all_runs.csv"),
        "summary_by_setting_csv": str(exp_dir / "summary_by_setting.csv"),
        "run_count": int(len(run_items)),
        "success_count": int((all_df["status"] == "ok").sum()) if not all_df.empty else 0,
    }
    (exp_dir / "done.json").write_text(json.dumps(done, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(done, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
