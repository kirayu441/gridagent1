from __future__ import annotations

import argparse
import json
import os
import re
from pathlib import Path
from typing import Any

import pandas as pd
import requests


def load_config(config_path: Path) -> dict[str, Any]:
    with config_path.open("r", encoding="utf-8") as config_file:
        return json.load(config_file)


def resolve_env_template(value: str) -> str:
    match = re.fullmatch(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}", value.strip())
    if not match:
        return value
    env_key = match.group(1)
    return os.getenv(env_key, "")


def ensure_parent_folder(file_path: Path) -> None:
    file_path.parent.mkdir(parents=True, exist_ok=True)


def fetch_to_file(url: str, output_path: Path, timeout_seconds: int = 120) -> None:
    ensure_parent_folder(output_path)
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    }
    response = requests.get(url, headers=headers, timeout=timeout_seconds)
    response.raise_for_status()
    output_path.write_bytes(response.content)


def response_to_frame(payload: Any) -> pd.DataFrame:
    if isinstance(payload, dict) and "data" in payload:
        payload = payload["data"]
    if isinstance(payload, dict):
        sample_value = next(iter(payload.values())) if payload else None
        if isinstance(sample_value, dict):
            frame = pd.DataFrame.from_dict(payload, orient="index")
        else:
            frame = pd.DataFrame({"power": payload})
        index_as_str = pd.Index([str(item) for item in frame.index])
        if len(index_as_str) > 0 and index_as_str.str.fullmatch(r"\d{11,}").all():
            frame.index = pd.to_datetime(index_as_str.astype("int64"), unit="ms", errors="coerce")
        else:
            frame.index = pd.to_datetime(frame.index, errors="coerce")
        frame = frame[~frame.index.isna()]
        frame = frame.sort_index()
        frame.index.name = "timestamp"
        return frame.reset_index()
    if isinstance(payload, list):
        frame = pd.DataFrame(payload)
        timestamp_columns = [column_name for column_name in frame.columns if "time" in column_name.lower() or "date" in column_name.lower()]
        if timestamp_columns:
            first_timestamp_column = timestamp_columns[0]
            frame[first_timestamp_column] = pd.to_datetime(frame[first_timestamp_column], errors="coerce")
            frame = frame.dropna(subset=[first_timestamp_column]).sort_values(first_timestamp_column)
        return frame
    raise ValueError("Renewables.ninja 响应格式无法识别。")


def split_date_chunks(date_from: str, date_to: str, chunk_days: int = 31) -> list[tuple[str, str]]:
    start = pd.to_datetime(date_from)
    end = pd.to_datetime(date_to)
    if pd.isna(start) or pd.isna(end) or start > end:
        return [(date_from, date_to)]
    chunks: list[tuple[str, str]] = []
    current = start
    while current <= end:
        current_end = min(current + pd.Timedelta(days=chunk_days - 1), end)
        chunks.append((current.strftime("%Y-%m-%d"), current_end.strftime("%Y-%m-%d")))
        current = current_end + pd.Timedelta(days=1)
    return chunks


def request_json_with_retry(endpoint_url: str, headers: dict[str, str], params: dict[str, Any], retries: int = 3) -> Any:
    last_error: Exception | None = None
    for _ in range(retries):
        try:
            response = requests.get(endpoint_url, headers=headers, params=params, timeout=180)
            try:
                response.raise_for_status()
            except requests.HTTPError as err:
                error_hint = response.text.strip().replace("\n", " ")
                if len(error_hint) > 300:
                    error_hint = error_hint[:300] + "..."
                raise RuntimeError(f"{err} | 详情: {error_hint}") from err
            return response.json()
        except Exception as err:
            last_error = err
    raise RuntimeError(f"请求失败，重试 {retries} 次仍未成功: {last_error}")


