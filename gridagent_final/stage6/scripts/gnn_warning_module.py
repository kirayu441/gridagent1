from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import networkx as nx
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.nn.functional as F


@dataclass
class WarningDataset:
    timestamps: pd.DatetimeIndex
    line_ids: list[str]
    from_bus: np.ndarray  # [E]
    to_bus: np.ndarray  # [E]
    node_ids: list[int]
    load_buses: list[int]
    source_buses: list[int]
    load_type_map: dict[int, str]
    node_x: np.ndarray  # [T,N,F_node]
    edge_dyn_x: np.ndarray  # [T,E,F_edge_dyn]
    edge_static_x: np.ndarray  # [E,F_edge_static]
    labels: np.ndarray  # [T,E], empirical outage probability
    metapath_names: list[str] | None = None
    metapath_index: np.ndarray | None = None  # [P,E,K], -1 for padding
    metapath_mask: np.ndarray | None = None  # [P,E,K], 0/1
    node_weather: dict[str, np.ndarray] | None = None
    node_weather_meta: dict[str, Any] | None = None


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


def minmax_scale(x: np.ndarray) -> np.ndarray:
    x = np.asarray(x, dtype=float)
    xmin = float(np.min(x))
    xmax = float(np.max(x))
    span = xmax - xmin
    if span < 1e-12:
        return np.zeros_like(x, dtype=float)
    return (x - xmin) / span


def minmax_scale_global(x: np.ndarray) -> np.ndarray:
    arr = np.asarray(x, dtype=float)
    xmin = float(np.min(arr))
    xmax = float(np.max(arr))
    span = xmax - xmin
    if span < 1e-12:
        return np.zeros_like(arr, dtype=float)
    return (arr - xmin) / span


def find_column(columns: list[str], include_keywords: list[str], exclude_keywords: list[str] | None = None) -> str | None:
    exclude_keywords = exclude_keywords or []
    lowered = [(c, c.lower()) for c in columns]
    for col, low in lowered:
        if all(k in low for k in include_keywords) and not any(k in low for k in exclude_keywords):
            return col
    return None


def load_grid_topology(grid_path: Path) -> dict[str, Any]:
    if not grid_path.exists():
        raise FileNotFoundError(f"missing grid topology: {grid_path}")
    payload = json.loads(grid_path.read_text(encoding="utf-8"))
    if not payload.get("nodes") or not payload.get("lines"):
        raise ValueError(f"invalid grid topology json: {grid_path}")
    return payload


def load_failure_features(failure_csv: Path) -> tuple[pd.DatetimeIndex, list[str], np.ndarray, np.ndarray, dict[str, tuple[int, int]]]:
    if not failure_csv.exists():
        raise FileNotFoundError(f"missing failure csv: {failure_csv}")

    df = pd.read_csv(failure_csv)
    required = {"timestamp", "line_id", "from_bus", "to_bus", "p_line"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"failure csv missing columns: {sorted(missing)}")

    if "v_surface_ms" not in df.columns:
        df["v_surface_ms"] = np.nan

    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    if df["timestamp"].isna().any():
        raise ValueError("invalid timestamp in failure csv")

    p_pivot = (
        df.pivot_table(index="timestamp", columns="line_id", values="p_line", aggfunc="mean")
        .sort_index()
        .sort_index(axis=1)
    )
    v_pivot = (
        df.pivot_table(index="timestamp", columns="line_id", values="v_surface_ms", aggfunc="mean")
        .reindex(index=p_pivot.index, columns=p_pivot.columns)
        .sort_index()
        .sort_index(axis=1)
    )

    if p_pivot.empty:
        raise ValueError("empty failure matrix after pivot")

    line_ids = [str(c) for c in p_pivot.columns]
    ts = pd.DatetimeIndex(p_pivot.index)

    line_map = (
        df.drop_duplicates(subset=["line_id"])\
        .set_index("line_id")[["from_bus", "to_bus"]]\
        .to_dict(orient="index")
    )
    edge_map: dict[str, tuple[int, int]] = {}
    for lid in line_ids:
        item = line_map.get(lid)
        if item is None:
            raise ValueError(f"line edge mapping missing: {lid}")
        edge_map[lid] = (int(item["from_bus"]), int(item["to_bus"]))

    p_arr = np.clip(p_pivot.to_numpy(dtype=float), 0.0, 1.0)
    v_arr = v_pivot.to_numpy(dtype=float)
    if np.isnan(v_arr).any():
        # Fallback to 0 if wind speed is unavailable.
        v_arr = np.nan_to_num(v_arr, nan=0.0)

    return ts, line_ids, p_arr, v_arr, edge_map


def load_contingency_labels(contingency_tensor: Path, expected_t: int, expected_e: int) -> np.ndarray:
    if not contingency_tensor.exists():
        raise FileNotFoundError(f"missing contingency tensor: {contingency_tensor}")
    arr = np.load(contingency_tensor)
    if arr.ndim != 3:
        raise ValueError(f"contingency tensor should be 3D [S,T,E], got {arr.shape}")
    if arr.shape[1] != expected_t or arr.shape[2] != expected_e:
        raise ValueError(
            f"tensor dimension mismatch: tensor={arr.shape}, expected T={expected_t}, E={expected_e}"
        )
    return np.clip(arr.mean(axis=0), 0.0, 1.0)


def load_time_features(
    aligned_csv: Path,
    target_ts: pd.DatetimeIndex,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, dict[str, Any]]:
    if not aligned_csv.exists():
        raise FileNotFoundError(f"missing aligned csv: {aligned_csv}")
    df = pd.read_csv(aligned_csv)
    if "timestamp" not in df.columns:
        raise ValueError(f"aligned csv missing timestamp: {aligned_csv}")

    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    df = df.dropna(subset=["timestamp"]).set_index("timestamp").sort_index()
    cols = list(df.columns)

    wind_col = find_column(cols, include_keywords=["wind", "electricity"])
    pv_col = find_column(cols, include_keywords=["pv", "electricity"])
    wind_speed_col = find_column(cols, include_keywords=["wind_speed"])
    load_cols = [c for c in cols if c.lower().startswith("load_")]

    if wind_col is None or pv_col is None or not load_cols:
        raise ValueError("aligned csv missing required wind/pv/load columns")

    aligned = df.reindex(target_ts).interpolate(method="time").ffill().bfill()

    wind = aligned[wind_col].to_numpy(dtype=float)
    pv = aligned[pv_col].to_numpy(dtype=float)
    load_total = aligned[load_cols].sum(axis=1).to_numpy(dtype=float)
    if wind_speed_col is not None:
        wind_speed = aligned[wind_speed_col].to_numpy(dtype=float)
    else:
        wind_speed = np.zeros(len(target_ts), dtype=float)

    feature_meta = {
        "wind_column": str(wind_col),
        "pv_column": str(pv_col),
        "load_columns": [str(c) for c in load_cols],
        "wind_speed_column": str(wind_speed_col) if wind_speed_col is not None else None,
        "wind_speed_fallback_zero": bool(wind_speed_col is None),
    }
    return wind, pv, load_total, wind_speed, feature_meta


def build_load_type_map(load_buses: list[int], priority_csv: Path | None) -> dict[int, str]:
    if priority_csv is not None and priority_csv.exists():
        df = pd.read_csv(priority_csv)
        if {"load_bus", "priority_level"}.issubset(df.columns):
            result: dict[int, str] = {}
            for _, row in df.iterrows():
                bus = int(row["load_bus"])
                lvl = int(row["priority_level"])
                result[bus] = "primary" if lvl == 1 else "secondary"
            for b in load_buses:
                if b not in result:
                    result[b] = "secondary"
            return result

    # Fallback: first 30% are treated as primary critical loads.
    n = len(load_buses)
    k_primary = max(1, int(np.ceil(0.30 * n)))
    sorted_load = sorted(load_buses)
    primary_set = set(sorted_load[:k_primary])
    return {b: ("primary" if b in primary_set else "secondary") for b in sorted_load}


def build_node_coordinate_array(nodes: list[dict[str, Any]], node_ids: list[int]) -> tuple[np.ndarray, list[str]]:
    node_map = {int(n["id"]): n for n in nodes if "id" in n}
    coords = np.zeros((len(node_ids), 2), dtype=float)
    source_tags: list[str] = []
    for i, b in enumerate(node_ids):
        row = node_map.get(int(b), {})
        lat = parse_optional_float(row.get("lat"))
        lon = parse_optional_float(row.get("lon"))
        if lat is not None and lon is not None:
            coords[i, 0] = float(lon)
            coords[i, 1] = float(lat)
            source_tags.append("lat_lon")
            continue
        lx = parse_optional_float(row.get("local_x"))
        ly = parse_optional_float(row.get("local_y"))
        if lx is not None and ly is not None:
            coords[i, 0] = float(lx)
            coords[i, 1] = float(ly)
            source_tags.append("local_xy")
            continue
        angle = 2.0 * np.pi * (i / max(len(node_ids), 1))
        radius = 1.0 + 0.2 * (i % 5)
        coords[i, 0] = radius * np.cos(angle)
        coords[i, 1] = radius * np.sin(angle)
        source_tags.append("synthetic_ring")
    return coords, source_tags


def build_spatial_influence(node_coords: np.ndarray, n_time: int) -> np.ndarray:
    if n_time <= 0 or node_coords.size == 0:
        return np.zeros((max(n_time, 0), node_coords.shape[0] if node_coords.ndim == 2 else 0), dtype=float)

    x = np.asarray(node_coords[:, 0], dtype=float)
    y = np.asarray(node_coords[:, 1], dtype=float)
    x = (x - x.mean()) / (x.std() + 1e-6)
    y = (y - y.mean()) / (y.std() + 1e-6)

    t = np.linspace(0.0, 1.0, n_time, dtype=float)
    # Smoothly moving weather center to create spatial heterogeneity across time.
    center_x = 1.4 - 2.8 * t
    center_y = 0.8 * np.sin(2.0 * np.pi * (t + 0.15))

    dx = x[None, :] - center_x[:, None]
    dy = y[None, :] - center_y[:, None]
    dist2 = dx * dx + dy * dy
    sigma2 = 0.95**2
    influence = np.exp(-dist2 / (2.0 * sigma2))
    influence = influence / np.clip(influence.max(axis=1, keepdims=True), 1e-6, None)
    return np.clip(influence, 0.0, 1.0)


