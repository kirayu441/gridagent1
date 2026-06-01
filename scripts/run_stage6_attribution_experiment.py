
from __future__ import annotations

import argparse
import json
import math
import subprocess
import sys
import time
from dataclasses import dataclass, asdict
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


def str2bool(raw: str) -> bool:
    val = str(raw).strip().lower()
    if val in {"1", "true", "yes", "y", "on"}:
        return True
    if val in {"0", "false", "no", "n", "off"}:
        return False
    raise ValueError(f"invalid boolean: {raw}")


def safe_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def can_import_warning_deps(python_exe: str) -> bool:
    probe = [python_exe, "-c", "import numpy,pandas,networkx,torch; print('ok')"]
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


@dataclass
class RunCase:
    block: str
    case_id: str
    seed: int
    label_method: str
    contingency_tensor: str
    model_variant: str
    warmup_on: bool
    gate_reg_on: bool
    risk_weight_on: bool
    preset: str
    metapath_topk: int
    hidden_dim: int
    epochs: int
    lr: float
    weight_decay: float
    train_ratio: float
    risk_weight_alpha: float
    risk_weight_beta: float
    risk_weight_threshold: float
    risk_weight_on_metapath_only: bool
    metapath_gate_reg_lambda: float
    metapath_attention_entropy_reg_lambda: float
    metapath_warmup_epochs: int
    run_baseline_comparison: bool


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run strict attribution experiments for Stage6 uplift: "
            "A) label x model, B) label x warmup x gate_reg x risk_weight, "
            "C) old/new metapath preset x label."
        )
    )
    parser.add_argument("--grid", default="data_final/formal_guangdong_2024/grid_topology.json")
    parser.add_argument("--aligned", default="data_final/formal_guangdong_2024/aligned_merged.csv")
    parser.add_argument("--failure-csv", default="results/component_failure_probability/formal2024/line_failure_timeseries_schloemer.csv")
    parser.add_argument("--load-priority-csv", default="results/load_prioritization_scheduling/formal2024/load_bus_priority_profile.csv")
    parser.add_argument("--c3po-tensor", default="results/spatiotemporal_contingency/formal2024_schloemer72h/contingency_tensor_c3po_ref.npy")
    parser.add_argument("--wangqmc-tensor", default="results/spatiotemporal_contingency/formal2024_schloemer72h/contingency_tensor_wang_qmc.npy")
    parser.add_argument("--output-root", default="results/early_warning")
    parser.add_argument("--tag", default="stage6_attribution")
    parser.add_argument("--resume-dir", default="", help="Existing experiment directory to resume. If set, do not create a new timestamped directory.")
    parser.add_argument("--python-exe", default="")

    parser.add_argument("--seeds", default="42,43,44,45,46")
    parser.add_argument("--run-block-a", type=str2bool, default=True)
    parser.add_argument("--run-block-b", type=str2bool, default=True)
    parser.add_argument("--run-block-c", type=str2bool, default=True)

    parser.add_argument("--horizon-hours", type=int, default=24)
    parser.add_argument("--horizon-start-index", type=int, default=0)
    parser.add_argument("--train-ratio", type=float, default=0.7)
    parser.add_argument("--hidden-dim", type=int, default=80)
    parser.add_argument("--epochs", type=int, default=700)
    parser.add_argument("--mc-scenarios", type=int, default=3000)
    parser.add_argument("--risk-high-threshold", type=float, default=0.70)
    parser.add_argument("--risk-medium-threshold", type=float, default=0.40)
    parser.add_argument("--hour-trigger-threshold", type=float, default=0.35)
    parser.add_argument("--risk-mean-floor", type=float, default=0.18)
    parser.add_argument("--risk-mean-cap", type=float, default=0.55)
    parser.add_argument("--scenario-intensity-alpha", type=float, default=2.0)
    parser.add_argument("--scenario-intensity-beta", type=float, default=6.0)
    parser.add_argument("--high-risk-threshold", type=float, default=0.10)
    parser.add_argument("--top-risk-quantile", type=float, default=0.90)

    parser.add_argument("--neutral-lr", type=float, default=0.0035)
    parser.add_argument("--neutral-weight-decay", type=float, default=0.00015)
    parser.add_argument("--neutral-topk", type=int, default=3)
    parser.add_argument("--neutral-risk-weight-threshold", type=float, default=0.10)

    parser.add_argument("--old-lr", type=float, default=0.0042)
    parser.add_argument("--old-weight-decay", type=float, default=0.00005)
    parser.add_argument("--old-topk", type=int, default=4)
    parser.add_argument("--old-warmup-epochs", type=int, default=0)
    parser.add_argument("--old-gate-reg-lambda", type=float, default=0.0)
    parser.add_argument("--old-risk-weight-alpha", type=float, default=0.0)
    parser.add_argument("--old-risk-weight-beta", type=float, default=0.0)
    parser.add_argument("--old-risk-weight-threshold", type=float, default=0.10)

    parser.add_argument("--new-lr", type=float, default=0.00315)
    parser.add_argument("--new-weight-decay", type=float, default=0.00015)
    parser.add_argument("--new-topk", type=int, default=3)
    parser.add_argument("--new-warmup-epochs", type=int, default=12)
    parser.add_argument("--new-gate-reg-lambda", type=float, default=0.0002)
    parser.add_argument("--new-risk-weight-alpha", type=float, default=1.0)
    parser.add_argument("--new-risk-weight-beta", type=float, default=2.0)
    parser.add_argument("--new-risk-weight-threshold", type=float, default=0.10)

    parser.add_argument("--reuse-existing", type=str2bool, default=True)
    parser.add_argument("--max-runs", type=int, default=0, help="Limit total run count. 0 means no limit.")
    parser.add_argument("--dry-run", type=str2bool, default=False)
    return parser.parse_args()

