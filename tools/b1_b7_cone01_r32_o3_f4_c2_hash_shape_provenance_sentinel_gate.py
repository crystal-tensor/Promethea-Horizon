#!/usr/bin/env python3
"""T-B1-004eh/T-B7-013q: R32 O3-F4 C2 hash-shape provenance sentinel."""

from __future__ import annotations

import argparse
import hashlib
import json
import time
from pathlib import Path
from typing import Any


METHOD = "b1_b7_cone01_r32_o3_f4_c2_hash_shape_provenance_sentinel_gate_v0"
STATUS = "cone01_r32_o3_f4_c2_hash_shape_fixture_rejected_unbound_provenance"
MODEL_STATUS = "o3_f4_c2_hash_shape_without_binding_rejected_no_c2_acceptance"
VERSION = "0.1"
TARGET_ID = "T-B1-004eh/T-B7-013q"
UPSTREAM_TARGET_ID = "T-B1-004eg/T-B7-013p"
FAMILY_ID = "O3-F4"
CANDIDATE_ID = "NL-C02"
STRICT_TOLERANCE = 1.0e-8
HASH_FIELDS = [
    "same_unitary_witness_hash",
    "source_circuit_hash",
    "candidate_circuit_hash",
    "replay_stdout_hash",
]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any], pretty: bool = True) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2 if pretty else None, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def stable_hash(payload: Any) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def is_sha256(value: Any) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(ch in "0123456789abcdef" for ch in value)
    )


def requirement(
    requirement_id: str, label: str, passed: bool, evidence: dict[str, Any]
) -> dict[str, Any]:
    return {
        "requirement_id": requirement_id,
        "label": label,
        "passed": bool(passed),
        "evidence": evidence,
    }


def row_binding_hash(row: dict[str, Any]) -> str:
    binding_payload = {
        "challenge_id": row["challenge_id"],
        "parameter_indices": row["parameter_indices"],
        "submitted_parameter_values": row["submitted_parameter_values"],
        "strict_tolerance": row["strict_tolerance"],
        "max_unitary_replay_error": row["max_unitary_replay_error"],
        "unitary_distance_metric": row["unitary_distance_metric"],
        "source_circuit_hash": row["source_circuit_hash"],
        "candidate_circuit_hash": row["candidate_circuit_hash"],
        "replay_command": row["replay_command"],
        "replay_stdout_hash": row["replay_stdout_hash"],
        "verifier_version": row["verifier_version"],
    }
    return stable_hash(binding_payload)


def build_hash_shape_fixture(r31_fixture: dict[str, Any], r31: dict[str, Any]) -> dict[str, Any]:
    rows = []
    for idx, row in enumerate(r31_fixture["rows"]):
        challenge_id = row["challenge_id"]
        shaped = {
            **row,
            "same_unitary_witness_hash": stable_hash(
                {"fake": "witness", "challenge_id": challenge_id, "idx": idx}
            ),
            "source_circuit_hash": stable_hash(
                {"fake": "source-circuit", "challenge_id": challenge_id}
            ),
            "candidate_circuit_hash": stable_hash(
                {"fake": "candidate-circuit", "challenge_id": challenge_id}
            ),
            "replay_command": (
                "python3 tools/replay_o3_f4_c2.py "
                f"--challenge-id {challenge_id} --strict-tolerance 1e-08"
            ),
            "replay_stdout_hash": stable_hash(
                {"fake": "stdout", "challenge_id": challenge_id}
            ),
            "verifier_version": "hash-shape-fixture-v0",
        }
        shaped["declared_provenance_binding_hash"] = stable_hash(
            {"fake": "declared-binding", "challenge_id": challenge_id}
        )
        rows.append(shaped)
    fixture = {
        "artifact_id": "B1-B7-cone01-O3-F4-C2-hash-shape-provenance.fixture",
        "source_target_id": TARGET_ID,
        "upstream_target_id": UPSTREAM_TARGET_ID,
        "family_id": FAMILY_ID,
        "candidate_id": CANDIDATE_ID,
        "source_r31_fixture_hash": r31["summary"]["fixture_hash"],
        "source_r31_preflight_hash": r31["summary"]["preflight_hash"],
        "strict_tolerance": STRICT_TOLERANCE,
        "rows": rows,
        "claim_boundary": {
            "supported": "negative sentinel only: sha256-shaped hashes are insufficient unless bound to replay provenance",
            "not_supported": "C2 acceptance, O3 closure, R5 reroute, B7 credit, STV credit, or resource savings",
        },
        "o3_closed": False,
        "reroute_allowed": False,
        "b7_credit_delta": 0,
    }
    fixture["fixture_row_table_hash"] = stable_hash(rows)
    fixture["fixture_hash"] = stable_hash(fixture)
    return fixture


