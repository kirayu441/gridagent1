from __future__ import annotations

import argparse
import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


def project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def run_cmd(cmd: list[str], cwd: Path) -> None:
    print(">>", " ".join(cmd))
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


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def ewm_topsis(matrix: np.ndarray, benefit_flags: list[bool]) -> np.ndarray:
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
    return score


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run paper comparison experiments and export a completed comparison table.")
    parser.add_argument(
        "--framework-run-root",
        default="results/gridagent_framework/formal2024_full_baseline_20260310_233109",
        help="Framework run root used as input anchor.",
    )
    parser.add_argument(
        "--config",
        default="configs/gridagent_framework.formal2024.json",
        help="Framework config path.",
    )
    parser.add_argument(
        "--output-dir",
        default="results/paper_comparison",
        help="Output root for experiment artifacts.",
    )
    return parser.parse_args()


def build_uniform_priority_csv(priority_csv: Path, output_csv: Path) -> Path:
    df = pd.read_csv(priority_csv)
    if "load_bus" not in df.columns:
        raise ValueError(f"invalid priority profile, missing load_bus: {priority_csv}")
    out = df.copy()
    out["priority_level"] = 2
    out["priority_weight"] = 1.0
    out.to_csv(output_csv, index=False, encoding="utf-8")
    return output_csv


def run_dispatch_with_profile(
    root: Path,
    config: dict[str, Any],
    framework_report: dict[str, Any],
    load_priority_csv: Path,
    output_dir: Path,
) -> Path:
    paths_cfg = config["paths"]
    dispatch_cfg = config.get("dispatch_optimization", {})
    scheduling_cfg = config.get("scheduling", {})
    cfg_seed = int(config.get("seed", 42))

    outputs = framework_report["details"]["outputs"]
    cmd = [
        "python",
        str(root / "scripts" / "dispatch_optimization_module.py"),
        "--strategy-mode",
        str(dispatch_cfg.get("strategy_mode", "contextual")),
        "--export-diagnostics",
        "--grid",
        str(paths_cfg["grid"]),
        "--trim-input",
        str(paths_cfg["trim_input"]),
        "--failure-csv",
        str(Path(outputs["failure_csv"]).resolve().relative_to(root)),
        "--uncertainty-dir",
        str(Path(outputs["uncertainty_dir"]).resolve().relative_to(root)),
        "--line-risk-csv",
        str(Path(outputs["line_risk_prediction_csv"]).resolve().relative_to(root)),
        "--load-priority-csv",
        str(load_priority_csv.resolve().relative_to(root)),
        "--output-dir",
        str(output_dir.resolve().relative_to(root)),
        "--horizon-hours",
        str(dispatch_cfg.get("horizon_hours", 24)),
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
        str(dispatch_cfg.get("slack_dispatchable_capacity", scheduling_cfg.get("slack_dispatchable_capacity", 1.2))),
        "--emergency-dg-capacities",
        str(dispatch_cfg.get("emergency_dg_capacities", scheduling_cfg.get("emergency_dg_capacities", "0.18,0.15,0.10"))),
        "--time-limit-sec",
        str(dispatch_cfg.get("time_limit_sec", 45.0)),
        "--mip-gap",
        str(dispatch_cfg.get("mip_gap", 0.02)),
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
        str(cfg_seed + 3000),
    ]
    run_cmd(cmd=cmd, cwd=root)

    comparison_csv = output_dir / "dispatch_model_comparison.csv"
    if not comparison_csv.exists():
        raise FileNotFoundError(f"missing dispatch comparison csv: {comparison_csv}")
    return comparison_csv


def pick_row(df: pd.DataFrame, model: str) -> pd.Series:
    row = df[df["model"] == model]
    if row.empty:
        raise ValueError(f"missing model row: {model}")
    return row.iloc[0]


def metric_or(row: pd.Series, key: str, fallback_key: str | None = None) -> float:
    if key in row.index and pd.notna(row[key]):
        return float(row[key])
    if fallback_key is not None and fallback_key in row.index and pd.notna(row[fallback_key]):
        return float(row[fallback_key])
    return float("nan")


def to_markdown_table(df: pd.DataFrame) -> str:
    fmt_df = df.copy()
    for col in fmt_df.columns:
        if pd.api.types.is_numeric_dtype(fmt_df[col]):
            fmt_df[col] = fmt_df[col].map(lambda x: f"{x:.6f}" if pd.notna(x) else "")
    headers = list(fmt_df.columns)
    lines = []
    lines.append("| " + " | ".join(headers) + " |")
    lines.append("|" + "|".join(["---"] * len(headers)) + "|")
    for _, row in fmt_df.iterrows():
        vals = [str(row[h]) if pd.notna(row[h]) else "" for h in headers]
        lines.append("| " + " | ".join(vals) + " |")
    return "\n".join(lines)


def append_improvement_row(df: pd.DataFrame) -> pd.DataFrame:
    baseline_mask = df["方法"].isin(["SCUC", "Stochastic UC", "Robust UC", "Wang-2024复现"])
    ours = df[df["方法"] == "GridAgent (Ours)"].iloc[0]
    baselines = df[baseline_mask]

    larger_better = {"关键负荷供电率 ↑", "Robustness ↑", "Rapidity ↑", "Sustainability ↑", "TOPSIS Score ↑"}
    smaller_better = {"Total Cost ↓", "EENS ↓", "Overload Count ↓", "Max Line Loading ↓", "Runtime (s) ↓"}

    row: dict[str, Any] = {"方法": "相对最佳基线提升(%)", "方法类别": "-", "参考文献": "-"}
    for col in df.columns:
        if col in {"方法", "方法类别", "参考文献"}:
            continue
        if col in larger_better:
            best = baselines[col].max()
            val = ours[col]
            row[col] = (val - best) / max(abs(best), 1e-12) * 100.0
        elif col in smaller_better:
            best = baselines[col].min()
            val = ours[col]
            row[col] = (best - val) / max(abs(best), 1e-12) * 100.0
        else:
            row[col] = np.nan
    return pd.concat([df, pd.DataFrame([row])], ignore_index=True)