def build_cases(args: argparse.Namespace, c3po_tensor: Path, wangqmc_tensor: Path) -> list[RunCase]:
    seeds = parse_int_list(args.seeds)
    labels = [
        ("c3po_ref", str(c3po_tensor)),
        ("wang_qmc", str(wangqmc_tensor)),
    ]

    cases: list[RunCase] = []

    if bool(args.run_block_a):
        for seed in seeds:
            for label_method, tensor in labels:
                for model in ("baseline_gnn", "metapath_v1"):
                    cid = f"A_label-{label_method}_model-{model}_seed-{seed}"
                    cases.append(
                        RunCase(
                            block="A",
                            case_id=cid,
                            seed=seed,
                            label_method=label_method,
                            contingency_tensor=tensor,
                            model_variant=model,
                            warmup_on=False,
                            gate_reg_on=False,
                            risk_weight_on=False,
                            preset="neutral",
                            metapath_topk=int(args.neutral_topk),
                            hidden_dim=int(args.hidden_dim),
                            epochs=int(args.epochs),
                            lr=float(args.neutral_lr),
                            weight_decay=float(args.neutral_weight_decay),
                            train_ratio=float(args.train_ratio),
                            risk_weight_alpha=0.0,
                            risk_weight_beta=0.0,
                            risk_weight_threshold=float(args.neutral_risk_weight_threshold),
                            risk_weight_on_metapath_only=False,
                            metapath_gate_reg_lambda=0.0,
                            metapath_attention_entropy_reg_lambda=0.0,
                            metapath_warmup_epochs=0,
                            run_baseline_comparison=False,
                        )
                    )

    if bool(args.run_block_b):
        for seed in seeds:
            for label_method, tensor in labels:
                for warmup_on in (False, True):
                    for gate_reg_on in (False, True):
                        for risk_weight_on in (False, True):
                            cid = (
                                f"B_label-{label_method}_warmup-{int(warmup_on)}"
                                f"_gate-{int(gate_reg_on)}_riskw-{int(risk_weight_on)}_seed-{seed}"
                            )
                            cases.append(
                                RunCase(
                                    block="B",
                                    case_id=cid,
                                    seed=seed,
                                    label_method=label_method,
                                    contingency_tensor=tensor,
                                    model_variant="metapath_v1",
                                    warmup_on=warmup_on,
                                    gate_reg_on=gate_reg_on,
                                    risk_weight_on=risk_weight_on,
                                    preset="factorial",
                                    metapath_topk=int(args.new_topk),
                                    hidden_dim=int(args.hidden_dim),
                                    epochs=int(args.epochs),
                                    lr=float(args.new_lr),
                                    weight_decay=float(args.new_weight_decay),
                                    train_ratio=float(args.train_ratio),
                                    risk_weight_alpha=float(args.new_risk_weight_alpha if risk_weight_on else 0.0),
                                    risk_weight_beta=float(args.new_risk_weight_beta if risk_weight_on else 0.0),
                                    risk_weight_threshold=float(args.new_risk_weight_threshold),
                                    risk_weight_on_metapath_only=False,
                                    metapath_gate_reg_lambda=float(args.new_gate_reg_lambda if gate_reg_on else 0.0),
                                    metapath_attention_entropy_reg_lambda=0.0,
                                    metapath_warmup_epochs=int(args.new_warmup_epochs if warmup_on else 0),
                                    run_baseline_comparison=False,
                                )
                            )

    if bool(args.run_block_c):
        for seed in seeds:
            for label_method, tensor in labels:
                cases.append(
                    RunCase(
                        block="C",
                        case_id=f"C_label-{label_method}_preset-old_seed-{seed}",
                        seed=seed,
                        label_method=label_method,
                        contingency_tensor=tensor,
                        model_variant="metapath_v1",
                        warmup_on=False,
                        gate_reg_on=False,
                        risk_weight_on=False,
                        preset="old",
                        metapath_topk=int(args.old_topk),
                        hidden_dim=int(args.hidden_dim),
                        epochs=int(args.epochs),
                        lr=float(args.old_lr),
                        weight_decay=float(args.old_weight_decay),
                        train_ratio=float(args.train_ratio),
                        risk_weight_alpha=float(args.old_risk_weight_alpha),
                        risk_weight_beta=float(args.old_risk_weight_beta),
                        risk_weight_threshold=float(args.old_risk_weight_threshold),
                        risk_weight_on_metapath_only=False,
                        metapath_gate_reg_lambda=float(args.old_gate_reg_lambda),
                        metapath_attention_entropy_reg_lambda=0.0,
                        metapath_warmup_epochs=int(args.old_warmup_epochs),
                        run_baseline_comparison=False,
                    )
                )
                cases.append(
                    RunCase(
                        block="C",
                        case_id=f"C_label-{label_method}_preset-new_seed-{seed}",
                        seed=seed,
                        label_method=label_method,
                        contingency_tensor=tensor,
                        model_variant="metapath_v1",
                        warmup_on=True,
                        gate_reg_on=True,
                        risk_weight_on=True,
                        preset="new",
                        metapath_topk=int(args.new_topk),
                        hidden_dim=int(args.hidden_dim),
                        epochs=int(args.epochs),
                        lr=float(args.new_lr),
                        weight_decay=float(args.new_weight_decay),
                        train_ratio=float(args.train_ratio),
                        risk_weight_alpha=float(args.new_risk_weight_alpha),
                        risk_weight_beta=float(args.new_risk_weight_beta),
                        risk_weight_threshold=float(args.new_risk_weight_threshold),
                        risk_weight_on_metapath_only=False,
                        metapath_gate_reg_lambda=float(args.new_gate_reg_lambda),
                        metapath_attention_entropy_reg_lambda=0.0,
                        metapath_warmup_epochs=int(args.new_warmup_epochs),
                        run_baseline_comparison=False,
                    )
                )
    return cases


