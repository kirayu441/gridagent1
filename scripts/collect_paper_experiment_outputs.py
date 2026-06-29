from __future__ import annotations

import csv
import json
import math
import shutil
from pathlib import Path
from statistics import mean, stdev

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "result_final" / "paper_experiment_outputs"
PKG_OUT = ROOT / "paper_submission_package" / "results" / "paper_experiments"


def ensure_dirs() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    PKG_OUT.mkdir(parents=True, exist_ok=True)


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def write_csv(name: str, rows: list[dict], fieldnames: list[str] | None = None) -> None:
    if fieldnames is None:
        keys: list[str] = []
        for row in rows:
            for key in row:
                if key not in keys:
                    keys.append(key)
        fieldnames = keys
    path = OUT / name
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def copy_outputs() -> None:
    for path in OUT.glob("*"):
        if path.is_file():
            shutil.copy2(path, PKG_OUT / path.name)


def safe_float(value: object) -> float | None:
    try:
        if value is None or value == "":
            return None
        v = float(value)
        if math.isnan(v):
            return None
        return v
    except (TypeError, ValueError):
        return None


def collect_main_prediction_comparison() -> None:
    model_dirs = [
        ("Baseline GNN", "baseline_gnn"),
        ("MLP", "mlp"),
        ("GCN", "gcn"),
        ("GAT", "gat"),
        ("GraphSAGE", "graphsage"),
        ("STGCN", "stgcn"),
        ("GridAgent-Risk", "metapath_v1"),
    ]
    rows: list[dict] = []
    for label, dirname in model_dirs:
        path = ROOT / "results" / "ablation" / "stage6_comparison" / dirname / "metrics.csv"
        if not path.exists():
            continue
        df = pd.read_csv(path)
        if df.empty:
            continue
        r = df.iloc[0]
        mse = safe_float(r.get("best_val_mse"))
        rows.append(
            {
                "model": label,
                "mae": r.get("val_mae", ""),
                "rmse": math.sqrt(mse) if mse is not None else "",
                "high_risk_mae": r.get("high_risk_mae", ""),
                "recall_at_10": "",
                "hit_at_10": "",
                "spearman_corr": r.get("spearman_corr", ""),
                "train_time_seconds": r.get("train_time_seconds", ""),
                "source": rel(path),
                "source_note": "MAE/RMSE/high-risk MAE are direct existing outputs; recall_at_10 and hit_at_10 require saved predictions or rerun with ranking metrics.",
            }
        )
    write_csv(
        "main_prediction_comparison.csv",
        rows,
        [
            "model",
            "mae",
            "rmse",
            "high_risk_mae",
            "recall_at_10",
            "hit_at_10",
            "spearman_corr",
            "train_time_seconds",
            "source",
            "source_note",
        ],
    )


def collect_ablation_study() -> None:
    path = ROOT / "results" / "early_warning" / "stage6_planA_full_20260415_20260415_002847" / "all_runs.csv"
    df = pd.read_csv(path)
    df = df[(df["status"] == "ok") & (df["label_method"] == "c3po_ref")]
    rows: list[dict] = []
    for variant, g in df.groupby("model_group", sort=False):
        vals = {
            "mae": g["val_mae"].mean(),
            "rmse": g["val_rmse"].mean(),
            "high_risk_mae": g["val_high_risk_mae"].mean(),
            "best_val_mse": g["best_val_mse"].mean(),
            "n": len(g),
        }
        rows.append(
            {
                "variant": variant,
                "mae": vals["mae"],
                "rmse": vals["rmse"],
                "high_risk_mae": vals["high_risk_mae"],
                "recall_at_10": "",
                "n": vals["n"],
                "source": rel(path),
                "source_note": "A0-A3 structural ablation aggregated from existing five-seed PlanA runs; recall_at_10 was not logged in this run.",
            }
        )
    write_csv(
        "ablation_study.csv",
        rows,
        ["variant", "mae", "rmse", "high_risk_mae", "recall_at_10", "n", "source", "source_note"],
    )


def dcg(relevances: list[int]) -> float:
    return sum(rel / math.log2(i + 2) for i, rel in enumerate(relevances))


def collect_topk_identification() -> None:
    pred_path = ROOT / "result_final" / "standardized_results" / "warning" / "line_risk_prediction.csv"
    truth_path = ROOT / "result_final" / "standardized_results" / "scenario" / "component_failure_prob.csv"
    pred = pd.read_csv(pred_path)
    truth = pd.read_csv(truth_path)
    truth_scores = truth.groupby("line")["failure_prob"].max().sort_values(ascending=False)
    pred_scores = pred.set_index("line_id")["risk_prob"].sort_values(ascending=False)
    all_truth_lines = list(truth_scores.index)
    rows: list[dict] = []
    row: dict[str, object] = {"model": "GridAgent-Risk"}
    for k in [5, 10, 20]:
        pred_top = set(pred_scores.head(k).index)
        truth_top = set(all_truth_lines[:k])
        hits = len(pred_top & truth_top)
        row[f"precision_at_{k}"] = hits / max(len(pred_top), 1)
        row[f"recall_at_{k}"] = hits / max(len(truth_top), 1)
        relevances = [1 if line in truth_top else 0 for line in pred_scores.head(k).index]
        ideal = [1] * min(k, len(truth_top))
        denom = dcg(ideal)
        row[f"ndcg_at_{k}"] = dcg(relevances) / denom if denom > 0 else ""
    row["source"] = f"{rel(pred_path)}; {rel(truth_path)}"
    row["source_note"] = "Computed by comparing final line-risk ranking against max component failure probability over the standardized scenario horizon."
    rows.append(row)
    write_csv(
        "topk_risk_identification.csv",
        rows,
        [
            "model",
            "precision_at_5",
            "recall_at_5",
            "ndcg_at_5",
            "precision_at_10",
            "recall_at_10",
            "ndcg_at_10",
            "precision_at_20",
            "recall_at_20",
            "ndcg_at_20",
            "source",
            "source_note",
        ],
    )


