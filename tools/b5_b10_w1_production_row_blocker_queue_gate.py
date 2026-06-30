#!/usr/bin/env python3
"""T-B5-006m/T-B10-014k: W1 production-row blocker queue gate."""

from __future__ import annotations

import argparse
import hashlib
import json
import time
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


METHOD = "b5_b10_w1_production_row_blocker_queue_gate_v0"
STATUS = "w1_production_row_blocker_queue_open_no_rows_submitted"
MODEL_STATUS = "w1_missing_fields_partitioned_into_pr_sized_solver_queue"
VERSION = "0.1"
EXPECTED_ROW_CONTRACT_HASH = "7ee407e20f51bd0c003d885c8d43282359f84bea9729f0da203b9b2c2970a9fc"
EXPECTED_FAILED_IDS = ["Q6", "Q7", "Q8"]


FIELD_PACKET_MAP = {
    "canonical_center_site": "W1-E4-env-residuals",
    "left_environment_hash": "W1-E4-env-residuals",
    "right_environment_hash": "W1-E4-env-residuals",
    "orthonormal_residual_norm": "W1-E4-env-residuals",
    "discarded_weight": "W1-E5-convergence",
    "wall_clock_seconds": "W1-E7-cost-ledger",
    "peak_memory_mb": "W1-E7-cost-ledger",
    "matvec_or_sweep_count": "W1-E7-cost-ledger",
}

FIELD_OWNER_MAP = {
    "W1-E4-env-residuals": "DMRG Solver Agent",
    "W1-E5-convergence": "Baseline Adversary",
    "W1-E7-cost-ledger": "Cost Ledger Agent",
}

PACKET_ACCEPTANCE = {
    "W1-E4-env-residuals": (
        "supply canonical center site plus left/right environment hashes and "
        "orthonormal residual norm for every locked row"
    ),
    "W1-E5-convergence": (
        "supply discarded-weight values under declared convergence thresholds before "
        "any seeded-pressure comparison"
    ),
    "W1-E7-cost-ledger": (
        "supply wall-clock, peak-memory, and matvec/sweep counts under the same-access "
        "row contract"
    ),
}


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any], pretty: bool) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(payload, indent=2 if pretty else None, sort_keys=True)
    path.write_text(text + "\n", encoding="utf-8")


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


def row_priority(row: dict[str, Any]) -> tuple[int, float, float, str]:
    """Sort higher-site rows first, then weaker prototype diagnostics."""
    fixed_sector_norm = float(row["prefilled_values"].get("fixed_sector_norm", 0.0))
    rel_error = float(row["prefilled_values"].get("relative_response_error", 0.0))
    return (-int(row["sites"]), -fixed_sector_norm, -rel_error, str(row["row_id"]))


