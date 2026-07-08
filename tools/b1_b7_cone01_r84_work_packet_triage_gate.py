#!/usr/bin/env python3
"""T-B1-004gh/T-B7-015q: R84 B7 gap-closure work-packet triage gate."""

from __future__ import annotations

import argparse
import hashlib
import json
import time
from pathlib import Path
from typing import Any


METHOD = "b1_b7_cone01_r84_work_packet_triage_gate_v0"
STATUS = "cone01_r84_work_packet_triage_ready_no_credit"
MODEL_STATUS = "r83_gap_closure_packets_ranked_for_next_filled_submission"
VERSION = "0.1"
TARGET_ID = "T-B1-004gh/T-B7-015q"
UPSTREAM_TARGET_ID = "T-B1-004gg/T-B7-015p"
SUBMISSION_DIR = "results/B1_B7_cone01_o3_f4_exit_route_submissions"

R83_RESULT = "results/B1_B7_cone01_R83_b7_gap_closure_contract_gate_v0.json"
R83_CONTRACT = f"{SUBMISSION_DIR}/R83-b7-gap-closure.contract.json"
R83_WORK_PACKETS = f"{SUBMISSION_DIR}/R83-b7-gap-closure-work-packets.json"
R83_TEMPLATE_PREFLIGHT = f"{SUBMISSION_DIR}/R83-b7-gap-closure-template.verdict.json"

R84_TRIAGE = f"{SUBMISSION_DIR}/R84-work-packet-triage.json"
R84_PRIORITY_PACKET = f"{SUBMISSION_DIR}/R84-priority-gap-closure-packet.json"
R84_BLOCKER_QUEUE = f"{SUBMISSION_DIR}/R84-work-packet-triage-blocker-queue.json"
R84_STDOUT = f"{SUBMISSION_DIR}/R84-work-packet-triage.stdout.txt"


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


def score_packet(packet: dict[str, Any], contract: dict[str, Any]) -> dict[str, Any]:
    min_reduction = int(contract["minimum_accepted_t_ledger_reduction"])
    candidate = packet.get("candidate_t_ledger_reduction")
    has_quantified_reduction = isinstance(candidate, int)
    margin = int(candidate) - min_reduction if has_quantified_reduction else None
    evidence_count = len(packet.get("required_evidence", []))
    target = packet.get("target", "")
    packet_id = packet["packet_id"]

    score = 0
    reasons: list[str] = []
    risks: list[str] = []
    failure_modes: list[str] = []

    if has_quantified_reduction:
        score += 40
        reasons.append("candidate T-ledger reduction is already quantified")
        if margin is not None and margin >= 0:
            score += 25
            reasons.append("candidate can close the current 1.20x gap if accepted")
        if margin is not None and margin > 0:
            score += 8
            reasons.append("candidate has positive margin over the 591-unit gap")
        elif margin == 0:
            risks.append("candidate has no slack above the 591-unit threshold")
    else:
        risks.append("candidate reduction is not numerically fixed before reprice")
        failure_modes.append("full reprice may move the bottleneck without producing accepted T-ledger credit")

    score += max(0, 18 - evidence_count)
    if packet.get("can_close_1_20_gap_if_accepted") is True:
        score += 10

    if "30 arbitrary" in target:
        score += 12
        reasons.append("work scope is concrete: exactly 30 arbitrary-rotation removals or reprices")
        failure_modes.extend(
            [
                "rotation rows are not source-backed",
                "logical-T mapping does not preserve the 20-units-per-rotation assumption",
                "STV reprice shows a downstream bottleneck dominates the apparent ledger win",
            ]
        )
    elif "591 source-backed" in target:
        score += 6
        reasons.append("work can be split into source-backed row batches")
        failure_modes.extend(
            [
                "row-level reductions double-count one source window",
                "exact 591-unit threshold leaves no tolerance for rejected rows",
                "machine-check replay transcripts do not bind to the submitted rows",
            ]
        )
    else:
        score -= 8
        reasons.append("full B7 reprice is useful as an audit backstop")
        risks.append("largest blast radius among the three packets")
        failure_modes.extend(
            [
                "same-access assumptions do not match R83",
                "factory/path bottleneck audit invalidates the reprice",
                "independent reproduction cannot recover the claimed 1.20x STV boundary",
            ]
        )

    return {
        "packet_id": packet_id,
        "target": target,
        "source_priority": packet.get("priority"),
        "candidate_t_ledger_reduction": candidate,
        "gap_to_close": min_reduction,
        "margin_over_gap": margin,
        "required_evidence_count": evidence_count,
        "required_evidence": packet.get("required_evidence", []),
        "triage_score": score,
        "triage_reasons": reasons,
        "triage_risks": risks,
        "kill_conditions": failure_modes,
        "claim_boundary": "Triage only. This packet is not accepted B7 credit until R83 gates pass.",
    }


