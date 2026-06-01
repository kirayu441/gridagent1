from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import networkx as nx
import numpy as np
import pandas as pd
from scipy.optimize import linprog


@dataclass(frozen=True)
class DispatchableGenerator:
    gen_id: str
    bus: int
    pmax: float
    gen_cost: float
    reserve_cost: float


@dataclass
class ScenarioInputs:
    timestamps: pd.DatetimeIndex
    line_ids: list[str]
    edges: list[tuple[int, int]]
    outages: np.ndarray  # [S,T,L], 1 outage / 0 healthy


def project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def parse_optional_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        x = float(value)
    except (TypeError, ValueError):
        return None
    if np.isnan(x):
        return None
    return float(x)


def parse_capacity_list(raw: str) -> list[float]:
    values: list[float] = []
    for part in raw.split(","):
        part = part.strip()
        if not part:
            continue
        values.append(float(part))
    return values


def load_grid(grid_path: Path) -> dict[str, Any]:
    if not grid_path.exists():
        raise FileNotFoundError(f"missing grid file: {grid_path}")
    payload = json.loads(grid_path.read_text(encoding="utf-8"))
    if not payload.get("nodes") or not payload.get("lines"):
        raise ValueError(f"invalid grid topology: {grid_path}")
    return payload


def load_contingencies(contingency_path: Path, failure_csv: Path) -> ScenarioInputs:
    if not contingency_path.exists():
        raise FileNotFoundError(f"missing contingency tensor: {contingency_path}")
    if not failure_csv.exists():
        raise FileNotFoundError(f"missing failure csv: {failure_csv}")

    outages = np.load(contingency_path)
    if outages.ndim != 3:
        raise ValueError(f"contingency tensor must be 3D, got {outages.shape}")

    fail = pd.read_csv(failure_csv)
    required = {"timestamp", "line_id", "from_bus", "to_bus"}
    missing = required - set(fail.columns)
    if missing:
        raise ValueError(f"failure csv missing columns: {sorted(missing)}")

    fail["timestamp"] = pd.to_datetime(fail["timestamp"], errors="coerce")
    if fail["timestamp"].isna().any():
        raise ValueError("invalid timestamp in failure csv")

    pivot = fail.pivot_table(index="timestamp", columns="line_id", values="p_line", aggfunc="mean").sort_index().sort_index(axis=1)
    line_ids = [str(x) for x in pivot.columns]
    timestamps = pd.DatetimeIndex(pivot.index)
    if outages.shape[1] != len(timestamps) or outages.shape[2] != len(line_ids):
        raise ValueError(
            f"dimension mismatch: tensor={outages.shape}, timestamps={len(timestamps)}, lines={len(line_ids)}"
        )

    edge_map = (
        fail.drop_duplicates(subset=["line_id"])
        .set_index("line_id")[["from_bus", "to_bus"]]
        .to_dict(orient="index")
    )
    edges: list[tuple[int, int]] = []
    for lid in line_ids:
        item = edge_map.get(lid)
        if item is None:
            raise ValueError(f"line edge missing: {lid}")
        edges.append((int(item["from_bus"]), int(item["to_bus"])))

    return ScenarioInputs(
        timestamps=timestamps,
        line_ids=line_ids,
        edges=edges,
        outages=outages.astype(np.int8),
    )


def derive_load_priorities(load_buses: list[int]) -> tuple[dict[int, int], dict[int, float]]:
    n = len(load_buses)
    k1 = max(1, int(np.ceil(0.30 * n)))
    k2 = max(1, int(np.ceil(0.30 * n)))
    sorted_buses = sorted(load_buses)
    p1 = set(sorted_buses[:k1])
    p2 = set(sorted_buses[k1 : k1 + k2])

    level_map: dict[int, int] = {}
    weight_map: dict[int, float] = {}
    for b in sorted_buses:
        if b in p1:
            level = 1
            weight = 1.0
        elif b in p2:
            level = 2
            weight = 0.5
        else:
            level = 3
            weight = 0.2
        level_map[b] = level
        weight_map[b] = weight
    return level_map, weight_map


