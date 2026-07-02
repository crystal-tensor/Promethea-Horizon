#!/usr/bin/env python3
"""T-B6-005h/T-B5-006o: DFT/B5 observable provenance manifest gate."""

from __future__ import annotations

import argparse
import hashlib
import json
import time
from pathlib import Path
from typing import Any


METHOD = "b6_b5_observable_provenance_manifest_gate_v0"
STATUS = "observable_provenance_manifest_open_missing_artifact"
MODEL_STATUS = "observable_provenance_manifest_required_before_priority_dft_b5_rows"
VERSION = "0.1"
EXPECTED_MANIFEST_ID = "B6B5-O1-monolayer-FeSe-STO-provenance-manifest"
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
    priority = load_json(args.priority_packet_gate)
    summary = priority["summary"]
    submission_path = args.submission_dir / f"{EXPECTED_MANIFEST_ID}.json"
    submitted_exists = submission_path.exists()
    submitted = load_json(submission_path) if submitted_exists else None
    required_keys = [
        "manifest_id",
        "material_id",
        "structure_reference_id",
        "structure_reference_hash",
        "dft_input_protocol_hash",
        "dft_output_parser_hash",
        "effective_model_protocol_hash",
        "b5_solver_protocol_hash",
        "same_access_cost_unit",
        "source_replay_hashes",
        "claim_boundary",
    ]
    production_required_keys = [
        "structure_reference_hash",
        "dft_input_protocol_hash",
        "dft_output_parser_hash",
        "effective_model_protocol_hash",
        "b5_solver_protocol_hash",
        "same_access_cost_unit",
        "source_replay_hashes",
    ]
    missing_keys = [key for key in required_keys if submitted is None or key not in submitted]
    production_present = [
        key for key in production_required_keys if submitted is not None and submitted.get(key) is not None
    ]
    source_backed = submitted is not None and submitted.get("source_evidence_files_present") is True
    material_bound = submitted is not None and submitted.get("material_id") == EXPECTED_MATERIAL_ID
    replay_hashes = submitted.get("source_replay_hashes") if submitted else None
    replay_bound = (
        isinstance(replay_hashes, dict)
        and replay_hashes.get("source_table_hash") == summary.get("source_table_hash")
        and replay_hashes.get("replay_formula_hash") == summary.get("replay_formula_hash")
        and replay_hashes.get("replay_table_hash") == summary.get("replay_table_hash")
    )

    manifest_packet = {
        "manifest_id": EXPECTED_MANIFEST_ID,
        "material_id": EXPECTED_MATERIAL_ID,
        "downstream_priority_packet": EXPECTED_MATERIAL_ID,
        "submission_artifact_path": str(submission_path),
        "source_priority_packet_gate": str(args.priority_packet_gate),
        "required_keys": required_keys,
        "production_required_keys": production_required_keys,
        "required_evidence_files": [
            "structure_reference_or_cif_manifest",
            "structure_reference_hash_source",
            "dft_input_protocol_note",
            "dft_output_parser_note",
            "effective_model_derivation_protocol",
            "b5_solver_protocol_note",
            "same_access_cost_unit_note",
            "source_replay_hash_manifest",
            "observable_join_key_audit",
            "claim_boundary_note",
        ],
        "accepted_only_if": [
            "manifest_id equals B6B5-O1-monolayer-FeSe-STO-provenance-manifest",
            "material_id equals monolayer_FeSe_STO_2012",
            "structure reference, DFT protocol, parser, effective-model protocol, B5 solver protocol, same-access cost unit, and replay hashes are present",
            "source_table_hash, replay_formula_hash, and replay_table_hash match the priority observable packet",
            "source evidence files are present and hash-bound",
            "claim_boundary forbids DFT-observable, B5-observable, material-discovery, mechanism-solved, and solution claims",
        ],
    }
    manifest_packet["manifest_hash"] = stable_hash(manifest_packet)

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
            "Priority observable packet remains valid and blocked only on P6/P7/P8",
            priority.get("method") == "b6_b5_observable_priority_packet_gate_v0"
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
            "Provenance manifest is bound to the rank-1 monolayer FeSe/STO material",
            summary.get("priority_material_id") == EXPECTED_MATERIAL_ID
            and summary.get("priority_material_rank") == 1,
            {
                "priority_material_id": summary.get("priority_material_id"),
                "priority_material_rank": summary.get("priority_material_rank"),
                "priority_material_family": summary.get("priority_material_family"),
            },
        ),
        requirement(
            "P3",
            "Manifest packet carries locked schema and evidence file classes",
            len(required_keys) == 11
            and len(production_required_keys) == 7
            and len(manifest_packet["required_evidence_files"]) == 10,
            {
                "required_key_count": len(required_keys),
                "production_required_key_count": len(production_required_keys),
                "required_evidence_file_count": len(manifest_packet["required_evidence_files"]),
            },
        ),
        requirement(
            "P4",
            "Observable row denominator and replay hashes remain preserved",
            summary.get("template_row_count") == 12
            and summary.get("source_table_hash") == "ce134d0a5d295af982b77be0a8a43e90ea19e828af20cc80ac3f20b7664d2fdc"
            and summary.get("replay_formula_hash") == "e23239648dd11aa8e0db8ecdeb5824506a5a379c9ba2777965c3aafa5d5d8230"
            and summary.get("replay_table_hash") == "c44099194d0bc04d74cd3c4c4e068bf51a9e114d11c6e0b5e3890786cda5b8de",
            {
                "template_row_count": summary.get("template_row_count"),
                "source_table_hash": summary.get("source_table_hash"),
                "replay_formula_hash": summary.get("replay_formula_hash"),
                "replay_table_hash": summary.get("replay_table_hash"),
            },
        ),
        requirement(
            "P5",
            "Current state has no accepted DFT/B5 observable row",
            summary.get("accepted_priority_dft_rows") == 0
            and summary.get("accepted_priority_b5_rows") == 0,
            {
                "accepted_priority_dft_rows": summary.get("accepted_priority_dft_rows"),
                "accepted_priority_b5_rows": summary.get("accepted_priority_b5_rows"),
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
            "Submitted manifest is source-backed, material-bound, and replay-hash-bound",
            source_backed and material_bound and replay_bound,
            {
                "source_evidence_files_present": source_backed,
                "material_bound": material_bound,
                "replay_bound": replay_bound,
            },
        ),
        requirement(
            "P9",
            "Forbidden observable, discovery, mechanism, and solution claims remain false",
            all(summary.get(key) is False for key in forbidden_claims),
            {key: summary.get(key) for key in forbidden_claims},
        ),
    ]

    passed = sum(row["passed"] for row in requirements)
    failed_ids = [row["requirement_id"] for row in requirements if not row["passed"]]
    validation_errors: list[str] = []
    if failed_ids != EXPECTED_FAILED_IDS:
        validation_errors.append(f"unexpected observable provenance manifest failures: {failed_ids}")
    if submitted_exists:
        validation_errors.append("gate expected no submitted manifest until an observable PR supplies one")

    payload_summary = {
        "manifest_id": EXPECTED_MANIFEST_ID,
        "priority_material_id": EXPECTED_MATERIAL_ID,
        "manifest_hash": manifest_packet["manifest_hash"],
        "manifest_requirement_count": len(requirements),
        "manifest_requirements_passed": passed,
        "manifest_requirements_failed": len(requirements) - passed,
        "failed_manifest_requirement_ids": failed_ids,
        "required_key_count": len(required_keys),
        "production_required_key_count": len(production_required_keys),
        "required_evidence_file_count": len(manifest_packet["required_evidence_files"]),
        "template_row_count": summary.get("template_row_count"),
        "submitted_manifest_exists": submitted_exists,
        "missing_key_count": len(missing_keys),
        "production_keys_present_count": len(production_present),
        "accepted_priority_dft_rows": summary.get("accepted_priority_dft_rows"),
        "accepted_priority_b5_rows": summary.get("accepted_priority_b5_rows"),
        "source_table_hash": summary.get("source_table_hash"),
        "replay_formula_hash": summary.get("replay_formula_hash"),
        "replay_table_hash": summary.get("replay_table_hash"),
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
        "title": "B6/B5 Observable Provenance Manifest Gate",
        "version": VERSION,
        "last_updated": args.last_updated,
        "method": METHOD,
        "status": STATUS,
        "model_status": MODEL_STATUS,
        "source_priority_packet_gate": str(args.priority_packet_gate),
        "summary": payload_summary,
        "observable_provenance_manifest_packet": manifest_packet,
        "requirements": requirements,
        "claim_boundary": {
            "what_is_supported": (
                "The rank-1 B6/B5 observable route now has a concrete provenance manifest packet "
                "that must be accepted before DFT/B5 observable rows can be considered."
            ),
            "what_is_not_supported": (
                "No provenance manifest, DFT row, or B5-computed observable row has been submitted "
                "or accepted; no material discovery, mechanism-solved, observable, or solution claim "
                "is supported."
            ),
            "next_gate": (
                "Submit B6B5-O1-monolayer-FeSe-STO-provenance-manifest with structure reference, "
                "DFT protocol, parser, effective-model protocol, B5 solver protocol, same-access "
                "cost unit, source replay hashes, and claim boundary."
            ),
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
    packet = payload["observable_provenance_manifest_packet"]
    lines = [
        "# B6/B5 Observable Provenance Manifest Gate",
        "",
        f"Status: `{payload['status']}`",
        "",
        "## Summary",
        "",
        f"- Method: `{payload['method']}`",
        f"- Manifest: `{summary['manifest_id']}`",
        f"- Priority material: `{summary['priority_material_id']}`",
        f"- Manifest hash: `{summary['manifest_hash']}`",
        f"- Requirements passed/failed: `{summary['manifest_requirements_passed']}` / `{summary['manifest_requirements_failed']}`",
        f"- Failed requirement IDs: `{summary['failed_manifest_requirement_ids']}`",
        f"- Required key / production key / evidence file count: `{summary['required_key_count']}` / `{summary['production_required_key_count']}` / `{summary['required_evidence_file_count']}`",
        f"- Template row count: `{summary['template_row_count']}`",
        f"- Submitted manifest exists: `{summary['submitted_manifest_exists']}`",
        f"- Accepted priority DFT/B5 rows: `{summary['accepted_priority_dft_rows']}` / `{summary['accepted_priority_b5_rows']}`",
        f"- validation_error_count: `{summary['validation_error_count']}`",
        "",
        "## Manifest Packet",
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
        for error in payload["validation_errors"]:
            lines.append(f"- {error}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--priority-packet-gate",
        type=Path,
        default=Path("results/B6_B5_observable_priority_packet_gate_v0.json"),
    )
    parser.add_argument(
        "--submission-dir",
        type=Path,
        default=Path("results/B6_B5_observable_provenance_manifest_submissions"),
    )
    parser.add_argument(
        "--json-output",
        type=Path,
        default=Path("results/B6_B5_observable_provenance_manifest_gate_v0.json"),
    )
    parser.add_argument(
        "--markdown-output",
        type=Path,
        default=Path("research/B6_B5_observable_provenance_manifest_gate.md"),
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
