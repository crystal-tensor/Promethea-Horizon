#!/usr/bin/env python3
"""T-B1-004fv/T-B7-015e: R72 source-backed positive-delta preflight gate."""

from __future__ import annotations

import argparse
import hashlib
import json
import time
from pathlib import Path
from typing import Any


METHOD = "b1_b7_cone01_r72_source_backed_delta_preflight_gate_v0"
STATUS = "cone01_r72_source_backed_delta_preflight_rejects_metadata_positive_row"
MODEL_STATUS = "positive_numbers_without_r1_r2_source_closure_are_rejected"
VERSION = "0.1"
TARGET_ID = "T-B1-004fv/T-B7-015e"
UPSTREAM_TARGET_ID = "T-B1-004fu/T-B7-015d"
SUBMISSION_DIR = "results/B1_B7_cone01_o3_f4_exit_route_submissions"
R71_CONTRACT = f"{SUBMISSION_DIR}/R71-R1-positive-delta-ledger.contract.json"
R71_TEMPLATE = f"{SUBMISSION_DIR}/R71-R1-positive-delta-ledger.template.json"
R70_PREFILL = f"{SUBMISSION_DIR}/R70-R1-line1381-prefill-machine-check-replay.json"
R66_RESULT = "results/B1_B7_cone01_R66_o3_f4_b7_zero_credit_ledger_retest_gate_v0.json"
R1_RESULT = "results/B1_B7_cone01_R1_line1381_resolution_packet_gate_v0.json"
R2_RESULT = "results/B1_B7_cone01_R2_line1378_overlap_recovery_packet_gate_v0.json"
R72_CANDIDATE = f"{SUBMISSION_DIR}/R72-R1-source-backed-positive-delta-candidate.json"
R72_BASE_VERDICT = f"{SUBMISSION_DIR}/R72-R1-source-backed-positive-delta.base-r71-verdict.json"
R72_HARDENED_VERDICT = f"{SUBMISSION_DIR}/R72-R1-source-backed-positive-delta.hardened-verdict.json"
R72_BLOCKER_QUEUE = f"{SUBMISSION_DIR}/R72-source-backed-delta-blocker-queue.json"


def stable_hash(payload: Any) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


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


def base_r71_verify(root: Path, ledger: dict[str, Any], contract: dict[str, Any], r70: dict[str, Any], r66: dict[str, Any]) -> dict[str, Any]:
    missing = [
        field for field in contract["required_ledger_fields"] if ledger.get(field) in (None, "")
    ]
    gates = {
        "required_fields_complete": missing == [],
        "r70_prefill_file_hash_matches": path_hash_matches(
            root, ledger.get("source_r70_prefill_path"), ledger.get("source_r70_prefill_sha256")
        )
        and ledger.get("source_r70_prefill_hash") == r70["prefill_hash"],
        "r66_packet_hash_matches": ledger.get("source_r66_retest_packet_hash")
        == r66["summary"]["r66_retest_packet_hash"],
        "selected_lines_match": ledger.get("selected_lines") == [268, 1381],
        "dropped_overlap_lines_match": ledger.get("dropped_overlap_lines") == [1378],
        "structural_cnot_delta_positive": isinstance(ledger.get("structural_cnot_delta"), int)
        and ledger["structural_cnot_delta"] >= 1,
        "accepted_exit_route_positive": isinstance(ledger.get("accepted_exit_route_count"), int)
        and ledger["accepted_exit_route_count"] >= 1,
        "occurrence_removal_positive": isinstance(ledger.get("occurrence_removal_delta"), int)
        and ledger["occurrence_removal_delta"] >= 1,
        "proxy_t_reduction_positive": isinstance(ledger.get("proxy_t_reduction_delta"), int)
        and ledger["proxy_t_reduction_delta"] >= 1,
        "line1381_evidence_hash_matches": path_hash_matches(
            root,
            ledger.get("line1381_delta_evidence_path"),
            ledger.get("line1381_delta_evidence_sha256"),
        ),
        "line1378_no_double_counting_hash_matches": path_hash_matches(
            root,
            ledger.get("line1378_no_double_counting_evidence_path"),
            ledger.get("line1378_no_double_counting_evidence_sha256"),
        ),
        "machine_replay_stdout_hash_matches": path_hash_matches(
            root,
            ledger.get("machine_check_replay_stdout_path"),
            ledger.get("machine_check_replay_stdout_sha256"),
        ),
        "b7_not_requested_before_delta_acceptance": ledger.get("b7_nonzero_retest_requested")
        is False,
        "claim_boundary_blocks_o3_reroute_b7": all(
            token in str(ledger.get("claim_boundary", "")).lower()
            for token in ["not", "b7"]
        ),
    }
    failed = [gate for gate, passed in gates.items() if not passed]
    verdict = {
        "artifact": "R72 replay of base R71 positive-delta verifier",
        "method": METHOD,
        "ledger_id": ledger.get("ledger_id"),
        "contract_hash": contract["contract_hash"],
        "gates": gates,
        "passed_gate_count": sum(1 for passed in gates.values() if passed),
        "failed_gate_count": len(failed),
        "failed_gates": failed,
        "missing_required_fields": missing,
        "base_r71_accepted": failed == [],
    }
    verdict["verdict_hash"] = stable_hash(verdict)
    return verdict


