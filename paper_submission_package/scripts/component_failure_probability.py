from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from scipy.stats import norm


@dataclass
class TyphoonState:
    t: int
    timestamp: pd.Timestamp
    lat: float
    lon: float
    central_pressure_hpa: float
    peripheral_pressure_hpa: float
    vmax_ms: float
    move_speed_ms: float
    move_dir_deg: float


@dataclass
class LineAsset:
    line_id: str
    from_bus: int
    to_bus: int
    lat1: float
    lon1: float
    lat2: float
    lon2: float
    towers: int
    spans: int
    design_line_load_n: float
    design_tower_load_kn: float

    @property
    def mid_lat(self) -> float:
        return (self.lat1 + self.lat2) / 2.0

    @property
    def mid_lon(self) -> float:
        return (self.lon1 + self.lon2) / 2.0


def estimate_rmax_km(peripheral_pressure_hpa: float, central_pressure_hpa: float) -> float:
    delta_p = max(peripheral_pressure_hpa - central_pressure_hpa, 1e-3)
    return float(np.exp(5.0237 - 0.0247 * delta_p))


def latlon_delta_km(origin_lat: float, origin_lon: float, target_lat: float, target_lon: float) -> tuple[float, float]:
    mean_lat_rad = np.deg2rad((origin_lat + target_lat) / 2.0)
    dx_east_km = (target_lon - origin_lon) * 111.32 * np.cos(mean_lat_rad)
    dy_north_km = (target_lat - origin_lat) * 110.57
    return float(dx_east_km), float(dy_north_km)


def local_xy_to_latlon(x_local: float, y_local: float, anchor_lat: float, anchor_lon: float, unit_km_per_local: float) -> tuple[float, float]:
    east_km = x_local * unit_km_per_local
    north_km = y_local * unit_km_per_local
    lat = anchor_lat + north_km / 110.57
    lon = anchor_lon + east_km / (111.32 * np.cos(np.deg2rad(anchor_lat)))
    return float(lat), float(lon)


def _circular_vector_with_inflow(vr: float, dx_east_km: float, dy_north_km: float, inflow_deg: float = 20.0) -> tuple[float, float]:
    r = np.hypot(dx_east_km, dy_north_km)
    if r < 1e-6:
        return 0.0, 0.0
    theta = np.deg2rad(inflow_deg)
    x = dy_north_km
    y = dx_east_km
    a_coeff = -(y * np.cos(theta) + x * np.sin(theta)) / r
    b_coeff = (x * np.cos(theta) - y * np.sin(theta)) / r
    return float(vr * b_coeff), float(vr * a_coeff)


def _moving_vector(vm: float, move_dir_deg: float) -> tuple[float, float]:
    rad = np.deg2rad(move_dir_deg)
    return float(vm * np.sin(rad)), float(vm * np.cos(rad))


def batts_model_components(r_km: float, rmax_km: float, vmax_ms: float, move_speed_ms: float, a: float = 0.5) -> tuple[float, float]:
    r_km = max(r_km, 1e-6)
    rmax_km = max(rmax_km, 1e-6)
    if r_km <= rmax_km:
        vr = vmax_ms * (r_km / rmax_km)
    else:
        vr = vmax_ms * (rmax_km / r_km) ** a
    return float(vr), float(move_speed_ms)


def schloemer_model_components(r_km: float, rmax_km: float, vmax_ms: float, move_speed_ms: float) -> tuple[float, float]:
    r_km = max(r_km, 1e-6)
    rmax_km = max(rmax_km, 1e-6)
    vr = vmax_ms * (rmax_km / r_km) * np.exp(1.0 - rmax_km / r_km)
    numerator = 3.0 * (rmax_km**1.5) * (r_km**1.5)
    denominator = (rmax_km**3) + (r_km**3) + (rmax_km**1.5) * (r_km**1.5)
    vm = move_speed_ms * numerator / max(denominator, 1e-9)
    return float(vr), float(vm)