def normalize_factor_by_weights(factor: np.ndarray, weights: np.ndarray) -> np.ndarray:
    w = np.asarray(weights, dtype=float)
    if w.ndim != 1:
        raise ValueError("weights should be 1D")
    if factor.ndim != 2 or factor.shape[1] != len(w):
        raise ValueError("factor shape should be [T,N] and match weights length")

    if np.sum(w) <= 1e-12:
        w = np.ones_like(w, dtype=float)
    w = w / np.clip(np.sum(w), 1e-12, None)
    avg = (factor * w[None, :]).sum(axis=1, keepdims=True)
    return factor / np.clip(avg, 1e-6, None)


def build_bus_to_lines(from_bus: np.ndarray, to_bus: np.ndarray) -> dict[int, list[int]]:
    bus_to_lines: dict[int, list[int]] = {}
    for idx, (u, v) in enumerate(zip(from_bus.tolist(), to_bus.tolist(), strict=False)):
        bus_to_lines.setdefault(int(u), []).append(int(idx))
        bus_to_lines.setdefault(int(v), []).append(int(idx))
    return bus_to_lines


def build_line_graph(bus_to_lines: dict[int, list[int]], n_edge: int) -> nx.Graph:
    g = nx.Graph()
    g.add_nodes_from(range(n_edge))
    for line_group in bus_to_lines.values():
        unique_lines = sorted(set(int(x) for x in line_group))
        for i in range(len(unique_lines)):
            for j in range(i + 1, len(unique_lines)):
                g.add_edge(unique_lines[i], unique_lines[j])
    return g


def rank_and_pack_neighbors(
    candidates_by_line: list[list[int]],
    line_dist: np.ndarray,
    topk: int,
) -> tuple[np.ndarray, np.ndarray]:
    n_edge = len(candidates_by_line)
    k = max(int(topk), 1)
    idx = np.full((n_edge, k), -1, dtype=np.int64)
    mask = np.zeros((n_edge, k), dtype=np.float32)

    for i in range(n_edge):
        unique = sorted(
            {int(j) for j in candidates_by_line[i] if int(j) != i},
            key=lambda j: (float(line_dist[i, j]), int(j)),
        )
        if not unique:
            unique = [int(i)]
        selected = unique[:k]
        idx[i, : len(selected)] = np.asarray(selected, dtype=np.int64)
        mask[i, : len(selected)] = 1.0

    return idx, mask


def build_fixed_metapath_tensors(
    from_bus: np.ndarray,
    to_bus: np.ndarray,
    source_buses: list[int],
    primary_load_buses: list[int],
    topk: int,
) -> tuple[list[str], np.ndarray, np.ndarray]:
    n_edge = len(from_bus)
    if n_edge == 0:
        return [], np.zeros((0, 0, 0), dtype=np.int64), np.zeros((0, 0, 0), dtype=np.float32)

    bus_to_lines = build_bus_to_lines(from_bus=from_bus, to_bus=to_bus)
    line_graph = build_line_graph(bus_to_lines=bus_to_lines, n_edge=n_edge)

    inf = float(n_edge + 10)
    line_dist = np.full((n_edge, n_edge), inf, dtype=float)
    for i in range(n_edge):
        line_dist[i, i] = 0.0
        sp = nx.single_source_shortest_path_length(line_graph, i, cutoff=4)
        for j, d in sp.items():
            line_dist[i, int(j)] = float(d)

    share_bus_candidates = [list(line_graph.neighbors(i)) for i in range(n_edge)]

    two_hop_candidates: list[list[int]] = []
    for i in range(n_edge):
        cands = [j for j in range(n_edge) if j != i and abs(line_dist[i, j] - 2.0) < 1e-9]
        if not cands:
            cands = share_bus_candidates[i]
        two_hop_candidates.append(cands)

    def build_anchor_bridge(anchor_buses: list[int]) -> list[list[int]]:
        anchor_lines: set[int] = set()
        for b in anchor_buses:
            anchor_lines.update(int(x) for x in bus_to_lines.get(int(b), []))

        out: list[list[int]] = []
        for i in range(n_edge):
            if not anchor_lines:
                out.append(list(share_bus_candidates[i]))
                continue

            reachable = [(line_dist[i, j], j) for j in anchor_lines if line_dist[i, j] < inf]
            if not reachable:
                out.append(list(share_bus_candidates[i]))
                continue

            d_min = min(d for d, _ in reachable)
            near = [j for d, j in reachable if d <= d_min + 1.0]
            cands = set(int(j) for j in near)
            for j in near:
                cands.update(int(u) for u in line_graph.neighbors(int(j)))
            if not cands:
                cands.update(int(j) for j in share_bus_candidates[i])
            out.append(sorted(cands))
        return out

    source_bridge_candidates = build_anchor_bridge(anchor_buses=source_buses)
    primary_load_bridge_candidates = build_anchor_bridge(anchor_buses=primary_load_buses)

    metapath_names = [
        "share_bus",
        "two_hop_topology",
        "source_bridge",
        "primary_load_bridge",
    ]
    per_path_candidates = [
        share_bus_candidates,
        two_hop_candidates,
        source_bridge_candidates,
        primary_load_bridge_candidates,
    ]

    idx_list: list[np.ndarray] = []
    mask_list: list[np.ndarray] = []
    for cands in per_path_candidates:
        idx, mask = rank_and_pack_neighbors(candidates_by_line=cands, line_dist=line_dist, topk=topk)
        idx_list.append(idx)
        mask_list.append(mask)

    return metapath_names, np.stack(idx_list, axis=0), np.stack(mask_list, axis=0)


def build_dataset(
    grid_payload: dict[str, Any],
    timestamps: pd.DatetimeIndex,
    line_ids: list[str],
    edge_map: dict[str, tuple[int, int]],
    p_line: np.ndarray,
    v_surface: np.ndarray,
    labels: np.ndarray,
    aligned_csv: Path,
    priority_csv: Path | None,
    metapath_topk: int = 6,
) -> WarningDataset:
    nodes = grid_payload.get("nodes", [])
    lines = grid_payload.get("lines", [])
    generators = grid_payload.get("generators", [])

    node_ids = sorted(int(n["id"]) for n in nodes if "id" in n)
    node_to_idx = {b: i for i, b in enumerate(node_ids)}
    n_node = len(node_ids)
    n_time = len(timestamps)
    n_edge = len(line_ids)

    load_buses = sorted(int(n["id"]) for n in nodes if str(n.get("type", "")).lower() == "load")

    source_special = {
        int(g["bus"])
        for g in generators
        if "bus" in g and str(g.get("type", "")).lower() in {"thermal", "slack", "ext_grid"}
    }
    source_positive = {
        int(g["bus"])
        for g in generators
        if "bus" in g and (parse_optional_float(g.get("capacity")) or 0.0) > 0.0
    }
    source_buses = sorted(source_special | source_positive)
    if not source_buses and node_ids:
        source_buses = [node_ids[0]]

    load_type_map = build_load_type_map(load_buses=load_buses, priority_csv=priority_csv)

    wind_total, pv_total, load_total, wind_speed, time_feature_meta = load_time_features(
        aligned_csv=aligned_csv,
        target_ts=timestamps,
    )

    # Static node features
    graph = nx.Graph()
    graph.add_nodes_from(node_ids)
    for lid in line_ids:
        u, v = edge_map[lid]
        graph.add_edge(u, v)
    degree = np.array([graph.degree(b) for b in node_ids], dtype=float)
    degree_norm = minmax_scale(degree)

    # Build load share (primary gets higher share in stress stage)
    primary_loads = [b for b in load_buses if load_type_map.get(b, "secondary") == "primary"]
    secondary_loads = [b for b in load_buses if b not in set(primary_loads)]
    load_share = np.zeros(n_node, dtype=float)
    if load_buses:
        # Keep a simple weighted share close to earlier scheduling assumptions.
        base = np.array([1.8 if b in primary_loads else 1.0 for b in load_buses], dtype=float)
        base /= base.sum()
        for b, sh in zip(load_buses, base):
            load_share[node_to_idx[b]] = float(sh)

    # Renewable share by bus from generator capacities.
    wind_caps = np.zeros(n_node, dtype=float)
    pv_caps = np.zeros(n_node, dtype=float)
    for g in generators:
        bus = int(g.get("bus", -1))
        if bus not in node_to_idx:
            continue
        cap = max(parse_optional_float(g.get("capacity")) or 0.0, 0.0)
        gtype = str(g.get("type", "")).lower()
        if gtype == "wind":
            wind_caps[node_to_idx[bus]] += cap
        elif gtype == "pv":
            pv_caps[node_to_idx[bus]] += cap

    if wind_caps.sum() <= 1e-12:
        wind_caps += 1e-6
    if pv_caps.sum() <= 1e-12:
        pv_caps += 1e-6
    wind_share = wind_caps / wind_caps.sum()
    pv_share = pv_caps / pv_caps.sum()

    is_load = np.array([1.0 if b in set(load_buses) else 0.0 for b in node_ids], dtype=float)
    is_source = np.array([1.0 if b in set(source_buses) else 0.0 for b in node_ids], dtype=float)

    node_static = np.stack(
        [
            degree_norm,
            is_load,
            is_source,
            load_share,
            minmax_scale(wind_share),
            minmax_scale(pv_share),
        ],
        axis=1,
    )

    # Dynamic node features with spatially heterogeneous weather field.
    node_coords, coord_sources = build_node_coordinate_array(nodes=nodes, node_ids=node_ids)
    influence = build_spatial_influence(node_coords=node_coords, n_time=n_time)

    wind_factor = np.clip(0.65 + 0.75 * influence, 0.35, 1.60)
    pv_factor = np.clip(1.08 - 0.40 * influence, 0.35, 1.35)
    load_factor = np.clip(0.95 + 0.14 * influence, 0.75, 1.35)
    ws_factor = np.clip(0.55 + 0.95 * influence, 0.35, 1.70)

    wind_factor = normalize_factor_by_weights(wind_factor, weights=wind_share)
    pv_factor = normalize_factor_by_weights(pv_factor, weights=pv_share)
    load_factor = normalize_factor_by_weights(load_factor, weights=load_share)

    node_wind_raw = np.clip(wind_total[:, None] * wind_factor, 0.0, None)
    node_pv_raw = np.clip(pv_total[:, None] * pv_factor, 0.0, None)
    node_load_raw = np.clip(load_total[:, None] * load_factor, 0.0, None)
    node_ws_raw = np.clip(wind_speed[:, None] * ws_factor + 2.0 * influence, 0.0, None)

    coord_source_count: dict[str, int] = {}
    for tag in coord_sources:
        coord_source_count[tag] = int(coord_source_count.get(tag, 0) + 1)

    wind_node_scaled = minmax_scale_global(node_wind_raw)
    pv_node_scaled = minmax_scale_global(node_pv_raw)
    load_node_scaled = minmax_scale_global(node_load_raw)
    ws_node_scaled = minmax_scale_global(node_ws_raw)

    hour = np.array([ts.hour for ts in timestamps], dtype=float)
    hour_sin = np.sin(2 * np.pi * hour / 24.0)
    hour_cos = np.cos(2 * np.pi * hour / 24.0)

    node_x = np.zeros((n_time, n_node, node_static.shape[1] + 6), dtype=float)
    for t in range(n_time):
        node_load = np.clip(load_total[t] * load_share * load_factor[t], 0.0, None)
        node_wind = np.clip(wind_total[t] * wind_share * wind_factor[t], 0.0, None)
        node_pv = np.clip(pv_total[t] * pv_share * pv_factor[t], 0.0, None)
        node_ren = node_wind + node_pv
        node_x[t, :, :] = np.concatenate(
            [
                node_static,
                np.stack(
                    [
                        minmax_scale(node_load),
                        minmax_scale(node_ren),
                        wind_node_scaled[t],
                        pv_node_scaled[t],
                        load_node_scaled[t],
                        ws_node_scaled[t],
                    ],
                    axis=1,
                ),
            ],
            axis=1,
        )

    # Edge static features
    line_meta = {str(r.get("id")): r for r in lines}
    length = np.zeros(n_edge, dtype=float)
    capacity = np.zeros(n_edge, dtype=float)
    from_bus = np.zeros(n_edge, dtype=int)
    to_bus = np.zeros(n_edge, dtype=int)
    for i, lid in enumerate(line_ids):
        u, v = edge_map[lid]
        from_bus[i] = u
        to_bus[i] = v
        meta = line_meta.get(lid, {})
        length[i] = parse_optional_float(meta.get("length_km")) or 1.0
        capacity[i] = parse_optional_float(meta.get("capacity")) or 1.0

    edge_static = np.stack([minmax_scale(length), minmax_scale(capacity)], axis=1)

    # Edge dynamic features
    edge_dyn_x = np.stack([minmax_scale(p_line), minmax_scale(v_surface)], axis=2)

    primary_load_buses = [b for b, t in load_type_map.items() if t == "primary"]
    metapath_names, metapath_index, metapath_mask = build_fixed_metapath_tensors(
        from_bus=from_bus,
        to_bus=to_bus,
        source_buses=source_buses,
        primary_load_buses=primary_load_buses,
        topk=metapath_topk,
    )

    return WarningDataset(
        timestamps=timestamps,
        line_ids=line_ids,
        from_bus=from_bus,
        to_bus=to_bus,
        node_ids=node_ids,
        load_buses=load_buses,
        source_buses=source_buses,
        load_type_map=load_type_map,
        node_x=node_x,
        edge_dyn_x=edge_dyn_x,
        edge_static_x=edge_static,
        labels=np.clip(labels, 0.0, 1.0),
        metapath_names=metapath_names,
        metapath_index=metapath_index,
        metapath_mask=metapath_mask,
        node_weather={
            "influence": influence,
            "wind_factor": wind_factor,
            "pv_factor": pv_factor,
            "load_factor": load_factor,
            "wind_speed_factor": ws_factor,
            "wind_raw": node_wind_raw,
            "pv_raw": node_pv_raw,
            "load_raw": node_load_raw,
            "wind_speed_raw": node_ws_raw,
        },
        node_weather_meta={
            "method": "global_timeseries_projected_to_nodes_with_spatial_influence",
            "time_feature_columns": time_feature_meta,
            "coordinate_source_count": coord_source_count,
            "factor_formulas": {
                "wind_factor": "clip(0.65 + 0.75 * influence, 0.35, 1.60), then weighted-normalized by wind_share",
                "pv_factor": "clip(1.08 - 0.40 * influence, 0.35, 1.35), then weighted-normalized by pv_share",
                "load_factor": "clip(0.95 + 0.14 * influence, 0.75, 1.35), then weighted-normalized by load_share",
                "wind_speed_factor": "clip(0.55 + 0.95 * influence, 0.35, 1.70)",
            },
            "shares": {
                "wind_share_sum": float(wind_share.sum()),
                "pv_share_sum": float(pv_share.sum()),
                "load_share_sum": float(load_share.sum()),
            },
        },
    )


