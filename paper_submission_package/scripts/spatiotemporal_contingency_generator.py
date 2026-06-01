from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import networkx as nx
import numpy as np
import pandas as pd
from scipy.stats import qmc


@dataclass
class FailureInput:
    timestamps: pd.DatetimeIndex
    line_ids: list[str]
    p_line: np.ndarray
    line_edges: list[tuple[int, int]]


def project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def parse_optional_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        out = float(value)
    except (TypeError, ValueError):
        return None
    if np.isnan(out):
        return None
    return float(out)


def load_failure_input(path: Path, max_steps: int | None) -> FailureInput:
    if not path.exists():
        raise FileNotFoundError(f"missing file: {path}")

    frame = pd.read_csv(path)
    required = {"timestamp", "line_id", "from_bus", "to_bus", "p_line"}
    missing = required - set(frame.columns)
    if missing:
        raise ValueError(f"failure csv missing columns: {sorted(missing)}")

    frame["timestamp"] = pd.to_datetime(frame["timestamp"], errors="coerce")
    if frame["timestamp"].isna().any():
        raise ValueError("invalid timestamp in failure csv")

    pivot = (
        frame.pivot_table(index="timestamp", columns="line_id", values="p_line", aggfunc="mean")
        .sort_index()
        .sort_index(axis=1)
    )
    if pivot.empty:
        raise ValueError("empty p_line matrix after pivot")

    if max_steps is not None and max_steps > 0:
        pivot = pivot.iloc[:max_steps, :]

    line_ids = [str(x) for x in pivot.columns]
    timestamps = pd.DatetimeIndex(pivot.index)
    p_line = np.clip(pivot.to_numpy(dtype=float), 0.0, 1.0)

    edge_map = (
        frame.drop_duplicates(subset=["line_id"])
        .set_index("line_id")[["from_bus", "to_bus"]]
        .to_dict(orient="index")
    )
    line_edges: list[tuple[int, int]] = []
    for line_id in line_ids:
        item = edge_map.get(line_id)
        if item is None:
            raise ValueError(f"line {line_id} has no edge mapping")
        line_edges.append((int(item["from_bus"]), int(item["to_bus"])))

    return FailureInput(
        timestamps=timestamps,
        line_ids=line_ids,
        p_line=p_line,
        line_edges=line_edges,
    )


def load_grid_roles(grid_path: Path) -> tuple[list[int], list[int], list[int]]:
    if not grid_path.exists():
        raise FileNotFoundError(f"missing file: {grid_path}")
    payload = json.loads(grid_path.read_text(encoding="utf-8"))

    nodes = payload.get("nodes", [])
    generators = payload.get("generators", [])
    lines = payload.get("lines", [])
    if not nodes or not lines:
        raise ValueError(f"invalid grid topology: {grid_path}")

    all_buses = sorted({int(n["id"]) for n in nodes if "id" in n})
    load_buses = sorted({int(n["id"]) for n in nodes if str(n.get("type", "")).lower() == "load"})
    source_buses_positive = sorted(
        {
            int(g["bus"])
            for g in generators
            if "bus" in g and (parse_optional_float(g.get("capacity")) or 0.0) > 0.0
        }
    )
    source_buses_special = sorted(
        {
            int(g["bus"])
            for g in generators
            if "bus" in g and str(g.get("type", "")).lower() in {"thermal", "slack", "ext_grid"}
        }
    )
    source_buses = sorted(set(source_buses_positive) | set(source_buses_special))
    if not source_buses:
        source_buses = [all_buses[0]]
    return all_buses, load_buses, source_buses


def sobol_uniforms(n_scenarios: int, n_time: int, n_line: int, seed: int) -> np.ndarray:
    dim = n_time * n_line
    m_power = int(np.ceil(np.log2(max(n_scenarios, 2))))
    sampler = qmc.Sobol(d=dim, scramble=True, seed=seed)
    draws = sampler.random_base2(m=m_power)[:n_scenarios]
    return draws.reshape(n_scenarios, n_time, n_line)


def wang_stateful_contingency(
    p_line: np.ndarray,
    uniforms: np.ndarray,
    warning_end_t: int,
    repair_hours: int,
) -> np.ndarray:
    n_scenarios, n_time, n_line = uniforms.shape
    normal_state = np.ones((n_scenarios, n_line), dtype=np.int8)
    outages = np.zeros((n_scenarios, n_time, n_line), dtype=np.int8)

    for t in range(n_time):
        if t >= warning_end_t + repair_hours:
            outages[:, t, :] = 0
            normal_state[:, :] = 1
            continue
        p_t = p_line[t, :][None, :]
        pm = 1.0 - normal_state * (1.0 - p_t)
        outage_t = (uniforms[:, t, :] < pm).astype(np.int8)
        outages[:, t, :] = outage_t
        normal_state[:, :] = 1 - outage_t
    return outages


