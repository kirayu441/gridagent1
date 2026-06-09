from __future__ import annotations

import csv
import json
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "result_final" / "paper_experiment_outputs_rerun"
PKG_OUT = ROOT / "paper_submission_package" / "results" / "paper_experiments_rerun"
RUN_ROOT = OUT / "stage6_model_runs"
LOG_ROOT = OUT / "logs"

GRID = ROOT / "gridagent_final" / "stage6" / "inputs" / "grid_topology.ieee118_full.json"
ALIGNED = ROOT / "gridagent_final" / "stage6" / "inputs" / "aligned_merged.guangdong2024.csv"
FAILURE = ROOT / "gridagent_final" / "stage6" / "inputs" / "line_failure_timeseries_schloemer.csv"


MODEL_ORDER = [
    "mlp",
    "baseline_gnn",
    "graphsage",
    "gat",
    "stgcn",
    "metapath_v1",
    "metapath_local",
    "gcn",
]


def ensure_dirs() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    PKG_OUT.mkdir(parents=True, exist_ok=True)
    RUN_ROOT.mkdir(parents=True, exist_ok=True)
    LOG_ROOT.mkdir(parents=True, exist_ok=True)


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def run_model(model: str) -> dict:
    out_dir = RUN_ROOT / model
    log_path = LOG_ROOT / f"{model}.log"
    cmd = [
        sys.executable,
        str(ROOT / "scripts" / "gnn_ablation_experiment.py"),
        "--model-type",
        model,
        "--output-dir",
        str(out_dir),
        "--grid-path",
        str(GRID),
        "--aligned-csv",
        str(ALIGNED),
        "--failure-csv",
        str(FAILURE),
        "--hidden-dim",
        "80",
        "--epochs",
        "700",
        "--patience",
        "60",
        "--learning-rate",
        "0.00315",
        "--weight-decay",
        "0.00015",
        "--train-ratio",
        "0.7",
        "--metapath-topk",
        "4",
        "--seed",
        "42",
    ]
    start = time.time()
    with log_path.open("w", encoding="utf-8") as log:
        proc = subprocess.run(cmd, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT, text=True)
    return {
        "model": model,
        "returncode": proc.returncode,
        "runtime_sec": time.time() - start,
        "output_dir": rel(out_dir),
        "log": rel(log_path),
    }


def write_csv(path: Path, rows: list[dict], fieldnames: list[str] | None = None) -> None:
    if fieldnames is None:
        fields: list[str] = []
        for row in rows:
            for key in row:
                if key not in fields:
                    fields.append(key)
        fieldnames = fields
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def historical_average_baseline() -> None:
    from gnn_warning_module import build_dataset, load_failure_features, load_grid_topology

    ts, line_ids, p_arr, v_arr, edge_map = load_failure_features(FAILURE)
    data = build_dataset(
        grid_payload=load_grid_topology(GRID),
        timestamps=ts,
        line_ids=line_ids,
        edge_map=edge_map,
        p_line=p_arr,
        v_surface=v_arr,
        labels=p_arr,
        aligned_csv=ALIGNED,
        priority_csv=None,
        metapath_topk=4,
    )
    split = int(np.floor(len(ts) * 0.7))
    train = data.labels[:split]
    truth = data.labels[split:]
    pred = np.repeat(train.mean(axis=0, keepdims=True), truth.shape[0], axis=0)
    out_dir = RUN_ROOT / "historical_average"
    out_dir.mkdir(parents=True, exist_ok=True)

    wide_pred = pd.DataFrame(pred, columns=data.line_ids)
    wide_pred.insert(0, "timestamp", data.timestamps[split:].astype(str).to_numpy())
    wide_pred.to_csv(out_dir / "validation_predictions_wide.csv", index=False)
    wide_truth = pd.DataFrame(truth, columns=data.line_ids)
    wide_truth.insert(0, "timestamp", data.timestamps[split:].astype(str).to_numpy())
    wide_truth.to_csv(out_dir / "validation_truth_wide.csv", index=False)

    pred_score = pred.max(axis=0)
    truth_score = truth.max(axis=0)
    rank_df = pd.DataFrame(
        {
            "line_id": data.line_ids,
            "predicted_max_risk": pred_score,
            "true_max_risk": truth_score,
        }
    )
    rank_df["predicted_rank"] = rank_df["predicted_max_risk"].rank(method="first", ascending=False).astype(int)
    rank_df["true_rank"] = rank_df["true_max_risk"].rank(method="first", ascending=False).astype(int)
    rank_df.sort_values("predicted_rank").to_csv(out_dir / "line_ranking_validation.csv", index=False)

    err = pred - truth
    metrics = compute_metrics_from_arrays(pred, truth, runtime=0.0, num_parameters=0)
    metrics["model_type"] = "historical_average"
    pd.DataFrame([metrics]).to_csv(out_dir / "metrics.csv", index=False)