def build_load_demands(
    trim_path: Path,
    timestamps: pd.DatetimeIndex,
    load_buses: list[int],
    level_map: dict[int, int],
    seed: int,
    priority_stress_factor: float = 1.0,
) -> tuple[np.ndarray, dict[int, float]]:
    if not trim_path.exists():
        raise FileNotFoundError(f"missing trim file: {trim_path}")
    trim = pd.read_csv(trim_path)
    if "timestamp" not in trim.columns:
        raise ValueError(f"trim file missing timestamp: {trim_path}")
    trim["timestamp"] = pd.to_datetime(trim["timestamp"], errors="coerce")
    trim = trim.dropna(subset=["timestamp"]).set_index("timestamp").sort_index()

    load_cols = [c for c in trim.columns if c.startswith("load_")]
    if not load_cols:
        raise ValueError("trim input has no load_ columns")
    total = trim[load_cols].sum(axis=1)
    aligned = total.reindex(timestamps).interpolate(method="time").ffill().bfill()
    demand_total = aligned.to_numpy(dtype=float)

    rng = np.random.default_rng(seed)
    stress = max(float(priority_stress_factor), 0.1)
    alpha = np.array(
        [2.4 * stress if level_map[b] == 1 else 1.6 if level_map[b] == 2 else 1.0 for b in load_buses],
        dtype=float,
    )
    shares = rng.dirichlet(alpha)
    share_map = {bus: float(sh) for bus, sh in zip(load_buses, shares)}
    load_matrix = demand_total[:, None] * shares[None, :]
    return load_matrix, share_map


def build_renewable_profiles(
    uncertainty_dir: Path,
    grid: dict[str, Any],
    timestamps: pd.DatetimeIndex,
    n_scenarios: int,
    seed: int,
) -> tuple[np.ndarray, dict[str, Any]]:
    typical_path = uncertainty_dir / "typical_scenarios.npy"
    prob_path = uncertainty_dir / "scenario_probabilities.csv"
    history_path = uncertainty_dir / "history_series.csv"
    if not typical_path.exists() or not prob_path.exists() or not history_path.exists():
        raise FileNotFoundError(f"missing uncertainty outputs in {uncertainty_dir}")

    typical = np.load(typical_path)  # [K,T,2], [:,:,0]=wind, [:,:,1]=pv
    probs = pd.read_csv(prob_path)["probability"].to_numpy(dtype=float)
    probs = probs / probs.sum()
    history = pd.read_csv(history_path)
    history["timestamp"] = pd.to_datetime(history["timestamp"], errors="coerce")
    history = history.dropna(subset=["timestamp"]).set_index("timestamp").sort_index()

    ref_ts = pd.DatetimeIndex(history.index)
    pos = ref_ts.get_indexer(timestamps, method="nearest")
    if np.any(pos < 0):
        raise ValueError("cannot align contingency timestamps to uncertainty timeline")
    typical_window = typical[:, pos, :]

    rng = np.random.default_rng(seed)
    sampled_k = rng.choice(np.arange(typical_window.shape[0]), size=n_scenarios, replace=True, p=probs)
    selected = typical_window[sampled_k, :, :]  # [S,T,2]

    generators = grid.get("generators", [])
    wind_buses = [int(g["bus"]) for g in generators if str(g.get("type", "")).lower() == "wind"]
    pv_items = [(int(g["bus"]), parse_optional_float(g.get("capacity")) or 0.0) for g in generators if str(g.get("type", "")).lower() == "pv"]
    pv_buses = [b for b, _ in pv_items]
    pv_caps = np.array([c for _, c in pv_items], dtype=float)
    if len(wind_buses) == 0:
        wind_buses = [0]
    if len(pv_buses) == 0:
        pv_buses = [0]
        pv_caps = np.array([1.0], dtype=float)
    if pv_caps.sum() <= 0:
        pv_caps = np.ones_like(pv_caps)
    pv_share = pv_caps / pv_caps.sum()

    all_buses = sorted({int(n["id"]) for n in grid.get("nodes", [])})
    bus_to_idx = {b: i for i, b in enumerate(all_buses)}
    ren_bus = np.zeros((n_scenarios, len(timestamps), len(all_buses)), dtype=float)
    for s in range(n_scenarios):
        for t in range(len(timestamps)):
            wind_total = max(float(selected[s, t, 0]), 0.0)
            pv_total = max(float(selected[s, t, 1]), 0.0)
            for b in wind_buses:
                if b in bus_to_idx:
                    ren_bus[s, t, bus_to_idx[b]] += wind_total / len(wind_buses)
            for (b, _), sh in zip(pv_items if pv_items else [(0, 1.0)], pv_share):
                if b in bus_to_idx:
                    ren_bus[s, t, bus_to_idx[b]] += pv_total * float(sh)
    meta = {
        "typical_scenario_count": int(typical.shape[0]),
        "sampled_ids_preview": sampled_k[: min(10, len(sampled_k))].tolist(),
        "wind_buses": wind_buses,
        "pv_buses": pv_buses,
    }
    return ren_bus, meta


