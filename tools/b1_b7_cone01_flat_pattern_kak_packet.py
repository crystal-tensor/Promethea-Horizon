#!/usr/bin/env python3
"""KAK-work-packet gate for B1/B7 cone_01 invariant-flat patterns.

T-B1-004p reduced the 11 invariant-flat cone_01 windows to three normalized
pattern groups. This gate does not solve those patterns. It computes a compact
two-qubit nonlocal-invariant packet for the three groups, checks whether their
nearest pi/4-grid representatives share the same nonlocal fingerprint, and
records why that still is not an occurrence-removing rewrite certificate.
"""

from __future__ import annotations

import argparse
import json
import math
import re
from pathlib import Path
from typing import Any

import numpy as np

from b1_b7_cone01_local_invariant_obligation_gate import invariant_fingerprint, nearest_pi_over_four
from b1_b7_cone01_phase_removal_gate import residual_norm, unitary_for_ops


ROOT = Path(__file__).resolve().parents[1]
SOURCE_PATH = ROOT / "results" / "B1_B7_cone01_invariant_flat_residual_gate_v0.json"
JSON_OUT = ROOT / "results" / "B1_B7_cone01_flat_pattern_kak_packet_v0.json"
MD_OUT = ROOT / "research" / "B1_B7_cone01_flat_pattern_kak_packet.md"

METHOD = "b1_b7_cone01_flat_pattern_kak_packet_v0"
STATUS = "cone01_flat_pattern_kak_packet_not_rewrite_certificate"
MODEL_STATUS = "nonlocal_class_packet_requires_local_dressing_or_rewrite_certificate"
EXACT_TOLERANCE = 1e-8
FINGERPRINT_TOLERANCE = 1e-8
PROXY_T_PER_OCCURRENCE = 20
REQUIRED_OCCURRENCE_REMOVALS = 30


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def display_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path)


def normalized_qubit(label: str) -> int:
    if label == "partner":
        return 0
    if label == "target":
        return 1
    raise ValueError(f"unsupported normalized qubit label: {label}")


def parse_normalized_op(text: str) -> dict[str, Any]:
    if text.startswith("cx "):
        labels = re.findall(r"q\[(partner|target)\]", text)
        if len(labels) != 2:
            raise ValueError(f"bad cx text: {text}")
        return {"gate": "cx", "qubits": [normalized_qubit(label) for label in labels], "text": text}
    match = re.match(r"(rz|ry|rx)\(([^)]+)\) q\[(partner|target)\];", text)
    if not match:
        raise ValueError(f"bad normalized op text: {text}")
    return {
        "gate": match.group(1),
        "params": match.group(2),
        "qubits": [normalized_qubit(match.group(3))],
        "text": text,
    }


def replace_target_ry_with_grid(ops: list[dict[str, Any]], theta: float) -> list[dict[str, Any]]:
    output = []
    replaced = False
    for op in ops:
        clone = dict(op)
        if clone["gate"] == "ry" and clone["qubits"] == [1] and not replaced:
            clone["params"] = f"{theta:.17g}"
            clone["text"] = f"ry({theta:.17g}) q[target];"
            replaced = True
        output.append(clone)
    if not replaced:
        raise ValueError("normalized pattern does not contain a target RY")
    return output


def fingerprint_key(values: list[float], digits: int = 10) -> tuple[float, ...]:
    return tuple(round(float(value), digits) for value in values)


def analyze_pattern(group: dict[str, Any]) -> dict[str, Any]:
    ops = [parse_normalized_op(text) for text in group["normalized_window_text"]]
    target = unitary_for_ops(ops, [0, 1])
    theta = float(group["theta"])
    grid_label, grid_angle, theta_to_grid_distance = nearest_pi_over_four(theta)
    grid_ops = replace_target_ry_with_grid(ops, grid_angle)
    grid_unitary = unitary_for_ops(grid_ops, [0, 1])
    fingerprint = [float(value) for value in invariant_fingerprint(target)]
    grid_fingerprint = [float(value) for value in invariant_fingerprint(grid_unitary)]
    fingerprint_distance = float(np.linalg.norm(np.array(fingerprint) - np.array(grid_fingerprint)))
    grid_residual = residual_norm(grid_unitary, target)
    return {
        "pattern_id": group["pattern_id"],
        "theta": group["theta"],
        "occurrence_count": group["occurrence_count"],
        "line_numbers": group["line_numbers"],
        "target_qubits": group["target_qubits"],
        "partner_qubits": group["partner_qubits"],
        "normalized_window_text": group["normalized_window_text"],
        "nonlocal_fingerprint": fingerprint,
        "nearest_grid_label": grid_label,
        "nearest_grid_angle": grid_angle,
        "theta_to_nearest_grid_distance": theta_to_grid_distance,
        "nearest_grid_nonlocal_fingerprint": grid_fingerprint,
        "nearest_grid_nonlocal_fingerprint_distance": fingerprint_distance,
        "nearest_grid_nonlocal_match": fingerprint_distance <= FINGERPRINT_TOLERANCE,
        "same_envelope_grid_residual_norm": grid_residual,
        "same_envelope_grid_exact_pass": grid_residual <= EXACT_TOLERANCE,
        "local_dressing_or_rewrite_obligation": grid_residual > EXACT_TOLERANCE
        and fingerprint_distance <= FINGERPRINT_TOLERANCE,
    }


