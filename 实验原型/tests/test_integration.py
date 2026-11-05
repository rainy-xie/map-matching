"""Boundary tests exercise separate inference processes, not only module mocks."""
import csv
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from gpsmap.io import load_observations

ROOT = Path(__file__).resolve().parents[1]


class IntegrationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.observations = self.root / "observations.csv"
        self.observations.write_text("t_s,x_m,y_m,sigma_m\n0,3,3,2\n2,8,6,2\n5,12,12,2\n")
        self.map = self.root / "map.json"
        self.map.write_text(json.dumps({"name": "integration", "bounds": [0, 0, 20, 20],
            "crs": "LOCAL_SYNTHETIC_METRES", "source": "test", "background":
            {"passability": "unknown", "source": "unverified test fixture"}, "features": []}))

    def tearDown(self):
        self.temp.cleanup()

    def run_model(self, name, observations=None):
        return subprocess.run([sys.executable, "-m", "gpsmap", "infer", "--observations",
            str(observations or self.observations), "--map", str(self.map), "--cell-size", "4",
            "--output", str(self.root / name)], cwd=ROOT, capture_output=True, text=True)

    def test_inference_ignores_changed_and_absent_reference(self):
        reference = self.root / "reference"
        reference.mkdir()
        truth = reference / "trajectory.csv"
        truth.write_text("t_s,x_m,y_m\n0,0,0\n2,0,0\n5,0,0\n")
        self.assertEqual(self.run_model("a").returncode, 0)
        truth.write_text("This is deliberately invalid reference data, unavailable to the model")
        self.assertEqual(self.run_model("b").returncode, 0)
        truth.unlink()
        reference.rmdir()
        self.assertEqual(self.run_model("c").returncode, 0)
        expected = (self.root / "a/predictions.csv").read_bytes()
        self.assertEqual(expected, (self.root / "b/predictions.csv").read_bytes())
        self.assertEqual(expected, (self.root / "c/predictions.csv").read_bytes())
        with (self.root / "a/predictions.csv").open() as f:
            rows = list(csv.DictReader(f))
        self.assertEqual([r["status"] for r in rows], ["map_unknown"] * 3)

    def test_reference_path_is_denied_and_output_not_overwritten(self):
        reference = self.root / "reference"
        reference.mkdir()
        fake_observation = reference / "observations.csv"
        fake_observation.write_bytes(self.observations.read_bytes())
        failed = self.run_model("denied", fake_observation)
        self.assertNotEqual(failed.returncode, 0)
        self.assertIn("forbidden to open the reference", failed.stderr)
        self.assertEqual(self.run_model("once").returncode, 0)
        repeated = self.run_model("once")
        self.assertNotEqual(repeated.returncode, 0)
        self.assertIn("FileExistsError", repeated.stderr)

    def test_observations_reject_reference_columns_and_invalid_time(self):
        for text in ("t_s,x_m,y_m,sigma_m,truth_x\n0,0,0,1,3\n",
                     "t_s,x_m,y_m,sigma_m\n0,0,0,1\n0,1,1,1\n",
                     "t_s,x_m,y_m,sigma_m\n0,nan,0,1\n"):
            self.observations.write_text(text)
            with self.assertRaises(ValueError):
                load_observations(self.observations)


if __name__ == "__main__":
    unittest.main()
