#!/usr/bin/env python3
"""T-B1-004fj/T-B7-014s: R60 C4/C5 same-access denominator contract gate."""

from __future__ import annotations

import argparse
import hashlib
import json
import time
from pathlib import Path
from typing import Any


METHOD = "b1_b7_cone01_r60_o3_f4_c4_c5_same_access_denominator_contract_gate_v0"
STATUS = "cone01_r60_c4_c5_same_access_denominator_contract_emitted_zero_b7_credit"
MODEL_STATUS = "o3_f4_c4_c5_denominator_contract_ready_no_denominator_rows_accepted"
VERSION = "0.1"
TARGET_ID = "T-B1-004fj/T-B7-014s"
UPSTREAM_TARGET_ID = "T-B1-004fi/T-B7-014r"
R60_ACCEPTANCE_SCHEMA_VERSION = "r60_c4_c5_same_access_denominator_row_v0"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def stable_hash(payload: Any) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def req(requirement_id: str, label: str, passed: bool, evidence: dict[str, Any]) -> dict[str, Any]:
    return {
        "requirement_id": requirement_id,
        "label": label,
        "passed": bool(passed),
        "evidence": evidence,
    }


def out_dir(root: Path) -> Path:
    return root / "results/B1_B7_cone01_o3_f4_numerical_refit_submissions/source_backed_rows"


def build_template(root: Path, certificate: dict[str, Any]) -> dict[str, Any]:
    challenge_id = certificate["challenge_id"]
    required_fields = [
        "challenge_id",
        "acceptance_schema_version",
        "denominator_method_id",
        "denominator_implementation_path",
        "reproducible_command",
        "access_model_hash",
        "same_access_statement",
        "source_circuit_file",
        "source_circuit_sha256",
        "candidate_circuit_file",
        "candidate_circuit_sha256",
        "r59_certificate_file",
        "r59_certificate_hash",
        "unitary_distance_metric",
        "strict_tolerance",
        "denominator_distance",
        "denominator_cost_units",
        "denominator_cost_value",
        "denominator_beats_r59_positive_distance",
        "denominator_rejects_r59_negative_control_pressure",
        "leakage_audit_statement",
        "verifier_transcript_path",
        "verifier_transcript_sha256",
        "claim_boundary",
    ]
    access_model = {
        "challenge_id": challenge_id,
        "allowed_inputs": [
            certificate["source_circuit_file"],
            certificate["candidate_circuit_file"],
            certificate["certificate_file"],
        ],
        "forbidden_inputs": [
            "future C6 optimizer traces",
            "hidden solver traces not listed in this template",
            "hardware calibration data",
            "unbound external oracles",
            "manual post-hoc angle edits",
        ],
        "same_access_rules": [
            "use the same source and candidate OpenQASM 3.0 files that R59 hash-bound",
            "use the same single_qubit_rz_operator_norm metric and strict tolerance",
            "echo all R59 source/candidate/certificate hashes exactly",
            "submit a verifier transcript and implementation path before acceptance",
            "state whether the denominator beats the R59 positive distance and negative-control pressure",
        ],
    }
    template = {
        "artifact": "R60 C4/C5 same-access denominator submission template",
        "challenge_id": challenge_id,
        "source_target_id": TARGET_ID,
        "upstream_target_id": UPSTREAM_TARGET_ID,
        "method": METHOD,
        "acceptance_schema_version": R60_ACCEPTANCE_SCHEMA_VERSION,
        "required_fields": required_fields,
        "required_field_count": len(required_fields),
        "access_model": access_model,
        "access_model_hash": stable_hash(access_model),
        "r59_certificate_file": certificate["certificate_file"],
        "r59_certificate_hash": certificate["certificate_hash"],
        "r59_certificate_file_sha256": certificate["certificate_file_sha256"],
        "source_circuit_file": certificate["source_circuit_file"],
        "source_circuit_sha256": certificate["source_circuit_sha256"],
        "candidate_circuit_file": certificate["candidate_circuit_file"],
        "candidate_circuit_sha256": certificate["candidate_circuit_sha256"],
        "unitary_distance_metric": certificate["unitary_distance_metric"],
        "strict_tolerance": certificate["strict_tolerance"],
        "r59_positive_replay_distance": certificate["positive_replay_distance"],
        "acceptance_conditions": {
            "same_access_statement_required": True,
            "hash_echo_required": True,
            "verifier_transcript_required": True,
            "leakage_audit_required": True,
            "denominator_distance_must_be_finite": True,
            "denominator_must_not_use_forbidden_inputs": True,
            "no_b7_credit_from_template": True,
        },
        "submitted_denominator_row": None,
        "denominator_row_submitted": False,
        "denominator_row_accepted": False,
        "blocking_reason": (
            "No source-backed same-access denominator row has been submitted for this "
            "challenge. This template is a contract, not a denominator win."
        ),
        "claim_boundary": (
            "Template only; no C4/C5 denominator comparison completion, no O3 closure, "
            "no reroute, no B7 credit, and no STV credit."
        ),
    }
    template["template_hash"] = stable_hash(template)
    template_file = out_dir(root) / f"{challenge_id}.r60_c4_c5_denominator_submission_template.json"
    write_json(template_file, template)
    template["template_file"] = str(template_file.relative_to(root))
    template["template_file_sha256"] = file_hash(template_file)
    return template


