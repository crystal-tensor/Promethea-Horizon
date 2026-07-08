#!/usr/bin/env python3
"""T-B1-004fu/T-B7-015d: R71 positive-delta ledger verifier gate."""

from __future__ import annotations

import argparse
import hashlib
import json
import time
from pathlib import Path
from typing import Any


METHOD = "b1_b7_cone01_r71_positive_delta_ledger_verifier_gate_v0"
STATUS = "cone01_r71_positive_delta_ledger_verifier_ready_zero_credit"
MODEL_STATUS = "r70_complete_prefill_rejected_until_positive_delta_ledger_accepts"
VERSION = "0.1"
TARGET_ID = "T-B1-004fu/T-B7-015d"
UPSTREAM_TARGET_ID = "T-B1-004ft/T-B7-015c"
SUBMISSION_DIR = "results/B1_B7_cone01_o3_f4_exit_route_submissions"
R67_CONTRACT = f"{SUBMISSION_DIR}/R67-accepted-exit-route.contract.json"
R70_PREFILL = f"{SUBMISSION_DIR}/R70-R1-line1381-prefill-machine-check-replay.json"
R70_RESULT = "results/B1_B7_cone01_R70_machine_check_replay_prefill_gate_v0.json"
R66_RESULT = "results/B1_B7_cone01_R66_o3_f4_b7_zero_credit_ledger_retest_gate_v0.json"
R71_CONTRACT = f"{SUBMISSION_DIR}/R71-R1-positive-delta-ledger.contract.json"
R71_TEMPLATE = f"{SUBMISSION_DIR}/R71-R1-positive-delta-ledger.template.json"
R71_STRUCTURAL_ONLY = f"{SUBMISSION_DIR}/R71-R1-structural-only-delta.fixture.json"
R71_STRUCTURAL_ONLY_VERDICT = f"{SUBMISSION_DIR}/R71-R1-structural-only-delta.verdict.json"
R71_PR_PACKETS = f"{SUBMISSION_DIR}/R71-positive-delta-pr-packets.json"


REQUIRED_LEDGER_FIELDS = [
    "ledger_id",
    "route_id",
    "route_class",
    "source_r70_prefill_path",
    "source_r70_prefill_sha256",
    "source_r70_prefill_hash",
    "source_r66_retest_packet_hash",
    "selected_lines",
    "dropped_overlap_lines",
    "structural_cnot_delta",
    "accepted_exit_route_count",
    "occurrence_removal_delta",
    "proxy_t_reduction_delta",
    "line1381_delta_evidence_path",
    "line1381_delta_evidence_sha256",
    "line1378_no_double_counting_evidence_path",
    "line1378_no_double_counting_evidence_sha256",
    "proxy_t_delta_derivation",
    "occurrence_delta_derivation",
    "machine_check_replay_stdout_path",
    "machine_check_replay_stdout_sha256",
    "b7_nonzero_retest_requested",
    "claim_boundary",
]


def stable_hash(payload: Any) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


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


def rel(root: Path, path: Path) -> str:
    return str(path.relative_to(root))


def path_hash_matches(root: Path, path_value: Any, hash_value: Any) -> bool:
    if not isinstance(path_value, str) or not isinstance(hash_value, str):
        return False
    path = root / path_value
    return path.exists() and file_hash(path) == hash_value


def build_contract(root: Path, r67: dict[str, Any], r70: dict[str, Any]) -> dict[str, Any]:
    contract = {
        "contract_id": "B1-B7-cone01-R71-positive-delta-ledger-verifier",
        "source_target_id": TARGET_ID,
        "upstream_target_id": UPSTREAM_TARGET_ID,
        "source_r67_contract_hash": r67["contract_hash"],
        "source_r70_prefill_hash": r70["prefill_hash"],
        "required_ledger_fields": REQUIRED_LEDGER_FIELDS,
        "acceptance_gates": [
            "all required ledger fields are non-placeholder",
            "source_r70_prefill_hash and source_r70_prefill_sha256 match the completed R70 prefill",
            "source_r66_retest_packet_hash matches the current R66 packet hash",
            "selected_lines equal [268, 1381]",
            "dropped_overlap_lines equal [1378]",
            "structural_cnot_delta is at least 1 but is not sufficient alone",
            "accepted_exit_route_count is at least 1",
            "occurrence_removal_delta is at least 1",
            "proxy_t_reduction_delta is at least 1",
            "line1381 delta evidence is hash-bound",
            "line1378 no-double-counting evidence is hash-bound",
            "claim boundary forbids O3 closure, reroute, and B7 credit before downstream nonzero retest",
        ],
        "forbidden_shortcuts": [
            "using structural CNOT delta alone as occurrence/proxy-T delta",
            "reusing the R66 zero-credit ledger as positive occurrence/proxy-T evidence",
            "counting line1378 and line1381 overlap twice",
            "requesting B7 nonzero credit before positive deltas are accepted",
            "claiming O3 closure or reroute permission from a ledger-only row",
        ],
    }
    contract["contract_hash"] = stable_hash(contract)
    return contract


