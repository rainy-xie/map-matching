#!/usr/bin/env python3
"""Independently check two full runs, all-error metrics, and original file hashes."""
import argparse
import csv
import json
import math
from pathlib import Path
from gpsmap.io import sha256, write_json

ROOT = Path(__file__).resolve().parent


def require(condition, description):
    if not condition:
        raise AssertionError(description)


def check(baseline: Path, repeat: Path) -> dict:
    config = json.loads((ROOT / "configs/default.json").read_text())
    scenarios = {"obstacle_detour", "free_offroad", "stop_and_go", "narrow_passage", "open_low_noise", "wrong_map", "fengtai_historical"}
    expected = {f"{s}_seed{seed}" for s in scenarios for seed in config["seeds"]}
    for run in (baseline, repeat):
        actual = {p.name for p in (run / "datasets").iterdir() if p.is_dir()}
        require(actual == expected, "Dataset set differs from all fixed scenarios and seeds")
    identical_inputs, identical_predictions = 0, 0
    for name in sorted(expected):
        for filename in ("map.json", "metadata.json", "observations.csv", "reference/trajectory.csv"):
            a, b = (r / "datasets" / name / filename for r in (baseline, repeat))
            require(a.read_bytes() == b.read_bytes(), f"Non-reproducible input: {name}/{filename}")
            identical_inputs += 1
        for method in ("map_only", "hmm"):
            a, b = (r / "results" / name / method / "predictions.csv" for r in (baseline, repeat))
            require(a.read_bytes() == b.read_bytes(), f"Non-reproducible prediction: {name}/{method}")
            identical_predictions += 1
    metrics_checked = 0
    original_metrics = json.loads((baseline / "results/metrics.json").read_text())
    require(len(original_metrics) == len(expected) * 3, "Missing method results")
    for row in original_metrics:
        method, name = row["method"], row["dataset"]
        folder = baseline / "results" / name / method
        if method != "raw":
            folder /= "evaluation"
        with (folder / f"{method}_errors.csv").open() as f:
            errors = list(csv.DictReader(f))
        require(len(errors) == row["n"] == 71, "Metric denominator omitted observations")
        # Recompute from coordinates, not the evaluation module's error column.
        values = [math.hypot(float(p["estimate_x_m"]) - float(p["reference_x_m"]),
                            float(p["estimate_y_m"]) - float(p["reference_y_m"])) for p in errors]
        values.sort()
        q = .95 * (len(values) - 1)
        q0 = int(q)
        calculated = {"rmse_m": math.sqrt(sum(v * v for v in values) / len(values)),
                      "mean_m": sum(values) / len(values), "median_m": values[len(values) // 2],
                      "p95_m": values[q0] * (1 - q + q0) + values[q0 + 1] * (q - q0),
                      "max_m": values[-1]}
        for key, val in calculated.items():
            require(math.isclose(val, row[key], abs_tol=1e-8, rel_tol=1e-9), f"Metric mismatch: {name}/{method}/{key}")
        if name.startswith("fengtai") and method != "raw":
            require(row["map_unknown_count"] == row["n"], "Historical map was reported as confirmed traversable")
        metrics_checked += 1
    repeat_metrics = json.loads((repeat / "results/metrics.json").read_text())
    strip = lambda row: {k: v for k, v in row.items() if not k.endswith("_s")}
    require([strip(r) for r in original_metrics] == [strip(r) for r in repeat_metrics], "Non-timing statistics changed between repeats")
    environment = json.loads((baseline / "results/environment.json").read_text())
    for name, digest in environment["source_sha256"].items():
        require(sha256(ROOT / name) == digest, f"Source changed since experiment: {name}")
    originals = json.loads((ROOT / "data/original_sources_sha256.json").read_text())
    for name, record in originals.items():
        require(sha256(ROOT.parent / name) == record["sha256"], f"Original material modified: {name}")
    return {"passed": True, "baseline": str(baseline), "repeat": str(repeat),
            "dataset_count": len(expected), "identical_input_files": identical_inputs,
            "byte_identical_prediction_files": identical_predictions,
            "metric_rows_independently_recomputed": metrics_checked,
            "matching_source_files": len(environment["source_sha256"]),
            "unchanged_original_files": len(originals),
            "timing_equality_required": False,
            "scope": "Reproducibility and arithmetic checks; not evidence of real-world accuracy"}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("baseline", type=Path)
    parser.add_argument("repeat", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError("Preserve verification records; use a new output")
    report = check(args.baseline.resolve(), args.repeat.resolve())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    write_json(args.output, report)
    print(json.dumps(report, ensure_ascii=False, indent=2))