def typhoon_wind_speed_gradient(state: TyphoonState, target_lat: float, target_lon: float, model_name: str) -> float:
    dx_east_km, dy_north_km = latlon_delta_km(state.lat, state.lon, target_lat, target_lon)
    r_km = max(np.hypot(dx_east_km, dy_north_km), 1e-6)
    rmax_km = estimate_rmax_km(state.peripheral_pressure_hpa, state.central_pressure_hpa)

    if model_name == "batts":
        vr, vm = batts_model_components(r_km, rmax_km, state.vmax_ms, state.move_speed_ms)
    elif model_name == "schloemer":
        vr, vm = schloemer_model_components(r_km, rmax_km, state.vmax_ms, state.move_speed_ms)
    else:
        raise ValueError(f"Unsupported model_name={model_name}")

    vr_east, vr_north = _circular_vector_with_inflow(vr, dx_east_km, dy_north_km, inflow_deg=20.0)
    vm_east, vm_north = _moving_vector(vm, state.move_dir_deg)
    return float(np.hypot(vr_east + vm_east, vr_north + vm_north))


def boundary_layer_and_gust_correction(v_gradient_ms: float) -> float:
    alpha = 0.8 if v_gradient_ms > 40.0 else 0.71
    return float(1.08 * alpha * v_gradient_ms)


def _alpha_uneven_coefficient(v_ms: float) -> float:
    if v_ms < 20.0:
        return 1.0
    if v_ms < 30.0:
        return 1.2
    return 1.4


def line_wind_load_n(
    v_ms: float,
    theta_deg: float = 90.0,
    mu_z: float = 1.38,
    mu_sc: float = 1.1,
    beta_c: float = 1.0,
    d_mm: float = 18.0,
    lp_m: float = 300.0,
) -> float:
    alpha = _alpha_uneven_coefficient(v_ms)
    sin_term = np.sin(np.deg2rad(theta_deg)) ** 2
    return float((alpha * mu_z * mu_sc * beta_c * d_mm * lp_m * (v_ms**2) * sin_term) / 1600.0)


def tower_wind_load_kn(v_ms: float, mu_z: float = 1.8, mu_s: float = 2.0, beta_z: float = 1.25, area_m2: float = 20.0) -> float:
    return float((mu_z * mu_s * beta_z * area_m2 * (v_ms**2)) / 1600.0)


def stress_strength_failure_probability(mu_actual: float, sigma_actual: float, mu_design: float, sigma_design: float) -> float:
    sigma_total = np.sqrt(max(sigma_actual**2 + sigma_design**2, 1e-12))
    z = (mu_design - mu_actual) / sigma_total
    return float(1.0 - norm.cdf(z))


def line_failure_probability_series_system(p_tower: float, p_span: float, n_towers: int, n_spans: int) -> float:
    return float(1.0 - ((1.0 - p_tower) ** n_towers) * ((1.0 - p_span) ** n_spans))


def make_bus_coordinates(nodes: list[dict[str, Any]], center_lat: float, center_lon: float) -> dict[int, tuple[float, float]]:
    ids = sorted(int(item["id"]) for item in nodes if "id" in item)
    if not ids:
        raise ValueError("grid nodes is empty")
    result: dict[int, tuple[float, float]] = {}
    total = len(ids)
    for idx, node_id in enumerate(ids):
        angle = 2.0 * np.pi * (idx / max(total, 1)) + node_id * 0.17
        radius = 0.04 + 0.015 * (idx % 5)
        lat = center_lat + float(radius * np.sin(angle))
        lon = center_lon + float(radius * np.cos(angle))
        result[node_id] = (lat, lon)
    return result


