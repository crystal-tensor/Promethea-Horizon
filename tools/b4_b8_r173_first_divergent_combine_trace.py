#!/usr/bin/env python3
"""Run the preregistered R173 source-level rounding-divergence trace."""

from __future__ import annotations

import argparse
import json
import math
import os
import platform
import struct
import sys
import time
from fractions import Fraction
from pathlib import Path
from typing import Any

from b4_b8_r119_private_observable_bundle_gate import write_json
from b4_b8_r126_calibration_attribution_ledger import file_sha256
from b4_b8_r128_transpiler_loop_layout_ranking import package_version
from b4_b8_r153_independent_seed_replication_holdout import TARGET_CLASSES
from b4_b8_r154_deterministic_automatic_replay import canonical_hash, target_descriptor
from b4_b8_r165_candidate_selection_replay import (
    bits_to_float,
    candidate_replay,
    mapping_vector,
    new_config,
    normalize_error_trace,
    normalize_events,
)


METHOD = "b4_b8_r173_first_divergent_combine_trace_v0"
PROTOCOL_PATH = "results/B4_B8_R173_first_divergent_combine_protocol_v0.json"
CONTRACT_PATH = "benchmarks/B4_B8_R173_first_divergent_combine_contract_v0.json"
OUT_DIR = "results/B4_B8_R173_first_divergent_combine_trace"
RESULT_PATH = "results/B4_B8_R173_first_divergent_combine_trace_v0.json"
REPORT_PATH = "research/B4_B8_R173_first_divergent_combine_trace.md"
R160_CASES_PATH = "results/B4_B8_R160_deterministic_error_map_remediation/case_analysis.json"
R173_TARGET = "T-B4-002cq/T-B8-003cu/T-B10-009cg-r173"


def float_bits(value: float) -> int:
    return struct.unpack("!Q", struct.pack("!d", value))[0]


def validate_payload(payload: dict[str, Any], label: str) -> str:
    body = dict(payload)
    observed = body.pop("payload_hash", None)
    if not observed or observed != canonical_hash(body):
        raise ValueError(f"R173 {label} payload hash mismatch")
    return str(observed)


def validate_bindings(root: Path, protocol: dict[str, Any], contract: dict[str, Any]) -> None:
    protocol_hash = validate_payload(protocol, "protocol")
    validate_payload(contract, "contract")
    if protocol.get("method") != "b4_b8_r173_first_divergent_combine_protocol_v0":
        raise ValueError("R173 protocol identity mismatch")
    if contract.get("contract_id") != "B4-B8-R173-first-divergent-combine-contract-v0":
        raise ValueError("R173 contract identity mismatch")
    if contract.get("execution_started") is not False:
        raise ValueError("R173 contract is not unopened")
    if contract.get("protocol_payload_hash") != protocol_hash:
        raise ValueError("R173 protocol binding mismatch")
    for binding_id, binding in contract["source_bindings"].items():
        path = root / binding["path"]
        if not path.exists() or file_sha256(path) != binding["sha256"]:
            raise ValueError(f"R173 source binding mismatch: {binding_id}")
        if "payload_hash" in binding:
            payload = json.loads(path.read_text(encoding="utf-8"))
            if payload.get("payload_hash") != binding["payload_hash"]:
                raise ValueError(f"R173 source payload mismatch: {binding_id}")


def parse_leaf_rows(encoded: str) -> list[tuple[str, int]]:
    rows: list[tuple[str, int]] = []
    for item in encoded.split(";"):
        if not item or "=" not in item:
            continue
        label, raw_bits = item.rsplit("=", 1)
        rows.append((label, int(raw_bits)))
    return rows


def exact_sum_from_bits(bits: list[int]) -> Fraction:
    return sum((Fraction.from_float(bits_to_float(value)) for value in bits), Fraction(0, 1))