def build_payload(args: argparse.Namespace) -> dict[str, Any]:
    started = time.time()
    r59 = load_json(args.r59_result)
    r59_summary = r59["summary"]
    certificates = sorted(
        r59["r59_c3_replay_certificate_packet"]["certificates"],
        key=lambda item: item["challenge_id"],
    )
    templates = [build_template(args.root, item) for item in certificates]
    submitted_rows = [item for item in templates if item["denominator_row_submitted"]]
    accepted_rows = [item for item in templates if item["denominator_row_accepted"]]
    contract = {
        "artifact": "R60 C4/C5 all-row same-access denominator contract bundle",
        "source_target_id": TARGET_ID,
        "upstream_target_id": UPSTREAM_TARGET_ID,
        "method": METHOD,
        "acceptance_schema_version": R60_ACCEPTANCE_SCHEMA_VERSION,
        "source_r59_result": str(args.r59_result),
        "source_r59_file_sha256": file_hash(args.r59_result),
        "source_r59_bundle_hash": r59_summary["r59_bundle_hash"],
        "source_r59_c3_complete": r59_summary["c3_same_unitary_replay_certificate_complete"],
        "strict_tolerance": r59_summary["strict_tolerance"],
        "row_count": len(templates),
        "template_count": len(templates),
        "submitted_denominator_row_count": len(submitted_rows),
        "accepted_denominator_row_count": len(accepted_rows),
        "blocked_denominator_row_count": len(templates) - len(accepted_rows),
        "required_acceptance_schema_fields": templates[0]["required_fields"] if templates else [],
        "required_acceptance_schema_field_count": templates[0]["required_field_count"]
        if templates
        else 0,
        "template_hashes": {item["challenge_id"]: item["template_hash"] for item in templates},
        "template_files": {item["challenge_id"]: item["template_file"] for item in templates},
        "template_file_sha256": {
            item["challenge_id"]: item["template_file_sha256"] for item in templates
        },
        "c4_c5_same_access_denominator_contract_emitted": len(templates) == 8,
        "c4_c5_same_access_denominator_comparison_complete": False,
        "c6_leakage_free_optimizer_trace_complete": False,
        "c7_machine_check_replay_bundle_complete": False,
        "o3_closed": False,
        "reroute_allowed": False,
        "b7_credit_delta": 0,
        "b7_space_time_volume_credit": 0,
        "resource_saving_claimed": False,
        "b7_ledger_improvement_claimed": False,
        "claim_boundary": (
            "R60 emits the C4/C5 denominator contract and eight row templates. It does "
            "not accept a denominator row, complete C4/C5, close O3, reroute, or grant "
            "B7/STV/resource credit."
        ),
    }
    contract["contract_hash"] = stable_hash(contract)
    write_json(args.contract_output, contract)
    zero_credit_ok = (
        r59_summary["o3_closed"] is False
        and r59_summary["reroute_allowed"] is False
        and r59_summary["b7_credit_delta"] == 0
        and r59_summary["b7_space_time_volume_credit"] == 0
        and r59_summary["resource_saving_claimed"] is False
        and r59_summary["b7_ledger_improvement_claimed"] is False
    )
    requirements = [
        req(
            "D1",
            "R59 upstream completed C3 for all 8 rows and still has zero B7 credit",
            r59_summary["c3_same_unitary_replay_certificate_complete"] is True
            and r59_summary["row_count"] == 8
            and zero_credit_ok,
            {
                "r59_row_count": r59_summary["row_count"],
                "r59_c3_complete": r59_summary["c3_same_unitary_replay_certificate_complete"],
                "zero_credit_ok": zero_credit_ok,
            },
        ),
        req(
            "D2",
            "R60 emits one denominator submission template for each R59 row",
            len(templates) == 8
            and len({item["challenge_id"] for item in templates}) == 8
            and all(item["template_file_sha256"] for item in templates),
            {
                "template_count": len(templates),
                "challenge_ids": [item["challenge_id"] for item in templates],
            },
        ),
        req(
            "D3",
            "Each template is bound to the R59 source, candidate, and certificate hashes",
            all(
                item["source_circuit_sha256"]
                and item["candidate_circuit_sha256"]
                and item["r59_certificate_hash"]
                and item["r59_certificate_file_sha256"]
                for item in templates
            ),
            {
                "missing_hash_bindings": [
                    item["challenge_id"]
                    for item in templates
                    if not (
                        item["source_circuit_sha256"]
                        and item["candidate_circuit_sha256"]
                        and item["r59_certificate_hash"]
                        and item["r59_certificate_file_sha256"]
                    )
                ]
            },
        ),
        req(
            "D4",
            "The same-access schema forbids hidden traces, external oracles, and unbound inputs",
            all(
                "unbound external oracles" in item["access_model"]["forbidden_inputs"]
                and "hardware calibration data" in item["access_model"]["forbidden_inputs"]
                for item in templates
            ),
            {
                "access_model_hashes": {
                    item["challenge_id"]: item["access_model_hash"] for item in templates
                }
            },
        ),
        req(
            "D5",
            "The denominator acceptance schema exposes all required review fields",
            contract["required_acceptance_schema_field_count"] == 24
            and all(item["required_field_count"] == 24 for item in templates),
            {
                "required_acceptance_schema_field_count": contract[
                    "required_acceptance_schema_field_count"
                ],
                "required_fields": contract["required_acceptance_schema_fields"],
            },
        ),
        req(
            "D6",
            "No denominator row is accepted yet, so C4/C5 stays incomplete",
            contract["submitted_denominator_row_count"] == 0
            and contract["accepted_denominator_row_count"] == 0
            and contract["c4_c5_same_access_denominator_comparison_complete"] is False,
            {
                "submitted_denominator_row_count": contract["submitted_denominator_row_count"],
                "accepted_denominator_row_count": contract["accepted_denominator_row_count"],
                "c4_c5_same_access_denominator_comparison_complete": contract[
                    "c4_c5_same_access_denominator_comparison_complete"
                ],
            },
        ),
        req(
            "D7",
            "R60 preserves O3/reroute/B7 zero-credit boundaries",
            zero_credit_ok
            and contract["o3_closed"] is False
            and contract["reroute_allowed"] is False
            and contract["b7_credit_delta"] == 0,
            {
                "o3_closed": contract["o3_closed"],
                "reroute_allowed": contract["reroute_allowed"],
                "b7_credit_delta": contract["b7_credit_delta"],
                "b7_space_time_volume_credit": contract["b7_space_time_volume_credit"],
            },
        ),
        req(
            "D8",
            "The all-row C4/C5 contract bundle is hash-bound",
            bool(contract["contract_hash"]) and file_hash(args.contract_output),
            {
                "contract_hash": contract["contract_hash"],
                "contract_file_sha256": file_hash(args.contract_output),
            },
        ),
    ]
    failed = [item["requirement_id"] for item in requirements if not item["passed"]]
    summary = {
        "source_r59_bundle_hash": r59_summary["r59_bundle_hash"],
        "source_r59_file_sha256": file_hash(args.r59_result),
        "r60_contract_hash": contract["contract_hash"],
        "r60_contract_file_sha256": file_hash(args.contract_output),
        "row_count": contract["row_count"],
        "template_count": contract["template_count"],
        "required_acceptance_schema_field_count": contract[
            "required_acceptance_schema_field_count"
        ],
        "submitted_denominator_row_count": contract["submitted_denominator_row_count"],
        "accepted_denominator_row_count": contract["accepted_denominator_row_count"],
        "blocked_denominator_row_count": contract["blocked_denominator_row_count"],
        "c3_same_unitary_replay_certificate_complete": True,
        "c4_c5_same_access_denominator_contract_emitted": contract[
            "c4_c5_same_access_denominator_contract_emitted"
        ],
        "c4_c5_same_access_denominator_comparison_complete": False,
        "c6_leakage_free_optimizer_trace_complete": False,
        "c7_machine_check_replay_bundle_complete": False,
        "o3_closed": False,
        "reroute_allowed": False,
        "b7_credit_delta": 0,
        "b7_space_time_volume_credit": 0,
        "resource_saving_claimed": False,
        "b7_ledger_improvement_claimed": False,
        "remaining_open_obligations": [
            "submit_C4_C5_same_access_denominator_rows",
            "accept_8_denominator_rows_under_R60_schema",
            "C6_leakage_free_optimizer_trace",
            "C7_machine_check_replay_bundle",
            "B7_ledger_retest_after_C4_C7",
        ],
        "remaining_open_obligation_count": 5,
        "template_hashes": contract["template_hashes"],
        "requirement_count": len(requirements),
        "requirements_passed": len(requirements) - len(failed),
        "requirements_failed": len(failed),
        "failed_requirement_ids": failed,
        "validation_error_count": len(failed),
    }
    return {
        "title": "B1/B7 Cone01 R60 O3-F4 C4/C5 Same-Access Denominator Contract Gate",
        "version": VERSION,
        "last_updated": "2026-07-08",
        "benchmark_id": "B1",
        "linked_benchmark_id": "B7",
        "method": METHOD,
        "status": STATUS,
        "model_status": MODEL_STATUS,
        "source_target_id": TARGET_ID,
        "upstream_target_id": UPSTREAM_TARGET_ID,
        "r60_c4_c5_denominator_contract_packet": {
            "source_r59_result": str(args.r59_result),
            "contract_output": str(args.contract_output),
            "contract": contract,
            "templates": templates,
        },
        "requirements": requirements,
        "summary": summary,
        "claim_boundary": {
            "what_is_supported": (
                "R60 turns the C4/C5 same-access denominator requirement into an "
                "eight-row submission contract with hash-bound source/candidate/"
                "certificate inputs, access-model hashes, forbidden-input rules, "
                "and 24 required acceptance fields."
            ),
            "what_is_not_supported": (
                "R60 does not submit or accept a denominator row, does not complete "
                "C4/C5, does not audit C6 leakage, does not produce a C7 machine-check "
                "bundle, and does not grant O3/reroute/B7/STV credit."
            ),
            "next_gate": (
                "Submit source-backed denominator rows under the R60 schema, then "
                "run the acceptance verifier before any B7 ledger retest."
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
        "# B1/B7 Cone01 R60 O3-F4 C4/C5 Same-Access Denominator Contract Gate",
        "",
        f"- Target: `{payload['source_target_id']}`",
        f"- Upstream target: `{payload['upstream_target_id']}`",
        f"- Method: `{payload['method']}`",
        f"- Status: `{payload['status']}`",
        f"- R60 contract hash: `{s['r60_contract_hash']}`",
        "",
        "## Result",
        "",
        (
            f"R60 passes {s['requirements_passed']}/{s['requirement_count']} contract "
            "requirements by emitting the C4/C5 same-access denominator schema and "
            "8 row-level submission templates. It accepts 0 denominator rows, so C4/C5, "
            "C6, C7, O3 closure, reroute, and B7 ledger credit remain blocked."
        ),
        "",
        "## Contract Evidence",
        "",
        f"- Row count: `{s['row_count']}`",
        f"- Template count: `{s['template_count']}`",
        f"- Required acceptance fields per row: `{s['required_acceptance_schema_field_count']}`",
        f"- Submitted denominator rows: `{s['submitted_denominator_row_count']}`",
        f"- Accepted denominator rows: `{s['accepted_denominator_row_count']}`",
        f"- Blocked denominator rows: `{s['blocked_denominator_row_count']}`",
        f"- C4/C5 contract emitted: `{s['c4_c5_same_access_denominator_contract_emitted']}`",
        f"- C4/C5 comparison complete: `{s['c4_c5_same_access_denominator_comparison_complete']}`",
        f"- B7 credit delta: `{s['b7_credit_delta']}`",
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
            "## Remaining Open Obligations",
            "",
        ]
    )
    for item in s["remaining_open_obligations"]:
        lines.append(f"- `{item}`")
    lines.extend(["", f"- validation_error_count: `{s['validation_error_count']}`", ""])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument(
        "--r59-result",
        type=Path,
        default=Path("results/B1_B7_cone01_R59_o3_f4_c3_same_unitary_replay_certificate_gate_v0.json"),
    )
    parser.add_argument(
        "--contract-output",
        type=Path,
        default=Path(
            "results/B1_B7_cone01_o3_f4_numerical_refit_submissions/source_backed_rows/"
            "O3-F4-all8.r60_c4_c5_denominator_contract_bundle.json"
        ),
    )
    parser.add_argument(
        "--json-output",
        type=Path,
        default=Path(
            "results/B1_B7_cone01_R60_o3_f4_c4_c5_same_access_denominator_contract_gate_v0.json"
        ),
    )
    parser.add_argument(
        "--markdown-output",
        type=Path,
        default=Path(
            "research/B1_B7_cone01_R60_o3_f4_c4_c5_same_access_denominator_contract_gate.md"
        ),
    )
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
                    "requirements_passed": s["requirements_passed"],
                    "requirements_failed": s["requirements_failed"],
                    "row_count": s["row_count"],
                    "template_count": s["template_count"],
                    "submitted_denominator_row_count": s[
                        "submitted_denominator_row_count"
                    ],
                    "accepted_denominator_row_count": s[
                        "accepted_denominator_row_count"
                    ],
                    "c4_c5_same_access_denominator_contract_emitted": s[
                        "c4_c5_same_access_denominator_contract_emitted"
                    ],
                    "c4_c5_same_access_denominator_comparison_complete": s[
                        "c4_c5_same_access_denominator_comparison_complete"
                    ],
                    "o3_closed": s["o3_closed"],
                    "reroute_allowed": s["reroute_allowed"],
                    "b7_credit_delta": s["b7_credit_delta"],
                    "r60_contract_hash": s["r60_contract_hash"],
                    "json_output": str(args.json_output),
                },
                indent=2,
                sort_keys=True,
            )
        )


if __name__ == "__main__":
    main()
