# 引言初稿（中文）

## 1 引言

极端天气正在持续加剧电力系统运行中的时空不确定性与级联风险。在高比例新能源接入场景下，风电和光伏出力波动会改变线路潮流分布，天气驱动的元件脆弱性又会进一步放大线路故障传播的可能性，使得电网运行状态呈现明显的时变性、耦合性和结构依赖性 [1]。对于调度与韧性分析而言，线路级风险并不是一个可有可无的附加指标，而是连接故障传播分析与运行决策的重要中间量：如果能够在多源时空背景下提前刻画未来线路风险，就有可能更有效地支撑后续的告警、策略切换和关键负荷保障。

尽管线路风险预测具有重要意义，现有方法通常仍局限于较窄的信息视角。部分研究主要依赖局部天气特征或静态拓扑属性来判断线路失效概率，难以反映新能源不确定性和时空故障传播的联合作用 [1]；另一部分关于级联故障的图建模研究则表明，故障传播往往并不严格受限于物理邻接关系，而更适合通过交互图或扩散图进行表达 [2,3]。与此同时，近年来基于图神经网络的电网运行风险分析方法显示出良好的预测潜力，但其输入通常以单一图特征或单一步骤的运行状态为主，缺少对故障传播上下文和运行场景背景的统一刻画 [4,5]。对于极端天气下的电网风险分析，这种割裂式建模会带来两个问题。首先，线路级预测结果容易脱离真实运行背景，难以体现“某条线路为什么在当前场景下变得更危险”。其次，即使模型能够输出逐线路风险分数，这些分数也常常缺少统一的结构化组织方式，难以被下游调度与韧性分析模块直接消费。

从更广义的数据分析链路角度看，问题的关键并不只是“是否能把风险预测得更准”，而是如何将新能源场景、不确定失效先验、时空故障传播上下文和拓扑语义统一组织为面向线路级风险预测的输入表示，并进一步将预测结果转化为可服务于下游决策的结构化风险摘要。也就是说，本文关注的核心任务并非单一的故障概率估计或单一的调度优化，而是**线路级时空风险预测**：给定多源时空运行数据、网络拓扑以及故障传播上下文，如何构建统一的线路级风险表示，预测未来线路风险，并验证该预测结果对下游调度与韧性分析是否真正有用。这里的新能源场景背景并非附属信息，而是因为场景压缩与不确定性表示已被证明是现代电力系统规划和运行分析中的关键支撑环节 [6,7]。

围绕这一任务，本文提出一个风险感知图分析框架。该框架将来自多个阶段的上下文信息统一到线路级风险表示中：首先，从年度风光负荷时序中构造代表性不确定场景，作为线路风险分析的运行背景；其次，基于极端天气脆弱性建模生成线路失效概率先验，并进一步构造时空故障传播张量，作为风险传播上下文；随后，在网络拓扑之上整合新能源场景、失效先验、故障传播上下文和结构语义，形成统一的线路级图输入；最后，利用风险感知图模型预测未来线路风险，并将结果进一步组织为结构化风险摘要，以供下游调度与韧性分析模块直接消费。这里对故障传播上下文的引入，与近期将级联故障视为图扩散过程来学习和预测的思路是一致的 [3]。

本文采用广东省 2024 年风光负荷时序数据和 IEEE 118 节点全网拓扑作为实验对象，构建并验证了一条从场景背景、失效先验、故障传播上下文到线路级风险预测、再到调度与韧性分析的完整实验链路。在这条链路中，线路级时空风险预测是核心任务，而场景生成、故障场景构造和下游调度模块分别承担背景构建、风险上下文构造和任务价值验证的角色。与将所有阶段并列为同等主角的写法不同，本文将重点集中在线路级风险预测这一核心问题上，并以此重新组织多阶段输入与输出关系。总体上，这一思路与近年来面向运行风险评估的 GNN surrogate 和 evolving-topology 风险分析研究形成互补：前者强调快速近似风险量化，后者强调在动态图条件下提取风险表示，而本文进一步强调将多阶段上下文组织到统一线路级输入中 [4,5,8]。