def evaluate_fixture(fixture: dict[str, Any]) -> dict[str, Any]:
    rows = fixture.get("rows", [])
    numeric_errors = [
        float(row["max_unitary_replay_error"])
        for row in rows
        if isinstance(row, dict) and isinstance(row.get("max_unitary_replay_error"), (int, float))
    ]
    hash_shape_failures = []
    command_shape_failures = []
    binding_mismatches = []
    for row in rows:
        challenge_id = row.get("challenge_id")
        for field in HASH_FIELDS:
            if not is_sha256(row.get(field)):
                hash_shape_failures.append(f"{challenge_id}:{field}")
        if not (
            isinstance(row.get("replay_command"), str)
            and row["replay_command"].startswith("python3 tools/")
            and "--challenge-id" in row["replay_command"]
        ):
            command_shape_failures.append(str(challenge_id))
        expected_binding = row_binding_hash(row)
        if row.get("declared_provenance_binding_hash") != expected_binding:
            binding_mismatches.append(
                {
                    "challenge_id": challenge_id,
                    "declared": row.get("declared_provenance_binding_hash"),
                    "expected": expected_binding,
                }
            )
    tolerance_pass_count = sum(error <= STRICT_TOLERANCE for error in numeric_errors)
    surface_pass = len(rows) == 8 and len(numeric_errors) == 8 and tolerance_pass_count == 8
    hash_shape_pass = not hash_shape_failures
    command_shape_pass = not command_shape_failures
    binding_pass = not binding_mismatches
    accepted = surface_pass and hash_shape_pass and command_shape_pass and binding_pass
    result = {
        "accepted": accepted,
        "surface_pass": surface_pass,
        "hash_shape_pass": hash_shape_pass,
        "command_shape_pass": command_shape_pass,
        "binding_pass": binding_pass,
        "row_count": len(rows),
        "numeric_replay_error_count": len(numeric_errors),
        "tolerance_pass_count": tolerance_pass_count,
        "max_observed_replay_error": max(numeric_errors) if numeric_errors else None,
        "strict_tolerance": STRICT_TOLERANCE,
        "hash_shape_failure_count": len(hash_shape_failures),
        "hash_shape_failures": hash_shape_failures,
        "command_shape_failure_count": len(command_shape_failures),
        "command_shape_failures": command_shape_failures,
        "binding_mismatch_count": len(binding_mismatches),
        "binding_mismatches": binding_mismatches,
        "claim_boundary_zero_credit": fixture.get("o3_closed") is False
        and fixture.get("reroute_allowed") is False
        and fixture.get("b7_credit_delta") == 0,
    }
    result["preflight_hash"] = stable_hash(result)
    return result


