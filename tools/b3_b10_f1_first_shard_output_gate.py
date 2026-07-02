#!/usr/bin/env python3
"""T-B3-026/T-B10-015m: accept the first B3/B10 F1 covariance shard output."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


METHOD = "b3_b10_f1_first_shard_output_gate_v0"
STATUS = "first_full_covariance_shard_output_recorded_zero_credit"
MODEL_STATUS = "one_of_sixty_five_full_covariance_shards_produced_no_row_credit"
SOURCE_TARGET_ID = "T-B3-026/T-B10-015m"
EXPECTED_WORK_ORDER_METHOD = "b3_b10_f1_full_covariance_work_order_gate_v0"
EXPECTED_WORKER_METHOD = "b3_b10_f1_full_covariance_row_worker_v0"
EXPECTED_SHARD_ID = "h2o_symmetric_oh_stretch-full-covariance-shard-001"
EXPECTED_SHARD_HASH = "0294e8bc505c5cca1512513058fda2dad6883fa93d5063bc6888a03cec52a2ad"
EXPECTED_TOTAL_SHARDS = 65


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


def find_shard_contract(work_order: dict[str, Any], shard_id: str) -> dict[str, Any]:
    for order in work_order.get("work_orders", []):
        for shard in order.get("shards", []):
            if shard.get("shard_id") == shard_id:
                return shard
    return {}


def build_payload(args: argparse.Namespace) -> dict[str, Any]:
    work_order = load_json(args.work_order_gate)
    shard = load_json(args.shard_output)
    contract = find_shard_contract(work_order, shard.get("shard_id"))
    shard_summary = shard.get("full_covariance_matrix_shard", {}).get("summary", {})
    shard_hash = shard.get("full_covariance_matrix_shard_hash")
    produced_shard_count = 1 if args.shard_output.exists() else 0

    requirements = [
        requirement(
            "P1",
            work_order.get("method") == EXPECTED_WORK_ORDER_METHOD
            and work_order.get("summary", {}).get("worker_exists") is True
            and work_order.get("summary", {}).get("total_shard_count") == EXPECTED_TOTAL_SHARDS,
            "Work-order gate is current and recognizes the worker",
            {
                "method": work_order.get("method"),
                "worker_exists": work_order.get("summary", {}).get("worker_exists"),
                "total_shard_count": work_order.get("summary", {}).get("total_shard_count"),
                "work_order_gate_hash": file_hash(args.work_order_gate),
            },
        ),
        requirement(
            "P2",
            shard.get("method") == EXPECTED_WORKER_METHOD
            and shard.get("status") == "full_covariance_shard_computed_zero_credit"
            and not shard.get("validation_errors"),
            "Shard output was produced by the full-covariance worker",
            {
                "method": shard.get("method"),
                "status": shard.get("status"),
                "shard_file_hash": file_hash(args.shard_output),
            },
        ),
        requirement(
            "P3",
            shard.get("shard_id") == EXPECTED_SHARD_ID
            and contract.get("shard_id") == EXPECTED_SHARD_ID,
            "Shard output matches a work-order contract",
            {
                "shard_id": shard.get("shard_id"),
                "contract_hash": contract.get("shard_contract_hash"),
                "expected_output": contract.get("expected_output"),
            },
        ),
        requirement(
            "P4",
            shard_hash == EXPECTED_SHARD_HASH and shard_summary.get("group_count") == 512,
            "Shard covariance hash and group count are stable",
            {
                "full_covariance_matrix_shard_hash": shard_hash,
                "group_count": shard_summary.get("group_count"),
                "nonzero_covariance_pair_count": shard_summary.get("nonzero_covariance_pair_count"),
            },
        ),
        requirement(
            "P5",
            all(
                shard.get(key)
                for key in [
                    "compiled_state_replay_hash",
                    "qwc_group_manifest_hash",
                    "measurement_basis_manifest_hash",
                    "stdout_stderr_returncode_hash",
                    "wall_time_memory_ledger_hash",
                    "claim_boundary_hash",
                ]
            ),
            "Required worker hashes are present",
            {
                "compiled_state_replay_hash": shard.get("compiled_state_replay_hash"),
                "qwc_group_manifest_hash": shard.get("qwc_group_manifest_hash"),
                "measurement_basis_manifest_hash": shard.get("measurement_basis_manifest_hash"),
            },
        ),
        requirement(
            "P6",
            shard.get("claim_boundary", {}).get("what_is_not_supported")
            and work_order.get("summary", {}).get("b10_t1_credit_allowed") is False,
            "Claim boundary preserves zero credit",
            {
                "accepted_full_covariance_row_count": work_order.get("summary", {}).get(
                    "accepted_full_covariance_row_count"
                ),
                "denominator_win_count": work_order.get("summary", {}).get("denominator_win_count"),
                "b10_t1_credit_allowed": work_order.get("summary", {}).get("b10_t1_credit_allowed"),
            },
        ),
        requirement(
            "P7",
            produced_shard_count == 1,
            "Exactly one shard output is recorded by this gate",
            {"produced_shard_count": produced_shard_count, "required_total_shard_count": EXPECTED_TOTAL_SHARDS},
        ),
        requirement(
            "P8",
            produced_shard_count == EXPECTED_TOTAL_SHARDS,
            "All 65 shard outputs have been produced",
            {"produced_shard_count": produced_shard_count, "required_total_shard_count": EXPECTED_TOTAL_SHARDS},
        ),
        requirement(
            "P9",
            False,
            "LiH/H2O/N2 rows are assembled from all shards",
            {"assembled_row_count": 0},
        ),
        requirement(
            "P10",
            False,
            "Four-row F1 artifact is accepted",
            {"accepted_full_covariance_row_count": 0},
        ),
    ]
    failed = [item["id"] for item in requirements if not item["passed"]]
    validation_errors: list[str] = []
    if failed != ["P8", "P9", "P10"]:
        validation_errors.append(f"unexpected_failed_requirement_ids:{failed}")

    summary = {
        "produced_shard_count": produced_shard_count,
        "required_total_shard_count": EXPECTED_TOTAL_SHARDS,
        "remaining_shard_count": EXPECTED_TOTAL_SHARDS - produced_shard_count,
        "recorded_shard_id": shard.get("shard_id"),
        "recorded_shard_hash": shard_hash,
        "recorded_shard_group_count": shard_summary.get("group_count"),
        "recorded_shard_nonzero_covariance_pair_count": shard_summary.get(
            "nonzero_covariance_pair_count"
        ),
        "recorded_shard_variance_sum": shard_summary.get("variance_sum"),
        "requirements_passed": len(requirements) - len(failed),
        "requirements_failed": len(failed),
        "failed_requirement_ids": failed,
        "assembled_row_count": 0,
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
        "title": "B3/B10 F1 First Shard Output Gate",
        "version": "0.1",
        "last_updated": args.last_updated,
        "status": STATUS,
        "method": METHOD,
        "model_status": MODEL_STATUS,
        "source_work_order_gate": str(args.work_order_gate),
        "source_shard_output": str(args.shard_output),
        "shard_contract": contract,
        "requirements": requirements,
        "summary": summary,
        "claim_boundary": {
            "what_is_supported": "One H2O full-covariance shard output exists and matches its work-order contract.",
            "what_is_not_supported": "This is not all shards, not an assembled row, not an accepted F1 artifact, not a denominator win, not B3/B10 credit, and not quantum advantage.",
            "next_gate": "Produce the remaining 64 shard outputs, assemble LiH/H2O/N2 rows, then submit the four-row F1 artifact.",
        },
        "validation_errors": validation_errors,
    }


def render_markdown(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    lines = [
        "# B3/B10 F1 First Shard Output Gate",
        "",
        f"- Target: `{payload['source_target_id']}`",
        f"- Method: `{payload['method']}`",
        f"- Status: `{payload['status']}`",
        f"- Recorded shard: `{summary['recorded_shard_id']}`",
        f"- Shard hash: `{summary['recorded_shard_hash']}`",
        "",
        "## Result",
        "",
        (
            f"The gate records 1/{summary['required_total_shard_count']} full-covariance shard output. "
            f"It passes {summary['requirements_passed']}/"
            f"{summary['requirements_passed'] + summary['requirements_failed']} requirements and "
            f"intentionally fails {summary['failed_requirement_ids']} because the remaining shards, "
            "assembled rows, and accepted F1 artifact do not exist yet."
        ),
        "",
        "## Shard Summary",
        "",
        f"- Group count: `{summary['recorded_shard_group_count']}`",
        f"- Nonzero covariance pairs: `{summary['recorded_shard_nonzero_covariance_pair_count']}`",
        f"- Variance sum: `{summary['recorded_shard_variance_sum']}`",
        f"- Remaining shards: `{summary['remaining_shard_count']}`",
        "",
        "## Requirement Results",
        "",
    ]
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
            "This shard gate does not claim a reaction-dynamics solution, quantum advantage, B3 reopen credit, B10-T1 credit, or BQP separation.",
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
        "--work-order-gate",
        type=Path,
        default=Path("results/B3_B10_F1_full_covariance_work_order_gate_v0.json"),
    )
    parser.add_argument(
        "--shard-output",
        type=Path,
        default=Path(
            "results/B3_B10_F1_full_covariance_shards/"
            "h2o_symmetric_oh_stretch/shard_001.json"
        ),
    )
    parser.add_argument(
        "--json-output",
        type=Path,
        default=Path("results/B3_B10_F1_first_shard_output_gate_v0.json"),
    )
    parser.add_argument(
        "--markdown-output",
        type=Path,
        default=Path("research/B3_B10_F1_first_shard_output_gate.md"),
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
                "recorded_shard_hash": payload["summary"]["recorded_shard_hash"],
                "produced_shard_count": payload["summary"]["produced_shard_count"],
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
        raise SystemExit("B3/B10 F1 first shard output gate validation failed")


if __name__ == "__main__":
    main()