def derive_design_parameters(length_km: float, capacity: float) -> tuple[int, int, float, float]:
    length_km = max(float(length_km), 0.1)
    capacity = max(float(capacity), 1.0)
    towers = max(2, int(round(length_km / 0.30)) + 1)
    spans = max(3, int(round(length_km / 0.12)))
    design_line_load_n = 6500.0 + 180.0 * length_km + 220.0 * capacity
    design_tower_load_kn = 80.0 + 6.0 * length_km + 3.5 * capacity
    return towers, spans, design_line_load_n, design_tower_load_kn


def parse_optional_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    if np.isnan(parsed):
        return None
    return float(parsed)


def load_line_assets(grid_path: Path, center_lat: float, center_lon: float) -> list[LineAsset]:
    with grid_path.open("r", encoding="utf-8") as f:
        payload = json.load(f)
    nodes = payload.get("nodes", [])
    lines = payload.get("lines", [])
    if not nodes or not lines:
        raise ValueError(f"invalid grid topology: {grid_path}")

    geo_ref = payload.get("geo_reference", {}) if isinstance(payload.get("geo_reference"), dict) else {}
    anchor_lat = parse_optional_float(geo_ref.get("anchor_lat")) or center_lat
    anchor_lon = parse_optional_float(geo_ref.get("anchor_lon")) or center_lon
    unit_km_per_local = parse_optional_float(geo_ref.get("unit_km_per_local")) or 1.5

    bus_coords: dict[int, tuple[float, float]] = {}
    for row in nodes:
        if "id" not in row:
            continue
        node_id = int(row["id"])
        lat = parse_optional_float(row.get("lat"))
        lon = parse_optional_float(row.get("lon"))
        if lat is not None and lon is not None:
            bus_coords[node_id] = (lat, lon)
            continue
        local_x = parse_optional_float(row.get("local_x"))
        local_y = parse_optional_float(row.get("local_y"))
        if local_x is not None and local_y is not None:
            bus_coords[node_id] = local_xy_to_latlon(
                x_local=local_x,
                y_local=local_y,
                anchor_lat=anchor_lat,
                anchor_lon=anchor_lon,
                unit_km_per_local=unit_km_per_local,
            )

    if len(bus_coords) < len(nodes):
        fallback = make_bus_coordinates(nodes=nodes, center_lat=center_lat, center_lon=center_lon)
        for key, value in fallback.items():
            if key not in bus_coords:
                bus_coords[key] = value

    assets: list[LineAsset] = []
    for row in lines:
        from_bus = int(row.get("from", row.get("from_bus")))
        to_bus = int(row.get("to", row.get("to_bus")))
        if from_bus not in bus_coords or to_bus not in bus_coords:
            continue
        length_km = float(row.get("length_km", 1.0))
        capacity = float(row.get("capacity", 5.0))
        towers, spans, design_line_load_n, design_tower_load_kn = derive_design_parameters(length_km, capacity)
        lat1 = parse_optional_float(row.get("from_lat"))
        lon1 = parse_optional_float(row.get("from_lon"))
        lat2 = parse_optional_float(row.get("to_lat"))
        lon2 = parse_optional_float(row.get("to_lon"))
        if lat1 is None or lon1 is None:
            lat1, lon1 = bus_coords[from_bus]
        if lat2 is None or lon2 is None:
            lat2, lon2 = bus_coords[to_bus]
        assets.append(
            LineAsset(
                line_id=str(row.get("id", f"L_{from_bus}_{to_bus}")),
                from_bus=from_bus,
                to_bus=to_bus,
                lat1=lat1,
                lon1=lon1,
                lat2=lat2,
                lon2=lon2,
                towers=towers,
                spans=spans,
                design_line_load_n=design_line_load_n,
                design_tower_load_kn=design_tower_load_kn,
            )
        )
    if not assets:
        raise ValueError(f"no valid lines parsed from {grid_path}")
    return assets


