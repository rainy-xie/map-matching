"""The model command receives observations, map, and config, never reference paths."""
from __future__ import annotations
import argparse
import csv
import importlib.metadata
import json
import os
import platform
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo
from . import __version__
from .contracts import ModelConfig
from .io import load_observations, write_estimates, write_json, sha256

ROOT = Path(__file__).resolve().parents[1]


def fresh_dir(path: Path):
    path.mkdir(parents=True, exist_ok=False)


def environment_record():
    paths = sorted(list((ROOT / "gpsmap").glob("*.py")) + list((ROOT / "tests").glob("*.py"))
                   + list((ROOT / "configs").glob("*.json")) + [ROOT / "requirements.txt"])
    return {
        "prototype_version": __version__,
        "started_at": datetime.now(ZoneInfo("Asia/Shanghai")).isoformat(),
        "python": sys.version, "executable": sys.executable,
        "platform": platform.platform(), "machine": platform.machine(),
        "packages": {name: importlib.metadata.version(name) for name in
                     ("numpy", "shapely", "pyproj", "pyogrio", "matplotlib")},
        "source_sha256": {str(p.relative_to(ROOT)): sha256(p) for p in paths},
        "timing_policy": "perf_counter wall seconds; one cold subprocess per method and dataset; no runtime confidence interval",
    }


def infer_command(args):
    # The audit guard makes accidental reference reads a visible error. It is a
    # correctness guard for this prototype, not a security sandbox.
    def deny_reference(event, values):
        if event == "open" and values and isinstance(values[0], (str, bytes, os.PathLike)):
            p = Path(os.fsdecode(values[0]))
            if "reference" in p.parts:
                raise PermissionError("Inference is forbidden to open the reference directory")
    sys.addaudithook(deny_reference)
    from .spatial import GridMap
    from .inference import infer, map_only
    observation = load_observations(args.observations)
    config = json.loads(args.config.read_text(encoding="utf-8"))
    model_config = ModelConfig(**config["model"])
    spec = json.loads(args.map.read_text(encoding="utf-8"))
    fresh_dir(args.output)
    started = time.perf_counter()
    spatial = GridMap(spec, args.cell_size)
    build_s = time.perf_counter() - started
    started = time.perf_counter()
    estimates, diagnostics = (infer if args.method == "hmm" else map_only)(observation, spatial, model_config)
    infer_s = time.perf_counter() - started
    if len(estimates) != len(observation) or any(a.t_s != b.t_s for a, b in zip(estimates, observation)):
        raise RuntimeError("Estimator violated one-output-per-observation contract")
    write_estimates(args.output / "predictions.csv", estimates)
    write_json(args.output / "diagnostics.json", diagnostics)
    write_json(args.output / "run.json", {
        "method": args.method, "label": "SYNTHETIC", "mode": "offline_full_sequence",
        "parameters": config["model"], "cell_size_m": args.cell_size,
        "map_build_s": build_s, "inference_s": infer_s,
        "map_statistics": spatial.statistics(), "n": len(observation),
        "inputs_sha256": {"observations": sha256(args.observations), "map": sha256(args.map), "config": sha256(args.config)},
        "reference_access": "No reference argument; audit guard denies opens of paths with a reference component",
    })
    print(json.dumps({"method": args.method, "n": len(estimates), "map_build_s": build_s, "inference_s": infer_s}))


def prepare_command(args):
    from .prepare_map import build_real_sample
    result = build_real_sample(args.source, args.output, cell_size_m=args.cell_size)
    print(result)


def generate_command(args):
    from .evaluation import generate_suite
    config = json.loads(args.config.read_text(encoding="utf-8"))
    if args.first_seed:
        config["seeds"] = config["seeds"][:1]
    spec = json.loads(args.fengtai_map.read_text(encoding="utf-8")) if args.fengtai_map else None
    result = generate_suite(args.output, config, fengtai_spec=spec)
    print(json.dumps([str(p) for p in result], ensure_ascii=False, indent=2))


