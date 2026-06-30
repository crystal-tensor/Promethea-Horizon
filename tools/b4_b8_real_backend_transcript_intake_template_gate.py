#!/usr/bin/env python3
"""Build the real-backend transcript intake template for B4/B8/B10."""

from __future__ import annotations

import argparse
import hashlib
import json
import time
from pathlib import Path
from typing import Any


METHOD = "b4_b8_real_backend_transcript_intake_template_gate_v0"
STATUS = "real_backend_transcript_intake_template_open_missing_rows"
MODEL_STATUS = "hardware_transcript_schema_and_margin_packets_built_no_real_rows"
VERSION = "0.1"
EXPECTED_FAILED_IDS = ["T5", "T6", "T7"]
REQUIRED_ROW_KEYS = [
    "transcript_id",
    "backend_name",
    "backend_properties_hash",
    "job_id_hash",
    "circuit_id",
    "qasm_sha256",
    "refresh_mode",
    "shot_count",
    "private_predicate_bit_count",
    "hidden_predicate_mask_hash",
    "leakage_condition",
    "accepted_count",
    "total_count",
    "acceptance_rate",
    "readout_mitigation_tag",
    "calibration_timestamp_utc",
    "raw_counts_sha256",
    "postprocess_script_sha256",
    "claim_boundary",
]
PRODUCTION_REQUIRED_KEYS = [
    "backend_name",
    "backend_properties_hash",
    "job_id_hash",
    "shot_count",
    "leakage_condition",
    "accepted_count",
    "total_count",
    "acceptance_rate",
    "raw_counts_sha256",
    "postprocess_script_sha256",
]


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


def build_intake_row(
    packet_id: str,
    blocks_margin_gate: str,
    owner_role: str,
    acceptance_rule: str,
    current_budget: dict[str, Any],
) -> dict[str, Any]:
    template = {
        "packet_id": packet_id,
        "blocks_margin_gate": blocks_margin_gate,
        "owner_role": owner_role,
        "acceptance_rule": acceptance_rule,
        "current_budget": current_budget,
        "required_row_keys": REQUIRED_ROW_KEYS,
        "production_required_keys": PRODUCTION_REQUIRED_KEYS,
        "submitted_real_backend_rows": 0,
        "accepted_real_backend_rows": 0,
        "ready_for_margin_retest": False,
    }
    template["template_hash"] = stable_hash(
        {
            "packet_id": packet_id,
            "blocks_margin_gate": blocks_margin_gate,
            "required_row_keys": REQUIRED_ROW_KEYS,
            "production_required_keys": PRODUCTION_REQUIRED_KEYS,
            "acceptance_rule": acceptance_rule,
        }
    )
    return template


