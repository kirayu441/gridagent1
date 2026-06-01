# Project Core Index (Code/Config/Docs Only)

- Generated on: 2026-04-07
- Scope: code, config, docs, dashboard, manuscript files (excludes `results/`, `data_final/`, `.venv/`, caches).
- Total indexed files: 64

## Count by Top-Level

| Top-Level | Count |
|---|---:|
| `configs` | 4 |
| `dashboard` | 3 |
| `docs` | 16 |
| `paper` | 2 |
| `requirements-dataset.txt` | 1 |
| `scripts` | 38 |

## Core Inventory

| File | Approx Content |
|---|---|
| `configs/gridagent_framework.formal2024.json` | Main full-run config for formal2024 dataset (Stage1-Stage7). |
| `configs/gridagent_framework.formal2024.quicktest.json` | Lightweight quick-test config for formal2024 (shorter horizon and smaller settings). |
| `configs/gridagent_framework.ieee118_n60.metapath_opt124.json` | Main config for IEEE118_N60 + MetaPath optimization experiments. |
| `configs/multiscenario_fusion.formal2024.json` | Config for multi-scenario fusion design and strategy evaluation. |
| `dashboard/gridagent_dashboard.py` | Streamlit dashboard entrypoint; loads runs and renders pipeline/dispatch/resilience views. |
| `dashboard/README.md` | Dashboard usage guide and startup instructions. |
| `dashboard/requirements-visualization.txt` | Visualization-specific Python dependencies (Streamlit, plotting libs). |
| `docs/CLEANUP_LOG.md` | Cleanup history and rationale for file moves/deletions. |
| `docs/DATASET_PIPELINE.md` | Data pipeline documentation for weather/wind/PV/load preprocessing. |
| `docs/formal2024_fullrun_results_report.md` | Formal2024 baseline full-run result report. |
| `docs/GridAgent_Formal2024_Complete_Paper.md` | Long-form paper draft for GridAgent formal2024 study. |
| `docs/GridAgent_PaperStyle_Overview_Formal2024.md` | Paper-style project overview for external readers. |
| `docs/GridAgent_Visualization_User_Guide.md` | User guide for the visualization dashboard pages. |
| `docs/IEEE60_Node_Weather_Source.md` | Source notes for IEEE60 node weather data construction. |
| `docs/paper745.txt` | Reference excerpts/notes related to paper methods. |
| `docs/pipeline_chain_catalog_formal2024.csv` | Structured catalog of formal2024 pipeline chains and parameters. |
| `docs/pipeline_chain_catalog_formal2024.md` | Markdown catalog of formal2024 pipeline chains (24 chains). |
| `docs/PROJECT_CORE_INDEX_20260407.md` | Auto-generated core index (code/config/docs only, excludes results/data). |
| `docs/PROJECT_FILE_CATALOG_20260407.md` | Auto-generated full file catalog (all files including results). |
| `docs/PROJECT_FULL_SUMMARY_FOR_AI.md` | Comprehensive AI-facing context summary of the whole project. |
| `docs/PROJECT_STRUCTURE.md` | Project structure snapshot with file descriptions (older curated version). |
| `docs/PROJECT_TREE_FULL.txt` | Full filesystem tree snapshot for audit/reference. |
| `docs/RESULTS_CLEANUP_SUGGESTIONS_20260407.md` | Measured cleanup recommendations for results directory with reclaim estimates. |
| `paper/paper_experiment_ch/experiment_section_cn.md` | Chinese experiment section draft for manuscript. |
| `paper/paper_experiment_en/experiment_section.md` | English experiment section draft for manuscript. |
| `requirements-dataset.txt` | Python dependencies for dataset preparation and experiment pipeline. |
| `scripts/analyze_stage123_results.py` | Post-analysis helper for Stage1-3 comparison outputs. |
| `scripts/build_dataset.py` | Builds aligned modeling dataset from prepared raw sources. |
| `scripts/build_ieee_subgrid.py` | Builds IEEE subgrid topology variants (e.g., n60 extraction). |
| `scripts/component_failure_probability.py` | Stage2: computes line failure probabilities under typhoon wind field assumptions. |
| `scripts/dataset_config.example.json` | Template config for dataset building/downloading pipeline. |
| `scripts/dataset_config.formal_guangdong_2024.json` | Concrete dataset config for formal Guangdong 2024 sources. |
| `scripts/dispatch_optimization_module.py` | Stage7: SCUC/Stochastic/Robust dispatch + contextual strategy switching. |
| `scripts/download_data.py` | Downloads external weather/power data used by dataset pipeline. |
| `scripts/export_standard_results.py` | Exports framework outputs into standardized result folder layout. |
| `scripts/generate_mock_data.py` | Generates synthetic/mock data for local debugging and demos. |
| `scripts/generate_scaled_topology.py` | Creates scaled topology variants for size/structure experiments. |
| `scripts/gnn_ablation_experiment.py` | Runs Stage6 model ablation experiments across GNN variants. |
| `scripts/gnn_models/__init__.py` | Model registry exports for Stage6 GNN architectures. |
| `scripts/gnn_models/base_model.py` | Base model utilities/common blocks for warning models. |
| `scripts/gnn_models/baseline_gnn.py` | Baseline GNN architecture for line-risk prediction. |
| `scripts/gnn_models/gat.py` | Graph Attention Network variant for Stage6 ablation. |
| `scripts/gnn_models/gcn.py` | Graph Convolutional Network variant for Stage6 ablation. |
| `scripts/gnn_models/graphsage.py` | GraphSAGE variant for Stage6 ablation. |
| `scripts/gnn_models/metapath_v1.py` | MetaPath V1 semantic-enhanced warning model. |
| `scripts/gnn_models/mlp.py` | MLP baseline variant for non-graph comparison. |
| `scripts/gnn_models/stgcn.py` | Spatiotemporal GCN-style warning variant. |
| `scripts/gnn_warning_module.py` | Stage6: line-risk early warning with baseline GNN and MetaPath V1. |
| `scripts/gridagent_framework.py` | Main Stage1-Stage7 orchestrator for end-to-end GridAgent runs. |
| `scripts/legacy/run_matpower_resilience_batch.m` | Legacy MATLAB batch script for MATPOWER resilience experiments. |
| `scripts/legacy/typhoon_grid_resilience_demo.py` | Legacy typhoon-grid resilience demo script. |
| `scripts/load_prioritization_scheduling.py` | Stage4: load prioritization and pre-disaster scheduling optimization. |
| `scripts/module_sensitivity_analysis.py` | Sensitivity analysis across modules and indicator contributions. |
| `scripts/multi_criteria_resilience_assessment.py` | Stage5: EWM+TOPSIS multi-criteria resilience assessment. |
| `scripts/multiscenario_fusion_experiment.py` | Builds multi-scenario fusion experiment design matrices and manifests. |
| `scripts/multiscenario_fusion_run.py` | Executes multi-scenario fusion experiment batches. |
| `scripts/prepare_formal_sources.py` | Prepares and aligns formal source files into pipeline-ready tables. |
| `scripts/run_end_to_end_resilience.py` | Convenience runner for end-to-end resilience workflow. |
| `scripts/run_paper_comparison_experiment.py` | Runs paper-table comparison experiments and outputs manuscript tables. |
| `scripts/run_warning_scale_experiments.py` | Runs warning-module scaling experiments across settings. |
| `scripts/spatiotemporal_contingency_generator.py` | Stage3: generates spatiotemporal contingency tensors/scenarios. |
| `scripts/stage1_method_comparison.py` | Compares Stage1 uncertainty methods (DPGMM/LSTM/ARIMA/Copula, etc.). |
| `scripts/stage123_method_comparison.py` | Joint comparison pipeline for Stage1-3 method combinations. |
| `scripts/wind_pv_uncertainty_modeling.py` | Stage1: wind/PV uncertainty modeling and typical scenario generation. |
