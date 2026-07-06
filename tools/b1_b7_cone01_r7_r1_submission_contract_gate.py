#!/usr/bin/env python3
"""T-B1-004di/T-B7-012r: R7 R1 submission contract gate."""

from __future__ import annotations

import argparse
import hashlib
import json
import time
from pathlib import Path
from typing import Any


METHOD = "b1_b7_cone01_r7_r1_submission_contract_gate_v0"
STATUS = "cone01_r7_r1_submission_contract_ready_for_external_pr"
MODEL_STATUS = "r1_line1381_submission_contract_hash_bound_to_r6_inventory"
VERSION = "0.1"
TARGET_ID = "T-B1-004di/T-B7-012r"
CONTRACT_ID = "B1-B7-cone01-R7-R1-submission-contract"
EXPECTED_R1_PACKET_ID = "B1-B7-cone01-R1-line1381-resolution"
EXPECTED_R6_METHOD = "b1_b7_cone01_r6_r1_source_evidence_inventory_gate_v0"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any], pretty: bool) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2 if pretty else None, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def stable_hash(payload: Any) -> str:
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def requirement(requirement_id: str, label: str, passed: bool, evidence: dict[str, Any]) -> dict[str, Any]:
    return {
        "requirement_id": requirement_id,
        "label": label,
        "passed": bool(passed),
        "evidence": evidence,
    }


def build_contract(
    *,
    r1: dict[str, Any],
    r6: dict[str, Any],
    submission_path: Path,
) -> dict[str, Any]:
    r1_summary = r1["summary"]
    r1_packet = r1["r1_line1381_resolution_packet"]
    r6_summary = r6["summary"]
    inventory = r6["r1_source_evidence_inventory_packet"]
    evidence_rows = [
        {
            "evidence_id": row["evidence_id"],
            "class": row["class"],
            "result_path": row["result_path"],
            "report_path": row["report_path"],
            "result_sha256": row["result_sha256"],
            "report_sha256": row["report_sha256"],
            "method": row["method"],
            "status": row["status"],
            "must_bind_in_submission": True,
        }
        for row in inventory["evidence_rows"]
    ]

    contract = {
        "contract_id": CONTRACT_ID,
        "target_submission_artifact": str(submission_path),
        "target_packet_id": EXPECTED_R1_PACKET_ID,
        "source_target_id": TARGET_ID,
        "source_r1_packet_hash": r1_summary.get("r1_packet_hash"),
        "source_r6_inventory_hash": r6_summary.get("inventory_hash"),
        "source_r6_inventory_table_hash": r6_summary.get("inventory_table_hash"),
        "source_triage_hash": r6_summary.get("triage_hash"),
        "source_acceptance_packet_hash": r6_summary.get("acceptance_packet_hash"),
        "selected_route_id": r6_summary.get("selected_route_id"),
        "selected_line_numbers": r1_summary.get("selected_line_numbers"),
        "line1381_current_boundary": {
            "off_grid_parameter_count": r6_summary.get("line1381_off_grid_parameter_count"),
            "unpriced_proxy_t_pressure": r6_summary.get("line1381_unpriced_proxy_t_pressure"),
            "accepted_occurrence_removal": r6_summary.get("accepted_occurrence_removal"),
            "accepted_proxy_t_reduction": r6_summary.get("accepted_proxy_t_reduction"),
            "b7_credit_delta": r6_summary.get("b7_credit_delta"),
        },
        "required_manifest_fields": r1_packet["required_keys"],
        "required_production_fields": r1_packet["production_required_keys"],
        "required_submission_file_classes": inventory["required_submission_files"],
        "evidence_bindings": evidence_rows,
        "acceptance_routes": [
            {
                "route_id": "A",
                "name": "parameter_elimination_with_replay_or_symbolic_equivalence",
                "required_predicates": [
                    "packet_id == B1-B7-cone01-R1-line1381-resolution",
                    "source_r6_inventory_hash matches this contract",
                    "line1381_off_grid_parameter_count_before == 5",
                    "line1381_off_grid_parameter_count_after == 0",
                    "line1381_resolution_artifact_hash is present",
                    "full_replay_or_symbolic_equivalence_hash is present",
                    "resource_delta_ledger_hash is present",
                    "no_double_counting_ledger_hash is present",
                    "all six evidence rows are referenced by hash",
                ],
                "accepted_before_resource_escape_packet": False,
            },
            {
                "route_id": "B",
                "name": "physical_pricing_replay_beats_boundary",
                "required_predicates": [
                    "packet_id == B1-B7-cone01-R1-line1381-resolution",
                    "source_r6_inventory_hash matches this contract",
                    "physical_pricing_replay.cost_minus_credit <= 0",
                    "physical_pricing_replay_hash is present",
                    "resource_delta_ledger_hash is present",
                    "no_double_counting_ledger_hash is present",
                    "all six evidence rows are referenced by hash",
                    "claim boundary forbids B7 credit until resource-escape acceptance accepts the route",
                ],
                "accepted_before_resource_escape_packet": False,
            },
        ],
        "negative_result_route": {
            "accepted_as_r1_solution": False,
            "useful_if": (
                "A checked impossibility or pricing-dominance lemma shows the selected R1 line1381 "
                "route should be abandoned and R5 should be rerun against R2/R3/R4."
            ),
            "required_artifacts": [
                "negative_lemma_or_counterexample",
                "source_evidence_binding_table",
                "claim_boundary_note",
                "reroute_recommendation",
            ],
        },
        "forbidden_claims_before_acceptance": {
            "resource_saving_claimed": False,
            "b7_ledger_improvement_claimed": False,
            "b7_space_time_volume_credit": 0,
            "accepted_occurrence_removal": 0,
            "accepted_proxy_t_reduction": 0,
        },
    }
    contract["contract_hash"] = stable_hash(contract)
    return contract


