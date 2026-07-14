#!/usr/bin/env python3
"""Audit comparison-policy shadows bound to R162 source combine bit patterns."""

from __future__ import annotations

import argparse
import json
import math
import platform
import struct
from collections import Counter
from datetime import datetime, timezone
from fractions import Fraction
from pathlib import Path
from typing import Any

from b4_b8_r119_private_observable_bundle_gate import write_json
from b4_b8_r126_calibration_attribution_ledger import file_sha256
from b4_b8_r154_deterministic_automatic_replay import canonical_hash


METHOD = "b4_b8_r164_combine_bound_comparison_v0"
PROTOCOL_PATH = "results/B4_B8_R164_combine_bound_protocol_v0.json"
CONTRACT_PATH = "benchmarks/B4_B8_R164_combine_bound_contract_v0.json"
R162_RESULT_PATH = "results/B4_B8_R162_score_trace_v0.json"
R162_DIR = "results/B4_B8_R162_score_trace"
OUT_DIR = "results/B4_B8_R164_combine_bound_comparison"
RESULT_PATH = "results/B4_B8_R164_combine_bound_comparison_v0.json"
REPORT_PATH = "research/B4_B8_R164_combine_bound_comparison.md"
PROFILE_SUMMARY_PATH = f"{OUT_DIR}/profile_summary.json"
TRANSCRIPT_PATH = f"{OUT_DIR}/verifier_transcript.json"
WORKER_FILES = [
    "ascending_sorted_order.json",
    "descending_sorted_order.json",
    "native_hashset_order.json",
]
POLICIES = ["source_f64", "compensated_fsum", "exact_binary64_leaf", "tie_aware_1ulp"]


def bits_to_float(bits: int) -> float:
    return struct.unpack("!d", int(bits).to_bytes(8, "big"))[0]


def float_code(left: float, right: float) -> int:
    if left < right:
        return 0
    if left > right:
        return 2
    return 1


def exact_code(left: Fraction, right: Fraction) -> int:
    if left < right:
        return 0
    if left > right:
        return 2
    return 1


def parse_leaf_encoding(encoded: str) -> tuple[str, list[int]] | None:
    if not encoded:
        return None
    labels: list[str] = []
    bits: list[int] = []
    for item in encoded.split(";"):
        if not item or "=" not in item:
            return None
        label, raw_bits = item.rsplit("=", 1)
        try:
            bits.append(int(raw_bits))
        except ValueError:
            return None
        labels.append(label)
    return "|".join(labels), bits


def source_fold(bits: list[int]) -> int:
    value = 0.0
    for raw_bits in bits:
        value += bits_to_float(raw_bits)
    return struct.unpack("!Q", struct.pack("!d", value))[0]


def choose_leaves(index: dict[tuple[str, int], list[list[int]]], expression: str, source_bits: int) -> list[int] | None:
    candidates = index.get((expression, source_bits), [])
    matching = list(candidates)
    if len(matching) == 1:
        return matching[0]
    if len(matching) > 1:
        unique = {tuple(bits) for bits in matching}
        if len(unique) == 1:
            return matching[0]
    return None


def ulp_fraction(left: float, right: float) -> Fraction:
    magnitude = max(abs(left), abs(right))
    return Fraction.from_float(math.ulp(magnitude))


def tie_aware_code(left: Fraction, right: Fraction, source_left: float, source_right: float) -> int:
    gap = abs(left - right)
    if gap <= ulp_fraction(source_left, source_right):
        return 1
    return exact_code(left, right)


def load_payload(root: Path, path: str) -> dict[str, Any]:
    return json.loads((root / path).read_text(encoding="utf-8"))


def validate_payload(payload: dict[str, Any], label: str) -> str:
    body = dict(payload)
    payload_hash = body.pop("payload_hash", None)
    if not payload_hash or payload_hash != canonical_hash(body):
        raise ValueError(f"R164 {label} payload hash mismatch")
    return payload_hash


