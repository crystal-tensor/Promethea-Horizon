#!/usr/bin/env python3
"""T-B1-004gi/T-B7-015r: R85 G1 rotation-row intake gate."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import time
from pathlib import Path
from typing import Any


TOOL_DIR = Path(__file__).resolve().parent
if str(TOOL_DIR) not in sys.path:
    sys.path.insert(0, str(TOOL_DIR))

from b7_ft_synthesis_ledger import (  # noqa: E402
    GATE_RE,
    PARAM_RE,
    QUBIT_RE,
    classify_rotation,
    gate_rotation_params,
    split_params,
)


METHOD = "b1_b7_cone01_r85_g1_rotation_row_intake_gate_v0"
STATUS = "cone01_r85_g1_source_rotation_rows_intake_ready_no_credit"
MODEL_STATUS = "r84_selected_g1_materialized_as_source_backed_rotation_row_intake"
VERSION = "0.1"
TARGET_ID = "T-B1-004gi/T-B7-015r"
UPSTREAM_TARGET_ID = "T-B1-004gh/T-B7-015q"
SUBMISSION_DIR = "results/B1_B7_cone01_o3_f4_exit_route_submissions"

R84_RESULT = "results/B1_B7_cone01_R84_work_packet_triage_gate_v0.json"
R84_PRIORITY_PACKET = f"{SUBMISSION_DIR}/R84-priority-gap-closure-packet.json"
R83_CONTRACT = f"{SUBMISSION_DIR}/R83-b7-gap-closure.contract.json"
B7_NUMERIC_STRUCTURE = "results/B7_gcm_h6_numeric_rotation_structure_v0.json"
SOURCE_QASM = "results/b1_u3_phase_factored_optimizer/qasmbench_medium_exact/gcm_h6.qasm"

R85_SOURCE_ROWS = f"{SUBMISSION_DIR}/R85-G1-source-rotation-rows.json"
R85_T_MAPPING = f"{SUBMISSION_DIR}/R85-G1-candidate-logical-t-mapping.json"
R85_NO_DOUBLE_COUNTING = f"{SUBMISSION_DIR}/R85-G1-no-double-counting-screen.json"
R85_PREFLIGHT = f"{SUBMISSION_DIR}/R85-G1-row-intake-preflight.verdict.json"
R85_BLOCKER_QUEUE = f"{SUBMISSION_DIR}/R85-G1-row-intake-blocker-queue.json"
R85_STDOUT = f"{SUBMISSION_DIR}/R85-G1-row-intake.stdout.txt"


def stable_hash(payload: Any) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def stable_self_hash(payload: dict[str, Any], hash_key: str) -> str:
    copy = dict(payload)
    copy.pop(hash_key, None)
    return stable_hash(copy)


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def req(requirement_id: str, label: str, passed: bool, evidence: dict[str, Any]) -> dict[str, Any]:
    return {
        "requirement_id": requirement_id,
        "label": label,
        "passed": bool(passed),
        "evidence": evidence,
    }


def extract_arbitrary_rotation_components(qasm_path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line_number, raw in enumerate(qasm_path.read_text(encoding="utf-8").splitlines(), start=1):
        code = raw.strip()
        lower = code.lower()
        if (
            not lower
            or lower.startswith("//")
            or lower.startswith("openqasm")
            or lower.startswith("include")
            or lower.startswith("qreg")
            or lower.startswith("creg")
            or lower.startswith("barrier")
            or lower.startswith("measure")
        ):
            continue
        param_match = PARAM_RE.match(lower)
        gate_match = GATE_RE.match(lower)
        if param_match:
            gate = param_match.group(1)
            params = split_params(param_match.group(2))
            operand_text = param_match.group(3)
        elif gate_match:
            gate = gate_match.group(1)
            params = []
            operand_text = gate_match.group(2)
        else:
            continue
        qubits = [f"q[{value}]" for value in QUBIT_RE.findall(operand_text)]
        for component_index, (axis, expression) in enumerate(gate_rotation_params(gate, params)):
            family = classify_rotation(expression)
            if family != "arbitrary_numeric_rotation":
                continue
            source_component_id = f"gcm_h6:L{line_number}:C{component_index}:{axis}:{expression}:{','.join(qubits)}"
            rows.append(
                {
                    "row_id": f"G1-R{len(rows) + 1:02d}",
                    "source_component_id": source_component_id,
                    "source_qasm_path": SOURCE_QASM,
                    "source_line_number": line_number,
                    "source_line_text": code,
                    "source_line_sha256": hashlib.sha256(code.encode("utf-8")).hexdigest(),
                    "gate": gate,
                    "axis": axis,
                    "angle_expression": expression,
                    "rotation_family": family,
                    "qubits": qubits,
                    "component_index_in_gate_rotation_expansion": component_index,
                    "candidate_proxy_t_cost_before": 20,
                    "candidate_proxy_t_cost_after_if_removed_or_repriced": 0,
                    "candidate_t_ledger_reduction": 20,
                    "evidence_status": "source_row_identified_not_replay_verified",
                    "accepted": False,
                }
            )
    return rows


def build_source_rows(
    root: Path,
    r84_result: dict[str, Any],
    priority_packet: dict[str, Any],
    b7_numeric: dict[str, Any],
) -> dict[str, Any]:
    all_components = extract_arbitrary_rotation_components(root / SOURCE_QASM)
    selected = all_components[:30]
    payload = {
        "artifact": "R85 G1 source-backed rotation row intake",
        "method": METHOD,
        "source_target_id": TARGET_ID,
        "upstream_target_id": UPSTREAM_TARGET_ID,
        "route_id": priority_packet["route_id"],
        "source_qasm_path": SOURCE_QASM,
        "source_qasm_sha256": file_hash(root / SOURCE_QASM),
        "source_b7_numeric_structure_path": B7_NUMERIC_STRUCTURE,
        "source_b7_numeric_structure_sha256": file_hash(root / B7_NUMERIC_STRUCTURE),
        "source_b7_numeric_structure_status": b7_numeric["status"],
        "source_r84_payload_hash": r84_result["payload_hash"],
        "total_arbitrary_numeric_components_by_b7_classifier": len(all_components),
        "b7_reported_arbitrary_numeric_rotations": b7_numeric["after_ft_resource"][
            "rotation_family_counts"
        ]["arbitrary_numeric_rotation"],
        "selection_rule": "first_30_arbitrary_numeric_rotation_components_in_qasm_order",
        "selected_row_count": len(selected),
        "target_selected_row_count": 30,
        "rows": selected,
        "claim_boundary": (
            "These are source-backed candidate rows only. They are not accepted "
            "rotation removals, not replay evidence, and not B7 credit."
        ),
    }
    payload["source_rows_hash"] = stable_self_hash(payload, "source_rows_hash")
    return payload


def build_candidate_t_mapping(source_rows: dict[str, Any], priority_packet: dict[str, Any]) -> dict[str, Any]:
    rows = [
        {
            "row_id": row["row_id"],
            "source_component_id": row["source_component_id"],
            "candidate_t_ledger_reduction": row["candidate_t_ledger_reduction"],
            "accepted_t_ledger_reduction": 0,
            "accepted": False,
        }
        for row in source_rows["rows"]
    ]
    total_candidate = sum(row["candidate_t_ledger_reduction"] for row in rows)
    mapping = {
        "artifact": "R85 G1 candidate logical-T mapping",
        "method": METHOD,
        "source_target_id": TARGET_ID,
        "upstream_target_id": UPSTREAM_TARGET_ID,
        "route_id": priority_packet["route_id"],
        "source_rows_hash": source_rows["source_rows_hash"],
        "candidate_row_count": len(rows),
        "candidate_t_ledger_reduction": total_candidate,
        "minimum_accepted_t_ledger_reduction": priority_packet[
            "minimum_accepted_t_ledger_reduction"
        ],
        "candidate_after_t_ledger_if_all_rows_accepted": priority_packet[
            "target_1_20_max_after_t_ledger"
        ]
        - (
            total_candidate
            - priority_packet["minimum_accepted_t_ledger_reduction"]
        ),
        "accepted_t_ledger_reduction": 0,
        "rows": rows,
        "claim_boundary": "Candidate mapping only; accepted logical-T reduction remains zero.",
    }
    mapping["mapping_hash"] = stable_self_hash(mapping, "mapping_hash")
    return mapping


def build_no_double_counting_screen(source_rows: dict[str, Any]) -> dict[str, Any]:
    component_ids = [row["source_component_id"] for row in source_rows["rows"]]
    line_component_pairs = [
        [row["source_line_number"], row["component_index_in_gate_rotation_expansion"]]
        for row in source_rows["rows"]
    ]
    screen = {
        "artifact": "R85 G1 no-double-counting screen",
        "method": METHOD,
        "source_target_id": TARGET_ID,
        "upstream_target_id": UPSTREAM_TARGET_ID,
        "source_rows_hash": source_rows["source_rows_hash"],
        "selected_row_count": source_rows["selected_row_count"],
        "unique_source_component_count": len(set(component_ids)),
        "unique_line_component_pair_count": len({tuple(pair) for pair in line_component_pairs}),
        "duplicate_source_component_ids": sorted(
            component_id for component_id in set(component_ids) if component_ids.count(component_id) > 1
        ),
        "same_line_multi_component_rows": [
            row["row_id"]
            for row in source_rows["rows"]
            if sum(1 for other in source_rows["rows"] if other["source_line_number"] == row["source_line_number"]) > 1
        ],
        "screen_passed": len(set(component_ids)) == len(component_ids),
        "accepted_b7_credit_delta": 0,
        "claim_boundary": (
            "The screen checks uniqueness of selected source components only. It is "
            "not a full no-double-counting proof for an accepted rewrite."
        ),
    }
    screen["screen_hash"] = stable_self_hash(screen, "screen_hash")
    return screen


def build_preflight(
    source_rows: dict[str, Any],
    mapping: dict[str, Any],
    no_double_counting: dict[str, Any],
    priority_packet: dict[str, Any],
) -> dict[str, Any]:
    gates = {
        "source_rows_present": source_rows["selected_row_count"] == 30,
        "source_rows_match_b7_classifier_count": source_rows[
            "total_arbitrary_numeric_components_by_b7_classifier"
        ]
        == source_rows["b7_reported_arbitrary_numeric_rotations"]
        == 270,
        "candidate_t_ledger_reduction_reaches_600": mapping[
            "candidate_t_ledger_reduction"
        ]
        == priority_packet["candidate_t_ledger_reduction"]
        == 600,
        "component_uniqueness_screen_passed": no_double_counting["screen_passed"] is True,
        "replay_stdout_present": False,
        "stv_reprice_ledger_present": False,
        "filled_r83_submission_present": False,
        "downstream_b7_replay_present": False,
    }
    failed = [gate for gate, passed in gates.items() if not passed]
    preflight = {
        "artifact": "R85 G1 row-intake preflight verdict",
        "method": METHOD,
        "source_target_id": TARGET_ID,
        "upstream_target_id": UPSTREAM_TARGET_ID,
        "route_id": priority_packet["route_id"],
        "source_rows_hash": source_rows["source_rows_hash"],
        "mapping_hash": mapping["mapping_hash"],
        "no_double_counting_screen_hash": no_double_counting["screen_hash"],
        "gates": gates,
        "passed_gate_count": sum(1 for passed in gates.values() if passed),
        "failed_gate_count": len(failed),
        "failed_gates": failed,
        "accepted": False,
        "accepted_b7_credit_delta": 0,
        "accepted_b7_space_time_volume_credit": 0,
        "o3_closed": False,
        "reroute_allowed": False,
        "resource_saving_claimed": False,
        "claim_boundary": (
            "R85 accepts source-row intake shape only. It rejects credit because "
            "replay stdout, STV reprice, filled R83 submission, and downstream B7 replay are missing."
        ),
    }
    preflight["preflight_hash"] = stable_self_hash(preflight, "preflight_hash")
    return preflight


def build_blocker_queue(preflight: dict[str, Any]) -> dict[str, Any]:
    queue = {
        "artifact": "R85 G1 row-intake blocker queue",
        "method": METHOD,
        "source_target_id": TARGET_ID,
        "upstream_target_id": UPSTREAM_TARGET_ID,
        "preflight_hash": preflight["preflight_hash"],
        "accepted_b7_credit_delta": 0,
        "queue": [
            {
                "blocker_id": "R85-G1-1",
                "priority": 1,
                "target_gate": "row_replay_stdout_present",
                "needed_artifact": "machine-check replay stdout binding all 30 selected source components",
            },
            {
                "blocker_id": "R85-G1-2",
                "priority": 2,
                "target_gate": "stv_reprice_ledger_present",
                "needed_artifact": "STV reprice ledger showing candidate rows map to the 1.20x target",
            },
            {
                "blocker_id": "R85-G1-3",
                "priority": 3,
                "target_gate": "filled_r83_submission_present",
                "needed_artifact": "all 33 R83 production fields filled with matching hashes",
            },
            {
                "blocker_id": "R85-G1-4",
                "priority": 4,
                "target_gate": "downstream_b7_replay_present",
                "needed_artifact": "full downstream B7 replay before any nonzero B7 credit",
            },
        ],
    }
    queue["blocker_queue_hash"] = stable_self_hash(queue, "blocker_queue_hash")
    return queue


def build_payload(args: argparse.Namespace) -> dict[str, Any]:
    root = Path(args.repo_root).resolve()
    r84_result = load_json(root / R84_RESULT)
    priority_packet = load_json(root / R84_PRIORITY_PACKET)
    r83_contract = load_json(root / R83_CONTRACT)
    b7_numeric = load_json(root / B7_NUMERIC_STRUCTURE)

    source_rows = build_source_rows(root, r84_result, priority_packet, b7_numeric)
    write_json(root / R85_SOURCE_ROWS, source_rows)
    mapping = build_candidate_t_mapping(source_rows, priority_packet)
    write_json(root / R85_T_MAPPING, mapping)
    no_double_counting = build_no_double_counting_screen(source_rows)
    write_json(root / R85_NO_DOUBLE_COUNTING, no_double_counting)
    preflight = build_preflight(source_rows, mapping, no_double_counting, priority_packet)
    write_json(root / R85_PREFLIGHT, preflight)
    blocker_queue = build_blocker_queue(preflight)
    write_json(root / R85_BLOCKER_QUEUE, blocker_queue)
    stdout = {
        "artifact": "R85 G1 row-intake stdout",
        "method": METHOD,
        "source_target_id": TARGET_ID,
        "selected_row_count": source_rows["selected_row_count"],
        "candidate_t_ledger_reduction": mapping["candidate_t_ledger_reduction"],
        "preflight_accepted": preflight["accepted"],
        "failed_gate_count": preflight["failed_gate_count"],
        "accepted_b7_credit_delta": 0,
        "source_rows_hash": source_rows["source_rows_hash"],
        "mapping_hash": mapping["mapping_hash"],
    }
    write_json(root / R85_STDOUT, stdout)

    requirements = [
        req(
            "A1",
            "R84 selects G1 as the upstream route",
            r84_result["summary"]["recommended_packet_id"] == "R83-G1-30-arbitrary-rotation-batch"
            and priority_packet["route_id"] == "R83-G1-30-arbitrary-rotation-batch",
            {
                "r84_payload_hash": r84_result["payload_hash"],
                "route_id": priority_packet["route_id"],
            },
        ),
        req(
            "A2",
            "R85 source QASM matches B7 numeric-structure classifier count",
            source_rows["total_arbitrary_numeric_components_by_b7_classifier"] == 270
            and source_rows["b7_reported_arbitrary_numeric_rotations"] == 270,
            {
                "source_qasm": SOURCE_QASM,
                "source_qasm_sha256": source_rows["source_qasm_sha256"],
                "classifier_count": source_rows[
                    "total_arbitrary_numeric_components_by_b7_classifier"
                ],
                "b7_reported_count": source_rows["b7_reported_arbitrary_numeric_rotations"],
            },
        ),
        req(
            "A3",
            "R85 materializes exactly 30 source-backed G1 candidate rows",
            source_rows["selected_row_count"] == 30
            and all(row["source_line_sha256"] for row in source_rows["rows"]),
            {
                "selected_row_count": source_rows["selected_row_count"],
                "source_rows_hash": source_rows["source_rows_hash"],
            },
        ),
        req(
            "A4",
            "R85 candidate mapping reaches the 600-unit G1 target without accepted credit",
            mapping["candidate_t_ledger_reduction"] == 600
            and mapping["accepted_t_ledger_reduction"] == 0,
            {
                "candidate_t_ledger_reduction": mapping["candidate_t_ledger_reduction"],
                "accepted_t_ledger_reduction": mapping["accepted_t_ledger_reduction"],
                "mapping_hash": mapping["mapping_hash"],
            },
        ),
        req(
            "A5",
            "R85 no-double-counting screen has unique selected source components",
            no_double_counting["screen_passed"] is True
            and no_double_counting["unique_source_component_count"] == 30,
            {
                "screen_hash": no_double_counting["screen_hash"],
                "unique_source_component_count": no_double_counting[
                    "unique_source_component_count"
                ],
            },
        ),
        req(
            "A6",
            "R85 preflight rejects credit until replay, STV, R83 fill, and B7 replay exist",
            preflight["accepted"] is False
            and preflight["accepted_b7_credit_delta"] == 0
            and set(preflight["failed_gates"])
            == {
                "replay_stdout_present",
                "stv_reprice_ledger_present",
                "filled_r83_submission_present",
                "downstream_b7_replay_present",
            },
            {
                "preflight_hash": preflight["preflight_hash"],
                "failed_gates": preflight["failed_gates"],
                "accepted_b7_credit_delta": preflight["accepted_b7_credit_delta"],
            },
        ),
        req(
            "A7",
            "R85 preserves claim boundaries and emits next blockers",
            preflight["o3_closed"] is False
            and preflight["reroute_allowed"] is False
            and preflight["resource_saving_claimed"] is False
            and len(blocker_queue["queue"]) == 4,
            {
                "blocker_queue_hash": blocker_queue["blocker_queue_hash"],
                "blocker_ids": [item["blocker_id"] for item in blocker_queue["queue"]],
            },
        ),
    ]
    failed_requirements = [
        requirement["requirement_id"]
        for requirement in requirements
        if not requirement["passed"]
    ]
    validation_errors = []
    if failed_requirements:
        validation_errors.append("one or more R85 requirements failed")
    if preflight["accepted_b7_credit_delta"] != 0:
        validation_errors.append("R85 must not grant B7 credit")
    if r83_contract["minimum_accepted_t_ledger_reduction"] != 591:
        validation_errors.append("R83 contract gap changed unexpectedly")

    payload = {
        "artifact": "B1/B7 cone01 R85 G1 rotation-row intake gate",
        "method": METHOD,
        "version": VERSION,
        "status": STATUS,
        "model_status": MODEL_STATUS,
        "source_target_id": TARGET_ID,
        "upstream_target_id": UPSTREAM_TARGET_ID,
        "generated_at_unix": int(time.time()),
        "source_rows_path": R85_SOURCE_ROWS,
        "source_rows_hash": source_rows["source_rows_hash"],
        "candidate_t_mapping_path": R85_T_MAPPING,
        "candidate_t_mapping_hash": mapping["mapping_hash"],
        "no_double_counting_screen_path": R85_NO_DOUBLE_COUNTING,
        "no_double_counting_screen_hash": no_double_counting["screen_hash"],
        "preflight_path": R85_PREFLIGHT,
        "preflight_hash": preflight["preflight_hash"],
        "blocker_queue_path": R85_BLOCKER_QUEUE,
        "blocker_queue_hash": blocker_queue["blocker_queue_hash"],
        "stdout_path": R85_STDOUT,
        "stdout_sha256": file_hash(root / R85_STDOUT),
        "requirement_count": len(requirements),
        "requirements_passed": sum(1 for requirement in requirements if requirement["passed"]),
        "requirements_failed": len(failed_requirements),
        "failed_requirement_ids": failed_requirements,
        "requirements": requirements,
        "validation_error_count": len(validation_errors),
        "validation_errors": validation_errors,
        "summary": {
            "method": METHOD,
            "status": STATUS,
            "model_status": MODEL_STATUS,
            "source_target_id": TARGET_ID,
            "upstream_target_id": UPSTREAM_TARGET_ID,
            "route_id": priority_packet["route_id"],
            "source_qasm_path": SOURCE_QASM,
            "source_qasm_sha256": source_rows["source_qasm_sha256"],
            "total_arbitrary_numeric_components_by_b7_classifier": source_rows[
                "total_arbitrary_numeric_components_by_b7_classifier"
            ],
            "selected_row_count": source_rows["selected_row_count"],
            "candidate_t_ledger_reduction": mapping["candidate_t_ledger_reduction"],
            "accepted_t_ledger_reduction": mapping["accepted_t_ledger_reduction"],
            "minimum_accepted_t_ledger_reduction": r83_contract[
                "minimum_accepted_t_ledger_reduction"
            ],
            "candidate_after_t_ledger_if_all_rows_accepted": priority_packet[
                "candidate_after_t_ledger_if_accepted"
            ],
            "target_1_20_max_after_t_ledger": priority_packet[
                "target_1_20_max_after_t_ledger"
            ],
            "no_double_counting_screen_passed": no_double_counting["screen_passed"],
            "preflight_accepted": preflight["accepted"],
            "preflight_failed_gate_count": preflight["failed_gate_count"],
            "failed_gates": preflight["failed_gates"],
            "accepted_b7_credit_delta": 0,
            "accepted_b7_space_time_volume_credit": 0,
            "o3_closed": False,
            "reroute_allowed": False,
            "resource_saving_claimed": False,
            "source_rows_hash": source_rows["source_rows_hash"],
            "candidate_t_mapping_hash": mapping["mapping_hash"],
            "no_double_counting_screen_hash": no_double_counting["screen_hash"],
            "preflight_hash": preflight["preflight_hash"],
            "blocker_queue_hash": blocker_queue["blocker_queue_hash"],
            "payload_hash": None,
            "requirements_passed": sum(
                1 for requirement in requirements if requirement["passed"]
            ),
            "requirements_failed": len(failed_requirements),
            "failed_requirement_ids": failed_requirements,
            "validation_error_count": len(validation_errors),
        },
    }
    payload["payload_hash"] = stable_self_hash(payload, "payload_hash")
    payload["summary"]["payload_hash"] = payload["payload_hash"]
    return payload


def write_report(root: Path, payload: dict[str, Any]) -> None:
    summary = payload["summary"]
    lines = [
        "# B1/B7 Cone01 R85 G1 Rotation-Row Intake Gate",
        "",
        f"- Target: `{TARGET_ID}`",
        f"- Upstream target: `{UPSTREAM_TARGET_ID}`",
        f"- Method: `{METHOD}`",
        f"- Status: `{STATUS}`",
        f"- Model status: `{MODEL_STATUS}`",
        "",
        "## Result",
        "",
        "R85 materializes the R84-selected G1 route into a source-backed row intake.",
        "It extracts the first 30 `arbitrary_numeric_rotation` components from the",
        "`gcm_h6` QASM under the same B7 classifier that reports 270 arbitrary",
        "numeric rotations. The selected rows give a candidate `600` T-ledger-unit",
        "mapping, but the preflight still rejects any credit because replay stdout,",
        "STV reprice, a filled R83 submission, and downstream B7 replay are missing.",
        "",
        "## Key Counters",
        "",
        f"- B7 classifier arbitrary components: `{summary['total_arbitrary_numeric_components_by_b7_classifier']}`",
        f"- Selected G1 source rows: `{summary['selected_row_count']}`",
        f"- Candidate T-ledger reduction: `{summary['candidate_t_ledger_reduction']}`",
        f"- Accepted T-ledger reduction: `{summary['accepted_t_ledger_reduction']}`",
        f"- Candidate after T-ledger if all rows accepted: `{summary['candidate_after_t_ledger_if_all_rows_accepted']}`",
        f"- No-double-counting screen passed: `{summary['no_double_counting_screen_passed']}`",
        f"- Preflight accepted: `{summary['preflight_accepted']}`",
        f"- Accepted B7 credit delta: `{summary['accepted_b7_credit_delta']}`",
        "",
        "## Failed Credit Gates",
        "",
    ]
    for gate in summary["failed_gates"]:
        lines.append(f"- `{gate}`")
    lines.extend(["", "## Requirements", ""])
    for requirement in payload["requirements"]:
        status = "PASS" if requirement["passed"] else "FAIL"
        lines.append(f"- `{requirement['requirement_id']}` {status}: {requirement['label']}")
    lines.extend(
        [
            "",
            "## Artifacts",
            "",
            "- Result JSON: `results/B1_B7_cone01_R85_g1_rotation_row_intake_gate_v0.json`",
            f"- Source rows: `{R85_SOURCE_ROWS}`",
            f"- Candidate T mapping: `{R85_T_MAPPING}`",
            f"- No-double-counting screen: `{R85_NO_DOUBLE_COUNTING}`",
            f"- Preflight verdict: `{R85_PREFLIGHT}`",
            f"- Blocker queue: `{R85_BLOCKER_QUEUE}`",
            f"- Stdout: `{R85_STDOUT}`",
            "",
            "## Claim Boundary",
            "",
            "R85 is an intake gate, not a rewrite certificate. It does not prove that",
            "the selected rotations can be removed or repriced, does not provide replay",
            "stdout, does not provide a full STV reprice, does not fill every R83 field,",
            "and does not run downstream B7 replay. B7 credit remains zero.",
            "",
        ]
    )
    report_path = root / "research/B1_B7_cone01_R85_g1_rotation_row_intake_gate.md"
    report_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()
    root = Path(args.repo_root).resolve()
    payload = build_payload(args)
    result_path = root / "results/B1_B7_cone01_R85_g1_rotation_row_intake_gate_v0.json"
    write_json(result_path, payload)
    write_report(root, payload)
    if args.pretty:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(json.dumps(payload, sort_keys=True))


if __name__ == "__main__":
    main()