def run_cmd(cmd: list[str], cwd: Path, log_path: Path, dry_run: bool) -> tuple[int, float]:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    if dry_run:
        log_path.write_text("DRY RUN\n" + " ".join(cmd) + "\n", encoding="utf-8")
        print("[dry-run]", " ".join(cmd))
        return 0, 0.0

    t0 = time.perf_counter()
    print(">>", " ".join(cmd))
    proc = subprocess.run(cmd, cwd=str(cwd), text=True, capture_output=True, check=False)
    dt = float(time.perf_counter() - t0)

    content = [
        "CMD: " + " ".join(cmd),
        "",
        "STDOUT:",
        proc.stdout or "",
        "",
        "STDERR:",
        proc.stderr or "",
        "",
        f"RETURNCODE: {proc.returncode}",
        f"WALL_SECONDS: {dt:.3f}",
    ]
    log_path.write_text("\n".join(content), encoding="utf-8")
    return int(proc.returncode), dt


def model_metrics_from_report(report: dict[str, Any]) -> dict[str, float]:
    out: dict[str, float] = {}
    fit_quality = report.get("fit_quality", {}) if isinstance(report, dict) else {}
    val = fit_quality.get("validation", {}) if isinstance(fit_quality, dict) else {}
    train = report.get("training", {}) if isinstance(report, dict) else {}
    out["val_mae"] = float(val.get("mae", math.nan))
    out["val_rmse"] = float(val.get("rmse", math.nan))
    out["val_brier"] = float(val.get("brier", math.nan))
    out["val_high_risk_mae"] = float(val.get("high_risk_mae", math.nan))
    out["val_top_risk_mae"] = float(val.get("top_risk_mae", math.nan))
    out["best_val_mse"] = float(train.get("best_val_mse", math.nan))
    out["metapath_gate_mean"] = float(train.get("metapath_gate_mean", math.nan)) if train.get("metapath_gate_mean") is not None else math.nan
    out["epochs_effective"] = float(train.get("epochs_effective", math.nan))
    return out