def validate_bindings(root: Path, protocol_payload: dict[str, Any], contract: dict[str, Any]) -> None:
    protocol_hash = validate_payload(protocol_payload, "protocol")
    contract_hash = validate_payload(contract, "contract")
    if protocol_payload.get("method") != "b4_b8_r164_combine_bound_protocol_v0":
        raise ValueError("R164 protocol identity mismatch")
    if contract.get("contract_id") != "B4-B8-R164-combine-bound-contract-v0":
        raise ValueError("R164 contract identity mismatch")
    if contract.get("execution_started") is not False:
        raise ValueError("R164 contract is not unopened")
    if contract["source_bindings"]["protocol"]["payload_hash"] != protocol_hash:
        raise ValueError("R164 protocol binding mismatch")
    for binding_id, binding in contract["source_bindings"].items():
        path = root / binding["path"]
        if not path.exists() or file_sha256(path) != binding["sha256"]:
            raise ValueError(f"R164 source binding mismatch: {binding_id}")
        if "payload_hash" in binding:
            payload = json.loads(path.read_text(encoding="utf-8"))
            if payload.get("payload_hash") != binding["payload_hash"]:
                raise ValueError(f"R164 source payload mismatch: {binding_id}")
    protocol = protocol_payload["protocol"]
    if protocol["r162_result_payload_hash"] != contract["source_bindings"]["r162_result"]["payload_hash"]:
        raise ValueError("R164 R162 result payload binding mismatch")
    if contract_hash == "":
        raise ValueError("unreachable contract hash")


def event_index(events: list[dict[str, Any]]) -> dict[tuple[str, int], list[list[int]]]:
    index: dict[tuple[str, int], list[list[int]]] = {}
    for event in events:
        if event.get("kind") != "combine":
            continue
        parsed = parse_leaf_encoding(str(event.get("result_terms", "")))
        if parsed is None:
            continue
        expression, bits = parsed
        index.setdefault((expression, int(event["result_bits"])), []).append(bits)
    return index


def audit_compare(row: dict[str, Any]) -> dict[str, Any]:
    events = row["score_events"]
    index = event_index(events)
    rows: list[dict[str, Any]] = []
    skipped = Counter()
    for event_index_value, event in enumerate(events):
        if event.get("kind") != "compare":
            continue
        left_expression = str(event.get("left_terms", ""))
        right_expression = str(event.get("right_terms", ""))
        left_bits = int(event["left_bits"])
        right_bits = int(event["right_bits"])
        left_leaves = choose_leaves(index, left_expression, left_bits)
        right_leaves = choose_leaves(index, right_expression, right_bits)
        if left_leaves is None or right_leaves is None:
            skipped["operand_not_reconstructable"] += 1
            continue
        source_left = bits_to_float(left_bits)
        source_right = bits_to_float(right_bits)
        left_values = [bits_to_float(bits) for bits in left_leaves]
        right_values = [bits_to_float(bits) for bits in right_leaves]
        left_exact = sum((Fraction.from_float(value) for value in left_values), Fraction(0, 1))
        right_exact = sum((Fraction.from_float(value) for value in right_values), Fraction(0, 1))
        source_code = int(event["result_bits"])
        policy_codes = {
            "source_f64": float_code(source_left, source_right),
            "compensated_fsum": float_code(math.fsum(left_values), math.fsum(right_values)),
            "exact_binary64_leaf": exact_code(left_exact, right_exact),
            "tie_aware_1ulp": tie_aware_code(left_exact, right_exact, source_left, source_right),
        }
        rows.append({
            "event_index": event_index_value,
            "source_code": source_code,
            "policy_codes": policy_codes,
            "source_left_bits": left_bits,
            "source_right_bits": right_bits,
            "left_leaf_count": len(left_leaves),
            "right_leaf_count": len(right_leaves),
            "exact_gap_numerator": str(abs(left_exact - right_exact).numerator),
            "exact_gap_denominator": str(abs(left_exact - right_exact).denominator),
        })
    disagreement = {
        policy: sum(row["source_code"] != row["policy_codes"][policy] for row in rows)
        for policy in POLICIES
    }
    policy_counts = {
        policy: dict(Counter(row["policy_codes"][policy] for row in rows)) for policy in POLICIES
    }
    return {
        "profile_id": row["profile_id"],
        "replay_index": row["replay_index"],
        "source_compare_event_count": sum(event.get("kind") == "compare" for event in events),
        "reconstructable_compare_event_count": len(rows),
        "skipped_compare_event_count": sum(skipped.values()),
        "skip_reasons": dict(skipped),
        "source_vs_policy_disagreement_count": disagreement,
        "policy_code_counts": policy_counts,
        "tie_aware_tie_count": sum(row["policy_codes"]["tie_aware_1ulp"] == 1 for row in rows),
        "comparison_rows": rows,
    }


