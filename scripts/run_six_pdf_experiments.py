from __future__ import annotations

import argparse
import csv
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "result_final" / "six_pdf_experiments"
PKG_OUT = ROOT / "paper_submission_package" / "results" / "six_pdf_experiments"
BASE = ROOT / "result_final" / "paper_experiment_outputs_rerun"
STAGE7 = ROOT / "gridagent_final" / "stage7"
PROJECT_PYTHON = ROOT / ".venv" / "Scripts" / "python.exe"

STAGE6_RUNS = BASE / "stage6_model_runs"
GRID = STAGE7 / "inputs" / "grid_topology.ieee118_full.json"
TRIM = STAGE7 / "inputs" / "TRIM_input.guangdong2024.csv"
FAILURE = STAGE7 / "inputs" / "line_failure_timeseries_schloemer.csv"
UNCERTAINTY = STAGE7 / "inputs" / "stage1_formal_output"
PRIORITY = STAGE7 / "inputs" / "load_bus_priority_profile.csv"

INPUTS = OUT / "inputs"
RUNS = OUT / "dispatch_runs"
LOGS = OUT / "logs"


MODEL_LABELS = {
    "historical_average": "Historical Average",
    "failure_prior": "Failure Prior",
    "mlp": "MLP",
    "baseline_gnn": "Baseline GNN",
    "gcn": "GCN",
    "gat": "GAT",
    "graphsage": "GraphSAGE",
    "stgcn": "STGCN",
    "metapath_v1": "GridAgent-Risk",
    "oracle": "Oracle",
}


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def ensure_dirs() -> None:
    for p in [OUT, PKG_OUT, INPUTS, RUNS, LOGS]:
        p.mkdir(parents=True, exist_ok=True)


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
    if path.is_relative_to(OUT):
        target = PKG_OUT / path.relative_to(OUT)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, target)