def analyze_candidate_chain(
    events: list[dict[str, Any]], candidate: dict[str, Any]
) -> dict[str, Any]:
    target_bits = [int(value) for value in candidate["source_leaf_bits"]]
    final_matches = []
    for event_index, event in enumerate(events):
        if event["kind"] != "combine":
            continue
        leaves = parse_leaf_rows(event["result_terms"])
        if (
            [bits for _, bits in leaves] == target_bits
            and int(event["result_bits"]) == int(candidate["source_score_bits"])
        ):
            final_matches.append((event_index, leaves))
    if len(final_matches) != 1:
        raise ValueError(
            f"R173 expected one final combine for candidate {candidate['candidate_index']}, "
            f"found {len(final_matches)}"
        )
    final_event_index, full_leaves = final_matches[0]
    chain = []
    for event_index, event in enumerate(events):
        if event["kind"] != "combine":
            continue
        leaves = parse_leaf_rows(event["result_terms"])
        if not leaves or leaves != full_leaves[: len(leaves)]:
            continue
        exact = exact_sum_from_bits([bits for _, bits in leaves])
        correctly_rounded_bits = float_bits(float(exact))
        native_addition_bits = float_bits(
            bits_to_float(int(event["left_bits"]))
            + bits_to_float(int(event["right_bits"]))
        )
        chain.append(
            {
                "event_index": event_index,
                "leaf_count": len(leaves),
                "left_bits": int(event["left_bits"]),
                "right_bits": int(event["right_bits"]),
                "result_bits": int(event["result_bits"]),
                "correctly_rounded_exact_bits": correctly_rounded_bits,
                "signed_ulp_delta_from_correctly_rounded_exact": int(event["result_bits"])
                - correctly_rounded_bits,
                "native_addition_verified": native_addition_bits == int(event["result_bits"]),
                "left_terms": event["left_terms"],
                "right_terms": event["right_terms"],
                "leaf_rows": [
                    {"label": label, "bits": bits} for label, bits in leaves
                ],
            }
        )
    first = next(
        (
            row
            for row in chain
            if row["signed_ulp_delta_from_correctly_rounded_exact"] != 0
        ),
        None,
    )
    final = next(
        (
            row
            for row in chain
            if row["event_index"] == final_event_index
            and row["leaf_count"] == len(full_leaves)
        ),
        None,
    )
    if final is None:
        raise ValueError("R173 final combine is absent from the candidate chain")
    return {
        "candidate_index": int(candidate["candidate_index"]),
        "mapping_vector": [int(value) for value in candidate["mapping_vector"]],
        "source_score_bits": int(candidate["source_score_bits"]),
        "exact_score_numerator": str(candidate["exact_score_numerator"]),
        "exact_score_denominator": str(candidate["exact_score_denominator"]),
        "leaf_count": int(candidate["leaf_count"]),
        "chain_event_count": len(chain),
        "first_divergence": first,
        "final_combine": final,
        "all_chain_native_additions_verified": all(
            row["native_addition_verified"] for row in chain
        ),
        "chain": chain,
    }


def analyze_trace(
    events: list[dict[str, Any]], replay: dict[str, Any], input_id: str, profile_id: str
) -> dict[str, Any]:
    source_index = int(replay["selected_candidate_index"]["source_f64"])
    exact_index = int(replay["selected_candidate_index"]["exact_binary64_leaf"])
    if source_index == exact_index:
        raise ValueError(f"R173 {input_id}/{profile_id} has no source/exact split")
    candidates = replay["candidates"]
    exact_candidate = candidates[exact_index]
    source_candidate = candidates[source_index]
    exact_total = Fraction(
        int(exact_candidate["exact_score_numerator"]),
        int(exact_candidate["exact_score_denominator"]),
    )
    source_total = Fraction(
        int(source_candidate["exact_score_numerator"]),
        int(source_candidate["exact_score_denominator"]),
    )
    branches = [
        analyze_candidate_chain(events, exact_candidate),
        analyze_candidate_chain(events, source_candidate),
    ]
    all_combine_native = all(
        float_bits(
            bits_to_float(int(event["left_bits"]))
            + bits_to_float(int(event["right_bits"]))
        )
        == int(event["result_bits"])
        for event in events
        if event["kind"] == "combine"
    )
    return {
        "input_id": input_id,
        "profile_id": profile_id,
        "source_selected_candidate_index": source_index,
        "exact_selected_candidate_index": exact_index,
        "source_selected_mapping": replay["selected_mapping_vector"]["source_f64"],
        "exact_selected_mapping": replay["selected_mapping_vector"][
            "exact_binary64_leaf"
        ],
        "source_score_bit_gap": abs(
            int(source_candidate["source_score_bits"])
            - int(exact_candidate["source_score_bits"])
        ),
        "exact_totals_equal": exact_total == source_total,
        "exact_policy_preserves_first_seen_tie": exact_total == source_total
        and exact_index < source_index,
        "all_combine_native_additions_verified": all_combine_native,
        "branches": branches,
    }