def build_typhoon_track(
    start_time: str,
    hours: int,
    center_lat: float,
    center_lon: float,
    intensity_scale: float,
    move_dir_deg: float,
    move_speed_ms: float,
) -> list[TyphoonState]:
    timestamps = pd.date_range(start=start_time, periods=hours, freq="1h")
    states: list[TyphoonState] = []
    for t, ts in enumerate(timestamps):
        progress = t / max(hours - 1, 1)
        lat = center_lat + 0.45 - 0.90 * progress
        lon = center_lon + 0.75 - 1.45 * progress
        bell = np.exp(-((progress - 0.5) ** 2) / 0.06)
        vmax = (21.0 + 19.0 * intensity_scale) + 12.0 * bell
        pc = 1007.0 - (17.0 * intensity_scale) - 24.0 * bell
        states.append(
            TyphoonState(
                t=t,
                timestamp=ts,
                lat=float(lat),
                lon=float(lon),
                central_pressure_hpa=float(pc),
                peripheral_pressure_hpa=1010.0,
                vmax_ms=float(vmax),
                move_speed_ms=float(move_speed_ms),
                move_dir_deg=float(move_dir_deg),
            )
        )
    return states


def compute_line_failure_timeseries(
    track: list[TyphoonState],
    lines: list[LineAsset],
    model_name: str,
    design_scale: float,
) -> pd.DataFrame:
    records: list[dict[str, Any]] = []
    for state in track:
        for line in lines:
            v_gradient = typhoon_wind_speed_gradient(state, line.mid_lat, line.mid_lon, model_name=model_name)
            v_surface = boundary_layer_and_gust_correction(v_gradient)

            actual_line_load_n = line_wind_load_n(v_surface)
            actual_tower_load_kn = tower_wind_load_kn(v_surface)

            mu_design_line = line.design_line_load_n * design_scale
            sigma_design_line = mu_design_line * 0.03
            mu_design_tower = line.design_tower_load_kn * design_scale
            sigma_design_tower = mu_design_tower * 0.10

            sigma_actual_line = max(actual_line_load_n * 0.12, 1e-6)
            sigma_actual_tower = max(actual_tower_load_kn * 0.12, 1e-6)

            p_span = stress_strength_failure_probability(
                mu_actual=actual_line_load_n,
                sigma_actual=sigma_actual_line,
                mu_design=mu_design_line,
                sigma_design=sigma_design_line,
            )
            p_tower = stress_strength_failure_probability(
                mu_actual=actual_tower_load_kn,
                sigma_actual=sigma_actual_tower,
                mu_design=mu_design_tower,
                sigma_design=sigma_design_tower,
            )
            p_line = line_failure_probability_series_system(
                p_tower=p_tower,
                p_span=p_span,
                n_towers=line.towers,
                n_spans=line.spans,
            )
            records.append(
                {
                    "timestamp": str(state.timestamp),
                    "model": model_name,
                    "line_id": line.line_id,
                    "from_bus": line.from_bus,
                    "to_bus": line.to_bus,
                    "v_surface_ms": float(v_surface),
                    "p_tower": float(np.clip(p_tower, 0.0, 1.0)),
                    "p_span": float(np.clip(p_span, 0.0, 1.0)),
                    "p_line": float(np.clip(p_line, 0.0, 1.0)),
                    "towers": int(line.towers),
                    "spans": int(line.spans),
                    "design_line_load_n": float(line.design_line_load_n),
                    "design_tower_load_kn": float(line.design_tower_load_kn),
                }
            )
    return pd.DataFrame.from_records(records)


