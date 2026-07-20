#!/usr/bin/env python3
"""Independently recompute R173 trace arithmetic without importing Qiskit."""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
from fractions import Fraction
from pathlib import Path
from typing import Any


METHOD = "b4_b8_r173_independent_divergence_oracle_v0"
SOURCE_PATH = "results/B4_B8_R173_first_divergent_combine_trace_v0.json"
R160_CASES_PATH = "results/B4_B8_R160_deterministic_error_map_remediation/case_analysis.json"
RESULT_PATH = "results/B4_B8_R173_independent_divergence_oracle_v0.json"
REPORT_PATH = "research/B4_B8_R173_independent_divergence_oracle.md"


def canonical_hash(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()
    ).hexdigest()


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def bits_to_float(bits: int) -> float:
    return struct.unpack("!d", int(bits).to_bytes(8, "big"))[0]


def float_bits(value: float) -> int:
    return struct.unpack("!Q", struct.pack("!d", value))[0]


def parse_leaf_rows(encoded: str) -> list[tuple[str, int]]:
    rows = []
    for item in encoded.split(";"):
        if item and "=" in item:
            label, raw_bits = item.rsplit("=", 1)
            rows.append((label, int(raw_bits)))
    return rows


def parse_candidate_event(event: dict[str, Any], candidate_index: int) -> dict[str, Any]:
    marker = "leaves="
    if marker not in event["result_terms"]:
        raise ValueError("R173 oracle candidate has no leaves")
    leaves = parse_leaf_rows(event["result_terms"].split(marker, 1)[1])
    exact = sum(
        (Fraction.from_float(bits_to_float(bits)) for _, bits in leaves),
        Fraction(0, 1),
    )
    mapping = []
    for item in event["left_terms"].split("|"):
        virtual, physical = item.split("->")
        mapping.append((int(virtual[1:]), int(physical[1:])))
    mapping.sort()
    return {
        "candidate_index": candidate_index,
        "mapping_vector": [physical for _, physical in mapping],
        "source_score_bits": int(event["left_bits"]),
        "source_leaf_bits": [bits for _, bits in leaves],
        "exact": exact,
    }


def select(candidates: list[dict[str, Any]], exact: bool) -> dict[str, Any]:
    incumbent = candidates[0]
    for candidate in candidates[1:]:
        if exact:
            better = candidate["exact"] < incumbent["exact"]
        else:
            better = bits_to_float(candidate["source_score_bits"]) < bits_to_float(
                incumbent["source_score_bits"]
            )
        if better:
            incumbent = candidate
    return incumbent


def analyze_candidate(events: list[dict[str, Any]], candidate: dict[str, Any]) -> dict[str, Any]:
    target_bits = candidate["source_leaf_bits"]
    final_matches = []
    for event_index, event in enumerate(events):
        if event["kind"] != "combine":
            continue
        leaves = parse_leaf_rows(event["result_terms"])
        if [bits for _, bits in leaves] == target_bits and int(event["result_bits"]) == candidate["source_score_bits"]:
            final_matches.append((event_index, leaves))
    if len(final_matches) != 1:
        raise ValueError("R173 oracle final-combine cardinality mismatch")
    final_event_index, full_leaves = final_matches[0]
    chain = []
    for event_index, event in enumerate(events):
        if event["kind"] != "combine":
            continue
        leaves = parse_leaf_rows(event["result_terms"])
        if not leaves or leaves != full_leaves[: len(leaves)]:
            continue
        exact = sum(
            (Fraction.from_float(bits_to_float(bits)) for _, bits in leaves),
            Fraction(0, 1),
        )
        correct_bits = float_bits(float(exact))
        native_bits = float_bits(
            bits_to_float(event["left_bits"]) + bits_to_float(event["right_bits"])
        )
        chain.append(
            {
                "event_index": event_index,
                "leaf_count": len(leaves),
                "result_bits": int(event["result_bits"]),
                "correctly_rounded_exact_bits": correct_bits,
                "signed_ulp_delta_from_correctly_rounded_exact": int(event["result_bits"]) - correct_bits,
                "native_addition_verified": native_bits == int(event["result_bits"]),
            }
        )
    first = next((row for row in chain if row["signed_ulp_delta_from_correctly_rounded_exact"]), None)
    final = next((row for row in chain if row["event_index"] == final_event_index and row["leaf_count"] == len(full_leaves)), None)
    if first is None or final is None:
        raise ValueError("R173 oracle could not localize candidate chain")
    return {
        "candidate_index": candidate["candidate_index"],
        "first_event_index": first["event_index"],
        "first_leaf_count": first["leaf_count"],
        "first_signed_ulp_delta": first["signed_ulp_delta_from_correctly_rounded_exact"],
        "final_event_index": final["event_index"],
        "final_signed_ulp_delta": final["signed_ulp_delta_from_correctly_rounded_exact"],
        "all_chain_native_additions_verified": all(row["native_addition_verified"] for row in chain),
    }


