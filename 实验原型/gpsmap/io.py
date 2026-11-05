"""Strict CSV boundaries shared by the command line and integration checks."""
from __future__ import annotations
import csv
import hashlib
import json
from dataclasses import asdict
from pathlib import Path
from .contracts import Observation, Estimate


def load_observations(path: Path) -> list[Observation]:
    with Path(path).open(newline="", encoding="utf-8") as f:
        rows = csv.DictReader(f)
        if rows.fieldnames != ["t_s", "x_m", "y_m", "sigma_m"]:
            raise ValueError("Observation CSV must contain ONLY t_s,x_m,y_m,sigma_m in that order")
        result = [Observation(**{key: float(value) for key, value in row.items()}) for row in rows]
    if not result:
        raise ValueError("Observation CSV is empty")
    if any(b.t_s <= a.t_s for a, b in zip(result, result[1:])):
        raise ValueError("Observation timestamps must be strictly increasing")
    return result


def write_estimates(path: Path, values: list[Estimate]):
    with Path(path).open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(Estimate.__dataclass_fields__))
        writer.writeheader()
        for value in values:
            row = asdict(value)
            writer.writerow({k: format(v, ".12g") if isinstance(v, float) else v for k, v in row.items()})


def write_json(path: Path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()
