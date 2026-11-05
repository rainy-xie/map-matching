# 毕业论文参考文献目录

更新于2026年11月4日。文献文件统计沿用2026年10月27日记录：已下载14份PDF，共237个物理PDF页，约51.0 MiB。其中11篇论文或综述、1个教材章节、1份制图规范，以及1份教程勘误。

建议从[阅读导引](00_阅读导引.md)开始；[BibTeX引用库](references.bib)可用于导入参考文献工具；[下载与阅读总清单](download-manifest.json)记录来源、版本、实际阅读深度和校验结果。

截至2026年11月4日，学生已借助ChatGPT完成Newson、Behr、Ma和Albert四篇核心文献的第一轮重点阅读，并整理为[阅读笔记](02_阅读笔记.md)。这是面向项目所需部分的阅读理解，不表示全篇通读、逐式推导或算法复现。下文各条“资料准备阅读核查”记录此前整理材料时对原文的核查范围，不代表学生已逐篇学完其余文献。

下一辅导起点是[四篇文献串联与课题设计](03_四篇文献串联与课题设计.md)，用同一个小例子横向说明空间表示、候选、观测、转移和评价，再按问题查ISOM、LaValle等工具资料。研究假设仍待验证，真实GPS与独立位置参照仍需取得；已有合成原型的证据与边界见[研究进度与接力说明](../研究进度与接力说明.md)。

