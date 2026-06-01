from __future__ import annotations

import argparse
import json
import math
from collections import deque
from pathlib import Path
from typing import Any

import networkx as nx
import numpy as np
import pandas as pd

try:
    import pandapower as pp
    import pandapower.networks as ppn
except ImportError as exc:  # pragma: no cover
    raise ImportError(
        "build_ieee_subgrid.py requires pandapower. "
        "Install with `pip install pandapower` in the active environment."
    ) from exc


def project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Extract a connected N-bus subgrid from a larger IEEE/MATPOWER pandapower case."
    )
    parser.add_argument(
        "--case",
        default="case118",
        choices=[
            "case118",
            "case300",
            "case57",
            "case39",
            "case30",
            "case14",
            "case1354pegase",
            "case2869pegase",
        ],
        help="Pandapower network case function name.",
    )
    parser.add_argument("--target-nodes", type=int, default=60, help="Target node count in extracted subgrid.")
    parser.add_argument("--seed-bus", type=int, default=-1, help="Optional start bus id. -1 means auto.")
    parser.add_argument("--layout-seed", type=int, default=42, help="Seed for synthetic geo layout.")
    parser.add_argument("--anchor-lat", type=float, default=23.1291)
    parser.add_argument("--anchor-lon", type=float, default=113.2644)
    parser.add_argument("--unit-km-per-local", type=float, default=3.0)
    parser.add_argument("--output-grid", default="data_final/ieee118_n60/grid_topology.json")
    return parser.parse_args()


def get_case_network(case_name: str) -> Any:
    fn = getattr(ppn, case_name, None)
    if fn is None:
        raise ValueError(f"Unsupported case: {case_name}")
    return fn()


def map_sgen_type(raw_type: str) -> str:
    rt = str(raw_type).strip().lower()
    if "pv" in rt:
        return "pv"
    if "wind" in rt or rt in {"wp"}:
        return "wind"
    return "renewable"


def local_xy_to_latlon(
    x_local: float,
    y_local: float,
    anchor_lat: float,
    anchor_lon: float,
    unit_km_per_local: float,
) -> tuple[float, float]:
    east_km = x_local * unit_km_per_local
    north_km = y_local * unit_km_per_local
    lat = anchor_lat + north_km / 110.57
    lon = anchor_lon + east_km / (111.32 * np.cos(np.deg2rad(anchor_lat)))
    return float(lat), float(lon)


def parse_optional_float(value: Any) -> float | None:
    try:
        if value is None:
            return None
        x = float(value)
        if np.isnan(x):
            return None
        return float(x)
    except Exception:
        return None


def build_bus_graph(net: Any) -> tuple[nx.Graph, list[tuple[int, int, str, int]]]:
    g = nx.Graph()
    bus_ids = [int(i) for i in net.bus.index.tolist()]
    g.add_nodes_from(bus_ids)
    edges: list[tuple[int, int, str, int]] = []

    for idx, row in net.line.iterrows():
        u = int(row["from_bus"])
        v = int(row["to_bus"])
        g.add_edge(u, v, etype="line", element_idx=int(idx))
        edges.append((u, v, "line", int(idx)))

    for idx, row in net.trafo.iterrows():
        u = int(row["hv_bus"])
        v = int(row["lv_bus"])
        g.add_edge(u, v, etype="trafo", element_idx=int(idx))
        edges.append((u, v, "trafo", int(idx)))

    return g, edges


def get_source_buses(net: Any) -> set[int]:
    buses: set[int] = set()
    if len(net.ext_grid):
        buses.update(int(x) for x in net.ext_grid["bus"].tolist())
    if len(net.gen):
        buses.update(int(x) for x in net.gen["bus"].tolist())
    if len(net.sgen):
        buses.update(int(x) for x in net.sgen["bus"].tolist())
    return buses


def choose_seed_bus(g: nx.Graph, source_buses: set[int], user_seed: int) -> int:
    if user_seed >= 0 and user_seed in g:
        return int(user_seed)
    if source_buses:
        return max(source_buses, key=lambda b: (g.degree[b], -int(b)))
    return max(g.nodes(), key=lambda b: (g.degree[b], -int(b)))