def build_payload(args: argparse.Namespace) -> dict[str, Any]:
    started = time.time()
    r1 = load_json(args.r1_gate)
    r6 = load_json(args.r6_inventory)
    r1_summary = r1["summary"]
    r6_summary = r6["summary"]
    inventory = r6["r1_source_evidence_inventory_packet"]
    submission_path = args.submission_dir / f"{EXPECTED_R1_PACKET_ID}.json"
    contract_path = args.submission_dir / f"{EXPECTED_R1_PACKET_ID}.contract.json"
    contract = build_contract(r1=r1, r6=r6, submission_path=submission_path)

    evidence_rows = contract["evidence_bindings"]
    required_files = contract["required_submission_file_classes"]
    route_a = contract["acceptance_routes"][0]
    route_b = contract["acceptance_routes"][1]
    forbidden = contract["forbidden_claims_before_acceptance"]
    required_hash_fields = [
        "source_r1_packet_hash",
        "source_r6_inventory_hash",
        "source_r6_inventory_table_hash",
        "source_triage_hash",
        "source_acceptance_packet_hash",
        "contract_hash",
    ]
    missing_contract_hash_fields = [
        field for field in required_hash_fields if not contract.get(field)
    ]

    requirements = [
        requirement(
            "C1",
            "R6 inventory is current and source-bound to R1",
            r6.get("method") == EXPECTED_R6_METHOD
            and r6_summary.get("selected_route_id") == "R1"
            and r6_summary.get("r1_packet_id") == EXPECTED_R1_PACKET_ID
            and r6_summary.get("requirements_failed") == 0,
            {
                "r6_method": r6.get("method"),
                "selected_route_id": r6_summary.get("selected_route_id"),
                "r1_packet_id": r6_summary.get("r1_packet_id"),
                "r6_requirements_failed": r6_summary.get("requirements_failed"),
            },
        ),
        requirement(
            "C2",
            "The real R1 submission artifact is still absent",
            not submission_path.exists()
            and r1_summary.get("submitted_r1_artifact_exists") is False,
            {
                "target_submission_artifact": str(submission_path),
                "target_submission_exists": submission_path.exists(),
                "r1_submitted_artifact_exists": r1_summary.get("submitted_r1_artifact_exists"),
            },
        ),
        requirement(
            "C3",
            "Contract is non-conflicting and points at a separate .contract.json artifact",
            contract_path.name.endswith(".contract.json")
            and contract_path != submission_path
            and contract["target_submission_artifact"] == str(submission_path),
            {
                "contract_path": str(contract_path),
                "submission_path": str(submission_path),
            },
        ),
        requirement(
            "C4",
            "All six R6 evidence rows are hash-bound in the contract",
            len(evidence_rows) == 6
            and all(row.get("result_sha256") and row.get("report_sha256") for row in evidence_rows),
            {
                "evidence_row_count": len(evidence_rows),
                "missing_hash_rows": [
                    row["evidence_id"]
                    for row in evidence_rows
                    if not row.get("result_sha256") or not row.get("report_sha256")
                ],
            },
        ),
        requirement(
            "C5",
            "All eight missing R1 submission file classes are represented",
            len(required_files) == 8
            and required_files == inventory.get("required_submission_files"),
            {
                "required_submission_file_count": len(required_files),
                "source_required_submission_file_count": len(
                    inventory.get("required_submission_files", [])
                ),
            },
        ),
        requirement(
            "C6",
            "Route A requires eliminating all five line1381 off-grid parameters",
            route_a["route_id"] == "A"
            and any("line1381_off_grid_parameter_count_after == 0" in item for item in route_a["required_predicates"])
            and any("full_replay_or_symbolic_equivalence_hash" in item for item in route_a["required_predicates"]),
            {"route_a_predicates": route_a["required_predicates"]},
        ),
        requirement(
            "C7",
            "Route B requires honest physical pricing to beat the current boundary",
            route_b["route_id"] == "B"
            and any("cost_minus_credit <= 0" in item for item in route_b["required_predicates"])
            and any("no_double_counting_ledger_hash" in item for item in route_b["required_predicates"]),
            {"route_b_predicates": route_b["required_predicates"]},
        ),
        requirement(
            "C8",
            "Forbidden B1/B7 claims remain impossible inside the contract",
            forbidden.get("resource_saving_claimed") is False
            and forbidden.get("b7_ledger_improvement_claimed") is False
            and forbidden.get("b7_space_time_volume_credit") == 0
            and forbidden.get("accepted_occurrence_removal") == 0
            and forbidden.get("accepted_proxy_t_reduction") == 0,
            forbidden,
        ),
        requirement(
            "C9",
            "Negative R1 evidence can be submitted without pretending to solve R1",
            contract["negative_result_route"]["accepted_as_r1_solution"] is False
            and len(contract["negative_result_route"]["required_artifacts"]) == 4,
            contract["negative_result_route"],
        ),
        requirement(
            "C10",
            "Contract is hash-bound to R1, R6, triage, and acceptance packet sources",
            not missing_contract_hash_fields,
            {"missing_contract_hash_fields": missing_contract_hash_fields},
        ),
    ]

    passed = sum(row["passed"] for row in requirements)
    failed_ids = [row["requirement_id"] for row in requirements if not row["passed"]]
    validation_errors: list[str] = []
    if failed_ids:
        validation_errors.append(f"unexpected R7 contract failures: {failed_ids}")

    summary = {
        "contract_id": CONTRACT_ID,
        "contract_hash": contract["contract_hash"],
        "contract_path": str(contract_path),
        "target_submission_artifact": str(submission_path),
        "target_submission_exists": submission_path.exists(),
        "r1_packet_id": EXPECTED_R1_PACKET_ID,
        "r1_packet_hash": r1_summary.get("r1_packet_hash"),
        "r6_inventory_hash": r6_summary.get("inventory_hash"),
        "r6_inventory_table_hash": r6_summary.get("inventory_table_hash"),
        "indexed_evidence_row_count": len(evidence_rows),
        "required_submission_file_count": len(required_files),
        "acceptance_route_count": len(contract["acceptance_routes"]),
        "negative_result_route_available": True,
        "line1381_off_grid_parameter_count": r6_summary.get("line1381_off_grid_parameter_count"),
        "line1381_unpriced_proxy_t_pressure": r6_summary.get(
            "line1381_unpriced_proxy_t_pressure"
        ),
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
        "title": "B1/B7 Cone01 R7 R1 Submission Contract Gate",
        "version": VERSION,
        "last_updated": args.last_updated,
        "method": METHOD,
        "status": STATUS,
        "model_status": MODEL_STATUS,
        "source_r1_gate": str(args.r1_gate),
        "source_r6_inventory": str(args.r6_inventory),
        "summary": summary,
        "r1_submission_contract": contract,
        "requirements": requirements,
        "claim_boundary": {
            "what_is_supported": (
                "R7 creates a hash-bound R1 submission contract that external PRs can satisfy or refute."
            ),
            "what_is_not_supported": (
                "No submitted R1 resolution artifact, line1381 parameter elimination, physical-pricing "
                "win, accepted exit route, occurrence removal, proxy-T reduction, B7 credit, or resource "
                "saving is supported."
            ),
            "next_gate": (
                "Submit the target R1 artifact against this contract, either by eliminating all five "
                "line1381 off-grid parameters with replay/symbolic equivalence or by providing a "
                "physical-pricing replay with cost-minus-credit <= 0."
            ),
            "resource_saving_claimed": False,
            "b7_ledger_improvement_claimed": False,
        },
        "validation_errors": validation_errors,
        "runtime_seconds": round(time.time() - started, 6),
    }


