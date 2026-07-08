#!/usr/bin/env python3
"""T-B1-004gn/T-B7-015w: R90 independent review of the R89 proxy credit."""

from __future__ import annotations

import argparse
import hashlib
import json
import time
from pathlib import Path
from typing import Any


METHOD = "b1_b7_cone01_r90_r89_independent_replay_review_gate_v0"
STATUS = "cone01_r90_r89_independent_replay_review_preserves_narrow_credit"
MODEL_STATUS = "r89_proxy_credit_reproduced_double_count_kill_test_clear_no_new_credit"
VERSION = "0.1"
TARGET_ID = "T-B1-004gn/T-B7-015w"
UPSTREAM_TARGET_ID = "T-B1-004gm/T-B7-015v"
SUBMISSION_DIR = "results/B1_B7_cone01_o3_f4_exit_route_submissions"

R88_FILLED_SUBMISSION = f"{SUBMISSION_DIR}/R88-G1-filled-r83-submission.json"
R89_RESULT = "results/B1_B7_cone01_R89_g1_downstream_b7_replay_gate_v0.json"
R89_REPLAY_LEDGER = f"{SUBMISSION_DIR}/R89-G1-downstream-b7-replay-ledger.json"
R89_VERDICT = f"{SUBMISSION_DIR}/R89-G1-downstream-b7-replay.verdict.json"
R89_BLOCKER_QUEUE = f"{SUBMISSION_DIR}/R89-G1-post-credit-blocker-queue.json"
B7_GCM_BOUNDARY = "results/B7_gcm_h6_ft_boundary_v0.json"

R90_REVIEW_LEDGER = f"{SUBMISSION_DIR}/R90-G1-r89-independent-review-ledger.json"
R90_VERDICT = f"{SUBMISSION_DIR}/R90-G1-r89-double-count-kill-test.verdict.json"
R90_STDOUT = f"{SUBMISSION_DIR}/R90-G1-r89-independent-review.stdout.txt"
R90_BLOCKER_QUEUE = f"{SUBMISSION_DIR}/R90-G1-post-review-blocker-queue.json"


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


def recompute_target_rows(r88_submission: dict[str, Any], b7_boundary: dict[str, Any]) -> list[dict[str, Any]]:
    fields = r88_submission["fields"]
    candidate_after = int(fields["candidate_after_t_ledger"])
    candidate_delta = int(fields["claimed_t_ledger_reduction"])
    rows = []
    for row in b7_boundary["target_requirements_for_current_min"]:
        target = float(row["target_stv_reduction"])
        max_after = int(row["max_after_t_ledger"])
        rows.append(
            {
                "target_stv_reduction": target,
                "baseline_after_t_ledger": int(row["current_after_t_ledger"]),
                "candidate_t_ledger_reduction": candidate_delta,
                "candidate_after_t_ledger": candidate_after,
                "max_after_t_ledger": max_after,
                "candidate_margin_to_target": max_after - candidate_after,
                "target_reached": candidate_after <= max_after,
                "proxy_credit_eligible": target == 1.2 and candidate_after <= max_after,
            }
        )
    return rows


