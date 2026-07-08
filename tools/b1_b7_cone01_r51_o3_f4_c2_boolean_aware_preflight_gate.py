#!/usr/bin/env python3
"""T-B1-004fa/T-B7-014j: R51 boolean-aware C01 preflight gate."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import time
from pathlib import Path
from typing import Any


METHOD = "b1_b7_cone01_r51_o3_f4_c2_boolean_aware_preflight_gate_v0"
STATUS = "cone01_r51_o3_f4_c2_boolean_aware_preflight_rejects_actual_row_flags_only"
MODEL_STATUS = "o3_f4_c2_c01_boolean_empty_semantics_fixed_actual_row_still_flag_blocked"
VERSION = "0.1"
TARGET_ID = "T-B1-004fa/T-B7-014j"
UPSTREAM_TARGET_ID = "T-B1-004ez/T-B7-014i"
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
BOOLEAN_KEYS = {
    "source_backed_replay",
    "same_unitary_certificate",
    "smoke_only_not_c2_acceptance",
}


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


def is_sha256(value: Any) -> bool:
    return isinstance(value, str) and bool(SHA256_RE.fullmatch(value))


def req(requirement_id: str, label: str, passed: bool, evidence: dict[str, Any]) -> dict[str, Any]:
    return {
        "requirement_id": requirement_id,
        "label": label,
        "passed": bool(passed),
        "evidence": evidence,
    }


def legacy_empty_keys(row: dict[str, Any], contract: dict[str, Any]) -> list[str]:
    return [
        key
        for key in contract["production_required_keys"]
        if key not in row or row.get(key) in (None, "", False)
    ]


def boolean_aware_empty_keys(row: dict[str, Any], contract: dict[str, Any]) -> list[str]:
    keys = []
    for key in contract["production_required_keys"]:
        if key not in row:
            keys.append(key)
            continue
        value = row.get(key)
        if key in BOOLEAN_KEYS:
            if not isinstance(value, bool):
                keys.append(key)
            continue
        if value in (None, ""):
            keys.append(key)
    return keys


def build_boolean_aware_verifier(r49_verifier: dict[str, Any], r50: dict[str, Any]) -> dict[str, Any]:
    spec = {
        "verifier_id": "B1-B7-cone01-O3-F4-C2-C01-boolean-aware-row-preflight-verifier",
        "source_target_id": TARGET_ID,
        "upstream_target_id": UPSTREAM_TARGET_ID,
        "selected_challenge_id": SELECTED_CHALLENGE_ID,
        "source_r49_verifier_hash": r49_verifier["verifier_hash"],
        "source_r50_presubmission_row_hash": r50["summary"]["presubmission_row_hash"],
        "required_keys": r49_verifier["required_keys"],
        "production_required_keys": r49_verifier["production_required_keys"],
        "boolean_production_keys": sorted(BOOLEAN_KEYS),
        "file_hash_pairs": FILE_HASH_PAIRS,
        "required_boolean_state": {
            "source_backed_replay": True,
            "same_unitary_certificate": True,
            "smoke_only_not_c2_acceptance": False,
        },
        "required_schema": "source_backed_unitary_equivalence_v1",
        "required_claim_boundary_tokens": ["no C2", "O3", "reroute", "B7", "STV"],
        "boolean_empty_semantics": (
            "Boolean production keys are complete when present as booleans. "
            "Their accepted value is checked only by required_boolean_state."
        ),
        "hard_reject_if": [
            "any required key is absent",
            "any non-boolean production-required key is null or empty string",
            "any boolean production-required key is absent or non-boolean",
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
    empty_production_keys = boolean_aware_empty_keys(row, contract)
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
    return {
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
    }


def build_payload(args: argparse.Namespace) -> dict[str, Any]:
    started = time.time()
    contract = load_json(args.contract_input)
    r49_verifier = load_json(args.r49_verifier)
    r50 = load_json(args.r50_result)
    row = load_json(args.presubmission_input)
    spec = build_boolean_aware_verifier(r49_verifier, r50)
    write_json(args.verifier_output, spec)

    actual_eval = verify_row(row, contract, spec, args.root)
    semantic_flip_row = dict(row)
    semantic_flip_row.update(
        {
            "source_backed_replay": True,
            "same_unitary_certificate": True,
            "smoke_only_not_c2_acceptance": False,
        }
    )
    legacy_semantic_empty = legacy_empty_keys(semantic_flip_row, contract)
    boolean_aware_semantic_empty = boolean_aware_empty_keys(semantic_flip_row, contract)
    semantic_flip_eval = verify_row(semantic_flip_row, contract, spec, args.root)
    evaluation = {
        "verifier_hash": spec["verifier_hash"],
        "actual_row_hash": row["presubmission_row_hash"],
        "actual_row_verification": actual_eval,
        "semantic_flip_is_simulation_only": True,
        "semantic_flip_legacy_empty_keys": legacy_semantic_empty,
        "semantic_flip_boolean_aware_empty_keys": boolean_aware_semantic_empty,
        "semantic_flip_boolean_aware_verification": semantic_flip_eval,
        "accepted_source_backed_row_count": 1 if actual_eval["accepted"] else 0,
        "actual_row_rejected": actual_eval["accepted"] is False,
    }
    evaluation["evaluation_hash"] = stable_hash(evaluation)
    requirements = [
        req(
            "S1",
            "R50 baseline is clean and file/hash complete but still flag-blocked",
            r50["summary"].get("requirements_passed") == 8
            and r50["summary"].get("requirements_failed") == 0
            and r50["summary"].get("file_hash_failure_count") == 0
            and r50["summary"].get("flag_failure_count") == 3
            and r50["summary"].get("accepted_source_backed_row_count") == 0,
            {
                "r50_requirements_passed": r50["summary"].get("requirements_passed"),
                "r50_file_hash_failure_count": r50["summary"].get("file_hash_failure_count"),
                "r50_flag_failure_count": r50["summary"].get("flag_failure_count"),
                "r50_accepted_source_backed_row_count": r50["summary"].get("accepted_source_backed_row_count"),
            },
        ),
        req(
            "S2",
            "R51 proves legacy false-as-empty semantics would block a semantically correct false flag",
            "smoke_only_not_c2_acceptance" in legacy_semantic_empty,
            {"legacy_semantic_empty_keys": legacy_semantic_empty},
        ),
        req(
            "S3",
            "R51 emits a boolean-aware verifier that does not treat valid boolean false as missing",
            "smoke_only_not_c2_acceptance" not in boolean_aware_semantic_empty
            and len(boolean_aware_semantic_empty) == 0,
            {"boolean_aware_semantic_empty_keys": boolean_aware_semantic_empty},
        ),
        req(
            "S4",
            "Actual R50 row has no production-key or file/hash failures under boolean-aware semantics",
            actual_eval["empty_production_key_count"] == 0
            and actual_eval["file_hash_failure_count"] == 0,
            {
                "actual_empty_production_key_count": actual_eval["empty_production_key_count"],
                "actual_file_hash_failure_count": actual_eval["file_hash_failure_count"],
            },
        ),
        req(
            "S5",
            "Actual R50 row is still rejected only on source-backed boolean flags",
            actual_eval["accepted"] is False
            and set(actual_eval["flag_failures"]) == {
                "source_backed_replay",
                "same_unitary_certificate",
                "smoke_only_not_c2_acceptance",
            },
            {
                "actual_accepted": actual_eval["accepted"],
                "actual_flag_failures": actual_eval["flag_failures"],
            },
        ),
        req(
            "S6",
            "Semantic flip simulation is not counted as a submitted or accepted row",
            evaluation["semantic_flip_is_simulation_only"] is True
            and evaluation["accepted_source_backed_row_count"] == 0,
            {
                "semantic_flip_is_simulation_only": evaluation["semantic_flip_is_simulation_only"],
                "accepted_source_backed_row_count": evaluation["accepted_source_backed_row_count"],
            },
        ),
        req(
            "S7",
            "R51 preserves schema and zero-credit boundary checks",
            actual_eval["schema_passed"] is True and actual_eval["boundary_tokens_present"] is True,
            {
                "schema_passed": actual_eval["schema_passed"],
                "boundary_tokens_present": actual_eval["boundary_tokens_present"],
            },
        ),
        req(
            "S8",
            "R51 claims no C2, O3, reroute, B7, STV, C3-C7, or resource progress",
            True,
            {
                "c2_accepted": False,
                "o3_closed": False,
                "reroute_allowed": False,
                "b7_credit_delta": 0,
                "b7_space_time_volume_credit": 0,
                "c3_c7_progress_claimed": False,
                "resource_saving_claimed": False,
            },
        ),
    ]
    failed = [item["requirement_id"] for item in requirements if not item["passed"]]
    summary = {
        "source_r49_verifier_hash": r49_verifier["verifier_hash"],
        "source_r50_presubmission_row_hash": r50["summary"]["presubmission_row_hash"],
        "selected_challenge_id": SELECTED_CHALLENGE_ID,
        "boolean_aware_verifier_hash": spec["verifier_hash"],
        "boolean_aware_verifier_file_sha256": file_hash(args.verifier_output),
        "evaluation_hash": evaluation["evaluation_hash"],
        "legacy_semantic_flip_empty_key_count": len(legacy_semantic_empty),
        "legacy_semantic_flip_empty_keys": legacy_semantic_empty,
        "boolean_aware_semantic_flip_empty_key_count": len(boolean_aware_semantic_empty),
        "actual_empty_production_key_count": actual_eval["empty_production_key_count"],
        "actual_file_hash_failure_count": actual_eval["file_hash_failure_count"],
        "actual_flag_failure_count": actual_eval["flag_failure_count"],
        "actual_flag_failures": actual_eval["flag_failures"],
        "actual_row_rejected": evaluation["actual_row_rejected"],
        "accepted_source_backed_row_count": evaluation["accepted_source_backed_row_count"],
        "source_backed_replay": row["source_backed_replay"],
        "same_unitary_certificate": row["same_unitary_certificate"],
        "smoke_only_not_c2_acceptance": row["smoke_only_not_c2_acceptance"],
        "c2_strict_replay_rows_accepted": False,
        "o3_closed": False,
        "reroute_allowed": False,
        "b7_credit_delta": 0,
        "b7_space_time_volume_credit": 0,
        "resource_saving_claimed": False,
        "b7_ledger_improvement_claimed": False,
        "remaining_open_obligations": [
            "replace_smoke_unitary_distance_witness_with_source_backed_replay_witness",
            "replace_r40_dry_run_verifier_with_real_same_unitary_verifier",
            "replace_signature_blocker_note_with_verifier_signature",
            "submit_actual_row_with_evidence_backed_boolean_flags",
            "rerun_R51_then_R47_after_flag_evidence",
        ],
        "remaining_open_obligation_count": 5,
        "requirement_count": len(requirements),
        "requirements_passed": len(requirements) - len(failed),
        "requirements_failed": len(failed),
        "failed_requirement_ids": failed,
        "validation_error_count": len(failed),
    }
    return {
        "title": "B1/B7 Cone01 R51 O3-F4 C2 Boolean-Aware Preflight Gate",
        "version": VERSION,
        "last_updated": "2026-07-08",
        "benchmark_id": "B1",
        "linked_benchmark_id": "B7",
        "method": METHOD,
        "status": STATUS,
        "model_status": MODEL_STATUS,
        "source_target_id": TARGET_ID,
        "upstream_target_id": UPSTREAM_TARGET_ID,
        "boolean_aware_preflight_packet": {
            "contract_input": str(args.contract_input),
            "source_r49_verifier": str(args.r49_verifier),
            "source_r50_result": str(args.r50_result),
            "presubmission_input": str(args.presubmission_input),
            "verifier_output": str(args.verifier_output),
            "evaluation": evaluation,
        },
        "requirements": requirements,
        "summary": summary,
        "claim_boundary": {
            "what_is_supported": (
                "R51 fixes the preflight gate semantics so boolean production keys "
                "are treated as present when they are booleans, while their accepted "
                "values remain enforced by required_boolean_state."
            ),
            "what_is_not_supported": (
                "R51 does not submit evidence-backed source_backed_replay=true, "
                "same_unitary_certificate=true, or smoke_only_not_c2_acceptance=false; "
                "it does not accept C2, close O3, permit reroute, or grant B7/STV credit."
            ),
            "next_gate": (
                "Replace the smoke witness, dry-run verifier, and signature blocker "
                "with evidence-backed artifacts, then rerun R51 and R47."
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
        "# B1/B7 Cone01 R51 O3-F4 C2 Boolean-Aware Preflight Gate",
        "",
        f"- Target: `{payload['source_target_id']}`",
        f"- Upstream target: `{payload['upstream_target_id']}`",
        f"- Method: `{payload['method']}`",
        f"- Status: `{payload['status']}`",
        f"- Selected challenge: `{s['selected_challenge_id']}`",
        f"- Boolean-aware verifier hash: `{s['boolean_aware_verifier_hash']}`",
        f"- Evaluation hash: `{s['evaluation_hash']}`",
        "",
        "## Result",
        "",
        (
            f"R51 passes {s['requirements_passed']}/{s['requirement_count']} "
            "requirements by fixing boolean-empty preflight semantics while keeping "
            "the actual C01 row rejected on the three source-backed flags."
        ),
        "",
        "## Gate Semantics",
        "",
        f"- Legacy semantic-flip empty keys: `{s['legacy_semantic_flip_empty_keys']}`",
        f"- Boolean-aware semantic-flip empty-key count: `{s['boolean_aware_semantic_flip_empty_key_count']}`",
        f"- Actual empty production keys: `{s['actual_empty_production_key_count']}`",
        f"- Actual file-hash failures: `{s['actual_file_hash_failure_count']}`",
        f"- Actual flag failures: `{s['actual_flag_failure_count']}`",
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
    parser.add_argument("--contract-input", type=Path, default=Path("results/B1_B7_cone01_o3_f4_numerical_refit_submissions/B1-B7-cone01-O3-F4-C2-C01-source-backed-row-intake.contract.json"))
    parser.add_argument("--r49-verifier", type=Path, default=Path("results/B1_B7_cone01_o3_f4_numerical_refit_submissions/B1-B7-cone01-O3-F4-C2-C01-source-backed-row-preflight.verifier.json"))
    parser.add_argument("--r50-result", type=Path, default=Path("results/B1_B7_cone01_R50_o3_f4_c2_c01_hash_matched_presubmission_gate_v0.json"))
    parser.add_argument("--presubmission-input", type=Path, default=Path("results/B1_B7_cone01_o3_f4_numerical_refit_submissions/source_backed_rows/O3-F4-C01.hash_matched_presubmission.json"))
    parser.add_argument("--verifier-output", type=Path, default=Path("results/B1_B7_cone01_o3_f4_numerical_refit_submissions/source_backed_rows/O3-F4-C01.boolean_aware_preflight.verifier.json"))
    parser.add_argument("--json-output", type=Path, default=Path("results/B1_B7_cone01_R51_o3_f4_c2_boolean_aware_preflight_gate_v0.json"))
    parser.add_argument("--markdown-output", type=Path, default=Path("research/B1_B7_cone01_R51_o3_f4_c2_boolean_aware_preflight_gate.md"))
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
                    "legacy_semantic_flip_empty_key_count": s["legacy_semantic_flip_empty_key_count"],
                    "boolean_aware_semantic_flip_empty_key_count": s["boolean_aware_semantic_flip_empty_key_count"],
                    "actual_empty_production_key_count": s["actual_empty_production_key_count"],
                    "actual_file_hash_failure_count": s["actual_file_hash_failure_count"],
                    "actual_flag_failure_count": s["actual_flag_failure_count"],
                    "accepted_source_backed_row_count": s["accepted_source_backed_row_count"],
                    "boolean_aware_verifier_hash": s["boolean_aware_verifier_hash"],
                    "evaluation_hash": s["evaluation_hash"],
                    "json_output": str(args.json_output),
                },
                indent=2,
                sort_keys=True,
            )
        )


if __name__ == "__main__":
    main()
