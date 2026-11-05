import json
import math
from pathlib import Path
import tempfile
import unittest

from shapely.geometry import Point, box, mapping

from gpsmap.spatial import GridMap


def fixture(features=None, background="allowed", bounds=None):
    return {"name": "test", "bounds": bounds or [0, 0, 20, 20], "crs": "LOCAL_METRES",
            "source": "synthetic test", "background": {"passability": background, "source": "synthetic test"},
            "features": features or []}


def feature(geom, status):
    return {"type": "Feature", "geometry": mapping(geom),
            "properties": {"kind": "test_area", "passability": status, "source": "synthetic test"}}


def closest(grid, x, y):
    return grid.candidates(x, y, 10, 1)[0]


class SpatialTests(unittest.TestCase):
    def test_multicell_distance_and_cache(self):
        grid = GridMap(fixture(), 4)
        a, b = closest(grid, 2, 2), closest(grid, 18, 18)
        result = grid.connection(a, b)
        self.assertEqual(result.status, "reachable")
        self.assertAlmostEqual(result.distance_m, math.sqrt(2) * 16)
        grid.connection(a, closest(grid, 10, 10))
        self.assertEqual(grid.statistics()["dijkstra_runs"], 1)

    def test_obstacle_detour_and_disconnection(self):
        obstacle = feature(box(8, 4, 12, 16), "blocked")
        grid = GridMap(fixture([obstacle]), 4)
        a, b = closest(grid, 2, 10), closest(grid, 18, 10)
        self.assertGreater(grid.connection(a, b).distance_m, 16)
        self.assertTrue(all(not box(8, 4, 12, 16).covers(Point(n.x_m, n.y_m)) for n in grid.nodes))
        wall = GridMap(fixture([feature(box(8, 0, 12, 20), "blocked")]), 4)
        connection = wall.connection(closest(wall, 2, 10), closest(wall, 18, 10))
        self.assertEqual(connection.status, "unreachable")
        self.assertTrue(math.isinf(connection.distance_m))

    def test_diagonal_cannot_cut_blocked_corner(self):
        grid = GridMap(fixture([feature(box(3, 3, 5, 5), "blocked")], bounds=[0, 0, 8, 8]), 4)
        self.assertAlmostEqual(grid.connection(closest(grid, 2, 2), closest(grid, 6, 6)).distance_m, 8)

    def test_unknown_in_middle_is_retained(self):
        grid = GridMap(fixture([feature(box(8, 0, 12, 20), "unknown")]), 4)
        a, b = closest(grid, 2, 10), closest(grid, 18, 10)
        self.assertEqual(a.passability, "allowed")
        self.assertEqual(b.passability, "allowed")
        self.assertEqual(grid.connection(a, b).status, "unknown")
        all_unknown = GridMap(fixture(background="unknown"), 4)
        self.assertEqual(all_unknown.connection(closest(all_unknown, 2, 2), closest(all_unknown, 18, 18)).status, "unknown")

    def test_unknown_edge_without_unknown_endpoint(self):
        grid = GridMap(fixture([feature(box(7, 0, 7.5, 20), "unknown")]), 4)
        a, b = closest(grid, 6, 10), closest(grid, 10, 10)
        self.assertEqual((a.passability, b.passability), ("allowed", "allowed"))
        self.assertEqual(grid.connection(a, b).status, "unknown")

    def test_subgrid_gap_can_be_lost(self):
        # A continuous 1 m gap exists at y=9, but this 4 m grid has no centre
        # in the gap. This is an intentional, recorded baseline limitation.
        obstacles = [feature(box(8, 0, 12, 8.5), "blocked"),
                     feature(box(8, 9.5, 12, 20), "blocked")]
        grid = GridMap(fixture(obstacles), 4)
        self.assertEqual(grid.connection(closest(grid, 2, 10), closest(grid, 18, 10)).status,
                         "unreachable")

    def test_radius_order_boundary_and_foreign_candidate(self):
        grid = GridMap(fixture(), 4)
        nodes = grid.candidates(4, 4, 3, 10)
        self.assertEqual([n.node_id for n in nodes], [0, 1, 5, 6])
        self.assertEqual(grid.candidates(-.1, 4, 100, 10), [])
        self.assertEqual(grid.candidates(4, 4, 1, 10), [])
        self.assertTrue(grid.candidates(0, 0, 3, 10))
        self.assertTrue(grid.candidates(20, 20, 3, 10))
        other = GridMap(fixture(background="unknown"), 4)
        with self.assertRaises(ValueError):
            grid.connection(nodes[0], other.nodes[0])
        with self.assertRaises(ValueError):
            grid.candidates(float('nan'), 1, 10, 1)

    def test_partial_boundary_cells_and_provenance_export(self):
        grid = GridMap(fixture([feature(box(0, 0, 1, 1), "blocked")], bounds=[0, 0, 10, 7]), 4)
        self.assertEqual(grid.statistics()["region_count"], 6)
        self.assertEqual((grid.nodes[-1].x_m, grid.nodes[-1].y_m), (9, 5.5))
        with tempfile.TemporaryDirectory() as temp:
            path = grid.export_regions(Path(temp) / "regions.geojson")
            data = json.loads(path.read_text())
            props = data["features"][0]["properties"]
            self.assertTrue(props["intersects_blocked_geometry"])
            self.assertEqual(props["centre_passability"], "allowed")
            self.assertEqual(props["overlapping_features"][0]["source"], "synthetic test")


if __name__ == "__main__":
    unittest.main()
