from __future__ import annotations

import argparse
import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score, roc_auc_score


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


def format_progress(done: int, total: int) -> str:
    if total <= 0:
        return "进度：已完成 0/0 组（约 0.0%）"
    pct = 100.0 * float(done) / float(total)
    return f"进度：已完成 {done}/{total} 组（约 {pct:.1f}%）"


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


def load_failure_p_line(path: Path) -> tuple[np.ndarray, pd.DatetimeIndex, list[str]]:
    frame = pd.read_csv(path)
    frame["timestamp"] = pd.to_datetime(frame["timestamp"], errors="coerce")
    if frame["timestamp"].isna().any():
        raise ValueError(f"invalid timestamp in failure csv: {path}")
    pivot = (
        frame.pivot_table(index="timestamp", columns="line_id", values="p_line", aggfunc="mean")
        .sort_index()
        .sort_index(axis=1)
    )
    if pivot.empty:
        raise ValueError(f"empty failure matrix: {path}")
    return pivot.to_numpy(dtype=float), pd.DatetimeIndex(pivot.index), [str(c) for c in pivot.columns]


def warning_metrics(failure_csv: Path, contingency_tensor: Path, top_ratio: float = 0.1) -> dict[str, float]:
    p_line, _, _ = load_failure_p_line(failure_csv)
    outages = np.load(contingency_tensor)
    if outages.ndim != 3:
        raise ValueError(f"contingency tensor must be 3D: {contingency_tensor}")
    empirical = outages.mean(axis=0)

    t = min(p_line.shape[0], empirical.shape[0])
    l = min(p_line.shape[1], empirical.shape[1])
    p = np.clip(p_line[:t, :l], 0.0, 1.0)
    y = np.clip(empirical[:t, :l], 0.0, 1.0)

    p_flat = p.reshape(-1)
    y_flat = y.reshape(-1)
    brier = float(np.mean((p_flat - y_flat) ** 2))

    y_label = (y_flat >= np.quantile(y_flat, 0.90)).astype(int)
    if y_label.max() == y_label.min():
        auroc = np.nan
        auprc = np.nan
    else:
        auroc = float(roc_auc_score(y_label, p_flat))
        auprc = float(average_precision_score(y_label, p_flat))

    k = max(1, int(np.ceil(top_ratio * len(p_flat))))
    pred_idx = np.argpartition(-p_flat, k - 1)[:k]
    true_idx = np.argpartition(-y_flat, k - 1)[:k]
    pred_set = set(int(x) for x in pred_idx.tolist())
    true_set = set(int(x) for x in true_idx.tolist())
    overlap = len(pred_set & true_set)
    precision_topk = float(overlap / max(len(pred_set), 1))
    recall_topk = float(overlap / max(len(true_set), 1))
    if precision_topk + recall_topk <= 1e-12:
        f1_topk = 0.0
    else:
        f1_topk = float(2.0 * precision_topk * recall_topk / (precision_topk + recall_topk))

    lead_hours: list[float] = []
    for lid in range(l):
        pred_series = p[:, lid]
        true_series = y[:, lid]
        pred_thr = float(np.quantile(pred_series, 0.90))
        true_thr = float(np.quantile(true_series, 0.90))
        pred_idx_series = np.where(pred_series >= pred_thr)[0]
        true_idx_series = np.where(true_series >= true_thr)[0]
        if len(pred_idx_series) == 0 or len(true_idx_series) == 0:
            continue
        pred_t = int(pred_idx_series[0])
        true_t = int(true_idx_series[0])
        lead_hours.append(float(true_t - pred_t))
    avg_lead = float(np.mean(lead_hours)) if lead_hours else 0.0

    return {
        "warning_brier": brier,
        "warning_auroc": auroc,
        "warning_auprc": auprc,
        "warning_precision_top10": precision_topk,
        "warning_recall_top10": recall_topk,
        "warning_f1_top10": f1_topk,
        "warning_avg_lead_hours": avg_lead,
    }