def load_wide_pair(model: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    model_dir = STAGE6_RUNS / model
    pred = pd.read_csv(model_dir / "validation_predictions_wide.csv")
    truth = pd.read_csv(model_dir / "validation_truth_wide.csv")
    return pred, truth


def values(df: pd.DataFrame) -> np.ndarray:
    return df.drop(columns=["timestamp"], errors="ignore").to_numpy(dtype=float)


def brier_score(pred: np.ndarray, truth: np.ndarray) -> float:
    return float(np.mean((np.clip(pred, 0.0, 1.0) - np.clip(truth, 0.0, 1.0)) ** 2))


def ece_score(pred: np.ndarray, truth: np.ndarray, n_bins: int = 10) -> float:
    p = np.clip(pred.reshape(-1), 0.0, 1.0)
    y = np.clip(truth.reshape(-1), 0.0, 1.0)
    total = len(p)
    if total == 0:
        return float("nan")
    ece = 0.0
    for lo in np.linspace(0.0, 0.9, n_bins):
        hi = lo + 1.0 / n_bins
        if hi >= 1.0:
            mask = (p >= lo) & (p <= hi)
        else:
            mask = (p >= lo) & (p < hi)
        if mask.any():
            ece += float(mask.mean()) * abs(float(p[mask].mean()) - float(y[mask].mean()))
    return float(ece)


def dcg(gains: list[float]) -> float:
    return float(sum(g / np.log2(i + 2) for i, g in enumerate(gains)))


def ranking_metrics(pred_score: np.ndarray, truth_score: np.ndarray, ks: tuple[int, ...] = (10, 20)) -> dict[str, float]:
    order = list(np.argsort(-pred_score))
    truth_order = list(np.argsort(-truth_score))
    total_truth_risk = float(np.sum(np.sort(truth_score)[::-1][: max(ks)]))
    out: dict[str, float] = {}
    for k in ks:
        kk = min(k, len(order))
        pred_top = set(order[:kk])
        truth_top = set(truth_order[:kk])
        hits = len(pred_top & truth_top)
        rels = [1.0 if idx in truth_top else 0.0 for idx in order[:kk]]
        gains = [float(truth_score[idx]) for idx in order[:kk]]
        ideal_gains = list(np.sort(truth_score)[::-1][:kk])
        out[f"precision_at_{k}"] = hits / max(kk, 1)
        out[f"recall_at_{k}"] = hits / max(len(truth_top), 1)
        out[f"false_positives_at_{k}"] = kk - hits
        out[f"ndcg_at_{k}"] = dcg(rels) / max(dcg([1.0] * kk), 1e-12)
        out[f"risk_coverage_at_{k}"] = float(np.sum(gains) / max(total_truth_risk, 1e-12))
        out[f"value_ndcg_at_{k}"] = dcg(gains) / max(dcg(ideal_gains), 1e-12)
    return out


def make_failure_prior_and_oracle() -> None:
    source_pred, source_truth = load_wide_pair("mlp")
    truth = values(source_truth)
    split_ts = source_truth["timestamp"].astype(str).tolist()

    failure_df = pd.read_csv(FAILURE)
    failure_df["timestamp"] = failure_df["timestamp"].astype(str)
    p = (
        failure_df.pivot_table(index="timestamp", columns="line_id", values="p_line", aggfunc="mean")
        .reindex(index=split_ts)
        .sort_index(axis=1)
    )
    pred_cols = [c for c in source_truth.columns if c != "timestamp"]
    p = p.reindex(columns=pred_cols).interpolate().ffill().bfill().fillna(0.0)

    for model, arr in {"failure_prior": p.to_numpy(dtype=float), "oracle": truth}.items():
        out_dir = STAGE6_RUNS / model
        out_dir.mkdir(parents=True, exist_ok=True)
        pred = pd.DataFrame(arr, columns=pred_cols)
        pred.insert(0, "timestamp", split_ts)
        pred.to_csv(out_dir / "validation_predictions_wide.csv", index=False)
        source_truth.to_csv(out_dir / "validation_truth_wide.csv", index=False)
        pred_score = arr.max(axis=0)
        truth_score = truth.max(axis=0)
        rank = pd.DataFrame({"line_id": pred_cols, "predicted_max_risk": pred_score, "true_max_risk": truth_score})
        rank["predicted_rank"] = rank["predicted_max_risk"].rank(method="first", ascending=False).astype(int)
        rank["true_rank"] = rank["true_max_risk"].rank(method="first", ascending=False).astype(int)
        rank.sort_values("predicted_rank").to_csv(out_dir / "line_ranking_validation.csv", index=False)


def experiment_1_2_3_6_tables() -> None:
    make_failure_prior_and_oracle()
    prediction_rows: list[dict[str, Any]] = []
    topk_rows: list[dict[str, Any]] = []
    runtime_rows: list[dict[str, Any]] = []
    for model in [
        "historical_average",
        "failure_prior",
        "mlp",
        "gcn",
        "gat",
        "graphsage",
        "stgcn",
        "metapath_v1",
    ]:
        pred_df, truth_df = load_wide_pair(model)
        pred = values(pred_df)
        truth = values(truth_df)
        err = pred - truth
        truth_flat = truth.reshape(-1)
        high_mask = truth >= max(float(np.quantile(truth_flat, 0.9)), 1e-12)
        metrics_path = STAGE6_RUNS / model / "metrics.csv"
        runtime = 0.0
        if metrics_path.exists():
            m = pd.read_csv(metrics_path).iloc[0].to_dict()
            runtime = float(m.get("train_time_seconds", m.get("runtime_sec", 0.0)) or 0.0)
        row = {
            "model": MODEL_LABELS[model],
            "mae": float(np.mean(np.abs(err))),
            "rmse": float(np.sqrt(np.mean(err**2))),
            "high_risk_mae": float(np.mean(np.abs(err[high_mask]))),
            "brier_score": brier_score(pred, truth),
            "ece": ece_score(pred, truth),
            "runtime_sec": runtime,
            "source_prediction": rel(STAGE6_RUNS / model / "validation_predictions_wide.csv"),
            "source_truth": rel(STAGE6_RUNS / model / "validation_truth_wide.csv"),
        }
        prediction_rows.append(row)

    write_csv(OUT / "experiment1_main_risk_probability_estimation.csv", prediction_rows)

    ablation_rows = []
    ablation_map = {
        "A0_baseline_no_metapath": "No MetaPath",
        "A1_metapath_fixed": "Fixed MetaPath",
        "A2_metapath_adaptive_global": "Adaptive Global MetaPath",
        "A3_full_training_enhanced": "Adaptive Context MetaPath / GridAgent-Risk",
    }
    src = BASE / "ablation_study.csv"
    if src.exists():
        df = pd.read_csv(src)
        for _, r in df.iterrows():
            variant = str(r["variant"])
            if variant in ablation_map:
                ablation_rows.append(
                    {
                        "variant": ablation_map[variant],
                        "mae": r.get("mae"),
                        "rmse": r.get("rmse"),
                        "high_risk_mae": r.get("high_risk_mae"),
                        "spearman": r.get("spearman", ""),
                        "ndcg_at_10": r.get("ndcg_at_10", ""),
                        "source": rel(src),
                    }
                )
    write_csv(OUT / "experiment2_metapath_ablation_study.csv", ablation_rows)

    for model in ["failure_prior", "mlp", "metapath_v1", "oracle"]:
        pred_df, truth_df = load_wide_pair(model)
        pred_score = values(pred_df).max(axis=0)
        truth_score = values(truth_df).max(axis=0)
        row = {"model": MODEL_LABELS[model], **ranking_metrics(pred_score, truth_score)}
        row["source"] = rel(STAGE6_RUNS / model / "line_ranking_validation.csv")
        topk_rows.append(row)
    write_csv(OUT / "experiment3_high_risk_line_identification.csv", topk_rows)

    manifest = BASE / "runtime_scalability.csv"
    if manifest.exists():
        df = pd.read_csv(manifest)
        wanted = {
            "mlp": "MLP",
            "gcn": "GCN",
            "gat": "GAT",
            "stgcn": "STGCN",
            "metapath_v1": "GridAgent-Risk",
        }
        for model, label in wanted.items():
            rows = df[(df["module"] == "stage6_prediction") & (df["setting"] == model)]
            if not rows.empty:
                runtime_rows.append(
                    {
                        "method": label,
                        "metapath_construction_time_sec": 0.0 if model != "metapath_v1" else "",
                        "model_training_time_sec": float(rows.iloc[0]["runtime_sec"]),
                        "risk_prediction_time_sec": "",
                        "dispatch_validation_time_sec": "",
                        "total_pipeline_runtime_sec": float(rows.iloc[0]["runtime_sec"]),
                        "source": rel(manifest),
                    }
                )
        dispatch = df[df["module"] == "stage7_dispatch"]
        if not dispatch.empty:
            runtime_rows.append(
                {
                    "method": "Stage7 dispatch validation average",
                    "metapath_construction_time_sec": "",
                    "model_training_time_sec": "",
                    "risk_prediction_time_sec": "",
                    "dispatch_validation_time_sec": float(dispatch["runtime_sec"].mean()),
                    "total_pipeline_runtime_sec": float(dispatch["runtime_sec"].mean()),
                    "source": rel(manifest),
                }
            )
    write_csv(OUT / "experiment6_runtime_scalability_analysis.csv", runtime_rows)


def risk_level(x: float) -> str:
    if x >= 0.7:
        return "HIGH"
    if x >= 0.4:
        return "MEDIUM"
    return "LOW"


def base_line_scores(kind: str) -> pd.DataFrame:
    if kind == "no_warning":
        return pd.DataFrame(columns=["line_id", "risk_prob"])
    if kind == "failure_prior":
        df = pd.read_csv(FAILURE)
        scores = df.groupby("line_id", as_index=False)["p_line"].max().rename(columns={"p_line": "risk_prob"})
    elif kind == "oracle":
        rank = pd.read_csv(STAGE6_RUNS / "oracle" / "line_ranking_validation.csv")
        scores = rank[["line_id", "true_max_risk"]].rename(columns={"true_max_risk": "risk_prob"})
    else:
        rank = pd.read_csv(STAGE6_RUNS / kind / "line_ranking_validation.csv")
        scores = rank[["line_id", "predicted_max_risk"]].rename(columns={"predicted_max_risk": "risk_prob"})
    scores["risk_prob"] = pd.to_numeric(scores["risk_prob"], errors="coerce").fillna(0.0)
    return scores.sort_values("risk_prob", ascending=False)


def warning_file(kind: str, scenario: str, top_k: int, alpha: float) -> Path | None:
    if kind == "no_warning":
        return None
    scores = base_line_scores(kind).copy()
    scores["raw_risk_prob"] = scores["risk_prob"]
    scores["selected_topk"] = False
    if top_k > 0:
        selected = scores.head(top_k).index
        scores.loc[:, "risk_prob"] = 0.0
        scores.loc[selected, "risk_prob"] = 1.0
        scores.loc[selected, "selected_topk"] = True
    scores["risk_level"] = scores["risk_prob"].map(risk_level)
    scores["predicted_fail_hour"] = "-"
    out = INPUTS / f"{scenario}_{kind}_top{top_k}_alpha{alpha:.2f}.csv".replace(".", "p")
    scores[["line_id", "risk_prob", "risk_level", "predicted_fail_hour", "raw_risk_prob", "selected_topk"]].to_csv(out, index=False)
    return out


def pressure_grid(scenario: str, line_scale: float = 1.0, exposure_scale: float | None = None, outage: bool = False) -> Path:
    payload = json.loads(GRID.read_text(encoding="utf-8"))
    exposure_lines = set(base_line_scores("failure_prior").head(30)["line_id"].astype(str))
    outage_line = str(base_line_scores("failure_prior").iloc[0]["line_id"]) if outage else None
    for line in payload.get("lines", []):
        lid = str(line.get("id"))
        cap = float(line.get("capacity", 0.0))
        scale = float(line_scale)
        if exposure_scale is not None and lid in exposure_lines:
            scale *= float(exposure_scale)
        if outage_line is not None and lid == outage_line:
            scale = 0.001
        line["capacity_original"] = cap
        line["capacity"] = max(cap * scale, 1e-6)
    out = INPUTS / f"{scenario}_grid.json"
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return out


def pressure_trim(scenario: str, load_scale: float = 1.0) -> Path:
    df = pd.read_csv(TRIM)
    for col in [c for c in df.columns if c.startswith("load_")]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0) * float(load_scale)
    out = INPUTS / f"{scenario}_TRIM.csv"
    df.to_csv(out, index=False)
    return out


