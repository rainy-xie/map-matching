"""Offline maximum-score decoding; no file I/O and no access to reference data.

The Gaussian observation likelihood is combined with an unnormalised movement
potential. This is a deliberately simple HMM-style baseline, not a calibrated
posterior or an online filter.
"""
from __future__ import annotations

from collections import Counter
import math
from typing import Sequence

from .contracts import Candidate, Estimate, ModelConfig, Observation, SpatialMap


def observation_log_score(observation: Observation, candidate: Candidate) -> float:
    """Log density of an isotropic 2-D Gaussian, sigma measured per axis."""
    distance = math.hypot(candidate.x_m - observation.x_m,
                          candidate.y_m - observation.y_m)
    scaled = distance / observation.sigma_m
    score = -0.5 * scaled * scaled - math.log(2.0 * math.pi) - 2.0 * math.log(observation.sigma_m)
    if not math.isfinite(score):
        raise ValueError("Observation score is not finite; check coordinate/noise scales")
    return score


def _inputs(observations: Sequence[Observation], config: ModelConfig) -> list[Observation]:
    config.__post_init__()
    values = list(observations)
    for index, observation in enumerate(values):
        observation.__post_init__()
        if index:
            dt = observation.t_s - values[index - 1].t_s
            if not math.isfinite(dt) or dt <= 0:
                raise ValueError("Observation times must be strictly increasing with finite differences")
    return values


def _candidates(observation: Observation, spatial_map: SpatialMap,
                config: ModelConfig) -> list[Candidate]:
    candidates = list(spatial_map.candidates(observation.x_m, observation.y_m,
                                            config.candidate_radius_m, config.max_candidates))
    if len(candidates) > config.max_candidates:
        raise ValueError("Map returned more candidates than max_candidates")
    seen = set()
    for candidate in candidates:
        if candidate.node_id in seen:
            raise ValueError("Map returned duplicate candidate node_id")
        seen.add(candidate.node_id)
        if candidate.passability not in {"allowed", "unknown"}:
            raise ValueError("Candidate passability must be allowed or unknown")
        if not all(math.isfinite(v) for v in (candidate.x_m, candidate.y_m)):
            raise ValueError("Candidate coordinates must be finite")
        if math.hypot(candidate.x_m - observation.x_m,
                      candidate.y_m - observation.y_m) > config.candidate_radius_m + 1e-8:
            raise ValueError("Map returned a candidate outside the search radius")
    # Tie breaking is independent of a map implementation's container ordering.
    candidates.sort(key=lambda c: (math.hypot(c.x_m - observation.x_m,
                                            c.y_m - observation.y_m), c.node_id))
    return candidates


def _transition(a: Candidate, b: Candidate, dt: float, spatial_map: SpatialMap,
                config: ModelConfig, diagnostics: dict) -> tuple[float, bool]:
    diagnostics["transition_pairs"] += 1
    # Euclidean distance is a lower bound for the graph path length.
    if math.hypot(b.x_m - a.x_m, b.y_m - a.y_m) / dt > config.max_speed_mps:
        diagnostics["speed_rejected_pairs"] += 1
        return -math.inf, False
    connection = spatial_map.connection(a, b)
    diagnostics["connection_queries"] += 1
    if connection.status not in {"reachable", "unknown", "unreachable"}:
        raise ValueError("Invalid connection status returned by map")
    if connection.status == "unreachable":
        diagnostics["unreachable_pairs"] += 1
        return -math.inf, False
    distance = connection.distance_m
    if not math.isfinite(distance) or distance < 0:
        raise ValueError("Reachable/unknown connection distance must be finite and nonnegative")
    speed = distance / dt
    if speed > config.max_speed_mps:
        diagnostics["speed_rejected_pairs"] += 1
        return -math.inf, False
    scaled = speed / config.motion_sigma_mps
    score = -0.5 * scaled * scaled
    if not math.isfinite(score):
        raise ValueError("Movement score is not finite; check motion scale")
    return score, connection.status == "unknown"


def _diagnostics(method: str) -> dict:
    return {
        "method": method,
        "mode": "offline" if method == "hmm" else "independent_observations",
        "score_is_calibrated_probability": False,
        "transition_normalized": False,
        "segments": 0,
        "transition_pairs": 0,
        "connection_queries": 0,
        "speed_rejected_pairs": 0,
        "unreachable_pairs": 0,
        "no_candidate_indices": [],
        "reset_indices": [],
        "unknown_path_indices": [],
    }


def _complete_diagnostics(diagnostics: dict, estimates: list[Estimate]) -> None:
    diagnostics["observation_count"] = len(estimates)
    diagnostics["candidate_total"] = sum(e.candidate_count for e in estimates)
    diagnostics["candidate_max"] = max((e.candidate_count for e in estimates), default=0)
    diagnostics["status_counts"] = dict(Counter(e.status for e in estimates))


