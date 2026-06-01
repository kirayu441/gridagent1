from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

try:
    import pandapower.networks as ppn
except ImportError:
    ppn = None


DEFAULT_LOAD_URL = "https://zenodo.org/records/8322210/files/Appendix%201_Hourly%20electric%20power%20load%20final.csv?download=1"


def load_config(config_path: Path) -> dict[str, Any]:
    with config_path.open("r", encoding="utf-8") as config_file:
        return json.load(config_file)


def build_time_index(config: dict[str, Any]) -> pd.DatetimeIndex:
    return pd.date_range(start=config["start"], end=config["end"], freq=config.get("freq", "1h"))


def to_plain_timestamp_strings(time_index: pd.DatetimeIndex) -> pd.Series:
    plain = time_index.tz_localize(None) if time_index.tz is not None else time_index
    return pd.Series(plain.strftime("%Y-%m-%d %H:%M:%S"))


def align_source_to_target_length(raw_series: pd.Series, target_index: pd.DatetimeIndex) -> pd.Series:
    target_size = len(target_index)
    source_size = len(raw_series)
    if source_size == target_size:
        aligned = pd.Series(raw_series.to_numpy(dtype=float), index=target_index)
        return aligned

    non_leap_mask = ~((target_index.month == 2) & (target_index.day == 29))
    non_leap_index = target_index[non_leap_mask]
    if source_size == len(non_leap_index):
        aligned = pd.Series(raw_series.to_numpy(dtype=float), index=non_leap_index)
        aligned = aligned.reindex(target_index).interpolate(method="time").ffill().bfill()
        return aligned

    raise ValueError(
        f"源负荷长度无法对齐：source={source_size}, target={target_size}, target_non_leap={len(non_leap_index)}"
    )


def build_load_csv(
    config: dict[str, Any],
    load_url: str,
    source_columns: list[str],
    output_columns: list[str],
) -> tuple[Path, Path]:
    raw_dirs = config["raw_dirs"]
    region_root = Path(raw_dirs["load"]).parent
    nested_load_dir = Path(raw_dirs["load"])
    region_root.mkdir(parents=True, exist_ok=True)
    nested_load_dir.mkdir(parents=True, exist_ok=True)

    source_table = pd.read_csv(load_url, sep=";")
    for source_column in source_columns:
        if source_column not in source_table.columns:
            raise ValueError(f"负荷源缺少列: {source_column}")

    target_index = build_time_index(config)
    result = pd.DataFrame({"timestamp": to_plain_timestamp_strings(target_index)})

    for source_column, output_column in zip(source_columns, output_columns):
        aligned = align_source_to_target_length(source_table[source_column].astype(float), target_index=target_index)
        result[output_column] = aligned.to_numpy(dtype=float)

    root_output = region_root / "load.csv"
    nested_output = nested_load_dir / "load.csv"
    result.to_csv(root_output, index=False, encoding="utf-8")
    result.to_csv(nested_output, index=False, encoding="utf-8")
    return root_output, nested_output


def map_sgen_type(raw_type: str) -> str:
    normalized = raw_type.strip().upper()
    if normalized == "PV":
        return "pv"
    if normalized in {"WP", "WIND"}:
        return "wind"
    return "renewable"


def parse_geo_point(raw_geo: Any) -> tuple[float, float] | None:
    if raw_geo is None:
        return None
    if not isinstance(raw_geo, str):
        return None
    raw_geo = raw_geo.strip()
    if not raw_geo:
        return None
    try:
        payload = json.loads(raw_geo)
    except json.JSONDecodeError:
        return None
    if payload.get("type") != "Point":
        return None
    coords = payload.get("coordinates")
    if not isinstance(coords, list) or len(coords) < 2:
        return None
    try:
        return float(coords[0]), float(coords[1])
    except (TypeError, ValueError):
        return None


