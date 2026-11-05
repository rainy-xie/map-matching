# 实验原型 v0.1.0

本目录保存2026年11月2日的离线合成基线：7类场景、每类3个噪声种子，共21条轨迹。丰台只提供历史地图几何，通行性与现实配准未验证，结果不能作为真实运动员精度结论。

运行操作见下文；数据流、接口、公式和评价口径集中在[基线技术说明](docs/基线技术说明.md)，待实施的方法与验证见[后续实验设计](docs/后续实验设计.md)。当前完成状态与任务只在[研究进度](../研究进度与接力说明.md)维护，研究范围见[研究方案](../研究方案.md)。

## 运行完整基线

在当前机器可直接使用已有环境，输出目录必须是新目录：

```sh
cd /Users/xieyuxin1/Documents/毕设/实验原型
./run.sh runs/my-reproduction
```

脚本依次选择`GPSMAP_PYTHON`、本目录`.venv/bin/python`、数据核查目录的既有环境，最后才使用`python3`。新运行的`datasets/`保存合成输入，`results/`保存结果。v0.1验证环境为Python 3.12.14、macOS arm64；跨平台逐字复现尚未验证。

新机器可在本目录建立环境，直接依赖见[requirements.txt](requirements.txt)，完整固定版本见[requirements-lock.txt](requirements-lock.txt)：

```sh
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements-lock.txt
./run.sh runs/my-reproduction
```

## 单条定位与地图重建

以下使用当前机器的数据核查环境；新机器可换成本目录`.venv/bin/python`。输入含义和输出字段见[接口约定](docs/基线技术说明.md#接口约定)，参数使用[基线配置](configs/default.json)。

```sh
../数据核查/2026-11-01/.venv/bin/python -m gpsmap infer \
  --observations runs/2026-11-02-v0.1-verified/datasets/obstacle_detour_seed20261101/observations.csv \
  --map runs/2026-11-02-v0.1-verified/datasets/obstacle_detour_seed20261101/map.json \
  --config configs/default.json --cell-size 4 --method hmm \
  --output runs/one-track-reproduction
```

已有[丰台样区](data/maps/fengtai_map.json)可用于本版丰台合成场景及几何接口复现。重建需要本地完整GPKG，来源与裁切规则见[地图与空间查询](docs/基线技术说明.md#地图与空间查询)：

```sh
../数据核查/2026-11-01/.venv/bin/python -m gpsmap prepare-map \
  --source ../数据核查/2026-11-01/可用地图/丰台基础地图.gpkg \
  --output runs/rebuilt-map --cell-size 8
```

## 结果与复核

正式结果位于`runs/2026-11-02-v0.1-verified/`，本地重复运行位于同级`2026-11-02-v0.1-verified-repeat/`。查阅[结果报告](runs/2026-11-02-v0.1-verified/results/实验结果.md)、[指标CSV](runs/2026-11-02-v0.1-verified/results/metrics.csv)、[指标JSON](runs/2026-11-02-v0.1-verified/results/metrics.json)；历史过程见[运行记录](docs/运行记录_2026-11-02.md)、[版本记录](版本记录.md)和[复现核查](verification/final-reproducibility.json)。失败和退化结果均保留。

单元与集成测试可用对应环境运行：

```sh
../数据核查/2026-11-01/.venv/bin/python -m unittest discover -s tests -v
```

33项测试及两次完整重跑通过是2026年11月2日的记录，本次文档合并没有重跑算法。旧`verify.py`检查运行源码和`data/original_sources_sha256.json`；后者混入了现已修订或删除的文献说明路径，因此不能直接作为当前目录的完整验收。只有恢复对应旧快照后，旧命令`python verify.py <首轮目录> <重复目录> --output <新核验文件>`才适用。发布清单同样保留原五份技术说明的旧路径和哈希，未回写；对应关系与本次保留核验见[整理记录](../研究记录/2026-11-06_项目重组记录.md)。
