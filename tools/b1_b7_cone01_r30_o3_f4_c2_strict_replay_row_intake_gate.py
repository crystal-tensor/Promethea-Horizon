#!/usr/bin/env python3
"""T-B1-004ef/T-B7-013o: R30 O3-F4 C2 strict replay row intake gate."""

from __future__ import annotations

import argparse
import hashlib
import json
import time
from pathlib import Path
from typing import Any


METHOD = "b1_b7_cone01_r30_o3_f4_c2_strict_replay_row_intake_gate_v0"
STATUS = "cone01_r30_o3_f4_c2_strict_replay_row_template_ready_rejected"
MODEL_STATUS = "o3_f4_c2_replay_rows_template_ready_no_c2_acceptance"
VERSION = "0.1"
TARGET_ID = "T-B1-004ef/T-B7-013o"
UPSTREAM_TARGET_ID = "T-B1-004ee/T-B7-013n"
R29_TARGET_ID = "T-B1-004ee/T-B7-013n"
FAMILY_ID = "O3-F4"
CANDIDATE_ID = "NL-C02"
STRICT_TOLERANCE = 1.0e-8
C2_REQUIRED_ROW_KEYS = [
    "challenge_id",
    "parameter_indices",
    "source_initial_values",
    "submitted_parameter_values",
    "strict_tolerance",
    "max_unitary_replay_error",
    "unitary_distance_metric",
    "same_unitary_witness_hash",
    "source_circuit_hash",
    "candidate_circuit_hash",
    "replay_command",
    "replay_stdout_hash",
    "verifier_version",
]
TEMPLATE_MARKERS = ("<", ">", "required")


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


def contains_template_marker(value: Any) -> bool:
    if isinstance(value, str):
        return any(marker in value for marker in TEMPLATE_MARKERS)
    if isinstance(value, list):
        return any(contains_template_marker(item) for item in value)
    if isinstance(value, dict):
        return any(contains_template_marker(item) for item in value.values())
    return False


def challenge_packet_from_r24(r24: dict[str, Any]) -> dict[str, Any]:
    return r24["o3_f4_numerical_refit_harness_packet"]["challenge_packet"]


def build_c2_template(r24: dict[str, Any], r29: dict[str, Any]) -> dict[str, Any]:
    packet = challenge_packet_from_r24(r24)
    rows = []
    for row in packet["challenge_rows"]:
        rows.append(
            {
                "challenge_id": row["challenge_id"],
                "parameter_indices": row["parameter_indices"],
                "source_initial_values": row["initial_values"],
                "submitted_parameter_values": "<five candidate parameters after refit>",
                "strict_tolerance": STRICT_TOLERANCE,
                "max_unitary_replay_error": "<must be <= 1e-08>",
                "unitary_distance_metric": "<operator_norm|diamond_proxy|statevector_span_bound>",
                "same_unitary_witness_hash": "<sha256>",
                "source_circuit_hash": "<sha256>",
                "candidate_circuit_hash": "<sha256>",
                "replay_command": "<command>",
                "replay_stdout_hash": "<sha256>",
                "verifier_version": "<tool-or-agent-version>",
            }
        )
    template = {
        "artifact_id": "B1-B7-cone01-O3-F4-C2-strict-replay-rows.<submitter-id>",
        "source_target_id": TARGET_ID,
        "upstream_target_id": R29_TARGET_ID,
        "family_id": FAMILY_ID,
        "candidate_id": CANDIDATE_ID,
        "source_r24_challenge_packet_hash": packet["challenge_packet_hash"],
        "source_r29_preflight_hash": r29["summary"]["preflight_hash"],
        "strict_tolerance": STRICT_TOLERANCE,
        "required_row_count": 8,
        "required_row_keys": C2_REQUIRED_ROW_KEYS,
        "rows": rows,
        "claim_boundary": {
            "supported": "C2 strict replay row submission only after all row fields are source-backed and replay errors are <= 1e-08.",
            "not_supported": "C2 acceptance, O3 closure, R5 reroute, B7 credit, STV credit, or resource savings before this template is filled and accepted.",
        },
        "o3_closed": False,
        "reroute_allowed": False,
        "b7_credit_delta": 0,
    }
    template["row_table_hash"] = stable_hash(rows)
    template["template_hash"] = stable_hash(template)
    return template


