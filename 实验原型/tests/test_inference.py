"""Decoder correctness tests with independent exhaustive sequence enumeration."""
import itertools
import math
import unittest

from gpsmap.contracts import Candidate, Connection, ModelConfig, Observation
from gpsmap.inference import infer, map_only, observation_log_score


class TinyMap:
    def __init__(self, positions=(0.0, 4.0, 8.0), unknown_edges=False, disconnected=False):
        self.nodes = [Candidate(i, x, 0.0, str(i), "allowed")
                      for i, x in enumerate(positions)]
        self.spec = {}
        self.unknown_edges = unknown_edges
        self.disconnected = disconnected
        self.calls = 0

    def candidates(self, x_m, y_m, radius_m, max_candidates):
        return sorted([c for c in self.nodes if math.hypot(c.x_m - x_m, c.y_m - y_m) <= radius_m],
                      key=lambda c: (math.hypot(c.x_m - x_m, c.y_m - y_m), c.node_id))[:max_candidates]

    def connection(self, a, b):
        self.calls += 1
        if self.disconnected and a.node_id != b.node_id:
            return Connection("unreachable", math.inf)
        return Connection("unknown" if self.unknown_edges else "reachable",
                          math.hypot(a.x_m - b.x_m, a.y_m - b.y_m))

    def statistics(self):
        return {"nodes": len(self.nodes)}


