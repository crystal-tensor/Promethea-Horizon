#!/usr/bin/env python3
"""T-B1-004gb/T-B7-015k: R78 positive-route packet contract gate."""

from __future__ import annotations

import argparse
import hashlib
import json
import time
from pathlib import Path
from typing import Any


METHOD = "b1_b7_cone01_r78_positive_route_packet_contract_gate_v0"
STATUS = "cone01_r78_positive_route_packet_contract_emitted_zero_credit"
MODEL_STATUS = "post_r77_positive_route_packet_required_before_b7_retest"
VERSION = "0.1"
TARGET_ID = "T-B1-004gb/T-B7-015k"
UPSTREAM_TARGET_ID = "T-B1-004ga/T-B7-015j"
SUBMISSION_DIR = "results/B1_B7_cone01_o3_f4_exit_route_submissions"
R77_RESULT = "results/B1_B7_cone01_R77_r76_hardened_preflight_rerun_gate_v0.json"
R77_BLOCKER_QUEUE = f"{SUBMISSION_DIR}/R77-post-r76-hardened-blocker-queue.json"
R76_SUBMISSION = f"{SUBMISSION_DIR}/R76-r1-d1-d2-d3-source-closure-submission.json"
R67_CONTRACT = f"{SUBMISSION_DIR}/R67-accepted-exit-route.contract.json"
R71_CONTRACT = f"{SUBMISSION_DIR}/R71-R1-positive-delta-ledger.contract.json"
R78_CONTRACT = f"{SUBMISSION_DIR}/R78-positive-route-packet.contract.json"
R78_TEMPLATE = f"{SUBMISSION_DIR}/R78-positive-route-packet.template.json"
R78_PREFLIGHT = f"{SUBMISSION_DIR}/R78-positive-route-packet.current-empty-preflight.verdict.json"
R78_BLOCKER_QUEUE = f"{SUBMISSION_DIR}/R78-positive-route-packet-blocker-queue.json"
R78_STDOUT = f"{SUBMISSION_DIR}/R78-positive-route-packet-contract.stdout.txt"


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


def path_hash_matches(root: Path, path_value: Any, hash_value: Any) -> bool:
    if not isinstance(path_value, str) or not isinstance(hash_value, str):
        return False
    path = root / path_value
    return path.exists() and file_hash(path) == hash_value