def r160_guardrail(root: Path) -> dict[str, Any]:
    payload = json.loads((root / R160_CASES_PATH).read_text(encoding="utf-8"))
    tie_rows = []
    for row in payload["tie_baseline"]["mode_rows"]:
        oracle = row["oracle"]
        tie_rows.append(
            {
                "mode": row["mode"],
                "minimizer_count": int(oracle["minimizer_count"]),
                "classified_as_exact_tie": int(oracle["minimizer_count"]) > 1,
                "first_seen_selection_stable": bool(row["stable"]),
            }
        )
    non_tie_rows = []
    for case in payload["case_rows"]:
        if case["all_replays_within_oracle"]:
            continue
        for row in case["mode_rows"]:
            oracle = row["oracle"]
            minimum = Fraction(oracle["minimum_score_fraction"])
            second = Fraction(oracle["second_distinct_score_fraction"])
            non_tie_rows.append(
                {
                    "case_id": case["case_id"],
                    "mode": row["mode"],
                    "minimizer_count": int(oracle["minimizer_count"]),
                    "exact_gap_numerator": str((second - minimum).numerator),
                    "exact_gap_denominator": str((second - minimum).denominator),
                    "classified_as_non_tie": minimum < second
                    and int(oracle["minimizer_count"]) == 1,
                    "oracle_minimizer_vectors": oracle["minimizer_vectors"],
                }
            )
    return {
        "source_path": R160_CASES_PATH,
        "source_sha256": file_sha256(root / R160_CASES_PATH),
        "tie_control_count": len(tie_rows),
        "tie_controls_passed": sum(
            row["classified_as_exact_tie"] and row["first_seen_selection_stable"]
            for row in tie_rows
        ),
        "non_tie_control_count": len(non_tie_rows),
        "non_tie_controls_passed": sum(
            row["classified_as_non_tie"] for row in non_tie_rows
        ),
        "tie_controls": tie_rows,
        "non_tie_controls": non_tie_rows,
    }


def environment() -> dict[str, Any]:
    return {
        "python": platform.python_version(),
        "qiskit": package_version("qiskit"),
        "qiskit_aer": package_version("qiskit-aer"),
        "qiskit_ibm_runtime": package_version("qiskit-ibm-runtime"),
        "pythonpath_head": sys.path[0],
    }


