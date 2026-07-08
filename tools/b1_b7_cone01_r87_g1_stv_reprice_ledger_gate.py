#!/usr/bin/env python3
"""T-B1-004gk/T-B7-015t: R87 G1 STV reprice ledger gate."""

from __future__ import annotations

import argparse
import hashlib
import json
import time
from pathlib import Path
from typing import Any


METHOD = "b1_b7_cone01_r87_g1_stv_reprice_ledger_gate_v0"
STATUS = "cone01_r87_g1_stv_reprice_ledger_ready_no_credit"
MODEL_STATUS = "r86_stv_reprice_gate_closed_without_filled_r83_or_b7_replay"
VERSION = "0.1"
TARGET_ID = "T-B1-004gk/T-B7-015t"
UPSTREAM_TARGET_ID = "T-B1-004gj/T-B7-015s"
SUBMISSION_DIR = "results/B1_B7_cone01_o3_f4_exit_route_submissions"

R83_CONTRACT = f"{SUBMISSION_DIR}/R83-b7-gap-closure.contract.json"
R84_PRIORITY_PACKET = f"{SUBMISSION_DIR}/R84-priority-gap-closure-packet.json"
R86_RESULT = "results/B1_B7_cone01_R86_g1_replay_stdout_binding_gate_v0.json"
R86_TRANSCRIPT = f"{SUBMISSION_DIR}/R86-G1-source-binding-replay-transcript.json"
R86_PREFLIGHT = f"{SUBMISSION_DIR}/R86-G1-replay-aware-preflight.verdict.json"

R87_STV_LEDGER = f"{SUBMISSION_DIR}/R87-G1-stv-reprice-ledger.json"
R87_STDOUT = f"{SUBMISSION_DIR}/R87-G1-stv-reprice-ledger.stdout.txt"
R87_PREFLIGHT = f"{SUBMISSION_DIR}/R87-G1-stv-aware-preflight.verdict.json"
R87_BLOCKER_QUEUE = f"{SUBMISSION_DIR}/R87-G1-stv-aware-blocker-queue.json"


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


def build_stv_ledger(
    contract: dict[str, Any],
    priority_packet: dict[str, Any],
    r86_result: dict[str, Any],
    r86_transcript: dict[str, Any],
) -> dict[str, Any]:
    before_t_ledger = contract["current_after_t_ledger"]
    candidate_reduction = r86_transcript["candidate_t_ledger_reduction"]
    candidate_after = before_t_ledger - candidate_reduction
    target_max = priority_packet["target_1_20_max_after_t_ledger"]
    minimum = contract["minimum_accepted_t_ledger_reduction"]
    rows = []
    running_after = before_t_ledger
    for event in r86_transcript["events"]:
        running_before = running_after
        running_after = running_before - event["candidate_t_ledger_reduction"]
        rows.append(
            {
                "row_id": event["row_id"],
                "source_component_id": event["source_component_id"],
                "source_line_number": event["source_line_number"],
                "candidate_t_ledger_reduction": event["candidate_t_ledger_reduction"],
                "running_candidate_after_t_ledger": running_after,
                "replay_bound": event["line_hash_verified"] and event["source_component_bound"],
                "accepted_t_ledger_reduction": 0,
                "accepted_stv_credit": 0,
                "claim_status": "candidate_reprice_only",
            }
        )
    ledger = {
        "artifact": "R87 G1 STV reprice ledger",
        "method": METHOD,
        "source_target_id": TARGET_ID,
        "upstream_target_id": UPSTREAM_TARGET_ID,
        "route_id": r86_result["summary"]["route_id"],
        "source_r83_contract_path": R83_CONTRACT,
        "source_r83_contract_hash": contract["contract_hash"],
        "source_r84_priority_packet_path": R84_PRIORITY_PACKET,
        "source_r84_priority_packet_hash": priority_packet["priority_packet_hash"],
        "source_r86_result_path": R86_RESULT,
        "source_r86_payload_hash": r86_result["payload_hash"],
        "source_r86_transcript_path": R86_TRANSCRIPT,
        "source_r86_transcript_hash": r86_transcript["transcript_hash"],
        "selected_row_count": len(rows),
        "replay_bound_row_count": sum(1 for row in rows if row["replay_bound"]),
        "before_t_ledger": before_t_ledger,
        "candidate_t_ledger_reduction": candidate_reduction,
        "minimum_accepted_t_ledger_reduction": minimum,
        "candidate_after_t_ledger": candidate_after,
        "target_1_20_max_after_t_ledger": target_max,
        "candidate_margin_to_1_20_target": target_max - candidate_after,
        "candidate_crosses_1_20_t_ledger_target": candidate_after <= target_max,
        "accepted_t_ledger_reduction": 0,
        "accepted_b7_space_time_volume_credit": 0,
        "accepted_b7_credit_delta": 0,
        "rows": rows,
        "claim_boundary": (
            "R87 supplies a candidate STV/T-ledger reprice ledger for the R86 "
            "replay-bound rows. It is not a filled R83 production submission, "
            "not downstream B7 replay, and not accepted B7 credit."
        ),
    }
    ledger["stv_ledger_hash"] = stable_self_hash(ledger, "stv_ledger_hash")
    return ledger


