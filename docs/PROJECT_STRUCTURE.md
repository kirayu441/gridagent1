# Project Structure (Cleaned)

- Updated at: 2026-03-10
- Scope: current retained project files after cleanup (excluding internal `.git` files).

## Top Level
```text
gridagent1
├── .git
├── configs
├── data_final
├── docs
├── results
├── scripts
└── requirements-dataset.txt
```

## File Descriptions

### Root
| File | Description |
|---|---|
| `requirements-dataset.txt` | Python dependencies for dataset download and preprocessing pipeline. |

### configs/
| File | Description |
|---|---|
| `configs/gridagent_framework.formal2024.json` | Main config for unified GridAgent workflow on `formal2024` dataset. |
| `configs/multiscenario_fusion.formal2024.json` | Config for multi-scenario fusion experiment and strategy comparison. |

### data_final/
| File | Description |
|---|---|
| `data_final/aligned_merged.csv` | Aligned weather-generation-load merged time series (demo root copy). |
| `data_final/DPGMM_input.csv` | Input features for Wind-PV uncertainty modeling (DPGMM). |
| `data_final/grid_topology.json` | Grid topology, buses/lines and static electrical parameters. |
| `data_final/integrity_report.json` | Data integrity and alignment check summary. |
| `data_final/TRIM_input.csv` | Prepared input table for TRIM/C3PO contingency generation. |

### data_final/formal_guangdong_2024/
| File | Description |
|---|---|
| `data_final/formal_guangdong_2024/aligned_merged.csv` | Formal 2024 aligned weather-generation-load merged series. |
| `data_final/formal_guangdong_2024/DPGMM_input.csv` | Formal 2024 DPGMM modeling input dataset. |
| `data_final/formal_guangdong_2024/grid_topology.json` | Formal 2024 grid topology and component metadata. |
| `data_final/formal_guangdong_2024/integrity_report.json` | Formal 2024 data quality/integrity validation report. |
| `data_final/formal_guangdong_2024/TRIM_input.csv` | Formal 2024 contingency module input table. |

### docs/
| File | Description |
|---|---|
| `docs/CLEANUP_LOG.md` | Cleanup actions, moved/deleted items, and rationale log. |
| `docs/DATASET_PIPELINE.md` | Data source, download, alignment and preprocessing instructions. |
| `docs/paper745.txt` | Working notes/excerpts for Wang et al. (2024) related methods. |
| `docs/PROJECT_STRUCTURE.md` | Simplified project structure with per-file descriptions. |
| `docs/PROJECT_TREE_FULL.txt` | Full filesystem tree snapshot kept for audit/reference. |

### scripts/
| File | Description |
|---|---|
| `scripts/build_dataset.py` | Build unified modeling dataset from prepared source files. |
| `scripts/component_failure_probability.py` | Compute line/tower failure probability using Batts/Schloemer + stress-strength. |
| `scripts/dataset_config.example.json` | Example dataset config template for custom environments. |
| `scripts/dataset_config.formal_guangdong_2024.json` | Concrete dataset config for formal Guangdong 2024 run. |
| `scripts/download_data.py` | Download external weather/power data (including Renewables.ninja). |
| `scripts/dispatch_optimization_module.py` | Context-aware dispatch module: SCUC/Stochastic/Robust are solved, then strategy is switched by risk/uncertainty context for operational output. |
| `scripts/generate_mock_data.py` | Generate demo/synthetic data for quick validation. |
| `scripts/gridagent_framework.py` | Unified orchestrator: uncertainty -> failure -> contingency -> scheduling -> resilience. |
| `scripts/load_prioritization_scheduling.py` | Load prioritization and pre-disaster dispatch/shedding optimization module. |
| `scripts/module_sensitivity_analysis.py` | Module-level influence and sensitivity analysis across pipeline outputs. |
| `scripts/multi_criteria_resilience_assessment.py` | EWM + TOPSIS based multi-criteria resilience scoring and ranking. |
| `scripts/multiscenario_fusion_experiment.py` | Build multi-scenario test design (env matrix + strategy pool). |
| `scripts/multiscenario_fusion_run.py` | Execute edge/cloud batch runs with checkpoint/progress reporting. |
| `scripts/prepare_formal_sources.py` | Prepare/clean/alignment utilities for formal source datasets. |
| `scripts/run_end_to_end_resilience.py` | End-to-end runner for full resilience workflow. |
| `scripts/spatiotemporal_contingency_generator.py` | Generate spatio-temporal contingency sets via MC/QMC and reference methods. |
| `scripts/wind_pv_uncertainty_modeling.py` | Wind-PV uncertainty modeling and typical scenario generation (DPGMM). |

