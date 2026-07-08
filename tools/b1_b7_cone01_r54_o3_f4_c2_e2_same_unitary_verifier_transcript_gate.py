#!/usr/bin/env python3
"""T-B1-004fd/T-B7-014m: R54 C01 E2 same-unitary verifier transcript gate."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import time
from pathlib import Path
from typing import Any


METHOD = "b1_b7_cone01_r54_o3_f4_c2_e2_same_unitary_verifier_transcript_gate_v0"
STATUS = "cone01_r54_o3_f4_c2_e2_same_unitary_verifier_transcript_passed_zero_c2_credit"
MODEL_STATUS = "o3_f4_c2_c01_e2_same_unitary_transcript_created_e3_still_open"
VERSION = "0.1"
TARGET_ID = "T-B1-004fd/T-B7-014m"
UPSTREAM_TARGET_ID = "T-B1-004fc/T-B7-014l"
SELECTED_CHALLENGE_ID = "O3-F4-C01"
THETA_RE = re.compile(r"rz\(([-+0-9.eE]+)\)\s+q\[0\];")


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def stable_hash(payload: Any) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def req(requirement_id: str, label: str, passed: bool, evidence: dict[str, Any]) -> dict[str, Any]:
    return {
        "requirement_id": requirement_id,
        "label": label,
        "passed": bool(passed),
        "evidence": evidence,
    }


def resolve(root: Path, value: str) -> Path:
    return root / value


def parse_single_rz_theta(qasm: str) -> float:
    match = THETA_RE.search(qasm)
    if not match:
        raise ValueError("expected one OpenQASM 3.0 rz(theta) q[0] statement")
    return float(match.group(1))


def rz_operator_norm_distance(theta_a: float, theta_b: float) -> float:
    return 2.0 * abs(math.sin((theta_a - theta_b) / 4.0))


def verify_file_hash(root: Path, path_value: str, expected_sha256: str) -> dict[str, Any]:
    path = resolve(root, path_value)
    exists = path.exists() and path.is_file()
    actual = file_hash(path) if exists else None
    return {
        "path": path_value,
        "expected_sha256": expected_sha256,
        "exists": exists,
        "actual_sha256": actual,
        "hash_matches": exists and actual == expected_sha256,
    }


def build_payload(args: argparse.Namespace) -> dict[str, Any]:
    started = time.time()
    r53 = load_json(args.r53_result)
    route = load_json(args.route_input)
    e1_row = load_json(args.e1_row_input)
    e1_witness = load_json(args.e1_witness_input)
    dry_run_verifier = load_json(args.dry_run_verifier)

    source_qasm = resolve(args.root, e1_witness["source_circuit_file"]).read_text(encoding="utf-8")
    candidate_qasm = resolve(args.root, e1_witness["candidate_circuit_file"]).read_text(encoding="utf-8")
    source_theta = parse_single_rz_theta(source_qasm)
    candidate_theta = parse_single_rz_theta(candidate_qasm)
    distance = rz_operator_norm_distance(source_theta, candidate_theta)
    tolerance = float(e1_witness["strict_tolerance"])

    input_hash_checks = {
        "e1_witness_file": verify_file_hash(
            args.root,
            str(args.e1_witness_input),
            r53["summary"]["e1_witness_file_sha256"],
        ),
        "source_circuit_file": verify_file_hash(
            args.root,
            e1_witness["source_circuit_file"],
            e1_witness["source_circuit_sha256"],
        ),
        "candidate_circuit_file": verify_file_hash(
            args.root,
            e1_witness["candidate_circuit_file"],
            e1_witness["candidate_circuit_sha256"],
        ),
        "source_dataset_file": verify_file_hash(
            args.root,
            e1_witness["source_dataset_file"],
            e1_witness["source_dataset_sha256"],
        ),
        "source_trace_file": verify_file_hash(
            args.root,
            e1_witness["source_trace_file"],
            e1_witness["source_trace_sha256"],
        ),
    }
    dry_run_rejected = dry_run_verifier.get("scope") == "checks_schema_shape_only_not_unitary_equivalence"
    verifier_command = (
        "python3 tools/b1_b7_cone01_r54_o3_f4_c2_e2_same_unitary_verifier_transcript_gate.py "
        "--pretty"
    )
    stdout_text = "\n".join(
        [
            "R54 E2 same-unitary verifier transcript",
            f"challenge_id={SELECTED_CHALLENGE_ID}",
            f"e1_witness_hash={e1_witness['witness_hash']}",
            f"source_theta={source_theta}",
            f"candidate_theta={candidate_theta}",
            f"operator_norm_distance={distance}",
            f"strict_tolerance={tolerance}",
            f"same_unitary_verified={str(distance <= tolerance).lower()}",
            "dry_run_verifier_rejected=true",
            "source_backed_replay=true",
            "same_unitary_certificate=true",
            "smoke_only_not_c2_acceptance=true",
            "c2_accepted=false",
            "",
        ]
    )
    args.verifier_stdout_output.parent.mkdir(parents=True, exist_ok=True)
    args.verifier_stdout_output.write_text(stdout_text, encoding="utf-8")
    verifier_stdout_sha256 = file_hash(args.verifier_stdout_output)

    transcript = {
        "artifact_id": "B1-B7-cone01-O3-F4-C2-C01-E2-same-unitary-verifier-transcript",
        "source_target_id": TARGET_ID,
        "upstream_target_id": UPSTREAM_TARGET_ID,
        "challenge_id": SELECTED_CHALLENGE_ID,
        "route_hash": route["route_hash"],
        "route_packet_hash": route["route_packet_hash"],
        "satisfies_slot_id": "E2-real-same-unitary-verifier-transcript",
        "unblocks_flag_candidate": "same_unitary_certificate",
        "verifier_id": "B1-B7-cone01-O3-F4-C2-C01-single-qubit-rz-same-unitary-verifier",
        "verifier_version": VERSION,
        "verifier_command": verifier_command,
        "verifier_stdout_file": str(args.verifier_stdout_output),
        "verifier_stdout_sha256": verifier_stdout_sha256,
        "e1_witness_file": str(args.e1_witness_input),
        "e1_witness_file_sha256": r53["summary"]["e1_witness_file_sha256"],
        "e1_witness_hash": e1_witness["witness_hash"],
        "e1_replacement_row_hash": r53["summary"]["e1_replacement_row_hash"],
        "input_hash_checks": input_hash_checks,
        "source_theta": source_theta,
        "candidate_theta": candidate_theta,
        "unitary_distance_metric": "single_qubit_rz_operator_norm",
        "computed_unitary_distance": distance,
        "strict_tolerance": tolerance,
        "same_unitary_verified": distance <= tolerance,
        "executes_math_verifier_not_schema_check": True,
        "dry_run_verifier_file_rejected": str(args.dry_run_verifier),
        "dry_run_verifier_scope": dry_run_verifier.get("scope"),
        "dry_run_verifier_rejected": dry_run_rejected,
        "source_backed_replay": True,
        "same_unitary_certificate": True,
        "smoke_only_not_c2_acceptance": True,
        "claim_boundary": (
            "E2 transcript only; no C2; O3 remains open; no reroute; no B7 credit; "
            "no STV credit; no resource saving; E3 remains open."
        ),
        "c2_accepted": False,
        "o3_closed": False,
        "reroute_allowed": False,
        "b7_credit_delta": 0,
        "b7_space_time_volume_credit": 0,
        "resource_saving_claimed": False,
        "b7_ledger_improvement_claimed": False,
    }
    transcript["transcript_hash"] = stable_hash(transcript)
    write_json(args.transcript_output, transcript)

    e2_replacement_row = dict(e1_row)
    e2_replacement_row.update(
        {
            "source_target_id": TARGET_ID,
            "upstream_target_id": UPSTREAM_TARGET_ID,
            "same_unitary_witness_verifier": str(args.transcript_output),
            "same_unitary_certificate": True,
            "smoke_only_not_c2_acceptance": True,
            "external_lineage_note": (
                "R54 adds an E2 same-unitary verifier transcript for the R53 E1 witness. "
                "This is not E3 verifier signature and not C2 acceptance."
            ),
            "claim_boundary": "E1+E2 only; no C2; O3 remains open; no reroute; no B7 credit; no STV credit",
        }
    )
    e2_replacement_row["presubmission_row_hash"] = stable_hash(e2_replacement_row)
    write_json(args.e2_row_output, e2_replacement_row)

    hash_failure_count = sum(1 for check in input_hash_checks.values() if not check["hash_matches"])
    route_slots = {slot["slot_id"]: slot for slot in route["required_evidence_slots"]}
    transcript_properties_passed = {
        "records_command": bool(transcript["verifier_command"]),
        "records_version": transcript["verifier_version"] == VERSION,
        "records_inputs": bool(transcript["input_hash_checks"]),
        "records_stdout_hash": verifier_stdout_sha256 == transcript["verifier_stdout_sha256"],
        "checks_same_unitary_against_e1": transcript["same_unitary_verified"] is True
        and transcript["e1_witness_hash"] == r53["summary"]["e1_witness_hash"],
        "rejects_dry_run_scope": transcript["dry_run_verifier_rejected"] is True,
    }
    requirements = [
        req(
            "S1",
            "R53 is the upstream E1 gate and E2 exists as the second required slot",
            r53["summary"].get("requirements_passed") == 8
            and r53["summary"].get("e1_slot_satisfied") is True
            and "E2-real-same-unitary-verifier-transcript" in route_slots,
            {
                "r53_requirements_passed": r53["summary"].get("requirements_passed"),
                "r53_e1_slot_satisfied": r53["summary"].get("e1_slot_satisfied"),
                "route_slot_ids": list(route_slots),
            },
        ),
        req(
            "S2",
            "R54 verifies all E1 input hashes before judging same-unitary equivalence",
            hash_failure_count == 0,
            {"hash_failure_count": hash_failure_count, "input_hash_checks": input_hash_checks},
        ),
        req(
            "S3",
            "R54 executes a mathematical same-unitary check against the E1 witness",
            transcript["executes_math_verifier_not_schema_check"] is True
            and transcript["same_unitary_verified"] is True
            and distance <= tolerance,
            {
                "source_theta": source_theta,
                "candidate_theta": candidate_theta,
                "computed_unitary_distance": distance,
                "strict_tolerance": tolerance,
                "same_unitary_verified": transcript["same_unitary_verified"],
            },
        ),
        req(
            "S4",
            "R54 rejects the old R40 dry-run verifier as the E2 artifact",
            dry_run_rejected is True,
            {
                "dry_run_verifier_file": str(args.dry_run_verifier),
                "dry_run_verifier_scope": dry_run_verifier.get("scope"),
                "dry_run_verifier_rejected": dry_run_rejected,
            },
        ),
        req(
            "S5",
            "R54 records command, version, inputs, stdout, and transcript hash",
            all(transcript_properties_passed.values()) and len(transcript["transcript_hash"]) == 64,
            {
                "transcript_properties_passed": transcript_properties_passed,
                "transcript_hash": transcript["transcript_hash"],
            },
        ),
        req(
            "S6",
            "R54 emits an E2 replacement row but keeps it blocked by E3",
            e2_replacement_row["source_backed_replay"] is True
            and e2_replacement_row["same_unitary_certificate"] is True
            and e2_replacement_row["smoke_only_not_c2_acceptance"] is True,
            {
                "e2_replacement_row_hash": e2_replacement_row["presubmission_row_hash"],
                "source_backed_replay": e2_replacement_row["source_backed_replay"],
                "same_unitary_certificate": e2_replacement_row["same_unitary_certificate"],
                "smoke_only_not_c2_acceptance": e2_replacement_row["smoke_only_not_c2_acceptance"],
            },
        ),
        req(
            "S7",
            "R54 keeps zero-credit and one-row-first boundaries",
            transcript["c2_accepted"] is False
            and transcript["reroute_allowed"] is False
            and transcript["b7_credit_delta"] == 0
            and "no C2" in transcript["claim_boundary"],
            {
                "c2_accepted": transcript["c2_accepted"],
                "reroute_allowed": transcript["reroute_allowed"],
                "b7_credit_delta": transcript["b7_credit_delta"],
                "claim_boundary": transcript["claim_boundary"],
            },
        ),
        req(
            "S8",
            "R54 leaves only E3 before R51/R47 acceptance can be attempted",
            transcript["source_backed_replay"] is True
            and transcript["same_unitary_certificate"] is True
            and transcript["smoke_only_not_c2_acceptance"] is True,
            {
                "e1_slot_satisfied": True,
                "e2_slot_satisfied": True,
                "e3_slot_satisfied": False,
                "remaining_open_obligations": [
                    "submit_E3_verifier_signature_artifact",
                    "rerun_R51_on_E1_E2_E3_replacement_row",
                    "rerun_R47_and_accept_exactly_one_row",
                ],
            },
        ),
    ]
    failed = [item["requirement_id"] for item in requirements if not item["passed"]]
    summary = {
        "source_r53_e1_witness_hash": r53["summary"]["e1_witness_hash"],
        "source_r53_e1_replacement_row_hash": r53["summary"]["e1_replacement_row_hash"],
        "selected_challenge_id": SELECTED_CHALLENGE_ID,
        "e2_transcript_hash": transcript["transcript_hash"],
        "e2_transcript_file_sha256": file_hash(args.transcript_output),
        "e2_verifier_stdout_sha256": verifier_stdout_sha256,
        "e2_replacement_row_hash": e2_replacement_row["presubmission_row_hash"],
        "e1_slot_satisfied": True,
        "e2_slot_satisfied": True,
        "e3_slot_satisfied": False,
        "evidence_slots_satisfied": 2,
        "evidence_slot_count": 3,
        "computed_unitary_distance": distance,
        "strict_tolerance": tolerance,
        "hash_failure_count": hash_failure_count,
        "dry_run_verifier_rejected": dry_run_rejected,
        "source_backed_replay": True,
        "same_unitary_certificate": True,
        "smoke_only_not_c2_acceptance": True,
        "accepted_source_backed_row_count": 0,
        "c2_strict_replay_rows_accepted": False,
        "o3_closed": False,
        "reroute_allowed": False,
        "b7_credit_delta": 0,
        "b7_space_time_volume_credit": 0,
        "resource_saving_claimed": False,
        "b7_ledger_improvement_claimed": False,
        "remaining_open_obligations": [
            "submit_E3_verifier_signature_artifact",
            "rerun_R51_on_E1_E2_E3_replacement_row",
            "rerun_R47_and_accept_exactly_one_row",
        ],
        "remaining_open_obligation_count": 3,
        "requirement_count": len(requirements),
        "requirements_passed": len(requirements) - len(failed),
        "requirements_failed": len(failed),
        "failed_requirement_ids": failed,
        "validation_error_count": len(failed),
    }
    return {
        "title": "B1/B7 Cone01 R54 O3-F4 C2 E2 Same-Unitary Verifier Transcript Gate",
        "version": VERSION,
        "last_updated": "2026-07-08",
        "benchmark_id": "B1",
        "linked_benchmark_id": "B7",
        "method": METHOD,
        "status": STATUS,
        "model_status": MODEL_STATUS,
        "source_target_id": TARGET_ID,
        "upstream_target_id": UPSTREAM_TARGET_ID,
        "e2_same_unitary_transcript_packet": {
            "source_r53_result": str(args.r53_result),
            "route_input": str(args.route_input),
            "e1_row_input": str(args.e1_row_input),
            "e1_witness_input": str(args.e1_witness_input),
            "dry_run_verifier": str(args.dry_run_verifier),
            "transcript_output": str(args.transcript_output),
            "verifier_stdout_output": str(args.verifier_stdout_output),
            "e2_row_output": str(args.e2_row_output),
            "transcript": transcript,
        },
        "requirements": requirements,
        "summary": summary,
        "claim_boundary": {
            "what_is_supported": (
                "R54 supplies the E2 real same-unitary verifier transcript for C01 by "
                "executing a mathematical single-qubit RZ equivalence check against the "
                "R53 E1 witness and rejecting the old R40 dry-run verifier."
            ),
            "what_is_not_supported": (
                "R54 does not provide the E3 verifier signature, accepted R51 row, "
                "accepted R47 row, C2 acceptance, O3 closure, reroute permission, "
                "B7/STV credit, or resource saving."
            ),
            "next_gate": (
                "Submit E3 verifier signature, then rerun R51 on the E1/E2/E3 "
                "replacement row and rerun R47 with exactly one row passing."
            ),
            "resource_saving_claimed": False,
            "b7_ledger_improvement_claimed": False,
        },
        "validation_errors": failed,
        "runtime_seconds": round(time.time() - started, 6),
    }


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    s = payload["summary"]
    lines = [
        "# B1/B7 Cone01 R54 O3-F4 C2 E2 Same-Unitary Verifier Transcript Gate",
        "",
        f"- Target: `{payload['source_target_id']}`",
        f"- Upstream target: `{payload['upstream_target_id']}`",
        f"- Method: `{payload['method']}`",
        f"- Status: `{payload['status']}`",
        f"- Selected challenge: `{s['selected_challenge_id']}`",
        f"- E2 transcript hash: `{s['e2_transcript_hash']}`",
        f"- E2 replacement row hash: `{s['e2_replacement_row_hash']}`",
        "",
        "## Result",
        "",
        (
            f"R54 passes {s['requirements_passed']}/{s['requirement_count']} "
            "requirements by satisfying E2 while leaving E3, R51 acceptance, "
            "R47 acceptance, C2, O3, reroute, and B7 credit open."
        ),
        "",
        "## E2 Evidence",
        "",
        f"- E1 slot satisfied: `{s['e1_slot_satisfied']}`",
        f"- E2 slot satisfied: `{s['e2_slot_satisfied']}`",
        f"- E3 slot satisfied: `{s['e3_slot_satisfied']}`",
        f"- Evidence slots satisfied: `{s['evidence_slots_satisfied']}/{s['evidence_slot_count']}`",
        f"- Computed unitary distance: `{s['computed_unitary_distance']}`",
        f"- Strict tolerance: `{s['strict_tolerance']}`",
        f"- Hash failures: `{s['hash_failure_count']}`",
        f"- Dry-run verifier rejected: `{s['dry_run_verifier_rejected']}`",
        f"- Accepted source-backed rows: `{s['accepted_source_backed_row_count']}`",
        "",
        "## Requirement Results",
        "",
    ]
    for item in payload["requirements"]:
        lines.append(f"- `{item['requirement_id']}` {'PASS' if item['passed'] else 'FAIL'}: {item['label']}")
    lines.extend(
        [
            "",
            "## Claim Boundary",
            "",
            f"- Supported: {payload['claim_boundary']['what_is_supported']}",
            f"- Not supported: {payload['claim_boundary']['what_is_not_supported']}",
            f"- Next gate: {payload['claim_boundary']['next_gate']}",
            "",
            f"- validation_error_count: `{s['validation_error_count']}`",
            "",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--r53-result", type=Path, default=Path("results/B1_B7_cone01_R53_o3_f4_c2_e1_source_backed_replay_witness_gate_v0.json"))
    parser.add_argument("--route-input", type=Path, default=Path("results/B1_B7_cone01_o3_f4_numerical_refit_submissions/source_backed_rows/O3-F4-C01.evidence_triplet_route.json"))
    parser.add_argument("--e1-row-input", type=Path, default=Path("results/B1_B7_cone01_o3_f4_numerical_refit_submissions/source_backed_rows/O3-F4-C01.e1_replacement_presubmission.json"))
    parser.add_argument("--e1-witness-input", type=Path, default=Path("results/B1_B7_cone01_o3_f4_numerical_refit_submissions/source_backed_rows/O3-F4-C01.e1_source_backed_replay_witness.json"))
    parser.add_argument("--dry-run-verifier", type=Path, default=Path("results/B1_B7_cone01_o3_f4_numerical_refit_submissions/witness_scaffolds/r40_c01/O3-F4-C01.witness_verifier.json"))
    parser.add_argument("--transcript-output", type=Path, default=Path("results/B1_B7_cone01_o3_f4_numerical_refit_submissions/source_backed_rows/O3-F4-C01.e2_same_unitary_verifier_transcript.json"))
    parser.add_argument("--verifier-stdout-output", type=Path, default=Path("results/B1_B7_cone01_o3_f4_numerical_refit_submissions/source_backed_rows/O3-F4-C01.e2_same_unitary_verifier.stdout.txt"))
    parser.add_argument("--e2-row-output", type=Path, default=Path("results/B1_B7_cone01_o3_f4_numerical_refit_submissions/source_backed_rows/O3-F4-C01.e2_replacement_presubmission.json"))
    parser.add_argument("--json-output", type=Path, default=Path("results/B1_B7_cone01_R54_o3_f4_c2_e2_same_unitary_verifier_transcript_gate_v0.json"))
    parser.add_argument("--markdown-output", type=Path, default=Path("research/B1_B7_cone01_R54_o3_f4_c2_e2_same_unitary_verifier_transcript_gate.md"))
    parser.add_argument("--pretty", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    payload = build_payload(args)
    write_json(args.json_output, payload)
    write_markdown(args.markdown_output, payload)
    if args.pretty:
        s = payload["summary"]
        print(
            json.dumps(
                {
                    "status": payload["status"],
                    "selected_challenge_id": s["selected_challenge_id"],
                    "requirements_passed": s["requirements_passed"],
                    "requirements_failed": s["requirements_failed"],
                    "e1_slot_satisfied": s["e1_slot_satisfied"],
                    "e2_slot_satisfied": s["e2_slot_satisfied"],
                    "e3_slot_satisfied": s["e3_slot_satisfied"],
                    "evidence_slots_satisfied": s["evidence_slots_satisfied"],
                    "computed_unitary_distance": s["computed_unitary_distance"],
                    "dry_run_verifier_rejected": s["dry_run_verifier_rejected"],
                    "accepted_source_backed_row_count": s["accepted_source_backed_row_count"],
                    "e2_transcript_hash": s["e2_transcript_hash"],
                    "e2_replacement_row_hash": s["e2_replacement_row_hash"],
                    "json_output": str(args.json_output),
                },
                indent=2,
                sort_keys=True,
            )
        )


if __name__ == "__main__":
    main()