def dcg(relevances: list[int]) -> float:
    return float(sum(rel / np.log2(i + 2) for i, rel in enumerate(relevances)))


def topk_metrics(pred: np.ndarray, truth: np.ndarray) -> dict[str, float]:
    pred_score = pred.max(axis=0)
    truth_score = truth.max(axis=0)
    pred_order = list(np.argsort(-pred_score))
    truth_order = list(np.argsort(-truth_score))
    metrics: dict[str, float] = {}
    for k in [5, 10, 20]:
        kk = min(k, len(pred_order), len(truth_order))
        pred_top = set(pred_order[:kk])
        truth_top = set(truth_order[:kk])
        hits = len(pred_top & truth_top)
        metrics[f"precision_at_{k}"] = hits / max(len(pred_top), 1)
        metrics[f"recall_at_{k}"] = hits / max(len(truth_top), 1)
        metrics[f"hit_at_{k}"] = 1.0 if hits > 0 else 0.0
        rels = [1 if idx in truth_top else 0 for idx in pred_order[:kk]]
        metrics[f"ndcg_at_{k}"] = dcg(rels) / dcg([1] * kk)
    return metrics


def compute_metrics_from_arrays(pred: np.ndarray, truth: np.ndarray, runtime: float, num_parameters: int) -> dict:
    err = pred - truth
    mae = float(np.mean(np.abs(err)))
    rmse = float(np.sqrt(np.mean(err**2)))
    mask = truth >= 0.1
    if mask.any():
        high_risk_mae = float(np.mean(np.abs(err[mask])))
    else:
        threshold = float(np.quantile(truth.reshape(-1), 0.9))
        top_mask = truth >= threshold
        high_risk_mae = float(np.mean(np.abs(err[top_mask]))) if top_mask.any() else float("nan")
    corr = pd.Series(pred.reshape(-1)).corr(pd.Series(truth.reshape(-1)), method="spearman")
    metrics = {
        "train_time_seconds": runtime,
        "val_mae": mae,
        "horizon_mae": float(np.mean(np.abs(pred[int(pred.shape[0] * 0.8) :] - truth[int(truth.shape[0] * 0.8) :]))),
        "best_val_mse": float(np.mean(err**2)),
        "high_risk_mae": high_risk_mae,
        "top_risk_mae": high_risk_mae,
        "spearman_corr": float(corr) if pd.notna(corr) else 0.0,
        "num_parameters": num_parameters,
    }
    metrics.update(topk_metrics(pred, truth))
    return metrics