def build_dispatchable_generators(
    grid: dict[str, Any],
    load_buses: list[int],
    level_map: dict[int, int],
    slack_dispatchable_capacity: float,
    emergency_dg_caps: list[float],
) -> list[DispatchableGenerator]:
    gens = grid.get("generators", [])
    dispatchable: list[DispatchableGenerator] = []

    for g in gens:
        gtype = str(g.get("type", "")).lower()
        if gtype in {"thermal", "slack", "ext_grid"}:
            bus = int(g.get("bus", 0))
            cap = max(parse_optional_float(g.get("capacity")) or 0.0, 0.0)
            cap = max(cap, slack_dispatchable_capacity if bus == 0 else 0.0)
            if cap > 0:
                dispatchable.append(
                    DispatchableGenerator(
                        gen_id=str(g.get("id", f"TH_{bus}")),
                        bus=bus,
                        pmax=float(cap),
                        gen_cost=110.0,
                        reserve_cost=35.0,
                    )
                )

    chosen = [b for b in sorted(load_buses) if level_map[b] == 1] + [b for b in sorted(load_buses) if level_map[b] == 2]
    if not chosen:
        chosen = sorted(load_buses)
    for i, cap in enumerate(emergency_dg_caps):
        if cap <= 0:
            continue
        bus = chosen[i % len(chosen)]
        dispatchable.append(
            DispatchableGenerator(
                gen_id=f"EMG_DG_{i+1}",
                bus=bus,
                pmax=float(cap),
                gen_cost=140.0,
                reserve_cost=45.0,
            )
        )
    if not dispatchable:
        raise ValueError("no dispatchable generators available after initialization")
    return dispatchable


