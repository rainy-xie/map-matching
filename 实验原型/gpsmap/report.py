"""Concise descriptive report; no significance claims from three noise seeds."""
from collections import defaultdict
from pathlib import Path
import json
import math


def write_report(output_dir: Path, rows: list[dict]):
    grouped = defaultdict(list)
    for row in rows:
        grouped[(row["scenario"], row["method"])].append(row)
    scope = json.loads((output_dir / "suite_run.json").read_text(encoding="utf-8"))
    scope_text = ("本次未筛选输入数据集目录中的轨迹。" if scope["all_planned_datasets_in_input_were_run"]
                  else "本次只运行筛选后的部分轨迹，不代表完整预设套件。")
    lines = ["# 第一版合成实验结果", "", "以下均为合成轨迹与合成 GPS 观测；丰台场景仅使用真实历史地图作为底图。结果不能外推到真实运动员定位精度。",
             "", f"参数在首次联调前冻结；本次运行 {scope['datasets']} 条轨迹。{scope_text}表中 RMSE 是按各条轨迹点数加权汇总平方误差后开方；P95 是各运行的 P95 均值，不是合并样本的 P95。计时为本机单次墙钟时间，非性能基准。", "",
             "| 场景 | 方法 | 轨迹数 | 汇总 RMSE/m | 运行 P95 均值/m | 平均推断/s | 平均建图/s |", "| --- | --- | ---: | ---: | ---: | ---: | ---: |"]
    summary = []
    for (scenario, method), values in sorted(grouped.items()):
        n = sum(v["n"] for v in values)
        rmse = math.sqrt(sum(v["rmse_m"] ** 2 * v["n"] for v in values) / n)
        p95 = sum(v["p95_m"] for v in values) / len(values)
        elapsed = sum(v["inference_s"] for v in values) / len(values)
        build = sum(v["map_build_s"] for v in values) / len(values)
        lines.append(f"| {scenario} | {method} | {len(values)} | {rmse:.3f} | {p95:.3f} | {elapsed:.4f} | {build:.4f} |")
        summary.append({"scenario": scenario, "method": method, "runs": len(values), "n": n,
                        "pooled_rmse_m": rmse, "mean_run_p95_m": p95, "mean_inference_s": elapsed, "mean_map_build_s": build})
    lines += ["", "## 退化结果与失败状态", "", "以下列出 HMM 比原始 GPS 的逐轨迹 RMSE 更大的运行；即使状态为 ok，误差恶化也属于需要保留的失败案例。"]
    raw = {r["dataset"]: r for r in rows if r["method"] == "raw"}
    worse = [r for r in rows if r["method"] == "hmm" and r["rmse_m"] > raw[r["dataset"]]["rmse_m"]]
    for row in worse:
        lines.append(f"\n- {row['dataset']}：原始 {raw[row['dataset']]['rmse_m']:.3f} m → HMM {row['rmse_m']:.3f} m；[轨迹图]({row['dataset']}/trajectory.png)。")
    if not worse:
        lines.append("\n本次运行未出现整条轨迹 RMSE 恶化；这不表示无逐点恶化，也不表示真实环境有效。")
    lines += ["", "无候选或不可达重启的回退点已纳入误差，详见 metrics.json 的 status_counts 和每个方法的 diagnostics.json。unknown 反映地图知识不足，不代表已经确认可通行。", "",
              "## 证据与复现", "", "metrics.csv / metrics.json 保留每轨迹每方法全部统计；各目录含预测坐标、逐点误差、轨迹图、数据哈希及计时。environment.json 记录解释器、库版本、代码 SHA-256；config.json 记录冻结参数。重复运行应比较预测坐标与状态，时间允许变化。", "",
              "本版只实现均匀格网基线。格网中心造成量化误差，八邻接最短路近似可能高估距离；候选半径和数量截断可排除正确位置；零均值运动代价偏好小步长，可能压缩转弯和快速移动。离线 Viterbi 使用未来观测，不是在线定位。HMM 路径分数未作置信度校准。"]
    (output_dir / "实验结果.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (output_dir / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