def summarize_model(df: pd.DataFrame, top_k: int = 5) -> dict[str, Any]:
    grouped = (
        df.groupby("line_id", as_index=False)
        .agg(
            p_line_mean=("p_line", "mean"),
            p_line_max=("p_line", "max"),
            p_tower_mean=("p_tower", "mean"),
            p_span_mean=("p_span", "mean"),
            vmax_surface=("v_surface_ms", "max"),
        )
        .sort_values(by="p_line_mean", ascending=False)
    )
    top = grouped.head(top_k).to_dict(orient="records")
    return {
        "line_count": int(df["line_id"].nunique()),
        "time_steps": int(df["timestamp"].nunique()),
        "overall_p_line_mean": float(df["p_line"].mean()),
        "overall_p_line_max": float(df["p_line"].max()),
        "top_vulnerable_lines": top,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compute transmission line/tower failure probabilities using Batts/Schloemer + stress-strength."
    )
    parser.add_argument(
        "--grid",
        default="data_final/formal_guangdong_2024/grid_topology.json",
        help="Path to grid topology json.",
    )
    parser.add_argument(
        "--output-dir",
        default="results/component_failure_probability/formal2024",
        help="Output directory.",
    )
    parser.add_argument(
        "--model",
        choices=("batts", "schloemer", "both"),
        default="both",
        help="Wind field model.",
    )
    parser.add_argument("--start-time", default="2024-09-01 00:00:00", help="Typhoon track start time.")
    parser.add_argument("--hours", type=int, default=72, help="Typhoon duration in hours.")
    parser.add_argument("--center-lat", type=float, default=23.1291, help="Grid center latitude.")
    parser.add_argument("--center-lon", type=float, default=113.2644, help="Grid center longitude.")
    parser.add_argument("--intensity-scale", type=float, default=1.0, help="Typhoon intensity scale.")
    parser.add_argument("--move-dir-deg", type=float, default=300.0, help="Typhoon moving direction.")
    parser.add_argument("--move-speed-ms", type=float, default=6.0, help="Typhoon moving speed.")
    parser.add_argument("--design-scale", type=float, default=1.0, help="Design strength scale.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    root = Path(__file__).resolve().parent.parent
    grid_path = (root / args.grid).resolve()
    output_dir = (root / args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    lines = load_line_assets(grid_path=grid_path, center_lat=args.center_lat, center_lon=args.center_lon)
    track = build_typhoon_track(
        start_time=args.start_time,
        hours=args.hours,
        center_lat=args.center_lat,
        center_lon=args.center_lon,
        intensity_scale=args.intensity_scale,
        move_dir_deg=args.move_dir_deg,
        move_speed_ms=args.move_speed_ms,
    )
    models = ["batts", "schloemer"] if args.model == "both" else [args.model]

    summary: dict[str, Any] = {
        "grid_path": str(grid_path),
        "output_dir": str(output_dir),
        "track": {
            "start": str(track[0].timestamp) if track else None,
            "end": str(track[-1].timestamp) if track else None,
            "hours": int(args.hours),
            "intensity_scale": float(args.intensity_scale),
            "move_dir_deg": float(args.move_dir_deg),
            "move_speed_ms": float(args.move_speed_ms),
        },
        "models": {},
    }

    for model_name in models:
        print(f"running model={model_name} ...")
        result_df = compute_line_failure_timeseries(
            track=track,
            lines=lines,
            model_name=model_name,
            design_scale=args.design_scale,
        )
        csv_path = output_dir / f"line_failure_timeseries_{model_name}.csv"
        result_df.to_csv(csv_path, index=False, encoding="utf-8")
        model_summary = summarize_model(result_df, top_k=5)
        model_summary["timeseries_csv"] = str(csv_path)
        summary["models"][model_name] = model_summary
        print(
            f"  mean_p_line={model_summary['overall_p_line_mean']:.4f}, "
            f"max_p_line={model_summary['overall_p_line_max']:.4f}"
        )

    if set(models) == {"batts", "schloemer"}:
        batts_mean = summary["models"]["batts"]["overall_p_line_mean"]
        sch_mean = summary["models"]["schloemer"]["overall_p_line_mean"]
        summary["comparison"] = {
            "mean_p_line_batts": float(batts_mean),
            "mean_p_line_schloemer": float(sch_mean),
            "delta_schloemer_minus_batts": float(sch_mean - batts_mean),
        }

    report_path = output_dir / "failure_probability_report.json"
    with report_path.open("w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    print(f"report -> {report_path}")


if __name__ == "__main__":
    main()