def build_contract(
    root: Path,
    r77: dict[str, Any],
    r77_blocker_queue: dict[str, Any],
    r76_submission: dict[str, Any],
    r67_contract: dict[str, Any],
    r71_contract: dict[str, Any],
) -> dict[str, Any]:
    d3 = r76_submission["packets"]["R73-D3-line1378-source-backed-no-double-counting"]
    contract = {
        "contract_id": "B1-B7-cone01-R78-positive-route-packet-contract",
        "source_target_id": TARGET_ID,
        "upstream_target_id": UPSTREAM_TARGET_ID,
        "source_r77_result_path": R77_RESULT,
        "source_r77_result_sha256": file_hash(root / R77_RESULT),
        "source_r77_payload_hash": r77["summary"]["payload_hash"],
        "source_r77_blocker_queue_path": R77_BLOCKER_QUEUE,
        "source_r77_blocker_queue_sha256": file_hash(root / R77_BLOCKER_QUEUE),
        "source_r77_blocker_queue_hash": r77_blocker_queue["blocker_queue_hash"],
        "source_r67_contract_path": R67_CONTRACT,
        "source_r67_contract_sha256": file_hash(root / R67_CONTRACT),
        "source_r67_contract_hash": r67_contract["contract_hash"],
        "source_r71_contract_path": R71_CONTRACT,
        "source_r71_contract_sha256": file_hash(root / R71_CONTRACT),
        "source_r71_contract_hash": r71_contract["contract_hash"],
        "r76_no_double_counting_ledger_path": d3["no_double_counting_ledger_path"],
        "r76_no_double_counting_ledger_sha256": d3["no_double_counting_ledger_sha256"],
        "required_promotion_gates": [
            "accepted_exit_route_positive",
            "accepted_occurrence_positive",
            "accepted_proxy_t_positive",
        ],
        "production_required_fields": [
            "packet_id",
            "route_id",
            "route_class",
            "source_r77_payload_hash",
            "source_r67_contract_hash",
            "source_r71_contract_hash",
            "source_r76_no_double_counting_ledger_path",
            "source_r76_no_double_counting_ledger_sha256",
            "accepted_route_artifact_path",
            "accepted_route_artifact_sha256",
            "full_circuit_or_route_bounded_replay_command",
            "full_circuit_or_route_bounded_replay_stdout_path",
            "full_circuit_or_route_bounded_replay_stdout_sha256",
            "same_unitary_or_symbolic_certificate_path",
            "same_unitary_or_symbolic_certificate_sha256",
            "occurrence_acceptance_ledger_path",
            "occurrence_acceptance_ledger_sha256",
            "proxy_t_acceptance_ledger_path",
            "proxy_t_acceptance_ledger_sha256",
            "no_double_counting_preservation_verdict_path",
            "no_double_counting_preservation_verdict_sha256",
            "accepted_exit_route_count",
            "accepted_occurrence_removal",
            "accepted_proxy_t_reduction",
            "b7_nonzero_retest_requested",
            "claim_boundary",
        ],
        "acceptance_rules": [
            "all production_required_fields are present and non-placeholder",
            "all *_sha256 fields match the referenced artifact bytes",
            "source_r77_payload_hash matches the current R77 payload hash",
            "source_r76_no_double_counting_ledger_sha256 preserves the R76 exclusion ledger",
            "accepted_exit_route_count >= 1",
            "accepted_occurrence_removal >= 1",
            "accepted_proxy_t_reduction >= 1",
            "b7_nonzero_retest_requested is false inside this packet; a separate downstream B7 retest must unlock it",
            "claim_boundary explicitly forbids O3 closure, reroute permission, resource saving, and B7 credit",
        ],
        "forbidden_shortcuts": [
            "source-closure-only packets",
            "prefill-only proxy-T pricing",
            "metadata-only positive integers",
            "line1378/line1381 double counting",
            "B7 retest request before all three positive-promotion gates pass",
        ],
    }
    contract["contract_hash"] = stable_self_hash(contract, "contract_hash")
    return contract


def build_template(contract: dict[str, Any]) -> dict[str, Any]:
    template: dict[str, Any] = {
        "packet_id": "B1-B7-cone01-R78-positive-route-packet-template",
        "contract_id": contract["contract_id"],
        "contract_hash": contract["contract_hash"],
        "route_id": None,
        "route_class": None,
        "source_r77_payload_hash": contract["source_r77_payload_hash"],
        "source_r67_contract_hash": contract["source_r67_contract_hash"],
        "source_r71_contract_hash": contract["source_r71_contract_hash"],
        "source_r76_no_double_counting_ledger_path": contract[
            "r76_no_double_counting_ledger_path"
        ],
        "source_r76_no_double_counting_ledger_sha256": contract[
            "r76_no_double_counting_ledger_sha256"
        ],
        "accepted_route_artifact_path": None,
        "accepted_route_artifact_sha256": None,
        "full_circuit_or_route_bounded_replay_command": None,
        "full_circuit_or_route_bounded_replay_stdout_path": None,
        "full_circuit_or_route_bounded_replay_stdout_sha256": None,
        "same_unitary_or_symbolic_certificate_path": None,
        "same_unitary_or_symbolic_certificate_sha256": None,
        "occurrence_acceptance_ledger_path": None,
        "occurrence_acceptance_ledger_sha256": None,
        "proxy_t_acceptance_ledger_path": None,
        "proxy_t_acceptance_ledger_sha256": None,
        "no_double_counting_preservation_verdict_path": None,
        "no_double_counting_preservation_verdict_sha256": None,
        "accepted_exit_route_count": 0,
        "accepted_occurrence_removal": 0,
        "accepted_proxy_t_reduction": 0,
        "b7_nonzero_retest_requested": False,
        "claim_boundary": (
            "Template only. This packet cannot close O3, permit reroute, claim "
            "resource saving, or grant B7 credit until a filled packet passes "
            "all R78 positive-promotion gates and a downstream B7 retest accepts it."
        ),
    }
    template["template_hash"] = stable_self_hash(template, "template_hash")
    return template