def execute(root: Path, protocol: dict[str, Any], preregistration: dict[str, str]) -> dict[str, Any]:
    import qiskit
    from qiskit import qasm3
    from qiskit._accelerate.vf2_layout import vf2_layout_pass_average_score_traced
    from qiskit.converters import circuit_to_dag

    binary_candidates = sorted(Path(qiskit.__file__).resolve().parent.glob("_accelerate*.so"))
    if len(binary_candidates) != 1:
        raise ValueError(f"R173 expected one accelerator binary, found {len(binary_candidates)}")
    if file_sha256(binary_candidates[0]) != protocol["instrumented_binary_sha256"]:
        raise ValueError("R173 imported accelerator hash mismatch")
    out_dir = root / OUT_DIR
    if out_dir.exists():
        raise ValueError("R173 trace directory already exists")
    out_dir.mkdir(parents=True)
    backend = TARGET_CLASSES[protocol["snapshot_name"]]()
    target_desc = target_descriptor(backend)
    trace_artifacts = []
    for input_spec in protocol["inputs"]:
        circuit = qasm3.load(root / input_spec["path"])
        dag = circuit_to_dag(circuit)
        for profile in protocol["profiles"]:
            started = time.perf_counter()
            output, raw_events, raw_error_trace = vf2_layout_pass_average_score_traced(
                dag,
                backend.target,
                new_config(),
                strict_direction=False,
                operation_order=profile["operation_order"],
            )
            events = normalize_events(raw_events)
            error_trace = normalize_error_trace(raw_error_trace)
            replay = candidate_replay(events, circuit.num_qubits)
            output_mapping = mapping_vector(output.new_mapping(), circuit.num_qubits)
            analysis = analyze_trace(
                events, replay, input_spec["input_id"], profile["profile_id"]
            )
            artifact = {
                "input_id": input_spec["input_id"],
                "profile_id": profile["profile_id"],
                "operation_order": profile["operation_order"],
                "preregistration": preregistration,
                "protocol_payload_hash": protocol["payload_hash"],
                "input_sha256": file_sha256(root / input_spec["path"]),
                "target_descriptor_sha256": target_desc["descriptor_hash"],
                "output_mapping": output_mapping,
                "source_return_match": bool(replay["source_return_match"]),
                "candidate_replay": replay,
                "analysis": analysis,
                "score_events": events,
                "score_events_hash": canonical_hash(events),
                "error_trace": error_trace,
                "error_trace_hash": canonical_hash(error_trace),
                "elapsed_seconds": time.perf_counter() - started,
                "simulation_execution_count": 0,
                "total_simulated_shots": 0,
            }
            artifact["trace_payload_hash"] = canonical_hash(artifact)
            path = out_dir / f"{input_spec['input_id']}_{profile['profile_id']}.json"
            write_json(path, artifact)
            trace_artifacts.append(
                {
                    "input_id": input_spec["input_id"],
                    "profile_id": profile["profile_id"],
                    "path": str(path.relative_to(root)),
                    "sha256": file_sha256(path),
                    "trace_payload_hash": artifact["trace_payload_hash"],
                    "analysis": analysis,
                }
            )
    controls = r160_guardrail(root)
    analyses = [row["analysis"] for row in trace_artifacts]
    branches = [branch for row in analyses for branch in row["branches"]]
    requirements = [
        ("P1", len(trace_artifacts) == 6),
        ("P2", all(row["source_return_match"] for row in [json.loads((root / item["path"]).read_text()) for item in trace_artifacts])),
        ("P3", all(row["all_combine_native_additions_verified"] for row in analyses)),
        ("P4", all(row["exact_totals_equal"] for row in analyses)),
        ("P5", all(row["source_score_bit_gap"] == 1 for row in analyses)),
        ("P6", all(branch["first_divergence"] is not None for branch in branches)),
        ("P7", all(branch["all_chain_native_additions_verified"] for branch in branches)),
        ("P8", all(row["exact_policy_preserves_first_seen_tie"] for row in analyses)),
        ("P9", controls["tie_controls_passed"] == controls["tie_control_count"] == 4 and controls["non_tie_controls_passed"] == controls["non_tie_control_count"] == 28),
        ("P10", preregistration["discussion"].startswith("https://github.com/crystal-tensor/Prometheus-plan/discussions/")),
    ]
    result = {
        "title": "B4/B8/B10 R173 first divergent combine trace",
        "version": 0,
        "method": METHOD,
        "status": "first_divergent_combine_localized" if all(passed for _, passed in requirements) else "first_divergent_combine_incomplete",
        "classification": "two_graph_rounding_path_localized_with_exact_guardrail" if all(passed for _, passed in requirements) else "incomplete",
        "source_target_id": R173_TARGET,
        "upstream_target_id": "T-B4-002cp/T-B8-003ct/T-B10-009cf-r172",
        "preregistration": preregistration,
        "environment": environment(),
        "summary": {
            "input_count": len(protocol["inputs"]),
            "profile_count": len(protocol["profiles"]),
            "trace_count": len(trace_artifacts),
            "candidate_branch_count": len(branches),
            "localized_branch_count": sum(branch["first_divergence"] is not None for branch in branches),
            "native_addition_verified_trace_count": sum(row["all_combine_native_additions_verified"] for row in analyses),
            "exact_tie_trace_count": sum(row["exact_totals_equal"] for row in analyses),
            "one_ulp_source_split_count": sum(row["source_score_bit_gap"] == 1 for row in analyses),
            "exact_first_seen_policy_pass_count": sum(row["exact_policy_preserves_first_seen_tie"] for row in analyses),
            "r160_tie_controls_passed": controls["tie_controls_passed"],
            "r160_tie_control_count": controls["tie_control_count"],
            "r160_non_tie_controls_passed": controls["non_tie_controls_passed"],
            "r160_non_tie_control_count": controls["non_tie_control_count"],
            "qiskit_calls_performed": len(trace_artifacts),
            "simulation_execution_count": 0,
            "total_simulated_shots": 0,
            "source_patch_performed": False,
            "production_policy_changed": False,
            "confirmed_qiskit_bug_claimed": False,
            "quantum_advantage_claimed": False,
            "bqp_separation_claimed": False,
            "solved_frontier_claimed": False,
            "new_credit_delta": 0,
        },
        "trace_artifacts": trace_artifacts,
        "r160_policy_guardrail": controls,
        "requirements": [
            {"requirement_id": requirement_id, "passed": passed}
            for requirement_id, passed in requirements
        ],
        "requirements_passed": sum(passed for _, passed in requirements),
        "requirements_failed": sum(not passed for _, passed in requirements),
        "artifacts": {
            "protocol": PROTOCOL_PATH,
            "contract": CONTRACT_PATH,
            "trace_directory": OUT_DIR,
            "result": RESULT_PATH,
            "markdown_report": REPORT_PATH,
        },
        "claim_boundary": {
            "what_is_supported": "source-level localization of the first correctly-rounded-exact-prefix divergence on the R170 and R172 tied candidate branches, plus an exact-score tie/non-tie comparison guardrail",
            "what_is_not_supported": "undefined floating-point behavior, a confirmed Qiskit bug, a merged source patch, production performance, route improvement, hardware relevance, quantum advantage, BQP separation, solved B4/B8/B10, or new credit",
        },
    }
    result["payload_hash"] = canonical_hash(result)
    write_json(root / RESULT_PATH, result)
    (root / REPORT_PATH).write_text(build_report(result), encoding="utf-8")
    return result


