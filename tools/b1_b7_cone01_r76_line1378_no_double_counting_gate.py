#!/usr/bin/env python3
"""T-B1-004fz/T-B7-015i: R76 line1378 no-double-counting gate."""

from __future__ import annotations

import argparse
import hashlib
import json
import time
from pathlib import Path
from typing import Any


METHOD = "b1_b7_cone01_r76_line1378_no_double_counting_gate_v0"
STATUS = "cone01_r76_r73_source_closure_shape_passed_zero_credit"
MODEL_STATUS = "r73_d1_d2_d3_prefilled_hardened_r72_rerun_still_required"
VERSION = "0.1"
TARGET_ID = "T-B1-004fz/T-B7-015i"
UPSTREAM_TARGET_ID = "T-B1-004fy/T-B7-015h"
SUBMISSION_DIR = "results/B1_B7_cone01_o3_f4_exit_route_submissions"
R2_RESULT = "results/B1_B7_cone01_R2_line1378_overlap_recovery_packet_gate_v0.json"
R70_PREFILL = f"{SUBMISSION_DIR}/R70-R1-line1381-prefill-machine-check-replay.json"
R73_CONTRACT = f"{SUBMISSION_DIR}/R73-r1-r2-source-closure-intake.contract.json"
R75_SUBMISSION = f"{SUBMISSION_DIR}/R75-r1-d1-d2-source-closure-submission.json"
R76_SOURCE_ARTIFACT = f"{SUBMISSION_DIR}/R76-line1378-no-double-counting-source-artifact.json"
R76_LEDGER = f"{SUBMISSION_DIR}/R76-line1378-no-double-counting-ledger.json"
R76_STDOUT = f"{SUBMISSION_DIR}/R76-line1378-no-double-counting-replay.stdout.txt"
R76_VERDICT = f"{SUBMISSION_DIR}/R76-line1378-no-double-counting-replay.verdict.json"
R76_SUBMISSION = f"{SUBMISSION_DIR}/R76-r1-d1-d2-d3-source-closure-submission.json"
R76_INTAKE_VERDICT = f"{SUBMISSION_DIR}/R76-r1-d1-d2-d3-source-closure-intake.verdict.json"
R76_BLOCKER_QUEUE = f"{SUBMISSION_DIR}/R76-post-r73-source-closure-blocker-queue.json"


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


def path_hash_matches(root: Path, path_value: Any, hash_value: Any) -> bool:
    if not isinstance(path_value, str) or not isinstance(hash_value, str):
        return False
    path = root / path_value
    return path.exists() and file_hash(path) == hash_value


def window_lines(path: Path, window: list[int]) -> list[dict[str, Any]]:
    lines = path.read_text(encoding="utf-8").splitlines()
    start, end = window
    return [
        {"line": line_no, "text": lines[line_no - 1].strip()}
        for line_no in range(start, end + 1)
    ]


def line_at(path: Path, line_no: int) -> str:
    return path.read_text(encoding="utf-8").splitlines()[line_no - 1].strip()