def preflight_packet(root: Path, contract: dict[str, Any], packet: dict[str, Any]) -> dict[str, Any]:
    missing = [
        field for field in contract["production_required_fields"] if packet.get(field) in (None, "")
    ]
    hash_failures = []
    hash_fields_seen = 0
    for field in contract["production_required_fields"]:
        if not field.endswith("_sha256"):
            continue
        path_field = field[: -len("_sha256")] + "_path"
        value = packet.get(field)
        path_value = packet.get(path_field)
        if value in (None, "") or path_value in (None, ""):
            continue
        hash_fields_seen += 1
        if not path_hash_matches(root, path_value, value):
            hash_failures.append(field)

    gates = {
        "all_required_fields_complete": missing == [],
        "all_hash_bound_artifacts_match": missing == [] and hash_failures == [],
        "source_r77_payload_hash_matches": packet.get("source_r77_payload_hash")
        == contract["source_r77_payload_hash"],
        "r76_no_double_counting_preserved": packet.get(
            "source_r76_no_double_counting_ledger_sha256"
        )
        == contract["r76_no_double_counting_ledger_sha256"],
        "accepted_exit_route_positive": packet.get("accepted_exit_route_count", 0) >= 1,
        "accepted_occurrence_positive": packet.get("accepted_occurrence_removal", 0) >= 1,
        "accepted_proxy_t_positive": packet.get("accepted_proxy_t_reduction", 0) >= 1,
        "b7_not_requested_inside_packet": packet.get("b7_nonzero_retest_requested") is False,
        "claim_boundary_blocks_b7": "b7 credit" in str(packet.get("claim_boundary", "")).lower()
        and "cannot" in str(packet.get("claim_boundary", "")).lower(),
    }
    failed = [gate for gate, passed in gates.items() if not passed]
    verdict = {
        "artifact": "R78 positive-route packet current-empty preflight verdict",
        "method": METHOD,
        "source_target_id": TARGET_ID,
        "contract_id": contract["contract_id"],
        "contract_hash": contract["contract_hash"],
        "packet_id": packet["packet_id"],
        "packet_hash": packet["template_hash"],
        "gates": gates,
        "passed_gate_count": sum(1 for passed in gates.values() if passed),
        "failed_gate_count": len(failed),
        "failed_gates": failed,
        "missing_required_fields": missing,
        "missing_required_field_count": len(missing),
        "hash_fields_seen": hash_fields_seen,
        "hash_failures": hash_failures,
        "accepted": failed == [],
        "accepted_exit_route_count": 0,
        "accepted_occurrence_removal": 0,
        "accepted_proxy_t_reduction": 0,
        "b7_credit_delta": 0,
        "b7_nonzero_retest_allowed": False,
        "rejection_reason": "template_only_no_positive_route_artifacts_or_positive_deltas",
    }
    verdict["verdict_hash"] = stable_self_hash(verdict, "verdict_hash")
    return verdict


