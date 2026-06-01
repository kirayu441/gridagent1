from __future__ import annotations

import argparse
import json
import math
import subprocess
import time
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd


@dataclass
class PlanACase:
    block: str
    case_id: str
    seed: int
    label_method: str
    model_group: str
    contingency_tensor: str
    metapath_v1_enabled: bool
    metapath_attention_mode: str
    metapath_topk: int
    hidden_dim: int
    epochs: int
    lr: float
    weight_decay: float
    train_ratio: float
    risk_weight_alpha: float
    risk_weight_beta: float
    risk_weight_threshold: float
    metapath_gate_reg_lambda: float
    metapath_attention_entropy_reg_lambda: float
    metapath_warmup_epochs: int


def project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def parse_int_list(v: str) -> list[int]:
    items = [x.strip() for x in str(v).split(",") if x.strip()]
    return [int(x) for x in items]


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Plan A: Stage6 strict experiment for A0/A1/A2/A3 under two label tensors."
    )
    p.add_argument("--grid", default="data_final/formal_guangdong_2024/grid_topology.json")
    p.add_argument("--aligned", default="data_final/formal_guangdong_2024/aligned_merged.csv")
    p.add_argument(
        "--failure-csv",
        default="results/component_failure_probability/formal2024/line_failure_timeseries_schloemer.csv",
    )
    p.add_argument(
        "--load-priority-csv",
        default="results/load_prioritization_scheduling/formal2024/load_bus_priority_profile.csv",
    )
    p.add_argument(
        "--c3po-tensor",
        default="results/spatiotemporal_contingency/formal2024_schloemer72h/contingency_tensor_c3po_ref.npy",
    )
    p.add_argument(
        "--wangqmc-tensor",
        default="results/spatiotemporal_contingency/formal2024_schloemer72h/contingency_tensor_wang_qmc.npy",
    )
    p.add_argument("--output-root", default="results/early_warning")
    p.add_argument("--tag", default="stage6_planA_full")
    p.add_argument("--resume-dir", default="")
    p.add_argument("--python-exe", default="")
    p.add_argument("--seeds", default="42,43,44,45,46")
    p.add_argument("--max-runs", type=int, default=0)
    p.add_argument("--reuse-existing", action=argparse.BooleanOptionalAction, default=True)
    p.add_argument("--dry-run", action=argparse.BooleanOptionalAction, default=False)

    p.add_argument("--horizon-hours", type=int, default=24)
    p.add_argument("--horizon-start-index", type=int, default=0)
    p.add_argument("--train-ratio", type=float, default=0.7)
    p.add_argument("--hidden-dim", type=int, default=80)
    p.add_argument("--epochs", type=int, default=700)
    p.add_argument("--mc-scenarios", type=int, default=3000)
    p.add_argument("--risk-high-threshold", type=float, default=0.7)
    p.add_argument("--risk-medium-threshold", type=float, default=0.4)
    p.add_argument("--hour-trigger-threshold", type=float, default=0.35)
    p.add_argument("--risk-mean-floor", type=float, default=0.18)
    p.add_argument("--risk-mean-cap", type=float, default=0.55)
    p.add_argument("--scenario-intensity-alpha", type=float, default=2.0)
    p.add_argument("--scenario-intensity-beta", type=float, default=6.0)
    p.add_argument("--high-risk-threshold", type=float, default=0.1)
    p.add_argument("--top-risk-quantile", type=float, default=0.9)

    # Neutral training setup for architecture-only comparison.
    p.add_argument("--lr", type=float, default=0.0042)
    p.add_argument("--weight-decay", type=float, default=0.00005)
    p.add_argument("--metapath-topk", type=int, default=4)
    p.add_argument("--risk-weight-threshold", type=float, default=0.1)
    return p.parse_args()


def pick_python_exe(python_exe: str) -> str:
    s = str(python_exe).strip()
    return s if s else "python"


def build_cases(args: argparse.Namespace, c3po: Path, wang: Path) -> list[PlanACase]:
    label_to_tensor = {
        "c3po_ref": str(c3po),
        "wang_qmc": str(wang),
    }
    model_groups = [
        ("A0_baseline", False, "fixed"),
        ("A1_metapath_fixed", True, "fixed"),
        ("A2_metapath_adaptive_global", True, "adaptive_global"),
        ("A3_metapath_adaptive_context", True, "adaptive_context"),
    ]
    seeds = parse_int_list(args.seeds)
    out: list[PlanACase] = []
    for seed in seeds:
        for label_method, tensor in label_to_tensor.items():
            for group_name, use_metapath, attention_mode in model_groups:
                case_id = f"A_label-{label_method}_group-{group_name}_seed-{seed}"
                out.append(
                    PlanACase(
                        block="A",
                        case_id=case_id,
                        seed=int(seed),
                        label_method=label_method,
                        model_group=group_name,
                        contingency_tensor=tensor,
                        metapath_v1_enabled=bool(use_metapath),
                        metapath_attention_mode=str(attention_mode),
                        metapath_topk=int(args.metapath_topk),
                        hidden_dim=int(args.hidden_dim),
                        epochs=int(args.epochs),
                        lr=float(args.lr),
                        weight_decay=float(args.weight_decay),
                        train_ratio=float(args.train_ratio),
                        risk_weight_alpha=0.0,
                        risk_weight_beta=0.0,
                        risk_weight_threshold=float(args.risk_weight_threshold),
                        metapath_gate_reg_lambda=0.0,
                        metapath_attention_entropy_reg_lambda=0.0,
                        metapath_warmup_epochs=0,
                    )
                )
    return out