def priority_file(scenario: str, beta: float) -> Path:
    df = pd.read_csv(PRIORITY)
    is_critical = pd.to_numeric(df["priority_level"], errors="coerce").fillna(3).astype(int) == 1
    df.loc[is_critical, "priority_weight"] = pd.to_numeric(df.loc[is_critical, "priority_weight"], errors="coerce").fillna(1.0) * (1.0 + float(beta))
    out = INPUTS / f"{scenario}_priority_beta{beta:.2f}.csv".replace(".", "p")
    df.to_csv(out, index=False)
    return out


def zero_failure_file() -> Path:
    out = INPUTS / "line_failure_zero_for_no_warning.csv"
    if out.exists():
        return out
    df = pd.read_csv(FAILURE)
    if "p_line" in df.columns:
        df["p_line"] = 0.0
    if "v_surface_ms" in df.columns:
        df["v_surface_ms"] = 0.0
    df.to_csv(out, index=False)
    return out


SCENARIOS = {
    "S1_load_plus20": {"load_scale": 1.20, "line_scale": 1.0, "reserve_ratio": 0.15},
    "S2_exposure_linecap_minus20": {"load_scale": 1.0, "line_scale": 1.0, "exposure_scale": 0.80, "reserve_ratio": 0.15},
    "S3_reserve_minus40": {"load_scale": 1.0, "line_scale": 1.0, "reserve_ratio": 0.09},
    "S4_high_risk_n1_outage": {"load_scale": 1.0, "line_scale": 1.0, "reserve_ratio": 0.15, "outage": True},
    "S5_combined_load20_linecap20": {"load_scale": 1.20, "line_scale": 1.0, "exposure_scale": 0.80, "reserve_ratio": 0.15},
}