def map_only(observations: Sequence[Observation], spatial_map: SpatialMap,
             config: ModelConfig) -> tuple[list[Estimate], dict]:
    """Choose the maximum observation-likelihood candidate independently."""
    values = _inputs(observations, config)
    diagnostics = _diagnostics("map_only")
    estimates = []
    for index, observation in enumerate(values):
        candidates = _candidates(observation, spatial_map, config)
        if not candidates:
            estimates.append(Estimate(observation.t_s, observation.x_m, observation.y_m,
                                      "", "no_candidates", 0))
            diagnostics["no_candidate_indices"].append(index)
            continue
        best = max(range(len(candidates)), key=lambda j: observation_log_score(observation, candidates[j]))
        candidate = candidates[best]
        status = "map_unknown" if candidate.passability == "unknown" else "ok"
        if status == "map_unknown":
            diagnostics["unknown_path_indices"].append(index)
        estimates.append(Estimate(observation.t_s, candidate.x_m, candidate.y_m,
                                  candidate.region_id, status, len(candidates)))
    _complete_diagnostics(diagnostics, estimates)
    return estimates, diagnostics


def infer(observations: Sequence[Observation], spatial_map: SpatialMap,
          config: ModelConfig) -> tuple[list[Estimate], dict]:
    """Decode each feasible segment with deterministic log-domain Viterbi.

    No candidates: retain that raw observation, explicitly mark the failure,
    and break the chain. No feasible transition: finish the previous segment
    and restart at the current time. Every input gets exactly one output.
    """
    values = _inputs(observations, config)
    diagnostics = _diagnostics("hmm")
    estimates: list[Estimate | None] = [None] * len(values)
    # Each row: input index, candidate list, parent indices, unknown edges,
    # whether this row begins a reset caused by infeasible transitions.
    rows: list[tuple[int, list[Candidate], list[int], list[bool], bool]] = []
    scores: list[float] = []

    def finish_segment() -> None:
        if not rows:
            return
        chosen = max(range(len(scores)), key=scores.__getitem__)
        for index, candidates, parents, unknown_edges, reset in reversed(rows):
            candidate = candidates[chosen]
            unknown = candidate.passability == "unknown" or unknown_edges[chosen]
            if unknown:
                diagnostics["unknown_path_indices"].append(index)
            status = "reset_unreachable" if reset else "map_unknown" if unknown else "ok"
            estimates[index] = Estimate(values[index].t_s, candidate.x_m, candidate.y_m,
                                         candidate.region_id, status, len(candidates))
            chosen = parents[chosen]
        diagnostics["segments"] += 1
        rows.clear()

    for index, observation in enumerate(values):
        candidates = _candidates(observation, spatial_map, config)
        if not candidates:
            finish_segment()
            scores = []
            estimates[index] = Estimate(observation.t_s, observation.x_m, observation.y_m,
                                         "", "no_candidates", 0)
            diagnostics["no_candidate_indices"].append(index)
            continue
        emissions = [observation_log_score(observation, c) for c in candidates]
        reset = False
        if rows:
            previous_index, previous_candidates, _, _, _ = rows[-1]
            dt = observation.t_s - values[previous_index].t_s
            next_scores = [-math.inf] * len(candidates)
            parents = [-1] * len(candidates)
            unknown_edges = [False] * len(candidates)
            for current_j, current in enumerate(candidates):
                for previous_j, previous in enumerate(previous_candidates):
                    if not math.isfinite(scores[previous_j]):
                        continue
                    transition, unknown = _transition(previous, current, dt, spatial_map,
                                                      config, diagnostics)
                    value = scores[previous_j] + transition + emissions[current_j]
                    if value > next_scores[current_j]:
                        next_scores[current_j] = value
                        parents[current_j] = previous_j
                        unknown_edges[current_j] = unknown
            if not any(math.isfinite(v) for v in next_scores):
                finish_segment()
                diagnostics["reset_indices"].append(index)
                reset = True
            else:
                scores = next_scores
                rows.append((index, candidates, parents, unknown_edges, False))
        if not rows:
            scores = emissions
            rows.append((index, candidates, [-1] * len(candidates),
                         [False] * len(candidates), reset))
        # An additive constant per time step cannot change the winning path.
        # Recentring prevents long tracks from accumulating large magnitudes.
        best_score = max(scores)
        scores = [v - best_score for v in scores]

    finish_segment()
    diagnostics["unknown_path_indices"].sort()
    if any(e is None for e in estimates):
        raise RuntimeError("Internal decoder error: output alignment was lost")
    result = list(estimates)
    _complete_diagnostics(diagnostics, result)
    return result, diagnostics
