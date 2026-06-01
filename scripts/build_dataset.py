from __future__ import annotations

import argparse
import json
import re
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

import numpy as np
import pandas as pd

try:
    import netCDF4
except ImportError:
    netCDF4 = None


TIME_COLUMN_CANDIDATES = ("timestamp", "time", "datetime", "date")


@dataclass
class PipelineArtifacts:
    trim_path: Path
    dpgmm_path: Path
    grid_path: Path
    report_path: Path
    merged_path: Path


def sanitize_column_name(raw_name: str) -> str:
    compact_name = re.sub(r"[^0-9a-zA-Z_]+", "_", raw_name)
    compact_name = re.sub(r"_+", "_", compact_name).strip("_")
    return compact_name.lower()


def load_config(config_path: Path) -> dict[str, Any]:
    with config_path.open("r", encoding="utf-8") as config_file:
        return json.load(config_file)


def find_time_column(columns: Iterable[str]) -> str:
    lowered = {column.lower(): column for column in columns}
    for candidate in TIME_COLUMN_CANDIDATES:
        if candidate in lowered:
            return lowered[candidate]
    for original in columns:
        lowered_name = original.lower()
        if "time" in lowered_name or "date" in lowered_name:
            return original
    raise ValueError("未找到时间列，请确保包含 timestamp/time/datetime/date 字段。")


def normalize_index_timezone(frame: pd.DataFrame, timezone_name: str | None) -> pd.DataFrame:
    if frame.empty:
        return frame
    normalized = frame.copy()
    if timezone_name:
        if normalized.index.tz is None:
            normalized.index = normalized.index.tz_localize(timezone_name)
        else:
            normalized.index = normalized.index.tz_convert(timezone_name)
    else:
        if normalized.index.tz is not None:
            normalized.index = normalized.index.tz_convert("UTC").tz_localize(None)
    return normalized


def read_csv_timeseries(file_path: Path, source_prefix: str, timezone_name: str | None) -> pd.DataFrame:
    table = pd.read_csv(file_path)
    if table.empty:
        return pd.DataFrame()
    time_column = find_time_column(table.columns)
    table[time_column] = pd.to_datetime(table[time_column], errors="coerce")
    table = table.dropna(subset=[time_column]).sort_values(time_column).set_index(time_column)

    numeric_part = table.select_dtypes(include=[np.number]).copy()
    if numeric_part.empty:
        for column_name in table.columns:
            numeric_part[column_name] = pd.to_numeric(table[column_name], errors="coerce")
        numeric_part = numeric_part.select_dtypes(include=[np.number])

    numeric_part = numeric_part.dropna(axis=1, how="all")
    if numeric_part.empty:
        return pd.DataFrame()

    stem = sanitize_column_name(file_path.stem)
    renamed_columns = {}
    for column_name in numeric_part.columns:
        renamed_columns[column_name] = f"{source_prefix}_{stem}_{sanitize_column_name(column_name)}"
    numeric_part = numeric_part.rename(columns=renamed_columns)
    numeric_part = numeric_part[~numeric_part.index.duplicated(keep="first")]
    numeric_part = normalize_index_timezone(numeric_part, timezone_name)
    return numeric_part.sort_index()


def infer_netcdf_time_variable(dataset: Any) -> str:
    for candidate in TIME_COLUMN_CANDIDATES:
        if candidate in dataset.variables:
            return candidate
    for variable_name in dataset.variables:
        if "time" in variable_name.lower() or "date" in variable_name.lower():
            return variable_name
    raise ValueError("NetCDF 中未找到时间变量。")


def read_netcdf_timeseries(file_path: Path, source_prefix: str, timezone_name: str | None) -> pd.DataFrame:
    if netCDF4 is None:
        raise ImportError("读取 NetCDF 需要安装 netCDF4 包。")
    dataset = netCDF4.Dataset(file_path)
    try:
        time_variable_name = infer_netcdf_time_variable(dataset)
        time_variable = dataset.variables[time_variable_name]
        time_values = netCDF4.num2date(time_variable[:], units=time_variable.units)
        time_index = pd.to_datetime(time_values)
        result = pd.DataFrame(index=time_index)
        for variable_name, variable in dataset.variables.items():
            if variable_name == time_variable_name:
                continue
            if len(variable.shape) != 1:
                continue
            if variable.shape[0] != len(time_index):
                continue
            if not np.issubdtype(variable.dtype, np.number):
                continue
            final_name = f"{source_prefix}_{sanitize_column_name(file_path.stem)}_{sanitize_column_name(variable_name)}"
            result[final_name] = np.array(variable[:], dtype=float)
        result = result.dropna(axis=1, how="all")
        result = normalize_index_timezone(result, timezone_name)
        result = result[~result.index.duplicated(keep="first")]
        return result.sort_index()
    finally:
        dataset.close()