def build_payload(args: argparse.Namespace) -> dict[str, Any]:
    started = time.time()
    intake = load_json(args.intake_template)
    implementation = load_json(args.implementation_contract)
    rows = sorted(intake.get("template_rows", []), key=row_priority)

    row_contract_hash = intake["summary"].get("row_contract_hash")
    production_required_keys = list(intake.get("production_required_keys", []))
    row_queue: list[dict[str, Any]] = []
    packet_rows: dict[str, list[str]] = defaultdict(list)
    packet_field_counter: Counter[str] = Counter()
    field_counter: Counter[str] = Counter()

    for order, row in enumerate(rows, start=1):
        missing_fields = list(row.get("production_missing_keys", []))
        field_counter.update(missing_fields)
        packet_ids = sorted({FIELD_PACKET_MAP[field] for field in missing_fields})
        for packet_id in packet_ids:
            packet_rows[packet_id].append(row["row_id"])
        for field in missing_fields:
            packet_field_counter[FIELD_PACKET_MAP[field]] += 1
        row_queue.append(
            {
                "priority": order,
                "row_id": row["row_id"],
                "sites": int(row["sites"]),
                "u_over_t": float(row["u_over_t"]),
                "template_hash": row["template_hash"],
                "prototype_trace_hash": row.get("prototype_trace_hash"),
                "prototype_fixed_sector_norm": float(row["prefilled_values"].get("fixed_sector_norm", 0.0)),
                "prototype_energy_variance": float(row["prefilled_values"].get("energy_variance", 0.0)),
                "prototype_relative_response_error": float(
                    row["prefilled_values"].get("relative_response_error", 0.0)
                ),
                "seeded_pressure_relative_response_error": float(
                    row["prefilled_values"].get("seeded_pressure_relative_response_error", 0.0)
                ),
                "missing_production_field_count": len(missing_fields),
                "missing_production_fields": missing_fields,
                "blocking_packet_ids": packet_ids,
                "submission_artifact_path": row.get("submission_artifact_path"),
                "submitted_production_row_present": bool(row.get("submitted_production_row_present")),
                "accepted_production_row": bool(row.get("accepted_production_row")),
            }
        )

    packet_queue: list[dict[str, Any]] = []
    for packet_id in sorted(packet_rows):
        packet_queue.append(
            {
                "packet_id": packet_id,
                "owner_role": FIELD_OWNER_MAP[packet_id],
                "row_count": len(packet_rows[packet_id]),
                "row_ids": packet_rows[packet_id],
                "missing_field_count": packet_field_counter[packet_id],
                "acceptance": PACKET_ACCEPTANCE[packet_id],
            }
        )

    implementation_packets = {
        item["packet_id"]: item for item in implementation.get("implementation_packets", [])
    }
    packet_contract_matches = [
        packet["packet_id"] in implementation_packets for packet in packet_queue
    ]
    blocker_queue_hash = stable_hash({"row_queue": row_queue, "packet_queue": packet_queue})
    submitted_rows = sum(row["submitted_production_row_present"] for row in row_queue)
    accepted_rows = sum(row["accepted_production_row"] for row in row_queue)
    missing_field_total = sum(row["missing_production_field_count"] for row in row_queue)

    requirements = [
        requirement(
            "Q1",
            "Input intake template preserves the locked B5/B10 row contract hash",
            row_contract_hash == EXPECTED_ROW_CONTRACT_HASH,
            {"row_contract_hash": row_contract_hash, "expected": EXPECTED_ROW_CONTRACT_HASH},
        ),
        requirement(
            "Q2",
            "Nine row-level production blockers are queued",
            len(row_queue) == 9,
            {"row_queue_count": len(row_queue), "required_rows": 9},
        ),
        requirement(
            "Q3",
            "All eight production-required keys are mapped to implementation packets",
            sorted(FIELD_PACKET_MAP) == sorted(production_required_keys),
            {
                "mapped_keys": sorted(FIELD_PACKET_MAP),
                "production_required_keys": sorted(production_required_keys),
            },
        ),
        requirement(
            "Q4",
            "Queue is partitioned into existing W1 implementation packets",
            all(packet_contract_matches) and len(packet_queue) == 3,
            {
                "packet_ids": [packet["packet_id"] for packet in packet_queue],
                "packet_contract_matches": packet_contract_matches,
            },
        ),
        requirement(
            "Q5",
            "Missing production fields are exhaustively accounted for",
            missing_field_total == intake["summary"].get("production_missing_key_total") == 72,
            {
                "queue_missing_field_total": missing_field_total,
                "intake_missing_field_total": intake["summary"].get("production_missing_key_total"),
            },
        ),
        requirement(
            "Q6",
            "At least one submitted production row exists",
            submitted_rows > 0,
            {"submitted_production_row_count": submitted_rows},
        ),
        requirement(
            "Q7",
            "At least one production row is accepted",
            accepted_rows > 0,
            {"accepted_production_row_count": accepted_rows},
        ),
        requirement(
            "Q8",
            "All blocker packets have at least one completed production row",
            all(any(row["accepted_production_row"] for row in row_queue if packet["packet_id"] in row["blocking_packet_ids"]) for packet in packet_queue),
            {"completed_packet_count": 0, "required_packet_count": len(packet_queue)},
        ),
        requirement(
            "Q9",
            "Forbidden positive-route claims remain false while queue is open",
            all(
                not intake["summary"].get(key)
                for key in [
                    "production_dmrg_claimed",
                    "same_access_positive_route_claimed",
                    "quantum_advantage_claimed",
                    "bqp_separation_claimed",
                ]
            ),
            {
                "production_dmrg_claimed": intake["summary"].get("production_dmrg_claimed"),
                "same_access_positive_route_claimed": intake["summary"].get(
                    "same_access_positive_route_claimed"
                ),
                "quantum_advantage_claimed": intake["summary"].get("quantum_advantage_claimed"),
                "bqp_separation_claimed": intake["summary"].get("bqp_separation_claimed"),
            },
        ),
    ]
    passed = sum(1 for item in requirements if item["passed"])
    failed_ids = [item["requirement_id"] for item in requirements if not item["passed"]]
    validation_errors: list[str] = []
    if failed_ids != EXPECTED_FAILED_IDS:
        validation_errors.append(f"unexpected failed queue requirements: {failed_ids}")
    if len(row_queue) != 9:
        validation_errors.append("blocker queue must preserve nine locked rows")
    if missing_field_total != 72:
        validation_errors.append("blocker queue must account for 72 missing production fields")
    if submitted_rows != 0 or accepted_rows != 0:
        validation_errors.append("queue gate must not fabricate submitted or accepted production rows")

    summary = {
        "row_contract_hash": row_contract_hash,
        "source_intake_status": intake.get("status"),
        "source_implementation_contract_status": implementation.get("status"),
        "queue_requirement_count": len(requirements),
        "queue_requirements_passed": passed,
        "queue_requirements_failed": len(requirements) - passed,
        "failed_queue_requirement_ids": failed_ids,
        "row_queue_count": len(row_queue),
        "packet_queue_count": len(packet_queue),
        "production_required_key_count": len(production_required_keys),
        "missing_production_field_total": missing_field_total,
        "submitted_production_row_count": submitted_rows,
        "accepted_production_row_count": accepted_rows,
        "field_missing_counts": dict(sorted(field_counter.items())),
        "packet_missing_counts": {
            packet["packet_id"]: packet["missing_field_count"] for packet in packet_queue
        },
        "blocker_queue_hash": blocker_queue_hash,
        "w1_queue_ready_for_agent_prs": True,
        "production_dmrg_claimed": False,
        "same_access_positive_route_claimed": False,
        "quantum_advantage_claimed": False,
        "bqp_separation_claimed": False,
        "validation_error_count": len(validation_errors),
    }

    return {
        "benchmark_id": "B5",
        "linked_benchmark_id": "B10",
        "source_target_id": "B10-T1",
        "dependency_benchmarks": ["B5", "B10"],
        "title": "B5/B10 W1 Production Row Blocker Queue Gate v0",
        "version": VERSION,
        "last_updated": args.last_updated,
        "method": METHOD,
        "status": STATUS,
        "model_status": MODEL_STATUS,
        "source_intake_template_result": str(args.intake_template),
        "source_implementation_contract_result": str(args.implementation_contract),
        "summary": summary,
        "requirements": requirements,
        "production_required_keys": production_required_keys,
        "row_queue": row_queue,
        "packet_queue": packet_queue,
        "claim_boundary": {
            "what_is_supported": (
                "The 72 missing W1 production fields are now partitioned into a "
                "row-prioritized queue and three existing implementation packets for agent PRs."
            ),
            "what_is_not_supported": (
                "No production DMRG row has been submitted or accepted; no canonical "
                "environment, convergence, seeded-pressure win, cost ledger, positive route, "
                "quantum advantage, or BQP separation is supported."
            ),
            "next_gate": (
                "Submit the first row artifact from the priority queue, then require W1-E4 "
                "environment/residual fields, W1-E5 discarded-weight convergence fields, "
                "and W1-E7 cost fields before any row can be accepted."
            ),
            "production_dmrg_claimed": False,
            "same_access_positive_route_claimed": False,
            "quantum_advantage_claimed": False,
            "bqp_separation_claimed": False,
        },
        "validation_errors": validation_errors,
        "runtime_seconds": time.time() - started,
    }