def build_blocker_queue(contract: dict[str, Any], preflight: dict[str, Any]) -> dict[str, Any]:
    queue = {
        "artifact": "R78 positive-route packet blocker queue",
        "method": METHOD,
        "source_target_id": TARGET_ID,
        "upstream_target_id": UPSTREAM_TARGET_ID,
        "contract_hash": contract["contract_hash"],
        "current_preflight_accepted": preflight["accepted"],
        "failed_gates": preflight["failed_gates"],
        "queue": [
            {
                "blocker_id": "R78-A",
                "priority": 1,
                "target_gate": "accepted_exit_route_positive",
                "needed_artifact": "accepted route artifact plus replay command/stdout and same-unitary or symbolic certificate",
            },
            {
                "blocker_id": "R78-B",
                "priority": 2,
                "target_gate": "accepted_occurrence_positive",
                "needed_artifact": "occurrence acceptance ledger proving at least one counted removal",
            },
            {
                "blocker_id": "R78-C",
                "priority": 3,
                "target_gate": "accepted_proxy_t_positive",
                "needed_artifact": "proxy-T acceptance ledger proving counted reduction beyond prefill-only pricing",
            },
            {
                "blocker_id": "R78-D",
                "priority": 4,
                "target_gate": "r76_no_double_counting_preserved",
                "needed_artifact": "no-double-counting preservation verdict that keeps line1378 excluded or otherwise accounted without overlap",
            },
        ],
        "b7_rule": "Do not run nonzero B7 retest until R78-A/B/C pass together.",
    }
    queue["blocker_queue_hash"] = stable_self_hash(queue, "blocker_queue_hash")
    return queue