### scripts/legacy/
| File | Description |
|---|---|
| `scripts/legacy/run_matpower_resilience_batch.m` | Legacy MATLAB batch script for MATPOWER-based resilience runs. |
| `scripts/legacy/typhoon_grid_resilience_demo.py` | Legacy demo script for typhoon-grid resilience simulation. |

### results/
| File | Description |
|---|---|
| `results/end_to_end_resilience_summary.json` | Consolidated summary of end-to-end workflow outputs. |
| `results/load_prioritization_paper_extracted.txt` | Extracted notes from load-prioritization reference paper. |
| `results/pending_work.md` | Pending tasks and known gaps to continue later. |

### results/component_failure_probability/formal2024/
| File | Description |
|---|---|
| `results/component_failure_probability/formal2024/failure_probability_report.json` | Formal report of component failure model assumptions and key statistics. |
| `results/component_failure_probability/formal2024/line_failure_timeseries_batts.csv` | Time-series line failure probabilities under Batts wind-field model. |
| `results/component_failure_probability/formal2024/line_failure_timeseries_schloemer.csv` | Time-series line failure probabilities under Schloemer wind-field model. |

### results/load_prioritization_scheduling/formal2024/
| File | Description |
|---|---|
| `results/load_prioritization_scheduling/formal2024/load_bus_priority_profile.csv` | Priority level/weights for each load bus used in optimization. |
| `results/load_prioritization_scheduling/formal2024/load_prioritization_report.json` | Scheduling optimization report and solution quality summary. |
| `results/load_prioritization_scheduling/formal2024/policy_comparison.csv` | Comparative metrics across scheduling/shedding policies. |
| `results/load_prioritization_scheduling/formal2024/pre_disaster_dispatch_schedule.csv` | Optimized pre-disaster generator dispatch schedule. |
| `results/load_prioritization_scheduling/formal2024/scenario_metrics.csv` | Scenario-level reliability/cost/curtailment metrics. |
| `results/load_prioritization_scheduling/formal2024/worst_scenario_shedding_detail.csv` | Detailed load-shedding actions in worst-case scenario. |

### results/module_sensitivity/formal2024/
| File | Description |
|---|---|
| `results/module_sensitivity/formal2024/indicator_ewm_weights.csv` | Entropy weight method (EWM) weights for resilience indicators. |
| `results/module_sensitivity/formal2024/module_influence_weights.csv` | Estimated contribution weights of each module to final resilience score. |
| `results/module_sensitivity/formal2024/module_level_summary.csv` | Module-level KPI summary table for sensitivity inspection. |
| `results/module_sensitivity/formal2024/sensitivity_report.json` | Full sensitivity analysis report and conclusions. |
| `results/module_sensitivity/formal2024/sensitivity_runs.csv` | Raw run-level records used for sensitivity analysis. |
| `results/module_sensitivity/formal2024/single_indicator_best_runs.csv` | Best-performing runs per single resilience indicator. |

### results/multi_criteria_resilience/formal2024/
| File | Description |
|---|---|
| `results/multi_criteria_resilience/formal2024/ewm_topsis_result.csv` | Final composite score and ranking from EWM+TOPSIS. |
| `results/multi_criteria_resilience/formal2024/indicator_table.csv` | Indicator matrix after normalization/standardization steps. |
| `results/multi_criteria_resilience/formal2024/multi_criteria_report.json` | Summary report for multi-criteria resilience evaluation. |
| `results/multi_criteria_resilience/formal2024/single_indicator_ranking.csv` | Ranking results when each indicator is evaluated independently. |

### results/multiscenario_fusion/phase1_design/
| File | Description |
|---|---|
| `results/multiscenario_fusion/phase1_design/env_matrix_full.csv` | Full Cartesian environment matrix (all intensity/wind/load combinations). |
| `results/multiscenario_fusion/phase1_design/env_matrix_sampled.csv` | Sampled environment subset for staged evaluation. |
| `results/multiscenario_fusion/phase1_design/experiment_manifest.json` | Experiment manifest defining stage/run mapping and parameters. |
| `results/multiscenario_fusion/phase1_design/experiment_manifest_cloud_top2.json` | Manifest for cloud stage focusing on top-2 strategies. |
| `results/multiscenario_fusion/phase1_design/load_scenarios.csv` | Candidate load scenario definitions for fusion tests. |
| `results/multiscenario_fusion/phase1_design/step6_final_delivery.md` | Final delivery note for phase-1 fusion test. |
| `results/multiscenario_fusion/phase1_design/step6_final_summary.json` | Structured final summary metrics for phase-1 fusion test. |
| `results/multiscenario_fusion/phase1_design/strategy_pool.csv` | Full strategy candidate pool before staged filtering. |
| `results/multiscenario_fusion/phase1_design/strategy_pool_top2_cloud.csv` | Selected top-2 strategies used in cloud comparison stage. |
| `results/multiscenario_fusion/phase1_design/wind_pv_variants.csv` | Wind/PV generation variant definitions for multi-scenario fusion. |