def recompute_trace(trace: dict[str, Any]) -> dict[str, Any]:
    events = trace["score_events"]
    yielded_events = [
        event
        for event in events
        if event["kind"] == "candidate"
        and not event["result_terms"].startswith("returned_by_minimize_vf2")
    ]
    returned_events = [
        event
        for event in events
        if event["kind"] == "candidate"
        and event["result_terms"].startswith("returned_by_minimize_vf2")
    ]
    candidates = [parse_candidate_event(event, index) for index, event in enumerate(yielded_events)]
    returned = parse_candidate_event(returned_events[-1], len(candidates))
    source = select(candidates, exact=False)
    exact = select(candidates, exact=True)
    pair = [exact, source]
    branch_rows = [analyze_candidate(events, candidate) for candidate in pair]
    all_combine_native = all(
        float_bits(bits_to_float(event["left_bits"]) + bits_to_float(event["right_bits"]))
        == int(event["result_bits"])
        for event in events
        if event["kind"] == "combine"
    )
    return {
        "input_id": trace["input_id"],
        "profile_id": trace["profile_id"],
        "score_events_hash_match": canonical_hash(events) == trace["score_events_hash"],
        "source_return_match": source["mapping_vector"] == returned["mapping_vector"]
        and source["source_score_bits"] == returned["source_score_bits"],
        "source_selected_candidate_index": source["candidate_index"],
        "exact_selected_candidate_index": exact["candidate_index"],
        "exact_totals_equal": source["exact"] == exact["exact"],
        "source_score_bit_gap": abs(source["source_score_bits"] - exact["source_score_bits"]),
        "exact_policy_preserves_first_seen_tie": source["exact"] == exact["exact"]
        and exact["candidate_index"] < source["candidate_index"],
        "all_combine_native_additions_verified": all_combine_native,
        "branches": branch_rows,
    }


