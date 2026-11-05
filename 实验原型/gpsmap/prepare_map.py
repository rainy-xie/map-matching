"""Read-only historical-map crop and its explicitly unknown spatial baseline."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
from matplotlib.patches import Patch, PathPatch
from matplotlib.path import Path as MplPath
import numpy as np
import pyogrio
from pyogrio.raw import read
from pyproj import Transformer
import shapely
from shapely.geometry import box, mapping
from shapely.geometry.polygon import orient
from shapely.strtree import STRtree

from .spatial import GridMap


def _json_value(value):
    if isinstance(value, np.generic):
        return value.item()
    return value


def _draw_geometry(ax, geometry, colour):
    kind = geometry.geom_type
    if kind in {"MultiPolygon", "GeometryCollection", "MultiLineString"}:
        for child in geometry.geoms:
            _draw_geometry(ax, child, colour)
    elif kind == "Polygon":
        geometry = orient(geometry, sign=1.0)
        vertices, codes = [], []
        for ring in [geometry.exterior, *geometry.interiors]:
            coords = list(ring.coords)
            vertices.extend(coords)
            codes.extend([MplPath.MOVETO] + [MplPath.LINETO] * (len(coords) - 2) + [MplPath.CLOSEPOLY])
        ax.add_patch(PathPatch(MplPath(vertices, codes), facecolor=colour,
                               edgecolor=colour, linewidth=0.4, alpha=0.65))
    elif kind == "LineString":
        ax.plot(*geometry.xy, color=colour, linewidth=1.0)


def build_real_sample(gpkg_path, output_dir, cell_size_m=8.0) -> Path:
    """Select first fixed-order 400 m crop containing meaningful three-layer content.

    Selection examines source water features in ascending GPKG fid, then boundary
    fractions 0,1/8,...,7/8. It accepts the first 400 m square fully inside the
    district with >=1000 m2 water, >=1000 m2 vegetation and >=100 m road length.
    Attributes are retained as original codes, never converted to traversability.
    """
    gpkg_path = Path(gpkg_path).resolve()
    output_dir = Path(output_dir)
    expected = ["fengtai_map.json", "fengtai_regions.geojson", "fengtai_preview.png", "fengtai_provenance.json"]
    if any((output_dir / name).exists() for name in expected):
        raise FileExistsError("Derived-map output exists; choose a fresh output directory")
    source_hash = hashlib.sha256(gpkg_path.read_bytes()).hexdigest()
    project = Transformer.from_crs("EPSG:4326", "EPSG:32650", always_xy=True)
    inverse = Transformer.from_crs("EPSG:32650", "EPSG:4326", always_xy=True)
    layers = {}
    for layer in ("道路", "植被", "水系", "丰台政区"):
        meta, fids, wkb, fields = read(gpkg_path, layer=layer, return_fids=True)
        if meta["crs"] != "EPSG:4326":
            raise ValueError(f"Unexpected source CRS for {layer}: {meta['crs']}")
        geometries = shapely.transform(shapely.from_wkb(wkb), project.transform, interleaved=False)
        layers[layer] = {"geometries": geometries, "fids": fids,
                         "fields": dict(zip(meta["fields"], fields)), "tree": STRtree(geometries)}
    district = shapely.union_all(layers["丰台政区"]["geometries"])
    selection = None
    for water_index in np.argsort(layers["水系"]["fids"], kind="stable"):
        boundary = layers["水系"]["geometries"][water_index].boundary
        for fraction_index in range(8):
            point = boundary.interpolate(fraction_index / 8, normalized=True)
            origin = (math.floor(point.x - 200), math.floor(point.y - 200))
            square = box(origin[0], origin[1], origin[0] + 400, origin[1] + 400)
            if not district.covers(square):
                continue
            clipped = {}
            for layer in ("道路", "植被", "水系"):
                indices = sorted(layers[layer]["tree"].query(square, predicate="intersects"))
                clipped[layer] = [(i, layers[layer]["geometries"][i].intersection(square)) for i in indices]
            water_area = sum(g.area for _, g in clipped["水系"])
            vegetation_area = sum(g.area for _, g in clipped["植被"])
            road_length = sum(g.length for _, g in clipped["道路"])
            if water_area >= 1000 and vegetation_area >= 1000 and road_length >= 100:
                selection = (origin, clipped, int(layers["水系"]["fids"][water_index]), fraction_index,
                             water_area, vegetation_area, road_length)
                break
        if selection:
            break
    if selection is None:
        raise ValueError("No crop satisfied the fixed selection rule; revise the rule explicitly")
    origin, clipped, anchor_fid, fraction_index, water_area, vegetation_area, road_length = selection
    origin_x, origin_y = origin
    provenance = {
        "source_file": str(gpkg_path), "source_sha256": source_hash,
        "source_crs_from_metadata": "EPSG:4326", "projected_crs": "EPSG:32650",
        "local_origin_utm_m": [origin_x, origin_y],
        "utm_bounds_m": [origin_x, origin_y, origin_x + 400, origin_y + 400],
        "approx_wgs84_corners": [list(inverse.transform(x, y)) for x, y in
                                  [(origin_x, origin_y), (origin_x + 400, origin_y + 400)]],
        "selection_rule": "First water fid ascending, boundary fraction 0/8..7/8; 400m square snapped down to integer UTM origin, inside district; water>=1000m2, vegetation>=1000m2, roads>=100m",
        "anchor_water_fid": anchor_fid, "anchor_boundary_fraction": fraction_index / 8,
        "cropped_water_area_m2_sum": water_area, "cropped_vegetation_area_m2_sum": vegetation_area,
        "cropped_road_length_m_sum": road_length,
        "source_layer_feature_counts": {name: len(data["geometries"]) for name, data in layers.items()},
        "cropped_feature_counts": {name: len(items) for name, items in clipped.items()},
        "cautions": ["Coordinates follow source metadata; no independent registration",
                     "Historical map; no verified survey date or current field consistency",
                     "Water, vegetation, road and background traversability all remain unknown",
                     "Road width, slope and vehicle speed are not used as athlete parameters",
                     "Service-point layer is neither read nor exported",
                     "A synthetic trajectory on this map is not evidence of a real traversable route"],
    }
    features = []
    kinds = {"道路": "road", "植被": "vegetation", "水系": "water"}
    colours = {"道路": "#697586", "植被": "#96c899", "水系": "#74b7db"}
    local_geometries = {}
    for layer in ("植被", "水系", "道路"):
        local_geometries[layer] = []
        for index, geom in clipped[layer]:
            if geom.is_empty:
                continue
            # Zero-dimensional boundary touches are irrelevant to map context.
            if geom.geom_type in {"Point", "MultiPoint"}:
                continue
            local = shapely.transform(geom, lambda x, y: (x - origin_x, y - origin_y), interleaved=False)
            local_geometries[layer].append(local)
            properties = {
                "kind": kinds[layer], "passability": "unknown",
                "source": "historical_teacher_gpkg_geometry_and_code; traversability_unverified",
                "source_layer": layer, "source_fid": int(layers[layer]["fids"][index]),
                "original_code": _json_value(layers[layer]["fields"]["编码"][index]),
            }
            features.append({"type": "Feature", "geometry": mapping(local), "properties": properties})
    spec = {
        "name": "fengtai_historical_400m_unknown",
        "bounds": [0.0, 0.0, 400.0, 400.0],
        "crs": "LOCAL_METRES_FROM_EPSG:32650",
        "source": "historical_teacher_map; source metadata not independently registered",
        "background": {"passability": "unknown", "source": "No verified land-cover or traversability evidence"},
        "features": features, "metadata": provenance,
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    target = output_dir / "fengtai_map.json"
    target.write_text(json.dumps(spec, ensure_ascii=False, indent=2), encoding="utf-8")
    grid = GridMap(spec, cell_size_m)
    grid.export_regions(output_dir / "fengtai_regions.geojson")
    provenance["grid_statistics"] = grid.statistics()
    provenance["versions"] = {"numpy": np.__version__, "shapely": shapely.__version__, "pyogrio": pyogrio.__version__}
    (output_dir / "fengtai_provenance.json").write_text(json.dumps(provenance, ensure_ascii=False, indent=2), encoding="utf-8")
    fig, ax = plt.subplots(figsize=(8.4, 8.5), dpi=160)
    fig.subplots_adjust(left=.12, right=.96, bottom=.18, top=.88)
    ax.set_facecolor("#f4f5f7")
    for layer in ("植被", "水系", "道路"):
        for geometry in local_geometries[layer]:
            _draw_geometry(ax, geometry, colours[layer])
    grid_lines = []
    for value in np.arange(0, 400 + cell_size_m / 2, cell_size_m):
        grid_lines.extend([[(value, 0), (value, 400)], [(0, value), (400, value)]])
    ax.add_collection(LineCollection(grid_lines, colors="#374151", linewidths=.28, alpha=.15))
    ax.set(xlim=(0, 400), ylim=(0, 400), xlabel="Local easting / m", ylabel="Local northing / m")
    ax.set_aspect("equal")
    fig.suptitle("Fengtai historical map | 400 m sample", fontsize=16, y=.96)
    ax.set_title(f"{cell_size_m:g} m uniform grid; all traversability UNKNOWN", fontsize=11, pad=10)
    ax.legend(handles=[Patch(color=colours[layer], label=kinds[layer]) for layer in ("植被", "水系", "道路")],
              loc="lower left", framealpha=.9)
    fig.text(.12, .105, "Blank background is UNKNOWN, not confirmed open ground.", fontsize=10)
    fig.text(.12, .075, "CRS: WGS84 metadata → UTM 50N → local origin; no field registration.", fontsize=9)
    fig.text(.12, .045, "Map-derived geometry only. No observed GPS or independent field reference.", fontsize=9)
    fig.savefig(output_dir / "fengtai_preview.png", dpi=160)
    plt.close(fig)
    return target


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--cell-size", type=float, default=8.0)
    args = parser.parse_args()
    print(build_real_sample(args.source, args.output, args.cell_size))


if __name__ == "__main__":
    main()