class GraphMessageLayer(nn.Module):
    def __init__(self, hidden_dim: int) -> None:
        super().__init__()
        self.self_fc = nn.Linear(hidden_dim, hidden_dim)
        self.nei_fc = nn.Linear(hidden_dim, hidden_dim)
        self.norm = nn.LayerNorm(hidden_dim)

    def forward(self, h: torch.Tensor, src: torch.Tensor, dst: torch.Tensor) -> torch.Tensor:
        n = h.shape[0]
        agg = torch.zeros_like(h)
        agg.index_add_(0, dst, h[src])
        agg.index_add_(0, src, h[dst])

        deg = torch.zeros(n, device=h.device)
        ones = torch.ones(src.shape[0], device=h.device)
        deg.index_add_(0, dst, ones)
        deg.index_add_(0, src, ones)
        deg = deg.clamp_min(1.0).unsqueeze(1)

        h_next = self.self_fc(h) + self.nei_fc(agg / deg)
        h_next = F.gelu(h_next)
        return self.norm(h_next)


class LineRiskGNN(nn.Module):
    def __init__(self, node_dim: int, edge_dyn_dim: int, edge_static_dim: int, hidden_dim: int = 64) -> None:
        super().__init__()
        self.node_encoder = nn.Sequential(
            nn.Linear(node_dim, hidden_dim),
            nn.GELU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.GELU(),
        )
        self.mp1 = GraphMessageLayer(hidden_dim)
        self.mp2 = GraphMessageLayer(hidden_dim)
        self.edge_head = nn.Sequential(
            nn.Linear(hidden_dim * 2 + edge_dyn_dim + edge_static_dim, hidden_dim),
            nn.GELU(),
            nn.Dropout(p=0.10),
            nn.Linear(hidden_dim, 1),
        )

    def forward(
        self,
        node_x: torch.Tensor,
        edge_dyn_x: torch.Tensor,
        edge_static_x: torch.Tensor,
        src: torch.Tensor,
        dst: torch.Tensor,
    ) -> torch.Tensor:
        h = self.node_encoder(node_x)
        h = self.mp1(h, src, dst)
        h = self.mp2(h, src, dst)
        edge_feat = torch.cat([h[src], h[dst], edge_dyn_x, edge_static_x], dim=1)
        out = self.edge_head(edge_feat).squeeze(1)
        return torch.sigmoid(out)


class MetaPathSemanticBlock(nn.Module):
    def __init__(
        self,
        hidden_dim: int,
        num_metapaths: int,
        attention_mode: str = "fixed",
        edge_dyn_dim: int = 0,
    ) -> None:
        super().__init__()
        self.num_metapaths = int(num_metapaths)
        self.attention_mode = str(attention_mode)
        self.score_proj = nn.Linear(hidden_dim, hidden_dim)
        self.context_vectors = nn.Parameter(torch.randn(self.num_metapaths, hidden_dim) * 0.02)
        self.global_path_bias = nn.Parameter(torch.zeros(self.num_metapaths))
        self.condition_proj: nn.Linear | None = None
        if self.attention_mode == "adaptive_context" and int(edge_dyn_dim) > 0:
            self.condition_proj = nn.Linear(int(edge_dyn_dim), hidden_dim, bias=False)

    def forward(
        self,
        edge_repr: torch.Tensor,
        metapath_index: torch.Tensor,
        metapath_mask: torch.Tensor,
        edge_context: torch.Tensor | None = None,
    ) -> tuple[torch.Tensor, torch.Tensor]:
        # metapath_index: [P,E,K], metapath_mask: [P,E,K]
        safe_index = metapath_index.clamp_min(0)
        neighbor_repr = edge_repr[safe_index]  # [P,E,K,H]
        mask = metapath_mask.unsqueeze(-1)  # [P,E,K,1]

        denom = mask.sum(dim=2).clamp_min(1.0)  # [P,E,1]
        path_repr = (neighbor_repr * mask).sum(dim=2) / denom  # [P,E,H]

        path_repr_ep = path_repr.permute(1, 0, 2)  # [E,P,H]
        score_feat = torch.tanh(self.score_proj(path_repr_ep))  # [E,P,H]
        score = torch.einsum("eph,ph->ep", score_feat, self.context_vectors)  # [E,P]
        if self.attention_mode == "adaptive_global":
            # Add sample-level adaptive bias from current metapath representations.
            global_ctx = torch.tanh(path_repr_ep.mean(dim=0))  # [P,H]
            adaptive_bias = (global_ctx * self.context_vectors).sum(dim=1)  # [P]
            score = score + adaptive_bias.unsqueeze(0) + self.global_path_bias.unsqueeze(0)
        elif self.attention_mode == "adaptive_context" and self.condition_proj is not None and edge_context is not None:
            cond = torch.tanh(self.condition_proj(edge_context))  # [E,H]
            score = score + torch.einsum("eph,eh->ep", score_feat, cond)
        alpha = torch.softmax(score, dim=1)

        context = (alpha.unsqueeze(-1) * path_repr_ep).sum(dim=1)  # [E,H]
        return context, alpha


