#!/usr/bin/env python3
"""T-B3-042/T-B10-015ac: P8-A accepted-row replay intake template gate."""

from __future__ import annotations

import argparse
import hashlib
import json
import time
from pathlib import Path
from typing import Any


METHOD = "b3_b10_p8a_accepted_row_replay_intake_template_gate_v0"
STATUS = "b3_b10_p8a_accepted_row_replay_intake_open_missing_rows"
MODEL_STATUS = "p8a_row_replay_templates_ready_no_accepted_rows"
VERSION = "0.1"
EXPECTED_FAILED_IDS = ["A6", "A7", "A8"]
EXPECTED_PRESSURE_PACKET_HASH = "55384c1a143b50d9b334193c3e55151f33bc9511b90dd19a21f22198bf9fe0b0"


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


def build_template_row(
    row_id: str,
    row_hash: str,
    row_index: int,
    submission: dict[str, Any],
    required_keys: list[str],
    production_required_keys: list[str],
    submission_dir: Path,
) -> dict[str, Any]:
    row_path = submission_dir / f"{row_id}.json"
    submitted_exists = row_path.exists()
    submitted = load_json(row_path) if submitted_exists else None
    prefilled_values = {
        "row_id": row_id,
        "row_index": row_index,
        "candidate_row_hash": row_hash,
        "acceptance_submission_hash": submission.get("acceptance_submission_hash"),
        "row_bundle_hash": submission.get("row_scope", {}).get("row_bundle_hash"),
        "row_scope_hash": submission.get("row_scope_hash"),
        "full_covariance_row_table_hash": submission.get("full_covariance_row_table_hash"),
        "compiled_state_replay_hash": submission.get("compiled_state_replay_hash"),
        "pauli_grouping_covariance_replay_hash": submission.get(
            "pauli_grouping_covariance_replay_hash"
        ),
        "derivative_estimator_replay_hash": submission.get("derivative_estimator_replay_hash"),
        "row_acceptance_packet_id": submission.get("acceptance_packet_id"),
    }
    missing_required_keys = [key for key in required_keys if key not in prefilled_values]
    production_missing_keys = [
        key for key in production_required_keys if submitted is None or submitted.get(key) is None
    ]
    accepted_row = (
        submitted is not None
        and submitted.get("row_id") == row_id
        and submitted.get("candidate_row_hash") == row_hash
        and submitted.get("source_evidence_files_present") is True
        and submitted.get("row_replay_returncode") == 0
        and submitted.get("row_acceptance_decision") == "accepted"
        and submitted.get("accepted_full_covariance_row") is True
        and submitted.get("forbidden_claims", {}).get("b3_reopen_ready") is False
        and submitted.get("forbidden_claims", {}).get("b10_t1_credit_allowed") is False
    )
    template = {
        "row_id": row_id,
        "row_index": row_index,
        "candidate_row_hash": row_hash,
        "prefilled_values": prefilled_values,
        "required_row_keys": required_keys,
        "prefilled_required_keys": [key for key in required_keys if key in prefilled_values],
        "missing_required_keys": missing_required_keys,
        "production_required_keys": production_required_keys,
        "production_missing_keys": production_missing_keys,
        "submission_artifact_path": str(row_path),
        "submitted_row_present": submitted_exists,
        "accepted_full_covariance_row": accepted_row,
    }
    template["template_hash"] = stable_hash(
        {
            "row_id": row_id,
            "candidate_row_hash": row_hash,
            "acceptance_submission_hash": submission.get("acceptance_submission_hash"),
            "required_row_keys": required_keys,
            "production_required_keys": production_required_keys,
        }
    )
    return template


