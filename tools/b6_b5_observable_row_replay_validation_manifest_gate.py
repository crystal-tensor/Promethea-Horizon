#!/usr/bin/env python3
"""T-B6-005j/T-B5-006r: DFT/B5 observable row replay-validation manifest gate."""

from __future__ import annotations

import argparse
import hashlib
import json
import time
from pathlib import Path
from typing import Any


METHOD = "b6_b5_observable_row_replay_validation_manifest_gate_v0"
STATUS = "observable_row_replay_validation_manifest_open_missing_artifact"
MODEL_STATUS = "observable_row_replay_validation_manifest_required_before_priority_dft_b5_rows"
VERSION = "0.1"
EXPECTED_REPLAY_MANIFEST_ID = "B6B5-O1-monolayer-FeSe-STO-replay-validation-manifest"
EXPECTED_ROW_REPLAY_MANIFEST_ID = "B6B5-O1-monolayer-FeSe-STO-row-replay-validation-manifest"
EXPECTED_MATERIAL_ID = "monolayer_FeSe_STO_2012"
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
    replay = load_json(args.replay_validation_manifest_gate)
    intake = load_json(args.intake_template_gate)
    replay_summary = replay["summary"]
    replay_packet = replay["observable_replay_validation_manifest_packet"]
    intake_summary = intake["summary"]
    submission_path = args.submission_dir / f"{EXPECTED_ROW_REPLAY_MANIFEST_ID}.json"
    submitted_exists = submission_path.exists()
    submitted = load_json(submission_path) if submitted_exists else None

    required_keys = [
        "manifest_id",
        "source_replay_validation_manifest_id",
        "material_id",
        "replay_validation_manifest_hash",
        "provenance_manifest_hash",
        "template_table_hash",
        "dft_row_table_hash",
        "b5_observable_row_table_hash",
        "structure_reference_hash",
        "dft_input_deck_replay_hash",
        "dft_output_parser_replay_hash",
        "effective_model_mapping_hash",
        "b5_solver_observable_replay_hash",
        "same_access_cost_ledger_hash",
        "negative_control_audit_hash",
        "family_prior_denominator_hash",
        "row_acceptance_ledger_hash",
        "claim_boundary",
    ]
    production_required_keys = [
        "replay_validation_manifest_hash",
        "provenance_manifest_hash",
        "template_table_hash",
        "dft_row_table_hash",
        "b5_observable_row_table_hash",
        "structure_reference_hash",
        "dft_input_deck_replay_hash",
        "dft_output_parser_replay_hash",
        "effective_model_mapping_hash",
        "b5_solver_observable_replay_hash",
        "same_access_cost_ledger_hash",
        "negative_control_audit_hash",
        "family_prior_denominator_hash",
        "row_acceptance_ledger_hash",
        "claim_boundary",
    ]
    evidence_files = [
        "accepted_observable_replay_validation_manifest",
        "observable_row_template_table",
        "dft_row_table",
        "b5_observable_row_table",
        "structure_reference_manifest",
        "dft_input_deck_replay",
        "dft_output_parser_replay",
        "effective_model_mapping",
        "b5_solver_observable_replay",
        "same_access_cost_ledger",
        "negative_control_audit",
        "family_prior_denominator_table",
        "row_acceptance_ledger",
        "claim_boundary_note",
    ]

    missing_keys = [key for key in required_keys if submitted is None or key not in submitted]
    production_present = [
        key for key in production_required_keys if submitted is not None and submitted.get(key) is not None
    ]
    source_hashes = submitted.get("source_replay_hashes") if submitted else None
    replay_bound = (
        isinstance(source_hashes, dict)
        and source_hashes.get("replay_validation_manifest_hash") == replay_summary.get("manifest_hash")
        and source_hashes.get("provenance_manifest_hash")
        == replay_summary.get("provenance_manifest_hash")
        and source_hashes.get("source_table_hash") == replay_summary.get("source_table_hash")
        and source_hashes.get("replay_formula_hash") == replay_summary.get("replay_formula_hash")
        and source_hashes.get("replay_table_hash") == replay_summary.get("replay_table_hash")
        and source_hashes.get("template_table_hash") == intake_summary.get("template_table_hash")
    )
    source_backed = submitted is not None and submitted.get("source_evidence_files_present") is True
    manifest_bound = (
        submitted is not None
        and submitted.get("manifest_id") == EXPECTED_ROW_REPLAY_MANIFEST_ID
        and submitted.get("source_replay_validation_manifest_id") == EXPECTED_REPLAY_MANIFEST_ID
        and submitted.get("material_id") == EXPECTED_MATERIAL_ID
        and submitted.get("replay_validation_manifest_hash") == replay_summary.get("manifest_hash")
        and submitted.get("provenance_manifest_hash") == replay_summary.get("provenance_manifest_hash")
    )
    claim_boundary_bound = (
        submitted is not None
        and isinstance(submitted.get("claim_boundary"), dict)
        and submitted["claim_boundary"].get("accepted_priority_dft_rows") == 0
        and submitted["claim_boundary"].get("accepted_priority_b5_rows") == 0
        and submitted["claim_boundary"].get("dft_observable_claimed") is False
        and submitted["claim_boundary"].get("b5_computed_observable_claimed") is False
        and submitted["claim_boundary"].get("material_discovery_claimed") is False
        and submitted["claim_boundary"].get("mechanism_solved") is False
        and submitted["claim_boundary"].get("solution_claimed") is False
    )

    row_packet = {
        "manifest_id": EXPECTED_ROW_REPLAY_MANIFEST_ID,
        "source_replay_validation_manifest_id": EXPECTED_REPLAY_MANIFEST_ID,
        "material_id": EXPECTED_MATERIAL_ID,
        "source_replay_validation_manifest_gate": str(args.replay_validation_manifest_gate),
        "source_intake_template_gate": str(args.intake_template_gate),
        "submission_artifact_path": str(submission_path),
        "replay_validation_manifest_hash": replay_summary.get("manifest_hash"),
        "provenance_manifest_hash": replay_summary.get("provenance_manifest_hash"),
        "template_table_hash": intake_summary.get("template_table_hash"),
        "source_table_hash": replay_summary.get("source_table_hash"),
        "replay_formula_hash": replay_summary.get("replay_formula_hash"),
        "replay_table_hash": replay_summary.get("replay_table_hash"),
        "record_count": replay_summary.get("record_count"),
        "family_count": replay_summary.get("family_count"),
        "negative_control_count": replay_summary.get("negative_control_count"),
        "post_split_record_count": replay_summary.get("post_split_record_count"),
        "selected_negative_controls_in_top_k": replay_summary.get("selected_negative_controls_in_top_k"),
        "required_keys": required_keys,
        "production_required_keys": production_required_keys,
        "required_evidence_files": evidence_files,
        "accepted_only_if": [
            "manifest_id equals B6B5-O1-monolayer-FeSe-STO-row-replay-validation-manifest",
            "source_replay_validation_manifest_id equals B6B5-O1-monolayer-FeSe-STO-replay-validation-manifest",
            "material_id equals monolayer_FeSe_STO_2012",
            "replay_validation_manifest_hash, provenance_manifest_hash, and template_table_hash match source gates",
            "DFT row table, B5 observable row table, structure reference, DFT input/output replay, effective-model mapping, B5 solver replay, same-access ledger, negative-control audit, family-prior denominator, and row-acceptance ledger are hash-bound",
            "row_acceptance_ledger keeps accepted DFT/B5 rows at 0 until both channels are submitted and audited",
            "source evidence files are present and source_replay_hashes bind the source table, formula, replay table, replay-validation manifest, provenance manifest, and template table",
            "claim_boundary forbids DFT-observable, B5-observable, material-discovery, mechanism-solved, and solution claims until rows are accepted",
        ],
    }
    row_packet["manifest_hash"] = stable_hash(row_packet)

    forbidden_claims = [
        "dft_observable_claimed",
        "b5_computed_observable_claimed",
        "material_discovery_claimed",
        "mechanism_solved",
        "solution_claimed",
    ]
    requirements = [
        requirement(
            "P1",
            "Observable replay-validation manifest gate remains valid and blocked only on P6/P7/P8",
            replay.get("method") == "b6_b5_observable_replay_validation_manifest_gate_v0"
            and replay_summary.get("validation_error_count") == 0
            and replay_summary.get("failed_manifest_requirement_ids") == ["P6", "P7", "P8"],
            {
                "source_status": replay.get("status"),
                "failed_manifest_requirement_ids": replay_summary.get("failed_manifest_requirement_ids"),
                "validation_error_count": replay_summary.get("validation_error_count"),
            },
        ),
        requirement(
            "P2",
            "Row replay manifest is bound to rank-1 monolayer FeSe/STO and source replay manifest",
            replay_summary.get("manifest_id") == EXPECTED_REPLAY_MANIFEST_ID
            and replay_summary.get("priority_material_id") == EXPECTED_MATERIAL_ID
            and replay_packet.get("manifest_hash") == replay_summary.get("manifest_hash"),
            {
                "source_replay_validation_manifest_id": replay_summary.get("manifest_id"),
                "priority_material_id": replay_summary.get("priority_material_id"),
                "replay_validation_manifest_hash": replay_summary.get("manifest_hash"),
            },
        ),
        requirement(
            "P3",
            "Row replay packet carries locked DFT/B5 schema and evidence classes",
            len(required_keys) == 18
            and len(production_required_keys) == 15
            and len(evidence_files) == 14,
            {
                "required_key_count": len(required_keys),
                "production_required_key_count": len(production_required_keys),
                "required_evidence_file_count": len(evidence_files),
            },
        ),
        requirement(
            "P4",
            "Replay scope, template table, and negative-control denominator remain preserved",
            replay_summary.get("record_count") == 56
            and replay_summary.get("family_count") == 28
            and replay_summary.get("negative_control_count") == 18
            and replay_summary.get("selected_negative_controls_in_top_k") == 2
            and intake_summary.get("template_row_count") == 12
            and intake_summary.get("template_table_hash") is not None,
            {
                "record_count": replay_summary.get("record_count"),
                "family_count": replay_summary.get("family_count"),
                "negative_control_count": replay_summary.get("negative_control_count"),
                "selected_negative_controls_in_top_k": replay_summary.get(
                    "selected_negative_controls_in_top_k"
                ),
                "template_row_count": intake_summary.get("template_row_count"),
                "template_table_hash": intake_summary.get("template_table_hash"),
            },
        ),
        requirement(
            "P5",
            "Current state has no accepted DFT/B5 observable rows and no discovery claim",
            intake_summary.get("accepted_dft_rows") == 0
            and intake_summary.get("accepted_b5_rows") == 0
            and all(replay_summary.get(key) is False for key in forbidden_claims),
            {
                "accepted_dft_rows": intake_summary.get("accepted_dft_rows"),
                "accepted_b5_rows": intake_summary.get("accepted_b5_rows"),
                **{key: replay_summary.get(key) for key in forbidden_claims},
            },
        ),
        requirement(
            "P6",
            "Row replay-validation manifest artifact has been submitted",
            submitted_exists,
            {"submission_artifact_path": str(submission_path), "exists": submitted_exists},
        ),
        requirement(
            "P7",
            "Submitted row replay manifest satisfies the locked DFT/B5 replay schema",
            submitted_exists and not missing_keys and len(production_present) == len(production_required_keys),
            {
                "missing_keys": missing_keys,
                "production_keys_present": production_present,
                "production_required_keys": production_required_keys,
                "submitted_key_count": len(submitted) if submitted else 0,
            },
        ),
        requirement(
            "P8",
            "Submitted row replay manifest is source-backed, gate-bound, replay-bound, and claim-boundary-safe",
            source_backed and manifest_bound and replay_bound and claim_boundary_bound,
            {
                "source_evidence_files_present": source_backed,
                "manifest_bound": manifest_bound,
                "replay_bound": replay_bound,
                "claim_boundary_bound": claim_boundary_bound,
            },
        ),
        requirement(
            "P9",
            "Forbidden observable, discovery, mechanism, and solution claims remain false",
            intake_summary.get("accepted_dft_rows") == 0
            and intake_summary.get("accepted_b5_rows") == 0
            and all(replay_summary.get(key) is False for key in forbidden_claims),
            {
                "accepted_dft_rows": intake_summary.get("accepted_dft_rows"),
                "accepted_b5_rows": intake_summary.get("accepted_b5_rows"),
                **{key: replay_summary.get(key) for key in forbidden_claims},
            },
        ),
    ]

    passed = sum(row["passed"] for row in requirements)
    failed_ids = [row["requirement_id"] for row in requirements if not row["passed"]]
    validation_errors: list[str] = []
    if failed_ids != EXPECTED_FAILED_IDS:
        validation_errors.append(f"unexpected observable row replay-validation manifest failures: {failed_ids}")
    if submitted_exists:
        validation_errors.append("gate expected no submitted row replay-validation manifest until an observable PR supplies one")

    summary = {
        "manifest_id": EXPECTED_ROW_REPLAY_MANIFEST_ID,
        "source_replay_validation_manifest_id": EXPECTED_REPLAY_MANIFEST_ID,
        "priority_material_id": EXPECTED_MATERIAL_ID,
        "replay_validation_manifest_hash": replay_summary.get("manifest_hash"),
        "provenance_manifest_hash": replay_summary.get("provenance_manifest_hash"),
        "manifest_hash": row_packet["manifest_hash"],
        "manifest_requirement_count": len(requirements),
        "manifest_requirements_passed": passed,
        "manifest_requirements_failed": len(requirements) - passed,
        "failed_manifest_requirement_ids": failed_ids,
        "required_key_count": len(required_keys),
        "production_required_key_count": len(production_required_keys),
        "required_evidence_file_count": len(evidence_files),
        "record_count": replay_summary.get("record_count"),
        "family_count": replay_summary.get("family_count"),
        "negative_control_count": replay_summary.get("negative_control_count"),
        "post_split_record_count": replay_summary.get("post_split_record_count"),
        "selected_negative_controls_in_top_k": replay_summary.get("selected_negative_controls_in_top_k"),
        "template_row_count": intake_summary.get("template_row_count"),
        "template_table_hash": intake_summary.get("template_table_hash"),
        "submitted_manifest_exists": submitted_exists,
        "submitted_key_count": len(submitted) if submitted else 0,
        "missing_key_count": len(missing_keys),
        "production_keys_present_count": len(production_present),
        "accepted_priority_dft_rows": 0,
        "accepted_priority_b5_rows": 0,
        "source_table_hash": replay_summary.get("source_table_hash"),
        "replay_formula_hash": replay_summary.get("replay_formula_hash"),
        "replay_table_hash": replay_summary.get("replay_table_hash"),
        "dft_observable_claimed": False,
        "b5_computed_observable_claimed": False,
        "material_discovery_claimed": False,
        "mechanism_solved": False,
        "solution_claimed": False,
        "validation_error_count": len(validation_errors),
    }
    return {
        "benchmark_id": "B6",
        "linked_benchmark_id": "B5",
        "problem_id": 37,
        "title": "B6/B5 Observable Row Replay-Validation Manifest Gate",
        "version": VERSION,
        "last_updated": args.last_updated,
        "method": METHOD,
        "status": STATUS,
        "model_status": MODEL_STATUS,
        "source_replay_validation_manifest_gate": str(args.replay_validation_manifest_gate),
        "source_intake_template_gate": str(args.intake_template_gate),
        "summary": summary,
        "observable_row_replay_validation_manifest_packet": row_packet,
        "requirements": requirements,
        "claim_boundary": {
            "what_is_supported": (
                "The rank-1 B6/B5 observable route now has a row replay-validation "
                "manifest packet after the replay manifest and before DFT/B5 observable "
                "rows can count."
            ),
            "what_is_not_supported": (
                "No row replay-validation manifest, DFT row, or B5-computed observable row "
                "has been submitted or accepted; no material discovery, mechanism-solved, "
                "observable, or solution claim is supported."
            ),
            "next_gate": (
                "Submit B6B5-O1-monolayer-FeSe-STO-row-replay-validation-manifest with "
                "DFT and B5 row tables, structure reference, DFT replay, effective-model "
                "mapping, B5 solver replay, same-access cost ledger, negative-control audit, "
                "family-prior denominator, row acceptance ledger, and claim boundary."
            ),
            "accepted_priority_dft_rows": 0,
            "accepted_priority_b5_rows": 0,
            "dft_observable_claimed": False,
            "b5_computed_observable_claimed": False,
            "material_discovery_claimed": False,
            "mechanism_solved": False,
            "solution_claimed": False,
        },
        "validation_errors": validation_errors,
        "runtime_seconds": round(time.time() - started, 6),
    }