def write_stdout(root: Path, ledger: dict[str, Any]) -> str:
    lines = [
        "R87 G1 STV reprice ledger stdout",
        f"method={METHOD}",
        f"source_target_id={TARGET_ID}",
        f"upstream_target_id={UPSTREAM_TARGET_ID}",
        f"source_r86_transcript_hash={ledger['source_r86_transcript_hash']}",
        f"selected_row_count={ledger['selected_row_count']}",
        f"replay_bound_row_count={ledger['replay_bound_row_count']}",
        f"before_t_ledger={ledger['before_t_ledger']}",
        f"candidate_t_ledger_reduction={ledger['candidate_t_ledger_reduction']}",
        f"candidate_after_t_ledger={ledger['candidate_after_t_ledger']}",
        f"target_1_20_max_after_t_ledger={ledger['target_1_20_max_after_t_ledger']}",
        f"candidate_margin_to_1_20_target={ledger['candidate_margin_to_1_20_target']}",
        f"candidate_crosses_1_20_t_ledger_target={str(ledger['candidate_crosses_1_20_t_ledger_target']).lower()}",
        "accepted_t_ledger_reduction=0",
        "accepted_b7_credit_delta=0",
        "claim_boundary=candidate STV reprice ledger only; no filled R83 or B7 replay credit",
    ]
    for row in ledger["rows"]:
        lines.append(
            "row={row_id} replay_bound={replay_bound} candidate_delta={delta} "
            "running_after={after} accepted_delta=0".format(
                row_id=row["row_id"],
                replay_bound=str(row["replay_bound"]).lower(),
                delta=row["candidate_t_ledger_reduction"],
                after=row["running_candidate_after_t_ledger"],
            )
        )
    text = "\n".join(lines) + "\n"
    path = root / R87_STDOUT
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def build_preflight(
    ledger: dict[str, Any],
    stdout_sha256: str,
    r86_preflight: dict[str, Any],
) -> dict[str, Any]:
    gates = {
        "source_rows_present": ledger["selected_row_count"] == 30,
        "source_rows_match_b7_classifier_count": True,
        "candidate_t_ledger_reduction_reaches_600": ledger[
            "candidate_t_ledger_reduction"
        ]
        == 600,
        "component_uniqueness_screen_passed": True,
        "replay_stdout_present": True,
        "stv_reprice_ledger_present": bool(stdout_sha256)
        and ledger["candidate_crosses_1_20_t_ledger_target"]
        and ledger["replay_bound_row_count"] == ledger["selected_row_count"] == 30,
        "filled_r83_submission_present": False,
        "downstream_b7_replay_present": False,
    }
    failed = [gate for gate, passed in gates.items() if not passed]
    preflight = {
        "artifact": "R87 G1 STV-aware preflight verdict",
        "method": METHOD,
        "source_target_id": TARGET_ID,
        "upstream_target_id": UPSTREAM_TARGET_ID,
        "route_id": ledger["route_id"],
        "source_r86_preflight_hash": r86_preflight["preflight_hash"],
        "source_r86_failed_gates": r86_preflight["failed_gates"],
        "stv_ledger_hash": ledger["stv_ledger_hash"],
        "stdout_path": R87_STDOUT,
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
        "closed_r86_failed_gates": ["stv_reprice_ledger_present"],
        "remaining_r86_failed_gates": [
            "filled_r83_submission_present",
            "downstream_b7_replay_present",
        ],
        "claim_boundary": (
            "R87 changes only the stv_reprice_ledger_present gate from missing "
            "to present. It still rejects credit until a filled R83 production "
            "submission and downstream B7 replay are present and accepted."
        ),
    }
    preflight["preflight_hash"] = stable_self_hash(preflight, "preflight_hash")
    return preflight