def build_metadata_positive_candidate(root: Path, template: dict[str, Any], r1: dict[str, Any], r2: dict[str, Any]) -> dict[str, Any]:
    candidate = dict(template)
    candidate.update(
        {
            "ledger_id": "B1-B7-cone01-R72-source-backed-positive-delta-candidate",
            "route_class": "line1381_positive_delta_candidate_source_backed_preflight",
            "accepted_exit_route_count": 1,
            "occurrence_removal_delta": 1,
            "proxy_t_reduction_delta": 1,
            "line1381_delta_evidence_path": R1_RESULT,
            "line1381_delta_evidence_sha256": file_hash(root / R1_RESULT),
            "line1378_no_double_counting_evidence_path": R2_RESULT,
            "line1378_no_double_counting_evidence_sha256": file_hash(root / R2_RESULT),
            "proxy_t_delta_derivation": (
                "Preflight candidate only: requests proxy_t_reduction_delta=1 from "
                "the R1 line1381 packet, but R1 still fails P6/P7/P8 and has no "
                "submitted source-backed resolution artifact."
            ),
            "occurrence_delta_derivation": (
                "Preflight candidate only: requests occurrence_removal_delta=1 "
                "from selected lines [268, 1381], but R1 and R2 remain open and "
                "line1378 recovery is not source-backed."
            ),
            "claim_boundary": (
                "R72 candidate row for hardened preflight only. It is not accepted, "
                "not an O3 closure, not a reroute permission, and not B7 credit."
            ),
            "source_r1_requirements_passed": r1["summary"]["requirements_passed"],
            "source_r1_requirements_failed": r1["summary"]["requirements_failed"],
            "source_r1_failed_requirement_ids": r1["summary"]["failed_requirement_ids"],
            "source_r2_requirements_passed": r2["summary"]["requirements_passed"],
            "source_r2_requirements_failed": r2["summary"]["requirements_failed"],
            "source_r2_failed_requirement_ids": r2["summary"]["failed_requirement_ids"],
        }
    )
    candidate["candidate_hash"] = stable_hash(candidate)
    return candidate


def hardened_verify(ledger: dict[str, Any], base_verdict: dict[str, Any], r1: dict[str, Any], r2: dict[str, Any]) -> dict[str, Any]:
    r1_summary = r1["summary"]
    r2_summary = r2["summary"]
    gates = {
        "base_r71_verifier_accepts_metadata_shape": base_verdict["base_r71_accepted"] is True,
        "r1_packet_requirements_all_pass": r1_summary["requirements_failed"] == 0,
        "r1_submitted_source_backed_artifact_exists": r1_summary["submitted_r1_artifact_exists"]
        is True,
        "r1_accepted_occurrence_positive": r1_summary["accepted_occurrence_removal"] >= 1,
        "r1_accepted_proxy_t_positive": r1_summary["accepted_proxy_t_reduction"] >= 1,
        "r2_packet_requirements_all_pass": r2_summary["requirements_failed"] == 0,
        "r2_submitted_source_backed_artifact_exists": r2_summary["submitted_r2_artifact_exists"]
        is True,
        "r2_no_double_counting_recovery_valid": r2_summary["line1378_delta_recovered_after"] is True,
        "ledger_positive_values_not_metadata_only": (
            "Preflight candidate only" not in ledger.get("proxy_t_delta_derivation", "")
            and "Preflight candidate only" not in ledger.get("occurrence_delta_derivation", "")
        ),
        "b7_credit_still_zero": ledger.get("b7_nonzero_retest_requested") is False,
    }
    failed = [gate for gate, passed in gates.items() if not passed]
    verdict = {
        "artifact": "R72 hardened source-backed positive-delta preflight verdict",
        "method": METHOD,
        "source_target_id": TARGET_ID,
        "upstream_target_id": UPSTREAM_TARGET_ID,
        "ledger_id": ledger["ledger_id"],
        "candidate_hash": ledger["candidate_hash"],
        "base_r71_accepted": base_verdict["base_r71_accepted"],
        "hardened_accepted": failed == [],
        "gates": gates,
        "passed_gate_count": sum(1 for passed in gates.values() if passed),
        "failed_gate_count": len(failed),
        "failed_gates": failed,
        "source_r1_failed_requirement_ids": r1_summary["failed_requirement_ids"],
        "source_r2_failed_requirement_ids": r2_summary["failed_requirement_ids"],
        "accepted_exit_route_count": 0,
        "accepted_occurrence_removal": 0,
        "accepted_proxy_t_reduction": 0,
        "b7_credit_delta": 0,
        "claim_boundary": (
            "R72 is a hardened preflight. It demonstrates that positive numeric "
            "metadata can satisfy the base R71 shape while still failing source-backed "
            "R1/R2 evidence closure. No exit route or B7 credit is accepted."
        ),
    }
    verdict["verdict_hash"] = stable_hash(verdict)
    return verdict


