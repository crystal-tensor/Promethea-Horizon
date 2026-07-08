#!/usr/bin/env python3
"""T-B1-004ft/T-B7-015c: R70 R1 machine-check replay prefill gate."""

from __future__ import annotations

import argparse
import hashlib
import json
import shlex
import subprocess
import sys
import time
from pathlib import Path
from typing import Any


METHOD = "b1_b7_cone01_r70_machine_check_replay_prefill_gate_v0"
STATUS = "cone01_r70_r1_machine_check_replay_prefill_zero_credit"
MODEL_STATUS = "r69_prefill_machine_check_replay_fields_filled_positive_delta_still_blocked"
VERSION = "0.1"
TARGET_ID = "T-B1-004ft/T-B7-015c"
UPSTREAM_TARGET_ID = "T-B1-004fs/T-B7-015b"
SUBMISSION_DIR = "results/B1_B7_cone01_o3_f4_exit_route_submissions"
R69_PREFILL = f"{SUBMISSION_DIR}/R69-R1-line1381-prefill-source-openqasm3.json"
R70_PREFILL = f"{SUBMISSION_DIR}/R70-R1-line1381-prefill-machine-check-replay.json"
R70_STDOUT = f"{SUBMISSION_DIR}/R70-R1-line1381-machine-check-replay.stdout.txt"
R70_TRANSCRIPT = f"{SUBMISSION_DIR}/R70-R1-line1381-machine-check-replay-transcript.json"
R70_BLOCKER_QUEUE = f"{SUBMISSION_DIR}/R70-positive-delta-blocker-queue.json"
CONTRACT = f"{SUBMISSION_DIR}/R67-accepted-exit-route.contract.json"
R59_RESULT = "results/B1_B7_cone01_R59_o3_f4_c3_same_unitary_replay_certificate_gate_v0.json"
R65_RESULT = "results/B1_B7_cone01_R65_o3_f4_c7_machine_check_replay_gate_v0.json"
R66_RESULT = "results/B1_B7_cone01_R66_o3_f4_b7_zero_credit_ledger_retest_gate_v0.json"


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


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def rel(root: Path, path: Path) -> str:
    return str(path.relative_to(root))


def req(requirement_id: str, label: str, passed: bool, evidence: dict[str, Any]) -> dict[str, Any]:
    return {
        "requirement_id": requirement_id,
        "label": label,
        "passed": bool(passed),
        "evidence": evidence,
    }


def count_prefilled(contract: dict[str, Any], draft: dict[str, Any]) -> tuple[int, list[str]]:
    placeholders = [
        field
        for field in contract["required_submission_fields"]
        if draft.get(field) in (None, "")
    ]
    return len(contract["required_submission_fields"]) - len(placeholders), placeholders


def qasm_header_ok(path: Path) -> bool:
    lines = path.read_text(encoding="utf-8").splitlines()
    return len(lines) >= 2 and lines[0] == "OPENQASM 3.0;" and lines[1] == 'include "stdgates.inc";'


def qasm_op_counts(path: Path) -> dict[str, int]:
    counts: dict[str, int] = {"U": 0, "rz": 0, "cx": 0, "measure": 0}
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if (
            not line
            or line.startswith("//")
            or line.startswith("OPENQASM")
            or line.startswith("include ")
            or line.startswith("qubit[")
            or line.startswith("bit[")
        ):
            continue
        if line.startswith("U("):
            counts["U"] += 1
        elif line.startswith("rz("):
            counts["rz"] += 1
        elif line.startswith("cx "):
            counts["cx"] += 1
        elif "= measure " in line:
            counts["measure"] += 1
        else:
            raise ValueError(f"unparsed OpenQASM3 line in {path}: {line}")
    return counts


def expected_hash_key(path_key: str) -> str:
    return path_key.removesuffix("_path") + "_sha256"


def referenced_file_checks(root: Path, prefill: dict[str, Any]) -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = []
    for key, value in sorted(prefill.items()):
        if not key.endswith("_path") or not isinstance(value, str):
            continue
        expected_key = expected_hash_key(key)
        expected_hash = prefill.get(expected_key)
        if not isinstance(expected_hash, str):
            continue
        path = root / value
        actual_hash = file_hash(path) if path.exists() else None
        checks.append(
            {
                "field": key,
                "path": value,
                "exists": path.exists(),
                "actual_sha256": actual_hash,
                "expected_sha256": expected_hash,
                "hash_matches": actual_hash == expected_hash,
            }
        )
    return checks


