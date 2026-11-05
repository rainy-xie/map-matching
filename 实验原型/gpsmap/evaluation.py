"""Synthetic fixtures and independent evaluation. Never imported by inference.

References are analytical/piecewise-linear paths, not shortest paths or decoded
states. All fixture settings below are declared before looking at model results.
"""
from __future__ import annotations

from collections import Counter
import csv
import hashlib
import json
import math
from pathlib import Path
import re
from typing import Mapping

import numpy as np


SOURCE = "synthetic_design_v0.1; explicit experimental assumption"
SCENARIOS = ("obstacle_detour", "free_offroad", "stop_and_go", "narrow_passage",
             "open_low_noise", "wrong_map")


def _write_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
                    encoding="utf-8")


def _write_csv(path: Path, columns: list[str], rows) -> None:
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream, lineterminator="\n")
        writer.writerow(columns)
        for row in rows:
            writer.writerow([format(float(v), ".10f") if isinstance(v, (float, np.floating))
                             else v for v in row])


def _rectangle(x0, y0, x1, y1, *, kind="obstacle", passability="blocked") -> dict:
    return {"type": "Feature", "properties": {"kind": kind, "passability": passability,
            "source": SOURCE}, "geometry": {"type": "Polygon", "coordinates":
            [[[x0, y0], [x1, y0], [x1, y1], [x0, y1], [x0, y0]]]}}


def _base_map(name: str) -> dict:
    return {"name": name, "bounds": [0.0, 0.0, 200.0, 160.0],
            "crs": "LOCAL_SYNTHETIC_METRES", "source": SOURCE,
            "background": {"passability": "allowed", "source": SOURCE}, "features": []}


def _interpolate(t: np.ndarray, knots: list[list[float]]) -> np.ndarray:
    values = np.asarray(knots, dtype=float)
    return np.column_stack([np.interp(t, values[:, 0], values[:, j]) for j in (1, 2)])