def bfs_pick_connected_nodes(g: nx.Graph, seed: int, target_nodes: int) -> list[int]:
    if seed not in g:
        raise ValueError(f"seed bus {seed} not in graph")

    selected: list[int] = []
    seen: set[int] = {seed}
    q: deque[int] = deque([seed])
    while q and len(selected) < target_nodes:
        u = q.popleft()
        selected.append(int(u))
        nbs = sorted(g.neighbors(u), key=lambda x: (-g.degree[x], int(x)))
        for v in nbs:
            if v in seen:
                continue
            seen.add(v)
            q.append(v)
    return selected


def build_positions_for_buses(
    g_sub: nx.Graph,
    selected_buses: list[int],
    layout_seed: int,
    anchor_lat: float,
    anchor_lon: float,
    unit_km_per_local: float,
) -> dict[int, dict[str, float]]:
    pos = nx.spring_layout(g_sub, seed=int(layout_seed))
    out: dict[int, dict[str, float]] = {}
    for b in selected_buses:
        x = float(pos[b][0] * 10.0)
        y = float(pos[b][1] * 10.0)
        lat, lon = local_xy_to_latlon(
            x_local=x,
            y_local=y,
            anchor_lat=anchor_lat,
            anchor_lon=anchor_lon,
            unit_km_per_local=unit_km_per_local,
        )
        out[int(b)] = {
            "local_x": x,
            "local_y": y,
            "lat": lat,
            "lon": lon,
        }
    return out


def edge_capacity_mw_from_line(net: Any, line_idx: int) -> float:
    row = net.line.loc[line_idx]
    vn = parse_optional_float(net.bus.loc[int(row["from_bus"]), "vn_kv"]) or 110.0
    max_i = parse_optional_float(row.get("max_i_ka")) or 0.0
    cap = 1.732 * vn * max_i
    if cap <= 0:
        cap = 100.0
    return float(cap)


def edge_capacity_mw_from_trafo(net: Any, trafo_idx: int) -> float:
    row = net.trafo.loc[trafo_idx]
    sn = parse_optional_float(row.get("sn_mva")) or 0.0
    if sn <= 0:
        sn = 80.0
    return float(sn)


def edge_length_km_from_line(net: Any, line_idx: int) -> float:
    row = net.line.loc[line_idx]
    lk = parse_optional_float(row.get("length_km"))
    if lk is None or lk <= 0:
        lk = 1.0
    return float(lk)


def geo_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    mean_lat = math.radians((lat1 + lat2) / 2.0)
    dy = (lat2 - lat1) * 111.0
    dx = (lon2 - lon1) * 111.0 * math.cos(mean_lat)
    return float(max(math.hypot(dx, dy), 0.6))


