#!/usr/bin/env python3
"""T-B4-002h/T-B8-003l: scout real-backend packet evidence without promotion."""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any


METHOD = "b4_b8_real_backend_packet_scout_v0"
STATUS = "real_backend_packet_scout_failed_missing_real_backend_evidence"
MODEL_STATUS = "contract_packets_mapped_but_no_real_backend_or_hardware_transcripts"
VERSION = "0.1"
FAILED_IDS = ["S5", "S6", "S7", "S8", "S9"]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any], pretty: bool) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(payload, indent=2 if pretty else None, sort_keys=True)
    path.write_text(text + "\n", encoding="utf-8")


def requirement(requirement_id: str, label: str, passed: bool, evidence: dict[str, Any]) -> dict[str, Any]:
    return {
        "requirement_id": requirement_id,
        "label": label,
        "passed": bool(passed),
        "evidence": evidence,
    }


def build_payload(root: Path) -> dict[str, Any]:
    start = time.time()
    contract = load_json(root / "results/B4_B8_real_backend_transcript_contract_gate_v0.json")
    readiness = load_json(root / "results/B4_B8_real_backend_transcript_readiness_gate_v0.json")
    fitted = load_json(root / "results/B4_B8_private_challenge_fitted_spoofer_attack_v0.json")

    contract_packets = contract.get("contract_packets", [])
    packet_ids = contract.get("contract_packet_ids", [])
    real_backend_properties_used = bool(contract.get("real_backend_properties_used"))
    hardware_execution_performed = bool(contract.get("hardware_execution_performed"))
    real_backend_transcript_rows = int(contract.get("real_backend_transcript_rows", 0))
    leakage_separated_real_training_performed = bool(
        contract.get("leakage_separated_real_training_performed")
    )
    leakage_blind_acceptance = float(contract.get("leakage_blind_max_no_leak_fitted_acceptance", 1.0))
    full_leakage_acceptance = float(
        contract.get("leakage_aware_max_full_private_material_leak_fitted_acceptance", 1.0)
    )

    rows = []
    source_failures = contract.get("failed_contract_requirement_ids", [])
    for packet in contract_packets:
        packet_id = packet["packet_id"]
        blocks_gate = packet["blocks_gate"]
        rows.append(
            {
                "packet_id": packet_id,
                "blocks_gate": blocks_gate,
                "owner_role": packet["owner_role"],
                "required_artifact_count": len(packet.get("required_artifacts", [])),
                "current_real_evidence_rows": 0,
                "ready_for_positive_claim": False,
                "source_failure_preserved": blocks_gate in source_failures,
            }
        )

    requirements = [
        requirement(
            "S1",
            "Real-backend transcript contract is present and open",
            contract.get("status") == "real_backend_transcript_contract_open_missing_hardware_evidence"
            and contract.get("data_contract_ready_for_prs") is True,
            {
                "source_status": contract.get("status"),
                "contract_packet_count": contract.get("contract_packet_count"),
            },
        ),
        requirement(
            "S2",
            "Synthetic fitted-spoofer and backend-calibrated controls remain available",
            readiness.get("fitted_evaluation_row_count") == 640
            and readiness.get("backend_calibrated_aer_circuit_count") == 5760,
            {
                "fitted_evaluation_row_count": readiness.get("fitted_evaluation_row_count"),
                "backend_calibrated_aer_circuit_count": readiness.get(
                    "backend_calibrated_aer_circuit_count"
                ),
                "source_fitted_method": fitted.get("method"),
            },
        ),
        requirement(
            "S3",
            "Five contract packets map to five preserved readiness blockers",
            len(packet_ids) == 5 and source_failures == ["K5", "K6", "K7", "K8", "K9"],
            {
                "packet_ids": packet_ids,
                "source_failures": source_failures,
            },
        ),
        requirement(
            "S4",
            "Forbidden advantage and soundness claims remain false",
            all(
                contract.get(key) is False
                for key in [
                    "protocol_soundness_proved",
                    "cryptographic_soundness_proved",
                    "sampling_hardness_proved",
                    "quantum_advantage_claimed",
                    "bqp_separation_claimed",
                ]
            ),
            {
                "protocol_soundness_proved": contract.get("protocol_soundness_proved"),
                "quantum_advantage_claimed": contract.get("quantum_advantage_claimed"),
                "bqp_separation_claimed": contract.get("bqp_separation_claimed"),
            },
        ),
        requirement(
            "S5",
            "Real backend properties are present",
            real_backend_properties_used,
            {"real_backend_properties_used": real_backend_properties_used},
        ),
        requirement(
            "S6",
            "Hardware execution transcripts are present",
            hardware_execution_performed and real_backend_transcript_rows > 0,
            {
                "hardware_execution_performed": hardware_execution_performed,
                "real_backend_transcript_rows": real_backend_transcript_rows,
            },
        ),
        requirement(
            "S7",
            "Leakage-separated training on real transcript rows is present",
            leakage_separated_real_training_performed and real_backend_transcript_rows > 0,
            {
                "leakage_separated_real_training_performed": leakage_separated_real_training_performed,
                "real_backend_transcript_rows": real_backend_transcript_rows,
            },
        ),
        requirement(
            "S8",
            "Leakage-blind no-leak fitted acceptance reaches <= 0.10 on real rows",
            leakage_blind_acceptance <= 0.10 and real_backend_transcript_rows > 0,
            {
                "leakage_blind_max_no_leak_fitted_acceptance": leakage_blind_acceptance,
                "real_backend_transcript_rows": real_backend_transcript_rows,
            },
        ),
        requirement(
            "S9",
            "Full-private-material leakage is contained or explicitly excluded on real rows",
            full_leakage_acceptance <= 0.25 and real_backend_transcript_rows > 0,
            {
                "leakage_aware_max_full_private_material_leak_fitted_acceptance": full_leakage_acceptance,
                "real_backend_transcript_rows": real_backend_transcript_rows,
            },
        ),
    ]

    passed = sum(1 for item in requirements if item["passed"])
    failed = len(requirements) - passed
    failed_ids = [item["requirement_id"] for item in requirements if not item["passed"]]
    validation_errors = []
    if failed_ids != FAILED_IDS:
        validation_errors.append(f"Expected failed ids {FAILED_IDS}, got {failed_ids}")
    if len(rows) != 5:
        validation_errors.append("Expected five contract packet rows")

    summary = {
        "source_contract_status": contract.get("status"),
        "source_readiness_status": readiness.get("status"),
        "packet_scout_requirement_count": len(requirements),
        "packet_scout_requirements_passed": passed,
        "packet_scout_requirements_failed": failed,
        "failed_packet_scout_requirement_ids": failed_ids,
        "contract_packet_count": len(rows),
        "contract_packet_ids": packet_ids,
        "source_transcript_case_count": contract.get("source_transcript_case_count"),
        "train_row_count": contract.get("train_row_count"),
        "holdout_row_count": contract.get("holdout_row_count"),
        "fitted_evaluation_row_count": contract.get("fitted_evaluation_row_count"),
        "backend_calibrated_aer_circuit_count": contract.get(
            "backend_calibrated_aer_circuit_count"
        ),
        "qiskit_generic_backend_v2_used": contract.get("qiskit_generic_backend_v2_used"),
        "backend_calibrated_noise_parameters_instantiated": contract.get(
            "backend_calibrated_noise_parameters_instantiated"
        ),
        "real_backend_properties_used": real_backend_properties_used,
        "hardware_execution_performed": hardware_execution_performed,
        "real_backend_transcript_rows": real_backend_transcript_rows,
        "leakage_separated_real_training_performed": leakage_separated_real_training_performed,
        "private_safe_max_no_leak_fitted_acceptance": contract.get(
            "private_safe_max_no_leak_fitted_acceptance"
        ),
        "leakage_blind_max_no_leak_fitted_acceptance": leakage_blind_acceptance,
        "leakage_aware_max_full_private_material_leak_fitted_acceptance": full_leakage_acceptance,
        "real_backend_packet_scout_ready": False,
        "real_backend_transcript_readiness": False,
        "protocol_soundness_proved": False,
        "cryptographic_soundness_proved": False,
        "sampling_hardness_proved": False,
        "quantum_advantage_claimed": False,
        "bqp_separation_claimed": False,
    }

    return {
        "benchmark": "B4/B8",
        "benchmark_id": "B4_B8",
        "title": "B4/B8 real backend packet scout",
        "version": VERSION,
        "method": METHOD,
        "status": STATUS,
        "model_status": MODEL_STATUS,
        "last_updated": "2026-07-01",
        "elapsed_seconds": time.time() - start,
        "summary": summary,
        "rows": rows,
        "requirements": requirements,
        "claim_boundary": {
            "real_backend_packet_scout_built": True,
            "real_backend_properties_used": False,
            "hardware_execution_performed": False,
            "real_backend_transcript_readiness": False,
            "protocol_soundness_proved": False,
            "cryptographic_soundness_proved": False,
            "sampling_hardness_proved": False,
            "quantum_advantage_claimed": False,
            "bqp_separation_claimed": False,
            "what_is_supported": "The five real-backend transcript contract packets are mapped to the current simulated/fitted evidence and remain ready for PR handoff.",
            "what_is_not_supported": "No real backend properties, hardware execution, leakage-separated real fitting, protocol soundness, sampling hardness, quantum advantage, or BQP separation is established.",
        },
        "validation_error_count": len(validation_errors),
        "validation_errors": validation_errors,
    }


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    summary = payload["summary"]
    lines = [
        "# B4/B8 Real Backend Packet Scout v0.1",
        "",
        f"Status: **{payload['status']}**",
        "",
        "## Summary",
        "",
        f"- Method: `{payload['method']}`",
        f"- Model status: `{payload['model_status']}`",
        f"- Requirements passed/failed: {summary['packet_scout_requirements_passed']} / {summary['packet_scout_requirements_failed']}",
        f"- Failed requirement IDs: {', '.join(summary['failed_packet_scout_requirement_ids'])}",
        f"- Contract packets: {summary['contract_packet_count']}",
        f"- Backend-calibrated Aer circuits: {summary['backend_calibrated_aer_circuit_count']}",
        f"- Fitted evaluation / holdout rows: {summary['fitted_evaluation_row_count']} / {summary['holdout_row_count']}",
        f"- Real backend transcript rows: {summary['real_backend_transcript_rows']}",
        f"- Real backend properties used: {summary['real_backend_properties_used']}",
        f"- Hardware execution performed: {summary['hardware_execution_performed']}",
        f"- Leakage-blind no-leak fitted acceptance: {summary['leakage_blind_max_no_leak_fitted_acceptance']}",
        f"- Full-private-material leakage acceptance: {summary['leakage_aware_max_full_private_material_leak_fitted_acceptance']}",
        "",
        "## Requirement Results",
        "",
    ]
    for item in payload["requirements"]:
        marker = "PASS" if item["passed"] else "FAIL"
        lines.append(f"- {item['requirement_id']} [{marker}]: {item['label']}")
    lines.extend(
        [
            "",
            "## Claim Boundary",
            "",
            "- Supported: The real-backend contract packet surface is mapped to current controls and remains PR-ready.",
            "- Not supported: This is not real backend evidence, not hardware execution, not protocol soundness, not sampling hardness, not quantum advantage, and not BQP separation.",
            "- Next gate: Submit real backend properties, hardware transcript rows, leakage-separated fitted rows, a leakage-blind no-leak margin <= 0.10, and a full-leakage containment or exclusion boundary.",
            "",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--json-output", type=Path, default=Path("results/B4_B8_real_backend_packet_scout_v0.json"))
    parser.add_argument("--markdown-output", type=Path, default=Path("research/B4_B8_real_backend_packet_scout.md"))
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()

    root = args.root.resolve()
    payload = build_payload(root)
    write_json(root / args.json_output, payload, args.pretty)
    write_markdown(root / args.markdown_output, payload)
    print(payload["status"])
    print(
        payload["summary"]["packet_scout_requirements_passed"],
        payload["summary"]["packet_scout_requirements_failed"],
        payload["summary"]["failed_packet_scout_requirement_ids"],
    )


if __name__ == "__main__":
    main()