def _fixture(name: str, sigma: float, fengtai_spec: dict | None = None):
    t = np.linspace(0.0, 140.0, 71)
    spec = _base_map(name)
    description = ""
    route: dict = {}
    bias = np.zeros((len(t), 2))
    if name == "obstacle_detour":
        spec["features"] = [_rectangle(80.0, 45.0, 120.0, 110.0)]
        knots = [[0, 20, 80], [25, 62, 80], [50, 68, 122], [90, 132, 122],
                 [115, 140, 80], [140, 180, 80]]
        truth = _interpolate(t, knots)
        route = {"kind": "hand_authored_time_waypoints", "knots_t_x_y": knots}
        description = "Manual off-road detour around a synthetic blocked rectangle; no routing solver used."
    elif name == "free_offroad":
        # Nonuniform time gaps are intentional and shared exactly by all methods.
        dt = np.resize(np.array([1.5, 2.0, 2.5]), 70)
        t = np.r_[0.0, np.cumsum(dt)]
        u = t / t[-1]
        truth = np.column_stack([20.0 + 160.0 * u, 88.0 + 24.0 * np.sin(2 * np.pi * u)])
        spec["features"] = [{"type": "Feature", "properties": {
            "kind": "decorative_road", "passability": "unknown", "source": SOURCE,
            "note": "Decorative line only; no verified road width or traversability polygon."},
            "geometry": {"type": "LineString", "coordinates": [[10, 35], [190, 35]]}}]
        route = {"kind": "analytic_curve", "formula": "x=20+160u; y=88+24sin(2*pi*u); u=t/t[-1]",
                 "dt_pattern_s": [1.5, 2.0, 2.5]}
        description = "Legal free movement away from the drawn road; no road-snapping assumption."
    elif name == "stop_and_go":
        knots = [[0, 25, 45], [45, 85, 85], [85, 85, 85], [140, 175, 115]]
        truth = _interpolate(t, knots)
        route = {"kind": "hand_authored_time_waypoints", "knots_t_x_y": knots,
                 "stationary_interval_s": [45, 85]}
        description = "A manually prescribed forty-second stop, followed by movement."
    elif name == "narrow_passage":
        spec["features"] = [_rectangle(90, 0, 110, 70), _rectangle(90, 86, 110, 160)]
        u = t / t[-1]
        truth = np.column_stack([20 + 160 * u, 78 + 2 * np.sin(2 * np.pi * u)])
        route = {"kind": "analytic_curve", "formula": "x=20+160u; y=78+2sin(2*pi*u)",
                 "passage_y_range_m": [70, 86], "passage_width_m": 16}
        description = "A 16 m synthetic passage, only four nominal 4 m grid cells across."
    elif name == "open_low_noise":
        sigma = 0.35
        u = t / t[-1]
        truth = np.column_stack([21.3 + 154.0 * u, 35.7 + 82.0 * u])
        route = {"kind": "analytic_line", "formula": "x=21.3+154u; y=35.7+82u"}
        description = "Weak map information and low GPS noise; grid quantization may worsen an already good observation."
    elif name == "wrong_map":
        # This rectangle is deliberately false: the reference world is open.
        spec["features"] = [_rectangle(70, 50, 130, 110, kind="deliberately_false_obstacle")]
        u = t / t[-1]
        truth = np.column_stack([20 + 160 * u, np.full_like(u, 80.0)])
        route = {"kind": "analytic_line_in_open_reference_world", "formula": "x=20+160u; y=80",
                 "map_error": "The model rectangle does not exist in the synthetic reference world."}
        description = "Incorrect map constraint can force detours, resets, or raw-GPS fallback; all points remain in metrics."
    elif name == "fengtai_historical":
        if fengtai_spec is None:
            raise ValueError("fengtai_spec required")
        spec = json.loads(json.dumps(fengtai_spec))
        x0, y0, x1, y1 = map(float, spec["bounds"])
        t = np.linspace(0.0, 210.0, 71)
        u = t / t[-1]
        truth = np.column_stack([x0 + (x1 - x0) * (0.2 + 0.6 * u),
                                y0 + (y1 - y0) * (0.48 + 0.12 * np.sin(2 * np.pi * u))])
        route = {"kind": "analytic_curve_on_unverified_historical_background",
                 "formula": "x=xmin+width*(.2+.6u); y=ymin+height*(.48+.12sin(2*pi*u))",
                 "real_world_feasibility": "unknown; this is not an observed athlete route"}
        description = "Synthetic coordinates on a historical map. No field position or passability validation."
    else:
        raise ValueError(f"Unknown scenario: {name}")
    return spec, t, truth, sigma, bias, route, description


