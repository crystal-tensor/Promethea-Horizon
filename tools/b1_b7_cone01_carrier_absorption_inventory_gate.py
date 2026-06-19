#!/usr/bin/env python3
"""Inventory gate for B1/B7 cone_01 single-carrier absorption.

T-B1-004u/v/w established that a single non-Clifford carrier can exactify the
three invariant-flat packets, but that the current ledger treats those carriers
as replacement and they do not naturally coalesce across residual patterns.

This gate asks a narrower follow-up question: do those carrier angles already
appear in the native optimized gcm_h6 rotation inventory in a way that could be
used as an absorption target?  The answer is still not enough.  Some carrier
angles appear elsewhere in the inventory, but one residual pattern has no
matching carrier-angle inventory at all, no pattern has line-local absorption
evidence, and accepted B7 reduction remains zero.
"""

from __future__ import annotations

import argparse
import ast
import json
import math
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
LEDGER_PATH = ROOT / "results" / "B1_B7_cone01_single_carrier_ledger_gate_v0.json"
SHAREABILITY_PATH = ROOT / "results" / "B1_B7_cone01_single_carrier_shareability_gate_v0.json"
PACKET_PATH = ROOT / "results" / "B1_B7_cone01_flat_pattern_kak_packet_v0.json"
INVENTORY_QASM_PATH = ROOT / "results" / "b1_native_t_resource_optimizer" / "qasmbench_medium_exact" / "gcm_h6.qasm"
JSON_OUT = ROOT / "results" / "B1_B7_cone01_carrier_absorption_inventory_gate_v0.json"
MD_OUT = ROOT / "research" / "B1_B7_cone01_carrier_absorption_inventory_gate.md"

METHOD = "b1_b7_cone01_carrier_absorption_inventory_gate_v0"
STATUS = "cone01_carrier_absorption_inventory_negative_gate"
MODEL_STATUS = "carrier_inventory_matches_do_not_form_line_local_absorption_certificate"
PROXY_T_PER_OCCURRENCE = 20
REQUIRED_OCCURRENCE_REMOVALS = 30
ANGLE_TOLERANCE = 1e-9
ROTATION_RE = re.compile(r"^(u3|rx|ry|rz)\((.*)\) q\[(\d+)\];$")


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


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


def wrap_angle(value: float) -> float:
    return (float(value) + math.pi) % (2.0 * math.pi) - math.pi


def same_angle(left: float, right: float, tolerance: float = ANGLE_TOLERANCE) -> bool:
    return abs(wrap_angle(left - right)) <= tolerance


def same_abs_angle(left: float, right: float, tolerance: float = ANGLE_TOLERANCE) -> bool:
    return abs(abs(wrap_angle(left)) - abs(wrap_angle(right))) <= tolerance


def eval_angle_expr(expr: str) -> float:
    tree = ast.parse(expr.strip(), mode="eval")

    def evaluate(node: ast.AST) -> float:
        if isinstance(node, ast.Expression):
            return evaluate(node.body)
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return float(node.value)
        if isinstance(node, ast.Name) and node.id == "pi":
            return math.pi
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
            return -evaluate(node.operand)
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.UAdd):
            return evaluate(node.operand)
        if isinstance(node, ast.BinOp):
            left = evaluate(node.left)
            right = evaluate(node.right)
            if isinstance(node.op, ast.Add):
                return left + right
            if isinstance(node.op, ast.Sub):
                return left - right
            if isinstance(node.op, ast.Mult):
                return left * right
            if isinstance(node.op, ast.Div):
                return left / right
        raise ValueError(f"unsupported angle expression: {expr!r}")

    return evaluate(tree)


def split_args(raw: str) -> list[str]:
    return [item.strip() for item in raw.split(",")]