def build_payload(args: argparse.Namespace) -> dict[str, Any]:
    started = time.time()
    p8_pressure = load_json(args.p8_pressure_gate)
    submission = load_json(args.acceptance_packet_submission)
    pressure_summary = p8_pressure["summary"]
    candidate_ids = submission["full_covariance_row_table"]["candidate_row_ids"]
    candidate_hashes = submission["full_covariance_row_table"]["candidate_row_hashes"]

    required_keys = [
        "row_id",
        "row_index",
        "candidate_row_hash",
        "acceptance_submission_hash",
        "row_bundle_hash",
        "row_scope_hash",
        "full_covariance_row_table_hash",
        "compiled_state_replay_hash",
        "pauli_grouping_covariance_replay_hash",
        "derivative_estimator_replay_hash",
        "row_acceptance_packet_id",
        "row_observable_table_hash",
        "covariance_matrix_replay_hash",
        "row_replay_command_hash",
        "row_replay_stdout_hash",
        "row_replay_returncode",
        "row_acceptance_decision",
        "same_access_denominator_link_hash",
        "claim_boundary_hash",
        "source_evidence_files_present",
    ]
    prefilled_key_set = {
        "row_id",
        "row_index",
        "candidate_row_hash",
        "acceptance_submission_hash",
        "row_bundle_hash",
        "row_scope_hash",
        "full_covariance_row_table_hash",
        "compiled_state_replay_hash",
        "pauli_grouping_covariance_replay_hash",
        "derivative_estimator_replay_hash",
        "row_acceptance_packet_id",
    }
    production_required_keys = [key for key in required_keys if key not in prefilled_key_set]
    template_rows = [
        build_template_row(
            row_id=row_id,
            row_hash=row_hash,
            row_index=index,
            submission=submission,
            required_keys=required_keys,
            production_required_keys=production_required_keys,
            submission_dir=args.submission_dir,
        )
        for index, (row_id, row_hash) in enumerate(zip(candidate_ids, candidate_hashes), start=1)
    ]

    row_template_count = len(template_rows)
    template_table_hash = stable_hash(template_rows)
    submitted_row_count = sum(row["submitted_row_present"] for row in template_rows)
    accepted_row_count = sum(row["accepted_full_covariance_row"] for row in template_rows)
    production_missing_key_total = sum(len(row["production_missing_keys"]) for row in template_rows)
    min_prefilled_key_count = min(
        (len(row["prefilled_required_keys"]) for row in template_rows), default=0
    )

    requirements = [
        requirement(
            "A1",
            "P8 pressure gate is current and points to P8-A as a ready packet",
            p8_pressure.get("method") == "b3_b10_f1_p8_acceptance_pressure_gate_v0"
            and pressure_summary.get("pressure_packet_hash") == EXPECTED_PRESSURE_PACKET_HASH
            and "P8-A" in pressure_summary.get("ready_pressure_packet_ids", [])
            and pressure_summary.get("validation_error_count") == 0,
            {
                "method": p8_pressure.get("method"),
                "pressure_packet_hash": pressure_summary.get("pressure_packet_hash"),
                "ready_pressure_packet_ids": pressure_summary.get("ready_pressure_packet_ids"),
                "validation_error_count": pressure_summary.get("validation_error_count"),
            },
        ),
        requirement(
            "A2",
            "Four F1 candidate row templates are generated",
            row_template_count == 4
            and candidate_ids
            == [
                "B3B10-F1-pilot-row-h2-ccpvdz-compiled-ucc-adapt-v0",
                "B3B10-F1-row-h2o-symmetric-oh-stretch-full-covariance-v0",
                "B3B10-F1-row-n2-bond-stretch-full-covariance-v0",
                "B3B10-F1-row-lih-bond-stretch-full-covariance-v0",
            ],
            {"row_template_count": row_template_count, "candidate_row_ids": candidate_ids},
        ),
        requirement(
            "A3",
            "Every template preserves the submitted F1 packet hashes",
            all(
                row["prefilled_values"].get("acceptance_submission_hash")
                == submission.get("acceptance_submission_hash")
                and row["prefilled_values"].get("row_bundle_hash")
                == submission.get("row_scope", {}).get("row_bundle_hash")
                and row["prefilled_values"].get("full_covariance_row_table_hash")
                == submission.get("full_covariance_row_table_hash")
                for row in template_rows
            ),
            {
                "acceptance_submission_hash": submission.get("acceptance_submission_hash"),
                "row_bundle_hash": submission.get("row_scope", {}).get("row_bundle_hash"),
                "full_covariance_row_table_hash": submission.get("full_covariance_row_table_hash"),
            },
        ),
        requirement(
            "A4",
            "P8-A row schema and production evidence keys are fixed",
            len(required_keys) == 20 and len(production_required_keys) == 9,
            {
                "required_row_key_count": len(required_keys),
                "production_required_key_count": len(production_required_keys),
            },
        ),
        requirement(
            "A5",
            "Templates carry provenance only and preserve zero-credit boundary",
            pressure_summary.get("accepted_full_covariance_row_count") == 0
            and pressure_summary.get("denominator_win_count") == 0
            and pressure_summary.get("b10_t1_credit_allowed") is False
            and pressure_summary.get("bqp_separation_claimed") is False,
            {
                "accepted_full_covariance_row_count": pressure_summary.get(
                    "accepted_full_covariance_row_count"
                ),
                "denominator_win_count": pressure_summary.get("denominator_win_count"),
                "b10_t1_credit_allowed": pressure_summary.get("b10_t1_credit_allowed"),
                "bqp_separation_claimed": pressure_summary.get("bqp_separation_claimed"),
            },
        ),
        requirement(
            "A6",
            "Submitted P8-A row replay artifacts exist for all four candidate rows",
            submitted_row_count == 4,
            {"submitted_row_count": submitted_row_count, "required_rows": 4},
        ),
        requirement(
            "A7",
            "Production replay keys are populated for all submitted P8-A rows",
            production_missing_key_total == 0,
            {
                "production_required_key_count": len(production_required_keys),
                "production_missing_key_total": production_missing_key_total,
            },
        ),
        requirement(
            "A8",
            "At least one submitted P8-A row is accepted as a full-covariance row",
            accepted_row_count > 0,
            {"accepted_full_covariance_row_count": accepted_row_count},
        ),
        requirement(
            "A9",
            "No P8-A template promotes B3, B10, advantage, or BQP credit",
            submission.get("b3_reopen_boundary", {}).get("b3_reopen_ready") is False
            and submission.get("b10_access_boundary", {}).get("b10_t1_credit_allowed") is False
            and submission.get("claim_boundary", {}).get("quantum_advantage_claimed") is False
            and submission.get("claim_boundary", {}).get("bqp_separation_claimed") is False,
            {
                "b3_reopen_ready": submission.get("b3_reopen_boundary", {}).get("b3_reopen_ready"),
                "b10_t1_credit_allowed": submission.get("b10_access_boundary", {}).get(
                    "b10_t1_credit_allowed"
                ),
                "quantum_advantage_claimed": submission.get("claim_boundary", {}).get(
                    "quantum_advantage_claimed"
                ),
                "bqp_separation_claimed": submission.get("claim_boundary", {}).get(
                    "bqp_separation_claimed"
                ),
            },
        ),
    ]
    passed = sum(row["passed"] for row in requirements)
    failed_ids = [row["requirement_id"] for row in requirements if not row["passed"]]
    validation_errors: list[str] = []
    if failed_ids != EXPECTED_FAILED_IDS:
        validation_errors.append(f"unexpected P8-A intake failures: {failed_ids}")
    if accepted_row_count != 0:
        validation_errors.append("P8-A template gate must not fabricate accepted rows")
    if pressure_summary.get("denominator_win_count") != 0:
        validation_errors.append("P8-A template gate must preserve zero denominator wins")

    summary = {
        "intake_template_id": "B3B10-P8A-accepted-row-replay-intake",
        "source_pressure_packet_hash": pressure_summary.get("pressure_packet_hash"),
        "acceptance_submission_hash": submission.get("acceptance_submission_hash"),
        "row_bundle_hash": submission.get("row_scope", {}).get("row_bundle_hash"),
        "template_table_hash": template_table_hash,
        "row_template_count": row_template_count,
        "required_row_key_count": len(required_keys),
        "production_required_key_count": len(production_required_keys),
        "prefilled_required_key_count_min": min_prefilled_key_count,
        "submitted_row_count": submitted_row_count,
        "accepted_full_covariance_row_count": accepted_row_count,
        "denominator_win_count": pressure_summary.get("denominator_win_count"),
        "production_missing_key_total": production_missing_key_total,
        "intake_requirement_count": len(requirements),
        "intake_requirements_passed": passed,
        "intake_requirements_failed": len(requirements) - passed,
        "failed_intake_requirement_ids": failed_ids,
        "ready_for_p8b_denominator_replay": False,
        "b3_reopen_ready": False,
        "b10_t1_credit_allowed": False,
        "quantum_advantage_claimed": False,
        "bqp_separation_claimed": False,
        "validation_error_count": len(validation_errors),
    }

    return {
        "benchmark_id": "B3_B10",
        "problem_ids": [49, 11],
        "title": "B3/B10 P8-A Accepted-Row Replay Intake Template Gate",
        "version": VERSION,
        "last_updated": args.last_updated,
        "method": METHOD,
        "status": STATUS,
        "model_status": MODEL_STATUS,
        "source_p8_pressure_gate": str(args.p8_pressure_gate),
        "source_acceptance_packet_submission": str(args.acceptance_packet_submission),
        "source_target_id": "B10-T1",
        "dependency_benchmarks": ["B3", "B10"],
        "summary": summary,
        "row_templates": template_rows,
        "requirements": requirements,
        "claim_boundary": {
            "what_is_supported": (
                "P8-A now has four row-level intake templates for H2, H2O, N2, and LiH. "
                "The templates bind the submitted F1 packet hashes and identify the exact "
                "production replay keys required before any row can be accepted."
            ),
            "what_is_not_supported": (
                "No P8-A row replay artifact has been submitted or accepted. This gate does "
                "not establish accepted rows, denominator wins, B3 reopen, B10-T1 credit, "
                "quantum advantage, or BQP separation."
            ),
            "next_gate": (
                "Submit one or more row replay artifacts under the P8-A submission directory "
                "with observable-table, covariance replay, command, stdout, returncode, "
                "acceptance decision, denominator-link, and claim-boundary hashes."
            ),
            "accepted_full_covariance_row_count": accepted_row_count,
            "denominator_win_count": pressure_summary.get("denominator_win_count"),
            "b3_reopen_ready": False,
            "b10_t1_credit_allowed": False,
            "quantum_advantage_claimed": False,
            "bqp_separation_claimed": False,
        },
        "validation_errors": validation_errors,
        "runtime_seconds": round(time.time() - started, 6),
    }