| 用途 | 文献 | 年份 | PDF页数 | 原始来源 |
| --- | --- | --- | ---: | --- |
| 核心1：HMM匹配流程 | [Hidden Markov Map Matching Through Noise and Sparseness](01_HMM%E5%9F%BA%E7%A1%80%E4%B8%8E%E7%BB%BC%E8%BF%B0/Newson_Krumm_2009_HMM_Map_Matching.pdf) | 2009 | 8 | [来源](https://www.microsoft.com/en-us/research/publication/hidden-markov-map-matching-noise-sparseness/) |
| 核心2：开放区剖分匹配 | [Map Matching for Semi-Restricted Trajectories](03_%E5%8C%BA%E5%9F%9F%E5%89%96%E5%88%86%E4%B8%8E%E7%A9%BA%E9%97%B4%E8%A1%A8%E7%A4%BA/2021_Behr_Map_Matching_for_Semi_Restricted_Trajectories.pdf) | 2021 | 16 | [来源](https://drops.dagstuhl.de/entities/document/10.4230/LIPIcs.GIScience.2021.II.12) |
| 核心3：行人开放区HMM | [An Enhanced Hidden Markov Model for Map-Matching in Pedestrian Navigation](02_%E5%BC%80%E6%94%BE%E5%8C%BA%E5%9F%9F%E5%9C%B0%E5%9B%BE%E5%8C%B9%E9%85%8D/Ma_2024_EHMM_P.pdf) | 2024 | 27 | [来源](https://www.mdpi.com/2079-9292/13/9/1685) |
| 核心4：定向图运动成本 | [Route planning on orienteering maps with least-cost path analysis](04_%E5%AE%9A%E5%90%91%E5%9C%B0%E5%9B%BE%E4%B8%8E%E8%BF%90%E5%8A%A8%E5%BB%BA%E6%A8%A1/2021_Albert_Route_planning_orienteering_LCP.pdf) | 2021 | 7 | [来源](https://ica-proc.copernicus.org/articles/4/4/2021/) |
| 随读随查：地图语义规范 | [International Specification for Orienteering Maps: ISOM 2017-2, Revision 6, January 2024](04_%E5%AE%9A%E5%90%91%E5%9C%B0%E5%9B%BE%E4%B8%8E%E8%BF%90%E5%8A%A8%E5%BB%BA%E6%A8%A1/2024_IOF_ISOM_2017-2_Revision6.pdf) | 2024 | 44 | [来源](https://orienteering.sport/iof/mapping/) |
| 工具书：HMM基础 | [A Tutorial on Hidden Markov Models and Selected Applications in Speech Recognition](01_HMM%E5%9F%BA%E7%A1%80%E4%B8%8E%E7%BB%BC%E8%BF%B0/Rabiner_1989_HMM_Tutorial.pdf) | 1989 | 30 | [来源](https://web.ece.ucsb.edu/Faculty/Rabiner/ece259/publications.html) |
| 配套勘误 | [Correction to A Tutorial on Hidden Markov Models and Selected Applications in Speech Recognition](01_HMM%E5%9F%BA%E7%A1%80%E4%B8%8E%E7%BB%BC%E8%BF%B0/Rabiner_HMM_Tutorial_Errata.pdf) | 未注明 | 2 | [来源](https://web.ece.ucsb.edu/Faculty/Rabiner/ece259/publications.html) |
| 工具书：几何剖分 | [Planning Algorithms — Chapter 6: Combinatorial Motion Planning](03_%E5%8C%BA%E5%9F%9F%E5%89%96%E5%88%86%E4%B8%8E%E7%A9%BA%E9%97%B4%E8%A1%A8%E7%A4%BA/2006_LaValle_Planning_Algorithms_Chapter6.pdf) | 2006 | 36 | [来源](https://lavalle.pl/planning/) |
| 简单离路基线 | [An Algorithm for Map Matching Given Incomplete Road Data](02_%E5%BC%80%E6%94%BE%E5%8C%BA%E5%9F%9F%E5%9C%B0%E5%9B%BE%E5%8C%B9%E9%85%8D/Haunert_Budig_2012_Incomplete_Road_Data.pdf) | 2012 | 4 | [来源](https://doi.org/10.1145/2424321.2424402) |
| 方法借鉴：状态分辨率 | [Online Target Localization using Adaptive Belief Propagation in the HMM Framework](03_%E5%8C%BA%E5%9F%9F%E5%89%96%E5%88%86%E4%B8%8E%E7%A9%BA%E9%97%B4%E8%A1%A8%E7%A4%BA/2022_Seo_Kia_Adaptive_Belief_Propagation_HMM.pdf) | 2022 | 8 | [来源](https://arxiv.org/abs/2203.03815) |
| 方法借鉴：坡度速度 | [Using crowdsourced fitness tracker data to model the relationship between slope and travel rates](04_%E5%AE%9A%E5%90%91%E5%9C%B0%E5%9B%BE%E4%B8%8E%E8%BF%90%E5%8A%A8%E5%BB%BA%E6%A8%A1/2019_Campbell_Slope_and_travel_rates.pdf) | 2019 | 15 | [来源](https://doi.org/10.1016/j.apgeog.2019.03.008) |
| 概览与实验设计 | [A Survey on Map-Matching Algorithms](01_HMM%E5%9F%BA%E7%A1%80%E4%B8%8E%E7%BB%BC%E8%BF%B0/Chao_2019_Map_Matching_Survey_arxiv.pdf) | 2019 | 12 | [来源](https://arxiv.org/abs/1910.13065) |
| 扩展：道路内外混合滤波 | [Map matching when the map is wrong: Efficient on/off road vehicle tracking and map learning](02_%E5%BC%80%E6%94%BE%E5%8C%BA%E5%9F%9F%E5%9C%B0%E5%9B%BE%E5%8C%B9%E9%85%8D/Murphy_2019_On_Off_Road_sIMM.pdf) | 2019 | 10 | [来源](https://arxiv.org/abs/1809.09755) |
| 近期补充：方向约束 | [AC-HMM: azimuth-constrained hidden Markov model-based map matching for robust pedestrian positioning in urban canyons](05_%E8%BF%91%E6%9C%9F%E8%A1%A5%E5%85%85%E4%B8%8E%E8%BF%90%E5%8A%A8%E7%BA%A6%E6%9D%9F/2026_Wang_AC_HMM_Azimuth_Constrained_Pedestrian.pdf) | 2026 | 18 | [作者公开版本](https://ahmedmansoour.github.io/indoor-positioning-hub/publications/ac-hmm-azimuth-constrained-map-matching-urban-canyons.html) |

新增[核心文献对照与研究问题](01_核心文献对照与研究问题.md)，用于从阅读进入方法设计；近期补检与访问限制记录见[检索记录](检索记录_2026-10-27.md)。

## 每篇的主要用途与适用边界

### F02 Hidden Markov Map Matching Through Noise and Sparseness

作者：Paul Newson；John Krumm。出版信息：ACM SIGSPATIAL GIS 2009:336–343。

以道路候选为状态，结合GPS距离观测和路径距离差转移，用Viterbi求最可能路线；通过降采样和加噪评价稳健性。

**与课题的关系：** 第一篇精读，建立观测—候选—转移—序列求解的完整流程；同时借鉴噪声和采样率实验。

**适用边界：** 针对车辆道路网络，不能直接表示越野穿林；论文是离线批处理。其人工真值为走过的路线，不是每个时刻的精确坐标，路线匹配正确不等于逐点定位误差为零。

**阅读位置：** §3 HMM Map Matching（PDF pp.3–4）；§4 Algorithm Particulars（PDF pp.5–6）；§5 Ground Truth Data（PDF p.6）；§6–7 Results/Conclusions（PDF pp.6–7）

**资料准备阅读核查（2026年10月）：** 已阅读摘要、问题定义、HMM方法、实现细节、数据及实验结论；未复现；首页渲染核验

### Behr2021SemiRestricted Map Matching for Semi-Restricted Trajectories

作者：Timon Behr；Thomas C. van Dijk；Axel Forsch；Jan-Henrik Haunert；Sabine Storandt。出版信息：11th International Conference on Geographic Information Science (GIScience 2021) – Part II, LIPIcs 208, 12:1–12:16。

面向道路与开放空间混合运动，将开放多边形三角剖分的边并入路网，在图边上生成候选位置，以能量模型和Dijkstra推断匹配路径；三角形本身不是HMM状态。利用OSM及真实步行、骑行轨迹评价离路片段识别与轨迹表示。

**与课题的关系：** 直接相关：可作为道路—面状区域统一表示、剖分后候选生成及基线设计的核心参考。作者代码：https://github.com/tcvdijk/tessa。

**适用边界：** 使用能量最小化而非概率HMM；实验主要依靠人工标注的离路片段，以及相对输入GPS计算的Fréchet和归一化DTW形状距离，不等于高精度坐标真值验证。未直接验证定向越野的植被通行性或运动员特征。

**阅读位置：** Abstract（PDF p.1）；§2.1–2.2 Methodology（PDF pp.4–7）；Figure 5（PDF p.8，已视觉核对）；§3 Experiments（PDF pp.8–13）；§4 Conclusion and Future Work（PDF pp.13–14）

**资料准备阅读核查（2026年10月）：** 已阅读摘要、方法、实验与结论；核对剖分示意图，尚未复现代码

### MaWangLee2024 An Enhanced Hidden Markov Model for Map-Matching in Pedestrian Navigation

作者：Shengjie Ma；Pei Wang；Hyukjoon Lee。出版信息：Electronics, 13(9), article 1685。

EHMM-P通过短时校准改善初始匹配，加入开放区域隐状态，并以道路总长度及运动距离、方向、位置差调整概率。先识别开放区观测，再接入预训练Y-net生成轨迹；在校园手机GPS上与常规HMM及Behr方法比较。

**与课题的关系：** 与课题最接近的重点论文。帮助区分“识别人在开放区”和“纠正开放区坐标”，可借鉴初始分布、状态转换、道路/开放区分开评价。证明开放区域HMM与运动特征结合并非空白。

**适用边界：** 核心EHMM-P只增加一个特殊open-field状态，开放区候选坐标取GPS观测本身；区域内轨迹恢复另靠Y-net，并非语义自适应剖分。 Y-net阶段用开放区前几个观测及退出前的目的地观测，不能把完整流程直接作为无延迟实时方法。 校园行走条件，未验证林地、坡地和定向越野跑动；搜索半径不随环境自适应，高斯假设和启发式参数有适用边界。 数据因隐私不公开，仅可向通讯作者申请；真值通过地标距离/角度人工测录，正文未完整交代独立测量设备精度与误差预算。 表3的4.63 m是作者报告的平均定位误差减少量，不是绝对误差；开放区轨迹效果包含Y-net贡献，不能全部归因于HMM。

**阅读位置：** Abstract；4.1 Problem Definition；4.2.1 Initial States（短时校准与到达点）；4.2.2 Emission and Transition（附加open-field状态；道路总长度因子；距离/方向/位置差）；4.2.3 Algorithm（浏览）；4.2.4 Y-net开放区域轨迹预测；5.1 Data Collection and Data Preprocessing；5.2 Results and Discussion；6 Conclusions及Data Availability

**资料准备阅读核查（2026年10月）：** 全文结构浏览，精读摘要、4.2方法、5实验、6结论；视觉核对第10页开放区状态及发射模型；未逐式推导或复现。

### T01 Route planning on orienteering maps with least-cost path analysis

作者：Gáspár Albert；Zsófia Sárközy。出版信息：Proceedings of the International Cartographic Association, 4, article 4 (ICC 2021)。

将定向地图的等高线、道路和覆盖类型转成成本栅格，用最小成本路径模拟路线选择。第2.4节式(1)的地形成本为`HCR = TRI × sqrt(abs(PC) × SLO)`；参与合成的各成本变量先归一化到0.1—1。以11名专家的手绘路线调参，与26名运动员的选线比较，说明地图语义可转为运动代价。

**与课题的关系：** 最直接对应地图语义如何成为区域属性和移动代价；可作为均匀栅格加地图成本的参照方法，再检验语义驱动剖分能否改善HMM定位纠正。路线规划输出不能直接当作实际轨迹真值。

**适用边界：** 单一约5.17平方公里场地；主要验证为手绘理想路线，未开展专门的实地跑测；时间换算仅粗略参考历史比赛GPS；部分石地等地物因源数据问题未处理。文中60%地形和40%覆盖成本组合及表1权重为该案例经验调参，不能直接当通用参数。会议贡献基于摘要单盲评审。

**阅读位置：** PDF p.1 Abstract and Introduction；PDF pp.2-4 Sections 2.1-2.5 Materials and methods；Table 1（PDF p.3）；§2.4式(1)及变量归一化、§2.5成本融合（PDF p.4）；PDF p.5 Section 3 Results, Figure 6；PDF p.6 Sections 4-5 Discussion and Conclusion

**资料准备阅读核查（2026年10月）：** 全文初读：摘要、完整方法、结果、讨论和结论；未复现计算

### T03 International Specification for Orienteering Maps: ISOM 2017-2, Revision 6, January 2024

作者：IOF Map Commission；International Orienteering Federation。出版信息：International Orienteering Federation technical specification。

官方地图符号规范提供地物、可跑性、障碍及方向性信息。第2.3节给出相对速度分级，第2.6至2.8节解释制图综合、精度和地理配准，可用于建立地图语义到区域属性的映射。

**与课题的关系：** 先定义每类区域的语义、相对通行速度和边界约束；将禁止进入与物理上难穿越区分；考虑制图位移和配准误差，避免把图上边界视为绝对准确。

**适用边界：** 这是制图规范而非算法论文，也不是每位运动员的实测速度模型。已核验为Revision 6 January 2024，PDF注明2024-02-01生效、2025-01-01强制；本次不保证其为最新版本。文件来自拉脱维亚定向联合会技术委员会公开链接，PDF内版权及出版信息确认IOF来源。ISOM的impassable/uncrossable不自动等同比赛禁入；不能混用短距离定向ISSprOM的规则语义。

**阅读位置：** PDF pp.1-2 version and publication information；PDF p.4 Section 1.1 conventions, Section 2.1；PDF pp.5-6 Sections 2.2-2.4 content, runnability and barriers；PDF pp.6-8 Sections 2.6-2.8 generalisation, accuracy and georeferencing；PDF pp.27-28 Symbols 405-410 vegetation；PDF p.34 Symbol 520 area that shall not be entered

**资料准备阅读核查（2026年10月）：** 相关条文精读：版本页、地图内容、可跑性、障碍、制图综合、精度、地理配准以及植被和禁入符号；未逐条读完全部制图尺寸

### F01 A Tutorial on Hidden Markov Models and Selected Applications in Speech Recognition

作者：Lawrence R. Rabiner。出版信息：Proceedings of the IEEE 77(2):257–286。

HMM经典教程，系统区分模型要素、观测序列概率、最优状态序列和参数估计。适合查清初始分布、转移概率、观测模型及Viterbi回溯。

**与课题的关系：** 为地图匹配中的概率模型和动态规划提供基础；先理解状态与观测，再结合Newson论文读具体定位建模。

**适用边界：** 主要应用是语音；并非地图匹配方法或空间剖分创新。下载版本是扫描件，无法直接全文搜索；不必先读完全部语音识别内容。

**阅读位置：** II.B Elements of an HMM（PDF pp.4–5，印刷页260–261）；II.C The Three Basic Problems（PDF p.5）；III.A–B（PDF pp.6–8；Viterbi在PDF p.8/印刷页264）

**资料准备阅读核查（2026年10月）：** 视觉阅读首页及PDF第4–8页（HMM要素、三个基本问题、前向后向与Viterbi）；未通读语音应用部分

### F01a Correction to A Tutorial on Hidden Markov Models and Selected Applications in Speech Recognition

作者：Lawrence R. Rabiner。出版信息：Author errata, undated PDF。

修正原教程中模型比较公式及缩放计算说明。

**与课题的关系：** 阅读原教程对应公式时一并核对，作为配套附件。

**适用边界：** 不是独立研究论文；文件未标明修订日期，不将网页条目的年份当成该PDF的修订年份。

**阅读位置：** 全篇2页

**资料准备阅读核查（2026年10月）：** 已读2页作者勘误，未逐式复核证明

### LaValle2006Ch6 Planning Algorithms — Chapter 6: Combinatorial Motion Planning

作者：Steven M. LaValle。出版信息：Planning Algorithms, Cambridge University Press（作者公开章节）。

介绍精确单元分解、垂直/梯形剖分与三角剖分，说明如何把连续自由空间转成保持连通性的邻接图。适合学习区域、边界、孔洞与图的关系，以及二维剖分必须满足的基本条件。

**与课题的关系：** 基础方法借鉴：用于定义剖分和拓扑连通性、理解单元内可达性；不是GPS地图匹配论文，也不是课题创新证据。

**适用边界：** 主要解决运动规划与几何连通性；没有GPS噪声、HMM观测模型或定向地图语义。教材的规划最优性、完备性不能直接等同于定位准确性。

**阅读位置：** §6.1 Introduction（书页249–251；PDF pp.2–3）；§6.2.1 Representation（书页252–253；PDF pp.3–4）；§6.2.2 Vertical Cell Decomposition（书页253–260；PDF pp.4–7）；Figures 6.3–6.5（书页255–256；PDF p.5，已视觉核对）；§6.3.2 2D Decompositions（书页268–270；PDF pp.11–12）

**资料准备阅读核查（2026年10月）：** 选读§6.1、§6.2.1–6.2.2及§6.3.2；核对二维剖分与邻接图示意，未通读全章

### HaunertBudig2012 An Algorithm for Map Matching Given Incomplete Road Data

作者：Jan-Henrik Haunert；Benedikt Budig。出版信息：Proceedings of the 20th International Conference on Advances in Geographic Information Systems (SIGSPATIAL 2012)。

扩展道路HMM，为每个GPS点增加位于原观测处的离路候选，用道路内最短路和带代价的道路外连接统一匹配。作者在4次徒步、7799个GPS点上检验不完整路网处理，并报告离路区段识别结果。

**与课题的关系：** 说明HMM处理行人离路或缺失道路早已有研究；可作简单离路候选基线，并启发道路/区域转换代价设计。其引用的加权区域最短路也连接了地图匹配与区域通行代价。

**适用边界：** 离路候选直接取原GPS点，不能据此声称已纠正离路坐标误差。 离路-离路使用直线，离路单位代价为常量；未建模定向地图中的植被、障碍和分区语义。 假设相邻观测间最多切换一次道路内外；总体仍偏好已知路网。 离线算法；仅4次徒步案例和运行时间，缺乏系统的逐点坐标误差基准；不应将23个识别区段全正确等同于普遍100%准确率。

**阅读位置：** Abstract；1 Motivation；2 Related Work；3 Our Algorithm（每个GPS点增加离路候选；三类连接；式5–9）；4 Experimental Results（4次徒步、7799点、65 km）；5 Conclusion and Future Work

**资料准备阅读核查（2026年10月）：** 全文通读（4页，含方法、实验、结论）；关键方法与实验页已渲染检查；未复现实验。

### SeoKia2022AdaptiveHMM Online Target Localization using Adaptive Belief Propagation in the HMM Framework

作者：Min-Won Seo；Solmaz S. Kia。出版信息：IEEE Robotics and Automation Letters 7(4):10288–10295（下载arXiv v5作者稿）。

把二维位置离散为HMM状态，按四叉树启发的由粗到细策略缩小Viterbi搜索空间，以减少计算与存储。室内UWB实验检验定位与开销，适合借鉴空间分辨率和推断成本之间的取舍。

**与课题的关系：** 方法借鉴：连接自适应空间离散、HMM和定位，可用于思考“哪里细分、状态数如何影响计算”。并非直接的户外GPS地图匹配。

**适用边界：** 测量来自室内UWB锚点；细化主要由概率支持区域驱动，不等于定向地图语义剖分。第一组用动作捕捉参照，第二组用规定几何路线；不能移用其误差数值证明户外效果，粗层误判的影响也应另行检验。

**阅读位置：** Abstract/§I Introduction（PDF pp.1–2）；§II Problem Definition（PDF p.2）；§III A–D（PDF pp.2–5）；Figure 4（PDF p.4，已视觉核对）；§IV Experimental Demonstrations（PDF pp.5–7）；§V Conclusions（PDF p.7）

**资料准备阅读核查（2026年10月）：** 已阅读摘要、问题定义、方法、实验与结论；核对自适应细分图，尚未复现

### T02 Using crowdsourced fitness tracker data to model the relationship between slope and travel rates

作者：Michael J. Campbell；Philip E. Dennison；Bret W. Butler；Wesley G. Page。出版信息：Applied Geography, 106, 93-107。

利用约3万名用户42万次活动构建坡度与移动速度的分位数模型，拟合时区分上下坡影响。清洗后约105万条记录随机分半训练验证，并用另取的100条徒步记录比较旅行时间。

**与课题的关系：** 支持采用随坡度、方向和个体能力变化的速度范围，而不是固定速度阈值；可用于HMM转移可达性和候选区域搜索半径。按高程变化分割同质坡段的思路也可启发运动约束下的剖分。

**适用边界：** 数据为盐湖城周边自然路面步道上的混合徒步、慢跑和跑步，不能直接代表离路穿越林地的定向运动员；匿名聚合数据无法确定每个样本的运动方式、疲劳和个体特征；植被、地表粗糙度等未建模；分位数拟合误差不是GPS定位误差，也不是个体瞬时速度预测误差；现有分位数须重新标定。

**阅读位置：** PDF p.1 Abstract；PDF pp.4-8 Section 3 Methods (slope segmentation, filtering, percentile fits, random split validation, 100 AllTrails hikes)；PDF pp.8-11 Section 4 Results；PDF pp.11-14 Sections 5-6 Discussion and Conclusions

**资料准备阅读核查（2026年10月）：** 关键章节初读：摘要、数据处理及拟合方法、验证设计、主要结果、讨论和结论；未逐项核验附录参数或复现

### F03 A Survey on Map-Matching Algorithms

作者：Pingfu Chao；Yehong Xu；Wen Hua；Xiaofang Zhou。出版信息：arXiv preprint 1910.13065v1 (submitted to ADC 2020)。

按相似度、状态转移、候选演化及评分框架梳理地图匹配，比较代表方法，分析采样、地图密度和轨迹质量带来的挑战。

**与课题的关系：** 用于搭建相关工作框架、理解在线与离线区别，并设计采样率、异常点和计算成本实验。

**适用边界：** 下载为2019 arXiv v1，不能代表2026最新研究；主要讨论户外车辆路网，不能以此断言行人或开放空间研究不存在。

**阅读位置：** §2 Problem Definition；§3.2 State-Transition Model；§4 Challenges and Evaluations；§5 Conclusion

**资料准备阅读核查（2026年10月）：** 阅读摘要、问题定义、方法分类、状态转移模型、实验和结论；其他分类浏览；未复现

### MurphyPaoYuen2019 Map matching when the map is wrong: Efficient on/off road vehicle tracking and map learning

作者：James Murphy；Yuanyuan Pao；Albert Yuen。出版信息：Proceedings of the 12th ACM SIGSPATIAL International Workshop on Computational Transportation Science (IWCTS 2019)。

用sIMM结合道路HMM和独立运行的自由空间Kalman类滤波器，按观测切换道路内外模型，并用反向过程恢复轨迹。车辆GPS与不完整路网案例展示减少错误吸路，也可依据重复离路轨迹发现地图遗漏。

**与课题的关系：** 提供道路/自由空间混合模型参考，提醒地图约束可能出错、需要保留离路解释；适合做扩展阅读而非第一版复现目标。

**适用边界：** 对象是主要沿道路行驶的车辆，离路模型是回退机制，不能直接推广为越野运动员模型。 自由空间滤波器不利用区域语义、地形或障碍；并非区域剖分方法。 展示以地图缺失案例和Lyft轨迹地图学习为主，没有系统的公开逐点真值精度基准。 报告运行时间约常规HMM的2–4倍；完整反向轨迹重建依赖后续观测，应与可在线运行的前向滤波区分。

**阅读位置：** Abstract；2 Existing Work（双模型与semi-interaction）；3.1 Outline of Approach；3.2.1 Forward sIMM Algorithm；3.3 MAP State Sequence Estimation（目标与反向采样框架）；4.1 Vehicle Localization；4.2 Map Learning；4.3 Performance；5 Conclusions

**资料准备阅读核查（2026年10月）：** 精读摘要、3.1模型框架、3.2.1算法、3.3目标说明及4实验、5结论；浏览概率推导，未逐式推导或复现；第8页图文渲染核对。

## 版本与文件说明

所有PDF均保留原文，未改写作者内容。下载来自出版者、作者或机构公开来源；IOF规范采用拉脱维亚定向联合会技术委员会链接的IOF版本，已核验Revision 6 January 2024，不宣称当前最新。

Chao综述为2019 arXiv v1；Murphy下载为2019 arXiv v2，与2018首次提交年份区分；Seo下载为arXiv v5作者稿。LaValle只收录第6章，PDF为双页排版。Rabiner为扫描件，另附作者勘误。

各目录TXT是自动提取文本，仅供搜索。公式、表格和双栏顺序应回到原PDF核对。此前文献准备阅读核查与学生现有的[四篇阅读笔记](02_阅读笔记.md)分别记录；当前没有据此完成文献算法复现，也不构成完整查新结论。

### Wang2026ACHMM AC-HMM: azimuth-constrained hidden Markov model-based map matching for robust pedestrian positioning in urban canyons

作者：Jingxian Wang；Ahmed Mansour；Mengyu Ding；Duojie Weng；Huan Luo；Wu Chen。在线发表于2026年6月9日，Geo-spatial Information Science。

在道路HMM中结合短期、长期运动方向和道路连接关系，缓解城市人行道误匹配。方向来自手机传感器；匹配位置投影到选定道路边。

**与课题的关系：** 补充运动方向约束相关工作，说明加入方向信息已有先例；可借鉴特征与模型连接方式，不能视为开放区域剖分方案。

**适用边界：** 场景为城市人行道，未验证定向越野自由穿林；参数在作者数据上标定。参照使用已知坐标灯柱及步数插值，不能直接外推为野外真值方案；原始传感器数据需向作者申请。

**阅读位置：** PDF p.2 abstract；PDF pp.6-10 method framework, azimuth constraints, emission and transition design；PDF p.12 section 3.1.2 trajectory collection and reference；PDF pp.16-17 conclusions and data availability

**资料准备阅读核查（2026年10月）：** 选读摘要、方法框架与方向约束、采集与参照构建、结论及数据声明；首页视觉核验；未逐式复核或复现