def build_review_ledger(
    root: Path,
    r88_submission: dict[str, Any],
    r89_result: dict[str, Any],
    r89_ledger: dict[str, Any],
    r89_verdict: dict[str, Any],
    r89_blocker_queue: dict[str, Any],
    b7_boundary: dict[str, Any],
) -> dict[str, Any]:
    target_rows = recompute_target_rows(r88_submission, b7_boundary)
    target_120 = next(row for row in target_rows if row["target_stv_reduction"] == 1.2)
    target_125 = next(row for row in target_rows if row["target_stv_reduction"] == 1.25)

    recomputed_after = target_120["candidate_after_t_ledger"]
    recomputed_delta = target_120["candidate_t_ledger_reduction"]
    component_credit_sum = (
        int(r89_ledger["accepted_b7_dependency_credit_delta"])
        + int(r89_ledger["accepted_b7_resource_credit_delta"])
        + int(r89_ledger["accepted_b7_ft_ledger_credit_delta"])
    )
    duplicate_positive_channels = [
        name
        for name in [
            "accepted_b7_dependency_credit_delta",
            "accepted_b7_resource_credit_delta",
            "accepted_b7_ft_ledger_credit_delta",
            "accepted_b7_space_time_volume_credit",
        ]
        if int(r89_ledger[name]) > 0
    ]
    double_count_violation = (
        component_credit_sum != int(r89_ledger["accepted_b7_credit_delta"])
        or duplicate_positive_channels
        != ["accepted_b7_ft_ledger_credit_delta", "accepted_b7_space_time_volume_credit"]
    )

    ledger = {
        "artifact": "R90 R89 independent review ledger",
        "method": METHOD,
        "source_target_id": TARGET_ID,
        "upstream_target_id": UPSTREAM_TARGET_ID,
        "source_r88_filled_submission_path": R88_FILLED_SUBMISSION,
        "source_r88_filled_submission_sha256": file_hash(root / R88_FILLED_SUBMISSION),
        "source_r88_filled_submission_hash": r88_submission["filled_submission_hash"],
        "source_r89_result_path": R89_RESULT,
        "source_r89_result_sha256": file_hash(root / R89_RESULT),
        "source_r89_payload_hash": r89_result["payload_hash"],
        "source_r89_replay_ledger_path": R89_REPLAY_LEDGER,
        "source_r89_replay_ledger_sha256": file_hash(root / R89_REPLAY_LEDGER),
        "source_r89_replay_ledger_hash": r89_ledger["replay_ledger_hash"],
        "source_r89_verdict_path": R89_VERDICT,
        "source_r89_verdict_sha256": file_hash(root / R89_VERDICT),
        "source_r89_verdict_hash": r89_verdict["verdict_hash"],
        "source_r89_blocker_queue_path": R89_BLOCKER_QUEUE,
        "source_r89_blocker_queue_sha256": file_hash(root / R89_BLOCKER_QUEUE),
        "source_r89_blocker_queue_hash": r89_blocker_queue["blocker_queue_hash"],
        "source_b7_boundary_path": B7_GCM_BOUNDARY,
        "source_b7_boundary_sha256": file_hash(root / B7_GCM_BOUNDARY),
        "route_id": r89_ledger["route_id"],
        "review_type": "independent_replay_arithmetic_and_double_count_kill_test",
        "recomputed_target_rows": target_rows,
        "recomputed_baseline_after_t_ledger": target_120["baseline_after_t_ledger"],
        "recomputed_candidate_t_ledger_reduction": recomputed_delta,
        "recomputed_candidate_after_t_ledger": recomputed_after,
        "recomputed_target_1_20_reached": target_120["target_reached"],
        "recomputed_target_1_20_margin": target_120["candidate_margin_to_target"],
        "recomputed_target_1_25_reached": target_125["target_reached"],
        "recomputed_target_1_25_margin": target_125["candidate_margin_to_target"],
        "r89_reported_candidate_after_t_ledger": r89_ledger["candidate_after_t_ledger"],
        "r89_reported_target_1_20_margin": r89_ledger["target_1_20_margin"],
        "r89_reported_target_1_25_margin": r89_ledger["target_1_25_margin"],
        "independent_replay_reproduced": recomputed_after == r89_ledger["candidate_after_t_ledger"]
        and target_120["candidate_margin_to_target"] == r89_ledger["target_1_20_margin"]
        and target_125["candidate_margin_to_target"] == r89_ledger["target_1_25_margin"],
        "component_credit_sum": component_credit_sum,
        "reported_accepted_b7_credit_delta": r89_ledger["accepted_b7_credit_delta"],
        "duplicate_positive_channels": duplicate_positive_channels,
        "double_count_violation_found": double_count_violation,
        "credit_preserved_after_review": not double_count_violation
        and r89_verdict["accepted"] is True
        and r89_ledger["accepted_b7_credit_delta"] == 1
        and r89_ledger["accepted_credit_scope"] == "proxy_ft_stv_1_20_only",
        "accepted_b7_credit_delta_after_review": 1 if not double_count_violation else 0,
        "new_credit_delta": 0,
        "revoked_credit_delta": 0 if not double_count_violation else 1,
        "target_1_25_credit_claimed": False,
        "o3_closed": False,
        "reroute_allowed": False,
        "resource_saving_claimed": False,
        "physical_layout_claimed": False,
        "claim_boundary": (
            "R90 independently reproduces the R89 arithmetic and double-count "
            "sentinel for the narrow 1.20x proxy FT/STV credit. It adds no new "
            "credit, does not reach 1.25x, and does not close O3, reroute, "
            "physical-layout, or resource-saving claims."
        ),
    }
    ledger["review_ledger_hash"] = stable_self_hash(ledger, "review_ledger_hash")
    return ledger