def pre_disaster_schedule(
    generators: list[DispatchableGenerator],
    demand_total: np.ndarray,
    renewable_expected: np.ndarray,
    reserve_ratio: float,
) -> tuple[np.ndarray, np.ndarray, dict[str, Any]]:
    # Variables: p[g,t], r[g,t], u[t], rs[t]
    n_t = len(demand_total)
    n_g = len(generators)
    n_var = 2 * n_t * n_g + 2 * n_t

    def idx_p(t: int, g: int) -> int:
        return t * n_g + g

    p_offset = 0
    r_offset = n_t * n_g
    u_offset = 2 * n_t * n_g
    rs_offset = 2 * n_t * n_g + n_t

    c = np.zeros(n_var, dtype=float)
    for t in range(n_t):
        for g, gen in enumerate(generators):
            c[p_offset + idx_p(t, g)] = gen.gen_cost
            c[r_offset + idx_p(t, g)] = gen.reserve_cost
        c[u_offset + t] = 3_000.0
        c[rs_offset + t] = 700.0

    A_ub: list[np.ndarray] = []
    b_ub: list[float] = []
    A_eq: list[np.ndarray] = []
    b_eq: list[float] = []

    # p + r <= pmax
    for t in range(n_t):
        for g, gen in enumerate(generators):
            row = np.zeros(n_var, dtype=float)
            row[p_offset + idx_p(t, g)] = 1.0
            row[r_offset + idx_p(t, g)] = 1.0
            A_ub.append(row)
            b_ub.append(gen.pmax)

    # Demand coverage: sum(p) + u >= demand - renewable
    for t in range(n_t):
        row = np.zeros(n_var, dtype=float)
        for g in range(n_g):
            row[p_offset + idx_p(t, g)] = -1.0
        row[u_offset + t] = -1.0
        A_ub.append(row)
        b_ub.append(-(demand_total[t] - renewable_expected[t]))

    # Reserve: sum(r) + rs >= reserve_ratio * demand
    for t in range(n_t):
        row = np.zeros(n_var, dtype=float)
        for g in range(n_g):
            row[r_offset + idx_p(t, g)] = -1.0
        row[rs_offset + t] = -1.0
        A_ub.append(row)
        b_ub.append(-(reserve_ratio * demand_total[t]))

    bounds: list[tuple[float, float | None]] = [(0.0, None)] * n_var
    result = linprog(
        c=c,
        A_ub=np.array(A_ub, dtype=float),
        b_ub=np.array(b_ub, dtype=float),
        A_eq=np.array(A_eq, dtype=float) if A_eq else None,
        b_eq=np.array(b_eq, dtype=float) if b_eq else None,
        bounds=bounds,
        method="highs",
    )
    if not result.success:
        raise RuntimeError(f"pre-disaster scheduling LP failed: {result.message}")

    x = result.x
    p = np.zeros((n_t, n_g), dtype=float)
    r = np.zeros((n_t, n_g), dtype=float)
    u = np.zeros(n_t, dtype=float)
    rs = np.zeros(n_t, dtype=float)
    for t in range(n_t):
        for g in range(n_g):
            p[t, g] = x[p_offset + idx_p(t, g)]
            r[t, g] = x[r_offset + idx_p(t, g)]
        u[t] = x[u_offset + t]
        rs[t] = x[rs_offset + t]

    summary = {
        "objective_value": float(result.fun),
        "avg_base_dispatch": float(p.mean()),
        "avg_reserve": float(r.mean()),
        "avg_unserved_planning_shortfall": float(u.mean()),
        "avg_reserve_shortfall": float(rs.mean()),
    }
    return p, r, summary


def optimal_weighted_shedding(
    demand: np.ndarray,
    weights: np.ndarray,
    available_supply: float,
) -> tuple[np.ndarray, np.ndarray]:
    # Continuous LP optimum = greedy supply allocation by descending weight.
    n = len(demand)
    served = np.zeros(n, dtype=float)
    order = np.argsort(-weights)
    rem = max(float(available_supply), 0.0)
    for idx in order:
        if rem <= 1e-12:
            break
        alloc = min(float(demand[idx]), rem)
        served[idx] = alloc
        rem -= alloc
    shed = demand - served
    return served, shed


