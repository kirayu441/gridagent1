from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


def load_config(config_path: Path) -> dict[str, Any]:
    with config_path.open("r", encoding="utf-8") as config_file:
        return json.load(config_file)


def ensure_dirs(config: dict[str, Any]) -> None:
    Path(config["raw_dirs"]["wind_solar"]).mkdir(parents=True, exist_ok=True)
    Path(config["raw_dirs"]["load"]).mkdir(parents=True, exist_ok=True)
    Path(config["raw_dirs"]["weather"]).mkdir(parents=True, exist_ok=True)
    Path(config["raw_dirs"]["grid"]).mkdir(parents=True, exist_ok=True)


def build_time_index(config: dict[str, Any]) -> pd.DatetimeIndex:
    return pd.date_range(
        start=config["start"],
        end=config["end"],
        freq=config.get("freq", "1h"),
    )


def synthesize_wind_series(time_index: pd.DatetimeIndex, seed: int) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    total_points = len(time_index)
    day_phase = np.linspace(0, 2 * np.pi * total_points / 24 / 7, total_points)
    seasonal_phase = np.linspace(0, 2 * np.pi, total_points)
    wind_a = 580 + 220 * np.sin(day_phase) + 110 * np.sin(seasonal_phase) + rng.normal(0, 55, total_points)
    wind_b = 430 + 190 * np.sin(day_phase + 0.8) + 95 * np.sin(seasonal_phase + 0.3) + rng.normal(0, 45, total_points)
    frame = pd.DataFrame(
        {
            "timestamp": time_index,
            "wind_1MW": np.clip(wind_a, 0, 1000),
            "wind_2MW": np.clip(wind_b, 0, 1000),
        }
    )
    return frame


def synthesize_pv_series(time_index: pd.DatetimeIndex, seed: int) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    hours = time_index.hour.to_numpy()
    day_profile = np.maximum(0.0, np.sin(np.pi * (hours - 6) / 12))
    seasonality = 0.7 + 0.3 * np.sin(2 * np.pi * time_index.dayofyear.to_numpy() / 365)
    pv_a = 900 * day_profile * seasonality + rng.normal(0, 25, len(time_index))
    pv_b = 650 * day_profile * (0.9 + 0.1 * seasonality) + rng.normal(0, 20, len(time_index))
    frame = pd.DataFrame(
        {
            "timestamp": time_index,
            "pv_1MW": np.clip(pv_a, 0, 1000),
            "pv_2MW": np.clip(pv_b, 0, 1000),
        }
    )
    return frame


def synthesize_load_series(time_index: pd.DatetimeIndex, seed: int) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    daily = 0.5 + 0.5 * np.sin(2 * np.pi * (time_index.hour.to_numpy() - 8) / 24)
    weekly = 0.2 * np.cos(2 * np.pi * time_index.dayofweek.to_numpy() / 7)
    seasonal = 0.15 * np.sin(2 * np.pi * time_index.dayofyear.to_numpy() / 365)
    load_a = 780 + 260 * daily + 130 * weekly + 110 * seasonal + rng.normal(0, 35, len(time_index))
    load_b = 650 + 200 * daily + 100 * weekly + 90 * seasonal + rng.normal(0, 30, len(time_index))
    frame = pd.DataFrame(
        {
            "timestamp": time_index,
            "load_node_1": np.clip(load_a, 200, None),
            "load_node_2": np.clip(load_b, 150, None),
        }
    )
    return frame


def synthesize_weather_series(time_index: pd.DatetimeIndex, seed: int) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    temp = 18 + 9 * np.sin(2 * np.pi * (time_index.dayofyear.to_numpy() - 60) / 365) + rng.normal(0, 1.2, len(time_index))
    wind_speed = 6 + 2.5 * np.sin(2 * np.pi * time_index.hour.to_numpy() / 24) + rng.normal(0, 0.8, len(time_index))
    irradiance = 850 * np.maximum(0.0, np.sin(np.pi * (time_index.hour.to_numpy() - 6) / 12)) + rng.normal(0, 25, len(time_index))
    frame = pd.DataFrame(
        {
            "timestamp": time_index,
            "temperature_c": temp,
            "wind_speed_ms": np.clip(wind_speed, 0, None),
            "irradiance_wm2": np.clip(irradiance, 0, None),
        }
    )
    return frame


def write_grid_tables(config: dict[str, Any]) -> None:
    grid_dir = Path(config["raw_dirs"]["grid"])
    nodes = pd.DataFrame(
        [
            {"id": 1, "type": "bus"},
            {"id": 2, "type": "load"},
            {"id": 3, "type": "load"},
            {"id": 4, "type": "generator"},
        ]
    )
    lines = pd.DataFrame(
        [
            {"id": "L1", "from": 1, "to": 2, "capacity": 120, "redundancy": 1},
            {"id": "L2", "from": 1, "to": 3, "capacity": 100, "redundancy": 1},
            {"id": "L3", "from": 4, "to": 1, "capacity": 150, "redundancy": 2},
        ]
    )
    generators = pd.DataFrame(
        [
            {"id": "G1", "type": "wind", "capacity": 10},
            {"id": "G2", "type": "pv", "capacity": 5},
            {"id": "G3", "type": "thermal", "capacity": 25},
        ]
    )
    nodes.to_csv(grid_dir / "nodes.csv", index=False, encoding="utf-8")
    lines.to_csv(grid_dir / "lines.csv", index=False, encoding="utf-8")
    generators.to_csv(grid_dir / "generators.csv", index=False, encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="生成可跑通流程的示例原始数据（风光+负荷+气象+配网）。")
    parser.add_argument(
        "--config",
        default="scripts/dataset_config.example.json",
        help="配置文件路径，默认 scripts/dataset_config.example.json",
    )
    parser.add_argument("--seed", type=int, default=2026, help="随机种子，默认 2026")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = load_config(Path(args.config))
    ensure_dirs(config)
    time_index = build_time_index(config)

    wind_frame = synthesize_wind_series(time_index=time_index, seed=args.seed)
    pv_frame = synthesize_pv_series(time_index=time_index, seed=args.seed + 1)
    load_frame = synthesize_load_series(time_index=time_index, seed=args.seed + 2)
    weather_frame = synthesize_weather_series(time_index=time_index, seed=args.seed + 3)

    wind_frame.to_csv(Path(config["raw_dirs"]["wind_solar"]) / "wind_demo.csv", index=False, encoding="utf-8")
    pv_frame.to_csv(Path(config["raw_dirs"]["wind_solar"]) / "pv_demo.csv", index=False, encoding="utf-8")
    load_frame.to_csv(Path(config["raw_dirs"]["load"]) / "load_demo.csv", index=False, encoding="utf-8")
    weather_frame.to_csv(Path(config["raw_dirs"]["weather"]) / "weather_demo.csv", index=False, encoding="utf-8")

    write_grid_tables(config)
    print("示例原始数据已生成。")


if __name__ == "__main__":
    main()