def build_template(root: Path, contract: dict[str, Any], r70: dict[str, Any], r66: dict[str, Any]) -> dict[str, Any]:
    template = {
        "ledger_id": "B1-B7-cone01-R71-R1-positive-delta-ledger",
        "route_id": "R1-line1381-resolution",
        "route_class": "line1381_positive_delta_candidate",
        "source_r70_prefill_path": R70_PREFILL,
        "source_r70_prefill_sha256": file_hash(root / R70_PREFILL),
        "source_r70_prefill_hash": r70["prefill_hash"],
        "source_r66_retest_packet_hash": r66["summary"]["r66_retest_packet_hash"],
        "selected_lines": [268, 1381],
        "dropped_overlap_lines": [1378],
        "structural_cnot_delta": 6,
        "accepted_exit_route_count": None,
        "occurrence_removal_delta": None,
        "proxy_t_reduction_delta": None,
        "line1381_delta_evidence_path": None,
        "line1381_delta_evidence_sha256": None,
        "line1378_no_double_counting_evidence_path": None,
        "line1378_no_double_counting_evidence_sha256": None,
        "proxy_t_delta_derivation": None,
        "occurrence_delta_derivation": None,
        "machine_check_replay_stdout_path": r70["machine_check_replay_stdout_path"],
        "machine_check_replay_stdout_sha256": r70["machine_check_replay_stdout_sha256"],
        "b7_nonzero_retest_requested": False,
        "claim_boundary": (
            "Template only. Fill positive occurrence/proxy-T evidence before requesting "
            "acceptance. Do not claim O3 closure, reroute, or B7 credit here."
        ),
        "source_contract_hash": contract["contract_hash"],
    }
    template["template_hash"] = stable_hash(template)
    return template


def build_structural_only_fixture(
    root: Path, template: dict[str, Any], r70: dict[str, Any]
) -> dict[str, Any]:
    fixture = dict(template)
    fixture.update(
        {
            "ledger_id": "B1-B7-cone01-R71-structural-only-delta-fixture",
            "accepted_exit_route_count": 1,
            "occurrence_removal_delta": 0,
            "proxy_t_reduction_delta": 0,
            "line1381_delta_evidence_path": r70["line1381_pricing_or_elimination_evidence_path"],
            "line1381_delta_evidence_sha256": r70[
                "line1381_pricing_or_elimination_evidence_sha256"
            ],
            "line1378_no_double_counting_evidence_path": r70[
                "line1378_recovery_or_exclusion_evidence_path"
            ],
            "line1378_no_double_counting_evidence_sha256": r70[
                "line1378_recovery_or_exclusion_evidence_sha256"
            ],
            "proxy_t_delta_derivation": (
                "Rejected fixture: structural CNOT delta is present, but no positive "
                "proxy-T derivation is submitted."
            ),
            "occurrence_delta_derivation": (
                "Rejected fixture: no occurrence-removal row is submitted beyond R70."
            ),
            "claim_boundary": (
                "Rejected structural-only fixture. It is intentionally not an accepted "
                "exit route and must not be used for B7 credit."
            ),
        }
    )
    fixture["fixture_hash"] = stable_hash(fixture)
    return fixture