class LineRiskMetaPathGNN(nn.Module):
    def __init__(
        self,
        node_dim: int,
        edge_dyn_dim: int,
        edge_static_dim: int,
        hidden_dim: int,
        num_metapaths: int,
        metapath_attention_mode: str = "fixed",
    ) -> None:
        super().__init__()
        self.node_encoder = nn.Sequential(
            nn.Linear(node_dim, hidden_dim),
            nn.GELU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.GELU(),
        )
        self.mp1 = GraphMessageLayer(hidden_dim)
        self.mp2 = GraphMessageLayer(hidden_dim)

        self.edge_base_encoder = nn.Sequential(
            nn.Linear(hidden_dim * 2 + edge_dyn_dim + edge_static_dim, hidden_dim),
            nn.GELU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.GELU(),
        )
        self.metapath_block = MetaPathSemanticBlock(
            hidden_dim=hidden_dim,
            num_metapaths=num_metapaths,
            attention_mode=metapath_attention_mode,
            edge_dyn_dim=edge_dyn_dim,
        )
        self.base_head = nn.Sequential(
            nn.Linear(hidden_dim * 2 + edge_dyn_dim + edge_static_dim, hidden_dim),
            nn.GELU(),
            nn.Dropout(p=0.10),
            nn.Linear(hidden_dim, 1),
        )
        self.delta_head = nn.Sequential(
            nn.Linear(hidden_dim * 2 + edge_dyn_dim + edge_static_dim, hidden_dim),
            nn.GELU(),
            nn.Dropout(p=0.05),
            nn.Linear(hidden_dim, 1),
        )
        self.gate_head = nn.Sequential(
            nn.Linear(hidden_dim * 2 + edge_dyn_dim + edge_static_dim, hidden_dim),
            nn.GELU(),
            nn.Linear(hidden_dim, 1),
        )
        gate_last = self.gate_head[-1]
        if isinstance(gate_last, nn.Linear):
            nn.init.constant_(gate_last.bias, -2.0)

    def forward(
        self,
        node_x: torch.Tensor,
        edge_dyn_x: torch.Tensor,
        edge_static_x: torch.Tensor,
        src: torch.Tensor,
        dst: torch.Tensor,
        metapath_index: torch.Tensor,
        metapath_mask: torch.Tensor,
        delta_scale: float = 1.0,
        return_attention: bool = False,
    ) -> torch.Tensor | tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        h = self.node_encoder(node_x)
        h = self.mp1(h, src, dst)
        h = self.mp2(h, src, dst)

        edge_raw = torch.cat([h[src], h[dst], edge_dyn_x, edge_static_x], dim=1)
        base_logit = self.base_head(edge_raw).squeeze(1)
        edge_repr = self.edge_base_encoder(edge_raw)
        metapath_context, alpha = self.metapath_block(
            edge_repr=edge_repr,
            metapath_index=metapath_index,
            metapath_mask=metapath_mask,
            edge_context=edge_dyn_x,
        )
        delta_feat = torch.cat([edge_repr, metapath_context, edge_dyn_x, edge_static_x], dim=1)
        delta_logit = self.delta_head(delta_feat).squeeze(1)
        gate = torch.sigmoid(self.gate_head(edge_raw).squeeze(1))
        scale = float(np.clip(delta_scale, 0.0, 1.0))
        out = torch.sigmoid(base_logit + (scale * gate) * delta_logit)

        if return_attention:
            return out, alpha, gate
        return out


def compute_risk_weight_tensor(
    truth: torch.Tensor,
    alpha: float,
    beta: float,
    threshold: float,
) -> torch.Tensor:
    thr = float(np.clip(threshold, 0.0, 1.0))
    base = torch.ones_like(truth)
    if float(alpha) > 0.0:
        base = base + float(alpha) * truth
    if float(beta) > 0.0:
        base = base + float(beta) * (truth >= thr).to(truth.dtype)
    return base


def weighted_mse_loss(pred: torch.Tensor, truth: torch.Tensor, weight: torch.Tensor) -> torch.Tensor:
    err2 = (pred - truth) ** 2
    # Normalize by mean weight to keep loss scale stable across different risk mixes.
    return (err2 * weight).mean() / weight.mean().clamp_min(1e-6)


def evaluate_prob_metrics(
    pred: np.ndarray,
    truth: np.ndarray,
    high_risk_threshold: float = 0.10,
    top_risk_quantile: float = 0.90,
) -> dict[str, float]:
    pred_flat = np.asarray(pred, dtype=float).reshape(-1)
    truth_flat = np.asarray(truth, dtype=float).reshape(-1)

    if pred_flat.size == 0 or truth_flat.size == 0:
        return {
            "mae": float("nan"),
            "rmse": float("nan"),
            "brier": float("nan"),
            "high_risk_mae": float("nan"),
            "high_risk_rmse": float("nan"),
            "high_risk_count": 0.0,
            "high_risk_ratio": 0.0,
            "top_risk_mae": float("nan"),
            "top_risk_rmse": float("nan"),
            "top_risk_count": 0.0,
            "top_risk_ratio": 0.0,
            "high_risk_threshold": float(np.clip(high_risk_threshold, 0.0, 1.0)),
            "top_risk_quantile": float(np.clip(top_risk_quantile, 0.0, 1.0)),
            "top_risk_threshold": float("nan"),
        }

    err = pred_flat - truth_flat
    mse = float(np.mean(err ** 2))
    mae = float(np.mean(np.abs(err)))
    rmse = float(np.sqrt(mse))

    thr = float(np.clip(high_risk_threshold, 0.0, 1.0))
    mask_high = truth_flat >= thr
    high_count = int(mask_high.sum())
    if high_count > 0:
        err_high = err[mask_high]
        high_mae = float(np.mean(np.abs(err_high)))
        high_rmse = float(np.sqrt(np.mean(err_high ** 2)))
    else:
        high_mae = float("nan")
        high_rmse = float("nan")

    q = float(np.clip(top_risk_quantile, 0.0, 1.0))
    top_thr = float(np.quantile(truth_flat, q))
    mask_top = truth_flat >= top_thr
    top_count = int(mask_top.sum())
    if top_count > 0:
        err_top = err[mask_top]
        top_mae = float(np.mean(np.abs(err_top)))
        top_rmse = float(np.sqrt(np.mean(err_top ** 2)))
    else:
        top_mae = float("nan")
        top_rmse = float("nan")

    total = max(int(truth_flat.size), 1)
    return {
        "mae": mae,
        "rmse": rmse,
        "brier": mse,
        "high_risk_mae": high_mae,
        "high_risk_rmse": high_rmse,
        "high_risk_count": float(high_count),
        "high_risk_ratio": float(high_count / total),
        "top_risk_mae": top_mae,
        "top_risk_rmse": top_rmse,
        "top_risk_count": float(top_count),
        "top_risk_ratio": float(top_count / total),
        "high_risk_threshold": thr,
        "top_risk_quantile": q,
        "top_risk_threshold": top_thr,
    }