def build_triage(root: Path, r83_result: dict[str, Any], contract: dict[str, Any], packets: dict[str, Any]) -> dict[str, Any]:
    rows = [score_packet(packet, contract) for packet in packets["packets"]]
    rows.sort(
        key=lambda row: (
            -int(row["triage_score"]),
            row["margin_over_gap"] is None,
            -(row["margin_over_gap"] or -10**9),
            int(row["source_priority"] or 99),
        )
    )
    for rank, row in enumerate(rows, start=1):
        row["triage_rank"] = rank
        row["recommended_for_next_pr"] = rank == 1

    triage = {
        "artifact": "R84 B7 gap-closure work-packet triage",
        "method": METHOD,
        "source_target_id": TARGET_ID,
        "upstream_target_id": UPSTREAM_TARGET_ID,
        "source_r83_result_path": R83_RESULT,
        "source_r83_result_sha256": file_hash(root / R83_RESULT),
        "source_r83_payload_hash": r83_result["payload_hash"],
        "source_r83_contract_path": R83_CONTRACT,
        "source_r83_contract_sha256": file_hash(root / R83_CONTRACT),
        "source_r83_contract_hash": contract["contract_hash"],
        "source_r83_work_packets_path": R83_WORK_PACKETS,
        "source_r83_work_packets_sha256": file_hash(root / R83_WORK_PACKETS),
        "source_r83_work_packet_hash": packets["work_packet_hash"],
        "minimum_accepted_t_ledger_reduction": contract["minimum_accepted_t_ledger_reduction"],
        "target_1_20_max_after_t_ledger": contract["target_1_20_max_after_t_ledger"],
        "current_after_t_ledger": contract["current_after_t_ledger"],
        "rows": rows,
        "recommended_packet_id": rows[0]["packet_id"],
        "recommended_packet_target": rows[0]["target"],
        "recommended_packet_candidate_t_ledger_reduction": rows[0]["candidate_t_ledger_reduction"],
        "recommended_packet_margin_over_gap": rows[0]["margin_over_gap"],
        "claim_boundary": (
            "R84 ranks R83 work packets and emits the next intake packet. It grants "
            "no B7 credit, no O3 closure, no reroute permission, and no resource saving."
        ),
    }
    triage["triage_hash"] = stable_self_hash(triage, "triage_hash")
    return triage


def build_priority_packet(contract: dict[str, Any], triage: dict[str, Any]) -> dict[str, Any]:
    selected = triage["rows"][0]
    packet = {
        "artifact": "R84 priority gap-closure packet",
        "method": METHOD,
        "source_target_id": TARGET_ID,
        "upstream_target_id": UPSTREAM_TARGET_ID,
        "route_id": selected["packet_id"],
        "selected_target": selected["target"],
        "contract_id": contract["contract_id"],
        "contract_hash": contract["contract_hash"],
        "minimum_accepted_t_ledger_reduction": contract["minimum_accepted_t_ledger_reduction"],
        "candidate_t_ledger_reduction": selected["candidate_t_ledger_reduction"],
        "candidate_after_t_ledger_if_accepted": contract["current_after_t_ledger"]
        - int(selected["candidate_t_ledger_reduction"]),
        "target_1_20_max_after_t_ledger": contract["target_1_20_max_after_t_ledger"],
        "required_submission_fields": contract["production_required_fields"],
        "required_evidence": selected["required_evidence"],
        "next_pr_acceptance_tests": [
            "fill all 33 R83 production fields",
            "bind 30 source-backed rotation rows or equivalent accepted rows",
            "include replay stdout and matching sha256",
            "include logical-T mapping ledger",
            "include STV reprice ledger",
            "include no-double-counting ledger",
            "keep o3_closed=false until downstream audit",
            "keep reroute_allowed=false until downstream audit",
            "keep resource_saving_claimed=false until downstream audit",
            "request no B7 credit before downstream B7 replay",
        ],
        "kill_conditions": selected["kill_conditions"],
        "claim_boundary": "Priority packet only; it is not a filled R83 submission and grants zero credit.",
        "accepted_b7_credit_delta": 0,
        "accepted_b7_space_time_volume_credit": 0,
        "o3_closed": False,
        "reroute_allowed": False,
        "resource_saving_claimed": False,
    }
    packet["priority_packet_hash"] = stable_self_hash(packet, "priority_packet_hash")
    return packet