与传统只关注某一类输入特征或某一个局部模块性能的工作相比，本文的区别主要在于以下三个方面。第一，本文将新能源不确定场景、失效先验与故障传播上下文统一组织为线路级风险输入表示，使风险预测不再依赖单一局部特征，而能够反映更完整的运行背景。第二，本文采用图分析模型来建模线路之间的结构依赖和风险传播关联，使预测结果不仅具有逐线路刻画能力，也具有对网络结构上下文的响应能力。第三，本文并不将预测结果停留在单纯的误差评估层面，而是将其进一步转化为结构化风险摘要，并通过下游调度与韧性分析任务验证这些摘要是否具有真实的决策支持价值。

基于上述思路，本文的主要贡献可概括如下：

1. **提出统一的线路级时空风险表示。**  
   本文将新能源不确定场景、元件失效概率、时空故障传播上下文和拓扑语义整合为统一的线路级输入表示，为极端天气下的线路风险预测提供更完整的上下文背景。

2. **提出风险传播上下文增强的图风险预测框架。**  
   本文在统一表示之上构建风险感知图分析模型，对未来线路风险进行预测，并显式利用结构依赖和时空风险上下文提升预测能力。

3. **设计面向下游任务的结构化风险摘要接口。**  
   本文将线路级预测结果进一步组织为可被告警、调度与韧性分析模块直接消费的风险摘要，从而使风险预测结果能够服务于后续决策流程。

4. **在真实年度时序与全网拓扑上验证该任务的实用价值。**  
   基于广东 2024 年时序数据与 IEEE 118 全节点拓扑，本文验证了线路级时空风险预测不仅能获得优于基线的预测效果，而且能够为下游调度与韧性分析提供有效支持。

本文其余部分组织如下。第 2 节定义本文涉及的核心输入、线路级风险表示与任务目标；第 3 节给出整体框架概览；第 4 节介绍线路级风险表示构造过程；第 5 节介绍风险感知图预测模型；第 6 节介绍结构化风险摘要及其下游接口；第 7 节给出实验评估；第 8 节综述相关工作；第 9 节讨论当前方法的限制与改进方向；第 10 节总结全文。

---

## 引言参考文献（草稿）

[1] Panteli, M., Pickering, C., Wilkinson, S., Dawson, R., and Mancarella, P. *Power System Resilience to Extreme Weather: Fragility Modeling, Probabilistic Impact Assessment, and Adaptation Measures*. IEEE Transactions on Power Systems, 2017. [链接](https://eprints.ncl.ac.uk/229241)

[2] Guo, C., and Xie, L. *Interaction Graphs for Cascading Failure Analysis in Power Grids: A Survey*. arXiv, 2019. [链接](https://arxiv.org/abs/1911.00475)

[3] Xiang, B., Cautis, B., Xiao, X., Mula, O., Niyato, D., and Lakshmanan, L. V. S. *Predicting Cascading Failures with a Hyperparametric Diffusion Model*. KDD, 2024. [链接](https://doi.org/10.1145/3637528.3672048)

[4] Marot, A., Rozemberczki, B., Chakraborty, S., et al. *Graph neural networks for power grid operational risk assessment under evolving grid topology*. arXiv, 2024. [链接](https://arxiv.org/abs/2405.07343)

[5] Donnot, B., Marot, A., and Venzke, A. *Power grid operational risk assessment using graph neural network surrogates*. arXiv, 2023. [链接](https://arxiv.org/abs/2311.12309)

[6] Chen, J., Song, Z., Zhang, Y., and Ouyang, H. *A review of scenario analysis methods in planning and operation of modern power systems: Methodologies, applications, and challenges*. Electric Power Systems Research, 2022. [链接](https://www.sciencedirect.com/science/article/abs/pii/S0378779621007033)

[7] Huang, Y., Wang, J., and Zeng, B. *Planning of distributed renewable energy systems under uncertainty based on statistical machine learning*. Protection and Control of Modern Power Systems, 2022. [链接](https://link.springer.com/article/10.1186/s41601-022-00262-x)

[8] Donnot, B., Marot, A., and Venzke, A. *Operational risk quantification of power grids using graph neural network surrogates of the DC OPF*. arXiv, 2023. [链接](https://arxiv.org/abs/2311.03661)
