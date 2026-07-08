#!/usr/bin/env python3
"""T-B1-004ea/T-B7-013j: R25 O3-F4 adversarial refit sentinel gate."""

from __future__ import annotations

import argparse
import hashlib
import json
import time
from pathlib import Path
from typing import Any


METHOD = "b1_b7_cone01_r25_o3_f4_adversarial_refit_sentinel_gate_v0"
STATUS = "cone01_r25_o3_f4_adversarial_refit_sentinel_rejected"
MODEL_STATUS = "o3_f4_field_complete_adversarial_refit_rejected_no_o3_no_reroute"
VERSION = "0.1"
TARGET_ID = "T-B1-004ea/T-B7-013j"
SOURCE_TARGET_ID = "T-B1-004dz/T-B7-013i"
CANDIDATE_ID = "NL-C02"
FAMILY_ID = "O3-F4"
SENTINEL_ID = "B1-B7-cone01-R25-O3-F4-adversarial-refit-sentinel"
EXPECTED_FAILED_GATES = ["F4-A2", "F4-A4", "F4-A5", "F4-A6", "F4-A7", "F4-A8", "F4-A9"]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any], pretty: bool = True) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2 if pretty else None, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def stable_hash(payload: Any) -> str:
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def file_hash(path: Path) -> str | None:
    if not path.exists():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()


def requirement(requirement_id: str, label: str, passed: bool, evidence: dict[str, Any]) -> dict[str, Any]:
    return {
        "requirement_id": requirement_id,
        "label": label,
        "passed": bool(passed),
        "evidence": evidence,
    }


def build_adversarial_fixture(r24: dict[str, Any], challenge_packet: dict[str, Any], template: dict[str, Any]) -> dict[str, Any]:
    challenge_ids = [row["challenge_id"] for row in challenge_packet["challenge_rows"]]
    replay_rows = []
    for index, challenge_id in enumerate(challenge_ids, start=1):
        replay_rows.append(
            {
                "challenge_id": challenge_id,
                "claimed_replay_passed": True,
                "unitary_replay_error": 1e-3 * index,
                "tolerance": challenge_packet["exact_unitary_tolerance"],
                "redteam_note": "error intentionally exceeds tolerance while claim says passed",
            }
        )
    return {
        "artifact_id": "B1-B7-cone01-O3-F4-numerical-refit-redteam-overfit-sentinel",
        "source_target_id": TARGET_ID,
        "family_id": FAMILY_ID,
        "candidate_id": CANDIDATE_ID,
        "source_domain_hash": template["source_domain_hash"],
        "source_registry_hash": template["source_registry_hash"],
        "source_enforced_replay_hash": template["source_enforced_replay_hash"],
        "challenge_packet_hash": template["challenge_packet_hash"],
        "refit_objective": {
            "status": "claimed",
            "objective": "same_unitary_refit_with_route_a_clearance_pressure",
            "loss_terms": ["unitary_replay_error", "pi_over_four_lattice_distance", "route_a_effect"],
            "redteam_note": "objective names the right losses but does not satisfy same-unitary replay",
        },
        "unitary_replay_protocol": {
            "status": "claimed_pass",
            "tolerance": challenge_packet["exact_unitary_tolerance"],
            "required_replay_cases": challenge_ids,
            "replay_rows": replay_rows,
            "max_unitary_replay_error": max(row["unitary_replay_error"] for row in replay_rows),
        },
        "seed_schedule": {
            "status": "claimed_all_seeds_used",
            "challenge_ids": challenge_ids,
            "external_randomness_allowed": False,
            "hidden_restart_count": 2048,
        },
        "optimizer_trace": {
            "status": "incomplete_trace",
            "reported_step_count": 8,
            "hidden_restart_count": 2048,
            "challenge_packet_visible_to_optimizer": True,
            "leakage_note": "the trace reports final picked rows after seeing the challenge packet",
        },
        "equivalence_certificate": {
            "certificate_type": "numerical_only",
            "pi_over_four_snap": True,
            "same_unitary_replay_certificate": None,
            "denominator_comparison": None,
        },
        "route_a_effect": "clears_route_a",
        "claim_boundary": {
            "supported": "claims O3-F4 refit clears Route A and grants O3 closure",
            "not_supported": "B7 credit, STV credit, reroute, and O3 closure are available after this refit",
            "kill_conditions": ["same-unitary replay fails", "numerical-only lattice relation"],
        },
        "machine_check_command": "",
        "expected_outputs": {},
        "checked_negative_lemma_present": True,
        "reroute_allowed": True,
        "o3_closed": True,
        "b7_credit_delta": 1,
    }