def c3po_reference_contingency(p_line: np.ndarray, uniforms: np.ndarray) -> np.ndarray:
    return (uniforms < p_line[None, :, :]).astype(np.int8)


def trim_reference_contingency(
    p_line: np.ndarray,
    n_scenarios: int,
    seed: int,
    phi: float = 0.85,
    alpha: float = 0.75,
    beta: float = 0.45,
) -> np.ndarray:
    rng = np.random.default_rng(seed)
    n_time, n_line = p_line.shape

    clipped = np.clip(p_line, 1e-5, 1.0 - 1e-5)
    logit = np.log(clipped / (1.0 - clipped))
    line_mean = p_line.mean(axis=0)
    line_weight = (line_mean - line_mean.mean()) / max(float(line_mean.std()), 1e-6)

    noise = rng.normal(0.0, 1.0, size=(n_scenarios, n_time))
    stress = np.zeros((n_scenarios, n_time), dtype=float)
    for t in range(n_time):
        if t == 0:
            stress[:, t] = noise[:, t]
        else:
            stress[:, t] = phi * stress[:, t - 1] + np.sqrt(max(1.0 - phi**2, 1e-8)) * noise[:, t]

    adjusted = (
        logit[None, :, :]
        + alpha * stress[:, :, None]
        + beta * line_weight[None, None, :]
    )
    prob = 1.0 / (1.0 + np.exp(-adjusted))
    uniforms = rng.random((n_scenarios, n_time, n_line))
    return (uniforms < prob).astype(np.int8)


def disconnected_load_matrix(
    outages: np.ndarray,
    line_edges: list[tuple[int, int]],
    all_buses: list[int],
    load_buses: list[int],
    source_buses: list[int],
) -> np.ndarray:
    n_scenarios, n_time, n_line = outages.shape
    result = np.zeros((n_scenarios, n_time), dtype=int)

    for s in range(n_scenarios):
        for t in range(n_time):
            graph = nx.Graph()
            graph.add_nodes_from(all_buses)
            for lid in range(n_line):
                if outages[s, t, lid] == 0:
                    u, v = line_edges[lid]
                    graph.add_edge(u, v)

            reachable: set[int] = set()
            for src in source_buses:
                if src in graph:
                    reachable.update(nx.node_connected_component(graph, src))
            result[s, t] = sum(1 for bus in load_buses if bus not in reachable)
    return result


def pairwise_hamming_diversity(outages: np.ndarray, max_samples: int = 120) -> float:
    n_scenarios = outages.shape[0]
    if n_scenarios <= 1:
        return 0.0
    use_n = min(n_scenarios, max_samples)
    sample = outages[:use_n].reshape(use_n, -1)
    total = 0.0
    count = 0
    for i in range(use_n):
        xor = np.not_equal(sample[i + 1 :], sample[i])
        if xor.size == 0:
            continue
        dist = xor.mean(axis=1)
        total += float(dist.sum())
        count += len(dist)
    return float(total / max(count, 1))


def evaluate_method(
    method: str,
    outages: np.ndarray,
    p_line: np.ndarray,
    high_risk_quantile: float,
    disconnected_loads: np.ndarray,
) -> dict[str, Any]:
    empirical = outages.mean(axis=0)
    mae_prob = float(np.abs(empirical - p_line).mean())

    high_threshold = float(np.quantile(p_line, high_risk_quantile))
    high_mask = p_line >= high_threshold
    low_mask = ~high_mask

    hit_any = outages.max(axis=0)
    high_risk_coverage = float(hit_any[high_mask].mean()) if high_mask.any() else 0.0

    high_event_rate = float(outages[:, high_mask].mean()) if high_mask.any() else 0.0
    low_event_rate = float(outages[:, low_mask].mean()) if low_mask.any() else 0.0

    line_outage_count = outages.sum(axis=2)
    multi_line_rate = float((line_outage_count >= 2).mean())
    severe_multi_line_rate = float((line_outage_count >= 4).mean())

    multi_load_rate = float((disconnected_loads >= 2).mean())
    severe_load_rate = float((disconnected_loads >= 4).mean())

    return {
        "method": method,
        "mae_empirical_vs_input_probability": mae_prob,
        "high_risk_threshold": high_threshold,
        "high_risk_coverage": high_risk_coverage,
        "high_risk_event_rate": high_event_rate,
        "low_risk_event_rate": low_event_rate,
        "risk_lift_ratio": float(high_event_rate / max(low_event_rate, 1e-8)),
        "avg_outage_rate": float(outages.mean()),
        "multi_line_event_rate_ge2": multi_line_rate,
        "severe_multi_line_event_rate_ge4": severe_multi_line_rate,
        "avg_disconnected_loads": float(disconnected_loads.mean()),
        "max_disconnected_loads": int(disconnected_loads.max(initial=0)),
        "multi_load_event_rate_ge2": multi_load_rate,
        "severe_multi_load_event_rate_ge4": severe_load_rate,
        "scenario_diversity_hamming": pairwise_hamming_diversity(outages),
    }