def replay_transcript(root: Path, prefill_path: Path) -> dict[str, Any]:
    prefill = load_json(prefill_path)
    contract = load_json(root / CONTRACT)
    r59 = load_json(root / R59_RESULT)
    r65 = load_json(root / R65_RESULT)
    r66 = load_json(root / R66_RESULT)

    source_qasm = root / prefill["source_openqasm3_path"]
    candidate_qasm = root / prefill["candidate_openqasm3_path"]
    source_counts = qasm_op_counts(source_qasm)
    candidate_counts = qasm_op_counts(candidate_qasm)
    file_checks = referenced_file_checks(root, prefill)
    r69_prefilled_count, r69_placeholders = count_prefilled(contract, prefill)
    source_hash = file_hash(source_qasm)
    candidate_hash = file_hash(candidate_qasm)

    replay_checks = {
        "contract_hash_matches": prefill["contract_hash"] == contract["contract_hash"],
        "source_r66_packet_hash_matches": (
            prefill["source_r66_retest_packet_hash"]
            == r66["summary"]["r66_retest_packet_hash"]
            == contract["source_r66_retest_packet_hash"]
        ),
        "source_openqasm3_hash_matches": source_hash == prefill["source_openqasm3_sha256"],
        "candidate_openqasm3_hash_matches": (
            candidate_hash == prefill["candidate_openqasm3_sha256"]
        ),
        "source_openqasm3_header_ok": qasm_header_ok(source_qasm),
        "candidate_openqasm3_header_ok": qasm_header_ok(candidate_qasm),
        "referenced_file_hashes_match": all(item["hash_matches"] for item in file_checks),
        "r59_same_unitary_certificate_complete": (
            r59["summary"]["c3_same_unitary_replay_certificate_complete"] is True
            and r59["summary"]["positive_replay_passed_count"] == 8
            and r59["summary"]["negative_control_rejected_count"] == 8
        ),
        "r65_machine_check_complete": (
            r65["summary"]["c7_machine_check_replay_complete"] is True
            and r65["summary"]["passed_verdict_count"] == 8
            and r65["summary"]["failed_verdict_count"] == 0
            and r65["summary"]["all_replay_commands_exit_zero"] is True
        ),
        "r66_zero_credit_boundary_complete": (
            r66["summary"]["ledger_retest_boundary_complete"] is True
            and r66["summary"]["accepted_exit_route_count"] == 0
            and r66["summary"]["accepted_occurrence_removal"] == 0
            and r66["summary"]["accepted_proxy_t_reduction"] == 0
            and r66["summary"]["b7_credit_delta"] == 0
        ),
        "r69_has_exactly_three_machine_replay_placeholders": (
            r69_prefilled_count == 26
            and r69_placeholders
            == [
                "machine_check_replay_command",
                "machine_check_replay_stdout_path",
                "machine_check_replay_stdout_sha256",
            ]
        ),
    }
    structural_deltas = {
        "source_counts": source_counts,
        "candidate_counts": candidate_counts,
        "cx_delta_source_minus_candidate": source_counts["cx"] - candidate_counts["cx"],
        "u_delta_candidate_minus_source": candidate_counts["U"] - source_counts["U"],
        "rz_delta_candidate_minus_source": candidate_counts["rz"] - source_counts["rz"],
        "measure_delta": candidate_counts["measure"] - source_counts["measure"],
    }
    replay_passed = all(replay_checks.values())
    transcript = {
        "artifact": "R70 R1 line1381 machine-check replay transcript",
        "method": METHOD,
        "source_target_id": TARGET_ID,
        "upstream_target_id": UPSTREAM_TARGET_ID,
        "prefill_input": rel(root, prefill_path),
        "route_id": prefill["route_id"],
        "route_class": "line1381_resolution_machine_replay_prefilled_not_accepted",
        "source_openqasm3_path": prefill["source_openqasm3_path"],
        "source_openqasm3_sha256": source_hash,
        "candidate_openqasm3_path": prefill["candidate_openqasm3_path"],
        "candidate_openqasm3_sha256": candidate_hash,
        "contract_hash": contract["contract_hash"],
        "source_r66_retest_packet_hash": r66["summary"]["r66_retest_packet_hash"],
        "r59_bundle_hash": r59["summary"]["r59_bundle_hash"],
        "r65_bundle_hash": r65["summary"]["r65_bundle_hash"],
        "r66_retest_packet_hash": r66["summary"]["r66_retest_packet_hash"],
        "r69_prefilled_field_count": r69_prefilled_count,
        "r69_placeholder_fields": r69_placeholders,
        "structural_deltas": structural_deltas,
        "referenced_file_checks": file_checks,
        "replay_checks": replay_checks,
        "machine_check_replay_passed": replay_passed,
        "accepted_exit_route_count": 0,
        "occurrence_removal_delta": 0,
        "proxy_t_reduction_delta": 0,
        "b7_nonzero_retest_requested": False,
        "b7_credit_delta": 0,
        "claim_boundary": (
            "R70 supplies a machine-check replay stdout/hash for the R1 line1381 "
            "submission prefill by binding source/candidate OpenQASM3 artifacts "
            "and the R59/R65/R66 evidence chain. It does not accept the route, "
            "does not provide positive occurrence/proxy-T deltas, and does not "
            "grant B7 credit."
        ),
    }
    transcript["transcript_hash"] = stable_hash(transcript)
    return transcript