def run_command(args):
    from .evaluation import evaluate_run, plot_comparison
    config = json.loads(args.config.read_text(encoding="utf-8"))
    ModelConfig(**config["model"])
    datasets = sorted(p.parent for p in args.datasets.glob("*/observations.csv"))
    if args.scenario:
        datasets = [p for p in datasets if json.loads((p / "metadata.json").read_text())["scenario"] == args.scenario]
    if args.limit:
        datasets = datasets[:args.limit]
    if not datasets:
        raise ValueError("No datasets found")
    fresh_dir(args.output)
    write_json(args.output / "environment.json", environment_record())
    write_json(args.output / "config.json", config)
    rows = []
    suite_start = time.perf_counter()
    for dataset in datasets:
        metadata = json.loads((dataset / "metadata.json").read_text(encoding="utf-8"))
        dest = args.output / dataset.name
        dest.mkdir()
        started = time.perf_counter()
        metrics = evaluate_run(dataset, dataset / "observations.csv", dest / "raw", "raw")
        evaluation_s = time.perf_counter() - started
        common = {"dataset": dataset.name, "scenario": metadata["scenario"], "seed": metadata["seed"], "label": metadata["label"]}
        rows.append({**common, "method": "raw", **metrics, "map_build_s": 0.0, "inference_s": 0.0, "evaluation_s": evaluation_s})
        predictions = {}
        for method in ("map_only", "hmm"):
            output = dest / method
            command = [sys.executable, "-m", "gpsmap", "infer", "--observations", str(dataset / "observations.csv"),
                       "--map", str(dataset / "map.json"), "--config", str(args.config),
                       "--cell-size", str(metadata["cell_size_m"]), "--method", method, "--output", str(output)]
            start_process = time.perf_counter()
            completed = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, check=True)
            process_s = time.perf_counter() - start_process
            (dest / f"{method}_stdout.txt").write_text(completed.stdout, encoding="utf-8")
            (dest / f"{method}_stderr.txt").write_text(completed.stderr, encoding="utf-8")
            run = json.loads((output / "run.json").read_text(encoding="utf-8"))
            started = time.perf_counter()
            metrics = evaluate_run(dataset, output / "predictions.csv", output / "evaluation", method)
            evaluation_s = time.perf_counter() - started
            rows.append({**common, "method": method, **metrics, "map_build_s": run["map_build_s"],
                         "inference_s": run["inference_s"], "subprocess_s": process_s,
                         "evaluation_s": evaluation_s, "map_statistics": run["map_statistics"]})
            predictions[method] = output / "predictions.csv"
        plot_comparison(dataset, predictions, dest / "trajectory.png")
        write_json(dest / "input_sha256.json", {str(p.relative_to(dataset)): sha256(p)
                   for p in sorted(dataset.rglob("*")) if p.is_file()})
        print(f"Completed {dataset.name}", flush=True)
    write_json(args.output / "metrics.json", rows)
    keys = sorted(set().union(*(row.keys() for row in rows)))
    with (args.output / "metrics.csv").open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: json.dumps(v, ensure_ascii=False) if isinstance(v, (dict, list)) else v for k, v in row.items()})
    write_json(args.output / "suite_run.json", {"datasets": len(datasets), "wall_s": time.perf_counter() - suite_start,
               "all_planned_datasets_in_input_were_run": not bool(args.limit or args.scenario),
               "scope": "mechanism tests, not a statistical field efficacy study"})
    from .report import write_report
    write_report(args.output, rows)
    print(f"Results: {args.output}")


def main():
    parser = argparse.ArgumentParser(description="Synthetic GPS correction prototype v" + __version__)
    sub = parser.add_subparsers(dest="command", required=True)
    prepare = sub.add_parser("prepare-map")
    prepare.add_argument("--source", type=Path, required=True)
    prepare.add_argument("--output", type=Path, required=True)
    prepare.add_argument("--cell-size", type=float, default=8.0)
    prepare.set_defaults(func=prepare_command)
    generate = sub.add_parser("generate")
    generate.add_argument("--output", type=Path, required=True)
    generate.add_argument("--config", type=Path, default=ROOT / "configs/default.json")
    generate.add_argument("--fengtai-map", type=Path)
    generate.add_argument("--first-seed", action="store_true")
    generate.set_defaults(func=generate_command)
    infer = sub.add_parser("infer")
    infer.add_argument("--observations", type=Path, required=True)
    infer.add_argument("--map", type=Path, required=True)
    infer.add_argument("--config", type=Path, default=ROOT / "configs/default.json")
    infer.add_argument("--cell-size", type=float, required=True)
    infer.add_argument("--method", choices=("hmm", "map_only"), default="hmm")
    infer.add_argument("--output", type=Path, required=True)
    infer.set_defaults(func=infer_command)
    run = sub.add_parser("run")
    run.add_argument("--datasets", type=Path, required=True)
    run.add_argument("--output", type=Path, required=True)
    run.add_argument("--config", type=Path, default=ROOT / "configs/default.json")
    run.add_argument("--scenario")
    run.add_argument("--limit", type=int)
    run.set_defaults(func=run_command)
    args = parser.parse_args()
    # Resolve paths once so subprocess cwd changes cannot alter their meaning.
    for key, value in vars(args).items():
        if isinstance(value, Path):
            setattr(args, key, value.resolve())
    args.func(args)
