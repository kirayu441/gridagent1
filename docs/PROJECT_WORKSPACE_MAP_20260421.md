# GridAgent1 工作区整理图谱

更新时间：2026-04-21

## 1. 先说结论

当前 `gridagent1` 工作区不是“东西少但乱”，而是“东西很多、层次混在一起”。

最重要的结构可以压缩成 5 层：

1. `configs/`：主流程配置
2. `scripts/`：算法实现和主流程入口
3. `results/`：所有运行结果与实验产物
4. `dashboard/`：可视化展示
5. `docs/` + `paper/`：说明、论文、实验记录

另外，根目录还有一批 `tmp_*`、`streamlit*.log`、`scripts.zip` 这类临时或辅助文件，不属于主线。

---

## 2. 顶层目录梳理

### 核心目录

- `configs/`
  - 主流程配置文件
  - 当前最关键的是：
    - `gridagent_framework.formal2024.json`
    - `gridagent_framework.formal2024.quicktest.json`
    - `gridagent_framework.ieee118_n60.metapath_opt124.json`

- `scripts/`
  - 项目主逻辑目录
  - 包含主流程入口、各 Stage 模块、实验脚本、数据准备脚本
  - 是整个项目最值得重点看的目录

- `results/`
  - 输出结果目录
  - 文件最多，当前约 5000+ 个文件
  - 包含主流程 run、Stage6 实验、Stage7 调度结果、Stage8 物理校核结果等

- `dashboard/`
  - Streamlit 可视化页面
  - 当前核心文件：
    - `gridagent_dashboard.py`
    - `README.md`

- `data_final/`
  - 数据集与拓扑输入
  - 包含 `formal_guangdong_2024`、`ieee118_n60`、`scaled` 等数据

- `docs/`
  - 项目说明、实验记录、结构说明、论文风格文档
  - 当前已经有不少整理材料

- `paper/`
  - 论文内容草稿

### 非主线但存在的文件

- `.venv/`
  - Python 虚拟环境
- `streamlit.stdout.log`
- `streamlit.stderr.log`
  - 本地可视化启动日志
- `tmp_*.txt/json`
  - 临时摘录、笔记、代码包材料
- `scripts.zip`
  - 脚本目录压缩包
- `requirements-dataset.txt`
  - 数据处理依赖

---

## 3. scripts 目录重新分类

`scripts/` 里混着 4 类文件，建议以后脑内按这 4 类区分。

### A. 主流程核心

这些文件是“产品主线”。

- `gridagent_framework.py`
  - 主框架入口
  - 串联 Stage1 到 Stage8

- `wind_pv_uncertainty_modeling.py`
  - Stage1 风光不确定性建模

- `component_failure_probability.py`
  - Stage2 设备/线路失效概率

- `spatiotemporal_contingency_generator.py`
  - Stage3 时空故障场景生成

- `load_prioritization_scheduling.py`
  - Stage4 负荷优先级调度

- `multi_criteria_resilience_assessment.py`
  - Stage5 韧性评估与 EWM-TOPSIS

- `gnn_warning_module.py`
  - Stage6 GNN 风险预警

- `dispatch_optimization_module.py`
  - Stage7 调度优化

- `steady_state_physics_module.py`
  - Stage8 稳态物理校核与规则闭环

### B. 数据与拓扑准备

- `build_dataset.py`
- `prepare_formal_sources.py`
- `download_data.py`
- `generate_mock_data.py`
- `generate_scaled_topology.py`
- `build_ieee_subgrid.py`

作用：
- 准备输入数据
- 构造测试系统
- 生成缩放拓扑或演示数据

### C. 主流程辅助与导出

- `export_standard_results.py`
- `run_end_to_end_resilience.py`
- `multiscenario_fusion_run.py`

作用：
- 跑整链条
- 导出标准结果
- 做多场景融合类流程

### D. 实验/论文/对比脚本

这些不是主产线，而是研究验证线。