def fetch_renewables_ninja_series(
    base_url: str,
    endpoint_name: str,
    token: str,
    query_params: dict[str, Any],
    output_csv: Path,
) -> None:
    headers = {"Authorization": f"Token {token}"}
    endpoint_url = f"{base_url.rstrip('/')}/{endpoint_name}"
    date_from = query_params.get("date_from")
    date_to = query_params.get("date_to")
    chunk_frames: list[pd.DataFrame] = []
    if date_from and date_to:
        for chunk_start, chunk_end in split_date_chunks(str(date_from), str(date_to), chunk_days=31):
            chunk_params = dict(query_params)
            chunk_params["date_from"] = chunk_start
            chunk_params["date_to"] = chunk_end
            payload = request_json_with_retry(endpoint_url=endpoint_url, headers=headers, params=chunk_params, retries=3)
            chunk_frames.append(response_to_frame(payload))
    else:
        payload = request_json_with_retry(endpoint_url=endpoint_url, headers=headers, params=query_params, retries=3)
        chunk_frames.append(response_to_frame(payload))

    frame = pd.concat(chunk_frames, axis=0, ignore_index=True)
    if "timestamp" in frame.columns:
        frame["timestamp"] = pd.to_datetime(frame["timestamp"], errors="coerce")
        frame = frame.dropna(subset=["timestamp"]).drop_duplicates(subset=["timestamp"]).sort_values("timestamp")
        frame["timestamp"] = frame["timestamp"].dt.strftime("%Y-%m-%d %H:%M:%S")
    ensure_parent_folder(output_csv)
    frame.to_csv(output_csv, index=False, encoding="utf-8")


def run_manual_downloads(config: dict[str, Any]) -> None:
    for download_item in config.get("manual_downloads", []):
        url = str(download_item["url"])
        output_path = Path(download_item["output"])
        try:
            fetch_to_file(url=url, output_path=output_path)
            print(f"已下载: {url} -> {output_path}")
        except requests.RequestException as err:
            print(f"下载失败(已跳过): {url} | 原因: {err}")


def run_renewables_ninja(config: dict[str, Any]) -> None:
    ninja_cfg = config.get("renewables_ninja", {})
    if not ninja_cfg.get("enabled", False):
        print("Renewables.ninja 自动下载未启用。")
        return
    token = resolve_env_template(str(ninja_cfg.get("api_token", "")).strip())
    if not token:
        print("未提供有效 Renewables.ninja token，已跳过风光自动下载（可用 ${RENEWABLES_NINJA_TOKEN}）。")
        return

    raw_dirs = config["raw_dirs"]
    wind_output = Path(raw_dirs["wind_solar"]) / "renewables_ninja_wind.csv"
    pv_output = Path(raw_dirs["wind_solar"]) / "renewables_ninja_pv.csv"
    base_url = str(ninja_cfg.get("base_url", "https://www.renewables.ninja/api/data"))

    wind_params = dict(ninja_cfg.get("wind_params", {}))
    pv_params = dict(ninja_cfg.get("pv_params", {}))

    try:
        fetch_renewables_ninja_series(
            base_url=base_url,
            endpoint_name="wind",
            token=token,
            query_params=wind_params,
            output_csv=wind_output,
        )
        print(f"已下载 Renewables.ninja 风电数据 -> {wind_output}")
    except Exception as err:
        print(f"风电下载失败(已跳过): {err}")

    try:
        fetch_renewables_ninja_series(
            base_url=base_url,
            endpoint_name="pv",
            token=token,
            query_params=pv_params,
            output_csv=pv_output,
        )
        print(f"已下载 Renewables.ninja 光伏数据 -> {pv_output}")
    except Exception as err:
        print(f"光伏下载失败(已跳过): {err}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="下载风光/负荷/配网原始数据（支持 Renewables.ninja + 通用 URL）。")
    parser.add_argument(
        "--config",
        default="scripts/dataset_config.example.json",
        help="配置文件路径，默认 scripts/dataset_config.example.json",
    )
    parser.add_argument(
        "--skip-manual-downloads",
        action="store_true",
        help="跳过 manual_downloads，只执行 Renewables.ninja 下载。",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config_path = Path(args.config)
    config = load_config(config_path)
    if args.skip_manual_downloads:
        print("已跳过 manual_downloads。")
    else:
        run_manual_downloads(config)
    run_renewables_ninja(config)
    print("原始数据下载步骤完成。")


if __name__ == "__main__":
    main()