def build_report(result: dict[str, Any]) -> str:
    summary = result["summary"]
    rows = []
    for trace in result["trace_artifacts"]:
        analysis = trace["analysis"]
        first = [
            f"c{branch['candidate_index']}@leaf{branch['first_divergence']['leaf_count']}"
            for branch in analysis["branches"]
        ]
        final = [
            str(branch["final_combine"]["signed_ulp_delta_from_correctly_rounded_exact"])
            for branch in analysis["branches"]
        ]
        rows.append(
            f"| {trace['input_id']} | {trace['profile_id']} | {' / '.join(first)} | {' / '.join(final)} | {analysis['source_score_bit_gap']} |"
        )
    return "\n".join(
        [
            "# B4/B8/B10 R173 First Divergent Combine Trace",
            "",
            f"- Status: `{result['status']}`",
            f"- Classification: `{result['classification']}`",
            f"- Requirements: `{result['requirements_passed']}/10`",
            f"- Payload hash: `{result['payload_hash']}`",
            "",
            "## Research Question",
            "",
            "Where does source-order binary64 first separate two candidates whose retained leaf sums are exactly equal?",
            "",
            "## Result",
            "",
            f"R173 localizes the first divergence on `{summary['localized_branch_count']}/{summary['candidate_branch_count']}` selected branches across `{summary['trace_count']}` source traces. Every traced combine reproduces native binary64 `left + right`; the observed split is therefore an accumulation-order effect under the declared instrumented path, not evidence of undefined addition behavior.",
            "",
            "| Input | Profile | First divergent prefix | Final signed ULP debt | Source gap |",
            "|---|---|---:|---:|---:|",
            *rows,
            "",
            "## Policy Guardrail",
            "",
            f"The exact retained-leaf, first-seen policy passes `{summary['exact_first_seen_policy_pass_count']}/{summary['trace_count']}` R170/R172 exact-tie traces. The immutable R160 score control classifies `{summary['r160_tie_controls_passed']}/{summary['r160_tie_control_count']}` tie rows as ties and `{summary['r160_non_tie_controls_passed']}/{summary['r160_non_tie_control_count']}` non-tie rows as strict inequalities.",
            "",
            "## Claim Boundary",
            "",
            result["claim_boundary"]["what_is_not_supported"].capitalize() + ".",
            "",
        ]
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--preregistration-commit", required=True)
    parser.add_argument("--preregistration-discussion", required=True)
    parser.add_argument("--preregistration-created-at", required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    protocol = json.loads((root / PROTOCOL_PATH).read_text(encoding="utf-8"))
    contract = json.loads((root / CONTRACT_PATH).read_text(encoding="utf-8"))
    validate_bindings(root, protocol, contract)
    result = execute(
        root,
        protocol,
        {
            "commit": args.preregistration_commit,
            "discussion": args.preregistration_discussion,
            "created_at": args.preregistration_created_at,
        },
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["requirements_failed"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