def run_dispatch(
    scenario: str,
    warning_kind: str,
    grid: Path,
    trim: Path,
    priority: Path,
    reserve_ratio: float,
    top_k: int,
    alpha: float,
    beta: float,
    time_limit: float,
) -> dict[str, Any]:
    out_dir = RUNS / scenario / f"{warning_kind}_top{top_k}_alpha{alpha:.2f}_beta{beta:.2f}".replace(".", "p")
    log = LOGS / f"{scenario}_{warning_kind}_top{top_k}_alpha{alpha:.2f}_beta{beta:.2f}.log".replace(".", "p")
    line_risk = warning_file(warning_kind, scenario, top_k=top_k, alpha=alpha)
    failure_csv = zero_failure_file() if warning_kind == "no_warning" else FAILURE
    cmd = [
        str(PROJECT_PYTHON if PROJECT_PYTHON.exists() else Path(sys.executable)),
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
        str(priority),
        "--output-dir",
        str(out_dir),
        "--horizon-hours",
        "24",
        "--horizon-start-index",
        "24",
        "--reserve-ratio",
        str(reserve_ratio),
        "--line-derate-coeff",
        str(alpha),
        "--robust-line-factor",
        "0.90",
        "--robust-load-high",
        "1.20",
        "--robust-wind-low",
        "0.70",
        "--time-limit-sec",
        str(time_limit),
        "--seed",
        "60623",
    ]
    if line_risk is not None:
        cmd.extend(["--line-risk-csv", str(line_risk)])
    start = time.time()
    with log.open("w", encoding="utf-8") as f:
        proc = subprocess.run(cmd, cwd=STAGE7, stdout=f, stderr=subprocess.STDOUT, text=True)
    row: dict[str, Any] = {
        "scenario": scenario,
        "warning_strategy": warning_kind,
        "top_k": top_k,
        "alpha_max": alpha,
        "critical_load_beta": beta,
        "returncode": proc.returncode,
        "wall_runtime_sec": time.time() - start,
        "run_dir": rel(out_dir),
        "log": rel(log),
        "line_risk_csv": rel(line_risk) if line_risk else "",
    }
    comp = out_dir / "dispatch_model_comparison.csv"
    if comp.exists():
        df = pd.read_csv(comp)
        r = df[df["model"] == "Contextual_Adaptive"]
        if r.empty:
            r = df.head(1)
        rr = r.iloc[0]
        row.update(
            {
                "dispatch_cost": float(rr["total_cost"]),
                "eens": float(rr["EENS"]),
                "load_shedding": float(rr["EENS"]),
                "critical_load_supply_rate": float(rr["critical_load_supply_rate"]),
                "overload_count": int(rr["overload_count"]),
                "max_loading_ratio": float(rr["max_line_loading"]),
                "dispatch_runtime_sec": float(rr.get("runtime_sec", row["wall_runtime_sec"])),
                "source": rel(comp),
            }
        )
    return row