def evaluate_c2_template(template: dict[str, Any], r24: dict[str, Any]) -> dict[str, Any]:
    packet = challenge_packet_from_r24(r24)
    expected_ids = [row["challenge_id"] for row in packet["challenge_rows"]]
    rows = template.get("rows", [])
    actual_ids = [row.get("challenge_id") for row in rows if isinstance(row, dict)]
    missing_ids = [challenge_id for challenge_id in expected_ids if challenge_id not in actual_ids]
    extra_ids = [challenge_id for challenge_id in actual_ids if challenge_id not in expected_ids]
    missing_key_rows = {
        row.get("challenge_id", f"row_{idx}"): [
            key for key in C2_REQUIRED_ROW_KEYS if key not in row
        ]
        for idx, row in enumerate(rows)
        if isinstance(row, dict)
    }
    missing_key_rows = {key: val for key, val in missing_key_rows.items() if val}
    placeholder_cells = []
    replay_errors = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        for key in C2_REQUIRED_ROW_KEYS:
            if key in row and contains_template_marker(row[key]):
                placeholder_cells.append(f"{row.get('challenge_id')}:{key}")
        err = row.get("max_unitary_replay_error")
        if isinstance(err, (int, float)):
            replay_errors.append(float(err))
    accepted = (
        len(rows) == 8
        and not missing_ids
        and not extra_ids
        and not missing_key_rows
        and not placeholder_cells
        and len(replay_errors) == 8
        and max(replay_errors) <= STRICT_TOLERANCE
        and template.get("strict_tolerance") == STRICT_TOLERANCE
        and template.get("source_r24_challenge_packet_hash")
        == packet["challenge_packet_hash"]
    )
    result = {
        "accepted": accepted,
        "row_count": len(rows),
        "expected_row_count": 8,
        "expected_challenge_ids": expected_ids,
        "actual_challenge_ids": actual_ids,
        "missing_challenge_ids": missing_ids,
        "extra_challenge_ids": extra_ids,
        "missing_key_rows": missing_key_rows,
        "placeholder_cell_count": len(placeholder_cells),
        "placeholder_cells": placeholder_cells,
        "numeric_replay_error_count": len(replay_errors),
        "max_observed_replay_error": max(replay_errors) if replay_errors else None,
        "strict_tolerance": STRICT_TOLERANCE,
        "challenge_packet_hash_matches": template.get("source_r24_challenge_packet_hash")
        == packet["challenge_packet_hash"],
        "claim_boundary_zero_credit": template.get("o3_closed") is False
        and template.get("reroute_allowed") is False
        and template.get("b7_credit_delta") == 0,
    }
    result["preflight_hash"] = stable_hash(result)
    return result