def write_markdown(payload: dict[str, Any], path: Path) -> None:
    summary = payload["summary"]
    packet = payload["observable_row_replay_validation_manifest_packet"]
    lines = [
        "# B6/B5 Observable Row Replay-Validation Manifest Gate",
        "",
        f"Status: `{payload['status']}`",
        "",
        "## Summary",
        "",
        f"- Method: `{payload['method']}`",
        f"- Manifest: `{summary['manifest_id']}`",
        f"- Source replay manifest: `{summary['source_replay_validation_manifest_id']}`",
        f"- Priority material: `{summary['priority_material_id']}`",
        f"- Replay-validation manifest hash: `{summary['replay_validation_manifest_hash']}`",
        f"- Provenance manifest hash: `{summary['provenance_manifest_hash']}`",
        f"- Manifest hash: `{summary['manifest_hash']}`",
        f"- Requirements passed/failed: `{summary['manifest_requirements_passed']}` / `{summary['manifest_requirements_failed']}`",
        f"- Failed requirement IDs: `{summary['failed_manifest_requirement_ids']}`",
        f"- Required key / production key / evidence file count: `{summary['required_key_count']}` / `{summary['production_required_key_count']}` / `{summary['required_evidence_file_count']}`",
        f"- Replay scope records/families/negative controls: `{summary['record_count']}` / `{summary['family_count']}` / `{summary['negative_control_count']}`",
        f"- Template rows / negative controls in top-k: `{summary['template_row_count']}` / `{summary['selected_negative_controls_in_top_k']}`",
        f"- Submitted manifest exists: `{summary['submitted_manifest_exists']}`",
        f"- Accepted priority DFT/B5 rows: `{summary['accepted_priority_dft_rows']}` / `{summary['accepted_priority_b5_rows']}`",
        f"- validation_error_count: `{summary['validation_error_count']}`",
        "",
        "## Row Replay-Validation Manifest Packet",
        "",
        f"- Submission path: `{packet['submission_artifact_path']}`",
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
    for row in payload["requirements"]:
        state = "PASS" if row["passed"] else "FAIL"
        lines.append(f"- {row['requirement_id']} [{state}]: {row['label']}")
    lines.extend(
        [
            "",
            "## Claim Boundary",
            "",
            f"- Supported: {payload['claim_boundary']['what_is_supported']}",
            f"- Not supported: {payload['claim_boundary']['what_is_not_supported']}",
            f"- Next gate: {payload['claim_boundary']['next_gate']}",
            f"- accepted_priority_dft_rows: {payload['claim_boundary']['accepted_priority_dft_rows']}",
            f"- accepted_priority_b5_rows: {payload['claim_boundary']['accepted_priority_b5_rows']}",
            f"- dft_observable_claimed: {payload['claim_boundary']['dft_observable_claimed']}",
            f"- b5_computed_observable_claimed: {payload['claim_boundary']['b5_computed_observable_claimed']}",
            f"- material_discovery_claimed: {payload['claim_boundary']['material_discovery_claimed']}",
            f"- mechanism_solved: {payload['claim_boundary']['mechanism_solved']}",
            f"- solution_claimed: {payload['claim_boundary']['solution_claimed']}",
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
        "--replay-validation-manifest-gate",
        type=Path,
        default=Path("results/B6_B5_observable_replay_validation_manifest_gate_v0.json"),
    )
    parser.add_argument(
        "--intake-template-gate",
        type=Path,
        default=Path("results/B6_B5_observable_row_intake_template_gate_v0.json"),
    )
    parser.add_argument(
        "--submission-dir",
        type=Path,
        default=Path("results/B6_B5_observable_row_replay_validation_manifest_submissions"),
    )
    parser.add_argument(
        "--json-output",
        type=Path,
        default=Path("results/B6_B5_observable_row_replay_validation_manifest_gate_v0.json"),
    )
    parser.add_argument(
        "--markdown-output",
        type=Path,
        default=Path("research/B6_B5_observable_row_replay_validation_manifest_gate.md"),
    )
    parser.add_argument("--last-updated", default="2026-07-02")
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()

    payload = build_payload(args)
    write_json(args.json_output, payload, pretty=args.pretty)
    write_markdown(payload, args.markdown_output)
    print(json.dumps(payload["summary"], indent=2 if args.pretty else None, sort_keys=True))
    if payload["validation_errors"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
