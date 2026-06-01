# scripts 目录说明

本目录用于存放论文投稿包中的核心原始脚本源码。当前按照“主实验链路脚本”和“数据构建与输入准备脚本”两层结构进行整理，便于将正式实验代码与数据准备代码分开管理。

## 一、主实验链路脚本

根目录下的脚本对应论文主流程中的各个阶段模块：

- `wind_pv_uncertainty_modeling.py`  
  Stage1 风光不确定性建模与典型场景生成脚本，用于生成后续调度与韧性分析所需的新能源场景。

- `component_failure_probability.py`  
  Stage2 元件失效概率建模脚本，用于结合天气或环境因子计算节点、线路等元件的故障概率。

- `spatiotemporal_contingency_generator.py`  
  Stage3 时空故障集生成脚本，用于基于 Stage2 的失效概率结果构造故障场景。

- `load_prioritization_scheduling.py`  
  Stage4 负荷优先级调度脚本，用于进行关键负荷和一般负荷的供电调度与策略分配。

- `multi_criteria_resilience_assessment.py`  
  Stage5 多指标韧性评估脚本，用于从恢复、供电、风险等多个角度汇总韧性指标。

- `gnn_warning_module.py`  
  Stage6 线路级 GNN 风险预警主脚本，用于训练和评估图神经网络预警模型。

- `dispatch_optimization_module.py`  
  Stage7 调度优化脚本，用于在多场景条件下进行资源分配和系统调度优化。

- `export_standard_results.py`  
  Stage8 标准化结果导出脚本，用于整理最终结果表、标准化输出和交付材料。

- `gridagent_framework.py`  
  总控脚本或统一串联脚本，用于将各阶段模块按流程进行调用与衔接。

## 二、Stage6 子模块脚本

`gnn_models/` 目录保存 Stage6 GNN 预警模型依赖的子模块：

- `__init__.py`：模块初始化文件。
- `base_model.py`：基础模型或公共层定义。
- `baseline_gnn.py`：基础 GNN Baseline 实现。
- `metapath_v1.py`：MetaPath V1 语义增强版本实现。

## 三、数据构建与输入准备脚本

`data_preparation/` 目录用于存放正式实验数据集的准备、清洗、构建和拓扑处理脚本：

- `prepare_formal_sources.py`  
  用于构建正式数据源的基础输入，尤其适合广东 2024 正式实验数据的源文件整理与对齐准备。

- `download_data.py`  
  用于下载或抓取外部原始数据，支持按配置文件拉取风光、负荷等数据源。

- `build_dataset.py`  
  数据集总构建脚本，用于读取多源输入、进行时间对齐、字段规范化，并输出正式实验所需的数据包。

- `build_ieee_subgrid.py`  
  用于从 Pandapower IEEE 标准算例中抽取指定节点规模的子电网，适合构建论文中的测试拓扑。

- `generate_scaled_topology.py`  
  用于在基础拓扑上进行扩展、平铺或比例化生成，以得到不同规模的实验电网拓扑。

## 四、数据构建配置文件

- `data_preparation/dataset_config.example.json`  
  示例数据构建配置文件，用于说明字段格式和原始数据目录组织方式。

- `data_preparation/dataset_config.formal_guangdong_2024.json`  
  广东 2024 正式实验数据构建配置文件，是当前正式数据集准备的重要配置入口。

## 五、当前整理原则

本目录当前采取“先全面收集、后逐步精简”的整理策略：

1. 根目录只保留 Stage1-Stage8 主实验链路的核心脚本；
2. 数据准备、拓扑构建和数据集配置统一放入 `data_preparation/`；
3. 暂不放入大量分析性、临时性或对比实验脚本，这些内容后续优先整理到 `compare/`、`docs/` 或 `stage_result/` 中；
4. 在论文最终提交前，再根据投稿需要进一步收缩为最小可复现脚本集合。

## 六、后续建议

后续可继续在本目录做两类补充：

1. 增加每个脚本的最小运行示例；
2. 增加统一入口说明，明确从 `data_preparation/` 到 Stage1-Stage8 的推荐执行顺序；
3. 若后续投稿包要求更细，可进一步把 `data_preparation/` 中的配置文件拆分到顶层 `configs/` 目录。