def run_cmd(cmd: list[str], cwd: Path, log_path: Path, dry_run: bool) -> tuple[int, float]:
    if dry_run:
        log_path.write_text("DRY_RUN\n" + " ".join(cmd) + "\n", encoding="utf-8")
        return 0, 0.0
    t0 = time.perf_counter()
    proc = subprocess.run(cmd, cwd=str(cwd), text=True, capture_output=True)
    wall = time.perf_counter() - t0
    msg = (
        "CMD: " + " ".join(cmd) + "\n\n"
        + "STDOUT:\n" + (proc.stdout or "") + "\n\n"
        + "STDERR:\n" + (proc.stderr or "") + "\n\n"
        + f"RETURNCODE: {proc.returncode}\n"
        + f"WALL_SECONDS: {wall:.3f}\n"
    )
    log_path.write_text(msg, encoding="utf-8")
    return int(proc.returncode), float(wall)


def safe_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def model_metrics_from_report(report: dict[str, Any]) -> dict[str, float]:
    train = report.get("training", {}) if isinstance(report, dict) else {}
    fit = report.get("fit_quality", {}) if isinstance(report, dict) else {}
    val = fit.get("validation", {}) if isinstance(fit, dict) else {}
    obj = train.get("objective", {}) if isinstance(train, dict) else {}
    out = {
        "val_mae": float(val.get("mae", math.nan)) if val.get("mae") is not None else math.nan,
        "val_rmse": float(val.get("rmse", math.nan)) if val.get("rmse") is not None else math.nan,
        "val_high_risk_mae": float(val.get("high_risk_mae", math.nan))
        if val.get("high_risk_mae") is not None
        else math.nan,
        "best_val_mse": float(train.get("best_val_mse", math.nan)) if train.get("best_val_mse") is not None else math.nan,
        "metapath_gate_mean": float(train.get("metapath_gate_mean", math.nan))
        if train.get("metapath_gate_mean") is not None
        else math.nan,
        "epochs_effective": float(train.get("epochs_effective", math.nan)) if train.get("epochs_effective") is not None else math.nan,
    }
    out["metapath_attention_mode_reported"] = str(obj.get("metapath_attention_mode", ""))
    return out


def aggregate(all_df: pd.DataFrame, out_dir: Path) -> None:
    if all_df.empty:
        return
    summary = (
        all_df.groupby(["label_method", "model_group"], as_index=False)
        .agg(
            n=("seed", "count"),
            val_mae_mean=("val_mae", "mean"),
            val_mae_std=("val_mae", "std"),
            best_val_mse_mean=("best_val_mse", "mean"),
            high_risk_mae_mean=("val_high_risk_mae", "mean"),
        )
        .sort_values(["label_method", "model_group"])
    )
    summary.to_csv(out_dir / "planA_summary.csv", index=False, encoding="utf-8")

    piv = all_df.pivot_table(
        index=["label_method", "seed"],
        columns="model_group",
        values=["val_mae", "best_val_mse", "val_high_risk_mae"],
        aggfunc="first",
    )
    piv.columns = ["_".join(c) for c in piv.columns]
    piv = piv.reset_index()

    for g in ("A1_metapath_fixed", "A2_metapath_adaptive_global", "A3_metapath_adaptive_context"):
        piv[f"delta_val_mae_A0_minus_{g}"] = piv.get("val_mae_A0_baseline", math.nan) - piv.get(f"val_mae_{g}", math.nan)
        piv[f"delta_best_val_mse_A0_minus_{g}"] = piv.get("best_val_mse_A0_baseline", math.nan) - piv.get(
            f"best_val_mse_{g}", math.nan
        )
        piv[f"delta_hr_mae_A0_minus_{g}"] = piv.get("val_high_risk_mae_A0_baseline", math.nan) - piv.get(
            f"val_high_risk_mae_{g}", math.nan
        )
    piv.to_csv(out_dir / "planA_pairwise_seed.csv", index=False, encoding="utf-8")

    delta_cols = [c for c in piv.columns if c.startswith("delta_")]
    delta_summary = (
        piv.groupby("label_method", as_index=False)[delta_cols]
        .mean(numeric_only=True)
        .sort_values("label_method")
    )
    delta_summary.to_csv(out_dir / "planA_delta_summary.csv", index=False, encoding="utf-8")