def write_markdown(payload: dict[str, Any], path: Path) -> None:
    summary = payload["summary"]
    lines = [
        "# B5/B10 W1 Production Row Blocker Queue Gate v0.1",
        "",
        f"Status: **{payload['status']}**",
        "",
        "## Summary",
        "",
        f"- Method: `{payload['method']}`",
        f"- Model status: `{payload['model_status']}`",
        f"- Row contract hash: `{summary['row_contract_hash']}`",
        f"- Requirements passed/failed: {summary['queue_requirements_passed']} / {summary['queue_requirements_failed']}",
        f"- Failed requirement IDs: {summary['failed_queue_requirement_ids']}",
        f"- Row queue / packet queue: {summary['row_queue_count']} / {summary['packet_queue_count']}",
        f"- Missing production fields: {summary['missing_production_field_total']}",
        f"- Submitted / accepted production rows: {summary['submitted_production_row_count']} / {summary['accepted_production_row_count']}",
        f"- Blocker queue hash: `{summary['blocker_queue_hash']}`",
        "",
        "## Packet Queue",
        "",
        "| packet | owner | rows | missing fields | acceptance |",
        "| --- | --- | ---: | ---: | --- |",
    ]
    for packet in payload["packet_queue"]:
        lines.append(
            f"| {packet['packet_id']} | {packet['owner_role']} | {packet['row_count']} | "
            f"{packet['missing_field_count']} | {packet['acceptance']} |"
        )
    lines.extend(
        [
            "",
            "## Row Queue",
            "",
            "| priority | row_id | sites | missing fields | packets | prototype response error | seeded pressure error |",
            "| ---: | --- | ---: | ---: | --- | ---: | ---: |",
        ]
    )
    for row in payload["row_queue"]:
        lines.append(
            f"| {row['priority']} | {row['row_id']} | {row['sites']} | "
            f"{row['missing_production_field_count']} | {', '.join(row['blocking_packet_ids'])} | "
            f"{row['prototype_relative_response_error']} | {row['seeded_pressure_relative_response_error']} |"
        )
    lines.extend(
        [
            "",
            "## Requirement Results",
            "",
        ]
    )
    for item in payload["requirements"]:
        state = "PASS" if item["passed"] else "FAIL"
        lines.append(f"- {item['requirement_id']} [{state}]: {item['label']}")
    lines.extend(
        [
            "",
            "## Claim Boundary",
            "",
            f"- Supported: {payload['claim_boundary']['what_is_supported']}",
            f"- Not supported: {payload['claim_boundary']['what_is_not_supported']}",
            f"- Next gate: {payload['claim_boundary']['next_gate']}",
            f"- production_dmrg_claimed: {payload['claim_boundary']['production_dmrg_claimed']}",
            f"- same_access_positive_route_claimed: {payload['claim_boundary']['same_access_positive_route_claimed']}",
            f"- quantum_advantage_claimed: {payload['claim_boundary']['quantum_advantage_claimed']}",
            f"- bqp_separation_claimed: {payload['claim_boundary']['bqp_separation_claimed']}",
            "",
            "## Validation",
            "",
            f"- validation_error_count: {len(payload['validation_errors'])}",
        ]
    )
    if payload["validation_errors"]:
        lines.extend(f"- {error}" for error in payload["validation_errors"])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--intake-template",
        type=Path,
        default=Path("results/B5_B10_w1_production_row_intake_template_gate_v0.json"),
    )
    parser.add_argument(
        "--implementation-contract",
        type=Path,
        default=Path("results/B5_B10_w1_implementation_contract_gate_v0.json"),
    )
    parser.add_argument(
        "--json-output",
        type=Path,
        default=Path("results/B5_B10_w1_production_row_blocker_queue_gate_v0.json"),
    )
    parser.add_argument(
        "--markdown-output",
        type=Path,
        default=Path("research/B5_B10_w1_production_row_blocker_queue_gate.md"),
    )
    parser.add_argument("--last-updated", default="2026-07-01")
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()

    payload = build_payload(args)
    write_json(args.json_output, payload, args.pretty)
    write_markdown(payload, args.markdown_output)
    print(payload["status"])
    print(
        payload["summary"]["queue_requirements_passed"],
        payload["summary"]["queue_requirements_failed"],
        payload["summary"]["failed_queue_requirement_ids"],
    )


if __name__ == "__main__":
    main()
