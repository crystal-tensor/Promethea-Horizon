#!/usr/bin/env python3
"""T-B1-004gr/T-B7-016a: R94 maintainer verdict and counter contract."""

from __future__ import annotations

import argparse
import hashlib
import json
import time
from pathlib import Path
from typing import Any


METHOD = "b1_b7_cone01_r94_maintainer_verdict_counter_contract_gate_v0"
STATUS = "cone01_r94_maintainer_verdict_contract_open_no_verdict_yet"
MODEL_STATUS = "r93_nonfixture_intake_ready_but_maintainer_verdict_missing"
VERSION = "0.1"
TARGET_ID = "T-B1-004gr/T-B7-016a"
UPSTREAM_TARGET_ID = "T-B1-004gq/T-B7-015z"
SUBMISSION_DIR = "results/B1_B7_cone01_o3_f4_exit_route_submissions"

R93_RESULT = "results/B1_B7_cone01_R93_nonfixture_external_intake_gate_v0.json"
R93_INTAKE_CONTRACT = f"{SUBMISSION_DIR}/R93-G1-nonfixture-external-intake-contract.json"
R93_PACKET_TEMPLATE = f"{SUBMISSION_DIR}/R93-G1-nonfixture-external-submission-packet.template.json"
R93_PREFLIGHT = f"{SUBMISSION_DIR}/R93-G1-nonfixture-external-intake-preflight.verdict.json"
R93_BLOCKER_QUEUE = f"{SUBMISSION_DIR}/R93-G1-post-nonfixture-intake-blocker-queue.json"

R94_VERDICT_CONTRACT = f"{SUBMISSION_DIR}/R94-G1-maintainer-verdict-contract.json"
R94_VERDICT_TEMPLATE = f"{SUBMISSION_DIR}/R94-G1-maintainer-verdict.template.json"
R94_EMPTY_VERDICT = f"{SUBMISSION_DIR}/R94-G1-empty-maintainer-verdict.json"
R94_PREFLIGHT = f"{SUBMISSION_DIR}/R94-G1-maintainer-verdict-preflight.verdict.json"
R94_STDOUT = f"{SUBMISSION_DIR}/R94-G1-maintainer-verdict.stdout.txt"
R94_BLOCKER_QUEUE = f"{SUBMISSION_DIR}/R94-G1-post-verdict-blocker-queue.json"

RESULT_PATH = "results/B1_B7_cone01_R94_maintainer_verdict_counter_contract_gate_v0.json"
REPORT_PATH = "research/B1_B7_cone01_R94_maintainer_verdict_counter_contract_gate.md"

VERDICT_REQUIRED_FIELDS = [
    "verdict_id",
    "maintainer_id",
    "source_r93_packet_hash",
    "source_r93_preflight_hash",
    "reviewed_packet_path",
    "reviewed_packet_sha256",
    "review_transcript_path",
    "review_transcript_sha256",
    "review_mode",
    "evidence_sufficiency",
    "counter_target",
    "counter_delta",
    "credit_decision",
    "double_count_decision",
    "one_unit_credit_preserved",
    "one_unit_credit_revoked",
    "new_credit_delta",
    "accepted_external_reproduction_count_after",
    "accepted_external_falsification_count_after",
    "claim_boundary",
    "o3_closed",
    "resource_saving_claimed",
    "physical_layout_claimed",
    "review_timestamp_unix",
]

PRODUCTION_REQUIRED_FIELDS = [
    "verdict_id",
    "maintainer_id",
    "source_r93_packet_hash",
    "source_r93_preflight_hash",
    "reviewed_packet_path",
    "reviewed_packet_sha256",
    "review_transcript_path",
    "review_transcript_sha256",
    "review_mode",
    "evidence_sufficiency",
    "counter_target",
    "counter_delta",
    "credit_decision",
    "double_count_decision",
    "claim_boundary",
]


def stable_hash(payload: Any) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def stable_self_hash(payload: dict[str, Any], hash_key: str) -> str:
    copy = dict(payload)
    copy.pop(hash_key, None)
    return stable_hash(copy)


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def req(requirement_id: str, label: str, passed: bool, evidence: dict[str, Any]) -> dict[str, Any]:
    return {
        "requirement_id": requirement_id,
        "label": label,
        "passed": bool(passed),
        "evidence": evidence,
    }