def collect_downstream_dispatch() -> None:
    path = ROOT / "gridagent_final" / "stage7" / "outputs" / "formal_ieee118_full_contextual_stage1baseline_a2_c3po_ref_h24" / "dispatch_model_comparison.csv"
    df = pd.read_csv(path)
    rows = []
    for _, r in df.iterrows():
        rows.append(
            {
                "warning_strategy": r["model"],
                "dispatch_cost": r["total_cost"],
                "eens": r["EENS"],
                "critical_load_supply_rate": r["critical_load_supply_rate"],
                "overload_count": r["overload_count"],
                "runtime_sec": r["runtime_sec"],
                "source": rel(path),
                "source_note": "Existing Stage7 dispatch comparison. This compares dispatch formulations under the final warning context, not a no-warning/prior-only warning ablation.",
            }
        )
    write_csv(
        "downstream_dispatch_utility.csv",
        rows,
        [
            "warning_strategy",
            "dispatch_cost",
            "eens",
            "critical_load_supply_rate",
            "overload_count",
            "runtime_sec",
            "source",
            "source_note",
        ],
    )


def collect_dataset_statistics() -> None:
    topology_path = ROOT / "data_final" / "ieee118_full" / "grid_topology.json"
    aligned_path = ROOT / "gridagent_final" / "stage6" / "inputs" / "aligned_merged.guangdong2024.csv"
    fail_path = ROOT / "gridagent_final" / "stage6" / "inputs" / "line_failure_timeseries_schloemer.csv"
    summary_path = ROOT / "result_final" / "standardized_results" / "summary" / "experiment_summary.json"
    topology = json.loads(topology_path.read_text(encoding="utf-8"))
    aligned = pd.read_csv(aligned_path)
    failure = pd.read_csv(fail_path)
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    rows = [
        {
            "dataset": "IEEE118-full Guangdong-2024 final chain",
            "time_steps": len(aligned),
            "time_start": aligned["timestamp"].iloc[0],
            "time_end": aligned["timestamp"].iloc[-1],
            "feature_columns": len(aligned.columns) - 1,
            "nodes": len(topology.get("nodes", [])),
            "lines": len(topology.get("lines", [])),
            "generators": len(topology.get("generators", [])),
            "failure_rows": len(failure),
            "scenario_count": summary.get("selected_chain", {}).get("n_scenarios", ""),
            "source": f"{rel(topology_path)}; {rel(aligned_path)}; {rel(fail_path)}; {rel(summary_path)}",
        }
    ]
    write_csv("dataset_statistics.csv", rows)


def collect_risk_label_distribution() -> None:
    path = ROOT / "gridagent_final" / "stage6" / "inputs" / "line_failure_timeseries_schloemer.csv"
    df = pd.read_csv(path)
    bins = [
        ("zero", df["p_line"] <= 0),
        ("low_(0,0.01]", (df["p_line"] > 0) & (df["p_line"] <= 0.01)),
        ("medium_(0.01,0.10]", (df["p_line"] > 0.01) & (df["p_line"] <= 0.10)),
        ("high_>0.10", df["p_line"] > 0.10),
    ]
    total = len(df)
    rows = [
        {
            "risk_bin": name,
            "count": int(mask.sum()),
            "ratio": float(mask.sum() / total) if total else 0.0,
            "source": rel(path),
        }
        for name, mask in bins
    ]
    write_csv("risk_label_distribution.csv", rows)


def collect_runtime_scalability() -> None:
    rows: list[dict] = []
    for path in sorted((ROOT / "results" / "ablation" / "stage6_comparison").glob("*/metrics.csv")):
        df = pd.read_csv(path)
        if df.empty:
            continue
        r = df.iloc[0]
        rows.append(
            {
                "module": "warning_prediction",
                "setting": r.get("model_type", path.parent.name),
                "runtime_sec": r.get("train_time_seconds", ""),
                "num_parameters": r.get("num_parameters", ""),
                "source": rel(path),
            }
        )
    dpath = ROOT / "gridagent_final" / "stage7" / "outputs" / "formal_ieee118_full_contextual_stage1baseline_a2_c3po_ref_h24" / "dispatch_model_comparison.csv"
    ddf = pd.read_csv(dpath)
    for _, r in ddf.iterrows():
        rows.append(
            {
                "module": "dispatch_optimization",
                "setting": r["model"],
                "runtime_sec": r["runtime_sec"],
                "num_parameters": "",
                "source": rel(dpath),
            }
        )
    write_csv("runtime_scalability.csv", rows)