def build_payload(args: argparse.Namespace) -> tuple[dict[str, Any], dict[str, Any]]:
    started = time.time()
    r31 = load_json(args.r31_sentinel)
    r31_fixture = load_json(args.r31_fixture)
    fixture = build_hash_shape_fixture(r31_fixture, r31)
    preflight = evaluate_fixture(fixture)
    requirements = [
        requirement(
            "S1",
            "R31 source is validation-clean and fixture hash matches",
            r31["summary"].get("validation_error_count") == 0
            and r31["summary"].get("fixture_hash") == r31_fixture.get("fixture_hash"),
            {
                "r31_validation_error_count": r31["summary"].get("validation_error_count"),
                "r31_fixture_hash": r31["summary"].get("fixture_hash"),
                "fixture_hash": r31_fixture.get("fixture_hash"),
            },
        ),
        requirement(
            "S2",
            "Hash-shape fixture preserves all 8 C2 rows and tolerance-passing errors",
            preflight["row_count"] == 8
            and preflight["numeric_replay_error_count"] == 8
            and preflight["tolerance_pass_count"] == 8,
            {
                "row_count": preflight["row_count"],
                "numeric_replay_error_count": preflight["numeric_replay_error_count"],
                "tolerance_pass_count": preflight["tolerance_pass_count"],
            },
        ),
        requirement(
            "S3",
            "All witness/circuit/stdout hashes have valid sha256 shape",
            preflight["hash_shape_pass"] is True
            and preflight["hash_shape_failure_count"] == 0,
            {
                "hash_shape_pass": preflight["hash_shape_pass"],
                "hash_shape_failure_count": preflight["hash_shape_failure_count"],
            },
        ),
        requirement(
            "S4",
            "Replay commands have executable command shape",
            preflight["command_shape_pass"] is True
            and preflight["command_shape_failure_count"] == 0,
            {
                "command_shape_pass": preflight["command_shape_pass"],
                "command_shape_failure_count": preflight["command_shape_failure_count"],
            },
        ),
        requirement(
            "S5",
            "Hash shape and command shape are rejected without provenance binding",
            preflight["accepted"] is False
            and preflight["surface_pass"] is True
            and preflight["hash_shape_pass"] is True
            and preflight["command_shape_pass"] is True
            and preflight["binding_pass"] is False
            and preflight["binding_mismatch_count"] == 8,
            {
                "accepted": preflight["accepted"],
                "binding_pass": preflight["binding_pass"],
                "binding_mismatch_count": preflight["binding_mismatch_count"],
            },
        ),
        requirement(
            "S6",
            "Fixture keeps C2, O3, reroute, and B7 credit unaccepted",
            preflight["accepted"] is False
            and fixture["o3_closed"] is False
            and fixture["reroute_allowed"] is False
            and fixture["b7_credit_delta"] == 0,
            {
                "c2_accepted": preflight["accepted"],
                "o3_closed": fixture["o3_closed"],
                "reroute_allowed": fixture["reroute_allowed"],
                "b7_credit_delta": fixture["b7_credit_delta"],
            },
        ),
        requirement(
            "S7",
            "Fixture and preflight are hash-bound",
            bool(fixture["fixture_hash"])
            and bool(fixture["fixture_row_table_hash"])
            and bool(preflight["preflight_hash"]),
            {
                "fixture_hash": fixture["fixture_hash"],
                "fixture_row_table_hash": fixture["fixture_row_table_hash"],
                "preflight_hash": preflight["preflight_hash"],
            },
        ),
        requirement(
            "S8",
            "R32 remains scoped to C2 provenance and claims no C3-C7 progress",
            True,
            {
                "scope": "C2 provenance-binding sentinel",
                "c3_c7_progress_claimed": False,
            },
        ),
    ]
    failed_requirements = [
        item["requirement_id"] for item in requirements if not item["passed"]
    ]
    summary = {
        "candidate_id": CANDIDATE_ID,
        "family_id": FAMILY_ID,
        "source_r31_fixture_hash": r31["summary"]["fixture_hash"],
        "source_r31_preflight_hash": r31["summary"]["preflight_hash"],
        "source_r31_fixture_file_sha256": file_hash(args.r31_fixture),
        "fixture_hash": fixture["fixture_hash"],
        "fixture_row_table_hash": fixture["fixture_row_table_hash"],
        "preflight_hash": preflight["preflight_hash"],
        "strict_tolerance": STRICT_TOLERANCE,
        "row_count": preflight["row_count"],
        "numeric_replay_error_count": preflight["numeric_replay_error_count"],
        "tolerance_pass_count": preflight["tolerance_pass_count"],
        "max_observed_replay_error": preflight["max_observed_replay_error"],
        "hash_shape_pass": preflight["hash_shape_pass"],
        "hash_shape_failure_count": preflight["hash_shape_failure_count"],
        "command_shape_pass": preflight["command_shape_pass"],
        "command_shape_failure_count": preflight["command_shape_failure_count"],
        "binding_pass": preflight["binding_pass"],
        "binding_mismatch_count": preflight["binding_mismatch_count"],
        "c2_strict_replay_rows_accepted": False,
        "c2_hash_shape_fixture_accepted": False,
        "o3_f4_artifact_accepted": False,
        "same_unitary_replay_certificate_complete": False,
        "same_access_denominator_comparison_complete": False,
        "leakage_free_optimizer_trace_complete": False,
        "machine_check_replay_complete": False,
        "o3_closed": False,
        "checked_negative_lemma_present": False,
        "nlc02_full_lemma_ready": False,
        "reroute_allowed": False,
        "accepted_route_count": 0,
        "accepted_occurrence_removal": 0,
        "accepted_proxy_t_reduction": 0,
        "b7_credit_delta": 0,
        "b7_space_time_volume_credit": 0,
        "resource_saving_claimed": False,
        "b7_ledger_improvement_claimed": False,
        "remaining_open_obligations": [
            "C2_replay_provenance_binding_hash",
            "C2_replay_command_execution_artifact",
            "C3_same_unitary_replay_certificate",
            "C4_C5_same_access_denominator_comparison",
            "C6_leakage_free_optimizer_trace",
            "C7_machine_check_replay_bundle",
        ],
        "remaining_open_obligation_count": 6,
        "requirement_count": len(requirements),
        "requirements_passed": len(requirements) - len(failed_requirements),
        "requirements_failed": len(failed_requirements),
        "failed_requirement_ids": failed_requirements,
        "validation_error_count": len(failed_requirements),
    }
    payload = {
        "title": "B1/B7 Cone01 R32 O3-F4 C2 Hash-Shape Provenance Sentinel",
        "version": VERSION,
        "last_updated": "2026-07-08",
        "benchmark_id": "B1",
        "linked_benchmark_id": "B7",
        "method": METHOD,
        "status": STATUS,
        "model_status": MODEL_STATUS,
        "source_target_id": TARGET_ID,
        "upstream_target_id": UPSTREAM_TARGET_ID,
        "o3_f4_c2_hash_shape_provenance_sentinel_packet": {
            "source_r31_sentinel": str(args.r31_sentinel),
            "source_r31_fixture": str(args.r31_fixture),
            "fixture_output": str(args.fixture_output),
            "fixture": fixture,
            "preflight_result": preflight,
        },
        "requirements": requirements,
        "summary": summary,
        "claim_boundary": {
            "what_is_supported": (
                "R32 proves sha256-shaped hashes and plausible replay commands "
                "are not enough for C2 acceptance unless the row's declared "
                "provenance binding hash matches the replay payload."
            ),
            "what_is_not_supported": (
                "R32 does not accept C2, does not complete the certificate triad, "
                "does not close O3, and does not permit reroute, B7 credit, STV "
                "credit, or resource-saving claims."
            ),
            "next_gate": (
                "Submit C2 rows whose provenance binding hashes are recomputable "
                "from challenge id, submitted parameters, replay error, circuit "
                "hashes, replay command, stdout hash, and verifier version."
            ),
            "resource_saving_claimed": False,
            "b7_ledger_improvement_claimed": False,
        },
        "validation_errors": failed_requirements,
        "runtime_seconds": round(time.time() - started, 6),
    }
    return payload, fixture


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    summary = payload["summary"]
    lines = [
        "# B1/B7 Cone01 R32 O3-F4 C2 Hash-Shape Provenance Sentinel",
        "",
        f"- Target: `{payload['source_target_id']}`",
        f"- Upstream target: `{payload['upstream_target_id']}`",
        f"- Method: `{payload['method']}`",
        f"- Status: `{payload['status']}`",
        f"- Fixture hash: `{summary['fixture_hash']}`",
        f"- Fixture row-table hash: `{summary['fixture_row_table_hash']}`",
        f"- Preflight hash: `{summary['preflight_hash']}`",
        "",
        "## Result",
        "",
        (
            f"R32 passes {summary['requirements_passed']}/"
            f"{summary['requirement_count']} requirements by rejecting a "
            "hash-shaped C2 fixture whose replay provenance is not bound to the rows."
        ),
        "",
        "## Sentinel Outcome",
        "",
        f"- Row count: `{summary['row_count']}`",
        f"- Tolerance pass count: `{summary['tolerance_pass_count']}`",
        f"- Hash shape pass: `{summary['hash_shape_pass']}`",
        f"- Command shape pass: `{summary['command_shape_pass']}`",
        f"- Binding pass: `{summary['binding_pass']}`",
        f"- Binding mismatch count: `{summary['binding_mismatch_count']}`",
        f"- C2 accepted: `{summary['c2_strict_replay_rows_accepted']}`",
        "",
        "## Requirement Results",
        "",
    ]
    for item in payload["requirements"]:
        mark = "PASS" if item["passed"] else "FAIL"
        lines.append(f"- `{item['requirement_id']}` {mark}: {item['label']}")
    lines.extend(
        [
            "",
            "## Claim Boundary",
            "",
            f"- Supported: {payload['claim_boundary']['what_is_supported']}",
            f"- Not supported: {payload['claim_boundary']['what_is_not_supported']}",
            f"- Next gate: {payload['claim_boundary']['next_gate']}",
            "",
            f"- validation_error_count: `{summary['validation_error_count']}`",
            "",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--r31-sentinel",
        type=Path,
        default=Path("results/B1_B7_cone01_R31_o3_f4_c2_numeric_only_overclaim_sentinel_gate_v0.json"),
    )
    parser.add_argument(
        "--r31-fixture",
        type=Path,
        default=Path(
            "results/B1_B7_cone01_o3_f4_numerical_refit_submissions/"
            "B1-B7-cone01-O3-F4-C2-numeric-only-overclaim.fixture.json"
        ),
    )
    parser.add_argument(
        "--fixture-output",
        type=Path,
        default=Path(
            "results/B1_B7_cone01_o3_f4_numerical_refit_submissions/"
            "B1-B7-cone01-O3-F4-C2-hash-shape-provenance.fixture.json"
        ),
    )
    parser.add_argument(
        "--json-output",
        type=Path,
        default=Path("results/B1_B7_cone01_R32_o3_f4_c2_hash_shape_provenance_sentinel_gate_v0.json"),
    )
    parser.add_argument(
        "--markdown-output",
        type=Path,
        default=Path("research/B1_B7_cone01_R32_o3_f4_c2_hash_shape_provenance_sentinel_gate.md"),
    )
    parser.add_argument("--pretty", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    payload, fixture = build_payload(args)
    write_json(args.fixture_output, fixture, pretty=True)
    write_json(args.json_output, payload, pretty=True)
    write_markdown(args.markdown_output, payload)
    if args.pretty:
        print(
            json.dumps(
                {
                    "status": payload["status"],
                    "requirements_passed": payload["summary"]["requirements_passed"],
                    "requirements_failed": payload["summary"]["requirements_failed"],
                    "fixture_hash": payload["summary"]["fixture_hash"],
                    "preflight_hash": payload["summary"]["preflight_hash"],
                    "hash_shape_pass": payload["summary"]["hash_shape_pass"],
                    "command_shape_pass": payload["summary"]["command_shape_pass"],
                    "binding_pass": payload["summary"]["binding_pass"],
                    "binding_mismatch_count": payload["summary"]["binding_mismatch_count"],
                    "c2_strict_replay_rows_accepted": payload["summary"][
                        "c2_strict_replay_rows_accepted"
                    ],
                    "o3_closed": payload["summary"]["o3_closed"],
                    "reroute_allowed": payload["summary"]["reroute_allowed"],
                    "b7_credit_delta": payload["summary"]["b7_credit_delta"],
                    "fixture_output": str(args.fixture_output),
                    "json_output": str(args.json_output),
                    "markdown_output": str(args.markdown_output),
                },
                indent=2,
                sort_keys=True,
            )
        )


if __name__ == "__main__":
    main()