def build_verdict_contract(
    root: Path,
    r93_result: dict[str, Any],
    r93_contract: dict[str, Any],
    r93_template: dict[str, Any],
    r93_preflight: dict[str, Any],
    r93_blocker_queue: dict[str, Any],
) -> dict[str, Any]:
    contract = {
        "artifact": "R94 G1 maintainer verdict and counter contract",
        "method": METHOD,
        "source_target_id": TARGET_ID,
        "upstream_target_id": UPSTREAM_TARGET_ID,
        "source_r93_result_path": R93_RESULT,
        "source_r93_result_sha256": file_hash(root / R93_RESULT),
        "source_r93_payload_hash": r93_result["payload_hash"],
        "source_r93_intake_contract_path": R93_INTAKE_CONTRACT,
        "source_r93_intake_contract_sha256": file_hash(root / R93_INTAKE_CONTRACT),
        "source_r93_intake_contract_hash": r93_contract["intake_contract_hash"],
        "source_r93_packet_template_path": R93_PACKET_TEMPLATE,
        "source_r93_packet_template_sha256": file_hash(root / R93_PACKET_TEMPLATE),
        "source_r93_packet_template_hash": r93_template["packet_template_hash"],
        "source_r93_preflight_path": R93_PREFLIGHT,
        "source_r93_preflight_sha256": file_hash(root / R93_PREFLIGHT),
        "source_r93_preflight_hash": r93_preflight["preflight_hash"],
        "source_r93_blocker_queue_path": R93_BLOCKER_QUEUE,
        "source_r93_blocker_queue_sha256": file_hash(root / R93_BLOCKER_QUEUE),
        "source_r93_blocker_queue_hash": r93_blocker_queue["blocker_queue_hash"],
        "contract_id": "R94-G1-maintainer-verdict-counter-contract",
        "route_id": r93_contract["route_id"],
        "required_fields": VERDICT_REQUIRED_FIELDS,
        "required_field_count": len(VERDICT_REQUIRED_FIELDS),
        "production_required_fields": PRODUCTION_REQUIRED_FIELDS,
        "production_required_field_count": len(PRODUCTION_REQUIRED_FIELDS),
        "allowed_review_modes": [
            "external_reproduction_review",
            "external_falsification_review",
            "insufficient_evidence_review",
            "new_credit_candidate_quarantine_review",
        ],
        "allowed_evidence_sufficiency": [
            "sufficient_for_reproduction_counter",
            "sufficient_for_falsification_counter",
            "insufficient_evidence_no_counter",
            "quarantine_new_credit_candidate",
        ],
        "allowed_counter_targets": [
            "accepted_external_reproduction_count",
            "accepted_external_falsification_count",
            "new_credit_candidate_pending_review",
            "no_counter_change",
        ],
        "allowed_credit_decisions": [
            "preserve_one_unit_proxy_credit",
            "revoke_one_unit_proxy_credit",
            "insufficient_evidence_no_counter",
            "quarantine_new_credit_candidate",
            "reject_double_counted_submission",
        ],
        "counter_transition_rules": {
            "accepted_external_reproduction_count": {
                "allowed_delta": [0, 1],
                "requires": [
                    "filled_nonfixture_r93_packet",
                    "review_transcript",
                    "sufficient_for_reproduction_counter",
                    "double_count_decision_no_duplicate",
                    "claim_boundary_safe",
                ],
            },
            "accepted_external_falsification_count": {
                "allowed_delta": [0, 1],
                "requires": [
                    "filled_nonfixture_r93_packet",
                    "review_transcript",
                    "sufficient_for_falsification_counter",
                    "double_count_decision_no_duplicate",
                    "claim_boundary_safe",
                ],
            },
            "new_credit_candidate_pending_review": {
                "allowed_delta": [0],
                "requires": [
                    "separate_new_credit_gate_after_quarantine",
                    "no_direct_R94_credit_increment",
                ],
            },
            "no_counter_change": {"allowed_delta": [0], "requires": ["explicit_no_counter_reason"]},
        },
        "pre_r94_accepted_external_reproduction_count": 0,
        "pre_r94_accepted_external_falsification_count": 0,
        "pre_r94_new_credit_delta": 0,
        "current_counter_delta": 0,
        "accepted_external_reproduction_count": 0,
        "accepted_external_falsification_count": 0,
        "new_credit_delta": 0,
        "o3_closed": False,
        "resource_saving_claimed": False,
        "physical_layout_claimed": False,
        "claim_boundary": (
            "R94 defines how a maintainer verdict may move external reproduction "
            "or falsification counters after a filled R93 non-fixture packet. "
            "The current empty verdict is rejected, no counters move, and no "
            "new B7/O3/layout/resource-saving claim is made."
        ),
    }
    contract["verdict_contract_hash"] = stable_self_hash(contract, "verdict_contract_hash")
    return contract