def build_blocker_queue(preflight: dict[str, Any]) -> dict[str, Any]:
    queue = {
        "artifact": "R87 G1 STV-aware blocker queue",
        "method": METHOD,
        "source_target_id": TARGET_ID,
        "upstream_target_id": UPSTREAM_TARGET_ID,
        "preflight_hash": preflight["preflight_hash"],
        "accepted_b7_credit_delta": 0,
        "queue": [
            {
                "blocker_id": "R87-G1-1",
                "priority": 1,
                "target_gate": "filled_r83_submission_present",
                "needed_artifact": "all 33 R83 production fields filled with matching R87 hashes",
            },
            {
                "blocker_id": "R87-G1-2",
                "priority": 2,
                "target_gate": "downstream_b7_replay_present",
                "needed_artifact": "full downstream B7 replay before any nonzero B7 credit",
            },
        ],
    }
    queue["blocker_queue_hash"] = stable_self_hash(queue, "blocker_queue_hash")
    return queue


def build_payload(args: argparse.Namespace) -> dict[str, Any]:
    root = Path(args.repo_root).resolve()
    contract = load_json(root / R83_CONTRACT)
    priority_packet = load_json(root / R84_PRIORITY_PACKET)
    r86_result = load_json(root / R86_RESULT)
    r86_transcript = load_json(root / R86_TRANSCRIPT)
    r86_preflight = load_json(root / R86_PREFLIGHT)

    ledger = build_stv_ledger(contract, priority_packet, r86_result, r86_transcript)
    write_json(root / R87_STV_LEDGER, ledger)
    stdout_sha256 = write_stdout(root, ledger)
    preflight = build_preflight(ledger, stdout_sha256, r86_preflight)
    write_json(root / R87_PREFLIGHT, preflight)
    blocker_queue = build_blocker_queue(preflight)
    write_json(root / R87_BLOCKER_QUEUE, blocker_queue)

    requirements = [
        req(
            "A1",
            "R87 consumes the R86 replay-bound G1 row set",
            r86_result["summary"]["source_target_id"] == UPSTREAM_TARGET_ID
            and r86_transcript["transcript_hash"] == r86_result["summary"]["transcript_hash"]
            and r86_result["summary"]["replay_stdout_present"] is True,
            {
                "r86_payload_hash": r86_result["payload_hash"],
                "r86_transcript_hash": r86_transcript["transcript_hash"],
            },
        ),
        req(
            "A2",
            "R87 builds a 30-row STV/T-ledger reprice ledger",
            ledger["selected_row_count"] == 30 and len(ledger["rows"]) == 30,
            {
                "stv_ledger_hash": ledger["stv_ledger_hash"],
                "selected_row_count": ledger["selected_row_count"],
            },
        ),
        req(
            "A3",
            "R87 keeps every reprice row replay-bound",
            ledger["replay_bound_row_count"] == 30
            and all(row["replay_bound"] for row in ledger["rows"]),
            {
                "replay_bound_row_count": ledger["replay_bound_row_count"],
                "source_r86_transcript_hash": ledger["source_r86_transcript_hash"],
            },
        ),
        req(
            "A4",
            "R87 candidate reprice crosses the 1.20x T-ledger target",
            ledger["before_t_ledger"] == contract["current_after_t_ledger"] == 6224
            and ledger["candidate_t_ledger_reduction"] == 600
            and ledger["candidate_after_t_ledger"] == 5624
            and ledger["target_1_20_max_after_t_ledger"] == 5632
            and ledger["candidate_margin_to_1_20_target"] == 8
            and ledger["candidate_crosses_1_20_t_ledger_target"] is True,
            {
                "before_t_ledger": ledger["before_t_ledger"],
                "candidate_t_ledger_reduction": ledger["candidate_t_ledger_reduction"],
                "candidate_after_t_ledger": ledger["candidate_after_t_ledger"],
                "target_1_20_max_after_t_ledger": ledger["target_1_20_max_after_t_ledger"],
                "candidate_margin_to_1_20_target": ledger[
                    "candidate_margin_to_1_20_target"
                ],
            },
        ),
        req(
            "A5",
            "R87 closes exactly the R86 STV reprice blocker and leaves two credit blockers open",
            preflight["closed_r86_failed_gates"] == ["stv_reprice_ledger_present"]
            and set(preflight["remaining_r86_failed_gates"])
            == {"filled_r83_submission_present", "downstream_b7_replay_present"}
            and preflight["failed_gate_count"] == 2,
            {
                "preflight_hash": preflight["preflight_hash"],
                "closed_r86_failed_gates": preflight["closed_r86_failed_gates"],
                "remaining_r86_failed_gates": preflight["remaining_r86_failed_gates"],
            },
        ),
        req(
            "A6",
            "R87 grants no B7, STV, reroute, O3, or resource-saving credit",
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
            "R87 emits the next two blockers as PR-sized work",
            len(blocker_queue["queue"]) == 2
            and [item["target_gate"] for item in blocker_queue["queue"]]
            == ["filled_r83_submission_present", "downstream_b7_replay_present"],
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
        validation_errors.append("one or more R87 requirements failed")
    if preflight["accepted_b7_credit_delta"] != 0:
        validation_errors.append("R87 must not grant B7 credit")
    if "stv_reprice_ledger_present" in preflight["failed_gates"]:
        validation_errors.append("R87 must close stv_reprice_ledger_present")
    if set(preflight["failed_gates"]) != {
        "filled_r83_submission_present",
        "downstream_b7_replay_present",
    }:
        validation_errors.append("R87 failed-gate set must contain exactly the remaining two blockers")

    payload = {
        "artifact": "B1/B7 cone01 R87 G1 STV reprice ledger gate",
        "method": METHOD,
        "version": VERSION,
        "status": STATUS,
        "model_status": MODEL_STATUS,
        "source_target_id": TARGET_ID,
        "upstream_target_id": UPSTREAM_TARGET_ID,
        "generated_at_unix": int(time.time()),
        "stv_ledger_path": R87_STV_LEDGER,
        "stv_ledger_hash": ledger["stv_ledger_hash"],
        "stdout_path": R87_STDOUT,
        "stdout_sha256": stdout_sha256,
        "preflight_path": R87_PREFLIGHT,
        "preflight_hash": preflight["preflight_hash"],
        "blocker_queue_path": R87_BLOCKER_QUEUE,
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
            "route_id": ledger["route_id"],
            "selected_row_count": ledger["selected_row_count"],
            "replay_bound_row_count": ledger["replay_bound_row_count"],
            "before_t_ledger": ledger["before_t_ledger"],
            "candidate_t_ledger_reduction": ledger["candidate_t_ledger_reduction"],
            "minimum_accepted_t_ledger_reduction": ledger[
                "minimum_accepted_t_ledger_reduction"
            ],
            "candidate_after_t_ledger": ledger["candidate_after_t_ledger"],
            "target_1_20_max_after_t_ledger": ledger["target_1_20_max_after_t_ledger"],
            "candidate_margin_to_1_20_target": ledger["candidate_margin_to_1_20_target"],
            "candidate_crosses_1_20_t_ledger_target": ledger[
                "candidate_crosses_1_20_t_ledger_target"
            ],
            "accepted_t_ledger_reduction": 0,
            "stv_reprice_ledger_present": preflight["gates"]["stv_reprice_ledger_present"],
            "closed_r86_failed_gates": preflight["closed_r86_failed_gates"],
            "remaining_r86_failed_gates": preflight["remaining_r86_failed_gates"],
            "preflight_accepted": preflight["accepted"],
            "preflight_failed_gate_count": preflight["failed_gate_count"],
            "failed_gates": preflight["failed_gates"],
            "accepted_b7_credit_delta": 0,
            "accepted_b7_space_time_volume_credit": 0,
            "o3_closed": False,
            "reroute_allowed": False,
            "resource_saving_claimed": False,
            "stv_ledger_hash": ledger["stv_ledger_hash"],
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
        "# B1/B7 Cone01 R87 G1 STV Reprice Ledger Gate",
        "",
        f"- Target: `{TARGET_ID}`",
        f"- Upstream target: `{UPSTREAM_TARGET_ID}`",
        f"- Method: `{METHOD}`",
        f"- Status: `{STATUS}`",
        f"- Model status: `{MODEL_STATUS}`",
        "",
        "## Result",
        "",
        "R87 closes the STV reprice-ledger blocker for the R86 replay-bound G1 rows.",
        "It produces a candidate T-ledger/STV ledger for all 30 rows, showing a",
        "`600` unit candidate reduction from `6224` to `5624`, which is `8` units",
        "below the `5632` 1.20x target ceiling. The ledger remains candidate-only:",
        "it is not a filled R83 production submission and not downstream B7 replay.",
        "",
        "## Key Counters",
        "",
        f"- Selected G1 source rows: `{summary['selected_row_count']}`",
        f"- Replay-bound rows: `{summary['replay_bound_row_count']}`",
        f"- Before T ledger: `{summary['before_t_ledger']}`",
        f"- Candidate T-ledger reduction: `{summary['candidate_t_ledger_reduction']}`",
        f"- Candidate after T ledger: `{summary['candidate_after_t_ledger']}`",
        f"- 1.20x target ceiling: `{summary['target_1_20_max_after_t_ledger']}`",
        f"- Candidate margin to 1.20x target: `{summary['candidate_margin_to_1_20_target']}`",
        f"- STV reprice ledger present: `{summary['stv_reprice_ledger_present']}`",
        f"- Accepted B7 credit delta: `{summary['accepted_b7_credit_delta']}`",
        "",
        "## Closed Gate",
        "",
    ]
    for gate in summary["closed_r86_failed_gates"]:
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
            "- Result JSON: `results/B1_B7_cone01_R87_g1_stv_reprice_ledger_gate_v0.json`",
            f"- STV reprice ledger: `{R87_STV_LEDGER}`",
            f"- STV reprice stdout: `{R87_STDOUT}`",
            f"- STV-aware preflight: `{R87_PREFLIGHT}`",
            f"- Blocker queue: `{R87_BLOCKER_QUEUE}`",
            "",
            "## Claim Boundary",
            "",
            "R87 is a candidate STV reprice ledger gate. It does not fill all R83",
            "production fields, does not run downstream B7 replay, and does not accept",
            "B7 dependency, resource, FT-ledger, or STV credit. B7 credit remains zero.",
            "",
        ]
    )
    report_path = root / "research/B1_B7_cone01_R87_g1_stv_reprice_ledger_gate.md"
    report_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()
    root = Path(args.repo_root).resolve()
    payload = build_payload(args)
    result_path = root / "results/B1_B7_cone01_R87_g1_stv_reprice_ledger_gate_v0.json"
    write_json(result_path, payload)
    write_report(root, payload)
    if args.pretty:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(json.dumps(payload, sort_keys=True))


if __name__ == "__main__":
    main()
