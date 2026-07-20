#!/usr/bin/env python3
"""Freeze the R173 first-divergent-combine protocol before formal execution."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from b4_b8_r119_private_observable_bundle_gate import write_json
from b4_b8_r126_calibration_attribution_ledger import file_sha256
from b4_b8_r154_deterministic_automatic_replay import canonical_hash


METHOD = "b4_b8_r173_first_divergent_combine_protocol_v0"
PROTOCOL_PATH = "results/B4_B8_R173_first_divergent_combine_protocol_v0.json"
CONTRACT_PATH = "benchmarks/B4_B8_R173_first_divergent_combine_contract_v0.json"
REPORT_PATH = "research/B4_B8_R173_first_divergent_combine_protocol.md"
EXECUTOR_PATH = "tools/b4_b8_r173_first_divergent_combine_trace.py"
ORACLE_PATH = "tools/b4_b8_r173_independent_divergence_oracle.py"
BINARY_PATH = "research/source_lineage/Qiskit_2_4_1_R165_candidate_selection_accelerate.cpython-312-darwin.so"
PATCH_PATH = "research/source_lineage/Qiskit_2_4_1_R165_candidate_selection.patch"
BUILD_MANIFEST_PATH = "research/source_lineage/Qiskit_2_4_1_R165_candidate_selection_build_manifest.json"
R160_CASES_PATH = "results/B4_B8_R160_deterministic_error_map_remediation/case_analysis.json"


INPUTS = [
    {
        "input_id": "r170_path",
        "path": "benchmarks/B4_B8_R170_near_tie_candidate_v0.qasm",
        "upstream_result": "results/B4_B8_R170_near_tie_candidate_replay_v0.json",
        "degree_sequence": [2, 2, 2, 1, 1],
    },
    {
        "input_id": "r172_t_tree",
        "path": "benchmarks/B4_B8_R172_second_near_tie_candidate_v0.qasm",
        "upstream_result": "results/B4_B8_R172_second_near_tie_candidate_replay_v0.json",
        "degree_sequence": [3, 2, 1, 1, 1],
    },
]


def payload_binding(root: Path, path: str) -> dict[str, str]:
    payload = json.loads((root / path).read_text(encoding="utf-8"))
    return {
        "path": path,
        "sha256": file_sha256(root / path),
        "payload_hash": str(payload["payload_hash"]),
    }


def file_binding(root: Path, path: str) -> dict[str, str]:
    return {"path": path, "sha256": file_sha256(root / path)}


def build_report(protocol: dict[str, Any], contract: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# B4/B8/B10 R173 First Divergent Combine Protocol",
            "",
            f"- Status: `{protocol['status']}`",
            f"- Protocol payload hash: `{protocol['payload_hash']}`",
            f"- Contract payload hash: `{contract['payload_hash']}`",
            f"- Planned source traces: `{len(protocol['inputs']) * len(protocol['profiles'])}`",
            "",
            "## Research Question",
            "",
            protocol["research_question"],
            "",
            "## Frozen Analysis",
            "",
            "For the source-selected and exact-retained-leaf-selected candidates, R173 reconstructs the source combine chain from the complete event trace. At each prefix it compares the recorded binary64 result with the correctly rounded exact sum of the retained binary64 leaves. The first unequal bit pattern is the declared first divergent combine.",
            "",
            "Every recorded combine must also equal native binary64 `left + right`. This separates ordinary accumulation-order sensitivity from malformed arithmetic evidence.",
            "",
            "## Policy Guardrail",
            "",
            "The candidate policy compares exact retained-leaf fractions and preserves first-seen order only on exact equality. It must pass all six R170/R172 exact-tie traces, all four R160 tie-baseline mode rows, and all 28 R160 unique-minimum non-tie rows.",
            "",
            "## Claim Boundary",
            "",
            "Execution is unopened. The protocol does not claim a Qiskit bug, source patch, production remedy, route improvement, hardware result, quantum advantage, BQP separation, solved frontier, or new credit.",
            "",
        ]
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    root = args.root.resolve()
    for path in [PROTOCOL_PATH, CONTRACT_PATH, REPORT_PATH]:
        if (root / path).exists():
            raise ValueError(f"R173 preregistration artifact already exists: {path}")
    instrumented_binary_hash = file_sha256(root / BINARY_PATH)
    protocol_inputs = []
    for item in INPUTS:
        upstream = json.loads((root / item["upstream_result"]).read_text(encoding="utf-8"))
        protocol_inputs.append(
            {
                **item,
                "sha256": file_sha256(root / item["path"]),
                "upstream_result_sha256": file_sha256(root / item["upstream_result"]),
                "upstream_result_payload_hash": upstream["payload_hash"],
            }
        )
    protocol: dict[str, Any] = {
        "title": "B4/B8/B10 R173 first divergent combine protocol",
        "version": 0,
        "method": METHOD,
        "status": "preregistered_execution_unopened",
        "source_target_id": "T-B4-002cq/T-B8-003cu/T-B10-009cg-r173",
        "upstream_target_id": "T-B4-002cp/T-B8-003ct/T-B10-009cf-r172",
        "research_question": "At which source-level binary64 combine does each R170/R172 exact-tie candidate branch first diverge from the correctly rounded exact prefix, and can an exact-total policy preserve both true ties and declared non-ties?",
        "snapshot_name": "FakeNairobiV2",
        "qiskit_version": "2.4.1",
        "instrumented_binary_path": BINARY_PATH,
        "instrumented_binary_sha256": instrumented_binary_hash,
        "inputs": protocol_inputs,
        "profiles": [
            {"profile_id": "native_hashset_order", "operation_order": "native", "replay_count": 1},
            {"profile_id": "ascending_sorted_order", "operation_order": "ascending", "replay_count": 1},
            {"profile_id": "descending_sorted_order", "operation_order": "descending", "replay_count": 1},
        ],
        "formal_qiskit_call_count": 6,
        "first_divergence_rule": {
            "candidate_pair": "source_f64 winner and exact_binary64_leaf first-seen winner",
            "chain_binding": "unique final combine whose retained leaf-bit vector and result bits match the candidate",
            "prefix_order": "source event order restricted to exact labeled prefixes of the final candidate leaf vector",
            "reference": "correctly rounded exact Fraction sum of retained binary64 leaves",
            "first_divergence": "first chain event whose result bits differ from the reference bits",
            "native_addition_check": "every combine result bits must equal binary64(left + right)",
        },
        "policy_under_test": {
            "policy_id": "exact_retained_leaf_first_seen_v0",
            "strict_order": "candidate exact Fraction total is lower than incumbent exact Fraction total",
            "tie_rule": "retain first-seen incumbent only when exact Fraction totals are equal",
            "r170_r172_requirement": "6/6 exact-tie traces retain the first-seen exact winner",
            "r160_tie_requirement": "4/4 tie-baseline mode rows remain ties and stable",
            "r160_non_tie_requirement": "28/28 unique-minimum mode rows remain strict non-ties",
        },
        "accepted_outcomes": [
            "localization_complete_policy_guardrail_pass",
            "localization_complete_policy_guardrail_fail",
            "localization_incomplete",
            "source_trace_binding_failure",
        ],
        "claim_boundary": {
            "what_is_supported_if_passed": "source-level combine localization on two nonisomorphic exact-tie inputs plus an exact score-level tie/non-tie guardrail",
            "what_is_not_supported": "undefined arithmetic, a confirmed Qiskit bug, source patch, production remedy, route improvement, hardware relevance, quantum advantage, BQP separation, solved B4/B8/B10, or new credit",
        },
        "simulation_execution_count": 0,
        "total_simulated_shots": 0,
        "execution_started": False,
    }
    protocol["payload_hash"] = canonical_hash(protocol)
    write_json(root / PROTOCOL_PATH, protocol)
    source_bindings = {
        "protocol": payload_binding(root, PROTOCOL_PATH),
        "executor": file_binding(root, EXECUTOR_PATH),
        "independent_oracle": file_binding(root, ORACLE_PATH),
        "instrumented_binary": file_binding(root, BINARY_PATH),
        "instrumentation_patch": file_binding(root, PATCH_PATH),
        "build_manifest": payload_binding(root, BUILD_MANIFEST_PATH),
        "r160_case_analysis": file_binding(root, R160_CASES_PATH),
    }
    for item in protocol_inputs:
        source_bindings[f"{item['input_id']}_qasm"] = file_binding(root, item["path"])
        source_bindings[f"{item['input_id']}_result"] = payload_binding(root, item["upstream_result"])
    contract: dict[str, Any] = {
        "contract_id": "B4-B8-R173-first-divergent-combine-contract-v0",
        "version": 0,
        "status": "preregistered_execution_unopened",
        "protocol_payload_hash": protocol["payload_hash"],
        "source_bindings": source_bindings,
        "required_outputs": [
            "results/B4_B8_R173_first_divergent_combine_trace/*.json",
            "results/B4_B8_R173_first_divergent_combine_trace_v0.json",
            "research/B4_B8_R173_first_divergent_combine_trace.md",
            "results/B4_B8_R173_independent_divergence_oracle_v0.json",
            "research/B4_B8_R173_independent_divergence_oracle.md",
        ],
        "execution_started": False,
        "claim_boundary": protocol["claim_boundary"],
    }
    contract["payload_hash"] = canonical_hash(contract)
    write_json(root / CONTRACT_PATH, contract)
    (root / REPORT_PATH).write_text(build_report(protocol, contract), encoding="utf-8")
    print(
        json.dumps(
            {
                "protocol_path": PROTOCOL_PATH,
                "protocol_payload_hash": protocol["payload_hash"],
                "contract_path": CONTRACT_PATH,
                "contract_payload_hash": contract["payload_hash"],
                "execution_started": False,
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