def aggregate_block_a(df: pd.DataFrame, out_dir: Path) -> pd.DataFrame:
    dfa = df[(df["block"] == "A") & (df["status"] == "ok")].copy()
    if dfa.empty:
        return pd.DataFrame()
    piv = dfa.pivot_table(
        index=["label_method", "seed"],
        columns="model_variant",
        values=["val_mae", "val_rmse", "best_val_mse", "val_high_risk_mae"],
        aggfunc="first",
    )
    piv.columns = [f"{a}_{b}" for a, b in piv.columns]
    piv = piv.reset_index()
    piv["delta_val_mae"] = piv.get("val_mae_baseline_gnn", math.nan) - piv.get("val_mae_metapath_v1", math.nan)
    piv["delta_val_rmse"] = piv.get("val_rmse_baseline_gnn", math.nan) - piv.get("val_rmse_metapath_v1", math.nan)
    piv["delta_best_val_mse"] = piv.get("best_val_mse_baseline_gnn", math.nan) - piv.get("best_val_mse_metapath_v1", math.nan)
    piv["delta_val_high_risk_mae"] = piv.get("val_high_risk_mae_baseline_gnn", math.nan) - piv.get("val_high_risk_mae_metapath_v1", math.nan)
    piv.to_csv(out_dir / "blockA_pairwise.csv", index=False, encoding="utf-8")

    summary = (
        piv.groupby("label_method", as_index=False)
        .agg(
            n=("seed", "count"),
            delta_val_mae_mean=("delta_val_mae", "mean"),
            delta_val_mae_std=("delta_val_mae", "std"),
            delta_val_rmse_mean=("delta_val_rmse", "mean"),
            delta_best_val_mse_mean=("delta_best_val_mse", "mean"),
            delta_val_high_risk_mae_mean=("delta_val_high_risk_mae", "mean"),
        )
    )
    summary.to_csv(out_dir / "blockA_summary.csv", index=False, encoding="utf-8")
    return summary