def generate_suite(output_dir: str | Path, config: dict,
                   fengtai_spec: dict | None = None) -> list[Path]:
    """Generate all declared scenarios; refuse to overwrite any existing output.

    `sigma_m` is synthetic per-axis standard deviation, not a device accuracy
    estimate. Independent NumPy SeedSequence streams make scenarios reproducible.
    """
    output_dir = Path(output_dir)
    if output_dir.exists():
        raise FileExistsError(f"Preserve existing datasets: {output_dir}")
    seeds = config.get("seeds", [20261101, 20261102, 20261103])
    if not seeds or len(set(seeds)) != len(seeds):
        raise ValueError("seeds must be nonempty and unique")
    if any(isinstance(s, bool) or not isinstance(s, int) or s < 0 for s in seeds):
        raise ValueError("seeds must be nonnegative integers")
    sigma = float(config.get("nominal_observation_sigma_m", 6.0))
    if not math.isfinite(sigma) or sigma <= 0:
        raise ValueError("nominal_observation_sigma_m must be finite and positive")
    sizes = [float(config.get("synthetic_cell_size_m", 4.0)),
             float(config.get("fengtai_cell_size_m", 8.0))]
    if any(not math.isfinite(v) or v <= 0 for v in sizes):
        raise ValueError("cell sizes must be finite and positive")
    names = list(SCENARIOS) + (["fengtai_historical"] if fengtai_spec is not None else [])
    output_dir.mkdir(parents=True)
    datasets: list[Path] = []
    for scenario_index, name in enumerate(names):
        spec, t, truth, obs_sigma, bias, route, description = _fixture(name, sigma, fengtai_spec)
        for seed in seeds:
            folder = output_dir / f"{name}_seed{seed}"
            (folder / "reference").mkdir(parents=True)
            rng = np.random.default_rng(np.random.SeedSequence([seed, scenario_index]))
            observed = truth + rng.normal(0.0, obs_sigma, size=truth.shape) + bias
            _write_json(folder / "map.json", spec)
            _write_csv(folder / "reference" / "trajectory.csv", ["t_s", "x_m", "y_m"],
                       zip(t, truth[:, 0], truth[:, 1]))
            _write_csv(folder / "observations.csv", ["t_s", "x_m", "y_m", "sigma_m"],
                       zip(t, observed[:, 0], observed[:, 1], np.full(len(t), obs_sigma)))
            metadata = {"scenario": name, "seed": seed,
                        "label": "synthetic_on_historical_map" if name == "fengtai_historical" else "synthetic",
                        "dataset_version": "0.1.0", "n": len(t),
                        "cell_size_m": sizes[1 if name == "fengtai_historical" else 0],
                        "time_basis": "seconds relative to arbitrary synthetic start",
                        "coordinates": spec.get("crs", "local metres"),
                        "reference_source": "independent hand-authored or analytic route; no HMM or graph routing",
                        "reference_definition": route, "description": description,
                        "noise": {"kind": "independent isotropic Gaussian", "sigma_per_axis_m": obs_sigma,
                                  "bias_m": [0.0, 0.0], "rng": "numpy.default_rng / PCG64",
                                  "seed_sequence_entropy": [seed, scenario_index],
                                  "source": "synthetic engineering setting, not measured GPS error"},
                        "parameter_policy": "fixed before model results; no result-based selection",
                        "split": "mechanism_suite_not_generalization_test",
                        "config_sha256": hashlib.sha256(json.dumps(config, sort_keys=True,
                                                    ensure_ascii=False).encode()).hexdigest()}
            _write_json(folder / "metadata.json", metadata)
            datasets.append(folder)
    return datasets


def _read_trajectory(path: str | Path) -> tuple[np.ndarray, list[dict]]:
    with Path(path).open(newline="", encoding="utf-8") as stream:
        reader = csv.DictReader(stream)
        if reader.fieldnames is None or not {"t_s", "x_m", "y_m"}.issubset(reader.fieldnames):
            raise ValueError(f"Missing trajectory columns in {path}")
        rows = list(reader)
    if not rows:
        raise ValueError(f"Empty trajectory: {path}")
    try:
        points = np.array([[float(row[k]) for k in ("t_s", "x_m", "y_m")] for row in rows])
    except (ValueError, TypeError) as exc:
        raise ValueError(f"Invalid numeric trajectory: {path}") from exc
    if not np.isfinite(points).all() or np.any(np.diff(points[:, 0]) <= 0):
        raise ValueError(f"Nonfinite values or nonincreasing timestamps: {path}")
    return points, rows


def _aligned(reference: np.ndarray, predicted: np.ndarray) -> None:
    if len(reference) != len(predicted) or not np.allclose(reference[:, 0], predicted[:, 0],
                                                        rtol=0.0, atol=1e-8):
        raise ValueError("Every reference timestamp must have exactly one corresponding estimate; no filtering")


