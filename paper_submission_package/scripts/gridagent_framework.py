from __future__ import annotations

import argparse
import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


ALL_CONTINGENCY_METHODS = ("wang_qmc", "wang_mc", "c3po_ref", "trim_ref")


def project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def resolve_path(root: Path, raw: str) -> Path:
    return (root / raw).resolve()


def run_cmd(cmd: list[str], cwd: Path, dry_run: bool = False) -> None:
    print(">>", " ".join(cmd))
    if dry_run:
        return
    proc = subprocess.run(cmd, cwd=str(cwd), text=True, capture_output=True, check=False)
    if proc.returncode != 0:
        raise RuntimeError(
            f"command failed ({proc.returncode}): {' '.join(cmd)}\n"
            f"STDOUT:\n{proc.stdout}\n\nSTDERR:\n{proc.stderr}"
        )
    if proc.stdout.strip():
        print(proc.stdout.strip())
    if proc.stderr.strip():
        print(proc.stderr.strip())


def maybe_run(
    cmd: list[str],
    expected_outputs: list[Path],
    cwd: Path,
    reuse_existing: bool,
    dry_run: bool,
) -> None:
    if reuse_existing and all(p.exists() for p in expected_outputs):
        print(f"skip (exists): {expected_outputs[0]}")
        return
    run_cmd(cmd=cmd, cwd=cwd, dry_run=dry_run)
    if dry_run:
        return
    for p in expected_outputs:
        if not p.exists():
            raise FileNotFoundError(f"expected output missing: {p}")


def calc_rapidity_sustainability(worst_detail_csv: Path, policy: str = "priority_with_reserve") -> tuple[float, float]:
    df = pd.read_csv(worst_detail_csv)
    df = df[df["policy"] == policy].copy()
    if df.empty:
        return 0.0, 0.0
    by_t = df.groupby("timestamp", as_index=False).agg(demand_total=("demand", "sum"), shed_total=("shed", "sum"))
    demand = by_t["demand_total"].to_numpy(dtype=float)
    shed = by_t["shed_total"].to_numpy(dtype=float)
    with np.errstate(divide="ignore", invalid="ignore"):
        shed_ratio = np.divide(shed, demand, out=np.zeros_like(shed), where=demand > 1e-12)
    shed_ratio = np.clip(shed_ratio, 0.0, 1.0)
    sustainability = float(np.clip(1.0 - shed_ratio.mean(), 0.0, 1.0))
    peak = float(shed_ratio.max(initial=0.0))
    if peak <= 1e-9 or len(shed_ratio) <= 1:
        rapidity = 1.0
    else:
        peak_idx = int(np.argmax(shed_ratio))
        target = 0.2 * peak
        rec_idx = None
        for i in range(peak_idx, len(shed_ratio)):
            if shed_ratio[i] <= target:
                rec_idx = i
                break
        if rec_idx is None:
            rec_hours = float(len(shed_ratio))
        else:
            rec_hours = float(rec_idx - peak_idx)
        tau = max(len(shed_ratio) / 3.0, 1.0)
        rapidity = float(np.exp(-rec_hours / tau))
    return rapidity, sustainability


def ewm_topsis(matrix: np.ndarray, benefit_flags: list[bool]) -> tuple[np.ndarray, np.ndarray]:
    x = np.array(matrix, dtype=float)
    benefit = np.array(benefit_flags, dtype=bool)
    x_forward = np.zeros_like(x)
    for j in range(x.shape[1]):
        col = x[:, j]
        cmin = float(col.min())
        cmax = float(col.max())
        span = cmax - cmin
        if span < 1e-12:
            x_forward[:, j] = 1.0
        elif benefit[j]:
            x_forward[:, j] = (col - cmin) / span
        else:
            x_forward[:, j] = (cmax - col) / span

    p = x_forward / np.clip(x_forward.sum(axis=0, keepdims=True), 1e-12, None)
    k = 1.0 / np.log(max(x.shape[0], 2))
    safe_p = np.clip(p, 1e-12, 1.0)
    entropy = -k * np.sum(p * np.log(safe_p), axis=0)
    divergence = 1.0 - entropy
    if divergence.sum() <= 1e-12:
        w = np.full(x.shape[1], 1.0 / x.shape[1], dtype=float)
    else:
        w = divergence / divergence.sum()

    r = x_forward / np.clip(np.sqrt((x_forward**2).sum(axis=0, keepdims=True)), 1e-12, None)
    v = r * w
    ideal_best = v.max(axis=0)
    ideal_worst = v.min(axis=0)
    d_plus = np.sqrt(((v - ideal_best) ** 2).sum(axis=1))
    d_minus = np.sqrt(((v - ideal_worst) ** 2).sum(axis=1))
    score = d_minus / np.clip(d_plus + d_minus, 1e-12, None)
    return score, w


def evaluate_candidate_run(
    policy_csv: Path,
    worst_csv: Path,
    failure_model: str,
    contingency_method: str,
    reserve_ratio: float,
    run_tag: str,
    run_dir: Path,
) -> dict[str, Any]:
    policy_df = pd.read_csv(policy_csv)
    row = policy_df[policy_df["policy"] == "priority_with_reserve"]
    if row.empty:
        raise ValueError(f"priority_with_reserve not found: {policy_csv}")
    r = row.iloc[0]
    rapidity, sustainability = calc_rapidity_sustainability(worst_detail_csv=worst_csv, policy="priority_with_reserve")
    return {
        "run_tag": run_tag,
        "failure_model": failure_model,
        "contingency_method": contingency_method,
        "reserve_ratio": float(reserve_ratio),
        "Priority": float(r["critical_served_ratio"]),
        "Robustness": float(r["rr"]),
        "Rapidity": float(rapidity),
        "Sustainability": float(sustainability),
        "RA": float(r.get("ra", np.nan)),
        "expected_total_shed": float(r["expected_total_shed"]),
        "expected_weighted_shed_cost": float(r["expected_weighted_shed_cost"]),
        "run_dir": str(run_dir),
    }