def build_verdict_template(contract: dict[str, Any]) -> dict[str, Any]:
    template = {
        "artifact": "R94 G1 maintainer verdict template",
        "contract_id": contract["contract_id"],
        "verdict_contract_hash": contract["verdict_contract_hash"],
        "fields": {field: None for field in contract["required_fields"]},
        "allowed_review_modes": contract["allowed_review_modes"],
        "allowed_evidence_sufficiency": contract["allowed_evidence_sufficiency"],
        "allowed_counter_targets": contract["allowed_counter_targets"],
        "allowed_credit_decisions": contract["allowed_credit_decisions"],
        "instructions": [
            "Bind the reviewed R93 packet path and SHA-256 before any verdict.",
            "Attach a review transcript path and SHA-256.",
            "Use counter_delta=0 unless the evidence sufficiency and counter target match.",
            "Never use R94 alone to grant new credit, O3 closure, layout closure, or resource-saving claims.",
        ],
    }
    template["verdict_template_hash"] = stable_self_hash(template, "verdict_template_hash")
    return template


def build_empty_verdict(contract: dict[str, Any], template: dict[str, Any]) -> dict[str, Any]:
    fields = dict(template["fields"])
    fields.update(
        {
            "verdict_id": "R94-G1-empty-maintainer-verdict",
            "source_r93_preflight_hash": contract["source_r93_preflight_hash"],
            "counter_delta": 0,
            "one_unit_credit_preserved": False,
            "one_unit_credit_revoked": False,
            "new_credit_delta": 0,
            "accepted_external_reproduction_count_after": 0,
            "accepted_external_falsification_count_after": 0,
            "o3_closed": False,
            "resource_saving_claimed": False,
            "physical_layout_claimed": False,
            "claim_boundary": "empty_maintainer_verdict_no_review_evidence",
        }
    )
    verdict = {
        "artifact": "R94 current empty maintainer verdict",
        "contract_id": contract["contract_id"],
        "verdict_contract_hash": contract["verdict_contract_hash"],
        "verdict_template_hash": template["verdict_template_hash"],
        "fields": fields,
    }
    verdict["verdict_hash"] = stable_self_hash(verdict, "verdict_hash")
    return verdict