def build_blocker_queue(triage: dict[str, Any], priority_packet: dict[str, Any]) -> dict[str, Any]:
    queue = {
        "artifact": "R84 work-packet triage blocker queue",
        "method": METHOD,
        "source_target_id": TARGET_ID,
        "upstream_target_id": UPSTREAM_TARGET_ID,
        "triage_hash": triage["triage_hash"],
        "priority_packet_hash": priority_packet["priority_packet_hash"],
        "queue": [
            {
                "blocker_id": "R84-B7-1",
                "priority": 1,
                "target_gate": "fill_R83_G1_rotation_rows",
                "needed_artifact": "30 source-backed arbitrary-rotation removal/reprice rows",
            },
            {
                "blocker_id": "R84-B7-2",
                "priority": 2,
                "target_gate": "bind_G1_rows_to_logical_T_and_STV",
                "needed_artifact": "logical-T mapping ledger, STV reprice ledger, and no-double-counting ledger",
            },
            {
                "blocker_id": "R84-B7-3",
                "priority": 3,
                "target_gate": "downstream_B7_replay_after_filled_submission",
                "needed_artifact": "rerun B7 gap ledger before any nonzero B7 credit",
            },
        ],
        "accepted_b7_credit_delta": 0,
    }
    queue["blocker_queue_hash"] = stable_self_hash(queue, "blocker_queue_hash")
    return queue