def recompute_r160_controls(root: Path) -> dict[str, int]:
    payload = json.loads((root / R160_CASES_PATH).read_text(encoding="utf-8"))
    tie_rows = payload["tie_baseline"]["mode_rows"]
    tie_passed = sum(int(row["oracle"]["minimizer_count"]) > 1 and row["stable"] for row in tie_rows)
    non_tie_rows = [
        row
        for case in payload["case_rows"]
        if not case["all_replays_within_oracle"]
        for row in case["mode_rows"]
    ]
    non_tie_passed = 0
    for row in non_tie_rows:
        oracle = row["oracle"]
        minimum = Fraction(oracle["minimum_score_fraction"])
        second = Fraction(oracle["second_distinct_score_fraction"])
        non_tie_passed += minimum < second and int(oracle["minimizer_count"]) == 1
    return {
        "tie_control_count": len(tie_rows),
        "tie_controls_passed": tie_passed,
        "non_tie_control_count": len(non_tie_rows),
        "non_tie_controls_passed": non_tie_passed,
    }


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def build_report(result: dict[str, Any]) -> str:
    summary = result["summary"]
    return "\n".join(
        [
            "# B4/B8/B10 R173 Independent Divergence Oracle",
            "",
            f"- Status: `{result['status']}`",
            f"- Classification: `{result['classification']}`",
            f"- Requirements: `{result['requirements_passed']}/10`",
            f"- Payload hash: `{result['payload_hash']}`",
            "",
            "## Result",
            "",
            f"The standard-library oracle verifies `{summary['trace_payload_hash_match_count']}/{summary['trace_count']}` trace payload hashes, `{summary['score_event_hash_match_count']}/{summary['trace_count']}` score-event hashes, and localizes all `{summary['localized_branch_count']}` selected branches without importing Qiskit.",
            "",
            f"It independently passes `{summary['r160_tie_controls_passed']}/{summary['r160_tie_control_count']}` exact-tie controls and `{summary['r160_non_tie_controls_passed']}/{summary['r160_non_tie_control_count']}` exact non-tie controls.",
            "",
            "## Claim Boundary",
            "",
            "This verifies arithmetic replay and evidence integrity. It is not a source patch, production compiler remedy, confirmed Qiskit bug, hardware result, quantum advantage, BQP separation, solved frontier, or new credit.",
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
    if (root / RESULT_PATH).exists():
        raise ValueError("R173 independent oracle artifact already exists")
    source = json.loads((root / SOURCE_PATH).read_text(encoding="utf-8"))
    source_body = dict(source)
    source_hash = source_body.pop("payload_hash")
    if canonical_hash(source_body) != source_hash:
        raise ValueError("R173 source result payload hash mismatch")
    trace_rows = []
    trace_hash_matches = 0
    for item in source["trace_artifacts"]:
        path = root / item["path"]
        if file_sha256(path) != item["sha256"]:
            raise ValueError(f"R173 trace file hash mismatch: {item['path']}")
        trace = json.loads(path.read_text(encoding="utf-8"))
        trace_body = dict(trace)
        observed = trace_body.pop("trace_payload_hash")
        trace_hash_matches += canonical_hash(trace_body) == observed == item["trace_payload_hash"]
        trace_rows.append(recompute_trace(trace))
    controls = recompute_r160_controls(root)
    branches = [branch for row in trace_rows for branch in row["branches"]]
    requirements = [
        ("P1", len(trace_rows) == 6),
        ("P2", trace_hash_matches == len(trace_rows)),
        ("P3", all(row["score_events_hash_match"] for row in trace_rows)),
        ("P4", all(row["source_return_match"] for row in trace_rows)),
        ("P5", all(row["exact_totals_equal"] and row["source_score_bit_gap"] == 1 for row in trace_rows)),
        ("P6", all(row["exact_policy_preserves_first_seen_tie"] for row in trace_rows)),
        ("P7", all(row["all_combine_native_additions_verified"] for row in trace_rows)),
        ("P8", all(branch["all_chain_native_additions_verified"] for branch in branches) and len(branches) == 12),
        ("P9", controls == {"tie_control_count": 4, "tie_controls_passed": 4, "non_tie_control_count": 28, "non_tie_controls_passed": 28}),
        ("P10", args.preregistration_discussion == source["preregistration"]["discussion"] and args.preregistration_commit == source["preregistration"]["commit"]),
    ]
    result = {
        "title": "B4/B8/B10 R173 independent divergence oracle",
        "version": 0,
        "method": METHOD,
        "status": "independent_divergence_oracle_complete" if all(passed for _, passed in requirements) else "independent_divergence_oracle_incomplete",
        "classification": "independent_rounding_path_reproduction" if all(passed for _, passed in requirements) else "incomplete",
        "source_target_id": "T-B4-002cr/T-B8-003cv/T-B10-009ch-r173-oracle",
        "upstream_target_id": source["source_target_id"],
        "preregistration": {
            "commit": args.preregistration_commit,
            "discussion": args.preregistration_discussion,
            "created_at": args.preregistration_created_at,
        },
        "source_result_payload_hash": source_hash,
        "trace_rows": trace_rows,
        "summary": {
            "trace_count": len(trace_rows),
            "trace_payload_hash_match_count": trace_hash_matches,
            "score_event_hash_match_count": sum(row["score_events_hash_match"] for row in trace_rows),
            "source_return_match_count": sum(row["source_return_match"] for row in trace_rows),
            "localized_branch_count": len(branches),
            "native_addition_verified_trace_count": sum(row["all_combine_native_additions_verified"] for row in trace_rows),
            "r160_tie_control_count": controls["tie_control_count"],
            "r160_tie_controls_passed": controls["tie_controls_passed"],
            "r160_non_tie_control_count": controls["non_tie_control_count"],
            "r160_non_tie_controls_passed": controls["non_tie_controls_passed"],
            "qiskit_calls_performed": 0,
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
        "requirements": [{"requirement_id": key, "passed": passed} for key, passed in requirements],
        "requirements_passed": sum(passed for _, passed in requirements),
        "requirements_failed": sum(not passed for _, passed in requirements),
        "artifacts": {"source_result": SOURCE_PATH, "result": RESULT_PATH, "markdown_report": REPORT_PATH},
        "claim_boundary": {
            "what_is_supported": "independent standard-library reproduction of the R173 arithmetic localization and exact tie/non-tie score guardrail",
            "what_is_not_supported": "a source patch, production compiler remedy, confirmed Qiskit bug, hardware result, quantum advantage, BQP separation, solved B4/B8/B10, or new credit",
        },
    }
    result["payload_hash"] = canonical_hash(result)
    write_json(root / RESULT_PATH, result)
    (root / REPORT_PATH).write_text(build_report(result), encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["requirements_failed"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