class InferenceTests(unittest.TestCase):
    def test_gaussian_density_in_two_dimensions(self):
        observation = Observation(0, 0, 0, 3)
        candidate = Candidate(0, 0, 0, "a", "allowed")
        self.assertAlmostEqual(observation_log_score(observation, candidate),
                               -math.log(2 * math.pi) - 2 * math.log(3))

    def test_viterbi_matches_independent_exhaustive_enumeration(self):
        spatial_map = TinyMap()
        config = ModelConfig(candidate_radius_m=20, motion_sigma_mps=1.7, max_speed_mps=6)
        observations = [Observation(0, 2.8, 0.5, 2.1), Observation(1.3, 7.1, -0.4, 2.8),
                        Observation(3.7, 4.3, 0.1, 1.5), Observation(4.5, 0.1, 0.0, 1.2)]

        def score(path):
            value = 0.0
            for i, candidate in enumerate(path):
                obs = observations[i]
                value -= ((candidate.x_m - obs.x_m) ** 2 + (candidate.y_m - obs.y_m) ** 2) / (2 * obs.sigma_m ** 2)
                if i:
                    speed = abs(candidate.x_m - path[i - 1].x_m) / (obs.t_s - observations[i - 1].t_s)
                    if speed > config.max_speed_mps:
                        return -math.inf
                    value -= speed ** 2 / (2 * config.motion_sigma_mps ** 2)
            return value

        paths = list(itertools.product(spatial_map.nodes, repeat=len(observations)))
        expected = max(paths, key=score)
        actual, diagnostics = infer(observations, spatial_map, config)
        self.assertEqual([e.x_m for e in actual], [c.x_m for c in expected])
        self.assertEqual([e.t_s for e in actual], [o.t_s for o in observations])
        self.assertEqual(diagnostics["segments"], 1)
        self.assertFalse(diagnostics["score_is_calibrated_probability"])

    def test_future_observations_can_change_first_estimate(self):
        spatial_map = TinyMap((0.0, 4.0))
        config = ModelConfig(candidate_radius_m=10, motion_sigma_mps=0.25)
        observations = [Observation(0, 3, 0, 3), Observation(1, 0, 0, 0.5)]
        one, _ = infer(observations[:1], spatial_map, config)
        whole, _ = infer(observations, spatial_map, config)
        self.assertEqual(one[0].x_m, 4)
        self.assertEqual(whole[0].x_m, 0)

    def test_no_candidates_retains_raw_coordinate_and_breaks_chain(self):
        observations = [Observation(0, 1, 0, 1), Observation(1, 1000, 4, 1), Observation(2, 7, 0, 1)]
        result, diagnostics = infer(observations, TinyMap(), ModelConfig(candidate_radius_m=2))
        self.assertEqual([e.x_m for e in result], [0, 1000, 8])
        self.assertEqual(result[1].y_m, 4)
        self.assertEqual(result[1].status, "no_candidates")
        self.assertEqual(result[1].candidate_count, 0)
        self.assertEqual(diagnostics["no_candidate_indices"], [1])
        self.assertEqual(diagnostics["segments"], 2)

    def test_disconnected_restart_preserves_completed_segment(self):
        spatial_map = TinyMap((0.0, 10.0), disconnected=True)
        observations = [Observation(0, 0, 0, 1), Observation(2, 0.1, 0, 1),
                        Observation(4, 10, 0, 1), Observation(6, 10.1, 0, 1)]
        result, diagnostics = infer(observations, spatial_map, ModelConfig(candidate_radius_m=1))
        self.assertEqual([e.x_m for e in result], [0, 0, 10, 10])
        self.assertEqual([e.status for e in result], ["ok", "ok", "reset_unreachable", "ok"])
        self.assertEqual(diagnostics["reset_indices"], [2])
        self.assertEqual(diagnostics["segments"], 2)

    def test_actual_time_difference_controls_speed_gate(self):
        spatial_map = TinyMap((0.0, 10.0))
        config = ModelConfig(candidate_radius_m=1, max_speed_mps=6)
        slow, _ = infer([Observation(0, 0, 0, 1), Observation(2, 10, 0, 1)], spatial_map, config)
        fast, _ = infer([Observation(0, 0, 0, 1), Observation(0.5, 10, 0, 1)], spatial_map, config)
        self.assertEqual(slow[1].status, "ok")
        self.assertEqual(fast[1].status, "reset_unreachable")

    def test_unknown_path_is_not_reported_as_confirmed(self):
        spatial_map = TinyMap((0.0, 10.0), unknown_edges=True)
        result, diagnostics = infer([Observation(0, 0, 0, 1), Observation(2, 10, 0, 1)],
                                    spatial_map, ModelConfig(candidate_radius_m=1))
        self.assertEqual(result[1].status, "map_unknown")
        self.assertEqual(diagnostics["unknown_path_indices"], [1])

    def test_speed_boundary_and_unknown_restart_priority(self):
        spatial_map = TinyMap((0.0, 10.0))
        spatial_map.nodes = [Candidate(c.node_id, c.x_m, c.y_m, c.region_id, "unknown")
                             for c in spatial_map.nodes]
        observations = [Observation(0, 0, 0, 1), Observation(1.25, 10, 0, 1),
                        Observation(1.875, 0, 0, 1)]
        result, diagnostics = infer(observations, spatial_map,
                                    ModelConfig(candidate_radius_m=1, max_speed_mps=8))
        # Exactly 8 m/s is allowed; the next step is 16 m/s and must restart.
        self.assertEqual([e.status for e in result],
                         ["map_unknown", "map_unknown", "reset_unreachable"])
        self.assertEqual(diagnostics["reset_indices"], [2])
        # The primary reset status must not erase the unknown-map provenance.
        self.assertEqual(diagnostics["unknown_path_indices"], [0, 1, 2])

    def test_map_only_has_no_movement_queries(self):
        spatial_map = TinyMap()
        result, diagnostics = map_only([Observation(0, 3, 0, 1), Observation(1, 7, 0, 1)],
                                       spatial_map, ModelConfig())
        self.assertEqual([e.x_m for e in result], [4, 8])
        self.assertEqual(spatial_map.calls, 0)
        self.assertEqual(diagnostics["connection_queries"], 0)

    def test_empty_sequence_and_single_unknown_candidate(self):
        result, diagnostics = infer([], TinyMap(), ModelConfig())
        self.assertEqual(result, [])
        self.assertEqual(diagnostics["segments"], 0)
        spatial_map = TinyMap((0.0,))
        spatial_map.nodes = [Candidate(0, 0, 0, "0", "unknown")]
        result, _ = infer([Observation(0, 0, 0, 1)], spatial_map, ModelConfig())
        self.assertEqual(result[0].status, "map_unknown")

    def test_invalid_numeric_and_time_inputs_rejected(self):
        for sigma in (0, -1, math.inf, math.nan):
            with self.assertRaises(ValueError):
                Observation(0, 0, 0, sigma)
        for second in (0, -1):
            observations = [Observation(0, 0, 0, 1), Observation(second, 1, 0, 1)]
            for method in (infer, map_only):
                with self.assertRaises(ValueError):
                    method(observations, TinyMap(), ModelConfig())
        with self.assertRaises(ValueError):
            ModelConfig(max_speed_mps=0)

    def test_invalid_map_distance_rejected(self):
        spatial_map = TinyMap((0.0,))
        spatial_map.connection = lambda a, b: Connection("reachable", math.nan)
        with self.assertRaises(ValueError):
            infer([Observation(0, 0, 0, 1), Observation(1, 0, 0, 1)], spatial_map, ModelConfig())

    def test_ties_are_deterministic(self):
        spatial_map = TinyMap((-1.0, 1.0))
        observations = [Observation(0, 0, 0, 1), Observation(1, 0, 0, 1)]
        first, _ = infer(observations, spatial_map, ModelConfig())
        spatial_map.nodes.reverse()
        second, _ = infer(observations, spatial_map, ModelConfig())
        self.assertEqual(first, second)
        self.assertEqual([e.x_m for e in first], [-1, -1])


if __name__ == "__main__":
    unittest.main()
