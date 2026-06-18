#!/usr/bin/env python3
"""Feasibility gate for B1/B7 gcm_h6 cone rewrite targets.

The target selector finds families with enough occurrences to matter for B7.
This tool asks a stricter question: among those families, which occurrences are
inside pair-local CNOT windows simple enough to be a plausible next semantic
rewrite/synthesis target? It still does not rewrite the circuit.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path


METHOD = "b1_b7_gcm_h6_cone_feasibility_gate_v0"
STATUS = "cone_feasibility_gate_candidate_windows_not_rewrite"
MODEL_STATUS = "posthoc_window_feasibility_not_semantic_certificate"
VERSION = "0.1"
PROXY_T_COST_PER_ARBITRARY_ROTATION = 20

GATE_RE = re.compile(r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*(?:\(([^)]*)\))?\s+(.+);")
QUBIT_RE = re.compile(r"q\[(\d+)\]")
DECIMAL_RE = re.compile(r"[-+]?(?:\d+\.\d*|\.\d+)(?:[eE][-+]?\d+)?")
ROTATION_GATES = {"rx", "ry", "rz"}


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict, pretty: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2 if pretty else None, sort_keys=True) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def parse_qasm(path: Path) -> list[dict]:
    ops = []
    for line_number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        code = raw.split("//", 1)[0].strip()
        if not code or code.startswith(("OPENQASM", "include", "qreg", "creg")):
            continue
        match = GATE_RE.match(code)
        if not match:
            continue
        gate = match.group(1).lower()
        params = match.group(2) or ""
        qubits = [int(item) for item in QUBIT_RE.findall(match.group(3))]
        ops.append(
            {
                "op_index": len(ops),
                "line_number": line_number,
                "gate": gate,
                "params": params,
                "qubits": qubits,
                "text": code,
            }
        )
    return ops


def is_arbitrary_rotation(op: dict) -> bool:
    return op["gate"] in ROTATION_GATES and bool(op["qubits"]) and bool(DECIMAL_RE.search(op["params"]))


def cx_role(op: dict, qubit: int) -> tuple[str, int] | None:
    if op["gate"] != "cx" or len(op["qubits"]) != 2 or qubit not in op["qubits"]:
        return None
    control, target = op["qubits"]
    if qubit == control:
        return ("control", target)
    return ("target", control)


def nearest_cx(ops: list[dict], op_index: int, qubit: int, direction: int) -> tuple[int | None, tuple[str, int] | None]:
    indices = range(op_index - 1, -1, -1) if direction < 0 else range(op_index + 1, len(ops))
    for idx in indices:
        role = cx_role(ops[idx], qubit)
        if role:
            return idx, role
    return None, None


def classify_rotations(ops: list[dict]) -> list[dict]:
    rows = []
    for op in ops:
        if not is_arbitrary_rotation(op):
            continue
        qubit = op["qubits"][0]
        prev_idx, prev_role = nearest_cx(ops, op["op_index"], qubit, -1)
        next_idx, next_role = nearest_cx(ops, op["op_index"], qubit, 1)
        if prev_idx is None or next_idx is None or prev_role is None or next_role is None:
            continue
        cone_signature = (
            op["gate"],
            prev_role[0],
            prev_role[1],
            next_role[0],
            next_role[1],
        )
        pair = {qubit, prev_role[1], next_role[1]}
        window = ops[prev_idx + 1 : next_idx]
        pair_local_window = all(set(item["qubits"]).issubset(pair) for item in window)
        arbitrary_in_window = [item for item in window if is_arbitrary_rotation(item)]
        rows.append(
            {
                "line_number": op["line_number"],
                "op_index": op["op_index"],
                "gate": op["gate"],
                "params": op["params"],
                "qubit": qubit,
                "cone_signature": cone_signature,
                "previous_cx_index": prev_idx,
                "next_cx_index": next_idx,
                "previous_cx_line": ops[prev_idx]["line_number"],
                "next_cx_line": ops[next_idx]["line_number"],
                "previous_cx_role": prev_role[0],
                "previous_cx_partner": prev_role[1],
                "next_cx_role": next_role[0],
                "next_cx_partner": next_role[1],
                "strict_direct_sandwich": prev_idx == op["op_index"] - 1 and next_idx == op["op_index"] + 1,
                "pair_local_window": pair_local_window,
                "window_operation_count": len(window),
                "window_arbitrary_rotation_count": len(arbitrary_in_window),
                "pair_local_single_arbitrary_window": pair_local_window and len(arbitrary_in_window) == 1,
                "window_text": [item["text"] for item in window],
            }
        )
    return rows


def target_cone_signatures(selector: dict) -> dict[tuple, str]:
    signatures = {}
    for row in selector.get("top_cone_targets", []):
        if not row.get("meets_gcm_h6_one_sided_target_if_one_removed_per_occurrence"):
            continue
        signature = (
            row["gate"],
            row["previous_cx_role"],
            row["previous_cx_partner"],
            row["next_cx_role"],
            row["next_cx_partner"],
        )
        signatures[signature] = row["cone_id"]
    return signatures


def build_payload(args: argparse.Namespace) -> dict:
    selector = read_json(args.selector)
    target = int(selector["summary"]["target_removed_arbitrary_occurrences_for_gcm_h6_1_20"])
    ops = parse_qasm(args.qasm)
    classified = classify_rotations(ops)
    target_signatures = target_cone_signatures(selector)
    grouped: dict[tuple, list[dict]] = defaultdict(list)
    for row in classified:
        if row["cone_signature"] in target_signatures:
            grouped[row["cone_signature"]].append(row)

    cone_rows = []
    for signature, members in sorted(grouped.items(), key=lambda item: target_signatures[item[0]]):
        direct_count = sum(1 for row in members if row["strict_direct_sandwich"])
        pair_local_count = sum(1 for row in members if row["pair_local_window"])
        pair_local_single_count = sum(1 for row in members if row["pair_local_single_arbitrary_window"])
        window_ops = Counter(row["window_operation_count"] for row in members)
        window_arbs = Counter(row["window_arbitrary_rotation_count"] for row in members)
        cone_rows.append(
            {
                "cone_id": target_signatures[signature],
                "signature": list(signature),
                "occurrence_count": len(members),
                "strict_direct_sandwich_count": direct_count,
                "pair_local_window_count": pair_local_count,
                "pair_local_single_arbitrary_window_count": pair_local_single_count,
                "meets_target_by_pair_local_single_windows": pair_local_single_count >= target,
                "pair_local_single_window_shortfall": max(0, target - pair_local_single_count),
                "window_operation_count_histogram": dict(sorted(window_ops.items())),
                "window_arbitrary_rotation_count_histogram": dict(sorted(window_arbs.items())),
                "example_windows": [
                    {
                        "line_number": row["line_number"],
                        "qubit": row["qubit"],
                        "params": row["params"],
                        "previous_cx_line": row["previous_cx_line"],
                        "next_cx_line": row["next_cx_line"],
                        "window_text": row["window_text"],
                    }
                    for row in members[:5]
                ],
                "rewrite_claimed": False,
                "semantic_certificate_available": False,
            }
        )

    leading = max(cone_rows, key=lambda row: row["pair_local_single_arbitrary_window_count"]) if cone_rows else {}
    summary = {
        "target_removed_arbitrary_occurrences_for_gcm_h6_1_20": target,
        "target_proxy_t_ledger_reduction_for_gcm_h6_1_20": target * PROXY_T_COST_PER_ARBITRARY_ROTATION,
        "target_cone_class_count": len(cone_rows),
        "target_cone_total_occurrences": sum(row["occurrence_count"] for row in cone_rows),
        "strict_direct_sandwich_total": sum(row["strict_direct_sandwich_count"] for row in cone_rows),
        "pair_local_window_total": sum(row["pair_local_window_count"] for row in cone_rows),
        "pair_local_single_arbitrary_window_total": sum(
            row["pair_local_single_arbitrary_window_count"] for row in cone_rows
        ),
        "cone_classes_meeting_target_by_pair_local_single_windows": sum(
            1 for row in cone_rows if row["meets_target_by_pair_local_single_windows"]
        ),
        "leading_feasible_cone_id": leading.get("cone_id"),
        "leading_feasible_pair_local_single_window_count": leading.get(
            "pair_local_single_arbitrary_window_count", 0
        ),
        "leading_feasible_direct_sandwich_count": leading.get("strict_direct_sandwich_count", 0),
        "rewrite_claimed": False,
        "resource_saving_claimed": False,
        "semantic_certificate_claimed": False,
    }
    payload = {
        "benchmark_id": "B1",
        "problem_id": 25,
        "linked_b7_problem_id": 21,
        "title": "B1/B7 gcm_h6 cone feasibility gate",
        "version": VERSION,
        "last_updated": args.last_updated,
        "status": STATUS,
        "model_status": MODEL_STATUS,
        "method": METHOD,
        "source_qasm": str(args.qasm),
        "source_selector": str(args.selector),
        "workload": "qasmbench_medium_exact/gcm_h6.qasm",
        "summary": summary,
        "cone_feasibility_rows": cone_rows,
        "claim_boundary": {
            "rewrite_claimed": False,
            "resource_saving_claimed": False,
            "semantic_certificate_claimed": False,
            "physical_layout_claimed": False,
            "interpretation": "cone_01_has_enough_pair_local_single_arbitrary_windows_but_no_rewrite_certificate",
            "next_gate": (
                "Run an exact local two-qubit synthesis or constructive semantic rewrite on the leading "
                "pair-local single-arbitrary windows, then re-run the B7 FT ledger only after replayable "
                "certificates exist."
            ),
        },
    }
    errors = validate(payload)
    payload["summary"]["validation_error_count"] = len(errors)
    payload["validation_errors"] = errors
    return payload


def validate(payload: dict) -> list[str]:
    errors = []
    summary = payload["summary"]
    claims = payload["claim_boundary"]
    if payload.get("benchmark_id") != "B1":
        errors.append("benchmark_id must be B1")
    if payload.get("method") != METHOD:
        errors.append("method mismatch")
    if payload.get("status") != STATUS:
        errors.append("status mismatch")
    if summary.get("target_removed_arbitrary_occurrences_for_gcm_h6_1_20") != 30:
        errors.append("target occurrence count must remain 30")
    if summary.get("target_cone_class_count") != 3:
        errors.append("target cone class count should remain 3")
    if summary.get("leading_feasible_cone_id") != "cone_01":
        errors.append("leading feasible cone should be cone_01")
    if summary.get("leading_feasible_pair_local_single_window_count") != 35:
        errors.append("cone_01 pair-local single-arbitrary count should remain 35")
    if summary.get("cone_classes_meeting_target_by_pair_local_single_windows") != 1:
        errors.append("exactly one cone class should meet target by pair-local single windows")
    if summary.get("strict_direct_sandwich_total") != 4:
        errors.append("strict direct sandwich total should remain 4")
    for key in ("rewrite_claimed", "resource_saving_claimed", "semantic_certificate_claimed", "physical_layout_claimed"):
        if claims.get(key) is not False:
            errors.append(f"claim boundary must keep {key}=False")
    return errors


def markdown(payload: dict) -> str:
    summary = payload["summary"]
    lines = [
        "# B1/B7 gcm_h6 Cone Feasibility Gate v0.1",
        "",
        f"Status: **{payload['status']}**",
        "",
        "This gate checks whether the B1/B7 target-selector cones contain local",
        "windows simple enough for the next exact rewrite/synthesis attempt. It does",
        "not rewrite the circuit and does not claim a resource saving.",
        "",
        "## Summary",
        "",
        f"- Target removed arbitrary occurrences: {summary['target_removed_arbitrary_occurrences_for_gcm_h6_1_20']}",
        f"- Target proxy-T ledger reduction: {summary['target_proxy_t_ledger_reduction_for_gcm_h6_1_20']}",
        f"- Target cone classes evaluated: {summary['target_cone_class_count']}",
        f"- Target cone total occurrences: {summary['target_cone_total_occurrences']}",
        f"- Strict direct CNOT-rotation-CNOT sandwiches: {summary['strict_direct_sandwich_total']}",
        f"- Pair-local windows: {summary['pair_local_window_total']}",
        f"- Pair-local single-arbitrary windows: {summary['pair_local_single_arbitrary_window_total']}",
        "- Cone classes meeting target by pair-local single-arbitrary windows: "
        f"{summary['cone_classes_meeting_target_by_pair_local_single_windows']}",
        f"- Leading feasible cone: {summary['leading_feasible_cone_id']}",
        "- Leading feasible cone pair-local single-arbitrary windows: "
        f"{summary['leading_feasible_pair_local_single_window_count']}",
        "",
        "## Cone Feasibility Table",
        "",
        "| Cone | Occurrences | Direct sandwiches | Pair-local windows | Pair-local single-arb windows | Meets 30? | Certificate? |",
        "|---|---:|---:|---:|---:|---|---|",
    ]
    for row in payload["cone_feasibility_rows"]:
        lines.append(
            f"| {row['cone_id']} | {row['occurrence_count']} | {row['strict_direct_sandwich_count']} | "
            f"{row['pair_local_window_count']} | {row['pair_local_single_arbitrary_window_count']} | "
            f"{row['meets_target_by_pair_local_single_windows']} | {row['semantic_certificate_available']} |"
        )
    lines.extend(
        [
            "",
            "## Claim Boundary",
            "",
            "- No rewrite is claimed.",
            "- No resource saving is claimed.",
            "- No semantic certificate is claimed.",
            "- No physical layout result is claimed.",
            "",
            "## Next Gate",
            "",
            "`T-B1-004` should now focus on `cone_01`: synthesize or prove a local",
            "two-qubit semantic rewrite for at least 30 of its pair-local single-arbitrary",
            "windows, emit replayable certificates, and only then re-run the B7 FT ledger.",
            "",
        ]
    )
    return "\n".join(lines)


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--qasm",
        type=Path,
        default=Path("results/b1_u3_phase_factored_optimizer/qasmbench_medium_exact/gcm_h6.qasm"),
    )
    parser.add_argument(
        "--selector",
        type=Path,
        default=Path("results/B1_B7_gcm_h6_target_selector_v0.json"),
    )
    parser.add_argument(
        "--json-output",
        type=Path,
        default=Path("results/B1_B7_gcm_h6_cone_feasibility_gate_v0.json"),
    )
    parser.add_argument(
        "--markdown-output",
        type=Path,
        default=Path("research/B1_B7_gcm_h6_cone_feasibility_gate.md"),
    )
    parser.add_argument("--last-updated", default="2026-06-18")
    parser.add_argument("--pretty", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    payload = build_payload(args)
    write_json(args.json_output, payload, pretty=args.pretty)
    write_text(args.markdown_output, markdown(payload))
    if payload["validation_errors"]:
        for error in payload["validation_errors"]:
            print(f"validation error: {error}", file=sys.stderr)
        return 1
    print(f"wrote {args.json_output}")
    print(f"wrote {args.markdown_output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
