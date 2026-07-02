#!/usr/bin/env python3
"""T-B7-010d/T-B1-004cw: provenance manifest gate for w8_21 symbolic certificate."""

from __future__ import annotations

import argparse
import hashlib
import json
import time
from pathlib import Path
from typing import Any


METHOD = "b7_w8_21_symbolic_certificate_provenance_manifest_gate_v0"
STATUS = "w8_21_symbolic_certificate_provenance_manifest_open_missing_artifact"
MODEL_STATUS = "w8_21_symbolic_certificate_manifest_required_before_theory_artifact_acceptance"
VERSION = "0.1"
EXPECTED_PACKET_ID = "B7-S1-w8-21-symbolic-kak-obstruction"
EXPECTED_MANIFEST_ID = "B7S1-w8-21-symbolic-certificate-provenance-manifest"
EXPECTED_TEMPLATE_ID = "w8_21"
EXPECTED_FAILED_IDS = ["P6", "P7", "P8"]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any], pretty: bool) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(payload, indent=2 if pretty else None, sort_keys=True)
    path.write_text(text + "\n", encoding="utf-8")


def stable_hash(payload: Any) -> str:
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def requirement(requirement_id: str, label: str, passed: bool, evidence: dict[str, Any]) -> dict[str, Any]:
    return {
        "requirement_id": requirement_id,
        "label": label,
        "passed": bool(passed),
        "evidence": evidence,
    }