def evaluate_run(dataset_dir: str | Path, prediction_csv: str | Path,
                 output_dir: str | Path, method_name: str) -> dict:
    """Evaluate every time step, including explicit inference failures/fallbacks."""
    if not re.fullmatch(r"[A-Za-z0-9_-]+", method_name):
        raise ValueError("method_name must be a simple filename-safe identifier")
    dataset_dir, output_dir = Path(dataset_dir), Path(output_dir)
    reference, _ = _read_trajectory(dataset_dir / "reference" / "trajectory.csv")
    predicted, rows = _read_trajectory(prediction_csv)
    _aligned(reference, predicted)
    errors = np.linalg.norm(predicted[:, 1:] - reference[:, 1:], axis=1)
    states = [row.get("status") or "raw" for row in rows]
    metadata = json.loads((dataset_dir / "metadata.json").read_text(encoding="utf-8"))
    result = {"method": method_name, "scenario": metadata["scenario"], "seed": metadata["seed"],
              "label": metadata["label"], "n": len(errors),
              "rmse_m": float(np.sqrt(np.mean(errors ** 2))), "mean_m": float(np.mean(errors)),
              "median_m": float(np.median(errors)), "p95_m": float(np.percentile(errors, 95)),
              "max_m": float(np.max(errors)), "status_counts": dict(sorted(Counter(states).items())),
              "failure_count": sum(s in {"no_candidates", "reset_unreachable"} for s in states),
              "map_unknown_count": states.count("map_unknown"),
              "aggregation": "all timestamps, unweighted; no success-only exclusion",
              "percentile_method": "numpy linear"}
    output_dir.mkdir(parents=True, exist_ok=True)
    error_path = output_dir / f"{method_name}_errors.csv"
    summary_path = output_dir / f"{method_name}_metrics.json"
    if error_path.exists() or summary_path.exists():
        raise FileExistsError("Preserve prior evaluation output; choose a new directory or method name")
    _write_csv(error_path, ["t_s", "reference_x_m", "reference_y_m", "estimate_x_m", "estimate_y_m",
                           "error_m", "status"],
               [(reference[i, 0], reference[i, 1], reference[i, 2], predicted[i, 1], predicted[i, 2],
                 errors[i], states[i]) for i in range(len(reference))])
    _write_json(summary_path, result)
    return result


def _draw_geometry(ax, geometry: dict, properties: dict) -> None:
    from matplotlib.patches import Polygon as PolygonPatch
    kind = geometry["type"]
    coords = geometry.get("coordinates", [])
    blocked = properties.get("passability") == "blocked"
    unknown = properties.get("passability", "unknown") == "unknown"
    if kind == "GeometryCollection":
        for g in geometry.get("geometries", []):
            _draw_geometry(ax, g, properties)
    elif kind == "MultiPolygon":
        for poly in coords:
            _draw_geometry(ax, {"type": "Polygon", "coordinates": poly}, properties)
    elif kind == "Polygon":
        # Explicit holes are drawn with the axes background, keeping islands visible.
        face = "#c8c3bb" if blocked else "#dbe9e3"
        if "water" in properties.get("kind", "").lower():
            face = "#d7e9f2"
        for index, ring in enumerate(coords):
            ax.add_patch(PolygonPatch(ring, closed=True,
                         facecolor=face if index == 0 else ax.get_facecolor(),
                         edgecolor="#848d95", linewidth=.55,
                         hatch="///" if unknown and index == 0 else None, alpha=.75, zorder=0))
    elif kind in {"LineString", "MultiLineString"}:
        lines = [coords] if kind == "LineString" else coords
        for line in lines:
            a = np.asarray(line, dtype=float)
            if len(a):
                ax.plot(a[:, 0], a[:, 1], color="#9ca3af", lw=.9, alpha=.7, zorder=1)