def main() -> None:
    args = parse_args()
    root = project_root()

    run_root = (root / args.framework_run_root).resolve()
    config_path = (root / args.config).resolve()
    if not run_root.exists():
        raise FileNotFoundError(f"framework run root not found: {run_root}")
    if not config_path.exists():
        raise FileNotFoundError(f"config not found: {config_path}")

    config = read_json(config_path)
    framework_report = read_json(run_root / "framework_report.json")
    outputs = framework_report["details"]["outputs"]

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_root = (root / args.output_dir / f"formal2024_comparison_{ts}").resolve()
    out_root.mkdir(parents=True, exist_ok=True)

    priority_profile_csv = Path(outputs["scheduling_dir"]) / "load_bus_priority_profile.csv"
    if not priority_profile_csv.exists():
        raise FileNotFoundError(f"missing priority profile: {priority_profile_csv}")
    uniform_profile_csv = out_root / "uniform_load_priority_profile.csv"
    build_uniform_priority_csv(priority_csv=priority_profile_csv, output_csv=uniform_profile_csv)

    uniform_dispatch_dir = out_root / "dispatch_uniform_priority"
    weighted_dispatch_dir = out_root / "dispatch_weighted_priority"

    uniform_cmp_csv = run_dispatch_with_profile(
        root=root,
        config=config,
        framework_report=framework_report,
        load_priority_csv=uniform_profile_csv,
        output_dir=uniform_dispatch_dir,
    )
    weighted_cmp_csv = run_dispatch_with_profile(
        root=root,
        config=config,
        framework_report=framework_report,
        load_priority_csv=priority_profile_csv,
        output_dir=weighted_dispatch_dir,
    )

    uniform_df = pd.read_csv(uniform_cmp_csv)
    weighted_df = pd.read_csv(weighted_cmp_csv)

    rows: list[dict[str, Any]] = []
    scuc = pick_row(uniform_df, "SCUC")
    stoch = pick_row(uniform_df, "Stochastic_UC")
    robust_uniform = pick_row(uniform_df, "Robust_UC")
    robust_weighted = pick_row(weighted_df, "Robust_UC")
    ours = pick_row(weighted_df, "Contextual_Adaptive")

    method_meta = [
        ("SCUC", "经典基线", "Carrion & Arroyo (2006)", scuc),
        ("Stochastic UC", "经典基线", "Takriti et al. (1996)", stoch),
        ("Robust UC", "经典基线", "Bertsimas & Sim (2004); Zhao & Guan (2013)", robust_uniform),
        ("Wang-2024复现", "同领域方法", "Wang et al. (2024)", robust_weighted),
        ("GridAgent (Ours)", "本文方法", "-", ours),
    ]

    for method, category, ref, r in method_meta:
        rows.append(
            {
                "方法": method,
                "方法类别": category,
                "参考文献": ref,
                "Total Cost ↓": metric_or(r, "total_cost"),
                "EENS ↓": metric_or(r, "EENS"),
                "关键负荷供电率 ↑": metric_or(r, "critical_load_supply_rate", fallback_key="priority_index"),
                "Overload Count ↓": metric_or(r, "overload_count"),
                "Max Line Loading ↓": metric_or(r, "max_line_loading"),
                "Robustness ↑": metric_or(r, "robustness", fallback_key="reliability_score"),
                "Rapidity ↑": metric_or(r, "rapidity"),
                "Sustainability ↑": metric_or(r, "sustainability"),
                "Runtime (s) ↓": metric_or(r, "runtime_sec"),
            }
        )

    result_df = pd.DataFrame(rows)
    topsis_input = result_df[["关键负荷供电率 ↑", "Robustness ↑", "Rapidity ↑", "Sustainability ↑"]].to_numpy(dtype=float)
    result_df["TOPSIS Score ↑"] = ewm_topsis(topsis_input, benefit_flags=[True, True, True, True])

    final_cols = [
        "方法",
        "方法类别",
        "参考文献",
        "Total Cost ↓",
        "EENS ↓",
        "关键负荷供电率 ↑",
        "Overload Count ↓",
        "Max Line Loading ↓",
        "Robustness ↑",
        "Rapidity ↑",
        "Sustainability ↑",
        "TOPSIS Score ↑",
        "Runtime (s) ↓",
    ]
    result_df = result_df[final_cols]
    result_df = append_improvement_row(result_df)

    csv_path = out_root / "comparison_table_filled.csv"
    md_path = out_root / "comparison_table_filled.md"
    meta_path = out_root / "comparison_metadata.json"

    result_df.to_csv(csv_path, index=False, encoding="utf-8")
    md_path.write_text(to_markdown_table(result_df), encoding="utf-8")
    meta_path.write_text(
        json.dumps(
            {
                "framework_run_root": str(run_root),
                "uniform_dispatch_dir": str(uniform_dispatch_dir),
                "weighted_dispatch_dir": str(weighted_dispatch_dir),
                "uniform_comparison_csv": str(uniform_cmp_csv),
                "weighted_comparison_csv": str(weighted_cmp_csv),
                "table_csv": str(csv_path),
                "table_md": str(md_path),
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    print("Done.")
    print(f"table csv -> {csv_path}")
    print(f"table md  -> {md_path}")
    print(f"meta json -> {meta_path}")


if __name__ == "__main__":
    main()
