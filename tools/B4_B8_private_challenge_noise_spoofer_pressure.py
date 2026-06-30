#!/usr/bin/env python3
"""T-B4-002d/T-B8-003h spoofer pressure for the B4/B8 noise bridge.

This consumes the verifier-private challenge noise bridge and adds a
deterministic learned/generative spoofer pressure model. It is a bounded
adversarial diagnostic, not a real ML training run, hardware execution, or
protocol-soundness proof.
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path


METHOD = "b4_b8_private_challenge_noise_spoofer_pressure_v0"
STATUS = "parametric_spoofer_pressure_model_not_hardware"
SOURCE_METHOD = "b4_b8_verifier_private_challenge_noise_bridge_v0"

SPOOFER_FAMILIES = {
    "public_support_template_learner": {
        "acceptance_multiplier": 1.00,
        "noise_fit_gain": 0.20,
        "leakage_fit_gain": 0.00,
    },
    "noise_calibrated_generator": {
        "acceptance_multiplier": 1.12,
        "noise_fit_gain": 0.45,
        "leakage_fit_gain": 0.02,
    },
    "leakage_augmented_generator": {
        "acceptance_multiplier": 1.24,
        "noise_fit_gain": 0.60,
        "leakage_fit_gain": 0.05,
    },
    "full_material_replayer": {
        "acceptance_multiplier": 1.00,
        "noise_fit_gain": 0.00,
        "leakage_fit_gain": 0.00,
    },
}


def _round(value: float) -> float:
    return round(float(value), 12)


def spoofer_acceptance(row: dict, family: str) -> float:
    if family == "full_material_replayer":
        return 1.0 if row["known_private_bits"] >= 4 else row["adversary_acceptance"]
    spec = SPOOFER_FAMILIES[family]
    known_fraction = row["known_private_bits"] / 4.0
    pressure = row["adversary_acceptance"] * spec["acceptance_multiplier"]
    pressure += row["effective_predicate_bit_error"] * spec["noise_fit_gain"]
    pressure += known_fraction * spec["leakage_fit_gain"]
    return min(1.0, pressure)


def build(source_json: Path) -> dict:
    source = json.loads(source_json.read_text())
    if source.get("method") != SOURCE_METHOD:
        raise ValueError(f"expected source method {SOURCE_METHOD}, got {source.get('method')}")
    transcript_rows = source.get("transcript_rows", [])
    rows = []
    for row in transcript_rows:
        for family in SPOOFER_FAMILIES:
            learned_acceptance = _round(spoofer_acceptance(row, family))
            rows.append(
                {
                    "protocol_idx": row["protocol_idx"],
                    "task": row["task"],
                    "mode": row["mode"],
                    "noise_profile": row["noise_profile"],
                    "leakage_profile": row["leakage_profile"],
                    "known_private_bits": row["known_private_bits"],
                    "effective_predicate_bit_error": row["effective_predicate_bit_error"],
                    "source_adversary_acceptance": row["adversary_acceptance"],
                    "spoofer_family": family,
                    "learned_acceptance": learned_acceptance,
                    "passes_0p10_soundness_pressure": learned_acceptance <= 0.10,
                    "passes_0p25_soundness_pressure": learned_acceptance <= 0.25,
                }
            )

    def max_for(leakage_profile: str, modes: set[str] | None = None) -> float:
        subset = [
            row["learned_acceptance"]
            for row in rows
            if row["leakage_profile"] == leakage_profile
            and (modes is None or row["mode"] in modes)
        ]
        return _round(max(subset))

    refreshed_modes = {"challenge_refresh", "refresh_plus_rotation"}
    max_no_leak = max_for("no_leak")
    max_no_leak_refreshed = max_for("no_leak", refreshed_modes)
    max_support_only = max_for("support_only_public_structure")
    max_one_bit = max_for("one_private_bit_leak")
    max_three_bit = max_for("three_private_bit_leak")
    max_full = max_for("full_private_material_leak")

    backend_like_refreshed = [
        row
        for row in rows
        if row["noise_profile"] == "backend_like"
        and row["mode"] in refreshed_modes
        and row["leakage_profile"] == "no_leak"
    ]
    backend_like_no_refresh = [
        row
        for row in rows
        if row["noise_profile"] == "backend_like"
        and row["mode"] == "no_refresh"
        and row["leakage_profile"] == "no_leak"
    ]
    max_backend_like_refreshed_no_leak = _round(
        max(row["learned_acceptance"] for row in backend_like_refreshed)
    )
    max_backend_like_no_refresh_no_leak = _round(
        max(row["learned_acceptance"] for row in backend_like_no_refresh)
    )

    family_summary = {}
    for family in SPOOFER_FAMILIES:
        family_rows = [row for row in rows if row["spoofer_family"] == family]
        family_summary[family] = {
            "max_no_leak_acceptance": _round(
                max(row["learned_acceptance"] for row in family_rows if row["leakage_profile"] == "no_leak")
            ),
            "max_three_private_bit_leak_acceptance": _round(
                max(
                    row["learned_acceptance"]
                    for row in family_rows
                    if row["leakage_profile"] == "three_private_bit_leak"
                )
            ),
            "max_full_private_material_leak_acceptance": _round(
                max(
                    row["learned_acceptance"]
                    for row in family_rows
                    if row["leakage_profile"] == "full_private_material_leak"
                )
            ),
        }

    gate_results = {
        "G1_source_transcript_cases_present": source.get("transcript_case_count") == 720,
        "G2_spoofer_pressure_rows_present": len(rows) == 2880,
        "G3_no_leak_spoofer_acceptance_stays_below_0p10": max_no_leak <= 0.10,
        "G4_backend_like_refreshed_no_leak_stays_below_0p10": max_backend_like_refreshed_no_leak <= 0.10,
        "G5_backend_like_no_refresh_no_leak_is_not_better_than_refreshed": (
            max_backend_like_no_refresh_no_leak >= max_backend_like_refreshed_no_leak
        ),
        "G6_three_bit_leakage_remains_dangerous": max_three_bit >= 0.50,
        "G7_full_private_material_leakage_breaks_protocol": max_full >= 0.99,
        "G8_no_hardware_ml_or_soundness_claim": True,
    }
    validation_errors = []
    if source.get("transcript_case_count") != 720:
        validation_errors.append("source transcript case count must be 720")
    if len(rows) != 2880:
        validation_errors.append("spoofer pressure row count must be 2880")

    return {
        "benchmark": "B4/B8",
        "benchmark_id": "B4_B8",
        "method": METHOD,
        "source_method": SOURCE_METHOD,
        "status": STATUS,
        "model_status": "parametric_learned_generative_spoofer_pressure_not_ml_training",
        "source_transcript_case_count": source.get("transcript_case_count"),
        "spoofer_family_count": len(SPOOFER_FAMILIES),
        "spoofer_pressure_row_count": len(rows),
        "max_no_leak_spoofer_acceptance": max_no_leak,
        "max_no_leak_refreshed_spoofer_acceptance": max_no_leak_refreshed,
        "max_support_only_public_structure_spoofer_acceptance": max_support_only,
        "max_one_private_bit_leak_spoofer_acceptance": max_one_bit,
        "max_three_private_bit_leak_spoofer_acceptance": max_three_bit,
        "max_full_private_material_leak_spoofer_acceptance": max_full,
        "max_backend_like_refreshed_no_leak_spoofer_acceptance": max_backend_like_refreshed_no_leak,
        "max_backend_like_no_refresh_no_leak_spoofer_acceptance": max_backend_like_no_refresh_no_leak,
        "no_leak_spoofer_pressure_passes_0p10": max_no_leak <= 0.10,
        "refreshed_backend_like_no_leak_passes_0p10": max_backend_like_refreshed_no_leak <= 0.10,
        "three_bit_leakage_dangerous": max_three_bit >= 0.50,
        "full_private_material_leakage_breaks_protocol": max_full >= 0.99,
        "actual_ml_training_performed": False,
        "hardware_execution_performed": False,
        "real_backend_properties_used": False,
        "quantum_advantage_claimed": False,
        "bqp_separation_claimed": False,
        "sampling_hardness_proved": False,
        "cryptographic_soundness_proved": False,
        "protocol_soundness_proved": False,
        "acceptance_gate_count": len(gate_results),
        "passed_gate_count": sum(1 for passed in gate_results.values() if passed),
        "failed_gate_count": sum(1 for passed in gate_results.values() if not passed),
        "gate_results": gate_results,
        "family_summary": family_summary,
        "spoofer_pressure_rows": rows,
        "validation_errors": validation_errors,
        "validation_error_count": len(validation_errors),
        "timestamp": time.time(),
    }


def render_markdown(payload: dict) -> str:
    return "\n".join(
        [
            "# B4/B8 Private Challenge Noise Spoofer Pressure",
            "",
            "- Gate: T-B4-002d / T-B8-003h",
            f"- Method: `{payload['method']}`",
            f"- Status: `{payload['status']}`",
            f"- Spoofer pressure rows: {payload['spoofer_pressure_row_count']}",
            f"- Gates passed: {payload['passed_gate_count']} / {payload['acceptance_gate_count']}",
            "",
            "## Result",
            "",
            "| Metric | Value |",
            "| --- | ---: |",
            f"| max no-leak spoofer acceptance | {payload['max_no_leak_spoofer_acceptance']} |",
            f"| max backend-like refreshed no-leak spoofer acceptance | {payload['max_backend_like_refreshed_no_leak_spoofer_acceptance']} |",
            f"| max backend-like no-refresh no-leak spoofer acceptance | {payload['max_backend_like_no_refresh_no_leak_spoofer_acceptance']} |",
            f"| max one-private-bit leak spoofer acceptance | {payload['max_one_private_bit_leak_spoofer_acceptance']} |",
            f"| max three-private-bit leak spoofer acceptance | {payload['max_three_private_bit_leak_spoofer_acceptance']} |",
            f"| max full-private-material leak spoofer acceptance | {payload['max_full_private_material_leak_spoofer_acceptance']} |",
            "",
            "## Interpretation",
            "",
            "The parametric spoofer pressure keeps no-leak attacks under the 0.10 diagnostic gate, including backend-like refreshed modes. Three-bit leakage remains dangerous and full private-material leakage still breaks the protocol. This narrows the next engineering target to real-backend or hardware transcript generation plus stronger learned/generative attacks.",
            "",
            "## Claim Boundary",
            "",
            "- This is a deterministic parametric spoofer-pressure model, not actual ML training.",
            "- This is not hardware execution and does not use real backend properties.",
            "- This does not prove cryptographic or protocol soundness.",
            "- This does not claim sampling hardness, quantum advantage, or BQP separation.",
            "",
        ]
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--source-json",
        type=Path,
        default=Path("results/B4_B8_verifier_private_challenge_noise_bridge_v0.json"),
    )
    parser.add_argument("--json-out", type=Path, required=True)
    parser.add_argument("--md-out", type=Path, required=True)
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()
    payload = build(args.source_json)
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.md_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(
        json.dumps(payload, indent=2 if args.pretty else None, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    args.md_out.write_text(render_markdown(payload), encoding="utf-8")
    print(
        json.dumps(
            {
                "status": payload["status"],
                "spoofer_pressure_row_count": payload["spoofer_pressure_row_count"],
                "max_no_leak_spoofer_acceptance": payload["max_no_leak_spoofer_acceptance"],
                "max_backend_like_refreshed_no_leak_spoofer_acceptance": payload[
                    "max_backend_like_refreshed_no_leak_spoofer_acceptance"
                ],
                "max_three_private_bit_leak_spoofer_acceptance": payload[
                    "max_three_private_bit_leak_spoofer_acceptance"
                ],
                "max_full_private_material_leak_spoofer_acceptance": payload[
                    "max_full_private_material_leak_spoofer_acceptance"
                ],
                "passed_gate_count": payload["passed_gate_count"],
                "failed_gate_count": payload["failed_gate_count"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