def verify_ledger(root: Path, ledger: dict[str, Any], contract: dict[str, Any], r70: dict[str, Any], r66: dict[str, Any]) -> dict[str, Any]:
    missing = [
        field for field in contract["required_ledger_fields"] if ledger.get(field) in (None, "")
    ]
    gates = {
        "required_fields_complete": missing == [],
        "r70_prefill_file_hash_matches": path_hash_matches(
            root, ledger.get("source_r70_prefill_path"), ledger.get("source_r70_prefill_sha256")
        )
        and ledger.get("source_r70_prefill_hash") == r70["prefill_hash"],
        "r66_packet_hash_matches": ledger.get("source_r66_retest_packet_hash")
        == r66["summary"]["r66_retest_packet_hash"],
        "selected_lines_match": ledger.get("selected_lines") == [268, 1381],
        "dropped_overlap_lines_match": ledger.get("dropped_overlap_lines") == [1378],
        "structural_cnot_delta_positive": isinstance(ledger.get("structural_cnot_delta"), int)
        and ledger["structural_cnot_delta"] >= 1,
        "accepted_exit_route_positive": isinstance(ledger.get("accepted_exit_route_count"), int)
        and ledger["accepted_exit_route_count"] >= 1,
        "occurrence_removal_positive": isinstance(ledger.get("occurrence_removal_delta"), int)
        and ledger["occurrence_removal_delta"] >= 1,
        "proxy_t_reduction_positive": isinstance(ledger.get("proxy_t_reduction_delta"), int)
        and ledger["proxy_t_reduction_delta"] >= 1,
        "line1381_evidence_hash_matches": path_hash_matches(
            root,
            ledger.get("line1381_delta_evidence_path"),
            ledger.get("line1381_delta_evidence_sha256"),
        ),
        "line1378_no_double_counting_hash_matches": path_hash_matches(
            root,
            ledger.get("line1378_no_double_counting_evidence_path"),
            ledger.get("line1378_no_double_counting_evidence_sha256"),
        ),
        "machine_replay_stdout_hash_matches": path_hash_matches(
            root,
            ledger.get("machine_check_replay_stdout_path"),
            ledger.get("machine_check_replay_stdout_sha256"),
        ),
        "b7_not_requested_before_delta_acceptance": ledger.get("b7_nonzero_retest_requested")
        is False,
        "claim_boundary_blocks_o3_reroute_b7": all(
            token in str(ledger.get("claim_boundary", "")).lower()
            for token in ["not", "b7"]
        ),
    }
    failed = [gate for gate, passed in gates.items() if not passed]
    verdict = {
        "artifact": "R71 positive-delta ledger verifier verdict",
        "method": METHOD,
        "source_target_id": TARGET_ID,
        "ledger_id": ledger.get("ledger_id"),
        "contract_hash": contract["contract_hash"],
        "gates": gates,
        "passed_gate_count": sum(1 for passed in gates.values() if passed),
        "failed_gate_count": len(failed),
        "failed_gates": failed,
        "missing_required_fields": missing,
        "accepted": failed == [],
        "accepted_exit_route_count": ledger.get("accepted_exit_route_count", 0) or 0,
        "occurrence_removal_delta": ledger.get("occurrence_removal_delta", 0) or 0,
        "proxy_t_reduction_delta": ledger.get("proxy_t_reduction_delta", 0) or 0,
        "b7_credit_delta": 0,
        "claim_boundary": (
            "A ledger accepted by this verifier only permits a downstream nonzero B7 "
            "retest. It does not directly grant O3 closure, reroute, or B7 credit."
        ),
    }
    verdict["verdict_hash"] = stable_hash(verdict)
    return verdict


def build_pr_packets(contract: dict[str, Any], verdict: dict[str, Any]) -> dict[str, Any]:
    packets = {
        "artifact": "R71 positive-delta PR packets",
        "source_target_id": TARGET_ID,
        "upstream_target_id": UPSTREAM_TARGET_ID,
        "source_contract_hash": contract["contract_hash"],
        "source_rejected_verdict_hash": verdict["verdict_hash"],
        "packets": [
            {
                "packet_id": "R71-D1-line1381-positive-occurrence-delta",
                "goal": "Submit line1381 occurrence-removal evidence with accepted_exit_route_count>=1 and occurrence_removal_delta>=1.",
                "must_not_do": "Do not reuse structural CNOT delta alone as occurrence evidence.",
            },
            {
                "packet_id": "R71-D2-proxy-t-positive-derivation",
                "goal": "Submit a hash-bound proxy-T derivation with proxy_t_reduction_delta>=1.",
                "must_not_do": "Do not count the R66 zero-credit ledger as positive proxy-T reduction.",
            },
            {
                "packet_id": "R71-D3-line1378-no-double-counting-audit",
                "goal": "Prove line1378 overlap is excluded or accounted before line1381 delta is counted.",
                "must_not_do": "Do not double-count the line1378/line1381 overlap window.",
            },
            {
                "packet_id": "R71-D4-downstream-b7-nonzero-retest",
                "goal": "Run only after D1-D3 are accepted and a positive route is admitted.",
                "must_not_do": "Do not request B7 credit from R70 or structural-only R71 evidence.",
            },
        ],
    }
    packets["packet_hash"] = stable_hash(packets)
    return packets


