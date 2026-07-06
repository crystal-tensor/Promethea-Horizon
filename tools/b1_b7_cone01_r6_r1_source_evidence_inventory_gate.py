#!/usr/bin/env python3
"""T-B1-004dh/T-B7-012q: R6 R1 source-evidence inventory gate."""

from __future__ import annotations

import argparse
import hashlib
import json
import time
from pathlib import Path
from typing import Any


METHOD = "b1_b7_cone01_r6_r1_source_evidence_inventory_gate_v0"
STATUS = "cone01_r6_r1_source_evidence_inventory_ready_missing_submission"
MODEL_STATUS = "r1_line1381_existing_evidence_indexed_but_resolution_artifact_missing"
VERSION = "0.1"
INVENTORY_ID = "B1-B7-cone01-R6-R1-source-evidence-inventory"
EXPECTED_R1_PACKET_ID = "B1-B7-cone01-R1-line1381-resolution"


SOURCE_EVIDENCE = [
    {
        "evidence_id": "E1",
        "class": "line1381_repaired_packet_candidate",
        "result_path": "results/B1_B7_cone01_five_parameter_line1381_exact_repair_gate_v0.json",
        "report_path": "research/B1_B7_cone01_five_parameter_line1381_exact_repair_gate.md",
        "why_it_matters": "Line 1381 has a bounded five-parameter exact packet repair candidate.",
    },
    {
        "evidence_id": "E2",
        "class": "line1381_local_u3_pricing_boundary",
        "result_path": "results/B1_B7_cone01_line1381_local_u3_pricing_gate_v0.json",
        "report_path": "research/B1_B7_cone01_line1381_local_u3_pricing_gate.md",
        "why_it_matters": "The exact packet still carries five off-grid local-U3 parameters and 100 proxy-T pressure.",
    },
    {
        "evidence_id": "E3",
        "class": "physical_synthesis_pricing_rejection",
        "result_path": "results/B1_B7_cone01_physical_synthesis_pricing_gate_v0.json",
        "report_path": "research/B1_B7_cone01_physical_synthesis_pricing_gate.md",
        "why_it_matters": "Physical synthesis pricing rejects line1381 B7 credit under current evidence.",
    },
    {
        "evidence_id": "E4",
        "class": "openqasm3_qiskit_loader_evidence_seal",
        "result_path": "results/B1_B7_cone01_openqasm3_qiskit_loader_evidence_seal_gate_v0.json",
        "report_path": "research/B1_B7_cone01_openqasm3_qiskit_loader_evidence_seal_gate.md",
        "why_it_matters": "OpenQASM 3/Qiskit loader evidence is replayable but does not accept local-U3 pricing.",
    },
    {
        "evidence_id": "E5",
        "class": "openqasm3_seeded_product_replay",
        "result_path": "results/B1_B7_cone01_openqasm3_qiskit_loader_seeded_product_replay_gate_v0.json",
        "report_path": "research/B1_B7_cone01_openqasm3_qiskit_loader_seeded_product_replay_gate.md",
        "why_it_matters": "Seeded product replay passes while still forbidding resource credit.",
    },
    {
        "evidence_id": "E6",
        "class": "seeded_resource_boundary",
        "result_path": "results/B1_B7_cone01_openqasm3_qiskit_loader_seeded_resource_boundary_gate_v0.json",
        "report_path": "research/B1_B7_cone01_openqasm3_qiskit_loader_seeded_resource_boundary_gate.md",
        "why_it_matters": "The seeded resource boundary names line1381 as a failed blocker with zero B7 credit.",
    },
]


REQUIRED_R1_SUBMISSION_FILES = [
    "line1381_resolution_manifest",
    "line1381_rewritten_patch_or_parameter_elimination_artifact",
    "full_replay_or_symbolic_equivalence_certificate",
    "physical_pricing_replay",
    "resource_delta_ledger",
    "no_double_counting_ledger",
    "qiskit_loader_seeded_replay_reference",
    "claim_boundary_note",
]


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


