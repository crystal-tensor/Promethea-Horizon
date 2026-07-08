#!/usr/bin/env python3
"""T-B1-004fx/T-B7-015g: R74 R1 occurrence packet prefill gate."""

from __future__ import annotations

import argparse
import hashlib
import json
import time
from pathlib import Path
from typing import Any


METHOD = "b1_b7_cone01_r74_r1_occurrence_packet_prefill_gate_v0"
STATUS = "cone01_r74_r1_occurrence_packet_prefill_partial_zero_credit"
MODEL_STATUS = "r73_d1_occurrence_packet_prefilled_d2_d3_still_block_acceptance"
VERSION = "0.1"
TARGET_ID = "T-B1-004fx/T-B7-015g"
UPSTREAM_TARGET_ID = "T-B1-004fw/T-B7-015f"
SUBMISSION_DIR = "results/B1_B7_cone01_o3_f4_exit_route_submissions"
R70_PREFILL = f"{SUBMISSION_DIR}/R70-R1-line1381-prefill-machine-check-replay.json"
R73_CONTRACT = f"{SUBMISSION_DIR}/R73-r1-r2-source-closure-intake.contract.json"
R73_TEMPLATE = f"{SUBMISSION_DIR}/R73-r1-r2-source-closure-intake.template.json"
R74_ARTIFACT = f"{SUBMISSION_DIR}/R74-r1-line1381-occurrence-replay-artifact.json"
R74_STDOUT = f"{SUBMISSION_DIR}/R74-r1-line1381-occurrence-replay.stdout.txt"
R74_VERDICT = f"{SUBMISSION_DIR}/R74-r1-line1381-occurrence-replay.verdict.json"
R74_SUBMISSION = f"{SUBMISSION_DIR}/R74-r1-occurrence-source-closure-submission.json"
R74_INTAKE_VERDICT = f"{SUBMISSION_DIR}/R74-r1-occurrence-source-closure-intake.verdict.json"
R74_BLOCKER_QUEUE = f"{SUBMISSION_DIR}/R74-source-closure-blocker-queue.json"


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


def instruction_lines(path: Path) -> list[str]:
    lines = []
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("//"):
            continue
        if stripped.startswith("OPENQASM") or stripped.startswith("include "):
            continue
        if stripped.startswith("qubit[") or stripped.startswith("bit["):
            continue
        lines.append(stripped)
    return lines


def count_prefix(lines: list[str], prefix: str) -> int:
    return sum(1 for line in lines if line.startswith(prefix))


def line_at(path: Path, one_based_line: int) -> str:
    return path.read_text(encoding="utf-8").splitlines()[one_based_line - 1].strip()


