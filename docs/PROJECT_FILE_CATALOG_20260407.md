# Project File Catalog (Auto-Generated)

- Generated on: 2026-04-07
- Root: C:\Users\yuhan\Desktop\gridagent1
- Total files indexed: 1513

## File Count by Top-Level

| Top-Level | Count |
|---|---:|
| `results` | 1414 |
| `scripts` | 56 |
| `data_final` | 13 |
| `docs` | 13 |
| `configs` | 4 |
| `dashboard` | 4 |
| `paper` | 2 |
| `requirements-dataset.txt` | 1 |
| `tmp_DPGMN_text.txt` | 1 |
| `tmp_gnn_warning_text.txt` | 1 |
| `tmp_H2DGL_pages5_8.txt` | 1 |
| `tmp_load_priority_dispatch_opt.txt` | 1 |
| `tmp_script_api_summary.json` | 1 |
| `tmp_typhoon_wind_field_text.txt` | 1 |

## File Count by Extension

| Extension | Count |
|---|---:|
| `.csv` | 1090 |
| `.json` | 263 |
| `.npy` | 41 |
| `.py` | 36 |
| `.log` | 25 |
| `.md` | 25 |
| `.pyc` | 19 |
| `.txt` | 12 |
| `.m` | 1 |
| `.zip` | 1 |

## Full Inventory

Each row includes relative path and rough content description.

### configs

| File | Rough Content |
|---|---|
| `configs/gridagent_framework.formal2024.json` | JSON object; top keys: seed, output_root, paths, wind_pv, failure, contingency, scheduling, warning, .... |
| `configs/gridagent_framework.formal2024.quicktest.json` | JSON object; top keys: seed, output_root, paths, wind_pv, failure, contingency, scheduling, warning, .... |
| `configs/gridagent_framework.ieee118_n60.metapath_opt124.json` | JSON object; top keys: seed, output_root, paths, wind_pv, failure, contingency, scheduling, warning, .... |
| `configs/multiscenario_fusion.formal2024.json` | JSON object; top keys: seed, output_root, base_inputs, typhoon_intensity_levels, wind_pv_variants, load_scenarios, env_sampling, strategy_pool. |

### dashboard

| File | Rough Content |
|---|---|
| `dashboard/__pycache__/gridagent_dashboard.cpython-311.pyc` | Compiled Python bytecode cache artifact. |
| `dashboard/gridagent_dashboard.py` | Python module/script; key symbols: safe_csv, safe_json, discover_standard_runs. |
| `dashboard/README.md` | Readme/instructions for the directory. |
| `dashboard/requirements-visualization.txt` | Text/markdown notes; starts with: streamlit>=1.35 |

### data_final

| File | Rough Content |
|---|---|
| `data_final/aligned_merged.csv` | Aligned weather-generation-load time series. |
| `data_final/DPGMM_input.csv` | Input features for wind/PV uncertainty modeling (DPGMM and variants). |
| `data_final/formal_guangdong_2024/aligned_merged.csv` | Aligned weather-generation-load time series. |
| `data_final/formal_guangdong_2024/DPGMM_input.csv` | Input features for wind/PV uncertainty modeling (DPGMM and variants). |
| `data_final/formal_guangdong_2024/grid_topology.json` | Grid topology with buses/lines/generators and static parameters. |
| `data_final/formal_guangdong_2024/integrity_report.json` | Data integrity and alignment check report. |
| `data_final/formal_guangdong_2024/TRIM_input.csv` | Input table for contingency/scheduling modules. |
| `data_final/grid_topology.json` | Grid topology with buses/lines/generators and static parameters. |
| `data_final/ieee118_full/grid_topology.json` | Grid topology with buses/lines/generators and static parameters. |
| `data_final/ieee118_n60/grid_topology.json` | Grid topology with buses/lines/generators and static parameters. |
| `data_final/integrity_report.json` | Data integrity and alignment check report. |
| `data_final/scaled/g60_n75/grid_topology.json` | Grid topology with buses/lines/generators and static parameters. |
| `data_final/TRIM_input.csv` | Input table for contingency/scheduling modules. |

### docs

| File | Rough Content |
|---|---|
| `docs/CLEANUP_LOG.md` | Text/markdown notes; starts with: # Cleanup Log |
| `docs/DATASET_PIPELINE.md` | Text/markdown notes; starts with: # 风光 + 气象 + 负荷 + 配网数据集流水线 |
| `docs/formal2024_fullrun_results_report.md` | Text/markdown notes; starts with: # GridAgent \`formal2024\` 全量实验结果报告（Baseline） |
| `docs/GridAgent_Formal2024_Complete_Paper.md` | Text/markdown notes; starts with: # GridAgent: 面向极端天气的风光不确定性驱动电网韧性评估与调度框架 |
| `docs/GridAgent_PaperStyle_Overview_Formal2024.md` | Text/markdown notes; starts with: # GridAgent 项目论文式说明（面向非本项目读者） |
| `docs/GridAgent_Visualization_User_Guide.md` | Text/markdown notes; starts with: # GridAgent1 可视化页面详细介绍（新手版） |
| `docs/IEEE60_Node_Weather_Source.md` | Text/markdown notes; starts with: # IEEE60 节点天气数据来源说明 |
| `docs/paper745.txt` | Text/markdown notes; starts with: ===== PAGE 1 ===== |
| `docs/pipeline_chain_catalog_formal2024.csv` | CSV table; columns: chain_id, failure_model, contingency_method, reserve_ratio, n_scenarios_edge, n_scenarios_cloud, run_tag_pattern. |
| `docs/pipeline_chain_catalog_formal2024.md` | Text/markdown notes; starts with: # formal2024 完整链路清单（24条） |
| `docs/PROJECT_FULL_SUMMARY_FOR_AI.md` | Text/markdown notes; starts with: # GridAgent1 项目全量上下文说明（供 GPT/AI 读取） |
| `docs/PROJECT_STRUCTURE.md` | Text/markdown notes; starts with: # Project Structure (Cleaned) |
| `docs/PROJECT_TREE_FULL.txt` | Text/markdown notes; starts with: Folder PATH listing for volume Windows-SSD |

### paper

| File | Rough Content |
|---|---|
| `paper/paper_experiment_ch/experiment_section_cn.md` | Chinese manuscript experiment section draft. |
| `paper/paper_experiment_en/experiment_section.md` | English manuscript experiment section draft. |

### requirements-dataset.txt

| File | Rough Content |
|---|---|
| `requirements-dataset.txt` | Python dependencies for data and experiment pipeline. |

### results

