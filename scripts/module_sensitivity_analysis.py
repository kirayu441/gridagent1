from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression


def project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def run_cmd(cmd: list[str], cwd: Path) -> None:
    proc = subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        raise RuntimeError(
            f"command failed ({proc.returncode}): {' '.join(cmd)}\n"
            f"STDOUT:\n{proc.stdout}\n\nSTDERR:\n{proc.stderr}"
        )


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


def influence_weights(df: pd.DataFrame, y_col: str, factors: list[str]) -> pd.DataFrame:
    y = df[y_col].to_numpy(dtype=float)
    x_full = pd.get_dummies(df[factors].astype(str), drop_first=True)
    if x_full.shape[1] == 0:
        return pd.DataFrame({"module": factors, "influence_weight": [0.0] * len(factors), "delta_r2": [0.0] * len(factors)})

    model = LinearRegression()
    model.fit(x_full, y)
    r2_full = float(model.score(x_full, y))
    rows: list[dict[str, Any]] = []

    for fac in factors:
        fac_cols = [c for c in x_full.columns if c.startswith(f"{fac}_")]
        if not fac_cols:
            delta = 0.0
        else:
            x_drop = x_full.drop(columns=fac_cols)
            if x_drop.shape[1] == 0:
                y_mean = np.full_like(y, y.mean())
                ss_res = float(((y - y_mean) ** 2).sum())
                ss_tot = float(((y - y.mean()) ** 2).sum())
                r2_drop = 1.0 - ss_res / max(ss_tot, 1e-12)
            else:
                m_drop = LinearRegression()
                m_drop.fit(x_drop, y)
                r2_drop = float(m_drop.score(x_drop, y))
            delta = max(r2_full - r2_drop, 0.0)
        rows.append({"module": fac, "delta_r2": float(delta)})

    out = pd.DataFrame(rows)
    total = float(out["delta_r2"].sum())
    if total <= 1e-12:
        out["influence_weight"] = 1.0 / len(out)
    else:
        out["influence_weight"] = out["delta_r2"] / total
    return out.sort_values("influence_weight", ascending=False).reset_index(drop=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Independent module validation + sensitivity analysis for resilience output."
    )
    parser.add_argument(
        "--output-dir",
        default="results/module_sensitivity/formal2024",
        help="Output directory.",
    )
    parser.add_argument(
        "--failure-models",
        default="schloemer,batts",
        help="Comma-separated failure models.",
    )
    parser.add_argument(
        "--contingency-methods",
        default="wang_qmc,wang_mc,c3po_ref,trim_ref",
        help="Comma-separated contingency methods.",
    )
    parser.add_argument(
        "--reserve-ratios",
        default="0.05,0.15,0.30",
        help="Comma-separated reserve ratios.",
    )
    parser.add_argument(
        "--n-scenarios",
        type=int,
        default=256,
        help="Scenario count for contingency generation (already generated data expected).",
    )
    parser.add_argument("--seed", type=int, default=42, help="Random seed.")
    parser.add_argument(
        "--rerun-scheduling",
        action="store_true",
        help="Force rerun scheduling even if output exists.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    root = project_root()
    output_dir = (root / args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    failure_models = [x.strip() for x in args.failure_models.split(",") if x.strip()]
    cont_methods = [x.strip() for x in args.contingency_methods.split(",") if x.strip()]
    reserve_ratios = [float(x.strip()) for x in args.reserve_ratios.split(",") if x.strip()]

    records: list[dict[str, Any]] = []

    total_runs = len(failure_models) * len(cont_methods) * len(reserve_ratios)
    run_idx = 0

    for fm in failure_models:
        fail_csv = root / "results" / "component_failure_probability" / "formal2024" / f"line_failure_timeseries_{fm}.csv"
        cont_dir = root / "results" / "spatiotemporal_contingency" / f"formal2024_{fm}72h"
        if not fail_csv.exists():
            raise FileNotFoundError(f"missing failure input: {fail_csv}")
        if not cont_dir.exists():
            raise FileNotFoundError(f"missing contingency dir: {cont_dir}")

        for cm in cont_methods:
            tensor = cont_dir / f"contingency_tensor_{cm}.npy"
            if not tensor.exists():
                raise FileNotFoundError(f"missing tensor: {tensor}")

            for rr in reserve_ratios:
                run_idx += 1
                tag = f"{fm}__{cm}__rr{str(rr).replace('.', 'p')}"
                run_dir = output_dir / "runs" / tag
                policy_csv = run_dir / "policy_comparison.csv"
                worst_csv = run_dir / "worst_scenario_shedding_detail.csv"
                print(f"[{run_idx}/{total_runs}] {tag}")

                if args.rerun_scheduling or not (policy_csv.exists() and worst_csv.exists()):
                    run_dir.mkdir(parents=True, exist_ok=True)
                    cmd = [
                        "python",
                        str(root / "scripts" / "load_prioritization_scheduling.py"),
                        "--grid",
                        str(root / "data_final" / "formal_guangdong_2024" / "grid_topology.json"),
                        "--trim-input",
                        str(root / "data_final" / "formal_guangdong_2024" / "TRIM_input.csv"),
                        "--contingency-tensor",
                        str(tensor),
                        "--failure-csv",
                        str(fail_csv),
                        "--uncertainty-dir",
                        str(root / "results" / "wind_pv_uncertainty" / "formal2024"),
                        "--output-dir",
                        str(run_dir),
                        "--reserve-ratio",
                        str(rr),
                        "--seed",
                        str(args.seed),
                    ]
                    run_cmd(cmd, cwd=root)

                policy_df = pd.read_csv(policy_csv)
                row = policy_df[policy_df["policy"] == "priority_with_reserve"]
                if row.empty:
                    raise ValueError(f"priority_with_reserve not found: {policy_csv}")
                r = row.iloc[0]
                rapidity, sustainability = calc_rapidity_sustainability(worst_detail_csv=worst_csv, policy="priority_with_reserve")

                records.append(
                    {
                        "failure_model": fm,
                        "contingency_method": cm,
                        "reserve_ratio": rr,
                        "run_tag": tag,
                        "Priority": float(r["critical_served_ratio"]),
                        "Robustness": float(r["rr"]),
                        "Rapidity": float(rapidity),
                        "Sustainability": float(sustainability),
                        "RA": float(r.get("ra", np.nan)),
                        "expected_total_shed": float(r["expected_total_shed"]),
                        "expected_weighted_shed_cost": float(r["expected_weighted_shed_cost"]),
                        "run_dir": str(run_dir),
                    }
                )

    df = pd.DataFrame(records)
    indicator_cols = ["Priority", "Robustness", "Rapidity", "Sustainability"]
    score, weights = ewm_topsis(df[indicator_cols].to_numpy(dtype=float), benefit_flags=[True, True, True, True])
    df["TOPSIS_Score"] = score
    df = df.sort_values("TOPSIS_Score", ascending=False).reset_index(drop=True)
    df["TOPSIS_Rank"] = np.arange(1, len(df) + 1)

    indicator_weight_df = pd.DataFrame(
        {"indicator": indicator_cols, "ewm_weight": weights}
    ).sort_values("ewm_weight", ascending=False)

    # module-level averages
    module_summary_rows: list[pd.DataFrame] = []
    for col in ["failure_model", "contingency_method", "reserve_ratio"]:
        tmp = (
            df.groupby(col, as_index=False)
            .agg(
                avg_topsis=("TOPSIS_Score", "mean"),
                avg_priority=("Priority", "mean"),
                avg_robustness=("Robustness", "mean"),
                avg_rapidity=("Rapidity", "mean"),
                avg_sustainability=("Sustainability", "mean"),
                avg_cost=("expected_weighted_shed_cost", "mean"),
            )
            .rename(columns={col: "level"})
        )
        tmp["module"] = col
        module_summary_rows.append(tmp)
    module_level_df = pd.concat(module_summary_rows, ignore_index=True)

    influence_df = influence_weights(
        df=df,
        y_col="TOPSIS_Score",
        factors=["failure_model", "contingency_method", "reserve_ratio"],
    )
    key_module = str(influence_df.iloc[0]["module"]) if not influence_df.empty else None

    # single-indicator top settings
    single_rows: list[dict[str, Any]] = []
    for ind in indicator_cols:
        top = df.sort_values(ind, ascending=False).iloc[0]
        single_rows.append(
            {
                "indicator": ind,
                "best_run_tag": str(top["run_tag"]),
                "best_value": float(top[ind]),
                "failure_model": str(top["failure_model"]),
                "contingency_method": str(top["contingency_method"]),
                "reserve_ratio": float(top["reserve_ratio"]),
            }
        )
    single_df = pd.DataFrame(single_rows)

    runs_csv = output_dir / "sensitivity_runs.csv"
    module_csv = output_dir / "module_level_summary.csv"
    influence_csv = output_dir / "module_influence_weights.csv"
    indicator_w_csv = output_dir / "indicator_ewm_weights.csv"
    single_csv = output_dir / "single_indicator_best_runs.csv"

    df.to_csv(runs_csv, index=False, encoding="utf-8")
    module_level_df.to_csv(module_csv, index=False, encoding="utf-8")
    influence_df.to_csv(influence_csv, index=False, encoding="utf-8")
    indicator_weight_df.to_csv(indicator_w_csv, index=False, encoding="utf-8")
    single_df.to_csv(single_csv, index=False, encoding="utf-8")

    best = df.iloc[0]
    report = {
        "experiment_design": {
            "failure_models": failure_models,
            "contingency_methods": cont_methods,
            "reserve_ratios": reserve_ratios,
            "run_count": int(len(df)),
        },
        "resilience_indicators": indicator_cols,
        "best_run": {
            "run_tag": str(best["run_tag"]),
            "failure_model": str(best["failure_model"]),
            "contingency_method": str(best["contingency_method"]),
            "reserve_ratio": float(best["reserve_ratio"]),
            "TOPSIS_Score": float(best["TOPSIS_Score"]),
        },
        "module_influence": influence_df.to_dict(orient="records"),
        "most_critical_module": key_module,
        "output_files": {
            "sensitivity_runs_csv": str(runs_csv),
            "module_level_summary_csv": str(module_csv),
            "module_influence_weights_csv": str(influence_csv),
            "indicator_ewm_weights_csv": str(indicator_w_csv),
            "single_indicator_best_runs_csv": str(single_csv),
        },
    }
    report_path = output_dir / "sensitivity_report.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    print("\nDone.")
    print(f"report -> {report_path}")
    print(f"best run -> {best['run_tag']} (TOPSIS={best['TOPSIS_Score']:.4f})")
    print(f"most critical module -> {key_module}")


if __name__ == "__main__":
    main()