def run_replay_command(root: Path, command: list[str], stdout_path: Path) -> dict[str, Any]:
    started = time.time()
    proc = subprocess.run(
        command,
        cwd=root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    runtime = round(time.time() - started, 6)
    write_text(stdout_path, proc.stdout)
    return {
        "returncode": proc.returncode,
        "stderr": proc.stderr,
        "runtime_seconds": runtime,
        "stdout_path": rel(root, stdout_path),
        "stdout_sha256": file_hash(stdout_path),
    }


def build_payload(args: argparse.Namespace) -> dict[str, Any]:
    root = Path(args.repo_root).resolve()
    contract = load_json(root / CONTRACT)
    r69_prefill_path = root / R69_PREFILL
    r69_prefill = load_json(r69_prefill_path)
    r69_count, r69_placeholders = count_prefilled(contract, r69_prefill)

    replay_command_parts = [
        "python3",
        "tools/b1_b7_cone01_r70_machine_check_replay_prefill_gate.py",
        "--repo-root",
        ".",
        "--replay-only",
        "--prefill",
        R69_PREFILL,
    ]
    replay_result = run_replay_command(root, replay_command_parts, root / R70_STDOUT)
    replay_stdout = (root / R70_STDOUT).read_text(encoding="utf-8")
    replay_payload = json.loads(replay_stdout)
    write_json(root / R70_TRANSCRIPT, replay_payload)

    r70_prefill = dict(r69_prefill)
    r70_prefill.update(
        {
            "template_id": "B1-B7-cone01-R70-R1-line1381-prefill-machine-check-replay",
            "source_target_id": TARGET_ID,
            "upstream_target_id": UPSTREAM_TARGET_ID,
            "route_class": "line1381_resolution_machine_replay_prefilled_not_accepted",
            "machine_check_replay_command": " ".join(
                shlex.quote(part) for part in replay_command_parts
            ),
            "machine_check_replay_stdout_path": R70_STDOUT,
            "machine_check_replay_stdout_sha256": replay_result["stdout_sha256"],
            "claim_boundary": (
                "R70 fills the machine-check replay command/stdout/hash fields "
                "for the R1 line1381 route prefill. It keeps accepted_exit_route_count=0, "
                "occurrence_removal_delta=0, proxy_t_reduction_delta=0, "
                "b7_nonzero_retest_requested=false, and B7 credit=0 because no positive "
                "delta ledger has been accepted."
            ),
        }
    )
    r70_prefill["prefill_hash"] = stable_hash(r70_prefill)
    write_json(root / R70_PREFILL, r70_prefill)
    r70_count, r70_placeholders = count_prefilled(contract, r70_prefill)

    blocker_queue = {
        "artifact": "R70 positive-delta blocker queue",
        "source_target_id": TARGET_ID,
        "upstream_target_id": UPSTREAM_TARGET_ID,
        "selected_next_route": "R1-line1381-resolution",
        "resolved_fields": [
            "machine_check_replay_command",
            "machine_check_replay_stdout_path",
            "machine_check_replay_stdout_sha256",
        ],
        "remaining_placeholder_fields": r70_placeholders,
        "acceptance_blockers": [
            {
                "blocker_id": "R70-B1",
                "priority": 1,
                "blocked_acceptance_rule": "occurrence_removal_delta and proxy_t_reduction_delta are positive",
                "current_values": {
                    "accepted_exit_route_count": r70_prefill["accepted_exit_route_count"],
                    "occurrence_removal_delta": r70_prefill["occurrence_removal_delta"],
                    "proxy_t_reduction_delta": r70_prefill["proxy_t_reduction_delta"],
                },
                "needed_artifact": "positive occurrence and proxy-T delta ledger accepted by the R67 contract",
            },
            {
                "blocker_id": "R70-B2",
                "priority": 2,
                "blocked_acceptance_rule": "B7 ledger retest only after nonzero accepted deltas",
                "current_values": {
                    "b7_nonzero_retest_requested": r70_prefill["b7_nonzero_retest_requested"],
                    "b7_credit_delta": 0,
                },
                "needed_artifact": "downstream B7 nonzero retest after an accepted positive delta route",
            },
        ],
    }
    blocker_queue["blocker_queue_hash"] = stable_hash(blocker_queue)
    write_json(root / R70_BLOCKER_QUEUE, blocker_queue)

    referenced_checks = replay_payload["referenced_file_checks"]
    structural = replay_payload["structural_deltas"]
    requirements = [
        req(
            "R1",
            "R69 input has exactly the three machine-check replay placeholders",
            r69_count == 26
            and r69_placeholders
            == [
                "machine_check_replay_command",
                "machine_check_replay_stdout_path",
                "machine_check_replay_stdout_sha256",
            ],
            {"r69_prefilled_field_count": r69_count, "r69_placeholder_fields": r69_placeholders},
        ),
        req(
            "R2",
            "replay command exits cleanly and emits hash-bound stdout",
            replay_result["returncode"] == 0 and replay_payload["machine_check_replay_passed"] is True,
            {
                "returncode": replay_result["returncode"],
                "stdout_path": replay_result["stdout_path"],
                "stdout_sha256": replay_result["stdout_sha256"],
                "transcript_hash": replay_payload["transcript_hash"],
            },
        ),
        req(
            "R3",
            "R70 prefill has no placeholder fields",
            r70_count == len(contract["required_submission_fields"]) and r70_placeholders == [],
            {"r70_prefilled_field_count": r70_count, "r70_placeholder_fields": r70_placeholders},
        ),
        req(
            "R4",
            "source and candidate OpenQASM3 artifacts are hash-bound",
            replay_payload["replay_checks"]["source_openqasm3_hash_matches"]
            and replay_payload["replay_checks"]["candidate_openqasm3_hash_matches"]
            and replay_payload["replay_checks"]["source_openqasm3_header_ok"]
            and replay_payload["replay_checks"]["candidate_openqasm3_header_ok"],
            {
                "source_openqasm3_sha256": replay_payload["source_openqasm3_sha256"],
                "candidate_openqasm3_sha256": replay_payload["candidate_openqasm3_sha256"],
            },
        ),
        req(
            "R5",
            "all referenced evidence files match submitted hashes",
            all(item["hash_matches"] for item in referenced_checks),
            {"checked_file_count": len(referenced_checks)},
        ),
        req(
            "R6",
            "R59/R65/R66 evidence chain is complete but zero-credit",
            replay_payload["replay_checks"]["r59_same_unitary_certificate_complete"]
            and replay_payload["replay_checks"]["r65_machine_check_complete"]
            and replay_payload["replay_checks"]["r66_zero_credit_boundary_complete"],
            {
                "r59_bundle_hash": replay_payload["r59_bundle_hash"],
                "r65_bundle_hash": replay_payload["r65_bundle_hash"],
                "r66_retest_packet_hash": replay_payload["r66_retest_packet_hash"],
            },
        ),
        req(
            "R7",
            "structural candidate CNOT reduction is detected but not accepted as a route",
            structural["cx_delta_source_minus_candidate"] == 6
            and r70_prefill["accepted_exit_route_count"] == 0,
            {
                "source_counts": structural["source_counts"],
                "candidate_counts": structural["candidate_counts"],
                "cx_delta_source_minus_candidate": structural["cx_delta_source_minus_candidate"],
            },
        ),
        req(
            "R8",
            "positive route deltas and B7 credit remain blocked",
            r70_prefill["accepted_exit_route_count"] == 0
            and r70_prefill["occurrence_removal_delta"] == 0
            and r70_prefill["proxy_t_reduction_delta"] == 0
            and r70_prefill["b7_nonzero_retest_requested"] is False,
            {
                "accepted_exit_route_count": r70_prefill["accepted_exit_route_count"],
                "occurrence_removal_delta": r70_prefill["occurrence_removal_delta"],
                "proxy_t_reduction_delta": r70_prefill["proxy_t_reduction_delta"],
                "b7_nonzero_retest_requested": r70_prefill["b7_nonzero_retest_requested"],
            },
        ),
        req(
            "R9",
            "remaining blocker queue is positive-delta only",
            r70_placeholders == [] and len(blocker_queue["acceptance_blockers"]) == 2,
            {"blocker_queue_hash": blocker_queue["blocker_queue_hash"]},
        ),
        req("R10", "R70 artifacts are written", True, {}),
    ]
    summary = {
        "method": METHOD,
        "status": STATUS,
        "model_status": MODEL_STATUS,
        "source_target_id": TARGET_ID,
        "upstream_target_id": UPSTREAM_TARGET_ID,
        "r69_prefilled_field_count": r69_count,
        "r69_placeholder_field_count": len(r69_placeholders),
        "r69_placeholder_fields": r69_placeholders,
        "r70_prefilled_field_count": r70_count,
        "r70_placeholder_field_count": len(r70_placeholders),
        "r70_placeholder_fields": r70_placeholders,
        "resolved_placeholder_field_count": 3,
        "machine_check_replay_command": r70_prefill["machine_check_replay_command"],
        "machine_check_replay_stdout_path": R70_STDOUT,
        "machine_check_replay_stdout_sha256": replay_result["stdout_sha256"],
        "machine_check_replay_transcript_path": R70_TRANSCRIPT,
        "machine_check_replay_transcript_sha256": file_hash(root / R70_TRANSCRIPT),
        "machine_check_replay_passed": replay_payload["machine_check_replay_passed"],
        "source_openqasm3_sha256": replay_payload["source_openqasm3_sha256"],
        "candidate_openqasm3_sha256": replay_payload["candidate_openqasm3_sha256"],
        "source_operation_counts": structural["source_counts"],
        "candidate_operation_counts": structural["candidate_counts"],
        "cx_delta_source_minus_candidate": structural["cx_delta_source_minus_candidate"],
        "accepted_exit_route_count": 0,
        "accepted_occurrence_removal": 0,
        "accepted_proxy_t_reduction": 0,
        "b7_nonzero_retest_allowed": False,
        "b7_credit_delta": 0,
        "o3_closed": False,
        "reroute_allowed": False,
        "resource_saving_claimed": False,
        "b7_ledger_improvement_claimed": False,
        "r70_prefill_hash": r70_prefill["prefill_hash"],
        "r70_prefill_file_sha256": file_hash(root / R70_PREFILL),
        "blocker_queue_hash": blocker_queue["blocker_queue_hash"],
        "blocker_queue_file_sha256": file_hash(root / R70_BLOCKER_QUEUE),
        "requirement_count": len(requirements),
        "requirements_passed": sum(1 for item in requirements if item["passed"]),
        "requirements_failed": sum(1 for item in requirements if not item["passed"]),
        "failed_requirement_ids": [
            item["requirement_id"] for item in requirements if not item["passed"]
        ],
        "validation_error_count": sum(1 for item in requirements if not item["passed"]),
    }
    payload = {
        "title": "B1/B7 Cone01 R70 Machine-Check Replay Prefill Gate",
        "version": VERSION,
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "summary": summary,
        "requirements": requirements,
        "replay_transcript": replay_payload,
        "claim_boundary": {
            "what_is_supported": (
                "R70 fills the machine-check replay command/stdout/hash fields "
                "for the R1 line1381 prefill and binds source/candidate OpenQASM3 "
                "plus the R59/R65/R66 evidence chain."
            ),
            "what_is_not_supported": (
                "R70 does not accept an exit route, does not provide positive "
                "occurrence/proxy-T delta evidence, does not close O3, does not "
                "allow reroute, and does not grant B7 credit."
            ),
            "next_gate": (
                "Produce a positive occurrence/proxy-T delta ledger that survives "
                "the R67 accepted-exit-route contract."
            ),
        },
        "artifacts": {
            "completed_prefill": R70_PREFILL,
            "machine_check_replay_stdout": R70_STDOUT,
            "machine_check_replay_transcript": R70_TRANSCRIPT,
            "blocker_queue": R70_BLOCKER_QUEUE,
        },
    }
    payload["summary"]["payload_hash"] = stable_hash(payload)
    return payload


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    s = payload["summary"]
    lines = [
        "# B1/B7 Cone01 R70 Machine-Check Replay Prefill Gate",
        "",
        "## Summary",
        "",
        f"- Status: `{s['status']}`",
        f"- R69 prefilled fields: `{s['r69_prefilled_field_count']}` / 29",
        f"- R70 prefilled fields: `{s['r70_prefilled_field_count']}` / 29",
        f"- Remaining placeholder fields: `{s['r70_placeholder_field_count']}`",
        f"- Machine-check replay stdout: `{s['machine_check_replay_stdout_path']}`",
        f"- Machine-check replay stdout SHA256: `{s['machine_check_replay_stdout_sha256']}`",
        f"- Source CNOT count: `{s['source_operation_counts']['cx']}`",
        f"- Candidate CNOT count: `{s['candidate_operation_counts']['cx']}`",
        f"- Structural CNOT delta: `{s['cx_delta_source_minus_candidate']}`",
        f"- Accepted exit routes: `{s['accepted_exit_route_count']}`",
        f"- Accepted occurrence removal: `{s['accepted_occurrence_removal']}`",
        f"- Accepted proxy-T reduction: `{s['accepted_proxy_t_reduction']}`",
        f"- B7 credit delta: `{s['b7_credit_delta']}`",
        f"- R70 blocker queue hash: `{s['blocker_queue_hash']}`",
        "",
        "R70 fills the three machine-check replay fields left open by R69. The R1 line1381 prefill now has 29 of 29 required fields populated, but it remains unaccepted because the positive occurrence/proxy-T delta rule is still unsatisfied.",
        "",
        "## Requirements",
        "",
    ]
    for item in payload["requirements"]:
        status = "PASS" if item["passed"] else "FAIL"
        lines.append(f"- `{item['requirement_id']}` {status}: {item['label']}")
    lines.extend(
        [
            "",
            "## Remaining Acceptance Blockers",
            "",
            "- Positive occurrence-removal delta accepted by the R67 contract.",
            "- Positive proxy-T delta accepted by the R67 contract.",
            "- Downstream B7 nonzero retest after a positive accepted route.",
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
    parser.add_argument("--prefill", default=R69_PREFILL)
    parser.add_argument("--replay-only", action="store_true")
    parser.add_argument(
        "--json-output",
        default="results/B1_B7_cone01_R70_machine_check_replay_prefill_gate_v0.json",
    )
    parser.add_argument(
        "--markdown-output",
        default="research/B1_B7_cone01_R70_machine_check_replay_prefill_gate.md",
    )
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()

    root = Path(args.repo_root).resolve()
    if args.replay_only:
        transcript = replay_transcript(root, root / args.prefill)
        print(json.dumps(transcript, indent=2, sort_keys=True))
        return

    payload = build_payload(args)
    json_path = root / args.json_output
    md_path = root / args.markdown_output
    write_json(json_path, payload)
    write_markdown(md_path, payload)
    if args.pretty:
        print(json.dumps(payload["summary"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