def build_payload(args: argparse.Namespace) -> dict[str, Any]:
    started = time.time()
    priority = load_json(args.priority_packet_gate)
    summary = priority["summary"]
    packet = priority["priority_symbolic_certificate_packet"]
    submission_path = args.submission_dir / f"{EXPECTED_MANIFEST_ID}.json"
    submitted_exists = submission_path.exists()
    submitted = load_json(submission_path) if submitted_exists else None

    required_manifest_keys = [
        "manifest_id",
        "packet_id",
        "template_id",
        "priority_packet_hash",
        "normalized_target_matrix_source_hash",
        "symbolic_coordinate_system_source_hash",
        "local_invariant_expression_source_hash",
        "tested_scaffold_exclusion_source_hash",
        "uncovered_route_statement_source_hash",
        "numeric_search_digest_source_hash",
        "theorem_or_notebook_environment_hash",
        "reproduction_command_hash",
        "claim_boundary",
    ]
    production_manifest_keys = [
        "normalized_target_matrix_source_hash",
        "symbolic_coordinate_system_source_hash",
        "local_invariant_expression_source_hash",
        "tested_scaffold_exclusion_source_hash",
        "uncovered_route_statement_source_hash",
        "theorem_or_notebook_environment_hash",
        "reproduction_command_hash",
    ]
    required_evidence_files = [
        "normalized_two_qubit_target_matrix_manifest",
        "symbolic_coordinate_system_note",
        "local_invariant_expression_derivation",
        "tested_scaffold_exclusion_table_source",
        "uncovered_global_route_statement",
        "numeric_search_digest_binding_43480_runs",
        "theorem_or_notebook_environment_manifest",
        "reproduction_command_manifest",
        "occurrence_ledger_nonpromotion_note",
        "claim_boundary_note",
    ]

    missing_keys = [key for key in required_manifest_keys if submitted is None or key not in submitted]
    production_present = [
        key for key in production_manifest_keys if submitted is not None and submitted.get(key) is not None
    ]
    replay_hashes = submitted.get("replay_hashes") if submitted else None
    replay_bound = (
        isinstance(replay_hashes, dict)
        and replay_hashes.get("priority_packet_hash") == summary.get("packet_hash")
        and replay_hashes.get("prior_optimizer_runs") == summary.get("prior_optimizer_runs")
        and replay_hashes.get("three_cnot_attempted_optimizer_runs")
        == summary.get("three_cnot_attempted_optimizer_runs")
    )
    source_backed = submitted is not None and submitted.get("source_evidence_files_present") is True
    manifest_bound = (
        submitted is not None
        and submitted.get("manifest_id") == EXPECTED_MANIFEST_ID
        and submitted.get("packet_id") == EXPECTED_PACKET_ID
        and submitted.get("template_id") == EXPECTED_TEMPLATE_ID
        and submitted.get("priority_packet_hash") == summary.get("packet_hash")
    )

    manifest_packet = {
        "manifest_id": EXPECTED_MANIFEST_ID,
        "packet_id": EXPECTED_PACKET_ID,
        "template_id": EXPECTED_TEMPLATE_ID,
        "source_priority_packet_gate": str(args.priority_packet_gate),
        "submission_artifact_path": str(submission_path),
        "priority_packet_hash": summary.get("packet_hash"),
        "prior_optimizer_runs": summary.get("prior_optimizer_runs"),
        "three_cnot_attempted_optimizer_runs": summary.get("three_cnot_attempted_optimizer_runs"),
        "three_cnot_passing_candidate_count": summary.get("three_cnot_passing_candidate_count"),
        "target_removed_arbitrary_occurrences": summary.get("target_removed_arbitrary_occurrences"),
        "target_removed_t_ledger": summary.get("target_removed_t_ledger"),
        "required_manifest_keys": required_manifest_keys,
        "production_manifest_keys": production_manifest_keys,
        "required_evidence_files": required_evidence_files,
        "accepted_only_if": [
            "manifest_id equals B7S1-w8-21-symbolic-certificate-provenance-manifest",
            "packet_id equals B7-S1-w8-21-symbolic-kak-obstruction",
            "template_id equals w8_21",
            "priority_packet_hash matches the source priority packet",
            "target-matrix, coordinate-system, invariant, exclusion-table, uncovered-route, notebook-environment, and reproduction-command hashes are present",
            "replay_hashes bind priority_packet_hash, 43,480 prior optimizer runs, and 8,880 three-CNOT attempted runs",
            "source evidence files are present and hash-bound",
            "claim_boundary forbids rewrite, global-lower-bound, resource-reduction, and B7-ledger-credit claims",
        ],
    }
    manifest_packet["manifest_hash"] = stable_hash(manifest_packet)

    requirements = [
        requirement(
            "P1",
            "Priority symbolic certificate packet remains valid and blocked only on P6/P7/P8",
            priority.get("method") == "b7_w8_21_symbolic_certificate_priority_packet_gate_v0"
            and summary.get("validation_error_count") == 0
            and summary.get("failed_priority_requirement_ids") == ["P6", "P7", "P8"],
            {
                "source_status": priority.get("status"),
                "failed_priority_requirement_ids": summary.get("failed_priority_requirement_ids"),
                "validation_error_count": summary.get("validation_error_count"),
            },
        ),
        requirement(
            "P2",
            "Manifest is bound to the w8_21 symbolic KAK obstruction packet",
            summary.get("priority_packet_id") == EXPECTED_PACKET_ID
            and summary.get("template_id") == EXPECTED_TEMPLATE_ID,
            {
                "priority_packet_id": summary.get("priority_packet_id"),
                "template_id": summary.get("template_id"),
            },
        ),
        requirement(
            "P3",
            "Manifest packet carries locked provenance schema and evidence file classes",
            len(required_manifest_keys) == 13
            and len(production_manifest_keys) == 7
            and len(required_evidence_files) == 10,
            {
                "required_manifest_key_count": len(required_manifest_keys),
                "production_manifest_key_count": len(production_manifest_keys),
                "required_evidence_file_count": len(required_evidence_files),
            },
        ),
        requirement(
            "P4",
            "Numerical negative boundary and target ledger pressure remain preserved",
            summary.get("prior_optimizer_runs") == 43480
            and summary.get("three_cnot_attempted_optimizer_runs") == 8880
            and summary.get("three_cnot_passing_candidate_count") == 0
            and summary.get("target_removed_arbitrary_occurrences") == 30
            and summary.get("target_removed_t_ledger") == 600,
            {
                "prior_optimizer_runs": summary.get("prior_optimizer_runs"),
                "three_cnot_attempted_optimizer_runs": summary.get(
                    "three_cnot_attempted_optimizer_runs"
                ),
                "three_cnot_passing_candidate_count": summary.get(
                    "three_cnot_passing_candidate_count"
                ),
                "target_removed_arbitrary_occurrences": summary.get(
                    "target_removed_arbitrary_occurrences"
                ),
                "target_removed_t_ledger": summary.get("target_removed_t_ledger"),
            },
        ),
        requirement(
            "P5",
            "Current B7 state has no accepted symbolic certificate or ledger credit",
            summary.get("accepted_symbolic_certificate_count") == 0
            and summary.get("ready_for_b7_ledger_retest_count") == 0
            and summary.get("b7_ledger_improvement_claimed") is False,
            {
                "accepted_symbolic_certificate_count": summary.get(
                    "accepted_symbolic_certificate_count"
                ),
                "ready_for_b7_ledger_retest_count": summary.get("ready_for_b7_ledger_retest_count"),
                "b7_ledger_improvement_claimed": summary.get("b7_ledger_improvement_claimed"),
            },
        ),
        requirement(
            "P6",
            "Provenance manifest artifact has been submitted",
            submitted_exists,
            {"submission_artifact_path": str(submission_path), "exists": submitted_exists},
        ),
        requirement(
            "P7",
            "Submitted manifest satisfies the locked provenance schema",
            submitted_exists and not missing_keys and len(production_present) == len(production_manifest_keys),
            {
                "missing_keys": missing_keys,
                "production_keys_present": production_present,
                "production_manifest_keys": production_manifest_keys,
                "submitted_key_count": len(submitted) if submitted else 0,
            },
        ),
        requirement(
            "P8",
            "Submitted manifest is source-backed, packet-bound, and replay-hash-bound",
            source_backed and manifest_bound and replay_bound,
            {
                "source_evidence_files_present": source_backed,
                "manifest_bound": manifest_bound,
                "replay_bound": replay_bound,
            },
        ),
        requirement(
            "P9",
            "Forbidden rewrite, lower-bound, resource, and ledger claims remain false",
            summary.get("new_rewrite_claimed") is False
            and summary.get("global_lower_bound_claimed") is False
            and summary.get("physical_resource_reduction_claimed") is False
            and summary.get("b7_ledger_improvement_claimed") is False,
            {
                "new_rewrite_claimed": summary.get("new_rewrite_claimed"),
                "global_lower_bound_claimed": summary.get("global_lower_bound_claimed"),
                "physical_resource_reduction_claimed": summary.get(
                    "physical_resource_reduction_claimed"
                ),
                "b7_ledger_improvement_claimed": summary.get("b7_ledger_improvement_claimed"),
            },
        ),
    ]

    passed = sum(row["passed"] for row in requirements)
    failed_ids = [row["requirement_id"] for row in requirements if not row["passed"]]
    validation_errors: list[str] = []
    if failed_ids != EXPECTED_FAILED_IDS:
        validation_errors.append(f"unexpected symbolic provenance manifest failures: {failed_ids}")
    if submitted_exists:
        validation_errors.append("gate expected no submitted provenance manifest until a theory PR supplies one")

    payload_summary = {
        "manifest_id": EXPECTED_MANIFEST_ID,
        "priority_packet_id": EXPECTED_PACKET_ID,
        "template_id": EXPECTED_TEMPLATE_ID,
        "priority_packet_hash": summary.get("packet_hash"),
        "manifest_hash": manifest_packet["manifest_hash"],
        "manifest_requirement_count": len(requirements),
        "manifest_requirements_passed": passed,
        "manifest_requirements_failed": len(requirements) - passed,
        "failed_manifest_requirement_ids": failed_ids,
        "required_manifest_key_count": len(required_manifest_keys),
        "production_manifest_key_count": len(production_manifest_keys),
        "required_evidence_file_count": len(required_evidence_files),
        "prior_optimizer_runs": summary.get("prior_optimizer_runs"),
        "three_cnot_attempted_optimizer_runs": summary.get("three_cnot_attempted_optimizer_runs"),
        "three_cnot_passing_candidate_count": summary.get("three_cnot_passing_candidate_count"),
        "target_removed_arbitrary_occurrences": summary.get("target_removed_arbitrary_occurrences"),
        "target_removed_t_ledger": summary.get("target_removed_t_ledger"),
        "submitted_manifest_exists": submitted_exists,
        "submitted_key_count": len(submitted) if submitted else 0,
        "missing_key_count": len(missing_keys),
        "production_keys_present_count": len(production_present),
        "accepted_symbolic_certificate_count": 0,
        "ready_for_b7_ledger_retest_count": 0,
        "new_rewrite_claimed": False,
        "global_lower_bound_claimed": False,
        "physical_resource_reduction_claimed": False,
        "b7_ledger_improvement_claimed": False,
        "validation_error_count": len(validation_errors),
    }

    return {
        "benchmark_id": "B7",
        "linked_benchmark_id": "B1",
        "problem_id": 21,
        "title": "B7 w8_21 Symbolic Certificate Provenance Manifest Gate",
        "version": VERSION,
        "last_updated": args.last_updated,
        "method": METHOD,
        "status": STATUS,
        "model_status": MODEL_STATUS,
        "source_priority_packet_gate": str(args.priority_packet_gate),
        "summary": payload_summary,
        "provenance_manifest_packet": manifest_packet,
        "requirements": requirements,
        "claim_boundary": {
            "what_is_supported": (
                "The first B7 w8_21 symbolic certificate route now has a provenance "
                "manifest packet that must bind target matrix, symbolic coordinates, "
                "local invariants, exclusion tables, notebook environment, and replay "
                "hashes before a theory artifact can be accepted."
            ),
            "what_is_not_supported": (
                "No provenance manifest or symbolic certificate has been submitted or "
                "accepted; no occurrence-removing rewrite, global lower bound, resource "
                "reduction, or B7 ledger improvement is supported."
            ),
            "next_gate": (
                f"Submit {submission_path} before the symbolic certificate JSON artifact, "
                "then rerun this gate and the priority packet gate."
            ),
            "new_rewrite_claimed": False,
            "global_lower_bound_claimed": False,
            "physical_resource_reduction_claimed": False,
            "b7_ledger_improvement_claimed": False,
        },
        "validation_errors": validation_errors,
        "runtime_seconds": round(time.time() - started, 6),
    }