def train_gnn(
    data: WarningDataset,
    hidden_dim: int,
    epochs: int,
    lr: float,
    weight_decay: float,
    train_ratio: float,
    seed: int,
    use_metapath_v1: bool,
    risk_weight_alpha: float,
    risk_weight_beta: float,
    risk_weight_threshold: float,
    risk_weight_on_metapath_only: bool,
    metapath_gate_reg_lambda: float,
    metapath_attention_entropy_reg_lambda: float,
    metapath_warmup_epochs: int,
    metapath_attention_mode: str,
    high_risk_threshold: float,
    top_risk_quantile: float,
) -> tuple[nn.Module, np.ndarray, dict[str, Any]]:
    torch.manual_seed(seed)
    np.random.seed(seed)

    device = torch.device("cpu")
    n_time = data.node_x.shape[0]

    split = int(np.floor(n_time * train_ratio))
    split = max(1, min(split, n_time - 1)) if n_time > 1 else 1
    idx_train = np.arange(0, split)
    idx_val = np.arange(split, n_time)

    node_x = torch.tensor(data.node_x, dtype=torch.float32, device=device)
    edge_dyn = torch.tensor(data.edge_dyn_x, dtype=torch.float32, device=device)
    edge_static = torch.tensor(data.edge_static_x, dtype=torch.float32, device=device)
    labels = torch.tensor(data.labels, dtype=torch.float32, device=device)

    node_to_idx = {b: i for i, b in enumerate(data.node_ids)}
    src_idx = torch.tensor([node_to_idx[int(b)] for b in data.from_bus], dtype=torch.long, device=device)
    dst_idx = torch.tensor([node_to_idx[int(b)] for b in data.to_bus], dtype=torch.long, device=device)

    metapath_enabled = bool(
        use_metapath_v1
        and data.metapath_index is not None
        and data.metapath_mask is not None
        and data.metapath_names is not None
        and len(data.metapath_names) > 0
    )

    metapath_index_t: torch.Tensor | None = None
    metapath_mask_t: torch.Tensor | None = None
    if metapath_enabled:
        metapath_index_t = torch.tensor(data.metapath_index, dtype=torch.long, device=device)
        metapath_mask_t = torch.tensor(data.metapath_mask, dtype=torch.float32, device=device)

    if metapath_enabled:
        model: nn.Module = LineRiskMetaPathGNN(
            node_dim=node_x.shape[2],
            edge_dyn_dim=edge_dyn.shape[2],
            edge_static_dim=edge_static.shape[1],
            hidden_dim=hidden_dim,
            num_metapaths=len(data.metapath_names or []),
            metapath_attention_mode=str(metapath_attention_mode),
        ).to(device)
    else:
        model = LineRiskGNN(
            node_dim=node_x.shape[2],
            edge_dyn_dim=edge_dyn.shape[2],
            edge_static_dim=edge_static.shape[1],
            hidden_dim=hidden_dim,
        ).to(device)

    def forward_one(
        t: int,
        return_attention: bool = False,
        delta_scale: float = 1.0,
    ) -> torch.Tensor | tuple[torch.Tensor, torch.Tensor | None, torch.Tensor | None]:
        if metapath_enabled:
            assert metapath_index_t is not None
            assert metapath_mask_t is not None
            return model(  # type: ignore[call-arg]
                node_x[t],
                edge_dyn[t],
                edge_static,
                src_idx,
                dst_idx,
                metapath_index_t,
                metapath_mask_t,
                delta_scale=delta_scale,
                return_attention=return_attention,
            )

        out = model(node_x[t], edge_dyn[t], edge_static, src_idx, dst_idx)  # type: ignore[call-arg]
        if return_attention:
            return out, None, None
        return out

    eff_lr = float(lr * 0.7) if metapath_enabled else float(lr)
    eff_weight_decay = float(weight_decay * 0.5) if metapath_enabled else float(weight_decay)
    optimizer = torch.optim.AdamW(model.parameters(), lr=eff_lr, weight_decay=eff_weight_decay)
    risk_weight_active = (float(risk_weight_alpha) > 0.0 or float(risk_weight_beta) > 0.0) and (
        metapath_enabled or (not bool(risk_weight_on_metapath_only))
    )
    gate_reg_active = bool(metapath_enabled and float(metapath_gate_reg_lambda) > 0.0)
    attn_entropy_reg_active = bool(metapath_enabled and float(metapath_attention_entropy_reg_lambda) > 0.0)
    warmup_epochs = max(int(metapath_warmup_epochs), 0)

    best_val = float("inf")
    best_state: dict[str, torch.Tensor] | None = None
    patience = 60
    patience_count = 0
    history: list[dict[str, float]] = []

    for ep in range(1, epochs + 1):
        model.train()
        train_loss = torch.tensor(0.0, device=device)
        train_gate_reg = torch.tensor(0.0, device=device)
        train_attn_entropy = torch.tensor(0.0, device=device)
        warmup_scale = 1.0
        if metapath_enabled and warmup_epochs > 0:
            warmup_scale = float(min(1.0, ep / warmup_epochs))
        for t in idx_train:
            gate_t: torch.Tensor | None = None
            alpha_t: torch.Tensor | None = None
            need_attention = bool(metapath_enabled and (gate_reg_active or attn_entropy_reg_active))
            if need_attention:
                pred_t, alpha_t, gate_t = forward_one(t, return_attention=True, delta_scale=warmup_scale)  # type: ignore[assignment]
            else:
                pred_t = forward_one(t, delta_scale=warmup_scale)  # type: ignore[assignment]

            if risk_weight_active:
                weight_t = compute_risk_weight_tensor(
                    truth=labels[t],
                    alpha=float(risk_weight_alpha),
                    beta=float(risk_weight_beta),
                    threshold=float(risk_weight_threshold),
                )
                pred_loss_t = weighted_mse_loss(pred_t, labels[t], weight_t)
            else:
                pred_loss_t = F.mse_loss(pred_t, labels[t])

            train_loss = train_loss + pred_loss_t
            if gate_reg_active and gate_t is not None:
                train_gate_reg = train_gate_reg + torch.mean(gate_t ** 2)
            if attn_entropy_reg_active and alpha_t is not None:
                ent = -(alpha_t * torch.log(alpha_t.clamp_min(1e-8))).sum(dim=1)
                ent_norm = ent / float(np.log(max((data.metapath_names and len(data.metapath_names)) or 2, 2)))
                train_attn_entropy = train_attn_entropy + ent_norm.mean()
        train_loss = train_loss / max(len(idx_train), 1)
        if gate_reg_active:
            train_gate_reg = train_gate_reg / max(len(idx_train), 1)
            train_loss = train_loss + float(metapath_gate_reg_lambda) * train_gate_reg
        if attn_entropy_reg_active:
            train_attn_entropy = train_attn_entropy / max(len(idx_train), 1)
            # Maximize entropy by subtracting entropy regularizer in minimization objective.
            train_loss = train_loss - float(metapath_attention_entropy_reg_lambda) * train_attn_entropy

        optimizer.zero_grad()
        train_loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=2.0)
        optimizer.step()

        model.eval()
        with torch.no_grad():
            if len(idx_val) > 0:
                val_loss = torch.tensor(0.0, device=device)
                for t in idx_val:
                    pred_t = forward_one(t, delta_scale=1.0)  # type: ignore[assignment]
                    val_loss = val_loss + F.mse_loss(pred_t, labels[t])
                val_loss = val_loss / len(idx_val)
            else:
                val_loss = train_loss.detach().clone()

        train_value = float(train_loss.item())
        val_value = float(val_loss.item())
        history.append(
            {
                "epoch": float(ep),
                "train_mse": train_value,
                "val_mse": val_value,
                "warmup_scale": float(warmup_scale),
                "train_gate_reg": float(train_gate_reg.item()),
                "train_attn_entropy": float(train_attn_entropy.item()),
            }
        )

        if val_value + 1e-8 < best_val:
            best_val = val_value
            best_state = {k: v.detach().clone() for k, v in model.state_dict().items()}
            patience_count = 0
        else:
            patience_count += 1
            if patience_count >= patience:
                break

    if best_state is not None:
        model.load_state_dict(best_state)

    model.eval()
    pred_all = np.zeros_like(data.labels, dtype=float)
    attention_mean_arr: np.ndarray | None = None
    gate_mean_value: float | None = None
    with torch.no_grad():
        if metapath_enabled:
            attention_acc = np.zeros(len(data.metapath_names or []), dtype=float)
            gate_acc = 0.0
        for t in range(n_time):
            if metapath_enabled:
                pred_t, alpha_t, gate_t = forward_one(t, return_attention=True, delta_scale=1.0)  # type: ignore[assignment]
                assert alpha_t is not None
                assert gate_t is not None
                attention_acc += alpha_t.mean(dim=0).cpu().numpy()
                gate_acc += float(gate_t.mean().item())
            else:
                pred_t = forward_one(t, delta_scale=1.0)  # type: ignore[assignment]
            pred_all[t] = pred_t.cpu().numpy()
        if metapath_enabled:
            attention_mean_arr = attention_acc / max(n_time, 1)
            gate_mean_value = gate_acc / max(n_time, 1)
    pred_all = np.clip(pred_all, 0.0, 1.0)

    train_metrics = evaluate_prob_metrics(
        pred_all[idx_train],
        data.labels[idx_train],
        high_risk_threshold=float(high_risk_threshold),
        top_risk_quantile=float(top_risk_quantile),
    )
    val_metrics = (
        evaluate_prob_metrics(
            pred_all[idx_val],
            data.labels[idx_val],
            high_risk_threshold=float(high_risk_threshold),
            top_risk_quantile=float(top_risk_quantile),
        )
        if len(idx_val)
        else train_metrics
    )

    summary = {
        "epochs_requested": int(epochs),
        "epochs_effective": int(len(history)),
        "best_val_mse": float(best_val),
        "train_split_count": int(len(idx_train)),
        "val_split_count": int(len(idx_val)),
        "model_variant": "metapath_v1" if metapath_enabled else "baseline_gnn",
        "optimizer": {
            "lr": float(eff_lr),
            "weight_decay": float(eff_weight_decay),
        },
        "objective": {
            "risk_weight_active": bool(risk_weight_active),
            "risk_weight_alpha": float(risk_weight_alpha),
            "risk_weight_beta": float(risk_weight_beta),
            "risk_weight_threshold": float(np.clip(risk_weight_threshold, 0.0, 1.0)),
            "risk_weight_on_metapath_only": bool(risk_weight_on_metapath_only),
            "metapath_gate_reg_lambda": float(metapath_gate_reg_lambda if metapath_enabled else 0.0),
            "metapath_attention_entropy_reg_lambda": float(
                metapath_attention_entropy_reg_lambda if metapath_enabled else 0.0
            ),
            "metapath_warmup_epochs": int(warmup_epochs if metapath_enabled else 0),
            "metapath_attention_mode": str(metapath_attention_mode if metapath_enabled else "disabled"),
        },
        "evaluation_focus": {
            "high_risk_threshold": float(np.clip(high_risk_threshold, 0.0, 1.0)),
            "top_risk_quantile": float(np.clip(top_risk_quantile, 0.0, 1.0)),
        },
        "train_metrics": train_metrics,
        "val_metrics": val_metrics,
        "history": history,
    }
    if metapath_enabled and attention_mean_arr is not None and data.metapath_names is not None:
        summary["metapath_attention_mean"] = {
            name: float(attention_mean_arr[i]) for i, name in enumerate(data.metapath_names)
        }
        summary["metapath_topk"] = int(data.metapath_index.shape[2]) if data.metapath_index is not None else 0
        if gate_mean_value is not None:
            summary["metapath_gate_mean"] = float(gate_mean_value)
    return model, pred_all, summary


def classify_risk_level(p: float, high: float, medium: float) -> str:
    if p >= high:
        return "HIGH"
    if p >= medium:
        return "MEDIUM"
    return "LOW"


def build_line_risk_prediction(
    line_ids: list[str],
    hourly_prob_horizon: np.ndarray,
    high_threshold: float,
    medium_threshold: float,
    hour_trigger: float,
) -> pd.DataFrame:
    # Operational warning uses maximum hourly risk within horizon rather than
    # cumulative failure probability to avoid saturation over long horizons.
    risk_prob = np.max(hourly_prob_horizon, axis=0)
    base_levels = [classify_risk_level(float(np.clip(p, 0.0, 1.0)), high_threshold, medium_threshold) for p in risk_prob]
    need_quantile_fallback = len(set(base_levels)) < 3 and len(risk_prob) >= 3
    if need_quantile_fallback:
        q_low = float(np.quantile(risk_prob, 0.33))
        q_high = float(np.quantile(risk_prob, 0.67))

        def _fallback_level(pv: float) -> str:
            if pv >= q_high:
                return "HIGH"
            if pv >= q_low:
                return "MEDIUM"
            return "LOW"

        levels = [_fallback_level(float(p)) for p in risk_prob]
    else:
        levels = base_levels

    rows: list[dict[str, Any]] = []
    for i, lid in enumerate(line_ids):
        p = float(np.clip(risk_prob[i], 0.0, 1.0))
        level = levels[i]

        if level == "LOW":
            fail_hour: str | int = "-"
        else:
            weights = np.clip(hourly_prob_horizon[:, i], 1e-8, None)
            hour_idx = np.arange(1, len(weights) + 1, dtype=float)
            exp_hour = float(np.sum(hour_idx * weights) / np.sum(weights))
            trigger_idx = np.where(hourly_prob_horizon[:, i] >= hour_trigger)[0]
            if len(trigger_idx) == 0:
                fail_hour = int(round(exp_hour))
            else:
                # Blend first-trigger and expectation to avoid over-early prediction.
                fail_hour = int(round(0.4 * (trigger_idx[0] + 1) + 0.6 * exp_hour))
            fail_hour = max(1, min(fail_hour, len(weights)))

        rows.append(
            {
                "line_id": lid,
                "risk_prob": round(p, 6),
                "risk_level": level,
                "predicted_fail_hour": fail_hour,
            }
        )

    out = pd.DataFrame(rows).sort_values(by=["risk_prob", "line_id"], ascending=[False, True]).reset_index(drop=True)
    return out