def save_method_outputs(
    output_dir: Path,
    method: str,
    timestamps: pd.DatetimeIndex,
    line_ids: list[str],
    p_line: np.ndarray,
    outages: np.ndarray,
    disconnected_loads: np.ndarray,
    write_default_name: bool = False,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    np.save(output_dir / f"contingency_tensor_{method}.npy", outages)

    empirical = outages.mean(axis=0)
    line_summary = pd.DataFrame(
        {
            "line_id": line_ids,
            "input_p_mean": p_line.mean(axis=0),
            "empirical_p_mean": empirical.mean(axis=0),
            "absolute_error_mean": np.abs(empirical.mean(axis=0) - p_line.mean(axis=0)),
        }
    ).sort_values("input_p_mean", ascending=False)
    line_summary.to_csv(output_dir / f"line_probability_summary_{method}.csv", index=False, encoding="utf-8")

    n_scenarios, n_time, _ = outages.shape
    rows: list[dict[str, Any]] = []
    ts_plain = timestamps.tz_localize(None) if timestamps.tz is not None else timestamps
    line_outage_counts = outages.sum(axis=2)
    for s in range(n_scenarios):
        for t in range(n_time):
            rows.append(
                {
                    "scenario_id": s,
                    "timestamp": str(ts_plain[t]),
                    "outage_line_count": int(line_outage_counts[s, t]),
                    "disconnected_load_count": int(disconnected_loads[s, t]),
                }
            )
    pd.DataFrame.from_records(rows).to_csv(
        output_dir / f"state_summary_{method}.csv", index=False, encoding="utf-8"
    )

    # Flatten tensor into scenario rows for downstream scheduling/assessment input.
    scenario_prob = 1.0 / max(n_scenarios, 1)
    scenario_rows: list[dict[str, Any]] = []
    for s in range(n_scenarios):
        sid = f"S{s + 1}"
        for t in range(n_time):
            failed_idx = np.flatnonzero(outages[s, t, :])
            failed_lines = [line_ids[i] for i in failed_idx]
            scenario_rows.append(
                {
                    "scenario": sid,
                    "scenario_id": s,
                    "timestamp": str(ts_plain[t]),
                    "failed_lines": "|".join(failed_lines),
                    "outage_line_count": int(len(failed_lines)),
                    "disconnected_load_count": int(disconnected_loads[s, t]),
                    "probability": float(scenario_prob),
                    "method": method,
                }
            )
    scenario_df = pd.DataFrame.from_records(scenario_rows)
    scenario_path = output_dir / f"contingency_scenarios_{method}.csv"
    scenario_df.to_csv(scenario_path, index=False, encoding="utf-8")
    if write_default_name:
        scenario_df.to_csv(output_dir / "contingency_scenarios.csv", index=False, encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate spatio-temporal contingency sets (MC/QMC + C3PO/TRIM-inspired references)."
    )
    parser.add_argument(
        "--failure-csv",
        default="results/component_failure_probability/formal2024/line_failure_timeseries_schloemer.csv",
        help="Line failure probability timeseries csv.",
    )
    parser.add_argument(
        "--grid",
        default="data_final/formal_guangdong_2024/grid_topology.json",
        help="Grid topology json path.",
    )
    parser.add_argument(
        "--output-dir",
        default="results/spatiotemporal_contingency/formal2024",
        help="Output directory.",
    )
    parser.add_argument(
        "--methods",
        choices=("all", "wang_qmc", "wang_mc", "c3po_ref", "trim_ref"),
        default="all",
        help="Generation method set.",
    )
    parser.add_argument("--n-scenarios", type=int, default=256, help="Number of generated scenarios.")
    parser.add_argument("--seed", type=int, default=42, help="Random seed.")
    parser.add_argument(
        "--warning-end-hour",
        type=int,
        default=-1,
        help="Warning end hour index for Wang stateful method. -1 means 75%% of horizon.",
    )
    parser.add_argument("--repair-hours", type=int, default=12, help="Repair window for Wang stateful method.")
    parser.add_argument(
        "--high-risk-quantile",
        type=float,
        default=0.90,
        help="Quantile threshold for high-risk coverage evaluation.",
    )
    parser.add_argument("--max-steps", type=int, default=None, help="Use only first N steps for debugging.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    root = project_root()
    failure_csv = (root / args.failure_csv).resolve()
    grid_path = (root / args.grid).resolve()
    output_dir = (root / args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    data = load_failure_input(path=failure_csv, max_steps=args.max_steps)
    all_buses, load_buses, source_buses = load_grid_roles(grid_path=grid_path)

    n_time, n_line = data.p_line.shape
    warning_end_t = args.warning_end_hour if args.warning_end_hour >= 0 else int(np.floor(0.75 * n_time))
    warning_end_t = int(np.clip(warning_end_t, 0, n_time - 1))
    methods = (
        ["wang_qmc", "wang_mc", "c3po_ref", "trim_ref"]
        if args.methods == "all"
        else [args.methods]
    )

    print(f"timestamps={n_time}, lines={n_line}, scenarios={args.n_scenarios}")
    print(f"methods={methods}")

    rng = np.random.default_rng(args.seed)
    results: dict[str, dict[str, Any]] = {}
    comparison_rows: list[dict[str, Any]] = []

    for method in methods:
        print(f"\nrunning method={method}")
        if method == "wang_qmc":
            uniforms = sobol_uniforms(args.n_scenarios, n_time, n_line, seed=args.seed)
            outages = wang_stateful_contingency(
                p_line=data.p_line,
                uniforms=uniforms,
                warning_end_t=warning_end_t,
                repair_hours=args.repair_hours,
            )
        elif method == "wang_mc":
            uniforms = rng.random((args.n_scenarios, n_time, n_line))
            outages = wang_stateful_contingency(
                p_line=data.p_line,
                uniforms=uniforms,
                warning_end_t=warning_end_t,
                repair_hours=args.repair_hours,
            )
        elif method == "c3po_ref":
            uniforms = rng.random((args.n_scenarios, n_time, n_line))
            outages = c3po_reference_contingency(p_line=data.p_line, uniforms=uniforms)
        elif method == "trim_ref":
            outages = trim_reference_contingency(
                p_line=data.p_line,
                n_scenarios=args.n_scenarios,
                seed=args.seed + 1000,
            )
        else:
            raise ValueError(f"unsupported method={method}")

        disconnected = disconnected_load_matrix(
            outages=outages,
            line_edges=data.line_edges,
            all_buses=all_buses,
            load_buses=load_buses,
            source_buses=source_buses,
        )

        metrics = evaluate_method(
            method=method,
            outages=outages,
            p_line=data.p_line,
            high_risk_quantile=args.high_risk_quantile,
            disconnected_loads=disconnected,
        )
        save_method_outputs(
            output_dir=output_dir,
            method=method,
            timestamps=data.timestamps,
            line_ids=data.line_ids,
            p_line=data.p_line,
            outages=outages,
            disconnected_loads=disconnected,
            write_default_name=(len(methods) == 1),
        )

        results[method] = metrics
        comparison_rows.append(metrics)
        print(
            f"  high_risk_coverage={metrics['high_risk_coverage']:.4f}, "
            f"multi_line>=2={metrics['multi_line_event_rate_ge2']:.4f}, "
            f"multi_load>=2={metrics['multi_load_event_rate_ge2']:.4f}"
        )

    comparison_df = pd.DataFrame(comparison_rows).sort_values(
        by=["high_risk_coverage", "multi_line_event_rate_ge2", "multi_load_event_rate_ge2"],
        ascending=False,
    )
    comparison_csv = output_dir / "method_comparison.csv"
    comparison_df.to_csv(comparison_csv, index=False, encoding="utf-8")

    output_files_by_method = {
        m: {
            "contingency_tensor_npy": str(output_dir / f"contingency_tensor_{m}.npy"),
            "state_summary_csv": str(output_dir / f"state_summary_{m}.csv"),
            "line_probability_summary_csv": str(output_dir / f"line_probability_summary_{m}.csv"),
            "contingency_scenarios_csv": str(output_dir / f"contingency_scenarios_{m}.csv"),
        }
        for m in methods
    }

    report = {
        "input": {
            "failure_csv": str(failure_csv),
            "grid_path": str(grid_path),
            "n_time": int(n_time),
            "n_line": int(n_line),
            "line_ids": data.line_ids,
            "n_scenarios": int(args.n_scenarios),
        },
        "sampling_config": {
            "methods": methods,
            "seed": int(args.seed),
            "warning_end_t": int(warning_end_t),
            "repair_hours": int(args.repair_hours),
            "high_risk_quantile": float(args.high_risk_quantile),
        },
        "grid_roles": {
            "source_buses": source_buses,
            "load_buses_count": len(load_buses),
            "all_buses_count": len(all_buses),
        },
        "metrics_by_method": results,
        "output_files_by_method": output_files_by_method,
        "contingency_scenarios_csv": str(output_dir / "contingency_scenarios.csv") if len(methods) == 1 else None,
        "comparison_csv": str(comparison_csv),
    }
    report_path = output_dir / "contingency_report.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nreport -> {report_path}")
    print(f"comparison -> {comparison_csv}")


if __name__ == "__main__":
    main()