def result_score(row: dict[str, Any]) -> float:
    return (
        float(row.get("eens", 1e9)) * 1000.0
        + float(row.get("overload_count", 1e6)) * 100.0
        - float(row.get("critical_load_supply_rate", 0.0)) * 100.0
        + float(row.get("dispatch_cost", 0.0)) * 1e-5
    )


def experiment_4(time_limit: float) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    strategies = ["no_warning", "failure_prior", "mlp", "metapath_v1", "oracle"]
    for scenario, cfg in SCENARIOS.items():
        grid = pressure_grid(
            scenario,
            line_scale=float(cfg.get("line_scale", 1.0)),
            exposure_scale=cfg.get("exposure_scale"),
            outage=bool(cfg.get("outage", False)),
        )
        trim = pressure_trim(scenario, load_scale=float(cfg.get("load_scale", 1.0)))
        priority = priority_file(scenario, beta=1.0)
        for strategy in strategies:
            row = run_dispatch(
                scenario,
                strategy,
                grid,
                trim,
                priority,
                reserve_ratio=float(cfg.get("reserve_ratio", 0.15)),
                top_k=20,
                alpha=0.10,
                beta=1.0,
                time_limit=time_limit,
            )
            rows.append(row)
            write_csv(OUT / "experiment4_risk_aware_dispatch_under_stress.csv", rows)
    write_csv(OUT / "experiment4_risk_aware_dispatch_under_stress.csv", rows)
    return rows


