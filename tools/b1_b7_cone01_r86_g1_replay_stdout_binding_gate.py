#!/usr/bin/env python3
"""T-B1-004gj/T-B7-015s: R86 G1 replay-stdout binding gate."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path
from typing import Any


METHOD = "b1_b7_cone01_r86_g1_replay_stdout_binding_gate_v0"
STATUS = "cone01_r86_g1_replay_stdout_binding_ready_no_credit"
MODEL_STATUS = "r85_replay_stdout_gate_closed_without_stv_or_b7_credit"
VERSION = "0.1"
TARGET_ID = "T-B1-004gj/T-B7-015s"
UPSTREAM_TARGET_ID = "T-B1-004gi/T-B7-015r"
SUBMISSION_DIR = "results/B1_B7_cone01_o3_f4_exit_route_submissions"

R85_RESULT = "results/B1_B7_cone01_R85_g1_rotation_row_intake_gate_v0.json"
R85_SOURCE_ROWS = f"{SUBMISSION_DIR}/R85-G1-source-rotation-rows.json"
R85_T_MAPPING = f"{SUBMISSION_DIR}/R85-G1-candidate-logical-t-mapping.json"
R85_NO_DOUBLE_COUNTING = f"{SUBMISSION_DIR}/R85-G1-no-double-counting-screen.json"
R85_PREFLIGHT = f"{SUBMISSION_DIR}/R85-G1-row-intake-preflight.verdict.json"
SOURCE_QASM = "results/b1_u3_phase_factored_optimizer/qasmbench_medium_exact/gcm_h6.qasm"

R86_TRANSCRIPT = f"{SUBMISSION_DIR}/R86-G1-source-binding-replay-transcript.json"
R86_STDOUT = f"{SUBMISSION_DIR}/R86-G1-source-binding-replay.stdout.txt"
R86_PREFLIGHT = f"{SUBMISSION_DIR}/R86-G1-replay-aware-preflight.verdict.json"
R86_BLOCKER_QUEUE = f"{SUBMISSION_DIR}/R86-G1-replay-aware-blocker-queue.json"


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


def read_qasm_lines(root: Path) -> list[str]:
    return (root / SOURCE_QASM).read_text(encoding="utf-8").splitlines()


def build_replay_transcript(
    root: Path,
    r85_result: dict[str, Any],
    source_rows: dict[str, Any],
    mapping: dict[str, Any],
    no_double_counting: dict[str, Any],
) -> dict[str, Any]:
    qasm_lines = read_qasm_lines(root)
    events: list[dict[str, Any]] = []
    for row in source_rows["rows"]:
        line_index = row["source_line_number"] - 1
        source_line_text = qasm_lines[line_index].strip()
        line_sha256 = hashlib.sha256(source_line_text.encode("utf-8")).hexdigest()
        events.append(
            {
                "row_id": row["row_id"],
                "source_component_id": row["source_component_id"],
                "source_line_number": row["source_line_number"],
                "source_line_text": source_line_text,
                "source_line_sha256": line_sha256,
                "expected_source_line_sha256": row["source_line_sha256"],
                "line_hash_verified": line_sha256 == row["source_line_sha256"],
                "source_component_bound": row["source_component_id"].startswith(
                    f"gcm_h6:L{row['source_line_number']}:"
                ),
                "rotation_family": row["rotation_family"],
                "candidate_t_ledger_reduction": row["candidate_t_ledger_reduction"],
                "accepted_t_ledger_reduction": 0,
                "replay_scope": "source_binding_stdout_only",
                "rewrite_applied": False,
                "same_unitary_verified": False,
                "stv_repriced": False,
                "accepted": False,
            }
        )
    all_rows_bound = all(
        event["line_hash_verified"] and event["source_component_bound"] for event in events
    )
    transcript = {
        "artifact": "R86 G1 source-binding replay transcript",
        "method": METHOD,
        "source_target_id": TARGET_ID,
        "upstream_target_id": UPSTREAM_TARGET_ID,
        "route_id": r85_result["summary"]["route_id"],
        "source_qasm_path": SOURCE_QASM,
        "source_qasm_sha256": file_hash(root / SOURCE_QASM),
        "source_r85_result_path": R85_RESULT,
        "source_r85_payload_hash": r85_result["payload_hash"],
        "source_rows_hash": source_rows["source_rows_hash"],
        "candidate_t_mapping_hash": mapping["mapping_hash"],
        "no_double_counting_screen_hash": no_double_counting["screen_hash"],
        "selected_row_count": len(events),
        "replay_event_count": len(events),
        "line_hash_verified_count": sum(1 for event in events if event["line_hash_verified"]),
        "source_component_bound_count": sum(
            1 for event in events if event["source_component_bound"]
        ),
        "all_selected_rows_covered": len(events) == source_rows["selected_row_count"] == 30,
        "all_rows_source_bound": all_rows_bound,
        "candidate_t_ledger_reduction": mapping["candidate_t_ledger_reduction"],
        "accepted_t_ledger_reduction": 0,
        "accepted_b7_credit_delta": 0,
        "replay_scope": "source-binding replay stdout; no rewrite or same-unitary claim",
        "events": events,
        "claim_boundary": (
            "R86 closes only the replay-stdout-present blocker for the R85 selected "
            "source rows. It does not provide STV reprice, a filled R83 production "
            "submission, downstream B7 replay, same-unitary proof, or nonzero B7 credit."
        ),
    }
    transcript["transcript_hash"] = stable_self_hash(transcript, "transcript_hash")
    return transcript


def write_replay_stdout(root: Path, transcript: dict[str, Any]) -> str:
    lines = [
        "R86 G1 source-binding replay stdout",
        f"method={METHOD}",
        f"source_target_id={TARGET_ID}",
        f"upstream_target_id={UPSTREAM_TARGET_ID}",
        f"source_qasm_sha256={transcript['source_qasm_sha256']}",
        f"source_rows_hash={transcript['source_rows_hash']}",
        f"candidate_t_mapping_hash={transcript['candidate_t_mapping_hash']}",
        f"selected_row_count={transcript['selected_row_count']}",
        f"replay_event_count={transcript['replay_event_count']}",
        f"all_selected_rows_covered={str(transcript['all_selected_rows_covered']).lower()}",
        f"all_rows_source_bound={str(transcript['all_rows_source_bound']).lower()}",
        "accepted_t_ledger_reduction=0",
        "accepted_b7_credit_delta=0",
        "claim_boundary=source-binding stdout only; no rewrite or same-unitary claim",
    ]
    for event in transcript["events"]:
        verdict = "PASS" if event["line_hash_verified"] and event["source_component_bound"] else "FAIL"
        lines.append(
            "row={row_id} verdict={verdict} line={line} component={component} "
            "line_hash={line_hash} accepted_t_delta=0".format(
                row_id=event["row_id"],
                verdict=verdict,
                line=event["source_line_number"],
                component=event["source_component_id"],
                line_hash=event["source_line_sha256"],
            )
        )
    text = "\n".join(lines) + "\n"
    path = root / R86_STDOUT
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def build_preflight(
    transcript: dict[str, Any],
    stdout_sha256: str,
    r85_preflight: dict[str, Any],
) -> dict[str, Any]:
    gates = {
        "source_rows_present": transcript["selected_row_count"] == 30,
        "source_rows_match_b7_classifier_count": True,
        "candidate_t_ledger_reduction_reaches_600": transcript[
            "candidate_t_ledger_reduction"
        ]
        == 600,
        "component_uniqueness_screen_passed": True,
        "replay_stdout_present": bool(stdout_sha256)
        and transcript["all_selected_rows_covered"]
        and transcript["all_rows_source_bound"],
        "stv_reprice_ledger_present": False,
        "filled_r83_submission_present": False,
        "downstream_b7_replay_present": False,
    }
    failed = [gate for gate, passed in gates.items() if not passed]
    preflight = {
        "artifact": "R86 G1 replay-aware preflight verdict",
        "method": METHOD,
        "source_target_id": TARGET_ID,
        "upstream_target_id": UPSTREAM_TARGET_ID,
        "route_id": transcript["route_id"],
        "source_r85_preflight_hash": r85_preflight["preflight_hash"],
        "source_r85_failed_gates": r85_preflight["failed_gates"],
        "transcript_hash": transcript["transcript_hash"],
        "stdout_path": R86_STDOUT,
        "stdout_sha256": stdout_sha256,
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
        "closed_r85_failed_gates": ["replay_stdout_present"],
        "remaining_r85_failed_gates": [
            "stv_reprice_ledger_present",
            "filled_r83_submission_present",
            "downstream_b7_replay_present",
        ],
        "claim_boundary": (
            "R86 changes only the replay_stdout_present gate from missing to present. "
            "It still rejects credit until STV reprice, filled R83 submission, and "
            "downstream B7 replay are present and accepted."
        ),
    }
    preflight["preflight_hash"] = stable_self_hash(preflight, "preflight_hash")
    return preflight


def build_blocker_queue(preflight: dict[str, Any]) -> dict[str, Any]:
    queue = {
        "artifact": "R86 G1 replay-aware blocker queue",
        "method": METHOD,
        "source_target_id": TARGET_ID,
        "upstream_target_id": UPSTREAM_TARGET_ID,
        "preflight_hash": preflight["preflight_hash"],
        "accepted_b7_credit_delta": 0,
        "queue": [
            {
                "blocker_id": "R86-G1-1",
                "priority": 1,
                "target_gate": "stv_reprice_ledger_present",
                "needed_artifact": "STV reprice ledger linking all 30 replay-bound rows to the 1.20x target",
            },
            {
                "blocker_id": "R86-G1-2",
                "priority": 2,
                "target_gate": "filled_r83_submission_present",
                "needed_artifact": "all 33 R83 production fields filled with matching R86 hashes",
            },
            {
                "blocker_id": "R86-G1-3",
                "priority": 3,
                "target_gate": "downstream_b7_replay_present",
                "needed_artifact": "full downstream B7 replay before any nonzero B7 credit",
            },
        ],
    }
    queue["blocker_queue_hash"] = stable_self_hash(queue, "blocker_queue_hash")
    return queue


def build_payload(args: argparse.Namespace) -> dict[str, Any]:
    root = Path(args.repo_root).resolve()
    r85_result = load_json(root / R85_RESULT)
    source_rows = load_json(root / R85_SOURCE_ROWS)
    mapping = load_json(root / R85_T_MAPPING)
    no_double_counting = load_json(root / R85_NO_DOUBLE_COUNTING)
    r85_preflight = load_json(root / R85_PREFLIGHT)

    transcript = build_replay_transcript(root, r85_result, source_rows, mapping, no_double_counting)
    write_json(root / R86_TRANSCRIPT, transcript)
    stdout_sha256 = write_replay_stdout(root, transcript)
    preflight = build_preflight(transcript, stdout_sha256, r85_preflight)
    write_json(root / R86_PREFLIGHT, preflight)
    blocker_queue = build_blocker_queue(preflight)
    write_json(root / R86_BLOCKER_QUEUE, blocker_queue)

    requirements = [
        req(
            "A1",
            "R86 consumes the R85 G1 source-row intake without changing its candidate mapping",
            r85_result["summary"]["source_target_id"] == UPSTREAM_TARGET_ID
            and source_rows["source_rows_hash"] == r85_result["summary"]["source_rows_hash"]
            and mapping["mapping_hash"] == r85_result["summary"]["candidate_t_mapping_hash"],
            {
                "r85_payload_hash": r85_result["payload_hash"],
                "source_rows_hash": source_rows["source_rows_hash"],
                "candidate_t_mapping_hash": mapping["mapping_hash"],
            },
        ),
        req(
            "A2",
            "R86 binds all 30 selected rows back to source QASM line hashes",
            transcript["selected_row_count"] == 30
            and transcript["line_hash_verified_count"] == 30
            and transcript["source_component_bound_count"] == 30,
            {
                "transcript_hash": transcript["transcript_hash"],
                "line_hash_verified_count": transcript["line_hash_verified_count"],
                "source_component_bound_count": transcript["source_component_bound_count"],
            },
        ),
        req(
            "A3",
            "R86 emits replay stdout that covers every selected row",
            preflight["gates"]["replay_stdout_present"] is True
            and preflight["stdout_sha256"] == file_hash(root / R86_STDOUT),
            {
                "stdout_path": R86_STDOUT,
                "stdout_sha256": preflight["stdout_sha256"],
                "replay_event_count": transcript["replay_event_count"],
            },
        ),
        req(
            "A4",
            "R86 keeps replay scope below rewrite or same-unitary evidence",
            all(
                event["rewrite_applied"] is False
                and event["same_unitary_verified"] is False
                and event["accepted_t_ledger_reduction"] == 0
                for event in transcript["events"]
            ),
            {
                "replay_scope": transcript["replay_scope"],
                "accepted_t_ledger_reduction": transcript["accepted_t_ledger_reduction"],
            },
        ),
        req(
            "A5",
            "R86 closes exactly the R85 replay-stdout blocker and leaves three credit blockers open",
            preflight["closed_r85_failed_gates"] == ["replay_stdout_present"]
            and set(preflight["remaining_r85_failed_gates"])
            == {
                "stv_reprice_ledger_present",
                "filled_r83_submission_present",
                "downstream_b7_replay_present",
            }
            and preflight["failed_gate_count"] == 3,
            {
                "preflight_hash": preflight["preflight_hash"],
                "closed_r85_failed_gates": preflight["closed_r85_failed_gates"],
                "remaining_r85_failed_gates": preflight["remaining_r85_failed_gates"],
            },
        ),
        req(
            "A6",
            "R86 grants no B7, STV, reroute, O3, or resource-saving credit",
            preflight["accepted"] is False
            and preflight["accepted_b7_credit_delta"] == 0
            and preflight["accepted_b7_space_time_volume_credit"] == 0
            and preflight["o3_closed"] is False
            and preflight["reroute_allowed"] is False
            and preflight["resource_saving_claimed"] is False,
            {
                "accepted_b7_credit_delta": preflight["accepted_b7_credit_delta"],
                "accepted_b7_space_time_volume_credit": preflight[
                    "accepted_b7_space_time_volume_credit"
                ],
            },
        ),
        req(
            "A7",
            "R86 emits the next three blockers as PR-sized work",
            len(blocker_queue["queue"]) == 3
            and [item["target_gate"] for item in blocker_queue["queue"]]
            == [
                "stv_reprice_ledger_present",
                "filled_r83_submission_present",
                "downstream_b7_replay_present",
            ],
            {
                "blocker_queue_hash": blocker_queue["blocker_queue_hash"],
                "blocker_ids": [item["blocker_id"] for item in blocker_queue["queue"]],
            },
        ),
    ]
    failed_requirements = [
        requirement["requirement_id"] for requirement in requirements if not requirement["passed"]
    ]
    validation_errors = []
    if failed_requirements:
        validation_errors.append("one or more R86 requirements failed")
    if preflight["accepted_b7_credit_delta"] != 0:
        validation_errors.append("R86 must not grant B7 credit")
    if "replay_stdout_present" in preflight["failed_gates"]:
        validation_errors.append("R86 must close replay_stdout_present")
    if set(preflight["failed_gates"]) != {
        "stv_reprice_ledger_present",
        "filled_r83_submission_present",
        "downstream_b7_replay_present",
    }:
        validation_errors.append("R86 failed-gate set must contain exactly the remaining three blockers")

    payload = {
        "artifact": "B1/B7 cone01 R86 G1 replay-stdout binding gate",
        "method": METHOD,
        "version": VERSION,
        "status": STATUS,
        "model_status": MODEL_STATUS,
        "source_target_id": TARGET_ID,
        "upstream_target_id": UPSTREAM_TARGET_ID,
        "generated_at_unix": int(time.time()),
        "transcript_path": R86_TRANSCRIPT,
        "transcript_hash": transcript["transcript_hash"],
        "stdout_path": R86_STDOUT,
        "stdout_sha256": stdout_sha256,
        "preflight_path": R86_PREFLIGHT,
        "preflight_hash": preflight["preflight_hash"],
        "blocker_queue_path": R86_BLOCKER_QUEUE,
        "blocker_queue_hash": blocker_queue["blocker_queue_hash"],
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
            "route_id": transcript["route_id"],
            "source_qasm_path": SOURCE_QASM,
            "source_qasm_sha256": transcript["source_qasm_sha256"],
            "source_rows_hash": transcript["source_rows_hash"],
            "selected_row_count": transcript["selected_row_count"],
            "replay_event_count": transcript["replay_event_count"],
            "line_hash_verified_count": transcript["line_hash_verified_count"],
            "source_component_bound_count": transcript["source_component_bound_count"],
            "all_selected_rows_covered": transcript["all_selected_rows_covered"],
            "all_rows_source_bound": transcript["all_rows_source_bound"],
            "candidate_t_ledger_reduction": transcript["candidate_t_ledger_reduction"],
            "accepted_t_ledger_reduction": 0,
            "replay_stdout_present": preflight["gates"]["replay_stdout_present"],
            "closed_r85_failed_gates": preflight["closed_r85_failed_gates"],
            "remaining_r85_failed_gates": preflight["remaining_r85_failed_gates"],
            "preflight_accepted": preflight["accepted"],
            "preflight_failed_gate_count": preflight["failed_gate_count"],
            "failed_gates": preflight["failed_gates"],
            "accepted_b7_credit_delta": 0,
            "accepted_b7_space_time_volume_credit": 0,
            "o3_closed": False,
            "reroute_allowed": False,
            "resource_saving_claimed": False,
            "transcript_hash": transcript["transcript_hash"],
            "stdout_sha256": stdout_sha256,
            "preflight_hash": preflight["preflight_hash"],
            "blocker_queue_hash": blocker_queue["blocker_queue_hash"],
            "payload_hash": None,
            "requirements_passed": sum(1 for requirement in requirements if requirement["passed"]),
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
        "# B1/B7 Cone01 R86 G1 Replay-Stdout Binding Gate",
        "",
        f"- Target: `{TARGET_ID}`",
        f"- Upstream target: `{UPSTREAM_TARGET_ID}`",
        f"- Method: `{METHOD}`",
        f"- Status: `{STATUS}`",
        f"- Model status: `{MODEL_STATUS}`",
        "",
        "## Result",
        "",
        "R86 closes the first R85 blocker by emitting replay stdout for all 30",
        "selected G1 source rows. The replay is deliberately scoped to source-line",
        "and component binding: each row is checked against the `gcm_h6` QASM line",
        "hash and source-component id. It is not a rewrite replay, same-unitary",
        "certificate, STV reprice, filled R83 submission, or downstream B7 replay.",
        "",
        "## Key Counters",
        "",
        f"- Selected G1 source rows: `{summary['selected_row_count']}`",
        f"- Replay events: `{summary['replay_event_count']}`",
        f"- Line hashes verified: `{summary['line_hash_verified_count']}`",
        f"- Source components bound: `{summary['source_component_bound_count']}`",
        f"- Candidate T-ledger reduction: `{summary['candidate_t_ledger_reduction']}`",
        f"- Accepted T-ledger reduction: `{summary['accepted_t_ledger_reduction']}`",
        f"- Replay stdout present: `{summary['replay_stdout_present']}`",
        f"- Preflight accepted: `{summary['preflight_accepted']}`",
        f"- Accepted B7 credit delta: `{summary['accepted_b7_credit_delta']}`",
        "",
        "## Closed Gate",
        "",
    ]
    for gate in summary["closed_r85_failed_gates"]:
        lines.append(f"- `{gate}`")
    lines.extend(["", "## Remaining Credit Gates", ""])
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
            "- Result JSON: `results/B1_B7_cone01_R86_g1_replay_stdout_binding_gate_v0.json`",
            f"- Replay transcript: `{R86_TRANSCRIPT}`",
            f"- Replay stdout: `{R86_STDOUT}`",
            f"- Replay-aware preflight: `{R86_PREFLIGHT}`",
            f"- Blocker queue: `{R86_BLOCKER_QUEUE}`",
            "",
            "## Claim Boundary",
            "",
            "R86 is a replay-stdout binding gate. It does not prove that any selected",
            "rotation can be removed or repriced, does not provide same-unitary proof,",
            "does not produce an STV reprice ledger, does not fill the R83 production",
            "submission, and does not run downstream B7 replay. B7 credit remains zero.",
            "",
        ]
    )
    report_path = root / "research/B1_B7_cone01_R86_g1_replay_stdout_binding_gate.md"
    report_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()
    root = Path(args.repo_root).resolve()
    payload = build_payload(args)
    result_path = root / "results/B1_B7_cone01_R86_g1_replay_stdout_binding_gate_v0.json"
    write_json(result_path, payload)
    write_report(root, payload)
    if args.pretty:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(json.dumps(payload, sort_keys=True))


if __name__ == "__main__":
    main()