def build_preflight(contract: dict[str, Any], verdict: dict[str, Any]) -> dict[str, Any]:
    fields = verdict["fields"]
    missing_required = [field for field in contract["required_fields"] if field not in fields]
    missing_production = [
        field for field in contract["production_required_fields"] if fields.get(field) in (None, "")
    ]
    counter_target = fields.get("counter_target")
    counter_delta = fields.get("counter_delta")
    credit_decision = fields.get("credit_decision")
    evidence_sufficiency = fields.get("evidence_sufficiency")

    gates = {
        "all_required_fields_present": not missing_required,
        "production_required_fields_present": not missing_production,
        "maintainer_identity_present": bool(fields.get("maintainer_id")),
        "reviewed_packet_bound": bool(fields.get("reviewed_packet_path"))
        and bool(fields.get("reviewed_packet_sha256")),
        "review_transcript_bound": bool(fields.get("review_transcript_path"))
        and bool(fields.get("review_transcript_sha256")),
        "r93_preflight_hash_bound": fields.get("source_r93_preflight_hash")
        == contract["source_r93_preflight_hash"],
        "r93_packet_hash_bound": bool(fields.get("source_r93_packet_hash")),
        "allowed_review_mode": fields.get("review_mode") in contract["allowed_review_modes"],
        "allowed_evidence_sufficiency": evidence_sufficiency
        in contract["allowed_evidence_sufficiency"],
        "allowed_counter_target": counter_target in contract["allowed_counter_targets"],
        "allowed_credit_decision": credit_decision in contract["allowed_credit_decisions"],
        "counter_delta_allowed": counter_target in contract["counter_transition_rules"]
        and counter_delta in contract["counter_transition_rules"].get(counter_target, {}).get(
            "allowed_delta", []
        ),
        "counter_delta_consistent": counter_delta == 0
        and fields.get("accepted_external_reproduction_count_after") == 0
        and fields.get("accepted_external_falsification_count_after") == 0,
        "no_direct_new_credit": fields.get("new_credit_delta") == 0,
        "claim_boundary_safe": fields.get("o3_closed") is False
        and fields.get("resource_saving_claimed") is False
        and fields.get("physical_layout_claimed") is False,
        "maintainer_verdict_accepted": False,
    }
    failed = [gate for gate, passed in gates.items() if not passed]
    preflight = {
        "artifact": "R94 maintainer verdict preflight verdict",
        "method": METHOD,
        "source_target_id": TARGET_ID,
        "upstream_target_id": UPSTREAM_TARGET_ID,
        "verdict_contract_hash": contract["verdict_contract_hash"],
        "verdict_hash": verdict["verdict_hash"],
        "gates": gates,
        "passed_gate_count": sum(1 for passed in gates.values() if passed),
        "failed_gate_count": len(failed),
        "failed_gates": failed,
        "missing_required_fields": missing_required,
        "missing_production_fields": missing_production,
        "empty_verdict_rejected": True,
        "maintainer_verdict_accepted": False,
        "counter_delta": 0,
        "accepted_external_reproduction_count": 0,
        "accepted_external_falsification_count": 0,
        "new_credit_delta": 0,
        "claim_boundary": contract["claim_boundary"],
    }
    preflight["preflight_hash"] = stable_self_hash(preflight, "preflight_hash")
    return preflight


def build_blocker_queue(contract: dict[str, Any], preflight: dict[str, Any]) -> dict[str, Any]:
    queue = {
        "artifact": "R94 post maintainer verdict blocker queue",
        "method": METHOD,
        "source_target_id": TARGET_ID,
        "upstream_target_id": UPSTREAM_TARGET_ID,
        "verdict_contract_hash": contract["verdict_contract_hash"],
        "preflight_hash": preflight["preflight_hash"],
        "queue": [
            {
                "blocker_id": "R94-G1-1",
                "priority": 1,
                "target_gate": "filled_nonfixture_r93_packet",
                "needed_artifact": "non-fixture R93 packet with external attestation and independent environment evidence",
            },
            {
                "blocker_id": "R94-G1-2",
                "priority": 2,
                "target_gate": "maintainer_review_transcript",
                "needed_artifact": "review transcript binding the packet hash, command transcript, double-count decision, and claim boundary",
            },
            {
                "blocker_id": "R94-G1-3",
                "priority": 3,
                "target_gate": "counter_update_verdict",
                "needed_artifact": "accepted maintainer verdict with an allowed counter target and zero direct new-credit increment",
            },
            {
                "blocker_id": "R94-G1-4",
                "priority": 4,
                "target_gate": "post_verdict_b7_boundary",
                "needed_artifact": "separate B7 boundary retest before any 1.25x, layout, O3, or resource-saving claim",
            },
        ],
    }
    queue["blocker_queue_hash"] = stable_self_hash(queue, "blocker_queue_hash")
    return queue


