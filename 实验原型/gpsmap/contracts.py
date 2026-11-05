"""Shared interface, owned by the integrating agent. Coordinates: metres; time: seconds."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, Sequence
import math


@dataclass(frozen=True)
class Observation:
    t_s: float
    x_m: float
    y_m: float
    sigma_m: float

    def __post_init__(self):
        if not all(math.isfinite(v) for v in (self.t_s, self.x_m, self.y_m, self.sigma_m)):
            raise ValueError("Observation values must be finite")
        if self.sigma_m <= 0:
            raise ValueError("sigma_m must be positive (per-axis standard deviation)")


@dataclass(frozen=True)
class Candidate:
    node_id: int
    x_m: float
    y_m: float
    region_id: str
    passability: str  # allowed, unknown; blocked nodes are not candidates


@dataclass(frozen=True)
class Connection:
    status: str  # reachable, unknown, unreachable
    distance_m: float  # graph shortest path; inf if unreachable


@dataclass(frozen=True)
class Estimate:
    t_s: float
    x_m: float
    y_m: float
    region_id: str
    status: str  # ok, map_unknown, no_candidates, reset_unreachable
    candidate_count: int


@dataclass(frozen=True)
class ModelConfig:
    candidate_radius_m: float = 30.0
    max_candidates: int = 48
    max_speed_mps: float = 8.0
    motion_sigma_mps: float = 3.0

    def __post_init__(self):
        vals = (self.candidate_radius_m, self.max_speed_mps, self.motion_sigma_mps)
        if not all(math.isfinite(v) and v > 0 for v in vals):
            raise ValueError("Model scales must be finite and positive")
        if isinstance(self.max_candidates, bool) or not isinstance(self.max_candidates, int) or self.max_candidates < 1:
            raise ValueError("max_candidates must be a positive integer")


class SpatialMap(Protocol):
    spec: dict
    nodes: Sequence[Candidate]

    def candidates(self, x_m: float, y_m: float, radius_m: float,
                   max_candidates: int) -> list[Candidate]: ...

    def connection(self, a: Candidate, b: Candidate) -> Connection: ...

    def statistics(self) -> dict: ...