def plot_comparison(dataset_dir: str | Path, predictions: Mapping[str, Path],
                    output_path: str | Path) -> None:
    """Save an overlay and per-time error plot, explicitly marked SYNTHETIC."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Patch

    dataset_dir, output_path = Path(dataset_dir), Path(output_path)
    if output_path.exists():
        raise FileExistsError(f"Preserve plot: {output_path}")
    spec = json.loads((dataset_dir / "map.json").read_text(encoding="utf-8"))
    metadata = json.loads((dataset_dir / "metadata.json").read_text(encoding="utf-8"))
    truth, _ = _read_trajectory(dataset_dir / "reference" / "trajectory.csv")
    observed, _ = _read_trajectory(dataset_dir / "observations.csv")
    _aligned(truth, observed)
    fig, (ax, error_ax) = plt.subplots(1, 2, figsize=(12.8, 5.4),
                                    gridspec_kw={"width_ratios": [1.12, 1]})
    fig.patch.set_facecolor("#f8fafc")
    ax.set_facecolor("#ffffff")
    for feature in spec.get("features", []):
        _draw_geometry(ax, feature["geometry"], feature.get("properties", {}))
    ax.plot(truth[:, 1], truth[:, 2], color="#151d2b", lw=2.2, label="Synthetic reference", zorder=5)
    ax.plot(observed[:, 1], observed[:, 2], ".-", color="#e09146", alpha=.65,
            lw=.65, ms=3, label="Raw GPS", zorder=3)
    error_ax.plot(truth[:, 0], np.linalg.norm(observed[:, 1:] - truth[:, 1:], axis=1),
                  color="#e09146", lw=1.1, label="Raw GPS")
    colors = ["#286eaa", "#b34a84", "#218775", "#7d69b0"]
    for index, (name, path) in enumerate(predictions.items()):
        estimate, rows = _read_trajectory(path)
        _aligned(truth, estimate)
        # Raw observations are always shown, even when the caller also supplies raw baseline.
        if Path(path).resolve() == (dataset_dir / "observations.csv").resolve():
            continue
        color = colors[index % len(colors)]
        states = [row.get("status", "ok") for row in rows]
        line_coordinates = []
        for i, state in enumerate(states):
            # A decoder reset or missing candidates does not establish a connecting
            # path. Show the fallback coordinate, but never join across that gap.
            if i and (state in {"no_candidates", "reset_unreachable"}
                      or states[i - 1] == "no_candidates"):
                line_coordinates.append((np.nan, np.nan))
            line_coordinates.append((estimate[i, 1], estimate[i, 2]))
        line_coordinates = np.asarray(line_coordinates)
        ax.plot(line_coordinates[:, 0], line_coordinates[:, 1], lw=1.5, color=color,
                alpha=.9, label=name, zorder=4)
        error_ax.plot(truth[:, 0], np.linalg.norm(estimate[:, 1:] - truth[:, 1:], axis=1),
                      lw=1.15, color=color, label=name)
        failed = np.array([row.get("status") in {"no_candidates", "reset_unreachable"} for row in rows])
        if failed.any():
            ax.scatter(estimate[failed, 1], estimate[failed, 2], marker="x", s=30, color="#b91c1c",
                       linewidths=1.3, zorder=6, label=f"{name} fallback/reset")
    ax.scatter(truth[0, 1], truth[0, 2], marker="o", s=38, facecolor="white", edgecolor="#151d2b", zorder=7)
    ax.set_aspect("equal", adjustable="box")
    xmin, ymin, xmax, ymax = spec["bounds"]
    ax.set_xlim(xmin, xmax)
    ax.set_ylim(ymin, ymax)
    ax.set_xlabel("Local x / m")
    ax.set_ylabel("Local y / m")
    ax.set_title("Trajectory overlay")
    error_ax.set_title("Error against synthetic reference (all timestamps)")
    error_ax.set_xlabel("Elapsed time / s")
    error_ax.set_ylabel("Position error / m")
    for item in (ax, error_ax):
        item.grid(alpha=.17)
        item.tick_params(labelsize=8)
    handles, labels = ax.get_legend_handles_labels()
    if any(f.get("properties", {}).get("passability") == "blocked" for f in spec.get("features", [])):
        handles.append(Patch(facecolor="#c8c3bb", label="Assumed obstacle in model map"))
        labels.append("Assumed obstacle in model map")
    if metadata["label"] == "synthetic_on_historical_map":
        handles.append(Patch(facecolor="#dbe9e3", hatch="///", label="Historical features; passability unknown"))
        labels.append("Historical features; passability unknown")
    ax.legend(handles, labels, fontsize=7, loc="best", framealpha=.9)
    error_ax.legend(fontsize=8, loc="best")
    fig.suptitle(f"SYNTHETIC | {metadata['scenario']} | seed {metadata['seed']}",
                 x=.06, ha="left", fontsize=14, fontweight="bold")
    footer = ("Historical map alignment and passability are unverified; route and observations are synthetic."
              if metadata["label"] == "synthetic_on_historical_map" else
              "Mechanism experiment only. Reference route is independent of HMM / graph routing; no field-accuracy claim.")
    if metadata["scenario"] == "wrong_map":
        footer = "Deliberate map error: the shaded obstacle does not exist in the synthetic reference world. All failures retained."
    fig.text(.06, .025, footer, fontsize=8, color="#475569")
    fig.tight_layout(rect=(0, .055, 1, .94))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=150)
    plt.close(fig)