def write_markdown(payload: dict[str, Any], path: Path) -> None:
    s = payload["summary"]
    lines = [
        "# B3/B10 P8-A Accepted-Row Replay Intake Template Gate",
        "",
        f"Status: `{payload['status']}`",
        "",
        "## Summary",
        "",
        f"- Method: `{payload['method']}`",
        f"- Intake template: `{s['intake_template_id']}`",
        f"- Source pressure packet hash: `{s['source_pressure_packet_hash']}`",
        f"- Acceptance submission hash: `{s['acceptance_submission_hash']}`",
        f"- Row bundle hash: `{s['row_bundle_hash']}`",
        f"- Template table hash: `{s['template_table_hash']}`",
        f"- Row templates: `{s['row_template_count']}`",
        f"- Required / production key count: `{s['required_row_key_count']}` / `{s['production_required_key_count']}`",
        f"- Submitted / accepted rows: `{s['submitted_row_count']}` / `{s['accepted_full_covariance_row_count']}`",
        f"- Denominator wins: `{s['denominator_win_count']}`",
        f"- Requirements passed/failed: `{s['intake_requirements_passed']}` / `{s['intake_requirements_failed']}`",
        f"- Failed requirement IDs: `{s['failed_intake_requirement_ids']}`",
        f"- validation_error_count: `{s['validation_error_count']}`",
        "",
        "## Row Templates",
        "",
    ]
    for row in payload["row_templates"]:
        lines.extend(
            [
                f"### {row['row_index']}. {row['row_id']}",
                "",
                f"- Candidate row hash: `{row['candidate_row_hash']}`",
                f"- Template hash: `{row['template_hash']}`",
                f"- Submitted row present: `{row['submitted_row_present']}`",
                f"- Accepted full-covariance row: `{row['accepted_full_covariance_row']}`",
                f"- Submission artifact path: `{row['submission_artifact_path']}`",
                "",
            ]
        )
    lines.extend(["## Requirement Results", ""])
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
            f"- accepted_full_covariance_row_count: {payload['claim_boundary']['accepted_full_covariance_row_count']}",
            f"- denominator_win_count: {payload['claim_boundary']['denominator_win_count']}",
            f"- b3_reopen_ready: {payload['claim_boundary']['b3_reopen_ready']}",
            f"- b10_t1_credit_allowed: {payload['claim_boundary']['b10_t1_credit_allowed']}",
            f"- quantum_advantage_claimed: {payload['claim_boundary']['quantum_advantage_claimed']}",
            f"- bqp_separation_claimed: {payload['claim_boundary']['bqp_separation_claimed']}",
            "",
            "## Validation",
            "",
            f"- validation_error_count: {s['validation_error_count']}",
        ]
    )
    if payload["validation_errors"]:
        lines.extend(f"- {error}" for error in payload["validation_errors"])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--p8-pressure-gate",
        type=Path,
        default=Path("results/B3_B10_F1_P8_acceptance_pressure_gate_v0.json"),
    )
    parser.add_argument(
        "--acceptance-packet-submission",
        type=Path,
        default=Path(
            "results/B3_B10_full_covariance_row_acceptance_packet_submissions/"
            "B3-R1-full-covariance-row-acceptance-packet.json"
        ),
    )
    parser.add_argument(
        "--submission-dir",
        type=Path,
        default=Path("results/B3_B10_P8A_accepted_row_replay_submissions"),
    )
    parser.add_argument(
        "--json-output",
        type=Path,
        default=Path("results/B3_B10_P8A_accepted_row_replay_intake_template_gate_v0.json"),
    )
    parser.add_argument(
        "--markdown-output",
        type=Path,
        default=Path("research/B3_B10_P8A_accepted_row_replay_intake_template_gate.md"),
    )
    parser.add_argument("--last-updated", default="2026-07-03")
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
