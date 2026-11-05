"""Uniform spatial baseline; explicit coordinates and conservative obstacle edges.

This graph is a computational approximation. Unknown traversability is retained,
not promoted to evidence of accessibility. No trajectory/reference is read here.
"""
from __future__ import annotations

from collections import OrderedDict
from copy import deepcopy
import heapq
import json
import math
from pathlib import Path

import numpy as np
from shapely.geometry import LineString, Point, box, mapping, shape
from shapely.ops import unary_union
from shapely.prepared import prep

from .contracts import Candidate, Connection


class GridMap:
    """Cell-centre graph with eight neighbours and cached source-node Dijkstra.

    Cell size affects candidate quantization and connectivity. Obstacles exclude
    covered centres and every intersecting edge, including boundary contact.
    Remaining cells can still overlap obstacles: exported properties make that
    explicit; a cell is not a claim that its entire area is traversable.
    """

    def __init__(self, spec: dict, cell_size_m: float):
        if not math.isfinite(cell_size_m) or cell_size_m <= 0:
            raise ValueError("cell_size_m must be finite and positive")
        self.spec = deepcopy(spec)
        bounds = tuple(float(v) for v in spec["bounds"])
        if len(bounds) != 4 or not all(math.isfinite(v) for v in bounds):
            raise ValueError("bounds must contain four finite coordinates")
        xmin, ymin, xmax, ymax = bounds
        if xmax <= xmin or ymax <= ymin:
            raise ValueError("bounds must have positive width and height")
        self.bounds = bounds
        self.cell_size_m = float(cell_size_m)
        self._background = spec["background"]["passability"]
        if self._background not in {"allowed", "unknown"}:
            raise ValueError("background must be allowed or unknown")
        if not spec["background"].get("source"):
            raise ValueError("background needs a provenance source")
        self._features = []
        grouped = {"allowed": [], "unknown": [], "blocked": []}
        for feature in spec.get("features", []):
            props = feature["properties"]
            status = props["passability"]
            geom = shape(feature["geometry"])
            if status not in grouped:
                raise ValueError(f"Unknown passability: {status}")
            if not props.get("source") or not props.get("kind"):
                raise ValueError("Features need kind and provenance source")
            if geom.is_empty or not geom.is_valid:
                raise ValueError("Features must be nonempty and valid")
            if status != "unknown" and geom.geom_type not in {"Polygon", "MultiPolygon"}:
                raise ValueError("Known passability needs an area geometry")
            self._features.append((geom, dict(props)))
            grouped[status].append(geom)
        self._blocked = unary_union(grouped["blocked"])
        self._unknown = unary_union(grouped["unknown"])
        self._allowed = unary_union(grouped["allowed"])
        self._blocked_p = prep(self._blocked)
        self._unknown_p = prep(self._unknown)
        self._allowed_p = prep(self._allowed)
        self._ncols = math.ceil((xmax - xmin) / self.cell_size_m)
        self._nrows = math.ceil((ymax - ymin) / self.cell_size_m)
        if self._ncols * self._nrows > 250_000:
            raise ValueError("Prototype grid exceeds 250000 cells; crop or increase cell size")
        self.nodes: list[Candidate] = []
        self._cells: list[tuple[int, int, object, str]] = []
        self._index_by_cell = {}
        for row in range(self._nrows):
            y0 = ymin + row * self.cell_size_m
            y1 = min(y0 + self.cell_size_m, ymax)
            for col in range(self._ncols):
                x0 = xmin + col * self.cell_size_m
                x1 = min(x0 + self.cell_size_m, xmax)
                geom = box(x0, y0, x1, y1)
                x, y = (x0 + x1) / 2, (y0 + y1) / 2
                point = Point(x, y)
                status = self._passability(point)
                self._cells.append((row, col, geom, status))
                if status == "blocked":
                    continue
                node_id = row * self._ncols + col
                self._index_by_cell[(row, col)] = len(self.nodes)
                self.nodes.append(Candidate(node_id, x, y, f"r{row}_c{col}", status))
        self._index_by_id = {node.node_id: i for i, node in enumerate(self.nodes)}
        self._xy = np.asarray([(n.x_m, n.y_m) for n in self.nodes], dtype=float).reshape(-1, 2)
        self._adj: list[list[tuple[int, float, bool]]] = [[] for _ in self.nodes]
        for (row, col), index in self._index_by_cell.items():
            a = self.nodes[index]
            # Each undirected edge once, then insert both directions.
            for dr, dc in ((0, 1), (1, -1), (1, 0), (1, 1)):
                other = self._index_by_cell.get((row + dr, col + dc))
                if other is None:
                    continue
                b = self.nodes[other]
                segment = LineString([(a.x_m, a.y_m), (b.x_m, b.y_m)])
                if self._blocked_p.intersects(segment):
                    continue
                unknown = self._has_unknown(segment)
                distance = math.hypot(a.x_m - b.x_m, a.y_m - b.y_m)
                self._adj[index].append((other, distance, unknown))
                self._adj[other].append((index, distance, unknown))
        self._cache: OrderedDict[int, tuple[np.ndarray, np.ndarray]] = OrderedDict()
        self._cache_limit = 128
        self._dijkstra_runs = 0
        self._connection_queries = 0

    def _passability(self, geom) -> str:
        if self._blocked_p.intersects(geom):
            return "blocked"
        if self._has_unknown(geom):
            return "unknown"
        return "allowed"

    def _has_unknown(self, geom) -> bool:
        if self._unknown_p.intersects(geom):
            return True
        return self._background == "unknown" and not self._allowed_p.covers(geom)

    def candidates(self, x_m: float, y_m: float, radius_m: float,
                   max_candidates: int) -> list[Candidate]:
        if not all(math.isfinite(v) for v in (x_m, y_m, radius_m)) or radius_m <= 0:
            raise ValueError("Candidate position and radius must be finite; radius positive")
        if isinstance(max_candidates, bool) or not isinstance(max_candidates, int) or max_candidates < 1:
            raise ValueError("max_candidates must be a positive integer")
        xmin, ymin, xmax, ymax = self.bounds
        if not (xmin <= x_m <= xmax and ymin <= y_m <= ymax):
            return []
        distances = np.sum((self._xy - [x_m, y_m]) ** 2, axis=1)
        indices = np.flatnonzero(distances <= radius_m * radius_m)
        # Existing node order is ascending id; stable sorting supplies tie-break.
        order = np.argsort(distances[indices], kind="stable")[:max_candidates]
        return [self.nodes[int(indices[i])] for i in order]

    def _index(self, node: Candidate) -> int:
        index = self._index_by_id.get(node.node_id)
        if index is None or self.nodes[index] != node:
            raise ValueError("Candidate does not belong to this map")
        return index

    def _distances(self, source: int) -> tuple[np.ndarray, np.ndarray]:
        if source in self._cache:
            self._cache.move_to_end(source)
            return self._cache[source]
        self._dijkstra_runs += 1
        distance = np.full(len(self.nodes), np.inf)
        unknown = np.ones(len(self.nodes), dtype=bool)
        distance[source] = 0.0
        unknown[source] = self.nodes[source].passability == "unknown"
        queue = [(0.0, bool(unknown[source]), source)]
        while queue:
            d, u, current = heapq.heappop(queue)
            if d > distance[current] or (d == distance[current] and u > unknown[current]):
                continue
            for adjacent, weight, edge_unknown in self._adj[current]:
                nd, nu = d + weight, bool(u or edge_unknown)
                if nd < distance[adjacent] or (nd == distance[adjacent] and nu < unknown[adjacent]):
                    distance[adjacent] = nd
                    unknown[adjacent] = nu
                    heapq.heappush(queue, (nd, nu, adjacent))
        self._cache[source] = (distance, unknown)
        if len(self._cache) > self._cache_limit:
            self._cache.popitem(last=False)
        return distance, unknown

    def connection(self, a: Candidate, b: Candidate) -> Connection:
        self._connection_queries += 1
        ia, ib = self._index(a), self._index(b)
        distance, unknown = self._distances(ia)
        d = float(distance[ib])
        if not math.isfinite(d):
            return Connection("unreachable", math.inf)
        return Connection("unknown" if unknown[ib] else "reachable", d)

    def statistics(self) -> dict:
        return {
            "partition": "uniform_grid_cell_centres",
            "cell_size_m": self.cell_size_m,
            "region_count": len(self._cells),
            "node_count": len(self.nodes),
            "undirected_edge_count": sum(len(v) for v in self._adj) // 2,
            "unknown_node_count": sum(n.passability == "unknown" for n in self.nodes),
            "connection_queries": self._connection_queries,
            "dijkstra_runs": self._dijkstra_runs,
            "cached_source_count": len(self._cache),
            "cache_source_limit": self._cache_limit,
        }

    def export_regions(self, path) -> Path:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        features = []
        for row, col, cell, status in self._cells:
            covered = [props for geom, props in self._features if geom.intersects(cell)]
            features.append({
                "type": "Feature", "geometry": mapping(cell),
                "properties": {
                    "region_id": f"r{row}_c{col}",
                    "node_id": row * self._ncols + col,
                    "centre_passability": status,
                    "has_candidate": status != "blocked",
                    "intersects_blocked_geometry": bool(self._blocked_p.intersects(cell)),
                    "background_source": self.spec["background"]["source"],
                    "overlapping_features": covered,
                    "classification_basis": "centre only; full-cell traversability is not asserted",
                },
            })
        payload = {"type": "FeatureCollection", "name": self.spec.get("name", "grid"),
                   "coordinate_system": self.spec.get("crs"), "features": features}
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return path