def render_markdown(payload: dict[str, Any]) -> str:
    s = payload["summary"]
    contract = payload["r1_submission_contract"]
    lines = [
        f"# {payload['title']}",
        "",
        f"- Target: `{payload['source_target_id']}`",
        f"- Method: `{payload['method']}`",
        f"- Status: `{payload['status']}`",
        f"- Contract: `{s['contract_id']}`",
        f"- Contract hash: `{s['contract_hash']}`",
        f"- Contract path: `{s['contract_path']}`",
        f"- Target submission: `{s['target_submission_artifact']}`",
        "",
        "## Result",
        "",
        (
            f"The R7 contract gate passes {s['requirements_passed']}/{s['requirement_count']} "
            "requirements. It creates a separate contract artifact for the next R1 PR while keeping "
            "the real R1 submission absent and B7 credit at zero."
        ),
        "",
        "## Acceptance Routes",
        "",
    ]
    for route in contract["acceptance_routes"]:
        lines.extend([f"### Route {route['route_id']} - {route['name']}", ""])
        for item in route["required_predicates"]:
            lines.append(f"- {item}")
        lines.append("")
    lines.extend(["## Evidence Bindings", ""])
    for row in contract["evidence_bindings"]:
        lines.append(
            f"- `{row['evidence_id']}` {row['class']} -> result `{row['result_sha256']}`, report `{row['report_sha256']}`"
        )
    lines.extend(["", "## Required Submission File Classes", ""])
    for item in contract["required_submission_file_classes"]:
        lines.append(f"- {item}")
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            f"- line1381 off-grid parameters: `{s['line1381_off_grid_parameter_count']}`",
            f"- line1381 unpriced proxy-T pressure: `{s['line1381_unpriced_proxy_t_pressure']}`",
            f"- Target submission exists: `{s['target_submission_exists']}`",
            f"- Accepted occurrence / proxy-T reduction: `{s['accepted_occurrence_removal']}` / `{s['accepted_proxy_t_reduction']}`",
            f"- B7 credit delta / STV credit: `{s['b7_credit_delta']}` / `{s['b7_space_time_volume_credit']}`",
            "",
            "## Requirement Results",
            "",
        ]
    )
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
            "This contract gate does not claim resource saving, occurrence removal, proxy-T reduction, B7 ledger improvement, FT resource credit, or a solved B1/B7 problem.",
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
        "--r1-gate",
        type=Path,
        default=Path("results/B1_B7_cone01_R1_line1381_resolution_packet_gate_v0.json"),
    )
    parser.add_argument(
        "--r6-inventory",
        type=Path,
        default=Path("results/B1_B7_cone01_R6_r1_source_evidence_inventory_gate_v0.json"),
    )
    parser.add_argument(
        "--submission-dir",
        type=Path,
        default=Path("results/B1_B7_cone01_r1_line1381_resolution_submissions"),
    )
    parser.add_argument(
        "--json-output",
        type=Path,
        default=Path("results/B1_B7_cone01_R7_r1_submission_contract_gate_v0.json"),
    )
    parser.add_argument(
        "--markdown-output",
        type=Path,
        default=Path("research/B1_B7_cone01_R7_r1_submission_contract_gate.md"),
    )
    parser.add_argument("--last-updated", default="2026-07-06")
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()

    payload = build_payload(args)
    contract_path = Path(payload["summary"]["contract_path"])
    write_json(contract_path, payload["r1_submission_contract"], args.pretty)
    write_json(args.json_output, payload, args.pretty)
    args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_output.write_text(render_markdown(payload), encoding="utf-8")
    print(
        json.dumps(
            {
                "status": payload["status"],
                "contract_hash": payload["summary"]["contract_hash"],
                "indexed_evidence_row_count": payload["summary"]["indexed_evidence_row_count"],
                "required_submission_file_count": payload["summary"][
                    "required_submission_file_count"
                ],
                "requirements_passed": payload["summary"]["requirements_passed"],
                "requirements_failed": payload["summary"]["requirements_failed"],
                "validation_error_count": payload["summary"]["validation_error_count"],
                "contract_output": str(contract_path),
                "json_output": str(args.json_output),
                "markdown_output": str(args.markdown_output),
            },
            indent=2,
            sort_keys=True,
        )
    )
    if payload["validation_errors"]:
        raise SystemExit("B1/B7 R7 R1 submission contract gate validation failed")


if __name__ == "__main__":
    main()
