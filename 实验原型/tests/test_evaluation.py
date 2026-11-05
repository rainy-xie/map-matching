import csv
import json
from pathlib import Path
import tempfile
import unittest

import numpy as np
from shapely.geometry import LineString, shape

from gpsmap.evaluation import SCENARIOS, evaluate_run, generate_suite, plot_comparison


class EvaluationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.config = {"seeds": [101, 102], "nominal_observation_sigma_m": 6,
                       "synthetic_cell_size_m": 4, "fengtai_cell_size_m": 8}

    def tearDown(self):
        self.temp.cleanup()

    def read(self, path):
        with path.open(newline="", encoding="utf-8") as stream:
            return list(csv.DictReader(stream))

    def test_reproducibility_and_reference_independence(self):
        a = generate_suite(self.root / "a", self.config)
        b = generate_suite(self.root / "b", self.config)
        self.assertEqual(len(a), 12)
        self.assertTrue(a[0].name.startswith("obstacle_detour"))
        for left, right in zip(a, b):
            for filename in ["map.json", "observations.csv", "reference/trajectory.csv", "metadata.json"]:
                self.assertEqual((left / filename).read_bytes(), (right / filename).read_bytes())
        for i in range(0, len(a), 2):
            self.assertEqual((a[i] / "reference/trajectory.csv").read_bytes(),
                             (a[i + 1] / "reference/trajectory.csv").read_bytes())
            self.assertNotEqual((a[i] / "observations.csv").read_bytes(),
                                (a[i + 1] / "observations.csv").read_bytes())
            self.assertEqual(set(self.read(a[i] / "observations.csv")[0]), {"t_s", "x_m", "y_m", "sigma_m"})
        with self.assertRaises(FileExistsError):
            generate_suite(self.root / "a", self.config)

    def test_reference_geometry_and_explicit_wrong_map(self):
        folders = generate_suite(self.root / "fixtures", {**self.config, "seeds": [101]})
        for folder in folders:
            meta = json.loads((folder / "metadata.json").read_text())
            spec = json.loads((folder / "map.json").read_text())
            coords = [(float(r["x_m"]), float(r["y_m"])) for r in self.read(folder / "reference/trajectory.csv")]
            track = LineString(coords)
            obstacles = [shape(f["geometry"]) for f in spec["features"]
                         if f["properties"]["passability"] == "blocked"]
            if meta["scenario"] == "wrong_map":
                self.assertTrue(any(track.intersects(g) for g in obstacles))
                self.assertIn("map_error", meta["reference_definition"])
            else:
                self.assertFalse(any(track.intersects(g) for g in obstacles))
            self.assertEqual(meta["label"], "synthetic")
            self.assertEqual(meta["n"], 71)
        free = folders[list(SCENARIOS).index("free_offroad")]
        times = [float(r["t_s"]) for r in self.read(free / "observations.csv")]
        self.assertGreater(len(set(np.diff(times))), 1)

    def test_known_errors_include_failed_rows(self):
        folder = self.root / "manual"
        (folder / "reference").mkdir(parents=True)
        (folder / "reference/trajectory.csv").write_text("t_s,x_m,y_m\n0,0,0\n2,0,0\n4,0,0\n")
        (folder / "metadata.json").write_text(json.dumps({"scenario": "manual", "seed": 1, "label": "synthetic"}))
        pred = folder / "prediction.csv"
        pred.write_text("t_s,x_m,y_m,status\n0,3,4,ok\n2,0,0,no_candidates\n4,0,10,reset_unreachable\n")
        report = evaluate_run(folder, pred, self.root / "metrics", "hmm")
        self.assertEqual(report["n"], 3)
        self.assertAlmostEqual(report["rmse_m"], np.sqrt(125 / 3))
        self.assertAlmostEqual(report["mean_m"], 5)
        self.assertAlmostEqual(report["median_m"], 5)
        self.assertAlmostEqual(report["p95_m"], 9.5)
        self.assertEqual(report["max_m"], 10)
        self.assertEqual(report["failure_count"], 2)
        self.assertEqual(len(self.read(self.root / "metrics/hmm_errors.csv")), 3)
        with self.assertRaises(FileExistsError):
            evaluate_run(folder, pred, self.root / "metrics", "hmm")

    def test_timestamp_and_nonfinite_validation(self):
        folder = generate_suite(self.root / "fixtures", {**self.config, "seeds": [101]})[0]
        malformed = self.root / "bad.csv"
        malformed.write_text("t_s,x_m,y_m\n0,0,0\n2,1,1\n")
        with self.assertRaises(ValueError):
            evaluate_run(folder, malformed, self.root / "badmetrics", "bad")
        malformed.write_text("t_s,x_m,y_m\n0,nan,0\n2,1,1\n")
        with self.assertRaises(ValueError):
            evaluate_run(folder, malformed, self.root / "badmetrics", "bad")
        malformed.write_text("t_s,x_m,y_m\n0,0,0\n0,1,1\n")
        with self.assertRaises(ValueError):
            evaluate_run(folder, malformed, self.root / "badmetrics", "bad")

    def test_real_background_stays_unknown_and_synthetic(self):
        spec = {"name": "historical", "bounds": [0, 0, 400, 400], "crs": "local UTM metres",
                "source": "historical, unverified", "background": {"passability": "unknown"}, "features": []}
        folders = generate_suite(self.root / "fixtures", {**self.config, "seeds": [101]}, spec)
        self.assertEqual(len(folders), 7)
        meta = json.loads((folders[-1] / "metadata.json").read_text())
        self.assertEqual(meta["label"], "synthetic_on_historical_map")
        self.assertEqual(meta["cell_size_m"], 8)
        self.assertEqual(json.loads((folders[-1] / "map.json").read_text())["background"]["passability"], "unknown")

    def test_all_fixture_maps_construct_with_shared_map_interface(self):
        from gpsmap.spatial import GridMap
        folders = generate_suite(self.root / "fixtures", {**self.config, "seeds": [101]})
        for folder in folders:
            spec = json.loads((folder / "map.json").read_text())
            grid = GridMap(spec, 4.0)
            self.assertGreater(len(grid.nodes), 0, folder.name)
        free = folders[list(SCENARIOS).index("free_offroad")]
        road = json.loads((free / "map.json").read_text())["features"][0]
        self.assertEqual(road["properties"]["passability"], "unknown")

    def test_baseline_and_plot(self):
        folder = generate_suite(self.root / "fixtures", {**self.config, "seeds": [101]})[0]
        metrics = evaluate_run(folder, folder / "observations.csv", self.root / "metrics", "raw_gps")
        self.assertGreater(metrics["rmse_m"], 0)
        self.assertEqual(metrics["status_counts"], {"raw": 71})
        path = self.root / "plot.png"
        plot_comparison(folder, {}, path)
        self.assertTrue(path.read_bytes().startswith(b"\x89PNG\r\n\x1a\n"))
        self.assertGreater(path.stat().st_size, 10000)


if __name__ == "__main__":
    unittest.main()