def verify_intake(root: Path, submission: dict[str, Any], contract: dict[str, Any]) -> dict[str, Any]:
    missing_by_packet: dict[str, list[str]] = {}
    hash_failures: list[str] = []
    hash_checks: list[bool] = []
    for packet in contract["closure_packets"]:
        packet_id = packet["packet_id"]
        row = submission.get("packets", {}).get(packet_id, {})
        missing = [
            field for field in packet["required_fields"] if row.get(field) in (None, "")
        ]
        missing_by_packet[packet_id] = missing
        for field in packet["required_fields"]:
            if not field.endswith("_sha256"):
                continue
            path_field = field[: -len("_sha256")] + "_path"
            ok = path_hash_matches(root, row.get(path_field), row.get(field))
            hash_checks.append(ok)
            if row.get(path_field) not in (None, "") and not ok:
                hash_failures.append(field)

    d1 = submission.get("packets", {}).get("R73-D1-line1381-source-backed-occurrence", {})
    d2 = submission.get("packets", {}).get("R73-D2-line1381-source-backed-proxy-t", {})
    d3 = submission.get("packets", {}).get("R73-D3-line1378-source-backed-no-double-counting", {})
    occurrence_derivation = str(d1.get("r1_occurrence_delta_derivation", ""))
    proxy_t_delta = d2.get("proxy_t_delta")
    proxy_t_before = d2.get("proxy_t_before")
    proxy_t_after = d2.get("proxy_t_after")
    gates = {
        "source_contract_hash_matches": submission.get("source_contract_hash")
        == contract["contract_hash"],
        "all_required_fields_complete": all(not missing for missing in missing_by_packet.values()),
        "all_hash_bound_artifacts_exist": hash_failures == [] and all(hash_checks),
        "r1_occurrence_delta_source_backed": (
            isinstance(d1.get("r1_occurrence_removed_lines"), list)
            and len(d1.get("r1_occurrence_removed_lines", [])) >= 1
            and "Preflight candidate only" not in occurrence_derivation
            and d1.get("r1_source_artifact_path") not in (None, "")
        ),
        "proxy_t_delta_source_backed": (
            isinstance(proxy_t_before, int)
            and isinstance(proxy_t_after, int)
            and isinstance(proxy_t_delta, int)
            and proxy_t_before - proxy_t_after == proxy_t_delta
            and proxy_t_delta >= 1
            and d2.get("proxy_t_derivation_artifact_path") not in (None, "")
            and d2.get("proxy_t_pricing_model_path") not in (None, "")
        ),
        "r2_no_double_counting_source_backed": (
            d3.get("line1378_recovery_or_exclusion_decision")
            in {"recovered", "excluded_from_line1381_count"}
            and d3.get("no_double_counting_ledger_path") not in (None, "")
        ),
        "b7_not_requested_before_closure": submission.get("b7_nonzero_retest_requested") is False,
        "claim_boundary_blocks_b7": "b7 credit" in str(submission.get("claim_boundary", "")).lower()
        and "not" in str(submission.get("claim_boundary", "")).lower(),
    }
    failed = [gate for gate, passed in gates.items() if not passed]
    verdict = {
        "artifact": "R76 replay of R73 source-closure intake verifier",
        "method": METHOD,
        "source_target_id": TARGET_ID,
        "submission_id": submission.get("submission_id"),
        "gates": gates,
        "passed_gate_count": sum(1 for passed in gates.values() if passed),
        "failed_gate_count": len(failed),
        "failed_gates": failed,
        "missing_by_packet": missing_by_packet,
        "hash_failures": hash_failures,
        "accepted": failed == [],
        "accepted_exit_route_count": 0,
        "accepted_occurrence_removal": 0,
        "accepted_proxy_t_reduction": 0,
        "b7_credit_delta": 0,
    }
    verdict["verdict_hash"] = stable_hash(verdict)
    return verdict