def run_failure_stage(
    root: Path,
    output_dir: Path,
    grid_path: Path,
    model: str,
    intensity_scale: float,
    start_time: str,
    hours: int,
    center_lat: float,
    center_lon: float,
    move_dir_deg: float,
    move_speed_ms: float,
    design_scale: float,
    reuse_existing: bool,
    dry_run: bool,
) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    failure_csv = output_dir / f"line_failure_timeseries_{model}.csv"
    cmd = [
        "python",
        str(root / "scripts" / "component_failure_probability.py"),
        "--grid",
        str(grid_path),
        "--output-dir",
        str(output_dir),
        "--model",
        model,
        "--start-time",
        start_time,
        "--hours",
        str(hours),
        "--center-lat",
        str(center_lat),
        "--center-lon",
        str(center_lon),
        "--intensity-scale",
        str(intensity_scale),
        "--move-dir-deg",
        str(move_dir_deg),
        "--move-speed-ms",
        str(move_speed_ms),
        "--design-scale",
        str(design_scale),
    ]
    maybe_run(cmd=cmd, expected_outputs=[failure_csv], cwd=root, reuse_existing=reuse_existing, dry_run=dry_run)
    return failure_csv


def run_contingency_stage(
    root: Path,
    output_dir: Path,
    failure_csv: Path,
    grid_path: Path,
    method: str,
    n_scenarios: int,
    seed: int,
    warning_end_hour: int,
    repair_hours: int,
    high_risk_quantile: float,
    reuse_existing: bool,
    dry_run: bool,
) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    tensor = output_dir / f"contingency_tensor_{method}.npy"
    cmd = [
        "python",
        str(root / "scripts" / "spatiotemporal_contingency_generator.py"),
        "--failure-csv",
        str(failure_csv),
        "--grid",
        str(grid_path),
        "--output-dir",
        str(output_dir),
        "--methods",
        method,
        "--n-scenarios",
        str(n_scenarios),
        "--seed",
        str(seed),
        "--warning-end-hour",
        str(warning_end_hour),
        "--repair-hours",
        str(repair_hours),
        "--high-risk-quantile",
        str(high_risk_quantile),
    ]
    maybe_run(cmd=cmd, expected_outputs=[tensor], cwd=root, reuse_existing=reuse_existing, dry_run=dry_run)
    return tensor