def build_payload(args: argparse.Namespace) -> dict[str, Any]:
    root = Path(args.repo_root).resolve()
    r77 = load_json(root / R77_RESULT)
    r77_blocker_queue = load_json(root / R77_BLOCKER_QUEUE)
    r76_submission = load_json(root / R76_SUBMISSION)
    r67_contract = load_json(root / R67_CONTRACT)
    r71_contract = load_json(root / R71_CONTRACT)
    r77_summary = r77["summary"]
    contract = build_contract(
        root, r77, r77_blocker_queue, r76_submission, r67_contract, r71_contract
    )
    write_json(root / R78_CONTRACT, contract)
    template = build_template(contract)
    write_json(root / R78_TEMPLATE, template)
    preflight = preflight_packet(root, contract, template)
    write_json(root / R78_PREFLIGHT, preflight)
    blocker_queue = build_blocker_queue(contract, preflight)
    write_json(root / R78_BLOCKER_QUEUE, blocker_queue)
    stdout_payload = {
        "artifact": "R78 positive-route packet contract stdout",
        "method": METHOD,
        "source_target_id": TARGET_ID,
        "contract_hash": contract["contract_hash"],
        "template_preflight_accepted": preflight["accepted"],
        "failed_gates": preflight["failed_gates"],
        "accepted_exit_route_count": 0,
        "accepted_occurrence_removal": 0,
        "accepted_proxy_t_reduction": 0,
        "b7_credit_delta": 0,
    }
    write_json(root / R78_STDOUT, stdout_payload)

    required_gates = [
        "accepted_exit_route_positive",
        "accepted_occurrence_positive",
        "accepted_proxy_t_positive",
    ]
    requirements = [
        req(
            "P1",
            "R77 is the post-source-closure upstream gate",
            r77_summary["r76_source_closure_passed"] is True
            and r77_summary["requirements_failed"] == 0
            and r77_summary["hardened_failed_gates"] == required_gates,
            {
                "r77_result_path": R77_RESULT,
                "r77_result_sha256": file_hash(root / R77_RESULT),
                "r77_failed_gates": r77_summary["hardened_failed_gates"],
            },
        ),
        req(
            "P2",
            "R78 contract targets exactly the three R77 promotion gates",
            contract["required_promotion_gates"] == required_gates,
            {"required_promotion_gates": contract["required_promotion_gates"]},
        ),
        req(
            "P3",
            "R78 preserves R76 no-double-counting evidence",
            path_hash_matches(
                root,
                contract["r76_no_double_counting_ledger_path"],
                contract["r76_no_double_counting_ledger_sha256"],
            ),
            {
                "r76_no_double_counting_ledger_path": contract[
                    "r76_no_double_counting_ledger_path"
                ],
                "r76_no_double_counting_ledger_sha256": contract[
                    "r76_no_double_counting_ledger_sha256"
                ],
            },
        ),
        req(
            "P4",
            "R78 contract requires replay, certificate, occurrence, proxy-T, and no-double-counting artifacts",
            all(
                field in contract["production_required_fields"]
                for field in [
                    "full_circuit_or_route_bounded_replay_stdout_path",
                    "same_unitary_or_symbolic_certificate_path",
                    "occurrence_acceptance_ledger_path",
                    "proxy_t_acceptance_ledger_path",
                    "no_double_counting_preservation_verdict_path",
                ]
            ),
            {"production_required_fields": contract["production_required_fields"]},
        ),
        req(
            "P5",
            "Current empty template is rejected",
            preflight["accepted"] is False and preflight["failed_gate_count"] >= 3,
            {
                "preflight_path": R78_PREFLIGHT,
                "preflight_sha256": file_hash(root / R78_PREFLIGHT),
                "failed_gates": preflight["failed_gates"],
                "missing_required_field_count": preflight["missing_required_field_count"],
            },
        ),
        req(
            "P6",
            "Accepted counters and B7 credit remain zero",
            preflight["accepted_exit_route_count"] == 0
            and preflight["accepted_occurrence_removal"] == 0
            and preflight["accepted_proxy_t_reduction"] == 0
            and preflight["b7_credit_delta"] == 0
            and preflight["b7_nonzero_retest_allowed"] is False,
            {
                "accepted_exit_route_count": preflight["accepted_exit_route_count"],
                "accepted_occurrence_removal": preflight["accepted_occurrence_removal"],
                "accepted_proxy_t_reduction": preflight["accepted_proxy_t_reduction"],
                "b7_credit_delta": preflight["b7_credit_delta"],
                "b7_nonzero_retest_allowed": preflight["b7_nonzero_retest_allowed"],
            },
        ),
        req(
            "P7",
            "R78 emits a PR-ready blocker queue",
            len(blocker_queue["queue"]) == 4
            and blocker_queue["current_preflight_accepted"] is False,
            {
                "blocker_queue_path": R78_BLOCKER_QUEUE,
                "blocker_queue_sha256": file_hash(root / R78_BLOCKER_QUEUE),
                "blocker_queue_hash": blocker_queue["blocker_queue_hash"],
            },
        ),
        req(
            "P8",
            "R78 preserves no-overclaim boundary",
            template["b7_nonzero_retest_requested"] is False
            and "cannot close O3" in template["claim_boundary"]
            and "B7 credit" in template["claim_boundary"],
            {"claim_boundary": template["claim_boundary"]},
        ),
    ]
    failed_requirements = [
        requirement["requirement_id"]
        for requirement in requirements
        if not requirement["passed"]
    ]
    validation_errors = []
    if preflight["accepted"]:
        validation_errors.append("R78 template preflight must be rejected")
    if r77_summary["hardened_accepted"] is not False:
        validation_errors.append("R78 expects R77 positive promotion to remain rejected")
    if preflight["b7_credit_delta"] != 0:
        validation_errors.append("R78 must preserve zero B7 credit")

    payload = {
        "artifact": "B1/B7 cone01 R78 positive-route packet contract gate",
        "method": METHOD,
        "version": VERSION,
        "status": STATUS,
        "model_status": MODEL_STATUS,
        "source_target_id": TARGET_ID,
        "upstream_target_id": UPSTREAM_TARGET_ID,
        "generated_at_unix": int(time.time()),
        "contract_path": R78_CONTRACT,
        "contract_hash": contract["contract_hash"],
        "template_path": R78_TEMPLATE,
        "template_hash": template["template_hash"],
        "preflight_path": R78_PREFLIGHT,
        "preflight_hash": preflight["verdict_hash"],
        "stdout_path": R78_STDOUT,
        "stdout_sha256": file_hash(root / R78_STDOUT),
        "blocker_queue_path": R78_BLOCKER_QUEUE,
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
            "r77_source_closure_passed": r77_summary["r76_source_closure_passed"],
            "r77_positive_promotion_passed": r77_summary["positive_promotion_passed"],
            "contract_targets": contract["required_promotion_gates"],
            "template_preflight_accepted": preflight["accepted"],
            "template_failed_gate_count": preflight["failed_gate_count"],
            "template_failed_gates": preflight["failed_gates"],
            "accepted_exit_route_count": 0,
            "accepted_occurrence_removal": 0,
            "accepted_proxy_t_reduction": 0,
            "b7_credit_delta": 0,
            "b7_nonzero_retest_allowed": False,
            "o3_closed": False,
            "reroute_allowed": False,
            "resource_saving_claimed": False,
            "b7_ledger_improvement_claimed": False,
            "contract_hash": contract["contract_hash"],
            "blocker_queue_hash": blocker_queue["blocker_queue_hash"],
            "payload_hash": None,
            "requirements_passed": sum(
                1 for requirement in requirements if requirement["passed"]
            ),
            "requirements_failed": len(failed_requirements),
            "failed_requirement_ids": failed_requirements,
            "validation_error_count": len(validation_errors),
        },
    }
    payload["payload_hash"] = stable_self_hash(payload, "payload_hash")
    payload["summary"]["payload_hash"] = payload["payload_hash"]
    return payload