def score_candidates(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    out = df.copy()
    indicators = ["Priority", "Robustness", "Rapidity", "Sustainability"]
    score, weights = ewm_topsis(out[indicators].to_numpy(dtype=float), benefit_flags=[True, True, True, True])
    out["TOPSIS_Score"] = score
    out = out.sort_values("TOPSIS_Score", ascending=False).reset_index(drop=True)
    out["TOPSIS_Rank"] = np.arange(1, len(out) + 1)
    w_df = pd.DataFrame({"indicator": indicators, "ewm_weight": weights}).sort_values("ewm_weight", ascending=False)
    return out, w_df


def reserve_tag(value: float) -> str:
    return str(value).replace(".", "p")


def pick_cloud_candidates(edge_ranked: pd.DataFrame, top_k: int, diversity_on_method: bool) -> pd.DataFrame:
    if edge_ranked.empty:
        return edge_ranked
    edge_ranked = edge_ranked.sort_values("TOPSIS_Score", ascending=False).reset_index(drop=True)
    if top_k <= 0:
        return edge_ranked.head(0)
    if not diversity_on_method:
        return edge_ranked.head(top_k).copy()

    selected_idx: list[int] = []
    seen_methods: set[str] = set()
    for idx, row in edge_ranked.iterrows():
        method = str(row["contingency_method"])
        if method in seen_methods:
            continue
        selected_idx.append(int(idx))
        seen_methods.add(method)
        if len(selected_idx) >= top_k:
            break
    if len(selected_idx) < top_k:
        for idx in range(len(edge_ranked)):
            if idx in selected_idx:
                continue
            selected_idx.append(idx)
            if len(selected_idx) >= top_k:
                break
    return edge_ranked.iloc[selected_idx].reset_index(drop=True)


def run_wind_pv_stage(
    root: Path,
    run_root: Path,
    wind_cfg: dict[str, Any],
    max_steps: int | None,
    reuse_existing: bool,
    dry_run: bool,
) -> Path:
    dataset = str(wind_cfg.get("dataset", "formal2024"))
    stage_root = run_root / str(wind_cfg.get("output_subdir", "stage1_wind_pv"))
    out_dir = stage_root / dataset
    expected = [out_dir / "typical_scenarios.npy", out_dir / "scenario_probabilities.csv", out_dir / "history_series.csv"]
    cmd = [
        "python",
        str(root / "scripts" / "wind_pv_uncertainty_modeling.py"),
        "--dataset",
        dataset,
        "--output-dir",
        str(stage_root),
        "--window-radius",
        str(wind_cfg.get("window_radius", 6)),
        "--max-components",
        str(wind_cfg.get("max_components", 8)),
        "--max-iter",
        str(wind_cfg.get("max_iter", 400)),
        "--n-sampled-scenarios",
        str(wind_cfg.get("n_sampled_scenarios", 200)),
        "--n-typical-scenarios",
        str(wind_cfg.get("n_typical_scenarios", 10)),
        "--seed",
        str(wind_cfg.get("seed", 42)),
    ]
    if max_steps is not None:
        cmd.extend(["--max-steps", str(max_steps)])
    maybe_run(cmd=cmd, expected_outputs=expected, cwd=root, reuse_existing=reuse_existing, dry_run=dry_run)
    return out_dir


def run_failure_stage_for_model(
    root: Path,
    run_root: Path,
    paths_cfg: dict[str, Any],
    failure_cfg: dict[str, Any],
    model: str,
    max_steps: int | None,
    reuse_existing: bool,
    dry_run: bool,
) -> Path:
    stage_dir = run_root / "stage2_failure" / model
    stage_dir.mkdir(parents=True, exist_ok=True)
    failure_csv = stage_dir / f"line_failure_timeseries_{model}.csv"
    hours = int(failure_cfg.get("hours", 72))
    if max_steps is not None:
        hours = max(1, min(hours, int(max_steps)))
    cmd = [
        "python",
        str(root / "scripts" / "component_failure_probability.py"),
        "--grid",
        str(resolve_path(root, str(paths_cfg["grid"]))),
        "--output-dir",
        str(stage_dir),
        "--model",
        model,
        "--start-time",
        str(failure_cfg.get("start_time", "2024-09-01 00:00:00")),
        "--hours",
        str(hours),
        "--center-lat",
        str(failure_cfg.get("center_lat", 23.1291)),
        "--center-lon",
        str(failure_cfg.get("center_lon", 113.2644)),
        "--intensity-scale",
        str(failure_cfg.get("intensity_scale", 1.0)),
        "--move-dir-deg",
        str(failure_cfg.get("move_dir_deg", 300.0)),
        "--move-speed-ms",
        str(failure_cfg.get("move_speed_ms", 6.0)),
        "--design-scale",
        str(failure_cfg.get("design_scale", 1.0)),
    ]
    maybe_run(cmd=cmd, expected_outputs=[failure_csv], cwd=root, reuse_existing=reuse_existing, dry_run=dry_run)
    return failure_csv


def run_contingency_stage(
    root: Path,
    paths_cfg: dict[str, Any],
    contingency_cfg: dict[str, Any],
    failure_csv: Path,
    output_dir: Path,
    methods: list[str],
    n_scenarios: int,
    seed: int,
    max_steps: int | None,
    reuse_existing: bool,
    dry_run: bool,
) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    method_set = sorted(set(methods))
    for m in method_set:
        if m not in ALL_CONTINGENCY_METHODS:
            raise ValueError(f"unsupported contingency method: {m}")
    expected_tensor = {m: output_dir / f"contingency_tensor_{m}.npy" for m in method_set}
    expected_scenarios = {m: output_dir / f"contingency_scenarios_{m}.csv" for m in method_set}

    if method_set == sorted(list(ALL_CONTINGENCY_METHODS)):
        cmd = [
            "python",
            str(root / "scripts" / "spatiotemporal_contingency_generator.py"),
            "--failure-csv",
            str(failure_csv),
            "--grid",
            str(resolve_path(root, str(paths_cfg["grid"]))),
            "--output-dir",
            str(output_dir),
            "--methods",
            "all",
            "--n-scenarios",
            str(n_scenarios),
            "--seed",
            str(seed),
            "--warning-end-hour",
            str(contingency_cfg.get("warning_end_hour", -1)),
            "--repair-hours",
            str(contingency_cfg.get("repair_hours", 12)),
            "--high-risk-quantile",
            str(contingency_cfg.get("high_risk_quantile", 0.9)),
        ]
        if max_steps is not None:
            cmd.extend(["--max-steps", str(max_steps)])
        maybe_run(
            cmd=cmd,
            expected_outputs=list(expected_tensor.values()) + list(expected_scenarios.values()),
            cwd=root,
            reuse_existing=reuse_existing,
            dry_run=dry_run,
        )
    else:
        for method in method_set:
            cmd = [
                "python",
                str(root / "scripts" / "spatiotemporal_contingency_generator.py"),
                "--failure-csv",
                str(failure_csv),
                "--grid",
                str(resolve_path(root, str(paths_cfg["grid"]))),
                "--output-dir",
                str(output_dir),
                "--methods",
                method,
                "--n-scenarios",
                str(n_scenarios),
                "--seed",
                str(seed),
                "--warning-end-hour",
                str(contingency_cfg.get("warning_end_hour", -1)),
                "--repair-hours",
                str(contingency_cfg.get("repair_hours", 12)),
                "--high-risk-quantile",
                str(contingency_cfg.get("high_risk_quantile", 0.9)),
            ]
            if max_steps is not None:
                cmd.extend(["--max-steps", str(max_steps)])
            maybe_run(
                cmd=cmd,
                expected_outputs=[expected_tensor[method], expected_scenarios[method]],
                cwd=root,
                reuse_existing=reuse_existing,
                dry_run=dry_run,
            )
    return expected_tensor


def run_scheduling_stage(
    root: Path,
    paths_cfg: dict[str, Any],
    scheduling_cfg: dict[str, Any],
    uncertainty_dir: Path,
    failure_csv: Path,
    contingency_tensor: Path,
    output_dir: Path,
    reserve_ratio: float,
    seed: int,
    reuse_existing: bool,
    dry_run: bool,
) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    policy_csv = output_dir / "policy_comparison.csv"
    worst_csv = output_dir / "worst_scenario_shedding_detail.csv"
    cmd = [
        "python",
        str(root / "scripts" / "load_prioritization_scheduling.py"),
        "--grid",
        str(resolve_path(root, str(paths_cfg["grid"]))),
        "--trim-input",
        str(resolve_path(root, str(paths_cfg["trim_input"]))),
        "--contingency-tensor",
        str(contingency_tensor),
        "--failure-csv",
        str(failure_csv),
        "--uncertainty-dir",
        str(uncertainty_dir),
        "--output-dir",
        str(output_dir),
        "--reserve-ratio",
        str(reserve_ratio),
        "--load-shed-cost",
        str(scheduling_cfg.get("load_shed_cost", 50.0)),
        "--slack-dispatchable-capacity",
        str(scheduling_cfg.get("slack_dispatchable_capacity", 1.20)),
        "--emergency-dg-capacities",
        str(scheduling_cfg.get("emergency_dg_capacities", "0.18,0.15,0.10")),
        "--seed",
        str(seed),
    ]
    maybe_run(
        cmd=cmd,
        expected_outputs=[policy_csv, worst_csv],
        cwd=root,
        reuse_existing=reuse_existing,
        dry_run=dry_run,
    )
    return policy_csv, worst_csv


def run_assessment_stage(
    root: Path,
    policy_csv: Path,
    worst_csv: Path,
    output_dir: Path,
    reuse_existing: bool,
    dry_run: bool,
) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    topsis_csv = output_dir / "ewm_topsis_result.csv"
    cmd = [
        "python",
        str(root / "scripts" / "multi_criteria_resilience_assessment.py"),
        "--policy-comparison",
        str(policy_csv),
        "--worst-detail",
        str(worst_csv),
        "--output-dir",
        str(output_dir),
    ]
    maybe_run(cmd=cmd, expected_outputs=[topsis_csv], cwd=root, reuse_existing=reuse_existing, dry_run=dry_run)
    return topsis_csv


def run_warning_stage(
    root: Path,
    paths_cfg: dict[str, Any],
    warning_cfg: dict[str, Any],
    failure_csv: Path,
    contingency_tensor: Path,
    load_priority_csv: Path,
    output_dir: Path,
    seed: int,
    reuse_existing: bool,
    dry_run: bool,
) -> dict[str, Path]:
    if not bool(warning_cfg.get("enabled", True)):
        return {}

    output_dir.mkdir(parents=True, exist_ok=True)
    default_aligned = str(Path(str(paths_cfg["trim_input"])).with_name("aligned_merged.csv"))
    aligned_raw = str(paths_cfg.get("aligned", default_aligned))
    aligned_path = resolve_path(root, aligned_raw)

    line_csv = output_dir / "line_risk_prediction.csv"
    nk_csv = output_dir / "nk_failure_risk.csv"
    critical_csv = output_dir / "critical_load_risk.csv"
    report_json = output_dir / "warning_report.json"

    cmd = [
        "python",
        str(root / "scripts" / "gnn_warning_module.py"),
        "--grid",
        str(resolve_path(root, str(paths_cfg["grid"]))),
        "--aligned",
        str(aligned_path),
        "--failure-csv",
        str(failure_csv),
        "--contingency-tensor",
        str(contingency_tensor),
        "--load-priority-csv",
        str(load_priority_csv),
        "--output-dir",
        str(output_dir),
        "--horizon-hours",
        str(warning_cfg.get("horizon_hours", 24)),
        "--horizon-start-index",
        str(warning_cfg.get("horizon_start_index", 0)),
        "--train-ratio",
        str(warning_cfg.get("train_ratio", 0.7)),
        "--hidden-dim",
        str(warning_cfg.get("hidden_dim", 64)),
        "--epochs",
        str(warning_cfg.get("epochs", 600)),
        "--lr",
        str(warning_cfg.get("lr", 1e-2)),
        "--weight-decay",
        str(warning_cfg.get("weight_decay", 1e-4)),
        "--mc-scenarios",
        str(warning_cfg.get("mc_scenarios", 3000)),
        "--risk-high-threshold",
        str(warning_cfg.get("risk_high_threshold", 0.70)),
        "--risk-medium-threshold",
        str(warning_cfg.get("risk_medium_threshold", 0.40)),
        "--hour-trigger-threshold",
        str(warning_cfg.get("hour_trigger_threshold", 0.35)),
        "--risk-mean-floor",
        str(warning_cfg.get("risk_mean_floor", 0.18)),
        "--risk-mean-cap",
        str(warning_cfg.get("risk_mean_cap", 0.55)),
        "--scenario-intensity-alpha",
        str(warning_cfg.get("scenario_intensity_alpha", 2.0)),
        "--scenario-intensity-beta",
        str(warning_cfg.get("scenario_intensity_beta", 6.0)),
        "--metapath-topk",
        str(warning_cfg.get("metapath_topk", 6)),
        "--risk-weight-alpha",
        str(warning_cfg.get("risk_weight_alpha", 2.0)),
        "--risk-weight-beta",
        str(warning_cfg.get("risk_weight_beta", 4.0)),
        "--risk-weight-threshold",
        str(warning_cfg.get("risk_weight_threshold", 0.10)),
        "--metapath-gate-reg-lambda",
        str(warning_cfg.get("metapath_gate_reg_lambda", 8e-4)),
        "--metapath-attention-entropy-reg-lambda",
        str(warning_cfg.get("metapath_attention_entropy_reg_lambda", 0.0)),
        "--metapath-warmup-epochs",
        str(warning_cfg.get("metapath_warmup_epochs", 35)),
        "--high-risk-threshold",
        str(warning_cfg.get("high_risk_threshold", 0.10)),
        "--top-risk-quantile",
        str(warning_cfg.get("top_risk_quantile", 0.90)),
        "--seed",
        str(seed),
    ]
    if bool(warning_cfg.get("metapath_v1_enabled", True)):
        cmd.append("--metapath-v1-enabled")
    else:
        cmd.append("--no-metapath-v1-enabled")
    if bool(warning_cfg.get("run_baseline_comparison", False)):
        cmd.append("--run-baseline-comparison")
    else:
        cmd.append("--no-run-baseline-comparison")
    if bool(warning_cfg.get("risk_weight_on_metapath_only", True)):
        cmd.append("--risk-weight-on-metapath-only")
    else:
        cmd.append("--no-risk-weight-on-metapath-only")
    maybe_run(
        cmd=cmd,
        expected_outputs=[line_csv, nk_csv, critical_csv, report_json],
        cwd=root,
        reuse_existing=reuse_existing,
        dry_run=dry_run,
    )
    return {
        "line_risk_prediction_csv": line_csv,
        "nk_failure_risk_csv": nk_csv,
        "critical_load_risk_csv": critical_csv,
        "warning_report_json": report_json,
    }


def run_dispatch_optimization_stage(
    root: Path,
    paths_cfg: dict[str, Any],
    dispatch_cfg: dict[str, Any],
    failure_csv: Path,
    uncertainty_dir: Path,
    line_risk_csv: Path | None,
    load_priority_csv: Path | None,
    output_dir: Path,
    seed: int,
    max_steps: int | None,
    reuse_existing: bool,
    dry_run: bool,
) -> dict[str, Path]:
    if not bool(dispatch_cfg.get("enabled", True)):
        return {}

    output_dir.mkdir(parents=True, exist_ok=True)
    report_json = output_dir / "dispatch_optimization_report.json"
    strategy_selection_csv = output_dir / "dispatch_strategy_selection.csv"
    strategy_summary_csv = output_dir / "dispatch_active_strategy_summary.csv"
    contextual_unit_csv = output_dir / "contextual_dispatch_unit_schedule.csv"
    contextual_load_csv = output_dir / "contextual_dispatch_load_shedding.csv"
    line_flow_csv = output_dir / "line_flow.csv"
    export_diagnostics = bool(dispatch_cfg.get("export_diagnostics", False))
    comparison_csv = output_dir / "dispatch_model_comparison.csv"
    topsis_csv = output_dir / "dispatch_ewm_topsis_result.csv"

    horizon_hours = int(dispatch_cfg.get("horizon_hours", 24))
    if max_steps is not None:
        horizon_hours = max(1, min(horizon_hours, int(max_steps)))

    cmd = [
        "python",
        str(root / "scripts" / "dispatch_optimization_module.py"),
        "--grid",
        str(resolve_path(root, str(paths_cfg["grid"]))),
        "--trim-input",
        str(resolve_path(root, str(paths_cfg["trim_input"]))),
        "--failure-csv",
        str(failure_csv),
        "--uncertainty-dir",
        str(uncertainty_dir),
        "--output-dir",
        str(output_dir),
        "--horizon-hours",
        str(horizon_hours),
        "--horizon-start-index",
        str(dispatch_cfg.get("horizon_start_index", 0)),
        "--reserve-ratio",
        str(dispatch_cfg.get("reserve_ratio", 0.15)),
        "--voll",
        str(dispatch_cfg.get("voll", 1200.0)),
        "--redispatch-penalty",
        str(dispatch_cfg.get("redispatch_penalty", 30.0)),
        "--line-derate-coeff",
        str(dispatch_cfg.get("line_derate_coeff", 0.35)),
        "--robust-line-factor",
        str(dispatch_cfg.get("robust_line_factor", 0.90)),
        "--stochastic-scenarios",
        str(dispatch_cfg.get("stochastic_scenarios", 6)),
        "--robust-set-size",
        str(dispatch_cfg.get("robust_set_size", 5)),
        "--robust-wind-low",
        str(dispatch_cfg.get("robust_wind_low", 0.7)),
        "--robust-wind-high",
        str(dispatch_cfg.get("robust_wind_high", 1.3)),
        "--robust-load-low",
        str(dispatch_cfg.get("robust_load_low", 0.9)),
        "--robust-load-high",
        str(dispatch_cfg.get("robust_load_high", 1.2)),
        "--slack-dispatchable-capacity",
        str(dispatch_cfg.get("slack_dispatchable_capacity", 1.20)),
        "--emergency-dg-capacities",
        str(dispatch_cfg.get("emergency_dg_capacities", "0.18,0.15,0.10")),
        "--time-limit-sec",
        str(dispatch_cfg.get("time_limit_sec", 45.0)),
        "--mip-gap",
        str(dispatch_cfg.get("mip_gap", 0.02)),
        "--strategy-mode",
        str(dispatch_cfg.get("strategy_mode", "contextual")),
        "--stochastic-uncertainty-threshold",
        str(dispatch_cfg.get("stochastic_uncertainty_threshold", 0.22)),
        "--stochastic-line-risk-threshold",
        str(dispatch_cfg.get("stochastic_line_risk_threshold", 0.45)),
        "--robust-line-risk-threshold",
        str(dispatch_cfg.get("robust_line_risk_threshold", 0.72)),
        "--robust-nk-threshold",
        str(dispatch_cfg.get("robust_nk_threshold", 3.0)),
        "--robust-critical-threshold",
        str(dispatch_cfg.get("robust_critical_threshold", 0.22)),
        "--robust-high-line-ratio-threshold",
        str(dispatch_cfg.get("robust_high_line_ratio_threshold", 0.30)),
        "--seed",
        str(seed),
    ]
    if line_risk_csv is not None:
        cmd.extend(["--line-risk-csv", str(line_risk_csv)])
    if load_priority_csv is not None:
        cmd.extend(["--load-priority-csv", str(load_priority_csv)])
    if export_diagnostics:
        cmd.append("--export-diagnostics")

    expected_outputs = [
        report_json,
        strategy_selection_csv,
        strategy_summary_csv,
        contextual_unit_csv,
        contextual_load_csv,
        line_flow_csv,
    ]
    if export_diagnostics:
        expected_outputs.extend([comparison_csv, topsis_csv])

    maybe_run(
        cmd=cmd,
        expected_outputs=expected_outputs,
        cwd=root,
        reuse_existing=reuse_existing,
        dry_run=dry_run,
    )
    outputs: dict[str, Path] = {
        "dispatch_optimization_report_json": report_json,
        "dispatch_strategy_selection_csv": strategy_selection_csv,
        "dispatch_active_strategy_summary_csv": strategy_summary_csv,
        "contextual_dispatch_unit_schedule_csv": contextual_unit_csv,
        "contextual_dispatch_load_shedding_csv": contextual_load_csv,
        "dispatch_line_flow_csv": line_flow_csv,
    }
    if export_diagnostics:
        outputs["dispatch_model_comparison_csv"] = comparison_csv
        outputs["dispatch_ewm_topsis_result_csv"] = topsis_csv
    return outputs


def run_steady_state_physics_stage(
    root: Path,
    paths_cfg: dict[str, Any],
    physics_cfg: dict[str, Any],
    dispatch_dir: Path,
    output_dir: Path,
    max_steps: int | None,
    reuse_existing: bool,
    dry_run: bool,
) -> dict[str, Path]:
    if not bool(physics_cfg.get("enabled", False)):
        return {}

    output_dir.mkdir(parents=True, exist_ok=True)
    summary_json = output_dir / "feasibility_summary.json"
    violations_csv = output_dir / "physics_violations.csv"
    corrected_load_csv = output_dir / "corrected_contextual_dispatch_load_shedding.csv"
    corrected_unit_csv = output_dir / "corrected_contextual_dispatch_unit_schedule.csv"
    correction_log_csv = output_dir / "correction_log.csv"
    critical_lines_csv = output_dir / "critical_lines_hourly.csv"
    vulnerable_buses_csv = output_dir / "vulnerable_buses_hourly.csv"
    load_area_csv = output_dir / "load_area_risk_hourly.csv"
    generator_actions_csv = output_dir / "generator_action_candidates.csv"
    rule_actions_csv = output_dir / "rule_based_actions_hourly.csv"
    rule_corrected_load_csv = output_dir / "rule_corrected_dispatch_load_shedding.csv"
    rule_corrected_unit_csv = output_dir / "rule_corrected_dispatch_unit_schedule.csv"
    rule_corrected_line_csv = output_dir / "rule_corrected_line_flow.csv"
    rule_action_log_csv = output_dir / "rule_action_execution_log.csv"
    rule_closure_summary_json = output_dir / "rule_closure_summary.json"
    experiment_metrics_csv = output_dir / "experiment_metrics_comparison.csv"
    action_type_summary_csv = output_dir / "action_type_summary.csv"
    hourly_closure_comparison_csv = output_dir / "hourly_closure_comparison.csv"

    horizon_hours = int(physics_cfg.get("horizon_hours", 24))
    if max_steps is not None:
        horizon_hours = max(1, min(horizon_hours, int(max_steps)))

    cmd = [
        "python",
        str(root / "scripts" / "steady_state_physics_module.py"),
        "--grid",
        str(resolve_path(root, str(paths_cfg["grid"]))),
        "--dispatch-dir",
        str(dispatch_dir),
        "--output-dir",
        str(output_dir),
        "--horizon-hours",
        str(horizon_hours),
        "--value-tol",
        str(physics_cfg.get("value_tolerance", 1e-9)),
        "--line-overload-tol",
        str(physics_cfg.get("line_overload_tolerance", 1e-9)),
    ]
    if bool(physics_cfg.get("auto_correct", True)):
        cmd.append("--auto-correct")
    else:
        cmd.append("--no-auto-correct")

    expected_outputs = [
        summary_json,
        violations_csv,
        critical_lines_csv,
        vulnerable_buses_csv,
        load_area_csv,
        generator_actions_csv,
        rule_actions_csv,
        rule_corrected_load_csv,
        rule_corrected_unit_csv,
        rule_corrected_line_csv,
        rule_action_log_csv,
        rule_closure_summary_json,
        experiment_metrics_csv,
        action_type_summary_csv,
        hourly_closure_comparison_csv,
    ]
    if bool(physics_cfg.get("auto_correct", True)):
        expected_outputs.extend([corrected_load_csv, corrected_unit_csv, correction_log_csv])
    maybe_run(
        cmd=cmd,
        expected_outputs=expected_outputs,
        cwd=root,
        reuse_existing=reuse_existing,
        dry_run=dry_run,
    )
    outputs: dict[str, Path] = {
        "steady_state_feasibility_summary_json": summary_json,
        "steady_state_physics_violations_csv": violations_csv,
        "steady_state_critical_lines_hourly_csv": critical_lines_csv,
        "steady_state_vulnerable_buses_hourly_csv": vulnerable_buses_csv,
        "steady_state_load_area_risk_hourly_csv": load_area_csv,
        "steady_state_generator_action_candidates_csv": generator_actions_csv,
        "steady_state_rule_based_actions_hourly_csv": rule_actions_csv,
        "steady_state_rule_corrected_dispatch_load_shedding_csv": rule_corrected_load_csv,
        "steady_state_rule_corrected_dispatch_unit_schedule_csv": rule_corrected_unit_csv,
        "steady_state_rule_corrected_line_flow_csv": rule_corrected_line_csv,
        "steady_state_rule_action_execution_log_csv": rule_action_log_csv,
        "steady_state_rule_closure_summary_json": rule_closure_summary_json,
        "steady_state_experiment_metrics_comparison_csv": experiment_metrics_csv,
        "steady_state_action_type_summary_csv": action_type_summary_csv,
        "steady_state_hourly_closure_comparison_csv": hourly_closure_comparison_csv,
    }
    if bool(physics_cfg.get("auto_correct", True)):
        outputs["steady_state_corrected_load_shedding_csv"] = corrected_load_csv
        outputs["steady_state_corrected_unit_schedule_csv"] = corrected_unit_csv
        outputs["steady_state_correction_log_csv"] = correction_log_csv
    return outputs


def read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="GridAgent unified framework: wind-pv -> failure -> contingency -> scheduling -> multi-criteria resilience."
    )
    parser.add_argument(
        "--config",
        default="configs/gridagent_framework.formal2024.json",
        help="Framework config json.",
    )
    parser.add_argument(
        "--mode",
        choices=("baseline", "adaptive"),
        default="adaptive",
        help="Run baseline single-chain or adaptive edge-cloud collaborative scheduling.",
    )
    parser.add_argument("--run-tag", default="", help="Optional output run tag. If empty, use timestamp.")
    parser.add_argument("--seed", type=int, default=None, help="Optional global seed override.")
    parser.add_argument("--max-steps", type=int, default=None, help="Optional debug truncation for time steps.")
    parser.add_argument(
        "--no-reuse-existing",
        action="store_true",
        help="Disable output cache reuse.",
    )
    parser.add_argument("--dry-run", action="store_true", help="Print commands only.")
    return parser.parse_args()