def run_scheduling_stage(
    root: Path,
    output_dir: Path,
    grid_path: Path,
    trim_input: Path,
    uncertainty_dir: Path,
    failure_csv: Path,
    contingency_tensor: Path,
    reserve_ratio: float,
    priority_stress_factor: float,
    seed: int,
    load_shed_cost: float,
    slack_dispatchable_capacity: float,
    emergency_dg_capacities: str,
    policy_set: str,
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
        str(grid_path),
        "--trim-input",
        str(trim_input),
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
        "--priority-stress-factor",
        str(priority_stress_factor),
        "--load-shed-cost",
        str(load_shed_cost),
        "--slack-dispatchable-capacity",
        str(slack_dispatchable_capacity),
        "--emergency-dg-capacities",
        emergency_dg_capacities,
        "--policy-set",
        policy_set,
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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run multi-scenario fusion evaluation: warning precision + scheduling optimization."
    )
    parser.add_argument(
        "--design-manifest",
        default="results/multiscenario_fusion/phase1_design/experiment_manifest.json",
        help="Path to experiment_manifest.json from design phase.",
    )
    parser.add_argument(
        "--output-subdir",
        default="edge_eval",
        help="Output subfolder under design run root.",
    )
    parser.add_argument(
        "--env-selection",
        choices=("shuffle", "head"),
        default="shuffle",
        help="How to select env cases when max-env-cases is set.",
    )
    parser.add_argument("--max-env-cases", type=int, default=6, help="Limit env cases for this run.")
    parser.add_argument("--max-strategies", type=int, default=6, help="Limit strategies for this run.")
    parser.add_argument(
        "--env-ids",
        default="",
        help="Optional comma-separated env sample ids to run only specific checkpoints (e.g., S0007,S0015).",
    )
    parser.add_argument("--min-intensity", type=float, default=None, help="Optional filter: keep env with intensity >= value.")
    parser.add_argument("--n-scenarios", type=int, default=64, help="Scenario count in contingency generation.")
    parser.add_argument("--seed", type=int, default=42, help="Random seed.")
    parser.add_argument("--start-time", default="2024-09-01 00:00:00", help="Typhoon start time.")
    parser.add_argument("--hours", type=int, default=72, help="Typhoon duration hours.")
    parser.add_argument("--center-lat", type=float, default=23.1291, help="Grid center latitude.")
    parser.add_argument("--center-lon", type=float, default=113.2644, help="Grid center longitude.")
    parser.add_argument("--move-dir-deg", type=float, default=300.0, help="Typhoon moving direction.")
    parser.add_argument("--move-speed-ms", type=float, default=6.0, help="Typhoon moving speed.")
    parser.add_argument("--design-scale", type=float, default=1.0, help="Asset design scale.")
    parser.add_argument("--warning-end-hour", type=int, default=-1, help="Warning end hour index.")
    parser.add_argument("--repair-hours", type=int, default=12, help="Repair hours.")
    parser.add_argument("--high-risk-quantile", type=float, default=0.90, help="High risk quantile.")
    parser.add_argument("--load-shed-cost", type=float, default=50.0, help="Load shedding cost.")
    parser.add_argument("--slack-dispatchable-capacity", type=float, default=1.2, help="Slack dispatchable cap.")
    parser.add_argument("--emergency-dg-capacities", default="0.18,0.15,0.10", help="Emergency DG capacities.")
    parser.add_argument(
        "--policy-set",
        choices=("all", "priority_only"),
        default="priority_only",
        help="Scheduling policy set for runtime speed/coverage tradeoff.",
    )
    parser.add_argument("--no-reuse-existing", action="store_true", help="Disable reusing existing outputs.")
    parser.add_argument("--dry-run", action="store_true", help="Print commands only.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    root = project_root()
    manifest_path = resolve_path(root, args.design_manifest)
    if not manifest_path.exists():
        raise FileNotFoundError(f"manifest not found: {manifest_path}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    run_root = Path(str(manifest["run_root"])).resolve()
    artifacts = manifest["artifacts"]
    sampled_env_csv = Path(str(artifacts["env_matrix_sampled_csv"])).resolve()
    strategy_csv = Path(str(artifacts["strategy_pool_csv"])).resolve()
    grid_path = resolve_path(root, "data_final/formal_guangdong_2024/grid_topology.json")

    env_df = pd.read_csv(sampled_env_csv)
    strategy_df = pd.read_csv(strategy_csv)
    if args.env_ids.strip():
        selected = {x.strip() for x in args.env_ids.split(",") if x.strip()}
        if "sample_id" in env_df.columns:
            env_df = env_df[env_df["sample_id"].isin(selected)].copy()
        else:
            env_df = env_df[env_df["env_id"].isin(selected)].copy()
    if args.min_intensity is not None:
        env_df = env_df[env_df["intensity_scale"] >= float(args.min_intensity)].copy()
    if args.env_selection == "shuffle":
        env_df = env_df.sample(frac=1.0, random_state=args.seed).reset_index(drop=True)
    if args.max_env_cases > 0:
        env_df = env_df.head(args.max_env_cases).copy()
    if args.max_strategies > 0:
        strategy_df = strategy_df.head(args.max_strategies).copy()

    output_dir = run_root / args.output_subdir
    output_dir.mkdir(parents=True, exist_ok=True)
    runtime_dir = output_dir / "runtime"
    runtime_dir.mkdir(parents=True, exist_ok=True)

    reuse_existing = not args.no_reuse_existing
    failure_cache: dict[tuple[str, str], Path] = {}
    contingency_cache: dict[tuple[str, str, str], Path] = {}
    records: list[dict[str, Any]] = []

    total = len(env_df) * len(strategy_df)
    done = 0
    print(format_progress(done=done, total=total))
    idx = 0
    for _, env in env_df.iterrows():
        env_id = str(env["sample_id"]) if "sample_id" in env and pd.notna(env["sample_id"]) else str(env["env_id"])
        intensity = float(env["intensity_scale"])
        uncertainty_dir = Path(str(env["uncertainty_dir"])).resolve()
        trim_input = Path(str(env["trim_input"])).resolve()
        load_scenario = str(env["load_scenario"])
        wind_variant = str(env["wind_variant"])
        stress_factor = float(env.get("priority_stress_factor", 1.0))

        for _, st in strategy_df.iterrows():
            idx += 1
            strategy_id = str(st["strategy_id"])
            failure_model = str(st["failure_model"])
            contingency_method = str(st["contingency_method"])
            reserve_ratio = float(st["reserve_ratio"])

            print(f"\n[{idx}/{total}] {env_id} + {strategy_id}")
            key_fail = (env_id, failure_model)
            if key_fail not in failure_cache:
                fail_dir = runtime_dir / "failure" / env_id / failure_model
                failure_cache[key_fail] = run_failure_stage(
                    root=root,
                    output_dir=fail_dir,
                    grid_path=grid_path,
                    model=failure_model,
                    intensity_scale=intensity,
                    start_time=args.start_time,
                    hours=args.hours,
                    center_lat=args.center_lat,
                    center_lon=args.center_lon,
                    move_dir_deg=args.move_dir_deg,
                    move_speed_ms=args.move_speed_ms,
                    design_scale=args.design_scale,
                    reuse_existing=reuse_existing,
                    dry_run=args.dry_run,
                )
            failure_csv = failure_cache[key_fail]

            key_cont = (env_id, failure_model, contingency_method)
            if key_cont not in contingency_cache:
                cont_dir = runtime_dir / "contingency" / env_id / failure_model
                contingency_cache[key_cont] = run_contingency_stage(
                    root=root,
                    output_dir=cont_dir,
                    failure_csv=failure_csv,
                    grid_path=grid_path,
                    method=contingency_method,
                    n_scenarios=args.n_scenarios,
                    seed=args.seed,
                    warning_end_hour=args.warning_end_hour,
                    repair_hours=args.repair_hours,
                    high_risk_quantile=args.high_risk_quantile,
                    reuse_existing=reuse_existing,
                    dry_run=args.dry_run,
                )
            contingency_tensor = contingency_cache[key_cont]

            sched_dir = runtime_dir / "scheduling" / env_id / strategy_id
            policy_csv, worst_csv = run_scheduling_stage(
                root=root,
                output_dir=sched_dir,
                grid_path=grid_path,
                trim_input=trim_input,
                uncertainty_dir=uncertainty_dir,
                failure_csv=failure_csv,
                contingency_tensor=contingency_tensor,
                reserve_ratio=reserve_ratio,
                priority_stress_factor=stress_factor,
                seed=args.seed,
                load_shed_cost=args.load_shed_cost,
                slack_dispatchable_capacity=args.slack_dispatchable_capacity,
                emergency_dg_capacities=args.emergency_dg_capacities,
                policy_set=args.policy_set,
                reuse_existing=reuse_existing,
                dry_run=args.dry_run,
            )

            if args.dry_run:
                done += 1
                print(format_progress(done=done, total=total))
                continue

            policy_df = pd.read_csv(policy_csv)
            row = policy_df[policy_df["policy"] == "priority_with_reserve"]
            if row.empty:
                raise ValueError(f"priority_with_reserve missing in {policy_csv}")
            r = row.iloc[0]
            rapidity, sustainability = calc_rapidity_sustainability(worst_detail_csv=worst_csv, policy="priority_with_reserve")
            warn = warning_metrics(failure_csv=failure_csv, contingency_tensor=contingency_tensor, top_ratio=0.10)
            records.append(
                {
                    "env_id": env_id,
                    "sample_id": env_id,
                    "intensity_scale": intensity,
                    "wind_variant": wind_variant,
                    "load_scenario": load_scenario,
                    "priority_stress_factor": stress_factor,
                    "strategy_id": strategy_id,
                    "run_tag": str(st.get("run_tag", "")),
                    "failure_model": failure_model,
                    "contingency_method": contingency_method,
                    "reserve_ratio": reserve_ratio,
                    "Priority": float(r["critical_served_ratio"]),
                    "Robustness": float(r["rr"]),
                    "Rapidity": float(rapidity),
                    "Sustainability": float(sustainability),
                    "RA": float(r.get("ra", np.nan)),
                    "expected_total_shed": float(r["expected_total_shed"]),
                    "expected_weighted_shed_cost": float(r["expected_weighted_shed_cost"]),
                    **warn,
                    "policy_csv": str(policy_csv),
                    "worst_csv": str(worst_csv),
                    "failure_csv": str(failure_csv),
                    "contingency_tensor": str(contingency_tensor),
                }
            )
            done += 1
            print(format_progress(done=done, total=total))

    if args.dry_run:
        print("Dry run done.")
        return

    if not records:
        raise RuntimeError("no run records generated")

    df = pd.DataFrame(records)
    indicators = [
        "warning_auprc",
        "warning_recall_top10",
        "warning_f1_top10",
        "Priority",
        "Robustness",
        "Rapidity",
        "Sustainability",
        "expected_weighted_shed_cost",
    ]
    benefit_flags = [True, True, True, True, True, True, True, False]
    mat = df[indicators].copy()
    mat = mat.fillna(mat.min(numeric_only=True)).fillna(0.0)
    score, weights = ewm_topsis(mat.to_numpy(dtype=float), benefit_flags=benefit_flags)
    df["FUSION_TOPSIS_Score"] = score
    df = df.sort_values("FUSION_TOPSIS_Score", ascending=False).reset_index(drop=True)
    df["FUSION_TOPSIS_Rank"] = np.arange(1, len(df) + 1)

    w_df = pd.DataFrame({"indicator": indicators, "ewm_weight": weights}).sort_values("ewm_weight", ascending=False)

    strategy_summary = (
        df.groupby(["strategy_id", "run_tag", "failure_model", "contingency_method", "reserve_ratio"], as_index=False)
        .agg(
            mean_fusion_score=("FUSION_TOPSIS_Score", "mean"),
            std_fusion_score=("FUSION_TOPSIS_Score", "std"),
            mean_warning_auprc=("warning_auprc", "mean"),
            mean_warning_recall_top10=("warning_recall_top10", "mean"),
            mean_rr=("Robustness", "mean"),
            mean_priority=("Priority", "mean"),
            mean_sustainability=("Sustainability", "mean"),
            mean_cost=("expected_weighted_shed_cost", "mean"),
            run_count=("env_id", "count"),
        )
        .sort_values("mean_fusion_score", ascending=False)
        .reset_index(drop=True)
    )
    strategy_summary["strategy_rank"] = np.arange(1, len(strategy_summary) + 1)

    env_summary = (
        df.groupby(["env_id", "intensity_scale", "wind_variant", "load_scenario"], as_index=False)
        .agg(
            best_fusion_score=("FUSION_TOPSIS_Score", "max"),
            avg_fusion_score=("FUSION_TOPSIS_Score", "mean"),
            avg_warning_auprc=("warning_auprc", "mean"),
            avg_rr=("Robustness", "mean"),
            avg_cost=("expected_weighted_shed_cost", "mean"),
        )
        .sort_values("best_fusion_score", ascending=False)
        .reset_index(drop=True)
    )

    best_row = df.iloc[0]
    best_strategy = strategy_summary.iloc[0]

    runs_csv = output_dir / "fusion_runs.csv"
    strategy_csv = output_dir / "fusion_strategy_summary.csv"
    env_csv = output_dir / "fusion_environment_summary.csv"
    weight_csv = output_dir / "fusion_indicator_weights.csv"
    df.to_csv(runs_csv, index=False, encoding="utf-8")
    strategy_summary.to_csv(strategy_csv, index=False, encoding="utf-8")
    env_summary.to_csv(env_csv, index=False, encoding="utf-8")
    w_df.to_csv(weight_csv, index=False, encoding="utf-8")

    report = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "design_manifest": str(manifest_path),
        "output_dir": str(output_dir),
        "run_config": {
            "max_env_cases": int(args.max_env_cases),
            "max_strategies": int(args.max_strategies),
            "n_scenarios": int(args.n_scenarios),
            "seed": int(args.seed),
            "hours": int(args.hours),
            "policy_set": str(args.policy_set),
        },
        "counts": {
            "runs": int(len(df)),
            "env_cases": int(df["env_id"].nunique()),
            "strategies": int(df["strategy_id"].nunique()),
        },
        "best_run": {
            "env_id": str(best_row["env_id"]),
            "strategy_id": str(best_row["strategy_id"]),
            "run_tag": str(best_row["run_tag"]),
            "fusion_score": float(best_row["FUSION_TOPSIS_Score"]),
            "warning_auprc": float(best_row["warning_auprc"]) if pd.notna(best_row["warning_auprc"]) else None,
            "robustness": float(best_row["Robustness"]),
            "expected_weighted_shed_cost": float(best_row["expected_weighted_shed_cost"]),
        },
        "best_strategy_global": {
            "strategy_id": str(best_strategy["strategy_id"]),
            "run_tag": str(best_strategy["run_tag"]),
            "failure_model": str(best_strategy["failure_model"]),
            "contingency_method": str(best_strategy["contingency_method"]),
            "reserve_ratio": float(best_strategy["reserve_ratio"]),
            "mean_fusion_score": float(best_strategy["mean_fusion_score"]),
        },
        "artifacts": {
            "fusion_runs_csv": str(runs_csv),
            "fusion_strategy_summary_csv": str(strategy_csv),
            "fusion_environment_summary_csv": str(env_csv),
            "fusion_indicator_weights_csv": str(weight_csv),
        },
    }
    report_path = output_dir / "fusion_report.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    print("\nDone.")
    print(f"runs        -> {runs_csv}")
    print(f"strategies  -> {strategy_csv}")
    print(f"environments-> {env_csv}")
    print(f"weights     -> {weight_csv}")
    print(f"report      -> {report_path}")


if __name__ == "__main__":
    main()
