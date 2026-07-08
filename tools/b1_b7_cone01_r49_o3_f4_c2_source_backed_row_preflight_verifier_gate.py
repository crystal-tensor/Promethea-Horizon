#!/usr/bin/env python3
"""T-B1-004ey/T-B7-014h: R49 O3-F4 C2 source-backed row preflight verifier gate."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import time
from pathlib import Path
from typing import Any


METHOD = "b1_b7_cone01_r49_o3_f4_c2_source_backed_row_preflight_verifier_gate_v0"
STATUS = "cone01_r49_o3_f4_c2_source_backed_row_preflight_verifier_rejects_template"
MODEL_STATUS = "o3_f4_c2_first_row_preflight_verifier_ready_template_rejected"
VERSION = "0.1"
TARGET_ID = "T-B1-004ey/T-B7-014h"
UPSTREAM_TARGET_ID = "T-B1-004ex/T-B7-014g"
SELECTED_CHALLENGE_ID = "O3-F4-C01"
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
FILE_HASH_PAIRS = [
    ("source_dataset_file", "source_dataset_sha256"),
    ("source_trace_file", "source_trace_sha256"),
    ("replay_environment_file", "replay_environment_sha256"),
    ("source_circuit_file", "source_circuit_sha256"),
    ("candidate_circuit_file", "candidate_circuit_sha256"),
    ("replay_stdout_file", "replay_stdout_sha256"),
    ("same_unitary_witness_file", "same_unitary_witness_sha256"),
    ("verifier_signature_file", "verifier_signature_sha256"),
]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def stable_hash(payload: Any) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def is_sha256(value: Any) -> bool:
    return isinstance(value, str) and bool(SHA256_RE.fullmatch(value))


def req(requirement_id: str, label: str, passed: bool, evidence: dict[str, Any]) -> dict[str, Any]:
    return {
        "requirement_id": requirement_id,
        "label": label,
        "passed": bool(passed),
        "evidence": evidence,
    }


def build_verifier_spec(r48: dict[str, Any], contract: dict[str, Any]) -> dict[str, Any]:
    spec = {
        "verifier_id": "B1-B7-cone01-O3-F4-C2-C01-source-backed-row-preflight-verifier",
        "source_target_id": TARGET_ID,
        "upstream_target_id": UPSTREAM_TARGET_ID,
        "selected_challenge_id": SELECTED_CHALLENGE_ID,
        "source_r48_contract_hash": r48["summary"]["contract_hash"],
        "source_r48_template_hash": r48["summary"]["template_hash"],
        "required_keys": contract["required_keys"],
        "production_required_keys": contract["production_required_keys"],
        "file_hash_pairs": FILE_HASH_PAIRS,
        "required_boolean_state": {
            "source_backed_replay": True,
            "same_unitary_certificate": True,
            "smoke_only_not_c2_acceptance": False,
        },
        "required_schema": "source_backed_unitary_equivalence_v1",
        "required_claim_boundary_tokens": ["no C2", "O3", "reroute", "B7", "STV"],
        "hard_reject_if": [
            "any required key is absent",
            "any production-required key is empty",
            "any file path is missing or hash-mismatched",
            "any sha256 field is malformed",
            "same_unitary_witness_schema is not source_backed_unitary_equivalence_v1",
            "source_backed_replay is not true",
            "same_unitary_certificate is not true",
            "smoke_only_not_c2_acceptance is not false",
            "claim boundary omits zero-credit tokens",
        ],
    }
    spec["verifier_hash"] = stable_hash(spec)
    return spec


def verify_row(row: dict[str, Any], contract: dict[str, Any], spec: dict[str, Any], root: Path) -> dict[str, Any]:
    missing_keys = [key for key in contract["required_keys"] if key not in row]
    empty_production_keys = [
        key
        for key in contract["production_required_keys"]
        if key not in row or row.get(key) in (None, "", False)
    ]
    malformed_sha_fields = [
        hash_key
        for _, hash_key in FILE_HASH_PAIRS
        if hash_key in row and row.get(hash_key) is not None and not is_sha256(row.get(hash_key))
    ]
    file_results = []
    for path_key, hash_key in FILE_HASH_PAIRS:
        path_value = row.get(path_key)
        expected_hash = row.get(hash_key)
        path = root / path_value if isinstance(path_value, str) else None
        exists = bool(path and path.exists() and path.is_file())
        actual_hash = file_hash(path) if exists else None
        file_results.append(
            {
                "path_key": path_key,
                "hash_key": hash_key,
                "path": path_value,
                "expected_hash": expected_hash,
                "exists": exists,
                "actual_hash": actual_hash,
                "hash_matches": exists and actual_hash == expected_hash,
            }
        )
    file_hash_failures = [
        item["path_key"]
        for item in file_results
        if not item["exists"] or not item["hash_matches"]
    ]
    flag_failures = [
        key
        for key, expected in spec["required_boolean_state"].items()
        if row.get(key) is not expected
    ]
    schema_passed = row.get("same_unitary_witness_schema") == spec["required_schema"]
    boundary_tokens_present = all(
        token in str(row.get("claim_boundary", "")) for token in spec["required_claim_boundary_tokens"]
    )
    accepted = (
        not missing_keys
        and not empty_production_keys
        and not malformed_sha_fields
        and not file_hash_failures
        and not flag_failures
        and schema_passed
        and boundary_tokens_present
    )
    failed_reasons = []
    if missing_keys:
        failed_reasons.append("required_keys_missing")
    if empty_production_keys:
        failed_reasons.append("production_required_keys_empty")
    if malformed_sha_fields:
        failed_reasons.append("malformed_sha256_fields")
    if file_hash_failures:
        failed_reasons.append("file_hash_checks_failed")
    if flag_failures:
        failed_reasons.append("source_backed_boolean_state_failed")
    if not schema_passed:
        failed_reasons.append("witness_schema_mismatch")
    if not boundary_tokens_present:
        failed_reasons.append("zero_credit_claim_boundary_missing")
    return {
        "challenge_id": row.get("challenge_id"),
        "accepted": accepted,
        "missing_key_count": len(missing_keys),
        "empty_production_key_count": len(empty_production_keys),
        "malformed_sha_field_count": len(malformed_sha_fields),
        "file_hash_failure_count": len(file_hash_failures),
        "flag_failure_count": len(flag_failures),
        "schema_passed": schema_passed,
        "boundary_tokens_present": boundary_tokens_present,
        "missing_keys": missing_keys,
        "empty_production_keys": empty_production_keys,
        "malformed_sha_fields": malformed_sha_fields,
        "file_hash_failures": file_hash_failures,
        "flag_failures": flag_failures,
        "file_results": file_results,
        "failed_reasons": failed_reasons,
    }


def build_payload(args: argparse.Namespace) -> dict[str, Any]:
    started = time.time()
    r48 = load_json(args.r48_result)
    contract = load_json(args.contract_input)
    template = load_json(args.template_input)
    spec = build_verifier_spec(r48, contract)
    write_json(args.verifier_output, spec)
    verification = verify_row(template, contract, spec, args.root)
    evaluation = {
        "verifier_hash": spec["verifier_hash"],
        "template_hash": template["template_hash"],
        "template_file_sha256": file_hash(args.template_input),
        "template_verification": verification,
        "accepted_source_backed_row_count": 1 if verification["accepted"] else 0,
        "template_rejected": verification["accepted"] is False,
    }
    evaluation["evaluation_hash"] = stable_hash(evaluation)
    expected_empty_template_keys = [
        key
        for key in contract["production_required_keys"]
        if template.get(key) in (None, "", False)
    ]
    requirements = [
        req(
            "S1",
            "R48 contract is validation-clean and still has no accepted source-backed row",
            r48["summary"].get("validation_error_count") == 0
            and r48["summary"].get("accepted_source_backed_row_count") == 0
            and r48["summary"].get("contract_hash") == contract["contract_hash"],
            {
                "r48_validation_error_count": r48["summary"].get("validation_error_count"),
                "r48_accepted_source_backed_row_count": r48["summary"].get("accepted_source_backed_row_count"),
                "r48_contract_hash": r48["summary"].get("contract_hash"),
                "contract_hash": contract["contract_hash"],
            },
        ),
        req(
            "S2",
            "R49 emits a hash-bound preflight verifier spec",
            spec["selected_challenge_id"] == SELECTED_CHALLENGE_ID
            and spec["source_r48_contract_hash"] == contract["contract_hash"]
            and bool(spec["verifier_hash"]),
            {
                "selected_challenge_id": spec["selected_challenge_id"],
                "source_r48_contract_hash": spec["source_r48_contract_hash"],
                "verifier_hash": spec["verifier_hash"],
            },
        ),
        req(
            "S3",
            "Verifier covers required keys, production keys, file hashes, booleans, schema, and boundary tokens",
            len(spec["required_keys"]) == contract["required_key_count"]
            and len(spec["production_required_keys"]) == contract["production_required_key_count"]
            and len(spec["file_hash_pairs"]) == 8
            and len(spec["required_boolean_state"]) == 3
            and len(spec["required_claim_boundary_tokens"]) == 5,
            {
                "required_key_count": len(spec["required_keys"]),
                "production_required_key_count": len(spec["production_required_keys"]),
                "file_hash_pair_count": len(spec["file_hash_pairs"]),
                "required_boolean_count": len(spec["required_boolean_state"]),
                "claim_boundary_token_count": len(spec["required_claim_boundary_tokens"]),
            },
        ),
        req(
            "S4",
            "R49 rejects the R48 placeholder template",
            evaluation["template_rejected"] is True
            and evaluation["accepted_source_backed_row_count"] == 0,
            {
                "template_rejected": evaluation["template_rejected"],
                "accepted_source_backed_row_count": evaluation["accepted_source_backed_row_count"],
                "failed_reasons": verification["failed_reasons"],
            },
        ),
        req(
            "S5",
            "Template rejection exposes production-key and file-hash gaps",
            verification["empty_production_key_count"] == len(expected_empty_template_keys)
            and verification["file_hash_failure_count"] == len(FILE_HASH_PAIRS),
            {
                "empty_production_key_count": verification["empty_production_key_count"],
                "expected_empty_template_key_count": len(expected_empty_template_keys),
                "expected_empty_template_keys": expected_empty_template_keys,
                "file_hash_failure_count": verification["file_hash_failure_count"],
                "file_hash_pair_count": len(FILE_HASH_PAIRS),
            },
        ),
        req(
            "S6",
            "Template rejection preserves source-backed boolean blockers",
            set(verification["flag_failures"]) == {
                "source_backed_replay",
                "same_unitary_certificate",
                "smoke_only_not_c2_acceptance",
            },
            {"flag_failures": verification["flag_failures"]},
        ),
        req(
            "S7",
            "R49 preserves C2/O3/reroute/B7 zero-credit boundaries",
            True,
            {
                "c2_accepted": False,
                "o3_closed": False,
                "reroute_allowed": False,
                "b7_credit_delta": 0,
                "b7_space_time_volume_credit": 0,
            },
        ),
        req(
            "S8",
            "R49 claims no C3-C7, occurrence-removal, or B7 ledger progress",
            True,
            {
                "c3_c7_progress_claimed": False,
                "occurrence_removal_claimed": False,
                "b7_ledger_credit_claimed": False,
            },
        ),
    ]
    failed = [item["requirement_id"] for item in requirements if not item["passed"]]
    summary = {
        "source_r48_contract_hash": r48["summary"]["contract_hash"],
        "source_r48_template_hash": r48["summary"]["template_hash"],
        "source_r48_file_sha256": file_hash(args.r48_result),
        "selected_challenge_id": SELECTED_CHALLENGE_ID,
        "verifier_hash": spec["verifier_hash"],
        "verifier_file_sha256": file_hash(args.verifier_output),
        "template_hash": template["template_hash"],
        "template_file_sha256": file_hash(args.template_input),
        "evaluation_hash": evaluation["evaluation_hash"],
        "required_key_count": len(spec["required_keys"]),
        "production_required_key_count": len(spec["production_required_keys"]),
        "file_hash_pair_count": len(FILE_HASH_PAIRS),
        "required_boolean_count": len(spec["required_boolean_state"]),
        "claim_boundary_token_count": len(spec["required_claim_boundary_tokens"]),
        "template_rejected": evaluation["template_rejected"],
        "accepted_source_backed_row_count": evaluation["accepted_source_backed_row_count"],
        "empty_production_key_count": verification["empty_production_key_count"],
        "file_hash_failure_count": verification["file_hash_failure_count"],
        "flag_failure_count": verification["flag_failure_count"],
        "schema_passed": verification["schema_passed"],
        "boundary_tokens_present": verification["boundary_tokens_present"],
        "c2_strict_replay_rows_accepted": False,
        "o3_closed": False,
        "reroute_allowed": False,
        "accepted_route_count": 0,
        "accepted_occurrence_removal": 0,
        "accepted_proxy_t_reduction": 0,
        "b7_credit_delta": 0,
        "b7_space_time_volume_credit": 0,
        "resource_saving_claimed": False,
        "b7_ledger_improvement_claimed": False,
        "remaining_open_obligations": [
            "submit_O3_F4_C01_source_backed_row_artifact_that_passes_R49_preflight",
            "provide_all_8_file_hash_pairs",
            "fill_all_14_production_required_keys",
            "flip_source_backed_boolean_state_with_evidence",
            "rerun_R47_and_R49_after_submission",
            "scale_source_backed_acceptance_from_1_row_to_8_rows",
            "C3_same_unitary_replay_certificate",
            "C4_C5_same_access_denominator_comparison",
            "C6_leakage_free_optimizer_trace",
            "C7_machine_check_replay_bundle",
        ],
        "remaining_open_obligation_count": 10,
        "requirement_count": len(requirements),
        "requirements_passed": len(requirements) - len(failed),
        "requirements_failed": len(failed),
        "failed_requirement_ids": failed,
        "validation_error_count": len(failed),
    }
    return {
        "title": "B1/B7 Cone01 R49 O3-F4 C2 Source-Backed Row Preflight Verifier Gate",
        "version": VERSION,
        "last_updated": "2026-07-08",
        "benchmark_id": "B1",
        "linked_benchmark_id": "B7",
        "method": METHOD,
        "status": STATUS,
        "model_status": MODEL_STATUS,
        "source_target_id": TARGET_ID,
        "upstream_target_id": UPSTREAM_TARGET_ID,
        "o3_f4_c2_source_backed_row_preflight_verifier_packet": {
            "source_r48_result": str(args.r48_result),
            "contract_input": str(args.contract_input),
            "template_input": str(args.template_input),
            "verifier_output": str(args.verifier_output),
            "verifier_spec": spec,
            "evaluation": evaluation,
        },
        "requirements": requirements,
        "summary": summary,
        "claim_boundary": {
            "what_is_supported": (
                "R49 turns the R48 row-intake contract into a runnable preflight "
                "verifier and proves the placeholder template is rejected for "
                "missing production evidence, file hashes, and source-backed flags."
            ),
            "what_is_not_supported": (
                "R49 does not submit or accept a source-backed row, does not flip "
                "source-backed flags, does not accept C2, close O3, allow reroute, "
                "or grant B7/STV credit."
            ),
            "next_gate": (
                "Submit O3-F4-C01 with all production keys, hash-matched files, "
                "source-backed booleans, verifier signature, and zero-credit claim "
                "boundary, then rerun R49 and R47."
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
        "# B1/B7 Cone01 R49 O3-F4 C2 Source-Backed Row Preflight Verifier Gate",
        "",
        f"- Target: `{payload['source_target_id']}`",
        f"- Upstream target: `{payload['upstream_target_id']}`",
        f"- Method: `{payload['method']}`",
        f"- Status: `{payload['status']}`",
        f"- Selected challenge: `{s['selected_challenge_id']}`",
        f"- Verifier hash: `{s['verifier_hash']}`",
        f"- Evaluation hash: `{s['evaluation_hash']}`",
        "",
        "## Result",
        "",
        (
            f"R49 passes {s['requirements_passed']}/{s['requirement_count']} "
            "requirements by emitting a runnable preflight verifier and rejecting "
            "the R48 placeholder template."
        ),
        "",
        "## Rejection Surface",
        "",
        f"- Template rejected: `{s['template_rejected']}`",
        f"- Accepted source-backed rows: `{s['accepted_source_backed_row_count']}`",
        f"- Production keys checked: `{s['production_required_key_count']}`",
        f"- Empty production keys: `{s['empty_production_key_count']}`",
        f"- File hash pairs checked: `{s['file_hash_pair_count']}`",
        f"- File hash failures: `{s['file_hash_failure_count']}`",
        f"- Boolean flag failures: `{s['flag_failure_count']}`",
        f"- C2 accepted: `{s['c2_strict_replay_rows_accepted']}`",
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
    parser.add_argument("--r48-result", type=Path, default=Path("results/B1_B7_cone01_R48_o3_f4_c2_source_backed_row_intake_gate_v0.json"))
    parser.add_argument("--contract-input", type=Path, default=Path("results/B1_B7_cone01_o3_f4_numerical_refit_submissions/B1-B7-cone01-O3-F4-C2-C01-source-backed-row-intake.contract.json"))
    parser.add_argument("--template-input", type=Path, default=Path("results/B1_B7_cone01_o3_f4_numerical_refit_submissions/B1-B7-cone01-O3-F4-C2-C01-source-backed-row-intake.template.json"))
    parser.add_argument("--verifier-output", type=Path, default=Path("results/B1_B7_cone01_o3_f4_numerical_refit_submissions/B1-B7-cone01-O3-F4-C2-C01-source-backed-row-preflight.verifier.json"))
    parser.add_argument("--json-output", type=Path, default=Path("results/B1_B7_cone01_R49_o3_f4_c2_source_backed_row_preflight_verifier_gate_v0.json"))
    parser.add_argument("--markdown-output", type=Path, default=Path("research/B1_B7_cone01_R49_o3_f4_c2_source_backed_row_preflight_verifier_gate.md"))
    parser.add_argument("--pretty", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    payload = build_payload(args)
    write_json(args.json_output, payload)
    write_markdown(args.markdown_output, payload)
    if args.pretty:
        s = payload["summary"]
        print(json.dumps({
            "status": payload["status"],
            "selected_challenge_id": s["selected_challenge_id"],
            "verifier_hash": s["verifier_hash"],
            "evaluation_hash": s["evaluation_hash"],
            "requirements_passed": s["requirements_passed"],
            "requirements_failed": s["requirements_failed"],
            "template_rejected": s["template_rejected"],
            "accepted_source_backed_row_count": s["accepted_source_backed_row_count"],
            "empty_production_key_count": s["empty_production_key_count"],
            "file_hash_failure_count": s["file_hash_failure_count"],
            "json_output": str(args.json_output),
        }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