- `stage1_method_comparison.py`
- `stage123_method_comparison.py`
- `analyze_stage123_results.py`
- `gnn_ablation_experiment.py`
- `run_stage6_attribution_experiment.py`
- `run_stage6_planA_experiment.py`
- `run_warning_scale_experiments.py`
- `run_paper_comparison_experiment.py`
- `module_sensitivity_analysis.py`
- `multiscenario_fusion_experiment.py`

建议理解为：
- “为了证明方法有效”的实验工具箱
- 不是日常主流程必须先看的部分

### E. 历史与遗留

- `legacy/typhoon_grid_resilience_demo.py`
- `legacy/run_matpower_resilience_batch.m`

这类文件建议视为历史参考，不作为当前主线阅读入口。

---

## 4. scripts 目录建议阅读顺序

如果以后要快速重新进入项目，建议按下面顺序看：

1. `scripts/gridagent_framework.py`
2. `configs/gridagent_framework.formal2024.json`
3. `scripts/gnn_warning_module.py`
4. `scripts/dispatch_optimization_module.py`
5. `scripts/steady_state_physics_module.py`
6. `dashboard/gridagent_dashboard.py`

这条顺序对应的是当前项目最重要的主线：

`Stage6 预警 -> Stage7 调度 -> Stage8 物理校核 -> Dashboard 展示`

---

## 5. configs 目录梳理

当前配置文件不多，但用途不同：

- `gridagent_framework.formal2024.json`
  - 正式主流程配置
  - 当前最重要

- `gridagent_framework.formal2024.quicktest.json`
  - 快速测试配置

- `gridagent_framework.ieee118_n60.metapath_opt124.json`
  - IEEE 118 / n60 相关试验配置

- `multiscenario_fusion.formal2024.json`
  - 多场景融合相关配置

建议：
- 主流程默认只盯 `gridagent_framework.formal2024.json`
- 其余配置作为专项实验配置

---

## 6. results 目录重新理解

`results/` 是当前最容易让人混乱的目录，因为里面既有主流程结果，也有单模块测试、论文实验、消融实验、快照、烟雾测试。

建议把它脑内拆成 5 类：

### A. 主流程结果

- `results/gridagent_framework/*`

这是最重要的结果目录。

当前主要 run 包括：

- `formal2024_full_baseline_20260310_233109`
- `formal2024_full_metapath_tuned_20260407`
- `formal2024_quick_std`
- `ieee118_n60_stagewise_20260324_195044`

如果以后要看“完整链条最后产出”，优先看这里。

### B. 标准导出结果

- `results/*_standard`

例如：

- `formal2024_full_baseline_20260310_233109_standard`
- `formal2024_quick_std_standard`

这类目录是把结果整理成统一结构后的标准输出版本。

### C. 单模块输出

例如：

- `results/wind_pv_uncertainty/`
- `results/component_failure_probability/`
- `results/load_prioritization_scheduling/`
- `results/dispatch_optimization/`
- `results/resilience/`
- `results/warning/`

作用：
- 单独查看某个 Stage 的运行结果
- 更适合开发或调试阶段

### D. Stage6 专项实验

- `results/early_warning/`
- `results/ablation/`

这是研究量最大、文件也最多的一块。

包括：
- Stage6 attribution
- Plan A 实验
- 模型消融
- 多种标签/元路径/门控组合对比

建议把它理解成：
- “论文实验仓”
- 不是主流程结果仓

### E. 论文与辅助产物

例如：

- `results/paper_comparison/`
- `results/multiscenario_fusion/`
- `results/timepoint_snapshots_*`
- `results/pending_work.md`

---

## 7. dashboard 目录梳理

这个目录现在很关键，因为它承担了“对外讲清项目”的职责。

核心文件：

- `dashboard/gridagent_dashboard.py`
  - 当前 Streamlit 页面主文件

- `dashboard/README.md`
  - 页面使用说明

- `dashboard/requirements-visualization.txt`
  - 可视化依赖

说明：
- 现在页面已经接到了 Stage8
- 并且开始做“运行驾驶舱 / 研究分析台”的双层结构
- 这个目录未来应该继续收敛，而不是继续膨胀