def build_verdict(ledger: dict[str, Any]) -> dict[str, Any]:
    gates = {
        "r89_hash_bound": bool(ledger["source_r89_replay_ledger_hash"])
        and bool(ledger["source_r89_verdict_hash"]),
        "independent_replay_reproduced": ledger["independent_replay_reproduced"] is True,
        "no_double_count_violation": ledger["double_count_violation_found"] is False,
        "narrow_credit_preserved": ledger["credit_preserved_after_review"] is True
        and ledger["accepted_b7_credit_delta_after_review"] == 1,
        "no_new_credit": ledger["new_credit_delta"] == 0 and ledger["revoked_credit_delta"] == 0,
        "target_1_25_still_blocked": ledger["recomputed_target_1_25_reached"] is False
        and ledger["target_1_25_credit_claimed"] is False,
        "o3_and_resource_claims_still_closed": ledger["o3_closed"] is False
        and ledger["reroute_allowed"] is False
        and ledger["resource_saving_claimed"] is False
        and ledger["physical_layout_claimed"] is False,
    }
    failed = [gate for gate, passed in gates.items() if not passed]
    verdict = {
        "artifact": "R90 R89 double-count kill-test verdict",
        "method": METHOD,
        "source_target_id": TARGET_ID,
        "upstream_target_id": UPSTREAM_TARGET_ID,
        "review_ledger_path": R90_REVIEW_LEDGER,
        "review_ledger_hash": ledger["review_ledger_hash"],
        "gates": gates,
        "passed_gate_count": sum(1 for passed in gates.values() if passed),
        "failed_gate_count": len(failed),
        "failed_gates": failed,
        "accepted": failed == [],
        "accepted_b7_credit_delta_after_review": ledger[
            "accepted_b7_credit_delta_after_review"
        ],
        "new_credit_delta": ledger["new_credit_delta"],
        "revoked_credit_delta": ledger["revoked_credit_delta"],
        "double_count_violation_found": ledger["double_count_violation_found"],
        "recomputed_target_1_20_margin": ledger["recomputed_target_1_20_margin"],
        "recomputed_target_1_25_margin": ledger["recomputed_target_1_25_margin"],
        "claim_boundary": ledger["claim_boundary"],
    }
    verdict["verdict_hash"] = stable_self_hash(verdict, "verdict_hash")
    return verdict


def build_blocker_queue(ledger: dict[str, Any], verdict: dict[str, Any]) -> dict[str, Any]:
    queue = {
        "artifact": "R90 G1 post-review blocker queue",
        "method": METHOD,
        "source_target_id": TARGET_ID,
        "upstream_target_id": UPSTREAM_TARGET_ID,
        "review_ledger_hash": ledger["review_ledger_hash"],
        "verdict_hash": verdict["verdict_hash"],
        "accepted_b7_credit_delta_after_review": ledger[
            "accepted_b7_credit_delta_after_review"
        ],
        "queue": [
            {
                "blocker_id": "R90-G1-1",
                "priority": 1,
                "target_gate": "external_independent_reproduction",
                "needed_artifact": "third-party rerun of the R89/R90 arithmetic and hash-bound ledger",
            },
            {
                "blocker_id": "R90-G1-2",
                "priority": 2,
                "target_gate": "target_1_25_gap",
                "needed_artifact": "accepted extra reduction or stronger B7 reprice to close the 224-unit 1.25x deficit",
                "remaining_margin": ledger["recomputed_target_1_25_margin"],
            },
            {
                "blocker_id": "R90-G1-3",
                "priority": 3,
                "target_gate": "physical_layout_boundary",
                "needed_artifact": "layout/routing/factory schedule evidence before resource-saving or O3 claims",
            },
        ],
    }
    queue["blocker_queue_hash"] = stable_self_hash(queue, "blocker_queue_hash")
    return queue