def aggregate_block_b(df: pd.DataFrame, out_dir: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    dfb = df[(df["block"] == "B") & (df["status"] == "ok")].copy()
    if dfb.empty:
        return pd.DataFrame(), pd.DataFrame()

    group_cols = ["label_method", "warmup_on", "gate_reg_on", "risk_weight_on"]
    combo = (
        dfb.groupby(group_cols, as_index=False)
        .agg(
            n=("seed", "count"),
            val_mae_mean=("val_mae", "mean"),
            val_mae_std=("val_mae", "std"),
            val_rmse_mean=("val_rmse", "mean"),
            best_val_mse_mean=("best_val_mse", "mean"),
            val_high_risk_mae_mean=("val_high_risk_mae", "mean"),
            gate_mean_mean=("metapath_gate_mean", "mean"),
            wall_seconds_mean=("wall_seconds", "mean"),
        )
        .sort_values(["label_method", "val_mae_mean"], ascending=[True, True])
        .reset_index(drop=True)
    )
    combo.to_csv(out_dir / "blockB_combo_summary.csv", index=False, encoding="utf-8")

    effects: list[dict[str, Any]] = []
    for label in sorted(dfb["label_method"].dropna().unique().tolist()):
        sub = dfb[dfb["label_method"] == label].copy()
        for factor in ("warmup_on", "gate_reg_on", "risk_weight_on"):
            on = sub[sub[factor] == True]
            off = sub[sub[factor] == False]
            effects.append(
                {
                    "label_method": label,
                    "factor": factor,
                    "n_on": int(len(on)),
                    "n_off": int(len(off)),
                    "val_mae_on_mean": float(on["val_mae"].mean()) if not on.empty else math.nan,
                    "val_mae_off_mean": float(off["val_mae"].mean()) if not off.empty else math.nan,
                    "val_mae_gain_off_minus_on": float(off["val_mae"].mean() - on["val_mae"].mean()) if (not on.empty and not off.empty) else math.nan,
                    "best_val_mse_gain_off_minus_on": float(off["best_val_mse"].mean() - on["best_val_mse"].mean()) if (not on.empty and not off.empty) else math.nan,
                    "high_risk_mae_gain_off_minus_on": float(off["val_high_risk_mae"].mean() - on["val_high_risk_mae"].mean()) if (not on.empty and not off.empty) else math.nan,
                }
            )
    effect_df = pd.DataFrame(effects)
    effect_df.to_csv(out_dir / "blockB_main_effects.csv", index=False, encoding="utf-8")
    return combo, effect_df


def aggregate_block_c(df: pd.DataFrame, out_dir: Path) -> pd.DataFrame:
    dfc = df[(df["block"] == "C") & (df["status"] == "ok")].copy()
    if dfc.empty:
        return pd.DataFrame()
    piv = dfc.pivot_table(
        index=["label_method", "seed"],
        columns="preset",
        values=["val_mae", "val_rmse", "best_val_mse", "val_high_risk_mae"],
        aggfunc="first",
    )
    piv.columns = [f"{a}_{b}" for a, b in piv.columns]
    piv = piv.reset_index()
    piv["delta_val_mae_old_minus_new"] = piv.get("val_mae_old", math.nan) - piv.get("val_mae_new", math.nan)
    piv["delta_best_val_mse_old_minus_new"] = piv.get("best_val_mse_old", math.nan) - piv.get("best_val_mse_new", math.nan)
    piv["delta_val_high_risk_mae_old_minus_new"] = piv.get("val_high_risk_mae_old", math.nan) - piv.get("val_high_risk_mae_new", math.nan)
    piv.to_csv(out_dir / "blockC_pairwise.csv", index=False, encoding="utf-8")

    summary = (
        piv.groupby("label_method", as_index=False)
        .agg(
            n=("seed", "count"),
            delta_val_mae_mean=("delta_val_mae_old_minus_new", "mean"),
            delta_val_mae_std=("delta_val_mae_old_minus_new", "std"),
            delta_best_val_mse_mean=("delta_best_val_mse_old_minus_new", "mean"),
            delta_high_risk_mae_mean=("delta_val_high_risk_mae_old_minus_new", "mean"),
        )
    )
    summary.to_csv(out_dir / "blockC_summary.csv", index=False, encoding="utf-8")
    return summary


def write_markdown_report(
    out_dir: Path,
    all_df: pd.DataFrame,
    a_summary: pd.DataFrame,
    b_combo: pd.DataFrame,
    b_effect: pd.DataFrame,
    c_summary: pd.DataFrame,
) -> None:
    def df_to_markdown_local(df: pd.DataFrame) -> str:
        if df is None or df.empty:
            return "_empty_"
        headers = [str(c) for c in df.columns]
        lines_local = []
        lines_local.append("| " + " | ".join(headers) + " |")
        lines_local.append("| " + " | ".join(["---"] * len(headers)) + " |")
        for _, row in df.iterrows():
            vals = []
            for h in headers:
                v = row[h]
                if pd.isna(v):
                    vals.append("")
                elif isinstance(v, float):
                    vals.append(f"{v:.6g}")
                else:
                    vals.append(str(v))
            lines_local.append("| " + " | ".join(vals) + " |")
        return "\n".join(lines_local)

    lines: list[str] = []
    lines.append("# Stage6 Attribution Report")
    lines.append("")
    lines.append(f"- Generated at: {datetime.now().isoformat(timespec='seconds')}")
    lines.append(f"- Experiment directory: `{out_dir}`")
    lines.append("")
    lines.append("## Run Summary")
    lines.append("")
    total = int(len(all_df))
    ok = int((all_df["status"] == "ok").sum()) if not all_df.empty else 0
    lines.append(f"- total_runs: {total}")
    lines.append(f"- success_runs: {ok}")
    if not all_df.empty:
        lines.append(f"- mean_wall_seconds: {float(all_df['wall_seconds'].mean()):.3f}")
    lines.append("")

    if not a_summary.empty:
        lines.append("## Block A (Label x Model, strategy OFF)")
        lines.append("")
        lines.append(df_to_markdown_local(a_summary))
        lines.append("")
        lines.append("Interpretation: positive delta means MetaPath outperforms baseline on the same label regime.")
        lines.append("")

    if not b_combo.empty:
        lines.append("## Block B (Label x Warmup x GateReg x RiskWeight)")
        lines.append("")
        lines.append("Top configurations by val_mae_mean:")
        lines.append("")
        lines.append(df_to_markdown_local(b_combo.head(8)))
        lines.append("")
    if not b_effect.empty:
        lines.append("Main effects (off-minus-on gains):")
        lines.append("")
        lines.append(df_to_markdown_local(b_effect))
        lines.append("")

    if not c_summary.empty:
        lines.append("## Block C (Old vs New MetaPath preset)")
        lines.append("")
        lines.append(df_to_markdown_local(c_summary))
        lines.append("")
        lines.append("Interpretation: positive delta means new preset is better than old preset.")
        lines.append("")

    lines.append("## Notes")
    lines.append("")
    lines.append("- This report is descriptive; inferential statistics can be added in a separate step if needed.")
    lines.append("- Use per-seed pairwise tables for confidence interval or significance testing.")
    lines.append("")
    (out_dir / "attribution_report.md").write_text("\n".join(lines), encoding="utf-8")

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

    cases = build_cases(args=args, c3po_tensor=c3po_tensor, wangqmc_tensor=wangqmc_tensor)
    if args.max_runs > 0:
        cases = cases[: int(args.max_runs)]

    manifest = {
        "python_exe": python_exe,
        "run_at": datetime.now().isoformat(timespec="seconds"),
        "run_block_a": bool(args.run_block_a),
        "run_block_b": bool(args.run_block_b),
        "run_block_c": bool(args.run_block_c),
        "seed_list": parse_int_list(args.seeds),
        "paths": {
            "grid": str(grid),
            "aligned": str(aligned),
            "failure_csv": str(failure_csv),
            "load_priority_csv": str(load_priority_csv),
            "c3po_tensor": str(c3po_tensor),
            "wangqmc_tensor": str(wangqmc_tensor),
        },
        "global_args": {
            "hidden_dim": int(args.hidden_dim),
            "epochs": int(args.epochs),
            "train_ratio": float(args.train_ratio),
            "reuse_existing": bool(args.reuse_existing),
            "dry_run": bool(args.dry_run),
        },
        "planned_case_count": int(len(cases)),
    }
    (out_dir / "experiment_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    matrix_df = pd.DataFrame([asdict(c) for c in cases])
    matrix_df.to_csv(out_dir / "experiment_matrix.csv", index=False, encoding="utf-8")

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
            ]

            if c.model_variant == "metapath_v1":
                cmd.append("--metapath-v1-enabled")
            else:
                cmd.append("--no-metapath-v1-enabled")

            if bool(c.risk_weight_on_metapath_only):
                cmd.append("--risk-weight-on-metapath-only")
            else:
                cmd.append("--no-risk-weight-on-metapath-only")

            if bool(c.run_baseline_comparison):
                cmd.append("--run-baseline-comparison")
            else:
                cmd.append("--no-run-baseline-comparison")

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

    a_summary = aggregate_block_a(all_df, out_dir)
    b_combo, b_effect = aggregate_block_b(all_df, out_dir)
    c_summary = aggregate_block_c(all_df, out_dir)
    write_markdown_report(out_dir, all_df, a_summary, b_combo, b_effect, c_summary)

    done = {
        "experiment_dir": str(out_dir),
        "all_runs_csv": str(out_dir / "all_runs.csv"),
        "matrix_csv": str(out_dir / "experiment_matrix.csv"),
        "blockA_summary_csv": str(out_dir / "blockA_summary.csv"),
        "blockB_combo_summary_csv": str(out_dir / "blockB_combo_summary.csv"),
        "blockB_main_effects_csv": str(out_dir / "blockB_main_effects.csv"),
        "blockC_summary_csv": str(out_dir / "blockC_summary.csv"),
        "attribution_report_md": str(out_dir / "attribution_report.md"),
        "run_count": int(len(all_df)),
        "success_count": int((all_df["status"] == "ok").sum()) if not all_df.empty else 0,
    }
    (out_dir / "done.json").write_text(json.dumps(done, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(done, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