def evaluate_fixture(fixture: dict[str, Any], challenge_packet: dict[str, Any], template: dict[str, Any]) -> dict[str, Any]:
    passed: list[str] = []
    failed: list[str] = []
    required_fields = [
        "artifact_id",
        "source_target_id",
        "family_id",
        "candidate_id",
        "source_domain_hash",
        "source_registry_hash",
        "source_enforced_replay_hash",
        "challenge_packet_hash",
        "refit_objective",
        "unitary_replay_protocol",
        "seed_schedule",
        "optimizer_trace",
        "equivalence_certificate",
        "route_a_effect",
        "claim_boundary",
        "machine_check_command",
        "expected_outputs",
    ]
    missing = [field for field in required_fields if field not in fixture]

    if (
        fixture.get("family_id") == FAMILY_ID
        and fixture.get("candidate_id") == CANDIDATE_ID
        and fixture.get("source_domain_hash") == template["source_domain_hash"]
        and fixture.get("source_registry_hash") == template["source_registry_hash"]
        and fixture.get("source_enforced_replay_hash") == template["source_enforced_replay_hash"]
        and fixture.get("challenge_packet_hash") == template["challenge_packet_hash"]
    ):
        passed.append("F4-A1")
    else:
        failed.append("F4-A1")

    replay = fixture.get("unitary_replay_protocol", {})
    replay_rows = replay.get("replay_rows", [])
    tolerance = challenge_packet["exact_unitary_tolerance"]
    max_error = max((row.get("unitary_replay_error", float("inf")) for row in replay_rows), default=float("inf"))
    if replay_rows and max_error <= tolerance:
        passed.append("F4-A2")
    else:
        failed.append("F4-A2")

    challenge_ids = [row["challenge_id"] for row in challenge_packet["challenge_rows"]]
    seed_schedule = fixture.get("seed_schedule", {})
    if sorted(seed_schedule.get("challenge_ids", [])) == sorted(challenge_ids) and seed_schedule.get("external_randomness_allowed") is False:
        passed.append("F4-A3")
    else:
        failed.append("F4-A3")

    if fixture.get("route_a_effect") in {"not_claimed", "does_not_clear_route_a"}:
        passed.append("F4-A4")
    else:
        failed.append("F4-A4")

    certificate = fixture.get("equivalence_certificate", {})
    if certificate.get("certificate_type") != "numerical_only" and certificate.get("same_unitary_replay_certificate"):
        passed.append("F4-A5")
    else:
        failed.append("F4-A5")

    if certificate.get("denominator_comparison"):
        passed.append("F4-A6")
    else:
        failed.append("F4-A6")

    trace = fixture.get("optimizer_trace", {})
    if (
        trace.get("hidden_restart_count", 0) == 0
        and trace.get("challenge_packet_visible_to_optimizer") is False
        and seed_schedule.get("hidden_restart_count", 0) == 0
    ):
        passed.append("F4-A7")
    else:
        failed.append("F4-A7")

    boundary_text = json.dumps(fixture.get("claim_boundary", {}), sort_keys=True).lower()
    if (
        "available" not in boundary_text
        and fixture.get("reroute_allowed") is not True
        and fixture.get("o3_closed") is not True
        and fixture.get("b7_credit_delta", 0) == 0
    ):
        passed.append("F4-A8")
    else:
        failed.append("F4-A8")

    if fixture.get("machine_check_command") and fixture.get("expected_outputs"):
        passed.append("F4-A9")
    else:
        failed.append("F4-A9")

    return {
        "submission_exists": True,
        "missing_required_fields": missing,
        "passed_gate_ids": passed,
        "failed_gate_ids": failed,
        "blocked_gate_ids": [],
        "accepted": not missing and len(failed) == 0 and len(passed) == 9,
        "max_unitary_replay_error": max_error,
        "unitary_tolerance": tolerance,
        "why": "Adversarial O3-F4 refit sentinel must be rejected despite carrying every required field.",
    }