def main() -> None:
    args = parse_args()
    root = project_root()
    output_path = (root / args.output_grid).resolve()

    net = get_case_network(args.case)
    g, edges = build_bus_graph(net)
    source_buses = get_source_buses(net)
    load_buses = set(int(x) for x in net.load["bus"].tolist()) if len(net.load) else set()
    target_nodes = int(max(5, args.target_nodes))

    seed_bus = choose_seed_bus(g=g, source_buses=source_buses, user_seed=int(args.seed_bus))
    selected = bfs_pick_connected_nodes(g=g, seed=seed_bus, target_nodes=target_nodes)
    if len(selected) < target_nodes:
        raise RuntimeError(
            f"could only extract {len(selected)} connected nodes from seed {seed_bus}; target={target_nodes}"
        )

    selected_set = set(selected)
    g_sub = g.subgraph(selected_set).copy()
    if not nx.is_connected(g_sub):
        raise RuntimeError("selected subgraph is not connected")

    pos_map = build_positions_for_buses(
        g_sub=g_sub,
        selected_buses=selected,
        layout_seed=int(args.layout_seed),
        anchor_lat=float(args.anchor_lat),
        anchor_lon=float(args.anchor_lon),
        unit_km_per_local=float(args.unit_km_per_local),
    )

    nodes: list[dict[str, Any]] = []
    for b in sorted(selected):
        bus_row = net.bus.loc[b]
        geo = pos_map[b]
        nodes.append(
            {
                "id": int(b),
                "type": "load" if int(b) in load_buses else "bus",
                "vn_kv": float(bus_row["vn_kv"]) if pd.notna(bus_row["vn_kv"]) else None,
                "local_x": float(geo["local_x"]),
                "local_y": float(geo["local_y"]),
                "lat": float(geo["lat"]),
                "lon": float(geo["lon"]),
            }
        )

    # Build line list from selected line + trafo assets.
    lines: list[dict[str, Any]] = []
    for u, v, etype, eidx in edges:
        if u not in selected_set or v not in selected_set:
            continue
        geo_u = pos_map[int(u)]
        geo_v = pos_map[int(v)]
        if etype == "line":
            cap = edge_capacity_mw_from_line(net, eidx)
            lk = edge_length_km_from_line(net, eidx)
        else:
            cap = edge_capacity_mw_from_trafo(net, eidx)
            lk = geo_distance_km(geo_u["lat"], geo_u["lon"], geo_v["lat"], geo_v["lon"])
        lines.append(
            {
                "id": "",  # fill later
                "from": int(u),
                "to": int(v),
                "capacity": float(round(cap, 6)),
                "length_km": float(round(lk, 6)),
                "from_lat": float(geo_u["lat"]),
                "from_lon": float(geo_u["lon"]),
                "to_lat": float(geo_v["lat"]),
                "to_lon": float(geo_v["lon"]),
                "mid_lat": float((geo_u["lat"] + geo_v["lat"]) / 2.0),
                "mid_lon": float((geo_u["lon"] + geo_v["lon"]) / 2.0),
                "asset_type": etype,
            }
        )

    # Stable relabel.
    lines = sorted(lines, key=lambda x: (int(x["from"]), int(x["to"]), str(x.get("asset_type", ""))))
    for i, ln in enumerate(lines):
        ln["id"] = f"L{i}"

    generators: list[dict[str, Any]] = []
    if len(net.ext_grid):
        for idx, row in net.ext_grid.iterrows():
            b = int(row["bus"])
            if b not in selected_set:
                continue
            cap = parse_optional_float(row.get("max_p_mw"))
            if cap is None:
                cap = parse_optional_float(row.get("p_mw"))
            if cap is None:
                cap = 120.0
            generators.append(
                {
                    "id": f"EG{int(idx)}",
                    "type": "ext_grid",
                    "bus": b,
                    "capacity": float(cap),
                }
            )

    if len(net.gen):
        for idx, row in net.gen.iterrows():
            b = int(row["bus"])
            if b not in selected_set:
                continue
            cap = parse_optional_float(row.get("max_p_mw"))
            if cap is None:
                cap = parse_optional_float(row.get("p_mw"))
            if cap is None:
                cap = 60.0
            generators.append(
                {
                    "id": f"G{int(idx)}",
                    "type": "thermal",
                    "bus": b,
                    "capacity": float(cap),
                }
            )

    if len(net.sgen):
        for idx, row in net.sgen.iterrows():
            b = int(row["bus"])
            if b not in selected_set:
                continue
            generators.append(
                {
                    "id": f"SG{int(idx)}",
                    "type": map_sgen_type(str(row.get("type", ""))),
                    "bus": b,
                    "capacity": float(parse_optional_float(row.get("p_mw")) or 0.0),
                }
            )

    payload = {
        "nodes": nodes,
        "lines": lines,
        "generators": generators,
        "source": f"pandapower.networks.{args.case} -> connected_subgraph_{len(nodes)}",
        "geo_reference": {
            "type": "synthetic_layout",
            "anchor_lat": float(args.anchor_lat),
            "anchor_lon": float(args.anchor_lon),
            "unit_km_per_local": float(args.unit_km_per_local),
            "layout_seed": int(args.layout_seed),
            "note": "Coordinates generated by spring layout for visualization only.",
        },
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    summary = {
        "output_grid": str(output_path),
        "case": args.case,
        "seed_bus": int(seed_bus),
        "node_count": len(nodes),
        "line_count": len(lines),
        "generator_count": len(generators),
        "load_nodes": int(sum(1 for n in nodes if str(n.get("type", "")).lower() == "load")),
        "source_nodes": int(len({int(g["bus"]) for g in generators if float(g.get("capacity", 0.0) or 0.0) > 0.0})),
        "connected": bool(nx.is_connected(g_sub)),
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