def evidence_row(source: dict[str, str]) -> dict[str, Any]:
    result_path = Path(source["result_path"])
    report_path = Path(source["report_path"])
    result = load_json(result_path) if result_path.exists() else {}
    summary = result.get("summary", {})
    return {
        **source,
        "result_exists": result_path.exists(),
        "report_exists": report_path.exists(),
        "result_sha256": file_hash(result_path),
        "report_sha256": file_hash(report_path),
        "method": result.get("method"),
        "status": result.get("status"),
        "validation_error_count": summary.get("validation_error_count"),
        "accepted_occurrence_removal": summary.get("accepted_occurrence_removal"),
        "accepted_proxy_t_reduction": summary.get("accepted_proxy_t_reduction"),
        "resource_saving_claimed": summary.get("resource_saving_claimed"),
        "b7_ledger_improvement_claimed": summary.get("b7_ledger_improvement_claimed"),
        "line1381_off_grid_parameter_count": (
            summary.get("line1381_replacement_off_pi_over_four_parameter_count")
            if summary.get("line1381_replacement_off_pi_over_four_parameter_count") is not None
            else summary.get("line1381_off_grid_parameter_count")
        ),
        "line1381_proxy_t_pressure": (
            summary.get("line1381_unpriced_proxy_t_pressure")
            if summary.get("line1381_unpriced_proxy_t_pressure") is not None
            else summary.get("placeholder_proxy_t_pressure")
        ),
    }