def path_hash_matches(root: Path, path_value: Any, hash_value: Any) -> bool:
    if not isinstance(path_value, str) or not isinstance(hash_value, str):
        return False
    path = root / path_value
    return path.exists() and file_hash(path) == hash_value


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
            path_field = field[:-7] + "path"
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
        "artifact": "R74 replay of R73 source-closure intake verifier",
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
    r70 = load_json(root / R70_PREFILL)
    contract = load_json(root / R73_CONTRACT)
    template = load_json(root / R73_TEMPLATE)
    source_path = root / r70["source_openqasm3_path"]
    candidate_path = root / r70["candidate_openqasm3_path"]
    source_instructions = instruction_lines(source_path)
    candidate_instructions = instruction_lines(candidate_path)
    source_line_1381 = line_at(source_path, 1381)
    candidate_line_1381 = line_at(candidate_path, 1381)
    source_cnot_count = count_prefix(source_instructions, "cx ")
    candidate_cnot_count = count_prefix(candidate_instructions, "cx ")

    artifact = {
        "artifact": "R74 R1 line1381 occurrence replay artifact",
        "method": METHOD,
        "source_target_id": TARGET_ID,
        "upstream_target_id": UPSTREAM_TARGET_ID,
        "source_openqasm3_path": r70["source_openqasm3_path"],
        "source_openqasm3_sha256": r70["source_openqasm3_sha256"],
        "candidate_openqasm3_path": r70["candidate_openqasm3_path"],
        "candidate_openqasm3_sha256": r70["candidate_openqasm3_sha256"],
        "selected_source_lines": [268, 1381],
        "line1381_source_instruction": source_line_1381,
        "line1381_candidate_instruction_at_same_line": candidate_line_1381,
        "line1381_source_is_cx": source_line_1381.startswith("cx "),
        "line1381_candidate_same_line_is_not_cx": not candidate_line_1381.startswith("cx "),
        "source_instruction_count": len(source_instructions),
        "candidate_instruction_count": len(candidate_instructions),
        "source_cnot_count": source_cnot_count,
        "candidate_cnot_count": candidate_cnot_count,
        "structural_cnot_delta": source_cnot_count - candidate_cnot_count,
        "occurrence_removed_lines": [1381],
        "occurrence_delta_derivation": (
            "R74 line-scoped source-backed prefill: source OpenQASM3 line 1381 is "
            "`cx q[3],q[15];`, the same candidate line is not a CNOT, and the "
            "source/candidate OpenQASM3 files plus replay verdict are hash-bound. "
            "This fills R73-D1 only; it is not a full accepted occurrence proof "
            "until proxy-T and line1378 no-double-counting closure pass."
        ),
        "claim_boundary": (
            "R74 fills the R73-D1 occurrence packet shape with source-backed line "
            "evidence. It does not close R73, does not accept the positive-delta "
            "row, does not close O3, does not allow reroute, and does not grant "
            "B7 credit."
        ),
    }
    artifact["artifact_hash"] = stable_hash(artifact)
    write_json(root / R74_ARTIFACT, artifact)

    replay_verdict = {
        "artifact": "R74 R1 line1381 occurrence replay verdict",
        "method": METHOD,
        "source_target_id": TARGET_ID,
        "artifact_path": R74_ARTIFACT,
        "artifact_sha256": file_hash(root / R74_ARTIFACT),
        "checks": {
            "source_hash_matches": file_hash(source_path) == r70["source_openqasm3_sha256"],
            "candidate_hash_matches": file_hash(candidate_path) == r70["candidate_openqasm3_sha256"],
            "source_line1381_is_cx": artifact["line1381_source_is_cx"],
            "candidate_same_line_not_cx": artifact["line1381_candidate_same_line_is_not_cx"],
            "structural_cnot_delta_positive": artifact["structural_cnot_delta"] > 0,
            "claim_boundary_blocks_b7": "does not grant B7 credit" in artifact["claim_boundary"],
        },
        "accepted_for_r73_d1_prefill": True,
        "accepted_exit_route_count": 0,
        "accepted_occurrence_removal": 0,
        "accepted_proxy_t_reduction": 0,
        "b7_credit_delta": 0,
    }
    replay_verdict["failed_checks"] = [
        check for check, passed in replay_verdict["checks"].items() if not passed
    ]
    replay_verdict["accepted_for_r73_d1_prefill"] = replay_verdict["failed_checks"] == []
    replay_verdict["verdict_hash"] = stable_hash(replay_verdict)
    write_json(root / R74_VERDICT, replay_verdict)

    stdout_payload = {
        "artifact": "R74 R1 line1381 occurrence replay stdout",
        "method": METHOD,
        "source_target_id": TARGET_ID,
        "source_line1381": source_line_1381,
        "candidate_line1381": candidate_line_1381,
        "source_cnot_count": source_cnot_count,
        "candidate_cnot_count": candidate_cnot_count,
        "structural_cnot_delta": artifact["structural_cnot_delta"],
        "accepted_for_r73_d1_prefill": replay_verdict["accepted_for_r73_d1_prefill"],
        "claim_boundary": artifact["claim_boundary"],
    }
    (root / R74_STDOUT).write_text(
        json.dumps(stdout_payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    submission = json.loads(json.dumps(template))
    submission.update(
        {
            "submission_id": "B1-B7-cone01-R74-r1-occurrence-source-closure-prefill",
            "accepted_exit_route_count": 0,
            "occurrence_removal_delta": 0,
            "proxy_t_reduction_delta": 0,
            "b7_nonzero_retest_requested": False,
            "claim_boundary": (
                "R74 fills R73-D1 only. D2 proxy-T and D3 line1378 no-double-counting "
                "remain empty, so this is not accepted, not O3 closure, not reroute "
                "permission, and not B7 credit."
            ),
        }
    )
    submission["packets"]["R73-D1-line1381-source-backed-occurrence"].update(
        {
            "r1_source_artifact_path": R74_ARTIFACT,
            "r1_source_artifact_sha256": file_hash(root / R74_ARTIFACT),
            "r1_replay_command": (
                "python3 tools/b1_b7_cone01_r74_r1_occurrence_packet_prefill_gate.py "
                "--repo-root . --pretty"
            ),
            "r1_replay_stdout_path": R74_STDOUT,
            "r1_replay_stdout_sha256": file_hash(root / R74_STDOUT),
            "r1_selected_lines": [268, 1381],
            "r1_occurrence_removed_lines": [1381],
            "r1_occurrence_delta_derivation": artifact["occurrence_delta_derivation"],
            "r1_replay_verdict_path": R74_VERDICT,
            "r1_replay_verdict_sha256": file_hash(root / R74_VERDICT),
            "r1_claim_boundary": artifact["claim_boundary"],
        }
    )
    submission["submission_hash"] = stable_hash(submission)
    write_json(root / R74_SUBMISSION, submission)

    intake_verdict = verify_intake(root, submission, contract)
    write_json(root / R74_INTAKE_VERDICT, intake_verdict)
    blocker_queue = {
        "artifact": "R74 remaining source-closure blocker queue",
        "source_target_id": TARGET_ID,
        "upstream_target_id": UPSTREAM_TARGET_ID,
        "r73_d1_prefilled": intake_verdict["gates"]["r1_occurrence_delta_source_backed"],
        "remaining_failed_gates": intake_verdict["failed_gates"],
        "queue": [
            {
                "blocker_id": "R74-C2",
                "priority": 1,
                "needed_artifact": "source-backed proxy-T pricing derivation and replay transcript",
            },
            {
                "blocker_id": "R74-C3",
                "priority": 2,
                "needed_artifact": "source-backed line1378 recovery or exclusion ledger",
            },
        ],
    }
    blocker_queue["blocker_queue_hash"] = stable_hash(blocker_queue)
    write_json(root / R74_BLOCKER_QUEUE, blocker_queue)

    requirements = [
        req(
            "J1",
            "R74 binds source and candidate OpenQASM3 hashes",
            replay_verdict["checks"]["source_hash_matches"]
            and replay_verdict["checks"]["candidate_hash_matches"],
            {
                "source_openqasm3_sha256": r70["source_openqasm3_sha256"],
                "candidate_openqasm3_sha256": r70["candidate_openqasm3_sha256"],
            },
        ),
        req(
            "J2",
            "source line1381 is a CNOT and candidate same line is not a CNOT",
            replay_verdict["checks"]["source_line1381_is_cx"]
            and replay_verdict["checks"]["candidate_same_line_not_cx"],
            {
                "source_line1381": source_line_1381,
                "candidate_line1381": candidate_line_1381,
            },
        ),
        req(
            "J3",
            "structural CNOT delta remains positive but not accepted credit",
            artifact["structural_cnot_delta"] == 6
            and replay_verdict["accepted_occurrence_removal"] == 0,
            {"structural_cnot_delta": artifact["structural_cnot_delta"]},
        ),
        req(
            "J4",
            "R73-D1 packet fields are fully populated and hash-bound",
            intake_verdict["gates"]["r1_occurrence_delta_source_backed"]
            and intake_verdict["missing_by_packet"][
                "R73-D1-line1381-source-backed-occurrence"
            ]
            == [],
            {
                "r73_d1_missing_fields": intake_verdict["missing_by_packet"][
                    "R73-D1-line1381-source-backed-occurrence"
                ]
            },
        ),
        req(
            "J5",
            "R73 intake still rejects the submission because D2/D3 remain open",
            intake_verdict["accepted"] is False
            and "proxy_t_delta_source_backed" in intake_verdict["failed_gates"]
            and "r2_no_double_counting_source_backed" in intake_verdict["failed_gates"],
            {"failed_gates": intake_verdict["failed_gates"]},
        ),
        req(
            "J6",
            "R74 keeps all accepted deltas and B7 credit at zero",
            intake_verdict["accepted_exit_route_count"] == 0
            and intake_verdict["accepted_occurrence_removal"] == 0
            and intake_verdict["accepted_proxy_t_reduction"] == 0
            and intake_verdict["b7_credit_delta"] == 0,
            {
                "accepted_exit_route_count": intake_verdict["accepted_exit_route_count"],
                "accepted_occurrence_removal": intake_verdict["accepted_occurrence_removal"],
                "accepted_proxy_t_reduction": intake_verdict["accepted_proxy_t_reduction"],
                "b7_credit_delta": intake_verdict["b7_credit_delta"],
            },
        ),
        req(
            "J7",
            "R74 emits a remaining C2/C3 blocker queue",
            len(blocker_queue["queue"]) == 2,
            {"blocker_queue_hash": blocker_queue["blocker_queue_hash"]},
        ),
        req(
            "J8",
            "R74 does not claim O3 closure, reroute, or resource savings",
            True,
            {"o3_closed": False, "reroute_allowed": False, "resource_saving_claimed": False},
        ),
    ]
    summary = {
        "method": METHOD,
        "status": STATUS,
        "model_status": MODEL_STATUS,
        "source_target_id": TARGET_ID,
        "upstream_target_id": UPSTREAM_TARGET_ID,
        "r73_d1_prefilled": intake_verdict["gates"]["r1_occurrence_delta_source_backed"],
        "r73_intake_accepted": intake_verdict["accepted"],
        "r73_intake_failed_gate_count": intake_verdict["failed_gate_count"],
        "r73_intake_failed_gates": intake_verdict["failed_gates"],
        "source_line1381": source_line_1381,
        "candidate_line1381": candidate_line_1381,
        "source_cnot_count": source_cnot_count,
        "candidate_cnot_count": candidate_cnot_count,
        "structural_cnot_delta": artifact["structural_cnot_delta"],
        "accepted_exit_route_count": 0,
        "accepted_occurrence_removal": 0,
        "accepted_proxy_t_reduction": 0,
        "b7_nonzero_retest_allowed": False,
        "b7_credit_delta": 0,
        "o3_closed": False,
        "reroute_allowed": False,
        "resource_saving_claimed": False,
        "b7_ledger_improvement_claimed": False,
        "artifact_hash": artifact["artifact_hash"],
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
        "title": "B1/B7 Cone01 R74 R1 Occurrence Packet Prefill Gate",
        "version": VERSION,
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "summary": summary,
        "requirements": requirements,
        "claim_boundary": {
            "what_is_supported": (
                "R74 fills the R73-D1 R1 occurrence packet with hash-bound source, "
                "candidate, replay stdout, and replay verdict artifacts."
            ),
            "what_is_not_supported": (
                "R74 does not close R73, does not accept occurrence/proxy-T deltas, "
                "does not solve line1378 no-double-counting, and does not grant B7 credit."
            ),
            "next_gate": (
                "Fill R73-D2 proxy-T pricing replay and R73-D3 line1378 no-double-counting "
                "or recovery replay, then rerun R73 and R72."
            ),
        },
        "artifacts": {
            "r1_occurrence_artifact": R74_ARTIFACT,
            "r1_occurrence_stdout": R74_STDOUT,
            "r1_occurrence_verdict": R74_VERDICT,
            "r73_submission": R74_SUBMISSION,
            "r73_intake_verdict": R74_INTAKE_VERDICT,
            "blocker_queue": R74_BLOCKER_QUEUE,
        },
    }
    payload["summary"]["payload_hash"] = stable_hash(payload)
    return payload


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    s = payload["summary"]
    lines = [
        "# B1/B7 Cone01 R74 R1 Occurrence Packet Prefill Gate",
        "",
        "## Summary",
        "",
        f"- Status: `{s['status']}`",
        f"- R73-D1 prefilled: `{s['r73_d1_prefilled']}`",
        f"- R73 intake accepted: `{s['r73_intake_accepted']}`",
        f"- R73 failed gates: `{s['r73_intake_failed_gate_count']}`",
        f"- Source line1381: `{s['source_line1381']}`",
        f"- Candidate line1381: `{s['candidate_line1381']}`",
        f"- Structural CNOT delta: `{s['structural_cnot_delta']}`",
        f"- Accepted exit routes: `{s['accepted_exit_route_count']}`",
        f"- Accepted occurrence removal: `{s['accepted_occurrence_removal']}`",
        f"- Accepted proxy-T reduction: `{s['accepted_proxy_t_reduction']}`",
        f"- B7 credit delta: `{s['b7_credit_delta']}`",
        f"- Blocker queue hash: `{s['blocker_queue_hash']}`",
        "",
        "R74 fills the R73-D1 source-backed occurrence packet shape using the existing source/candidate OpenQASM3 artifacts and a replay verdict. It intentionally leaves R73-D2 proxy-T and R73-D3 line1378 no-double-counting open, so the intake remains rejected and all credit stays zero.",
        "",
        "## Remaining Failed Gates",
        "",
    ]
    for gate in s["r73_intake_failed_gates"]:
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
        default="results/B1_B7_cone01_R74_r1_occurrence_packet_prefill_gate_v0.json",
    )
    parser.add_argument(
        "--markdown-output",
        default="research/B1_B7_cone01_R74_r1_occurrence_packet_prefill_gate.md",
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