def simulate_policy(
    policy_name: str,
    weights: np.ndarray,
    allow_reserve: bool,
    scenario_inputs: ScenarioInputs,
    all_buses: list[int],
    load_buses: list[int],
    source_buses: list[int],
    load_demand: np.ndarray,  # [T, Nload]
    renewable_bus: np.ndarray,  # [S,T,Nbus]
    generators: list[DispatchableGenerator],
    base_dispatch: np.ndarray,  # [T,G]
    reserve_dispatch: np.ndarray,  # [T,G]
    c_load: float,
) -> tuple[dict[str, Any], pd.DataFrame, pd.DataFrame]:
    n_s, n_t, n_l = scenario_inputs.outages.shape
    n_bus = len(all_buses)
    bus_to_idx = {b: i for i, b in enumerate(all_buses)}
    load_bus_to_pos = {b: i for i, b in enumerate(load_buses)}

    gen_bus_idx = np.array([bus_to_idx[g.bus] for g in generators], dtype=int)
    gen_cap_t = base_dispatch + (reserve_dispatch if allow_reserve else 0.0)

    shed_tensor = np.zeros((n_s, n_t, len(load_buses)), dtype=float)
    served_tensor = np.zeros_like(shed_tensor)
    outage_count = scenario_inputs.outages.sum(axis=2)

    scenario_rows: list[dict[str, Any]] = []
    best_state_rows: list[dict[str, Any]] = []

    for s in range(n_s):
        if (s + 1) % 32 == 0 or (s + 1) == n_s:
            print(f"  [{policy_name}] scenario {s + 1}/{n_s}")
        scenario_shed = 0.0
        scenario_cost = 0.0
        scenario_demand = float(load_demand.sum())
        for t in range(n_t):
            graph = nx.Graph()
            graph.add_nodes_from(all_buses)
            for lid in range(n_l):
                if scenario_inputs.outages[s, t, lid] == 0:
                    u, v = scenario_inputs.edges[lid]
                    graph.add_edge(u, v)

            components = list(nx.connected_components(graph))
            for comp in components:
                comp_list = sorted(comp)
                comp_load_buses = [b for b in load_buses if b in comp]
                if not comp_load_buses:
                    continue
                comp_positions = [load_bus_to_pos[b] for b in comp_load_buses]
                demand_vec = load_demand[t, comp_positions]
                weight_vec = weights[comp_positions]

                ren_supply = float(renewable_bus[s, t, [bus_to_idx[b] for b in comp_list]].sum())
                gen_mask = np.isin(gen_bus_idx, [bus_to_idx[b] for b in comp_list])
                gen_supply = float(gen_cap_t[t, gen_mask].sum()) if np.any(gen_mask) else 0.0
                avail = ren_supply + gen_supply

                served, shed = optimal_weighted_shedding(demand=demand_vec, weights=weight_vec, available_supply=avail)
                served_tensor[s, t, comp_positions] = served
                shed_tensor[s, t, comp_positions] = shed

        scenario_shed = float(shed_tensor[s].sum())
        scenario_cost = float((shed_tensor[s] * weights[None, :]).sum() * c_load)
        crit_mask = weights >= 0.999
        crit_shed = float(shed_tensor[s][:, crit_mask].sum()) if np.any(crit_mask) else 0.0
        scenario_rows.append(
            {
                "scenario_id": s,
                "total_shed": scenario_shed,
                "weighted_shed_cost": scenario_cost,
                "critical_shed": crit_shed,
                "total_demand": scenario_demand,
                "outage_lines_avg": float(outage_count[s].mean()),
                "outage_lines_max": int(outage_count[s].max(initial=0)),
            }
        )

    scenario_df = pd.DataFrame(scenario_rows)
    worst_id = int(scenario_df.sort_values("weighted_shed_cost", ascending=False).iloc[0]["scenario_id"])

    ts_plain = scenario_inputs.timestamps.tz_localize(None) if scenario_inputs.timestamps.tz is not None else scenario_inputs.timestamps
    for t in range(n_t):
        for i, bus in enumerate(load_buses):
            best_state_rows.append(
                {
                    "scenario_id": worst_id,
                    "timestamp": str(ts_plain[t]),
                    "load_bus": int(bus),
                    "priority_weight": float(weights[i]),
                    "demand": float(load_demand[t, i]),
                    "served": float(served_tensor[worst_id, t, i]),
                    "shed": float(shed_tensor[worst_id, t, i]),
                }
            )
    worst_detail_df = pd.DataFrame(best_state_rows)

    total_demand_all = float(load_demand.sum() * n_s)
    total_served_all = float(served_tensor.sum())
    total_shed_all = float(shed_tensor.sum())

    # Rr
    rr = float(total_served_all / max(total_demand_all, 1e-12))

    # RA (weighted served ratio by node, averaged by weights)
    node_ratio: list[float] = []
    node_w: list[float] = []
    for i in range(len(load_buses)):
        d_i = float(load_demand[:, i].sum() * n_s)
        s_i = float(served_tensor[:, :, i].sum())
        ratio = s_i / max(d_i, 1e-12)
        node_ratio.append(ratio)
        node_w.append(float(weights[i]))
    node_ratio_arr = np.array(node_ratio, dtype=float)
    node_w_arr = np.array(node_w, dtype=float)
    ra = float((node_ratio_arr * node_w_arr).sum() / max(node_w_arr.sum(), 1e-12))

    crit_mask = weights >= 0.999
    sec_mask = (weights >= 0.499) & (weights < 0.999)
    thr_mask = weights < 0.499

    summary = {
        "policy": policy_name,
        "allow_reserve": bool(allow_reserve),
        "rr": rr,
        "ra": ra,
        "expected_total_shed": float(total_shed_all / n_s),
        "expected_weighted_shed_cost": float((scenario_df["weighted_shed_cost"].mean())),
        "expected_critical_shed": float(scenario_df["critical_shed"].mean()),
        "critical_served_ratio": float(
            served_tensor[:, :, crit_mask].sum() / max(load_demand[:, crit_mask].sum() * n_s, 1e-12)
        )
        if np.any(crit_mask)
        else None,
        "secondary_served_ratio": float(
            served_tensor[:, :, sec_mask].sum() / max(load_demand[:, sec_mask].sum() * n_s, 1e-12)
        )
        if np.any(sec_mask)
        else None,
        "tertiary_served_ratio": float(
            served_tensor[:, :, thr_mask].sum() / max(load_demand[:, thr_mask].sum() * n_s, 1e-12)
        )
        if np.any(thr_mask)
        else None,
        "worst_scenario_id": worst_id,
    }
    return summary, scenario_df, worst_detail_df


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Load prioritization & pre-disaster scheduling based on contingency scenarios."
    )
    parser.add_argument(
        "--grid",
        default="data_final/formal_guangdong_2024/grid_topology.json",
        help="Grid topology json path.",
    )
    parser.add_argument(
        "--trim-input",
        default="data_final/formal_guangdong_2024/TRIM_input.csv",
        help="TRIM input csv path.",
    )
    parser.add_argument(
        "--contingency-tensor",
        default="results/spatiotemporal_contingency/formal2024_schloemer72h/contingency_tensor_wang_qmc.npy",
        help="Contingency tensor npy path.",
    )
    parser.add_argument(
        "--failure-csv",
        default="results/component_failure_probability/formal2024/line_failure_timeseries_schloemer.csv",
        help="Failure probability csv used for line ordering and timestamps.",
    )
    parser.add_argument(
        "--uncertainty-dir",
        default="results/wind_pv_uncertainty/formal2024",
        help="Wind/PV uncertainty result directory.",
    )
    parser.add_argument(
        "--output-dir",
        default="results/load_prioritization_scheduling/formal2024",
        help="Output directory.",
    )
    parser.add_argument(
        "--reserve-ratio",
        type=float,
        default=0.15,
        help="Reserve requirement ratio of total demand in pre-disaster scheduling.",
    )
    parser.add_argument(
        "--load-shed-cost",
        type=float,
        default=50.0,
        help="Load shedding cost coefficient c_L.",
    )
    parser.add_argument(
        "--slack-dispatchable-capacity",
        type=float,
        default=1.20,
        help="Fallback dispatchable capacity injected at bus0 if existing thermal capacity is insufficient.",
    )
    parser.add_argument(
        "--emergency-dg-capacities",
        default="0.18,0.15,0.10",
        help="Comma-separated emergency DG capacities.",
    )
    parser.add_argument(
        "--priority-stress-factor",
        type=float,
        default=1.0,
        help="Scale factor on priority-level-1 demand share concentration (>1 means more critical-load stress).",
    )
    parser.add_argument(
        "--policy-set",
        choices=("all", "priority_only"),
        default="all",
        help="Run all policy baselines or only priority_with_reserve.",
    )
    parser.add_argument("--seed", type=int, default=42, help="Random seed.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    root = project_root()

    grid_path = (root / args.grid).resolve()
    trim_path = (root / args.trim_input).resolve()
    contingency_path = (root / args.contingency_tensor).resolve()
    failure_csv = (root / args.failure_csv).resolve()
    uncertainty_dir = (root / args.uncertainty_dir).resolve()
    output_dir = (root / args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    print("loading inputs ...")
    grid = load_grid(grid_path)
    scenario_inputs = load_contingencies(contingency_path=contingency_path, failure_csv=failure_csv)
    all_buses = sorted({int(n["id"]) for n in grid.get("nodes", [])})
    load_buses = sorted({int(n["id"]) for n in grid.get("nodes", []) if str(n.get("type", "")).lower() == "load"})
    source_buses = sorted({int(g["bus"]) for g in grid.get("generators", []) if "bus" in g})
    if not source_buses:
        source_buses = [all_buses[0]]

    level_map, weight_map = derive_load_priorities(load_buses)
    weight_vec = np.array([weight_map[b] for b in load_buses], dtype=float)
    uniform_weight_vec = np.ones_like(weight_vec)

    load_demand, load_share_map = build_load_demands(
        trim_path=trim_path,
        timestamps=scenario_inputs.timestamps,
        load_buses=load_buses,
        level_map=level_map,
        seed=args.seed,
        priority_stress_factor=args.priority_stress_factor,
    )

    renewable_bus, ren_meta = build_renewable_profiles(
        uncertainty_dir=uncertainty_dir,
        grid=grid,
        timestamps=scenario_inputs.timestamps,
        n_scenarios=scenario_inputs.outages.shape[0],
        seed=args.seed + 100,
    )

    dispatchable = build_dispatchable_generators(
        grid=grid,
        load_buses=load_buses,
        level_map=level_map,
        slack_dispatchable_capacity=args.slack_dispatchable_capacity,
        emergency_dg_caps=parse_capacity_list(args.emergency_dg_capacities),
    )

    demand_total = load_demand.sum(axis=1)
    renewable_expected = renewable_bus.mean(axis=0).sum(axis=1)
    print("solving pre-disaster scheduling LP ...")
    base_p, reserve_p, schedule_summary = pre_disaster_schedule(
        generators=dispatchable,
        demand_total=demand_total,
        renewable_expected=renewable_expected,
        reserve_ratio=max(args.reserve_ratio, 0.0),
    )

    print("running post-disaster optimal shedding policies ...")
    summaries: list[dict[str, Any]] = []
    all_scenario_frames: list[pd.DataFrame] = []
    all_worst_frames: list[pd.DataFrame] = []

    if args.policy_set == "priority_only":
        policies = [
            ("priority_with_reserve", weight_vec, True),
        ]
    else:
        policies = [
            ("priority_with_reserve", weight_vec, True),
            ("uniform_with_reserve", uniform_weight_vec, True),
            ("priority_no_reserve", weight_vec, False),
        ]
    for name, w_vec, allow_reserve in policies:
        summary, scenario_df, worst_df = simulate_policy(
            policy_name=name,
            weights=w_vec,
            allow_reserve=allow_reserve,
            scenario_inputs=scenario_inputs,
            all_buses=all_buses,
            load_buses=load_buses,
            source_buses=source_buses,
            load_demand=load_demand,
            renewable_bus=renewable_bus,
            generators=dispatchable,
            base_dispatch=base_p,
            reserve_dispatch=reserve_p,
            c_load=args.load_shed_cost,
        )
        summaries.append(summary)
        scenario_df["policy"] = name
        worst_df["policy"] = name
        all_scenario_frames.append(scenario_df)
        all_worst_frames.append(worst_df)

    comparison_df = pd.DataFrame(summaries).sort_values(by=["ra", "rr"], ascending=False)
    scenario_summary_df = pd.concat(all_scenario_frames, ignore_index=True)
    worst_detail_df = pd.concat(all_worst_frames, ignore_index=True)

    dispatch_records: list[dict[str, Any]] = []
    for t, ts in enumerate(scenario_inputs.timestamps):
        for g, gen in enumerate(dispatchable):
            dispatch_records.append(
                {
                    "timestamp": str(ts),
                    "gen_id": gen.gen_id,
                    "bus": gen.bus,
                    "pmax": gen.pmax,
                    "base_dispatch": float(base_p[t, g]),
                    "reserve": float(reserve_p[t, g]),
                    "base_plus_reserve": float(base_p[t, g] + reserve_p[t, g]),
                }
            )
    dispatch_df = pd.DataFrame(dispatch_records)

    load_profile_records = []
    for i, bus in enumerate(load_buses):
        load_profile_records.append(
            {
                "load_bus": bus,
                "priority_level": level_map[bus],
                "priority_weight": weight_map[bus],
                "demand_share": load_share_map[bus],
            }
        )
    load_profile_df = pd.DataFrame(load_profile_records).sort_values(by=["priority_level", "load_bus"])

    comparison_path = output_dir / "policy_comparison.csv"
    scenario_path = output_dir / "scenario_metrics.csv"
    worst_path = output_dir / "worst_scenario_shedding_detail.csv"
    dispatch_path = output_dir / "pre_disaster_dispatch_schedule.csv"
    load_profile_path = output_dir / "load_bus_priority_profile.csv"

    comparison_df.to_csv(comparison_path, index=False, encoding="utf-8")
    scenario_summary_df.to_csv(scenario_path, index=False, encoding="utf-8")
    worst_detail_df.to_csv(worst_path, index=False, encoding="utf-8")
    dispatch_df.to_csv(dispatch_path, index=False, encoding="utf-8")
    load_profile_df.to_csv(load_profile_path, index=False, encoding="utf-8")

    report = {
        "inputs": {
            "grid": str(grid_path),
            "trim_input": str(trim_path),
            "contingency_tensor": str(contingency_path),
            "failure_csv": str(failure_csv),
            "uncertainty_dir": str(uncertainty_dir),
            "timestamps": {
                "start": str(scenario_inputs.timestamps.min()),
                "end": str(scenario_inputs.timestamps.max()),
                "steps": int(len(scenario_inputs.timestamps)),
            },
            "scenario_count": int(scenario_inputs.outages.shape[0]),
            "line_count": int(scenario_inputs.outages.shape[2]),
        },
        "modeling": {
            "priority_weights": {"level_1": 1.0, "level_2": 0.5, "level_3": 0.2},
            "reserve_ratio": float(args.reserve_ratio),
            "priority_stress_factor": float(args.priority_stress_factor),
            "policy_set": str(args.policy_set),
            "load_shed_cost": float(args.load_shed_cost),
            "dispatchable_generators": [gen.__dict__ for gen in dispatchable],
            "renewable_mapping": ren_meta,
            "schedule_summary": schedule_summary,
        },
        "outputs": {
            "policy_comparison_csv": str(comparison_path),
            "scenario_metrics_csv": str(scenario_path),
            "worst_scenario_shedding_detail_csv": str(worst_path),
            "pre_disaster_dispatch_schedule_csv": str(dispatch_path),
            "load_bus_priority_profile_csv": str(load_profile_path),
        },
    }
    report_path = output_dir / "load_prioritization_report.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    print("\nDone.")
    print(f"comparison -> {comparison_path}")
    print(f"report -> {report_path}")


if __name__ == "__main__":
    main()
