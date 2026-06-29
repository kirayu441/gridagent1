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
RUN_ROOT = OUT / "stage6_ablation_runs"
LOG_ROOT = OUT / "logs_ablation"

GRID = ROOT / "gridagent_final" / "stage6" / "inputs" / "grid_topology.ieee118_full.json"
ALIGNED = ROOT / "gridagent_final" / "stage6" / "inputs" / "aligned_merged.guangdong2024.csv"
FAILURE = ROOT / "gridagent_final" / "stage6" / "inputs" / "line_failure_timeseries_schloemer.csv"
TENSOR = ROOT / "gridagent_final" / "stage6" / "inputs" / "contingency_tensor_c3po_ref.npy"
PRIORITY = ROOT / "gridagent_final" / "stage6" / "inputs" / "load_bus_priority_profile.csv"


VARIANTS = [
    {
        "variant": "A0_baseline_no_metapath",
        "metapath": False,
        "attention": "fixed",
        "risk_alpha": 0.0,
        "risk_beta": 0.0,
        "gate_reg": 0.0,
        "entropy_reg": 0.0,
        "warmup": 0,
    },
    {
        "variant": "A1_metapath_fixed",
        "metapath": True,
        "attention": "fixed",
        "risk_alpha": 0.0,
        "risk_beta": 0.0,
        "gate_reg": 0.0,
        "entropy_reg": 0.0,
        "warmup": 0,
    },
    {
        "variant": "A2_metapath_adaptive_global",
        "metapath": True,
        "attention": "adaptive_global",
        "risk_alpha": 0.0,
        "risk_beta": 0.0,
        "gate_reg": 0.0,
        "entropy_reg": 0.0,
        "warmup": 0,
    },
    {
        "variant": "A3_full_training_enhanced",
        "metapath": True,
        "attention": "adaptive_global",
        "risk_alpha": 1.0,
        "risk_beta": 2.0,
        "gate_reg": 0.0002,
        "entropy_reg": 0.0,
        "warmup": 12,
    },
]


SEEDS = [42, 43, 44, 45, 46]


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def ensure_dirs() -> None:
    RUN_ROOT.mkdir(parents=True, exist_ok=True)
    LOG_ROOT.mkdir(parents=True, exist_ok=True)
    PKG_OUT.mkdir(parents=True, exist_ok=True)


def run_case(variant: dict, seed: int) -> dict:
    name = f"{variant['variant']}_seed_{seed}"
    out_dir = RUN_ROOT / name
    log_path = LOG_ROOT / f"{name}.log"
    cmd = [
        sys.executable,
        str(ROOT / "scripts" / "gnn_warning_module.py"),
        "--grid",
        str(GRID),
        "--aligned",
        str(ALIGNED),
        "--failure-csv",
        str(FAILURE),
        "--contingency-tensor",
        str(TENSOR),
        "--load-priority-csv",
        str(PRIORITY),
        "--output-dir",
        str(out_dir),
        "--horizon-hours",
        "24",
        "--horizon-start-index",
        "24",
        "--train-ratio",
        "0.7",
        "--hidden-dim",
        "80",
        "--epochs",
        "700",
        "--lr",
        "0.00315",
        "--weight-decay",
        "0.00015",
        "--mc-scenarios",
        "3000",
        "--metapath-attention-mode",
        str(variant["attention"]),
        "--metapath-topk",
        "4",
        "--risk-weight-alpha",
        str(variant["risk_alpha"]),
        "--risk-weight-beta",
        str(variant["risk_beta"]),
        "--risk-weight-threshold",
        "0.10",
        "--metapath-gate-reg-lambda",
        str(variant["gate_reg"]),
        "--metapath-attention-entropy-reg-lambda",
        str(variant["entropy_reg"]),
        "--metapath-warmup-epochs",
        str(variant["warmup"]),
        "--high-risk-threshold",
        "0.10",
        "--top-risk-quantile",
        "0.90",
        "--seed",
        str(seed),
        "--no-run-baseline-comparison",
    ]
    cmd.append("--metapath-v1-enabled" if variant["metapath"] else "--no-metapath-v1-enabled")
    start = time.time()
    with log_path.open("w", encoding="utf-8") as log:
        proc = subprocess.run(cmd, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT, text=True)
    return {
        "variant": variant["variant"],
        "seed": seed,
        "returncode": proc.returncode,
        "runtime_sec": time.time() - start,
        "run_dir": rel(out_dir),
        "log": rel(log_path),
    }