def build_payload(args: argparse.Namespace) -> dict[str, Any]:
    started = time.time()
    margin = load_json(args.margin_gate)
    packet_scout = load_json(args.packet_scout)
    margin_summary = margin["summary"]
    scout_summary = packet_scout["summary"]

    holdout_rows = int(margin_summary["holdout_row_count"])
    real_backend_rows = int(margin_summary["real_backend_transcript_rows"])
    failed_margin_ids = margin_summary["failed_margin_requirement_ids"]
    no_leak_allowed = margin_summary["leakage_blind_no_leak_budget"]["allowed_accepts"]
    full_leak_allowed = margin_summary["full_private_material_leak_budget"]["allowed_accepts"]

    intake_packets = [
        build_intake_row(
            "B4B8-M4-leakage-blind-no-leak-retest",
            "M4",
            "adversary_margin_agent",
            (
                "Submit leakage-blind no-leak real-backend transcript rows and rerun the "
                f"margin gate with accepted_count <= {no_leak_allowed}/{holdout_rows}."
            ),
            margin_summary["leakage_blind_no_leak_budget"],
        ),
        build_intake_row(
            "B4B8-M5-full-leakage-containment-or-exclusion",
            "M5",
            "protocol_boundary_agent",
            (
                "Either exclude full-private-material leakage by protocol design or submit "
                f"real-backend rows with accepted_count <= {full_leak_allowed}/{holdout_rows}."
            ),
            margin_summary["full_private_material_leak_budget"],
        ),
        build_intake_row(
            "B4B8-M6-real-backend-transcript-rows",
            "M6",
            "hardware_execution_agent",
            "Submit nonzero real-backend transcript rows with hashes for backend properties, jobs, raw counts, and postprocessing.",
            {"real_backend_transcript_rows": real_backend_rows, "required_minimum_rows": holdout_rows},
        ),
    ]

    template_table_hash = stable_hash(intake_packets)
    submitted_real_backend_rows = sum(row["submitted_real_backend_rows"] for row in intake_packets)
    accepted_real_backend_rows = sum(row["accepted_real_backend_rows"] for row in intake_packets)

    requirements = [
        requirement(
            "T1",
            "Real-backend soundness margin gate is present and failed on M4-M6",
            margin.get("method") == "b4_b8_real_backend_soundness_margin_gate_v0"
            and failed_margin_ids == ["M4", "M5", "M6"],
            {
                "source_method": margin.get("method"),
                "source_status": margin.get("status"),
                "failed_margin_requirement_ids": failed_margin_ids,
            },
        ),
        requirement(
            "T2",
            "Packet scout still preserves the real-backend evidence blockers",
            packet_scout.get("method") == "b4_b8_real_backend_packet_scout_v0"
            and scout_summary["failed_packet_scout_requirement_ids"] == ["S5", "S6", "S7", "S8", "S9"],
            {
                "source_method": packet_scout.get("method"),
                "failed_packet_scout_requirement_ids": scout_summary[
                    "failed_packet_scout_requirement_ids"
                ],
            },
        ),
        requirement(
            "T3",
            "Three margin-failure intake packets are generated",
            [row["blocks_margin_gate"] for row in intake_packets] == failed_margin_ids,
            {
                "packet_count": len(intake_packets),
                "packet_ids": [row["packet_id"] for row in intake_packets],
                "blocks_margin_gate_sequence": [row["blocks_margin_gate"] for row in intake_packets],
            },
        ),
        requirement(
            "T4",
            "Transcript row schema is explicit and hashable",
            len(REQUIRED_ROW_KEYS) == 19
            and len(PRODUCTION_REQUIRED_KEYS) == 10
            and bool(template_table_hash),
            {
                "required_row_key_count": len(REQUIRED_ROW_KEYS),
                "production_required_key_count": len(PRODUCTION_REQUIRED_KEYS),
                "template_table_hash": template_table_hash,
            },
        ),
        requirement(
            "T5",
            "Submitted real-backend transcript rows are present",
            submitted_real_backend_rows > 0,
            {"submitted_real_backend_rows": submitted_real_backend_rows},
        ),
        requirement(
            "T6",
            "Accepted real-backend transcript rows cover all margin packets",
            accepted_real_backend_rows >= len(intake_packets),
            {
                "accepted_real_backend_rows": accepted_real_backend_rows,
                "required_margin_packets": len(intake_packets),
            },
        ),
        requirement(
            "T7",
            "Real-backend margin retest is ready",
            all(row["ready_for_margin_retest"] for row in intake_packets),
            {
                "ready_packet_count": sum(row["ready_for_margin_retest"] for row in intake_packets),
                "required_packet_count": len(intake_packets),
            },
        ),
        requirement(
            "T8",
            "Forbidden soundness, advantage, and BQP claims remain false",
            all(
                margin["claim_boundary"].get(key) is False
                for key in [
                    "protocol_soundness_proved",
                    "cryptographic_soundness_proved",
                    "sampling_hardness_proved",
                    "quantum_advantage_claimed",
                    "bqp_separation_claimed",
                ]
            ),
            {
                "protocol_soundness_proved": margin["claim_boundary"].get(
                    "protocol_soundness_proved"
                ),
                "quantum_advantage_claimed": margin["claim_boundary"].get(
                    "quantum_advantage_claimed"
                ),
                "bqp_separation_claimed": margin["claim_boundary"].get("bqp_separation_claimed"),
            },
        ),
    ]

    passed_count = sum(row["passed"] for row in requirements)
    failed_ids = [row["requirement_id"] for row in requirements if not row["passed"]]
    validation_errors: list[str] = []
    if failed_ids != EXPECTED_FAILED_IDS:
        validation_errors.append(f"unexpected failed transcript-intake requirements: {failed_ids}")
    if real_backend_rows != 0:
        validation_errors.append("template gate must not fabricate real backend transcript rows")
    if submitted_real_backend_rows != 0 or accepted_real_backend_rows != 0:
        validation_errors.append("template gate should not accept transcript rows")

    summary = {
        "source_margin_status": margin.get("status"),
        "source_packet_scout_status": packet_scout.get("status"),
        "intake_requirement_count": len(requirements),
        "intake_requirements_passed": passed_count,
        "intake_requirements_failed": len(requirements) - passed_count,
        "failed_intake_requirement_ids": failed_ids,
        "failed_margin_requirement_ids": failed_margin_ids,
        "packet_count": len(intake_packets),
        "packet_ids": [row["packet_id"] for row in intake_packets],
        "required_row_key_count": len(REQUIRED_ROW_KEYS),
        "production_required_key_count": len(PRODUCTION_REQUIRED_KEYS),
        "template_table_hash": template_table_hash,
        "holdout_row_count": holdout_rows,
        "real_backend_transcript_rows": real_backend_rows,
        "submitted_real_backend_rows": submitted_real_backend_rows,
        "accepted_real_backend_rows": accepted_real_backend_rows,
        "no_leak_allowed_accepts_per_160": no_leak_allowed,
        "full_leak_allowed_accepts_per_160": full_leak_allowed,
        "leakage_blind_excess_accepts_per_160": margin_summary[
            "leakage_blind_excess_accepts_per_160"
        ],
        "full_leak_excess_accepts_per_160": margin_summary["full_leak_excess_accepts_per_160"],
        "real_backend_transcript_intake_ready": False,
        "real_backend_margin_retest_ready": False,
        "protocol_soundness_proved": False,
        "cryptographic_soundness_proved": False,
        "sampling_hardness_proved": False,
        "quantum_advantage_claimed": False,
        "bqp_separation_claimed": False,
        "validation_error_count": len(validation_errors),
    }

    return {
        "benchmark": "B4/B8",
        "benchmark_id": "B4_B8",
        "source_target_id": "B10-T2",
        "dependency_benchmarks": ["B4", "B8", "B10"],
        "title": "B4/B8 Real-Backend Transcript Intake Template Gate v0",
        "version": VERSION,
        "last_updated": args.last_updated,
        "method": METHOD,
        "status": STATUS,
        "model_status": MODEL_STATUS,
        "source_margin_gate_result": str(args.margin_gate),
        "source_packet_scout_result": str(args.packet_scout),
        "summary": summary,
        "requirements": requirements,
        "required_row_keys": REQUIRED_ROW_KEYS,
        "production_required_keys": PRODUCTION_REQUIRED_KEYS,
        "intake_packets": intake_packets,
        "claim_boundary": {
            "what_is_supported": (
                "The failed real-backend margin gates M4-M6 have been converted into "
                "hashable transcript intake packets with explicit row keys and acceptance budgets."
            ),
            "what_is_not_supported": (
                "No real backend rows are submitted or accepted, the margin gate is not ready "
                "to rerun, and no protocol soundness, quantum advantage, sampling hardness, "
                "or BQP separation is established."
            ),
            "next_gate": (
                "Submit real-backend transcript rows satisfying the 19-key schema, keep "
                "leakage-blind no-leak accepts <= 16/160, and either exclude full leakage "
                "or keep full-leak accepts <= 40/160."
            ),
            "protocol_soundness_proved": False,
            "cryptographic_soundness_proved": False,
            "sampling_hardness_proved": False,
            "quantum_advantage_claimed": False,
            "bqp_separation_claimed": False,
        },
        "validation_errors": validation_errors,
        "runtime_seconds": time.time() - started,
    }


