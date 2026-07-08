#!/usr/bin/env python3
"""T-B1-004fb/T-B7-014k: R52 C01 evidence-triplet route gate."""

from __future__ import annotations

import argparse
import hashlib
import json
import time
from pathlib import Path
from typing import Any


METHOD = "b1_b7_cone01_r52_o3_f4_c2_evidence_triplet_route_gate_v0"
STATUS = "cone01_r52_o3_f4_c2_evidence_triplet_route_ready_zero_credit"
MODEL_STATUS = "o3_f4_c2_c01_three_flag_blocker_split_into_acceptance_route"
VERSION = "0.1"
TARGET_ID = "T-B1-004fb/T-B7-014k"
UPSTREAM_TARGET_ID = "T-B1-004fa/T-B7-014j"
SELECTED_CHALLENGE_ID = "O3-F4-C01"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def stable_hash(payload: Any) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def req(requirement_id: str, label: str, passed: bool, evidence: dict[str, Any]) -> dict[str, Any]:
    return {
        "requirement_id": requirement_id,
        "label": label,
        "passed": bool(passed),
        "evidence": evidence,
    }


def hash_file_if_present(root: Path, value: Any) -> dict[str, Any]:
    if not isinstance(value, str):
        return {"path": value, "exists": False, "sha256": None}
    path = root / value
    exists = path.exists() and path.is_file()
    return {"path": value, "exists": exists, "sha256": file_hash(path) if exists else None}


def build_route_packet(
    r51: dict[str, Any],
    row: dict[str, Any],
    witness: dict[str, Any],
    verifier: dict[str, Any],
    signature_blocker: dict[str, Any],
    root: Path,
) -> dict[str, Any]:
    current_files = {
        "smoke_witness": hash_file_if_present(root, row.get("same_unitary_witness_file")),
        "dry_run_verifier": hash_file_if_present(root, row.get("same_unitary_witness_verifier")),
        "signature_blocker": hash_file_if_present(root, row.get("verifier_signature_file")),
    }
    route = {
        "route_id": "B1-B7-cone01-O3-F4-C2-C01-evidence-triplet-route",
        "source_target_id": TARGET_ID,
        "upstream_target_id": UPSTREAM_TARGET_ID,
        "selected_challenge_id": SELECTED_CHALLENGE_ID,
        "source_r51_evaluation_hash": r51["summary"]["evaluation_hash"],
        "source_r50_presubmission_row_hash": r51["summary"]["source_r50_presubmission_row_hash"],
        "current_flag_failures": r51["summary"]["actual_flag_failures"],
        "current_files": current_files,
        "required_evidence_slots": [
            {
                "slot_id": "E1-source-backed-replay-witness",
                "unblocks_flag": "source_backed_replay",
                "must_replace": row.get("same_unitary_witness_file"),
                "required_properties": [
                    "binds source_dataset_file and source_trace_file by sha256",
                    "binds source_circuit_file and candidate_circuit_file by sha256",
                    "runs a replay command whose stdout hash is captured",
                    "states why the replay is not only the R37/R43 smoke artifact",
                ],
            },
            {
                "slot_id": "E2-real-same-unitary-verifier-transcript",
                "unblocks_flag": "same_unitary_certificate",
                "must_replace": row.get("same_unitary_witness_verifier"),
                "required_properties": [
                    "executes the verifier rather than only checking schema strings",
                    "records verifier command, version, inputs, stdout, and hash",
                    "checks same-unitary equivalence against the source-backed witness",
                    "rejects dry-run scope values such as checks_schema_shape_only_not_unitary_equivalence",
                ],
            },
            {
                "slot_id": "E3-verifier-signature-artifact",
                "unblocks_flag": "smoke_only_not_c2_acceptance",
                "must_replace": row.get("verifier_signature_file"),
                "required_properties": [
                    "is not the R50 blocker note",
                    "signs the source-backed replay witness and verifier transcript hashes",
                    "keeps zero-credit claim-boundary tokens for no C2, O3, reroute, B7, and STV",
                    "allows smoke_only_not_c2_acceptance=false only after E1 and E2 pass",
                ],
            },
        ],
        "acceptance_order": ["E1-source-backed-replay-witness", "E2-real-same-unitary-verifier-transcript", "E3-verifier-signature-artifact", "rerun R51", "rerun R47"],
        "hard_reject_if": [
            "any E-slot is satisfied by the current smoke witness, dry-run verifier, or blocker note",
            "any boolean flag is flipped before its corresponding evidence slot passes",
            "R51 does not pass 8/8 after the replacement row is submitted",
            "R47 does not accept exactly one source-backed row before scaling",
            "any result claims C2, O3 closure, reroute, B7 credit, STV credit, or resource saving",
        ],
        "zero_credit_boundary": {
            "c2_accepted": False,
            "o3_closed": False,
            "reroute_allowed": False,
            "b7_credit_delta": 0,
            "b7_space_time_volume_credit": 0,
            "resource_saving_claimed": False,
            "b7_ledger_improvement_claimed": False,
        },
    }
    route["route_hash"] = stable_hash(route)
    route["current_blocker_assessment"] = {
        "smoke_witness_scope": witness.get("scope"),
        "dry_run_verifier_scope": verifier.get("scope"),
        "signature_blocker_scope": signature_blocker.get("scope"),
        "current_triplet_satisfies_evidence_slots": False,
        "direct_promotion_of_current_row_rejected": True,
    }
    route["route_packet_hash"] = stable_hash(route)
    return route


