#!/usr/bin/env python3
"""Local-equivalence invariant obligation gate for B1/B7 cone_01.

Earlier cone_01 gates showed that same-envelope deletion, RZ replacement, and
Euler reabsorption do not produce occurrence-removing certificates. This gate
asks a sharper structural question: does the RY(theta) parameter enter the
two-qubit window's local-equivalence fingerprint, or can it be treated as only
local one-qubit dressing?

The gate uses a magic-basis trace fingerprint of the det-normalized two-qubit
unitary. It is a numerical invariant diagnostic, not a KAK theorem and not a
rewrite certificate.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

import numpy as np

from b1_b7_cone01_phase_removal_gate import (
    angle_from_params,
    target_rows,
    unitary_for_ops,
)


METHOD = "b1_b7_cone01_local_invariant_obligation_gate_v0"
STATUS = "cone01_local_invariant_obligation_not_rewrite_certificate"
MODEL_STATUS = "local_equivalence_fingerprint_obligation_not_kak_theorem"
VERSION = "0.1"
EXACT_TOLERANCE = 1e-8
SENSITIVITY_THRESHOLD = 1e-6

MAGIC_BASIS = (1.0 / math.sqrt(2.0)) * np.array(
    [
        [1.0, 0.0, 0.0, 1.0j],
        [0.0, 1.0j, 1.0, 0.0],
        [0.0, 1.0j, -1.0, 0.0],
        [1.0, 0.0, 0.0, -1.0j],
    ],
    dtype=complex,
)


def display_path(path: Path) -> str:
    root = Path(__file__).resolve().parents[1]
    resolved = path.resolve()
    try:
        return str(resolved.relative_to(root))
    except ValueError:
        return str(path)


def write_json(path: Path, payload: dict[str, Any], pretty: bool) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2 if pretty else None, sort_keys=True) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def det_normalized(unitary: np.ndarray) -> np.ndarray:
    det = np.linalg.det(unitary)
    if abs(det) <= 1e-15:
        raise ValueError("singular two-qubit unitary")
    return unitary / det ** 0.25


def invariant_fingerprint(unitary: np.ndarray) -> np.ndarray:
    """Return a trace fingerprint invariant under local SU(2) x SU(2) dressing."""
    su4 = det_normalized(unitary)
    magic_unitary = MAGIC_BASIS.conj().T @ su4 @ MAGIC_BASIS
    m_matrix = magic_unitary.T @ magic_unitary
    trace_1 = np.trace(m_matrix) / 4.0
    trace_2 = np.trace(m_matrix @ m_matrix) / 4.0
    return np.array([trace_1.real, trace_1.imag, trace_2.real, trace_2.imag], dtype=float)


def clone_window_with_theta(window: list[dict[str, Any]], ry_op_index: int, theta: float) -> list[dict[str, Any]]:
    output = []
    for op in window:
        clone = dict(op)
        if op["op_index"] == ry_op_index:
            clone["params"] = f"{theta:.17g}"
            clone["text"] = f"ry({theta:.17g}) q[{op['qubits'][0]}];"
        output.append(clone)
    return output


def angle_distance(left: float, right: float) -> float:
    return abs((left - right + math.pi) % (2.0 * math.pi) - math.pi)


def nearest_pi_over_four(theta: float) -> tuple[str, float, float]:
    candidates = []
    for k in range(-8, 9):
        grid_angle = k * math.pi / 4.0
        candidates.append((angle_distance(theta, grid_angle), f"{k}*pi/4", grid_angle))
    distance, label, angle = min(candidates, key=lambda item: item[0])
    return label, angle, distance


def analyze_window(ops: list[dict[str, Any]], row: dict[str, Any]) -> dict[str, Any]:
    local_qubits = [row["previous_cx_partner"], row["qubit"]]
    window = ops[row["previous_cx_index"] : row["next_cx_index"] + 1]
    theta = angle_from_params(row["params"])
    base = invariant_fingerprint(unitary_for_ops(window, local_qubits))
    eps = 1e-6
    plus = invariant_fingerprint(
        unitary_for_ops(clone_window_with_theta(window, row["op_index"], theta + eps), local_qubits)
    )
    minus = invariant_fingerprint(
        unitary_for_ops(clone_window_with_theta(window, row["op_index"], theta - eps), local_qubits)
    )
    derivative = (plus - minus) / (2.0 * eps)
    derivative_norm = float(np.linalg.norm(derivative))
    grid_label, grid_angle, grid_angle_distance = nearest_pi_over_four(theta)
    grid = invariant_fingerprint(
        unitary_for_ops(clone_window_with_theta(window, row["op_index"], grid_angle), local_qubits)
    )
    grid_invariant_distance = float(np.linalg.norm(grid - base))
    local_equivalence_sensitive = derivative_norm > SENSITIVITY_THRESHOLD
    nearest_grid_invariant_mismatch = grid_invariant_distance > EXACT_TOLERANCE
    return {
        "line_number": row["line_number"],
        "op_index": row["op_index"],
        "qubit": row["qubit"],
        "partner": row["previous_cx_partner"],
        "original_ry_params": row["params"],
        "theta": theta,
        "previous_cx_line": row["previous_cx_line"],
        "next_cx_line": row["next_cx_line"],
        "window_operation_count": len(window),
        "window_text": [op["text"] for op in window],
        "invariant_fingerprint": [float(value) for value in base],
        "finite_difference_eps": eps,
        "local_equivalence_invariant_derivative": [float(value) for value in derivative],
        "local_equivalence_invariant_derivative_norm": derivative_norm,
        "local_equivalence_sensitive": local_equivalence_sensitive,
        "nearest_pi_over_four_label": grid_label,
        "nearest_pi_over_four_angle": grid_angle,
        "distance_to_nearest_pi_over_four": grid_angle_distance,
        "nearest_grid_invariant_distance": grid_invariant_distance,
        "nearest_grid_invariant_mismatch": nearest_grid_invariant_mismatch,
        "local_only_absorption_blocked_by_invariant": local_equivalence_sensitive,
    }


def build_payload(args: argparse.Namespace) -> dict[str, Any]:
    ops, rows = target_rows(args)
    analyses = [analyze_window(ops, row) for row in rows]
    sensitive = [row for row in analyses if row["local_equivalence_sensitive"]]
    grid_mismatch = [row for row in analyses if row["nearest_grid_invariant_mismatch"]]
    derivative_norms = [row["local_equivalence_invariant_derivative_norm"] for row in analyses]
    grid_distances = [row["nearest_grid_invariant_distance"] for row in analyses]
    local_only_absorption_blocked_count = len(sensitive)
    local_only_absorption_blocked_clears_target = local_only_absorption_blocked_count >= args.required_windows
    summary = {
        "target_cone_id": args.cone_id,
        "candidate_window_count": len(analyses),
        "required_exact_windows_for_b7_target": args.required_windows,
        "target_proxy_t_ledger_reduction_for_gcm_h6_1_20": args.required_windows * 20,
        "invariant_fingerprint": "magic_basis_det_normalized_trace_m_m2",
        "local_equivalence_sensitive_count": len(sensitive),
        "local_equivalence_flat_count": len(analyses) - len(sensitive),
        "nearest_grid_invariant_mismatch_count": len(grid_mismatch),
        "nearest_grid_invariant_match_count": len(analyses) - len(grid_mismatch),
        "local_only_absorption_blocked_count": local_only_absorption_blocked_count,
        "local_only_absorption_blocked_clears_b7_target": local_only_absorption_blocked_clears_target,
        "min_invariant_derivative_norm": float(min(derivative_norms)) if derivative_norms else None,
        "max_invariant_derivative_norm": float(max(derivative_norms)) if derivative_norms else None,
        "median_invariant_derivative_norm": float(np.median(derivative_norms)) if derivative_norms else None,
        "min_nearest_grid_invariant_distance": float(min(grid_distances)) if grid_distances else None,
        "max_nearest_grid_invariant_distance": float(max(grid_distances)) if grid_distances else None,
        "median_nearest_grid_invariant_distance": float(np.median(grid_distances)) if grid_distances else None,
        "exact_tolerance": EXACT_TOLERANCE,
        "sensitivity_threshold": SENSITIVITY_THRESHOLD,
        "rewrite_claimed": False,
        "resource_saving_claimed": False,
        "semantic_certificate_claimed": False,
        "kak_theorem_claimed": False,
        "obstruction_theorem_claimed": False,
        "validation_error_count": None,
    }
    payload = {
        "benchmark_id": "B1",
        "problem_id": 25,
        "linked_b7_problem_id": 21,
        "title": "B1/B7 cone_01 local-equivalence invariant obligation gate",
        "version": VERSION,
        "last_updated": args.last_updated,
        "status": STATUS,
        "model_status": MODEL_STATUS,
        "method": METHOD,
        "source_qasm": display_path(args.qasm),
        "source_selector": display_path(args.selector),
        "source_feasibility_gate": display_path(args.feasibility),
        "source_parameter_transfer_gate": display_path(args.parameter_transfer),
        "workload": "qasmbench_medium_exact/gcm_h6.qasm",
        "summary": summary,
        "top_windows_by_invariant_derivative": sorted(
            analyses,
            key=lambda item: item["local_equivalence_invariant_derivative_norm"],
            reverse=True,
        )[: args.report_limit],
        "invariant_flat_windows": [
            row
            for row in sorted(
                analyses,
                key=lambda item: item["local_equivalence_invariant_derivative_norm"],
            )
            if not row["local_equivalence_sensitive"]
        ],
        "claim_boundary": {
            "rewrite_claimed": False,
            "resource_saving_claimed": False,
            "semantic_certificate_claimed": False,
            "kak_theorem_claimed": False,
            "obstruction_theorem_claimed": False,
            "physical_layout_claimed": False,
            "supported_claim": (
                "A numerical magic-basis local-equivalence fingerprint shows that 24 of "
                "35 cone_01 windows carry theta in the two-qubit nonlocal fingerprint, "
                "so local-only absorption is blocked for those windows under this diagnostic."
            ),
            "unsupported_claims": [
                "No KAK theorem or formal local-equivalence proof is claimed.",
                "No occurrence-removing rewrite certificate is produced.",
                "The 11 invariant-flat windows are not solved by this diagnostic.",
                "The 24 blocked windows do not meet the 30-window B7 target by themselves.",
                "No B7 FT ledger improvement is counted.",
            ],
            "next_gate": (
                "Attack the 11 invariant-flat windows with exact synthesis or prove a stronger "
                "symbolic invariant; separately, produce replayable occurrence-removing certificates "
                "for at least 30 windows before any B7 resource delta can be counted."
            ),
        },
    }
    errors = validate(payload)
    payload["summary"]["validation_error_count"] = len(errors)
    payload["validation_errors"] = errors
    return payload


def validate(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    summary = payload["summary"]
    claims = payload["claim_boundary"]
    if payload.get("method") != METHOD:
        errors.append("method mismatch")
    if payload.get("status") != STATUS:
        errors.append("status mismatch")
    if payload.get("model_status") != MODEL_STATUS:
        errors.append("model_status mismatch")
    expected = {
        "candidate_window_count": 35,
        "required_exact_windows_for_b7_target": 30,
        "target_proxy_t_ledger_reduction_for_gcm_h6_1_20": 600,
        "local_equivalence_sensitive_count": 24,
        "local_equivalence_flat_count": 11,
        "nearest_grid_invariant_mismatch_count": 24,
        "nearest_grid_invariant_match_count": 11,
        "local_only_absorption_blocked_count": 24,
    }
    for field, value in expected.items():
        if summary.get(field) != value:
            errors.append(f"{field} expected {value}, got {summary.get(field)}")
    if summary.get("local_only_absorption_blocked_clears_b7_target") is not False:
        errors.append("local-only invariant blocking must not be treated as clearing B7 target")
    for field in [
        "rewrite_claimed",
        "resource_saving_claimed",
        "semantic_certificate_claimed",
        "kak_theorem_claimed",
        "obstruction_theorem_claimed",
    ]:
        if summary.get(field) is not False:
            errors.append(f"{field} must remain false in summary")
        if claims.get(field) is not False:
            errors.append(f"{field} must remain false in claim boundary")
    return errors


def markdown(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    lines = [
        "# B1/B7 cone_01 Local-Equivalence Invariant Obligation Gate",
        "",
        f"Status: `{payload['status']}`",
        "",
        "This artifact asks whether the `RY(theta)` parameter inside each `cone_01` "
        "window changes a numerical local-equivalence fingerprint of the two-qubit "
        "unitary. The fingerprint is built from magic-basis traces of the "
        "det-normalized unitary. It is a diagnostic, not a formal KAK theorem.",
        "",
        "## Summary",
        "",
        f"- Candidate windows: `{summary['candidate_window_count']}`",
        f"- Required exact windows for B7 target: `{summary['required_exact_windows_for_b7_target']}`",
        f"- Target proxy-T ledger reduction: `{summary['target_proxy_t_ledger_reduction_for_gcm_h6_1_20']}`",
        f"- Invariant fingerprint: `{summary['invariant_fingerprint']}`",
        f"- Local-equivalence sensitive windows: `{summary['local_equivalence_sensitive_count']}`",
        f"- Local-equivalence flat windows: `{summary['local_equivalence_flat_count']}`",
        f"- Nearest pi/4-grid invariant mismatches: `{summary['nearest_grid_invariant_mismatch_count']}`",
        f"- Nearest pi/4-grid invariant matches: `{summary['nearest_grid_invariant_match_count']}`",
        f"- Local-only absorption blocked count: `{summary['local_only_absorption_blocked_count']}`",
        f"- Local-only absorption blocked clears B7 target: `{summary['local_only_absorption_blocked_clears_b7_target']}`",
        f"- Min / median / max invariant derivative norm: `{summary['min_invariant_derivative_norm']}` / `{summary['median_invariant_derivative_norm']}` / `{summary['max_invariant_derivative_norm']}`",
        f"- Min / median / max nearest-grid invariant distance: `{summary['min_nearest_grid_invariant_distance']}` / `{summary['median_nearest_grid_invariant_distance']}` / `{summary['max_nearest_grid_invariant_distance']}`",
        f"- Validation errors: `{summary['validation_error_count']}`",
        "",
        "## Interpretation",
        "",
        "For 24 of 35 candidate windows, theta changes a local-equivalence invariant "
        "fingerprint. Those windows cannot be dismissed as purely local one-qubit "
        "dressing under this diagnostic. However, 24 is below the 30-window B7 "
        "target, and the 11 invariant-flat windows remain open. No occurrence-removing "
        "certificate or B7 resource saving is claimed.",
        "",
        "## Top Sensitive Windows",
        "",
        "| line | qubit | partner | derivative norm | nearest-grid distance |",
        "|---:|---:|---:|---:|---:|",
    ]
    for row in payload["top_windows_by_invariant_derivative"][:10]:
        lines.append(
            f"| {row['line_number']} | {row['qubit']} | {row['partner']} | "
            f"{row['local_equivalence_invariant_derivative_norm']:.12g} | "
            f"{row['nearest_grid_invariant_distance']:.12g} |"
        )
    lines.extend(
        [
            "",
            "## Invariant-Flat Window Lines",
            "",
            ", ".join(str(row["line_number"]) for row in payload["invariant_flat_windows"]) or "None",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    root = Path(__file__).resolve().parents[1]
    parser.add_argument(
        "--qasm",
        type=Path,
        default=root / "results" / "b1_u3_phase_factored_optimizer" / "qasmbench_medium_exact" / "gcm_h6.qasm",
    )
    parser.add_argument(
        "--selector",
        type=Path,
        default=root / "results" / "B1_B7_gcm_h6_target_selector_v0.json",
    )
    parser.add_argument(
        "--feasibility",
        type=Path,
        default=root / "results" / "B1_B7_gcm_h6_cone_feasibility_gate_v0.json",
    )
    parser.add_argument(
        "--parameter-transfer",
        type=Path,
        default=root / "results" / "B1_B7_cone01_parameter_transfer_gate_v0.json",
    )
    parser.add_argument(
        "--json-output",
        type=Path,
        default=root / "results" / "B1_B7_cone01_local_invariant_obligation_gate_v0.json",
    )
    parser.add_argument(
        "--markdown-output",
        type=Path,
        default=root / "research" / "B1_B7_cone01_local_invariant_obligation_gate.md",
    )
    parser.add_argument("--cone-id", default="cone_01")
    parser.add_argument("--required-windows", type=int, default=30)
    parser.add_argument("--report-limit", type=int, default=12)
    parser.add_argument("--last-updated", default="2026-06-18")
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()

    payload = build_payload(args)
    write_json(args.json_output, payload, args.pretty)
    write_text(args.markdown_output, markdown(payload))
    if args.pretty:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(f"Wrote {args.json_output}")
        print(f"Wrote {args.markdown_output}")


if __name__ == "__main__":
    main()