def build_blocker_queue(hardened: dict[str, Any]) -> dict[str, Any]:
    queue = {
        "artifact": "R72 source-backed positive-delta blocker queue",
        "source_target_id": TARGET_ID,
        "upstream_target_id": UPSTREAM_TARGET_ID,
        "failed_gates": hardened["failed_gates"],
        "queue": [
            {
                "blocker_id": "R72-D1",
                "priority": 1,
                "failed_gates": [
                    "r1_packet_requirements_all_pass",
                    "r1_submitted_source_backed_artifact_exists",
                    "r1_accepted_occurrence_positive",
                ],
                "needed_artifact": "source-backed R1 line1381 resolution artifact with accepted occurrence delta",
            },
            {
                "blocker_id": "R72-D2",
                "priority": 2,
                "failed_gates": [
                    "r1_accepted_proxy_t_positive",
                    "ledger_positive_values_not_metadata_only",
                ],
                "needed_artifact": "hash-bound proxy-T derivation not based on metadata-only positive integers",
            },
            {
                "blocker_id": "R72-D3",
                "priority": 3,
                "failed_gates": [
                    "r2_packet_requirements_all_pass",
                    "r2_submitted_source_backed_artifact_exists",
                    "r2_no_double_counting_recovery_valid",
                ],
                "needed_artifact": "source-backed line1378 no-double-counting or recovery artifact",
            },
        ],
    }
    queue["blocker_queue_hash"] = stable_hash(queue)
    return queue