### results/multiscenario_fusion/phase1_design/cloud_eval_v1/
| File | Description |
|---|---|
| `results/multiscenario_fusion/phase1_design/cloud_eval_v1/fusion_environment_summary.csv` | Aggregated performance per environment under cloud evaluation. |
| `results/multiscenario_fusion/phase1_design/cloud_eval_v1/fusion_indicator_weights.csv` | Indicator weighting table used in fusion scoring. |
| `results/multiscenario_fusion/phase1_design/cloud_eval_v1/fusion_report.json` | Main cloud evaluation report with best strategy/run outcomes. |
| `results/multiscenario_fusion/phase1_design/cloud_eval_v1/fusion_runs.csv` | Run-level records for all cloud evaluation combinations. |
| `results/multiscenario_fusion/phase1_design/cloud_eval_v1/fusion_strategy_summary.csv` | Aggregated strategy ranking summary in cloud stage. |

### results/multiscenario_fusion/phase1_design/step4_analysis/
| File | Description |
|---|---|
| `results/multiscenario_fusion/phase1_design/step4_analysis/by_intensity_delta.csv` | Performance deltas between strategies by typhoon intensity group. |
| `results/multiscenario_fusion/phase1_design/step4_analysis/by_intensity_strategy_metrics.csv` | Strategy metrics grouped by intensity level. |
| `results/multiscenario_fusion/phase1_design/step4_analysis/by_intensity_winner.csv` | Winning strategy label for each intensity group. |
| `results/multiscenario_fusion/phase1_design/step4_analysis/by_load_scenario_delta.csv` | Strategy deltas grouped by load scenario. |
| `results/multiscenario_fusion/phase1_design/step4_analysis/by_load_scenario_strategy_metrics.csv` | Strategy metrics grouped by load scenario class. |
| `results/multiscenario_fusion/phase1_design/step4_analysis/by_load_scenario_winner.csv` | Winning strategy label for each load scenario class. |
| `results/multiscenario_fusion/phase1_design/step4_analysis/by_wind_variant_delta.csv` | Strategy deltas grouped by wind/PV variant. |
| `results/multiscenario_fusion/phase1_design/step4_analysis/by_wind_variant_strategy_metrics.csv` | Strategy metrics grouped by wind/PV variant. |
| `results/multiscenario_fusion/phase1_design/step4_analysis/by_wind_variant_winner.csv` | Winning strategy label for each wind/PV variant. |
| `results/multiscenario_fusion/phase1_design/step4_analysis/environment_risk_view.csv` | Risk-profile view for each environment setting. |
| `results/multiscenario_fusion/phase1_design/step4_analysis/global_strategy_summary.csv` | Global summary and ranking of strategies in step-4 analysis. |
| `results/multiscenario_fusion/phase1_design/step4_analysis/step4_report.json` | Step-4 stratified analysis report and key findings. |

### results/spatiotemporal_contingency/formal2024_batts72h/
| File | Description |
|---|---|
| `results/spatiotemporal_contingency/formal2024_batts72h/contingency_report.json` | Summary report for 72h Batts-based contingency generation. |
| `results/spatiotemporal_contingency/formal2024_batts72h/contingency_tensor_c3po_ref.npy` | Contingency state tensor generated by C3PO reference method. |
| `results/spatiotemporal_contingency/formal2024_batts72h/contingency_tensor_trim_ref.npy` | Contingency state tensor generated by TRIM reference method. |
| `results/spatiotemporal_contingency/formal2024_batts72h/contingency_tensor_wang_mc.npy` | Contingency state tensor generated by Wang-style Monte Carlo sampling. |
| `results/spatiotemporal_contingency/formal2024_batts72h/contingency_tensor_wang_qmc.npy` | Contingency state tensor generated by Wang-style quasi-Monte Carlo sampling. |
| `results/spatiotemporal_contingency/formal2024_batts72h/line_probability_summary_c3po_ref.csv` | Line failure probability summary (C3PO reference). |
| `results/spatiotemporal_contingency/formal2024_batts72h/line_probability_summary_trim_ref.csv` | Line failure probability summary (TRIM reference). |
| `results/spatiotemporal_contingency/formal2024_batts72h/line_probability_summary_wang_mc.csv` | Line failure probability summary (Wang MC). |
| `results/spatiotemporal_contingency/formal2024_batts72h/line_probability_summary_wang_qmc.csv` | Line failure probability summary (Wang QMC). |
| `results/spatiotemporal_contingency/formal2024_batts72h/method_comparison.csv` | Cross-method comparison table for contingency statistics. |
| `results/spatiotemporal_contingency/formal2024_batts72h/state_summary_c3po_ref.csv` | State occurrence summary (C3PO reference). |
| `results/spatiotemporal_contingency/formal2024_batts72h/state_summary_trim_ref.csv` | State occurrence summary (TRIM reference). |
| `results/spatiotemporal_contingency/formal2024_batts72h/state_summary_wang_mc.csv` | State occurrence summary (Wang MC). |
| `results/spatiotemporal_contingency/formal2024_batts72h/state_summary_wang_qmc.csv` | State occurrence summary (Wang QMC). |

