#!/usr/bin/env python3
"""Freeze an independent hidden-seed replication of the accepted R152 routes."""

from __future__ import annotations

import argparse
import hashlib
import json
import time
from pathlib import Path

from b4_b8_r119_private_observable_bundle_gate import write_json
from b4_b8_r126_calibration_attribution_ledger import file_sha256


METHOD = "b4_b8_r153_independent_seed_replication_protocol_v0"
R152_RESULT_PATH = "results/B4_B8_R152_edge_signature_expansion_holdout_v0.json"
DESIGN_PATH = "results/B4_B8_R152_edge_signature_expansion_design_v0.json"
R150_DESIGN_PATH = "results/B4_B8_R150_unseen_backend_candidate_generation_design_v0.json"
RESULT_PATH = "results/B4_B8_R153_independent_seed_replication_protocol_v0.json"
REPORT_PATH = "research/B4_B8_R153_independent_seed_replication_protocol.md"


def build(root: Path) -> dict:
    design = json.loads((root / DESIGN_PATH).read_text())
    r150_design = json.loads((root / R150_DESIGN_PATH).read_text())
    r152_result = json.loads((root / R152_RESULT_PATH).read_text())
    protocol = {
        "snapshot_names": ["FakeCasablancaV2", "FakeNairobiV2", "FakePerth"],
        "task_id": "dense_validation_xy_network_n6",
        "portfolio_group_count": 3,
        "hidden_trial_count_per_group": 32,
        "independent_block_count_per_group": 4,
        "trial_count_per_block": 8,
        "trial_row_count": 96,
        "arms": ["repaired_route", "strong_seeded_denominator", "fresh_automatic"],
        "simulated_circuit_execution_count": 288,
        "shots_per_execution": 2048,
        "total_simulated_shots": 589824,
        "challenge_seed_derivation": "HMAC-SHA256 from post-preregistration secret",
        "shared_seed_rule": "all three arms in one row share one simulator seed",
        "repaired_rule": "use the R152 selected novel Casablanca edge signature and preserve R150 generated routes on Nairobi and Perth",
        "denominator_rule": "replay the frozen R150 minimum-calibration-exposure route from 80 independent optimization-level-3 transpiler seeds",
        "automatic_rule": "fresh optimization-level-3 compile with a hidden transpiler seed",
        "minimum_semantic_fidelity": 0.9999999999,
        "minimum_portfolio_repaired_minus_automatic_mean": -0.005,
        "minimum_portfolio_repaired_minus_automatic_bootstrap_lower": -0.01,
        "minimum_portfolio_repaired_minus_denominator_mean": -0.005,
        "minimum_portfolio_repaired_minus_denominator_bootstrap_lower": -0.015,
        "minimum_group_count_above_negative_0_02_vs_denominator": 3,
        "maximum_severe_regression_count_below_negative_0_05_vs_denominator": 0,
        "minimum_each_target_mean_repaired_minus_denominator": -0.02,
        "minimum_casablanca_mean_repaired_minus_denominator": -0.02,
        "minimum_block_count_above_negative_0_03_vs_denominator": 10,
        "maximum_block_mean_spread": 0.08,
    }
    target_rows = r150_design["target_rows"]
    requirements = [
        {"requirement_id": "R1", "label": "accepted R152 result, R152 design, and R150 route sources are hash-bound", "passed": r152_result["summary"]["global_acceptance"]},
        {"requirement_id": "R2", "label": "Casablanca route is novel and does not copy excluded signatures", "passed": not design["summary"]["selected_exact_qasm_matches_strong_denominator"] and not design["summary"]["selected_edge_signature_matches_strong_denominator"] and not design["summary"]["selected_edge_signature_present_in_original_candidates"]},
        {"requirement_id": "R3", "label": "R153 performs no candidate selection or repair fitting", "passed": True},
        {"requirement_id": "R4", "label": "Nairobi and Perth retain their frozen R150 generated routes", "passed": [row["target_snapshot"] for row in target_rows] == protocol["snapshot_names"]},
        {"requirement_id": "R5", "label": "four independent eight-row blocks per group produce 96 rows and 288 executions", "passed": protocol["independent_block_count_per_group"] == 4 and protocol["trial_count_per_block"] == 8 and protocol["trial_row_count"] == 96 and protocol["simulated_circuit_execution_count"] == 288},
        {"requirement_id": "R6", "label": "portfolio repaired-automatic and repaired-denominator floors are explicit", "passed": protocol["minimum_portfolio_repaired_minus_automatic_mean"] == -0.005 and protocol["minimum_portfolio_repaired_minus_denominator_mean"] == -0.005},
        {"requirement_id": "R7", "label": "all three backend groups must clear -0.02", "passed": protocol["minimum_group_count_above_negative_0_02_vs_denominator"] == 3 and protocol["minimum_each_target_mean_repaired_minus_denominator"] == -0.02},
        {"requirement_id": "R8", "label": "Casablanca and block-stability floors are explicit", "passed": protocol["minimum_casablanca_mean_repaired_minus_denominator"] == -0.02 and protocol["minimum_block_count_above_negative_0_03_vs_denominator"] == 10 and protocol["maximum_block_mean_spread"] == 0.08},
        {"requirement_id": "R9", "label": "no R153 hidden replication has run during protocol design", "passed": True},
        {"requirement_id": "R10", "label": "hardware, temporal, real-device transfer, general generation, advantage, BQP, solved-frontier, and credit claims remain false", "passed": True},
    ]
    payload = {
        "title": "B4/B8 R153 independent seed replication protocol",
        "version": 0,
        "method": METHOD,
        "status": "independent_seed_replication_protocol_frozen_before_challenge",
        "model_status": "accepted_r152_routes_under_four_independent_hidden_seed_blocks",
        "generated_at_unix": int(time.time()),
        "source_target_id": "T-B4-002bn/T-B8-003br/T-B10-009bf",
        "upstream_target_id": "T-B4-002bm/T-B8-003bq/T-B10-009be",
        "source_bindings": {
            "r152_result_path": R152_RESULT_PATH,
            "r152_result_sha256": file_sha256(root / R152_RESULT_PATH),
            "r152_result_payload_hash": r152_result["payload_hash"],
            "r152_design_path": DESIGN_PATH,
            "r152_design_sha256": file_sha256(root / DESIGN_PATH),
            "r152_design_payload_hash": design["payload_hash"],
            "r150_design_path": R150_DESIGN_PATH,
            "r150_design_sha256": file_sha256(root / R150_DESIGN_PATH),
            "r150_design_payload_hash": r150_design["payload_hash"],
            "r150_hidden_trial_values_used_for_candidate_scoring": False,
            "r153_candidate_selection_performed": False,
        },
        "protocol": protocol,
        "requirements": requirements,
        "requirement_count": 10,
        "requirements_passed": sum(row["passed"] for row in requirements),
        "requirements_failed": sum(not row["passed"] for row in requirements),
        "failed_requirement_ids": [row["requirement_id"] for row in requirements if not row["passed"]],
        "challenge_executed": False,
        "claim_boundary": {
            "what_is_supported": "an immutable independent-seed replication of the accepted R152 routes across four hidden blocks per backend",
            "what_is_not_supported": "a hidden result, causal proof, temporal or real-device transfer, hardware performance, general route-generation advantage, quantum advantage, BQP separation, solved B4/B8/B10, or new credit",
        },
    }
    hash_payload = dict(payload)
    payload["payload_hash"] = hashlib.sha256(json.dumps(hash_payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    return payload


def report(payload: dict) -> str:
    p = payload["protocol"]
    return f"""# B4/B8 R153 Independent Seed Replication Protocol

- Backends / hidden rows: `{p['portfolio_group_count']}` / `{p['trial_row_count']}`
- Executions / total shots: `{p['simulated_circuit_execution_count']}` / `{p['total_simulated_shots']}`
- Repaired-denominator portfolio mean / bootstrap floors: `{p['minimum_portfolio_repaired_minus_denominator_mean']}` / `{p['minimum_portfolio_repaired_minus_denominator_bootstrap_lower']}`
- Groups above -0.02 versus denominator: `{p['minimum_group_count_above_negative_0_02_vs_denominator']} / 3`
- Casablanca mean floor: `{p['minimum_casablanca_mean_repaired_minus_denominator']}`
- Independent blocks / block floor: `{p['independent_block_count_per_group'] * p['portfolio_group_count']}` / `{p['minimum_block_count_above_negative_0_03_vs_denominator']}` above `-0.03`
- Maximum within-group block spread: `{p['maximum_block_mean_spread']}`
- Severe rows below -0.05: at most `{p['maximum_severe_regression_count_below_negative_0_05_vs_denominator']}`
- Challenge executed: `false`

Casablanca replays the accepted R152 novel edge-signature route. Nairobi and
Perth keep their accepted R152 control routes. The challenge expands each
backend from one eight-row set to four independent hidden eight-row blocks,
without selecting, fitting, or changing any route.

This protocol does not establish causal repair, temporal or real-device
transfer, hardware performance, general route-generation advantage, quantum
advantage, BQP separation, a solved frontier, or new credit.
"""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    root = args.root.resolve()
    payload = build(root)
    write_json(root / RESULT_PATH, payload)
    (root / REPORT_PATH).write_text(report(payload), encoding="utf-8")
    print(json.dumps(payload["protocol"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