def run_baseline(
    root: Path,
    config: dict[str, Any],
    run_root: Path,
    seed: int,
    max_steps: int | None,
    reuse_existing: bool,
    dry_run: bool,
) -> dict[str, Any]:
    paths_cfg = config["paths"]
    wind_cfg = config["wind_pv"]
    failure_cfg = config["failure"]
    contingency_cfg = config["contingency"]
    scheduling_cfg = config["scheduling"]
    warning_cfg = config.get("warning", {})
    dispatch_cfg = config.get("dispatch_optimization", {})
    physics_cfg = config.get("steady_state_physics", {})
    baseline_cfg = config["baseline"]

    uncertainty_dir = run_wind_pv_stage(
        root=root,
        run_root=run_root,
        wind_cfg=wind_cfg,
        max_steps=max_steps,
        reuse_existing=reuse_existing,
        dry_run=dry_run,
    )

    failure_model = str(baseline_cfg.get("failure_model", "schloemer"))
    contingency_method = str(baseline_cfg.get("contingency_method", "c3po_ref"))
    reserve_ratio = float(baseline_cfg.get("reserve_ratio", 0.15))
    n_scenarios = int(baseline_cfg.get("n_scenarios", 256))

    failure_csv = run_failure_stage_for_model(
        root=root,
        run_root=run_root,
        paths_cfg=paths_cfg,
        failure_cfg=failure_cfg,
        model=failure_model,
        max_steps=max_steps,
        reuse_existing=reuse_existing,
        dry_run=dry_run,
    )

    contingency_dir = run_root / "stage3_contingency" / failure_model
    tensor_map = run_contingency_stage(
        root=root,
        paths_cfg=paths_cfg,
        contingency_cfg=contingency_cfg,
        failure_csv=failure_csv,
        output_dir=contingency_dir,
        methods=[contingency_method],
        n_scenarios=n_scenarios,
        seed=seed,
        max_steps=max_steps,
        reuse_existing=reuse_existing,
        dry_run=dry_run,
    )
    tensor = tensor_map[contingency_method]
    contingency_scenarios_csv = contingency_dir / f"contingency_scenarios_{contingency_method}.csv"
    if not contingency_scenarios_csv.exists():
        fallback_scenarios = contingency_dir / "contingency_scenarios.csv"
        if fallback_scenarios.exists():
            contingency_scenarios_csv = fallback_scenarios

    sched_dir = run_root / "stage4_scheduling" / f"{failure_model}__{contingency_method}__rr{reserve_tag(reserve_ratio)}"
    policy_csv, worst_csv = run_scheduling_stage(
        root=root,
        paths_cfg=paths_cfg,
        scheduling_cfg=scheduling_cfg,
        uncertainty_dir=uncertainty_dir,
        failure_csv=failure_csv,
        contingency_tensor=tensor,
        output_dir=sched_dir,
        reserve_ratio=reserve_ratio,
        seed=seed,
        reuse_existing=reuse_existing,
        dry_run=dry_run,
    )

    assess_dir = run_root / "stage5_assessment"
    topsis_csv = run_assessment_stage(
        root=root,
        policy_csv=policy_csv,
        worst_csv=worst_csv,
        output_dir=assess_dir,
        reuse_existing=reuse_existing,
        dry_run=dry_run,
    )

    warning_subdir = str(warning_cfg.get("output_subdir", "stage6_warning"))
    warning_dir = run_root / warning_subdir
    warning_outputs = run_warning_stage(
        root=root,
        paths_cfg=paths_cfg,
        warning_cfg=warning_cfg,
        failure_csv=failure_csv,
        contingency_tensor=tensor,
        load_priority_csv=sched_dir / "load_bus_priority_profile.csv",
        output_dir=warning_dir,
        seed=seed + 2000,
        reuse_existing=reuse_existing,
        dry_run=dry_run,
    )

    dispatch_subdir = str(dispatch_cfg.get("output_subdir", "stage7_dispatch_optimization"))
    dispatch_dir = run_root / dispatch_subdir
    line_risk_csv = warning_outputs.get("line_risk_prediction_csv")
    dispatch_outputs = run_dispatch_optimization_stage(
        root=root,
        paths_cfg=paths_cfg,
        dispatch_cfg=dispatch_cfg,
        failure_csv=failure_csv,
        uncertainty_dir=uncertainty_dir,
        line_risk_csv=line_risk_csv if line_risk_csv is not None else None,
        load_priority_csv=sched_dir / "load_bus_priority_profile.csv",
        output_dir=dispatch_dir,
        seed=seed + 3000,
        max_steps=max_steps,
        reuse_existing=reuse_existing,
        dry_run=dry_run,
    )
    physics_subdir = str(physics_cfg.get("output_subdir", "stage8_steady_state_physics"))
    physics_dir = run_root / physics_subdir
    physics_outputs = run_steady_state_physics_stage(
        root=root,
        paths_cfg=paths_cfg,
        physics_cfg=physics_cfg,
        dispatch_dir=dispatch_dir,
        output_dir=physics_dir,
        max_steps=max_steps,
        reuse_existing=reuse_existing,
        dry_run=dry_run,
    )

    metrics = evaluate_candidate_run(
        policy_csv=policy_csv,
        worst_csv=worst_csv,
        failure_model=failure_model,
        contingency_method=contingency_method,
        reserve_ratio=reserve_ratio,
        run_tag=f"{failure_model}__{contingency_method}__rr{reserve_tag(reserve_ratio)}",
        run_dir=sched_dir,
    ) if not dry_run else {}

    return {
        "mode": "baseline",
        "selected_chain": {
            "failure_model": failure_model,
            "contingency_method": contingency_method,
            "reserve_ratio": reserve_ratio,
            "n_scenarios": n_scenarios,
        },
        "outputs": {
            "uncertainty_dir": str(uncertainty_dir),
            "failure_csv": str(failure_csv),
            "contingency_tensor": str(tensor),
            "contingency_scenarios_csv": str(contingency_scenarios_csv),
            "scheduling_dir": str(sched_dir),
            "policy_comparison_csv": str(policy_csv),
            "worst_detail_csv": str(worst_csv),
            "assessment_dir": str(assess_dir),
            "assessment_topsis_csv": str(topsis_csv),
            **{k: str(v) for k, v in warning_outputs.items()},
            **{k: str(v) for k, v in dispatch_outputs.items()},
            **{k: str(v) for k, v in physics_outputs.items()},
        },
        "priority_policy_metrics": metrics,
    }


