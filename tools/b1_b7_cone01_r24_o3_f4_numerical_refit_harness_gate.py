#!/usr/bin/env python3
"""T-B1-004dz/T-B7-013i: R24 O3-F4 numerical refit harness gate."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import time
from pathlib import Path
from typing import Any


METHOD = "b1_b7_cone01_r24_o3_f4_numerical_refit_harness_gate_v0"
STATUS = "cone01_r24_o3_f4_numerical_refit_harness_ready_no_submission"
MODEL_STATUS = "o3_f4_refit_harness_ready_no_refit_artifact_no_reroute"
VERSION = "0.1"
TARGET_ID = "T-B1-004dz/T-B7-013i"
SOURCE_TARGET_ID = "T-B1-004dy/T-B7-013h"
CANDIDATE_ID = "NL-C02"
FAMILY_ID = "O3-F4"
HARNESS_ID = "B1-B7-cone01-R24-O3-F4-numerical-refit-harness"


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


def extract_o3_f4_family(r18: dict[str, Any]) -> dict[str, Any]:
    rows = r18["nlc02_o3_equivalence_family_registry_packet"]["family_rows"]
    for row in rows:
        if row["family_id"] == FAMILY_ID:
            return row
    raise KeyError(f"{FAMILY_ID} not found in R18 family registry")


def extract_o3_x2_falsifier(r18: dict[str, Any]) -> dict[str, Any]:
    rows = r18["nlc02_o3_equivalence_family_registry_packet"]["falsifier_rows"]
    for row in rows:
        if row["target_family"] == FAMILY_ID:
            return row
    raise KeyError(f"{FAMILY_ID} falsifier not found in R18 registry")


def build_challenge_packet(r13: dict[str, Any], r18: dict[str, Any], r23: dict[str, Any]) -> dict[str, Any]:
    domain = r13["nlc02_source_domain_binding_packet"]["canonical_domain"]
    values = domain["parameter_values"]
    indices = domain["parameter_indices"]
    perturbation_rows = []
    for row_id, scale in enumerate([0.125, -0.125, 0.25, -0.25, 0.375, -0.375, 0.5, -0.5], start=1):
        vector = []
        for offset, value in enumerate(values, start=1):
            vector.append(round(value + scale * math.sin(offset), 15))
        perturbation_rows.append(
            {
                "challenge_id": f"O3-F4-C{row_id:02d}",
                "initialization_policy": "source_domain_plus_deterministic_sine_perturbation",
                "perturbation_scale": scale,
                "parameter_indices": indices,
                "initial_values": vector,
            }
        )
    packet = {
        "challenge_packet_id": f"{HARNESS_ID}-challenge-packet",
        "source_domain_hash": r13["summary"]["domain_hash"],
        "source_registry_hash": r18["summary"]["registry_hash"],
        "source_enforced_replay_hash": r23["summary"]["replay_hash"],
        "line": domain["line"],
        "parameter_count": domain["parameter_count"],
        "parameter_indices": indices,
        "source_parameter_values": values,
        "exact_unitary_tolerance": domain["exact_tolerance"],
        "route_a_clearance_requires": [
            "same-unitary replay within exact tolerance on the bound source domain",
            "pi/4-lattice relation that is not only a numerical snap",
            "independent denominator replay against the R11/R12 leave-out rows",
            "claim-boundary denial of B7/STV/reroute/O3 closure until downstream gates pass",
        ],
        "challenge_rows": perturbation_rows,
    }
    packet["challenge_table_hash"] = stable_hash(perturbation_rows)
    packet["challenge_packet_hash"] = stable_hash(packet)
    return packet


def build_template(r13: dict[str, Any], r18: dict[str, Any], r23: dict[str, Any], challenge_packet: dict[str, Any]) -> dict[str, Any]:
    return {
        "artifact_id": "B1-B7-cone01-O3-F4-numerical-refit-<submitter>-<short-name>",
        "source_target_id": TARGET_ID,
        "family_id": FAMILY_ID,
        "candidate_id": CANDIDATE_ID,
        "source_domain_hash": r13["summary"]["domain_hash"],
        "source_registry_hash": r18["summary"]["registry_hash"],
        "source_enforced_replay_hash": r23["summary"]["replay_hash"],
        "challenge_packet_hash": challenge_packet["challenge_packet_hash"],
        "refit_objective": {
            "status": "required",
            "objective": "same_unitary_refit_with_route_a_clearance_pressure",
            "loss_terms": ["unitary_replay_error", "pi_over_four_lattice_distance", "route_a_effect"],
        },
        "unitary_replay_protocol": {
            "status": "required",
            "tolerance": challenge_packet["exact_unitary_tolerance"],
            "required_replay_cases": [row["challenge_id"] for row in challenge_packet["challenge_rows"]],
        },
        "seed_schedule": {
            "status": "required",
            "challenge_ids": [row["challenge_id"] for row in challenge_packet["challenge_rows"]],
            "external_randomness_allowed": False,
        },
        "optimizer_trace": "<required: ordered trace or proof that no accepted refit exists>",
        "equivalence_certificate": "<required: replayable same-unitary certificate or explicit rejection certificate>",
        "route_a_effect": "not_claimed|clears_route_a|does_not_clear_route_a",
        "claim_boundary": {
            "supported": "<required>",
            "not_supported": (
                "No B7 credit, STV credit, R5 reroute, O3 closure, or R1 solution may be claimed unless "
                "the O3-F4 harness, O3 closure checks, and downstream B7 ledgers pass."
            ),
            "kill_conditions": [
                "same-unitary replay fails",
                "lattice relation is numerical-only without replay",
                "optimizer trace omits challenge seeds",
                "claim boundary allows downstream credit",
            ],
        },
        "machine_check_command": "<required>",
        "expected_outputs": {
            "challenge_packet_hash": challenge_packet["challenge_packet_hash"],
            "artifact_hash": "<required after submission>",
            "checker_stdout_hash": "<required after submission>",
        },
    }


def build_acceptance_gates() -> list[dict[str, Any]]:
    return [
        {
            "gate_id": "F4-A1",
            "gate": "source_binding",
            "acceptance_rule": "artifact binds R13 domain hash, R18 registry hash, and R23 enforced replay hash",
        },
        {
            "gate_id": "F4-A2",
            "gate": "same_unitary_replay",
            "acceptance_rule": "all challenge cases replay the same local unitary within declared exact tolerance",
        },
        {
            "gate_id": "F4-A3",
            "gate": "seeded_multistart_coverage",
            "acceptance_rule": "all challenge seeds are used or explicitly rejected with a replayable certificate",
        },
        {
            "gate_id": "F4-A4",
            "gate": "route_a_effect_externalized",
            "acceptance_rule": "Route A effect is tested by the harness and is not self-asserted by the artifact",
        },
        {
            "gate_id": "F4-A5",
            "gate": "lattice_relation_not_numerical_only",
            "acceptance_rule": "pi/4 relation is supported by replayable same-unitary evidence, not a raw snap",
        },
        {
            "gate_id": "F4-A6",
            "gate": "denominator_pressure",
            "acceptance_rule": "result compares against R11/R12 leave-out residual rows under the same access model",
        },
        {
            "gate_id": "F4-A7",
            "gate": "overfit_and_leakage_guard",
            "acceptance_rule": "artifact discloses optimizer trace and forbids challenge leakage or hidden randomness",
        },
        {
            "gate_id": "F4-A8",
            "gate": "claim_boundary_polarity",
            "acceptance_rule": "claim boundary denies B7/STV/reroute/O3 closure until downstream gates pass",
        },
        {
            "gate_id": "F4-A9",
            "gate": "machine_check_hash_binding",
            "acceptance_rule": "machine command and expected outputs are present and hash-bound",
        },
    ]


def evaluate_absent_submission(acceptance_gates: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "submission_exists": False,
        "passed_gate_ids": [],
        "failed_gate_ids": [],
        "blocked_gate_ids": [row["gate_id"] for row in acceptance_gates],
        "accepted": False,
        "why": "No O3-F4 numerical refit artifact has been submitted to the harness path.",
    }


def build_payload(args: argparse.Namespace) -> dict[str, Any]:
    started = time.time()
    r13 = load_json(args.r13_binding)
    r18 = load_json(args.r18_registry)
    r23 = load_json(args.r23_enforced_replay)
    r13s = r13["summary"]
    r18s = r18["summary"]
    r23s = r23["summary"]
    o3_f4 = extract_o3_f4_family(r18)
    falsifier = extract_o3_x2_falsifier(r18)
    challenge_packet = build_challenge_packet(r13, r18, r23)
    template = build_template(r13, r18, r23, challenge_packet)
    gates = build_acceptance_gates()
    preflight = evaluate_absent_submission(gates)

    template_hash = stable_hash(template)
    gate_table_hash = stable_hash(gates)
    preflight_hash = stable_hash(preflight)

    harness_packet = {
        "harness_id": HARNESS_ID,
        "source_target_id": TARGET_ID,
        "source_r13_binding": str(args.r13_binding),
        "source_r18_registry": str(args.r18_registry),
        "source_r23_enforced_replay": str(args.r23_enforced_replay),
        "source_hashes": {
            "r13_binding_file": file_hash(args.r13_binding),
            "r18_registry_file": file_hash(args.r18_registry),
            "r23_enforced_replay_file": file_hash(args.r23_enforced_replay),
        },
        "source_domain_hash": r13s["domain_hash"],
        "source_registry_hash": r18s["registry_hash"],
        "source_enforced_replay_hash": r23s["replay_hash"],
        "source_o3_f4_family": o3_f4,
        "source_falsifier": falsifier,
        "challenge_packet_output": str(args.challenge_output),
        "template_output": str(args.template_output),
        "challenge_packet": challenge_packet,
        "template": template,
        "acceptance_gates": gates,
        "preflight_result": preflight,
        "decision": {
            "o3_f4_harness_ready": True,
            "o3_f4_template_emitted": True,
            "o3_f4_submission_exists": False,
            "o3_f4_preflight_accepted": False,
            "o3_f4_artifact_accepted": False,
            "o3_closed": False,
            "checked_negative_lemma_present": False,
            "nlc02_full_lemma_ready": False,
            "reroute_allowed": False,
            "why": (
                "R24 makes O3-F4 numerical refit submissions mechanically challengeable, but accepts no refit artifact "
                "and grants no O3, R5, or B7 credit."
            ),
        },
    }
    harness_packet["challenge_packet_hash"] = challenge_packet["challenge_packet_hash"]
    harness_packet["template_hash"] = template_hash
    harness_packet["gate_table_hash"] = gate_table_hash
    harness_packet["preflight_hash"] = preflight_hash
    harness_packet["harness_hash"] = stable_hash(harness_packet)

    requirements = [
        requirement(
            "P1",
            "R13 source domain is validation-clean and hash-bound",
            r13.get("method") == "b1_b7_cone01_r13_nlc02_source_domain_binding_gate_v0"
            and r13s.get("validation_error_count") == 0
            and bool(r13s.get("domain_hash")),
            {
                "r13_method": r13.get("method"),
                "r13_validation_error_count": r13s.get("validation_error_count"),
                "domain_hash": r13s.get("domain_hash"),
            },
        ),
        requirement(
            "P2",
            "R18 registry exposes O3-F4 as the numerical refit family",
            r18.get("method") == "b1_b7_cone01_r18_nlc02_o3_equivalence_family_registry_gate_v0"
            and r18s.get("validation_error_count") == 0
            and o3_f4["status"] == "open_needs_adversarial_refit_harness"
            and falsifier["falsifier_id"] == "O3-X2",
            {
                "r18_method": r18.get("method"),
                "r18_validation_error_count": r18s.get("validation_error_count"),
                "o3_f4_status": o3_f4["status"],
                "falsifier": falsifier,
            },
        ),
        requirement(
            "P3",
            "R23 enforced replay remains validation-clean and blocks overclaim A6",
            r23.get("method") == "b1_b7_cone01_r23_o3_f3_enforced_a6_preflight_replay_gate_v0"
            and r23s.get("validation_error_count") == 0
            and r23s.get("a6_newly_failed_for_overclaim") is True,
            {
                "r23_method": r23.get("method"),
                "r23_validation_error_count": r23s.get("validation_error_count"),
                "a6_newly_failed_for_overclaim": r23s.get("a6_newly_failed_for_overclaim"),
            },
        ),
        requirement(
            "P4",
            "Challenge packet covers all bound source parameters with deterministic seeds",
            challenge_packet["parameter_count"] == 5
            and len(challenge_packet["challenge_rows"]) == 8
            and all(row["parameter_indices"] == challenge_packet["parameter_indices"] for row in challenge_packet["challenge_rows"]),
            {
                "parameter_count": challenge_packet["parameter_count"],
                "challenge_count": len(challenge_packet["challenge_rows"]),
                "challenge_table_hash": challenge_packet["challenge_table_hash"],
            },
        ),
        requirement(
            "P5",
            "Template binds domain, registry, enforced replay, and challenge packet hashes",
            template["source_domain_hash"] == r13s["domain_hash"]
            and template["source_registry_hash"] == r18s["registry_hash"]
            and template["source_enforced_replay_hash"] == r23s["replay_hash"]
            and template["challenge_packet_hash"] == challenge_packet["challenge_packet_hash"],
            {
                "template_hash": template_hash,
                "source_domain_hash": template["source_domain_hash"],
                "source_registry_hash": template["source_registry_hash"],
                "source_enforced_replay_hash": template["source_enforced_replay_hash"],
                "challenge_packet_hash": template["challenge_packet_hash"],
            },
        ),
        requirement(
            "P6",
            "Acceptance gates cover replay, seed coverage, Route A, denominator, leakage, claim, and hash binding",
            len(gates) == 9 and [row["gate_id"] for row in gates] == [f"F4-A{i}" for i in range(1, 10)],
            {"gate_table_hash": gate_table_hash, "gate_ids": [row["gate_id"] for row in gates]},
        ),
        requirement(
            "P7",
            "Absent O3-F4 submission is blocked without accepting a refit",
            preflight["submission_exists"] is False
            and preflight["accepted"] is False
            and len(preflight["blocked_gate_ids"]) == 9,
            preflight,
        ),
        requirement(
            "P8",
            "R24 does not close O3, accept O3-F4, or permit reroute",
            harness_packet["decision"]["o3_f4_artifact_accepted"] is False
            and harness_packet["decision"]["o3_closed"] is False
            and harness_packet["decision"]["reroute_allowed"] is False,
            harness_packet["decision"],
        ),
        requirement(
            "P9",
            "R24 preserves zero B7/resource credit claims",
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
            "P10",
            "Harness packet is internally hash-bound",
            bool(harness_packet["harness_hash"])
            and bool(harness_packet["challenge_packet_hash"])
            and bool(harness_packet["template_hash"])
            and bool(harness_packet["gate_table_hash"])
            and bool(harness_packet["preflight_hash"]),
            {
                "harness_hash": harness_packet["harness_hash"],
                "challenge_packet_hash": harness_packet["challenge_packet_hash"],
                "template_hash": harness_packet["template_hash"],
                "gate_table_hash": harness_packet["gate_table_hash"],
                "preflight_hash": harness_packet["preflight_hash"],
            },
        ),
    ]

    passed = sum(row["passed"] for row in requirements)
    failed_ids = [row["requirement_id"] for row in requirements if not row["passed"]]
    validation_errors: list[str] = []
    if failed_ids:
        validation_errors.append(f"unexpected R24 O3-F4 harness failures: {failed_ids}")

    summary = {
        "harness_id": HARNESS_ID,
        "harness_hash": harness_packet["harness_hash"],
        "challenge_packet_hash": harness_packet["challenge_packet_hash"],
        "challenge_table_hash": challenge_packet["challenge_table_hash"],
        "template_hash": template_hash,
        "gate_table_hash": gate_table_hash,
        "preflight_hash": preflight_hash,
        "source_domain_hash": r13s["domain_hash"],
        "source_registry_hash": r18s["registry_hash"],
        "source_enforced_replay_hash": r23s["replay_hash"],
        "candidate_id": CANDIDATE_ID,
        "family_id": FAMILY_ID,
        "challenge_count": len(challenge_packet["challenge_rows"]),
        "acceptance_gate_count": len(gates),
        "o3_f4_harness_ready": True,
        "o3_f4_template_emitted": True,
        "o3_f4_submission_exists": False,
        "o3_f4_preflight_accepted": False,
        "o3_f4_artifact_accepted": False,
        "o3_closed": False,
        "remaining_open_obligations": ["O3-F3_symbolic_lu_artifact", "O3-F4_refit_artifact", "O3-F5_route_a_artifact"],
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
        "title": "B1/B7 Cone01 R24 O3-F4 Numerical Refit Harness Gate",
        "version": VERSION,
        "last_updated": args.last_updated,
        "method": METHOD,
        "status": STATUS,
        "model_status": MODEL_STATUS,
        "summary": summary,
        "o3_f4_numerical_refit_harness_packet": harness_packet,
        "requirements": requirements,
        "claim_boundary": {
            "what_is_supported": (
                "R24 defines a hash-bound O3-F4 numerical refit harness, challenge packet, submission template, "
                "and nine acceptance gates for future same-unitary refit artifacts."
            ),
            "what_is_not_supported": (
                "R24 does not submit or accept an O3-F4 refit artifact, does not close O3, and does not permit R5 reroute. "
                "No R1 solution, occurrence removal, proxy-T reduction, B7 credit, resource saving, or impossibility theorem is supported."
            ),
            "next_gate": (
                "Submit an O3-F4 numerical refit artifact against the challenge packet, or return to O3-F3 symbolic proof / "
                "O3-F5 Route A artifact pressure."
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
        f"- Harness hash: `{s['harness_hash']}`",
        f"- Challenge packet hash: `{s['challenge_packet_hash']}`",
        f"- Template hash: `{s['template_hash']}`",
        f"- Gate table hash: `{s['gate_table_hash']}`",
        f"- Preflight hash: `{s['preflight_hash']}`",
        "",
        "## Result",
        "",
        (
            f"R24 passes {s['requirements_passed']}/{s['requirement_count']} requirements. It turns O3-F4 from an open label "
            "in the R18 registry into a hash-bound numerical refit harness with deterministic challenge rows and acceptance gates."
        ),
        "",
        "## What Changed",
        "",
        "- O3-F4 now has a concrete submission template.",
        "- The challenge packet covers all five R13-bound line-1381 source parameters across 8 deterministic starts.",
        "- Acceptance requires same-unitary replay, seed coverage, denominator pressure, leakage guard, claim-boundary denial, and hash binding.",
        "- No O3-F4 artifact is submitted or accepted; B7 credit remains 0.",
        "",
        "## Harness Surface",
        "",
        f"- Challenge count: `{s['challenge_count']}`",
        f"- Acceptance gate count: `{s['acceptance_gate_count']}`",
        f"- O3-F4 template emitted: `{s['o3_f4_template_emitted']}`",
        f"- O3-F4 preflight accepted: `{s['o3_f4_preflight_accepted']}`",
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
            "This harness gate does not claim resource saving, occurrence removal, proxy-T reduction, B7 ledger improvement, FT resource credit, a checked impossibility theorem, an R5 reroute, or a solved B1/B7 problem.",
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
        "--r13-binding",
        type=Path,
        default=Path("results/B1_B7_cone01_R13_nlc02_source_domain_binding_gate_v0.json"),
    )
    parser.add_argument(
        "--r18-registry",
        type=Path,
        default=Path("results/B1_B7_cone01_R18_nlc02_o3_equivalence_family_registry_gate_v0.json"),
    )
    parser.add_argument(
        "--r23-enforced-replay",
        type=Path,
        default=Path("results/B1_B7_cone01_R23_o3_f3_enforced_a6_preflight_replay_gate_v0.json"),
    )
    parser.add_argument(
        "--challenge-output",
        type=Path,
        default=Path("results/B1_B7_cone01_o3_f4_numerical_refit_submissions/B1-B7-cone01-O3-F4-challenge-packet.json"),
    )
    parser.add_argument(
        "--template-output",
        type=Path,
        default=Path("results/B1_B7_cone01_o3_f4_numerical_refit_submissions/B1-B7-cone01-O3-F4-refit.template.json"),
    )
    parser.add_argument(
        "--json-output",
        type=Path,
        default=Path("results/B1_B7_cone01_R24_o3_f4_numerical_refit_harness_gate_v0.json"),
    )
    parser.add_argument(
        "--markdown-output",
        type=Path,
        default=Path("research/B1_B7_cone01_R24_o3_f4_numerical_refit_harness_gate.md"),
    )
    parser.add_argument("--last-updated", default="2026-07-08")
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()

    payload = build_payload(args)
    write_json(args.challenge_output, payload["o3_f4_numerical_refit_harness_packet"]["challenge_packet"], args.pretty)
    write_json(args.template_output, payload["o3_f4_numerical_refit_harness_packet"]["template"], args.pretty)
    write_json(args.json_output, payload, args.pretty)
    args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_output.write_text(render_markdown(payload), encoding="utf-8")
    print(
        json.dumps(
            {
                "status": payload["status"],
                "harness_hash": payload["summary"]["harness_hash"],
                "challenge_packet_hash": payload["summary"]["challenge_packet_hash"],
                "template_hash": payload["summary"]["template_hash"],
                "gate_table_hash": payload["summary"]["gate_table_hash"],
                "preflight_hash": payload["summary"]["preflight_hash"],
                "challenge_count": payload["summary"]["challenge_count"],
                "acceptance_gate_count": payload["summary"]["acceptance_gate_count"],
                "o3_f4_artifact_accepted": payload["summary"]["o3_f4_artifact_accepted"],
                "o3_closed": payload["summary"]["o3_closed"],
                "reroute_allowed": payload["summary"]["reroute_allowed"],
                "requirements_passed": payload["summary"]["requirements_passed"],
                "requirements_failed": payload["summary"]["requirements_failed"],
                "validation_error_count": payload["summary"]["validation_error_count"],
                "challenge_output": str(args.challenge_output),
                "template_output": str(args.template_output),
                "json_output": str(args.json_output),
                "markdown_output": str(args.markdown_output),
            },
            indent=2,
            sort_keys=True,
        )
    )
    if payload["validation_errors"]:
        raise SystemExit("B1/B7 R24 O3-F4 numerical refit harness gate validation failed")


if __name__ == "__main__":
    main()
