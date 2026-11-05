# 地图与运动约束辅助 GPS 定位纠正：原型 v0.1.0

2026-11-02 完成第一版可运行实验。已实现地图裁切与均匀格网、候选/连接查询、离线 HMM 风格 Viterbi、独立合成参照、原始 GPS 对照、逐点误差、耗时及轨迹叠图。7 类场景 × 3 个噪声种子，共 21 条轨迹，每条 71 点，全部跑了两遍。

**全部定位数据仍是合成的。** 丰台仅提供历史地图几何，通行性与现实坐标对齐均未验证。本版能证明流程可运行和复现，不能证明真实运动员精度提升，也没有证明新剖分方法优于现有方法。

建议先读[本轮运行记录](docs/运行记录_2026-11-02.md)与[实验设计和数据流](docs/实验设计与数据流.md)，再看[完整实验报告](runs/2026-11-02-v0.1-verified/results/实验结果.md)。机器可读结果保存在 [metrics.csv](runs/2026-11-02-v0.1-verified/results/metrics.csv) 和 [metrics.json](runs/2026-11-02-v0.1-verified/results/metrics.json)，源码与验收证据索引见[版本记录](版本记录.md)。

## 在当前机器复现

已有数据核查环境可以直接运行，无需重新安装。终端执行下面两行，输出目录必须是新目录；既有结果不会被覆盖。

```sh
cd /Users/xieyuxin1/Documents/毕设/实验原型
./run.sh runs/my-reproduction
```

脚本依次选择 `GPSMAP_PYTHON` 指定的解释器、本目录 `.venv/bin/python`、现有 `../数据核查/2026-11-01/.venv/bin/python`，否则使用 `python3`。本次实际验证环境为 Python 3.12.14、macOS arm64；一套 21 轨迹、三方法、含绘图的运行约一分钟。新目录下 `datasets/` 保存合成输入，`results/` 保存结果。

若在另一台机器上运行，需要 Python 3.12 和依赖，可创建独立环境：

```sh
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements-lock.txt
./run.sh runs/my-reproduction
```

[requirements.txt](requirements.txt) 固定直接依赖，[requirements-lock.txt](requirements-lock.txt) 额外记录当前绘图/投影依赖版本。跨平台安装和逐字复现尚未实测；已验证的是本机固定环境下两次完整重跑。PNG 可能受平台字体影响，验收以坐标、状态和数值结果为准。

## 已有结果和复核命令

正式首轮为 `runs/2026-11-02-v0.1-verified/`，重复运行是 `runs/2026-11-02-v0.1-verified-repeat/`。[复现核查记录](verification/final-reproducibility.json) 确认 84 份输入文件及 42 份预测文件逐字相同，63 行指标由独立代码从坐标重新计算一致，233 份原始资料哈希不变。耗时允许不同。

```sh
../数据核查/2026-11-01/.venv/bin/python -m unittest discover -s tests -v
../数据核查/2026-11-01/.venv/bin/python verify.py \
  runs/2026-11-02-v0.1-verified runs/my-reproduction \
  --output verification/my-reproduction.json
```

33 项测试已通过，包括独立穷举核对 Viterbi、地图绕障/禁止斜切、未知边传播、非等间隔采样、失败截段、手算误差、参照修改/删除不影响预测、输出不覆盖。`verify.py` 还核对源文件和原始资料，因此源代码有改动或原始资料不在原位置时会明确失败；此时应创建新版本并说明差异，而不是删除检查。

## 单独运行定位或重建真实地图样区

定位命令只接收观测、地图和参数，参考答案不在参数中。输入必须为 `t_s,x_m,y_m,sigma_m` 四列，米制坐标、秒时间、每轴标准差，时间严格递增。下面以保存的一条合成轨迹为例：

```sh
../数据核查/2026-11-01/.venv/bin/python -m gpsmap infer \
  --observations runs/2026-11-02-v0.1-verified/datasets/obstacle_detour_seed20261101/observations.csv \
  --map runs/2026-11-02-v0.1-verified/datasets/obstacle_detour_seed20261101/map.json \
  --config configs/default.json --cell-size 4 --method hmm \
  --output runs/one-track-reproduction
```

输出 `predictions.csv` 含时间、估计坐标、区域、状态和候选数；`diagnostics.json` 保存断链、回退、unknown 等诊断；`run.json` 记录参数、输入哈希、建图和推断耗时。`map_only` 使用相同候选逐时刻选择最近点；原始 GPS 基线完全不改坐标。

已有 [丰台样区](data/maps/fengtai_map.json) 可直接用于全部实验。若需从原始派生 GPKG 重建，执行：

```sh
../数据核查/2026-11-01/.venv/bin/python -m gpsmap prepare-map \
  --source ../数据核查/2026-11-01/可用地图/丰台基础地图.gpkg \
  --output runs/rebuilt-map --cell-size 8
```

裁图规则固定，输入只读。局部原点 UTM 50N `(424203,4412963) m`，范围 400 × 400 m，2,500 个节点和 9,702 条无向边，通行性全为 unknown。详见[地图说明](docs/地图说明.md)及[来源记录](data/maps/fengtai_provenance.json)。网格 GeoJSON 使用局部米制坐标，自带 `coordinate_system`，不是普通 WGS84 经纬度 GeoJSON。

## 参数和解释边界

[冻结配置](configs/default.json) 使用合成格网 4 m、丰台格网 8 m、搜索半径 30 m、候选上限 48、速度上限 8 m/s、运动尺度 3 m/s，种子为 20261101—20261103。它们都是工程假设。观测噪声一般为每轴 6 m，预设低噪声场景为 0.35 m；参照路线不由模型最短路生成。三次种子仅改变噪声，路线不变。

当前实现采用非归一化运动势的 HMM 风格路径评分和 Viterbi，不能将分数称为规范化概率或可靠置信度；它是使用未来观测的离线纠正，不是在线定位。输出是离散候选坐标，连接采样点的直线不是恢复出的完整行走路径。详见[定位说明](docs/定位说明.md)及[评测说明](docs/评测说明.md)。

低噪声场景与错误地图已经出现明确退化。所有回退和重启点均纳入误差，状态为 ok 也不代表坐标正确。当前三方法还不能完全分离地图、量化与运动先验贡献；丰台全 unknown 的结果更不能作为已知地物约束有效的证据。

首次联调历史保存在 `results/first-track/`；当时 `data/smoke/free_offroad` 含修复前的装饰线表示，只作为开发记录保留，不用于正式验收。正式数据已由修复后的生成器重新创建，路线、噪声、种子及模型参数未依结果调优。

共享接口、文件所有权与初始冻结约定见[接口与最小实验](docs/接口与最小实验.md)。下一项研究工作是增加无地图的运动对照、检查候选与分辨率敏感性，随后再比较边界保持剖分；真实 GPS 与独立参照仍需另外取得。