def load_timeseries_file(file_path: Path, source_prefix: str, timezone_name: str | None) -> pd.DataFrame:
    suffix = file_path.suffix.lower()
    if suffix == ".csv":
        return read_csv_timeseries(file_path=file_path, source_prefix=source_prefix, timezone_name=timezone_name)
    if suffix in {".nc", ".netcdf"}:
        return read_netcdf_timeseries(file_path=file_path, source_prefix=source_prefix, timezone_name=timezone_name)
    return pd.DataFrame()


def classify_wind_or_pv(file_path: Path) -> str:
    lowered = file_path.stem.lower()
    if "pv" in lowered or "solar" in lowered or "photo" in lowered:
        return "pv"
    if "wind" in lowered:
        return "wind"
    return "wind"


def split_generation_and_weather_columns(frame: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    if frame.empty:
        return frame, pd.DataFrame(index=frame.index)
    weather_keywords = (
        "wind_speed",
        "winddirection",
        "wind_direction",
        "irradiance",
        "temperature",
        "temp",
        "humidity",
        "pressure",
    )
    weather_columns = [
        column_name
        for column_name in frame.columns
        if any(keyword in column_name.lower() for keyword in weather_keywords)
    ]
    generation_columns = [column_name for column_name in frame.columns if column_name not in weather_columns]
    generation_frame = frame[generation_columns] if generation_columns else pd.DataFrame(index=frame.index)
    weather_frame = frame[weather_columns] if weather_columns else pd.DataFrame(index=frame.index)
    return generation_frame, weather_frame


def collect_source_frames(raw_dirs: dict[str, str], timezone_name: str | None) -> dict[str, list[pd.DataFrame]]:
    collection: dict[str, list[pd.DataFrame]] = {"wind": [], "pv": [], "load": [], "weather": []}

    wind_solar_dir = Path(raw_dirs["wind_solar"])
    load_dir = Path(raw_dirs["load"])
    weather_dir = Path(raw_dirs["weather"])

    for file_path in sorted(wind_solar_dir.glob("*")):
        if not file_path.is_file():
            continue
        source_type = classify_wind_or_pv(file_path)
        frame = load_timeseries_file(file_path=file_path, source_prefix=source_type, timezone_name=timezone_name)
        if not frame.empty:
            generation_frame, weather_frame = split_generation_and_weather_columns(frame)
            if not generation_frame.empty:
                collection[source_type].append(generation_frame)
            if not weather_frame.empty:
                collection["weather"].append(weather_frame)

    for file_path in sorted(load_dir.glob("*")):
        if not file_path.is_file():
            continue
        frame = load_timeseries_file(file_path=file_path, source_prefix="load", timezone_name=timezone_name)
        if not frame.empty:
            collection["load"].append(frame)

    for file_path in sorted(weather_dir.glob("*")):
        if not file_path.is_file():
            continue
        frame = load_timeseries_file(file_path=file_path, source_prefix="weather", timezone_name=timezone_name)
        if not frame.empty:
            collection["weather"].append(frame)
    return collection


def align_frames(frames: list[pd.DataFrame], time_index: pd.DatetimeIndex) -> pd.DataFrame:
    if not frames:
        return pd.DataFrame(index=time_index.copy())
    merged = pd.concat(frames, axis=1)
    merged = merged[~merged.index.duplicated(keep="first")].sort_index()
    merged = merged.reindex(time_index)
    merged = merged.interpolate(method="time", limit_direction="both")
    merged = merged.ffill().bfill()
    return merged


def normalize_frame(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return frame
    normalized = frame.copy()
    for column_name in normalized.columns:
        max_value = float(normalized[column_name].abs().max())
        if max_value > 0:
            normalized[column_name] = normalized[column_name] / max_value
        else:
            normalized[column_name] = 0.0
    return normalized


def calendar_features(time_index: pd.DatetimeIndex) -> pd.DataFrame:
    plain_index = time_index.tz_localize(None) if time_index.tz is not None else time_index
    return pd.DataFrame(
        {
            "HourOfDay": plain_index.hour,
            "DayOfYear": plain_index.dayofyear,
            "Month": plain_index.month,
            "Weekday": plain_index.dayofweek,
        },
        index=time_index,
    )


def build_grid_from_csv(raw_grid_dir: Path) -> dict[str, list[dict[str, Any]]]:
    def read_records(patterns: list[str]) -> list[dict[str, Any]]:
        for pattern in patterns:
            matches = sorted(raw_grid_dir.glob(pattern))
            if matches:
                table = pd.read_csv(matches[0])
                return table.to_dict(orient="records")
        return []

    nodes = read_records(["nodes*.csv", "*node*.csv"])
    lines = read_records(["lines*.csv", "*line*.csv"])
    generators = read_records(["generators*.csv", "*generator*.csv", "*gen*.csv"])
    return {"nodes": nodes, "lines": lines, "generators": generators}


def load_grid_topology(raw_grid_dir: Path) -> dict[str, Any]:
    json_candidates = sorted(raw_grid_dir.glob("*.json"))
    if json_candidates:
        with json_candidates[0].open("r", encoding="utf-8") as json_file:
            payload = json.load(json_file)
        payload.setdefault("nodes", [])
        payload.setdefault("lines", [])
        payload.setdefault("generators", [])
        return payload
    return build_grid_from_csv(raw_grid_dir)


def build_time_index(config: dict[str, Any]) -> pd.DatetimeIndex:
    timezone_name = config.get("timezone", None)
    index = pd.date_range(
        start=config["start"],
        end=config["end"],
        freq=config.get("freq", "1h"),
        tz=timezone_name if timezone_name else None,
    )
    return index


def ensure_output_dirs(config: dict[str, Any]) -> tuple[Path, Path]:
    processed_dir = Path(config["processed_dir"])
    final_dir = Path(config["final_dir"])
    processed_dir.mkdir(parents=True, exist_ok=True)
    final_dir.mkdir(parents=True, exist_ok=True)
    return processed_dir, final_dir


def save_outputs(
    config: dict[str, Any],
    trim_input: pd.DataFrame,
    dpgmm_input: pd.DataFrame,
    merged_aligned: pd.DataFrame,
    grid_topology: dict[str, Any],
    integrity_report: dict[str, Any],
) -> PipelineArtifacts:
    processed_dir, final_dir = ensure_output_dirs(config)

    trim_path = processed_dir / "TRIM_input.csv"
    dpgmm_path = processed_dir / "DPGMM_input.csv"
    merged_path = processed_dir / "aligned_merged.csv"
    grid_path = processed_dir / "grid_topology.json"
    report_path = processed_dir / "integrity_report.json"

    trim_to_save = trim_input.copy()
    trim_to_save.index = trim_to_save.index.tz_localize(None) if trim_to_save.index.tz is not None else trim_to_save.index
    trim_to_save.reset_index(names=["timestamp"]).to_csv(trim_path, index=False, encoding="utf-8")

    dpgmm_to_save = dpgmm_input.copy()
    dpgmm_to_save.to_csv(dpgmm_path, index=False, encoding="utf-8")

    merged_to_save = merged_aligned.copy()
    merged_to_save.index = merged_to_save.index.tz_localize(None) if merged_to_save.index.tz is not None else merged_to_save.index
    merged_to_save.reset_index(names=["timestamp"]).to_csv(merged_path, index=False, encoding="utf-8")

    with grid_path.open("w", encoding="utf-8") as grid_file:
        json.dump(grid_topology, grid_file, ensure_ascii=False, indent=2)
    with report_path.open("w", encoding="utf-8") as report_file:
        json.dump(integrity_report, report_file, ensure_ascii=False, indent=2)

    shutil.copy2(trim_path, final_dir / trim_path.name)
    shutil.copy2(dpgmm_path, final_dir / dpgmm_path.name)
    shutil.copy2(merged_path, final_dir / merged_path.name)
    shutil.copy2(grid_path, final_dir / grid_path.name)
    shutil.copy2(report_path, final_dir / report_path.name)

    return PipelineArtifacts(
        trim_path=trim_path,
        dpgmm_path=dpgmm_path,
        grid_path=grid_path,
        report_path=report_path,
        merged_path=merged_path,
    )


def make_integrity_report(
    time_index: pd.DatetimeIndex,
    wind_norm: pd.DataFrame,
    pv_norm: pd.DataFrame,
    load_norm: pd.DataFrame,
    weather_aligned: pd.DataFrame,
    grid_topology: dict[str, Any],
) -> dict[str, Any]:
    def section_report(name: str, frame: pd.DataFrame) -> dict[str, Any]:
        start_time = str(frame.index.min()) if not frame.empty else None
        end_time = str(frame.index.max()) if not frame.empty else None
        return {
            "name": name,
            "rows": int(len(frame)),
            "columns": int(frame.shape[1]),
            "missing_values": int(frame.isna().sum().sum()) if not frame.empty else 0,
            "start": start_time,
            "end": end_time,
        }

    expected_rows = int(len(time_index))
    report = {
        "expected_rows": expected_rows,
        "time_start": str(time_index.min()),
        "time_end": str(time_index.max()),
        "wind": section_report("wind", wind_norm),
        "pv": section_report("pv", pv_norm),
        "load": section_report("load", load_norm),
        "weather": section_report("weather", weather_aligned),
        "grid": {
            "nodes": len(grid_topology.get("nodes", [])),
            "lines": len(grid_topology.get("lines", [])),
            "generators": len(grid_topology.get("generators", [])),
        },
    }
    report["length_consistent"] = all(
        current["rows"] in (0, expected_rows)
        for current in (report["wind"], report["pv"], report["load"], report["weather"])
    )
    report["grid_complete"] = all(
        report["grid"][item] > 0 for item in ("nodes", "lines", "generators")
    )
    report["content_complete"] = all(
        current["columns"] > 0
        for current in (report["wind"], report["pv"], report["load"], report["weather"])
    )
    report["dataset_ready"] = bool(
        report["length_consistent"] and report["grid_complete"] and report["content_complete"]
    )
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="构建风光+气象+负荷+配网数据集，输出 TRIM / DPGMM / Grid 输入文件。")
    parser.add_argument(
        "--config",
        default="scripts/dataset_config.example.json",
        help="配置文件路径，默认 scripts/dataset_config.example.json",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = load_config(Path(args.config))
    timezone_name = config.get("timezone", None)
    time_index = build_time_index(config)

    source_frames = collect_source_frames(raw_dirs=config["raw_dirs"], timezone_name=timezone_name)
    wind_aligned = align_frames(source_frames["wind"], time_index)
    pv_aligned = align_frames(source_frames["pv"], time_index)
    load_aligned = align_frames(source_frames["load"], time_index)
    weather_aligned = align_frames(source_frames["weather"], time_index)

    wind_norm = normalize_frame(wind_aligned)
    pv_norm = normalize_frame(pv_aligned)
    load_norm = normalize_frame(load_aligned)

    trim_parts = [wind_norm, pv_norm, load_norm, weather_aligned, calendar_features(time_index)]
    trim_input = pd.concat(trim_parts, axis=1)
    dpgmm_input = pd.concat([wind_norm, pv_norm], axis=1)
    merged_aligned = pd.concat([wind_aligned, pv_aligned, load_aligned, weather_aligned], axis=1)

    raw_grid_dir = Path(config["raw_dirs"]["grid"])
    grid_topology = load_grid_topology(raw_grid_dir)
    integrity_report = make_integrity_report(
        time_index=time_index,
        wind_norm=wind_norm,
        pv_norm=pv_norm,
        load_norm=load_norm,
        weather_aligned=weather_aligned,
        grid_topology=grid_topology,
    )

    artifacts = save_outputs(
        config=config,
        trim_input=trim_input,
        dpgmm_input=dpgmm_input,
        merged_aligned=merged_aligned,
        grid_topology=grid_topology,
        integrity_report=integrity_report,
    )

    print(f"TRIM 输入文件: {artifacts.trim_path}")
    print(f"DPGMM 输入文件: {artifacts.dpgmm_path}")
    print(f"配网拓扑文件: {artifacts.grid_path}")
    print(f"对齐总表文件: {artifacts.merged_path}")
    print(f"完整性报告: {artifacts.report_path}")
    print(f"长度一致性: {integrity_report['length_consistent']}")
    print(f"配网完整性: {integrity_report['grid_complete']}")
    print(f"内容完整性: {integrity_report['content_complete']}")
    print(f"数据集可用: {integrity_report['dataset_ready']}")


if __name__ == "__main__":
    main()