| File | Rough Content |
|---|---|
| `results/ablation/stage1_comparison/arima/history_series.csv` | Historical time series used as model input. |
| `results/ablation/stage1_comparison/arima/sampled_scenarios.npy` | Sampled scenario tensor for simulation input. |
| `results/ablation/stage1_comparison/arima/scenario_probabilities.csv` | Probability assigned to each generated scenario. |
| `results/ablation/stage1_comparison/arima/typical_scenarios_long.csv` | Long-form scenario table by timestamp and scenario id. |
| `results/ablation/stage1_comparison/arima/typical_scenarios.npy` | NumPy tensor of representative scenarios. |
| `results/ablation/stage1_comparison/arima/uncertainty_report.json` | Stage1 uncertainty modeling report and metrics. |
| `results/ablation/stage1_comparison/copula/history_series.csv` | Historical time series used as model input. |
| `results/ablation/stage1_comparison/copula/sampled_scenarios.npy` | Sampled scenario tensor for simulation input. |
| `results/ablation/stage1_comparison/copula/scenario_probabilities.csv` | Probability assigned to each generated scenario. |
| `results/ablation/stage1_comparison/copula/typical_scenarios_long.csv` | Long-form scenario table by timestamp and scenario id. |
| `results/ablation/stage1_comparison/copula/typical_scenarios.npy` | NumPy tensor of representative scenarios. |
| `results/ablation/stage1_comparison/copula/uncertainty_report.json` | Stage1 uncertainty modeling report and metrics. |
| `results/ablation/stage1_comparison/dpgmm/history_series.csv` | Historical time series used as model input. |
| `results/ablation/stage1_comparison/dpgmm/sampled_scenarios.npy` | Sampled scenario tensor for simulation input. |
| `results/ablation/stage1_comparison/dpgmm/scenario_probabilities.csv` | Probability assigned to each generated scenario. |
| `results/ablation/stage1_comparison/dpgmm/typical_scenarios_long.csv` | Long-form scenario table by timestamp and scenario id. |
| `results/ablation/stage1_comparison/dpgmm/typical_scenarios.npy` | NumPy tensor of representative scenarios. |
| `results/ablation/stage1_comparison/dpgmm/uncertainty_report.json` | Stage1 uncertainty modeling report and metrics. |
| `results/ablation/stage1_comparison/lstm/history_series.csv` | Historical time series used as model input. |
| `results/ablation/stage1_comparison/lstm/sampled_scenarios.npy` | Sampled scenario tensor for simulation input. |
| `results/ablation/stage1_comparison/lstm/scenario_probabilities.csv` | Probability assigned to each generated scenario. |
| `results/ablation/stage1_comparison/lstm/typical_scenarios_long.csv` | Long-form scenario table by timestamp and scenario id. |
| `results/ablation/stage1_comparison/lstm/typical_scenarios.npy` | NumPy tensor of representative scenarios. |
| `results/ablation/stage1_comparison/lstm/uncertainty_report.json` | Stage1 uncertainty modeling report and metrics. |
| `results/ablation/stage1_comparison/stage1_comparison_report.json` | JSON object; top keys: experiment, dataset, methods, comparison. |
| `results/ablation/stage1_comparison/stage1_comparison_report.md` | Text/markdown notes; starts with: # Stage1 不确定性建模方法对比实验报告 |
| `results/ablation/stage123_comparison/comparison_results.json` | JSON object; top keys: experiment, timestamp, grid_path, stages. |
| `results/ablation/stage123_comparison/comparison_summary.md` | Text/markdown notes; starts with: # Layer 4: Stage1-3 Method Comparison Results |
| `results/ablation/stage123_comparison/detailed_analysis.md` | Text/markdown notes; starts with: # Stage1-3 Method Comparison - Detailed Analysis |
| `results/ablation/stage123_comparison/stage1_uncertainty/dpgmm/formal2024/history_series.csv` | Historical time series used as model input. |
| `results/ablation/stage123_comparison/stage1_uncertainty/dpgmm/formal2024/sampled_scenarios.npy` | Sampled scenario tensor for simulation input. |
| `results/ablation/stage123_comparison/stage1_uncertainty/dpgmm/formal2024/scenario_probabilities.csv` | Probability assigned to each generated scenario. |
| `results/ablation/stage123_comparison/stage1_uncertainty/dpgmm/formal2024/typical_scenarios_long.csv` | Long-form scenario table by timestamp and scenario id. |
| `results/ablation/stage123_comparison/stage1_uncertainty/dpgmm/formal2024/typical_scenarios.npy` | NumPy tensor of representative scenarios. |
| `results/ablation/stage123_comparison/stage1_uncertainty/dpgmm/formal2024/uncertainty_report.json` | Stage1 uncertainty modeling report and metrics. |
| `results/ablation/stage123_comparison/stage2_failure/batts/failure_probability_report.json` | Stage2 component/line failure probability report. |
| `results/ablation/stage123_comparison/stage2_failure/batts/line_failure_timeseries_batts.csv` | Time-series line failure probabilities under Batts model. |
| `results/ablation/stage123_comparison/stage2_failure/schloemer/failure_probability_report.json` | Stage2 component/line failure probability report. |
| `results/ablation/stage123_comparison/stage2_failure/schloemer/line_failure_timeseries_schloemer.csv` | Time-series line failure probabilities under Schloemer model. |
| `results/ablation/stage123_comparison/stage3_contingency/c3po_ref/contingency_report.json` | Stage3 spatiotemporal contingency generation report. |
| `results/ablation/stage123_comparison/stage3_contingency/c3po_ref/contingency_scenarios_c3po_ref.csv` | CSV table; columns: scenario, scenario_id, timestamp, failed_lines, outage_line_count, disconnected_load_count, probability, method. |
| `results/ablation/stage123_comparison/stage3_contingency/c3po_ref/contingency_scenarios.csv` | Generated contingency scenarios summary table. |
| `results/ablation/stage123_comparison/stage3_contingency/c3po_ref/contingency_tensor_c3po_ref.npy` | Contingency state tensor generated by C3PO reference method. |
| `results/ablation/stage123_comparison/stage3_contingency/c3po_ref/line_probability_summary_c3po_ref.csv` | Per-line probability summary for C3PO reference method. |
| `results/ablation/stage123_comparison/stage3_contingency/c3po_ref/method_comparison.csv` | Cross-method comparison metrics table. |
| `results/ablation/stage123_comparison/stage3_contingency/c3po_ref/state_summary_c3po_ref.csv` | State occurrence summary for C3PO reference method. |
| `results/ablation/stage123_comparison/stage3_contingency/trim_ref/contingency_report.json` | Stage3 spatiotemporal contingency generation report. |
| `results/ablation/stage123_comparison/stage3_contingency/trim_ref/contingency_scenarios_trim_ref.csv` | CSV table; columns: scenario, scenario_id, timestamp, failed_lines, outage_line_count, disconnected_load_count, probability, method. |
| `results/ablation/stage123_comparison/stage3_contingency/trim_ref/contingency_scenarios.csv` | Generated contingency scenarios summary table. |
| `results/ablation/stage123_comparison/stage3_contingency/trim_ref/contingency_tensor_trim_ref.npy` | Contingency state tensor generated by TRIM reference method. |
| `results/ablation/stage123_comparison/stage3_contingency/trim_ref/line_probability_summary_trim_ref.csv` | Per-line probability summary for TRIM reference method. |
| `results/ablation/stage123_comparison/stage3_contingency/trim_ref/method_comparison.csv` | Cross-method comparison metrics table. |
| `results/ablation/stage123_comparison/stage3_contingency/trim_ref/state_summary_trim_ref.csv` | State occurrence summary for TRIM reference method. |
| `results/ablation/stage123_comparison/stage3_contingency/wang_mc/contingency_report.json` | Stage3 spatiotemporal contingency generation report. |
| `results/ablation/stage123_comparison/stage3_contingency/wang_mc/contingency_scenarios_wang_mc.csv` | CSV table; columns: scenario, scenario_id, timestamp, failed_lines, outage_line_count, disconnected_load_count, probability, method. |
| `results/ablation/stage123_comparison/stage3_contingency/wang_mc/contingency_scenarios.csv` | Generated contingency scenarios summary table. |
| `results/ablation/stage123_comparison/stage3_contingency/wang_mc/contingency_tensor_wang_mc.npy` | Contingency state tensor generated by Wang-style Monte Carlo. |
| `results/ablation/stage123_comparison/stage3_contingency/wang_mc/line_probability_summary_wang_mc.csv` | Per-line probability summary for Wang MC method. |
| `results/ablation/stage123_comparison/stage3_contingency/wang_mc/method_comparison.csv` | Cross-method comparison metrics table. |
| `results/ablation/stage123_comparison/stage3_contingency/wang_mc/state_summary_wang_mc.csv` | State occurrence summary for Wang MC method. |
| `results/ablation/stage123_comparison/stage3_contingency/wang_qmc/contingency_report.json` | Stage3 spatiotemporal contingency generation report. |
| `results/ablation/stage123_comparison/stage3_contingency/wang_qmc/contingency_scenarios_wang_qmc.csv` | CSV table; columns: scenario, scenario_id, timestamp, failed_lines, outage_line_count, disconnected_load_count, probability, method. |
| `results/ablation/stage123_comparison/stage3_contingency/wang_qmc/contingency_scenarios.csv` | Generated contingency scenarios summary table. |
| `results/ablation/stage123_comparison/stage3_contingency/wang_qmc/contingency_tensor_wang_qmc.npy` | Contingency state tensor generated by Wang-style quasi-Monte Carlo. |
| `results/ablation/stage123_comparison/stage3_contingency/wang_qmc/line_probability_summary_wang_qmc.csv` | Per-line probability summary for Wang QMC method. |
| `results/ablation/stage123_comparison/stage3_contingency/wang_qmc/method_comparison.csv` | Cross-method comparison metrics table. |
| `results/ablation/stage123_comparison/stage3_contingency/wang_qmc/state_summary_wang_qmc.csv` | State occurrence summary for Wang QMC method. |
| `results/ablation/stage6_comparison/baseline_gnn/metrics.csv` | Evaluation metrics summary table. |
| `results/ablation/stage6_comparison/baseline_gnn/result.json` | Structured result summary for one model/run. |
| `results/ablation/stage6_comparison/baseline_gnn/training_history.csv` | Training history across epochs. |
| `results/ablation/stage6_comparison/gat/metrics.csv` | Evaluation metrics summary table. |
| `results/ablation/stage6_comparison/gat/result.json` | Structured result summary for one model/run. |
| `results/ablation/stage6_comparison/gat/training_history.csv` | Training history across epochs. |
| `results/ablation/stage6_comparison/gcn/metrics.csv` | Evaluation metrics summary table. |
| `results/ablation/stage6_comparison/gcn/result.json` | Structured result summary for one model/run. |
| `results/ablation/stage6_comparison/gcn/training_history.csv` | Training history across epochs. |
| `results/ablation/stage6_comparison/graphsage/metrics.csv` | Evaluation metrics summary table. |
| `results/ablation/stage6_comparison/graphsage/result.json` | Structured result summary for one model/run. |
| `results/ablation/stage6_comparison/graphsage/training_history.csv` | Training history across epochs. |
| `results/ablation/stage6_comparison/metapath_v1/metrics.csv` | Evaluation metrics summary table. |
| `results/ablation/stage6_comparison/metapath_v1/result.json` | Structured result summary for one model/run. |
| `results/ablation/stage6_comparison/metapath_v1/training_history.csv` | Training history across epochs. |
| `results/ablation/stage6_comparison/mlp/metrics.csv` | Evaluation metrics summary table. |
| `results/ablation/stage6_comparison/mlp/result.json` | Structured result summary for one model/run. |
| `results/ablation/stage6_comparison/mlp/training_history.csv` | Training history across epochs. |
| `results/ablation/stage6_comparison/README.md` | Readme/instructions for the directory. |
| `results/ablation/stage6_comparison/stgcn/metrics.csv` | Evaluation metrics summary table. |
| `results/ablation/stage6_comparison/stgcn/result.json` | Structured result summary for one model/run. |
| `results/ablation/stage6_comparison/stgcn/training_history.csv` | Training history across epochs. |
| `results/component_failure_probability/formal2024/failure_probability_report.json` | Stage2 component/line failure probability report. |
| `results/component_failure_probability/formal2024/line_failure_timeseries_batts.csv` | Time-series line failure probabilities under Batts model. |
| `results/component_failure_probability/formal2024/line_failure_timeseries_schloemer.csv` | Time-series line failure probabilities under Schloemer model. |
| `results/component_failure_probability/g60_n75/failure_probability_report.json` | Stage2 component/line failure probability report. |
| `results/component_failure_probability/g60_n75/line_failure_timeseries_schloemer.csv` | Time-series line failure probabilities under Schloemer model. |
| `results/component_failure_probability/ieee118_n60_stage2_calib/ds0p001_it2p8/failure_probability_report.json` | Stage2 component/line failure probability report. |
| `results/component_failure_probability/ieee118_n60_stage2_calib/ds0p001_it2p8/line_failure_timeseries_schloemer.csv` | Time-series line failure probabilities under Schloemer model. |
| `results/component_failure_probability/ieee118_n60_stage2_calib/ds0p001_it3p5/failure_probability_report.json` | Stage2 component/line failure probability report. |
| `results/component_failure_probability/ieee118_n60_stage2_calib/ds0p001_it3p5/line_failure_timeseries_schloemer.csv` | Time-series line failure probabilities under Schloemer model. |
| `results/component_failure_probability/ieee118_n60_stage2_calib/ds0p001_it4p2/failure_probability_report.json` | Stage2 component/line failure probability report. |
| `results/component_failure_probability/ieee118_n60_stage2_calib/ds0p001_it4p2/line_failure_timeseries_schloemer.csv` | Time-series line failure probabilities under Schloemer model. |
| `results/component_failure_probability/ieee118_n60_stage2_calib/ds0p001_it5p5/failure_probability_report.json` | Stage2 component/line failure probability report. |
| `results/component_failure_probability/ieee118_n60_stage2_calib/ds0p001_it5p5/line_failure_timeseries_schloemer.csv` | Time-series line failure probabilities under Schloemer model. |
| `results/component_failure_probability/ieee118_n60_stage2_calib/ds0p001_it7p0/failure_probability_report.json` | Stage2 component/line failure probability report. |
| `results/component_failure_probability/ieee118_n60_stage2_calib/ds0p001_it7p0/line_failure_timeseries_schloemer.csv` | Time-series line failure probabilities under Schloemer model. |
| `results/component_failure_probability/ieee118_n60_stage2_calib/ds0p002_it2p8/failure_probability_report.json` | Stage2 component/line failure probability report. |
| `results/component_failure_probability/ieee118_n60_stage2_calib/ds0p002_it2p8/line_failure_timeseries_schloemer.csv` | Time-series line failure probabilities under Schloemer model. |
| `results/component_failure_probability/ieee118_n60_stage2_calib/ds0p002_it3p5/failure_probability_report.json` | Stage2 component/line failure probability report. |
| `results/component_failure_probability/ieee118_n60_stage2_calib/ds0p002_it3p5/line_failure_timeseries_schloemer.csv` | Time-series line failure probabilities under Schloemer model. |
| `results/component_failure_probability/ieee118_n60_stage2_calib/ds0p002_it4p2/failure_probability_report.json` | Stage2 component/line failure probability report. |
| `results/component_failure_probability/ieee118_n60_stage2_calib/ds0p002_it4p2/line_failure_timeseries_schloemer.csv` | Time-series line failure probabilities under Schloemer model. |
| `results/component_failure_probability/ieee118_n60_stage2_calib/ds0p002_it5p5/failure_probability_report.json` | Stage2 component/line failure probability report. |
| `results/component_failure_probability/ieee118_n60_stage2_calib/ds0p002_it5p5/line_failure_timeseries_schloemer.csv` | Time-series line failure probabilities under Schloemer model. |
| `results/component_failure_probability/ieee118_n60_stage2_calib/ds0p002_it7p0/failure_probability_report.json` | Stage2 component/line failure probability report. |
| `results/component_failure_probability/ieee118_n60_stage2_calib/ds0p002_it7p0/line_failure_timeseries_schloemer.csv` | Time-series line failure probabilities under Schloemer model. |
| `results/component_failure_probability/ieee118_n60_stage2_calib/ds0p005_it2p8/failure_probability_report.json` | Stage2 component/line failure probability report. |
| `results/component_failure_probability/ieee118_n60_stage2_calib/ds0p005_it2p8/line_failure_timeseries_schloemer.csv` | Time-series line failure probabilities under Schloemer model. |
| `results/component_failure_probability/ieee118_n60_stage2_calib/ds0p005_it3p5/failure_probability_report.json` | Stage2 component/line failure probability report. |
| `results/component_failure_probability/ieee118_n60_stage2_calib/ds0p005_it3p5/line_failure_timeseries_schloemer.csv` | Time-series line failure probabilities under Schloemer model. |
| `results/component_failure_probability/ieee118_n60_stage2_calib/ds0p005_it4p2/failure_probability_report.json` | Stage2 component/line failure probability report. |
| `results/component_failure_probability/ieee118_n60_stage2_calib/ds0p005_it4p2/line_failure_timeseries_schloemer.csv` | Time-series line failure probabilities under Schloemer model. |
| `results/component_failure_probability/ieee118_n60_stage2_calib/ds0p005_it5p5/failure_probability_report.json` | Stage2 component/line failure probability report. |
| `results/component_failure_probability/ieee118_n60_stage2_calib/ds0p005_it5p5/line_failure_timeseries_schloemer.csv` | Time-series line failure probabilities under Schloemer model. |
| `results/component_failure_probability/ieee118_n60_stage2_calib/ds0p005_it7p0/failure_probability_report.json` | Stage2 component/line failure probability report. |
| `results/component_failure_probability/ieee118_n60_stage2_calib/ds0p005_it7p0/line_failure_timeseries_schloemer.csv` | Time-series line failure probabilities under Schloemer model. |
| `results/component_failure_probability/ieee118_n60_stage2_calib/ds0p010_it2p8/failure_probability_report.json` | Stage2 component/line failure probability report. |
| `results/component_failure_probability/ieee118_n60_stage2_calib/ds0p010_it2p8/line_failure_timeseries_schloemer.csv` | Time-series line failure probabilities under Schloemer model. |
| `results/component_failure_probability/ieee118_n60_stage2_calib/ds0p010_it3p5/failure_probability_report.json` | Stage2 component/line failure probability report. |
| `results/component_failure_probability/ieee118_n60_stage2_calib/ds0p010_it3p5/line_failure_timeseries_schloemer.csv` | Time-series line failure probabilities under Schloemer model. |
| `results/component_failure_probability/ieee118_n60_stage2_calib/ds0p010_it4p2/failure_probability_report.json` | Stage2 component/line failure probability report. |
| `results/component_failure_probability/ieee118_n60_stage2_calib/ds0p010_it4p2/line_failure_timeseries_schloemer.csv` | Time-series line failure probabilities under Schloemer model. |
| `results/component_failure_probability/ieee118_n60_stage2_calib/ds0p010_it5p5/failure_probability_report.json` | Stage2 component/line failure probability report. |
| `results/component_failure_probability/ieee118_n60_stage2_calib/ds0p010_it5p5/line_failure_timeseries_schloemer.csv` | Time-series line failure probabilities under Schloemer model. |
| `results/component_failure_probability/ieee118_n60_stage2_calib/ds0p010_it7p0/failure_probability_report.json` | Stage2 component/line failure probability report. |
| `results/component_failure_probability/ieee118_n60_stage2_calib/ds0p010_it7p0/line_failure_timeseries_schloemer.csv` | Time-series line failure probabilities under Schloemer model. |
| `results/component_failure_probability/ieee118_n60_stage2_calib/ds0p020_it2p8/failure_probability_report.json` | Stage2 component/line failure probability report. |
| `results/component_failure_probability/ieee118_n60_stage2_calib/ds0p020_it2p8/line_failure_timeseries_schloemer.csv` | Time-series line failure probabilities under Schloemer model. |
| `results/component_failure_probability/ieee118_n60_stage2_calib/ds0p020_it3p5/failure_probability_report.json` | Stage2 component/line failure probability report. |
| `results/component_failure_probability/ieee118_n60_stage2_calib/ds0p020_it3p5/line_failure_timeseries_schloemer.csv` | Time-series line failure probabilities under Schloemer model. |
| `results/component_failure_probability/ieee118_n60_stage2_calib/ds0p020_it4p2/failure_probability_report.json` | Stage2 component/line failure probability report. |
| `results/component_failure_probability/ieee118_n60_stage2_calib/ds0p020_it4p2/line_failure_timeseries_schloemer.csv` | Time-series line failure probabilities under Schloemer model. |
| `results/component_failure_probability/ieee118_n60_stage2_calib/ds0p020_it5p5/failure_probability_report.json` | Stage2 component/line failure probability report. |
| `results/component_failure_probability/ieee118_n60_stage2_calib/ds0p020_it5p5/line_failure_timeseries_schloemer.csv` | Time-series line failure probabilities under Schloemer model. |
| `results/component_failure_probability/ieee118_n60_stage2_calib/ds0p020_it7p0/failure_probability_report.json` | Stage2 component/line failure probability report. |
| `results/component_failure_probability/ieee118_n60_stage2_calib/ds0p020_it7p0/line_failure_timeseries_schloemer.csv` | Time-series line failure probabilities under Schloemer model. |
| `results/component_failure_probability/ieee118_n60_stage2_calib/ds0p030_it2p8/failure_probability_report.json` | Stage2 component/line failure probability report. |
| `results/component_failure_probability/ieee118_n60_stage2_calib/ds0p030_it2p8/line_failure_timeseries_schloemer.csv` | Time-series line failure probabilities under Schloemer model. |
| `results/component_failure_probability/ieee118_n60_stage2_calib/ds0p030_it3p5/failure_probability_report.json` | Stage2 component/line failure probability report. |
| `results/component_failure_probability/ieee118_n60_stage2_calib/ds0p030_it3p5/line_failure_timeseries_schloemer.csv` | Time-series line failure probabilities under Schloemer model. |
| `results/component_failure_probability/ieee118_n60_stage2_calib/ds0p030_it4p2/failure_probability_report.json` | Stage2 component/line failure probability report. |
| `results/component_failure_probability/ieee118_n60_stage2_calib/ds0p030_it4p2/line_failure_timeseries_schloemer.csv` | Time-series line failure probabilities under Schloemer model. |
| `results/component_failure_probability/ieee118_n60_stage2_calib/ds0p030_it5p5/failure_probability_report.json` | Stage2 component/line failure probability report. |
| `results/component_failure_probability/ieee118_n60_stage2_calib/ds0p030_it5p5/line_failure_timeseries_schloemer.csv` | Time-series line failure probabilities under Schloemer model. |
| `results/component_failure_probability/ieee118_n60_stage2_calib/ds0p030_it7p0/failure_probability_report.json` | Stage2 component/line failure probability report. |
| `results/component_failure_probability/ieee118_n60_stage2_calib/ds0p030_it7p0/line_failure_timeseries_schloemer.csv` | Time-series line failure probabilities under Schloemer model. |
| `results/component_failure_probability/ieee118_n60_stage2_calib/sweep_summary.json` | JSON object; top keys: rows, top10. |
| `results/component_failure_probability/ieee118_n60_stagewise_tune/ds0p03_it1p00/failure_probability_report.json` | Stage2 component/line failure probability report. |
| `results/component_failure_probability/ieee118_n60_stagewise_tune/ds0p03_it1p00/line_failure_timeseries_schloemer.csv` | Time-series line failure probabilities under Schloemer model. |
| `results/component_failure_probability/ieee118_n60_stagewise_tune/ds0p03_it1p40/failure_probability_report.json` | Stage2 component/line failure probability report. |
| `results/component_failure_probability/ieee118_n60_stagewise_tune/ds0p03_it1p40/line_failure_timeseries_schloemer.csv` | Time-series line failure probabilities under Schloemer model. |
| `results/component_failure_probability/ieee118_n60_stagewise_tune/ds0p03_it1p80/failure_probability_report.json` | Stage2 component/line failure probability report. |
| `results/component_failure_probability/ieee118_n60_stagewise_tune/ds0p03_it1p80/line_failure_timeseries_schloemer.csv` | Time-series line failure probabilities under Schloemer model. |
| `results/component_failure_probability/ieee118_n60_stagewise_tune/ds0p03_it2p20/failure_probability_report.json` | Stage2 component/line failure probability report. |
| `results/component_failure_probability/ieee118_n60_stagewise_tune/ds0p03_it2p20/line_failure_timeseries_schloemer.csv` | Time-series line failure probabilities under Schloemer model. |
| `results/component_failure_probability/ieee118_n60_stagewise_tune/ds0p03_it2p80/failure_probability_report.json` | Stage2 component/line failure probability report. |
| `results/component_failure_probability/ieee118_n60_stagewise_tune/ds0p03_it2p80/line_failure_timeseries_schloemer.csv` | Time-series line failure probabilities under Schloemer model. |
| `results/component_failure_probability/ieee118_n60_stagewise_tune/ds0p05_it1p00/failure_probability_report.json` | Stage2 component/line failure probability report. |
| `results/component_failure_probability/ieee118_n60_stagewise_tune/ds0p05_it1p00/line_failure_timeseries_schloemer.csv` | Time-series line failure probabilities under Schloemer model. |
| `results/component_failure_probability/ieee118_n60_stagewise_tune/ds0p05_it1p40/failure_probability_report.json` | Stage2 component/line failure probability report. |
| `results/component_failure_probability/ieee118_n60_stagewise_tune/ds0p05_it1p40/line_failure_timeseries_schloemer.csv` | Time-series line failure probabilities under Schloemer model. |
| `results/component_failure_probability/ieee118_n60_stagewise_tune/ds0p05_it1p80/failure_probability_report.json` | Stage2 component/line failure probability report. |
| `results/component_failure_probability/ieee118_n60_stagewise_tune/ds0p05_it1p80/line_failure_timeseries_schloemer.csv` | Time-series line failure probabilities under Schloemer model. |
| `results/component_failure_probability/ieee118_n60_stagewise_tune/ds0p05_it2p20/failure_probability_report.json` | Stage2 component/line failure probability report. |
| `results/component_failure_probability/ieee118_n60_stagewise_tune/ds0p05_it2p20/line_failure_timeseries_schloemer.csv` | Time-series line failure probabilities under Schloemer model. |
| `results/component_failure_probability/ieee118_n60_stagewise_tune/ds0p05_it2p80/failure_probability_report.json` | Stage2 component/line failure probability report. |
| `results/component_failure_probability/ieee118_n60_stagewise_tune/ds0p05_it2p80/line_failure_timeseries_schloemer.csv` | Time-series line failure probabilities under Schloemer model. |
| `results/component_failure_probability/ieee118_n60_stagewise_tune/ds0p08_it1p00/failure_probability_report.json` | Stage2 component/line failure probability report. |
| `results/component_failure_probability/ieee118_n60_stagewise_tune/ds0p08_it1p00/line_failure_timeseries_schloemer.csv` | Time-series line failure probabilities under Schloemer model. |
| `results/component_failure_probability/ieee118_n60_stagewise_tune/ds0p08_it1p40/failure_probability_report.json` | Stage2 component/line failure probability report. |
| `results/component_failure_probability/ieee118_n60_stagewise_tune/ds0p08_it1p40/line_failure_timeseries_schloemer.csv` | Time-series line failure probabilities under Schloemer model. |
| `results/component_failure_probability/ieee118_n60_stagewise_tune/ds0p08_it1p80/failure_probability_report.json` | Stage2 component/line failure probability report. |
| `results/component_failure_probability/ieee118_n60_stagewise_tune/ds0p08_it1p80/line_failure_timeseries_schloemer.csv` | Time-series line failure probabilities under Schloemer model. |
| `results/component_failure_probability/ieee118_n60_stagewise_tune/ds0p08_it2p20/failure_probability_report.json` | Stage2 component/line failure probability report. |
| `results/component_failure_probability/ieee118_n60_stagewise_tune/ds0p08_it2p20/line_failure_timeseries_schloemer.csv` | Time-series line failure probabilities under Schloemer model. |
| `results/component_failure_probability/ieee118_n60_stagewise_tune/ds0p08_it2p80/failure_probability_report.json` | Stage2 component/line failure probability report. |
| `results/component_failure_probability/ieee118_n60_stagewise_tune/ds0p08_it2p80/line_failure_timeseries_schloemer.csv` | Time-series line failure probabilities under Schloemer model. |
| `results/component_failure_probability/ieee118_n60_stagewise_tune/ds0p15_it1p00/failure_probability_report.json` | Stage2 component/line failure probability report. |
| `results/component_failure_probability/ieee118_n60_stagewise_tune/ds0p15_it1p00/line_failure_timeseries_schloemer.csv` | Time-series line failure probabilities under Schloemer model. |
| `results/component_failure_probability/ieee118_n60_stagewise_tune/ds0p15_it1p40/failure_probability_report.json` | Stage2 component/line failure probability report. |
| `results/component_failure_probability/ieee118_n60_stagewise_tune/ds0p15_it1p40/line_failure_timeseries_schloemer.csv` | Time-series line failure probabilities under Schloemer model. |
| `results/component_failure_probability/ieee118_n60_stagewise_tune/ds0p15_it1p80/failure_probability_report.json` | Stage2 component/line failure probability report. |
| `results/component_failure_probability/ieee118_n60_stagewise_tune/ds0p15_it1p80/line_failure_timeseries_schloemer.csv` | Time-series line failure probabilities under Schloemer model. |
| `results/component_failure_probability/ieee118_n60_stagewise_tune/ds0p15_it2p20/failure_probability_report.json` | Stage2 component/line failure probability report. |
| `results/component_failure_probability/ieee118_n60_stagewise_tune/ds0p15_it2p20/line_failure_timeseries_schloemer.csv` | Time-series line failure probabilities under Schloemer model. |
| `results/component_failure_probability/ieee118_n60_stagewise_tune/ds0p15_it2p80/failure_probability_report.json` | Stage2 component/line failure probability report. |
| `results/component_failure_probability/ieee118_n60_stagewise_tune/ds0p15_it2p80/line_failure_timeseries_schloemer.csv` | Time-series line failure probabilities under Schloemer model. |
| `results/component_failure_probability/ieee118_n60_stagewise_tune/ds0p30_it1p00/failure_probability_report.json` | Stage2 component/line failure probability report. |
| `results/component_failure_probability/ieee118_n60_stagewise_tune/ds0p30_it1p00/line_failure_timeseries_schloemer.csv` | Time-series line failure probabilities under Schloemer model. |
| `results/component_failure_probability/ieee118_n60_stagewise_tune/ds0p30_it1p40/failure_probability_report.json` | Stage2 component/line failure probability report. |
| `results/component_failure_probability/ieee118_n60_stagewise_tune/ds0p30_it1p40/line_failure_timeseries_schloemer.csv` | Time-series line failure probabilities under Schloemer model. |
| `results/component_failure_probability/ieee118_n60_stagewise_tune/ds0p30_it1p80/failure_probability_report.json` | Stage2 component/line failure probability report. |
| `results/component_failure_probability/ieee118_n60_stagewise_tune/ds0p30_it1p80/line_failure_timeseries_schloemer.csv` | Time-series line failure probabilities under Schloemer model. |
| `results/component_failure_probability/ieee118_n60_stagewise_tune/ds0p30_it2p20/failure_probability_report.json` | Stage2 component/line failure probability report. |
| `results/component_failure_probability/ieee118_n60_stagewise_tune/ds0p30_it2p20/line_failure_timeseries_schloemer.csv` | Time-series line failure probabilities under Schloemer model. |
| `results/component_failure_probability/ieee118_n60_stagewise_tune/ds0p30_it2p80/failure_probability_report.json` | Stage2 component/line failure probability report. |
| `results/component_failure_probability/ieee118_n60_stagewise_tune/ds0p30_it2p80/line_failure_timeseries_schloemer.csv` | Time-series line failure probabilities under Schloemer model. |
| `results/component_failure_probability/ieee118_n60_stagewise_tune/ds0p60_it1p00/failure_probability_report.json` | Stage2 component/line failure probability report. |
| `results/component_failure_probability/ieee118_n60_stagewise_tune/ds0p60_it1p00/line_failure_timeseries_schloemer.csv` | Time-series line failure probabilities under Schloemer model. |
| `results/component_failure_probability/ieee118_n60_stagewise_tune/ds0p60_it1p40/failure_probability_report.json` | Stage2 component/line failure probability report. |
| `results/component_failure_probability/ieee118_n60_stagewise_tune/ds0p60_it1p40/line_failure_timeseries_schloemer.csv` | Time-series line failure probabilities under Schloemer model. |
| `results/component_failure_probability/ieee118_n60_stagewise_tune/ds0p60_it1p80/failure_probability_report.json` | Stage2 component/line failure probability report. |
| `results/component_failure_probability/ieee118_n60_stagewise_tune/ds0p60_it1p80/line_failure_timeseries_schloemer.csv` | Time-series line failure probabilities under Schloemer model. |
| `results/component_failure_probability/ieee118_n60_stagewise_tune/ds0p60_it2p20/failure_probability_report.json` | Stage2 component/line failure probability report. |
| `results/component_failure_probability/ieee118_n60_stagewise_tune/ds0p60_it2p20/line_failure_timeseries_schloemer.csv` | Time-series line failure probabilities under Schloemer model. |
| `results/component_failure_probability/ieee118_n60_stagewise_tune/ds0p60_it2p80/failure_probability_report.json` | Stage2 component/line failure probability report. |
| `results/component_failure_probability/ieee118_n60_stagewise_tune/ds0p60_it2p80/line_failure_timeseries_schloemer.csv` | Time-series line failure probabilities under Schloemer model. |
| `results/component_failure_probability/ieee118_n60_stagewise_tune/ds1p00_it1p00/failure_probability_report.json` | Stage2 component/line failure probability report. |
| `results/component_failure_probability/ieee118_n60_stagewise_tune/ds1p00_it1p00/line_failure_timeseries_schloemer.csv` | Time-series line failure probabilities under Schloemer model. |
| `results/component_failure_probability/ieee118_n60_stagewise_tune/ds1p00_it1p40/failure_probability_report.json` | Stage2 component/line failure probability report. |
| `results/component_failure_probability/ieee118_n60_stagewise_tune/ds1p00_it1p40/line_failure_timeseries_schloemer.csv` | Time-series line failure probabilities under Schloemer model. |
| `results/component_failure_probability/ieee118_n60_stagewise_tune/ds1p00_it1p80/failure_probability_report.json` | Stage2 component/line failure probability report. |
| `results/component_failure_probability/ieee118_n60_stagewise_tune/ds1p00_it1p80/line_failure_timeseries_schloemer.csv` | Time-series line failure probabilities under Schloemer model. |
| `results/component_failure_probability/ieee118_n60_stagewise_tune/ds1p00_it2p20/failure_probability_report.json` | Stage2 component/line failure probability report. |
| `results/component_failure_probability/ieee118_n60_stagewise_tune/ds1p00_it2p20/line_failure_timeseries_schloemer.csv` | Time-series line failure probabilities under Schloemer model. |
| `results/component_failure_probability/ieee118_n60_stagewise_tune/ds1p00_it2p80/failure_probability_report.json` | Stage2 component/line failure probability report. |
| `results/component_failure_probability/ieee118_n60_stagewise_tune/ds1p00_it2p80/line_failure_timeseries_schloemer.csv` | Time-series line failure probabilities under Schloemer model. |
| `results/component_failure_probability/ieee118_n60_tune/ds0p60_it1p00/failure_probability_report.json` | Stage2 component/line failure probability report. |
| `results/component_failure_probability/ieee118_n60_tune/ds0p60_it1p00/line_failure_timeseries_schloemer.csv` | Time-series line failure probabilities under Schloemer model. |
| `results/component_failure_probability/ieee118_n60_tune/ds0p60_it1p20/failure_probability_report.json` | Stage2 component/line failure probability report. |
| `results/component_failure_probability/ieee118_n60_tune/ds0p60_it1p20/line_failure_timeseries_schloemer.csv` | Time-series line failure probabilities under Schloemer model. |
| `results/component_failure_probability/ieee118_n60_tune/ds0p60_it1p40/failure_probability_report.json` | Stage2 component/line failure probability report. |
| `results/component_failure_probability/ieee118_n60_tune/ds0p60_it1p40/line_failure_timeseries_schloemer.csv` | Time-series line failure probabilities under Schloemer model. |
| `results/component_failure_probability/ieee118_n60_tune/ds0p70_it1p00/failure_probability_report.json` | Stage2 component/line failure probability report. |
| `results/component_failure_probability/ieee118_n60_tune/ds0p70_it1p00/line_failure_timeseries_schloemer.csv` | Time-series line failure probabilities under Schloemer model. |
| `results/component_failure_probability/ieee118_n60_tune/ds0p70_it1p20/failure_probability_report.json` | Stage2 component/line failure probability report. |
| `results/component_failure_probability/ieee118_n60_tune/ds0p70_it1p20/line_failure_timeseries_schloemer.csv` | Time-series line failure probabilities under Schloemer model. |
| `results/component_failure_probability/ieee118_n60_tune/ds0p70_it1p40/failure_probability_report.json` | Stage2 component/line failure probability report. |
| `results/component_failure_probability/ieee118_n60_tune/ds0p70_it1p40/line_failure_timeseries_schloemer.csv` | Time-series line failure probabilities under Schloemer model. |
| `results/component_failure_probability/ieee118_n60_tune/ds0p80_it1p00/failure_probability_report.json` | Stage2 component/line failure probability report. |
| `results/component_failure_probability/ieee118_n60_tune/ds0p80_it1p00/line_failure_timeseries_schloemer.csv` | Time-series line failure probabilities under Schloemer model. |
| `results/component_failure_probability/ieee118_n60_tune/ds0p80_it1p20/failure_probability_report.json` | Stage2 component/line failure probability report. |
| `results/component_failure_probability/ieee118_n60_tune/ds0p80_it1p20/line_failure_timeseries_schloemer.csv` | Time-series line failure probabilities under Schloemer model. |
| `results/component_failure_probability/ieee118_n60_tune/ds0p80_it1p40/failure_probability_report.json` | Stage2 component/line failure probability report. |
| `results/component_failure_probability/ieee118_n60_tune/ds0p80_it1p40/line_failure_timeseries_schloemer.csv` | Time-series line failure probabilities under Schloemer model. |
| `results/component_failure_probability/ieee118_n60_tune/ds0p90_it1p00/failure_probability_report.json` | Stage2 component/line failure probability report. |
| `results/component_failure_probability/ieee118_n60_tune/ds0p90_it1p00/line_failure_timeseries_schloemer.csv` | Time-series line failure probabilities under Schloemer model. |
| `results/component_failure_probability/ieee118_n60_tune/ds0p90_it1p20/failure_probability_report.json` | Stage2 component/line failure probability report. |
| `results/component_failure_probability/ieee118_n60_tune/ds0p90_it1p20/line_failure_timeseries_schloemer.csv` | Time-series line failure probabilities under Schloemer model. |
| `results/component_failure_probability/ieee118_n60_tune/ds0p90_it1p40/failure_probability_report.json` | Stage2 component/line failure probability report. |
| `results/component_failure_probability/ieee118_n60_tune/ds0p90_it1p40/line_failure_timeseries_schloemer.csv` | Time-series line failure probabilities under Schloemer model. |
| `results/component_failure_probability/ieee118_n60_tune/ds1p00_it1p00/failure_probability_report.json` | Stage2 component/line failure probability report. |
| `results/component_failure_probability/ieee118_n60_tune/ds1p00_it1p00/line_failure_timeseries_schloemer.csv` | Time-series line failure probabilities under Schloemer model. |
| `results/component_failure_probability/ieee118_n60_tune/ds1p00_it1p20/failure_probability_report.json` | Stage2 component/line failure probability report. |
| `results/component_failure_probability/ieee118_n60_tune/ds1p00_it1p20/line_failure_timeseries_schloemer.csv` | Time-series line failure probabilities under Schloemer model. |
| `results/component_failure_probability/ieee118_n60_tune/ds1p00_it1p40/failure_probability_report.json` | Stage2 component/line failure probability report. |
| `results/component_failure_probability/ieee118_n60_tune/ds1p00_it1p40/line_failure_timeseries_schloemer.csv` | Time-series line failure probabilities under Schloemer model. |
| `results/component_failure_probability/ieee118_n60_tune/sweep_summary.json` | JSON object; top keys: Length, LongLength, Rank, SyncRoot, IsReadOnly, IsFixedSize, IsSynchronized, Count. |
| `results/component_failure_probability/ieee118_n60/failure_probability_report.json` | Stage2 component/line failure probability report. |
| `results/component_failure_probability/ieee118_n60/line_failure_timeseries_schloemer.csv` | Time-series line failure probabilities under Schloemer model. |
| `results/dashboard_streamlit.log` | Runtime log output from Streamlit dashboard. |
| `results/dispatch_optimization/formal2024_contextual_smoke/contextual_dispatch_hourly_cost.csv` | Context-aware hourly operational cost trace. |
| `results/dispatch_optimization/formal2024_contextual_smoke/contextual_dispatch_load_shedding.csv` | Context-aware load shedding schedule. |
| `results/dispatch_optimization/formal2024_contextual_smoke/contextual_dispatch_unit_schedule.csv` | Context-aware dispatch generation schedule. |
| `results/dispatch_optimization/formal2024_contextual_smoke/dispatch_active_strategy_summary.csv` | Summary of active dispatch strategy over time. |
| `results/dispatch_optimization/formal2024_contextual_smoke/dispatch_ewm_topsis_result.csv` | Dispatch strategy composite ranking from EWM+TOPSIS. |
| `results/dispatch_optimization/formal2024_contextual_smoke/dispatch_indicator_weights.csv` | Indicator weights used in dispatch strategy scoring. |
| `results/dispatch_optimization/formal2024_contextual_smoke/dispatch_model_comparison.csv` | SCUC/Stochastic/Robust model comparison metrics. |
| `results/dispatch_optimization/formal2024_contextual_smoke/dispatch_optimization_report.json` | Stage7 dispatch optimization report. |
| `results/dispatch_optimization/formal2024_contextual_smoke/dispatch_strategy_selection.csv` | Risk-context strategy switching record by time step. |
| `results/dispatch_optimization/formal2024_contextual_smoke/robust_uc_first_stage_schedule.csv` | Robust UC first-stage schedule output. |
| `results/dispatch_optimization/formal2024_contextual_smoke/robust_uc_scenario_summary.csv` | Robust UC scenario summary metrics. |
| `results/dispatch_optimization/formal2024_contextual_smoke/robust_uc_worst_load_shedding.csv` | Worst-case load shedding under robust UC. |
| `results/dispatch_optimization/formal2024_contextual_smoke/scuc_load_shedding.csv` | SCUC load shedding output table. |
| `results/dispatch_optimization/formal2024_contextual_smoke/scuc_schedule.csv` | SCUC schedule output table. |
| `results/dispatch_optimization/formal2024_contextual_smoke/stochastic_uc_expected_load_shedding.csv` | Expected load shedding under stochastic UC. |
| `results/dispatch_optimization/formal2024_contextual_smoke/stochastic_uc_first_stage_schedule.csv` | Stochastic UC first-stage schedule output. |
| `results/dispatch_optimization/formal2024_contextual_smoke/stochastic_uc_scenario_summary.csv` | Stochastic UC scenario summary metrics. |
| `results/dispatch_optimization/formal2024_contextual_verify_nocompare/contextual_dispatch_hourly_cost.csv` | Context-aware hourly operational cost trace. |
| `results/dispatch_optimization/formal2024_contextual_verify_nocompare/contextual_dispatch_load_shedding.csv` | Context-aware load shedding schedule. |
| `results/dispatch_optimization/formal2024_contextual_verify_nocompare/contextual_dispatch_unit_schedule.csv` | Context-aware dispatch generation schedule. |
| `results/dispatch_optimization/formal2024_contextual_verify_nocompare/dispatch_active_strategy_summary.csv` | Summary of active dispatch strategy over time. |
| `results/dispatch_optimization/formal2024_contextual_verify_nocompare/dispatch_indicator_weights.csv` | Indicator weights used in dispatch strategy scoring. |
| `results/dispatch_optimization/formal2024_contextual_verify_nocompare/dispatch_optimization_report.json` | Stage7 dispatch optimization report. |
| `results/dispatch_optimization/formal2024_contextual_verify_nocompare/dispatch_strategy_selection.csv` | Risk-context strategy switching record by time step. |
| `results/dispatch_optimization/formal2024_contextual_verify_nocompare/robust_uc_first_stage_schedule.csv` | Robust UC first-stage schedule output. |
| `results/dispatch_optimization/formal2024_contextual_verify_nocompare/robust_uc_scenario_summary.csv` | Robust UC scenario summary metrics. |
| `results/dispatch_optimization/formal2024_contextual_verify_nocompare/robust_uc_worst_load_shedding.csv` | Worst-case load shedding under robust UC. |
| `results/dispatch_optimization/formal2024_contextual_verify_nocompare/scuc_load_shedding.csv` | SCUC load shedding output table. |
| `results/dispatch_optimization/formal2024_contextual_verify_nocompare/scuc_schedule.csv` | SCUC schedule output table. |
| `results/dispatch_optimization/formal2024_contextual_verify_nocompare/stochastic_uc_expected_load_shedding.csv` | Expected load shedding under stochastic UC. |
| `results/dispatch_optimization/formal2024_contextual_verify_nocompare/stochastic_uc_first_stage_schedule.csv` | Stochastic UC first-stage schedule output. |
| `results/dispatch_optimization/formal2024_contextual_verify_nocompare/stochastic_uc_scenario_summary.csv` | Stochastic UC scenario summary metrics. |
| `results/dispatch_optimization/formal2024_lineflow_smoke/contextual_dispatch_hourly_cost.csv` | Context-aware hourly operational cost trace. |
| `results/dispatch_optimization/formal2024_lineflow_smoke/contextual_dispatch_load_shedding.csv` | Context-aware load shedding schedule. |
| `results/dispatch_optimization/formal2024_lineflow_smoke/contextual_dispatch_unit_schedule.csv` | Context-aware dispatch generation schedule. |
| `results/dispatch_optimization/formal2024_lineflow_smoke/dispatch_active_strategy_summary.csv` | Summary of active dispatch strategy over time. |
| `results/dispatch_optimization/formal2024_lineflow_smoke/dispatch_indicator_weights.csv` | Indicator weights used in dispatch strategy scoring. |
| `results/dispatch_optimization/formal2024_lineflow_smoke/dispatch_optimization_report.json` | Stage7 dispatch optimization report. |
| `results/dispatch_optimization/formal2024_lineflow_smoke/dispatch_strategy_selection.csv` | Risk-context strategy switching record by time step. |
| `results/dispatch_optimization/formal2024_lineflow_smoke/line_flow.csv` | Line flow results from dispatch optimization. |
| `results/dispatch_optimization/formal2024_lineflow_smoke/robust_uc_first_stage_schedule.csv` | Robust UC first-stage schedule output. |
| `results/dispatch_optimization/formal2024_lineflow_smoke/robust_uc_scenario_summary.csv` | Robust UC scenario summary metrics. |
| `results/dispatch_optimization/formal2024_lineflow_smoke/robust_uc_worst_load_shedding.csv` | Worst-case load shedding under robust UC. |
| `results/dispatch_optimization/formal2024_lineflow_smoke/scuc_load_shedding.csv` | SCUC load shedding output table. |
| `results/dispatch_optimization/formal2024_lineflow_smoke/scuc_schedule.csv` | SCUC schedule output table. |
| `results/dispatch_optimization/formal2024_lineflow_smoke/stochastic_uc_expected_load_shedding.csv` | Expected load shedding under stochastic UC. |
| `results/dispatch_optimization/formal2024_lineflow_smoke/stochastic_uc_first_stage_schedule.csv` | Stochastic UC first-stage schedule output. |
| `results/dispatch_optimization/formal2024_lineflow_smoke/stochastic_uc_scenario_summary.csv` | Stochastic UC scenario summary metrics. |
| `results/dispatch_optimization/formal2024_quick24/dispatch_ewm_topsis_result.csv` | Dispatch strategy composite ranking from EWM+TOPSIS. |
| `results/dispatch_optimization/formal2024_quick24/dispatch_indicator_weights.csv` | Indicator weights used in dispatch strategy scoring. |
| `results/dispatch_optimization/formal2024_quick24/dispatch_model_comparison.csv` | SCUC/Stochastic/Robust model comparison metrics. |
| `results/dispatch_optimization/formal2024_quick24/dispatch_optimization_report.json` | Stage7 dispatch optimization report. |
| `results/dispatch_optimization/formal2024_quick24/robust_uc_first_stage_schedule.csv` | Robust UC first-stage schedule output. |
| `results/dispatch_optimization/formal2024_quick24/robust_uc_scenario_summary.csv` | Robust UC scenario summary metrics. |
| `results/dispatch_optimization/formal2024_quick24/robust_uc_worst_load_shedding.csv` | Worst-case load shedding under robust UC. |
| `results/dispatch_optimization/formal2024_quick24/scuc_load_shedding.csv` | SCUC load shedding output table. |
| `results/dispatch_optimization/formal2024_quick24/scuc_schedule.csv` | SCUC schedule output table. |
| `results/dispatch_optimization/formal2024_quick24/stochastic_uc_expected_load_shedding.csv` | Expected load shedding under stochastic UC. |
| `results/dispatch_optimization/formal2024_quick24/stochastic_uc_first_stage_schedule.csv` | Stochastic UC first-stage schedule output. |
| `results/dispatch_optimization/formal2024_quick24/stochastic_uc_scenario_summary.csv` | Stochastic UC scenario summary metrics. |
| `results/dispatch_optimization/formal2024_smoke/dispatch_ewm_topsis_result.csv` | Dispatch strategy composite ranking from EWM+TOPSIS. |
| `results/dispatch_optimization/formal2024_smoke/dispatch_indicator_weights.csv` | Indicator weights used in dispatch strategy scoring. |
| `results/dispatch_optimization/formal2024_smoke/dispatch_model_comparison.csv` | SCUC/Stochastic/Robust model comparison metrics. |
| `results/dispatch_optimization/formal2024_smoke/dispatch_optimization_report.json` | Stage7 dispatch optimization report. |
| `results/dispatch_optimization/formal2024_smoke/robust_uc_first_stage_schedule.csv` | Robust UC first-stage schedule output. |
| `results/dispatch_optimization/formal2024_smoke/robust_uc_scenario_summary.csv` | Robust UC scenario summary metrics. |
| `results/dispatch_optimization/formal2024_smoke/robust_uc_worst_load_shedding.csv` | Worst-case load shedding under robust UC. |
| `results/dispatch_optimization/formal2024_smoke/scuc_load_shedding.csv` | SCUC load shedding output table. |
| `results/dispatch_optimization/formal2024_smoke/scuc_schedule.csv` | SCUC schedule output table. |
| `results/dispatch_optimization/formal2024_smoke/stochastic_uc_expected_load_shedding.csv` | Expected load shedding under stochastic UC. |
| `results/dispatch_optimization/formal2024_smoke/stochastic_uc_first_stage_schedule.csv` | Stochastic UC first-stage schedule output. |
| `results/dispatch_optimization/formal2024_smoke/stochastic_uc_scenario_summary.csv` | Stochastic UC scenario summary metrics. |
| `results/dispatch/generation_schedule.csv` | Generation schedule output table. |
| `results/dispatch/line_flow.csv` | Line flow results from dispatch optimization. |
| `results/dispatch/load_shedding.csv` | Load shedding output table. |
| `results/dispatch/reserve_schedule.csv` | Reserve allocation schedule output table. |
| `results/dpgmn_method_extracted.txt` | Text/markdown notes; starts with: PAGES=13 |
| `results/early_warning/formal2024_metapath_v1_compare/baseline_calibrated_hourly_line_probability.csv` | Baseline calibrated hourly line probabilities. |
| `results/early_warning/formal2024_metapath_v1_compare/baseline_line_risk_prediction.csv` | Baseline model line risk predictions. |
| `results/early_warning/formal2024_metapath_v1_compare/calibrated_hourly_line_probability.csv` | Calibrated hourly line failure probability matrix. |
| `results/early_warning/formal2024_metapath_v1_compare/critical_load_risk.csv` | Critical load risk indicators over horizon. |
| `results/early_warning/formal2024_metapath_v1_compare/line_risk_prediction.csv` | Predicted line-level risk probabilities and labels. |
| `results/early_warning/formal2024_metapath_v1_compare/metapath_attention_summary.csv` | MetaPath semantic attention summary statistics. |
| `results/early_warning/formal2024_metapath_v1_compare/model_comparison.csv` | Model comparison metrics (baseline vs variants). |
| `results/early_warning/formal2024_metapath_v1_compare/nk_failure_risk.csv` | N-k style system-level failure risk indicators. |
| `results/early_warning/formal2024_metapath_v1_compare/warning_report.json` | Stage6 warning model report with performance metrics. |
| `results/early_warning/formal2024_metapath_v1_opt1/baseline_calibrated_hourly_line_probability.csv` | Baseline calibrated hourly line probabilities. |
| `results/early_warning/formal2024_metapath_v1_opt1/baseline_line_risk_prediction.csv` | Baseline model line risk predictions. |
| `results/early_warning/formal2024_metapath_v1_opt1/calibrated_hourly_line_probability.csv` | Calibrated hourly line failure probability matrix. |
| `results/early_warning/formal2024_metapath_v1_opt1/critical_load_risk.csv` | Critical load risk indicators over horizon. |
| `results/early_warning/formal2024_metapath_v1_opt1/line_risk_prediction.csv` | Predicted line-level risk probabilities and labels. |
| `results/early_warning/formal2024_metapath_v1_opt1/metapath_attention_summary.csv` | MetaPath semantic attention summary statistics. |
| `results/early_warning/formal2024_metapath_v1_opt1/model_comparison.csv` | Model comparison metrics (baseline vs variants). |
| `results/early_warning/formal2024_metapath_v1_opt1/nk_failure_risk.csv` | N-k style system-level failure risk indicators. |
| `results/early_warning/formal2024_metapath_v1_opt1/warning_report.json` | Stage6 warning model report with performance metrics. |
| `results/early_warning/formal2024_metapath_v1_tuned/baseline_calibrated_hourly_line_probability.csv` | Baseline calibrated hourly line probabilities. |
| `results/early_warning/formal2024_metapath_v1_tuned/baseline_line_risk_prediction.csv` | Baseline model line risk predictions. |
| `results/early_warning/formal2024_metapath_v1_tuned/calibrated_hourly_line_probability.csv` | Calibrated hourly line failure probability matrix. |
| `results/early_warning/formal2024_metapath_v1_tuned/critical_load_risk.csv` | Critical load risk indicators over horizon. |
| `results/early_warning/formal2024_metapath_v1_tuned/line_risk_prediction.csv` | Predicted line-level risk probabilities and labels. |
| `results/early_warning/formal2024_metapath_v1_tuned/metapath_attention_summary.csv` | MetaPath semantic attention summary statistics. |
| `results/early_warning/formal2024_metapath_v1_tuned/model_comparison.csv` | Model comparison metrics (baseline vs variants). |
| `results/early_warning/formal2024_metapath_v1_tuned/nk_failure_risk.csv` | N-k style system-level failure risk indicators. |
| `results/early_warning/formal2024_metapath_v1_tuned/warning_report.json` | Stage6 warning model report with performance metrics. |
| `results/early_warning/formal2024_tmp/calibrated_hourly_line_probability.csv` | Calibrated hourly line failure probability matrix. |
| `results/early_warning/formal2024_tmp/critical_load_risk.csv` | Critical load risk indicators over horizon. |
| `results/early_warning/formal2024_tmp/line_risk_prediction.csv` | Predicted line-level risk probabilities and labels. |
| `results/early_warning/formal2024_tmp/nk_failure_risk.csv` | N-k style system-level failure risk indicators. |
| `results/early_warning/formal2024_tmp/warning_report.json` | Stage6 warning model report with performance metrics. |
| `results/early_warning/formal2024_tmp2/calibrated_hourly_line_probability.csv` | Calibrated hourly line failure probability matrix. |
| `results/early_warning/formal2024_tmp2/critical_load_risk.csv` | Critical load risk indicators over horizon. |
| `results/early_warning/formal2024_tmp2/line_risk_prediction.csv` | Predicted line-level risk probabilities and labels. |
| `results/early_warning/formal2024_tmp2/nk_failure_risk.csv` | N-k style system-level failure risk indicators. |
| `results/early_warning/formal2024_tmp2/warning_report.json` | Stage6 warning model report with performance metrics. |
| `results/early_warning/formal2024/calibrated_hourly_line_probability.csv` | Calibrated hourly line failure probability matrix. |
| `results/early_warning/formal2024/critical_load_risk.csv` | Critical load risk indicators over horizon. |
| `results/early_warning/formal2024/line_risk_prediction.csv` | Predicted line-level risk probabilities and labels. |
| `results/early_warning/formal2024/nk_failure_risk.csv` | N-k style system-level failure risk indicators. |
| `results/early_warning/formal2024/warning_report.json` | Stage6 warning model report with performance metrics. |
| `results/early_warning/g60_n75_stageA_20260324_183639/all_runs.csv` | Summary of all run settings/results in a sweep. |
| `results/early_warning/g60_n75_stageA_20260324_183639/done.json` | Completion flag/metadata for finished run. |
| `results/early_warning/g60_n75_stageA_20260324_183639/experiment_config.json` | Experiment configuration snapshot for a run. |
| `results/early_warning/g60_n75_stageA_20260324_183639/r001_k4_h80_ep300_lr0.006_wd0.0001_tr0.700_s42/baseline_calibrated_hourly_line_probability.csv` | Baseline calibrated hourly line probabilities. |
| `results/early_warning/g60_n75_stageA_20260324_183639/r001_k4_h80_ep300_lr0.006_wd0.0001_tr0.700_s42/baseline_line_risk_prediction.csv` | Baseline model line risk predictions. |
| `results/early_warning/g60_n75_stageA_20260324_183639/r001_k4_h80_ep300_lr0.006_wd0.0001_tr0.700_s42/calibrated_hourly_line_probability.csv` | Calibrated hourly line failure probability matrix. |
| `results/early_warning/g60_n75_stageA_20260324_183639/r001_k4_h80_ep300_lr0.006_wd0.0001_tr0.700_s42/critical_load_risk.csv` | Critical load risk indicators over horizon. |
| `results/early_warning/g60_n75_stageA_20260324_183639/r001_k4_h80_ep300_lr0.006_wd0.0001_tr0.700_s42/line_risk_prediction.csv` | Predicted line-level risk probabilities and labels. |
| `results/early_warning/g60_n75_stageA_20260324_183639/r001_k4_h80_ep300_lr0.006_wd0.0001_tr0.700_s42/metapath_attention_summary.csv` | MetaPath semantic attention summary statistics. |
| `results/early_warning/g60_n75_stageA_20260324_183639/r001_k4_h80_ep300_lr0.006_wd0.0001_tr0.700_s42/model_comparison.csv` | Model comparison metrics (baseline vs variants). |
| `results/early_warning/g60_n75_stageA_20260324_183639/r001_k4_h80_ep300_lr0.006_wd0.0001_tr0.700_s42/nk_failure_risk.csv` | N-k style system-level failure risk indicators. |
| `results/early_warning/g60_n75_stageA_20260324_183639/r001_k4_h80_ep300_lr0.006_wd0.0001_tr0.700_s42/train.log` | Log file captured during script/dashboard execution. |
| `results/early_warning/g60_n75_stageA_20260324_183639/r001_k4_h80_ep300_lr0.006_wd0.0001_tr0.700_s42/warning_report.json` | Stage6 warning model report with performance metrics. |
| `results/early_warning/g60_n75_stageA_20260324_183639/r002_k4_h80_ep300_lr0.006_wd0.0001_tr0.700_s43/baseline_calibrated_hourly_line_probability.csv` | Baseline calibrated hourly line probabilities. |
| `results/early_warning/g60_n75_stageA_20260324_183639/r002_k4_h80_ep300_lr0.006_wd0.0001_tr0.700_s43/baseline_line_risk_prediction.csv` | Baseline model line risk predictions. |
| `results/early_warning/g60_n75_stageA_20260324_183639/r002_k4_h80_ep300_lr0.006_wd0.0001_tr0.700_s43/calibrated_hourly_line_probability.csv` | Calibrated hourly line failure probability matrix. |
| `results/early_warning/g60_n75_stageA_20260324_183639/r002_k4_h80_ep300_lr0.006_wd0.0001_tr0.700_s43/critical_load_risk.csv` | Critical load risk indicators over horizon. |
| `results/early_warning/g60_n75_stageA_20260324_183639/r002_k4_h80_ep300_lr0.006_wd0.0001_tr0.700_s43/line_risk_prediction.csv` | Predicted line-level risk probabilities and labels. |
| `results/early_warning/g60_n75_stageA_20260324_183639/r002_k4_h80_ep300_lr0.006_wd0.0001_tr0.700_s43/metapath_attention_summary.csv` | MetaPath semantic attention summary statistics. |
| `results/early_warning/g60_n75_stageA_20260324_183639/r002_k4_h80_ep300_lr0.006_wd0.0001_tr0.700_s43/model_comparison.csv` | Model comparison metrics (baseline vs variants). |
| `results/early_warning/g60_n75_stageA_20260324_183639/r002_k4_h80_ep300_lr0.006_wd0.0001_tr0.700_s43/nk_failure_risk.csv` | N-k style system-level failure risk indicators. |
| `results/early_warning/g60_n75_stageA_20260324_183639/r002_k4_h80_ep300_lr0.006_wd0.0001_tr0.700_s43/train.log` | Log file captured during script/dashboard execution. |
| `results/early_warning/g60_n75_stageA_20260324_183639/r002_k4_h80_ep300_lr0.006_wd0.0001_tr0.700_s43/warning_report.json` | Stage6 warning model report with performance metrics. |
| `results/early_warning/g60_n75_stageA_20260324_183639/r003_k4_h80_ep300_lr0.006_wd0.0001_tr0.700_s44/baseline_calibrated_hourly_line_probability.csv` | Baseline calibrated hourly line probabilities. |
| `results/early_warning/g60_n75_stageA_20260324_183639/r003_k4_h80_ep300_lr0.006_wd0.0001_tr0.700_s44/baseline_line_risk_prediction.csv` | Baseline model line risk predictions. |
| `results/early_warning/g60_n75_stageA_20260324_183639/r003_k4_h80_ep300_lr0.006_wd0.0001_tr0.700_s44/calibrated_hourly_line_probability.csv` | Calibrated hourly line failure probability matrix. |
| `results/early_warning/g60_n75_stageA_20260324_183639/r003_k4_h80_ep300_lr0.006_wd0.0001_tr0.700_s44/critical_load_risk.csv` | Critical load risk indicators over horizon. |
| `results/early_warning/g60_n75_stageA_20260324_183639/r003_k4_h80_ep300_lr0.006_wd0.0001_tr0.700_s44/line_risk_prediction.csv` | Predicted line-level risk probabilities and labels. |
| `results/early_warning/g60_n75_stageA_20260324_183639/r003_k4_h80_ep300_lr0.006_wd0.0001_tr0.700_s44/metapath_attention_summary.csv` | MetaPath semantic attention summary statistics. |
| `results/early_warning/g60_n75_stageA_20260324_183639/r003_k4_h80_ep300_lr0.006_wd0.0001_tr0.700_s44/model_comparison.csv` | Model comparison metrics (baseline vs variants). |
| `results/early_warning/g60_n75_stageA_20260324_183639/r003_k4_h80_ep300_lr0.006_wd0.0001_tr0.700_s44/nk_failure_risk.csv` | N-k style system-level failure risk indicators. |
| `results/early_warning/g60_n75_stageA_20260324_183639/r003_k4_h80_ep300_lr0.006_wd0.0001_tr0.700_s44/train.log` | Log file captured during script/dashboard execution. |
| `results/early_warning/g60_n75_stageA_20260324_183639/r003_k4_h80_ep300_lr0.006_wd0.0001_tr0.700_s44/warning_report.json` | Stage6 warning model report with performance metrics. |
| `results/early_warning/g60_n75_stageA_20260324_183639/summary_by_setting.csv` | Aggregated sweep metrics by configuration setting. |
| `results/early_warning/g60_n75_stageB_20260324_184320/all_runs.csv` | Summary of all run settings/results in a sweep. |
| `results/early_warning/g60_n75_stageB_20260324_184320/done.json` | Completion flag/metadata for finished run. |
| `results/early_warning/g60_n75_stageB_20260324_184320/experiment_config.json` | Experiment configuration snapshot for a run. |
| `results/early_warning/g60_n75_stageB_20260324_184320/r001_k3_h80_ep700_lr0.006_wd0.0001_tr0.700_s42/baseline_calibrated_hourly_line_probability.csv` | Baseline calibrated hourly line probabilities. |
| `results/early_warning/g60_n75_stageB_20260324_184320/r001_k3_h80_ep700_lr0.006_wd0.0001_tr0.700_s42/baseline_line_risk_prediction.csv` | Baseline model line risk predictions. |
| `results/early_warning/g60_n75_stageB_20260324_184320/r001_k3_h80_ep700_lr0.006_wd0.0001_tr0.700_s42/calibrated_hourly_line_probability.csv` | Calibrated hourly line failure probability matrix. |
| `results/early_warning/g60_n75_stageB_20260324_184320/r001_k3_h80_ep700_lr0.006_wd0.0001_tr0.700_s42/critical_load_risk.csv` | Critical load risk indicators over horizon. |
| `results/early_warning/g60_n75_stageB_20260324_184320/r001_k3_h80_ep700_lr0.006_wd0.0001_tr0.700_s42/line_risk_prediction.csv` | Predicted line-level risk probabilities and labels. |
| `results/early_warning/g60_n75_stageB_20260324_184320/r001_k3_h80_ep700_lr0.006_wd0.0001_tr0.700_s42/metapath_attention_summary.csv` | MetaPath semantic attention summary statistics. |
| `results/early_warning/g60_n75_stageB_20260324_184320/r001_k3_h80_ep700_lr0.006_wd0.0001_tr0.700_s42/model_comparison.csv` | Model comparison metrics (baseline vs variants). |
| `results/early_warning/g60_n75_stageB_20260324_184320/r001_k3_h80_ep700_lr0.006_wd0.0001_tr0.700_s42/nk_failure_risk.csv` | N-k style system-level failure risk indicators. |
| `results/early_warning/g60_n75_stageB_20260324_184320/r001_k3_h80_ep700_lr0.006_wd0.0001_tr0.700_s42/train.log` | Log file captured during script/dashboard execution. |
| `results/early_warning/g60_n75_stageB_20260324_184320/r001_k3_h80_ep700_lr0.006_wd0.0001_tr0.700_s42/warning_report.json` | Stage6 warning model report with performance metrics. |
| `results/early_warning/g60_n75_stageB_20260324_184320/r002_k3_h80_ep700_lr0.006_wd0.0001_tr0.700_s43/baseline_calibrated_hourly_line_probability.csv` | Baseline calibrated hourly line probabilities. |
| `results/early_warning/g60_n75_stageB_20260324_184320/r002_k3_h80_ep700_lr0.006_wd0.0001_tr0.700_s43/baseline_line_risk_prediction.csv` | Baseline model line risk predictions. |
| `results/early_warning/g60_n75_stageB_20260324_184320/r002_k3_h80_ep700_lr0.006_wd0.0001_tr0.700_s43/calibrated_hourly_line_probability.csv` | Calibrated hourly line failure probability matrix. |
| `results/early_warning/g60_n75_stageB_20260324_184320/r002_k3_h80_ep700_lr0.006_wd0.0001_tr0.700_s43/critical_load_risk.csv` | Critical load risk indicators over horizon. |
| `results/early_warning/g60_n75_stageB_20260324_184320/r002_k3_h80_ep700_lr0.006_wd0.0001_tr0.700_s43/line_risk_prediction.csv` | Predicted line-level risk probabilities and labels. |
| `results/early_warning/g60_n75_stageB_20260324_184320/r002_k3_h80_ep700_lr0.006_wd0.0001_tr0.700_s43/metapath_attention_summary.csv` | MetaPath semantic attention summary statistics. |
| `results/early_warning/g60_n75_stageB_20260324_184320/r002_k3_h80_ep700_lr0.006_wd0.0001_tr0.700_s43/model_comparison.csv` | Model comparison metrics (baseline vs variants). |
| `results/early_warning/g60_n75_stageB_20260324_184320/r002_k3_h80_ep700_lr0.006_wd0.0001_tr0.700_s43/nk_failure_risk.csv` | N-k style system-level failure risk indicators. |
| `results/early_warning/g60_n75_stageB_20260324_184320/r002_k3_h80_ep700_lr0.006_wd0.0001_tr0.700_s43/train.log` | Log file captured during script/dashboard execution. |
| `results/early_warning/g60_n75_stageB_20260324_184320/r002_k3_h80_ep700_lr0.006_wd0.0001_tr0.700_s43/warning_report.json` | Stage6 warning model report with performance metrics. |
| `results/early_warning/g60_n75_stageB_20260324_184320/r003_k3_h80_ep700_lr0.006_wd0.0001_tr0.700_s44/baseline_calibrated_hourly_line_probability.csv` | Baseline calibrated hourly line probabilities. |
| `results/early_warning/g60_n75_stageB_20260324_184320/r003_k3_h80_ep700_lr0.006_wd0.0001_tr0.700_s44/baseline_line_risk_prediction.csv` | Baseline model line risk predictions. |
| `results/early_warning/g60_n75_stageB_20260324_184320/r003_k3_h80_ep700_lr0.006_wd0.0001_tr0.700_s44/calibrated_hourly_line_probability.csv` | Calibrated hourly line failure probability matrix. |
| `results/early_warning/g60_n75_stageB_20260324_184320/r003_k3_h80_ep700_lr0.006_wd0.0001_tr0.700_s44/critical_load_risk.csv` | Critical load risk indicators over horizon. |
| `results/early_warning/g60_n75_stageB_20260324_184320/r003_k3_h80_ep700_lr0.006_wd0.0001_tr0.700_s44/line_risk_prediction.csv` | Predicted line-level risk probabilities and labels. |
| `results/early_warning/g60_n75_stageB_20260324_184320/r003_k3_h80_ep700_lr0.006_wd0.0001_tr0.700_s44/metapath_attention_summary.csv` | MetaPath semantic attention summary statistics. |
| `results/early_warning/g60_n75_stageB_20260324_184320/r003_k3_h80_ep700_lr0.006_wd0.0001_tr0.700_s44/model_comparison.csv` | Model comparison metrics (baseline vs variants). |
| `results/early_warning/g60_n75_stageB_20260324_184320/r003_k3_h80_ep700_lr0.006_wd0.0001_tr0.700_s44/nk_failure_risk.csv` | N-k style system-level failure risk indicators. |
| `results/early_warning/g60_n75_stageB_20260324_184320/r003_k3_h80_ep700_lr0.006_wd0.0001_tr0.700_s44/train.log` | Log file captured during script/dashboard execution. |
| `results/early_warning/g60_n75_stageB_20260324_184320/r003_k3_h80_ep700_lr0.006_wd0.0001_tr0.700_s44/warning_report.json` | Stage6 warning model report with performance metrics. |
| `results/early_warning/g60_n75_stageB_20260324_184320/r004_k3_h80_ep700_lr0.006_wd0.0001_tr0.700_s45/baseline_calibrated_hourly_line_probability.csv` | Baseline calibrated hourly line probabilities. |
| `results/early_warning/g60_n75_stageB_20260324_184320/r004_k3_h80_ep700_lr0.006_wd0.0001_tr0.700_s45/baseline_line_risk_prediction.csv` | Baseline model line risk predictions. |
| `results/early_warning/g60_n75_stageB_20260324_184320/r004_k3_h80_ep700_lr0.006_wd0.0001_tr0.700_s45/calibrated_hourly_line_probability.csv` | Calibrated hourly line failure probability matrix. |
| `results/early_warning/g60_n75_stageB_20260324_184320/r004_k3_h80_ep700_lr0.006_wd0.0001_tr0.700_s45/critical_load_risk.csv` | Critical load risk indicators over horizon. |
| `results/early_warning/g60_n75_stageB_20260324_184320/r004_k3_h80_ep700_lr0.006_wd0.0001_tr0.700_s45/line_risk_prediction.csv` | Predicted line-level risk probabilities and labels. |
| `results/early_warning/g60_n75_stageB_20260324_184320/r004_k3_h80_ep700_lr0.006_wd0.0001_tr0.700_s45/metapath_attention_summary.csv` | MetaPath semantic attention summary statistics. |
| `results/early_warning/g60_n75_stageB_20260324_184320/r004_k3_h80_ep700_lr0.006_wd0.0001_tr0.700_s45/model_comparison.csv` | Model comparison metrics (baseline vs variants). |
| `results/early_warning/g60_n75_stageB_20260324_184320/r004_k3_h80_ep700_lr0.006_wd0.0001_tr0.700_s45/nk_failure_risk.csv` | N-k style system-level failure risk indicators. |
| `results/early_warning/g60_n75_stageB_20260324_184320/r004_k3_h80_ep700_lr0.006_wd0.0001_tr0.700_s45/train.log` | Log file captured during script/dashboard execution. |
| `results/early_warning/g60_n75_stageB_20260324_184320/r004_k3_h80_ep700_lr0.006_wd0.0001_tr0.700_s45/warning_report.json` | Stage6 warning model report with performance metrics. |
| `results/early_warning/g60_n75_stageB_20260324_184320/r005_k3_h80_ep700_lr0.006_wd0.0001_tr0.700_s46/baseline_calibrated_hourly_line_probability.csv` | Baseline calibrated hourly line probabilities. |
| `results/early_warning/g60_n75_stageB_20260324_184320/r005_k3_h80_ep700_lr0.006_wd0.0001_tr0.700_s46/baseline_line_risk_prediction.csv` | Baseline model line risk predictions. |
| `results/early_warning/g60_n75_stageB_20260324_184320/r005_k3_h80_ep700_lr0.006_wd0.0001_tr0.700_s46/calibrated_hourly_line_probability.csv` | Calibrated hourly line failure probability matrix. |
| `results/early_warning/g60_n75_stageB_20260324_184320/r005_k3_h80_ep700_lr0.006_wd0.0001_tr0.700_s46/critical_load_risk.csv` | Critical load risk indicators over horizon. |
| `results/early_warning/g60_n75_stageB_20260324_184320/r005_k3_h80_ep700_lr0.006_wd0.0001_tr0.700_s46/line_risk_prediction.csv` | Predicted line-level risk probabilities and labels. |
| `results/early_warning/g60_n75_stageB_20260324_184320/r005_k3_h80_ep700_lr0.006_wd0.0001_tr0.700_s46/metapath_attention_summary.csv` | MetaPath semantic attention summary statistics. |
| `results/early_warning/g60_n75_stageB_20260324_184320/r005_k3_h80_ep700_lr0.006_wd0.0001_tr0.700_s46/model_comparison.csv` | Model comparison metrics (baseline vs variants). |
| `results/early_warning/g60_n75_stageB_20260324_184320/r005_k3_h80_ep700_lr0.006_wd0.0001_tr0.700_s46/nk_failure_risk.csv` | N-k style system-level failure risk indicators. |
| `results/early_warning/g60_n75_stageB_20260324_184320/r005_k3_h80_ep700_lr0.006_wd0.0001_tr0.700_s46/train.log` | Log file captured during script/dashboard execution. |
| `results/early_warning/g60_n75_stageB_20260324_184320/r005_k3_h80_ep700_lr0.006_wd0.0001_tr0.700_s46/warning_report.json` | Stage6 warning model report with performance metrics. |
| `results/early_warning/g60_n75_stageB_20260324_184320/r006_k4_h80_ep700_lr0.006_wd0.0001_tr0.700_s42/baseline_calibrated_hourly_line_probability.csv` | Baseline calibrated hourly line probabilities. |
| `results/early_warning/g60_n75_stageB_20260324_184320/r006_k4_h80_ep700_lr0.006_wd0.0001_tr0.700_s42/baseline_line_risk_prediction.csv` | Baseline model line risk predictions. |
| `results/early_warning/g60_n75_stageB_20260324_184320/r006_k4_h80_ep700_lr0.006_wd0.0001_tr0.700_s42/calibrated_hourly_line_probability.csv` | Calibrated hourly line failure probability matrix. |
| `results/early_warning/g60_n75_stageB_20260324_184320/r006_k4_h80_ep700_lr0.006_wd0.0001_tr0.700_s42/critical_load_risk.csv` | Critical load risk indicators over horizon. |
| `results/early_warning/g60_n75_stageB_20260324_184320/r006_k4_h80_ep700_lr0.006_wd0.0001_tr0.700_s42/line_risk_prediction.csv` | Predicted line-level risk probabilities and labels. |
| `results/early_warning/g60_n75_stageB_20260324_184320/r006_k4_h80_ep700_lr0.006_wd0.0001_tr0.700_s42/metapath_attention_summary.csv` | MetaPath semantic attention summary statistics. |
| `results/early_warning/g60_n75_stageB_20260324_184320/r006_k4_h80_ep700_lr0.006_wd0.0001_tr0.700_s42/model_comparison.csv` | Model comparison metrics (baseline vs variants). |
| `results/early_warning/g60_n75_stageB_20260324_184320/r006_k4_h80_ep700_lr0.006_wd0.0001_tr0.700_s42/nk_failure_risk.csv` | N-k style system-level failure risk indicators. |
| `results/early_warning/g60_n75_stageB_20260324_184320/r006_k4_h80_ep700_lr0.006_wd0.0001_tr0.700_s42/train.log` | Log file captured during script/dashboard execution. |
| `results/early_warning/g60_n75_stageB_20260324_184320/r006_k4_h80_ep700_lr0.006_wd0.0001_tr0.700_s42/warning_report.json` | Stage6 warning model report with performance metrics. |
| `results/early_warning/g60_n75_stageB_20260324_184320/r007_k4_h80_ep700_lr0.006_wd0.0001_tr0.700_s43/baseline_calibrated_hourly_line_probability.csv` | Baseline calibrated hourly line probabilities. |
| `results/early_warning/g60_n75_stageB_20260324_184320/r007_k4_h80_ep700_lr0.006_wd0.0001_tr0.700_s43/baseline_line_risk_prediction.csv` | Baseline model line risk predictions. |
| `results/early_warning/g60_n75_stageB_20260324_184320/r007_k4_h80_ep700_lr0.006_wd0.0001_tr0.700_s43/calibrated_hourly_line_probability.csv` | Calibrated hourly line failure probability matrix. |
| `results/early_warning/g60_n75_stageB_20260324_184320/r007_k4_h80_ep700_lr0.006_wd0.0001_tr0.700_s43/critical_load_risk.csv` | Critical load risk indicators over horizon. |
| `results/early_warning/g60_n75_stageB_20260324_184320/r007_k4_h80_ep700_lr0.006_wd0.0001_tr0.700_s43/line_risk_prediction.csv` | Predicted line-level risk probabilities and labels. |
| `results/early_warning/g60_n75_stageB_20260324_184320/r007_k4_h80_ep700_lr0.006_wd0.0001_tr0.700_s43/metapath_attention_summary.csv` | MetaPath semantic attention summary statistics. |
| `results/early_warning/g60_n75_stageB_20260324_184320/r007_k4_h80_ep700_lr0.006_wd0.0001_tr0.700_s43/model_comparison.csv` | Model comparison metrics (baseline vs variants). |
| `results/early_warning/g60_n75_stageB_20260324_184320/r007_k4_h80_ep700_lr0.006_wd0.0001_tr0.700_s43/nk_failure_risk.csv` | N-k style system-level failure risk indicators. |
| `results/early_warning/g60_n75_stageB_20260324_184320/r007_k4_h80_ep700_lr0.006_wd0.0001_tr0.700_s43/train.log` | Log file captured during script/dashboard execution. |
| `results/early_warning/g60_n75_stageB_20260324_184320/r007_k4_h80_ep700_lr0.006_wd0.0001_tr0.700_s43/warning_report.json` | Stage6 warning model report with performance metrics. |
| `results/early_warning/g60_n75_stageB_20260324_184320/r008_k4_h80_ep700_lr0.006_wd0.0001_tr0.700_s44/baseline_calibrated_hourly_line_probability.csv` | Baseline calibrated hourly line probabilities. |
| `results/early_warning/g60_n75_stageB_20260324_184320/r008_k4_h80_ep700_lr0.006_wd0.0001_tr0.700_s44/baseline_line_risk_prediction.csv` | Baseline model line risk predictions. |
| `results/early_warning/g60_n75_stageB_20260324_184320/r008_k4_h80_ep700_lr0.006_wd0.0001_tr0.700_s44/calibrated_hourly_line_probability.csv` | Calibrated hourly line failure probability matrix. |
| `results/early_warning/g60_n75_stageB_20260324_184320/r008_k4_h80_ep700_lr0.006_wd0.0001_tr0.700_s44/critical_load_risk.csv` | Critical load risk indicators over horizon. |
| `results/early_warning/g60_n75_stageB_20260324_184320/r008_k4_h80_ep700_lr0.006_wd0.0001_tr0.700_s44/line_risk_prediction.csv` | Predicted line-level risk probabilities and labels. |
| `results/early_warning/g60_n75_stageB_20260324_184320/r008_k4_h80_ep700_lr0.006_wd0.0001_tr0.700_s44/metapath_attention_summary.csv` | MetaPath semantic attention summary statistics. |
| `results/early_warning/g60_n75_stageB_20260324_184320/r008_k4_h80_ep700_lr0.006_wd0.0001_tr0.700_s44/model_comparison.csv` | Model comparison metrics (baseline vs variants). |
| `results/early_warning/g60_n75_stageB_20260324_184320/r008_k4_h80_ep700_lr0.006_wd0.0001_tr0.700_s44/nk_failure_risk.csv` | N-k style system-level failure risk indicators. |
| `results/early_warning/g60_n75_stageB_20260324_184320/r008_k4_h80_ep700_lr0.006_wd0.0001_tr0.700_s44/train.log` | Log file captured during script/dashboard execution. |
| `results/early_warning/g60_n75_stageB_20260324_184320/r008_k4_h80_ep700_lr0.006_wd0.0001_tr0.700_s44/warning_report.json` | Stage6 warning model report with performance metrics. |
| `results/early_warning/g60_n75_stageB_20260324_184320/r009_k4_h80_ep700_lr0.006_wd0.0001_tr0.700_s45/baseline_calibrated_hourly_line_probability.csv` | Baseline calibrated hourly line probabilities. |
| `results/early_warning/g60_n75_stageB_20260324_184320/r009_k4_h80_ep700_lr0.006_wd0.0001_tr0.700_s45/baseline_line_risk_prediction.csv` | Baseline model line risk predictions. |
| `results/early_warning/g60_n75_stageB_20260324_184320/r009_k4_h80_ep700_lr0.006_wd0.0001_tr0.700_s45/calibrated_hourly_line_probability.csv` | Calibrated hourly line failure probability matrix. |
| `results/early_warning/g60_n75_stageB_20260324_184320/r009_k4_h80_ep700_lr0.006_wd0.0001_tr0.700_s45/critical_load_risk.csv` | Critical load risk indicators over horizon. |
| `results/early_warning/g60_n75_stageB_20260324_184320/r009_k4_h80_ep700_lr0.006_wd0.0001_tr0.700_s45/line_risk_prediction.csv` | Predicted line-level risk probabilities and labels. |
| `results/early_warning/g60_n75_stageB_20260324_184320/r009_k4_h80_ep700_lr0.006_wd0.0001_tr0.700_s45/metapath_attention_summary.csv` | MetaPath semantic attention summary statistics. |
| `results/early_warning/g60_n75_stageB_20260324_184320/r009_k4_h80_ep700_lr0.006_wd0.0001_tr0.700_s45/model_comparison.csv` | Model comparison metrics (baseline vs variants). |
| `results/early_warning/g60_n75_stageB_20260324_184320/r009_k4_h80_ep700_lr0.006_wd0.0001_tr0.700_s45/nk_failure_risk.csv` | N-k style system-level failure risk indicators. |
| `results/early_warning/g60_n75_stageB_20260324_184320/r009_k4_h80_ep700_lr0.006_wd0.0001_tr0.700_s45/train.log` | Log file captured during script/dashboard execution. |
| `results/early_warning/g60_n75_stageB_20260324_184320/r009_k4_h80_ep700_lr0.006_wd0.0001_tr0.700_s45/warning_report.json` | Stage6 warning model report with performance metrics. |
| `results/early_warning/g60_n75_stageB_20260324_184320/r010_k4_h80_ep700_lr0.006_wd0.0001_tr0.700_s46/baseline_calibrated_hourly_line_probability.csv` | Baseline calibrated hourly line probabilities. |
| `results/early_warning/g60_n75_stageB_20260324_184320/r010_k4_h80_ep700_lr0.006_wd0.0001_tr0.700_s46/baseline_line_risk_prediction.csv` | Baseline model line risk predictions. |
| `results/early_warning/g60_n75_stageB_20260324_184320/r010_k4_h80_ep700_lr0.006_wd0.0001_tr0.700_s46/calibrated_hourly_line_probability.csv` | Calibrated hourly line failure probability matrix. |
| `results/early_warning/g60_n75_stageB_20260324_184320/r010_k4_h80_ep700_lr0.006_wd0.0001_tr0.700_s46/critical_load_risk.csv` | Critical load risk indicators over horizon. |
| `results/early_warning/g60_n75_stageB_20260324_184320/r010_k4_h80_ep700_lr0.006_wd0.0001_tr0.700_s46/line_risk_prediction.csv` | Predicted line-level risk probabilities and labels. |
| `results/early_warning/g60_n75_stageB_20260324_184320/r010_k4_h80_ep700_lr0.006_wd0.0001_tr0.700_s46/metapath_attention_summary.csv` | MetaPath semantic attention summary statistics. |
| `results/early_warning/g60_n75_stageB_20260324_184320/r010_k4_h80_ep700_lr0.006_wd0.0001_tr0.700_s46/model_comparison.csv` | Model comparison metrics (baseline vs variants). |
| `results/early_warning/g60_n75_stageB_20260324_184320/r010_k4_h80_ep700_lr0.006_wd0.0001_tr0.700_s46/nk_failure_risk.csv` | N-k style system-level failure risk indicators. |
| `results/early_warning/g60_n75_stageB_20260324_184320/r010_k4_h80_ep700_lr0.006_wd0.0001_tr0.700_s46/train.log` | Log file captured during script/dashboard execution. |
| `results/early_warning/g60_n75_stageB_20260324_184320/r010_k4_h80_ep700_lr0.006_wd0.0001_tr0.700_s46/warning_report.json` | Stage6 warning model report with performance metrics. |
| `results/early_warning/g60_n75_stageB_20260324_184320/r011_k5_h80_ep700_lr0.006_wd0.0001_tr0.700_s42/baseline_calibrated_hourly_line_probability.csv` | Baseline calibrated hourly line probabilities. |
| `results/early_warning/g60_n75_stageB_20260324_184320/r011_k5_h80_ep700_lr0.006_wd0.0001_tr0.700_s42/baseline_line_risk_prediction.csv` | Baseline model line risk predictions. |
| `results/early_warning/g60_n75_stageB_20260324_184320/r011_k5_h80_ep700_lr0.006_wd0.0001_tr0.700_s42/calibrated_hourly_line_probability.csv` | Calibrated hourly line failure probability matrix. |
| `results/early_warning/g60_n75_stageB_20260324_184320/r011_k5_h80_ep700_lr0.006_wd0.0001_tr0.700_s42/critical_load_risk.csv` | Critical load risk indicators over horizon. |
| `results/early_warning/g60_n75_stageB_20260324_184320/r011_k5_h80_ep700_lr0.006_wd0.0001_tr0.700_s42/line_risk_prediction.csv` | Predicted line-level risk probabilities and labels. |
| `results/early_warning/g60_n75_stageB_20260324_184320/r011_k5_h80_ep700_lr0.006_wd0.0001_tr0.700_s42/metapath_attention_summary.csv` | MetaPath semantic attention summary statistics. |
| `results/early_warning/g60_n75_stageB_20260324_184320/r011_k5_h80_ep700_lr0.006_wd0.0001_tr0.700_s42/model_comparison.csv` | Model comparison metrics (baseline vs variants). |
| `results/early_warning/g60_n75_stageB_20260324_184320/r011_k5_h80_ep700_lr0.006_wd0.0001_tr0.700_s42/nk_failure_risk.csv` | N-k style system-level failure risk indicators. |
| `results/early_warning/g60_n75_stageB_20260324_184320/r011_k5_h80_ep700_lr0.006_wd0.0001_tr0.700_s42/train.log` | Log file captured during script/dashboard execution. |
| `results/early_warning/g60_n75_stageB_20260324_184320/r011_k5_h80_ep700_lr0.006_wd0.0001_tr0.700_s42/warning_report.json` | Stage6 warning model report with performance metrics. |
| `results/early_warning/g60_n75_stageB_20260324_184320/r012_k5_h80_ep700_lr0.006_wd0.0001_tr0.700_s43/baseline_calibrated_hourly_line_probability.csv` | Baseline calibrated hourly line probabilities. |
| `results/early_warning/g60_n75_stageB_20260324_184320/r012_k5_h80_ep700_lr0.006_wd0.0001_tr0.700_s43/baseline_line_risk_prediction.csv` | Baseline model line risk predictions. |
| `results/early_warning/g60_n75_stageB_20260324_184320/r012_k5_h80_ep700_lr0.006_wd0.0001_tr0.700_s43/calibrated_hourly_line_probability.csv` | Calibrated hourly line failure probability matrix. |
| `results/early_warning/g60_n75_stageB_20260324_184320/r012_k5_h80_ep700_lr0.006_wd0.0001_tr0.700_s43/critical_load_risk.csv` | Critical load risk indicators over horizon. |
| `results/early_warning/g60_n75_stageB_20260324_184320/r012_k5_h80_ep700_lr0.006_wd0.0001_tr0.700_s43/line_risk_prediction.csv` | Predicted line-level risk probabilities and labels. |
| `results/early_warning/g60_n75_stageB_20260324_184320/r012_k5_h80_ep700_lr0.006_wd0.0001_tr0.700_s43/metapath_attention_summary.csv` | MetaPath semantic attention summary statistics. |
| `results/early_warning/g60_n75_stageB_20260324_184320/r012_k5_h80_ep700_lr0.006_wd0.0001_tr0.700_s43/model_comparison.csv` | Model comparison metrics (baseline vs variants). |
| `results/early_warning/g60_n75_stageB_20260324_184320/r012_k5_h80_ep700_lr0.006_wd0.0001_tr0.700_s43/nk_failure_risk.csv` | N-k style system-level failure risk indicators. |
| `results/early_warning/g60_n75_stageB_20260324_184320/r012_k5_h80_ep700_lr0.006_wd0.0001_tr0.700_s43/train.log` | Log file captured during script/dashboard execution. |
| `results/early_warning/g60_n75_stageB_20260324_184320/r012_k5_h80_ep700_lr0.006_wd0.0001_tr0.700_s43/warning_report.json` | Stage6 warning model report with performance metrics. |
| `results/early_warning/g60_n75_stageB_20260324_184320/r013_k5_h80_ep700_lr0.006_wd0.0001_tr0.700_s44/baseline_calibrated_hourly_line_probability.csv` | Baseline calibrated hourly line probabilities. |
| `results/early_warning/g60_n75_stageB_20260324_184320/r013_k5_h80_ep700_lr0.006_wd0.0001_tr0.700_s44/baseline_line_risk_prediction.csv` | Baseline model line risk predictions. |
| `results/early_warning/g60_n75_stageB_20260324_184320/r013_k5_h80_ep700_lr0.006_wd0.0001_tr0.700_s44/calibrated_hourly_line_probability.csv` | Calibrated hourly line failure probability matrix. |
| `results/early_warning/g60_n75_stageB_20260324_184320/r013_k5_h80_ep700_lr0.006_wd0.0001_tr0.700_s44/critical_load_risk.csv` | Critical load risk indicators over horizon. |
| `results/early_warning/g60_n75_stageB_20260324_184320/r013_k5_h80_ep700_lr0.006_wd0.0001_tr0.700_s44/line_risk_prediction.csv` | Predicted line-level risk probabilities and labels. |
| `results/early_warning/g60_n75_stageB_20260324_184320/r013_k5_h80_ep700_lr0.006_wd0.0001_tr0.700_s44/metapath_attention_summary.csv` | MetaPath semantic attention summary statistics. |
| `results/early_warning/g60_n75_stageB_20260324_184320/r013_k5_h80_ep700_lr0.006_wd0.0001_tr0.700_s44/model_comparison.csv` | Model comparison metrics (baseline vs variants). |
| `results/early_warning/g60_n75_stageB_20260324_184320/r013_k5_h80_ep700_lr0.006_wd0.0001_tr0.700_s44/nk_failure_risk.csv` | N-k style system-level failure risk indicators. |
| `results/early_warning/g60_n75_stageB_20260324_184320/r013_k5_h80_ep700_lr0.006_wd0.0001_tr0.700_s44/train.log` | Log file captured during script/dashboard execution. |
| `results/early_warning/g60_n75_stageB_20260324_184320/r013_k5_h80_ep700_lr0.006_wd0.0001_tr0.700_s44/warning_report.json` | Stage6 warning model report with performance metrics. |
| `results/early_warning/g60_n75_stageB_20260324_184320/r014_k5_h80_ep700_lr0.006_wd0.0001_tr0.700_s45/baseline_calibrated_hourly_line_probability.csv` | Baseline calibrated hourly line probabilities. |
| `results/early_warning/g60_n75_stageB_20260324_184320/r014_k5_h80_ep700_lr0.006_wd0.0001_tr0.700_s45/baseline_line_risk_prediction.csv` | Baseline model line risk predictions. |
| `results/early_warning/g60_n75_stageB_20260324_184320/r014_k5_h80_ep700_lr0.006_wd0.0001_tr0.700_s45/calibrated_hourly_line_probability.csv` | Calibrated hourly line failure probability matrix. |
| `results/early_warning/g60_n75_stageB_20260324_184320/r014_k5_h80_ep700_lr0.006_wd0.0001_tr0.700_s45/critical_load_risk.csv` | Critical load risk indicators over horizon. |
| `results/early_warning/g60_n75_stageB_20260324_184320/r014_k5_h80_ep700_lr0.006_wd0.0001_tr0.700_s45/line_risk_prediction.csv` | Predicted line-level risk probabilities and labels. |
| `results/early_warning/g60_n75_stageB_20260324_184320/r014_k5_h80_ep700_lr0.006_wd0.0001_tr0.700_s45/metapath_attention_summary.csv` | MetaPath semantic attention summary statistics. |
| `results/early_warning/g60_n75_stageB_20260324_184320/r014_k5_h80_ep700_lr0.006_wd0.0001_tr0.700_s45/model_comparison.csv` | Model comparison metrics (baseline vs variants). |
| `results/early_warning/g60_n75_stageB_20260324_184320/r014_k5_h80_ep700_lr0.006_wd0.0001_tr0.700_s45/nk_failure_risk.csv` | N-k style system-level failure risk indicators. |
| `results/early_warning/g60_n75_stageB_20260324_184320/r014_k5_h80_ep700_lr0.006_wd0.0001_tr0.700_s45/train.log` | Log file captured during script/dashboard execution. |
| `results/early_warning/g60_n75_stageB_20260324_184320/r014_k5_h80_ep700_lr0.006_wd0.0001_tr0.700_s45/warning_report.json` | Stage6 warning model report with performance metrics. |
| `results/early_warning/g60_n75_stageB_20260324_184320/r015_k5_h80_ep700_lr0.006_wd0.0001_tr0.700_s46/baseline_calibrated_hourly_line_probability.csv` | Baseline calibrated hourly line probabilities. |
| `results/early_warning/g60_n75_stageB_20260324_184320/r015_k5_h80_ep700_lr0.006_wd0.0001_tr0.700_s46/baseline_line_risk_prediction.csv` | Baseline model line risk predictions. |
| `results/early_warning/g60_n75_stageB_20260324_184320/r015_k5_h80_ep700_lr0.006_wd0.0001_tr0.700_s46/calibrated_hourly_line_probability.csv` | Calibrated hourly line failure probability matrix. |
| `results/early_warning/g60_n75_stageB_20260324_184320/r015_k5_h80_ep700_lr0.006_wd0.0001_tr0.700_s46/critical_load_risk.csv` | Critical load risk indicators over horizon. |
| `results/early_warning/g60_n75_stageB_20260324_184320/r015_k5_h80_ep700_lr0.006_wd0.0001_tr0.700_s46/line_risk_prediction.csv` | Predicted line-level risk probabilities and labels. |
| `results/early_warning/g60_n75_stageB_20260324_184320/r015_k5_h80_ep700_lr0.006_wd0.0001_tr0.700_s46/metapath_attention_summary.csv` | MetaPath semantic attention summary statistics. |
| `results/early_warning/g60_n75_stageB_20260324_184320/r015_k5_h80_ep700_lr0.006_wd0.0001_tr0.700_s46/model_comparison.csv` | Model comparison metrics (baseline vs variants). |
| `results/early_warning/g60_n75_stageB_20260324_184320/r015_k5_h80_ep700_lr0.006_wd0.0001_tr0.700_s46/nk_failure_risk.csv` | N-k style system-level failure risk indicators. |
| `results/early_warning/g60_n75_stageB_20260324_184320/r015_k5_h80_ep700_lr0.006_wd0.0001_tr0.700_s46/train.log` | Log file captured during script/dashboard execution. |
| `results/early_warning/g60_n75_stageB_20260324_184320/r015_k5_h80_ep700_lr0.006_wd0.0001_tr0.700_s46/warning_report.json` | Stage6 warning model report with performance metrics. |
| `results/early_warning/g60_n75_stageB_20260324_184320/summary_by_setting.csv` | Aggregated sweep metrics by configuration setting. |
| `results/early_warning/g60_n75_weatherfield_smoke/baseline_calibrated_hourly_line_probability.csv` | Baseline calibrated hourly line probabilities. |
| `results/early_warning/g60_n75_weatherfield_smoke/baseline_line_risk_prediction.csv` | Baseline model line risk predictions. |
| `results/early_warning/g60_n75_weatherfield_smoke/calibrated_hourly_line_probability.csv` | Calibrated hourly line failure probability matrix. |
| `results/early_warning/g60_n75_weatherfield_smoke/critical_load_risk.csv` | Critical load risk indicators over horizon. |
| `results/early_warning/g60_n75_weatherfield_smoke/line_risk_prediction.csv` | Predicted line-level risk probabilities and labels. |
| `results/early_warning/g60_n75_weatherfield_smoke/metapath_attention_summary.csv` | MetaPath semantic attention summary statistics. |
| `results/early_warning/g60_n75_weatherfield_smoke/model_comparison.csv` | Model comparison metrics (baseline vs variants). |
| `results/early_warning/g60_n75_weatherfield_smoke/nk_failure_risk.csv` | N-k style system-level failure risk indicators. |
| `results/early_warning/g60_n75_weatherfield_smoke/warning_report.json` | Stage6 warning model report with performance metrics. |
| `results/early_warning/ieee118_n60_weatherfield_smoke/baseline_calibrated_hourly_line_probability.csv` | Baseline calibrated hourly line probabilities. |
| `results/early_warning/ieee118_n60_weatherfield_smoke/baseline_line_risk_prediction.csv` | Baseline model line risk predictions. |
| `results/early_warning/ieee118_n60_weatherfield_smoke/calibrated_hourly_line_probability.csv` | Calibrated hourly line failure probability matrix. |
| `results/early_warning/ieee118_n60_weatherfield_smoke/critical_load_risk.csv` | Critical load risk indicators over horizon. |
| `results/early_warning/ieee118_n60_weatherfield_smoke/line_risk_prediction.csv` | Predicted line-level risk probabilities and labels. |
| `results/early_warning/ieee118_n60_weatherfield_smoke/metapath_attention_summary.csv` | MetaPath semantic attention summary statistics. |
| `results/early_warning/ieee118_n60_weatherfield_smoke/model_comparison.csv` | Model comparison metrics (baseline vs variants). |
| `results/early_warning/ieee118_n60_weatherfield_smoke/nk_failure_risk.csv` | N-k style system-level failure risk indicators. |
| `results/early_warning/ieee118_n60_weatherfield_smoke/warning_report.json` | Stage6 warning model report with performance metrics. |
| `results/early_warning/ieee118_n60_weatherfield_traceability_smoke/baseline_calibrated_hourly_line_probability.csv` | Baseline calibrated hourly line probabilities. |
| `results/early_warning/ieee118_n60_weatherfield_traceability_smoke/baseline_line_risk_prediction.csv` | Baseline model line risk predictions. |
| `results/early_warning/ieee118_n60_weatherfield_traceability_smoke/calibrated_hourly_line_probability.csv` | Calibrated hourly line failure probability matrix. |
| `results/early_warning/ieee118_n60_weatherfield_traceability_smoke/critical_load_risk.csv` | Critical load risk indicators over horizon. |
| `results/early_warning/ieee118_n60_weatherfield_traceability_smoke/line_risk_prediction.csv` | Predicted line-level risk probabilities and labels. |
| `results/early_warning/ieee118_n60_weatherfield_traceability_smoke/metapath_attention_summary.csv` | MetaPath semantic attention summary statistics. |
| `results/early_warning/ieee118_n60_weatherfield_traceability_smoke/model_comparison.csv` | Model comparison metrics (baseline vs variants). |
| `results/early_warning/ieee118_n60_weatherfield_traceability_smoke/nk_failure_risk.csv` | N-k style system-level failure risk indicators. |
| `results/early_warning/ieee118_n60_weatherfield_traceability_smoke/node_weather_horizon.csv` | Forecast horizon weather features per node. |
| `results/early_warning/ieee118_n60_weatherfield_traceability_smoke/node_weather_summary.csv` | Aggregated node weather statistics. |
| `results/early_warning/ieee118_n60_weatherfield_traceability_smoke/node_weather_timeseries.csv` | Node-level weather time series used by warning stage. |
| `results/early_warning/ieee118_n60_weatherfield_traceability_smoke/warning_report.json` | Stage6 warning model report with performance metrics. |
| `results/early_warning/metapath_scale_real_smoke_20260324_144922/all_runs.csv` | Summary of all run settings/results in a sweep. |
| `results/early_warning/metapath_scale_real_smoke_20260324_144922/done.json` | Completion flag/metadata for finished run. |
| `results/early_warning/metapath_scale_real_smoke_20260324_144922/experiment_config.json` | Experiment configuration snapshot for a run. |
| `results/early_warning/metapath_scale_real_smoke_20260324_144922/r001_k4_h32_ep5_lr0.01_wd0.0001_tr0.700_s42/train.log` | Log file captured during script/dashboard execution. |
| `results/early_warning/metapath_scale_real_smoke_20260324_144922/summary_by_setting.csv` | Aggregated sweep metrics by configuration setting. |
| `results/early_warning/metapath_scale_real_smoke2_20260324_145242/all_runs.csv` | Summary of all run settings/results in a sweep. |
| `results/early_warning/metapath_scale_real_smoke2_20260324_145242/done.json` | Completion flag/metadata for finished run. |
| `results/early_warning/metapath_scale_real_smoke2_20260324_145242/experiment_config.json` | Experiment configuration snapshot for a run. |
| `results/early_warning/metapath_scale_real_smoke2_20260324_145242/r001_k4_h32_ep5_lr0.01_wd0.0001_tr0.700_s42/baseline_calibrated_hourly_line_probability.csv` | Baseline calibrated hourly line probabilities. |
| `results/early_warning/metapath_scale_real_smoke2_20260324_145242/r001_k4_h32_ep5_lr0.01_wd0.0001_tr0.700_s42/baseline_line_risk_prediction.csv` | Baseline model line risk predictions. |
| `results/early_warning/metapath_scale_real_smoke2_20260324_145242/r001_k4_h32_ep5_lr0.01_wd0.0001_tr0.700_s42/calibrated_hourly_line_probability.csv` | Calibrated hourly line failure probability matrix. |
| `results/early_warning/metapath_scale_real_smoke2_20260324_145242/r001_k4_h32_ep5_lr0.01_wd0.0001_tr0.700_s42/critical_load_risk.csv` | Critical load risk indicators over horizon. |
| `results/early_warning/metapath_scale_real_smoke2_20260324_145242/r001_k4_h32_ep5_lr0.01_wd0.0001_tr0.700_s42/line_risk_prediction.csv` | Predicted line-level risk probabilities and labels. |
| `results/early_warning/metapath_scale_real_smoke2_20260324_145242/r001_k4_h32_ep5_lr0.01_wd0.0001_tr0.700_s42/metapath_attention_summary.csv` | MetaPath semantic attention summary statistics. |
| `results/early_warning/metapath_scale_real_smoke2_20260324_145242/r001_k4_h32_ep5_lr0.01_wd0.0001_tr0.700_s42/model_comparison.csv` | Model comparison metrics (baseline vs variants). |
| `results/early_warning/metapath_scale_real_smoke2_20260324_145242/r001_k4_h32_ep5_lr0.01_wd0.0001_tr0.700_s42/nk_failure_risk.csv` | N-k style system-level failure risk indicators. |
| `results/early_warning/metapath_scale_real_smoke2_20260324_145242/r001_k4_h32_ep5_lr0.01_wd0.0001_tr0.700_s42/train.log` | Log file captured during script/dashboard execution. |
| `results/early_warning/metapath_scale_real_smoke2_20260324_145242/r001_k4_h32_ep5_lr0.01_wd0.0001_tr0.700_s42/warning_report.json` | Stage6 warning model report with performance metrics. |
| `results/early_warning/metapath_scale_real_smoke2_20260324_145242/summary_by_setting.csv` | Aggregated sweep metrics by configuration setting. |
| `results/early_warning/metapath_scale_smoke_20260324_144859/all_runs.csv` | Summary of all run settings/results in a sweep. |
| `results/early_warning/metapath_scale_smoke_20260324_144859/done.json` | Completion flag/metadata for finished run. |
| `results/early_warning/metapath_scale_smoke_20260324_144859/experiment_config.json` | Experiment configuration snapshot for a run. |
| `results/early_warning/metapath_scale_smoke_20260324_144859/r001_k3_h64_ep700_lr0.006_wd0.0001_tr0.700_s42/train.log` | Log file captured during script/dashboard execution. |
| `results/early_warning/metapath_scale_smoke_20260324_144859/r002_k3_h64_ep700_lr0.006_wd0.0001_tr0.700_s43/train.log` | Log file captured during script/dashboard execution. |
| `results/early_warning/metapath_scale_smoke_20260324_144859/summary_by_setting.csv` | Aggregated sweep metrics by configuration setting. |
| `results/early_warning/metapath_scale_smoke2_20260324_145147/all_runs.csv` | Summary of all run settings/results in a sweep. |
| `results/early_warning/metapath_scale_smoke2_20260324_145147/done.json` | Completion flag/metadata for finished run. |
| `results/early_warning/metapath_scale_smoke2_20260324_145147/experiment_config.json` | Experiment configuration snapshot for a run. |
| `results/early_warning/metapath_scale_smoke2_20260324_145147/r001_k3_h64_ep700_lr0.006_wd0.0001_tr0.700_s42/train.log` | Log file captured during script/dashboard execution. |
| `results/early_warning/metapath_scale_smoke2_20260324_145147/summary_by_setting.csv` | Aggregated sweep metrics by configuration setting. |
| `results/early_warning/metapath_scale_smoke2_20260324_145214/all_runs.csv` | Summary of all run settings/results in a sweep. |
| `results/early_warning/metapath_scale_smoke2_20260324_145214/done.json` | Completion flag/metadata for finished run. |
| `results/early_warning/metapath_scale_smoke2_20260324_145214/experiment_config.json` | Experiment configuration snapshot for a run. |
| `results/early_warning/metapath_scale_smoke2_20260324_145214/r001_k3_h64_ep700_lr0.006_wd0.0001_tr0.700_s42/train.log` | Log file captured during script/dashboard execution. |
| `results/early_warning/metapath_scale_smoke2_20260324_145214/summary_by_setting.csv` | Aggregated sweep metrics by configuration setting. |
| `results/early_warning/metapath_sweep_v1/a_topk4_lr0.01_hd64/baseline_calibrated_hourly_line_probability.csv` | Baseline calibrated hourly line probabilities. |
| `results/early_warning/metapath_sweep_v1/a_topk4_lr0.01_hd64/baseline_line_risk_prediction.csv` | Baseline model line risk predictions. |
| `results/early_warning/metapath_sweep_v1/a_topk4_lr0.01_hd64/calibrated_hourly_line_probability.csv` | Calibrated hourly line failure probability matrix. |
| `results/early_warning/metapath_sweep_v1/a_topk4_lr0.01_hd64/critical_load_risk.csv` | Critical load risk indicators over horizon. |
| `results/early_warning/metapath_sweep_v1/a_topk4_lr0.01_hd64/line_risk_prediction.csv` | Predicted line-level risk probabilities and labels. |
| `results/early_warning/metapath_sweep_v1/a_topk4_lr0.01_hd64/metapath_attention_summary.csv` | MetaPath semantic attention summary statistics. |
| `results/early_warning/metapath_sweep_v1/a_topk4_lr0.01_hd64/model_comparison.csv` | Model comparison metrics (baseline vs variants). |
| `results/early_warning/metapath_sweep_v1/a_topk4_lr0.01_hd64/nk_failure_risk.csv` | N-k style system-level failure risk indicators. |
| `results/early_warning/metapath_sweep_v1/a_topk4_lr0.01_hd64/warning_report.json` | Stage6 warning model report with performance metrics. |
| `results/early_warning/metapath_sweep_v1/b_topk3_lr0.008_hd64/baseline_calibrated_hourly_line_probability.csv` | Baseline calibrated hourly line probabilities. |
| `results/early_warning/metapath_sweep_v1/b_topk3_lr0.008_hd64/baseline_line_risk_prediction.csv` | Baseline model line risk predictions. |
| `results/early_warning/metapath_sweep_v1/b_topk3_lr0.008_hd64/calibrated_hourly_line_probability.csv` | Calibrated hourly line failure probability matrix. |
| `results/early_warning/metapath_sweep_v1/b_topk3_lr0.008_hd64/critical_load_risk.csv` | Critical load risk indicators over horizon. |
| `results/early_warning/metapath_sweep_v1/b_topk3_lr0.008_hd64/line_risk_prediction.csv` | Predicted line-level risk probabilities and labels. |
| `results/early_warning/metapath_sweep_v1/b_topk3_lr0.008_hd64/metapath_attention_summary.csv` | MetaPath semantic attention summary statistics. |
| `results/early_warning/metapath_sweep_v1/b_topk3_lr0.008_hd64/model_comparison.csv` | Model comparison metrics (baseline vs variants). |
| `results/early_warning/metapath_sweep_v1/b_topk3_lr0.008_hd64/nk_failure_risk.csv` | N-k style system-level failure risk indicators. |
| `results/early_warning/metapath_sweep_v1/b_topk3_lr0.008_hd64/warning_report.json` | Stage6 warning model report with performance metrics. |
| `results/early_warning/metapath_sweep_v1/c_topk5_lr0.006_hd64/baseline_calibrated_hourly_line_probability.csv` | Baseline calibrated hourly line probabilities. |
| `results/early_warning/metapath_sweep_v1/c_topk5_lr0.006_hd64/baseline_line_risk_prediction.csv` | Baseline model line risk predictions. |
| `results/early_warning/metapath_sweep_v1/c_topk5_lr0.006_hd64/calibrated_hourly_line_probability.csv` | Calibrated hourly line failure probability matrix. |
| `results/early_warning/metapath_sweep_v1/c_topk5_lr0.006_hd64/critical_load_risk.csv` | Critical load risk indicators over horizon. |
| `results/early_warning/metapath_sweep_v1/c_topk5_lr0.006_hd64/line_risk_prediction.csv` | Predicted line-level risk probabilities and labels. |
| `results/early_warning/metapath_sweep_v1/c_topk5_lr0.006_hd64/metapath_attention_summary.csv` | MetaPath semantic attention summary statistics. |
| `results/early_warning/metapath_sweep_v1/c_topk5_lr0.006_hd64/model_comparison.csv` | Model comparison metrics (baseline vs variants). |
| `results/early_warning/metapath_sweep_v1/c_topk5_lr0.006_hd64/nk_failure_risk.csv` | N-k style system-level failure risk indicators. |
| `results/early_warning/metapath_sweep_v1/c_topk5_lr0.006_hd64/warning_report.json` | Stage6 warning model report with performance metrics. |
| `results/early_warning/metapath_sweep_v1/d_topk4_lr0.006_hd80/baseline_calibrated_hourly_line_probability.csv` | Baseline calibrated hourly line probabilities. |
| `results/early_warning/metapath_sweep_v1/d_topk4_lr0.006_hd80/baseline_line_risk_prediction.csv` | Baseline model line risk predictions. |
| `results/early_warning/metapath_sweep_v1/d_topk4_lr0.006_hd80/calibrated_hourly_line_probability.csv` | Calibrated hourly line failure probability matrix. |
| `results/early_warning/metapath_sweep_v1/d_topk4_lr0.006_hd80/critical_load_risk.csv` | Critical load risk indicators over horizon. |
| `results/early_warning/metapath_sweep_v1/d_topk4_lr0.006_hd80/line_risk_prediction.csv` | Predicted line-level risk probabilities and labels. |
| `results/early_warning/metapath_sweep_v1/d_topk4_lr0.006_hd80/metapath_attention_summary.csv` | MetaPath semantic attention summary statistics. |
| `results/early_warning/metapath_sweep_v1/d_topk4_lr0.006_hd80/model_comparison.csv` | Model comparison metrics (baseline vs variants). |
| `results/early_warning/metapath_sweep_v1/d_topk4_lr0.006_hd80/nk_failure_risk.csv` | N-k style system-level failure risk indicators. |
| `results/early_warning/metapath_sweep_v1/d_topk4_lr0.006_hd80/warning_report.json` | Stage6 warning model report with performance metrics. |
| `results/early_warning/metapath_sweep_v1/sweep_summary.csv` | CSV table; columns: baseline_best_val_mse, baseline_horizon_mae, baseline_val_mae, delta_best_val_mse, delta_horizon_mae, delta_val_mae, metapath_best_val_mse, metapath_horizon_mae, .... |
| `results/early_warning/metapath_sweep_v2/r1_topk4_lr0.006_hd80_ep700/baseline_calibrated_hourly_line_probability.csv` | Baseline calibrated hourly line probabilities. |
| `results/early_warning/metapath_sweep_v2/r1_topk4_lr0.006_hd80_ep700/baseline_line_risk_prediction.csv` | Baseline model line risk predictions. |
| `results/early_warning/metapath_sweep_v2/r1_topk4_lr0.006_hd80_ep700/calibrated_hourly_line_probability.csv` | Calibrated hourly line failure probability matrix. |
| `results/early_warning/metapath_sweep_v2/r1_topk4_lr0.006_hd80_ep700/critical_load_risk.csv` | Critical load risk indicators over horizon. |
| `results/early_warning/metapath_sweep_v2/r1_topk4_lr0.006_hd80_ep700/line_risk_prediction.csv` | Predicted line-level risk probabilities and labels. |
| `results/early_warning/metapath_sweep_v2/r1_topk4_lr0.006_hd80_ep700/metapath_attention_summary.csv` | MetaPath semantic attention summary statistics. |
| `results/early_warning/metapath_sweep_v2/r1_topk4_lr0.006_hd80_ep700/model_comparison.csv` | Model comparison metrics (baseline vs variants). |
| `results/early_warning/metapath_sweep_v2/r1_topk4_lr0.006_hd80_ep700/nk_failure_risk.csv` | N-k style system-level failure risk indicators. |
| `results/early_warning/metapath_sweep_v2/r1_topk4_lr0.006_hd80_ep700/warning_report.json` | Stage6 warning model report with performance metrics. |
| `results/early_warning/metapath_sweep_v2/r2_topk4_lr0.005_hd80_ep900/baseline_calibrated_hourly_line_probability.csv` | Baseline calibrated hourly line probabilities. |
| `results/early_warning/metapath_sweep_v2/r2_topk4_lr0.005_hd80_ep900/baseline_line_risk_prediction.csv` | Baseline model line risk predictions. |
| `results/early_warning/metapath_sweep_v2/r2_topk4_lr0.005_hd80_ep900/calibrated_hourly_line_probability.csv` | Calibrated hourly line failure probability matrix. |
| `results/early_warning/metapath_sweep_v2/r2_topk4_lr0.005_hd80_ep900/critical_load_risk.csv` | Critical load risk indicators over horizon. |
| `results/early_warning/metapath_sweep_v2/r2_topk4_lr0.005_hd80_ep900/line_risk_prediction.csv` | Predicted line-level risk probabilities and labels. |
| `results/early_warning/metapath_sweep_v2/r2_topk4_lr0.005_hd80_ep900/metapath_attention_summary.csv` | MetaPath semantic attention summary statistics. |
| `results/early_warning/metapath_sweep_v2/r2_topk4_lr0.005_hd80_ep900/model_comparison.csv` | Model comparison metrics (baseline vs variants). |
| `results/early_warning/metapath_sweep_v2/r2_topk4_lr0.005_hd80_ep900/nk_failure_risk.csv` | N-k style system-level failure risk indicators. |
| `results/early_warning/metapath_sweep_v2/r2_topk4_lr0.005_hd80_ep900/warning_report.json` | Stage6 warning model report with performance metrics. |
| `results/early_warning/metapath_sweep_v2/r3_topk3_lr0.005_hd80_ep900/baseline_calibrated_hourly_line_probability.csv` | Baseline calibrated hourly line probabilities. |
| `results/early_warning/metapath_sweep_v2/r3_topk3_lr0.005_hd80_ep900/baseline_line_risk_prediction.csv` | Baseline model line risk predictions. |
| `results/early_warning/metapath_sweep_v2/r3_topk3_lr0.005_hd80_ep900/calibrated_hourly_line_probability.csv` | Calibrated hourly line failure probability matrix. |
| `results/early_warning/metapath_sweep_v2/r3_topk3_lr0.005_hd80_ep900/critical_load_risk.csv` | Critical load risk indicators over horizon. |
| `results/early_warning/metapath_sweep_v2/r3_topk3_lr0.005_hd80_ep900/line_risk_prediction.csv` | Predicted line-level risk probabilities and labels. |
| `results/early_warning/metapath_sweep_v2/r3_topk3_lr0.005_hd80_ep900/metapath_attention_summary.csv` | MetaPath semantic attention summary statistics. |
| `results/early_warning/metapath_sweep_v2/r3_topk3_lr0.005_hd80_ep900/model_comparison.csv` | Model comparison metrics (baseline vs variants). |
| `results/early_warning/metapath_sweep_v2/r3_topk3_lr0.005_hd80_ep900/nk_failure_risk.csv` | N-k style system-level failure risk indicators. |
| `results/early_warning/metapath_sweep_v2/r3_topk3_lr0.005_hd80_ep900/warning_report.json` | Stage6 warning model report with performance metrics. |
| `results/early_warning/metapath_sweep_v2/r4_topk5_lr0.005_hd96_ep900/baseline_calibrated_hourly_line_probability.csv` | Baseline calibrated hourly line probabilities. |
| `results/early_warning/metapath_sweep_v2/r4_topk5_lr0.005_hd96_ep900/baseline_line_risk_prediction.csv` | Baseline model line risk predictions. |
| `results/early_warning/metapath_sweep_v2/r4_topk5_lr0.005_hd96_ep900/calibrated_hourly_line_probability.csv` | Calibrated hourly line failure probability matrix. |
| `results/early_warning/metapath_sweep_v2/r4_topk5_lr0.005_hd96_ep900/critical_load_risk.csv` | Critical load risk indicators over horizon. |
| `results/early_warning/metapath_sweep_v2/r4_topk5_lr0.005_hd96_ep900/line_risk_prediction.csv` | Predicted line-level risk probabilities and labels. |
| `results/early_warning/metapath_sweep_v2/r4_topk5_lr0.005_hd96_ep900/metapath_attention_summary.csv` | MetaPath semantic attention summary statistics. |
| `results/early_warning/metapath_sweep_v2/r4_topk5_lr0.005_hd96_ep900/model_comparison.csv` | Model comparison metrics (baseline vs variants). |
| `results/early_warning/metapath_sweep_v2/r4_topk5_lr0.005_hd96_ep900/nk_failure_risk.csv` | N-k style system-level failure risk indicators. |
| `results/early_warning/metapath_sweep_v2/r4_topk5_lr0.005_hd96_ep900/warning_report.json` | Stage6 warning model report with performance metrics. |
| `results/early_warning/metapath_sweep_v2/r5_topk4_lr0.004_hd96_ep1200/baseline_calibrated_hourly_line_probability.csv` | Baseline calibrated hourly line probabilities. |
| `results/early_warning/metapath_sweep_v2/r5_topk4_lr0.004_hd96_ep1200/baseline_line_risk_prediction.csv` | Baseline model line risk predictions. |
| `results/early_warning/metapath_sweep_v2/r5_topk4_lr0.004_hd96_ep1200/calibrated_hourly_line_probability.csv` | Calibrated hourly line failure probability matrix. |
| `results/early_warning/metapath_sweep_v2/r5_topk4_lr0.004_hd96_ep1200/critical_load_risk.csv` | Critical load risk indicators over horizon. |
| `results/early_warning/metapath_sweep_v2/r5_topk4_lr0.004_hd96_ep1200/line_risk_prediction.csv` | Predicted line-level risk probabilities and labels. |
| `results/early_warning/metapath_sweep_v2/r5_topk4_lr0.004_hd96_ep1200/metapath_attention_summary.csv` | MetaPath semantic attention summary statistics. |
| `results/early_warning/metapath_sweep_v2/r5_topk4_lr0.004_hd96_ep1200/model_comparison.csv` | Model comparison metrics (baseline vs variants). |
| `results/early_warning/metapath_sweep_v2/r5_topk4_lr0.004_hd96_ep1200/nk_failure_risk.csv` | N-k style system-level failure risk indicators. |
| `results/early_warning/metapath_sweep_v2/r5_topk4_lr0.004_hd96_ep1200/warning_report.json` | Stage6 warning model report with performance metrics. |
| `results/early_warning/metapath_sweep_v2/sweep_summary.csv` | CSV table; columns: baseline_best_val_mse, baseline_horizon_mae, baseline_val_mae, delta_best_val_mse, delta_horizon_mae, delta_val_mae, metapath_best_val_mse, metapath_horizon_mae, .... |
| `results/early_warning/metapath_sweep_v3_allwin/s01_k4_h80_lr0.006_ep700/baseline_calibrated_hourly_line_probability.csv` | Baseline calibrated hourly line probabilities. |
| `results/early_warning/metapath_sweep_v3_allwin/s01_k4_h80_lr0.006_ep700/baseline_line_risk_prediction.csv` | Baseline model line risk predictions. |
| `results/early_warning/metapath_sweep_v3_allwin/s01_k4_h80_lr0.006_ep700/calibrated_hourly_line_probability.csv` | Calibrated hourly line failure probability matrix. |
| `results/early_warning/metapath_sweep_v3_allwin/s01_k4_h80_lr0.006_ep700/critical_load_risk.csv` | Critical load risk indicators over horizon. |
| `results/early_warning/metapath_sweep_v3_allwin/s01_k4_h80_lr0.006_ep700/line_risk_prediction.csv` | Predicted line-level risk probabilities and labels. |
| `results/early_warning/metapath_sweep_v3_allwin/s01_k4_h80_lr0.006_ep700/metapath_attention_summary.csv` | MetaPath semantic attention summary statistics. |
| `results/early_warning/metapath_sweep_v3_allwin/s01_k4_h80_lr0.006_ep700/model_comparison.csv` | Model comparison metrics (baseline vs variants). |
| `results/early_warning/metapath_sweep_v3_allwin/s01_k4_h80_lr0.006_ep700/nk_failure_risk.csv` | N-k style system-level failure risk indicators. |
| `results/early_warning/metapath_sweep_v3_allwin/s01_k4_h80_lr0.006_ep700/warning_report.json` | Stage6 warning model report with performance metrics. |
| `results/early_warning/metapath_sweep_v3_allwin/s02_k4_h80_lr0.0055_ep800/baseline_calibrated_hourly_line_probability.csv` | Baseline calibrated hourly line probabilities. |
| `results/early_warning/metapath_sweep_v3_allwin/s02_k4_h80_lr0.0055_ep800/baseline_line_risk_prediction.csv` | Baseline model line risk predictions. |
| `results/early_warning/metapath_sweep_v3_allwin/s02_k4_h80_lr0.0055_ep800/calibrated_hourly_line_probability.csv` | Calibrated hourly line failure probability matrix. |
| `results/early_warning/metapath_sweep_v3_allwin/s02_k4_h80_lr0.0055_ep800/critical_load_risk.csv` | Critical load risk indicators over horizon. |
| `results/early_warning/metapath_sweep_v3_allwin/s02_k4_h80_lr0.0055_ep800/line_risk_prediction.csv` | Predicted line-level risk probabilities and labels. |
| `results/early_warning/metapath_sweep_v3_allwin/s02_k4_h80_lr0.0055_ep800/metapath_attention_summary.csv` | MetaPath semantic attention summary statistics. |
| `results/early_warning/metapath_sweep_v3_allwin/s02_k4_h80_lr0.0055_ep800/model_comparison.csv` | Model comparison metrics (baseline vs variants). |
| `results/early_warning/metapath_sweep_v3_allwin/s02_k4_h80_lr0.0055_ep800/nk_failure_risk.csv` | N-k style system-level failure risk indicators. |
| `results/early_warning/metapath_sweep_v3_allwin/s02_k4_h80_lr0.0055_ep800/warning_report.json` | Stage6 warning model report with performance metrics. |
| `results/early_warning/metapath_sweep_v3_allwin/s03_k4_h80_lr0.005_ep900/baseline_calibrated_hourly_line_probability.csv` | Baseline calibrated hourly line probabilities. |
| `results/early_warning/metapath_sweep_v3_allwin/s03_k4_h80_lr0.005_ep900/baseline_line_risk_prediction.csv` | Baseline model line risk predictions. |
| `results/early_warning/metapath_sweep_v3_allwin/s03_k4_h80_lr0.005_ep900/calibrated_hourly_line_probability.csv` | Calibrated hourly line failure probability matrix. |
| `results/early_warning/metapath_sweep_v3_allwin/s03_k4_h80_lr0.005_ep900/critical_load_risk.csv` | Critical load risk indicators over horizon. |
| `results/early_warning/metapath_sweep_v3_allwin/s03_k4_h80_lr0.005_ep900/line_risk_prediction.csv` | Predicted line-level risk probabilities and labels. |
| `results/early_warning/metapath_sweep_v3_allwin/s03_k4_h80_lr0.005_ep900/metapath_attention_summary.csv` | MetaPath semantic attention summary statistics. |
| `results/early_warning/metapath_sweep_v3_allwin/s03_k4_h80_lr0.005_ep900/model_comparison.csv` | Model comparison metrics (baseline vs variants). |
| `results/early_warning/metapath_sweep_v3_allwin/s03_k4_h80_lr0.005_ep900/nk_failure_risk.csv` | N-k style system-level failure risk indicators. |
| `results/early_warning/metapath_sweep_v3_allwin/s03_k4_h80_lr0.005_ep900/warning_report.json` | Stage6 warning model report with performance metrics. |
| `results/early_warning/metapath_sweep_v3_allwin/s04_k4_h80_lr0.0045_ep1000/baseline_calibrated_hourly_line_probability.csv` | Baseline calibrated hourly line probabilities. |
| `results/early_warning/metapath_sweep_v3_allwin/s04_k4_h80_lr0.0045_ep1000/baseline_line_risk_prediction.csv` | Baseline model line risk predictions. |
| `results/early_warning/metapath_sweep_v3_allwin/s04_k4_h80_lr0.0045_ep1000/calibrated_hourly_line_probability.csv` | Calibrated hourly line failure probability matrix. |
| `results/early_warning/metapath_sweep_v3_allwin/s04_k4_h80_lr0.0045_ep1000/critical_load_risk.csv` | Critical load risk indicators over horizon. |
| `results/early_warning/metapath_sweep_v3_allwin/s04_k4_h80_lr0.0045_ep1000/line_risk_prediction.csv` | Predicted line-level risk probabilities and labels. |
| `results/early_warning/metapath_sweep_v3_allwin/s04_k4_h80_lr0.0045_ep1000/metapath_attention_summary.csv` | MetaPath semantic attention summary statistics. |
| `results/early_warning/metapath_sweep_v3_allwin/s04_k4_h80_lr0.0045_ep1000/model_comparison.csv` | Model comparison metrics (baseline vs variants). |
| `results/early_warning/metapath_sweep_v3_allwin/s04_k4_h80_lr0.0045_ep1000/nk_failure_risk.csv` | N-k style system-level failure risk indicators. |
| `results/early_warning/metapath_sweep_v3_allwin/s04_k4_h80_lr0.0045_ep1000/warning_report.json` | Stage6 warning model report with performance metrics. |
| `results/early_warning/metapath_sweep_v3_allwin/s05_k3_h80_lr0.005_ep900/baseline_calibrated_hourly_line_probability.csv` | Baseline calibrated hourly line probabilities. |
| `results/early_warning/metapath_sweep_v3_allwin/s05_k3_h80_lr0.005_ep900/baseline_line_risk_prediction.csv` | Baseline model line risk predictions. |
| `results/early_warning/metapath_sweep_v3_allwin/s05_k3_h80_lr0.005_ep900/calibrated_hourly_line_probability.csv` | Calibrated hourly line failure probability matrix. |
| `results/early_warning/metapath_sweep_v3_allwin/s05_k3_h80_lr0.005_ep900/critical_load_risk.csv` | Critical load risk indicators over horizon. |
| `results/early_warning/metapath_sweep_v3_allwin/s05_k3_h80_lr0.005_ep900/line_risk_prediction.csv` | Predicted line-level risk probabilities and labels. |
| `results/early_warning/metapath_sweep_v3_allwin/s05_k3_h80_lr0.005_ep900/metapath_attention_summary.csv` | MetaPath semantic attention summary statistics. |
| `results/early_warning/metapath_sweep_v3_allwin/s05_k3_h80_lr0.005_ep900/model_comparison.csv` | Model comparison metrics (baseline vs variants). |
| `results/early_warning/metapath_sweep_v3_allwin/s05_k3_h80_lr0.005_ep900/nk_failure_risk.csv` | N-k style system-level failure risk indicators. |
| `results/early_warning/metapath_sweep_v3_allwin/s05_k3_h80_lr0.005_ep900/warning_report.json` | Stage6 warning model report with performance metrics. |
| `results/early_warning/metapath_sweep_v3_allwin/s06_k5_h80_lr0.005_ep900/baseline_calibrated_hourly_line_probability.csv` | Baseline calibrated hourly line probabilities. |
| `results/early_warning/metapath_sweep_v3_allwin/s06_k5_h80_lr0.005_ep900/baseline_line_risk_prediction.csv` | Baseline model line risk predictions. |
| `results/early_warning/metapath_sweep_v3_allwin/s06_k5_h80_lr0.005_ep900/calibrated_hourly_line_probability.csv` | Calibrated hourly line failure probability matrix. |
| `results/early_warning/metapath_sweep_v3_allwin/s06_k5_h80_lr0.005_ep900/critical_load_risk.csv` | Critical load risk indicators over horizon. |
| `results/early_warning/metapath_sweep_v3_allwin/s06_k5_h80_lr0.005_ep900/line_risk_prediction.csv` | Predicted line-level risk probabilities and labels. |
| `results/early_warning/metapath_sweep_v3_allwin/s06_k5_h80_lr0.005_ep900/metapath_attention_summary.csv` | MetaPath semantic attention summary statistics. |
| `results/early_warning/metapath_sweep_v3_allwin/s06_k5_h80_lr0.005_ep900/model_comparison.csv` | Model comparison metrics (baseline vs variants). |
| `results/early_warning/metapath_sweep_v3_allwin/s06_k5_h80_lr0.005_ep900/nk_failure_risk.csv` | N-k style system-level failure risk indicators. |
| `results/early_warning/metapath_sweep_v3_allwin/s06_k5_h80_lr0.005_ep900/warning_report.json` | Stage6 warning model report with performance metrics. |
| `results/early_warning/metapath_sweep_v3_allwin/s07_k4_h72_lr0.006_ep800/baseline_calibrated_hourly_line_probability.csv` | Baseline calibrated hourly line probabilities. |
| `results/early_warning/metapath_sweep_v3_allwin/s07_k4_h72_lr0.006_ep800/baseline_line_risk_prediction.csv` | Baseline model line risk predictions. |
| `results/early_warning/metapath_sweep_v3_allwin/s07_k4_h72_lr0.006_ep800/calibrated_hourly_line_probability.csv` | Calibrated hourly line failure probability matrix. |
| `results/early_warning/metapath_sweep_v3_allwin/s07_k4_h72_lr0.006_ep800/critical_load_risk.csv` | Critical load risk indicators over horizon. |
| `results/early_warning/metapath_sweep_v3_allwin/s07_k4_h72_lr0.006_ep800/line_risk_prediction.csv` | Predicted line-level risk probabilities and labels. |
| `results/early_warning/metapath_sweep_v3_allwin/s07_k4_h72_lr0.006_ep800/metapath_attention_summary.csv` | MetaPath semantic attention summary statistics. |
| `results/early_warning/metapath_sweep_v3_allwin/s07_k4_h72_lr0.006_ep800/model_comparison.csv` | Model comparison metrics (baseline vs variants). |
| `results/early_warning/metapath_sweep_v3_allwin/s07_k4_h72_lr0.006_ep800/nk_failure_risk.csv` | N-k style system-level failure risk indicators. |
| `results/early_warning/metapath_sweep_v3_allwin/s07_k4_h72_lr0.006_ep800/warning_report.json` | Stage6 warning model report with performance metrics. |
| `results/early_warning/metapath_sweep_v3_allwin/s08_k4_h88_lr0.006_ep800/baseline_calibrated_hourly_line_probability.csv` | Baseline calibrated hourly line probabilities. |
| `results/early_warning/metapath_sweep_v3_allwin/s08_k4_h88_lr0.006_ep800/baseline_line_risk_prediction.csv` | Baseline model line risk predictions. |
| `results/early_warning/metapath_sweep_v3_allwin/s08_k4_h88_lr0.006_ep800/calibrated_hourly_line_probability.csv` | Calibrated hourly line failure probability matrix. |
| `results/early_warning/metapath_sweep_v3_allwin/s08_k4_h88_lr0.006_ep800/critical_load_risk.csv` | Critical load risk indicators over horizon. |
| `results/early_warning/metapath_sweep_v3_allwin/s08_k4_h88_lr0.006_ep800/line_risk_prediction.csv` | Predicted line-level risk probabilities and labels. |
| `results/early_warning/metapath_sweep_v3_allwin/s08_k4_h88_lr0.006_ep800/metapath_attention_summary.csv` | MetaPath semantic attention summary statistics. |
| `results/early_warning/metapath_sweep_v3_allwin/s08_k4_h88_lr0.006_ep800/model_comparison.csv` | Model comparison metrics (baseline vs variants). |
| `results/early_warning/metapath_sweep_v3_allwin/s08_k4_h88_lr0.006_ep800/nk_failure_risk.csv` | N-k style system-level failure risk indicators. |
| `results/early_warning/metapath_sweep_v3_allwin/s08_k4_h88_lr0.006_ep800/warning_report.json` | Stage6 warning model report with performance metrics. |
| `results/early_warning/metapath_sweep_v3_allwin/s09_k4_h96_lr0.006_ep800/baseline_calibrated_hourly_line_probability.csv` | Baseline calibrated hourly line probabilities. |
| `results/early_warning/metapath_sweep_v3_allwin/s09_k4_h96_lr0.006_ep800/baseline_line_risk_prediction.csv` | Baseline model line risk predictions. |
| `results/early_warning/metapath_sweep_v3_allwin/s09_k4_h96_lr0.006_ep800/calibrated_hourly_line_probability.csv` | Calibrated hourly line failure probability matrix. |
| `results/early_warning/metapath_sweep_v3_allwin/s09_k4_h96_lr0.006_ep800/critical_load_risk.csv` | Critical load risk indicators over horizon. |
| `results/early_warning/metapath_sweep_v3_allwin/s09_k4_h96_lr0.006_ep800/line_risk_prediction.csv` | Predicted line-level risk probabilities and labels. |
| `results/early_warning/metapath_sweep_v3_allwin/s09_k4_h96_lr0.006_ep800/metapath_attention_summary.csv` | MetaPath semantic attention summary statistics. |
| `results/early_warning/metapath_sweep_v3_allwin/s09_k4_h96_lr0.006_ep800/model_comparison.csv` | Model comparison metrics (baseline vs variants). |
| `results/early_warning/metapath_sweep_v3_allwin/s09_k4_h96_lr0.006_ep800/nk_failure_risk.csv` | N-k style system-level failure risk indicators. |
| `results/early_warning/metapath_sweep_v3_allwin/s09_k4_h96_lr0.006_ep800/warning_report.json` | Stage6 warning model report with performance metrics. |
| `results/early_warning/metapath_sweep_v3_allwin/s10_k3_h96_lr0.005_ep900/baseline_calibrated_hourly_line_probability.csv` | Baseline calibrated hourly line probabilities. |
| `results/early_warning/metapath_sweep_v3_allwin/s10_k3_h96_lr0.005_ep900/baseline_line_risk_prediction.csv` | Baseline model line risk predictions. |
| `results/early_warning/metapath_sweep_v3_allwin/s10_k3_h96_lr0.005_ep900/calibrated_hourly_line_probability.csv` | Calibrated hourly line failure probability matrix. |
| `results/early_warning/metapath_sweep_v3_allwin/s10_k3_h96_lr0.005_ep900/critical_load_risk.csv` | Critical load risk indicators over horizon. |
| `results/early_warning/metapath_sweep_v3_allwin/s10_k3_h96_lr0.005_ep900/line_risk_prediction.csv` | Predicted line-level risk probabilities and labels. |
| `results/early_warning/metapath_sweep_v3_allwin/s10_k3_h96_lr0.005_ep900/metapath_attention_summary.csv` | MetaPath semantic attention summary statistics. |
| `results/early_warning/metapath_sweep_v3_allwin/s10_k3_h96_lr0.005_ep900/model_comparison.csv` | Model comparison metrics (baseline vs variants). |
| `results/early_warning/metapath_sweep_v3_allwin/s10_k3_h96_lr0.005_ep900/nk_failure_risk.csv` | N-k style system-level failure risk indicators. |
| `results/early_warning/metapath_sweep_v3_allwin/s10_k3_h96_lr0.005_ep900/warning_report.json` | Stage6 warning model report with performance metrics. |
| `results/early_warning/metapath_sweep_v3_allwin/s11_k4_h64_lr0.007_ep700/baseline_calibrated_hourly_line_probability.csv` | Baseline calibrated hourly line probabilities. |
| `results/early_warning/metapath_sweep_v3_allwin/s11_k4_h64_lr0.007_ep700/baseline_line_risk_prediction.csv` | Baseline model line risk predictions. |
| `results/early_warning/metapath_sweep_v3_allwin/s11_k4_h64_lr0.007_ep700/calibrated_hourly_line_probability.csv` | Calibrated hourly line failure probability matrix. |
| `results/early_warning/metapath_sweep_v3_allwin/s11_k4_h64_lr0.007_ep700/critical_load_risk.csv` | Critical load risk indicators over horizon. |
| `results/early_warning/metapath_sweep_v3_allwin/s11_k4_h64_lr0.007_ep700/line_risk_prediction.csv` | Predicted line-level risk probabilities and labels. |
| `results/early_warning/metapath_sweep_v3_allwin/s11_k4_h64_lr0.007_ep700/metapath_attention_summary.csv` | MetaPath semantic attention summary statistics. |
| `results/early_warning/metapath_sweep_v3_allwin/s11_k4_h64_lr0.007_ep700/model_comparison.csv` | Model comparison metrics (baseline vs variants). |
| `results/early_warning/metapath_sweep_v3_allwin/s11_k4_h64_lr0.007_ep700/nk_failure_risk.csv` | N-k style system-level failure risk indicators. |
| `results/early_warning/metapath_sweep_v3_allwin/s11_k4_h64_lr0.007_ep700/warning_report.json` | Stage6 warning model report with performance metrics. |
| `results/early_warning/metapath_sweep_v3_allwin/s12_k4_h112_lr0.0045_ep1000/calibrated_hourly_line_probability.csv` | Calibrated hourly line failure probability matrix. |
| `results/early_warning/metapath_sweep_v3_allwin/s12_k4_h112_lr0.0045_ep1000/critical_load_risk.csv` | Critical load risk indicators over horizon. |
| `results/early_warning/metapath_sweep_v3_allwin/s12_k4_h112_lr0.0045_ep1000/line_risk_prediction.csv` | Predicted line-level risk probabilities and labels. |
| `results/early_warning/metapath_sweep_v3_allwin/s12_k4_h112_lr0.0045_ep1000/nk_failure_risk.csv` | N-k style system-level failure risk indicators. |
| `results/early_warning/metapath_sweep_v3_allwin/sweep_report.json` | JSON object; top keys: summary_csv, allwin_count, allwin, best_by_val_delta, best_by_mse_delta. |
| `results/early_warning/metapath_sweep_v3_allwin/sweep_summary.csv` | CSV table; columns: baseline_best_val_mse, baseline_horizon_mae, baseline_val_mae, delta_best_val_mse, delta_horizon_mae, delta_val_mae, metapath_best_val_mse, metapath_horizon_mae, .... |
| `results/end_to_end_resilience_summary.json` | Consolidated summary for end-to-end resilience workflow. |
| `results/formal2024_full_baseline_20260310_233109_standard.zip` | Archive file (packaged output or dependency bundle). |
| `results/formal2024_full_baseline_20260310_233109_standard/dispatch/generation_schedule.csv` | Generation schedule output table. |
| `results/formal2024_full_baseline_20260310_233109_standard/dispatch/line_flow.csv` | Line flow results from dispatch optimization. |
| `results/formal2024_full_baseline_20260310_233109_standard/dispatch/load_shedding.csv` | Load shedding output table. |
| `results/formal2024_full_baseline_20260310_233109_standard/dispatch/reserve_schedule.csv` | Reserve allocation schedule output table. |
| `results/formal2024_full_baseline_20260310_233109_standard/resilience/resilience_metrics.csv` | CSV table; columns: policy, Priority, Robustness, Rapidity, Sustainability. |
| `results/formal2024_full_baseline_20260310_233109_standard/resilience/topsis_ranking.csv` | CSV table; columns: policy, score, rank. |
| `results/formal2024_full_baseline_20260310_233109_standard/scenario/component_failure_prob.csv` | CSV table; columns: line, hour, failure_prob. |
| `results/formal2024_full_baseline_20260310_233109_standard/scenario/contingency_scenarios.csv` | Generated contingency scenarios summary table. |
| `results/formal2024_full_baseline_20260310_233109_standard/scenario/wind_solar_scenarios.csv` | CSV table; columns: timestamp, wind_s0, wind_s1, wind_s2, wind_s3, wind_s4, wind_s5, wind_s6, .... |
| `results/formal2024_full_baseline_20260310_233109_standard/summary/experiment_summary.json` | JSON object; top keys: framework, mode, run_root, timestamp, selected_chain, best_candidate, standard_outputs. |
| `results/formal2024_full_baseline_20260310_233109_standard/summary/indicator_table.csv` | Indicator matrix for resilience evaluation. |
| `results/formal2024_full_baseline_20260310_233109_standard/warning/critical_load_risk.csv` | Critical load risk indicators over horizon. |
| `results/formal2024_full_baseline_20260310_233109_standard/warning/line_risk_prediction.csv` | Predicted line-level risk probabilities and labels. |
| `results/formal2024_full_baseline_20260310_233109_standard/warning/nk_failure_risk.csv` | N-k style system-level failure risk indicators. |
| `results/formal2024_quick_std_standard/dispatch/generation_schedule.csv` | Generation schedule output table. |
| `results/formal2024_quick_std_standard/dispatch/line_flow.csv` | Line flow results from dispatch optimization. |
| `results/formal2024_quick_std_standard/dispatch/load_shedding.csv` | Load shedding output table. |
| `results/formal2024_quick_std_standard/dispatch/reserve_schedule.csv` | Reserve allocation schedule output table. |
| `results/formal2024_quick_std_standard/README.md` | Readme/instructions for the directory. |
| `results/formal2024_quick_std_standard/resilience/resilience_metrics.csv` | CSV table; columns: policy, Priority, Robustness, Rapidity, Sustainability. |
| `results/formal2024_quick_std_standard/resilience/topsis_ranking.csv` | CSV table; columns: policy, score, rank. |
| `results/formal2024_quick_std_standard/scenario/component_failure_prob.csv` | CSV table; columns: line, hour, failure_prob. |
| `results/formal2024_quick_std_standard/scenario/contingency_scenarios.csv` | Generated contingency scenarios summary table. |
| `results/formal2024_quick_std_standard/scenario/wind_solar_scenarios.csv` | CSV table; columns: timestamp, wind_s0, wind_s1, wind_s2, wind_s3, solar_s0, solar_s1, solar_s2, .... |
| `results/formal2024_quick_std_standard/summary/experiment_summary.json` | JSON object; top keys: framework, mode, run_root, timestamp, selected_chain, best_candidate, standard_outputs. |
| `results/formal2024_quick_std_standard/summary/indicator_table.csv` | Indicator matrix for resilience evaluation. |
| `results/formal2024_quick_std_standard/warning/critical_load_risk.csv` | Critical load risk indicators over horizon. |
| `results/formal2024_quick_std_standard/warning/line_risk_prediction.csv` | Predicted line-level risk probabilities and labels. |
| `results/formal2024_quick_std_standard/warning/nk_failure_risk.csv` | N-k style system-level failure risk indicators. |
| `results/gridagent_framework/dispatch_opt_integration_dryrun/framework_report.json` | End-to-end framework run report. |
| `results/gridagent_framework/dispatch_opt_integration_smoke/framework_report.json` | End-to-end framework run report. |
| `results/gridagent_framework/dispatch_opt_integration_smoke/stage1_wind_pv/formal2024/history_series.csv` | Historical time series used as model input. |
| `results/gridagent_framework/dispatch_opt_integration_smoke/stage1_wind_pv/formal2024/sampled_scenarios.npy` | Sampled scenario tensor for simulation input. |
| `results/gridagent_framework/dispatch_opt_integration_smoke/stage1_wind_pv/formal2024/scenario_probabilities.csv` | Probability assigned to each generated scenario. |
| `results/gridagent_framework/dispatch_opt_integration_smoke/stage1_wind_pv/formal2024/typical_scenarios_long.csv` | Long-form scenario table by timestamp and scenario id. |
| `results/gridagent_framework/dispatch_opt_integration_smoke/stage1_wind_pv/formal2024/typical_scenarios.npy` | NumPy tensor of representative scenarios. |
| `results/gridagent_framework/dispatch_opt_integration_smoke/stage1_wind_pv/formal2024/uncertainty_report.json` | Stage1 uncertainty modeling report and metrics. |
| `results/gridagent_framework/dispatch_opt_integration_smoke/stage2_failure/schloemer/failure_probability_report.json` | Stage2 component/line failure probability report. |
| `results/gridagent_framework/dispatch_opt_integration_smoke/stage2_failure/schloemer/line_failure_timeseries_schloemer.csv` | Time-series line failure probabilities under Schloemer model. |
| `results/gridagent_framework/dispatch_opt_integration_smoke/stage3_contingency/schloemer/contingency_report.json` | Stage3 spatiotemporal contingency generation report. |
| `results/gridagent_framework/dispatch_opt_integration_smoke/stage3_contingency/schloemer/contingency_scenarios_c3po_ref.csv` | CSV table; columns: scenario, scenario_id, timestamp, failed_lines, outage_line_count, disconnected_load_count, probability, method. |
| `results/gridagent_framework/dispatch_opt_integration_smoke/stage3_contingency/schloemer/contingency_scenarios.csv` | Generated contingency scenarios summary table. |
| `results/gridagent_framework/dispatch_opt_integration_smoke/stage3_contingency/schloemer/contingency_tensor_c3po_ref.npy` | Contingency state tensor generated by C3PO reference method. |
| `results/gridagent_framework/dispatch_opt_integration_smoke/stage3_contingency/schloemer/line_probability_summary_c3po_ref.csv` | Per-line probability summary for C3PO reference method. |
| `results/gridagent_framework/dispatch_opt_integration_smoke/stage3_contingency/schloemer/method_comparison.csv` | Cross-method comparison metrics table. |
| `results/gridagent_framework/dispatch_opt_integration_smoke/stage3_contingency/schloemer/state_summary_c3po_ref.csv` | State occurrence summary for C3PO reference method. |
| `results/gridagent_framework/dispatch_opt_integration_smoke/stage4_scheduling/schloemer__c3po_ref__rr0p3/load_bus_priority_profile.csv` | Per-load-bus priority/weight profile. |
| `results/gridagent_framework/dispatch_opt_integration_smoke/stage4_scheduling/schloemer__c3po_ref__rr0p3/load_prioritization_report.json` | Stage4 load prioritization and scheduling report. |
| `results/gridagent_framework/dispatch_opt_integration_smoke/stage4_scheduling/schloemer__c3po_ref__rr0p3/policy_comparison.csv` | Policy comparison results for scheduling stage. |
| `results/gridagent_framework/dispatch_opt_integration_smoke/stage4_scheduling/schloemer__c3po_ref__rr0p3/pre_disaster_dispatch_schedule.csv` | Optimized pre-disaster generation dispatch schedule. |
| `results/gridagent_framework/dispatch_opt_integration_smoke/stage4_scheduling/schloemer__c3po_ref__rr0p3/scenario_metrics.csv` | Scenario-level reliability/cost/shedding metrics. |
| `results/gridagent_framework/dispatch_opt_integration_smoke/stage4_scheduling/schloemer__c3po_ref__rr0p3/worst_scenario_shedding_detail.csv` | Detailed shedding actions under worst scenario. |
| `results/gridagent_framework/dispatch_opt_integration_smoke/stage5_assessment/ewm_topsis_result.csv` | Composite ranking result from EWM+TOPSIS. |
| `results/gridagent_framework/dispatch_opt_integration_smoke/stage5_assessment/indicator_table.csv` | Indicator matrix for resilience evaluation. |
| `results/gridagent_framework/dispatch_opt_integration_smoke/stage5_assessment/multi_criteria_report.json` | Stage5 multi-criteria resilience assessment report. |
| `results/gridagent_framework/dispatch_opt_integration_smoke/stage5_assessment/single_indicator_ranking.csv` | Ranking by each single resilience indicator. |
| `results/gridagent_framework/dispatch_opt_integration_smoke/stage6_warning/calibrated_hourly_line_probability.csv` | Calibrated hourly line failure probability matrix. |
| `results/gridagent_framework/dispatch_opt_integration_smoke/stage6_warning/critical_load_risk.csv` | Critical load risk indicators over horizon. |
| `results/gridagent_framework/dispatch_opt_integration_smoke/stage6_warning/line_risk_prediction.csv` | Predicted line-level risk probabilities and labels. |
| `results/gridagent_framework/dispatch_opt_integration_smoke/stage6_warning/nk_failure_risk.csv` | N-k style system-level failure risk indicators. |
| `results/gridagent_framework/dispatch_opt_integration_smoke/stage6_warning/warning_report.json` | Stage6 warning model report with performance metrics. |
| `results/gridagent_framework/dispatch_opt_integration_smoke/stage7_dispatch_optimization/contextual_dispatch_hourly_cost.csv` | Context-aware hourly operational cost trace. |
| `results/gridagent_framework/dispatch_opt_integration_smoke/stage7_dispatch_optimization/contextual_dispatch_load_shedding.csv` | Context-aware load shedding schedule. |
| `results/gridagent_framework/dispatch_opt_integration_smoke/stage7_dispatch_optimization/contextual_dispatch_unit_schedule.csv` | Context-aware dispatch generation schedule. |
| `results/gridagent_framework/dispatch_opt_integration_smoke/stage7_dispatch_optimization/dispatch_active_strategy_summary.csv` | Summary of active dispatch strategy over time. |
| `results/gridagent_framework/dispatch_opt_integration_smoke/stage7_dispatch_optimization/dispatch_ewm_topsis_result.csv` | Dispatch strategy composite ranking from EWM+TOPSIS. |
| `results/gridagent_framework/dispatch_opt_integration_smoke/stage7_dispatch_optimization/dispatch_indicator_weights.csv` | Indicator weights used in dispatch strategy scoring. |
| `results/gridagent_framework/dispatch_opt_integration_smoke/stage7_dispatch_optimization/dispatch_model_comparison.csv` | SCUC/Stochastic/Robust model comparison metrics. |
| `results/gridagent_framework/dispatch_opt_integration_smoke/stage7_dispatch_optimization/dispatch_optimization_report.json` | Stage7 dispatch optimization report. |
| `results/gridagent_framework/dispatch_opt_integration_smoke/stage7_dispatch_optimization/dispatch_strategy_selection.csv` | Risk-context strategy switching record by time step. |
| `results/gridagent_framework/dispatch_opt_integration_smoke/stage7_dispatch_optimization/line_flow.csv` | Line flow results from dispatch optimization. |
| `results/gridagent_framework/dispatch_opt_integration_smoke/stage7_dispatch_optimization/robust_uc_first_stage_schedule.csv` | Robust UC first-stage schedule output. |
| `results/gridagent_framework/dispatch_opt_integration_smoke/stage7_dispatch_optimization/robust_uc_scenario_summary.csv` | Robust UC scenario summary metrics. |
| `results/gridagent_framework/dispatch_opt_integration_smoke/stage7_dispatch_optimization/robust_uc_worst_load_shedding.csv` | Worst-case load shedding under robust UC. |
| `results/gridagent_framework/dispatch_opt_integration_smoke/stage7_dispatch_optimization/scuc_load_shedding.csv` | SCUC load shedding output table. |
| `results/gridagent_framework/dispatch_opt_integration_smoke/stage7_dispatch_optimization/scuc_schedule.csv` | SCUC schedule output table. |
| `results/gridagent_framework/dispatch_opt_integration_smoke/stage7_dispatch_optimization/stochastic_uc_expected_load_shedding.csv` | Expected load shedding under stochastic UC. |
| `results/gridagent_framework/dispatch_opt_integration_smoke/stage7_dispatch_optimization/stochastic_uc_first_stage_schedule.csv` | Stochastic UC first-stage schedule output. |
| `results/gridagent_framework/dispatch_opt_integration_smoke/stage7_dispatch_optimization/stochastic_uc_scenario_summary.csv` | Stochastic UC scenario summary metrics. |
| `results/gridagent_framework/formal2024_full_baseline_20260310_233109/framework_report.json` | End-to-end framework run report. |
| `results/gridagent_framework/formal2024_full_baseline_20260310_233109/stage1_wind_pv/formal2024/history_series.csv` | Historical time series used as model input. |
| `results/gridagent_framework/formal2024_full_baseline_20260310_233109/stage1_wind_pv/formal2024/sampled_scenarios.npy` | Sampled scenario tensor for simulation input. |
| `results/gridagent_framework/formal2024_full_baseline_20260310_233109/stage1_wind_pv/formal2024/scenario_probabilities.csv` | Probability assigned to each generated scenario. |
| `results/gridagent_framework/formal2024_full_baseline_20260310_233109/stage1_wind_pv/formal2024/typical_scenarios_long.csv` | Long-form scenario table by timestamp and scenario id. |
| `results/gridagent_framework/formal2024_full_baseline_20260310_233109/stage1_wind_pv/formal2024/typical_scenarios.npy` | NumPy tensor of representative scenarios. |
| `results/gridagent_framework/formal2024_full_baseline_20260310_233109/stage1_wind_pv/formal2024/uncertainty_report.json` | Stage1 uncertainty modeling report and metrics. |
| `results/gridagent_framework/formal2024_full_baseline_20260310_233109/stage2_failure/schloemer/failure_probability_report.json` | Stage2 component/line failure probability report. |
| `results/gridagent_framework/formal2024_full_baseline_20260310_233109/stage2_failure/schloemer/line_failure_timeseries_schloemer.csv` | Time-series line failure probabilities under Schloemer model. |
| `results/gridagent_framework/formal2024_full_baseline_20260310_233109/stage3_contingency/schloemer/contingency_report.json` | Stage3 spatiotemporal contingency generation report. |
| `results/gridagent_framework/formal2024_full_baseline_20260310_233109/stage3_contingency/schloemer/contingency_scenarios_c3po_ref.csv` | CSV table; columns: scenario, scenario_id, timestamp, failed_lines, outage_line_count, disconnected_load_count, probability, method. |
| `results/gridagent_framework/formal2024_full_baseline_20260310_233109/stage3_contingency/schloemer/contingency_scenarios.csv` | Generated contingency scenarios summary table. |
| `results/gridagent_framework/formal2024_full_baseline_20260310_233109/stage3_contingency/schloemer/contingency_tensor_c3po_ref.npy` | Contingency state tensor generated by C3PO reference method. |
| `results/gridagent_framework/formal2024_full_baseline_20260310_233109/stage3_contingency/schloemer/line_probability_summary_c3po_ref.csv` | Per-line probability summary for C3PO reference method. |
| `results/gridagent_framework/formal2024_full_baseline_20260310_233109/stage3_contingency/schloemer/method_comparison.csv` | Cross-method comparison metrics table. |
| `results/gridagent_framework/formal2024_full_baseline_20260310_233109/stage3_contingency/schloemer/state_summary_c3po_ref.csv` | State occurrence summary for C3PO reference method. |
| `results/gridagent_framework/formal2024_full_baseline_20260310_233109/stage4_scheduling/schloemer__c3po_ref__rr0p3/load_bus_priority_profile.csv` | Per-load-bus priority/weight profile. |
| `results/gridagent_framework/formal2024_full_baseline_20260310_233109/stage4_scheduling/schloemer__c3po_ref__rr0p3/load_prioritization_report.json` | Stage4 load prioritization and scheduling report. |
| `results/gridagent_framework/formal2024_full_baseline_20260310_233109/stage4_scheduling/schloemer__c3po_ref__rr0p3/policy_comparison.csv` | Policy comparison results for scheduling stage. |
| `results/gridagent_framework/formal2024_full_baseline_20260310_233109/stage4_scheduling/schloemer__c3po_ref__rr0p3/pre_disaster_dispatch_schedule.csv` | Optimized pre-disaster generation dispatch schedule. |
| `results/gridagent_framework/formal2024_full_baseline_20260310_233109/stage4_scheduling/schloemer__c3po_ref__rr0p3/scenario_metrics.csv` | Scenario-level reliability/cost/shedding metrics. |
| `results/gridagent_framework/formal2024_full_baseline_20260310_233109/stage4_scheduling/schloemer__c3po_ref__rr0p3/worst_scenario_shedding_detail.csv` | Detailed shedding actions under worst scenario. |
| `results/gridagent_framework/formal2024_full_baseline_20260310_233109/stage5_assessment/ewm_topsis_result.csv` | Composite ranking result from EWM+TOPSIS. |
| `results/gridagent_framework/formal2024_full_baseline_20260310_233109/stage5_assessment/indicator_table.csv` | Indicator matrix for resilience evaluation. |
| `results/gridagent_framework/formal2024_full_baseline_20260310_233109/stage5_assessment/multi_criteria_report.json` | Stage5 multi-criteria resilience assessment report. |
| `results/gridagent_framework/formal2024_full_baseline_20260310_233109/stage5_assessment/single_indicator_ranking.csv` | Ranking by each single resilience indicator. |
| `results/gridagent_framework/formal2024_full_baseline_20260310_233109/stage6_warning/calibrated_hourly_line_probability.csv` | Calibrated hourly line failure probability matrix. |
| `results/gridagent_framework/formal2024_full_baseline_20260310_233109/stage6_warning/critical_load_risk.csv` | Critical load risk indicators over horizon. |
| `results/gridagent_framework/formal2024_full_baseline_20260310_233109/stage6_warning/line_risk_prediction.csv` | Predicted line-level risk probabilities and labels. |
| `results/gridagent_framework/formal2024_full_baseline_20260310_233109/stage6_warning/nk_failure_risk.csv` | N-k style system-level failure risk indicators. |
| `results/gridagent_framework/formal2024_full_baseline_20260310_233109/stage6_warning/warning_report.json` | Stage6 warning model report with performance metrics. |
| `results/gridagent_framework/formal2024_full_baseline_20260310_233109/stage7_dispatch_optimization/contextual_dispatch_hourly_cost.csv` | Context-aware hourly operational cost trace. |
| `results/gridagent_framework/formal2024_full_baseline_20260310_233109/stage7_dispatch_optimization/contextual_dispatch_load_shedding.csv` | Context-aware load shedding schedule. |
| `results/gridagent_framework/formal2024_full_baseline_20260310_233109/stage7_dispatch_optimization/contextual_dispatch_unit_schedule.csv` | Context-aware dispatch generation schedule. |
| `results/gridagent_framework/formal2024_full_baseline_20260310_233109/stage7_dispatch_optimization/dispatch_active_strategy_summary.csv` | Summary of active dispatch strategy over time. |
| `results/gridagent_framework/formal2024_full_baseline_20260310_233109/stage7_dispatch_optimization/dispatch_indicator_weights.csv` | Indicator weights used in dispatch strategy scoring. |
| `results/gridagent_framework/formal2024_full_baseline_20260310_233109/stage7_dispatch_optimization/dispatch_optimization_report.json` | Stage7 dispatch optimization report. |
| `results/gridagent_framework/formal2024_full_baseline_20260310_233109/stage7_dispatch_optimization/dispatch_strategy_selection.csv` | Risk-context strategy switching record by time step. |
| `results/gridagent_framework/formal2024_full_baseline_20260310_233109/stage7_dispatch_optimization/line_flow.csv` | Line flow results from dispatch optimization. |
| `results/gridagent_framework/formal2024_full_baseline_20260310_233109/stage7_dispatch_optimization/robust_uc_first_stage_schedule.csv` | Robust UC first-stage schedule output. |
| `results/gridagent_framework/formal2024_full_baseline_20260310_233109/stage7_dispatch_optimization/robust_uc_scenario_summary.csv` | Robust UC scenario summary metrics. |
| `results/gridagent_framework/formal2024_full_baseline_20260310_233109/stage7_dispatch_optimization/robust_uc_worst_load_shedding.csv` | Worst-case load shedding under robust UC. |
| `results/gridagent_framework/formal2024_full_baseline_20260310_233109/stage7_dispatch_optimization/scuc_load_shedding.csv` | SCUC load shedding output table. |
| `results/gridagent_framework/formal2024_full_baseline_20260310_233109/stage7_dispatch_optimization/scuc_schedule.csv` | SCUC schedule output table. |
| `results/gridagent_framework/formal2024_full_baseline_20260310_233109/stage7_dispatch_optimization/stochastic_uc_expected_load_shedding.csv` | Expected load shedding under stochastic UC. |
| `results/gridagent_framework/formal2024_full_baseline_20260310_233109/stage7_dispatch_optimization/stochastic_uc_first_stage_schedule.csv` | Stochastic UC first-stage schedule output. |
| `results/gridagent_framework/formal2024_full_baseline_20260310_233109/stage7_dispatch_optimization/stochastic_uc_scenario_summary.csv` | Stochastic UC scenario summary metrics. |
| `results/gridagent_framework/formal2024_quick_std/framework_report.json` | End-to-end framework run report. |
| `results/gridagent_framework/formal2024_quick_std/stage1_wind_pv/formal2024/history_series.csv` | Historical time series used as model input. |
| `results/gridagent_framework/formal2024_quick_std/stage1_wind_pv/formal2024/sampled_scenarios.npy` | Sampled scenario tensor for simulation input. |
| `results/gridagent_framework/formal2024_quick_std/stage1_wind_pv/formal2024/scenario_probabilities.csv` | Probability assigned to each generated scenario. |
| `results/gridagent_framework/formal2024_quick_std/stage1_wind_pv/formal2024/typical_scenarios_long.csv` | Long-form scenario table by timestamp and scenario id. |
| `results/gridagent_framework/formal2024_quick_std/stage1_wind_pv/formal2024/typical_scenarios.npy` | NumPy tensor of representative scenarios. |
| `results/gridagent_framework/formal2024_quick_std/stage1_wind_pv/formal2024/uncertainty_report.json` | Stage1 uncertainty modeling report and metrics. |
| `results/gridagent_framework/formal2024_quick_std/stage2_failure/schloemer/failure_probability_report.json` | Stage2 component/line failure probability report. |
| `results/gridagent_framework/formal2024_quick_std/stage2_failure/schloemer/line_failure_timeseries_schloemer.csv` | Time-series line failure probabilities under Schloemer model. |
| `results/gridagent_framework/formal2024_quick_std/stage3_contingency/schloemer/contingency_report.json` | Stage3 spatiotemporal contingency generation report. |
| `results/gridagent_framework/formal2024_quick_std/stage3_contingency/schloemer/contingency_scenarios_c3po_ref.csv` | CSV table; columns: scenario, scenario_id, timestamp, failed_lines, outage_line_count, disconnected_load_count, probability, method. |
| `results/gridagent_framework/formal2024_quick_std/stage3_contingency/schloemer/contingency_scenarios.csv` | Generated contingency scenarios summary table. |
| `results/gridagent_framework/formal2024_quick_std/stage3_contingency/schloemer/contingency_tensor_c3po_ref.npy` | Contingency state tensor generated by C3PO reference method. |
| `results/gridagent_framework/formal2024_quick_std/stage3_contingency/schloemer/line_probability_summary_c3po_ref.csv` | Per-line probability summary for C3PO reference method. |
| `results/gridagent_framework/formal2024_quick_std/stage3_contingency/schloemer/method_comparison.csv` | Cross-method comparison metrics table. |
| `results/gridagent_framework/formal2024_quick_std/stage3_contingency/schloemer/state_summary_c3po_ref.csv` | State occurrence summary for C3PO reference method. |
| `results/gridagent_framework/formal2024_quick_std/stage4_scheduling/schloemer__c3po_ref__rr0p3/load_bus_priority_profile.csv` | Per-load-bus priority/weight profile. |
| `results/gridagent_framework/formal2024_quick_std/stage4_scheduling/schloemer__c3po_ref__rr0p3/load_prioritization_report.json` | Stage4 load prioritization and scheduling report. |
| `results/gridagent_framework/formal2024_quick_std/stage4_scheduling/schloemer__c3po_ref__rr0p3/policy_comparison.csv` | Policy comparison results for scheduling stage. |
| `results/gridagent_framework/formal2024_quick_std/stage4_scheduling/schloemer__c3po_ref__rr0p3/pre_disaster_dispatch_schedule.csv` | Optimized pre-disaster generation dispatch schedule. |
| `results/gridagent_framework/formal2024_quick_std/stage4_scheduling/schloemer__c3po_ref__rr0p3/scenario_metrics.csv` | Scenario-level reliability/cost/shedding metrics. |
| `results/gridagent_framework/formal2024_quick_std/stage4_scheduling/schloemer__c3po_ref__rr0p3/worst_scenario_shedding_detail.csv` | Detailed shedding actions under worst scenario. |
| `results/gridagent_framework/formal2024_quick_std/stage5_assessment/ewm_topsis_result.csv` | Composite ranking result from EWM+TOPSIS. |
| `results/gridagent_framework/formal2024_quick_std/stage5_assessment/indicator_table.csv` | Indicator matrix for resilience evaluation. |
| `results/gridagent_framework/formal2024_quick_std/stage5_assessment/multi_criteria_report.json` | Stage5 multi-criteria resilience assessment report. |
| `results/gridagent_framework/formal2024_quick_std/stage5_assessment/single_indicator_ranking.csv` | Ranking by each single resilience indicator. |
| `results/gridagent_framework/formal2024_quick_std/stage6_warning/calibrated_hourly_line_probability.csv` | Calibrated hourly line failure probability matrix. |
| `results/gridagent_framework/formal2024_quick_std/stage6_warning/critical_load_risk.csv` | Critical load risk indicators over horizon. |
| `results/gridagent_framework/formal2024_quick_std/stage6_warning/line_risk_prediction.csv` | Predicted line-level risk probabilities and labels. |
| `results/gridagent_framework/formal2024_quick_std/stage6_warning/nk_failure_risk.csv` | N-k style system-level failure risk indicators. |
| `results/gridagent_framework/formal2024_quick_std/stage6_warning/warning_report.json` | Stage6 warning model report with performance metrics. |
| `results/gridagent_framework/formal2024_quick_std/stage7_dispatch_optimization/contextual_dispatch_hourly_cost.csv` | Context-aware hourly operational cost trace. |
| `results/gridagent_framework/formal2024_quick_std/stage7_dispatch_optimization/contextual_dispatch_load_shedding.csv` | Context-aware load shedding schedule. |
| `results/gridagent_framework/formal2024_quick_std/stage7_dispatch_optimization/contextual_dispatch_unit_schedule.csv` | Context-aware dispatch generation schedule. |
| `results/gridagent_framework/formal2024_quick_std/stage7_dispatch_optimization/dispatch_active_strategy_summary.csv` | Summary of active dispatch strategy over time. |
| `results/gridagent_framework/formal2024_quick_std/stage7_dispatch_optimization/dispatch_indicator_weights.csv` | Indicator weights used in dispatch strategy scoring. |
| `results/gridagent_framework/formal2024_quick_std/stage7_dispatch_optimization/dispatch_optimization_report.json` | Stage7 dispatch optimization report. |
| `results/gridagent_framework/formal2024_quick_std/stage7_dispatch_optimization/dispatch_strategy_selection.csv` | Risk-context strategy switching record by time step. |
| `results/gridagent_framework/formal2024_quick_std/stage7_dispatch_optimization/line_flow.csv` | Line flow results from dispatch optimization. |
| `results/gridagent_framework/formal2024_quick_std/stage7_dispatch_optimization/robust_uc_first_stage_schedule.csv` | Robust UC first-stage schedule output. |
| `results/gridagent_framework/formal2024_quick_std/stage7_dispatch_optimization/robust_uc_scenario_summary.csv` | Robust UC scenario summary metrics. |
| `results/gridagent_framework/formal2024_quick_std/stage7_dispatch_optimization/robust_uc_worst_load_shedding.csv` | Worst-case load shedding under robust UC. |
| `results/gridagent_framework/formal2024_quick_std/stage7_dispatch_optimization/scuc_load_shedding.csv` | SCUC load shedding output table. |
| `results/gridagent_framework/formal2024_quick_std/stage7_dispatch_optimization/scuc_schedule.csv` | SCUC schedule output table. |
| `results/gridagent_framework/formal2024_quick_std/stage7_dispatch_optimization/stochastic_uc_expected_load_shedding.csv` | Expected load shedding under stochastic UC. |
| `results/gridagent_framework/formal2024_quick_std/stage7_dispatch_optimization/stochastic_uc_first_stage_schedule.csv` | Stochastic UC first-stage schedule output. |
| `results/gridagent_framework/formal2024_quick_std/stage7_dispatch_optimization/stochastic_uc_scenario_summary.csv` | Stochastic UC scenario summary metrics. |
| `results/gridagent_framework/ieee118_n60_opt124_dryrun/framework_report.json` | End-to-end framework run report. |
| `results/gridagent_framework/ieee118_n60_stagewise_20260324_195044/run_tag.txt` | Run tag marker for experiment identification. |
| `results/gridagent_framework/ieee118_n60_stagewise_20260324_195044/stage1_wind_pv/formal2024/history_series.csv` | Historical time series used as model input. |
| `results/gridagent_framework/ieee118_n60_stagewise_20260324_195044/stage1_wind_pv/formal2024/sampled_scenarios.npy` | Sampled scenario tensor for simulation input. |
| `results/gridagent_framework/ieee118_n60_stagewise_20260324_195044/stage1_wind_pv/formal2024/scenario_probabilities.csv` | Probability assigned to each generated scenario. |
| `results/gridagent_framework/ieee118_n60_stagewise_20260324_195044/stage1_wind_pv/formal2024/typical_scenarios_long.csv` | Long-form scenario table by timestamp and scenario id. |
| `results/gridagent_framework/ieee118_n60_stagewise_20260324_195044/stage1_wind_pv/formal2024/typical_scenarios.npy` | NumPy tensor of representative scenarios. |
| `results/gridagent_framework/ieee118_n60_stagewise_20260324_195044/stage1_wind_pv/formal2024/uncertainty_report.json` | Stage1 uncertainty modeling report and metrics. |
| `results/gridagent_framework/ieee118_n60_stagewise_20260324_195044/stage2_failure/schloemer/failure_probability_report.json` | Stage2 component/line failure probability report. |
| `results/gridagent_framework/ieee118_n60_stagewise_20260324_195044/stage2_failure/schloemer/line_failure_timeseries_schloemer.csv` | Time-series line failure probabilities under Schloemer model. |
| `results/gridagent_framework/ieee118_n60_stagewise_20260324_195044/stage3_contingency/schloemer/contingency_report.json` | Stage3 spatiotemporal contingency generation report. |
| `results/gridagent_framework/ieee118_n60_stagewise_20260324_195044/stage3_contingency/schloemer/contingency_scenarios_c3po_ref.csv` | CSV table; columns: scenario, scenario_id, timestamp, failed_lines, outage_line_count, disconnected_load_count, probability, method. |
| `results/gridagent_framework/ieee118_n60_stagewise_20260324_195044/stage3_contingency/schloemer/contingency_scenarios.csv` | Generated contingency scenarios summary table. |
| `results/gridagent_framework/ieee118_n60_stagewise_20260324_195044/stage3_contingency/schloemer/contingency_tensor_c3po_ref.npy` | Contingency state tensor generated by C3PO reference method. |
| `results/gridagent_framework/ieee118_n60_stagewise_20260324_195044/stage3_contingency/schloemer/line_probability_summary_c3po_ref.csv` | Per-line probability summary for C3PO reference method. |
| `results/gridagent_framework/ieee118_n60_stagewise_20260324_195044/stage3_contingency/schloemer/method_comparison.csv` | Cross-method comparison metrics table. |
| `results/gridagent_framework/ieee118_n60_stagewise_20260324_195044/stage3_contingency/schloemer/state_summary_c3po_ref.csv` | State occurrence summary for C3PO reference method. |
| `results/gridagent_framework/ieee118_n60_stagewise_20260324_195044/stage4_scheduling/schloemer__c3po_ref__rr0p30/load_bus_priority_profile.csv` | Per-load-bus priority/weight profile. |
| `results/gridagent_framework/ieee118_n60_stagewise_20260324_195044/stage4_scheduling/schloemer__c3po_ref__rr0p30/load_prioritization_report.json` | Stage4 load prioritization and scheduling report. |
| `results/gridagent_framework/ieee118_n60_stagewise_20260324_195044/stage4_scheduling/schloemer__c3po_ref__rr0p30/policy_comparison.csv` | Policy comparison results for scheduling stage. |
| `results/gridagent_framework/ieee118_n60_stagewise_20260324_195044/stage4_scheduling/schloemer__c3po_ref__rr0p30/pre_disaster_dispatch_schedule.csv` | Optimized pre-disaster generation dispatch schedule. |
| `results/gridagent_framework/ieee118_n60_stagewise_20260324_195044/stage4_scheduling/schloemer__c3po_ref__rr0p30/scenario_metrics.csv` | Scenario-level reliability/cost/shedding metrics. |
| `results/gridagent_framework/ieee118_n60_stagewise_20260324_195044/stage4_scheduling/schloemer__c3po_ref__rr0p30/worst_scenario_shedding_detail.csv` | Detailed shedding actions under worst scenario. |
| `results/gridagent_framework/ieee118_n60_stagewise_20260324_195044/stage5_assessment/ewm_topsis_result.csv` | Composite ranking result from EWM+TOPSIS. |
| `results/gridagent_framework/ieee118_n60_stagewise_20260324_195044/stage5_assessment/indicator_table.csv` | Indicator matrix for resilience evaluation. |
| `results/gridagent_framework/ieee118_n60_stagewise_20260324_195044/stage5_assessment/multi_criteria_report.json` | Stage5 multi-criteria resilience assessment report. |
| `results/gridagent_framework/ieee118_n60_stagewise_20260324_195044/stage5_assessment/single_indicator_ranking.csv` | Ranking by each single resilience indicator. |
| `results/gridagent_framework/ieee118_n60_stagewise_20260324_195044/stage6_warning_before_lambda0005_20260325_002847/baseline_calibrated_hourly_line_probability.csv` | Baseline calibrated hourly line probabilities. |
| `results/gridagent_framework/ieee118_n60_stagewise_20260324_195044/stage6_warning_before_lambda0005_20260325_002847/baseline_line_risk_prediction.csv` | Baseline model line risk predictions. |
| `results/gridagent_framework/ieee118_n60_stagewise_20260324_195044/stage6_warning_before_lambda0005_20260325_002847/calibrated_hourly_line_probability.csv` | Calibrated hourly line failure probability matrix. |
| `results/gridagent_framework/ieee118_n60_stagewise_20260324_195044/stage6_warning_before_lambda0005_20260325_002847/critical_load_risk.csv` | Critical load risk indicators over horizon. |
| `results/gridagent_framework/ieee118_n60_stagewise_20260324_195044/stage6_warning_before_lambda0005_20260325_002847/line_risk_prediction.csv` | Predicted line-level risk probabilities and labels. |
| `results/gridagent_framework/ieee118_n60_stagewise_20260324_195044/stage6_warning_before_lambda0005_20260325_002847/metapath_attention_summary.csv` | MetaPath semantic attention summary statistics. |
| `results/gridagent_framework/ieee118_n60_stagewise_20260324_195044/stage6_warning_before_lambda0005_20260325_002847/model_comparison.csv` | Model comparison metrics (baseline vs variants). |
| `results/gridagent_framework/ieee118_n60_stagewise_20260324_195044/stage6_warning_before_lambda0005_20260325_002847/nk_failure_risk.csv` | N-k style system-level failure risk indicators. |
| `results/gridagent_framework/ieee118_n60_stagewise_20260324_195044/stage6_warning_before_lambda0005_20260325_002847/node_weather_horizon.csv` | Forecast horizon weather features per node. |
| `results/gridagent_framework/ieee118_n60_stagewise_20260324_195044/stage6_warning_before_lambda0005_20260325_002847/node_weather_summary.csv` | Aggregated node weather statistics. |
| `results/gridagent_framework/ieee118_n60_stagewise_20260324_195044/stage6_warning_before_lambda0005_20260325_002847/node_weather_timeseries.csv` | Node-level weather time series used by warning stage. |
| `results/gridagent_framework/ieee118_n60_stagewise_20260324_195044/stage6_warning_before_lambda0005_20260325_002847/warning_report.json` | Stage6 warning model report with performance metrics. |
| `results/gridagent_framework/ieee118_n60_stagewise_20260324_195044/stage6_warning_before_opt124_20260324_233556/baseline_calibrated_hourly_line_probability.csv` | Baseline calibrated hourly line probabilities. |
| `results/gridagent_framework/ieee118_n60_stagewise_20260324_195044/stage6_warning_before_opt124_20260324_233556/baseline_line_risk_prediction.csv` | Baseline model line risk predictions. |
| `results/gridagent_framework/ieee118_n60_stagewise_20260324_195044/stage6_warning_before_opt124_20260324_233556/calibrated_hourly_line_probability.csv` | Calibrated hourly line failure probability matrix. |
| `results/gridagent_framework/ieee118_n60_stagewise_20260324_195044/stage6_warning_before_opt124_20260324_233556/critical_load_risk.csv` | Critical load risk indicators over horizon. |
| `results/gridagent_framework/ieee118_n60_stagewise_20260324_195044/stage6_warning_before_opt124_20260324_233556/line_risk_prediction.csv` | Predicted line-level risk probabilities and labels. |
| `results/gridagent_framework/ieee118_n60_stagewise_20260324_195044/stage6_warning_before_opt124_20260324_233556/metapath_attention_summary.csv` | MetaPath semantic attention summary statistics. |
| `results/gridagent_framework/ieee118_n60_stagewise_20260324_195044/stage6_warning_before_opt124_20260324_233556/model_comparison.csv` | Model comparison metrics (baseline vs variants). |
| `results/gridagent_framework/ieee118_n60_stagewise_20260324_195044/stage6_warning_before_opt124_20260324_233556/nk_failure_risk.csv` | N-k style system-level failure risk indicators. |
| `results/gridagent_framework/ieee118_n60_stagewise_20260324_195044/stage6_warning_before_opt124_20260324_233556/node_weather_horizon.csv` | Forecast horizon weather features per node. |
| `results/gridagent_framework/ieee118_n60_stagewise_20260324_195044/stage6_warning_before_opt124_20260324_233556/node_weather_summary.csv` | Aggregated node weather statistics. |
| `results/gridagent_framework/ieee118_n60_stagewise_20260324_195044/stage6_warning_before_opt124_20260324_233556/node_weather_timeseries.csv` | Node-level weather time series used by warning stage. |
| `results/gridagent_framework/ieee118_n60_stagewise_20260324_195044/stage6_warning_before_opt124_20260324_233556/warning_report.json` | Stage6 warning model report with performance metrics. |
| `results/gridagent_framework/ieee118_n60_stagewise_20260324_195044/stage6_warning_entropy_test_0001/baseline_calibrated_hourly_line_probability.csv` | Baseline calibrated hourly line probabilities. |
| `results/gridagent_framework/ieee118_n60_stagewise_20260324_195044/stage6_warning_entropy_test_0001/baseline_line_risk_prediction.csv` | Baseline model line risk predictions. |
| `results/gridagent_framework/ieee118_n60_stagewise_20260324_195044/stage6_warning_entropy_test_0001/calibrated_hourly_line_probability.csv` | Calibrated hourly line failure probability matrix. |
| `results/gridagent_framework/ieee118_n60_stagewise_20260324_195044/stage6_warning_entropy_test_0001/critical_load_risk.csv` | Critical load risk indicators over horizon. |
| `results/gridagent_framework/ieee118_n60_stagewise_20260324_195044/stage6_warning_entropy_test_0001/line_risk_prediction.csv` | Predicted line-level risk probabilities and labels. |
| `results/gridagent_framework/ieee118_n60_stagewise_20260324_195044/stage6_warning_entropy_test_0001/metapath_attention_summary.csv` | MetaPath semantic attention summary statistics. |
| `results/gridagent_framework/ieee118_n60_stagewise_20260324_195044/stage6_warning_entropy_test_0001/model_comparison.csv` | Model comparison metrics (baseline vs variants). |
| `results/gridagent_framework/ieee118_n60_stagewise_20260324_195044/stage6_warning_entropy_test_0001/nk_failure_risk.csv` | N-k style system-level failure risk indicators. |
| `results/gridagent_framework/ieee118_n60_stagewise_20260324_195044/stage6_warning_entropy_test_0001/node_weather_horizon.csv` | Forecast horizon weather features per node. |
| `results/gridagent_framework/ieee118_n60_stagewise_20260324_195044/stage6_warning_entropy_test_0001/node_weather_summary.csv` | Aggregated node weather statistics. |
| `results/gridagent_framework/ieee118_n60_stagewise_20260324_195044/stage6_warning_entropy_test_0001/node_weather_timeseries.csv` | Node-level weather time series used by warning stage. |
| `results/gridagent_framework/ieee118_n60_stagewise_20260324_195044/stage6_warning_entropy_test_0001/warning_report.json` | Stage6 warning model report with performance metrics. |
| `results/gridagent_framework/ieee118_n60_stagewise_20260324_195044/stage6_warning_entropy_test_0005/baseline_calibrated_hourly_line_probability.csv` | Baseline calibrated hourly line probabilities. |
| `results/gridagent_framework/ieee118_n60_stagewise_20260324_195044/stage6_warning_entropy_test_0005/baseline_line_risk_prediction.csv` | Baseline model line risk predictions. |
| `results/gridagent_framework/ieee118_n60_stagewise_20260324_195044/stage6_warning_entropy_test_0005/calibrated_hourly_line_probability.csv` | Calibrated hourly line failure probability matrix. |
| `results/gridagent_framework/ieee118_n60_stagewise_20260324_195044/stage6_warning_entropy_test_0005/critical_load_risk.csv` | Critical load risk indicators over horizon. |
| `results/gridagent_framework/ieee118_n60_stagewise_20260324_195044/stage6_warning_entropy_test_0005/line_risk_prediction.csv` | Predicted line-level risk probabilities and labels. |
| `results/gridagent_framework/ieee118_n60_stagewise_20260324_195044/stage6_warning_entropy_test_0005/metapath_attention_summary.csv` | MetaPath semantic attention summary statistics. |
| `results/gridagent_framework/ieee118_n60_stagewise_20260324_195044/stage6_warning_entropy_test_0005/model_comparison.csv` | Model comparison metrics (baseline vs variants). |
| `results/gridagent_framework/ieee118_n60_stagewise_20260324_195044/stage6_warning_entropy_test_0005/nk_failure_risk.csv` | N-k style system-level failure risk indicators. |
| `results/gridagent_framework/ieee118_n60_stagewise_20260324_195044/stage6_warning_entropy_test_0005/node_weather_horizon.csv` | Forecast horizon weather features per node. |
| `results/gridagent_framework/ieee118_n60_stagewise_20260324_195044/stage6_warning_entropy_test_0005/node_weather_summary.csv` | Aggregated node weather statistics. |
| `results/gridagent_framework/ieee118_n60_stagewise_20260324_195044/stage6_warning_entropy_test_0005/node_weather_timeseries.csv` | Node-level weather time series used by warning stage. |
| `results/gridagent_framework/ieee118_n60_stagewise_20260324_195044/stage6_warning_entropy_test_0005/warning_report.json` | Stage6 warning model report with performance metrics. |
| `results/gridagent_framework/ieee118_n60_stagewise_20260324_195044/stage6_warning_entropy_test/baseline_calibrated_hourly_line_probability.csv` | Baseline calibrated hourly line probabilities. |
| `results/gridagent_framework/ieee118_n60_stagewise_20260324_195044/stage6_warning_entropy_test/baseline_line_risk_prediction.csv` | Baseline model line risk predictions. |
| `results/gridagent_framework/ieee118_n60_stagewise_20260324_195044/stage6_warning_entropy_test/calibrated_hourly_line_probability.csv` | Calibrated hourly line failure probability matrix. |
| `results/gridagent_framework/ieee118_n60_stagewise_20260324_195044/stage6_warning_entropy_test/critical_load_risk.csv` | Critical load risk indicators over horizon. |
| `results/gridagent_framework/ieee118_n60_stagewise_20260324_195044/stage6_warning_entropy_test/line_risk_prediction.csv` | Predicted line-level risk probabilities and labels. |
| `results/gridagent_framework/ieee118_n60_stagewise_20260324_195044/stage6_warning_entropy_test/metapath_attention_summary.csv` | MetaPath semantic attention summary statistics. |
| `results/gridagent_framework/ieee118_n60_stagewise_20260324_195044/stage6_warning_entropy_test/model_comparison.csv` | Model comparison metrics (baseline vs variants). |
| `results/gridagent_framework/ieee118_n60_stagewise_20260324_195044/stage6_warning_entropy_test/nk_failure_risk.csv` | N-k style system-level failure risk indicators. |
| `results/gridagent_framework/ieee118_n60_stagewise_20260324_195044/stage6_warning_entropy_test/node_weather_horizon.csv` | Forecast horizon weather features per node. |
| `results/gridagent_framework/ieee118_n60_stagewise_20260324_195044/stage6_warning_entropy_test/node_weather_summary.csv` | Aggregated node weather statistics. |
| `results/gridagent_framework/ieee118_n60_stagewise_20260324_195044/stage6_warning_entropy_test/node_weather_timeseries.csv` | Node-level weather time series used by warning stage. |
| `results/gridagent_framework/ieee118_n60_stagewise_20260324_195044/stage6_warning_entropy_test/warning_report.json` | Stage6 warning model report with performance metrics. |
| `results/gridagent_framework/ieee118_n60_stagewise_20260324_195044/stage6_warning_split70_h0_backup/baseline_calibrated_hourly_line_probability.csv` | Baseline calibrated hourly line probabilities. |
| `results/gridagent_framework/ieee118_n60_stagewise_20260324_195044/stage6_warning_split70_h0_backup/baseline_line_risk_prediction.csv` | Baseline model line risk predictions. |
| `results/gridagent_framework/ieee118_n60_stagewise_20260324_195044/stage6_warning_split70_h0_backup/calibrated_hourly_line_probability.csv` | Calibrated hourly line failure probability matrix. |
| `results/gridagent_framework/ieee118_n60_stagewise_20260324_195044/stage6_warning_split70_h0_backup/critical_load_risk.csv` | Critical load risk indicators over horizon. |
| `results/gridagent_framework/ieee118_n60_stagewise_20260324_195044/stage6_warning_split70_h0_backup/line_risk_prediction.csv` | Predicted line-level risk probabilities and labels. |
| `results/gridagent_framework/ieee118_n60_stagewise_20260324_195044/stage6_warning_split70_h0_backup/metapath_attention_summary.csv` | MetaPath semantic attention summary statistics. |
| `results/gridagent_framework/ieee118_n60_stagewise_20260324_195044/stage6_warning_split70_h0_backup/model_comparison.csv` | Model comparison metrics (baseline vs variants). |
| `results/gridagent_framework/ieee118_n60_stagewise_20260324_195044/stage6_warning_split70_h0_backup/nk_failure_risk.csv` | N-k style system-level failure risk indicators. |
| `results/gridagent_framework/ieee118_n60_stagewise_20260324_195044/stage6_warning_split70_h0_backup/node_weather_horizon.csv` | Forecast horizon weather features per node. |
| `results/gridagent_framework/ieee118_n60_stagewise_20260324_195044/stage6_warning_split70_h0_backup/node_weather_summary.csv` | Aggregated node weather statistics. |
| `results/gridagent_framework/ieee118_n60_stagewise_20260324_195044/stage6_warning_split70_h0_backup/node_weather_timeseries.csv` | Node-level weather time series used by warning stage. |
| `results/gridagent_framework/ieee118_n60_stagewise_20260324_195044/stage6_warning_split70_h0_backup/warning_report.json` | Stage6 warning model report with performance metrics. |
| `results/gridagent_framework/ieee118_n60_stagewise_20260324_195044/stage6_warning/baseline_calibrated_hourly_line_probability.csv` | Baseline calibrated hourly line probabilities. |
| `results/gridagent_framework/ieee118_n60_stagewise_20260324_195044/stage6_warning/baseline_line_risk_prediction.csv` | Baseline model line risk predictions. |
| `results/gridagent_framework/ieee118_n60_stagewise_20260324_195044/stage6_warning/calibrated_hourly_line_probability.csv` | Calibrated hourly line failure probability matrix. |
| `results/gridagent_framework/ieee118_n60_stagewise_20260324_195044/stage6_warning/critical_load_risk.csv` | Critical load risk indicators over horizon. |
| `results/gridagent_framework/ieee118_n60_stagewise_20260324_195044/stage6_warning/line_risk_prediction.csv` | Predicted line-level risk probabilities and labels. |
| `results/gridagent_framework/ieee118_n60_stagewise_20260324_195044/stage6_warning/metapath_attention_summary.csv` | MetaPath semantic attention summary statistics. |
| `results/gridagent_framework/ieee118_n60_stagewise_20260324_195044/stage6_warning/model_comparison.csv` | Model comparison metrics (baseline vs variants). |
| `results/gridagent_framework/ieee118_n60_stagewise_20260324_195044/stage6_warning/nk_failure_risk.csv` | N-k style system-level failure risk indicators. |
| `results/gridagent_framework/ieee118_n60_stagewise_20260324_195044/stage6_warning/node_weather_horizon.csv` | Forecast horizon weather features per node. |
| `results/gridagent_framework/ieee118_n60_stagewise_20260324_195044/stage6_warning/node_weather_summary.csv` | Aggregated node weather statistics. |
| `results/gridagent_framework/ieee118_n60_stagewise_20260324_195044/stage6_warning/node_weather_timeseries.csv` | Node-level weather time series used by warning stage. |
| `results/gridagent_framework/ieee118_n60_stagewise_20260324_195044/stage6_warning/warning_report.json` | Stage6 warning model report with performance metrics. |
| `results/gridagent_framework/ieee118_n60_stagewise_20260324_195044/stage7_dispatch_optimization_comparison/contextual_dispatch_hourly_cost.csv` | Context-aware hourly operational cost trace. |
| `results/gridagent_framework/ieee118_n60_stagewise_20260324_195044/stage7_dispatch_optimization_comparison/contextual_dispatch_load_shedding.csv` | Context-aware load shedding schedule. |
| `results/gridagent_framework/ieee118_n60_stagewise_20260324_195044/stage7_dispatch_optimization_comparison/contextual_dispatch_unit_schedule.csv` | Context-aware dispatch generation schedule. |
| `results/gridagent_framework/ieee118_n60_stagewise_20260324_195044/stage7_dispatch_optimization_comparison/dispatch_active_strategy_summary.csv` | Summary of active dispatch strategy over time. |
| `results/gridagent_framework/ieee118_n60_stagewise_20260324_195044/stage7_dispatch_optimization_comparison/dispatch_ewm_topsis_result.csv` | Dispatch strategy composite ranking from EWM+TOPSIS. |
| `results/gridagent_framework/ieee118_n60_stagewise_20260324_195044/stage7_dispatch_optimization_comparison/dispatch_indicator_weights.csv` | Indicator weights used in dispatch strategy scoring. |
| `results/gridagent_framework/ieee118_n60_stagewise_20260324_195044/stage7_dispatch_optimization_comparison/dispatch_model_comparison.csv` | SCUC/Stochastic/Robust model comparison metrics. |
| `results/gridagent_framework/ieee118_n60_stagewise_20260324_195044/stage7_dispatch_optimization_comparison/dispatch_optimization_report.json` | Stage7 dispatch optimization report. |
| `results/gridagent_framework/ieee118_n60_stagewise_20260324_195044/stage7_dispatch_optimization_comparison/dispatch_strategy_selection.csv` | Risk-context strategy switching record by time step. |
| `results/gridagent_framework/ieee118_n60_stagewise_20260324_195044/stage7_dispatch_optimization_comparison/line_flow.csv` | Line flow results from dispatch optimization. |
| `results/gridagent_framework/ieee118_n60_stagewise_20260324_195044/stage7_dispatch_optimization_comparison/robust_uc_first_stage_schedule.csv` | Robust UC first-stage schedule output. |
| `results/gridagent_framework/ieee118_n60_stagewise_20260324_195044/stage7_dispatch_optimization_comparison/robust_uc_scenario_summary.csv` | Robust UC scenario summary metrics. |
| `results/gridagent_framework/ieee118_n60_stagewise_20260324_195044/stage7_dispatch_optimization_comparison/robust_uc_worst_load_shedding.csv` | Worst-case load shedding under robust UC. |
| `results/gridagent_framework/ieee118_n60_stagewise_20260324_195044/stage7_dispatch_optimization_comparison/scuc_load_shedding.csv` | SCUC load shedding output table. |
| `results/gridagent_framework/ieee118_n60_stagewise_20260324_195044/stage7_dispatch_optimization_comparison/scuc_schedule.csv` | SCUC schedule output table. |
| `results/gridagent_framework/ieee118_n60_stagewise_20260324_195044/stage7_dispatch_optimization_comparison/stochastic_uc_expected_load_shedding.csv` | Expected load shedding under stochastic UC. |
| `results/gridagent_framework/ieee118_n60_stagewise_20260324_195044/stage7_dispatch_optimization_comparison/stochastic_uc_first_stage_schedule.csv` | Stochastic UC first-stage schedule output. |
| `results/gridagent_framework/ieee118_n60_stagewise_20260324_195044/stage7_dispatch_optimization_comparison/stochastic_uc_scenario_summary.csv` | Stochastic UC scenario summary metrics. |
| `results/gridagent_framework/ieee118_n60_stagewise_20260324_195044/stage7_dispatch_optimization/contextual_dispatch_hourly_cost.csv` | Context-aware hourly operational cost trace. |
| `results/gridagent_framework/ieee118_n60_stagewise_20260324_195044/stage7_dispatch_optimization/contextual_dispatch_load_shedding.csv` | Context-aware load shedding schedule. |
| `results/gridagent_framework/ieee118_n60_stagewise_20260324_195044/stage7_dispatch_optimization/contextual_dispatch_unit_schedule.csv` | Context-aware dispatch generation schedule. |
| `results/gridagent_framework/ieee118_n60_stagewise_20260324_195044/stage7_dispatch_optimization/dispatch_active_strategy_summary.csv` | Summary of active dispatch strategy over time. |
| `results/gridagent_framework/ieee118_n60_stagewise_20260324_195044/stage7_dispatch_optimization/dispatch_indicator_weights.csv` | Indicator weights used in dispatch strategy scoring. |
| `results/gridagent_framework/ieee118_n60_stagewise_20260324_195044/stage7_dispatch_optimization/dispatch_optimization_report.json` | Stage7 dispatch optimization report. |
| `results/gridagent_framework/ieee118_n60_stagewise_20260324_195044/stage7_dispatch_optimization/dispatch_strategy_selection.csv` | Risk-context strategy switching record by time step. |
| `results/gridagent_framework/ieee118_n60_stagewise_20260324_195044/stage7_dispatch_optimization/line_flow.csv` | Line flow results from dispatch optimization. |
| `results/gridagent_framework/ieee118_n60_stagewise_20260324_195044/stage7_dispatch_optimization/robust_uc_first_stage_schedule.csv` | Robust UC first-stage schedule output. |
| `results/gridagent_framework/ieee118_n60_stagewise_20260324_195044/stage7_dispatch_optimization/robust_uc_scenario_summary.csv` | Robust UC scenario summary metrics. |
| `results/gridagent_framework/ieee118_n60_stagewise_20260324_195044/stage7_dispatch_optimization/robust_uc_worst_load_shedding.csv` | Worst-case load shedding under robust UC. |
| `results/gridagent_framework/ieee118_n60_stagewise_20260324_195044/stage7_dispatch_optimization/scuc_load_shedding.csv` | SCUC load shedding output table. |
| `results/gridagent_framework/ieee118_n60_stagewise_20260324_195044/stage7_dispatch_optimization/scuc_schedule.csv` | SCUC schedule output table. |
| `results/gridagent_framework/ieee118_n60_stagewise_20260324_195044/stage7_dispatch_optimization/stochastic_uc_expected_load_shedding.csv` | Expected load shedding under stochastic UC. |
| `results/gridagent_framework/ieee118_n60_stagewise_20260324_195044/stage7_dispatch_optimization/stochastic_uc_first_stage_schedule.csv` | Stochastic UC first-stage schedule output. |
| `results/gridagent_framework/ieee118_n60_stagewise_20260324_195044/stage7_dispatch_optimization/stochastic_uc_scenario_summary.csv` | Stochastic UC scenario summary metrics. |
| `results/gridagent_framework/latest_run.json` | Pointer to latest framework run directory. |
| `results/gridagent_framework/warning_integration_dryrun/framework_report.json` | End-to-end framework run report. |
| `results/gridagent_framework/warning_integration_smoke/framework_report.json` | End-to-end framework run report. |
| `results/gridagent_framework/warning_integration_smoke/stage1_wind_pv/formal2024/history_series.csv` | Historical time series used as model input. |
| `results/gridagent_framework/warning_integration_smoke/stage1_wind_pv/formal2024/sampled_scenarios.npy` | Sampled scenario tensor for simulation input. |
| `results/gridagent_framework/warning_integration_smoke/stage1_wind_pv/formal2024/scenario_probabilities.csv` | Probability assigned to each generated scenario. |
| `results/gridagent_framework/warning_integration_smoke/stage1_wind_pv/formal2024/typical_scenarios_long.csv` | Long-form scenario table by timestamp and scenario id. |
| `results/gridagent_framework/warning_integration_smoke/stage1_wind_pv/formal2024/typical_scenarios.npy` | NumPy tensor of representative scenarios. |
| `results/gridagent_framework/warning_integration_smoke/stage1_wind_pv/formal2024/uncertainty_report.json` | Stage1 uncertainty modeling report and metrics. |
| `results/gridagent_framework/warning_integration_smoke/stage2_failure/schloemer/failure_probability_report.json` | Stage2 component/line failure probability report. |
| `results/gridagent_framework/warning_integration_smoke/stage2_failure/schloemer/line_failure_timeseries_schloemer.csv` | Time-series line failure probabilities under Schloemer model. |
| `results/gridagent_framework/warning_integration_smoke/stage3_contingency/schloemer/contingency_report.json` | Stage3 spatiotemporal contingency generation report. |
| `results/gridagent_framework/warning_integration_smoke/stage3_contingency/schloemer/contingency_tensor_c3po_ref.npy` | Contingency state tensor generated by C3PO reference method. |
| `results/gridagent_framework/warning_integration_smoke/stage3_contingency/schloemer/line_probability_summary_c3po_ref.csv` | Per-line probability summary for C3PO reference method. |
| `results/gridagent_framework/warning_integration_smoke/stage3_contingency/schloemer/method_comparison.csv` | Cross-method comparison metrics table. |
| `results/gridagent_framework/warning_integration_smoke/stage3_contingency/schloemer/state_summary_c3po_ref.csv` | State occurrence summary for C3PO reference method. |
| `results/gridagent_framework/warning_integration_smoke/stage4_scheduling/schloemer__c3po_ref__rr0p3/load_bus_priority_profile.csv` | Per-load-bus priority/weight profile. |
| `results/gridagent_framework/warning_integration_smoke/stage4_scheduling/schloemer__c3po_ref__rr0p3/load_prioritization_report.json` | Stage4 load prioritization and scheduling report. |
| `results/gridagent_framework/warning_integration_smoke/stage4_scheduling/schloemer__c3po_ref__rr0p3/policy_comparison.csv` | Policy comparison results for scheduling stage. |
| `results/gridagent_framework/warning_integration_smoke/stage4_scheduling/schloemer__c3po_ref__rr0p3/pre_disaster_dispatch_schedule.csv` | Optimized pre-disaster generation dispatch schedule. |
| `results/gridagent_framework/warning_integration_smoke/stage4_scheduling/schloemer__c3po_ref__rr0p3/scenario_metrics.csv` | Scenario-level reliability/cost/shedding metrics. |
| `results/gridagent_framework/warning_integration_smoke/stage4_scheduling/schloemer__c3po_ref__rr0p3/worst_scenario_shedding_detail.csv` | Detailed shedding actions under worst scenario. |
| `results/gridagent_framework/warning_integration_smoke/stage5_assessment/ewm_topsis_result.csv` | Composite ranking result from EWM+TOPSIS. |
| `results/gridagent_framework/warning_integration_smoke/stage5_assessment/indicator_table.csv` | Indicator matrix for resilience evaluation. |
| `results/gridagent_framework/warning_integration_smoke/stage5_assessment/multi_criteria_report.json` | Stage5 multi-criteria resilience assessment report. |
| `results/gridagent_framework/warning_integration_smoke/stage5_assessment/single_indicator_ranking.csv` | Ranking by each single resilience indicator. |
| `results/gridagent_framework/warning_integration_smoke/stage6_warning/calibrated_hourly_line_probability.csv` | Calibrated hourly line failure probability matrix. |
| `results/gridagent_framework/warning_integration_smoke/stage6_warning/critical_load_risk.csv` | Critical load risk indicators over horizon. |
| `results/gridagent_framework/warning_integration_smoke/stage6_warning/line_risk_prediction.csv` | Predicted line-level risk probabilities and labels. |
| `results/gridagent_framework/warning_integration_smoke/stage6_warning/nk_failure_risk.csv` | N-k style system-level failure risk indicators. |
| `results/gridagent_framework/warning_integration_smoke/stage6_warning/warning_report.json` | Stage6 warning model report with performance metrics. |
| `results/load_prioritization_paper_extracted.txt` | Text/markdown notes; starts with: ===== PAGE 1 ===== |
| `results/load_prioritization_scheduling/formal2024/load_bus_priority_profile.csv` | Per-load-bus priority/weight profile. |
| `results/load_prioritization_scheduling/formal2024/load_prioritization_report.json` | Stage4 load prioritization and scheduling report. |
| `results/load_prioritization_scheduling/formal2024/policy_comparison.csv` | Policy comparison results for scheduling stage. |
| `results/load_prioritization_scheduling/formal2024/pre_disaster_dispatch_schedule.csv` | Optimized pre-disaster generation dispatch schedule. |
| `results/load_prioritization_scheduling/formal2024/scenario_metrics.csv` | Scenario-level reliability/cost/shedding metrics. |
| `results/load_prioritization_scheduling/formal2024/worst_scenario_shedding_detail.csv` | Detailed shedding actions under worst scenario. |
| `results/module_sensitivity/formal2024/indicator_ewm_weights.csv` | CSV table; columns: indicator, ewm_weight. |
| `results/module_sensitivity/formal2024/module_influence_weights.csv` | CSV table; columns: module, delta_r2, influence_weight. |
| `results/module_sensitivity/formal2024/module_level_summary.csv` | CSV table; columns: level, avg_topsis, avg_priority, avg_robustness, avg_rapidity, avg_sustainability, avg_cost, module. |
| `results/module_sensitivity/formal2024/sensitivity_report.json` | JSON object; top keys: experiment_design, resilience_indicators, best_run, module_influence, most_critical_module, output_files. |
| `results/module_sensitivity/formal2024/sensitivity_runs.csv` | CSV table; columns: failure_model, contingency_method, reserve_ratio, run_tag, Priority, Robustness, Rapidity, Sustainability, .... |
| `results/module_sensitivity/formal2024/single_indicator_best_runs.csv` | CSV table; columns: indicator, best_run_tag, best_value, failure_model, contingency_method, reserve_ratio. |
| `results/multi_criteria_resilience/formal2024/ewm_topsis_result.csv` | Composite ranking result from EWM+TOPSIS. |
| `results/multi_criteria_resilience/formal2024/indicator_table.csv` | Indicator matrix for resilience evaluation. |
| `results/multi_criteria_resilience/formal2024/multi_criteria_report.json` | Stage5 multi-criteria resilience assessment report. |
| `results/multi_criteria_resilience/formal2024/single_indicator_ranking.csv` | Ranking by each single resilience indicator. |
| `results/multiscenario_fusion/phase1_design/cloud_eval_v1/fusion_environment_summary.csv` | CSV table; columns: env_id, intensity_scale, wind_variant, load_scenario, best_fusion_score, avg_fusion_score, avg_warning_auprc, avg_rr, .... |
| `results/multiscenario_fusion/phase1_design/cloud_eval_v1/fusion_indicator_weights.csv` | CSV table; columns: indicator, ewm_weight. |
| `results/multiscenario_fusion/phase1_design/cloud_eval_v1/fusion_report.json` | JSON object; top keys: generated_at, design_manifest, output_dir, run_config, counts, best_run, best_strategy_global, artifacts. |
| `results/multiscenario_fusion/phase1_design/cloud_eval_v1/fusion_runs.csv` | CSV table; columns: env_id, sample_id, intensity_scale, wind_variant, load_scenario, priority_stress_factor, strategy_id, run_tag, .... |
| `results/multiscenario_fusion/phase1_design/cloud_eval_v1/fusion_strategy_summary.csv` | CSV table; columns: strategy_id, run_tag, failure_model, contingency_method, reserve_ratio, mean_fusion_score, std_fusion_score, mean_warning_auprc, .... |
| `results/multiscenario_fusion/phase1_design/env_matrix_full.csv` | CSV table; columns: env_id, intensity_idx, wind_idx, load_idx, intensity_scale, wind_variant, wind_scale, pv_scale, .... |
| `results/multiscenario_fusion/phase1_design/env_matrix_sampled.csv` | CSV table; columns: env_id, intensity_idx, wind_idx, load_idx, intensity_scale, wind_variant, wind_scale, pv_scale, .... |
| `results/multiscenario_fusion/phase1_design/experiment_manifest_cloud_top2.json` | JSON object; top keys: run_tag, generated_at, config_path, run_root, seed, phase, inputs, counts, .... |
| `results/multiscenario_fusion/phase1_design/experiment_manifest.json` | JSON object; top keys: run_tag, generated_at, config_path, run_root, seed, phase, inputs, counts, .... |
| `results/multiscenario_fusion/phase1_design/load_scenarios.csv` | CSV table; columns: load_scenario, demand_scale, priority_stress_factor, trim_input. |
| `results/multiscenario_fusion/phase1_design/step4_analysis/by_intensity_delta.csv` | CSV table; columns: intensity_scale, delta_STR001_minus_STR003. |
| `results/multiscenario_fusion/phase1_design/step4_analysis/by_intensity_strategy_metrics.csv` | CSV table; columns: intensity_scale, strategy_id, run_tag, mean_fusion_score, std_fusion_score, mean_warning_auprc, mean_warning_recall_top10, mean_rr, .... |
| `results/multiscenario_fusion/phase1_design/step4_analysis/by_intensity_winner.csv` | CSV table; columns: intensity_scale, strategy_id, run_tag, mean_fusion_score, std_fusion_score, mean_warning_auprc, mean_warning_recall_top10, mean_rr, .... |
| `results/multiscenario_fusion/phase1_design/step4_analysis/by_load_scenario_delta.csv` | CSV table; columns: load_scenario, delta_STR001_minus_STR003. |
| `results/multiscenario_fusion/phase1_design/step4_analysis/by_load_scenario_strategy_metrics.csv` | CSV table; columns: load_scenario, strategy_id, run_tag, mean_fusion_score, std_fusion_score, mean_warning_auprc, mean_warning_recall_top10, mean_rr, .... |
| `results/multiscenario_fusion/phase1_design/step4_analysis/by_load_scenario_winner.csv` | CSV table; columns: load_scenario, strategy_id, run_tag, mean_fusion_score, std_fusion_score, mean_warning_auprc, mean_warning_recall_top10, mean_rr, .... |
| `results/multiscenario_fusion/phase1_design/step4_analysis/by_wind_variant_delta.csv` | CSV table; columns: wind_variant, delta_STR001_minus_STR003. |
| `results/multiscenario_fusion/phase1_design/step4_analysis/by_wind_variant_strategy_metrics.csv` | CSV table; columns: wind_variant, strategy_id, run_tag, mean_fusion_score, std_fusion_score, mean_warning_auprc, mean_warning_recall_top10, mean_rr, .... |
| `results/multiscenario_fusion/phase1_design/step4_analysis/by_wind_variant_winner.csv` | CSV table; columns: wind_variant, strategy_id, run_tag, mean_fusion_score, std_fusion_score, mean_warning_auprc, mean_warning_recall_top10, mean_rr, .... |
| `results/multiscenario_fusion/phase1_design/step4_analysis/environment_risk_view.csv` | CSV table; columns: env_id, intensity_scale, wind_variant, load_scenario, best_fusion_score, avg_fusion_score, avg_warning_auprc, avg_rr, .... |
| `results/multiscenario_fusion/phase1_design/step4_analysis/global_strategy_summary.csv` | CSV table; columns: strategy_id, run_tag, failure_model, contingency_method, reserve_ratio, mean_fusion_score, std_fusion_score, mean_warning_auprc, .... |
| `results/multiscenario_fusion/phase1_design/step4_analysis/step4_report.json` | JSON object; top keys: source, output_dir, counts, best_strategy_global, intensity_winner_counts, wind_winner_counts, load_winner_counts, files. |
| `results/multiscenario_fusion/phase1_design/step6_final_delivery.md` | Text/markdown notes; starts with: # Step6 Final Delivery |
| `results/multiscenario_fusion/phase1_design/step6_final_summary.json` | JSON object; top keys: step, source, global_recommended_strategy, best_single_run, counts, outputs, notes. |
| `results/multiscenario_fusion/phase1_design/strategy_pool_top2_cloud.csv` | CSV table; columns: strategy_id, run_tag, failure_model, contingency_method, reserve_ratio. |
| `results/multiscenario_fusion/phase1_design/strategy_pool.csv` | CSV table; columns: strategy_id, run_tag, failure_model, contingency_method, reserve_ratio. |
| `results/multiscenario_fusion/phase1_design/wind_pv_variants.csv` | CSV table; columns: variant, wind_scale, pv_scale, uncertainty_dir. |
| `results/paper_comparison/formal2024_comparison_20260316_134803/comparison_table_filled.csv` | Filled comparison table for manuscript reporting. |
| `results/paper_comparison/formal2024_comparison_20260316_134803/dispatch_uniform_priority/contextual_dispatch_hourly_cost.csv` | Context-aware hourly operational cost trace. |
| `results/paper_comparison/formal2024_comparison_20260316_134803/dispatch_uniform_priority/contextual_dispatch_load_shedding.csv` | Context-aware load shedding schedule. |
| `results/paper_comparison/formal2024_comparison_20260316_134803/dispatch_uniform_priority/contextual_dispatch_unit_schedule.csv` | Context-aware dispatch generation schedule. |
| `results/paper_comparison/formal2024_comparison_20260316_134803/dispatch_uniform_priority/dispatch_active_strategy_summary.csv` | Summary of active dispatch strategy over time. |
| `results/paper_comparison/formal2024_comparison_20260316_134803/dispatch_uniform_priority/dispatch_ewm_topsis_result.csv` | Dispatch strategy composite ranking from EWM+TOPSIS. |
| `results/paper_comparison/formal2024_comparison_20260316_134803/dispatch_uniform_priority/dispatch_indicator_weights.csv` | Indicator weights used in dispatch strategy scoring. |
| `results/paper_comparison/formal2024_comparison_20260316_134803/dispatch_uniform_priority/dispatch_model_comparison.csv` | SCUC/Stochastic/Robust model comparison metrics. |
| `results/paper_comparison/formal2024_comparison_20260316_134803/dispatch_uniform_priority/dispatch_optimization_report.json` | Stage7 dispatch optimization report. |
| `results/paper_comparison/formal2024_comparison_20260316_134803/dispatch_uniform_priority/dispatch_strategy_selection.csv` | Risk-context strategy switching record by time step. |
| `results/paper_comparison/formal2024_comparison_20260316_134803/dispatch_uniform_priority/line_flow.csv` | Line flow results from dispatch optimization. |
| `results/paper_comparison/formal2024_comparison_20260316_134803/dispatch_uniform_priority/robust_uc_first_stage_schedule.csv` | Robust UC first-stage schedule output. |
| `results/paper_comparison/formal2024_comparison_20260316_134803/dispatch_uniform_priority/robust_uc_scenario_summary.csv` | Robust UC scenario summary metrics. |
| `results/paper_comparison/formal2024_comparison_20260316_134803/dispatch_uniform_priority/robust_uc_worst_load_shedding.csv` | Worst-case load shedding under robust UC. |
| `results/paper_comparison/formal2024_comparison_20260316_134803/dispatch_uniform_priority/scuc_load_shedding.csv` | SCUC load shedding output table. |
| `results/paper_comparison/formal2024_comparison_20260316_134803/dispatch_uniform_priority/scuc_schedule.csv` | SCUC schedule output table. |
| `results/paper_comparison/formal2024_comparison_20260316_134803/dispatch_uniform_priority/stochastic_uc_expected_load_shedding.csv` | Expected load shedding under stochastic UC. |
| `results/paper_comparison/formal2024_comparison_20260316_134803/dispatch_uniform_priority/stochastic_uc_first_stage_schedule.csv` | Stochastic UC first-stage schedule output. |
| `results/paper_comparison/formal2024_comparison_20260316_134803/dispatch_uniform_priority/stochastic_uc_scenario_summary.csv` | Stochastic UC scenario summary metrics. |
| `results/paper_comparison/formal2024_comparison_20260316_134803/dispatch_weighted_priority/contextual_dispatch_hourly_cost.csv` | Context-aware hourly operational cost trace. |
| `results/paper_comparison/formal2024_comparison_20260316_134803/dispatch_weighted_priority/contextual_dispatch_load_shedding.csv` | Context-aware load shedding schedule. |
| `results/paper_comparison/formal2024_comparison_20260316_134803/dispatch_weighted_priority/contextual_dispatch_unit_schedule.csv` | Context-aware dispatch generation schedule. |
| `results/paper_comparison/formal2024_comparison_20260316_134803/dispatch_weighted_priority/dispatch_active_strategy_summary.csv` | Summary of active dispatch strategy over time. |
| `results/paper_comparison/formal2024_comparison_20260316_134803/dispatch_weighted_priority/dispatch_ewm_topsis_result.csv` | Dispatch strategy composite ranking from EWM+TOPSIS. |
| `results/paper_comparison/formal2024_comparison_20260316_134803/dispatch_weighted_priority/dispatch_indicator_weights.csv` | Indicator weights used in dispatch strategy scoring. |
| `results/paper_comparison/formal2024_comparison_20260316_134803/dispatch_weighted_priority/dispatch_model_comparison.csv` | SCUC/Stochastic/Robust model comparison metrics. |
| `results/paper_comparison/formal2024_comparison_20260316_134803/dispatch_weighted_priority/dispatch_optimization_report.json` | Stage7 dispatch optimization report. |
| `results/paper_comparison/formal2024_comparison_20260316_134803/dispatch_weighted_priority/dispatch_strategy_selection.csv` | Risk-context strategy switching record by time step. |
| `results/paper_comparison/formal2024_comparison_20260316_134803/dispatch_weighted_priority/line_flow.csv` | Line flow results from dispatch optimization. |
| `results/paper_comparison/formal2024_comparison_20260316_134803/dispatch_weighted_priority/robust_uc_first_stage_schedule.csv` | Robust UC first-stage schedule output. |
| `results/paper_comparison/formal2024_comparison_20260316_134803/dispatch_weighted_priority/robust_uc_scenario_summary.csv` | Robust UC scenario summary metrics. |
| `results/paper_comparison/formal2024_comparison_20260316_134803/dispatch_weighted_priority/robust_uc_worst_load_shedding.csv` | Worst-case load shedding under robust UC. |
| `results/paper_comparison/formal2024_comparison_20260316_134803/dispatch_weighted_priority/scuc_load_shedding.csv` | SCUC load shedding output table. |
| `results/paper_comparison/formal2024_comparison_20260316_134803/dispatch_weighted_priority/scuc_schedule.csv` | SCUC schedule output table. |
| `results/paper_comparison/formal2024_comparison_20260316_134803/dispatch_weighted_priority/stochastic_uc_expected_load_shedding.csv` | Expected load shedding under stochastic UC. |
| `results/paper_comparison/formal2024_comparison_20260316_134803/dispatch_weighted_priority/stochastic_uc_first_stage_schedule.csv` | Stochastic UC first-stage schedule output. |
| `results/paper_comparison/formal2024_comparison_20260316_134803/dispatch_weighted_priority/stochastic_uc_scenario_summary.csv` | Stochastic UC scenario summary metrics. |
| `results/paper_comparison/formal2024_comparison_20260316_134803/uniform_load_priority_profile.csv` | CSV table; columns: load_bus, priority_level, priority_weight, demand_share. |
| `results/paper_comparison/formal2024_comparison_20260316_134844/comparison_metadata.json` | Metadata for paper comparison experiment batch. |
| `results/paper_comparison/formal2024_comparison_20260316_134844/comparison_table_filled.csv` | Filled comparison table for manuscript reporting. |
| `results/paper_comparison/formal2024_comparison_20260316_134844/comparison_table_filled.md` | Markdown version of manuscript comparison table. |
| `results/paper_comparison/formal2024_comparison_20260316_134844/dispatch_uniform_priority/contextual_dispatch_hourly_cost.csv` | Context-aware hourly operational cost trace. |
| `results/paper_comparison/formal2024_comparison_20260316_134844/dispatch_uniform_priority/contextual_dispatch_load_shedding.csv` | Context-aware load shedding schedule. |
| `results/paper_comparison/formal2024_comparison_20260316_134844/dispatch_uniform_priority/contextual_dispatch_unit_schedule.csv` | Context-aware dispatch generation schedule. |
| `results/paper_comparison/formal2024_comparison_20260316_134844/dispatch_uniform_priority/dispatch_active_strategy_summary.csv` | Summary of active dispatch strategy over time. |
| `results/paper_comparison/formal2024_comparison_20260316_134844/dispatch_uniform_priority/dispatch_ewm_topsis_result.csv` | Dispatch strategy composite ranking from EWM+TOPSIS. |
| `results/paper_comparison/formal2024_comparison_20260316_134844/dispatch_uniform_priority/dispatch_indicator_weights.csv` | Indicator weights used in dispatch strategy scoring. |
| `results/paper_comparison/formal2024_comparison_20260316_134844/dispatch_uniform_priority/dispatch_model_comparison.csv` | SCUC/Stochastic/Robust model comparison metrics. |
| `results/paper_comparison/formal2024_comparison_20260316_134844/dispatch_uniform_priority/dispatch_optimization_report.json` | Stage7 dispatch optimization report. |
| `results/paper_comparison/formal2024_comparison_20260316_134844/dispatch_uniform_priority/dispatch_strategy_selection.csv` | Risk-context strategy switching record by time step. |
| `results/paper_comparison/formal2024_comparison_20260316_134844/dispatch_uniform_priority/line_flow.csv` | Line flow results from dispatch optimization. |
| `results/paper_comparison/formal2024_comparison_20260316_134844/dispatch_uniform_priority/robust_uc_first_stage_schedule.csv` | Robust UC first-stage schedule output. |
| `results/paper_comparison/formal2024_comparison_20260316_134844/dispatch_uniform_priority/robust_uc_scenario_summary.csv` | Robust UC scenario summary metrics. |
| `results/paper_comparison/formal2024_comparison_20260316_134844/dispatch_uniform_priority/robust_uc_worst_load_shedding.csv` | Worst-case load shedding under robust UC. |
| `results/paper_comparison/formal2024_comparison_20260316_134844/dispatch_uniform_priority/scuc_load_shedding.csv` | SCUC load shedding output table. |
| `results/paper_comparison/formal2024_comparison_20260316_134844/dispatch_uniform_priority/scuc_schedule.csv` | SCUC schedule output table. |
| `results/paper_comparison/formal2024_comparison_20260316_134844/dispatch_uniform_priority/stochastic_uc_expected_load_shedding.csv` | Expected load shedding under stochastic UC. |
| `results/paper_comparison/formal2024_comparison_20260316_134844/dispatch_uniform_priority/stochastic_uc_first_stage_schedule.csv` | Stochastic UC first-stage schedule output. |
| `results/paper_comparison/formal2024_comparison_20260316_134844/dispatch_uniform_priority/stochastic_uc_scenario_summary.csv` | Stochastic UC scenario summary metrics. |
| `results/paper_comparison/formal2024_comparison_20260316_134844/dispatch_weighted_priority/contextual_dispatch_hourly_cost.csv` | Context-aware hourly operational cost trace. |
| `results/paper_comparison/formal2024_comparison_20260316_134844/dispatch_weighted_priority/contextual_dispatch_load_shedding.csv` | Context-aware load shedding schedule. |
| `results/paper_comparison/formal2024_comparison_20260316_134844/dispatch_weighted_priority/contextual_dispatch_unit_schedule.csv` | Context-aware dispatch generation schedule. |
| `results/paper_comparison/formal2024_comparison_20260316_134844/dispatch_weighted_priority/dispatch_active_strategy_summary.csv` | Summary of active dispatch strategy over time. |
| `results/paper_comparison/formal2024_comparison_20260316_134844/dispatch_weighted_priority/dispatch_ewm_topsis_result.csv` | Dispatch strategy composite ranking from EWM+TOPSIS. |
| `results/paper_comparison/formal2024_comparison_20260316_134844/dispatch_weighted_priority/dispatch_indicator_weights.csv` | Indicator weights used in dispatch strategy scoring. |
| `results/paper_comparison/formal2024_comparison_20260316_134844/dispatch_weighted_priority/dispatch_model_comparison.csv` | SCUC/Stochastic/Robust model comparison metrics. |
| `results/paper_comparison/formal2024_comparison_20260316_134844/dispatch_weighted_priority/dispatch_optimization_report.json` | Stage7 dispatch optimization report. |
| `results/paper_comparison/formal2024_comparison_20260316_134844/dispatch_weighted_priority/dispatch_strategy_selection.csv` | Risk-context strategy switching record by time step. |
| `results/paper_comparison/formal2024_comparison_20260316_134844/dispatch_weighted_priority/line_flow.csv` | Line flow results from dispatch optimization. |
| `results/paper_comparison/formal2024_comparison_20260316_134844/dispatch_weighted_priority/robust_uc_first_stage_schedule.csv` | Robust UC first-stage schedule output. |
| `results/paper_comparison/formal2024_comparison_20260316_134844/dispatch_weighted_priority/robust_uc_scenario_summary.csv` | Robust UC scenario summary metrics. |
| `results/paper_comparison/formal2024_comparison_20260316_134844/dispatch_weighted_priority/robust_uc_worst_load_shedding.csv` | Worst-case load shedding under robust UC. |
| `results/paper_comparison/formal2024_comparison_20260316_134844/dispatch_weighted_priority/scuc_load_shedding.csv` | SCUC load shedding output table. |
| `results/paper_comparison/formal2024_comparison_20260316_134844/dispatch_weighted_priority/scuc_schedule.csv` | SCUC schedule output table. |
| `results/paper_comparison/formal2024_comparison_20260316_134844/dispatch_weighted_priority/stochastic_uc_expected_load_shedding.csv` | Expected load shedding under stochastic UC. |
| `results/paper_comparison/formal2024_comparison_20260316_134844/dispatch_weighted_priority/stochastic_uc_first_stage_schedule.csv` | Stochastic UC first-stage schedule output. |
| `results/paper_comparison/formal2024_comparison_20260316_134844/dispatch_weighted_priority/stochastic_uc_scenario_summary.csv` | Stochastic UC scenario summary metrics. |
| `results/paper_comparison/formal2024_comparison_20260316_134844/uniform_load_priority_profile.csv` | CSV table; columns: load_bus, priority_level, priority_weight, demand_share. |
| `results/paper_comparison/stage7_comparison/formal2024_comparison_20260330_234957/comparison_metadata.json` | Metadata for paper comparison experiment batch. |
| `results/paper_comparison/stage7_comparison/formal2024_comparison_20260330_234957/comparison_table_filled.csv` | Filled comparison table for manuscript reporting. |
| `results/paper_comparison/stage7_comparison/formal2024_comparison_20260330_234957/comparison_table_filled.md` | Markdown version of manuscript comparison table. |
| `results/paper_comparison/stage7_comparison/formal2024_comparison_20260330_234957/dispatch_uniform_priority/contextual_dispatch_hourly_cost.csv` | Context-aware hourly operational cost trace. |
| `results/paper_comparison/stage7_comparison/formal2024_comparison_20260330_234957/dispatch_uniform_priority/contextual_dispatch_load_shedding.csv` | Context-aware load shedding schedule. |
| `results/paper_comparison/stage7_comparison/formal2024_comparison_20260330_234957/dispatch_uniform_priority/contextual_dispatch_unit_schedule.csv` | Context-aware dispatch generation schedule. |
| `results/paper_comparison/stage7_comparison/formal2024_comparison_20260330_234957/dispatch_uniform_priority/dispatch_active_strategy_summary.csv` | Summary of active dispatch strategy over time. |
| `results/paper_comparison/stage7_comparison/formal2024_comparison_20260330_234957/dispatch_uniform_priority/dispatch_ewm_topsis_result.csv` | Dispatch strategy composite ranking from EWM+TOPSIS. |
| `results/paper_comparison/stage7_comparison/formal2024_comparison_20260330_234957/dispatch_uniform_priority/dispatch_indicator_weights.csv` | Indicator weights used in dispatch strategy scoring. |
| `results/paper_comparison/stage7_comparison/formal2024_comparison_20260330_234957/dispatch_uniform_priority/dispatch_model_comparison.csv` | SCUC/Stochastic/Robust model comparison metrics. |
| `results/paper_comparison/stage7_comparison/formal2024_comparison_20260330_234957/dispatch_uniform_priority/dispatch_optimization_report.json` | Stage7 dispatch optimization report. |
| `results/paper_comparison/stage7_comparison/formal2024_comparison_20260330_234957/dispatch_uniform_priority/dispatch_strategy_selection.csv` | Risk-context strategy switching record by time step. |
| `results/paper_comparison/stage7_comparison/formal2024_comparison_20260330_234957/dispatch_uniform_priority/line_flow.csv` | Line flow results from dispatch optimization. |
| `results/paper_comparison/stage7_comparison/formal2024_comparison_20260330_234957/dispatch_uniform_priority/robust_uc_first_stage_schedule.csv` | Robust UC first-stage schedule output. |
| `results/paper_comparison/stage7_comparison/formal2024_comparison_20260330_234957/dispatch_uniform_priority/robust_uc_scenario_summary.csv` | Robust UC scenario summary metrics. |
| `results/paper_comparison/stage7_comparison/formal2024_comparison_20260330_234957/dispatch_uniform_priority/robust_uc_worst_load_shedding.csv` | Worst-case load shedding under robust UC. |
| `results/paper_comparison/stage7_comparison/formal2024_comparison_20260330_234957/dispatch_uniform_priority/scuc_load_shedding.csv` | SCUC load shedding output table. |
| `results/paper_comparison/stage7_comparison/formal2024_comparison_20260330_234957/dispatch_uniform_priority/scuc_schedule.csv` | SCUC schedule output table. |
| `results/paper_comparison/stage7_comparison/formal2024_comparison_20260330_234957/dispatch_uniform_priority/stochastic_uc_expected_load_shedding.csv` | Expected load shedding under stochastic UC. |
| `results/paper_comparison/stage7_comparison/formal2024_comparison_20260330_234957/dispatch_uniform_priority/stochastic_uc_first_stage_schedule.csv` | Stochastic UC first-stage schedule output. |
| `results/paper_comparison/stage7_comparison/formal2024_comparison_20260330_234957/dispatch_uniform_priority/stochastic_uc_scenario_summary.csv` | Stochastic UC scenario summary metrics. |
| `results/paper_comparison/stage7_comparison/formal2024_comparison_20260330_234957/dispatch_weighted_priority/contextual_dispatch_hourly_cost.csv` | Context-aware hourly operational cost trace. |
| `results/paper_comparison/stage7_comparison/formal2024_comparison_20260330_234957/dispatch_weighted_priority/contextual_dispatch_load_shedding.csv` | Context-aware load shedding schedule. |
| `results/paper_comparison/stage7_comparison/formal2024_comparison_20260330_234957/dispatch_weighted_priority/contextual_dispatch_unit_schedule.csv` | Context-aware dispatch generation schedule. |
| `results/paper_comparison/stage7_comparison/formal2024_comparison_20260330_234957/dispatch_weighted_priority/dispatch_active_strategy_summary.csv` | Summary of active dispatch strategy over time. |
| `results/paper_comparison/stage7_comparison/formal2024_comparison_20260330_234957/dispatch_weighted_priority/dispatch_ewm_topsis_result.csv` | Dispatch strategy composite ranking from EWM+TOPSIS. |
| `results/paper_comparison/stage7_comparison/formal2024_comparison_20260330_234957/dispatch_weighted_priority/dispatch_indicator_weights.csv` | Indicator weights used in dispatch strategy scoring. |
| `results/paper_comparison/stage7_comparison/formal2024_comparison_20260330_234957/dispatch_weighted_priority/dispatch_model_comparison.csv` | SCUC/Stochastic/Robust model comparison metrics. |
| `results/paper_comparison/stage7_comparison/formal2024_comparison_20260330_234957/dispatch_weighted_priority/dispatch_optimization_report.json` | Stage7 dispatch optimization report. |
| `results/paper_comparison/stage7_comparison/formal2024_comparison_20260330_234957/dispatch_weighted_priority/dispatch_strategy_selection.csv` | Risk-context strategy switching record by time step. |
| `results/paper_comparison/stage7_comparison/formal2024_comparison_20260330_234957/dispatch_weighted_priority/line_flow.csv` | Line flow results from dispatch optimization. |
| `results/paper_comparison/stage7_comparison/formal2024_comparison_20260330_234957/dispatch_weighted_priority/robust_uc_first_stage_schedule.csv` | Robust UC first-stage schedule output. |
| `results/paper_comparison/stage7_comparison/formal2024_comparison_20260330_234957/dispatch_weighted_priority/robust_uc_scenario_summary.csv` | Robust UC scenario summary metrics. |
| `results/paper_comparison/stage7_comparison/formal2024_comparison_20260330_234957/dispatch_weighted_priority/robust_uc_worst_load_shedding.csv` | Worst-case load shedding under robust UC. |
| `results/paper_comparison/stage7_comparison/formal2024_comparison_20260330_234957/dispatch_weighted_priority/scuc_load_shedding.csv` | SCUC load shedding output table. |
| `results/paper_comparison/stage7_comparison/formal2024_comparison_20260330_234957/dispatch_weighted_priority/scuc_schedule.csv` | SCUC schedule output table. |
| `results/paper_comparison/stage7_comparison/formal2024_comparison_20260330_234957/dispatch_weighted_priority/stochastic_uc_expected_load_shedding.csv` | Expected load shedding under stochastic UC. |
| `results/paper_comparison/stage7_comparison/formal2024_comparison_20260330_234957/dispatch_weighted_priority/stochastic_uc_first_stage_schedule.csv` | Stochastic UC first-stage schedule output. |
| `results/paper_comparison/stage7_comparison/formal2024_comparison_20260330_234957/dispatch_weighted_priority/stochastic_uc_scenario_summary.csv` | Stochastic UC scenario summary metrics. |
| `results/paper_comparison/stage7_comparison/formal2024_comparison_20260330_234957/experiment_section_cn.md` | Chinese manuscript experiment section draft. |
| `results/paper_comparison/stage7_comparison/formal2024_comparison_20260330_234957/experiment_section.md` | English manuscript experiment section draft. |
| `results/paper_comparison/stage7_comparison/formal2024_comparison_20260330_234957/uniform_load_priority_profile.csv` | CSV table; columns: load_bus, priority_level, priority_weight, demand_share. |
| `results/pending_work.md` | Text/markdown notes; starts with: # Pending Work Notes |
| `results/resilience/resilience_metrics.csv` | CSV table; columns: policy, Priority, Robustness, Rapidity, Sustainability. |
| `results/resilience/topsis_ranking.csv` | CSV table; columns: policy, score, rank. |
| `results/scenario/component_failure_prob.csv` | CSV table; columns: line, hour, failure_prob. |
| `results/scenario/contingency_scenarios.csv` | Generated contingency scenarios summary table. |
| `results/scenario/wind_solar_scenarios.csv` | CSV table; columns: timestamp, wind_s0, wind_s1, wind_s2, wind_s3, solar_s0, solar_s1, solar_s2, .... |
| `results/spatiotemporal_contingency/formal2024_batts72h/contingency_report.json` | Stage3 spatiotemporal contingency generation report. |
| `results/spatiotemporal_contingency/formal2024_batts72h/contingency_tensor_c3po_ref.npy` | Contingency state tensor generated by C3PO reference method. |
| `results/spatiotemporal_contingency/formal2024_batts72h/contingency_tensor_trim_ref.npy` | Contingency state tensor generated by TRIM reference method. |
| `results/spatiotemporal_contingency/formal2024_batts72h/contingency_tensor_wang_mc.npy` | Contingency state tensor generated by Wang-style Monte Carlo. |
| `results/spatiotemporal_contingency/formal2024_batts72h/contingency_tensor_wang_qmc.npy` | Contingency state tensor generated by Wang-style quasi-Monte Carlo. |
| `results/spatiotemporal_contingency/formal2024_batts72h/line_probability_summary_c3po_ref.csv` | Per-line probability summary for C3PO reference method. |
| `results/spatiotemporal_contingency/formal2024_batts72h/line_probability_summary_trim_ref.csv` | Per-line probability summary for TRIM reference method. |
| `results/spatiotemporal_contingency/formal2024_batts72h/line_probability_summary_wang_mc.csv` | Per-line probability summary for Wang MC method. |
| `results/spatiotemporal_contingency/formal2024_batts72h/line_probability_summary_wang_qmc.csv` | Per-line probability summary for Wang QMC method. |
| `results/spatiotemporal_contingency/formal2024_batts72h/method_comparison.csv` | Cross-method comparison metrics table. |
| `results/spatiotemporal_contingency/formal2024_batts72h/state_summary_c3po_ref.csv` | State occurrence summary for C3PO reference method. |
| `results/spatiotemporal_contingency/formal2024_batts72h/state_summary_trim_ref.csv` | State occurrence summary for TRIM reference method. |
| `results/spatiotemporal_contingency/formal2024_batts72h/state_summary_wang_mc.csv` | State occurrence summary for Wang MC method. |
| `results/spatiotemporal_contingency/formal2024_batts72h/state_summary_wang_qmc.csv` | State occurrence summary for Wang QMC method. |
| `results/spatiotemporal_contingency/formal2024_schloemer72h/contingency_report.json` | Stage3 spatiotemporal contingency generation report. |
| `results/spatiotemporal_contingency/formal2024_schloemer72h/contingency_tensor_c3po_ref.npy` | Contingency state tensor generated by C3PO reference method. |
| `results/spatiotemporal_contingency/formal2024_schloemer72h/contingency_tensor_trim_ref.npy` | Contingency state tensor generated by TRIM reference method. |
| `results/spatiotemporal_contingency/formal2024_schloemer72h/contingency_tensor_wang_mc.npy` | Contingency state tensor generated by Wang-style Monte Carlo. |
| `results/spatiotemporal_contingency/formal2024_schloemer72h/contingency_tensor_wang_qmc.npy` | Contingency state tensor generated by Wang-style quasi-Monte Carlo. |
| `results/spatiotemporal_contingency/formal2024_schloemer72h/line_probability_summary_c3po_ref.csv` | Per-line probability summary for C3PO reference method. |
| `results/spatiotemporal_contingency/formal2024_schloemer72h/line_probability_summary_trim_ref.csv` | Per-line probability summary for TRIM reference method. |
| `results/spatiotemporal_contingency/formal2024_schloemer72h/line_probability_summary_wang_mc.csv` | Per-line probability summary for Wang MC method. |
| `results/spatiotemporal_contingency/formal2024_schloemer72h/line_probability_summary_wang_qmc.csv` | Per-line probability summary for Wang QMC method. |
| `results/spatiotemporal_contingency/formal2024_schloemer72h/method_comparison.csv` | Cross-method comparison metrics table. |
| `results/spatiotemporal_contingency/formal2024_schloemer72h/state_summary_c3po_ref.csv` | State occurrence summary for C3PO reference method. |
| `results/spatiotemporal_contingency/formal2024_schloemer72h/state_summary_trim_ref.csv` | State occurrence summary for TRIM reference method. |
| `results/spatiotemporal_contingency/formal2024_schloemer72h/state_summary_wang_mc.csv` | State occurrence summary for Wang MC method. |
| `results/spatiotemporal_contingency/formal2024_schloemer72h/state_summary_wang_qmc.csv` | State occurrence summary for Wang QMC method. |
| `results/spatiotemporal_contingency/g60_n75_wangqmc/contingency_report.json` | Stage3 spatiotemporal contingency generation report. |
| `results/spatiotemporal_contingency/g60_n75_wangqmc/contingency_scenarios_wang_qmc.csv` | CSV table; columns: scenario, scenario_id, timestamp, failed_lines, outage_line_count, disconnected_load_count, probability, method. |
| `results/spatiotemporal_contingency/g60_n75_wangqmc/contingency_scenarios.csv` | Generated contingency scenarios summary table. |
| `results/spatiotemporal_contingency/g60_n75_wangqmc/contingency_tensor_wang_qmc.npy` | Contingency state tensor generated by Wang-style quasi-Monte Carlo. |
| `results/spatiotemporal_contingency/g60_n75_wangqmc/line_probability_summary_wang_qmc.csv` | Per-line probability summary for Wang QMC method. |
| `results/spatiotemporal_contingency/g60_n75_wangqmc/method_comparison.csv` | Cross-method comparison metrics table. |
| `results/spatiotemporal_contingency/g60_n75_wangqmc/state_summary_wang_qmc.csv` | State occurrence summary for Wang QMC method. |
| `results/spatiotemporal_contingency/ieee118_n60_wangqmc/contingency_report.json` | Stage3 spatiotemporal contingency generation report. |
| `results/spatiotemporal_contingency/ieee118_n60_wangqmc/contingency_scenarios_wang_qmc.csv` | CSV table; columns: scenario, scenario_id, timestamp, failed_lines, outage_line_count, disconnected_load_count, probability, method. |
| `results/spatiotemporal_contingency/ieee118_n60_wangqmc/contingency_scenarios.csv` | Generated contingency scenarios summary table. |
| `results/spatiotemporal_contingency/ieee118_n60_wangqmc/contingency_tensor_wang_qmc.npy` | Contingency state tensor generated by Wang-style quasi-Monte Carlo. |
| `results/spatiotemporal_contingency/ieee118_n60_wangqmc/line_probability_summary_wang_qmc.csv` | Per-line probability summary for Wang QMC method. |
| `results/spatiotemporal_contingency/ieee118_n60_wangqmc/method_comparison.csv` | Cross-method comparison metrics table. |
| `results/spatiotemporal_contingency/ieee118_n60_wangqmc/state_summary_wang_qmc.csv` | State occurrence summary for Wang QMC method. |
| `results/summary/experiment_summary.json` | JSON object; top keys: framework, mode, run_root, timestamp, selected_chain, best_candidate, standard_outputs. |
| `results/summary/indicator_table.csv` | Indicator matrix for resilience evaluation. |
| `results/timepoint_snapshots_formal2024_20240901_0000_1700/20240901_000000/dispatch_generation_schedule.csv` | CSV table; columns: timestamp, BOOSTER, EMG_1, EMG_2, EMG_3, TH0. |
| `results/timepoint_snapshots_formal2024_20240901_0000_1700/20240901_000000/dispatch_line_flow_full.csv` | CSV table; columns: timestamp, line_id, from_bus, to_bus, flow_mw, limit_mw, loading, overload_flag, .... |
| `results/timepoint_snapshots_formal2024_20240901_0000_1700/20240901_000000/dispatch_load_shedding_full.csv` | CSV table; columns: timestamp, node, load_type, shed_MW. |
| `results/timepoint_snapshots_formal2024_20240901_0000_1700/20240901_000000/dispatch_reserve_schedule.csv` | CSV table; columns: timestamp, reserve_up, reserve_down. |
| `results/timepoint_snapshots_formal2024_20240901_0000_1700/20240901_000000/scenario_component_failure_prob_full.csv` | CSV table; columns: timestamp, model, line_id, from_bus, to_bus, v_surface_ms, p_tower, p_span, .... |
| `results/timepoint_snapshots_formal2024_20240901_0000_1700/20240901_000000/scenario_contingency_scenarios_full.csv` | CSV table; columns: scenario, scenario_id, timestamp, failed_lines, outage_line_count, disconnected_load_count, probability, method. |
| `results/timepoint_snapshots_formal2024_20240901_0000_1700/20240901_000000/warning_dispatch_strategy_selection.csv` | CSV table; columns: timestamp, hour_index, hourly_line_risk, hourly_uncertainty, global_expected_nk_fail_lines, global_max_critical_outage_prob, global_high_line_ratio, selected_strategy, .... |
| `results/timepoint_snapshots_formal2024_20240901_0000_1700/20240901_000000/warning_hourly_line_risk_long.csv` | CSV table; columns: timestamp, line_id, risk_prob. |
| `results/timepoint_snapshots_formal2024_20240901_0000_1700/20240901_170000/dispatch_generation_schedule.csv` | CSV table; columns: timestamp, BOOSTER, EMG_1, EMG_2, EMG_3, TH0. |
| `results/timepoint_snapshots_formal2024_20240901_0000_1700/20240901_170000/dispatch_line_flow_full.csv` | CSV table; columns: timestamp, line_id, from_bus, to_bus, flow_mw, limit_mw, loading, overload_flag, .... |
| `results/timepoint_snapshots_formal2024_20240901_0000_1700/20240901_170000/dispatch_load_shedding_full.csv` | CSV table; columns: timestamp, node, load_type, shed_MW. |
| `results/timepoint_snapshots_formal2024_20240901_0000_1700/20240901_170000/dispatch_reserve_schedule.csv` | CSV table; columns: timestamp, reserve_up, reserve_down. |
| `results/timepoint_snapshots_formal2024_20240901_0000_1700/20240901_170000/scenario_component_failure_prob_full.csv` | CSV table; columns: timestamp, model, line_id, from_bus, to_bus, v_surface_ms, p_tower, p_span, .... |
| `results/timepoint_snapshots_formal2024_20240901_0000_1700/20240901_170000/scenario_contingency_scenarios_full.csv` | CSV table; columns: scenario, scenario_id, timestamp, failed_lines, outage_line_count, disconnected_load_count, probability, method. |
| `results/timepoint_snapshots_formal2024_20240901_0000_1700/20240901_170000/warning_dispatch_strategy_selection.csv` | CSV table; columns: timestamp, hour_index, hourly_line_risk, hourly_uncertainty, global_expected_nk_fail_lines, global_max_critical_outage_prob, global_high_line_ratio, selected_strategy, .... |
| `results/timepoint_snapshots_formal2024_20240901_0000_1700/20240901_170000/warning_hourly_line_risk_long.csv` | CSV table; columns: timestamp, line_id, risk_prob. |
| `results/timepoint_snapshots_formal2024_20240901_0000_1700/README.md` | Readme/instructions for the directory. |
| `results/timepoint_snapshots_formal2024_20240901_0000_1700/timepoint_snapshot_summary.csv` | Summary metrics across exported timepoint snapshots. |
| `results/timepoint_snapshots_formal2024_20240901_0000_1700/timepoint_snapshot_summary.json` | JSON summary for exported timepoint snapshots. |
| `results/warning/critical_load_risk.csv` | Critical load risk indicators over horizon. |
| `results/warning/line_risk_prediction.csv` | Predicted line-level risk probabilities and labels. |
| `results/warning/nk_failure_risk.csv` | N-k style system-level failure risk indicators. |
| `results/wind_pv_uncertainty/demo2020/history_series.csv` | Historical time series used as model input. |
| `results/wind_pv_uncertainty/demo2020/scenario_probabilities.csv` | Probability assigned to each generated scenario. |
| `results/wind_pv_uncertainty/demo2020/typical_scenarios.npy` | NumPy tensor of representative scenarios. |
| `results/wind_pv_uncertainty/demo2020/uncertainty_report.json` | Stage1 uncertainty modeling report and metrics. |
| `results/wind_pv_uncertainty/formal2024/history_series.csv` | Historical time series used as model input. |
| `results/wind_pv_uncertainty/formal2024/scenario_probabilities.csv` | Probability assigned to each generated scenario. |
| `results/wind_pv_uncertainty/formal2024/typical_scenarios.npy` | NumPy tensor of representative scenarios. |
| `results/wind_pv_uncertainty/formal2024/uncertainty_report.json` | Stage1 uncertainty modeling report and metrics. |