---

## 8. docs 目录梳理

`docs/` 实际上已经有很多重要信息，但目前比较分散。

建议按功能理解：

### A. 项目结构类

- `PROJECT_STRUCTURE.md`
- `PROJECT_TREE_FULL.txt`
- `PROJECT_FILE_CATALOG_20260407.md`
- `PROJECT_CORE_INDEX_20260407.md`
- `PROJECT_FULL_SUMMARY_FOR_AI.md`

### B. 结果总结类

- `formal2024_fullrun_results_report.md`
- `GridAgent_PaperStyle_Overview_Formal2024.md`
- `GridAgent_Formal2024_Complete_Paper.md`

### C. Stage6 专题类

- `STAGE6_WARNING_UPLIFT_REPORT_20260408.md`
- `STAGE6_ATTRIBUTION_EXPERIMENT_DESIGN_20260413.md`
- `STAGE6_PLANA_C3PO_REF_REPORT_20260415.md`
- `STAGE6_PLANA_A0A3_CODEPACK_FOR_GPT_20260415.md`
- `METAPATH_TUNE12_REPORT_20260407.md`

### D. 可视化与使用说明

- `GridAgent_Visualization_User_Guide.md`
- `GPT_PROJECT_GUIDE_20260413.md`

### E. 清理建议与历史记录

- `RESULTS_CLEANUP_SUGGESTIONS_20260407.md`
- `CLEANUP_LOG.md`

---

## 9. data_final 目录梳理

当前数据目录可以理解为“项目输入仓”。

主要内容：

- 根目录数据：
  - `aligned_merged.csv`
  - `DPGMM_input.csv`
  - `TRIM_input.csv`
  - `grid_topology.json`

- 正式数据集：
  - `formal_guangdong_2024/`

- IEEE 测试系统：
  - `ieee118_n60/`
  - `ieee118_full/`

- 缩放拓扑：
  - `scaled/g60_n75/`

建议：
- 以后把正式主流程默认只绑定 `formal_guangdong_2024`
- 其余目录作为测试或扩展系统

---

## 10. 根目录临时文件整理建议

这些文件当前不属于主线阅读入口：

- `tmp_DPGMN_text.txt`
- `tmp_gnn_warning_text.txt`
- `tmp_H2DGL_pages5_8.txt`
- `tmp_load_priority_dispatch_opt.txt`
- `tmp_script_api_summary.json`
- `tmp_typhoon_wind_field_text.txt`
- `streamlit.stdout.log`
- `streamlit.stderr.log`
- `scripts.zip`

建议后续单独放入一个目录，例如：

- `tmp_notes/`
- `logs/`
- `archives/`

当前先不移动，避免影响现有工作流。

---

## 11. 最终建议：以后怎么理解这个项目

如果只保留最重要的一句话：

`这是一个围绕台风电网风险的“场景生成 -> 风险预警 -> 调度优化 -> 物理校核”主流程项目，外加大量 Stage6/论文实验脚本和结果。`

如果只保留最重要的 4 个目录：

1. `configs/`
2. `scripts/`
3. `results/gridagent_framework/`
4. `dashboard/`

如果只保留最重要的 6 个文件：

1. `configs/gridagent_framework.formal2024.json`
2. `scripts/gridagent_framework.py`
3. `scripts/gnn_warning_module.py`
4. `scripts/dispatch_optimization_module.py`
5. `scripts/steady_state_physics_module.py`
6. `dashboard/gridagent_dashboard.py`

---

## 12. 后续整理建议

建议下一轮真正动手整理时，按下面顺序进行：

1. 先整理根目录
   - 临时文件、日志、压缩包归档

2. 再整理 `scripts/`
   - 主流程脚本
   - 数据准备脚本
   - 实验脚本
   - legacy

3. 再整理 `results/`
   - 主流程结果
   - 标准输出
   - 单模块输出
   - 实验结果

4. 最后整理 `docs/`
   - 合并重复说明文档
   - 保留一份主索引

这一步做完之后，整个项目会清楚很多。