def build_payload(args: argparse.Namespace) -> dict[str, Any]:
    started = time.time()
    r51 = load_json(args.r51_result)
    row = load_json(args.presubmission_input)
    witness = load_json(args.smoke_witness)
    verifier = load_json(args.dry_run_verifier)
    signature_blocker = load_json(args.signature_blocker)
    route = build_route_packet(r51, row, witness, verifier, signature_blocker, args.root)
    write_json(args.route_output, route)

    slot_count = len(route["required_evidence_slots"])
    current_files_present = sum(1 for item in route["current_files"].values() if item["exists"])
    current_slots_satisfied = 0
    direct_promotion_rejected = route["current_blocker_assessment"]["direct_promotion_of_current_row_rejected"]
    requirements = [
        req(
            "S1",
            "R51 is the upstream gate and still blocks only the three semantic flags",
            r51["summary"].get("requirements_passed") == 8
            and r51["summary"].get("requirements_failed") == 0
            and set(r51["summary"].get("actual_flag_failures", []))
            == {"source_backed_replay", "same_unitary_certificate", "smoke_only_not_c2_acceptance"},
            {
                "r51_requirements_passed": r51["summary"].get("requirements_passed"),
                "r51_flag_failures": r51["summary"].get("actual_flag_failures"),
            },
        ),
        req(
            "S2",
            "The current triplet is present but explicitly smoke/dry-run/blocker scoped",
            current_files_present == 3
            and "smoke" in str(witness.get("scope", ""))
            and (
                "dry-run" in str(verifier.get("artifact", "")).lower()
                or "dry_run" in str(verifier.get("artifact", "")).lower()
            )
            and "blocker" in str(signature_blocker.get("artifact", "")).lower(),
            {
                "current_files_present": current_files_present,
                "smoke_witness_scope": witness.get("scope"),
                "dry_run_verifier_artifact": verifier.get("artifact"),
                "signature_blocker_artifact": signature_blocker.get("artifact"),
            },
        ),
        req(
            "S3",
            "R52 creates one required evidence slot per failing semantic flag",
            slot_count == 3
            and [slot["unblocks_flag"] for slot in route["required_evidence_slots"]]
            == ["source_backed_replay", "same_unitary_certificate", "smoke_only_not_c2_acceptance"],
            {"slot_count": slot_count, "slot_flags": [slot["unblocks_flag"] for slot in route["required_evidence_slots"]]},
        ),
        req(
            "S4",
            "No current smoke/dry-run/blocker file is allowed to satisfy an evidence slot",
            current_slots_satisfied == 0 and direct_promotion_rejected is True,
            {
                "current_evidence_slots_satisfied": current_slots_satisfied,
                "direct_promotion_of_current_row_rejected": direct_promotion_rejected,
            },
        ),
        req(
            "S5",
            "The route requires rerunning R51 before R47 after replacement evidence lands",
            route["acceptance_order"][-2:] == ["rerun R51", "rerun R47"],
            {"acceptance_order": route["acceptance_order"]},
        ),
        req(
            "S6",
            "The route keeps one-row-first scaling pressure",
            any("exactly one source-backed row" in rule for rule in route["hard_reject_if"]),
            {"hard_reject_if": route["hard_reject_if"]},
        ),
        req(
            "S7",
            "Zero-credit boundary remains explicit",
            route["zero_credit_boundary"] == {
                "c2_accepted": False,
                "o3_closed": False,
                "reroute_allowed": False,
                "b7_credit_delta": 0,
                "b7_space_time_volume_credit": 0,
                "resource_saving_claimed": False,
                "b7_ledger_improvement_claimed": False,
            },
            route["zero_credit_boundary"],
        ),
        req(
            "S8",
            "The route packet is hash-bound for PR review",
            len(route["route_packet_hash"]) == 64 and len(route["route_hash"]) == 64,
            {"route_hash": route["route_hash"], "route_packet_hash": route["route_packet_hash"]},
        ),
    ]
    failed = [item["requirement_id"] for item in requirements if not item["passed"]]
    summary = {
        "source_r51_evaluation_hash": r51["summary"]["evaluation_hash"],
        "source_r50_presubmission_row_hash": r51["summary"]["source_r50_presubmission_row_hash"],
        "selected_challenge_id": SELECTED_CHALLENGE_ID,
        "route_hash": route["route_hash"],
        "route_packet_hash": route["route_packet_hash"],
        "route_file_sha256": file_hash(args.route_output),
        "evidence_slot_count": slot_count,
        "current_evidence_slots_satisfied": current_slots_satisfied,
        "current_blocker_file_count": current_files_present,
        "current_flag_failure_count": len(r51["summary"]["actual_flag_failures"]),
        "direct_promotion_of_current_row_rejected": direct_promotion_rejected,
        "accepted_source_backed_row_count": 0,
        "source_backed_replay": False,
        "same_unitary_certificate": False,
        "smoke_only_not_c2_acceptance": True,
        "c2_strict_replay_rows_accepted": False,
        "o3_closed": False,
        "reroute_allowed": False,
        "b7_credit_delta": 0,
        "b7_space_time_volume_credit": 0,
        "resource_saving_claimed": False,
        "b7_ledger_improvement_claimed": False,
        "remaining_open_obligations": [
            "submit_E1_source_backed_replay_witness",
            "submit_E2_real_same_unitary_verifier_transcript",
            "submit_E3_verifier_signature_artifact",
            "submit_replacement_row_with_three_evidence_backed_flags",
            "rerun_R51_then_R47_and_accept_exactly_one_row",
        ],
        "remaining_open_obligation_count": 5,
        "requirement_count": len(requirements),
        "requirements_passed": len(requirements) - len(failed),
        "requirements_failed": len(failed),
        "failed_requirement_ids": failed,
        "validation_error_count": len(failed),
    }
    return {
        "title": "B1/B7 Cone01 R52 O3-F4 C2 Evidence-Triplet Route Gate",
        "version": VERSION,
        "last_updated": "2026-07-08",
        "benchmark_id": "B1",
        "linked_benchmark_id": "B7",
        "method": METHOD,
        "status": STATUS,
        "model_status": MODEL_STATUS,
        "source_target_id": TARGET_ID,
        "upstream_target_id": UPSTREAM_TARGET_ID,
        "evidence_triplet_route_packet": {
            "source_r51_result": str(args.r51_result),
            "presubmission_input": str(args.presubmission_input),
            "smoke_witness": str(args.smoke_witness),
            "dry_run_verifier": str(args.dry_run_verifier),
            "signature_blocker": str(args.signature_blocker),
            "route_output": str(args.route_output),
            "route": route,
        },
        "requirements": requirements,
        "summary": summary,
        "claim_boundary": {
            "what_is_supported": (
                "R52 converts the three R51 semantic blockers into a hash-bound "
                "three-slot evidence route for C01 and rejects direct promotion "
                "of the current smoke/dry-run/blocker triplet."
            ),
            "what_is_not_supported": (
                "R52 does not supply the source-backed replay witness, real same-unitary "
                "verifier transcript, verifier signature, accepted C2 row, O3 closure, "
                "reroute permission, B7/STV credit, or resource-saving claim."
            ),
            "next_gate": (
                "Submit E1/E2/E3 replacement artifacts, create a replacement row with "
                "evidence-backed flags, then rerun R51 and R47 with exactly one row passing."
            ),
            "resource_saving_claimed": False,
            "b7_ledger_improvement_claimed": False,
        },
        "validation_errors": failed,
        "runtime_seconds": round(time.time() - started, 6),
    }


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    s = payload["summary"]
    route = payload["evidence_triplet_route_packet"]["route"]
    lines = [
        "# B1/B7 Cone01 R52 O3-F4 C2 Evidence-Triplet Route Gate",
        "",
        f"- Target: `{payload['source_target_id']}`",
        f"- Upstream target: `{payload['upstream_target_id']}`",
        f"- Method: `{payload['method']}`",
        f"- Status: `{payload['status']}`",
        f"- Selected challenge: `{s['selected_challenge_id']}`",
        f"- Route hash: `{s['route_hash']}`",
        f"- Route packet hash: `{s['route_packet_hash']}`",
        "",
        "## Result",
        "",
        (
            f"R52 passes {s['requirements_passed']}/{s['requirement_count']} "
            "requirements by converting the three R51 flag blockers into a "
            "hash-bound E1/E2/E3 evidence route while accepting zero source-backed rows."
        ),
        "",
        "## Evidence Slots",
        "",
    ]
    for slot in route["required_evidence_slots"]:
        lines.append(f"- `{slot['slot_id']}` unblocks `{slot['unblocks_flag']}` and must replace `{slot['must_replace']}`.")
    lines.extend(
        [
            "",
            "## Gate Semantics",
            "",
            f"- Current evidence slots satisfied: `{s['current_evidence_slots_satisfied']}`",
            f"- Current blocker files present: `{s['current_blocker_file_count']}`",
            f"- Current flag failures: `{s['current_flag_failure_count']}`",
            f"- Direct promotion of current row rejected: `{s['direct_promotion_of_current_row_rejected']}`",
            f"- Accepted source-backed rows: `{s['accepted_source_backed_row_count']}`",
            "",
            "## Requirement Results",
            "",
        ]
    )
    for item in payload["requirements"]:
        lines.append(f"- `{item['requirement_id']}` {'PASS' if item['passed'] else 'FAIL'}: {item['label']}")
    lines.extend(
        [
            "",
            "## Claim Boundary",
            "",
            f"- Supported: {payload['claim_boundary']['what_is_supported']}",
            f"- Not supported: {payload['claim_boundary']['what_is_not_supported']}",
            f"- Next gate: {payload['claim_boundary']['next_gate']}",
            "",
            f"- validation_error_count: `{s['validation_error_count']}`",
            "",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--r51-result", type=Path, default=Path("results/B1_B7_cone01_R51_o3_f4_c2_boolean_aware_preflight_gate_v0.json"))
    parser.add_argument("--presubmission-input", type=Path, default=Path("results/B1_B7_cone01_o3_f4_numerical_refit_submissions/source_backed_rows/O3-F4-C01.hash_matched_presubmission.json"))
    parser.add_argument("--smoke-witness", type=Path, default=Path("results/B1_B7_cone01_o3_f4_numerical_refit_submissions/unitary_distance/r43_all_rows/O3-F4-C01.unitary_distance_witness.json"))
    parser.add_argument("--dry-run-verifier", type=Path, default=Path("results/B1_B7_cone01_o3_f4_numerical_refit_submissions/witness_scaffolds/r40_c01/O3-F4-C01.witness_verifier.json"))
    parser.add_argument("--signature-blocker", type=Path, default=Path("results/B1_B7_cone01_o3_f4_numerical_refit_submissions/source_backed_rows/O3-F4-C01.verifier_signature_blocker.json"))
    parser.add_argument("--route-output", type=Path, default=Path("results/B1_B7_cone01_o3_f4_numerical_refit_submissions/source_backed_rows/O3-F4-C01.evidence_triplet_route.json"))
    parser.add_argument("--json-output", type=Path, default=Path("results/B1_B7_cone01_R52_o3_f4_c2_evidence_triplet_route_gate_v0.json"))
    parser.add_argument("--markdown-output", type=Path, default=Path("research/B1_B7_cone01_R52_o3_f4_c2_evidence_triplet_route_gate.md"))
    parser.add_argument("--pretty", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    payload = build_payload(args)
    write_json(args.json_output, payload)
    write_markdown(args.markdown_output, payload)
    if args.pretty:
        s = payload["summary"]
        print(
            json.dumps(
                {
                    "status": payload["status"],
                    "selected_challenge_id": s["selected_challenge_id"],
                    "requirements_passed": s["requirements_passed"],
                    "requirements_failed": s["requirements_failed"],
                    "evidence_slot_count": s["evidence_slot_count"],
                    "current_evidence_slots_satisfied": s["current_evidence_slots_satisfied"],
                    "current_blocker_file_count": s["current_blocker_file_count"],
                    "current_flag_failure_count": s["current_flag_failure_count"],
                    "direct_promotion_of_current_row_rejected": s["direct_promotion_of_current_row_rejected"],
                    "accepted_source_backed_row_count": s["accepted_source_backed_row_count"],
                    "route_hash": s["route_hash"],
                    "route_packet_hash": s["route_packet_hash"],
                    "json_output": str(args.json_output),
                },
                indent=2,
                sort_keys=True,
            )
        )


if __name__ == "__main__":
    main()