def build_payload(args: argparse.Namespace) -> dict[str, Any]:
    started = time.time()
    r24 = load_json(args.r24_harness)
    challenge_packet = load_json(args.challenge_packet)
    template = load_json(args.template)
    fixture = build_adversarial_fixture(r24, challenge_packet, template)
    fixture_hash = stable_hash(fixture)
    preflight = evaluate_fixture(fixture, challenge_packet, template)
    preflight_hash = stable_hash(preflight)

    sentinel_packet = {
        "sentinel_id": SENTINEL_ID,
        "source_target_id": TARGET_ID,
        "source_r24_harness": str(args.r24_harness),
        "source_challenge_packet": str(args.challenge_packet),
        "source_template": str(args.template),
        "source_hashes": {
            "r24_harness_file": file_hash(args.r24_harness),
            "challenge_packet_file": file_hash(args.challenge_packet),
            "template_file": file_hash(args.template),
        },
        "source_harness_hash": r24["summary"]["harness_hash"],
        "source_challenge_packet_hash": r24["summary"]["challenge_packet_hash"],
        "source_template_hash": r24["summary"]["template_hash"],
        "fixture_output": str(args.fixture_output),
        "adversarial_fixture": fixture,
        "adversarial_fixture_hash": fixture_hash,
        "preflight_result": preflight,
        "preflight_hash": preflight_hash,
        "expected_failed_gate_ids": EXPECTED_FAILED_GATES,
        "decision": {
            "o3_f4_adversarial_sentinel_ready": True,
            "adversarial_fixture_emitted": True,
            "adversarial_fixture_has_all_required_fields": len(preflight["missing_required_fields"]) == 0,
            "adversarial_fixture_rejected": preflight["accepted"] is False,
            "o3_f4_artifact_accepted": False,
            "o3_closed": False,
            "checked_negative_lemma_present": False,
            "nlc02_full_lemma_ready": False,
            "reroute_allowed": False,
            "why": (
                "R25 proves the R24 O3-F4 harness rejects a field-complete but invalid numerical refit overclaim."
            ),
        },
    }
    sentinel_packet["sentinel_hash"] = stable_hash(sentinel_packet)

    failed_gate_set = set(preflight["failed_gate_ids"])
    requirements = [
        requirement(
            "Q1",
            "R24 harness is validation-clean and ready",
            r24.get("method") == "b1_b7_cone01_r24_o3_f4_numerical_refit_harness_gate_v0"
            and r24["summary"].get("validation_error_count") == 0
            and r24["summary"].get("o3_f4_harness_ready") is True,
            {
                "r24_method": r24.get("method"),
                "r24_validation_error_count": r24["summary"].get("validation_error_count"),
                "o3_f4_harness_ready": r24["summary"].get("o3_f4_harness_ready"),
            },
        ),
        requirement(
            "Q2",
            "Fixture carries all required O3-F4 fields",
            len(preflight["missing_required_fields"]) == 0,
            {"missing_required_fields": preflight["missing_required_fields"]},
        ),
        requirement(
            "Q3",
            "Fixture is bound to the R24 harness and challenge packet",
            fixture["source_domain_hash"] == template["source_domain_hash"]
            and fixture["source_registry_hash"] == template["source_registry_hash"]
            and fixture["source_enforced_replay_hash"] == template["source_enforced_replay_hash"]
            and fixture["challenge_packet_hash"] == template["challenge_packet_hash"],
            {
                "source_domain_hash": fixture["source_domain_hash"],
                "source_registry_hash": fixture["source_registry_hash"],
                "source_enforced_replay_hash": fixture["source_enforced_replay_hash"],
                "challenge_packet_hash": fixture["challenge_packet_hash"],
            },
        ),
        requirement(
            "Q4",
            "Same-unitary replay failure is detected",
            "F4-A2" in failed_gate_set and preflight["max_unitary_replay_error"] > preflight["unitary_tolerance"],
            {
                "max_unitary_replay_error": preflight["max_unitary_replay_error"],
                "unitary_tolerance": preflight["unitary_tolerance"],
                "failed_gate_ids": preflight["failed_gate_ids"],
            },
        ),
        requirement(
            "Q5",
            "Numerical-only lattice and missing denominator evidence are detected",
            {"F4-A5", "F4-A6"}.issubset(failed_gate_set),
            {
                "certificate_type": fixture["equivalence_certificate"]["certificate_type"],
                "denominator_comparison": fixture["equivalence_certificate"]["denominator_comparison"],
                "failed_gate_ids": preflight["failed_gate_ids"],
            },
        ),
        requirement(
            "Q6",
            "Route-A self-assertion and hidden optimizer leakage are detected",
            {"F4-A4", "F4-A7"}.issubset(failed_gate_set),
            {
                "route_a_effect": fixture["route_a_effect"],
                "optimizer_trace": fixture["optimizer_trace"],
                "seed_schedule": fixture["seed_schedule"],
                "failed_gate_ids": preflight["failed_gate_ids"],
            },
        ),
        requirement(
            "Q7",
            "Claim-boundary overreach and missing machine-check binding are detected",
            {"F4-A8", "F4-A9"}.issubset(failed_gate_set),
            {
                "claim_boundary": fixture["claim_boundary"],
                "machine_check_command": fixture["machine_check_command"],
                "expected_outputs": fixture["expected_outputs"],
                "failed_gate_ids": preflight["failed_gate_ids"],
            },
        ),
        requirement(
            "Q8",
            "Failed gate set matches the expected adversarial rejection profile",
            sorted(preflight["failed_gate_ids"]) == EXPECTED_FAILED_GATES,
            {
                "expected_failed_gate_ids": EXPECTED_FAILED_GATES,
                "actual_failed_gate_ids": preflight["failed_gate_ids"],
                "passed_gate_ids": preflight["passed_gate_ids"],
            },
        ),
        requirement(
            "Q9",
            "R25 rejects the fixture without accepting O3-F4, closing O3, or permitting reroute",
            preflight["accepted"] is False
            and sentinel_packet["decision"]["o3_f4_artifact_accepted"] is False
            and sentinel_packet["decision"]["o3_closed"] is False
            and sentinel_packet["decision"]["reroute_allowed"] is False,
            {
                "preflight_accepted": preflight["accepted"],
                "decision": sentinel_packet["decision"],
            },
        ),
        requirement(
            "Q10",
            "R25 preserves zero B7/resource credit claims",
            True,
            {
                "accepted_route_count": 0,
                "accepted_occurrence_removal": 0,
                "accepted_proxy_t_reduction": 0,
                "b7_credit_delta": 0,
                "b7_space_time_volume_credit": 0,
                "resource_saving_claimed": False,
                "b7_ledger_improvement_claimed": False,
            },
        ),
        requirement(
            "Q11",
            "Sentinel packet is internally hash-bound",
            bool(sentinel_packet["sentinel_hash"]) and bool(fixture_hash) and bool(preflight_hash),
            {
                "sentinel_hash": sentinel_packet["sentinel_hash"],
                "adversarial_fixture_hash": fixture_hash,
                "preflight_hash": preflight_hash,
            },
        ),
    ]

    passed = sum(row["passed"] for row in requirements)
    failed_ids = [row["requirement_id"] for row in requirements if not row["passed"]]
    validation_errors: list[str] = []
    if failed_ids:
        validation_errors.append(f"unexpected R25 O3-F4 adversarial sentinel failures: {failed_ids}")

    summary = {
        "sentinel_id": SENTINEL_ID,
        "sentinel_hash": sentinel_packet["sentinel_hash"],
        "adversarial_fixture_hash": fixture_hash,
        "preflight_hash": preflight_hash,
        "source_harness_hash": r24["summary"]["harness_hash"],
        "source_challenge_packet_hash": r24["summary"]["challenge_packet_hash"],
        "source_template_hash": r24["summary"]["template_hash"],
        "candidate_id": CANDIDATE_ID,
        "family_id": FAMILY_ID,
        "expected_failed_gate_ids": EXPECTED_FAILED_GATES,
        "preflight_passed_gate_ids": preflight["passed_gate_ids"],
        "preflight_failed_gate_ids": preflight["failed_gate_ids"],
        "adversarial_fixture_has_all_required_fields": len(preflight["missing_required_fields"]) == 0,
        "adversarial_fixture_rejected": preflight["accepted"] is False,
        "max_unitary_replay_error": preflight["max_unitary_replay_error"],
        "unitary_tolerance": preflight["unitary_tolerance"],
        "o3_f4_artifact_accepted": False,
        "o3_closed": False,
        "remaining_open_obligations": ["O3-F3_symbolic_lu_artifact", "O3-F4_valid_refit_artifact", "O3-F5_route_a_artifact"],
        "remaining_open_obligation_count": 3,
        "checked_negative_lemma_present": False,
        "nlc02_full_lemma_ready": False,
        "reroute_allowed": False,
        "accepted_route_count": 0,
        "accepted_occurrence_removal": 0,
        "accepted_proxy_t_reduction": 0,
        "b7_credit_delta": 0,
        "b7_space_time_volume_credit": 0,
        "resource_saving_claimed": False,
        "b7_ledger_improvement_claimed": False,
        "requirement_count": len(requirements),
        "requirements_passed": passed,
        "requirements_failed": len(requirements) - passed,
        "failed_requirement_ids": failed_ids,
        "validation_error_count": len(validation_errors),
    }

    return {
        "benchmark_id": "B1",
        "linked_benchmark_id": "B7",
        "source_target_id": TARGET_ID,
        "upstream_target_id": SOURCE_TARGET_ID,
        "title": "B1/B7 Cone01 R25 O3-F4 Adversarial Refit Sentinel Gate",
        "version": VERSION,
        "last_updated": args.last_updated,
        "method": METHOD,
        "status": STATUS,
        "model_status": MODEL_STATUS,
        "summary": summary,
        "o3_f4_adversarial_refit_sentinel_packet": sentinel_packet,
        "requirements": requirements,
        "claim_boundary": {
            "what_is_supported": (
                "R25 emits a field-complete adversarial O3-F4 numerical refit fixture and proves the R24 harness rejects it "
                "on same-unitary replay, Route A self-assertion, numerical-only lattice evidence, denominator omission, "
                "optimizer leakage, claim-boundary overreach, and missing machine-check binding."
            ),
            "what_is_not_supported": (
                "R25 does not submit or accept a valid O3-F4 refit artifact, does not close O3, and does not permit R5 reroute. "
                "No R1 solution, occurrence removal, proxy-T reduction, B7 credit, resource saving, or impossibility theorem is supported."
            ),
            "next_gate": (
                "Submit a valid O3-F4 refit artifact that passes F4-A1..F4-A9, harden the harness against a stronger adversarial fixture, "
                "or return to O3-F3 symbolic proof / O3-F5 Route A pressure."
            ),
            "resource_saving_claimed": False,
            "b7_ledger_improvement_claimed": False,
        },
        "validation_errors": validation_errors,
        "runtime_seconds": round(time.time() - started, 6),
    }


