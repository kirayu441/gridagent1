# IEEE60 节点天气数据来源说明

## 1. 结论先行

当前 `ieee118_n60` 的 60 节点天气并不是“复制 60 份同一条天气曲线”，也不是每个节点直接接入独立气象站。  
它采用的是：

1. 系统级时序（风电/PV/负荷/风速）作为全局基线；
2. 基于节点空间位置的影响场（`influence`）生成节点差异；
3. 用节点份额（风电装机份额、光伏装机份额、负荷份额）做加权归一化，保证总量一致。

## 2. 基线时间序列来源

输入文件：`data_final/formal_guangdong_2024/aligned_merged.csv`

- 风电总量：`wind_renewables_ninja_wind_electricity`
- 光伏总量：`pv_renewables_ninja_pv_electricity`
- 负荷总量：`load_load_load_region1 + load_load_load_region2`
- 风速：`wind_renewables_ninja_wind_wind_speed`

## 3. 60 节点差异如何生成

### 3.1 节点坐标

优先使用 `grid_topology.json` 中每个节点的 `lat/lon`（若缺失，再退化到 `local_x/local_y`，最后才使用环形占位坐标）。

### 3.2 空间影响场

在每个时刻构造一个随时间平滑移动的“天气中心”，节点离中心越近，`influence` 越高（取值 0-1）。

### 3.3 四类因子

- `wind_factor = clip(0.65 + 0.75 * influence, 0.35, 1.60)`
- `pv_factor = clip(1.08 - 0.40 * influence, 0.35, 1.35)`
- `load_factor = clip(0.95 + 0.14 * influence, 0.75, 1.35)`
- `wind_speed_factor = clip(0.55 + 0.95 * influence, 0.35, 1.70)`

其中前三项会按对应份额做加权归一化，使时刻总量守恒。

## 4. 可核验输出

运行预警模块后会自动导出：

- `node_weather_timeseries.csv`：全时段每节点天气与因子；
- `node_weather_horizon.csv`：预警窗口内每节点天气与因子；
- `node_weather_summary.csv`：按节点聚合后的平均影响强度与平均天气量；
- `warning_report.json` 中 `node_weather_generation` 字段：完整来源与公式说明。

这四项用于论文中回答“节点天气数据如何得到”。