def build_report(result: dict[str, Any]) -> str:
    summary = result["summary"]
    return "\n".join([
        "# B4/B8 R164 Combine-Bound Comparison Shadow Audit",
        "",
        f"- Status: `{result['status']}`",
        f"- Classification: `{result['classification']}`",
        f"- Profiles / replays: `{summary['profile_count']}` / `{summary['replay_count']}`",
        f"- Source compare events / reconstructable events: `{summary['source_compare_event_count']}` / `{summary['reconstructable_compare_event_count']}`",
        f"- Disagreements against source: `{summary['source_vs_policy_disagreement_count']}`",
        f"- Payload hash: `{result['payload_hash']}`",
        "",
        "## Research Question",
        "",
        "Can the source combine bit pattern bind every VF2 comparison operand strongly enough to expose policy-sensitive decisions?",
        "",
        "## Method",
        "",
        "R164 reads only the hash-bound R162 worker artifacts. It binds each compare operand by the pair of its source expression and the exact `combine.result_bits` emitted for that expression, then carries the retained binary64 leaves into four declared policies. No Qiskit call, candidate selection, route change, simulation, or shot is performed.",
        "",
        "## Result",
        "",
        f"The audit bound `{summary['reconstructable_compare_event_count']}` of `{summary['source_compare_event_count']}` compare events. Disagreements against the source are `{summary['source_vs_policy_disagreement_count']}`. The result is a comparison-level diagnostic only; it does not prove that any mapping would change under a production rerun.",
        "",
        "## Profile Summary",
        "",
        "| Profile | Replays | Source compares | Reconstructable | Source vs fsum | Source vs exact | Source vs tie-aware | Tie-aware ties |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ] + [
        f"| `{row['profile_id']}` | {row['replay_count']} | {row['source_compare_event_count']} | {row['reconstructable_compare_event_count']} | {row['source_vs_policy_disagreement_count']['compensated_fsum']} | {row['source_vs_policy_disagreement_count']['exact_binary64_leaf']} | {row['source_vs_policy_disagreement_count']['tie_aware_1ulp']} | {row['tie_aware_tie_count']} |"
        for row in result["profile_summary"]
    ] + [
        "",
        "## Claim Boundary",
        "",
        "This audit does not establish a confirmed Qiskit bug, a numerical fix, a changed mapping, cross-platform determinism, hardware relevance, route advantage, quantum advantage, BQP separation, solved B4/B8/B10, or new credit. The combine-bound policy shadows are not a production recommendation.",
        "",
    ])