def run_adaptive(
    root: Path,
    config: dict[str, Any],
    run_root: Path,
    seed: int,
    max_steps: int | None,
    reuse_existing: bool,
    dry_run: bool,
) -> dict[str, Any]:
    paths_cfg = config["paths"]
    wind_cfg = config["wind_pv"]
    failure_cfg = config["failure"]
    contingency_cfg = config["contingency"]
    scheduling_cfg = config["scheduling"]
    warning_cfg = config.get("warning", {})
    dispatch_cfg = config.get("dispatch_optimization", {})
    physics_cfg = config.get("steady_state_physics", {})
    adaptive_cfg = config["adaptive_scheduler"]
    edge_cfg = adaptive_cfg["edge"]
    cloud_cfg = adaptive_cfg["cloud"]

    uncertainty_dir = run_wind_pv_stage(
        root=root,
        run_root=run_root,
        wind_cfg=wind_cfg,
        max_steps=max_steps,
        reuse_existing=reuse_existing,
        dry_run=dry_run,
    )

    failure_models = [str(x) for x in edge_cfg.get("failure_models", ["schloemer", "batts"])]
    contingency_methods = [str(x) for x in edge_cfg.get("contingency_methods", list(ALL_CONTINGENCY_METHODS))]
    reserve_ratios = [float(x) for x in edge_cfg.get("reserve_ratios", [0.05, 0.15, 0.30])]
    edge_n_scenarios = int(edge_cfg.get("n_scenarios", 64))
    cloud_n_scenarios = int(cloud_cfg.get("n_scenarios", 256))
    top_k = int(cloud_cfg.get("top_k", 4))
    diversity_on_method = bool(cloud_cfg.get("diversity_on_contingency", True))

    if top_k <= 0:
        raise ValueError("adaptive_scheduler.cloud.top_k must be >= 1")

    failure_csv_map: dict[str, Path] = {}
    for model in failure_models:
        failure_csv_map[model] = run_failure_stage_for_model(
            root=root,
            run_root=run_root,
            paths_cfg=paths_cfg,
            failure_cfg=failure_cfg,
            model=model,
            max_steps=max_steps,
            reuse_existing=reuse_existing,
            dry_run=dry_run,
        )

    edge_contingency_map: dict[tuple[str, str], Path] = {}
    for model in failure_models:
        edge_cont_dir = run_root / "edge" / "contingency" / model
        t_map = run_contingency_stage(
            root=root,
            paths_cfg=paths_cfg,
            contingency_cfg=contingency_cfg,
            failure_csv=failure_csv_map[model],
            output_dir=edge_cont_dir,
            methods=contingency_methods,
            n_scenarios=edge_n_scenarios,
            seed=seed,
            max_steps=max_steps,
            reuse_existing=reuse_existing,
            dry_run=dry_run,
        )
        for method, tensor in t_map.items():
            edge_contingency_map[(model, method)] = tensor

    edge_records: list[dict[str, Any]] = []
    for model in failure_models:
        for method in contingency_methods:
            tensor = edge_contingency_map[(model, method)]
            for rr in reserve_ratios:
                tag = f"{model}__{method}__rr{reserve_tag(rr)}"
                run_dir = run_root / "edge" / "runs" / tag
                policy_csv, worst_csv = run_scheduling_stage(
                    root=root,
                    paths_cfg=paths_cfg,
                    scheduling_cfg=scheduling_cfg,
                    uncertainty_dir=uncertainty_dir,
                    failure_csv=failure_csv_map[model],
                    contingency_tensor=tensor,
                    output_dir=run_dir,
                    reserve_ratio=rr,
                    seed=seed,
                    reuse_existing=reuse_existing,
                    dry_run=dry_run,
                )
                if not dry_run:
                    edge_records.append(
                        evaluate_candidate_run(
                            policy_csv=policy_csv,
                            worst_csv=worst_csv,
                            failure_model=model,
                            contingency_method=method,
                            reserve_ratio=rr,
                            run_tag=tag,
                            run_dir=run_dir,
                        )
                    )

    if dry_run:
        return {
            "mode": "adaptive",
            "dry_run": True,
            "outputs": {
                "uncertainty_dir": str(uncertainty_dir),
            },
        }

    edge_df = pd.DataFrame(edge_records)
    edge_ranked, edge_w = score_candidates(edge_df)
    edge_csv = run_root / "edge" / "edge_candidates_scored.csv"
    edge_w_csv = run_root / "edge" / "edge_indicator_weights.csv"
    edge_csv.parent.mkdir(parents=True, exist_ok=True)
    edge_ranked.to_csv(edge_csv, index=False, encoding="utf-8")
    edge_w.to_csv(edge_w_csv, index=False, encoding="utf-8")

    selected_cloud = pick_cloud_candidates(edge_ranked=edge_ranked, top_k=top_k, diversity_on_method=diversity_on_method)
    selected_cloud_csv = run_root / "edge" / "edge_selected_for_cloud.csv"
    selected_cloud.to_csv(selected_cloud_csv, index=False, encoding="utf-8")

    cloud_tensor_map: dict[tuple[str, str], Path] = {}
    for _, row in selected_cloud.iterrows():
        model = str(row["failure_model"])
        method = str(row["contingency_method"])
        key = (model, method)
        if key in cloud_tensor_map:
            continue
        cloud_cont_dir = run_root / "cloud" / "contingency" / model
        t_map = run_contingency_stage(
            root=root,
            paths_cfg=paths_cfg,
            contingency_cfg=contingency_cfg,
            failure_csv=failure_csv_map[model],
            output_dir=cloud_cont_dir,
            methods=[method],
            n_scenarios=cloud_n_scenarios,
            seed=seed + 1000,
            max_steps=max_steps,
            reuse_existing=reuse_existing,
            dry_run=dry_run,
        )
        cloud_tensor_map[key] = t_map[method]

    cloud_records: list[dict[str, Any]] = []
    for _, row in selected_cloud.iterrows():
        model = str(row["failure_model"])
        method = str(row["contingency_method"])
        rr = float(row["reserve_ratio"])
        tag = f"{model}__{method}__rr{reserve_tag(rr)}"
        run_dir = run_root / "cloud" / "runs" / tag
        policy_csv, worst_csv = run_scheduling_stage(
            root=root,
            paths_cfg=paths_cfg,
            scheduling_cfg=scheduling_cfg,
            uncertainty_dir=uncertainty_dir,
            failure_csv=failure_csv_map[model],
            contingency_tensor=cloud_tensor_map[(model, method)],
            output_dir=run_dir,
            reserve_ratio=rr,
            seed=seed + 1000,
            reuse_existing=reuse_existing,
            dry_run=dry_run,
        )
        cloud_records.append(
            evaluate_candidate_run(
                policy_csv=policy_csv,
                worst_csv=worst_csv,
                failure_model=model,
                contingency_method=method,
                reserve_ratio=rr,
                run_tag=tag,
                run_dir=run_dir,
            )
        )

    cloud_df = pd.DataFrame(cloud_records)
    cloud_ranked, cloud_w = score_candidates(cloud_df)
    cloud_csv = run_root / "cloud" / "cloud_candidates_scored.csv"
    cloud_w_csv = run_root / "cloud" / "cloud_indicator_weights.csv"
    cloud_csv.parent.mkdir(parents=True, exist_ok=True)
    cloud_ranked.to_csv(cloud_csv, index=False, encoding="utf-8")
    cloud_w.to_csv(cloud_w_csv, index=False, encoding="utf-8")

    best = cloud_ranked.iloc[0]
    best_policy_csv = Path(str(best["run_dir"])) / "policy_comparison.csv"
    best_worst_csv = Path(str(best["run_dir"])) / "worst_scenario_shedding_detail.csv"
    assessment_dir = run_root / "stage5_assessment_best"
    topsis_csv = run_assessment_stage(
        root=root,
        policy_csv=best_policy_csv,
        worst_csv=best_worst_csv,
        output_dir=assessment_dir,
        reuse_existing=reuse_existing,
        dry_run=dry_run,
    )

    best_failure_model = str(best["failure_model"])
    best_cont_method = str(best["contingency_method"])
    best_contingency_dir = run_root / "cloud" / "contingency" / best_failure_model
    best_contingency_scenarios_csv = best_contingency_dir / f"contingency_scenarios_{best_cont_method}.csv"
    if not best_contingency_scenarios_csv.exists():
        fallback_scenarios = best_contingency_dir / "contingency_scenarios.csv"
        if fallback_scenarios.exists():
            best_contingency_scenarios_csv = fallback_scenarios
    warning_subdir = str(warning_cfg.get("output_subdir", "stage6_warning"))
    warning_dir = run_root / warning_subdir
    warning_outputs = run_warning_stage(
        root=root,
        paths_cfg=paths_cfg,
        warning_cfg=warning_cfg,
        failure_csv=failure_csv_map[best_failure_model],
        contingency_tensor=cloud_tensor_map[(best_failure_model, best_cont_method)],
        load_priority_csv=Path(str(best["run_dir"])) / "load_bus_priority_profile.csv",
        output_dir=warning_dir,
        seed=seed + 2000,
        reuse_existing=reuse_existing,
        dry_run=dry_run,
    )

    dispatch_subdir = str(dispatch_cfg.get("output_subdir", "stage7_dispatch_optimization"))
    dispatch_dir = run_root / dispatch_subdir
    line_risk_csv = warning_outputs.get("line_risk_prediction_csv")
    dispatch_outputs = run_dispatch_optimization_stage(
        root=root,
        paths_cfg=paths_cfg,
        dispatch_cfg=dispatch_cfg,
        failure_csv=failure_csv_map[best_failure_model],
        uncertainty_dir=uncertainty_dir,
        line_risk_csv=line_risk_csv if line_risk_csv is not None else None,
        load_priority_csv=Path(str(best["run_dir"])) / "load_bus_priority_profile.csv",
        output_dir=dispatch_dir,
        seed=seed + 3000,
        max_steps=max_steps,
        reuse_existing=reuse_existing,
        dry_run=dry_run,
    )
    physics_subdir = str(physics_cfg.get("output_subdir", "stage8_steady_state_physics"))
    physics_dir = run_root / physics_subdir
    physics_outputs = run_steady_state_physics_stage(
        root=root,
        paths_cfg=paths_cfg,
        physics_cfg=physics_cfg,
        dispatch_dir=dispatch_dir,
        output_dir=physics_dir,
        max_steps=max_steps,
        reuse_existing=reuse_existing,
        dry_run=dry_run,
    )

    return {
        "mode": "adaptive",
        "edge_cloud_strategy": {
            "edge_stage": "low-cost quick screening over full candidate space",
            "cloud_stage": "high-fidelity rerun on selected candidates",
            "selection_policy": {
                "top_k": top_k,
                "diversity_on_contingency_method": diversity_on_method,
            },
        },
        "search_space": {
            "failure_models": failure_models,
            "contingency_methods": contingency_methods,
            "reserve_ratios": reserve_ratios,
            "edge_n_scenarios": edge_n_scenarios,
            "cloud_n_scenarios": cloud_n_scenarios,
            "edge_run_count": int(len(edge_ranked)),
            "cloud_run_count": int(len(cloud_ranked)),
        },
        "best_candidate": {
            "run_tag": str(best["run_tag"]),
            "failure_model": str(best["failure_model"]),
            "contingency_method": str(best["contingency_method"]),
            "reserve_ratio": float(best["reserve_ratio"]),
            "TOPSIS_Score": float(best["TOPSIS_Score"]),
        },
        "outputs": {
            "uncertainty_dir": str(uncertainty_dir),
            "failure_csv_by_model": {k: str(v) for k, v in failure_csv_map.items()},
            "edge_candidates_scored_csv": str(edge_csv),
            "edge_indicator_weights_csv": str(edge_w_csv),
            "edge_selected_for_cloud_csv": str(selected_cloud_csv),
            "cloud_candidates_scored_csv": str(cloud_csv),
            "cloud_indicator_weights_csv": str(cloud_w_csv),
            "best_assessment_dir": str(assessment_dir),
            "best_assessment_topsis_csv": str(topsis_csv),
            "best_contingency_scenarios_csv": str(best_contingency_scenarios_csv),
            **{k: str(v) for k, v in warning_outputs.items()},
            **{k: str(v) for k, v in dispatch_outputs.items()},
            **{k: str(v) for k, v in physics_outputs.items()},
        },
    }