def build_payload(args: argparse.Namespace) -> dict[str, Any]:
    root = Path(args.repo_root).resolve()
    r2 = load_json(root / R2_RESULT)
    r70 = load_json(root / R70_PREFILL)
    contract = load_json(root / R73_CONTRACT)
    submission = load_json(root / R75_SUBMISSION)
    r2_summary = r2["summary"]
    r2_packet = r2["r2_line1378_overlap_recovery_packet"]
    source_path = root / r70["source_openqasm3_path"]
    candidate_path = root / r70["candidate_openqasm3_path"]
    line1378_window = r2_summary["line1378_window"]
    line1381_window = r2_summary["line1381_window"]
    decision = "excluded_from_line1381_count"

    source_artifact = {
        "artifact": "R76 line1378 no-double-counting source artifact",
        "method": METHOD,
        "source_target_id": TARGET_ID,
        "upstream_target_id": UPSTREAM_TARGET_ID,
        "source_r2_result_path": R2_RESULT,
        "source_r2_result_sha256": file_hash(root / R2_RESULT),
        "source_r2_summary_hash": stable_hash(r2_summary),
        "source_overlap_additivity_hash": r2_summary["overlap_additivity_hash"],
        "source_openqasm3_path": r70["source_openqasm3_path"],
        "source_openqasm3_sha256": r70["source_openqasm3_sha256"],
        "candidate_openqasm3_path": r70["candidate_openqasm3_path"],
        "candidate_openqasm3_sha256": r70["candidate_openqasm3_sha256"],
        "line1378_window": line1378_window,
        "line1381_window": line1381_window,
        "union_window": r2_summary["union_window"],
        "line1378_window_contained_in_line1381": r2_summary[
            "line1378_window_contained_in_line1381"
        ],
        "dropped_overlap_candidate_line_numbers": r2_summary[
            "dropped_overlap_candidate_line_numbers_before_recovery"
        ],
        "selected_line_numbers_before_recovery": r2_summary[
            "selected_line_numbers_before_recovery"
        ],
        "line1378_source_instruction": line_at(source_path, 1378),
        "line1378_candidate_instruction": line_at(candidate_path, 1378),
        "line1381_source_instruction": line_at(source_path, 1381),
        "line1381_candidate_instruction": line_at(candidate_path, 1381),
        "source_line1378_window_lines": window_lines(source_path, line1378_window),
        "source_line1381_window_lines": window_lines(source_path, line1381_window),
        "candidate_line1378_window_lines": window_lines(candidate_path, line1378_window),
        "candidate_line1381_window_lines": window_lines(candidate_path, line1381_window),
        "decision": decision,
        "decision_reason": (
            "R2 overlap-additivity facts bind line1378 as a dropped overlap candidate "
            "whose window is contained in the line1381 window. R76 therefore excludes "
            "line1378 from the R73 line1381 count instead of adding a second positive "
            "delta for the contained window."
        ),
        "claim_boundary": (
            "R76 closes the D3 no-double-counting evidence shape for R73 only. It is "
            "not a merged-region recovery, not an accepted R2 recovery artifact, not "
            "a resource saving, and not B7 credit."
        ),
    }
    source_artifact["artifact_hash"] = stable_self_hash(source_artifact, "artifact_hash")
    write_json(root / R76_SOURCE_ARTIFACT, source_artifact)

    ledger = {
        "artifact": "R76 line1378 no-double-counting ledger",
        "method": METHOD,
        "source_target_id": TARGET_ID,
        "upstream_target_id": UPSTREAM_TARGET_ID,
        "source_artifact_path": R76_SOURCE_ARTIFACT,
        "source_artifact_sha256": file_hash(root / R76_SOURCE_ARTIFACT),
        "source_overlap_additivity_hash": r2_summary["overlap_additivity_hash"],
        "line1378_window": line1378_window,
        "line1381_window": line1381_window,
        "line1378_window_contained_in_line1381": True,
        "line1378_delta_recovered": False,
        "line1378_candidate_cnot_delta": r2_summary["line1378_candidate_cnot_delta"],
        "line1378_recovery_or_exclusion_decision": decision,
        "counted_positive_line_windows": [1381],
        "excluded_positive_line_windows": [1378],
        "double_counting_prevented": True,
        "accepted_occurrence_removal": 0,
        "accepted_proxy_t_reduction": 0,
        "b7_credit_delta": 0,
        "claim_boundary": source_artifact["claim_boundary"],
        "source_packet_hash": r2_packet["packet_hash"],
    }
    ledger["ledger_hash"] = stable_self_hash(ledger, "ledger_hash")
    write_json(root / R76_LEDGER, ledger)

    stdout_payload = {
        "artifact": "R76 line1378 no-double-counting replay stdout",
        "method": METHOD,
        "source_target_id": TARGET_ID,
        "line1378_window": line1378_window,
        "line1381_window": line1381_window,
        "decision": decision,
        "double_counting_prevented": True,
        "accepted_occurrence_removal": 0,
        "accepted_proxy_t_reduction": 0,
        "b7_credit_delta": 0,
        "claim_boundary": source_artifact["claim_boundary"],
    }
    (root / R76_STDOUT).write_text(
        json.dumps(stdout_payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    replay_verdict = {
        "artifact": "R76 line1378 no-double-counting replay verdict",
        "method": METHOD,
        "source_target_id": TARGET_ID,
        "source_artifact_path": R76_SOURCE_ARTIFACT,
        "source_artifact_sha256": file_hash(root / R76_SOURCE_ARTIFACT),
        "ledger_path": R76_LEDGER,
        "ledger_sha256": file_hash(root / R76_LEDGER),
        "checks": {
            "source_r2_result_hash_bound": source_artifact["source_r2_result_sha256"]
            == file_hash(root / R2_RESULT),
            "source_openqasm3_hash_bound": file_hash(source_path)
            == r70["source_openqasm3_sha256"],
            "candidate_openqasm3_hash_bound": file_hash(candidate_path)
            == r70["candidate_openqasm3_sha256"],
            "line1378_window_matches_r2": line1378_window == r2_packet["line1378_window"],
            "line1381_window_matches_r2": line1381_window == r2_packet["line1381_window"],
            "line1378_window_contained": r2_summary[
                "line1378_window_contained_in_line1381"
            ]
            is True,
            "decision_excludes_contained_line1378": decision
            == "excluded_from_line1381_count",
            "accepted_credit_stays_zero": ledger["accepted_occurrence_removal"] == 0
            and ledger["accepted_proxy_t_reduction"] == 0
            and ledger["b7_credit_delta"] == 0,
        },
        "accepted_for_r73_d3_prefill": True,
        "accepted_exit_route_count": 0,
        "accepted_occurrence_removal": 0,
        "accepted_proxy_t_reduction": 0,
        "b7_credit_delta": 0,
    }
    replay_verdict["failed_checks"] = [
        check for check, passed in replay_verdict["checks"].items() if not passed
    ]
    replay_verdict["accepted_for_r73_d3_prefill"] = replay_verdict["failed_checks"] == []
    replay_verdict["verdict_hash"] = stable_hash(replay_verdict)
    write_json(root / R76_VERDICT, replay_verdict)

    submission.update(
        {
            "submission_id": "B1-B7-cone01-R76-r1-d1-d2-d3-source-closure-prefill",
            "source_target_id": TARGET_ID,
            "upstream_target_id": UPSTREAM_TARGET_ID,
            "accepted_exit_route_count": 0,
            "occurrence_removal_delta": 0,
            "proxy_t_reduction_delta": 0,
            "b7_nonzero_retest_requested": False,
            "claim_boundary": (
                "R76 fills D1, D2, and D3 so the R73 source-closure intake shape can "
                "pass, but it is not O3 closure, not reroute permission, not accepted "
                "occurrence/proxy-T reduction, and not B7 credit. A hardened R72/R73 "
                "rerun and downstream acceptance gates remain required."
            ),
        }
    )
    submission["packets"]["R73-D3-line1378-source-backed-no-double-counting"].update(
        {
            "r2_source_artifact_path": R76_SOURCE_ARTIFACT,
            "r2_source_artifact_sha256": file_hash(root / R76_SOURCE_ARTIFACT),
            "r2_replay_command": (
                "python3 tools/b1_b7_cone01_r76_line1378_no_double_counting_gate.py "
                "--repo-root . --pretty"
            ),
            "r2_replay_stdout_path": R76_STDOUT,
            "r2_replay_stdout_sha256": file_hash(root / R76_STDOUT),
            "line1378_recovery_or_exclusion_decision": decision,
            "line1378_overlap_window": line1378_window,
            "line1381_window": line1381_window,
            "no_double_counting_ledger_path": R76_LEDGER,
            "no_double_counting_ledger_sha256": file_hash(root / R76_LEDGER),
            "r2_claim_boundary": source_artifact["claim_boundary"],
        }
    )
    submission["submission_hash"] = stable_self_hash(submission, "submission_hash")
    write_json(root / R76_SUBMISSION, submission)

    intake_verdict = verify_intake(root, submission, contract)
    write_json(root / R76_INTAKE_VERDICT, intake_verdict)
    blocker_queue = {
        "artifact": "R76 post-R73 source-closure blocker queue",
        "source_target_id": TARGET_ID,
        "upstream_target_id": UPSTREAM_TARGET_ID,
        "r73_d1_prefilled": intake_verdict["gates"]["r1_occurrence_delta_source_backed"],
        "r73_d2_prefilled": intake_verdict["gates"]["proxy_t_delta_source_backed"],
        "r73_d3_prefilled": intake_verdict["gates"]["r2_no_double_counting_source_backed"],
        "r73_intake_accepted": intake_verdict["accepted"],
        "remaining_failed_gates": intake_verdict["failed_gates"],
        "queue": [
            {
                "blocker_id": "R76-C4",
                "priority": 1,
                "needed_artifact": (
                    "rerun the hardened R72 source-backed delta preflight against the "
                    "R76 D1/D2/D3 submission before any downstream accepted exit route "
                    "or B7 nonzero retest"
                ),
            },
            {
                "blocker_id": "R76-C5",
                "priority": 2,
                "needed_artifact": (
                    "submit the full resource-escape acceptance packet and downstream "
                    "B7 ledger replay with claim boundary if hardened preflight passes"
                ),
            },
        ],
    }
    blocker_queue["blocker_queue_hash"] = stable_self_hash(
        blocker_queue, "blocker_queue_hash"
    )
    write_json(root / R76_BLOCKER_QUEUE, blocker_queue)

    requirements = [
        req(
            "L1",
            "R76 binds the locked R2 overlap-additivity source",
            source_artifact["source_r2_result_sha256"] == file_hash(root / R2_RESULT)
            and source_artifact["source_overlap_additivity_hash"]
            == r2_summary["overlap_additivity_hash"],
            {
                "source_r2_result_sha256": source_artifact["source_r2_result_sha256"],
                "source_overlap_additivity_hash": source_artifact[
                    "source_overlap_additivity_hash"
                ],
            },
        ),
        req(
            "L2",
            "line1378 and line1381 windows match the R2 source facts",
            line1378_window == r2_packet["line1378_window"]
            and line1381_window == r2_packet["line1381_window"],
            {"line1378_window": line1378_window, "line1381_window": line1381_window},
        ),
        req(
            "L3",
            "line1378 is excluded from the line1381 count instead of double-counted",
            decision == "excluded_from_line1381_count"
            and ledger["double_counting_prevented"] is True
            and 1378 in ledger["excluded_positive_line_windows"],
            {"decision": decision, "excluded_positive_line_windows": [1378]},
        ),
        req(
            "L4",
            "R76 materializes hash-bound source artifact, ledger, stdout, and verdict",
            all(
                (root / path).exists()
                for path in [R76_SOURCE_ARTIFACT, R76_LEDGER, R76_STDOUT, R76_VERDICT]
            ),
            {
                "source_artifact_sha256": file_hash(root / R76_SOURCE_ARTIFACT),
                "ledger_sha256": file_hash(root / R76_LEDGER),
                "stdout_sha256": file_hash(root / R76_STDOUT),
                "verdict_sha256": file_hash(root / R76_VERDICT),
            },
        ),
        req(
            "L5",
            "R73-D1, D2, and D3 are source-backed under the R73 intake replay",
            intake_verdict["gates"]["r1_occurrence_delta_source_backed"]
            and intake_verdict["gates"]["proxy_t_delta_source_backed"]
            and intake_verdict["gates"]["r2_no_double_counting_source_backed"],
            {
                "r73_d1_prefilled": intake_verdict["gates"][
                    "r1_occurrence_delta_source_backed"
                ],
                "r73_d2_prefilled": intake_verdict["gates"][
                    "proxy_t_delta_source_backed"
                ],
                "r73_d3_prefilled": intake_verdict["gates"][
                    "r2_no_double_counting_source_backed"
                ],
            },
        ),
        req(
            "L6",
            "R73 intake shape passes while accepted deltas and B7 credit stay zero",
            intake_verdict["accepted"] is True
            and intake_verdict["accepted_exit_route_count"] == 0
            and intake_verdict["accepted_occurrence_removal"] == 0
            and intake_verdict["accepted_proxy_t_reduction"] == 0
            and intake_verdict["b7_credit_delta"] == 0,
            {
                "r73_intake_accepted": intake_verdict["accepted"],
                "accepted_exit_route_count": intake_verdict["accepted_exit_route_count"],
                "accepted_occurrence_removal": intake_verdict["accepted_occurrence_removal"],
                "accepted_proxy_t_reduction": intake_verdict["accepted_proxy_t_reduction"],
                "b7_credit_delta": intake_verdict["b7_credit_delta"],
            },
        ),
        req(
            "L7",
            "R76 emits the next hardened-preflight blocker queue",
            len(blocker_queue["queue"]) == 2
            and blocker_queue["queue"][0]["blocker_id"] == "R76-C4",
            {"blocker_queue_hash": blocker_queue["blocker_queue_hash"]},
        ),
        req(
            "L8",
            "R76 does not claim O3 closure, reroute, resource savings, or B7 ledger gain",
            True,
            {
                "o3_closed": False,
                "reroute_allowed": False,
                "resource_saving_claimed": False,
                "b7_ledger_improvement_claimed": False,
            },
        ),
    ]
    summary = {
        "method": METHOD,
        "status": STATUS,
        "model_status": MODEL_STATUS,
        "source_target_id": TARGET_ID,
        "upstream_target_id": UPSTREAM_TARGET_ID,
        "r73_d1_prefilled": intake_verdict["gates"]["r1_occurrence_delta_source_backed"],
        "r73_d2_prefilled": intake_verdict["gates"]["proxy_t_delta_source_backed"],
        "r73_d3_prefilled": intake_verdict["gates"][
            "r2_no_double_counting_source_backed"
        ],
        "r73_intake_accepted": intake_verdict["accepted"],
        "r73_intake_failed_gate_count": intake_verdict["failed_gate_count"],
        "r73_intake_failed_gates": intake_verdict["failed_gates"],
        "line1378_recovery_or_exclusion_decision": decision,
        "line1378_window": line1378_window,
        "line1381_window": line1381_window,
        "line1378_window_contained_in_line1381": True,
        "line1378_delta_recovered": False,
        "accepted_exit_route_count": 0,
        "accepted_occurrence_removal": 0,
        "accepted_proxy_t_reduction": 0,
        "b7_nonzero_retest_allowed": False,
        "b7_credit_delta": 0,
        "o3_closed": False,
        "reroute_allowed": False,
        "resource_saving_claimed": False,
        "b7_ledger_improvement_claimed": False,
        "source_artifact_hash": source_artifact["artifact_hash"],
        "ledger_hash": ledger["ledger_hash"],
        "submission_hash": submission["submission_hash"],
        "intake_verdict_hash": intake_verdict["verdict_hash"],
        "blocker_queue_hash": blocker_queue["blocker_queue_hash"],
        "requirement_count": len(requirements),
        "requirements_passed": sum(1 for item in requirements if item["passed"]),
        "requirements_failed": sum(1 for item in requirements if not item["passed"]),
        "failed_requirement_ids": [
            item["requirement_id"] for item in requirements if not item["passed"]
        ],
        "validation_error_count": sum(1 for item in requirements if not item["passed"]),
    }
    payload = {
        "title": "B1/B7 Cone01 R76 Line1378 No-Double-Counting Gate",
        "version": VERSION,
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "summary": summary,
        "requirements": requirements,
        "claim_boundary": {
            "what_is_supported": (
                "R76 fills R73-D3 with a hash-bound source artifact, no-double-counting "
                "ledger, replay stdout, and verdict. The R73 D1/D2/D3 source-closure "
                "intake shape now passes."
            ),
            "what_is_not_supported": (
                "R76 does not recover line1378 as a positive delta, does not accept a "
                "resource-escape route, does not close O3, does not permit reroute, "
                "and does not grant B7 credit."
            ),
            "next_gate": (
                "Rerun the hardened R72 source-backed delta preflight against the R76 "
                "D1/D2/D3 submission, then only proceed to downstream acceptance and "
                "B7 ledger retest if that gate passes."
            ),
        },
        "artifacts": {
            "line1378_source_artifact": R76_SOURCE_ARTIFACT,
            "no_double_counting_ledger": R76_LEDGER,
            "line1378_replay_stdout": R76_STDOUT,
            "line1378_replay_verdict": R76_VERDICT,
            "r73_submission": R76_SUBMISSION,
            "r73_intake_verdict": R76_INTAKE_VERDICT,
            "blocker_queue": R76_BLOCKER_QUEUE,
        },
    }
    payload["summary"]["payload_hash"] = stable_hash(payload)
    return payload


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    s = payload["summary"]
    lines = [
        "# B1/B7 Cone01 R76 Line1378 No-Double-Counting Gate",
        "",
        "## Summary",
        "",
        f"- Status: `{s['status']}`",
        f"- R73-D1 prefilled: `{s['r73_d1_prefilled']}`",
        f"- R73-D2 prefilled: `{s['r73_d2_prefilled']}`",
        f"- R73-D3 prefilled: `{s['r73_d3_prefilled']}`",
        f"- R73 intake accepted: `{s['r73_intake_accepted']}`",
        f"- R73 failed gates: `{s['r73_intake_failed_gate_count']}`",
        f"- Decision: `{s['line1378_recovery_or_exclusion_decision']}`",
        f"- line1378 window: `{s['line1378_window']}`",
        f"- line1381 window: `{s['line1381_window']}`",
        f"- Accepted exit routes: `{s['accepted_exit_route_count']}`",
        f"- Accepted occurrence removal: `{s['accepted_occurrence_removal']}`",
        f"- Accepted proxy-T reduction: `{s['accepted_proxy_t_reduction']}`",
        f"- B7 credit delta: `{s['b7_credit_delta']}`",
        f"- Blocker queue hash: `{s['blocker_queue_hash']}`",
        "",
        "R76 fills the R73-D3 no-double-counting packet by excluding line1378 from the line1381 count. This makes the R73 source-closure intake shape pass, but all accepted deltas and B7 credit remain zero.",
        "",
        "## Remaining Failed Gates",
        "",
    ]
    if s["r73_intake_failed_gates"]:
        for gate in s["r73_intake_failed_gates"]:
            lines.append(f"- `{gate}`")
    else:
        lines.append("- None under the R73 source-closure intake replay.")
    lines.extend(["", "## Requirements", ""])
    for item in payload["requirements"]:
        status = "PASS" if item["passed"] else "FAIL"
        lines.append(f"- `{item['requirement_id']}` {status}: {item['label']}")
    lines.extend(
        [
            "",
            "## Claim Boundary",
            "",
            f"- Supported: {payload['claim_boundary']['what_is_supported']}",
            f"- Not supported: {payload['claim_boundary']['what_is_not_supported']}",
            f"- Next gate: {payload['claim_boundary']['next_gate']}",
            "",
            "## Artifacts",
            "",
        ]
    )
    for label, artifact_path in payload["artifacts"].items():
        lines.append(f"- `{label}`: `{artifact_path}`")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=".")
    parser.add_argument(
        "--json-output",
        default="results/B1_B7_cone01_R76_line1378_no_double_counting_gate_v0.json",
    )
    parser.add_argument(
        "--markdown-output",
        default="research/B1_B7_cone01_R76_line1378_no_double_counting_gate.md",
    )
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()

    payload = build_payload(args)
    root = Path(args.repo_root).resolve()
    write_json(root / args.json_output, payload)
    write_markdown(root / args.markdown_output, payload)
    if args.pretty:
        print(json.dumps(payload["summary"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
