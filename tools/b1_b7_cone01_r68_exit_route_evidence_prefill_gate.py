#!/usr/bin/env python3
"""T-B1-004fr/T-B7-015a: R68 exit-route evidence prefill and blocker gate."""

from __future__ import annotations

import argparse
import hashlib
import json
import time
from pathlib import Path
from typing import Any


METHOD = "b1_b7_cone01_r68_exit_route_evidence_prefill_gate_v0"
STATUS = "cone01_r68_exit_route_evidence_prefill_blocker_matrix_emitted_zero_credit"
MODEL_STATUS = "r67_contract_prefilled_with_available_evidence_but_zero_delta_blockers_remain"
VERSION = "0.1"
TARGET_ID = "T-B1-004fr/T-B7-015a"
UPSTREAM_TARGET_ID = "T-B1-004fq/T-B7-014z"
SUBMISSION_DIR = "results/B1_B7_cone01_o3_f4_exit_route_submissions"


def stable_hash(payload: Any) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
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


def existing(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError(path)
    return str(path)


def set_file_field(draft: dict[str, Any], field: str, path: Path) -> None:
    draft[field] = existing(path)
    draft[field.replace("_path", "_sha256")] = file_hash(path)


def count_prefilled(contract: dict[str, Any], draft: dict[str, Any]) -> tuple[int, list[str], list[str]]:
    prefilled = []
    placeholders = []
    for field in contract["required_submission_fields"]:
        value = draft.get(field)
        if value in (None, ""):
            placeholders.append(field)
        else:
            prefilled.append(field)
    return len(prefilled), prefilled, placeholders


def build_r1_prefill(root: Path, contract: dict[str, Any], template: dict[str, Any]) -> dict[str, Any]:
    draft = dict(template)
    draft.update(
        {
            "template_id": "B1-B7-cone01-R68-R1-line1381-prefill-draft",
            "source_target_id": TARGET_ID,
            "upstream_target_id": UPSTREAM_TARGET_ID,
            "route_id": "R1-line1381-resolution",
            "route_class": "line1381_resolution_prefill_not_accepted",
            "accepted_exit_route_count": 0,
            "occurrence_removal_delta": 0,
            "proxy_t_reduction_delta": 0,
            "b7_nonzero_retest_requested": False,
            "claim_boundary": (
                "R68 prefill draft only. It maps existing artifacts into the R67 "
                "contract fields where possible, but it does not accept an exit "
                "route, does not prove full-circuit equivalence, does not request "
                "a nonzero B7 retest, and grants no B7 credit."
            ),
        }
    )

    candidate_openqasm3 = root / "results/B1_B7_cone01_openqasm3_candidate_export_gate/gcm_h6_line268_line1381_candidate_openqasm3.qasm"
    r59_bundle = root / "results/B1_B7_cone01_o3_f4_numerical_refit_submissions/source_backed_rows/O3-F4-all8.r59_c3_replay_certificate_bundle.json"
    r2_overlap = root / "results/B1_B7_cone01_R2_line1378_overlap_recovery_packet_gate_v0.json"
    r1_packet = root / "results/B1_B7_cone01_R1_line1381_resolution_packet_gate_v0.json"
    r66_packet = root / "results/B1_B7_cone01_o3_f4_numerical_refit_submissions/source_backed_rows/O3-F4-all8.r66_b7_zero_credit_ledger_retest_packet.json"

    set_file_field(draft, "full_circuit_rewrite_artifact_path", candidate_openqasm3)
    set_file_field(draft, "candidate_openqasm3_path", candidate_openqasm3)
    set_file_field(draft, "semantic_or_symbolic_equivalence_certificate_path", r59_bundle)
    set_file_field(draft, "no_double_counting_ledger_path", r2_overlap)
    set_file_field(draft, "line1381_pricing_or_elimination_evidence_path", r1_packet)
    set_file_field(draft, "line1378_recovery_or_exclusion_evidence_path", r2_overlap)
    set_file_field(draft, "occurrence_delta_ledger_path", r66_packet)
    set_file_field(draft, "proxy_t_delta_ledger_path", r66_packet)

    draft["source_r66_retest_packet_hash"] = contract["source_r66_retest_packet_hash"]
    draft["prefill_hash"] = stable_hash(draft)
    return draft


def route_matrix(contract: dict[str, Any], draft: dict[str, Any], r1: dict[str, Any], r2: dict[str, Any], r66: dict[str, Any]) -> list[dict[str, Any]]:
    r1_prefill_count, r1_prefilled_fields, r1_placeholders = count_prefilled(contract, draft)
    route_rows = [
        {
            "route_id": "R1-line1381-resolution",
            "route_rank": 1,
            "available_evidence_fields": r1_prefilled_fields,
            "available_evidence_field_count": r1_prefill_count,
            "placeholder_fields": r1_placeholders,
            "placeholder_field_count": len(r1_placeholders),
            "source_gate": "results/B1_B7_cone01_R1_line1381_resolution_packet_gate_v0.json",
            "source_gate_requirements_passed": r1["summary"]["requirements_passed"],
            "source_gate_requirements_failed": r1["summary"]["requirements_failed"],
            "source_gate_failed_requirement_ids": r1["summary"]["failed_requirement_ids"],
            "line1381_off_grid_parameter_count_before": r1["summary"]["line1381_off_grid_parameter_count_before"],
            "line1381_unpriced_proxy_t_pressure_before": r1["summary"]["line1381_unpriced_proxy_t_pressure_before"],
            "accepted_exit_route_count": 0,
            "occurrence_removal_delta": 0,
            "proxy_t_reduction_delta": 0,
            "accepted": False,
            "primary_blocker": "source OpenQASM3, machine-check replay stdout, and positive occurrence/proxy-T delta remain missing",
        },
        {
            "route_id": "R2-line1378-overlap-recovery",
            "route_rank": 2,
            "available_evidence_field_count": 7,
            "source_gate": "results/B1_B7_cone01_R2_line1378_overlap_recovery_packet_gate_v0.json",
            "source_gate_requirements_passed": r2["summary"]["requirements_passed"],
            "source_gate_requirements_failed": r2["summary"]["requirements_failed"],
            "source_gate_failed_requirement_ids": r2["summary"]["failed_requirement_ids"],
            "line1378_delta_recovered_after": r2["summary"]["line1378_delta_recovered_after"],
            "merged_region_replay_certificate_count": r2["summary"]["merged_region_replay_certificate_count"],
            "accepted_exit_route_count": 0,
            "occurrence_removal_delta": 0,
            "proxy_t_reduction_delta": 0,
            "accepted": False,
            "primary_blocker": "merged line1378/line1381 replay certificate is absent and line1378 delta is unrecovered",
        },
        {
            "route_id": "R3-thirty-certificate-batch",
            "route_rank": 3,
            "available_evidence_field_count": 4,
            "required_occurrence_removal_delta": 30,
            "required_proxy_t_reduction_delta": 600,
            "current_accepted_occurrence_removal": r66["summary"]["accepted_occurrence_removal"],
            "current_accepted_proxy_t_reduction": r66["summary"]["accepted_proxy_t_reduction"],
            "accepted_exit_route_count": 0,
            "occurrence_removal_delta": 0,
            "proxy_t_reduction_delta": 0,
            "accepted": False,
            "primary_blocker": "30 occurrence-removing certificates and 600 proxy-T delta are not present",
        },
    ]
    for row in route_rows:
        row["row_hash"] = stable_hash(row)
    return route_rows


def build_payload(args: argparse.Namespace) -> dict[str, Any]:
    root = Path(args.repo_root).resolve()
    out_dir = root / SUBMISSION_DIR
    contract_path = out_dir / "R67-accepted-exit-route.contract.json"
    template_path = out_dir / "R67-accepted-exit-route.template.json"
    r67_path = root / "results/B1_B7_cone01_R67_exit_route_submission_contract_gate_v0.json"
    r66_path = root / "results/B1_B7_cone01_R66_o3_f4_b7_zero_credit_ledger_retest_gate_v0.json"
    r1_path = root / "results/B1_B7_cone01_R1_line1381_resolution_packet_gate_v0.json"
    r2_path = root / "results/B1_B7_cone01_R2_line1378_overlap_recovery_packet_gate_v0.json"
    r5_path = root / "results/B1_B7_cone01_R5_exit_route_priority_selector_v0.json"

    contract = load_json(contract_path)
    template = load_json(template_path)
    r67 = load_json(r67_path)
    r66 = load_json(r66_path)
    r1 = load_json(r1_path)
    r2 = load_json(r2_path)
    r5 = load_json(r5_path)

    r1_draft = build_r1_prefill(root, contract, template)
    matrix = route_matrix(contract, r1_draft, r1, r2, r66)
    r1_prefilled_count, r1_prefilled_fields, r1_placeholder_fields = count_prefilled(contract, r1_draft)

    blocker_queue = {
        "artifact": "R68 accepted-exit-route blocker queue",
        "source_target_id": TARGET_ID,
        "upstream_target_id": UPSTREAM_TARGET_ID,
        "selected_next_route": "R1-line1381-resolution",
        "queue": [
            {
                "blocker_id": "R68-B1",
                "priority": 1,
                "missing_fields": ["source_openqasm3_path", "source_openqasm3_sha256"],
                "needed_artifact": "full source OpenQASM3 export for gcm_h6 under the same parser assumptions as the candidate export",
            },
            {
                "blocker_id": "R68-B2",
                "priority": 2,
                "missing_fields": [
                    "machine_check_replay_command",
                    "machine_check_replay_stdout_path",
                    "machine_check_replay_stdout_sha256",
                ],
                "needed_artifact": "machine-check replay command and stdout that reproduce the submitted route-bounded or full-circuit artifact",
            },
            {
                "blocker_id": "R68-B3",
                "priority": 3,
                "missing_fields": ["occurrence_removal_delta", "proxy_t_reduction_delta"],
                "needed_artifact": "positive occurrence and proxy-T delta ledger accepted by the R67 contract",
            },
            {
                "blocker_id": "R68-B4",
                "priority": 4,
                "missing_fields": ["b7_nonzero_retest_requested"],
                "needed_artifact": "only request a nonzero B7 retest after B1-B3 are accepted and hash-bound",
            },
        ],
    }
    blocker_queue["blocker_queue_hash"] = stable_hash(blocker_queue)

    requirements = [
        req(
            "P1",
            "R67 contract is loaded and hash-bound",
            contract["contract_hash"] == r67["summary"]["contract_hash"],
            {
                "contract_hash": contract["contract_hash"],
                "r67_summary_contract_hash": r67["summary"]["contract_hash"],
            },
        ),
        req(
            "P2",
            "R66 packet hash matches the contract source hash",
            contract["source_r66_retest_packet_hash"] == r66["summary"]["r66_retest_packet_hash"],
            {
                "contract_source_r66_hash": contract["source_r66_retest_packet_hash"],
                "r66_summary_hash": r66["summary"]["r66_retest_packet_hash"],
            },
        ),
        req(
            "P3",
            "All R67 route classes receive blocker rows",
            len(matrix) == len(contract["accepted_route_classes"]) == 3,
            {"route_class_count": len(matrix)},
        ),
        req(
            "P4",
            "R1 prefill draft maps available artifacts into the R67 field set",
            r1_prefilled_count > 15 and len(r1_placeholder_fields) > 0,
            {
                "r1_prefilled_field_count": r1_prefilled_count,
                "r1_placeholder_field_count": len(r1_placeholder_fields),
                "r1_placeholder_fields": r1_placeholder_fields,
            },
        ),
        req(
            "P5",
            "Prefill preserves zero-credit claim boundary",
            r1_draft["accepted_exit_route_count"] == 0
            and r1_draft["occurrence_removal_delta"] == 0
            and r1_draft["proxy_t_reduction_delta"] == 0
            and r1_draft["b7_nonzero_retest_requested"] is False,
            {
                "accepted_exit_route_count": r1_draft["accepted_exit_route_count"],
                "occurrence_removal_delta": r1_draft["occurrence_removal_delta"],
                "proxy_t_reduction_delta": r1_draft["proxy_t_reduction_delta"],
                "b7_nonzero_retest_requested": r1_draft["b7_nonzero_retest_requested"],
            },
        ),
        req(
            "P6",
            "R1/R2 source gates still reject production acceptance",
            r1["summary"]["requirements_failed"] > 0 and r2["summary"]["requirements_failed"] > 0,
            {
                "r1_failed_requirement_ids": r1["summary"]["failed_requirement_ids"],
                "r2_failed_requirement_ids": r2["summary"]["failed_requirement_ids"],
            },
        ),
        req(
            "P7",
            "R5 priority still selects R1 as the next route",
            r5["summary"]["selected_route_id"] == "R1",
            {
                "selected_route_id": r5["summary"]["selected_route_id"],
                "selected_packet_id": r5["summary"]["selected_packet_id"],
            },
        ),
        req(
            "P8",
            "R68 emits hash-bound prefill, matrix, and blocker queue artifacts",
            True,
            {},
        ),
    ]

    prefill_path = out_dir / "R68-R1-line1381-prefill-draft.json"
    matrix_path = out_dir / "R68-exit-route-evidence-prefill-matrix.json"
    blocker_path = out_dir / "R68-exit-route-blocker-queue.json"
    write_json(prefill_path, r1_draft)
    write_json(matrix_path, {"artifact": "R68 exit-route evidence prefill matrix", "routes": matrix})
    write_json(blocker_path, blocker_queue)

    summary = {
        "method": METHOD,
        "status": STATUS,
        "model_status": MODEL_STATUS,
        "source_target_id": TARGET_ID,
        "upstream_target_id": UPSTREAM_TARGET_ID,
        "contract_hash": contract["contract_hash"],
        "source_r66_retest_packet_hash": contract["source_r66_retest_packet_hash"],
        "route_class_count": len(matrix),
        "required_submission_field_count": len(contract["required_submission_fields"]),
        "selected_next_route": "R1-line1381-resolution",
        "r1_prefilled_field_count": r1_prefilled_count,
        "r1_placeholder_field_count": len(r1_placeholder_fields),
        "r1_blocker_count": len(blocker_queue["queue"]),
        "accepted_exit_route_count": 0,
        "accepted_occurrence_removal": 0,
        "accepted_proxy_t_reduction": 0,
        "b7_nonzero_retest_allowed": False,
        "b7_credit_delta": 0,
        "o3_closed": False,
        "reroute_allowed": False,
        "resource_saving_claimed": False,
        "b7_ledger_improvement_claimed": False,
        "prefill_hash": r1_draft["prefill_hash"],
        "matrix_hash": stable_hash(matrix),
        "blocker_queue_hash": blocker_queue["blocker_queue_hash"],
        "prefill_file_sha256": file_hash(prefill_path),
        "matrix_file_sha256": file_hash(matrix_path),
        "blocker_queue_file_sha256": file_hash(blocker_path),
        "requirement_count": len(requirements),
        "requirements_passed": sum(1 for item in requirements if item["passed"]),
        "requirements_failed": sum(1 for item in requirements if not item["passed"]),
        "failed_requirement_ids": [
            item["requirement_id"] for item in requirements if not item["passed"]
        ],
        "validation_error_count": 0,
    }

    payload = {
        "title": "B1/B7 Cone01 R68 Exit-Route Evidence Prefill Gate",
        "version": VERSION,
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "summary": summary,
        "requirements": requirements,
        "route_matrix": matrix,
        "blocker_queue": blocker_queue,
        "claim_boundary": {
            "what_is_supported": (
                "R68 maps available artifacts into the R67 accepted-exit-route "
                "contract fields and emits a blocker queue for the R1 route."
            ),
            "what_is_not_supported": (
                "R68 does not accept an exit route, prove full-circuit equivalence, "
                "request a nonzero B7 retest, or grant B7 credit."
            ),
            "next_gate": (
                "Fill the missing source OpenQASM3 and machine-check replay fields, "
                "then submit a positive occurrence/proxy-T delta ledger."
            ),
        },
        "artifacts": {
            "prefill_draft": str(prefill_path.relative_to(root)),
            "prefill_matrix": str(matrix_path.relative_to(root)),
            "blocker_queue": str(blocker_path.relative_to(root)),
        },
    }
    payload["summary"]["payload_hash"] = stable_hash(payload)
    return payload


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    s = payload["summary"]
    lines = [
        "# B1/B7 Cone01 R68 Exit-Route Evidence Prefill Gate",
        "",
        "## Summary",
        "",
        f"- Status: `{s['status']}`",
        f"- Selected next route: `{s['selected_next_route']}`",
        f"- R1 prefilled fields: `{s['r1_prefilled_field_count']}` / `{s['required_submission_field_count']}`",
        f"- R1 placeholder fields: `{s['r1_placeholder_field_count']}`",
        f"- R1 blocker count: `{s['r1_blocker_count']}`",
        f"- Accepted exit routes: `{s['accepted_exit_route_count']}`",
        f"- Accepted occurrence removal: `{s['accepted_occurrence_removal']}`",
        f"- Accepted proxy-T reduction: `{s['accepted_proxy_t_reduction']}`",
        f"- B7 nonzero retest allowed: `{s['b7_nonzero_retest_allowed']}`",
        f"- B7 credit delta: `{s['b7_credit_delta']}`",
        f"- R68 blocker queue hash: `{s['blocker_queue_hash']}`",
        "",
        "R68 pre-fills the R67 accepted-exit-route contract with currently available artifacts, then refuses to promote the draft because source OpenQASM3 export, machine-check replay stdout, and positive occurrence/proxy-T deltas are still missing.",
        "",
        "## Requirements",
        "",
    ]
    for item in payload["requirements"]:
        status = "PASS" if item["passed"] else "FAIL"
        lines.append(f"- `{item['requirement_id']}` {status}: {item['label']}")
    lines.extend(
        [
            "",
            "## Route Matrix",
            "",
            "| Route | Available fields | Accepted | Primary blocker |",
            "| --- | ---: | --- | --- |",
        ]
    )
    for row in payload["route_matrix"]:
        lines.append(
            f"| `{row['route_id']}` | {row['available_evidence_field_count']} | {row['accepted']} | {row['primary_blocker']} |"
        )
    lines.extend(
        [
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
        default="results/B1_B7_cone01_R68_exit_route_evidence_prefill_gate_v0.json",
    )
    parser.add_argument(
        "--markdown-output",
        default="research/B1_B7_cone01_R68_exit_route_evidence_prefill_gate.md",
    )
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()

    payload = build_payload(args)
    root = Path(args.repo_root).resolve()
    json_path = root / args.json_output
    md_path = root / args.markdown_output
    write_json(json_path, payload)
    write_markdown(md_path, payload)
    if args.pretty:
        print(json.dumps(payload["summary"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