def write_markdown(payload: dict[str, Any], path: Path) -> None:
    summary = payload["summary"]
    packet = payload["provenance_manifest_packet"]
    lines = [
        "# B7 w8_21 Symbolic Certificate Provenance Manifest Gate",
        "",
        f"Status: `{payload['status']}`",
        "",
        "## Summary",
        "",
        f"- Method: `{payload['method']}`",
        f"- Manifest: `{summary['manifest_id']}`",
        f"- Priority packet: `{summary['priority_packet_id']}`",
        f"- Manifest hash: `{summary['manifest_hash']}`",
        f"- Requirements passed/failed: `{summary['manifest_requirements_passed']}` / `{summary['manifest_requirements_failed']}`",
        f"- Failed requirement IDs: `{summary['failed_manifest_requirement_ids']}`",
        f"- Required manifest keys / production manifest keys / evidence files: `{summary['required_manifest_key_count']}` / `{summary['production_manifest_key_count']}` / `{summary['required_evidence_file_count']}`",
        f"- Prior optimizer runs: `{summary['prior_optimizer_runs']}`",
        f"- Three-CNOT attempted runs / passing candidates: `{summary['three_cnot_attempted_optimizer_runs']}` / `{summary['three_cnot_passing_candidate_count']}`",
        f"- Target arbitrary removals / proxy-T ledger: `{summary['target_removed_arbitrary_occurrences']}` / `{summary['target_removed_t_ledger']}`",
        f"- Submitted manifest exists: `{summary['submitted_manifest_exists']}`",
        f"- Accepted symbolic certificates: `{summary['accepted_symbolic_certificate_count']}`",
        f"- validation_error_count: `{summary['validation_error_count']}`",
        "",
        "## Provenance Manifest Packet",
        "",
        f"- Submission path: `{packet['submission_artifact_path']}`",
        f"- Priority packet hash: `{packet['priority_packet_hash']}`",
        "",
        "Required evidence files:",
        "",
    ]
    for item in packet["required_evidence_files"]:
        lines.append(f"- {item}")
    lines.extend(["", "Acceptance predicates:", ""])
    for item in packet["accepted_only_if"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Requirement Results", ""])
    for item in payload["requirements"]:
        state = "PASS" if item["passed"] else "FAIL"
        lines.append(f"- {item['requirement_id']} [{state}]: {item['label']}")
    lines.extend(
        [
            "",
            "## Claim Boundary",
            "",
            f"- Supported: {payload['claim_boundary']['what_is_supported']}",
            f"- Not supported: {payload['claim_boundary']['what_is_not_supported']}",
            f"- Next gate: {payload['claim_boundary']['next_gate']}",
            f"- new_rewrite_claimed: {payload['claim_boundary']['new_rewrite_claimed']}",
            f"- global_lower_bound_claimed: {payload['claim_boundary']['global_lower_bound_claimed']}",
            f"- physical_resource_reduction_claimed: {payload['claim_boundary']['physical_resource_reduction_claimed']}",
            f"- b7_ledger_improvement_claimed: {payload['claim_boundary']['b7_ledger_improvement_claimed']}",
            "",
            "## Validation",
            "",
            f"- validation_error_count: {summary['validation_error_count']}",
        ]
    )
    if payload["validation_errors"]:
        lines.extend(f"- {error}" for error in payload["validation_errors"])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--priority-packet-gate",
        type=Path,
        default=Path("results/B7_w8_21_symbolic_certificate_priority_packet_gate_v0.json"),
    )
    parser.add_argument(
        "--submission-dir",
        type=Path,
        default=Path("results/B7_w8_21_symbolic_certificate_provenance_manifest_submissions"),
    )
    parser.add_argument(
        "--json-output",
        type=Path,
        default=Path("results/B7_w8_21_symbolic_certificate_provenance_manifest_gate_v0.json"),
    )
    parser.add_argument(
        "--markdown-output",
        type=Path,
        default=Path("research/B7_w8_21_symbolic_certificate_provenance_manifest_gate.md"),
    )
    parser.add_argument("--last-updated", default="2026-07-02")
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()

    payload = build_payload(args)
    write_json(args.json_output, payload, args.pretty)
    write_markdown(payload, args.markdown_output)
    print(json.dumps(payload["summary"], indent=2 if args.pretty else None, sort_keys=True))
    if payload["validation_errors"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