def main() -> None:
    args = parse_args()
    root = project_root()
    config_path = resolve_path(root, args.config)
    if not config_path.exists():
        raise FileNotFoundError(f"config not found: {config_path}")
    config = read_json(config_path)

    run_tag = args.run_tag.strip() or datetime.now().strftime("%Y%m%d_%H%M%S")
    output_root = resolve_path(root, str(config.get("output_root", "results/gridagent_framework")))
    run_root = output_root / run_tag
    run_root.mkdir(parents=True, exist_ok=True)

    reuse_existing = not args.no_reuse_existing
    cfg_seed = int(config.get("seed", 42))
    seed = int(args.seed) if args.seed is not None else cfg_seed
    started_at = datetime.now().isoformat(timespec="seconds")

    if args.mode == "baseline":
        details = run_baseline(
            root=root,
            config=config,
            run_root=run_root,
            seed=seed,
            max_steps=args.max_steps,
            reuse_existing=reuse_existing,
            dry_run=args.dry_run,
        )
    else:
        details = run_adaptive(
            root=root,
            config=config,
            run_root=run_root,
            seed=seed,
            max_steps=args.max_steps,
            reuse_existing=reuse_existing,
            dry_run=args.dry_run,
        )

    finished_at = datetime.now().isoformat(timespec="seconds")
    summary = {
        "framework": "GridAgent Framework",
        "timestamp": {
            "started_at": started_at,
            "finished_at": finished_at,
        },
        "config_path": str(config_path),
        "run_root": str(run_root),
        "mode": args.mode,
        "seed": seed,
        "max_steps": args.max_steps,
        "reuse_existing": reuse_existing,
        "dry_run": bool(args.dry_run),
        "details": details,
    }

    summary_path = run_root / "framework_report.json"
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    latest_path = output_root / "latest_run.json"
    latest_path.write_text(json.dumps({"run_tag": run_tag, "run_root": str(run_root)}, ensure_ascii=False, indent=2), encoding="utf-8")

    print("\nDone.")
    print(f"framework report -> {summary_path}")
    print(f"latest pointer  -> {latest_path}")


if __name__ == "__main__":
    main()
