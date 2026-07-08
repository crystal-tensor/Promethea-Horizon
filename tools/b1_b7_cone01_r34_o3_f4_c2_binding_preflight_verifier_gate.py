#!/usr/bin/env python3
"""T-B1-004ej/T-B7-013s: R34 O3-F4 C2 binding preflight verifier gate."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import time
from pathlib import Path
from typing import Any


METHOD = "b1_b7_cone01_r34_o3_f4_c2_binding_preflight_verifier_gate_v0"
STATUS = "cone01_r34_o3_f4_c2_binding_preflight_verifier_rejects_template"
MODEL_STATUS = "o3_f4_c2_binding_preflight_verifier_ready_no_c2_acceptance"
VERSION = "0.1"
TARGET_ID = "T-B1-004ej/T-B7-013s"
UPSTREAM_TARGET_ID = "T-B1-004ei/T-B7-013r"
FAMILY_ID = "O3-F4"
CANDIDATE_ID = "NL-C02"
STRICT_TOLERANCE = 1.0e-8
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


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


def requirement(
    requirement_id: str, label: str, passed: bool, evidence: dict[str, Any]
) -> dict[str, Any]:
    return {
        "requirement_id": requirement_id,
        "label": label,
        "passed": bool(passed),
        "evidence": evidence,
    }


def is_placeholder(value: Any) -> bool:
    return isinstance(value, str) and value.startswith("<") and value.endswith(">")


def is_sha256(value: Any) -> bool:
    return isinstance(value, str) and bool(SHA256_RE.fullmatch(value))


def recompute_template_hash(template: dict[str, Any]) -> str:
    template_without_hash = dict(template)
    template_without_hash.pop("template_hash", None)
    return stable_hash(template_without_hash)


def verify_row(
    row: dict[str, Any],
    contract: dict[str, Any],
    strict_tolerance: float,
) -> dict[str, Any]:
    binding_fields = contract["binding_fields"]
    required_artifacts = contract["required_execution_artifacts"]
    binding_payload = row.get("binding_payload", {})
    execution_artifacts = row.get("execution_artifacts", {})
    missing_binding_fields = [
        field for field in binding_fields if field not in binding_payload
    ]
    placeholder_binding_fields = [
        field for field in binding_fields if is_placeholder(binding_payload.get(field))
    ]
    missing_artifacts = [
        field for field in required_artifacts if field not in execution_artifacts
    ]
    placeholder_artifacts = [
        field for field in required_artifacts if is_placeholder(execution_artifacts.get(field))
    ]
    hash_cells = {
        "declared_provenance_binding_hash": row.get(
            "declared_provenance_binding_hash"
        ),
        "binding_payload.source_circuit_hash": binding_payload.get(
            "source_circuit_hash"
        ),
        "binding_payload.candidate_circuit_hash": binding_payload.get(
            "candidate_circuit_hash"
        ),
        "binding_payload.replay_stdout_hash": binding_payload.get(
            "replay_stdout_hash"
        ),
        "execution_artifacts.replay_stdout_hash": execution_artifacts.get(
            "replay_stdout_hash"
        ),
        "execution_artifacts.source_circuit_hash": execution_artifacts.get(
            "source_circuit_hash"
        ),
        "execution_artifacts.candidate_circuit_hash": execution_artifacts.get(
            "candidate_circuit_hash"
        ),
        "execution_artifacts.same_unitary_witness_hash": execution_artifacts.get(
            "same_unitary_witness_hash"
        ),
        "execution_artifacts.provenance_binding_hash": execution_artifacts.get(
            "provenance_binding_hash"
        ),
    }
    invalid_hash_cells = [
        key for key, value in hash_cells.items() if not is_sha256(value)
    ]
    declared_binding_hash = row.get("declared_provenance_binding_hash")
    recomputed_binding_hash = stable_hash(binding_payload)
    binding_hash_matches = declared_binding_hash == recomputed_binding_hash
    try:
        replay_error = float(row.get("max_unitary_replay_error"))
        replay_error_numeric = True
        replay_error_within_tolerance = replay_error <= strict_tolerance
    except (TypeError, ValueError):
        replay_error = None
        replay_error_numeric = False
        replay_error_within_tolerance = False
    claim_boundary = str(row.get("claim_boundary", ""))
    zero_credit_boundary_present = all(
        token in claim_boundary for token in ["no C2", "O3", "reroute", "B7", "STV"]
    )
    passed = (
        not missing_binding_fields
        and not placeholder_binding_fields
        and not missing_artifacts
        and not placeholder_artifacts
        and not invalid_hash_cells
        and binding_hash_matches
        and replay_error_numeric
        and replay_error_within_tolerance
        and zero_credit_boundary_present
    )
    return {
        "challenge_id": row.get("challenge_id"),
        "passed": passed,
        "missing_binding_fields": missing_binding_fields,
        "placeholder_binding_fields": placeholder_binding_fields,
        "missing_artifacts": missing_artifacts,
        "placeholder_artifacts": placeholder_artifacts,
        "invalid_hash_cells": invalid_hash_cells,
        "declared_provenance_binding_hash": declared_binding_hash,
        "recomputed_provenance_binding_hash": recomputed_binding_hash,
        "binding_hash_matches": binding_hash_matches,
        "max_unitary_replay_error": replay_error,
        "replay_error_numeric": replay_error_numeric,
        "replay_error_within_tolerance": replay_error_within_tolerance,
        "zero_credit_boundary_present": zero_credit_boundary_present,
    }


def evaluate_submission(
    r33: dict[str, Any],
    template: dict[str, Any],
    template_path: Path,
) -> dict[str, Any]:
    packet = r33["o3_f4_c2_provenance_binding_contract_packet"]
    contract = packet["contract"]
    rows = template.get("rows", [])
    row_results = [
        verify_row(row, contract, float(contract["strict_tolerance"])) for row in rows
    ]
    recomputed_template_hash = recompute_template_hash(template)
    evaluation = {
        "input_artifact": str(template_path),
        "input_artifact_sha256": file_hash(template_path),
        "contract_hash": contract["contract_hash"],
        "template_declared_hash": template.get("template_hash"),
        "template_recomputed_hash": recomputed_template_hash,
        "template_hash_matches": template.get("template_hash")
        == recomputed_template_hash,
        "row_count": len(rows),
        "required_row_count": contract["required_row_count"],
        "row_results": row_results,
        "rows_passed": sum(1 for row in row_results if row["passed"]),
        "rows_failed": sum(1 for row in row_results if not row["passed"]),
        "placeholder_binding_field_count": sum(
            len(row["placeholder_binding_fields"]) for row in row_results
        ),
        "placeholder_execution_artifact_count": sum(
            len(row["placeholder_artifacts"]) for row in row_results
        ),
        "invalid_hash_cell_count": sum(
            len(row["invalid_hash_cells"]) for row in row_results
        ),
        "binding_mismatch_count": sum(
            1 for row in row_results if not row["binding_hash_matches"]
        ),
        "nonnumeric_replay_error_count": sum(
            1 for row in row_results if not row["replay_error_numeric"]
        ),
        "zero_credit_boundary_failures": sum(
            1 for row in row_results if not row["zero_credit_boundary_present"]
        ),
        "accepted": False,
    }
    evaluation["accepted"] = (
        evaluation["template_hash_matches"]
        and evaluation["row_count"] == evaluation["required_row_count"]
        and evaluation["rows_passed"] == evaluation["required_row_count"]
        and template.get("o3_closed") is False
        and template.get("reroute_allowed") is False
        and template.get("b7_credit_delta") == 0
    )
    evaluation["failed_reasons"] = []
    if evaluation["row_count"] != evaluation["required_row_count"]:
        evaluation["failed_reasons"].append("row_count_mismatch")
    if evaluation["placeholder_binding_field_count"]:
        evaluation["failed_reasons"].append("placeholder_binding_fields")
    if evaluation["placeholder_execution_artifact_count"]:
        evaluation["failed_reasons"].append("placeholder_execution_artifacts")
    if evaluation["invalid_hash_cell_count"]:
        evaluation["failed_reasons"].append("invalid_hash_cells")
    if evaluation["binding_mismatch_count"]:
        evaluation["failed_reasons"].append("provenance_binding_hash_mismatch")
    if evaluation["nonnumeric_replay_error_count"]:
        evaluation["failed_reasons"].append("nonnumeric_replay_errors")
    if evaluation["zero_credit_boundary_failures"]:
        evaluation["failed_reasons"].append("missing_zero_credit_boundary")
    evaluation["preflight_hash"] = stable_hash(evaluation)
    return evaluation


def build_payload(args: argparse.Namespace) -> dict[str, Any]:
    started = time.time()
    r33 = load_json(args.r33_contract)
    template = load_json(args.template_input)
    packet = r33["o3_f4_c2_provenance_binding_contract_packet"]
    contract = packet["contract"]
    evaluation = evaluate_submission(r33, template, args.template_input)
    requirements = [
        requirement(
            "S1",
            "R33 source contract is validation-clean and still has no accepted C2 submission",
            r33["summary"].get("validation_error_count") == 0
            and r33["summary"].get("c2_provenance_binding_contract_ready") is True
            and r33["summary"].get("c2_provenance_submission_accepted") is False,
            {
                "r33_validation_error_count": r33["summary"].get(
                    "validation_error_count"
                ),
                "c2_provenance_binding_contract_ready": r33["summary"].get(
                    "c2_provenance_binding_contract_ready"
                ),
                "c2_provenance_submission_accepted": r33["summary"].get(
                    "c2_provenance_submission_accepted"
                ),
            },
        ),
        requirement(
            "S2",
            "Template is bound to the R33 contract hash",
            template.get("contract_hash") == contract["contract_hash"],
            {
                "template_contract_hash": template.get("contract_hash"),
                "r33_contract_hash": contract["contract_hash"],
            },
        ),
        requirement(
            "S3",
            "Template hash recomputes before row-level validation",
            evaluation["template_hash_matches"],
            {
                "template_declared_hash": evaluation["template_declared_hash"],
                "template_recomputed_hash": evaluation["template_recomputed_hash"],
            },
        ),
        requirement(
            "S4",
            "Verifier checks all 8 required C2 rows",
            evaluation["row_count"] == evaluation["required_row_count"] == 8,
            {
                "row_count": evaluation["row_count"],
                "required_row_count": evaluation["required_row_count"],
            },
        ),
        requirement(
            "S5",
            "Verifier rejects the placeholder template rather than treating it as progress",
            evaluation["accepted"] is False
            and evaluation["rows_passed"] == 0
            and evaluation["placeholder_binding_field_count"] == 88
            and evaluation["placeholder_execution_artifact_count"] == 72,
            {
                "accepted": evaluation["accepted"],
                "rows_passed": evaluation["rows_passed"],
                "placeholder_binding_field_count": evaluation[
                    "placeholder_binding_field_count"
                ],
                "placeholder_execution_artifact_count": evaluation[
                    "placeholder_execution_artifact_count"
                ],
                "failed_reasons": evaluation["failed_reasons"],
            },
        ),
        requirement(
            "S6",
            "Verifier rejects hash-shaped theatre by recomputing row provenance bindings",
            evaluation["binding_mismatch_count"] == 8
            and evaluation["invalid_hash_cell_count"] == 72,
            {
                "binding_mismatch_count": evaluation["binding_mismatch_count"],
                "invalid_hash_cell_count": evaluation["invalid_hash_cell_count"],
            },
        ),
        requirement(
            "S7",
            "Verifier enforces numeric replay evidence under strict tolerance",
            evaluation["nonnumeric_replay_error_count"] == 8
            and evaluation["rows_passed"] == 0,
            {
                "strict_tolerance": STRICT_TOLERANCE,
                "nonnumeric_replay_error_count": evaluation[
                    "nonnumeric_replay_error_count"
                ],
                "rows_passed": evaluation["rows_passed"],
            },
        ),
        requirement(
            "S8",
            "R34 preserves the zero-credit boundary",
            template.get("o3_closed") is False
            and template.get("reroute_allowed") is False
            and template.get("b7_credit_delta") == 0
            and evaluation["zero_credit_boundary_failures"] == 0,
            {
                "o3_closed": template.get("o3_closed"),
                "reroute_allowed": template.get("reroute_allowed"),
                "b7_credit_delta": template.get("b7_credit_delta"),
                "zero_credit_boundary_failures": evaluation[
                    "zero_credit_boundary_failures"
                ],
            },
        ),
    ]
    failed_requirements = [
        item["requirement_id"] for item in requirements if not item["passed"]
    ]
    summary = {
        "candidate_id": CANDIDATE_ID,
        "family_id": FAMILY_ID,
        "source_r33_contract_hash": contract["contract_hash"],
        "source_r33_template_hash": r33["summary"]["template_hash"],
        "source_r33_preflight_hash": r33["summary"]["preflight_hash"],
        "source_r33_file_sha256": file_hash(args.r33_contract),
        "template_file_sha256": file_hash(args.template_input),
        "template_recomputed_hash": evaluation["template_recomputed_hash"],
        "preflight_hash": evaluation["preflight_hash"],
        "strict_tolerance": STRICT_TOLERANCE,
        "binding_field_count": len(contract["binding_fields"]),
        "required_execution_artifact_count": len(
            contract["required_execution_artifacts"]
        ),
        "template_row_count": evaluation["row_count"],
        "rows_passed": evaluation["rows_passed"],
        "rows_failed": evaluation["rows_failed"],
        "placeholder_binding_field_count": evaluation[
            "placeholder_binding_field_count"
        ],
        "placeholder_execution_artifact_count": evaluation[
            "placeholder_execution_artifact_count"
        ],
        "invalid_hash_cell_count": evaluation["invalid_hash_cell_count"],
        "binding_mismatch_count": evaluation["binding_mismatch_count"],
        "nonnumeric_replay_error_count": evaluation["nonnumeric_replay_error_count"],
        "zero_credit_boundary_failures": evaluation["zero_credit_boundary_failures"],
        "binding_preflight_verifier_ready": True,
        "c2_provenance_binding_contract_ready": True,
        "c2_provenance_submission_accepted": False,
        "c2_strict_replay_rows_accepted": False,
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
            "C2_source_backed_execution_artifacts",
            "C2_valid_sha256_artifact_hashes",
            "C2_numeric_replay_errors_lte_1e-08",
            "C2_recomputed_provenance_binding_hashes",
            "C3_same_unitary_replay_certificate",
            "C4_C5_same_access_denominator_comparison",
            "C6_leakage_free_optimizer_trace",
            "C7_machine_check_replay_bundle",
        ],
        "remaining_open_obligation_count": 8,
        "requirement_count": len(requirements),
        "requirements_passed": len(requirements) - len(failed_requirements),
        "requirements_failed": len(failed_requirements),
        "failed_requirement_ids": failed_requirements,
        "validation_error_count": len(failed_requirements),
    }
    return {
        "title": "B1/B7 Cone01 R34 O3-F4 C2 Binding Preflight Verifier Gate",
        "version": VERSION,
        "last_updated": "2026-07-08",
        "benchmark_id": "B1",
        "linked_benchmark_id": "B7",
        "method": METHOD,
        "status": STATUS,
        "model_status": MODEL_STATUS,
        "source_target_id": TARGET_ID,
        "upstream_target_id": UPSTREAM_TARGET_ID,
        "o3_f4_c2_binding_preflight_verifier_packet": {
            "source_r33_contract": str(args.r33_contract),
            "template_input": str(args.template_input),
            "evaluation": evaluation,
        },
        "requirements": requirements,
        "summary": summary,
        "claim_boundary": {
            "what_is_supported": (
                "R34 implements a runnable C2 provenance-binding preflight "
                "verifier and proves that the R33 placeholder template is rejected."
            ),
            "what_is_not_supported": (
                "R34 does not accept a C2 submission, does not close O3, and "
                "does not permit reroute, B7 credit, STV credit, or resource-saving claims."
            ),
            "next_gate": (
                "Submit a non-placeholder C2 artifact with source-backed execution "
                "files, valid sha256 hashes, numeric replay errors <= 1e-08, and "
                "row provenance binding hashes that recompute."
            ),
            "resource_saving_claimed": False,
            "b7_ledger_improvement_claimed": False,
        },
        "validation_errors": failed_requirements,
        "runtime_seconds": round(time.time() - started, 6),
    }


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    summary = payload["summary"]
    lines = [
        "# B1/B7 Cone01 R34 O3-F4 C2 Binding Preflight Verifier Gate",
        "",
        f"- Target: `{payload['source_target_id']}`",
        f"- Upstream target: `{payload['upstream_target_id']}`",
        f"- Method: `{payload['method']}`",
        f"- Status: `{payload['status']}`",
        f"- Source R33 contract hash: `{summary['source_r33_contract_hash']}`",
        f"- Template recomputed hash: `{summary['template_recomputed_hash']}`",
        f"- Preflight hash: `{summary['preflight_hash']}`",
        "",
        "## Result",
        "",
        (
            f"R34 passes {summary['requirements_passed']}/"
            f"{summary['requirement_count']} requirements by implementing a "
            "runnable C2 binding preflight verifier and rejecting the current "
            "R33 placeholder template."
        ),
        "",
        "## Rejection Surface",
        "",
        f"- Rows passed / failed: `{summary['rows_passed']}` / `{summary['rows_failed']}`",
        f"- Placeholder binding fields: `{summary['placeholder_binding_field_count']}`",
        f"- Placeholder execution artifacts: `{summary['placeholder_execution_artifact_count']}`",
        f"- Invalid hash cells: `{summary['invalid_hash_cell_count']}`",
        f"- Binding mismatches: `{summary['binding_mismatch_count']}`",
        f"- Nonnumeric replay errors: `{summary['nonnumeric_replay_error_count']}`",
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
        "--r33-contract",
        type=Path,
        default=Path(
            "results/B1_B7_cone01_R33_o3_f4_c2_provenance_binding_contract_gate_v0.json"
        ),
    )
    parser.add_argument(
        "--template-input",
        type=Path,
        default=Path(
            "results/B1_B7_cone01_o3_f4_numerical_refit_submissions/"
            "B1-B7-cone01-O3-F4-C2-provenance-binding-submission.template.json"
        ),
    )
    parser.add_argument(
        "--json-output",
        type=Path,
        default=Path(
            "results/B1_B7_cone01_R34_o3_f4_c2_binding_preflight_verifier_gate_v0.json"
        ),
    )
    parser.add_argument(
        "--markdown-output",
        type=Path,
        default=Path(
            "research/B1_B7_cone01_R34_o3_f4_c2_binding_preflight_verifier_gate.md"
        ),
    )
    parser.add_argument("--pretty", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    payload = build_payload(args)
    write_json(args.json_output, payload, pretty=True)
    write_markdown(args.markdown_output, payload)
    if args.pretty:
        print(
            json.dumps(
                {
                    "status": payload["status"],
                    "requirements_passed": payload["summary"]["requirements_passed"],
                    "requirements_failed": payload["summary"]["requirements_failed"],
                    "preflight_hash": payload["summary"]["preflight_hash"],
                    "rows_passed": payload["summary"]["rows_passed"],
                    "rows_failed": payload["summary"]["rows_failed"],
                    "placeholder_binding_field_count": payload["summary"][
                        "placeholder_binding_field_count"
                    ],
                    "placeholder_execution_artifact_count": payload["summary"][
                        "placeholder_execution_artifact_count"
                    ],
                    "invalid_hash_cell_count": payload["summary"][
                        "invalid_hash_cell_count"
                    ],
                    "binding_mismatch_count": payload["summary"][
                        "binding_mismatch_count"
                    ],
                    "nonnumeric_replay_error_count": payload["summary"][
                        "nonnumeric_replay_error_count"
                    ],
                    "c2_strict_replay_rows_accepted": payload["summary"][
                        "c2_strict_replay_rows_accepted"
                    ],
                    "o3_closed": payload["summary"]["o3_closed"],
                    "reroute_allowed": payload["summary"]["reroute_allowed"],
                    "b7_credit_delta": payload["summary"]["b7_credit_delta"],
                    "json_output": str(args.json_output),
                    "markdown_output": str(args.markdown_output),
                },
                indent=2,
                sort_keys=True,
            )
        )


if __name__ == "__main__":
    main()