def main() -> None:
    args = parse_args()
    root = project_root()
    resume_dir = str(args.resume_dir).strip()
    if resume_dir:
        out_dir = (root / resume_dir).resolve() if not Path(resume_dir).is_absolute() else Path(resume_dir).resolve()
    else:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        out_dir = (root / args.output_root / f"{args.tag}_{ts}").resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    python_exe = pick_python_exe(args.python_exe)

    grid = (root / args.grid).resolve()
    aligned = (root / args.aligned).resolve()
    failure_csv = (root / args.failure_csv).resolve()
    load_priority_csv = (root / args.load_priority_csv).resolve()
    c3po_tensor = (root / args.c3po_tensor).resolve()
    wangqmc_tensor = (root / args.wangqmc_tensor).resolve()

    for p in (grid, aligned, failure_csv, load_priority_csv, c3po_tensor, wangqmc_tensor):
        if not p.exists():
            raise FileNotFoundError(f"missing input: {p}")

    cases = build_cases(args=args, c3po=c3po_tensor, wang=wangqmc_tensor)
    if args.max_runs > 0:
        cases = cases[: int(args.max_runs)]

    manifest = {
        "python_exe": python_exe,
        "run_at": datetime.now().isoformat(timespec="seconds"),
        "planned_case_count": int(len(cases)),
        "seeds": parse_int_list(args.seeds),
        "note": "Plan A full run: A0/A1/A2/A3 x c3po_ref/wang_qmc",
    }
    (out_dir / "experiment_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    pd.DataFrame([asdict(c) for c in cases]).to_csv(out_dir / "experiment_matrix.csv", index=False, encoding="utf-8")

    print(f"experiment_dir={out_dir}")
    print(f"total_cases={len(cases)}")
    print(f"python_exe={python_exe}")

    rows: list[dict[str, Any]] = []
    for idx, c in enumerate(cases, start=1):
        run_name = f"{idx:04d}_{c.case_id}"
        run_dir = out_dir / run_name
        run_dir.mkdir(parents=True, exist_ok=True)
        report_path = run_dir / "warning_report.json"
        log_path = run_dir / "run.log"

        skipped = False
        status = "ok"
        rc = 0
        wall_seconds = 0.0
        if bool(args.reuse_existing) and report_path.exists():
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
                str(c.contingency_tensor),
                "--load-priority-csv",
                str(load_priority_csv),
                "--output-dir",
                str(run_dir),
                "--horizon-hours",
                str(int(args.horizon_hours)),
                "--horizon-start-index",
                str(int(args.horizon_start_index)),
                "--train-ratio",
                str(float(c.train_ratio)),
                "--hidden-dim",
                str(int(c.hidden_dim)),
                "--epochs",
                str(int(c.epochs)),
                "--lr",
                str(float(c.lr)),
                "--weight-decay",
                str(float(c.weight_decay)),
                "--risk-weight-alpha",
                str(float(c.risk_weight_alpha)),
                "--risk-weight-beta",
                str(float(c.risk_weight_beta)),
                "--risk-weight-threshold",
                str(float(c.risk_weight_threshold)),
                "--metapath-gate-reg-lambda",
                str(float(c.metapath_gate_reg_lambda)),
                "--metapath-attention-entropy-reg-lambda",
                str(float(c.metapath_attention_entropy_reg_lambda)),
                "--metapath-warmup-epochs",
                str(int(c.metapath_warmup_epochs)),
                "--metapath-attention-mode",
                str(c.metapath_attention_mode),
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
                str(int(c.metapath_topk)),
                "--seed",
                str(int(c.seed)),
                "--no-run-baseline-comparison",
                "--no-risk-weight-on-metapath-only",
            ]
            cmd.append("--metapath-v1-enabled" if c.metapath_v1_enabled else "--no-metapath-v1-enabled")

            rc, wall_seconds = run_cmd(cmd=cmd, cwd=root, log_path=log_path, dry_run=bool(args.dry_run))
            if rc != 0:
                status = "failed"

        report = safe_json(report_path)
        metrics = model_metrics_from_report(report)
        row = {
            "run_name": run_name,
            "run_dir": str(run_dir),
            "status": status,
            "return_code": int(rc),
            "skipped": bool(skipped),
            "wall_seconds": float(wall_seconds),
            **asdict(c),
            **metrics,
        }
        rows.append(row)
        all_df = pd.DataFrame(rows)
        all_df.to_csv(out_dir / "all_runs.csv", index=False, encoding="utf-8")
        print(f"[{idx}/{len(cases)}] {run_name} status={status}")

    all_df = pd.DataFrame(rows)
    all_df.to_csv(out_dir / "all_runs.csv", index=False, encoding="utf-8")
    aggregate(all_df, out_dir)

    done = {
        "experiment_dir": str(out_dir),
        "run_count": int(len(all_df)),
        "success_count": int((all_df["status"] == "ok").sum()) if not all_df.empty else 0,
        "all_runs_csv": str(out_dir / "all_runs.csv"),
        "summary_csv": str(out_dir / "planA_summary.csv"),
        "delta_summary_csv": str(out_dir / "planA_delta_summary.csv"),
        "pairwise_seed_csv": str(out_dir / "planA_pairwise_seed.csv"),
    }
    (out_dir / "done.json").write_text(json.dumps(done, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(done, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

