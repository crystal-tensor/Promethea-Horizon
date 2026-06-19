#!/usr/bin/env python3
"""Local-dressing search gate for B1/B7 cone_01 flat patterns.

T-B1-004q showed that the three invariant-flat residual pattern groups share a
nonlocal fingerprint with nearest pi/4-grid representatives. This gate tests a
more concrete obligation: can a nearest-grid representative be dressed by
arbitrary one-qubit gates on both sides to reproduce the original two-qubit
window?

Even an exact numeric dressing is not a B7 resource saving. The dressing gates
carry their own arbitrary-angle cost unless a later certificate proves they can
be absorbed, shared, or made Clifford/exact under the occurrence ledger.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

import numpy as np
from scipy.optimize import least_squares

from b1_b7_cone01_flat_pattern_kak_packet import parse_normalized_op, replace_target_ry_with_grid
from b1_b7_cone01_phase_removal_gate import EXACT_TOLERANCE, residual_norm, residual_vector, ry, rz, unitary_for_ops


ROOT = Path(__file__).resolve().parents[1]
SOURCE_PATH = ROOT / "results" / "B1_B7_cone01_flat_pattern_kak_packet_v0.json"
JSON_OUT = ROOT / "results" / "B1_B7_cone01_local_dressing_search_gate_v0.json"
MD_OUT = ROOT / "research" / "B1_B7_cone01_local_dressing_search_gate.md"

METHOD = "b1_b7_cone01_local_dressing_search_gate_v0"
STATUS = "cone01_local_dressing_search_not_resource_certificate"
MODEL_STATUS = "numeric_local_dressing_requires_absorption_or_resource_accounting"
PROXY_T_PER_OCCURRENCE = 20
REQUIRED_OCCURRENCE_REMOVALS = 30
DEFAULT_SEEDS = 36


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, payload: dict[str, Any], pretty: bool) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2 if pretty else None, sort_keys=True) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def display_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path)


def su2_zyz(params: np.ndarray) -> np.ndarray:
    """Determinant-one one-qubit Euler block."""
    return rz(float(params[0])) @ ry(float(params[1])) @ rz(float(params[2]))


def pair_local(params: np.ndarray) -> np.ndarray:
    partner = su2_zyz(params[:3])
    target = su2_zyz(params[3:6])
    return np.kron(partner, target)


def dressed_unitary(grid_unitary: np.ndarray, values: np.ndarray) -> np.ndarray:
    left = pair_local(values[:6])
    right = pair_local(values[6:])
    return left @ grid_unitary @ right


def wrapped(values: np.ndarray) -> list[float]:
    wrapped_values = []
    for value in values:
        shifted = (float(value) + math.pi) % (2.0 * math.pi) - math.pi
        wrapped_values.append(shifted)
    return wrapped_values


def pi_over_four_distance(value: float) -> float:
    grid = round(value / (math.pi / 4.0)) * (math.pi / 4.0)
    return abs(value - grid)


def dressing_parameter_stats(values: list[float]) -> dict[str, Any]:
    nonzero = [v for v in values if abs(v) > 1e-7]
    off_grid = [v for v in values if pi_over_four_distance(v) > 1e-6]
    return {
        "euler_parameter_count": len(values),
        "nonzero_euler_parameter_count": len(nonzero),
        "off_pi_over_four_grid_parameter_count": len(off_grid),
        "max_pi_over_four_grid_distance": max((pi_over_four_distance(v) for v in values), default=0.0),
    }


def seed_points(pattern_id: str, seed_count: int) -> list[np.ndarray]:
    base = np.zeros(12, dtype=float)
    points = [base]
    rng_seed = 14004 + sum(ord(ch) for ch in pattern_id)
    rng = np.random.default_rng(rng_seed)
    for scale in [0.05, 0.25, 1.0, math.pi]:
        points.append(rng.normal(0.0, scale, size=12))
        points.append(rng.uniform(-scale, scale, size=12))
    while len(points) < seed_count:
        points.append(rng.uniform(-2.0 * math.pi, 2.0 * math.pi, size=12))
    return points[:seed_count]


def analyze_pattern(packet: dict[str, Any], seed_count: int, max_nfev: int) -> dict[str, Any]:
    ops = [parse_normalized_op(text) for text in packet["normalized_window_text"]]
    target = unitary_for_ops(ops, [0, 1])
    grid_ops = replace_target_ry_with_grid(ops, float(packet["nearest_grid_angle"]))
    grid_unitary = unitary_for_ops(grid_ops, [0, 1])

    def objective(values: np.ndarray) -> np.ndarray:
        return residual_vector(dressed_unitary(grid_unitary, values), target)

    best = None
    attempts = []
    for seed_index, seed in enumerate(seed_points(packet["pattern_id"], seed_count)):
        result = least_squares(
            objective,
            seed,
            method="trf",
            max_nfev=max_nfev,
            ftol=1e-13,
            xtol=1e-13,
            gtol=1e-13,
        )
        residual = float(np.linalg.norm(result.fun))
        attempt = {
            "seed_index": seed_index,
            "residual_norm": residual,
            "nfev": int(result.nfev),
            "success": bool(result.success),
        }
        attempts.append(attempt)
        if best is None or residual < best["residual_norm"]:
            best = {
                **attempt,
                "raw_parameters": [float(v) for v in result.x],
                "wrapped_parameters": wrapped(result.x),
            }

    assert best is not None
    stats = dressing_parameter_stats(best["wrapped_parameters"])
    exact_pass = best["residual_norm"] <= EXACT_TOLERANCE
    candidate = dressed_unitary(grid_unitary, np.array(best["raw_parameters"], dtype=float))
    return {
        "pattern_id": packet["pattern_id"],
        "occurrence_count": packet["occurrence_count"],
        "nearest_grid_label": packet["nearest_grid_label"],
        "nearest_grid_angle": packet["nearest_grid_angle"],
        "same_envelope_grid_residual_norm": packet["same_envelope_grid_residual_norm"],
        "local_dressing_search_seed_count": seed_count,
        "best_local_dressing_residual_norm": best["residual_norm"],
        "local_dressing_exact_pass": exact_pass,
        "best_attempt": best,
        "attempts": attempts,
        "dressing_parameter_stats": stats,
        "dressed_unitary_residual_crosscheck": residual_norm(candidate, target),
        "resource_accounting_obligation": exact_pass,
        "accepted_occurrence_removal": 0,
        "accepted_proxy_t_reduction": 0,
    }


def build_payload(seed_count: int, max_nfev: int) -> dict[str, Any]:
    source = load_json(SOURCE_PATH)
    packets = source.get("pattern_packets", [])
    analyses = [analyze_pattern(packet, seed_count, max_nfev) for packet in packets]
    exact_count = sum(1 for row in analyses if row["local_dressing_exact_pass"])
    total_occurrences = sum(int(row["occurrence_count"]) for row in analyses)
    off_grid_counts = [row["dressing_parameter_stats"]["off_pi_over_four_grid_parameter_count"] for row in analyses]
    max_residual = max((row["best_local_dressing_residual_norm"] for row in analyses), default=None)
    accepted_occurrence_removal = sum(int(row["accepted_occurrence_removal"]) for row in analyses)
    missing_occurrences = REQUIRED_OCCURRENCE_REMOVALS - accepted_occurrence_removal
    summary = {
        "source_method": source.get("method"),
        "source_status": source.get("status"),
        "pattern_group_count": len(analyses),
        "covered_invariant_flat_occurrence_count": total_occurrences,
        "local_dressing_search_seed_count": seed_count,
        "local_dressing_exact_pass_count": exact_count,
        "max_local_dressing_residual_norm": max_residual,
        "all_patterns_have_numeric_local_dressing": exact_count == len(analyses),
        "max_off_pi_over_four_grid_dressing_parameter_count": max(off_grid_counts, default=0),
        "accepted_occurrence_removal": accepted_occurrence_removal,
        "accepted_proxy_t_reduction": 0,
        "required_occurrence_removals_for_b7_target": REQUIRED_OCCURRENCE_REMOVALS,
        "missing_occurrences_after_gate": missing_occurrences,
        "missing_proxy_t_after_gate": missing_occurrences * PROXY_T_PER_OCCURRENCE,
        "rewrite_claimed": False,
        "semantic_certificate_claimed": False,
        "kak_theorem_claimed": False,
        "resource_saving_claimed": False,
        "b7_ledger_improvement_claimed": False,
        "validation_error_count": None,
    }
    payload = {
        "benchmark_id": "B1",
        "problem_id": 25,
        "linked_b7_problem_id": 21,
        "title": "B1/B7 cone_01 local-dressing search gate",
        "status": STATUS,
        "model_status": MODEL_STATUS,
        "method": METHOD,
        "source_result": display_path(SOURCE_PATH),
        "source_method": source.get("method"),
        "workload": "qasmbench_medium_exact/gcm_h6.qasm",
        "summary": summary,
        "pattern_dressing_results": analyses,
        "claim_boundary": {
            "rewrite_claimed": False,
            "semantic_certificate_claimed": False,
            "kak_theorem_claimed": False,
            "resource_saving_claimed": False,
            "b7_ledger_improvement_claimed": False,
            "supported_claim": (
                "A numerical SU(2)xSU(2) local-dressing search can match the nearest-grid "
                "representatives to the three original flat patterns, but the dressing "
                "parameters remain unaccounted arbitrary local rotations."
            ),
            "unsupported_claims": [
                "This is not a replayable circuit rewrite certificate.",
                "This is not a proof-assistant checked KAK/local-equivalence theorem.",
                "Arbitrary local dressing parameters are not free under the B7 occurrence ledger.",
                "The accepted occurrence removal and accepted proxy-T reduction remain zero.",
            ],
        },
    }
    errors = validate(payload)
    payload["summary"]["validation_error_count"] = len(errors)
    payload["validation_errors"] = errors
    return payload


def validate(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    summary = payload["summary"]
    if payload.get("method") != METHOD:
        errors.append("method_mismatch")
    if payload.get("source_method") != "b1_b7_cone01_flat_pattern_kak_packet_v0":
        errors.append("source_method_mismatch")
    if summary.get("pattern_group_count") != 3:
        errors.append("pattern_group_count_mismatch")
    if summary.get("covered_invariant_flat_occurrence_count") != 11:
        errors.append("covered_occurrence_count_mismatch")
    if summary.get("local_dressing_exact_pass_count") != 3:
        errors.append("local_dressing_exact_pass_count_mismatch")
    if summary.get("all_patterns_have_numeric_local_dressing") is not True:
        errors.append("all_patterns_should_have_numeric_local_dressing")
    if summary.get("accepted_occurrence_removal") != 0:
        errors.append("accepted_occurrence_removal_must_remain_zero")
    if summary.get("accepted_proxy_t_reduction") != 0:
        errors.append("accepted_proxy_t_reduction_must_remain_zero")
    if summary.get("missing_occurrences_after_gate") != 30:
        errors.append("missing_occurrences_after_gate_mismatch")
    if summary.get("missing_proxy_t_after_gate") != 600:
        errors.append("missing_proxy_t_after_gate_mismatch")
    if summary.get("max_off_pi_over_four_grid_dressing_parameter_count", 0) <= 0:
        errors.append("dressing_parameters_should_not_all_be_exact_grid")
    for field in [
        "rewrite_claimed",
        "semantic_certificate_claimed",
        "kak_theorem_claimed",
        "resource_saving_claimed",
        "b7_ledger_improvement_claimed",
    ]:
        if summary.get(field) is not False or payload["claim_boundary"].get(field) is not False:
            errors.append(f"forbidden_claim_{field}")
    for row in payload.get("pattern_dressing_results", []):
        if row.get("accepted_occurrence_removal") != 0:
            errors.append(f"pattern_{row.get('pattern_id')}_accepted_removal_nonzero")
        if row.get("dressed_unitary_residual_crosscheck", 1.0) > EXACT_TOLERANCE:
            errors.append(f"pattern_{row.get('pattern_id')}_crosscheck_failed")
    return errors


def write_markdown(payload: dict[str, Any], path: Path) -> None:
    summary = payload["summary"]
    lines = [
        "# B1/B7 Cone 01 Local-Dressing Search Gate",
        "",
        f"Status: `{payload['status']}`",
        "",
        "This artifact tests whether each flat-pattern nearest-grid representative can be matched to the original window with arbitrary one-qubit local dressing on both sides. It is a numerical obligation gate, not a circuit rewrite certificate and not a B7 resource claim.",
        "",
        "## Summary",
        "",
        f"- Pattern groups: `{summary['pattern_group_count']}`",
        f"- Covered invariant-flat occurrences: `{summary['covered_invariant_flat_occurrence_count']}`",
        f"- Local-dressing exact passes: `{summary['local_dressing_exact_pass_count']}`",
        f"- Max local-dressing residual: `{summary['max_local_dressing_residual_norm']}`",
        f"- Max off-grid dressing parameters per packet: `{summary['max_off_pi_over_four_grid_dressing_parameter_count']}`",
        f"- Accepted occurrence removal: `{summary['accepted_occurrence_removal']}`",
        f"- Missing occurrences after this gate: `{summary['missing_occurrences_after_gate']}`",
        "",
        "## Pattern Results",
        "",
        "| Pattern | Occurrences | Grid | Same-envelope residual | Dressed residual | Off-grid dressing params | Accepted removal |",
        "|---|---:|---|---:|---:|---:|---:|",
    ]
    for row in payload["pattern_dressing_results"]:
        stats = row["dressing_parameter_stats"]
        lines.append(
            "| {pattern_id} | {occurrence_count} | `{grid}` | `{same:.12g}` | `{dressed:.12g}` | `{off_grid}` | `{accepted}` |".format(
                pattern_id=row["pattern_id"],
                occurrence_count=row["occurrence_count"],
                grid=row["nearest_grid_label"],
                same=row["same_envelope_grid_residual_norm"],
                dressed=row["best_local_dressing_residual_norm"],
                off_grid=stats["off_pi_over_four_grid_parameter_count"],
                accepted=row["accepted_occurrence_removal"],
            )
        )
    lines.extend(
        [
            "",
            "## Claim Boundary",
            "",
            "- Numeric local dressing exists for the three packets in this bounded search.",
            "- The dressing introduces arbitrary local Euler parameters; those parameters are not free under the B7 occurrence ledger.",
            "- Accepted occurrence removal remains 0 and accepted proxy-T reduction remains 0.",
            "- No KAK theorem, semantic certificate, rewrite certificate, resource saving, or B7 ledger improvement is claimed.",
            "",
            f"Validation error count: `{summary['validation_error_count']}`",
            "",
        ]
    )
    write_text(path, "\n".join(lines))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json-output", type=Path, default=JSON_OUT)
    parser.add_argument("--markdown-output", type=Path, default=MD_OUT)
    parser.add_argument("--seeds", type=int, default=DEFAULT_SEEDS)
    parser.add_argument("--max-nfev", type=int, default=12000)
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()
    payload = build_payload(seed_count=args.seeds, max_nfev=args.max_nfev)
    write_json(args.json_output, payload, pretty=args.pretty)
    write_markdown(payload, args.markdown_output)
    print(json.dumps(payload["summary"], indent=2 if args.pretty else None, sort_keys=True))
    return 0 if not payload["validation_errors"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