def write_markdown(payload: dict[str, Any], path: Path) -> None:
    summary = payload["summary"]
    lines = [
        "# B4/B8 Real-Backend Transcript Intake Template Gate",
        "",
        f"Status: **{payload['status']}**",
        "",
        "## Summary",
        "",
        f"- Method: `{payload['method']}`",
        f"- Model status: `{payload['model_status']}`",
        f"- Intake requirements passed/failed: {summary['intake_requirements_passed']} / {summary['intake_requirements_failed']}",
        f"- Failed intake requirement IDs: {summary['failed_intake_requirement_ids']}",
        f"- Margin blockers covered: {summary['failed_margin_requirement_ids']}",
        f"- Transcript row schema keys: {summary['required_row_key_count']}",
        f"- Production-required row keys: {summary['production_required_key_count']}",
        f"- Template table hash: `{summary['template_table_hash']}`",
        f"- Holdout rows / real backend rows: {summary['holdout_row_count']} / {summary['real_backend_transcript_rows']}",
        f"- No-leak budget: <= {summary['no_leak_allowed_accepts_per_160']} accepts per 160",
        f"- Full-leak budget: <= {summary['full_leak_allowed_accepts_per_160']} accepts per 160",
        "",
        "## Intake Packets",
        "",
        "| Packet | Blocks | Owner | Submitted rows | Accepted rows | Ready |",
        "|---|---|---|---:|---:|---|",
    ]
    for row in payload["intake_packets"]:
        lines.append(
            f"| {row['packet_id']} | {row['blocks_margin_gate']} | {row['owner_role']} | "
            f"{row['submitted_real_backend_rows']} | {row['accepted_real_backend_rows']} | "
            f"{row['ready_for_margin_retest']} |"
        )
    lines.extend(
        [
            "",
            "## Transcript Row Schema",
            "",
            ", ".join(payload["required_row_keys"]),
            "",
            "## Requirement Results",
            "",
        ]
    )
    for row in payload["requirements"]:
        status = "PASS" if row["passed"] else "FAIL"
        lines.append(f"- {row['requirement_id']} [{status}]: {row['label']}")
    lines.extend(
        [
            "",
            "## Claim Boundary",
            "",
            f"- Supported: {payload['claim_boundary']['what_is_supported']}",
            f"- Not supported: {payload['claim_boundary']['what_is_not_supported']}",
            f"- Next gate: {payload['claim_boundary']['next_gate']}",
            f"- protocol_soundness_proved: {payload['claim_boundary']['protocol_soundness_proved']}",
            f"- quantum_advantage_claimed: {payload['claim_boundary']['quantum_advantage_claimed']}",
            f"- bqp_separation_claimed: {payload['claim_boundary']['bqp_separation_claimed']}",
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
        "--margin-gate",
        type=Path,
        default=Path("results/B4_B8_real_backend_soundness_margin_gate_v0.json"),
    )
    parser.add_argument(
        "--packet-scout",
        type=Path,
        default=Path("results/B4_B8_real_backend_packet_scout_v0.json"),
    )
    parser.add_argument(
        "--json-output",
        type=Path,
        default=Path("results/B4_B8_real_backend_transcript_intake_template_gate_v0.json"),
    )
    parser.add_argument(
        "--markdown-output",
        type=Path,
        default=Path("research/B4_B8_real_backend_transcript_intake_template_gate.md"),
    )
    parser.add_argument("--last-updated", default="2026-07-01")
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()

    payload = build_payload(args)
    write_json(args.json_output, payload, pretty=args.pretty)
    write_markdown(payload, args.markdown_output)

    summary = payload["summary"]
    print(json.dumps(summary, indent=2 if args.pretty else None, sort_keys=True))
    if payload["validation_errors"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