### scripts

| File | Rough Content |
|---|---|
| `scripts/__pycache__/build_ieee_subgrid.cpython-311.pyc` | Compiled Python bytecode cache artifact. |
| `scripts/__pycache__/dispatch_optimization_module.cpython-311.pyc` | Compiled Python bytecode cache artifact. |
| `scripts/__pycache__/export_standard_results.cpython-311.pyc` | Compiled Python bytecode cache artifact. |
| `scripts/__pycache__/generate_scaled_topology.cpython-311.pyc` | Compiled Python bytecode cache artifact. |
| `scripts/__pycache__/gnn_warning_module.cpython-311.pyc` | Compiled Python bytecode cache artifact. |
| `scripts/__pycache__/gridagent_framework.cpython-311.pyc` | Compiled Python bytecode cache artifact. |
| `scripts/__pycache__/run_paper_comparison_experiment.cpython-311.pyc` | Compiled Python bytecode cache artifact. |
| `scripts/__pycache__/run_warning_scale_experiments.cpython-311.pyc` | Compiled Python bytecode cache artifact. |
| `scripts/__pycache__/spatiotemporal_contingency_generator.cpython-311.pyc` | Compiled Python bytecode cache artifact. |
| `scripts/analyze_stage123_results.py` | Python module/script; starts with: """Detailed analysis of Stage1-3 comparison results""" |
| `scripts/build_dataset.py` | Python module/script; key symbols: PipelineArtifacts, sanitize_column_name, load_config. |
| `scripts/build_ieee_subgrid.py` | Python module/script; key symbols: project_root, parse_args, get_case_network. |
| `scripts/component_failure_probability.py` | Python module/script; key symbols: TyphoonState, LineAsset, mid_lat. |
| `scripts/dataset_config.example.json` | JSON object; top keys: region, timezone, start, end, freq, raw_dirs, processed_dir, final_dir, .... |
| `scripts/dataset_config.formal_guangdong_2024.json` | JSON object; top keys: region, timezone, start, end, freq, raw_dirs, processed_dir, final_dir, .... |
| `scripts/dispatch_optimization_module.py` | Python module/script; key symbols: UCUnit, UCLine, UCInputs. |
| `scripts/download_data.py` | Python module/script; key symbols: load_config, resolve_env_template, ensure_parent_folder. |
| `scripts/export_standard_results.py` | Python module/script; key symbols: project_root, read_json, ensure_dir. |
| `scripts/generate_mock_data.py` | Python module/script; key symbols: load_config, ensure_dirs, build_time_index. |
| `scripts/generate_scaled_topology.py` | Python module/script; key symbols: project_root, load_json, dump_json. |
| `scripts/gnn_ablation_experiment.py` | Python module/script; key symbols: ExperimentConfig, ExperimentResult, compute_risk_weight_tensor. |
| `scripts/gnn_models/__init__.py` | Python module/script; starts with: """ |
| `scripts/gnn_models/__pycache__/__init__.cpython-311.pyc` | Compiled Python bytecode cache artifact. |
| `scripts/gnn_models/__pycache__/base_model.cpython-311.pyc` | Compiled Python bytecode cache artifact. |
| `scripts/gnn_models/__pycache__/baseline_gnn.cpython-311.pyc` | Compiled Python bytecode cache artifact. |
| `scripts/gnn_models/__pycache__/gat.cpython-311.pyc` | Compiled Python bytecode cache artifact. |
| `scripts/gnn_models/__pycache__/gcn.cpython-311.pyc` | Compiled Python bytecode cache artifact. |
| `scripts/gnn_models/__pycache__/graphsage.cpython-311.pyc` | Compiled Python bytecode cache artifact. |
| `scripts/gnn_models/__pycache__/metapath_v1.cpython-311.pyc` | Compiled Python bytecode cache artifact. |
| `scripts/gnn_models/__pycache__/mlp.cpython-311.pyc` | Compiled Python bytecode cache artifact. |
| `scripts/gnn_models/__pycache__/stgcn.cpython-311.pyc` | Compiled Python bytecode cache artifact. |
| `scripts/gnn_models/base_model.py` | Python module/script; key symbols: BaseGNNModel, __init__, forward. |
| `scripts/gnn_models/baseline_gnn.py` | Python module/script; key symbols: GraphMessageLayer, __init__, forward. |
| `scripts/gnn_models/gat.py` | Python module/script; key symbols: GraphAttentionLayer, __init__, reset_parameters. |
| `scripts/gnn_models/gcn.py` | Python module/script; key symbols: GCNModel, __init__, _build_adjacency. |
| `scripts/gnn_models/graphsage.py` | Python module/script; key symbols: GraphSAGEModel, __init__, _aggregate_neighbors. |
| `scripts/gnn_models/metapath_v1.py` | Python module/script; key symbols: GraphMessageLayer, __init__, forward. |
| `scripts/gnn_models/mlp.py` | Python module/script; key symbols: MLPModel, __init__, forward. |
| `scripts/gnn_models/stgcn.py` | Python module/script; key symbols: TemporalConvLayer, __init__, forward. |
| `scripts/gnn_warning_module.py` | Python module/script; key symbols: WarningDataset, project_root, parse_optional_float. |
| `scripts/gridagent_framework.py` | Python module/script; key symbols: project_root, resolve_path, run_cmd. |
| `scripts/legacy/run_matpower_resilience_batch.m` | MATLAB script; starts with: function run_matpower_resilience_batch(input_mat, output_mat) |
| `scripts/legacy/typhoon_grid_resilience_demo.py` | Python module/script; key symbols: TyphoonState, LineAsset, mid_lat. |
| `scripts/load_prioritization_scheduling.py` | Python module/script; key symbols: DispatchableGenerator, ScenarioInputs, project_root. |
| `scripts/module_sensitivity_analysis.py` | Python module/script; key symbols: project_root, run_cmd, ewm_topsis. |
| `scripts/multi_criteria_resilience_assessment.py` | Python module/script; key symbols: project_root, ensure_columns, calc_priority_indicator. |
| `scripts/multiscenario_fusion_experiment.py` | Python module/script; key symbols: WindPVVariant, LoadScenario, project_root. |
| `scripts/multiscenario_fusion_run.py` | Python module/script; key symbols: project_root, resolve_path, run_cmd. |
| `scripts/prepare_formal_sources.py` | Python module/script; key symbols: load_config, build_time_index, to_plain_timestamp_strings. |
| `scripts/run_end_to_end_resilience.py` | Python module/script; key symbols: project_root, run_cmd, parse_args. |
| `scripts/run_paper_comparison_experiment.py` | Python module/script; key symbols: project_root, run_cmd, read_json. |
| `scripts/run_warning_scale_experiments.py` | Python module/script; key symbols: project_root, parse_int_list, parse_float_list. |
| `scripts/spatiotemporal_contingency_generator.py` | Python module/script; key symbols: FailureInput, project_root, parse_optional_float. |
| `scripts/stage1_method_comparison.py` | Python module/script; key symbols: project_root, DatasetSpec, default_dataset_specs. |
| `scripts/stage123_method_comparison.py` | Python module/script; key symbols: project_root, ensure_dir, run_shell_cmd. |
| `scripts/wind_pv_uncertainty_modeling.py` | Python module/script; key symbols: DatasetSpec, project_root, default_dataset_specs. |

### tmp_DPGMN_text.txt

| File | Rough Content |
|---|---|
| `tmp_DPGMN_text.txt` | Text/markdown notes; starts with: ===== PAGE 1 ===== |

### tmp_gnn_warning_text.txt

| File | Rough Content |
|---|---|
| `tmp_gnn_warning_text.txt` | Text/markdown notes; starts with: ===== PAGE 1 ===== |

### tmp_H2DGL_pages5_8.txt

| File | Rough Content |
|---|---|
| `tmp_H2DGL_pages5_8.txt` | Text/markdown notes; starts with: ===== PAGE 5 ===== |

### tmp_load_priority_dispatch_opt.txt

| File | Rough Content |
|---|---|
| `tmp_load_priority_dispatch_opt.txt` | Text/markdown notes; starts with: Journal of Electric Power Science and Technology Journal of Electric Power Science and Technology |

### tmp_script_api_summary.json

| File | Rough Content |
|---|---|
| `tmp_script_api_summary.json` | JSON object; top keys: build_dataset.py, build_ieee_subgrid.py, component_failure_probability.py, dispatch_optimization_module.py, download_data.py, export_standard_results.py, generate_mock_data.py, generate_scaled_topology.py, .... |

### tmp_typhoon_wind_field_text.txt

| File | Rough Content |
|---|---|
| `tmp_typhoon_wind_field_text.txt` | Text/markdown notes; starts with: ===== PAGE 1 ===== |