def build_payload(args: argparse.Namespace) -> dict[str, Any]:
    root = Path(args.repo_root).resolve()
    contract = load_json(root / R71_CONTRACT)
    template = load_json(root / R71_TEMPLATE)
    r70 = load_json(root / R70_PREFILL)
    r66 = load_json(root / R66_RESULT)
    r1 = load_json(root / R1_RESULT)
    r2 = load_json(root / R2_RESULT)

    candidate = build_metadata_positive_candidate(root, template, r1, r2)
    write_json(root / R72_CANDIDATE, candidate)
    base_verdict = base_r71_verify(root, candidate, contract, r70, r66)
    write_json(root / R72_BASE_VERDICT, base_verdict)
    hardened = hardened_verify(candidate, base_verdict, r1, r2)
    write_json(root / R72_HARDENED_VERDICT, hardened)
    blocker_queue = build_blocker_queue(hardened)
    write_json(root / R72_BLOCKER_QUEUE, blocker_queue)

    requirements = [
        req(
            "H1",
            "metadata-positive candidate is fully populated",
            base_verdict["missing_required_fields"] == [],
            {"candidate_hash": candidate["candidate_hash"]},
        ),
        req(
            "H2",
            "base R71 shape verifier accepts the metadata-positive row",
            base_verdict["base_r71_accepted"] is True,
            {"base_failed_gates": base_verdict["failed_gates"]},
        ),
        req(
            "H3",
            "hardened source-backed verifier rejects the same row",
            hardened["hardened_accepted"] is False,
            {"hardened_failed_gates": hardened["failed_gates"]},
        ),
        req(
            "H4",
            "R1 source packet still fails P6/P7/P8",
            r1["summary"]["failed_requirement_ids"] == ["P6", "P7", "P8"],
            {"r1_failed_requirement_ids": r1["summary"]["failed_requirement_ids"]},
        ),
        req(
            "H5",
            "R2 source packet still fails P6/P7/P8",
            r2["summary"]["failed_requirement_ids"] == ["P6", "P7", "P8"],
            {"r2_failed_requirement_ids": r2["summary"]["failed_requirement_ids"]},
        ),
        req(
            "H6",
            "R72 keeps accepted deltas and B7 credit at zero",
            hardened["accepted_exit_route_count"] == 0
            and hardened["accepted_occurrence_removal"] == 0
            and hardened["accepted_proxy_t_reduction"] == 0
            and hardened["b7_credit_delta"] == 0,
            {
                "accepted_exit_route_count": hardened["accepted_exit_route_count"],
                "accepted_occurrence_removal": hardened["accepted_occurrence_removal"],
                "accepted_proxy_t_reduction": hardened["accepted_proxy_t_reduction"],
                "b7_credit_delta": hardened["b7_credit_delta"],
            },
        ),
        req(
            "H7",
            "R72 emits a D1-D3 blocker queue",
            len(blocker_queue["queue"]) == 3,
            {"blocker_queue_hash": blocker_queue["blocker_queue_hash"]},
        ),
    ]
    summary = {
        "method": METHOD,
        "status": STATUS,
        "model_status": MODEL_STATUS,
        "source_target_id": TARGET_ID,
        "upstream_target_id": UPSTREAM_TARGET_ID,
        "candidate_hash": candidate["candidate_hash"],
        "base_r71_accepted": base_verdict["base_r71_accepted"],
        "base_r71_failed_gate_count": base_verdict["failed_gate_count"],
        "hardened_accepted": hardened["hardened_accepted"],
        "hardened_failed_gate_count": hardened["failed_gate_count"],
        "hardened_failed_gates": hardened["failed_gates"],
        "r1_failed_requirement_ids": r1["summary"]["failed_requirement_ids"],
        "r2_failed_requirement_ids": r2["summary"]["failed_requirement_ids"],
        "accepted_exit_route_count": 0,
        "accepted_occurrence_removal": 0,
        "accepted_proxy_t_reduction": 0,
        "b7_nonzero_retest_allowed": False,
        "b7_credit_delta": 0,
        "o3_closed": False,
        "reroute_allowed": False,
        "resource_saving_claimed": False,
        "b7_ledger_improvement_claimed": False,
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
        "title": "B1/B7 Cone01 R72 Source-Backed Delta Preflight Gate",
        "version": VERSION,
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "summary": summary,
        "requirements": requirements,
        "base_r71_verdict": base_verdict,
        "hardened_verdict": hardened,
        "claim_boundary": {
            "what_is_supported": (
                "R72 demonstrates that a metadata-positive R71 row can pass shape "
                "checks while failing source-backed R1/R2 closure."
            ),
            "what_is_not_supported": (
                "R72 does not accept the candidate row, does not accept occurrence "
                "or proxy-T deltas, and does not grant B7 credit."
            ),
            "next_gate": (
                "Replace the metadata-positive candidate with real R1/R2 source-backed "
                "artifacts that close P6/P7/P8."
            ),
        },
        "artifacts": {
            "candidate": R72_CANDIDATE,
            "base_r71_verdict": R72_BASE_VERDICT,
            "hardened_verdict": R72_HARDENED_VERDICT,
            "blocker_queue": R72_BLOCKER_QUEUE,
        },
    }
    payload["summary"]["payload_hash"] = stable_hash(payload)
    return payload


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    s = payload["summary"]
    lines = [
        "# B1/B7 Cone01 R72 Source-Backed Delta Preflight Gate",
        "",
        "## Summary",
        "",
        f"- Status: `{s['status']}`",
        f"- Base R71 accepted metadata-positive row: `{s['base_r71_accepted']}`",
        f"- Hardened source-backed accepted: `{s['hardened_accepted']}`",
        f"- Hardened failed gates: `{s['hardened_failed_gate_count']}`",
        f"- R1 failed requirements: `{s['r1_failed_requirement_ids']}`",
        f"- R2 failed requirements: `{s['r2_failed_requirement_ids']}`",
        f"- Accepted exit routes: `{s['accepted_exit_route_count']}`",
        f"- Accepted occurrence removal: `{s['accepted_occurrence_removal']}`",
        f"- Accepted proxy-T reduction: `{s['accepted_proxy_t_reduction']}`",
        f"- B7 credit delta: `{s['b7_credit_delta']}`",
        f"- Blocker queue hash: `{s['blocker_queue_hash']}`",
        "",
        "R72 fills a metadata-positive candidate row and shows why that is still not enough. The base R71 shape verifier accepts the row, but the hardened source-backed preflight rejects it because the R1 and R2 source packets still fail their P6/P7/P8 closure obligations.",
        "",
        "## Hardened Failed Gates",
        "",
    ]
    for gate in s["hardened_failed_gates"]:
        lines.append(f"- `{gate}`")
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
        default="results/B1_B7_cone01_R72_source_backed_delta_preflight_gate_v0.json",
    )
    parser.add_argument(
        "--markdown-output",
        default="research/B1_B7_cone01_R72_source_backed_delta_preflight_gate.md",
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