def sample_outage_paths(
    prob_horizon: np.ndarray,
    n_samples: int,
    seed: int,
    intensity_alpha: float,
    intensity_beta: float,
) -> np.ndarray:
    rng = np.random.default_rng(seed)
    h, e = prob_horizon.shape
    hour_score = prob_horizon.mean(axis=1)
    if hour_score.sum() <= 1e-12:
        hour_weight = np.full(h, 1.0 / h, dtype=float)
    else:
        hour_weight = hour_score / hour_score.sum()
    sampled_hour = rng.choice(np.arange(h), size=n_samples, replace=True, p=hour_weight)
    sampled_prob = prob_horizon[sampled_hour, :]  # [S,E]
    # Scenario intensity reflects uncertainty in disturbance severity.
    alpha = max(float(intensity_alpha), 0.1)
    beta = max(float(intensity_beta), 0.1)
    intensity = rng.beta(alpha, beta, size=n_samples)[:, None]
    sampled_prob = np.clip(sampled_prob * intensity, 0.0, 0.95)
    draws = rng.random((n_samples, e))
    fail_snapshot = (draws < sampled_prob).astype(np.int8)
    return fail_snapshot


def build_nk_failure_risk(outage_paths: np.ndarray) -> pd.DataFrame:
    fail_count = outage_paths.sum(axis=1)
    binc = np.bincount(fail_count.astype(int), minlength=int(fail_count.max()) + 1)
    prob = binc / max(int(len(fail_count)), 1)

    rows: list[dict[str, Any]] = []
    nonzero_k = np.where(prob > 0)[0]
    sorted_k = sorted(nonzero_k, key=lambda k: prob[k], reverse=True)
    for i, k in enumerate(sorted_k):
        rows.append(
            {
                "scenario": f"S{i + 1}",
                "expected_fail_lines": int(k),
                "probability": round(float(prob[k]), 6),
            }
        )
    return pd.DataFrame(rows)


def compute_critical_load_risk(
    outage_paths: np.ndarray,
    node_ids: list[int],
    line_from: np.ndarray,
    line_to: np.ndarray,
    load_buses: list[int],
    source_buses: list[int],
    load_type_map: dict[int, str],
) -> pd.DataFrame:
    n_s, n_l = outage_paths.shape
    critical_loads = [b for b in load_buses if load_type_map.get(b, "secondary") in {"primary", "secondary"}]
    critical_loads = sorted(critical_loads)

    disconnected_any = np.zeros((n_s, len(critical_loads)), dtype=bool)
    for s in range(n_s):
        g = nx.Graph()
        g.add_nodes_from(node_ids)
        alive = outage_paths[s, :] == 0
        for i in range(n_l):
            if alive[i]:
                g.add_edge(int(line_from[i]), int(line_to[i]))

        reachable: set[int] = set()
        for src in source_buses:
            if src in g:
                reachable.update(nx.node_connected_component(g, src))

        for j, b in enumerate(critical_loads):
            if b not in reachable:
                disconnected_any[s, j] = True

    outage_prob = disconnected_any.mean(axis=0)

    rows = []
    for j, bus in enumerate(critical_loads):
        ltype = load_type_map.get(bus, "secondary")
        rows.append(
            {
                "node": f"load_bus_{bus}",
                "load_type": ltype,
                "outage_prob": round(float(outage_prob[j]), 6),
            }
        )
    return pd.DataFrame(rows).sort_values(by=["outage_prob", "node"], ascending=[False, True]).reset_index(drop=True)


def export_node_weather_artifacts(
    dataset: WarningDataset,
    output_dir: Path,
    t0: int,
    t1: int,
) -> dict[str, str]:
    weather = dataset.node_weather
    if weather is None:
        return {}

    required_keys = [
        "influence",
        "wind_factor",
        "pv_factor",
        "load_factor",
        "wind_speed_factor",
        "wind_raw",
        "pv_raw",
        "load_raw",
        "wind_speed_raw",
    ]
    if any(k not in weather for k in required_keys):
        return {}

    n_time = len(dataset.timestamps)
    n_node = len(dataset.node_ids)
    if n_time <= 0 or n_node <= 0:
        return {}

    index_time = np.repeat(dataset.timestamps.astype(str).to_numpy(), n_node)
    index_node = np.tile(np.asarray(dataset.node_ids, dtype=int), n_time)

    base_df = pd.DataFrame(
        {
            "timestamp": index_time,
            "node_id": index_node,
            "influence": np.asarray(weather["influence"], dtype=float).reshape(-1),
            "wind_factor": np.asarray(weather["wind_factor"], dtype=float).reshape(-1),
            "pv_factor": np.asarray(weather["pv_factor"], dtype=float).reshape(-1),
            "load_factor": np.asarray(weather["load_factor"], dtype=float).reshape(-1),
            "wind_speed_factor": np.asarray(weather["wind_speed_factor"], dtype=float).reshape(-1),
            "wind_raw": np.asarray(weather["wind_raw"], dtype=float).reshape(-1),
            "pv_raw": np.asarray(weather["pv_raw"], dtype=float).reshape(-1),
            "load_raw": np.asarray(weather["load_raw"], dtype=float).reshape(-1),
            "wind_speed_raw": np.asarray(weather["wind_speed_raw"], dtype=float).reshape(-1),
        }
    )

    full_path = output_dir / "node_weather_timeseries.csv"
    base_df.to_csv(full_path, index=False, encoding="utf-8")

    t0 = int(np.clip(t0, 0, n_time))
    t1 = int(np.clip(t1, t0, n_time))
    horizon_ts = set(dataset.timestamps[t0:t1].astype(str).tolist())
    horizon_df = base_df[base_df["timestamp"].isin(horizon_ts)].copy()
    horizon_path = output_dir / "node_weather_horizon.csv"
    horizon_df.to_csv(horizon_path, index=False, encoding="utf-8")

    summary_df = (
        base_df.groupby("node_id", as_index=False)
        .agg(
            mean_influence=("influence", "mean"),
            mean_wind_factor=("wind_factor", "mean"),
            mean_pv_factor=("pv_factor", "mean"),
            mean_load_factor=("load_factor", "mean"),
            mean_wind_speed_factor=("wind_speed_factor", "mean"),
            mean_wind_raw=("wind_raw", "mean"),
            mean_pv_raw=("pv_raw", "mean"),
            mean_load_raw=("load_raw", "mean"),
            mean_wind_speed_raw=("wind_speed_raw", "mean"),
        )
        .sort_values("mean_influence", ascending=False)
        .reset_index(drop=True)
    )
    summary_path = output_dir / "node_weather_summary.csv"
    summary_df.to_csv(summary_path, index=False, encoding="utf-8")

    return {
        "node_weather_timeseries_csv": str(full_path),
        "node_weather_horizon_csv": str(horizon_path),
        "node_weather_summary_csv": str(summary_path),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="GNN-inspired early warning module for line risk, N-k risk, and critical load outage risk."
    )
    parser.add_argument(
        "--grid",
        default="data_final/formal_guangdong_2024/grid_topology.json",
        help="Grid topology json path.",
    )
    parser.add_argument(
        "--aligned",
        default="data_final/formal_guangdong_2024/aligned_merged.csv",
        help="Aligned wind/pv/load time-series csv path.",
    )
    parser.add_argument(
        "--failure-csv",
        default="results/component_failure_probability/formal2024/line_failure_timeseries_schloemer.csv",
        help="Line failure timeseries csv.",
    )
    parser.add_argument(
        "--contingency-tensor",
        default="results/spatiotemporal_contingency/formal2024_schloemer72h/contingency_tensor_wang_qmc.npy",
        help="Contingency tensor npy for supervision labels.",
    )
    parser.add_argument(
        "--load-priority-csv",
        default="results/load_prioritization_scheduling/formal2024/load_bus_priority_profile.csv",
        help="Optional load priority profile csv.",
    )
    parser.add_argument(
        "--output-dir",
        default="results/early_warning/formal2024",
        help="Output directory.",
    )
    parser.add_argument("--horizon-hours", type=int, default=24, help="Warning horizon in hours.")
    parser.add_argument("--horizon-start-index", type=int, default=0, help="Start index in timeline for warning horizon.")
    parser.add_argument("--train-ratio", type=float, default=0.7, help="Training split ratio in time axis.")
    parser.add_argument("--hidden-dim", type=int, default=64, help="Hidden dimension for GNN.")
    parser.add_argument("--epochs", type=int, default=600, help="Max training epochs.")
    parser.add_argument("--lr", type=float, default=1e-2, help="Learning rate.")
    parser.add_argument("--weight-decay", type=float, default=1e-4, help="Weight decay.")
    parser.add_argument("--mc-scenarios", type=int, default=3000, help="Monte Carlo scenario count for warning risk outputs.")
    parser.add_argument("--risk-high-threshold", type=float, default=0.70, help="High risk threshold for line risk level.")
    parser.add_argument("--risk-medium-threshold", type=float, default=0.40, help="Medium risk threshold for line risk level.")
    parser.add_argument("--hour-trigger-threshold", type=float, default=0.35, help="Per-hour trigger threshold for predicted fail hour.")
    parser.add_argument(
        "--risk-mean-floor",
        type=float,
        default=0.18,
        help="Lower bound of calibrated hourly risk mean.",
    )
    parser.add_argument(
        "--risk-mean-cap",
        type=float,
        default=0.55,
        help="Upper bound of calibrated hourly risk mean.",
    )
    parser.add_argument(
        "--scenario-intensity-alpha",
        type=float,
        default=2.0,
        help="Alpha of Beta distribution for scenario disturbance intensity.",
    )
    parser.add_argument(
        "--scenario-intensity-beta",
        type=float,
        default=6.0,
        help="Beta of Beta distribution for scenario disturbance intensity.",
    )
    parser.add_argument(
        "--metapath-topk",
        type=int,
        default=6,
        help="Top-k neighbors kept for each fixed metapath in V1.",
    )
    parser.add_argument(
        "--metapath-v1-enabled",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Enable fixed-metapath semantic-attention V1 model.",
    )
    parser.add_argument(
        "--metapath-attention-mode",
        type=str,
        choices=["fixed", "adaptive_global", "adaptive_context"],
        default="fixed",
        help="Semantic-attention mode for MetaPath branch.",
    )
    parser.add_argument(
        "--run-baseline-comparison",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Run an additional baseline model and export comparison files.",
    )
    parser.add_argument(
        "--risk-weight-alpha",
        type=float,
        default=2.0,
        help="Continuous risk weight coefficient in weighted MSE objective.",
    )
    parser.add_argument(
        "--risk-weight-beta",
        type=float,
        default=4.0,
        help="Step risk weight coefficient for labels >= risk-weight-threshold.",
    )
    parser.add_argument(
        "--risk-weight-threshold",
        type=float,
        default=0.10,
        help="Threshold used by risk-weight-beta indicator term.",
    )
    parser.add_argument(
        "--risk-weight-on-metapath-only",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Apply risk-weighted loss only to MetaPath model when baseline comparison is enabled.",
    )
    parser.add_argument(
        "--metapath-gate-reg-lambda",
        type=float,
        default=8e-4,
        help="L2 regularization coefficient on MetaPath gate to avoid over-correction.",
    )
    parser.add_argument(
        "--metapath-attention-entropy-reg-lambda",
        type=float,
        default=0.0,
        help="Entropy regularization coefficient on MetaPath attention to mitigate single-path collapse.",
    )
    parser.add_argument(
        "--metapath-warmup-epochs",
        type=int,
        default=35,
        help="Epochs for linear warmup of MetaPath residual correction.",
    )
    parser.add_argument(
        "--high-risk-threshold",
        type=float,
        default=0.10,
        help="Threshold used to compute high-risk subset metrics.",
    )
    parser.add_argument(
        "--top-risk-quantile",
        type=float,
        default=0.90,
        help="Quantile used for top-risk subset metrics.",
    )
    parser.add_argument("--seed", type=int, default=42, help="Random seed.")
    return parser.parse_args()