def build_payload(args: argparse.Namespace) -> dict[str, Any]:
    root = Path(args.repo_root).resolve()
    r83_result = load_json(root / R83_RESULT)
    contract = load_json(root / R83_CONTRACT)
    packets = load_json(root / R83_WORK_PACKETS)
    preflight = load_json(root / R83_TEMPLATE_PREFLIGHT)

    triage = build_triage(root, r83_result, contract, packets)
    write_json(root / R84_TRIAGE, triage)
    priority_packet = build_priority_packet(contract, triage)
    write_json(root / R84_PRIORITY_PACKET, priority_packet)
    blocker_queue = build_blocker_queue(triage, priority_packet)
    write_json(root / R84_BLOCKER_QUEUE, blocker_queue)
    stdout = {
        "artifact": "R84 work-packet triage stdout",
        "method": METHOD,
        "source_target_id": TARGET_ID,
        "recommended_packet_id": triage["recommended_packet_id"],
        "recommended_packet_candidate_t_ledger_reduction": triage[
            "recommended_packet_candidate_t_ledger_reduction"
        ],
        "recommended_packet_margin_over_gap": triage["recommended_packet_margin_over_gap"],
        "triage_hash": triage["triage_hash"],
        "priority_packet_hash": priority_packet["priority_packet_hash"],
        "accepted_b7_credit_delta": 0,
    }
    write_json(root / R84_STDOUT, stdout)

    requirements = [
        req(
            "A1",
            "R83 upstream contract is complete and zero-credit",
            r83_result["summary"]["requirements_failed"] == 0
            and r83_result["summary"]["accepted_b7_credit_delta"] == 0
            and r83_result["summary"]["minimum_accepted_t_ledger_reduction"] == 591,
            {
                "r83_result": R83_RESULT,
                "r83_payload_hash": r83_result["payload_hash"],
                "r83_requirements_failed": r83_result["summary"]["requirements_failed"],
            },
        ),
        req(
            "A2",
            "R84 validates R83 contract and work-packet hashes",
            contract["contract_hash"] == r83_result["summary"]["contract_hash"]
            and packets["work_packet_hash"] == r83_result["summary"]["work_packet_hash"],
            {
                "contract_hash": contract["contract_hash"],
                "work_packet_hash": packets["work_packet_hash"],
            },
        ),
        req(
            "A3",
            "R84 ranks all three R83 work packets",
            len(triage["rows"]) == 3
            and {row["packet_id"] for row in triage["rows"]}
            == {
                "R83-G1-30-arbitrary-rotation-batch",
                "R83-G2-591-proxy-t-row-batch",
                "R83-G3-full-b7-reprice",
            },
            {
                "ranked_packet_ids": [row["packet_id"] for row in triage["rows"]],
                "triage_hash": triage["triage_hash"],
            },
        ),
        req(
            "A4",
            "R84 selects the quantified 30-rotation batch as next PR",
            triage["recommended_packet_id"] == "R83-G1-30-arbitrary-rotation-batch"
            and triage["recommended_packet_candidate_t_ledger_reduction"] == 600
            and triage["recommended_packet_margin_over_gap"] == 9,
            {
                "recommended_packet_id": triage["recommended_packet_id"],
                "candidate_t_ledger_reduction": triage[
                    "recommended_packet_candidate_t_ledger_reduction"
                ],
                "margin_over_gap": triage["recommended_packet_margin_over_gap"],
            },
        ),
        req(
            "A5",
            "R84 priority packet preserves all R83 production fields",
            len(priority_packet["required_submission_fields"])
            == len(contract["production_required_fields"])
            == 33,
            {
                "required_submission_field_count": len(
                    priority_packet["required_submission_fields"]
                ),
                "priority_packet_hash": priority_packet["priority_packet_hash"],
            },
        ),
        req(
            "A6",
            "R84 leaves placeholder rejection and claim boundary intact",
            preflight["accepted"] is False
            and priority_packet["accepted_b7_credit_delta"] == 0
            and priority_packet["o3_closed"] is False
            and priority_packet["reroute_allowed"] is False
            and priority_packet["resource_saving_claimed"] is False,
            {
                "template_preflight_accepted": preflight["accepted"],
                "accepted_b7_credit_delta": priority_packet["accepted_b7_credit_delta"],
                "o3_closed": priority_packet["o3_closed"],
                "reroute_allowed": priority_packet["reroute_allowed"],
                "resource_saving_claimed": priority_packet["resource_saving_claimed"],
            },
        ),
        req(
            "A7",
            "R84 emits blockers for filled G1 evidence and downstream replay",
            len(blocker_queue["queue"]) == 3
            and blocker_queue["accepted_b7_credit_delta"] == 0,
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
        validation_errors.append("one or more R84 requirements failed")
    if priority_packet["accepted_b7_credit_delta"] != 0:
        validation_errors.append("R84 must not grant B7 credit")

    payload = {
        "artifact": "B1/B7 cone01 R84 work-packet triage gate",
        "method": METHOD,
        "version": VERSION,
        "status": STATUS,
        "model_status": MODEL_STATUS,
        "source_target_id": TARGET_ID,
        "upstream_target_id": UPSTREAM_TARGET_ID,
        "generated_at_unix": int(time.time()),
        "triage_path": R84_TRIAGE,
        "triage_hash": triage["triage_hash"],
        "priority_packet_path": R84_PRIORITY_PACKET,
        "priority_packet_hash": priority_packet["priority_packet_hash"],
        "blocker_queue_path": R84_BLOCKER_QUEUE,
        "blocker_queue_hash": blocker_queue["blocker_queue_hash"],
        "stdout_path": R84_STDOUT,
        "stdout_sha256": file_hash(root / R84_STDOUT),
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
            "source_r83_payload_hash": r83_result["payload_hash"],
            "source_r83_contract_hash": contract["contract_hash"],
            "source_r83_work_packet_hash": packets["work_packet_hash"],
            "ranked_work_packet_count": len(triage["rows"]),
            "recommended_packet_id": triage["recommended_packet_id"],
            "recommended_packet_candidate_t_ledger_reduction": triage[
                "recommended_packet_candidate_t_ledger_reduction"
            ],
            "recommended_packet_margin_over_gap": triage[
                "recommended_packet_margin_over_gap"
            ],
            "minimum_accepted_t_ledger_reduction": contract[
                "minimum_accepted_t_ledger_reduction"
            ],
            "candidate_after_t_ledger_if_accepted": priority_packet[
                "candidate_after_t_ledger_if_accepted"
            ],
            "target_1_20_max_after_t_ledger": contract["target_1_20_max_after_t_ledger"],
            "production_required_field_count": len(contract["production_required_fields"]),
            "template_preflight_accepted": preflight["accepted"],
            "accepted_b7_credit_delta": 0,
            "accepted_b7_space_time_volume_credit": 0,
            "o3_closed": False,
            "reroute_allowed": False,
            "resource_saving_claimed": False,
            "triage_hash": triage["triage_hash"],
            "priority_packet_hash": priority_packet["priority_packet_hash"],
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
        "# B1/B7 Cone01 R84 Work-Packet Triage Gate",
        "",
        f"- Target: `{TARGET_ID}`",
        f"- Upstream target: `{UPSTREAM_TARGET_ID}`",
        f"- Method: `{METHOD}`",
        f"- Status: `{STATUS}`",
        f"- Model status: `{MODEL_STATUS}`",
        "",
        "## Result",
        "",
        "R84 ranks the three R83 B7 gap-closure work packets and emits the next",
        "priority intake packet. The recommended next PR is",
        "`R83-G1-30-arbitrary-rotation-batch`: remove or reprice 30 source-backed",
        "arbitrary numeric rotations. If accepted under the R83 contract, the packet",
        "would supply `600` candidate T-ledger units against the `591` unit 1.20x",
        "gap, giving `9` units of margin before downstream B7 replay.",
        "",
        "## Key Counters",
        "",
        f"- Ranked work packets: `{summary['ranked_work_packet_count']}`",
        f"- Recommended packet: `{summary['recommended_packet_id']}`",
        f"- Candidate T-ledger reduction: `{summary['recommended_packet_candidate_t_ledger_reduction']}`",
        f"- Margin over current 1.20x gap: `{summary['recommended_packet_margin_over_gap']}`",
        f"- Candidate after T-ledger if accepted: `{summary['candidate_after_t_ledger_if_accepted']}`",
        f"- R83 production fields preserved: `{summary['production_required_field_count']}`",
        f"- Accepted B7 credit delta: `{summary['accepted_b7_credit_delta']}`",
        "",
        "## Ranked Packets",
        "",
    ]
    triage = load_json(root / R84_TRIAGE)
    for row in triage["rows"]:
        lines.extend(
            [
                f"- Rank `{row['triage_rank']}`: `{row['packet_id']}`",
                f"  - score: `{row['triage_score']}`",
                f"  - candidate T-ledger reduction: `{row['candidate_t_ledger_reduction']}`",
                f"  - margin over gap: `{row['margin_over_gap']}`",
                f"  - required evidence count: `{row['required_evidence_count']}`",
            ]
        )
    lines.extend(
        [
            "",
            "## Requirements",
            "",
        ]
    )
    for requirement in payload["requirements"]:
        status = "PASS" if requirement["passed"] else "FAIL"
        lines.append(f"- `{requirement['requirement_id']}` {status}: {requirement['label']}")
    lines.extend(
        [
            "",
            "## Artifacts",
            "",
            f"- Result JSON: `results/B1_B7_cone01_R84_work_packet_triage_gate_v0.json`",
            f"- Triage ledger: `{R84_TRIAGE}`",
            f"- Priority packet: `{R84_PRIORITY_PACKET}`",
            f"- Blocker queue: `{R84_BLOCKER_QUEUE}`",
            f"- Stdout: `{R84_STDOUT}`",
            "",
            "## Claim Boundary",
            "",
            "R84 is a triage and intake-routing gate. It does not fill the R83",
            "submission, does not close O3, does not allow reroute, does not claim",
            "resource saving, and does not grant B7 dependency, resource, FT-ledger,",
            "STV, or credit. A future R85-style submission must provide the actual",
            "source-backed rotation rows and pass the R83 gates before downstream",
            "B7 replay can even be attempted.",
            "",
        ]
    )
    report_path = root / "research/B1_B7_cone01_R84_work_packet_triage_gate.md"
    report_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()
    root = Path(args.repo_root).resolve()
    payload = build_payload(args)
    result_path = root / "results/B1_B7_cone01_R84_work_packet_triage_gate_v0.json"
    write_json(result_path, payload)
    write_report(root, payload)
    if args.pretty:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(json.dumps(payload, sort_keys=True))


if __name__ == "__main__":
    main()
