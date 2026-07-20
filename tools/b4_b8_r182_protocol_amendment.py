#!/usr/bin/env python3
"""Publish the unopened R182 workload-count label correction."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


SOURCE_PATH = "results/B4_B8_R182_score_cost_attribution_protocol_v0.json"
OUTPUT_PATH = (
    "results/B4_B8_R182_score_cost_attribution_protocol_amendment_v1.json"
)
REPORT_PATH = "research/B4_B8_R182_score_cost_attribution_protocol_amendment.md"
EXPECTED_SOURCE_HASH = (
    "c4108dd5cab9d33cfe6a69f7822892f8ae4a151d6d3c4b5f8f41c2bd297dbe03"
)


def canonical_hash(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def validate_payload(payload: dict[str, Any]) -> str:
    body = dict(payload)
    observed = body.pop("payload_hash", None)
    if observed != canonical_hash(body):
        raise ValueError("R182 v0 protocol payload hash mismatch")
    return str(observed)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def report(payload: dict[str, Any]) -> str:
    counts = payload["corrected_workload_counts"]
    return "\n".join(
        [
            "# B4/B8/B10 R182 Protocol Count-Label Amendment",
            "",
            "- Status: `public_correction_execution_unopened`",
            f"- Amendment payload hash: `{payload['payload_hash']}`",
            f"- Amended protocol hash: `{payload['amends_protocol_payload_hash']}`",
            "- Scientific execution: unopened",
            "",
            "## Correction",
            "",
            "The v0 workload arithmetic is internally consistent at the cell level but two aggregate field names incorrectly say `exact_policy`. Thirteen cells times 32 measurements equals 416 measurements per policy; across three exact policies the total is 1,248. Thirteen cells times 8 warmups equals 104 warmups per policy; across three policies the total is 312.",
            "",
            "## Authoritative Counts",
            "",
            f"- Cells per policy: `{counts['cells_per_policy']}`",
            f"- Measurements per cell: `{counts['measured_replays_per_cell']}`",
            f"- Warmups per cell: `{counts['warmups_per_cell']}`",
            f"- Measurements per policy: `{counts['measured_calls_per_policy']}`",
            f"- Warmups per policy: `{counts['warmup_calls_per_policy']}`",
            f"- Measurements across all policies: `{counts['measured_calls_all_policies']}`",
            f"- Warmups across all policies: `{counts['warmup_calls_all_policies']}`",
            "",
            "## Claim Boundary",
            "",
            "No workload cell, replay count, warmup count, hypothesis, threshold, policy, or acceptance requirement changed. This amendment corrects aggregate labels before any R182 build or measured worker starts. It is not experimental evidence or new credit.",
            "",
        ]
    )


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    for relative in (OUTPUT_PATH, REPORT_PATH):
        if (root / relative).exists():
            raise ValueError(f"R182 amendment output already exists: {relative}")
    source = json.loads((root / SOURCE_PATH).read_text(encoding="utf-8"))
    source_hash = validate_payload(source)
    if source_hash != EXPECTED_SOURCE_HASH:
        raise ValueError("R182 amendment source protocol is not the frozen v0 payload")
    cells = source["frozen_workload_cells"]
    policies = len(source["frozen_policies"])
    per_policy_measured = (
        cells["total_cells_per_exact_policy"]
        * cells["measured_replays_per_cell"]
    )
    per_policy_warmups = (
        cells["total_cells_per_exact_policy"] * cells["warmups_per_cell"]
    )
    payload: dict[str, Any] = {
        "title": "B4/B8/B10 R182 protocol count-label amendment",
        "version": 1,
        "method": "b4_b8_r182_protocol_count_label_amendment_v1",
        "status": "public_correction_execution_unopened",
        "amends_protocol_path": SOURCE_PATH,
        "amends_protocol_payload_hash": source_hash,
        "correction_reason": "13 times 32 and 13 times 8 were all-policy totals stored under misleading per-policy aggregate field names",
        "superseded_v0_field_labels": {
            "exact_policy_measured_call_count": {
                "stored_value": cells["exact_policy_measured_call_count"],
                "correct_label": "measured_calls_all_policies",
            },
            "exact_policy_warmup_call_count": {
                "stored_value": cells["exact_policy_warmup_call_count"],
                "correct_label": "warmup_calls_all_policies",
            },
        },
        "corrected_workload_counts": {
            "exact_policy_count": policies,
            "cells_per_policy": cells["total_cells_per_exact_policy"],
            "measured_replays_per_cell": cells["measured_replays_per_cell"],
            "warmups_per_cell": cells["warmups_per_cell"],
            "measured_calls_per_policy": per_policy_measured,
            "warmup_calls_per_policy": per_policy_warmups,
            "measured_calls_all_policies": per_policy_measured * policies,
            "warmup_calls_all_policies": per_policy_warmups * policies,
        },
        "unchanged_scientific_contract": {
            "workload_cells_changed": False,
            "cell_replay_counts_changed": False,
            "warmup_counts_changed": False,
            "policies_changed": False,
            "hypotheses_changed": False,
            "thresholds_changed": False,
            "acceptance_requirements_changed": False,
        },
        "execution_started": False,
        "build_started": False,
        "measured_worker_count": 0,
        "simulation_execution_count": 0,
        "total_simulated_shots": 0,
        "hardware_result_claimed": False,
        "quantum_advantage_claimed": False,
        "bqp_separation_claimed": False,
        "solved_frontier_claimed": False,
        "new_credit_delta": 0,
    }
    payload["payload_hash"] = canonical_hash(payload)
    write_json(root / OUTPUT_PATH, payload)
    (root / REPORT_PATH).write_text(report(payload), encoding="utf-8")
    print(
        json.dumps(
            {
                "status": payload["status"],
                "payload_hash": payload["payload_hash"],
                **payload["corrected_workload_counts"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