def collect_stage6_tables() -> None:
    rows: list[dict] = []
    topk_rows: list[dict] = []
    graph_rows: list[dict] = []
    label_map = {
        "historical_average": "Historical Average",
        "mlp": "MLP",
        "baseline_gnn": "Baseline GNN",
        "gcn": "GCN",
        "gat": "GAT",
        "graphsage": "GraphSAGE",
        "stgcn": "STGCN",
        "metapath_v1": "GridAgent-Risk",
        "metapath_local": "GridAgent-Risk-Local",
    }
    for model, label in label_map.items():
        path = RUN_ROOT / model / "metrics.csv"
        if not path.exists():
            continue
        r = pd.read_csv(path).iloc[0].to_dict()
        high_risk_mae = r.get("high_risk_mae", "")
        try:
            if pd.isna(float(high_risk_mae)):
                high_risk_mae = r.get("top_risk_mae", "")
        except (TypeError, ValueError):
            high_risk_mae = r.get("top_risk_mae", "")
        row = {
            "model": label,
            "mae": r.get("val_mae", ""),
            "rmse": np.sqrt(float(r.get("best_val_mse", 0.0))),
            "high_risk_mae": high_risk_mae,
            "recall_at_10": r.get("recall_at_10", ""),
            "hit_at_10": r.get("hit_at_10", ""),
            "ndcg_at_10": r.get("ndcg_at_10", ""),
            "spearman_corr": r.get("spearman_corr", ""),
            "runtime_sec": r.get("train_time_seconds", ""),
            "source": rel(path),
        }
        rows.append(row)
        topk_rows.append(
            {
                "model": label,
                "precision_at_5": r.get("precision_at_5", ""),
                "recall_at_5": r.get("recall_at_5", ""),
                "precision_at_10": r.get("precision_at_10", ""),
                "recall_at_10": r.get("recall_at_10", ""),
                "recall_at_20": r.get("recall_at_20", ""),
                "ndcg_at_10": r.get("ndcg_at_10", ""),
                "source": rel(path),
            }
        )
        if model in {"mlp", "gcn", "gat", "graphsage", "stgcn", "metapath_v1", "metapath_local"}:
            graph_rows.append(
                {
                    "variant": {
                        "mlp": "no_graph_mlp",
                        "gcn": "physical_graph_gcn",
                        "gat": "physical_graph_gat",
                        "graphsage": "physical_graph_graphsage",
                        "stgcn": "physical_graph_stgcn",
                        "metapath_v1": "physical_graph_metapath",
                        "metapath_local": "metapath_local_residual",
                    }[model],
                    "mae": r.get("val_mae", ""),
                    "rmse": np.sqrt(float(r.get("best_val_mse", 0.0))),
                    "high_risk_mae": high_risk_mae,
                    "recall_at_10": r.get("recall_at_10", ""),
                    "ndcg_at_10": r.get("ndcg_at_10", ""),
                    "source": rel(path),
                }
            )
    write_csv(OUT / "main_prediction_comparison.csv", rows)
    write_csv(OUT / "topk_risk_identification.csv", topk_rows)
    write_csv(OUT / "graph_structure_analysis.csv", graph_rows)


def export_metapath_local_seed_stability() -> None:
    stability_src = ROOT / "results" / "ablation" / "stage6_local_seed_sweep" / "seed_sweep_summary.csv"
    if not stability_src.exists():
        return
    df = pd.read_csv(stability_src, header=[0, 1], index_col=0)
    rows: list[dict] = []
    for model, values in df.iterrows():
        row: dict[str, object] = {"model": model}
        for metric, stat in df.columns:
            row[f"{metric}_{stat}"] = values[(metric, stat)]
        rows.append(row)
    write_csv(OUT / "metapath_local_seed_stability.csv", rows)


def update_ablation_study_with_metapath_local() -> None:
    ablation_path = OUT / "ablation_study.csv"
    stability_path = OUT / "metapath_local_seed_stability.csv"
    if not ablation_path.exists() or not stability_path.exists():
        return
    ablation = pd.read_csv(ablation_path)
    stability = pd.read_csv(stability_path)
    local = stability[stability["model"].eq("metapath_local")]
    if local.empty:
        return
    r = local.iloc[0]
    ablation = ablation[~ablation["variant"].eq("A4_metapath_local_residual")]
    new_row = {
        "variant": "A4_metapath_local_residual",
        "mae": r.get("val_mae_mean", ""),
        "rmse": np.sqrt(float(r.get("best_val_mse_mean", 0.0))),
        "high_risk_mae": r.get("high_risk_mae_mean", ""),
        "recall_at_10": r.get("precision_at_10_mean", ""),
        "ndcg_at_10": r.get("ndcg_at_10_mean", ""),
        "n": 5,
        "source": rel(stability_path),
    }
    ablation = pd.concat([ablation, pd.DataFrame([new_row])], ignore_index=True)
    ablation.to_csv(ablation_path, index=False)


def sync_outputs() -> None:
    for path in OUT.glob("*"):
        if path.is_file():
            import shutil

            shutil.copy2(path, PKG_OUT / path.name)


def main() -> None:
    ensure_dirs()
    manifest = {
        "started_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "data": {
            "grid": rel(GRID),
            "aligned": rel(ALIGNED),
            "failure": rel(FAILURE),
        },
        "runs": [],
    }
    historical_average_baseline()
    manifest["runs"].append({"model": "historical_average", "returncode": 0, "runtime_sec": 0.0})
    for model in MODEL_ORDER:
        info = run_model(model)
        manifest["runs"].append(info)
        (OUT / "run_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        if info["returncode"] != 0:
            break
    manifest["finished_at"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    (OUT / "run_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    collect_stage6_tables()
    export_metapath_local_seed_stability()
    update_ablation_study_with_metapath_local()
    sync_outputs()


if __name__ == "__main__":
    sys.path.insert(0, str(ROOT / "scripts"))
    main()