def write_stdout(root: Path, contract: dict[str, Any], preflight: dict[str, Any], queue: dict[str, Any]) -> str:
    text = "\n".join(
        [
            "R94 maintainer verdict counter contract stdout",
            f"method={METHOD}",
            f"source_target_id={TARGET_ID}",
            f"upstream_target_id={UPSTREAM_TARGET_ID}",
            f"verdict_contract_hash={contract['verdict_contract_hash']}",
            f"preflight_hash={preflight['preflight_hash']}",
            f"blocker_queue_hash={queue['blocker_queue_hash']}",
            f"required_field_count={contract['required_field_count']}",
            f"production_required_field_count={contract['production_required_field_count']}",
            f"failed_gate_count={preflight['failed_gate_count']}",
            "maintainer_verdict_accepted=false",
            "accepted_external_reproduction_count=0",
            "accepted_external_falsification_count=0",
            "new_credit_delta=0",
        ]
    ) + "\n"
    path = root / R94_STDOUT
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def build_payload(args: argparse.Namespace) -> dict[str, Any]:
    root = Path(args.repo_root).resolve()
    r93_result = load_json(root / R93_RESULT)
    r93_contract = load_json(root / R93_INTAKE_CONTRACT)
    r93_template = load_json(root / R93_PACKET_TEMPLATE)
    r93_preflight = load_json(root / R93_PREFLIGHT)
    r93_blocker_queue = load_json(root / R93_BLOCKER_QUEUE)

    contract = build_verdict_contract(
        root, r93_result, r93_contract, r93_template, r93_preflight, r93_blocker_queue
    )
    write_json(root / R94_VERDICT_CONTRACT, contract)
    template = build_verdict_template(contract)
    write_json(root / R94_VERDICT_TEMPLATE, template)
    empty_verdict = build_empty_verdict(contract, template)
    write_json(root / R94_EMPTY_VERDICT, empty_verdict)
    preflight = build_preflight(contract, empty_verdict)
    write_json(root / R94_PREFLIGHT, preflight)
    blocker_queue = build_blocker_queue(contract, preflight)
    write_json(root / R94_BLOCKER_QUEUE, blocker_queue)
    stdout_sha256 = write_stdout(root, contract, preflight, blocker_queue)

    requirements = [
        req(
            "A1",
            "R94 binds the R93 result, intake contract, packet template, preflight, and blocker queue",
            r93_result["summary"]["source_target_id"] == UPSTREAM_TARGET_ID
            and r93_result["intake_contract_hash"] == r93_contract["intake_contract_hash"]
            and r93_result["packet_template_hash"] == r93_template["packet_template_hash"]
            and r93_result["preflight_hash"] == r93_preflight["preflight_hash"],
            {
                "r93_payload_hash": r93_result["payload_hash"],
                "r93_intake_contract_hash": r93_contract["intake_contract_hash"],
                "r93_preflight_hash": r93_preflight["preflight_hash"],
                "r93_blocker_queue_hash": r93_blocker_queue["blocker_queue_hash"],
            },
        ),
        req(
            "A2",
            "R94 emits a maintainer verdict contract with explicit counter transition rules",
            contract["required_field_count"] == 24
            and contract["production_required_field_count"] == 15
            and set(contract["counter_transition_rules"])
            == {
                "accepted_external_reproduction_count",
                "accepted_external_falsification_count",
                "new_credit_candidate_pending_review",
                "no_counter_change",
            },
            {
                "verdict_contract_hash": contract["verdict_contract_hash"],
                "required_field_count": contract["required_field_count"],
                "production_required_field_count": contract["production_required_field_count"],
            },
        ),
        req(
            "A3",
            "R94 emits a fillable maintainer verdict template",
            template["verdict_contract_hash"] == contract["verdict_contract_hash"]
            and all(field in template["fields"] for field in VERDICT_REQUIRED_FIELDS),
            {
                "verdict_template_hash": template["verdict_template_hash"],
                "template_field_count": len(template["fields"]),
            },
        ),
        req(
            "A4",
            "R94 rejects the empty maintainer verdict before review evidence exists",
            preflight["empty_verdict_rejected"] is True
            and preflight["maintainer_verdict_accepted"] is False
            and preflight["failed_gate_count"] == 11,
            {
                "preflight_hash": preflight["preflight_hash"],
                "failed_gates": preflight["failed_gates"],
                "missing_production_field_count": len(preflight["missing_production_fields"]),
            },
        ),
        req(
            "A5",
            "R94 keeps external counters and new credit at zero",
            preflight["accepted_external_reproduction_count"] == 0
            and preflight["accepted_external_falsification_count"] == 0
            and preflight["counter_delta"] == 0
            and preflight["new_credit_delta"] == 0,
            {
                "accepted_external_reproduction_count": preflight[
                    "accepted_external_reproduction_count"
                ],
                "accepted_external_falsification_count": preflight[
                    "accepted_external_falsification_count"
                ],
                "counter_delta": preflight["counter_delta"],
                "new_credit_delta": preflight["new_credit_delta"],
            },
        ),
        req(
            "A6",
            "R94 keeps O3, resource-saving, and physical-layout claims closed",
            contract["o3_closed"] is False
            and contract["resource_saving_claimed"] is False
            and contract["physical_layout_claimed"] is False,
            {
                "o3_closed": contract["o3_closed"],
                "resource_saving_claimed": contract["resource_saving_claimed"],
                "physical_layout_claimed": contract["physical_layout_claimed"],
            },
        ),
        req(
            "A7",
            "R94 emits blockers for packet, transcript, verdict, and post-verdict B7 boundary",
            [item["target_gate"] for item in blocker_queue["queue"]]
            == [
                "filled_nonfixture_r93_packet",
                "maintainer_review_transcript",
                "counter_update_verdict",
                "post_verdict_b7_boundary",
            ],
            {
                "blocker_queue_hash": blocker_queue["blocker_queue_hash"],
                "blocker_ids": [item["blocker_id"] for item in blocker_queue["queue"]],
            },
        ),
    ]

    failed_requirements = [
        requirement["requirement_id"] for requirement in requirements if not requirement["passed"]
    ]
    validation_errors = []
    if failed_requirements:
        validation_errors.append("one or more R94 requirements failed")
    if preflight["maintainer_verdict_accepted"]:
        validation_errors.append("R94 must not accept the empty maintainer verdict")
    if preflight["new_credit_delta"] != 0:
        validation_errors.append("R94 must not grant new credit")

    payload = {
        "artifact": "B1/B7 cone01 R94 maintainer verdict counter contract gate",
        "method": METHOD,
        "version": VERSION,
        "status": STATUS,
        "model_status": MODEL_STATUS,
        "source_target_id": TARGET_ID,
        "upstream_target_id": UPSTREAM_TARGET_ID,
        "generated_at_unix": int(time.time()),
        "verdict_contract_path": R94_VERDICT_CONTRACT,
        "verdict_contract_hash": contract["verdict_contract_hash"],
        "verdict_template_path": R94_VERDICT_TEMPLATE,
        "verdict_template_hash": template["verdict_template_hash"],
        "empty_verdict_path": R94_EMPTY_VERDICT,
        "empty_verdict_hash": empty_verdict["verdict_hash"],
        "preflight_path": R94_PREFLIGHT,
        "preflight_hash": preflight["preflight_hash"],
        "stdout_path": R94_STDOUT,
        "stdout_sha256": stdout_sha256,
        "blocker_queue_path": R94_BLOCKER_QUEUE,
        "blocker_queue_hash": blocker_queue["blocker_queue_hash"],
        "requirement_count": len(requirements),
        "requirements_passed": sum(1 for requirement in requirements if requirement["passed"]),
        "requirements_failed": len(failed_requirements),
        "failed_requirement_ids": failed_requirements,
        "requirements": requirements,
        "validation_error_count": len(validation_errors),
        "validation_errors": validation_errors,
        "summary": {
            "method": METHOD,
            "status": STATUS,
            "model_status": MODEL_STATUS,
            "source_target_id": TARGET_ID,
            "upstream_target_id": UPSTREAM_TARGET_ID,
            "route_id": contract["route_id"],
            "contract_id": contract["contract_id"],
            "required_field_count": contract["required_field_count"],
            "production_required_field_count": contract[
                "production_required_field_count"
            ],
            "verdict_mode_count": len(contract["allowed_review_modes"]),
            "counter_transition_rule_count": len(contract["counter_transition_rules"]),
            "empty_verdict_rejected": preflight["empty_verdict_rejected"],
            "maintainer_verdict_accepted": preflight["maintainer_verdict_accepted"],
            "preflight_failed_gate_count": preflight["failed_gate_count"],
            "missing_production_field_count": len(preflight["missing_production_fields"]),
            "counter_delta": preflight["counter_delta"],
            "accepted_external_reproduction_count": preflight[
                "accepted_external_reproduction_count"
            ],
            "accepted_external_falsification_count": preflight[
                "accepted_external_falsification_count"
            ],
            "new_credit_delta": preflight["new_credit_delta"],
            "o3_closed": contract["o3_closed"],
            "resource_saving_claimed": contract["resource_saving_claimed"],
            "physical_layout_claimed": contract["physical_layout_claimed"],
            "verdict_contract_hash": contract["verdict_contract_hash"],
            "verdict_template_hash": template["verdict_template_hash"],
            "empty_verdict_hash": empty_verdict["verdict_hash"],
            "preflight_hash": preflight["preflight_hash"],
            "stdout_sha256": stdout_sha256,
            "blocker_queue_hash": blocker_queue["blocker_queue_hash"],
            "payload_hash": None,
            "requirements_passed": sum(1 for requirement in requirements if requirement["passed"]),
            "requirements_failed": len(failed_requirements),
            "failed_requirement_ids": failed_requirements,
            "validation_error_count": len(validation_errors),
        },
    }
    payload["payload_hash"] = stable_self_hash(payload, "payload_hash")
    payload["summary"]["payload_hash"] = payload["payload_hash"]
    return payload