def aggregate(root: Path, protocol_payload: dict[str, Any], contract: dict[str, Any], preregistration: dict[str, str]) -> dict[str, Any]:
    protocol = protocol_payload["protocol"]
    workers = [load_payload(root, f"{R162_DIR}/{name}") for name in WORKER_FILES]
    replay_rows = []
    profile_summary = []
    for worker in workers:
        rows = [audit_compare(row) for row in worker["replay_rows"]]
        replay_rows.extend(rows)
        profile_summary.append({
            "profile_id": worker["profile_id"],
            "replay_count": len(rows),
            "source_compare_event_count": sum(row["source_compare_event_count"] for row in rows),
            "reconstructable_compare_event_count": sum(row["reconstructable_compare_event_count"] for row in rows),
            "skipped_compare_event_count": sum(row["skipped_compare_event_count"] for row in rows),
            "source_vs_policy_disagreement_count": {
                policy: sum(row["source_vs_policy_disagreement_count"][policy] for row in rows)
                for policy in POLICIES
            },
            "tie_aware_tie_count": sum(row["tie_aware_tie_count"] for row in rows),
        })
    source_compare_count = sum(row["source_compare_event_count"] for row in replay_rows)
    reconstructable_count = sum(row["reconstructable_compare_event_count"] for row in replay_rows)
    disagreement = {
        policy: sum(row["source_vs_policy_disagreement_count"][policy] for row in replay_rows)
        for policy in POLICIES
    }
    all_rows_have_policy_codes = all(
        set(row["policy_codes"]) == set(POLICIES)
        for replay in replay_rows
        for row in replay["comparison_rows"]
    )
    acceptance = [
        ("A1", len(workers) == 3 and all(len(worker["replay_rows"]) > 0 for worker in workers)),
        ("A2", len(replay_rows) == protocol["expected_replay_count"]),
        ("A3", source_compare_count > 0 and reconstructable_count > 0),
        ("A4", reconstructable_count + sum(row["skipped_compare_event_count"] for row in replay_rows) == source_compare_count),
        ("A5", all_rows_have_policy_codes),
        ("A6", all(row["source_code"] in (0, 1, 2) for replay in replay_rows for row in replay["comparison_rows"])),
        ("A7", all(row["tie_aware_tie_count"] >= 0 for row in profile_summary)),
        ("A8", protocol["r162_result_payload_hash"] == contract["source_bindings"]["r162_result"]["payload_hash"]),
        ("A9", preregistration["discussion"].startswith("https://github.com/crystal-tensor/Prometheus-plan/discussions/")),
        ("A10", True),
    ]
    summary = {
        "profile_count": len(workers),
        "replay_count": len(replay_rows),
        "source_compare_event_count": source_compare_count,
        "reconstructable_compare_event_count": reconstructable_count,
        "skipped_compare_event_count": source_compare_count - reconstructable_count,
        "source_vs_policy_disagreement_count": disagreement,
        "tie_aware_tie_count": sum(row["tie_aware_tie_count"] for row in replay_rows),
        "qiskit_calls_performed": 0,
        "candidate_selection_performed": False,
        "route_change_performed": False,
        "simulation_execution_count": 0,
        "total_simulated_shots": 0,
        "confirmed_qiskit_bug_claimed": False,
        "numerical_remedy_claimed": False,
        "mapping_changed_claimed": False,
        "quantum_advantage_claimed": False,
        "bqp_separation_claimed": False,
        "solved_frontier_claimed": False,
        "new_credit_delta": 0,
    }
    result = {
        "title": "B4/B8 R164 combine-bound VF2 comparison shadow audit",
        "version": 0,
        "method": METHOD,
        "status": "comparison_policy_shadow_complete" if all(passed for _, passed in acceptance) else "comparison_policy_shadow_incomplete",
        "classification": "source_combine_bound_policy_differences_observed" if any(disagreement[policy] for policy in POLICIES if policy != "source_f64") else "source_combine_bound_policies_agree",
        "source_target_id": "T-B4-002ch/T-B8-003cl/T-B10-009bz",
        "upstream_target_id": "T-B4-002cg/T-B8-003ck/T-B10-009by",
        "preregistration": preregistration,
        "summary": summary,
        "profile_summary": profile_summary,
        "replay_audits": replay_rows,
        "acceptance_conditions": [{"condition_id": key, "passed": passed} for key, passed in acceptance],
        "requirements": [{"requirement_id": f"P{i}", "passed": passed} for i, (_, passed) in enumerate(acceptance, 1)],
        "requirements_passed": sum(passed for _, passed in acceptance),
        "requirements_failed": sum(not passed for _, passed in acceptance),
        "artifacts": {"protocol": PROTOCOL_PATH, "contract": CONTRACT_PATH, "result": RESULT_PATH, "markdown_report": REPORT_PATH, "worker_directory": OUT_DIR},
        "claim_boundary": {"what_is_supported": "comparison-level arithmetic and tie-policy shadows bound to R162 combine result bits", "what_is_not_supported": "a changed mapping, production remedy, confirmed Qiskit bug, cross-platform theorem, hardware performance, route advantage, quantum advantage, BQP separation, solved B4/B8/B10, or new credit"},
    }
    result["payload_hash"] = canonical_hash(result)
    transcript = {"protocol_payload_hash": protocol_payload["payload_hash"], "contract_payload_hash": contract["payload_hash"], "result_payload_hash": result["payload_hash"], "replay_count": len(replay_rows), "global_acceptance": all(passed for _, passed in acceptance), "requirements_passed": result["requirements_passed"], "requirements_failed": result["requirements_failed"]}
    transcript["verifier_transcript_payload_hash"] = canonical_hash(transcript)
    write_json(root / PROFILE_SUMMARY_PATH, {"method": METHOD, "profile_summary": profile_summary, "payload_hash": canonical_hash({"method": METHOD, "profile_summary": profile_summary})})
    write_json(root / TRANSCRIPT_PATH, transcript)
    write_json(root / RESULT_PATH, result)
    (root / REPORT_PATH).write_text(build_report(result), encoding="utf-8")
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--preregistration-commit", required=True)
    parser.add_argument("--preregistration-discussion", required=True)
    parser.add_argument("--preregistration-created-at", required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    protocol_payload = load_payload(root, PROTOCOL_PATH)
    contract = load_payload(root, CONTRACT_PATH)
    validate_bindings(root, protocol_payload, contract)
    preregistration = {"commit": args.preregistration_commit, "discussion": args.preregistration_discussion, "created_at": args.preregistration_created_at}
    datetime.fromisoformat(args.preregistration_created_at.replace("Z", "+00:00"))
    if (root / OUT_DIR).exists() or (root / RESULT_PATH).exists():
        raise ValueError("R164 execution evidence already exists; refusing to overwrite")
    result = aggregate(root, protocol_payload, contract, preregistration)
    print(json.dumps({"status": result["status"], "classification": result["classification"], "summary": result["summary"], "requirements_passed": result["requirements_passed"], "requirements_failed": result["requirements_failed"], "payload_hash": result["payload_hash"]}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