def build_payload(args: argparse.Namespace) -> tuple[dict[str, Any], dict[str, Any]]:
    started = time.time()
    r24 = load_json(args.r24_harness)
    r29 = load_json(args.r29_preflight)
    template = build_c2_template(r24, r29)
    preflight = evaluate_c2_template(template, r24)
    challenge_packet = challenge_packet_from_r24(r24)
    requirements = [
        requirement(
            "S1",
            "R24 and R29 sources are validation-clean",
            r24["summary"].get("validation_error_count") == 0
            and r29["summary"].get("validation_error_count") == 0,
            {
                "r24_validation_error_count": r24["summary"].get("validation_error_count"),
                "r29_validation_error_count": r29["summary"].get("validation_error_count"),
            },
        ),
        requirement(
            "S2",
            "C2 template covers exactly the 8 O3-F4 challenge rows",
            preflight["row_count"] == 8
            and not preflight["missing_challenge_ids"]
            and not preflight["extra_challenge_ids"],
            {
                "row_count": preflight["row_count"],
                "missing_challenge_ids": preflight["missing_challenge_ids"],
                "extra_challenge_ids": preflight["extra_challenge_ids"],
            },
        ),
        requirement(
            "S3",
            "Every C2 row has the required field surface",
            not preflight["missing_key_rows"],
            {"missing_key_rows": preflight["missing_key_rows"]},
        ),
        requirement(
            "S4",
            "Placeholder C2 rows are rejected and not accepted as replay evidence",
            preflight["accepted"] is False
            and preflight["placeholder_cell_count"] >= 8
            and preflight["numeric_replay_error_count"] == 0,
            {
                "accepted": preflight["accepted"],
                "placeholder_cell_count": preflight["placeholder_cell_count"],
                "numeric_replay_error_count": preflight["numeric_replay_error_count"],
            },
        ),
        requirement(
            "S5",
            "Strict tolerance and source challenge-packet hash are preserved",
            template["strict_tolerance"] == STRICT_TOLERANCE
            and template["source_r24_challenge_packet_hash"]
            == challenge_packet["challenge_packet_hash"],
            {
                "strict_tolerance": template["strict_tolerance"],
                "source_r24_challenge_packet_hash": template[
                    "source_r24_challenge_packet_hash"
                ],
            },
        ),
        requirement(
            "S6",
            "R30 keeps C2, O3, reroute, and B7 credit unaccepted",
            preflight["accepted"] is False
            and template["o3_closed"] is False
            and template["reroute_allowed"] is False
            and template["b7_credit_delta"] == 0,
            {
                "c2_accepted": preflight["accepted"],
                "o3_closed": template["o3_closed"],
                "reroute_allowed": template["reroute_allowed"],
                "b7_credit_delta": template["b7_credit_delta"],
            },
        ),
        requirement(
            "S7",
            "Template and preflight are hash-bound",
            bool(template["template_hash"])
            and bool(template["row_table_hash"])
            and bool(preflight["preflight_hash"]),
            {
                "template_hash": template["template_hash"],
                "row_table_hash": template["row_table_hash"],
                "preflight_hash": preflight["preflight_hash"],
            },
        ),
        requirement(
            "S8",
            "R30 narrows the next work to C2 without claiming C3-C7 progress",
            r29["summary"].get("failed_gate_ids", [])[0]
            == "C2-strict-replay-under-tolerance",
            {
                "r29_failed_gate_ids": r29["summary"].get("failed_gate_ids"),
                "r30_scope": "C2 strict replay rows only",
            },
        ),
    ]
    failed_requirements = [
        item["requirement_id"] for item in requirements if not item["passed"]
    ]
    summary = {
        "candidate_id": CANDIDATE_ID,
        "family_id": FAMILY_ID,
        "source_r24_challenge_packet_hash": challenge_packet["challenge_packet_hash"],
        "source_r24_challenge_table_hash": challenge_packet["challenge_table_hash"],
        "source_r29_preflight_hash": r29["summary"]["preflight_hash"],
        "template_hash": template["template_hash"],
        "row_table_hash": template["row_table_hash"],
        "preflight_hash": preflight["preflight_hash"],
        "strict_tolerance": STRICT_TOLERANCE,
        "required_row_count": 8,
        "template_row_count": preflight["row_count"],
        "placeholder_cell_count": preflight["placeholder_cell_count"],
        "numeric_replay_error_count": preflight["numeric_replay_error_count"],
        "c2_strict_replay_rows_template_emitted": True,
        "c2_strict_replay_rows_accepted": False,
        "c2_preflight_accepted": False,
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
            "C2_source_backed_strict_replay_rows",
            "C3_same_unitary_replay_certificate",
            "C4_C5_same_access_denominator_comparison",
            "C6_leakage_free_optimizer_trace",
            "C7_machine_check_replay_bundle",
        ],
        "remaining_open_obligation_count": 5,
        "requirement_count": len(requirements),
        "requirements_passed": len(requirements) - len(failed_requirements),
        "requirements_failed": len(failed_requirements),
        "failed_requirement_ids": failed_requirements,
        "validation_error_count": len(failed_requirements),
    }
    payload = {
        "title": "B1/B7 Cone01 R30 O3-F4 C2 Strict Replay Row Intake Gate",
        "version": VERSION,
        "last_updated": "2026-07-08",
        "benchmark_id": "B1",
        "linked_benchmark_id": "B7",
        "method": METHOD,
        "status": STATUS,
        "model_status": MODEL_STATUS,
        "source_target_id": TARGET_ID,
        "upstream_target_id": UPSTREAM_TARGET_ID,
        "o3_f4_c2_strict_replay_row_intake_packet": {
            "source_r24_harness": str(args.r24_harness),
            "source_r29_preflight": str(args.r29_preflight),
            "template_output": str(args.template_output),
            "template": template,
            "preflight_result": preflight,
        },
        "requirements": requirements,
        "summary": summary,
        "claim_boundary": {
            "what_is_supported": (
                "R30 emits a source-bound C2 strict replay row template and "
                "proves the placeholder rows are rejected until all 8 challenge "
                "rows contain numeric replay evidence under 1e-08."
            ),
            "what_is_not_supported": (
                "R30 does not accept C2, does not complete the certificate triad, "
                "does not close O3, and does not permit reroute, B7 credit, STV "
                "credit, or resource-saving claims."
            ),
            "next_gate": (
                "Submit 8 source-backed C2 replay rows with numeric max-unitary "
                "errors <= 1e-08, same-unitary witness hashes, source/candidate "
                "circuit hashes, replay commands, stdout hashes, and verifier "
                "versions."
            ),
            "resource_saving_claimed": False,
            "b7_ledger_improvement_claimed": False,
        },
        "validation_errors": failed_requirements,
        "runtime_seconds": round(time.time() - started, 6),
    }
    return payload, template


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    summary = payload["summary"]
    lines = [
        "# B1/B7 Cone01 R30 O3-F4 C2 Strict Replay Row Intake Gate",
        "",
        f"- Target: `{payload['source_target_id']}`",
        f"- Upstream target: `{payload['upstream_target_id']}`",
        f"- Method: `{payload['method']}`",
        f"- Status: `{payload['status']}`",
        f"- Source R24 challenge packet hash: `{summary['source_r24_challenge_packet_hash']}`",
        f"- Source R29 preflight hash: `{summary['source_r29_preflight_hash']}`",
        f"- Template hash: `{summary['template_hash']}`",
        f"- Row table hash: `{summary['row_table_hash']}`",
        f"- Preflight hash: `{summary['preflight_hash']}`",
        "",
        "## Result",
        "",
        (
            f"R30 passes {summary['requirements_passed']}/"
            f"{summary['requirement_count']} requirements by emitting 8 C2 "
            "strict replay row templates and rejecting them as placeholders."
        ),
        "",
        "## C2 Surface",
        "",
        f"- Required row count: `{summary['required_row_count']}`",
        f"- Template row count: `{summary['template_row_count']}`",
        f"- Placeholder cell count: `{summary['placeholder_cell_count']}`",
        f"- Numeric replay error count: `{summary['numeric_replay_error_count']}`",
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
        "--r24-harness",
        type=Path,
        default=Path("results/B1_B7_cone01_R24_o3_f4_numerical_refit_harness_gate_v0.json"),
    )
    parser.add_argument(
        "--r29-preflight",
        type=Path,
        default=Path("results/B1_B7_cone01_R29_o3_f4_certificate_triad_preflight_gate_v0.json"),
    )
    parser.add_argument(
        "--template-output",
        type=Path,
        default=Path(
            "results/B1_B7_cone01_o3_f4_numerical_refit_submissions/"
            "B1-B7-cone01-O3-F4-C2-strict-replay-rows.template.json"
        ),
    )
    parser.add_argument(
        "--json-output",
        type=Path,
        default=Path("results/B1_B7_cone01_R30_o3_f4_c2_strict_replay_row_intake_gate_v0.json"),
    )
    parser.add_argument(
        "--markdown-output",
        type=Path,
        default=Path("research/B1_B7_cone01_R30_o3_f4_c2_strict_replay_row_intake_gate.md"),
    )
    parser.add_argument("--pretty", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    payload, template = build_payload(args)
    write_json(args.template_output, template, pretty=True)
    write_json(args.json_output, payload, pretty=True)
    write_markdown(args.markdown_output, payload)
    if args.pretty:
        print(
            json.dumps(
                {
                    "status": payload["status"],
                    "requirements_passed": payload["summary"]["requirements_passed"],
                    "requirements_failed": payload["summary"]["requirements_failed"],
                    "template_hash": payload["summary"]["template_hash"],
                    "row_table_hash": payload["summary"]["row_table_hash"],
                    "preflight_hash": payload["summary"]["preflight_hash"],
                    "template_row_count": payload["summary"]["template_row_count"],
                    "placeholder_cell_count": payload["summary"]["placeholder_cell_count"],
                    "c2_strict_replay_rows_accepted": payload["summary"][
                        "c2_strict_replay_rows_accepted"
                    ],
                    "o3_closed": payload["summary"]["o3_closed"],
                    "reroute_allowed": payload["summary"]["reroute_allowed"],
                    "b7_credit_delta": payload["summary"]["b7_credit_delta"],
                    "template_output": str(args.template_output),
                    "json_output": str(args.json_output),
                    "markdown_output": str(args.markdown_output),
                },
                indent=2,
                sort_keys=True,
            )
        )


if __name__ == "__main__":
    main()
