# 风光 + 气象 + 负荷 + 配网数据集流水线

## 1. 安装环境

```bash
pip install -r requirements-dataset.txt
```

## 2. 目录结构

本仓库已创建以下目录：

- `data_raw/wind_solar`
- `data_raw/load`
- `data_raw/weather`
- `data_raw/grid`
- `data_processed`
- `data_final`
- `scripts`

## 3. 配置文件

默认配置：`scripts/dataset_config.example.json`

可按实验区域修改：

- `start` / `end` / `freq`
- `timezone`
- `renewables_ninja` 参数
- `manual_downloads` 下载源

已新增正式模板配置（广东 2025）：

- `scripts/dataset_config.formal_guangdong_2025.json`
- `scripts/dataset_config.formal_guangdong_2024.json`（推荐，Renewables.ninja 当前可用截止 2024-12-31）

## 4. 下载原始数据

```bash
python scripts/download_data.py --config scripts/dataset_config.example.json
```

若只想快速拉取 Renewables.ninja（跳过网页下载）：

```bash
python scripts/download_data.py --config scripts/dataset_config.formal_guangdong_2024.json --skip-manual-downloads
```

说明：

- `manual_downloads` 会按 URL 下载到指定路径。
- 若要自动下载 Renewables.ninja，请在配置中设置：
  - `renewables_ninja.enabled = true`
  - `renewables_ninja.api_token = 你的 token`
  - 或设置环境变量：`RENEWABLES_NINJA_TOKEN`
- 若 `figshare` 返回 403，请手工下载 SDWPF 文件后放入 `data_raw/wind_solar/`。

正式模板运行示例：

```bash
set RENEWABLES_NINJA_TOKEN=你的token
python scripts/download_data.py --config scripts/dataset_config.formal_guangdong_2025.json
python scripts/build_dataset.py --config scripts/dataset_config.formal_guangdong_2025.json
```

如遇到提示 `date_to must be 2024-12-31 or earlier`，请改用：

```bash
python scripts/download_data.py --config scripts/dataset_config.formal_guangdong_2024.json
python scripts/build_dataset.py --config scripts/dataset_config.formal_guangdong_2024.json
```

## 5. 生成示例原始数据（可选）

如果暂时没有真实数据，可先生成一套可跑通数据：

```bash
python scripts/generate_mock_data.py --config scripts/dataset_config.example.json
```

## 5.1 一键补全 formal 负荷+配网（推荐）

当你已有风光数据，但缺 `load.csv` / `grid.json` 时可执行：

```bash
python scripts/prepare_formal_sources.py --config scripts/dataset_config.formal_guangdong_2024.json
```

默认行为：

- 从 Zenodo 拉取省级小时负荷，默认使用 `GD,GX` 两列生成 `load_region1,load_region2`
- 用 `pandapower` 的 CIGRE MV（含 `pv_wind`）生成标准配网 `grid.json`
- 同时写入两套路径：
  - `data_raw/formal_guangdong_2024/load.csv` 与 `data_raw/formal_guangdong_2024/load/load.csv`
  - `data_raw/formal_guangdong_2024/grid.json` 与 `data_raw/formal_guangdong_2024/grid/grid.json`

## 6. 构建实验输入数据集

```bash
python scripts/build_dataset.py --config scripts/dataset_config.example.json
```

输出文件：

- `data_processed/TRIM_input.csv`
- `data_processed/DPGMM_input.csv`
- `data_processed/aligned_merged.csv`
- `data_processed/grid_topology.json`
- `data_processed/integrity_report.json`

同名文件会同步复制到 `data_final/`。

## 7. 完整性检查指标

`integrity_report.json` 中包含：

- 各模块行数、列数、缺失值数量
- 时间覆盖范围
- `length_consistent`（时间序列长度是否一致）
- `grid_complete`（配网节点/线路/机组是否齐全）
- `content_complete`（风光/负荷/气象列是否齐全）
- `dataset_ready`（可直接用于 TRIM + DPGMM + GridAgent）