def collect_multi_window() -> None:
    path = ROOT / "results" / "timepoint_snapshots_formal2024_20240901_0000_1700" / "timepoint_snapshot_summary.csv"
    df = pd.read_csv(path)
    rows = []
    for _, r in df.iterrows():
        rows.append(
            {
                "timestamp": r["timestamp"],
                "selected_strategy": r["selected_strategy"],
                "hourly_line_risk": r["hourly_line_risk"],
                "hourly_uncertainty": r["hourly_uncertainty"],
                "total_load_shedding_mw": r["total_load_shedding_mw"],
                "overload_count": r["overload_line_count"],
                "max_line_loading": r["max_line_loading"],
                "source": rel(path),
                "source_note": "Existing two-window snapshot output; broader multi-window evaluation still requires more windows.",
            }
        )
    write_csv("multi_window_evaluation.csv", rows)


def collect_graph_structure_proxy() -> None:
    mapping = {
        "mlp": "no_explicit_graph_mlp_proxy",
        "gcn": "real_graph_gcn",
        "gat": "real_graph_gat",
        "graphsage": "real_graph_graphsage",
        "stgcn": "real_graph_stgcn",
        "metapath_v1": "real_graph_metapath",
    }
    rows = []
    for dirname, variant in mapping.items():
        path = ROOT / "results" / "ablation" / "stage6_comparison" / dirname / "metrics.csv"
        if not path.exists():
            continue
        r = pd.read_csv(path).iloc[0]
        rows.append(
            {
                "variant": variant,
                "mae": r["val_mae"],
                "rmse": math.sqrt(float(r["best_val_mse"])),
                "high_risk_mae": r["high_risk_mae"],
                "spearman_corr": r["spearman_corr"],
                "evidence_level": "proxy" if dirname == "mlp" else "real_graph_encoder",
                "source": rel(path),
                "source_note": "Proxy graph-structure table from existing encoder comparison; no random-graph or fully-connected-graph run was found.",
            }
        )
    write_csv("graph_structure_analysis.csv", rows)


def collect_status() -> None:
    rows = [
        {"experiment": "E1 dataset statistics", "status": "completed", "output": "dataset_statistics.csv"},
        {"experiment": "E8 main model vs baselines", "status": "partially_completed", "output": "main_prediction_comparison.csv"},
        {"experiment": "E9 top-k risk identification", "status": "completed_for_final_model_only", "output": "topk_risk_identification.csv"},
        {"experiment": "E10 ablation study", "status": "partially_completed", "output": "ablation_study.csv"},
        {"experiment": "E11 graph structure analysis", "status": "proxy_completed", "output": "graph_structure_analysis.csv"},
        {"experiment": "E12 downstream dispatch utility", "status": "partially_completed", "output": "downstream_dispatch_utility.csv"},
        {"experiment": "E13 multi-window evaluation", "status": "partial_two_windows", "output": "multi_window_evaluation.csv"},
        {"experiment": "E14 risk label distribution", "status": "completed", "output": "risk_label_distribution.csv"},
        {"experiment": "E15 runtime scalability", "status": "completed_from_existing_runs", "output": "runtime_scalability.csv"},
    ]
    write_csv("experiment_completion_status.csv", rows)


def collect_markdown_summary() -> None:
    files = sorted(p.name for p in OUT.glob("*.csv"))
    lines = [
        "# Paper experiment outputs",
        "",
        "Generated from existing verified result files. Fields with unavailable ranking metrics are left blank and documented in `source_note`.",
        "",
        "## Files",
        "",
    ]
    for name in files:
        lines.append(f"- `{name}`")
    lines.extend(
        [
            "",
            "## Remaining true rerun gaps",
            "",
            "- `main_prediction_comparison.csv`: `recall_at_10` and `hit_at_10` need saved model predictions or a Stage6 rerun with ranking metrics.",
            "- `ablation_study.csv`: A0-A3 MAE/RMSE/high-risk MAE are available, but Recall@10 was not logged.",
            "- `graph_structure_analysis.csv`: current file is an encoder proxy; random graph and fully connected graph variants still need dedicated runs.",
            "- `downstream_dispatch_utility.csv`: current file compares dispatch formulations under final warning context; no-warning/prior-only warning ablation still needs a dedicated run.",
            "- `multi_window_evaluation.csv`: current file has two existing snapshots; a formal multi-window table should add more windows.",
        ]
    )
    (OUT / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    ensure_dirs()
    collect_main_prediction_comparison()
    collect_ablation_study()
    collect_topk_identification()
    collect_downstream_dispatch()
    collect_dataset_statistics()
    collect_risk_label_distribution()
    collect_runtime_scalability()
    collect_multi_window()
    collect_graph_structure_proxy()
    collect_status()
    collect_markdown_summary()
    copy_outputs()


if __name__ == "__main__":
    main()
