#!/usr/bin/env python3
"""Execute the preregistered R145 counterbalanced runtime benchmark."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import statistics
import time
from datetime import datetime
from pathlib import Path

from b4_b8_r119_private_observable_bundle_gate import write_json
from b4_b8_r126_calibration_attribution_ledger import file_sha256
from b4_b8_r144_live_runtime_benchmark import ensure_environment, identity, prepare, run_strategy


METHOD = "b4_b8_r145_counterbalanced_runtime_benchmark_v0"
CONTRACT_PATH = "benchmarks/B4_B8_R145_counterbalanced_runtime_contract_v0.json"
CONTRACT_SHA256 = "ab414301268580529042bc3e5e5e5f13a29a58b9cf78d08b191f34a856c48690"
PREREGISTRATION_COMMIT = "eb02ff81f16cf6bb11cfc3b86b6944fa76308ec0"
PREREGISTRATION_DISCUSSION = "https://github.com/crystal-tensor/Prometheus-plan/discussions/153"
PREREGISTRATION_CREATED_AT = "2026-07-13T09:20:54Z"
PROTOCOL_PATH = "results/B4_B8_R145_counterbalanced_runtime_protocol_v0.json"
R142_PATH = "results/B4_B8_R142_seed_robust_lcb_mapping_design_v0.json"
R143_PATH = "results/B4_B8_R143_successive_halving_lcb_design_v0.json"
RESULT_PATH = "results/B4_B8_R145_counterbalanced_runtime_benchmark_v0.json"
REPORT_PATH = "research/B4_B8_R145_counterbalanced_runtime_benchmark.md"
OUT_DIR = "results/B4_B8_R145_counterbalanced_runtime_benchmark"
COMMITMENT_PATH = f"{OUT_DIR}/challenge_commitment.json"
MEASUREMENT_PATH = f"{OUT_DIR}/runtime_measurement.json"
REVEAL_PATH = f"{OUT_DIR}/challenge_reveal.json"
TRANSCRIPT_PATH = f"{OUT_DIR}/verifier_transcript.json"


def utc_timestamp(value: str) -> int:
    return int(datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp())


def match_count(rows: list[dict], expected: dict) -> int:
    return sum(
        (tuple(row["mapping"]), row["policy_id"], row["realization_seed"])
        == expected[(row["snapshot"], row["task_id"])]
        for row in rows
    )


def report(payload: dict) -> str:
    summary = payload["summary"]
    verdict = "ACCEPT" if summary["global_acceptance"] else "REJECT"
    conditions = "\n".join(
        f"- {row['condition_id']} {'PASS' if row['passed'] else 'FAIL'}: "
        f"{row['label']}; value {row['value']}, threshold {row['threshold']}."
        for row in payload["acceptance_conditions"]
    )
    pair_values = ", ".join(f"{value:.2%}" for value in summary["pair_runtime_reduction_fractions"])
    return f"""# B4/B8 R145 Counterbalanced Runtime Benchmark

- Preregistered verdict: {verdict}
- Secret-selected schedule: `{summary['schedule_code']}`
- Full repeat seconds: `{summary['full_elapsed_seconds']}`
- Halving repeat seconds: `{summary['halving_elapsed_seconds']}`
- Pooled runtime reduction: `{summary['pooled_runtime_reduction_fraction']:.2%}`
- Adjacent pair runtime reductions: `{pair_values}`
- Pair-reduction spread: `{summary['pair_reduction_spread_fraction']:.2%}`
- Pooled halving/full per-execution ratio: `{summary['pooled_per_execution_runtime_ratio']:.6f}`
- Full / halving selection replay: `{summary['full_selection_match_count']} / 24`, `{summary['halving_selection_match_count']} / 24`
- Shared setup / warmup seconds: `{summary['shared_setup_seconds']:.6f}` / `{summary['warmup_seconds']:.6f}`
- Conditions passed / failed: `{summary['acceptance_conditions_passed']} / {summary['acceptance_conditions_failed']}`
- New credit delta: `0`

## Acceptance Conditions

{conditions}

## Claim Boundary