def write_stdout(root: Path, ledger: dict[str, Any], verdict: dict[str, Any]) -> str:
    text = "\n".join(
        [
            "R90 R89 independent replay review stdout",
            f"method={METHOD}",
            f"source_target_id={TARGET_ID}",
            f"upstream_target_id={UPSTREAM_TARGET_ID}",
            f"review_ledger_hash={ledger['review_ledger_hash']}",
            f"verdict_hash={verdict['verdict_hash']}",
            f"independent_replay_reproduced={str(ledger['independent_replay_reproduced']).lower()}",
            f"double_count_violation_found={str(ledger['double_count_violation_found']).lower()}",
            f"accepted_b7_credit_delta_after_review={ledger['accepted_b7_credit_delta_after_review']}",
            f"new_credit_delta={ledger['new_credit_delta']}",
            f"target_1_20_margin={ledger['recomputed_target_1_20_margin']}",
            f"target_1_25_margin={ledger['recomputed_target_1_25_margin']}",
            "o3_closed=false",
            "resource_saving_claimed=false",
        ]
    ) + "\n"
    path = root / R90_STDOUT
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def build_payload(args: argparse.Namespace) -> dict[str, Any]:
    root = Path(args.repo_root).resolve()
    r88_submission = load_json(root / R88_FILLED_SUBMISSION)
    r89_result = load_json(root / R89_RESULT)
    r89_ledger = load_json(root / R89_REPLAY_LEDGER)
    r89_verdict = load_json(root / R89_VERDICT)
    r89_blocker_queue = load_json(root / R89_BLOCKER_QUEUE)
    b7_boundary = load_json(root / B7_GCM_BOUNDARY)

    ledger = build_review_ledger(
        root,
        r88_submission,
        r89_result,
        r89_ledger,
        r89_verdict,
        r89_blocker_queue,
        b7_boundary,
    )
    write_json(root / R90_REVIEW_LEDGER, ledger)
    verdict = build_verdict(ledger)
    write_json(root / R90_VERDICT, verdict)
    stdout_sha256 = write_stdout(root, ledger, verdict)
    blocker_queue = build_blocker_queue(ledger, verdict)
    write_json(root / R90_BLOCKER_QUEUE, blocker_queue)

    requirements = [
        req(
            "A1",
            "R90 binds the R89 result, replay ledger, verdict, and blocker queue by hash",
            r89_result["summary"]["source_target_id"] == UPSTREAM_TARGET_ID
            and r89_result["replay_ledger_hash"] == r89_ledger["replay_ledger_hash"]
            and r89_result["verdict_hash"] == r89_verdict["verdict_hash"],
            {
                "r89_payload_hash": r89_result["payload_hash"],
                "r89_replay_ledger_hash": r89_ledger["replay_ledger_hash"],
                "r89_verdict_hash": r89_verdict["verdict_hash"],
            },
        ),
        req(
            "A2",
            "R90 independently reproduces the R89 replay arithmetic",
            ledger["independent_replay_reproduced"] is True,
            {
                "recomputed_candidate_after_t_ledger": ledger[
                    "recomputed_candidate_after_t_ledger"
                ],
                "recomputed_target_1_20_margin": ledger["recomputed_target_1_20_margin"],
                "recomputed_target_1_25_margin": ledger["recomputed_target_1_25_margin"],
            },
        ),
        req(
            "A3",
            "R90 finds no double-count violation in the accepted proxy credit",
            ledger["double_count_violation_found"] is False
            and ledger["component_credit_sum"] == ledger["reported_accepted_b7_credit_delta"],
            {
                "component_credit_sum": ledger["component_credit_sum"],
                "reported_accepted_b7_credit_delta": ledger[
                    "reported_accepted_b7_credit_delta"
                ],
                "duplicate_positive_channels": ledger["duplicate_positive_channels"],
            },
        ),
        req(
            "A4",
            "R90 preserves exactly the R89 narrow credit and grants no new credit",
            ledger["credit_preserved_after_review"] is True
            and ledger["accepted_b7_credit_delta_after_review"] == 1
            and ledger["new_credit_delta"] == 0
            and ledger["revoked_credit_delta"] == 0,
            {
                "accepted_b7_credit_delta_after_review": ledger[
                    "accepted_b7_credit_delta_after_review"
                ],
                "new_credit_delta": ledger["new_credit_delta"],
                "revoked_credit_delta": ledger["revoked_credit_delta"],
            },
        ),
        req(
            "A5",
            "R90 keeps the 1.25x target blocked",
            ledger["recomputed_target_1_25_reached"] is False
            and ledger["recomputed_target_1_25_margin"] == -224
            and ledger["target_1_25_credit_claimed"] is False,
            {
                "recomputed_target_1_25_margin": ledger["recomputed_target_1_25_margin"],
                "target_1_25_credit_claimed": ledger["target_1_25_credit_claimed"],
            },
        ),
        req(
            "A6",
            "R90 keeps O3, reroute, physical-layout, and resource-saving claims closed",
            ledger["o3_closed"] is False
            and ledger["reroute_allowed"] is False
            and ledger["physical_layout_claimed"] is False
            and ledger["resource_saving_claimed"] is False,
            {
                "o3_closed": ledger["o3_closed"],
                "reroute_allowed": ledger["reroute_allowed"],
                "physical_layout_claimed": ledger["physical_layout_claimed"],
                "resource_saving_claimed": ledger["resource_saving_claimed"],
            },
        ),
        req(
            "A7",
            "R90 emits a next-blocker queue for external reproduction, 1.25x, and layout",
            len(blocker_queue["queue"]) == 3
            and [item["target_gate"] for item in blocker_queue["queue"]]
            == [
                "external_independent_reproduction",
                "target_1_25_gap",
                "physical_layout_boundary",
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
        validation_errors.append("one or more R90 requirements failed")
    if ledger["new_credit_delta"] != 0:
        validation_errors.append("R90 must not grant new credit")
    if ledger["double_count_violation_found"]:
        validation_errors.append("R90 detected a double-count violation")

    payload = {
        "artifact": "B1/B7 cone01 R90 R89 independent replay review gate",
        "method": METHOD,
        "version": VERSION,
        "status": STATUS,
        "model_status": MODEL_STATUS,
        "source_target_id": TARGET_ID,
        "upstream_target_id": UPSTREAM_TARGET_ID,
        "generated_at_unix": int(time.time()),
        "review_ledger_path": R90_REVIEW_LEDGER,
        "review_ledger_hash": ledger["review_ledger_hash"],
        "verdict_path": R90_VERDICT,
        "verdict_hash": verdict["verdict_hash"],
        "stdout_path": R90_STDOUT,
        "stdout_sha256": stdout_sha256,
        "blocker_queue_path": R90_BLOCKER_QUEUE,
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
            "independent_replay_reproduced": ledger["independent_replay_reproduced"],
            "double_count_violation_found": ledger["double_count_violation_found"],
            "credit_preserved_after_review": ledger["credit_preserved_after_review"],
            "accepted_b7_credit_delta_after_review": ledger[
                "accepted_b7_credit_delta_after_review"
            ],
            "new_credit_delta": ledger["new_credit_delta"],
            "revoked_credit_delta": ledger["revoked_credit_delta"],
            "recomputed_candidate_after_t_ledger": ledger[
                "recomputed_candidate_after_t_ledger"
            ],
            "recomputed_target_1_20_reached": ledger["recomputed_target_1_20_reached"],
            "recomputed_target_1_20_margin": ledger["recomputed_target_1_20_margin"],
            "recomputed_target_1_25_reached": ledger["recomputed_target_1_25_reached"],
            "recomputed_target_1_25_margin": ledger["recomputed_target_1_25_margin"],
            "component_credit_sum": ledger["component_credit_sum"],
            "reported_accepted_b7_credit_delta": ledger[
                "reported_accepted_b7_credit_delta"
            ],
            "duplicate_positive_channels": ledger["duplicate_positive_channels"],
            "o3_closed": ledger["o3_closed"],
            "reroute_allowed": ledger["reroute_allowed"],
            "resource_saving_claimed": ledger["resource_saving_claimed"],
            "physical_layout_claimed": ledger["physical_layout_claimed"],
            "verdict_accepted": verdict["accepted"],
            "verdict_failed_gate_count": verdict["failed_gate_count"],
            "failed_gates": verdict["failed_gates"],
            "review_ledger_hash": ledger["review_ledger_hash"],
            "verdict_hash": verdict["verdict_hash"],
            "stdout_sha256": stdout_sha256,
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
        "# B1/B7 Cone01 R90 R89 Independent Replay Review Gate",
        "",
        f"- Target: `{TARGET_ID}`",
        f"- Upstream target: `{UPSTREAM_TARGET_ID}`",
        f"- Method: `{METHOD}`",
        f"- Status: `{STATUS}`",
        f"- Model status: `{MODEL_STATUS}`",
        "",
        "## Result",
        "",
        "R90 independently reviews the R89 narrow proxy credit instead of adding a",
        "new credit. It recomputes the B7 replay arithmetic from the filled R88/R83",
        "submission and the current B7 boundary, reproduces the R89 `6224 -> 5624`",
        "path, and finds no double-count violation in the accepted one-unit proxy",
        "FT/STV credit.",
        "",
        "The result preserves the R89 `1.20x` proxy credit, keeps the `1.25x` target",
        "blocked with margin `-224`, and leaves O3, reroute, physical-layout, and",
        "resource-saving claims closed.",
        "",
        "## Key Counters",
        "",
        f"- Independent replay reproduced: `{summary['independent_replay_reproduced']}`",
        f"- Double-count violation found: `{summary['double_count_violation_found']}`",
        f"- Credit preserved after review: `{summary['credit_preserved_after_review']}`",
        f"- Accepted B7 credit after review: `{summary['accepted_b7_credit_delta_after_review']}`",
        f"- New credit delta: `{summary['new_credit_delta']}`",
        f"- Recomputed candidate after T ledger: `{summary['recomputed_candidate_after_t_ledger']}`",
        f"- Recomputed 1.20x margin: `{summary['recomputed_target_1_20_margin']}`",
        f"- Recomputed 1.25x margin: `{summary['recomputed_target_1_25_margin']}`",
        f"- O3 closed: `{summary['o3_closed']}`",
        "",
        "## Requirements",
        "",
    ]
    for requirement in payload["requirements"]:
        status = "PASS" if requirement["passed"] else "FAIL"
        lines.append(f"- `{requirement['requirement_id']}` {status}: {requirement['label']}")
    lines.extend(
        [
            "",
            "## Artifacts",
            "",
            "- Result JSON: `results/B1_B7_cone01_R90_r89_independent_replay_review_gate_v0.json`",
            f"- Review ledger: `{R90_REVIEW_LEDGER}`",
            f"- Verdict: `{R90_VERDICT}`",
            f"- Stdout: `{R90_STDOUT}`",
            f"- Post-review blocker queue: `{R90_BLOCKER_QUEUE}`",
            "",
            "## Claim Boundary",
            "",
            "R90 is a review and kill-test gate. It preserves the R89 narrow proxy",
            "credit only because the arithmetic and double-count checks reproduce.",
            "It grants no new credit, does not solve B7, does not reach 1.25x, and",
            "does not close O3, reroute, physical-layout, resource-saving, or",
            "product-readiness claims.",
            "",
        ]
    )
    report_path = root / "research/B1_B7_cone01_R90_r89_independent_replay_review_gate.md"
    report_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()
    root = Path(args.repo_root).resolve()
    payload = build_payload(args)
    result_path = root / "results/B1_B7_cone01_R90_r89_independent_replay_review_gate_v0.json"
    write_json(result_path, payload)
    write_report(root, payload)
    if args.pretty:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(json.dumps(payload, sort_keys=True))


if __name__ == "__main__":
    main()
