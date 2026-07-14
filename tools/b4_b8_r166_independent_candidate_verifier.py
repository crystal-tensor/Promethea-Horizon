#!/usr/bin/env python3
"""Independently verify R165 candidate selections and run tamper baselines."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
import struct
from fractions import Fraction
from pathlib import Path
from typing import Any


METHOD = "b4_b8_r166_independent_candidate_verifier_v0"
PROTOCOL_PATH = "results/B4_B8_R166_independent_candidate_verifier_protocol_v0.json"
CONTRACT_PATH = "benchmarks/B4_B8_R166_independent_candidate_verifier_contract_v0.json"
R165_RESULT_PATH = "results/B4_B8_R165_candidate_selection_replay_v0.json"
R165_CONTRACT_PATH = "benchmarks/B4_B8_R165_candidate_selection_contract_v0.json"
R165_DIR = "results/B4_B8_R165_candidate_selection_replay"
RESULT_PATH = "results/B4_B8_R166_independent_candidate_verifier_v0.json"
REPORT_PATH = "research/B4_B8_R166_independent_candidate_verifier.md"
POLICIES = ["source_f64", "compensated_fsum", "exact_binary64_leaf", "tie_aware_1ulp"]


def canonical_hash(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_json(root: Path, relative: str) -> dict[str, Any]:
    return json.loads((root / relative).read_text(encoding="utf-8"))


def verify_payload(payload: dict[str, Any], field: str, label: str) -> str:
    body = dict(payload)
    observed = body.pop(field, None)
    expected = canonical_hash(body)
    if observed != expected:
        raise ValueError(f"R166 {label} payload hash mismatch")
    return str(observed)


def bits_to_float(bits: int) -> float:
    return struct.unpack("!d", int(bits).to_bytes(8, "big"))[0]


def float_bits(value: float) -> int:
    return struct.unpack("!Q", struct.pack("!d", value))[0]


def exact_leaf_sum(candidate: dict[str, Any]) -> Fraction:
    return sum((Fraction.from_float(bits_to_float(int(bits))) for bits in candidate["source_leaf_bits"]), Fraction(0, 1))


def ulp_fraction(left: float, right: float) -> Fraction:
    return Fraction.from_float(math.ulp(max(abs(left), abs(right))))


def compare(left: dict[str, Any], right: dict[str, Any], policy: str) -> int:
    if policy == "source_f64":
        a, b = float(left["source_score"]), float(right["source_score"])
    elif policy == "compensated_fsum":
        a = math.fsum(bits_to_float(int(bits)) for bits in left["source_leaf_bits"])
        b = math.fsum(bits_to_float(int(bits)) for bits in right["source_leaf_bits"])
    else:
        a_exact = exact_leaf_sum(left)
        b_exact = exact_leaf_sum(right)
        if policy == "tie_aware_1ulp" and abs(a_exact - b_exact) <= ulp_fraction(float(left["source_score"]), float(right["source_score"])):
            return 0
        return -1 if a_exact < b_exact else (1 if a_exact > b_exact else 0)
    return -1 if a < b else (1 if a > b else 0)


def select(candidates: list[dict[str, Any]], policy: str) -> dict[str, Any] | None:
    if not candidates:
        return None
    incumbent = candidates[0]
    for candidate in candidates[1:]:
        if compare(candidate, incumbent, policy) < 0:
            incumbent = candidate
    return incumbent


def validate_candidate(candidate: dict[str, Any], label: str) -> None:
    required = {
        "candidate_index", "mapping_vector", "mapping_terms", "source_score_bits", "source_score",
        "source_leaf_bits", "compensated_score_bits", "exact_score_numerator",
        "exact_score_denominator", "leaf_count",
    }
    missing = required - set(candidate)
    if missing:
        raise ValueError(f"R166 {label} missing fields: {sorted(missing)}")
    source_score = float(candidate["source_score"])
    if float_bits(source_score) != int(candidate["source_score_bits"]):
        raise ValueError(f"R166 {label} source score bits mismatch")
    leaves = [bits_to_float(int(bits)) for bits in candidate["source_leaf_bits"]]
    if int(candidate["leaf_count"]) != len(leaves):
        raise ValueError(f"R166 {label} leaf count mismatch")
    if float_bits(math.fsum(leaves)) != int(candidate["compensated_score_bits"]):
        raise ValueError(f"R166 {label} compensated score mismatch")
    exact = exact_leaf_sum(candidate)
    if str(exact.numerator) != str(candidate["exact_score_numerator"]):
        raise ValueError(f"R166 {label} exact numerator mismatch")
    if str(exact.denominator) != str(candidate["exact_score_denominator"]):
        raise ValueError(f"R166 {label} exact denominator mismatch")
    if not isinstance(candidate["mapping_vector"], list) or not candidate["mapping_vector"]:
        raise ValueError(f"R166 {label} empty mapping")


def verify_row(row: dict[str, Any]) -> dict[str, Any]:
    row_body = dict(row)
    observed_hash = row_body.pop("replay_payload_hash", None)
    if observed_hash != canonical_hash(row_body):
        raise ValueError("R166 replay row payload hash mismatch")
    replay = row["replay"]
    candidates = replay["candidates"]
    for index, candidate in enumerate(candidates):
        validate_candidate(candidate, f"candidate {index}")
        if int(candidate["candidate_index"]) != index:
            raise ValueError("R166 candidate index is not contiguous")
    returned = replay.get("returned_candidate")
    if returned is None:
        raise ValueError("R166 returned candidate is absent")
    validate_candidate(returned, "returned candidate")
    selections = {policy: select(candidates, policy) for policy in POLICIES}
    selected_indices = {policy: (value["candidate_index"] if value else None) for policy, value in selections.items()}
    selected_mappings = {policy: (value["mapping_vector"] if value else None) for policy, value in selections.items()}
    source = selections["source_f64"]
    source_return_match = bool(
        source is not None
        and source["mapping_vector"] == returned["mapping_vector"]
        and source["source_score_bits"] == returned["source_score_bits"]
    )
    changed = {
        policy: bool(source is not None and value is not None and value["mapping_vector"] != source["mapping_vector"])
        for policy, value in selections.items()
    }
    if replay["selected_candidate_index"] != selected_indices:
        raise ValueError("R166 stored selection index differs from independent selection")
    if replay["selected_mapping_vector"] != selected_mappings:
        raise ValueError("R166 stored selection mapping differs from independent selection")
    if replay["policy_changed_mapping"] != changed:
        raise ValueError("R166 stored policy-change flags differ from independent selection")
    if bool(replay["source_return_match"]) != source_return_match or bool(row["source_return_match"]) != source_return_match:
        raise ValueError("R166 source-return flag differs from independent selection")
    if int(replay["yielded_candidate_count"]) != len(candidates):
        raise ValueError("R166 yielded candidate count mismatch")
    return {
        "source_return_match": source_return_match,
        "candidate_count": len(candidates),
        "policy_changed_mapping": changed,
        "selected_candidate_index": selected_indices,
    }


def verify_manifests(root: Path, protocol: dict[str, Any], contract: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    manifests = []
    rows = []
    for profile in protocol["profiles"]:
        relative = f"{R165_DIR}/{profile['profile_id']}.json"
        manifest = read_json(root, relative)
        body = dict(manifest)
        observed = body.pop("manifest_payload_hash", None)
        if observed != canonical_hash(body):
            raise ValueError(f"R166 manifest hash mismatch: {relative}")
        if manifest["profile_id"] != profile["profile_id"] or manifest["replay_count"] != profile["replay_count"]:
            raise ValueError(f"R166 profile manifest does not match protocol: {relative}")
        manifests.append(manifest)
        rows.extend(manifest["replay_rows"])
    if len(manifests) != protocol["profile_count"] or len(rows) != protocol["total_replay_count"]:
        raise ValueError("R166 manifest or replay count mismatch")
    return manifests, rows


def adversarial_baselines(rows: list[dict[str, Any]]) -> dict[str, Any]:
    multi = next((row for row in rows if len(row["replay"]["candidates"]) >= 2), None)
    if multi is None:
        raise ValueError("R166 requires a multi-candidate row for adversarial baselines")
    tampered_hash = copy.deepcopy(multi)
    tampered_hash["replay"]["candidates"][0]["mapping_vector"][0] += 1
    try:
        verify_row(tampered_hash)
    except ValueError as error:
        hash_rejected = True
        hash_reason = str(error)
    else:
        hash_rejected = False
        hash_reason = "accepted unexpectedly"

    tampered_selection = copy.deepcopy(multi)
    original_selection = tampered_selection["replay"]["selected_candidate_index"]["source_f64"]
    alternate = 1 if int(original_selection) == 0 else 0
    tampered_selection["replay"]["selected_candidate_index"]["source_f64"] = alternate
    tampered_selection["replay_payload_hash"] = canonical_hash({key: value for key, value in tampered_selection.items() if key != "replay_payload_hash"})
    try:
        verify_row(tampered_selection)
    except ValueError as error:
        rehashed_selection_rejected = True
        rehashed_reason = str(error)
    else:
        rehashed_selection_rejected = False
        rehashed_reason = "accepted unexpectedly"

    dropped = copy.deepcopy(multi)
    source_index = int(dropped["replay"]["selected_candidate_index"]["source_f64"])
    dropped["replay"]["candidates"].pop(source_index)
    for index, candidate in enumerate(dropped["replay"]["candidates"]):
        candidate["candidate_index"] = index
    source_after_drop = select(dropped["replay"]["candidates"], "source_f64")
    returned = dropped["replay"]["returned_candidate"]
    drop_detected = source_after_drop is None or source_after_drop["mapping_vector"] != returned["mapping_vector"] or source_after_drop["source_score_bits"] != returned["source_score_bits"]

    reversed_candidates = copy.deepcopy(multi["replay"]["candidates"])
    reversed_candidates.reverse()
    original_source = select(multi["replay"]["candidates"], "source_f64")
    reversed_source = select(reversed_candidates, "source_f64")
    order_changed = bool(original_source and reversed_source and original_source["mapping_vector"] != reversed_source["mapping_vector"])
    return {
        "tampered_row_hash_rejected": hash_rejected,
        "tampered_row_hash_rejection_reason": hash_reason,
        "rehashed_stored_selection_rejected": rehashed_selection_rejected,
        "rehashed_stored_selection_rejection_reason": rehashed_reason,
        "dropped_source_selected_candidate_detected": drop_detected,
        "candidate_order_reversal_changed_source_selection": order_changed,
        "adversarial_fixture_profile_id": multi["profile_id"],
        "adversarial_fixture_replay_index": multi["replay_index"],
    }


def build_report(result: dict[str, Any]) -> str:
    summary = result["summary"]
    adv = result["adversarial_baselines"]
    return "\n".join([
        "# B4/B8 R166 Independent Candidate Verifier",
        "",
        f"- Status: `{result['status']}`",
        f"- Classification: `{result['classification']}`",
        f"- Profiles / replays: `{summary['profile_count']}` / `{summary['replay_count']}`",
        f"- Candidate rows verified: `{summary['row_payload_hash_match_count']}` / `{summary['replay_count']}`",
        f"- Source-return matches recomputed: `{summary['source_return_match_count']}` / `{summary['replay_count']}`",
        f"- Payload hash: `{result['payload_hash']}`",
        "",
        "## Research Question",
        "",
        "Does an independent implementation recover the R165 candidate-selection result, and does it reject altered candidate evidence?",
        "",
        "## Method",
        "",
        "R166 reads only the committed R165 result rows and profile manifests. It recomputes binary64, compensated, exact-leaf, and 1-ULP selection using a separate standard-library implementation, then checks row and manifest hashes. It does not call Qiskit or import the R165 executor.",
        "",
        "## Result",
        "",
        f"The independent verifier recovered `{summary['source_return_match_count']}` of `{summary['replay_count']}` source-return matches, `{summary['candidate_count']}` complete candidates, and the same policy-change counts `{summary['policy_changed_mapping_count']}`. Hash tampering was rejected: `{adv['tampered_row_hash_rejected']}`; a rehashed but false stored selection was rejected by recomputation: `{adv['rehashed_stored_selection_rejected']}`.",
        "",
        "## Claim Boundary",
        "",
        "This confirms reproducibility of the committed candidate-level evidence and the verifier's rejection behavior. It does not establish a production mapping change, an alternate search path, a confirmed Qiskit bug, cross-platform determinism, hardware relevance, route advantage, quantum advantage, BQP separation, solved B4/B8/B10, or new credit.",
        "",
    ])


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--preregistration-commit", required=True)
    parser.add_argument("--preregistration-discussion", required=True)
    parser.add_argument("--preregistration-created-at", required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    protocol = read_json(root, PROTOCOL_PATH)
    contract = read_json(root, CONTRACT_PATH)
    verify_payload(protocol, "payload_hash", "protocol")
    verify_payload(contract, "payload_hash", "contract")
    if contract["execution_started"] is not False:
        raise ValueError("R166 contract is not unopened")
    if contract["protocol_payload_hash"] != protocol["payload_hash"]:
        raise ValueError("R166 protocol binding mismatch")
    for binding in contract["source_bindings"].values():
        path = root / binding["path"]
        if not path.exists() or file_sha256(path) != binding["sha256"]:
            raise ValueError(f"R166 source binding mismatch: {binding['path']}")
    r165_result = read_json(root, R165_RESULT_PATH)
    verify_payload(r165_result, "payload_hash", "R165 result")
    r165_contract = read_json(root, R165_CONTRACT_PATH)
    verify_payload(r165_contract, "payload_hash", "R165 contract")
    source_spec = protocol["source_artifacts"]
    manifests, rows = verify_manifests(root, source_spec, contract)
    checks = [verify_row(row) for row in rows]
    candidate_count = sum(check["candidate_count"] for check in checks)
    source_matches = sum(check["source_return_match"] for check in checks)
    policy_changes = {policy: sum(check["policy_changed_mapping"][policy] for check in checks) for policy in POLICIES}
    expected = r165_result["summary"]
    aggregate_match = (
        candidate_count == expected["yielded_candidate_count"]
        and source_matches == expected["source_return_match_count"]
        and policy_changes == expected["policy_changed_mapping_count"]
    )
    adversarial = adversarial_baselines(rows)
    acceptance = {
        "A1": len(manifests) == source_spec["profile_count"],
        "A2": len(rows) == source_spec["total_replay_count"],
        "A3": len(checks) == len(rows),
        "A4": candidate_count == expected["yielded_candidate_count"],
        "A5": source_matches == expected["source_return_match_count"],
        "A6": policy_changes == expected["policy_changed_mapping_count"],
        "A7": aggregate_match,
        "A8": adversarial["tampered_row_hash_rejected"],
        "A9": adversarial["rehashed_stored_selection_rejected"],
        "A10": adversarial["dropped_source_selected_candidate_detected"],
    }
    summary = {
        "profile_count": len(manifests),
        "replay_count": len(rows),
        "row_payload_hash_match_count": len(checks),
        "candidate_count": candidate_count,
        "source_return_match_count": source_matches,
        "source_return_mismatch_count": len(rows) - source_matches,
        "policy_changed_mapping_count": policy_changes,
        "r165_result_aggregate_match": aggregate_match,
        "qiskit_calls_performed": 0,
        "simulation_execution_count": 0,
        "total_simulated_shots": 0,
        "new_credit_delta": 0,
    }
    result = {
        "title": "B4/B8 R166 independent candidate verifier",
        "version": 0,
        "method": METHOD,
        "status": "independent_reproduction_complete" if all(acceptance.values()) else "independent_reproduction_incomplete",
        "classification": "independent_reproduction_confirmed_adversarial_tamper_rejected" if all(acceptance.values()) else "independent_reproduction_incomplete",
        "preregistration": {"commit": args.preregistration_commit, "discussion": args.preregistration_discussion, "created_at": args.preregistration_created_at},
        "summary": summary,
        "acceptance_conditions": [{"condition_id": key, "passed": value} for key, value in acceptance.items()],
        "requirements_passed": sum(acceptance.values()),
        "requirements_failed": sum(not value for value in acceptance.values()),
        "adversarial_baselines": adversarial,
        "artifacts": {"protocol": PROTOCOL_PATH, "contract": CONTRACT_PATH, "result": RESULT_PATH, "markdown_report": REPORT_PATH, "source_result": R165_RESULT_PATH},
        "claim_boundary": {"what_is_supported": "independent recomputation of the committed R165 candidate-level selections and rejection of altered evidence", "what_is_not_supported": "a production mapping change, alternate search path, confirmed Qiskit bug, cross-platform determinism, hardware relevance, route advantage, quantum advantage, BQP separation, solved B4/B8/B10, or new credit"},
    }
    result["payload_hash"] = canonical_hash(result)
    (root / RESULT_PATH).write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (root / REPORT_PATH).write_text(build_report(result), encoding="utf-8")
    print(json.dumps({"status": result["status"], "classification": result["classification"], "summary": summary, "requirements_passed": result["requirements_passed"], "requirements_failed": result["requirements_failed"], "payload_hash": result["payload_hash"]}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
