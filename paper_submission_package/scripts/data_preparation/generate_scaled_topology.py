from __future__ import annotations

import argparse
import json
import math
from collections import Counter
from pathlib import Path
from typing import Any


def project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"missing json: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def dump_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def line_degree(lines: list[dict[str, Any]]) -> Counter[int]:
    deg: Counter[int] = Counter()
    for ln in lines:
        u = int(ln["from"])
        v = int(ln["to"])
        deg[u] += 1
        deg[v] += 1
    return deg


def length_km_from_geo(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    mean_lat = math.radians((lat1 + lat2) / 2.0)
    dy = (lat2 - lat1) * 111.0
    dx = (lon2 - lon1) * 111.0 * math.cos(mean_lat)
    return float(max(math.hypot(dx, dy), 1.0))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate scaled grid topology by tiling the base topology.")
    parser.add_argument("--base-grid", default="data_final/formal_guangdong_2024/grid_topology.json")
    parser.add_argument("--output-grid", default="data_final/scaled/g60_n75/grid_topology.json")
    parser.add_argument("--tile-rows", type=int, default=2)
    parser.add_argument("--tile-cols", type=int, default=2)
    parser.add_argument("--target-lines", type=int, default=75, help="Total line count after adding tie lines.")
    parser.add_argument("--lat-gap", type=float, default=0.16, help="Latitude gap between tiled blocks.")
    parser.add_argument("--lon-gap", type=float, default=0.16, help="Longitude gap between tiled blocks.")
    parser.add_argument("--local-x-gap", type=float, default=25.0)
    parser.add_argument("--local-y-gap", type=float, default=25.0)
    parser.add_argument("--seed-offset", type=int, default=1000, help="Only used for deterministic id spaces.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    root = project_root()
    base_path = (root / args.base_grid).resolve()
    out_path = (root / args.output_grid).resolve()
    base = load_json(base_path)

    base_nodes = list(base.get("nodes", []))
    base_lines = list(base.get("lines", []))
    base_gens = list(base.get("generators", []))
    if not base_nodes or not base_lines:
        raise ValueError("base grid has no nodes/lines")

    rows = int(max(args.tile_rows, 1))
    cols = int(max(args.tile_cols, 1))
    n_blocks = rows * cols
    if n_blocks < 1:
        raise ValueError("invalid tile settings")

    base_node_ids = sorted(int(n["id"]) for n in base_nodes)
    base_id_to_node = {int(n["id"]): n for n in base_nodes}
    n_base_nodes = len(base_node_ids)
    n_base_lines = len(base_lines)
    n_base_gens = len(base_gens)

    # Build deterministic node id mapping per block.
    block_node_id: dict[tuple[int, int], int] = {}
    all_nodes: list[dict[str, Any]] = []
    all_lines: list[dict[str, Any]] = []
    all_gens: list[dict[str, Any]] = []

    deg = line_degree(base_lines)
    connector_template = [nid for nid, _ in sorted(deg.items(), key=lambda x: (-x[1], x[0]))]
    if not connector_template:
        connector_template = base_node_ids[:]
    if len(connector_template) < 5:
        connector_template = (connector_template * 5)[:5]

    base_capacities = [float(ln.get("capacity", 5.0) or 5.0) for ln in base_lines]
    cap_mean = float(sum(base_capacities) / max(len(base_capacities), 1))

    # Tile nodes.
    for r in range(rows):
        for c in range(cols):
            b = r * cols + c
            id_offset = b * n_base_nodes
            lat_off = r * float(args.lat_gap)
            lon_off = c * float(args.lon_gap)
            x_off = c * float(args.local_x_gap)
            y_off = r * float(args.local_y_gap)

            for nid in base_node_ids:
                src = base_id_to_node[nid]
                new_id = id_offset + nid
                block_node_id[(b, nid)] = new_id
                out = dict(src)
                out["id"] = int(new_id)
                if "lat" in out:
                    out["lat"] = float(out["lat"]) + lat_off
                if "lon" in out:
                    out["lon"] = float(out["lon"]) + lon_off
                if "local_x" in out:
                    out["local_x"] = float(out["local_x"]) + x_off
                if "local_y" in out:
                    out["local_y"] = float(out["local_y"]) + y_off
                all_nodes.append(out)

    # Tile generators.
    for r in range(rows):
        for c in range(cols):
            b = r * cols + c
            node_offset = b * n_base_nodes
            gen_offset = b * max(n_base_gens, 1)
            for gi, g in enumerate(base_gens):
                out = dict(g)
                out["id"] = f"{str(g.get('id', 'G'))}_b{b}_{gi + args.seed_offset}"
                out["bus"] = int(node_offset + int(g.get("bus", 0)))
                all_gens.append(out)

    # Tile intra-block lines and rewrite geometry from current node coordinates.
    line_counter = 0
    node_geo = {int(n["id"]): (float(n.get("lat", 0.0)), float(n.get("lon", 0.0))) for n in all_nodes}
    used_pairs: set[tuple[int, int]] = set()

    def add_line(u: int, v: int, capacity: float, length_km: float | None = None) -> bool:
        nonlocal line_counter
        if u == v:
            return False
        a, b = (u, v) if u < v else (v, u)
        key = (a, b)
        if key in used_pairs:
            return False
        used_pairs.add(key)

        lat1, lon1 = node_geo[u]
        lat2, lon2 = node_geo[v]
        if length_km is None:
            length_km = length_km_from_geo(lat1=lat1, lon1=lon1, lat2=lat2, lon2=lon2)
        ln = {
            "id": f"L{line_counter}",
            "from": int(u),
            "to": int(v),
            "capacity": float(max(capacity, 0.5)),
            "length_km": float(max(length_km, 0.5)),
            "from_lat": float(lat1),
            "from_lon": float(lon1),
            "to_lat": float(lat2),
            "to_lon": float(lon2),
            "mid_lat": float((lat1 + lat2) / 2.0),
            "mid_lon": float((lon1 + lon2) / 2.0),
        }
        all_lines.append(ln)
        line_counter += 1
        return True

    for r in range(rows):
        for c in range(cols):
            b = r * cols + c
            node_offset = b * n_base_nodes
            for ln in base_lines:
                u_old = int(ln["from"])
                v_old = int(ln["to"])
                u = int(node_offset + u_old)
                v = int(node_offset + v_old)
                add_line(
                    u=u,
                    v=v,
                    capacity=float(ln.get("capacity", cap_mean) or cap_mean),
                    length_km=float(max(float(ln.get("length_km", 1.0) or 1.0), 0.5)),
                )

    # Connect base-isolated buses in each block so the expanded grid is structurally complete.
    isolated_base_nodes = [nid for nid in base_node_ids if deg.get(nid, 0) == 0]
    if isolated_base_nodes:
        anchor_template = connector_template[0]
        for r in range(rows):
            for c in range(cols):
                b = r * cols + c
                for nid in isolated_base_nodes:
                    u = block_node_id[(b, nid)]
                    v = block_node_id[(b, anchor_template)]
                    add_line(u=u, v=v, capacity=cap_mean * 0.95)

    target_lines = int(max(args.target_lines, len(all_lines)))
    need_ties = target_lines - len(all_lines)

    # Build adjacent block pairs in grid (right/down).
    adjacency: list[tuple[int, int]] = []
    for r in range(rows):
        for c in range(cols):
            b = r * cols + c
            if c + 1 < cols:
                adjacency.append((b, b + 1))
            if r + 1 < rows:
                adjacency.append((b, b + cols))
    if not adjacency and need_ties > 0:
        raise ValueError("cannot add tie lines without block adjacency")

    # Add inter-block tie lines in round-robin.
    if need_ties > 0:
        step = 0
        max_attempt = max(need_ties * 100, 1000)
        attempt = 0
        while need_ties > 0:
            if attempt >= max_attempt:
                raise RuntimeError("unable to construct enough unique tie lines, please adjust topology parameters")
            pair_idx = step % len(adjacency)
            b1, b2 = adjacency[pair_idx]
            k = (step // len(adjacency)) % len(connector_template)

            n1_template = connector_template[k % len(connector_template)]
            n2_template = connector_template[(k + pair_idx + 1) % len(connector_template)]
            u = block_node_id[(b1, n1_template)]
            v = block_node_id[(b2, n2_template)]
            step += 1
            attempt += 1
            if add_line(u=u, v=v, capacity=cap_mean):
                need_ties -= 1

    # Rebuild line ids to strict L0..L(n-1).
    for i, ln in enumerate(all_lines):
        ln["id"] = f"L{i}"

    out = {
        "nodes": all_nodes,
        "lines": all_lines,
        "generators": all_gens,
        "source": {
            "base_grid": str(base_path),
            "mode": "tiled_scaled",
            "tile_rows": rows,
            "tile_cols": cols,
        },
        "geo_reference": base.get("geo_reference", {}),
    }

    dump_json(out_path, out)

    # Light validation summary.
    node_ids = [int(n["id"]) for n in all_nodes]
    line_ids = [str(ln["id"]) for ln in all_lines]
    duplicates_nodes = len(node_ids) - len(set(node_ids))
    duplicates_lines = len(line_ids) - len(set(line_ids))
    print(
        json.dumps(
            {
                "output_grid": str(out_path),
                "node_count": len(all_nodes),
                "line_count": len(all_lines),
                "generator_count": len(all_gens),
                "duplicates_nodes": duplicates_nodes,
                "duplicates_lines": duplicates_lines,
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