def calibrate_hourly_probability(
    pred_horizon: np.ndarray,
    p_line_horizon: np.ndarray,
    v_surface_horizon: np.ndarray,
    mean_floor: float,
    mean_cap: float,
) -> np.ndarray:
    pred_s = minmax_scale_global(pred_horizon)
    p_s = minmax_scale_global(p_line_horizon)
    v_s = minmax_scale_global(v_surface_horizon)

    fused = 0.45 * pred_s + 0.35 * p_s + 0.20 * v_s
    base = 0.02 + 0.70 * fused

    target_mean = np.clip(
        float(np.mean(pred_horizon)) * 0.35 + 0.20,
        max(mean_floor, 0.05),
        min(mean_cap, 0.90),
    )
    scale = target_mean / max(float(base.mean()), 1e-6)
    calibrated = np.clip(base * scale, 0.02, 0.85)
    return calibrated


def run_warning_variant(
    data: WarningDataset,
    hidden_dim: int,
    epochs: int,
    lr: float,
    weight_decay: float,
    train_ratio: float,
    seed: int,
    use_metapath_v1: bool,
    t0: int,
    t1: int,
    p_line: np.ndarray,
    v_surface: np.ndarray,
    risk_mean_floor: float,
    risk_mean_cap: float,
    risk_high_threshold: float,
    risk_medium_threshold: float,
    hour_trigger_threshold: float,
    risk_weight_alpha: float,
    risk_weight_beta: float,
    risk_weight_threshold: float,
    risk_weight_on_metapath_only: bool,
    metapath_gate_reg_lambda: float,
    metapath_attention_entropy_reg_lambda: float,
    metapath_warmup_epochs: int,
    metapath_attention_mode: str,
    high_risk_threshold: float,
    top_risk_quantile: float,
) -> dict[str, Any]:
    _, pred_all, train_summary = train_gnn(
        data=data,
        hidden_dim=hidden_dim,
        epochs=epochs,
        lr=lr,
        weight_decay=weight_decay,
        train_ratio=train_ratio,
        seed=seed,
        use_metapath_v1=use_metapath_v1,
        risk_weight_alpha=float(risk_weight_alpha),
        risk_weight_beta=float(risk_weight_beta),
        risk_weight_threshold=float(risk_weight_threshold),
        risk_weight_on_metapath_only=bool(risk_weight_on_metapath_only),
        metapath_gate_reg_lambda=float(metapath_gate_reg_lambda),
        metapath_attention_entropy_reg_lambda=float(metapath_attention_entropy_reg_lambda),
        metapath_warmup_epochs=int(metapath_warmup_epochs),
        metapath_attention_mode=str(metapath_attention_mode),
        high_risk_threshold=float(high_risk_threshold),
        top_risk_quantile=float(top_risk_quantile),
    )

    pred_horizon = pred_all[t0:t1, :]
    p_line_horizon = p_line[t0:t1, :]
    v_surface_horizon = v_surface[t0:t1, :]
    calibrated_prob = calibrate_hourly_probability(
        pred_horizon=pred_horizon,
        p_line_horizon=p_line_horizon,
        v_surface_horizon=v_surface_horizon,
        mean_floor=float(risk_mean_floor),
        mean_cap=float(risk_mean_cap),
    )

    line_risk_df = build_line_risk_prediction(
        line_ids=data.line_ids,
        hourly_prob_horizon=calibrated_prob,
        high_threshold=float(risk_high_threshold),
        medium_threshold=float(risk_medium_threshold),
        hour_trigger=float(hour_trigger_threshold),
    )

    train_idx = int(max(1, min(int(np.floor(len(data.timestamps) * train_ratio)), len(data.timestamps) - 1)))
    train_metrics = evaluate_prob_metrics(
        pred_all[:train_idx],
        data.labels[:train_idx],
        high_risk_threshold=float(high_risk_threshold),
        top_risk_quantile=float(top_risk_quantile),
    )
    val_metrics = evaluate_prob_metrics(
        pred_all[train_idx:],
        data.labels[train_idx:],
        high_risk_threshold=float(high_risk_threshold),
        top_risk_quantile=float(top_risk_quantile),
    )
    horizon_metrics = (
        evaluate_prob_metrics(
            pred_horizon,
            data.labels[t0:t1],
            high_risk_threshold=float(high_risk_threshold),
            top_risk_quantile=float(top_risk_quantile),
        )
        if t1 > t0
        else val_metrics
    )

    return {
        "pred_all": pred_all,
        "pred_horizon": pred_horizon,
        "calibrated_prob": calibrated_prob,
        "line_risk_df": line_risk_df,
        "train_summary": train_summary,
        "train_metrics": train_metrics,
        "val_metrics": val_metrics,
        "horizon_metrics": horizon_metrics,
    }