def build_payload() -> dict[str, Any]:
    source = load_json(SOURCE_PATH)
    source_summary = source.get("summary", {})
    groups = source.get("flat_pattern_groups", [])
    analyses = [analyze_pattern(group) for group in groups]
    total_occurrences = sum(int(row["occurrence_count"]) for row in analyses)
    fingerprint_keys = {fingerprint_key(row["nonlocal_fingerprint"]) for row in analyses}
    grid_match_count = sum(1 for row in analyses if row["nearest_grid_nonlocal_match"])
    same_envelope_exact_count = sum(1 for row in analyses if row["same_envelope_grid_exact_pass"])
    local_dressing_count = sum(1 for row in analyses if row["local_dressing_or_rewrite_obligation"])
    max_occurrence_removal_if_all_patterns_solved = total_occurrences
    max_proxy_t_reduction_if_all_patterns_solved = total_occurrences * PROXY_T_PER_OCCURRENCE
    missing_occurrences = max(0, REQUIRED_OCCURRENCE_REMOVALS - total_occurrences)
    summary = {
        "source_method": source.get("method"),
        "source_status": source.get("status"),
        "pattern_group_count": len(analyses),
        "covered_invariant_flat_occurrence_count": total_occurrences,
        "source_invariant_flat_window_count": source_summary.get("invariant_flat_window_count"),
        "unique_nonlocal_fingerprint_count": len(fingerprint_keys),
        "all_patterns_share_nonlocal_fingerprint": len(fingerprint_keys) == 1,
        "nearest_grid_nonlocal_match_count": grid_match_count,
        "same_envelope_grid_exact_pass_count": same_envelope_exact_count,
        "local_dressing_or_rewrite_obligation_count": local_dressing_count,
        "best_same_envelope_grid_residual_norm": min(
            (row["same_envelope_grid_residual_norm"] for row in analyses),
            default=None,
        ),
        "max_same_envelope_grid_residual_norm": max(
            (row["same_envelope_grid_residual_norm"] for row in analyses),
            default=None,
        ),
        "required_occurrence_removals_for_b7_target": REQUIRED_OCCURRENCE_REMOVALS,
        "proxy_t_per_occurrence": PROXY_T_PER_OCCURRENCE,
        "max_occurrence_removal_if_all_patterns_solved": max_occurrence_removal_if_all_patterns_solved,
        "max_proxy_t_reduction_if_all_patterns_solved": max_proxy_t_reduction_if_all_patterns_solved,
        "all_patterns_solved_clears_b7_target": total_occurrences >= REQUIRED_OCCURRENCE_REMOVALS,
        "missing_occurrences_after_all_patterns_solved": missing_occurrences,
        "missing_proxy_t_after_all_patterns_solved": missing_occurrences * PROXY_T_PER_OCCURRENCE,
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
        "title": "B1/B7 cone_01 flat-pattern KAK packet",
        "status": STATUS,
        "model_status": MODEL_STATUS,
        "method": METHOD,
        "source_result": display_path(SOURCE_PATH),
        "source_method": source.get("method"),
        "workload": "qasmbench_medium_exact/gcm_h6.qasm",
        "summary": summary,
        "pattern_packets": analyses,
        "claim_boundary": {
            "rewrite_claimed": False,
            "semantic_certificate_claimed": False,
            "kak_theorem_claimed": False,
            "resource_saving_claimed": False,
            "b7_ledger_improvement_claimed": False,
            "supported_claim": (
                "The three invariant-flat pattern groups share one numerical nonlocal "
                "fingerprint and each matches a nearest pi/4-grid nonlocal fingerprint, "
                "but same-envelope grid replacement is still not exact."
            ),
            "unsupported_claims": [
                "This is not a KAK theorem or proof-assistant checked statement.",
                "This is not an occurrence-removing rewrite certificate.",
                "Nearest-grid nonlocal-class agreement is not a B7 ledger reduction.",
                "Solving all three pattern groups would still cover only 11 of 30 required occurrences.",
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
    claims = payload["claim_boundary"]
    if payload.get("method") != METHOD:
        errors.append("method_mismatch")
    if payload.get("source_method") != "b1_b7_cone01_invariant_flat_residual_gate_v0":
        errors.append("source_method_mismatch")
    if summary.get("pattern_group_count") != 3:
        errors.append("pattern_group_count_mismatch")
    if summary.get("covered_invariant_flat_occurrence_count") != 11:
        errors.append("covered_occurrence_count_mismatch")
    if summary.get("source_invariant_flat_window_count") != 11:
        errors.append("source_flat_window_count_mismatch")
    if summary.get("unique_nonlocal_fingerprint_count") != 1:
        errors.append("unique_nonlocal_fingerprint_count_mismatch")
    if summary.get("all_patterns_share_nonlocal_fingerprint") is not True:
        errors.append("patterns_should_share_nonlocal_fingerprint")
    if summary.get("nearest_grid_nonlocal_match_count") != 3:
        errors.append("nearest_grid_nonlocal_match_count_mismatch")
    if summary.get("same_envelope_grid_exact_pass_count") != 0:
        errors.append("same_envelope_grid_exact_pass_count_must_remain_zero")
    if summary.get("local_dressing_or_rewrite_obligation_count") != 3:
        errors.append("local_dressing_obligation_count_mismatch")
    if summary.get("all_patterns_solved_clears_b7_target") is not False:
        errors.append("flat_patterns_must_not_clear_b7_target")
    if summary.get("missing_occurrences_after_all_patterns_solved") != 19:
        errors.append("missing_occurrences_mismatch")
    if summary.get("missing_proxy_t_after_all_patterns_solved") != 380:
        errors.append("missing_proxy_t_mismatch")
    for field in [
        "rewrite_claimed",
        "semantic_certificate_claimed",
        "kak_theorem_claimed",
        "resource_saving_claimed",
        "b7_ledger_improvement_claimed",
    ]:
        if summary.get(field) is not False or claims.get(field) is not False:
            errors.append(f"forbidden_claim_{field}")
    return errors


def write_markdown(payload: dict[str, Any], path: Path) -> None:
    summary = payload["summary"]
    lines = [
        "# B1/B7 Cone 01 Flat-Pattern KAK Packet",
        "",
        f"Status: `{payload['status']}`",
        "",
        "This artifact turns the three invariant-flat residual pattern groups into "
        "a compact nonlocal-invariant work packet. It is not a KAK theorem, not a "
        "semantic rewrite certificate, and not a B7 resource claim.",
        "",
        "## Summary",
        "",
        f"- Pattern groups: `{summary['pattern_group_count']}`",
        f"- Covered invariant-flat occurrences: `{summary['covered_invariant_flat_occurrence_count']}`",
        f"- Unique nonlocal fingerprints: `{summary['unique_nonlocal_fingerprint_count']}`",
        f"- Nearest-grid nonlocal matches: `{summary['nearest_grid_nonlocal_match_count']}`",
        f"- Same-envelope grid exact passes: `{summary['same_envelope_grid_exact_pass_count']}`",
        f"- Local dressing or rewrite obligations: `{summary['local_dressing_or_rewrite_obligation_count']}`",
        f"- Max occurrence removal if all patterns are solved: `{summary['max_occurrence_removal_if_all_patterns_solved']}`",
        f"- Missing occurrences after all patterns are solved: `{summary['missing_occurrences_after_all_patterns_solved']}`",
        "",
        "## Pattern Packets",
        "",
        "| Pattern | Occurrences | Nearest grid | Nonlocal match | Same-envelope residual | Obligation |",
        "|---|---:|---|---|---:|---|",
    ]
    for row in payload["pattern_packets"]:
        lines.append(
            "| {pattern_id} | {occurrence_count} | `{nearest_grid_label}` | `{match}` | `{residual:.12g}` | `{obligation}` |".format(
                pattern_id=row["pattern_id"],
                occurrence_count=row["occurrence_count"],
                nearest_grid_label=row["nearest_grid_label"],
                match=row["nearest_grid_nonlocal_match"],
                residual=row["same_envelope_grid_residual_norm"],
                obligation=row["local_dressing_or_rewrite_obligation"],
            )
        )
    lines.extend(
        [
            "",
            "## Claim Boundary",
            "",
            "- Nearest-grid nonlocal-class agreement is a work-packet signal, not a rewrite.",
            "- Same-envelope grid replacement has zero exact passes across the three pattern groups.",
            "- All three groups together cover only 11 occurrences, so they cannot clear the B7 30-occurrence target alone.",
            "- No KAK theorem, semantic certificate, resource saving, or B7 ledger improvement is claimed.",
            "",
            f"Validation error count: `{summary['validation_error_count']}`",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json-output", type=Path, default=JSON_OUT)
    parser.add_argument("--markdown-output", type=Path, default=MD_OUT)
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()

    payload = build_payload()
    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
    args.json_output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(payload, args.markdown_output)
    if args.pretty:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(f"Wrote {args.json_output}")
        print(f"Wrote {args.markdown_output}")


if __name__ == "__main__":
    main()