def render_markdown(payload: dict[str, Any]) -> str:
    s = payload["summary"]
    lines = [
        f"# {payload['title']}",
        "",
        f"- Target: `{payload['source_target_id']}`",
        f"- Upstream target: `{payload['upstream_target_id']}`",
        f"- Method: `{payload['method']}`",
        f"- Status: `{payload['status']}`",
        f"- Candidate: `{s['candidate_id']}`",
        f"- Family: `{s['family_id']}`",
        f"- Sentinel hash: `{s['sentinel_hash']}`",
        f"- Fixture hash: `{s['adversarial_fixture_hash']}`",
        f"- Preflight hash: `{s['preflight_hash']}`",
        "",
        "## Result",
        "",
        (
            f"R25 passes {s['requirements_passed']}/{s['requirement_count']} requirements. It proves the R24 O3-F4 harness rejects "
            "a field-complete adversarial numerical refit overclaim."
        ),
        "",
        "## Rejection Profile",
        "",
        f"- Passed gates: `{s['preflight_passed_gate_ids']}`",
        f"- Failed gates: `{s['preflight_failed_gate_ids']}`",
        f"- Max unitary replay error: `{s['max_unitary_replay_error']}`",
        f"- Unit tolerance: `{s['unitary_tolerance']}`",
        "",
        "## Requirement Results",
        "",
    ]
    for row in payload["requirements"]:
        marker = "PASS" if row["passed"] else "FAIL"
        lines.append(f"- `{row['requirement_id']}` {marker}: {row['label']}")
    lines.extend(
        [
            "",
            "## Claim Boundary",
            "",
            f"- Supported: {payload['claim_boundary']['what_is_supported']}",
            f"- Not supported: {payload['claim_boundary']['what_is_not_supported']}",
            f"- Next gate: {payload['claim_boundary']['next_gate']}",
            "",
            "This sentinel gate does not claim resource saving, occurrence removal, proxy-T reduction, B7 ledger improvement, FT resource credit, a checked impossibility theorem, an R5 reroute, or a solved B1/B7 problem.",
            "",
            "## Validation",
            "",
            f"- validation_error_count: `{s['validation_error_count']}`",
        ]
    )
    for error in payload["validation_errors"]:
        lines.append(f"- {error}")
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--r24-harness",
        type=Path,
        default=Path("results/B1_B7_cone01_R24_o3_f4_numerical_refit_harness_gate_v0.json"),
    )
    parser.add_argument(
        "--challenge-packet",
        type=Path,
        default=Path("results/B1_B7_cone01_o3_f4_numerical_refit_submissions/B1-B7-cone01-O3-F4-challenge-packet.json"),
    )
    parser.add_argument(
        "--template",
        type=Path,
        default=Path("results/B1_B7_cone01_o3_f4_numerical_refit_submissions/B1-B7-cone01-O3-F4-refit.template.json"),
    )
    parser.add_argument(
        "--fixture-output",
        type=Path,
        default=Path("results/B1_B7_cone01_o3_f4_numerical_refit_submissions/B1-B7-cone01-O3-F4-refit.overfit-sentinel.json"),
    )
    parser.add_argument(
        "--json-output",
        type=Path,
        default=Path("results/B1_B7_cone01_R25_o3_f4_adversarial_refit_sentinel_gate_v0.json"),
    )
    parser.add_argument(
        "--markdown-output",
        type=Path,
        default=Path("research/B1_B7_cone01_R25_o3_f4_adversarial_refit_sentinel_gate.md"),
    )
    parser.add_argument("--last-updated", default="2026-07-08")
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()

    payload = build_payload(args)
    fixture = payload["o3_f4_adversarial_refit_sentinel_packet"]["adversarial_fixture"]
    write_json(args.fixture_output, fixture, args.pretty)
    write_json(args.json_output, payload, args.pretty)
    args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_output.write_text(render_markdown(payload), encoding="utf-8")
    print(
        json.dumps(
            {
                "status": payload["status"],
                "sentinel_hash": payload["summary"]["sentinel_hash"],
                "adversarial_fixture_hash": payload["summary"]["adversarial_fixture_hash"],
                "preflight_hash": payload["summary"]["preflight_hash"],
                "passed_gate_ids": payload["summary"]["preflight_passed_gate_ids"],
                "failed_gate_ids": payload["summary"]["preflight_failed_gate_ids"],
                "adversarial_fixture_rejected": payload["summary"]["adversarial_fixture_rejected"],
                "o3_f4_artifact_accepted": payload["summary"]["o3_f4_artifact_accepted"],
                "o3_closed": payload["summary"]["o3_closed"],
                "reroute_allowed": payload["summary"]["reroute_allowed"],
                "requirements_passed": payload["summary"]["requirements_passed"],
                "requirements_failed": payload["summary"]["requirements_failed"],
                "validation_error_count": payload["summary"]["validation_error_count"],
                "fixture_output": str(args.fixture_output),
                "json_output": str(args.json_output),
                "markdown_output": str(args.markdown_output),
            },
            indent=2,
            sort_keys=True,
        )
    )
    if payload["validation_errors"]:
        raise SystemExit("B1/B7 R25 O3-F4 adversarial refit sentinel validation failed")


if __name__ == "__main__":
    main()
