#!/usr/bin/env python3
"""T-B3-025/T-B10-015l: shard work orders for blocked B3/B10 F1 covariance rows."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any


METHOD = "b3_b10_f1_full_covariance_work_order_gate_v0"
STATUS = "f1_full_covariance_work_order_ready_zero_credit"
MODEL_STATUS = "remaining_blocked_rows_split_into_replayable_full_covariance_work_orders"
SOURCE_TARGET_ID = "T-B3-025/T-B10-015l"
EXPECTED_SCOUT_METHOD = "b3_b10_f1_remaining_row_extension_scout_v0"
EXPECTED_FAILED_IDS = ["P8", "P9", "P10"]
DEFAULT_GROUPS_PER_SHARD = 512


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def canonical_hash(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, payload: dict[str, Any], pretty: bool) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(
        payload,
        indent=2 if pretty else None,
        sort_keys=True,
        separators=None if pretty else (",", ":"),
    )
    path.write_text(text + "\n", encoding="utf-8")


def requirement(req_id: str, passed: bool, description: str, evidence: Any) -> dict[str, Any]:
    return {
        "id": req_id,
        "passed": bool(passed),
        "description": description,
        "evidence": evidence,
    }


def grouped_rows_by_molecule(grouped: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {row["molecule"]: row for row in grouped.get("rows", [])}


def build_shards(row: dict[str, Any], groups_per_shard: int) -> list[dict[str, Any]]:
    group_count = int(row["full_cover_group_count_proxy"])
    shards = []
    for shard_id, start in enumerate(range(0, group_count, groups_per_shard), start=1):
        end = min(start + groups_per_shard, group_count)
        shard = {
            "shard_id": f"{row['molecule']}-full-covariance-shard-{shard_id:03d}",
            "molecule": row["molecule"],
            "group_start_inclusive": start,
            "group_end_exclusive": end,
            "group_count": end - start,
            "expected_output": (
                "results/B3_B10_F1_full_covariance_shards/"
                f"{row['molecule']}/shard_{shard_id:03d}.json"
            ),
            "expected_output_hash_key": "full_covariance_matrix_shard_hash",
            "replay_command_template": (
                "python3 tools/b3_b10_f1_full_covariance_row_worker.py "
                f"--molecule {row['molecule']} --group-start {start} --group-end {end} "
                "--state-source compiled_ucc_adapt --emit-shard-json"
            ),
        }
        shard["shard_contract_hash"] = canonical_hash(shard)
        shards.append(shard)
    return shards


def work_order_from_extension(
    extension: dict[str, Any],
    grouped_row: dict[str, Any],
    groups_per_shard: int,
) -> dict[str, Any]:
    group_count_proxy = int(grouped_row["qwc_group_count"])
    random_term_count = int(extension["random_pauli_terms_under_compiled_state"])
    shard_count = int(math.ceil(group_count_proxy / groups_per_shard))
    avg_terms_per_group_proxy = random_term_count / max(1, group_count_proxy)
    pair_budget_proxy = int(
        math.ceil(group_count_proxy * avg_terms_per_group_proxy * max(0.0, avg_terms_per_group_proxy - 1.0) / 2.0)
    )
    order = {
        "work_order_id": f"B3B10-F1-full-covariance-work-order-{extension['molecule']}",
        "molecule": extension["molecule"],
        "coordinate": extension["coordinate"],
        "selected_ci_basis": extension["selected_ci_basis"],
        "total_qubits": extension["total_qubits"],
        "electrons": extension["electrons"],
        "ansatz_model": extension["ansatz_model"],
        "blocked_extension_row_hash": extension["extension_row_hash"],
        "blocked_reasons": extension["blocked_reasons"],
        "full_cover_group_count_proxy": group_count_proxy,
        "compiled_random_pauli_term_count": random_term_count,
        "hf_cover_nonzero_covariance_pair_count": grouped_row.get("nonzero_covariance_pair_count"),
        "hf_cover_group_size_histogram": grouped_row.get("group_size_histogram"),
        "planning_note": (
            "Group count and histogram are planning proxies from the full HF QWC cover; the worker "
            "must recompute or verify the compiled-state QWC cover before credit."
        ),
        "groups_per_shard": groups_per_shard,
        "shard_count": shard_count,
        "avg_terms_per_group_proxy": avg_terms_per_group_proxy,
        "pair_budget_proxy": pair_budget_proxy,
        "required_worker_outputs": [
            "compiled_state_replay_hash",
            "full_covariance_matrix_shard_hash",
            "qwc_group_manifest_hash",
            "measurement_basis_manifest_hash",
            "shot_allocation_or_exact_mode",
            "stdout_stderr_returncode_hash",
            "wall_time_memory_ledger",
            "claim_boundary_note",
        ],
        "row_acceptance_ready": False,
    }
    order["shards"] = build_shards(order, groups_per_shard)
    order["work_order_hash"] = canonical_hash(order)
    return order


def build_payload(args: argparse.Namespace) -> dict[str, Any]:
    scout = load_json(args.remaining_row_scout)
    grouped = load_json(args.grouped_covariance)
    grouped_by_mol = grouped_rows_by_molecule(grouped)
    extension_rows = scout.get("extension_rows", [])
    work_orders = [
        work_order_from_extension(row, grouped_by_mol[row["molecule"]], args.groups_per_shard)
        for row in extension_rows
    ]
    total_shards = sum(order["shard_count"] for order in work_orders)
    total_group_proxy = sum(order["full_cover_group_count_proxy"] for order in work_orders)
    max_shards = max(order["shard_count"] for order in work_orders)
    worker_exists = Path("tools/b3_b10_f1_full_covariance_row_worker.py").exists()
    shard_outputs_exist = all(Path(shard["expected_output"]).exists() for order in work_orders for shard in order["shards"])
    rows_ready = all(order["row_acceptance_ready"] for order in work_orders)

    requirements = [
        requirement(
            "P1",
            scout.get("method") == EXPECTED_SCOUT_METHOD
            and scout.get("summary", {}).get("failed_requirement_ids") == EXPECTED_FAILED_IDS
            and scout.get("summary", {}).get("validation_error_count") == 0,
            "Remaining-row scout is valid and still blocked on P8/P9/P10",
            {
                "method": scout.get("method"),
                "failed_requirement_ids": scout.get("summary", {}).get("failed_requirement_ids"),
                "source_file_hash": file_hash(args.remaining_row_scout),
            },
        ),
        requirement(
            "P2",
            len(work_orders) == 3
            and {order["molecule"] for order in work_orders}
            == {"lih_bond_stretch", "h2o_symmetric_oh_stretch", "n2_bond_stretch"},
            "LiH/H2O/N2 work orders are generated",
            {"work_order_ids": [order["work_order_id"] for order in work_orders]},
        ),
        requirement(
            "P3",
            all(order["shard_count"] > 0 for order in work_orders)
            and total_shards > len(work_orders),
            "Each work order is split into replayable shards",
            {
                "groups_per_shard": args.groups_per_shard,
                "total_shard_count": total_shards,
                "shard_counts": {order["molecule"]: order["shard_count"] for order in work_orders},
            },
        ),
        requirement(
            "P4",
            all(order["required_worker_outputs"] for order in work_orders),
            "Worker output contract is explicit for every row",
            {
                "required_worker_output_count": len(work_orders[0]["required_worker_outputs"])
                if work_orders
                else 0
            },
        ),
        requirement(
            "P5",
            all(order["blocked_reasons"] for order in work_orders),
            "Each work order preserves the blocker reasons from the scout",
            {
                "blocked_reasons_by_row": {
                    order["molecule"]: order["blocked_reasons"] for order in work_orders
                }
            },
        ),
        requirement(
            "P6",
            all(order["work_order_hash"] and all(shard["shard_contract_hash"] for shard in order["shards"]) for order in work_orders),
            "Work-order and shard contract hashes are reproducible",
            {"work_order_hashes": {order["molecule"]: order["work_order_hash"] for order in work_orders}},
        ),
        requirement(
            "P7",
            scout.get("summary", {}).get("b10_t1_credit_allowed") is False
            and scout.get("summary", {}).get("denominator_win_count") == 0
            and scout.get("summary", {}).get("accepted_full_covariance_row_count") == 0,
            "No B3/B10 credit, denominator win, or accepted row is claimed",
            {
                "accepted_full_covariance_row_count": scout.get("summary", {}).get(
                    "accepted_full_covariance_row_count"
                ),
                "denominator_win_count": scout.get("summary", {}).get("denominator_win_count"),
                "b10_t1_credit_allowed": scout.get("summary", {}).get("b10_t1_credit_allowed"),
            },
        ),
        requirement(
            "P8",
            worker_exists,
            "Full covariance worker implementation exists",
            {"expected_worker": "tools/b3_b10_f1_full_covariance_row_worker.py"},
        ),
        requirement(
            "P9",
            shard_outputs_exist,
            "All shard outputs have been produced",
            {"total_expected_shard_outputs": total_shards},
        ),
        requirement(
            "P10",
            rows_ready,
            "Remaining rows are assembled and ready for F1 acceptance",
            {"row_acceptance_ready_count": sum(1 for order in work_orders if order["row_acceptance_ready"])},
        ),
    ]

    failed = [item["id"] for item in requirements if not item["passed"]]
    validation_errors: list[str] = []
    expected_failures = ["P9", "P10"] if worker_exists else ["P8", "P9", "P10"]
    if failed != expected_failures:
        validation_errors.append(f"unexpected_failed_requirement_ids:{failed}")

    summary = {
        "work_order_count": len(work_orders),
        "total_shard_count": total_shards,
        "groups_per_shard": args.groups_per_shard,
        "total_full_cover_group_count_proxy": total_group_proxy,
        "max_row_shard_count": max_shards,
        "work_order_manifest_hash": canonical_hash(work_orders),
        "requirements_passed": len(requirements) - len(failed),
        "requirements_failed": len(failed),
        "failed_requirement_ids": failed,
        "worker_exists": worker_exists,
        "shard_outputs_exist": shard_outputs_exist,
        "row_acceptance_ready_count": 0,
        "accepted_full_covariance_row_count": 0,
        "denominator_win_count": 0,
        "b3_reopen_ready": False,
        "b10_t1_credit_allowed": False,
        "quantum_advantage_claimed": False,
        "reaction_dynamics_solution_claimed": False,
        "bqp_separation_claimed": False,
        "validation_error_count": len(validation_errors),
    }

    return {
        "benchmark_id": "B3_B10",
        "problem_ids": ["B3", "B10"],
        "source_target_id": SOURCE_TARGET_ID,
        "title": "B3/B10 F1 Full Covariance Work Order Gate",
        "version": "0.1",
        "last_updated": args.last_updated,
        "status": STATUS,
        "method": METHOD,
        "model_status": MODEL_STATUS,
        "source_remaining_row_scout": str(args.remaining_row_scout),
        "source_grouped_covariance": str(args.grouped_covariance),
        "work_orders": work_orders,
        "requirements": requirements,
        "summary": summary,
        "claim_boundary": {
            "what_is_supported": (
                "The three blocked LiH/H2O/N2 rows now have replayable full-covariance work orders "
                "and shard contracts."
            ),
            "what_is_not_supported": (
                "No full covariance worker, shard outputs, assembled rows, denominator win, B3 reopen, "
                "B10-T1 credit, quantum advantage, or BQP separation is supported."
            ),
            "next_gate": (
                "Implement the row worker, produce every shard output, assemble each row, and resubmit "
                "the four-row F1 artifact."
            ),
        },
        "validation_errors": validation_errors,
    }


def render_markdown(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    lines = [
        "# B3/B10 F1 Full Covariance Work Order Gate",
        "",
        f"- Target: `{payload['source_target_id']}`",
        f"- Method: `{payload['method']}`",
        f"- Status: `{payload['status']}`",
        f"- Work-order manifest hash: `{summary['work_order_manifest_hash']}`",
        "",
        "## Result",
        "",
        (
            f"The gate creates {summary['work_order_count']} work orders and "
            f"{summary['total_shard_count']} shard contracts for LiH/H2O/N2 full covariance. "
            f"It passes {summary['requirements_passed']}/"
            f"{summary['requirements_passed'] + summary['requirements_failed']} requirements and "
            f"intentionally fails {summary['failed_requirement_ids']} because no worker, shard outputs, "
            "or assembled rows exist yet."
        ),
        "",
        "## Work Orders",
        "",
        "| molecule | full-cover group proxy | shards | compiled random terms |",
        "|---|---:|---:|---:|",
    ]
    for order in payload["work_orders"]:
        lines.append(
            "| "
            f"{order['molecule']} | {order['full_cover_group_count_proxy']} | "
            f"{order['shard_count']} | {order['compiled_random_pauli_term_count']} |"
        )
    lines.extend(["", "## Requirement Results", ""])
    for req in payload["requirements"]:
        status = "PASS" if req["passed"] else "FAIL"
        lines.append(f"- `{req['id']}` {status}: {req['description']}")
    lines.extend(
        [
            "",
            "## Claim Boundary",
            "",
            f"- Supported: {payload['claim_boundary']['what_is_supported']}",
            f"- Not supported: {payload['claim_boundary']['what_is_not_supported']}",
            f"- Next gate: {payload['claim_boundary']['next_gate']}",
            "",
            "This work-order gate does not claim a reaction-dynamics solution, quantum advantage, B3 reopen credit, B10-T1 credit, or BQP separation.",
            "",
            "## Validation",
            "",
            f"- validation_error_count: `{summary['validation_error_count']}`",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--remaining-row-scout",
        type=Path,
        default=Path("results/B3_B10_F1_remaining_row_extension_scout_v0.json"),
    )
    parser.add_argument(
        "--grouped-covariance",
        type=Path,
        default=Path("results/B3_grouped_covariance_shot_floor_v0.json"),
    )
    parser.add_argument("--groups-per-shard", type=int, default=DEFAULT_GROUPS_PER_SHARD)
    parser.add_argument(
        "--json-output",
        type=Path,
        default=Path("results/B3_B10_F1_full_covariance_work_order_gate_v0.json"),
    )
    parser.add_argument(
        "--markdown-output",
        type=Path,
        default=Path("research/B3_B10_F1_full_covariance_work_order_gate.md"),
    )
    parser.add_argument("--last-updated", default="2026-07-03")
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
                "work_order_manifest_hash": payload["summary"]["work_order_manifest_hash"],
                "total_shard_count": payload["summary"]["total_shard_count"],
                "requirements_passed": payload["summary"]["requirements_passed"],
                "requirements_failed": payload["summary"]["requirements_failed"],
                "failed_requirement_ids": payload["summary"]["failed_requirement_ids"],
                "validation_error_count": payload["summary"]["validation_error_count"],
                "json_output": str(args.json_output),
                "markdown_output": str(args.markdown_output),
            },
            indent=2,
            sort_keys=True,
        )
    )
    if payload["validation_errors"]:
        raise SystemExit("B3/B10 F1 full covariance work-order gate validation failed")


if __name__ == "__main__":
    main()