def dcg(relevances: list[int]) -> float:
    return float(sum(rel / np.log2(i + 2) for i, rel in enumerate(relevances)))


def topk_from_line_risk(line_path: Path) -> dict[str, float]:
    pred = pd.read_csv(line_path)
    pred_order = pred.sort_values("risk_prob", ascending=False)["line_id"].tolist()

    tensor = np.load(TENSOR)
    truth = tensor.mean(axis=0)[24:48].max(axis=0)
    line_ids = [f"L{i}" for i in range(truth.shape[0])]
    truth_order = [line_ids[i] for i in np.argsort(-truth)]

    out: dict[str, float] = {}
    for k in [5, 10, 20]:
        kk = min(k, len(pred_order), len(truth_order))
        pred_top = set(pred_order[:kk])
        truth_top = set(truth_order[:kk])
        hits = len(pred_top & truth_top)
        out[f"precision_at_{k}"] = hits / max(len(pred_top), 1)
        out[f"recall_at_{k}"] = hits / max(len(truth_top), 1)
        rels = [1 if line in truth_top else 0 for line in pred_order[:kk]]
        out[f"ndcg_at_{k}"] = dcg(rels) / dcg([1] * kk)
    return out


def read_metrics(run_dir: Path) -> dict:
    report_path = run_dir / "warning_report.json"
    report = json.loads(report_path.read_text(encoding="utf-8"))
    val = report["fit_quality"]["validation"]
    training = report["training"]
    line_path = run_dir / "line_risk_prediction.csv"
    topk = topk_from_line_risk(line_path)
    high = val.get("high_risk_mae")
    if high is None or pd.isna(high):
        high = val.get("top_risk_mae")
    return {
        "mae": val.get("mae"),
        "rmse": val.get("rmse"),
        "high_risk_mae": high,
        "best_val_mse": training.get("best_val_mse"),
        **topk,
        "source": rel(report_path),
    }


def write_csv(path: Path, rows: list[dict]) -> None:
    fields: list[str] = []
    for row in rows:
        for key in row:
            if key not in fields:
                fields.append(key)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def aggregate() -> None:
    rows = []
    for variant in VARIANTS:
        for seed in SEEDS:
            run_dir = RUN_ROOT / f"{variant['variant']}_seed_{seed}"
            if not (run_dir / "warning_report.json").exists():
                continue
            rows.append({"variant": variant["variant"], "seed": seed, **read_metrics(run_dir)})
    write_csv(OUT / "ablation_study_runs.csv", rows)

    df = pd.DataFrame(rows)
    summary = []
    for variant, g in df.groupby("variant", sort=False):
        summary.append(
            {
                "variant": variant,
                "mae": g["mae"].mean(),
                "rmse": g["rmse"].mean(),
                "high_risk_mae": g["high_risk_mae"].mean(),
                "recall_at_10": g["recall_at_10"].mean(),
                "ndcg_at_10": g["ndcg_at_10"].mean(),
                "n": len(g),
                "source": "result_final/paper_experiment_outputs_rerun/ablation_study_runs.csv",
            }
        )
    write_csv(OUT / "ablation_study.csv", summary)


def sync_outputs() -> None:
    import shutil

    for path in [OUT / "ablation_study.csv", OUT / "ablation_study_runs.csv"]:
        if path.exists():
            shutil.copy2(path, PKG_OUT / path.name)


def main() -> None:
    ensure_dirs()
    manifest = {"started_at": time.strftime("%Y-%m-%dT%H:%M:%S"), "runs": []}
    for variant in VARIANTS:
        for seed in SEEDS:
            info = run_case(variant, seed)
            manifest["runs"].append(info)
            (OUT / "ablation_run_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
            if info["returncode"] != 0:
                manifest["failed_at"] = time.strftime("%Y-%m-%dT%H:%M:%S")
                (OUT / "ablation_run_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
                raise SystemExit(info["returncode"])
    manifest["finished_at"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    (OUT / "ablation_run_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    aggregate()
    sync_outputs()


if __name__ == "__main__":
    main()