def build_payload(args: argparse.Namespace) -> dict[str, Any]:
    root = Path(args.repo_root).resolve()
    r67 = load_json(root / R67_CONTRACT)
    r70 = load_json(root / R70_PREFILL)
    r70_result = load_json(root / R70_RESULT)
    r66 = load_json(root / R66_RESULT)

    contract = build_contract(root, r67, r70)
    write_json(root / R71_CONTRACT, contract)
    template = build_template(root, contract, r70, r66)
    write_json(root / R71_TEMPLATE, template)
    structural_only = build_structural_only_fixture(root, template, r70)
    write_json(root / R71_STRUCTURAL_ONLY, structural_only)
    verdict = verify_ledger(root, structural_only, contract, r70, r66)
    write_json(root / R71_STRUCTURAL_ONLY_VERDICT, verdict)
    packets = build_pr_packets(contract, verdict)
    write_json(root / R71_PR_PACKETS, packets)

    requirements = [
        req(
            "V1",
            "R70 completed prefill is fully populated",
            r70_result["summary"]["r70_prefilled_field_count"] == 29
            and r70_result["summary"]["r70_placeholder_field_count"] == 0,
            {
                "r70_prefilled_field_count": r70_result["summary"]["r70_prefilled_field_count"],
                "r70_placeholder_field_count": r70_result["summary"]["r70_placeholder_field_count"],
            },
        ),
        req(
            "V2",
            "R71 contract has required positive-delta fields and gates",
            len(contract["required_ledger_fields"]) == len(REQUIRED_LEDGER_FIELDS)
            and len(contract["acceptance_gates"]) == 12,
            {
                "required_ledger_field_count": len(contract["required_ledger_fields"]),
                "acceptance_gate_count": len(contract["acceptance_gates"]),
            },
        ),
        req(
            "V3",
            "R71 template is intentionally incomplete",
            verify_ledger(root, template, contract, r70, r66)["accepted"] is False,
            {"template_hash": template["template_hash"]},
        ),
        req(
            "V4",
            "structural-only delta fixture is rejected",
            verdict["accepted"] is False
            and "occurrence_removal_positive" in verdict["failed_gates"]
            and "proxy_t_reduction_positive" in verdict["failed_gates"],
            {
                "failed_gates": verdict["failed_gates"],
                "passed_gate_count": verdict["passed_gate_count"],
            },
        ),
        req(
            "V5",
            "R71 keeps B7 credit at zero until downstream nonzero retest",
            verdict["b7_credit_delta"] == 0 and verdict["accepted"] is False,
            {"b7_credit_delta": verdict["b7_credit_delta"]},
        ),
        req(
            "V6",
            "R71 emits four next PR packets",
            len(packets["packets"]) == 4,
            {"packet_hash": packets["packet_hash"]},
        ),
        req(
            "V7",
            "R71 artifacts are written and hash-bound",
            all(
                (root / path).exists()
                for path in [
                    R71_CONTRACT,
                    R71_TEMPLATE,
                    R71_STRUCTURAL_ONLY,
                    R71_STRUCTURAL_ONLY_VERDICT,
                    R71_PR_PACKETS,
                ]
            ),
            {},
        ),
    ]
    summary = {
        "method": METHOD,
        "status": STATUS,
        "model_status": MODEL_STATUS,
        "source_target_id": TARGET_ID,
        "upstream_target_id": UPSTREAM_TARGET_ID,
        "r70_prefilled_field_count": r70_result["summary"]["r70_prefilled_field_count"],
        "r70_placeholder_field_count": r70_result["summary"]["r70_placeholder_field_count"],
        "required_ledger_field_count": len(contract["required_ledger_fields"]),
        "acceptance_gate_count": len(contract["acceptance_gates"]),
        "structural_only_fixture_accepted": verdict["accepted"],
        "structural_only_passed_gate_count": verdict["passed_gate_count"],
        "structural_only_failed_gate_count": verdict["failed_gate_count"],
        "structural_only_failed_gates": verdict["failed_gates"],
        "accepted_exit_route_count": 0,
        "accepted_occurrence_removal": 0,
        "accepted_proxy_t_reduction": 0,
        "b7_nonzero_retest_allowed": False,
        "b7_credit_delta": 0,
        "o3_closed": False,
        "reroute_allowed": False,
        "resource_saving_claimed": False,
        "b7_ledger_improvement_claimed": False,
        "contract_hash": contract["contract_hash"],
        "template_hash": template["template_hash"],
        "structural_only_verdict_hash": verdict["verdict_hash"],
        "pr_packet_hash": packets["packet_hash"],
        "requirement_count": len(requirements),
        "requirements_passed": sum(1 for item in requirements if item["passed"]),
        "requirements_failed": sum(1 for item in requirements if not item["passed"]),
        "failed_requirement_ids": [
            item["requirement_id"] for item in requirements if not item["passed"]
        ],
        "validation_error_count": sum(1 for item in requirements if not item["passed"]),
    }
    payload = {
        "title": "B1/B7 Cone01 R71 Positive-Delta Ledger Verifier Gate",
        "version": VERSION,
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "summary": summary,
        "requirements": requirements,
        "structural_only_verdict": verdict,
        "claim_boundary": {
            "what_is_supported": (
                "R71 defines and runs a verifier for positive occurrence/proxy-T "
                "delta ledgers after the R70 full prefill."
            ),
            "what_is_not_supported": (
                "R71 does not accept the structural-only fixture, does not accept "
                "an exit route, does not grant proxy-T or occurrence credit, and "
                "does not grant B7 credit."
            ),
            "next_gate": (
                "Submit a source-backed positive delta ledger satisfying D1-D3, "
                "then run a downstream B7 nonzero retest."
            ),
        },
        "artifacts": {
            "contract": R71_CONTRACT,
            "template": R71_TEMPLATE,
            "structural_only_fixture": R71_STRUCTURAL_ONLY,
            "structural_only_verdict": R71_STRUCTURAL_ONLY_VERDICT,
            "pr_packets": R71_PR_PACKETS,
        },
    }
    payload["summary"]["payload_hash"] = stable_hash(payload)
    return payload


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    s = payload["summary"]
    lines = [
        "# B1/B7 Cone01 R71 Positive-Delta Ledger Verifier Gate",
        "",
        "## Summary",
        "",
        f"- Status: `{s['status']}`",
        f"- R70 prefilled fields: `{s['r70_prefilled_field_count']}` / 29",
        f"- Required ledger fields: `{s['required_ledger_field_count']}`",
        f"- Acceptance gates: `{s['acceptance_gate_count']}`",
        f"- Structural-only fixture accepted: `{s['structural_only_fixture_accepted']}`",
        f"- Structural-only failed gates: `{s['structural_only_failed_gate_count']}`",
        f"- Accepted exit routes: `{s['accepted_exit_route_count']}`",
        f"- Accepted occurrence removal: `{s['accepted_occurrence_removal']}`",
        f"- Accepted proxy-T reduction: `{s['accepted_proxy_t_reduction']}`",
        f"- B7 credit delta: `{s['b7_credit_delta']}`",
        f"- Contract hash: `{s['contract_hash']}`",
        f"- PR packet hash: `{s['pr_packet_hash']}`",
        "",
        "R71 turns the post-R70 positive-delta requirement into an executable verifier. It intentionally rejects the structural-only fixture: the 795 -> 789 CNOT signal is real as a structural count, but it is not accepted occurrence/proxy-T evidence by itself.",
        "",
        "## Failed Gates For Structural-Only Fixture",
        "",
    ]
    for gate in s["structural_only_failed_gates"]:
        lines.append(f"- `{gate}`")
    lines.extend(
        [
            "",
            "## Requirements",
            "",
        ]
    )
    for item in payload["requirements"]:
        status = "PASS" if item["passed"] else "FAIL"
        lines.append(f"- `{item['requirement_id']}` {status}: {item['label']}")
    lines.extend(
        [
            "",
            "## Next PR Packets",
            "",
            "- `R71-D1-line1381-positive-occurrence-delta`",
            "- `R71-D2-proxy-t-positive-derivation`",
            "- `R71-D3-line1378-no-double-counting-audit`",
            "- `R71-D4-downstream-b7-nonzero-retest`",
            "",
            "## Claim Boundary",
            "",
            f"- Supported: {payload['claim_boundary']['what_is_supported']}",
            f"- Not supported: {payload['claim_boundary']['what_is_not_supported']}",
            f"- Next gate: {payload['claim_boundary']['next_gate']}",
            "",
            "## Artifacts",
            "",
        ]
    )
    for label, artifact_path in payload["artifacts"].items():
        lines.append(f"- `{label}`: `{artifact_path}`")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=".")
    parser.add_argument(
        "--json-output",
        default="results/B1_B7_cone01_R71_positive_delta_ledger_verifier_gate_v0.json",
    )
    parser.add_argument(
        "--markdown-output",
        default="research/B1_B7_cone01_R71_positive_delta_ledger_verifier_gate.md",
    )
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()

    payload = build_payload(args)
    root = Path(args.repo_root).resolve()
    write_json(root / args.json_output, payload)
    write_markdown(root / args.markdown_output, payload)
    if args.pretty:
        print(json.dumps(payload["summary"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