def build_payload(args: argparse.Namespace) -> dict[str, Any]:
    started = time.time()
    r1 = load_json(args.r1_gate)
    r5 = load_json(args.r5_selector)
    r1_summary = r1["summary"]
    r5_summary = r5["summary"]
    submission_path = args.submission_dir / f"{EXPECTED_R1_PACKET_ID}.json"
    rows = [evidence_row(source) for source in SOURCE_EVIDENCE]
    inventory_table_hash = stable_hash(rows)

    available_rows = [row for row in rows if row["result_exists"] and row["report_exists"]]
    zero_credit_rows = [
        row
        for row in rows
        if row.get("accepted_occurrence_removal") == 0
        and row.get("accepted_proxy_t_reduction") == 0
        and row.get("resource_saving_claimed") is False
    ]
    blocker_rows = [
        row for row in rows if row.get("line1381_off_grid_parameter_count") == 5
    ]
    missing_submission_files = REQUIRED_R1_SUBMISSION_FILES
    inventory_packet = {
        "inventory_id": INVENTORY_ID,
        "source_r1_gate": str(args.r1_gate),
        "source_r5_selector": str(args.r5_selector),
        "r1_packet_id": EXPECTED_R1_PACKET_ID,
        "r1_packet_hash": r1_summary.get("r1_packet_hash"),
        "r5_selector_hash": r5_summary.get("selector_hash"),
        "triage_hash": r1_summary.get("triage_hash"),
        "acceptance_packet_hash": r1_summary.get("acceptance_packet_hash"),
        "inventory_table_hash": inventory_table_hash,
        "evidence_rows": rows,
        "required_submission_files": REQUIRED_R1_SUBMISSION_FILES,
        "submission_artifact_path": str(submission_path),
        "missing_submission_files": missing_submission_files,
        "first_next_pr": (
            "Submit the R1 line1381 resolution manifest and bind it to the six indexed evidence rows; "
            "then add either a parameter-elimination patch with full replay/symbolic equivalence or a "
            "physical-pricing replay that beats the current five-parameter 100-proxy-T boundary."
        ),
    }
    inventory_packet["inventory_hash"] = stable_hash(inventory_packet)

    requirements = [
        requirement(
            "I1",
            "R5 still selects R1 as the next exit-route PR",
            r5.get("method") == "b1_b7_cone01_r5_exit_route_priority_selector_v0"
            and r5_summary.get("selected_route_id") == "R1"
            and r5_summary.get("selected_packet_id") == EXPECTED_R1_PACKET_ID,
            {
                "method": r5.get("method"),
                "selected_route_id": r5_summary.get("selected_route_id"),
                "selected_packet_id": r5_summary.get("selected_packet_id"),
                "selector_hash": r5_summary.get("selector_hash"),
            },
        ),
        requirement(
            "I2",
            "R1 packet remains open because no submission artifact exists",
            r1.get("method") == "b1_b7_cone01_r1_line1381_resolution_packet_gate_v0"
            and r1_summary.get("submitted_r1_artifact_exists") is False
            and r1_summary.get("failed_requirement_ids") == ["P6", "P7", "P8"],
            {
                "method": r1.get("method"),
                "submitted_r1_artifact_exists": r1_summary.get("submitted_r1_artifact_exists"),
                "failed_requirement_ids": r1_summary.get("failed_requirement_ids"),
            },
        ),
        requirement(
            "I3",
            "All indexed source evidence result/report files exist",
            len(available_rows) == len(rows),
            {
                "available_row_count": len(available_rows),
                "required_row_count": len(rows),
                "missing_rows": [
                    row["evidence_id"]
                    for row in rows
                    if not row["result_exists"] or not row["report_exists"]
                ],
            },
        ),
        requirement(
            "I4",
            "Line1381 blocker remains visible in indexed evidence",
            len(blocker_rows) >= 3
            and r1_summary.get("line1381_off_grid_parameter_count_before") == 5
            and r1_summary.get("line1381_unpriced_proxy_t_pressure_before") == 100,
            {
                "blocker_row_count": len(blocker_rows),
                "r1_line1381_off_grid_parameter_count_before": r1_summary.get(
                    "line1381_off_grid_parameter_count_before"
                ),
                "r1_line1381_unpriced_proxy_t_pressure_before": r1_summary.get(
                    "line1381_unpriced_proxy_t_pressure_before"
                ),
            },
        ),
        requirement(
            "I5",
            "Indexed evidence still carries zero accepted B7 credit",
            len(zero_credit_rows) == len(rows)
            and r1_summary.get("accepted_occurrence_removal") == 0
            and r1_summary.get("accepted_proxy_t_reduction") == 0,
            {
                "zero_credit_row_count": len(zero_credit_rows),
                "required_row_count": len(rows),
                "r1_accepted_occurrence_removal": r1_summary.get("accepted_occurrence_removal"),
                "r1_accepted_proxy_t_reduction": r1_summary.get("accepted_proxy_t_reduction"),
            },
        ),
        requirement(
            "I6",
            "R1 required submission files remain missing",
            not submission_path.exists() and len(missing_submission_files) == 8,
            {
                "submission_artifact_path": str(submission_path),
                "submission_artifact_exists": submission_path.exists(),
                "missing_submission_file_count": len(missing_submission_files),
            },
        ),
        requirement(
            "I7",
            "Inventory packet is hash-bound to R1/R5 and evidence rows",
            bool(inventory_packet["inventory_hash"])
            and inventory_table_hash == inventory_packet["inventory_table_hash"]
            and r1_summary.get("r1_packet_hash") == inventory_packet["r1_packet_hash"],
            {
                "inventory_hash": inventory_packet["inventory_hash"],
                "inventory_table_hash": inventory_table_hash,
                "r1_packet_hash": r1_summary.get("r1_packet_hash"),
                "r5_selector_hash": r5_summary.get("selector_hash"),
            },
        ),
        requirement(
            "I8",
            "Forbidden resource claims remain false",
            r1_summary.get("b1_resource_saving_claimed") is False
            and r1_summary.get("b7_ledger_improvement_claimed") is False
            and r5_summary.get("b7_ledger_improvement_claimed") is False,
            {
                "r1_b1_resource_saving_claimed": r1_summary.get("b1_resource_saving_claimed"),
                "r1_b7_ledger_improvement_claimed": r1_summary.get(
                    "b7_ledger_improvement_claimed"
                ),
                "r5_b7_ledger_improvement_claimed": r5_summary.get(
                    "b7_ledger_improvement_claimed"
                ),
            },
        ),
    ]

    passed = sum(row["passed"] for row in requirements)
    failed_ids = [row["requirement_id"] for row in requirements if not row["passed"]]
    validation_errors: list[str] = []
    if failed_ids:
        validation_errors.append(f"unexpected R6 inventory failures: {failed_ids}")

    summary = {
        "inventory_id": INVENTORY_ID,
        "inventory_hash": inventory_packet["inventory_hash"],
        "inventory_table_hash": inventory_table_hash,
        "r1_packet_id": EXPECTED_R1_PACKET_ID,
        "r1_packet_hash": r1_summary.get("r1_packet_hash"),
        "r5_selector_hash": r5_summary.get("selector_hash"),
        "triage_hash": r1_summary.get("triage_hash"),
        "acceptance_packet_hash": r1_summary.get("acceptance_packet_hash"),
        "requirement_count": len(requirements),
        "requirements_passed": passed,
        "requirements_failed": len(requirements) - passed,
        "failed_requirement_ids": failed_ids,
        "indexed_evidence_row_count": len(rows),
        "available_evidence_row_count": len(available_rows),
        "line1381_blocker_row_count": len(blocker_rows),
        "missing_submission_file_count": len(missing_submission_files),
        "submission_artifact_exists": submission_path.exists(),
        "selected_route_id": r5_summary.get("selected_route_id"),
        "line1381_off_grid_parameter_count": r1_summary.get(
            "line1381_off_grid_parameter_count_before"
        ),
        "line1381_unpriced_proxy_t_pressure": r1_summary.get(
            "line1381_unpriced_proxy_t_pressure_before"
        ),
        "accepted_occurrence_removal": 0,
        "accepted_proxy_t_reduction": 0,
        "b7_credit_delta": 0,
        "b7_space_time_volume_credit": 0,
        "resource_saving_claimed": False,
        "b7_ledger_improvement_claimed": False,
        "validation_error_count": len(validation_errors),
    }

    return {
        "benchmark_id": "B1",
        "linked_benchmark_id": "B7",
        "source_target_id": "T-B1-004dh/T-B7-012q",
        "title": "B1/B7 Cone01 R6 R1 Source-Evidence Inventory Gate",
        "version": VERSION,
        "last_updated": args.last_updated,
        "method": METHOD,
        "status": STATUS,
        "model_status": MODEL_STATUS,
        "source_r1_gate": str(args.r1_gate),
        "source_r5_selector": str(args.r5_selector),
        "summary": summary,
        "r1_source_evidence_inventory_packet": inventory_packet,
        "requirements": requirements,
        "claim_boundary": {
            "what_is_supported": (
                "R6 indexes the source evidence that an R1 line1381 resolution submission must bind."
            ),
            "what_is_not_supported": (
                "No submitted R1 artifact, line1381 parameter elimination, accepted exit route, occurrence "
                "removal, proxy-T reduction, B7 ledger credit, or resource saving is supported."
            ),
            "next_gate": inventory_packet["first_next_pr"],
            "resource_saving_claimed": False,
            "b7_ledger_improvement_claimed": False,
        },
        "validation_errors": validation_errors,
        "runtime_seconds": round(time.time() - started, 6),
    }


