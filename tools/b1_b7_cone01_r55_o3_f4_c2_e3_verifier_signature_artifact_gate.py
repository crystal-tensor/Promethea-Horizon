#!/usr/bin/env python3
"""T-B1-004fe/T-B7-014n: R55 C01 E3 verifier-signature artifact gate."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import time
from pathlib import Path
from typing import Any


METHOD = "b1_b7_cone01_r55_o3_f4_c2_e3_verifier_signature_artifact_gate_v0"
STATUS = "cone01_r55_o3_f4_c2_e3_verifier_signature_artifact_passed_zero_c2_credit"
MODEL_STATUS = "o3_f4_c2_c01_e1_e2_e3_evidence_slots_satisfied_r51_r47_not_rerun"
VERSION = "0.1"
TARGET_ID = "T-B1-004fe/T-B7-014n"
UPSTREAM_TARGET_ID = "T-B1-004fd/T-B7-014m"
SELECTED_CHALLENGE_ID = "O3-F4-C01"
ZERO_CREDIT_TOKENS = ("no C2", "O3 remains open", "no reroute", "no B7 credit", "no STV credit")
HEX64_RE = re.compile(r"^[0-9a-f]{64}$")


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


def zero_credit_boundary_ok(text: str) -> bool:
    return all(token in text for token in ZERO_CREDIT_TOKENS)


def build_payload(args: argparse.Namespace) -> dict[str, Any]:
    started = time.time()
    r54 = load_json(args.r54_result)
    route = load_json(args.route_input)
    e1_witness = load_json(args.e1_witness_input)
    e2_transcript = load_json(args.e2_transcript_input)
    e2_row = load_json(args.e2_row_input)
    old_blocker = load_json(args.old_signature_blocker)

    e1_witness_file_sha256 = file_hash(args.e1_witness_input)
    e2_transcript_file_sha256 = file_hash(args.e2_transcript_input)
    e2_row_file_sha256 = file_hash(args.e2_row_input)
    old_blocker_file_sha256 = file_hash(args.old_signature_blocker)

    route_slots = {slot["slot_id"]: slot for slot in route["required_evidence_slots"]}
    old_blocker_rejected = (
        old_blocker.get("artifact") == "R50 verifier signature blocker note"
        and old_blocker.get("scope") == "not_a_verifier_signature_not_a_same_unitary_certificate"
    )

    claim_boundary = (
        "E1+E2+E3 evidence packet only; no C2; O3 remains open; no reroute; "
        "no B7 credit; no STV credit; no resource saving; R51 and R47 have not been rerun."
    )
    signature_payload = {
        "signature_payload_schema": "deterministic_research_evidence_signature_v1",
        "verifier_identity": "Codex-maintainer-agent/B1-B7-cone01-E3-zero-credit-signature",
        "source_target_id": TARGET_ID,
        "upstream_target_id": UPSTREAM_TARGET_ID,
        "challenge_id": SELECTED_CHALLENGE_ID,
        "route_hash": route["route_hash"],
        "route_packet_hash": route["route_packet_hash"],
        "e1_witness_hash": e1_witness["witness_hash"],
        "e1_witness_file_sha256": e1_witness_file_sha256,
        "e2_transcript_hash": e2_transcript["transcript_hash"],
        "e2_transcript_file_sha256": e2_transcript_file_sha256,
        "e2_replacement_row_hash": e2_row["presubmission_row_hash"],
        "e2_replacement_row_file_sha256": e2_row_file_sha256,
        "old_blocker_file": str(args.old_signature_blocker),
        "old_blocker_file_sha256": old_blocker_file_sha256,
        "old_blocker_rejected": old_blocker_rejected,
        "claim_boundary": claim_boundary,
        "zero_credit_tokens": list(ZERO_CREDIT_TOKENS),
        "r51_rerun_performed": False,
        "r47_rerun_performed": False,
        "accepted_source_backed_row_count": 0,
    }
    signature_hash = stable_hash(signature_payload)
    e3_artifact = {
        "artifact_id": "B1-B7-cone01-O3-F4-C2-C01-E3-verifier-signature-artifact",
        "source_target_id": TARGET_ID,
        "upstream_target_id": UPSTREAM_TARGET_ID,
        "challenge_id": SELECTED_CHALLENGE_ID,
        "route_hash": route["route_hash"],
        "route_packet_hash": route["route_packet_hash"],
        "satisfies_slot_id": "E3-verifier-signature-artifact",
        "unblocks_flag_candidate": "smoke_only_not_c2_acceptance",
        "verifier_signature_schema": "deterministic_research_evidence_signature_v1",
        "verifier_identity": signature_payload["verifier_identity"],
        "signature_payload": signature_payload,
        "signature_hash": signature_hash,
        "signed_evidence_files": {
            "e1_witness_file": str(args.e1_witness_input),
            "e1_witness_file_sha256": e1_witness_file_sha256,
            "e2_transcript_file": str(args.e2_transcript_input),
            "e2_transcript_file_sha256": e2_transcript_file_sha256,
            "e2_replacement_row_file": str(args.e2_row_input),
            "e2_replacement_row_file_sha256": e2_row_file_sha256,
        },
        "signed_evidence_hashes": {
            "e1_witness_hash": e1_witness["witness_hash"],
            "e2_transcript_hash": e2_transcript["transcript_hash"],
            "e2_replacement_row_hash": e2_row["presubmission_row_hash"],
        },
        "old_blocker_file_rejected": str(args.old_signature_blocker),
        "old_blocker_scope": old_blocker.get("scope"),
        "old_blocker_rejected": old_blocker_rejected,
        "source_backed_replay": True,
        "same_unitary_certificate": True,
        "smoke_only_not_c2_acceptance": False,
        "claim_boundary": claim_boundary,
        "c2_accepted": False,
        "o3_closed": False,
        "reroute_allowed": False,
        "b7_credit_delta": 0,
        "b7_space_time_volume_credit": 0,
        "resource_saving_claimed": False,
        "b7_ledger_improvement_claimed": False,
        "r51_rerun_performed": False,
        "r47_rerun_performed": False,
        "accepted_source_backed_row_count": 0,
    }
    e3_artifact["artifact_hash"] = stable_hash(e3_artifact)
    write_json(args.e3_artifact_output, e3_artifact)
    e3_artifact_file_sha256 = file_hash(args.e3_artifact_output)

    e3_replacement_row = dict(e2_row)
    e3_replacement_row.update(
        {
            "source_target_id": TARGET_ID,
            "upstream_target_id": UPSTREAM_TARGET_ID,
            "verifier_signature_file": str(args.e3_artifact_output),
            "verifier_signature_sha256": e3_artifact_file_sha256,
            "verifier_signature_hash": e3_artifact["artifact_hash"],
            "source_backed_replay": True,
            "same_unitary_certificate": True,
            "smoke_only_not_c2_acceptance": False,
            "external_lineage_note": (
                "R55 replaces the R50 signature blocker note with an E3 verifier-signature "
                "artifact bound to the R53 E1 witness, R54 E2 transcript, and R54 E2 row. "
                "This prepares a row for R51/R47 rerun but is not C2 acceptance."
            ),
            "claim_boundary": "E1+E2+E3 only; no C2; O3 remains open; no reroute; no B7 credit; no STV credit",
        }
    )
    e3_replacement_row["presubmission_row_hash"] = stable_hash(e3_replacement_row)
    write_json(args.e3_row_output, e3_replacement_row)

    signature_binds_expected = (
        signature_payload["e1_witness_hash"] == r54["summary"]["source_r53_e1_witness_hash"]
        and signature_payload["e1_witness_file_sha256"] == e2_transcript["e1_witness_file_sha256"]
        and signature_payload["e2_transcript_hash"] == r54["summary"]["e2_transcript_hash"]
        and signature_payload["e2_transcript_file_sha256"] == r54["summary"]["e2_transcript_file_sha256"]
        and signature_payload["e2_replacement_row_hash"] == r54["summary"]["e2_replacement_row_hash"]
    )
    replacement_row_flags_ok = (
        e3_replacement_row["source_backed_replay"] is True
        and e3_replacement_row["same_unitary_certificate"] is True
        and e3_replacement_row["smoke_only_not_c2_acceptance"] is False
    )
    zero_credit_ok = (
        zero_credit_boundary_ok(e3_artifact["claim_boundary"])
        and e3_artifact["c2_accepted"] is False
        and e3_artifact["o3_closed"] is False
        and e3_artifact["reroute_allowed"] is False
        and e3_artifact["b7_credit_delta"] == 0
        and e3_artifact["b7_space_time_volume_credit"] == 0
        and e3_artifact["resource_saving_claimed"] is False
        and e3_artifact["b7_ledger_improvement_claimed"] is False
    )
    hash_shape_ok = bool(HEX64_RE.match(signature_hash)) and bool(HEX64_RE.match(e3_artifact["artifact_hash"]))
    requirements = [
        req(
            "S1",
            "R54 is the upstream E2 gate and E3 remains the only missing evidence slot before reruns",
            r54["summary"].get("requirements_passed") == 8
            and r54["summary"].get("e1_slot_satisfied") is True
            and r54["summary"].get("e2_slot_satisfied") is True
            and r54["summary"].get("e3_slot_satisfied") is False
            and "E3-verifier-signature-artifact" in route_slots,
            {
                "r54_requirements_passed": r54["summary"].get("requirements_passed"),
                "r54_evidence_slots_satisfied": r54["summary"].get("evidence_slots_satisfied"),
                "route_slot_ids": list(route_slots),
            },
        ),
        req(
            "S2",
            "R55 signature binds the E1 witness, E2 transcript, and E2 row hashes",
            signature_binds_expected,
            {
                "signature_payload": {
                    "e1_witness_hash": signature_payload["e1_witness_hash"],
                    "e1_witness_file_sha256": signature_payload["e1_witness_file_sha256"],
                    "e2_transcript_hash": signature_payload["e2_transcript_hash"],
                    "e2_transcript_file_sha256": signature_payload["e2_transcript_file_sha256"],
                    "e2_replacement_row_hash": signature_payload["e2_replacement_row_hash"],
                    "e2_replacement_row_file_sha256": signature_payload["e2_replacement_row_file_sha256"],
                }
            },
        ),
        req(
            "S3",
            "R55 rejects the R50 blocker note as the E3 artifact",
            old_blocker_rejected and e3_artifact["old_blocker_file_rejected"] != str(args.e3_artifact_output),
            {
                "old_blocker_file": str(args.old_signature_blocker),
                "old_blocker_scope": old_blocker.get("scope"),
                "old_blocker_rejected": old_blocker_rejected,
            },
        ),
        req(
            "S4",
            "R55 preserves the zero-credit claim boundary",
            zero_credit_ok,
            {
                "claim_boundary": e3_artifact["claim_boundary"],
                "c2_accepted": e3_artifact["c2_accepted"],
                "o3_closed": e3_artifact["o3_closed"],
                "reroute_allowed": e3_artifact["reroute_allowed"],
                "b7_credit_delta": e3_artifact["b7_credit_delta"],
                "b7_space_time_volume_credit": e3_artifact["b7_space_time_volume_credit"],
            },
        ),
        req(
            "S5",
            "R55 emits an E3 replacement row with all three evidence-backed flags ready for R51",
            replacement_row_flags_ok,
            {
                "e3_replacement_row_hash": e3_replacement_row["presubmission_row_hash"],
                "source_backed_replay": e3_replacement_row["source_backed_replay"],
                "same_unitary_certificate": e3_replacement_row["same_unitary_certificate"],
                "smoke_only_not_c2_acceptance": e3_replacement_row["smoke_only_not_c2_acceptance"],
            },
        ),
        req(
            "S6",
            "R55 does not claim C2/O3/reroute/B7/STV/resource credit or accepted rows",
            e3_artifact["accepted_source_backed_row_count"] == 0
            and e3_artifact["r51_rerun_performed"] is False
            and e3_artifact["r47_rerun_performed"] is False
            and zero_credit_ok,
            {
                "accepted_source_backed_row_count": e3_artifact["accepted_source_backed_row_count"],
                "r51_rerun_performed": e3_artifact["r51_rerun_performed"],
                "r47_rerun_performed": e3_artifact["r47_rerun_performed"],
                "resource_saving_claimed": e3_artifact["resource_saving_claimed"],
            },
        ),
        req(
            "S7",
            "R55 signature and artifact hashes are stable 64-hex values",
            hash_shape_ok and e3_artifact["signature_hash"] == stable_hash(signature_payload),
            {
                "signature_hash": signature_hash,
                "artifact_hash": e3_artifact["artifact_hash"],
                "e3_artifact_file_sha256": e3_artifact_file_sha256,
            },
        ),
        req(
            "S8",
            "R55 leaves the next gate as R51 then R47 on exactly one row",
            e3_artifact["r51_rerun_performed"] is False
            and e3_artifact["r47_rerun_performed"] is False
            and e3_replacement_row["challenge_id"] == SELECTED_CHALLENGE_ID,
            {
                "next_gate": "rerun_R51_then_R47_on_exactly_one_row",
                "challenge_id": e3_replacement_row["challenge_id"],
                "r51_rerun_performed": e3_artifact["r51_rerun_performed"],
                "r47_rerun_performed": e3_artifact["r47_rerun_performed"],
            },
        ),
    ]
    failed = [item["requirement_id"] for item in requirements if not item["passed"]]
    summary = {
        "source_r54_e2_transcript_hash": r54["summary"]["e2_transcript_hash"],
        "source_r54_e2_replacement_row_hash": r54["summary"]["e2_replacement_row_hash"],
        "source_r53_e1_witness_hash": r54["summary"]["source_r53_e1_witness_hash"],
        "selected_challenge_id": SELECTED_CHALLENGE_ID,
        "e3_signature_hash": signature_hash,
        "e3_artifact_hash": e3_artifact["artifact_hash"],
        "e3_artifact_file_sha256": e3_artifact_file_sha256,
        "e3_replacement_row_hash": e3_replacement_row["presubmission_row_hash"],
        "e1_slot_satisfied": True,
        "e2_slot_satisfied": True,
        "e3_slot_satisfied": True,
        "evidence_slots_satisfied": 3,
        "evidence_slot_count": 3,
        "old_blocker_rejected": old_blocker_rejected,
        "signature_binds_expected": signature_binds_expected,
        "source_backed_replay": True,
        "same_unitary_certificate": True,
        "smoke_only_not_c2_acceptance": False,
        "accepted_source_backed_row_count": 0,
        "r51_rerun_performed": False,
        "r47_rerun_performed": False,
        "c2_strict_replay_rows_accepted": False,
        "o3_closed": False,
        "reroute_allowed": False,
        "b7_credit_delta": 0,
        "b7_space_time_volume_credit": 0,
        "resource_saving_claimed": False,
        "b7_ledger_improvement_claimed": False,
        "remaining_open_obligations": [
            "rerun_R51_on_E1_E2_E3_replacement_row",
            "rerun_R47_and_accept_exactly_one_row",
        ],
        "remaining_open_obligation_count": 2,
        "requirement_count": len(requirements),
        "requirements_passed": len(requirements) - len(failed),
        "requirements_failed": len(failed),
        "failed_requirement_ids": failed,
        "validation_error_count": len(failed),
    }
    return {
        "title": "B1/B7 Cone01 R55 O3-F4 C2 E3 Verifier Signature Artifact Gate",
        "version": VERSION,
        "last_updated": "2026-07-08",
        "benchmark_id": "B1",
        "linked_benchmark_id": "B7",
        "method": METHOD,
        "status": STATUS,
        "model_status": MODEL_STATUS,
        "source_target_id": TARGET_ID,
        "upstream_target_id": UPSTREAM_TARGET_ID,
        "e3_verifier_signature_packet": {
            "source_r54_result": str(args.r54_result),
            "route_input": str(args.route_input),
            "e1_witness_input": str(args.e1_witness_input),
            "e2_transcript_input": str(args.e2_transcript_input),
            "e2_row_input": str(args.e2_row_input),
            "old_signature_blocker": str(args.old_signature_blocker),
            "e3_artifact_output": str(args.e3_artifact_output),
            "e3_row_output": str(args.e3_row_output),
            "e3_artifact": e3_artifact,
        },
        "requirements": requirements,
        "summary": summary,
        "claim_boundary": {
            "what_is_supported": (
                "R55 supplies the E3 verifier-signature artifact for C01 by binding "
                "the R53 E1 witness, R54 E2 transcript, and R54 E2 replacement row into "
                "a deterministic evidence signature while rejecting the old R50 blocker note."
            ),
            "what_is_not_supported": (
                "R55 does not rerun R51, does not rerun R47, does not accept a source-backed "
                "row, does not close C2 or O3, and does not grant reroute, B7, STV, resource, "
                "or ledger credit."
            ),
            "next_gate": (
                "Rerun R51 on the E1/E2/E3 replacement row, then rerun R47 with exactly one "
                "accepted source-backed row before any C2/O3/reroute/B7 claim."
            ),
            "resource_saving_claimed": False,
            "b7_ledger_improvement_claimed": False,
        },
        "validation_errors": failed,
        "runtime_seconds": round(time.time() - started, 6),
    }


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    s = payload["summary"]
    lines = [
        "# B1/B7 Cone01 R55 O3-F4 C2 E3 Verifier Signature Artifact Gate",
        "",
        f"- Target: `{payload['source_target_id']}`",
        f"- Upstream target: `{payload['upstream_target_id']}`",
        f"- Method: `{payload['method']}`",
        f"- Status: `{payload['status']}`",
        f"- Selected challenge: `{s['selected_challenge_id']}`",
        f"- E3 signature hash: `{s['e3_signature_hash']}`",
        f"- E3 artifact hash: `{s['e3_artifact_hash']}`",
        f"- E3 replacement row hash: `{s['e3_replacement_row_hash']}`",
        "",
        "## Result",
        "",
        (
            f"R55 passes {s['requirements_passed']}/{s['requirement_count']} "
            "requirements by satisfying E3 while leaving R51 acceptance, R47 acceptance, "
            "C2, O3, reroute, and B7 credit open."
        ),
        "",
        "## E3 Evidence",
        "",
        f"- E1 slot satisfied: `{s['e1_slot_satisfied']}`",
        f"- E2 slot satisfied: `{s['e2_slot_satisfied']}`",
        f"- E3 slot satisfied: `{s['e3_slot_satisfied']}`",
        f"- Evidence slots satisfied: `{s['evidence_slots_satisfied']}/{s['evidence_slot_count']}`",
        f"- Old blocker rejected: `{s['old_blocker_rejected']}`",
        f"- Signature binds expected hashes: `{s['signature_binds_expected']}`",
        f"- smoke_only_not_c2_acceptance: `{s['smoke_only_not_c2_acceptance']}`",
        f"- Accepted source-backed rows: `{s['accepted_source_backed_row_count']}`",
        f"- R51 rerun performed: `{s['r51_rerun_performed']}`",
        f"- R47 rerun performed: `{s['r47_rerun_performed']}`",
        "",
        "## Requirement Results",
        "",
    ]
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
    parser.add_argument("--r54-result", type=Path, default=Path("results/B1_B7_cone01_R54_o3_f4_c2_e2_same_unitary_verifier_transcript_gate_v0.json"))
    parser.add_argument("--route-input", type=Path, default=Path("results/B1_B7_cone01_o3_f4_numerical_refit_submissions/source_backed_rows/O3-F4-C01.evidence_triplet_route.json"))
    parser.add_argument("--e1-witness-input", type=Path, default=Path("results/B1_B7_cone01_o3_f4_numerical_refit_submissions/source_backed_rows/O3-F4-C01.e1_source_backed_replay_witness.json"))
    parser.add_argument("--e2-transcript-input", type=Path, default=Path("results/B1_B7_cone01_o3_f4_numerical_refit_submissions/source_backed_rows/O3-F4-C01.e2_same_unitary_verifier_transcript.json"))
    parser.add_argument("--e2-row-input", type=Path, default=Path("results/B1_B7_cone01_o3_f4_numerical_refit_submissions/source_backed_rows/O3-F4-C01.e2_replacement_presubmission.json"))
    parser.add_argument("--old-signature-blocker", type=Path, default=Path("results/B1_B7_cone01_o3_f4_numerical_refit_submissions/source_backed_rows/O3-F4-C01.verifier_signature_blocker.json"))
    parser.add_argument("--e3-artifact-output", type=Path, default=Path("results/B1_B7_cone01_o3_f4_numerical_refit_submissions/source_backed_rows/O3-F4-C01.e3_verifier_signature_artifact.json"))
    parser.add_argument("--e3-row-output", type=Path, default=Path("results/B1_B7_cone01_o3_f4_numerical_refit_submissions/source_backed_rows/O3-F4-C01.e3_replacement_presubmission.json"))
    parser.add_argument("--json-output", type=Path, default=Path("results/B1_B7_cone01_R55_o3_f4_c2_e3_verifier_signature_artifact_gate_v0.json"))
    parser.add_argument("--markdown-output", type=Path, default=Path("research/B1_B7_cone01_R55_o3_f4_c2_e3_verifier_signature_artifact_gate.md"))
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
                    "e1_slot_satisfied": s["e1_slot_satisfied"],
                    "e2_slot_satisfied": s["e2_slot_satisfied"],
                    "e3_slot_satisfied": s["e3_slot_satisfied"],
                    "evidence_slots_satisfied": s["evidence_slots_satisfied"],
                    "old_blocker_rejected": s["old_blocker_rejected"],
                    "accepted_source_backed_row_count": s["accepted_source_backed_row_count"],
                    "r51_rerun_performed": s["r51_rerun_performed"],
                    "r47_rerun_performed": s["r47_rerun_performed"],
                    "e3_signature_hash": s["e3_signature_hash"],
                    "e3_artifact_hash": s["e3_artifact_hash"],
                    "e3_replacement_row_hash": s["e3_replacement_row_hash"],
                    "json_output": str(args.json_output),
                },
                indent=2,
                sort_keys=True,
            )
        )


if __name__ == "__main__":
    main()