def main() -> None:
    args = parse_args()
    root = project_root()

    grid_path = (root / args.grid).resolve()
    aligned_path = (root / args.aligned).resolve()
    failure_csv = (root / args.failure_csv).resolve()
    contingency_tensor = (root / args.contingency_tensor).resolve()
    priority_csv = (root / args.load_priority_csv).resolve() if args.load_priority_csv else None
    output_dir = (root / args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    grid_payload = load_grid_topology(grid_path)
    timestamps, line_ids, p_line, v_surface, edge_map = load_failure_features(failure_csv)
    labels = load_contingency_labels(contingency_tensor, expected_t=len(timestamps), expected_e=len(line_ids))

    dataset = build_dataset(
        grid_payload=grid_payload,
        timestamps=timestamps,
        line_ids=line_ids,
        edge_map=edge_map,
        p_line=p_line,
        v_surface=v_surface,
        labels=labels,
        aligned_csv=aligned_path,
        priority_csv=priority_csv,
        metapath_topk=max(int(args.metapath_topk), 1),
    )

    # warning horizon slice
    t0 = int(np.clip(args.horizon_start_index, 0, len(dataset.timestamps) - 1))
    t1 = int(min(t0 + max(args.horizon_hours, 1), len(dataset.timestamps)))
    ts_horizon = dataset.timestamps[t0:t1]

    primary_variant = run_warning_variant(
        data=dataset,
        hidden_dim=int(args.hidden_dim),
        epochs=int(args.epochs),
        lr=float(args.lr),
        weight_decay=float(args.weight_decay),
        train_ratio=float(args.train_ratio),
        seed=int(args.seed),
        use_metapath_v1=bool(args.metapath_v1_enabled),
        t0=t0,
        t1=t1,
        p_line=p_line,
        v_surface=v_surface,
        risk_mean_floor=float(args.risk_mean_floor),
        risk_mean_cap=float(args.risk_mean_cap),
        risk_high_threshold=float(args.risk_high_threshold),
        risk_medium_threshold=float(args.risk_medium_threshold),
        hour_trigger_threshold=float(args.hour_trigger_threshold),
        risk_weight_alpha=float(args.risk_weight_alpha),
        risk_weight_beta=float(args.risk_weight_beta),
        risk_weight_threshold=float(args.risk_weight_threshold),
        risk_weight_on_metapath_only=bool(args.risk_weight_on_metapath_only),
        metapath_gate_reg_lambda=float(args.metapath_gate_reg_lambda),
        metapath_attention_entropy_reg_lambda=float(args.metapath_attention_entropy_reg_lambda),
        metapath_warmup_epochs=int(args.metapath_warmup_epochs),
        metapath_attention_mode=str(args.metapath_attention_mode),
        high_risk_threshold=float(args.high_risk_threshold),
        top_risk_quantile=float(args.top_risk_quantile),
    )
    pred_all = primary_variant["pred_all"]
    calibrated_prob = primary_variant["calibrated_prob"]
    line_risk_df = primary_variant["line_risk_df"]
    train_summary = primary_variant["train_summary"]

    outage_paths = sample_outage_paths(
        prob_horizon=calibrated_prob,
        n_samples=int(args.mc_scenarios),
        seed=int(args.seed + 1000),
        intensity_alpha=float(args.scenario_intensity_alpha),
        intensity_beta=float(args.scenario_intensity_beta),
    )

    nk_df = build_nk_failure_risk(outage_paths=outage_paths)
    critical_df = compute_critical_load_risk(
        outage_paths=outage_paths,
        node_ids=dataset.node_ids,
        line_from=dataset.from_bus,
        line_to=dataset.to_bus,
        load_buses=dataset.load_buses,
        source_buses=dataset.source_buses,
        load_type_map=dataset.load_type_map,
    )

    line_path = output_dir / "line_risk_prediction.csv"
    nk_path = output_dir / "nk_failure_risk.csv"
    critical_path = output_dir / "critical_load_risk.csv"
    calibrated_path = output_dir / "calibrated_hourly_line_probability.csv"

    line_risk_df.to_csv(line_path, index=False, encoding="utf-8")
    nk_df.to_csv(nk_path, index=False, encoding="utf-8")
    critical_df.to_csv(critical_path, index=False, encoding="utf-8")
    pd.DataFrame(
        calibrated_prob,
        index=pd.Index(ts_horizon.astype(str), name="timestamp"),
        columns=dataset.line_ids,
    ).reset_index().to_csv(calibrated_path, index=False, encoding="utf-8")
    weather_outputs = export_node_weather_artifacts(
        dataset=dataset,
        output_dir=output_dir,
        t0=t0,
        t1=t1,
    )

    train_metrics = primary_variant["train_metrics"]
    val_metrics = primary_variant["val_metrics"]

    comparison_outputs: dict[str, Any] = {}
    if bool(args.run_baseline_comparison):
        compare_use_metapath = False if bool(args.metapath_v1_enabled) else True
        compare_label = "baseline_gnn" if not compare_use_metapath else "metapath_v1"
        primary_label = "metapath_v1" if bool(args.metapath_v1_enabled) else "baseline_gnn"

        baseline_variant = run_warning_variant(
            data=dataset,
            hidden_dim=int(args.hidden_dim),
            epochs=int(args.epochs),
            lr=float(args.lr),
            weight_decay=float(args.weight_decay),
            train_ratio=float(args.train_ratio),
            seed=int(args.seed),
            use_metapath_v1=compare_use_metapath,
            t0=t0,
            t1=t1,
            p_line=p_line,
            v_surface=v_surface,
            risk_mean_floor=float(args.risk_mean_floor),
            risk_mean_cap=float(args.risk_mean_cap),
            risk_high_threshold=float(args.risk_high_threshold),
            risk_medium_threshold=float(args.risk_medium_threshold),
            hour_trigger_threshold=float(args.hour_trigger_threshold),
            risk_weight_alpha=float(args.risk_weight_alpha),
            risk_weight_beta=float(args.risk_weight_beta),
            risk_weight_threshold=float(args.risk_weight_threshold),
            risk_weight_on_metapath_only=bool(args.risk_weight_on_metapath_only),
            metapath_gate_reg_lambda=float(args.metapath_gate_reg_lambda),
            metapath_attention_entropy_reg_lambda=float(args.metapath_attention_entropy_reg_lambda),
            metapath_warmup_epochs=int(args.metapath_warmup_epochs),
            metapath_attention_mode=str(args.metapath_attention_mode),
            high_risk_threshold=float(args.high_risk_threshold),
            top_risk_quantile=float(args.top_risk_quantile),
        )

        compare_prefix = "baseline" if compare_label == "baseline_gnn" else "metapath_v1_compare"
        baseline_line_path = output_dir / f"{compare_prefix}_line_risk_prediction.csv"
        baseline_calibrated_path = output_dir / f"{compare_prefix}_calibrated_hourly_line_probability.csv"
        baseline_variant["line_risk_df"].to_csv(baseline_line_path, index=False, encoding="utf-8")
        pd.DataFrame(
            baseline_variant["calibrated_prob"],
            index=pd.Index(ts_horizon.astype(str), name="timestamp"),
            columns=dataset.line_ids,
        ).reset_index().to_csv(baseline_calibrated_path, index=False, encoding="utf-8")

        comparison_rows = [
            {
                "model": primary_label,
                "train_mae": float(primary_variant["train_metrics"]["mae"]),
                "train_rmse": float(primary_variant["train_metrics"]["rmse"]),
                "val_mae": float(primary_variant["val_metrics"]["mae"]),
                "val_rmse": float(primary_variant["val_metrics"]["rmse"]),
                "horizon_mae": float(primary_variant["horizon_metrics"]["mae"]),
                "horizon_rmse": float(primary_variant["horizon_metrics"]["rmse"]),
                "val_high_risk_mae": float(primary_variant["val_metrics"].get("high_risk_mae", float("nan"))),
                "val_top_risk_mae": float(primary_variant["val_metrics"].get("top_risk_mae", float("nan"))),
                "horizon_high_risk_mae": float(primary_variant["horizon_metrics"].get("high_risk_mae", float("nan"))),
                "horizon_top_risk_mae": float(primary_variant["horizon_metrics"].get("top_risk_mae", float("nan"))),
                "best_val_mse": float(primary_variant["train_summary"]["best_val_mse"]),
            },
            {
                "model": compare_label,
                "train_mae": float(baseline_variant["train_metrics"]["mae"]),
                "train_rmse": float(baseline_variant["train_metrics"]["rmse"]),
                "val_mae": float(baseline_variant["val_metrics"]["mae"]),
                "val_rmse": float(baseline_variant["val_metrics"]["rmse"]),
                "horizon_mae": float(baseline_variant["horizon_metrics"]["mae"]),
                "horizon_rmse": float(baseline_variant["horizon_metrics"]["rmse"]),
                "val_high_risk_mae": float(baseline_variant["val_metrics"].get("high_risk_mae", float("nan"))),
                "val_top_risk_mae": float(baseline_variant["val_metrics"].get("top_risk_mae", float("nan"))),
                "horizon_high_risk_mae": float(baseline_variant["horizon_metrics"].get("high_risk_mae", float("nan"))),
                "horizon_top_risk_mae": float(baseline_variant["horizon_metrics"].get("top_risk_mae", float("nan"))),
                "best_val_mse": float(baseline_variant["train_summary"]["best_val_mse"]),
            },
        ]
        comparison_df = pd.DataFrame(comparison_rows)
        comparison_csv = output_dir / "model_comparison.csv"
        comparison_df.to_csv(comparison_csv, index=False, encoding="utf-8")

        winner_by_metric: dict[str, str] = {}
        for metric in [
            "val_mae",
            "horizon_mae",
            "val_high_risk_mae",
            "horizon_high_risk_mae",
            "val_top_risk_mae",
            "horizon_top_risk_mae",
            "best_val_mse",
        ]:
            if metric not in comparison_df.columns:
                continue
            metric_series = pd.to_numeric(comparison_df[metric], errors="coerce")
            valid = comparison_df.loc[metric_series.notna(), ["model", metric]].copy()
            if valid.empty:
                continue
            winner_by_metric[metric] = str(valid.sort_values(metric, ascending=True).iloc[0]["model"])

        comparison_outputs = {
            "enabled": True,
            "comparison_csv": str(comparison_csv),
            "comparison_model_line_risk_prediction_csv": str(baseline_line_path),
            "comparison_model_calibrated_hourly_line_probability_csv": str(baseline_calibrated_path),
            "comparison_model_training": baseline_variant["train_summary"],
            "winner_by_metric": winner_by_metric,
        }

    attention_summary_path: Path | None = None
    if isinstance(train_summary, dict) and "metapath_attention_mean" in train_summary:
        attn_items = train_summary.get("metapath_attention_mean", {})
        if isinstance(attn_items, dict) and attn_items:
            attention_summary_path = output_dir / "metapath_attention_summary.csv"
            pd.DataFrame(
                [{"metapath": str(k), "attention_weight": float(v)} for k, v in attn_items.items()]
            ).sort_values("attention_weight", ascending=False).to_csv(
                attention_summary_path, index=False, encoding="utf-8"
            )

    report = {
        "module": "GNN Early Warning",
        "inputs": {
            "grid": str(grid_path),
            "aligned": str(aligned_path),
            "failure_csv": str(failure_csv),
            "contingency_tensor": str(contingency_tensor),
            "load_priority_csv": str(priority_csv) if priority_csv is not None else None,
        },
        "horizon": {
            "start_index": int(t0),
            "end_index_exclusive": int(t1),
            "start_timestamp": str(ts_horizon.min()) if len(ts_horizon) else None,
            "end_timestamp": str(ts_horizon.max()) if len(ts_horizon) else None,
            "hours": int(len(ts_horizon)),
        },
        "training": train_summary,
        "fit_quality": {
            "train": train_metrics,
            "validation": val_metrics,
        },
        "node_weather_generation": dataset.node_weather_meta or {},
        "modeling": {
            "metapath_v1_enabled": bool(args.metapath_v1_enabled),
            "metapath_attention_mode": str(args.metapath_attention_mode),
            "metapath_topk": int(max(args.metapath_topk, 1)),
            "run_baseline_comparison": bool(args.run_baseline_comparison),
            "risk_weight_alpha": float(args.risk_weight_alpha),
            "risk_weight_beta": float(args.risk_weight_beta),
            "risk_weight_threshold": float(args.risk_weight_threshold),
            "risk_weight_on_metapath_only": bool(args.risk_weight_on_metapath_only),
            "metapath_gate_reg_lambda": float(args.metapath_gate_reg_lambda),
            "metapath_attention_entropy_reg_lambda": float(args.metapath_attention_entropy_reg_lambda),
            "metapath_warmup_epochs": int(args.metapath_warmup_epochs),
            "high_risk_threshold": float(args.high_risk_threshold),
            "top_risk_quantile": float(args.top_risk_quantile),
        },
        "risk_thresholds": {
            "high": float(args.risk_high_threshold),
            "medium": float(args.risk_medium_threshold),
            "hour_trigger": float(args.hour_trigger_threshold),
        },
        "calibration": {
            "risk_mean_floor": float(args.risk_mean_floor),
            "risk_mean_cap": float(args.risk_mean_cap),
            "calibrated_hourly_risk_mean": float(calibrated_prob.mean()),
            "calibrated_hourly_risk_min": float(calibrated_prob.min()),
            "calibrated_hourly_risk_max": float(calibrated_prob.max()),
        },
        "scenario_sampling": {
            "intensity_distribution": "Beta(alpha,beta)",
            "alpha": float(args.scenario_intensity_alpha),
            "beta": float(args.scenario_intensity_beta),
        },
        "mc_scenarios": int(args.mc_scenarios),
        "outputs": {
            "line_risk_prediction_csv": str(line_path),
            "nk_failure_risk_csv": str(nk_path),
            "critical_load_risk_csv": str(critical_path),
            "calibrated_hourly_line_probability_csv": str(calibrated_path),
        },
    }
    if weather_outputs:
        report["outputs"].update(weather_outputs)
    if attention_summary_path is not None:
        report["outputs"]["metapath_attention_summary_csv"] = str(attention_summary_path)
    if comparison_outputs:
        report["comparison"] = comparison_outputs

    report_path = output_dir / "warning_report.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    print("Done.")
    print(f"line risk -> {line_path}")
    print(f"N-k risk  -> {nk_path}")
    print(f"critical  -> {critical_path}")
    print(f"report    -> {report_path}")


if __name__ == "__main__":
    main()