def parse_rotation_inventory(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        match = ROTATION_RE.match(line.strip())
        if not match:
            continue
        gate, raw_args, qubit_text = match.groups()
        for arg_index, raw_arg in enumerate(split_args(raw_args)):
            rows.append(
                {
                    "line_number": line_number,
                    "gate": gate,
                    "argument_index": arg_index,
                    "raw_angle": raw_arg,
                    "angle": eval_angle_expr(raw_arg),
                    "qubit": int(qubit_text),
                    "text": line.strip(),
                }
            )
    return rows


def compact_matches(matches: list[dict[str, Any]], limit: int = 6) -> list[dict[str, Any]]:
    return [
        {
            "line_number": row["line_number"],
            "gate": row["gate"],
            "argument_index": row["argument_index"],
            "qubit": row["qubit"],
            "raw_angle": row["raw_angle"],
            "text": row["text"],
        }
        for row in matches[:limit]
    ]


def analyze_row(
    ledger_row: dict[str, Any],
    packet: dict[str, Any],
    inventory_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    angle = float(ledger_row["carrier_angle"])
    targets = set(int(q) for q in packet["target_qubits"])
    line_numbers = set(int(line) for line in packet["line_numbers"])

    exact_matches = [row for row in inventory_rows if same_angle(float(row["angle"]), angle)]
    abs_matches = [row for row in inventory_rows if same_abs_angle(float(row["angle"]), angle)]
    same_target_exact = [row for row in exact_matches if int(row["qubit"]) in targets]
    same_target_abs = [row for row in abs_matches if int(row["qubit"]) in targets]
    line_local_exact = [row for row in exact_matches if int(row["line_number"]) in line_numbers]
    line_local_abs = [row for row in abs_matches if int(row["line_number"]) in line_numbers]

    inventory_absorption_candidate = bool(abs_matches)
    same_target_inventory_candidate = bool(same_target_abs)
    line_local_absorption_candidate = bool(line_local_abs)
    accepted_occurrence_removal = 0

    return {
        "pattern_id": ledger_row["pattern_id"],
        "occurrence_count": int(ledger_row["occurrence_count"]),
        "carrier_signature": ledger_row["carrier_signature"],
        "carrier_angle": angle,
        "carrier_axis": ledger_row["carrier_axis"],
        "carrier_local_role": ledger_row["carrier_local_role"],
        "carrier_side": ledger_row["carrier_side"],
        "target_qubits": sorted(targets),
        "source_line_numbers": sorted(line_numbers),
        "inventory_exact_angle_match_count": len(exact_matches),
        "inventory_abs_angle_match_count": len(abs_matches),
        "same_target_exact_angle_match_count": len(same_target_exact),
        "same_target_abs_angle_match_count": len(same_target_abs),
        "line_local_exact_angle_match_count": len(line_local_exact),
        "line_local_abs_angle_match_count": len(line_local_abs),
        "inventory_absorption_candidate": inventory_absorption_candidate,
        "same_target_inventory_candidate": same_target_inventory_candidate,
        "line_local_absorption_candidate": line_local_absorption_candidate,
        "accepted_absorption_certificate": False,
        "accepted_occurrence_removal": accepted_occurrence_removal,
        "accepted_proxy_t_reduction": accepted_occurrence_removal * PROXY_T_PER_OCCURRENCE,
        "sample_abs_angle_matches": compact_matches(abs_matches),
        "sample_same_target_abs_angle_matches": compact_matches(same_target_abs),
        "claim_boundary": (
            "Inventory angle matches are candidate evidence only. They are not adjacency, commutation, "
            "line-local absorption, or replayable occurrence-removing certificates."
        ),
    }


def build_payload() -> dict[str, Any]:
    ledger = load_json(LEDGER_PATH)
    shareability = load_json(SHAREABILITY_PATH)
    packets = {row["pattern_id"]: row for row in load_json(PACKET_PATH)["pattern_packets"]}
    inventory_rows = parse_rotation_inventory(INVENTORY_QASM_PATH)
    rows = [
        analyze_row(row, packets[row["pattern_id"]], inventory_rows)
        for row in ledger.get("carrier_ledger_rows", [])
    ]

    accepted_removed = sum(row["accepted_occurrence_removal"] for row in rows)
    inventory_candidate_count = sum(1 for row in rows if row["inventory_absorption_candidate"])
    same_target_candidate_count = sum(1 for row in rows if row["same_target_inventory_candidate"])
    line_local_candidate_count = sum(1 for row in rows if row["line_local_absorption_candidate"])
    missing_after_gate = max(0, REQUIRED_OCCURRENCE_REMOVALS - accepted_removed)

    summary = {
        "source_method": ledger.get("method"),
        "source_status": ledger.get("status"),
        "source_shareability_method": shareability.get("method"),
        "source_shareability_status": shareability.get("status"),
        "inventory_qasm": display_path(INVENTORY_QASM_PATH),
        "rotation_argument_inventory_count": len(inventory_rows),
        "pattern_group_count": len(rows),
        "covered_invariant_flat_occurrence_count": sum(row["occurrence_count"] for row in rows),
        "carrier_signature_count": len({row["carrier_signature"] for row in rows}),
        "inventory_absorption_candidate_pattern_count": inventory_candidate_count,
        "same_target_inventory_candidate_pattern_count": same_target_candidate_count,
        "line_local_absorption_candidate_pattern_count": line_local_candidate_count,
        "patterns_without_inventory_angle_match": [
            row["pattern_id"] for row in rows if not row["inventory_absorption_candidate"]
        ],
        "patterns_without_same_target_angle_match": [
            row["pattern_id"] for row in rows if not row["same_target_inventory_candidate"]
        ],
        "all_patterns_have_inventory_angle_match": inventory_candidate_count == len(rows),
        "all_patterns_have_same_target_angle_match": same_target_candidate_count == len(rows),
        "all_patterns_have_line_local_absorption_candidate": line_local_candidate_count == len(rows),
        "accepted_absorption_certificate_count": 0,
        "accepted_occurrence_removal": accepted_removed,
        "accepted_proxy_t_reduction": accepted_removed * PROXY_T_PER_OCCURRENCE,
        "missing_occurrences_after_gate": missing_after_gate,
        "missing_proxy_t_after_gate": missing_after_gate * PROXY_T_PER_OCCURRENCE,
        "carrier_absorption_certificate_claimed": False,
        "carrier_ledger_reduction_claimed": False,
        "rewrite_claimed": False,
        "semantic_certificate_claimed": False,
        "resource_saving_claimed": False,
        "b7_ledger_improvement_claimed": False,
        "validation_error_count": None,
    }
    payload = {
        "benchmark_id": "B1",
        "problem_id": 25,
        "linked_b7_problem_id": 21,
        "title": "B1/B7 cone_01 carrier absorption inventory gate",
        "status": STATUS,
        "model_status": MODEL_STATUS,
        "method": METHOD,
        "source_result": display_path(LEDGER_PATH),
        "source_shareability_result": display_path(SHAREABILITY_PATH),
        "source_method": ledger.get("method"),
        "source_shareability_method": shareability.get("method"),
        "workload": ledger.get("workload", "qasmbench_medium_exact/gcm_h6.qasm"),
        "summary": summary,
        "carrier_absorption_inventory_rows": rows,
        "claim_boundary": {
            "carrier_absorption_certificate_claimed": False,
            "carrier_ledger_reduction_claimed": False,
            "rewrite_claimed": False,
            "semantic_certificate_claimed": False,
            "resource_saving_claimed": False,
            "b7_ledger_improvement_claimed": False,
            "supported_claim": (
                "Carrier angles were compared against the native optimized gcm_h6 rotation inventory. "
                "Inventory matches exist for only a subset of carrier patterns, and no line-local "
                "absorption certificate is accepted."
            ),
            "unsupported_claims": [
                "Inventory angle matches are not replayable rewrite certificates.",
                "Same-target matches are not adjacency, commutation, or absorption proofs.",
                "No carrier occurrence is removed from the accepted B7 ledger.",
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
    if payload.get("status") != STATUS:
        errors.append("status_mismatch")
    if payload.get("source_method") != "b1_b7_cone01_single_carrier_ledger_gate_v0":
        errors.append("source_method_mismatch")
    if payload.get("source_shareability_method") != "b1_b7_cone01_single_carrier_shareability_gate_v0":
        errors.append("source_shareability_method_mismatch")
    expected = {
        "pattern_group_count": 3,
        "covered_invariant_flat_occurrence_count": 11,
        "carrier_signature_count": 3,
        "inventory_absorption_candidate_pattern_count": 2,
        "same_target_inventory_candidate_pattern_count": 2,
        "line_local_absorption_candidate_pattern_count": 0,
        "accepted_absorption_certificate_count": 0,
        "accepted_occurrence_removal": 0,
        "accepted_proxy_t_reduction": 0,
        "missing_occurrences_after_gate": 30,
        "missing_proxy_t_after_gate": 600,
    }
    for field, value in expected.items():
        if summary.get(field) != value:
            errors.append(f"{field}_mismatch")
    if summary.get("patterns_without_inventory_angle_match") != ["flat_pattern_02"]:
        errors.append("patterns_without_inventory_angle_match_mismatch")
    if summary.get("patterns_without_same_target_angle_match") != ["flat_pattern_02"]:
        errors.append("patterns_without_same_target_angle_match_mismatch")
    if summary.get("all_patterns_have_inventory_angle_match") is not False:
        errors.append("inventory_match_must_not_cover_all_patterns")
    if summary.get("all_patterns_have_same_target_angle_match") is not False:
        errors.append("same_target_match_must_not_cover_all_patterns")
    if summary.get("all_patterns_have_line_local_absorption_candidate") is not False:
        errors.append("line_local_absorption_must_not_cover_all_patterns")
    for row in payload.get("carrier_absorption_inventory_rows", []):
        if row.get("accepted_absorption_certificate") is not False:
            errors.append(f"{row.get('pattern_id')}_accepted_certificate_must_be_false")
        if row.get("accepted_occurrence_removal") != 0:
            errors.append(f"{row.get('pattern_id')}_accepted_removal_must_be_zero")
    for field in [
        "carrier_absorption_certificate_claimed",
        "carrier_ledger_reduction_claimed",
        "rewrite_claimed",
        "semantic_certificate_claimed",
        "resource_saving_claimed",
        "b7_ledger_improvement_claimed",
    ]:
        if summary.get(field) is not False:
            errors.append(f"{field}_must_remain_false")
        if claims.get(field) is not False:
            errors.append(f"claim_boundary_{field}_must_remain_false")
    return errors


def markdown(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    lines = [
        "# B1/B7 Cone_01 Carrier Absorption Inventory Gate",
        "",
        f"Status: `{payload['status']}`",
        "",
        "This artifact consumes T-B1-004v/w and checks whether single-carrier angles have absorption targets in the native optimized gcm_h6 rotation inventory.",
        "",
        "## Summary",
        "",
        f"- Rotation argument inventory count: `{summary['rotation_argument_inventory_count']}`",
        f"- Pattern groups / covered occurrences: `{summary['pattern_group_count']}` / `{summary['covered_invariant_flat_occurrence_count']}`",
        f"- Inventory absorption candidate patterns: `{summary['inventory_absorption_candidate_pattern_count']}` / `{summary['pattern_group_count']}`",
        f"- Same-target inventory candidate patterns: `{summary['same_target_inventory_candidate_pattern_count']}` / `{summary['pattern_group_count']}`",
        f"- Line-local absorption candidate patterns: `{summary['line_local_absorption_candidate_pattern_count']}` / `{summary['pattern_group_count']}`",
        f"- Patterns without any inventory angle match: `{', '.join(summary['patterns_without_inventory_angle_match'])}`",
        f"- Accepted occurrence/proxy-T reduction: `{summary['accepted_occurrence_removal']}` / `{summary['accepted_proxy_t_reduction']}`",
        f"- Validation errors: `{summary['validation_error_count']}`",
        "",
        "## Rows",
        "",
        "| Pattern | Occurrences | Inventory abs-angle matches | Same-target matches | Line-local matches | Accepted reduction |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for row in payload["carrier_absorption_inventory_rows"]:
        lines.append(
            f"| {row['pattern_id']} | {row['occurrence_count']} | "
            f"{row['inventory_abs_angle_match_count']} | "
            f"{row['same_target_abs_angle_match_count']} | "
            f"{row['line_local_abs_angle_match_count']} | "
            f"{row['accepted_proxy_t_reduction']} |"
        )
    lines.extend(
        [
            "",
            "## Claim Boundary",
            "",
            "- Angle inventory matches are only candidate evidence.",
            "- Same-target matches are not adjacency, commutation, or absorption proofs.",
            "- `flat_pattern_02` has no carrier-angle inventory match under this parser.",
            "- No line-local carrier absorption certificate is accepted.",
            "- No rewrite, semantic certificate, physical cost model, or B7 ledger improvement is claimed.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json-out", type=Path, default=JSON_OUT)
    parser.add_argument("--md-out", type=Path, default=MD_OUT)
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()
    payload = build_payload()
    write_json(args.json_out, payload, args.pretty)
    write_text(args.md_out, markdown(payload))
    print(json.dumps(payload["summary"], indent=2 if args.pretty else None, sort_keys=True))


if __name__ == "__main__":
    main()