def experiment_5(time_limit: float) -> list[dict[str, Any]]:
    scenario = "S5_combined_load20_linecap20"
    cfg = SCENARIOS[scenario]
    grid = pressure_grid(
        scenario,
        line_scale=float(cfg.get("line_scale", 1.0)),
        exposure_scale=cfg.get("exposure_scale"),
        outage=bool(cfg.get("outage", False)),
    )
    trim = pressure_trim(scenario, load_scale=float(cfg.get("load_scale", 1.0)))
    rows: list[dict[str, Any]] = []
    for top_k in [10, 20, 30]:
        for alpha in [0.05, 0.10, 0.15]:
            for beta in [0.5, 1.0, 2.0]:
                priority = priority_file(f"{scenario}_sens", beta=beta)
                row = run_dispatch(
                    f"{scenario}_sensitivity",
                    "metapath_v1",
                    grid,
                    trim,
                    priority,
                    reserve_ratio=float(cfg.get("reserve_ratio", 0.15)),
                    top_k=top_k,
                    alpha=alpha,
                    beta=beta,
                    time_limit=time_limit,
                )
                rows.append(row)
                rows_sorted = sorted(rows, key=result_score)
                write_csv(OUT / "experiment5_dispatch_sensitivity_analysis.csv", rows_sorted)
    rows = sorted(rows, key=result_score)
    write_csv(OUT / "experiment5_dispatch_sensitivity_analysis.csv", rows)
    return rows


def write_summary(exp4: list[dict[str, Any]], exp5: list[dict[str, Any]]) -> None:
    best_by_scenario = []
    for scenario in SCENARIOS:
        rows = [r for r in exp4 if r["scenario"] == scenario and r.get("returncode") == 0]
        if rows:
            best_by_scenario.append(min(rows, key=result_score))
    best_sens = exp5[0] if exp5 else {}
    lines = [
        "# Six PDF Experiments Results",
        "",
        "This package was generated from actual CSV/JSON outputs and dispatch reruns, not from the PDF notes.",
        "",
        "## Outputs",
        "",
        "- `experiment1_main_risk_probability_estimation.csv`",
        "- `experiment2_metapath_ablation_study.csv`",
        "- `experiment3_high_risk_line_identification.csv`",
        "- `experiment4_risk_aware_dispatch_under_stress.csv`",
        "- `experiment5_dispatch_sensitivity_analysis.csv`",
        "- `experiment6_runtime_scalability_analysis.csv`",
        "",
        "## Best Stress-Scenario Dispatch Rows",
        "",
    ]
    for r in best_by_scenario:
        lines.append(
            f"- {r['scenario']}: {r['warning_strategy']} top_k={r['top_k']} alpha={r['alpha_max']} "
            f"beta={r['critical_load_beta']} EENS={r.get('eens')} critical_supply={r.get('critical_load_supply_rate')} "
            f"cost={r.get('dispatch_cost')}"
        )
    if best_sens:
        lines.extend(
            [
                "",
                "## Best Sensitivity Setting",
                "",
                f"- top_k={best_sens['top_k']}, alpha={best_sens['alpha_max']}, beta={best_sens['critical_load_beta']}, "
                f"EENS={best_sens.get('eens')}, overload={best_sens.get('overload_count')}, "
                f"critical_supply={best_sens.get('critical_load_supply_rate')}, cost={best_sens.get('dispatch_cost')}",
            ]
        )
    (OUT / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    shutil.copy2(OUT / "README.md", PKG_OUT / "README.md")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-dispatch", action="store_true")
    parser.add_argument("--time-limit-sec", type=float, default=30.0)
    args = parser.parse_args()

    ensure_dirs()
    manifest: dict[str, Any] = {
        "started_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "pdf_experiment_source": "D:/yuhan/downloads/5 Experiments 实验列表.pdf",
        "output_dir": rel(OUT),
    }
    experiment_1_2_3_6_tables()
    exp4: list[dict[str, Any]] = []
    exp5: list[dict[str, Any]] = []
    if not args.skip_dispatch:
        exp4 = experiment_4(args.time_limit_sec)
        exp5 = experiment_5(args.time_limit_sec)
    write_summary(exp4, exp5)
    manifest["finished_at"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    manifest["outputs"] = [rel(p) for p in sorted(OUT.glob("experiment*.csv"))] + [rel(OUT / "README.md")]
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    shutil.copy2(OUT / "manifest.json", PKG_OUT / "manifest.json")


if __name__ == "__main__":
    main()
