from __future__ import annotations

import csv
import json
import shutil
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "result_final" / "paper_experiment_outputs_rerun"
PKG_OUT = ROOT / "paper_submission_package" / "results" / "paper_experiments_rerun"


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


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


def dataset_statistics() -> None:
    topology_path = ROOT / "data_final" / "ieee118_full" / "grid_topology.json"
    aligned_path = ROOT / "gridagent_final" / "stage6" / "inputs" / "aligned_merged.guangdong2024.csv"
    failure_path = ROOT / "gridagent_final" / "stage6" / "inputs" / "line_failure_timeseries_schloemer.csv"
    tensor_path = ROOT / "gridagent_final" / "stage6" / "inputs" / "contingency_tensor_c3po_ref.npy"
    topology = json.loads(topology_path.read_text(encoding="utf-8"))
    aligned = pd.read_csv(aligned_path)
    failure = pd.read_csv(failure_path)
    rows = [
        {
            "dataset": "IEEE118-full Guangdong-2024 rerun chain",
            "time_steps": len(aligned),
            "time_start": aligned["timestamp"].iloc[0],
            "time_end": aligned["timestamp"].iloc[-1],
            "feature_columns": len(aligned.columns) - 1,
            "nodes": len(topology.get("nodes", [])),
            "lines": len(topology.get("lines", [])),
            "generators": len(topology.get("generators", [])),
            "failure_rows": len(failure),
            "stage6_failure_window_steps": failure["timestamp"].nunique(),
            "scenario_count": 256,
            "contingency_tensor": rel(tensor_path),
            "source": f"{rel(topology_path)}; {rel(aligned_path)}; {rel(failure_path)}",
        }
    ]
    write_csv(OUT / "dataset_statistics.csv", rows)


def risk_label_distribution() -> None:
    path = ROOT / "gridagent_final" / "stage6" / "inputs" / "line_failure_timeseries_schloemer.csv"
    df = pd.read_csv(path)
    bins = [
        ("zero", df["p_line"] <= 0),
        ("low_(0,0.01]", (df["p_line"] > 0) & (df["p_line"] <= 0.01)),
        ("medium_(0.01,0.10]", (df["p_line"] > 0.01) & (df["p_line"] <= 0.10)),
        ("high_>0.10", df["p_line"] > 0.10),
    ]
    rows = []
    for name, mask in bins:
        rows.append({"risk_bin": name, "count": int(mask.sum()), "ratio": float(mask.mean()), "source": rel(path)})
    write_csv(OUT / "risk_label_distribution.csv", rows)


def runtime_scalability() -> None:
    rows = []
    main_manifest = OUT / "run_manifest.json"
    if main_manifest.exists():
        data = json.loads(main_manifest.read_text(encoding="utf-8"))
        for run in data.get("runs", []):
            rows.append(
                {
                    "module": "stage6_prediction",
                    "setting": run.get("model"),
                    "runtime_sec": run.get("runtime_sec"),
                    "source": rel(main_manifest),
                }
            )
    ablation_manifest = OUT / "ablation_run_manifest.json"
    if ablation_manifest.exists():
        data = json.loads(ablation_manifest.read_text(encoding="utf-8"))
        for run in data.get("runs", []):
            rows.append(
                {
                    "module": "stage6_ablation",
                    "setting": f"{run.get('variant')}_seed_{run.get('seed')}",
                    "runtime_sec": run.get("runtime_sec"),
                    "source": rel(ablation_manifest),
                }
            )
    dispatch_manifest = OUT / "dispatch_run_manifest.json"
    if dispatch_manifest.exists():
        data = json.loads(dispatch_manifest.read_text(encoding="utf-8"))
        for run in data.get("runs", []):
            rows.append(
                {
                    "module": "stage7_dispatch",
                    "setting": run.get("warning_strategy"),
                    "runtime_sec": run.get("runtime_sec"),
                    "source": rel(dispatch_manifest),
                }
            )
    write_csv(OUT / "runtime_scalability.csv", rows)


def completion_status() -> None:
    rows = [
        {"experiment": "E1 dataset statistics", "status": "completed_rerun", "output": "dataset_statistics.csv"},
        {"experiment": "E8 main model vs baselines", "status": "completed_rerun", "output": "main_prediction_comparison.csv"},
        {"experiment": "E9 top-k risk identification", "status": "completed_rerun", "output": "topk_risk_identification.csv"},
        {"experiment": "E10 ablation study", "status": "completed_rerun_5seeds", "output": "ablation_study.csv"},
        {"experiment": "E11 graph structure analysis", "status": "completed_encoder_comparison", "output": "graph_structure_analysis.csv"},
        {"experiment": "E12 downstream dispatch utility", "status": "completed_rerun", "output": "downstream_dispatch_utility.csv"},
        {"experiment": "E13 multi-window evaluation", "status": "completed_24h_dispatch_selection", "output": "multi_window_evaluation.csv"},
        {"experiment": "E14 risk label distribution", "status": "completed_rerun", "output": "risk_label_distribution.csv"},
        {"experiment": "E15 runtime scalability", "status": "completed_rerun", "output": "runtime_scalability.csv"},
    ]
    write_csv(OUT / "experiment_completion_status.csv", rows)


def readme() -> None:
    lines = [
        "# Paper experiment rerun outputs",
        "",
        "This directory contains rerun-backed experiment tables for the ICDE paper package.",
        "",
        "## Core files",
        "",
    ]
    for name in [
        "dataset_statistics.csv",
        "main_prediction_comparison.csv",
        "topk_risk_identification.csv",
        "ablation_study.csv",
        "ablation_study_runs.csv",
        "graph_structure_analysis.csv",
        "downstream_dispatch_utility.csv",
        "multi_window_evaluation.csv",
        "risk_label_distribution.csv",
        "runtime_scalability.csv",
        "experiment_completion_status.csv",
    ]:
        lines.append(f"- `{name}`")
    lines.extend(
        [
            "",
            "## Run manifests",
            "",
            "- `run_manifest.json`: E8/E9 model reruns.",
            "- `ablation_run_manifest.json`: E10 full-grid ablation reruns.",
            "- `dispatch_run_manifest.json`: E12/E13 dispatch reruns.",
            "",
            "All CSV files are also synced to `paper_submission_package/results/paper_experiments_rerun`.",
        ]
    )
    (OUT / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def sync() -> None:
    PKG_OUT.mkdir(parents=True, exist_ok=True)
    for path in OUT.glob("*"):
        if path.is_file() and path.suffix.lower() in {".csv", ".json", ".md", ".log"}:
            shutil.copy2(path, PKG_OUT / path.name)


def main() -> None:
    dataset_statistics()
    risk_label_distribution()
    runtime_scalability()
    completion_status()
    readme()
    sync()


if __name__ == "__main__":
    main()