def write_report(root: Path, payload: dict[str, Any]) -> None:
    summary = payload["summary"]
    lines = [
        "# B1/B7 Cone01 R94 Maintainer Verdict Counter Contract Gate",
        "",
        f"- Target: `{TARGET_ID}`",
        f"- Upstream target: `{UPSTREAM_TARGET_ID}`",
        f"- Method: `{METHOD}`",
        f"- Status: `{STATUS}`",
        f"- Model status: `{MODEL_STATUS}`",
        "",
        "## Result",
        "",
        "R94 converts the R93 non-fixture intake blocker into a maintainer-verdict",
        "and counter-update contract. The contract defines which review modes,",
        "evidence sufficiency labels, counter targets, and credit decisions are",
        "allowed before an external reproduction or falsification counter can move.",
        "",
        "The current empty maintainer verdict is rejected. No external reproduction",
        "or falsification counter is incremented, `counter_delta` remains `0`, and",
        "no new B7 credit is granted.",
        "",
        "## Key Counters",
        "",
        f"- Required fields: `{summary['required_field_count']}`",
        f"- Production-required fields: `{summary['production_required_field_count']}`",
        f"- Verdict modes: `{summary['verdict_mode_count']}`",
        f"- Counter transition rules: `{summary['counter_transition_rule_count']}`",
        f"- Empty verdict rejected: `{summary['empty_verdict_rejected']}`",
        f"- Maintainer verdict accepted: `{summary['maintainer_verdict_accepted']}`",
        f"- Preflight failed gates: `{summary['preflight_failed_gate_count']}`",
        f"- Missing production fields: `{summary['missing_production_field_count']}`",
        f"- Counter delta: `{summary['counter_delta']}`",
        f"- Accepted external reproductions: `{summary['accepted_external_reproduction_count']}`",
        f"- Accepted external falsifications: `{summary['accepted_external_falsification_count']}`",
        f"- New credit delta: `{summary['new_credit_delta']}`",
        "",
        "## Requirements",
        "",
    ]
    for requirement in payload["requirements"]:
        status = "PASS" if requirement["passed"] else "FAIL"
        lines.append(f"- `{requirement['requirement_id']}` {status}: {requirement['label']}")
    lines.extend(
        [
            "",
            "## Artifacts",
            "",
            f"- Result JSON: `{RESULT_PATH}`",
            f"- Verdict contract: `{R94_VERDICT_CONTRACT}`",
            f"- Verdict template: `{R94_VERDICT_TEMPLATE}`",
            f"- Empty verdict: `{R94_EMPTY_VERDICT}`",
            f"- Preflight verdict: `{R94_PREFLIGHT}`",
            f"- Stdout: `{R94_STDOUT}`",
            f"- Blocker queue: `{R94_BLOCKER_QUEUE}`",
            "",
            "## Claim Boundary",
            "",
            "R94 is a maintainer-verdict and counter-control gate. It does not accept",
            "a reviewed external packet yet, does not increment reproduction or",
            "falsification counters, does not grant new B7 credit, and does not close",
            "1.25x, O3, physical layout, resource-saving, paper, patent, funding, or",
            "product-readiness claims.",
            "",
        ]
    )
    (root / REPORT_PATH).write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()
    root = Path(args.repo_root).resolve()
    payload = build_payload(args)
    write_json(root / RESULT_PATH, payload)
    write_report(root, payload)
    if args.pretty:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(json.dumps(payload, sort_keys=True))


if __name__ == "__main__":
    main()