def write_report(root: Path, payload: dict[str, Any]) -> None:
    report_path = root / "research/B1_B7_cone01_R78_positive_route_packet_contract_gate.md"
    summary = payload["summary"]
    lines = [
        "# B1/B7 Cone01 R78 Positive-Route Packet Contract Gate",
        "",
        f"- Target: `{TARGET_ID}`",
        f"- Upstream target: `{UPSTREAM_TARGET_ID}`",
        f"- Method: `{METHOD}`",
        f"- Status: `{STATUS}`",
        f"- Model status: `{MODEL_STATUS}`",
        "",
        "## Result",
        "",
        "R78 converts the post-R77 blocker into a concrete positive-route packet",
        "contract. It does not accept the current template. Instead, it defines",
        "the exact evidence a future PR must submit before B7 can even request a",
        "nonzero retest.",
        "",
        "## Key Counters",
        "",
        f"- R77 source closure passed: `{summary['r77_source_closure_passed']}`",
        f"- R77 positive promotion passed: `{summary['r77_positive_promotion_passed']}`",
        f"- Template preflight accepted: `{summary['template_preflight_accepted']}`",
        f"- Contract targets: `{summary['contract_targets']}`",
        f"- Accepted exit routes: `{summary['accepted_exit_route_count']}`",
        f"- Accepted occurrence removal: `{summary['accepted_occurrence_removal']}`",
        f"- Accepted proxy-T reduction: `{summary['accepted_proxy_t_reduction']}`",
        f"- B7 credit delta: `{summary['b7_credit_delta']}`",
        "",
        "## Requirements",
        "",
    ]
    for requirement in payload["requirements"]:
        status = "PASS" if requirement["passed"] else "FAIL"
        lines.append(
            f"- `{requirement['requirement_id']}` {status}: {requirement['label']}"
        )
    lines.extend(
        [
            "",
            "## Artifacts",
            "",
            f"- Result JSON: `results/B1_B7_cone01_R78_positive_route_packet_contract_gate_v0.json`",
            f"- Contract: `{R78_CONTRACT}`",
            f"- Template: `{R78_TEMPLATE}`",
            f"- Current-empty preflight: `{R78_PREFLIGHT}`",
            f"- Blocker queue: `{R78_BLOCKER_QUEUE}`",
            f"- Stdout: `{R78_STDOUT}`",
            "",
            "## Claim Boundary",
            "",
            "R78 is not an O3 closure, not reroute permission, not resource saving,",
            "and not B7 credit. It only makes the next accepted-positive-route PR",
            "auditable.",
            "",
        ]
    )
    report_path.write_text("\n".join(lines), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", default=".")
    parser.add_argument(
        "--output",
        default="results/B1_B7_cone01_R78_positive_route_packet_contract_gate_v0.json",
    )
    parser.add_argument("--pretty", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    root = Path(args.repo_root).resolve()
    payload = build_payload(args)
    write_json(root / args.output, payload)
    write_report(root, payload)
    print(json.dumps(payload, indent=2 if args.pretty else None, sort_keys=True))
    if payload["validation_error_count"] or payload["requirements_failed"]:
        raise SystemExit("B1/B7 R78 positive-route packet contract gate validation failed")


if __name__ == "__main__":
    main()