def render_markdown(payload: dict[str, Any]) -> str:
    s = payload["summary"]
    packet = payload["r1_source_evidence_inventory_packet"]
    lines = [
        f"# {payload['title']}",
        "",
        f"- Target: `{payload['source_target_id']}`",
        f"- Method: `{payload['method']}`",
        f"- Status: `{payload['status']}`",
        f"- Inventory: `{s['inventory_id']}`",
        f"- Inventory hash: `{s['inventory_hash']}`",
        f"- Inventory table hash: `{s['inventory_table_hash']}`",
        "",
        "## Result",
        "",
        (
            f"The R6 inventory gate passes {s['requirements_passed']}/{s['requirement_count']} "
            "requirements. It indexes the source evidence needed by R1 while keeping B7 credit at zero."
        ),
        "",
        "## Indexed Evidence",
        "",
    ]
    for row in packet["evidence_rows"]:
        lines.extend(
            [
                f"### {row['evidence_id']} - {row['class']}",
                "",
                f"- Result: `{row['result_path']}`",
                f"- Report: `{row['report_path']}`",
                f"- Status: `{row['status']}`",
                f"- Why it matters: {row['why_it_matters']}",
                f"- Accepted occurrence / proxy-T reduction: `{row['accepted_occurrence_removal']}` / `{row['accepted_proxy_t_reduction']}`",
                "",
            ]
        )
    lines.extend(["## Missing R1 Submission Files", ""])
    for item in packet["missing_submission_files"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Requirement Results", ""])
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
            "This inventory gate does not claim resource saving, occurrence removal, proxy-T reduction, B7 ledger improvement, FT resource credit, or a solved B1/B7 problem.",
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
        "--r5-selector",
        type=Path,
        default=Path("results/B1_B7_cone01_R5_exit_route_priority_selector_v0.json"),
    )
    parser.add_argument(
        "--submission-dir",
        type=Path,
        default=Path("results/B1_B7_cone01_r1_line1381_resolution_submissions"),
    )
    parser.add_argument(
        "--json-output",
        type=Path,
        default=Path("results/B1_B7_cone01_R6_r1_source_evidence_inventory_gate_v0.json"),
    )
    parser.add_argument(
        "--markdown-output",
        type=Path,
        default=Path("research/B1_B7_cone01_R6_r1_source_evidence_inventory_gate.md"),
    )
    parser.add_argument("--last-updated", default="2026-07-06")
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()

    payload = build_payload(args)
    write_json(args.json_output, payload, args.pretty)
    args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_output.write_text(render_markdown(payload), encoding="utf-8")
    print(
        json.dumps(
            {
                "status": payload["status"],
                "inventory_hash": payload["summary"]["inventory_hash"],
                "indexed_evidence_row_count": payload["summary"]["indexed_evidence_row_count"],
                "missing_submission_file_count": payload["summary"][
                    "missing_submission_file_count"
                ],
                "requirements_passed": payload["summary"]["requirements_passed"],
                "requirements_failed": payload["summary"]["requirements_failed"],
                "validation_error_count": payload["summary"]["validation_error_count"],
                "json_output": str(args.json_output),
                "markdown_output": str(args.markdown_output),
            },
            indent=2,
            sort_keys=True,
        )
    )
    if payload["validation_errors"]:
        raise SystemExit("B1/B7 R6 R1 source-evidence inventory gate validation failed")


if __name__ == "__main__":
    main()