### results/spatiotemporal_contingency/formal2024_schloemer72h/
| File | Description |
|---|---|
| `results/spatiotemporal_contingency/formal2024_schloemer72h/contingency_report.json` | Summary report for 72h Schloemer-based contingency generation. |
| `results/spatiotemporal_contingency/formal2024_schloemer72h/contingency_tensor_c3po_ref.npy` | Contingency state tensor generated by C3PO reference method. |
| `results/spatiotemporal_contingency/formal2024_schloemer72h/contingency_tensor_trim_ref.npy` | Contingency state tensor generated by TRIM reference method. |
| `results/spatiotemporal_contingency/formal2024_schloemer72h/contingency_tensor_wang_mc.npy` | Contingency state tensor generated by Wang-style Monte Carlo sampling. |
| `results/spatiotemporal_contingency/formal2024_schloemer72h/contingency_tensor_wang_qmc.npy` | Contingency state tensor generated by Wang-style quasi-Monte Carlo sampling. |
| `results/spatiotemporal_contingency/formal2024_schloemer72h/line_probability_summary_c3po_ref.csv` | Line failure probability summary (C3PO reference). |
| `results/spatiotemporal_contingency/formal2024_schloemer72h/line_probability_summary_trim_ref.csv` | Line failure probability summary (TRIM reference). |
| `results/spatiotemporal_contingency/formal2024_schloemer72h/line_probability_summary_wang_mc.csv` | Line failure probability summary (Wang MC). |
| `results/spatiotemporal_contingency/formal2024_schloemer72h/line_probability_summary_wang_qmc.csv` | Line failure probability summary (Wang QMC). |
| `results/spatiotemporal_contingency/formal2024_schloemer72h/method_comparison.csv` | Cross-method comparison table for contingency statistics. |
| `results/spatiotemporal_contingency/formal2024_schloemer72h/state_summary_c3po_ref.csv` | State occurrence summary (C3PO reference). |
| `results/spatiotemporal_contingency/formal2024_schloemer72h/state_summary_trim_ref.csv` | State occurrence summary (TRIM reference). |
| `results/spatiotemporal_contingency/formal2024_schloemer72h/state_summary_wang_mc.csv` | State occurrence summary (Wang MC). |
| `results/spatiotemporal_contingency/formal2024_schloemer72h/state_summary_wang_qmc.csv` | State occurrence summary (Wang QMC). |

### results/wind_pv_uncertainty/demo2020/
| File | Description |
|---|---|
| `results/wind_pv_uncertainty/demo2020/history_series.csv` | Historical input series used by uncertainty model (demo 2020). |
| `results/wind_pv_uncertainty/demo2020/scenario_probabilities.csv` | Probability of each generated typical wind/PV scenario (demo 2020). |
| `results/wind_pv_uncertainty/demo2020/typical_scenarios.npy` | Typical wind/PV scenario tensor output (demo 2020). |
| `results/wind_pv_uncertainty/demo2020/uncertainty_report.json` | Modeling report for demo 2020 uncertainty results. |

### results/wind_pv_uncertainty/formal2024/
| File | Description |
|---|---|
| `results/wind_pv_uncertainty/formal2024/history_series.csv` | Historical input series used by uncertainty model (formal 2024). |
| `results/wind_pv_uncertainty/formal2024/scenario_probabilities.csv` | Probability of each generated typical wind/PV scenario (formal 2024). |
| `results/wind_pv_uncertainty/formal2024/typical_scenarios.npy` | Typical wind/PV scenario tensor output (formal 2024). |
| `results/wind_pv_uncertainty/formal2024/uncertainty_report.json` | Modeling report for formal 2024 uncertainty results. |