def local_xy_to_latlon(x_local: float, y_local: float, anchor_lat: float, anchor_lon: float, unit_km_per_local: float) -> tuple[float, float]:
    east_km = x_local * unit_km_per_local
    north_km = y_local * unit_km_per_local
    lat = anchor_lat + north_km / 110.57
    lon = anchor_lon + east_km / (111.32 * np.cos(np.deg2rad(anchor_lat)))
    return float(lat), float(lon)


def build_grid_json(config: dict[str, Any]) -> tuple[Path, Path]:
    if ppn is None:
        raise ImportError("需要安装 pandapower 才能生成配网拓扑样例。")

    raw_dirs = config["raw_dirs"]
    region_root = Path(raw_dirs["grid"]).parent
    nested_grid_dir = Path(raw_dirs["grid"])
    region_root.mkdir(parents=True, exist_ok=True)
    nested_grid_dir.mkdir(parents=True, exist_ok=True)

    net = ppn.create_cigre_network_mv(with_der="pv_wind")
    load_buses = set(net.load["bus"].tolist()) if len(net.load) > 0 else set()
    geo_cfg = config.get("grid_geo_anchor", {})
    anchor_lat = float(geo_cfg.get("lat", 23.1291))
    anchor_lon = float(geo_cfg.get("lon", 113.2644))
    unit_km_per_local = float(geo_cfg.get("unit_km_per_local", 1.5))

    bus_geo_map: dict[int, dict[str, float | None]] = {}
    if "geo" in net.bus.columns:
        for bus_id, row in net.bus.iterrows():
            geo = parse_geo_point(row.get("geo"))
            if geo is None:
                bus_geo_map[int(bus_id)] = {
                    "local_x": None,
                    "local_y": None,
                    "lat": None,
                    "lon": None,
                }
                continue
            local_x, local_y = geo
            lat, lon = local_xy_to_latlon(
                x_local=local_x,
                y_local=local_y,
                anchor_lat=anchor_lat,
                anchor_lon=anchor_lon,
                unit_km_per_local=unit_km_per_local,
            )
            bus_geo_map[int(bus_id)] = {
                "local_x": float(local_x),
                "local_y": float(local_y),
                "lat": float(lat),
                "lon": float(lon),
            }

    nodes: list[dict[str, Any]] = []
    for bus_id, row in net.bus.iterrows():
        geo = bus_geo_map.get(
            int(bus_id),
            {"local_x": None, "local_y": None, "lat": None, "lon": None},
        )
        nodes.append(
            {
                "id": int(bus_id),
                "type": "load" if int(bus_id) in load_buses else "bus",
                "vn_kv": float(row["vn_kv"]) if pd.notna(row["vn_kv"]) else None,
                "local_x": geo["local_x"],
                "local_y": geo["local_y"],
                "lat": geo["lat"],
                "lon": geo["lon"],
            }
        )

    lines: list[dict[str, Any]] = []
    for line_id, row in net.line.iterrows():
        from_bus = int(row["from_bus"])
        to_bus = int(row["to_bus"])
        from_vn = float(net.bus.loc[from_bus, "vn_kv"]) if pd.notna(net.bus.loc[from_bus, "vn_kv"]) else 0.0
        max_i = float(row["max_i_ka"]) if pd.notna(row["max_i_ka"]) else 0.0
        capacity = float(np.sqrt(3) * from_vn * max_i)
        from_geo = bus_geo_map.get(from_bus, {"lat": None, "lon": None})
        to_geo = bus_geo_map.get(to_bus, {"lat": None, "lon": None})
        if from_geo["lat"] is not None and to_geo["lat"] is not None:
            mid_lat = (float(from_geo["lat"]) + float(to_geo["lat"])) / 2.0
            mid_lon = (float(from_geo["lon"]) + float(to_geo["lon"])) / 2.0
        else:
            mid_lat, mid_lon = None, None
        lines.append(
            {
                "id": f"L{int(line_id)}",
                "from": from_bus,
                "to": to_bus,
                "capacity": round(capacity, 6),
                "length_km": float(row["length_km"]) if pd.notna(row["length_km"]) else None,
                "from_lat": from_geo["lat"],
                "from_lon": from_geo["lon"],
                "to_lat": to_geo["lat"],
                "to_lon": to_geo["lon"],
                "mid_lat": mid_lat,
                "mid_lon": mid_lon,
            }
        )

    generators: list[dict[str, Any]] = []
    for ext_id, row in net.ext_grid.iterrows():
        max_p = float(row["max_p_mw"]) if "max_p_mw" in net.ext_grid.columns and pd.notna(row.get("max_p_mw", np.nan)) else 0.0
        generators.append(
            {
                "id": f"TH{int(ext_id)}",
                "type": "thermal",
                "bus": int(row["bus"]),
                "capacity": max_p,
            }
        )

    if "type" in net.sgen.columns:
        for sgen_id, row in net.sgen.iterrows():
            generators.append(
                {
                    "id": f"SG{int(sgen_id)}",
                    "type": map_sgen_type(str(row.get("type", ""))),
                    "bus": int(row["bus"]),
                    "capacity": float(row["p_mw"]) if pd.notna(row["p_mw"]) else 0.0,
                }
            )

    payload = {
        "nodes": nodes,
        "lines": lines,
        "generators": generators,
        "source": "pandapower.create_cigre_network_mv(with_der='pv_wind')",
        "geo_reference": {
            "type": "derived_from_pandapower_bus_geo",
            "anchor_lat": anchor_lat,
            "anchor_lon": anchor_lon,
            "unit_km_per_local": unit_km_per_local,
            "note": "Coordinates are mapped from CIGRE local diagram, not real Guangdong utility GIS.",
        },
    }

    root_output = region_root / "grid.json"
    nested_output = nested_grid_dir / "grid.json"
    with root_output.open("w", encoding="utf-8") as root_file:
        json.dump(payload, root_file, ensure_ascii=False, indent=2)
    with nested_output.open("w", encoding="utf-8") as nested_file:
        json.dump(payload, nested_file, ensure_ascii=False, indent=2)
    return root_output, nested_output


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="一键补全 formal 数据集的 load.csv 和 grid.json。")
    parser.add_argument(
        "--config",
        default="scripts/dataset_config.formal_guangdong_2024.json",
        help="配置文件路径，默认 scripts/dataset_config.formal_guangdong_2024.json",
    )
    parser.add_argument(
        "--load-url",
        default=DEFAULT_LOAD_URL,
        help="负荷数据源 URL（默认使用 Zenodo 省级小时负荷数据）。",
    )
    parser.add_argument(
        "--load-cols",
        default="GD,GX",
        help="源负荷列名，逗号分隔（默认 GD,GX）。",
    )
    parser.add_argument(
        "--out-cols",
        default="load_region1,load_region2",
        help="输出负荷列名，逗号分隔（默认 load_region1,load_region2）。",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = load_config(Path(args.config))

    source_columns = [item.strip() for item in args.load_cols.split(",") if item.strip()]
    output_columns = [item.strip() for item in args.out_cols.split(",") if item.strip()]
    if len(source_columns) == 0 or len(source_columns) != len(output_columns):
        raise ValueError("--load-cols 与 --out-cols 需要一一对应且非空。")

    load_root, load_nested = build_load_csv(
        config=config,
        load_url=args.load_url,
        source_columns=source_columns,
        output_columns=output_columns,
    )
    grid_root, grid_nested = build_grid_json(config=config)

    print(f"已生成负荷文件: {load_root}")
    print(f"已生成负荷文件: {load_nested}")
    print(f"已生成配网文件: {grid_root}")
    print(f"已生成配网文件: {grid_nested}")


if __name__ == "__main__":
    main()