Supported only if accepted: one same-machine counterbalanced repeated-order
execution-loop timing result. Not supported: cross-machine or cross-calibration
transfer, hardware or cloud billing savings, protocol soundness, quantum
advantage, BQP separation, solved B4/B8/B10, or new credit.
"""


def run_gate(root: Path) -> dict:
    root = root.resolve()
    if file_sha256(root / CONTRACT_PATH) != CONTRACT_SHA256:
        raise ValueError("R145 contract hash mismatch")
    contract = json.loads((root / CONTRACT_PATH).read_text())
    protocol_payload = json.loads((root / PROTOCOL_PATH).read_text())
    if (
        file_sha256(root / PROTOCOL_PATH) != contract["source_bindings"]["protocol_sha256"]
        or protocol_payload["payload_hash"] != contract["source_bindings"]["protocol_payload_hash"]
    ):
        raise ValueError("R145 protocol binding mismatch")

    protocol = protocol_payload["protocol"]
    r142 = json.loads((root / R142_PATH).read_text())
    r143 = json.loads((root / R143_PATH).read_text())
    out = root / OUT_DIR
    out.mkdir(parents=True, exist_ok=True)
    commitment_path = root / COMMITMENT_PATH
    measurement_path = root / MEASUREMENT_PATH
    reveal_path = root / REVEAL_PATH
    transcript_path = root / TRANSCRIPT_PATH

    if reveal_path.exists():
        secret = bytes.fromhex(json.loads(reveal_path.read_text())["challenge_secret_hex"])
    else:
        secret = os.urandom(32)
    commitment = hashlib.sha256(secret).hexdigest()
    if commitment_path.exists():
        commitment_payload = json.loads(commitment_path.read_text())
        if commitment_payload["challenge_secret_commitment_sha256"] != commitment:
            raise ValueError("R145 challenge commitment mismatch")
    else:
        commitment_payload = {
            "contract_sha256": CONTRACT_SHA256,
            "preregistration_commit": PREREGISTRATION_COMMIT,
            "preregistration_discussion": PREREGISTRATION_DISCUSSION,
            "preregistration_created_at": PREREGISTRATION_CREATED_AT,
            "challenge_generated_at_unix": int(time.time()),
            "challenge_secret_commitment_sha256": commitment,
            "secret_revealed": False,
        }
        write_json(commitment_path, commitment_payload)

    schedule_code = "ABBA" if secret[0] & 1 else "BAAB"
    schedule = ["full" if label == "A" else "halving" for label in schedule_code]
    measurement_reused = measurement_path.exists()
    if measurement_reused:
        measurement = json.loads(measurement_path.read_text())
    else:
        contexts, setup_ns, warmup_ns = prepare(root, r142)
        records = []
        for run_index, strategy in enumerate(schedule):
            record = run_strategy(
                strategy,
                contexts,
                protocol["design_seeds"],
                protocol["shots_per_execution"],
            )
            record["run_index"] = run_index
            records.append(record)
        measurement = {
            "contract_sha256": CONTRACT_SHA256,
            "measured_at_unix": int(time.time()),
            "schedule_code": schedule_code,
            "strategy_schedule": schedule,
            "shared_setup_ns": setup_ns,
            "warmup_ns": warmup_ns,
            "strategy_records": records,
        }
        write_json(measurement_path, measurement)
    if measurement["schedule_code"] != schedule_code or measurement["strategy_schedule"] != schedule:
        raise ValueError("R145 secret-selected schedule mismatch")

    reveal = {
        "contract_sha256": CONTRACT_SHA256,
        "challenge_secret_hex": secret.hex(),
        "challenge_secret_commitment_sha256": commitment,
        "commitment_matches": hashlib.sha256(secret).hexdigest() == commitment,
        "measurement_precedes_reveal": measurement_path.exists(),
        "schedule_code": schedule_code,
    }
    write_json(reveal_path, reveal)

    records = measurement["strategy_records"]
    full_records = [row for row in records if row["strategy"] == "full"]
    halving_records = [row for row in records if row["strategy"] == "halving"]
    expected_full = {
        (row["snapshot"], row["task_id"]): identity(row, "selected_")
        for row in r142["group_rows"]
    }
    expected_halving = {
        (row["snapshot"], row["task_id"]): identity(row, "selected_")
        for row in r143["group_rows"]
    }
    full_matches = sum(match_count(row["selection_rows"], expected_full) for row in full_records)
    halving_matches = sum(match_count(row["selection_rows"], expected_halving) for row in halving_records)
    full_elapsed_ns = sum(row["elapsed_ns"] for row in full_records)
    halving_elapsed_ns = sum(row["elapsed_ns"] for row in halving_records)
    full_executions = sum(row["total_execution_count"] for row in full_records)
    halving_executions = sum(row["total_execution_count"] for row in halving_records)
    pooled_reduction = 1 - halving_elapsed_ns / full_elapsed_ns
    per_execution_ratio = (halving_elapsed_ns / halving_executions) / (full_elapsed_ns / full_executions)
    pair_rows = []
    for pair_index, indices in enumerate(protocol["pairing_rule"]):
        pair = [records[index] for index in indices]
        full = next(row for row in pair if row["strategy"] == "full")
        halving = next(row for row in pair if row["strategy"] == "halving")
        pair_rows.append({
            "pair_index": pair_index,
            "run_indices": indices,
            "full_elapsed_ns": full["elapsed_ns"],
            "halving_elapsed_ns": halving["elapsed_ns"],
            "runtime_reduction_fraction": 1 - halving["elapsed_ns"] / full["elapsed_ns"],
        })
    pair_reductions = [row["runtime_reduction_fraction"] for row in pair_rows]
    pair_spread = max(pair_reductions) - min(pair_reductions)
    measurement_sha256 = file_sha256(measurement_path)
    summary = {
        "schedule_code": schedule_code,
        "strategy_schedule": schedule,
        "full_elapsed_ns": [row["elapsed_ns"] for row in full_records],
        "full_elapsed_seconds": [row["elapsed_seconds"] for row in full_records],
        "halving_elapsed_ns": [row["elapsed_ns"] for row in halving_records],
        "halving_elapsed_seconds": [row["elapsed_seconds"] for row in halving_records],
        "pooled_full_elapsed_seconds": full_elapsed_ns / 1e9,
        "pooled_halving_elapsed_seconds": halving_elapsed_ns / 1e9,
        "pooled_runtime_reduction_fraction": pooled_reduction,
        "pair_runtime_reduction_fractions": pair_reductions,
        "pair_reduction_spread_fraction": pair_spread,
        "execution_reduction_fraction": 1 - halving_executions / full_executions,
        "pooled_per_execution_runtime_ratio": per_execution_ratio,
        "full_execution_counts": [row["total_execution_count"] for row in full_records],
        "halving_execution_counts": [row["total_execution_count"] for row in halving_records],
        "full_execution_count_total": full_executions,
        "halving_execution_count_total": halving_executions,
        "full_selection_match_count": full_matches,
        "halving_selection_match_count": halving_matches,
        "shared_setup_seconds": measurement["shared_setup_ns"] / 1e9,
        "warmup_seconds": measurement["warmup_ns"] / 1e9,
        "measurement_reused": measurement_reused,
        "measurement_sha256": measurement_sha256,
        "cross_machine_transfer_claimed": False,
        "cross_calibration_transfer_claimed": False,
        "hardware_savings_claimed": False,
        "cloud_billing_savings_claimed": False,
        "quantum_advantage_claimed": False,
        "bqp_separation_claimed": False,
        "solved_frontier_claimed": False,
        "new_credit_delta": 0,
    }
    conditions = [
        {"condition_id": "A1", "label": "protocol and source bindings remain exact", "value": True, "threshold": True, "passed": True},
        {"condition_id": "A2", "label": "per-repeat execution counts", "value": [summary["full_execution_counts"], summary["halving_execution_counts"]], "threshold": [[1728, 1728], [816, 816]], "passed": summary["full_execution_counts"] == [1728, 1728] and summary["halving_execution_counts"] == [816, 816]},
        {"condition_id": "A3", "label": "two full repeats reproduce R142 selections", "value": full_matches, "threshold": 24, "passed": full_matches == 24},
        {"condition_id": "A4", "label": "two halving repeats reproduce R143 selections", "value": halving_matches, "threshold": 24, "passed": halving_matches == 24},
        {"condition_id": "A5", "label": "pooled execution-loop runtime reduction", "value": pooled_reduction, "threshold": ">= 0.30", "passed": pooled_reduction >= 0.30},
        {"condition_id": "A6", "label": "each adjacent pair runtime reduction", "value": pair_reductions, "threshold": "each >= 0.20", "passed": all(value >= 0.20 for value in pair_reductions)},
        {"condition_id": "A7", "label": "pair runtime-reduction spread", "value": pair_spread, "threshold": "<= 0.15", "passed": pair_spread <= 0.15},
        {"condition_id": "A8", "label": "pooled halving/full per-execution runtime ratio", "value": per_execution_ratio, "threshold": "0.5 to 2.0", "passed": 0.5 <= per_execution_ratio <= 2.0},
        {"condition_id": "A9", "label": "secret schedule and transcript hashes verify", "value": schedule_code, "threshold": "ABBA or BAAB from committed secret", "passed": reveal["commitment_matches"] and measurement["strategy_schedule"] == schedule},
        {"condition_id": "A10", "label": "downstream claims and credit remain false", "value": 0, "threshold": 0, "passed": not any([summary["cross_machine_transfer_claimed"], summary["cross_calibration_transfer_claimed"], summary["hardware_savings_claimed"], summary["cloud_billing_savings_claimed"], summary["quantum_advantage_claimed"], summary["bqp_separation_claimed"], summary["solved_frontier_claimed"], summary["new_credit_delta"]])},
    ]
    summary.update({
        "acceptance_conditions_passed": sum(row["passed"] for row in conditions),
        "acceptance_conditions_failed": sum(not row["passed"] for row in conditions),
        "failed_acceptance_condition_ids": [row["condition_id"] for row in conditions if not row["passed"]],
        "global_acceptance": all(row["passed"] for row in conditions),
    })
    transcript = {
        "contract_sha256": CONTRACT_SHA256,
        "measurement_sha256": measurement_sha256,
        "challenge_secret_commitment_sha256": commitment,
        "schedule_code": schedule_code,
        "pair_records": pair_rows,
        "acceptance_conditions": conditions,
        "global_acceptance": summary["global_acceptance"],
    }
    write_json(transcript_path, transcript)
    requirements = [
        {"requirement_id": "P1", "label": "public preregistration precedes measurement", "passed": measurement["measured_at_unix"] >= utc_timestamp(PREREGISTRATION_CREATED_AT)},
        {"requirement_id": "P2", "label": "secret commitment precedes completed measurement", "passed": commitment_payload["challenge_generated_at_unix"] <= measurement["measured_at_unix"]},
        {"requirement_id": "P3", "label": "secret reveal matches commitment", "passed": reveal["commitment_matches"]},
        {"requirement_id": "P4", "label": "contract and protocol hashes remain bound", "passed": True},
        {"requirement_id": "P5", "label": "four timed records follow the secret schedule", "passed": len(records) == 4 and [row["strategy"] for row in records] == schedule},
        {"requirement_id": "P6", "label": "all timing and execution values are positive", "passed": all(row["elapsed_ns"] > 0 and row["total_execution_count"] > 0 for row in records)},
        {"requirement_id": "P7", "label": "all 48 frozen selections replay", "passed": full_matches == 24 and halving_matches == 24},
        {"requirement_id": "P8", "label": "pairing rule creates two matched full/halving pairs", "passed": len(pair_rows) == 2 and all({records[index]["strategy"] for index in row["run_indices"]} == {"full", "halving"} for row in pair_rows)},
        {"requirement_id": "P9", "label": "all four phase artifacts exist", "passed": all(path.exists() for path in [commitment_path, measurement_path, reveal_path, transcript_path])},
        {"requirement_id": "P10", "label": "claim boundary and zero credit remain explicit", "passed": conditions[-1]["passed"]},
    ]
    payload = {
        "title": "B4/B8 R145 counterbalanced runtime benchmark",
        "version": 0,
        "method": METHOD,
        "status": "counterbalanced_runtime_preregistered_acceptance" if summary["global_acceptance"] else "counterbalanced_runtime_preregistered_rejection",
        "model_status": "same_machine_secret_selected_abba_or_baab_execution_loop_timing",
        "generated_at_unix": measurement["measured_at_unix"],
        "source_target_id": "T-B4-002az/T-B8-003bd/T-B10-009ar",
        "upstream_target_id": "T-B4-002ay/T-B8-003bc/T-B10-009aq",
        "summary": summary,
        "acceptance_conditions": conditions,
        "pair_records": pair_rows,
        "strategy_records": records,
        "requirements": requirements,
        "requirement_count": 10,
        "requirements_passed": sum(row["passed"] for row in requirements),
        "requirements_failed": sum(not row["passed"] for row in requirements),
        "failed_requirement_ids": [row["requirement_id"] for row in requirements if not row["passed"]],
        "artifacts": {
            "contract": CONTRACT_PATH,
            "challenge_commitment": COMMITMENT_PATH,
            "runtime_measurement": MEASUREMENT_PATH,
            "challenge_reveal": REVEAL_PATH,
            "verifier_transcript": TRANSCRIPT_PATH,
            "result": RESULT_PATH,
            "markdown_report": REPORT_PATH,
        },
        "claim_boundary": {
            "what_is_supported": "one same-machine counterbalanced repeated-order execution-loop timing result if all gates accept",
            "what_is_not_supported": "cross-machine or cross-calibration transfer, hardware or cloud billing savings, soundness, quantum advantage, BQP separation, solved B4/B8/B10, or new credit",
        },
    }
    hash_payload = dict(payload)
    payload["payload_hash"] = hashlib.sha256(json.dumps(hash_payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    write_json(root / RESULT_PATH, payload)
    (root / REPORT_PATH).write_text(report(payload), encoding="utf-8")
    return payload


def main() -> int:
    ensure_environment()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    payload = run_gate(args.root)
    print(json.dumps({"status": payload["status"], "summary": payload["summary"], "requirements_passed": payload["requirements_passed"], "requirements_failed": payload["requirements_failed"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
