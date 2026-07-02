#!/usr/bin/env python3
"""T-B3-027/T-B10-015n: record the complete H2O F1 covariance shard batch."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


METHOD = "b3_b10_f1_h2o_shard_batch_gate_v0"
STATUS = "h2o_full_covariance_shard_batch_recorded_zero_credit"
MODEL_STATUS = "one_of_three_remaining_molecule_shard_batches_complete_no_row_credit"
SOURCE_TARGET_ID = "T-B3-027/T-B10-015n"
EXPECTED_WORK_ORDER_METHOD = "b3_b10_f1_full_covariance_work_order_gate_v0"
EXPECTED_WORKER_METHOD = "b3_b10_f1_full_covariance_row_worker_v0"
EXPECTED_MOLECULE = "h2o_symmetric_oh_stretch"
EXPECTED_H2O_SHARDS = 7
EXPECTED_TOTAL_SHARDS = 65
EXPECTED_COMPILED_COVER_GROUP_COUNT = 3130
EXPECTED_SHARD_HASHES = [
    "0294e8bc505c5cca1512513058fda2dad6883fa93d5063bc6888a03cec52a2ad",
    "e3d387b2f886cd50235e6f2d2543fc10436543efac19af0a74038e5b531b4f4d",
    "7512802b816e5b0eb51d269e5505e3b75826f7d3afe48f6b58cbbbdfba3d013c",
    "e77074f473ac70857457551b1ae1c3992a6ede74220a14fc81c9a842fe02a336",
    "91a262989b2be8f5d592cf6a514b8b5894bede2b79b457db5dff0fa15740785a",
    "5af82883d7c2acd6d5e76997e3d95d27cb4383bfd7c476e2d79b79d5b85e9ea3",
    "7b9b2ee1ba793759ff78658fbd6faa2af3652c113fec2561308682c4aa72c949",
]


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


def expected_shard_paths(shard_dir: Path) -> list[Path]:
    return [shard_dir / f"shard_{index:03d}.json" for index in range(1, EXPECTED_H2O_SHARDS + 1)]


def summarize_shard(path: Path) -> dict[str, Any]:
    shard = load_json(path)
    summary = shard.get("full_covariance_matrix_shard", {}).get("summary", {})
    return {
        "path": str(path),
        "file_hash": file_hash(path),
        "shard_id": shard.get("shard_id"),
        "method": shard.get("method"),
        "status": shard.get("status"),
        "molecule": shard.get("molecule"),
        "group_start_inclusive": shard.get("group_start_inclusive"),
        "group_end_exclusive": shard.get("group_end_exclusive"),
        "group_count": summary.get("group_count"),
        "nonzero_covariance_pair_count": summary.get("nonzero_covariance_pair_count"),
        "variance_sum": summary.get("variance_sum"),
        "full_covariance_matrix_shard_hash": shard.get("full_covariance_matrix_shard_hash"),
        "compiled_state_replay_hash": shard.get("compiled_state_replay_hash"),
        "qwc_group_manifest_hash": shard.get("qwc_group_manifest_hash"),
        "measurement_basis_manifest_hash": shard.get("measurement_basis_manifest_hash"),
        "stdout_stderr_returncode_hash": shard.get("stdout_stderr_returncode_hash"),
        "wall_time_memory_ledger_hash": shard.get("wall_time_memory_ledger_hash"),
        "claim_boundary_hash": shard.get("claim_boundary_hash"),
        "validation_error_count": len(shard.get("validation_errors", [])),
        "what_is_not_supported": shard.get("claim_boundary", {}).get("what_is_not_supported"),
    }


def find_h2o_work_order(work_order: dict[str, Any]) -> dict[str, Any]:
    for order in work_order.get("work_orders", []):
        if order.get("molecule") == EXPECTED_MOLECULE:
            return order
    return {}


def build_payload(args: argparse.Namespace) -> dict[str, Any]:
    work_order = load_json(args.work_order_gate)
    paths = expected_shard_paths(args.shard_dir)
    existing_paths = [path for path in paths if path.exists()]
    shards = [summarize_shard(path) for path in existing_paths]
    h2o_order = find_h2o_work_order(work_order)
    shard_hashes = [item["full_covariance_matrix_shard_hash"] for item in shards]
    starts = [item["group_start_inclusive"] for item in shards]
    ends = [item["group_end_exclusive"] for item in shards]
    group_counts = [item["group_count"] for item in shards]
    produced_shard_count = len(shards)
    batch_hash = canonical_hash(
        [
            {
                "shard_id": item["shard_id"],
                "group_start_inclusive": item["group_start_inclusive"],
                "group_end_exclusive": item["group_end_exclusive"],
                "full_covariance_matrix_shard_hash": item["full_covariance_matrix_shard_hash"],
            }
            for item in shards
        ]
    )
    contiguous = bool(shards) and starts[0] == 0 and all(
        previous["group_end_exclusive"] == current["group_start_inclusive"]
        for previous, current in zip(shards, shards[1:])
    )
    actual_group_count = sum(item for item in group_counts if isinstance(item, int))
    total_variance_sum = sum(float(item["variance_sum"]) for item in shards)
    total_nonzero_pairs = sum(int(item["nonzero_covariance_pair_count"]) for item in shards)

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
            produced_shard_count == EXPECTED_H2O_SHARDS,
            "All expected H2O shard files exist",
            {
                "produced_h2o_shard_count": produced_shard_count,
                "expected_h2o_shard_count": EXPECTED_H2O_SHARDS,
                "missing_paths": [str(path) for path in paths if not path.exists()],
            },
        ),
        requirement(
            "P3",
            all(
                item["method"] == EXPECTED_WORKER_METHOD
                and item["status"] == "full_covariance_shard_computed_zero_credit"
                and item["molecule"] == EXPECTED_MOLECULE
                and item["validation_error_count"] == 0
                for item in shards
            ),
            "Every H2O shard was produced by the full-covariance worker",
            {"worker_method": EXPECTED_WORKER_METHOD, "validation_error_counts": [s["validation_error_count"] for s in shards]},
        ),
        requirement(
            "P4",
            contiguous
            and starts == [0, 512, 1024, 1536, 2048, 2560, 3072]
            and ends == [512, 1024, 1536, 2048, 2560, 3072, EXPECTED_COMPILED_COVER_GROUP_COUNT]
            and actual_group_count == EXPECTED_COMPILED_COVER_GROUP_COUNT,
            "H2O shards form one contiguous compiled QWC cover",
            {
                "starts": starts,
                "ends": ends,
                "actual_compiled_cover_group_count": actual_group_count,
                "planning_proxy_group_count": h2o_order.get("full_cover_group_count_proxy"),
            },
        ),
        requirement(
            "P5",
            shard_hashes == EXPECTED_SHARD_HASHES,
            "Shard hashes are stable",
            {"shard_hashes": shard_hashes, "h2o_shard_batch_hash": batch_hash},
        ),
        requirement(
            "P6",
            all(
                item.get(key)
                for item in shards
                for key in [
                    "compiled_state_replay_hash",
                    "qwc_group_manifest_hash",
                    "measurement_basis_manifest_hash",
                    "stdout_stderr_returncode_hash",
                    "wall_time_memory_ledger_hash",
                    "claim_boundary_hash",
                ]
            ),
            "Required worker hashes are present on every shard",
            {
                "shard_count_checked": produced_shard_count,
                "batch_hash": batch_hash,
            },
        ),
        requirement(
            "P7",
            all(item.get("what_is_not_supported") for item in shards)
            and work_order.get("summary", {}).get("b10_t1_credit_allowed") is False,
            "Claim boundaries preserve zero credit",
            {
                "accepted_full_covariance_row_count": 0,
                "denominator_win_count": 0,
                "b10_t1_credit_allowed": False,
            },
        ),
        requirement(
            "P8",
            produced_shard_count == EXPECTED_TOTAL_SHARDS,
            "All 65 global F1 shard outputs have been produced",
            {
                "produced_global_shard_count": produced_shard_count,
                "required_total_shard_count": EXPECTED_TOTAL_SHARDS,
                "remaining_global_shard_count": EXPECTED_TOTAL_SHARDS - produced_shard_count,
            },
        ),
        requirement(
            "P9",
            False,
            "LiH/H2O/N2 rows are assembled from all shards",
            {"assembled_row_count": 0, "h2o_row_assembled": False},
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
        "produced_h2o_shard_count": produced_shard_count,
        "required_h2o_shard_count": EXPECTED_H2O_SHARDS,
        "completed_molecule_shard_batch_count": 1 if produced_shard_count == EXPECTED_H2O_SHARDS else 0,
        "produced_global_shard_count": produced_shard_count,
        "required_total_shard_count": EXPECTED_TOTAL_SHARDS,
        "remaining_global_shard_count": EXPECTED_TOTAL_SHARDS - produced_shard_count,
        "h2o_compiled_cover_group_count": actual_group_count,
        "h2o_planning_proxy_group_count": h2o_order.get("full_cover_group_count_proxy"),
        "h2o_shard_batch_hash": batch_hash,
        "h2o_total_nonzero_covariance_pair_count": total_nonzero_pairs,
        "h2o_total_variance_sum": total_variance_sum,
        "requirements_passed": len(requirements) - len(failed),
        "requirements_failed": len(failed),
        "failed_requirement_ids": failed,
        "assembled_row_count": 0,
        "h2o_row_assembled": False,
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
        "title": "B3/B10 F1 H2O Shard Batch Gate",
        "version": "0.1",
        "last_updated": args.last_updated,
        "status": STATUS,
        "method": METHOD,
        "model_status": MODEL_STATUS,
        "source_work_order_gate": str(args.work_order_gate),
        "source_shard_dir": str(args.shard_dir),
        "h2o_work_order": h2o_order,
        "h2o_shards": shards,
        "requirements": requirements,
        "summary": summary,
        "validation_errors": validation_errors,
        "claim_boundary": {
            "what_is_supported": "All seven H2O compiled-state full-covariance shard outputs exist and form one contiguous compiled QWC cover.",
            "what_is_not_supported": "This is not an assembled F1 row, not a LiH/N2 result, not a four-row F1 artifact, not a denominator win, not B3/B10 credit, and not quantum advantage.",
        },
    }


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    summary = payload["summary"]
    lines = [
        "# B3/B10 F1 H2O Shard Batch Gate",
        "",
        f"- Target: `{payload['source_target_id']}`",
        f"- Method: `{payload['method']}`",
        f"- Status: `{payload['status']}`",
        f"- H2O shard batch hash: `{summary['h2o_shard_batch_hash']}`",
        f"- H2O shards: {summary['produced_h2o_shard_count']}/{summary['required_h2o_shard_count']}",
        f"- Global shards: {summary['produced_global_shard_count']}/{summary['required_total_shard_count']}",
        "",
        "## Result",
        "",
        (
            "The gate records a complete H2O shard batch for the F1 route. "
            f"It passes {summary['requirements_passed']}/10 requirements and intentionally fails "
            f"{summary['failed_requirement_ids']} because LiH/N2 shards, assembled rows, and the "
            "accepted four-row F1 artifact do not exist yet."
        ),
        "",
        "## H2O Batch Metrics",
        "",
        f"- Compiled cover groups: {summary['h2o_compiled_cover_group_count']}",
        f"- Planning proxy groups: {summary['h2o_planning_proxy_group_count']}",
        f"- Nonzero covariance pairs: {summary['h2o_total_nonzero_covariance_pair_count']}",
        f"- Variance sum: {summary['h2o_total_variance_sum']}",
        f"- Remaining global shards: {summary['remaining_global_shard_count']}",
        "",
        "## Requirements",
        "",
    ]
    for item in payload["requirements"]:
        marker = "PASS" if item["passed"] else "FAIL"
        lines.append(f"- `{item['id']}` {marker}: {item['description']}")
    lines.extend(
        [
            "",
            "## Claim Boundary",
            "",
            f"- Supported: {payload['claim_boundary']['what_is_supported']}",
            f"- Not supported: {payload['claim_boundary']['what_is_not_supported']}",
            "",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--work-order-gate",
        type=Path,
        default=Path("results/B3_B10_F1_full_covariance_work_order_gate_v0.json"),
    )
    parser.add_argument(
        "--shard-dir",
        type=Path,
        default=Path("results/B3_B10_F1_full_covariance_shards/h2o_symmetric_oh_stretch"),
    )
    parser.add_argument(
        "--json-output",
        type=Path,
        default=Path("results/B3_B10_F1_h2o_shard_batch_gate_v0.json"),
    )
    parser.add_argument(
        "--markdown-output",
        type=Path,
        default=Path("research/B3_B10_F1_h2o_shard_batch_gate.md"),
    )
    parser.add_argument("--last-updated", default="2026-07-03")
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()

    payload = build_payload(args)
    write_json(args.json_output, payload, args.pretty)
    write_markdown(args.markdown_output, payload)
    print(
        json.dumps(
            {
                "status": payload["status"],
                "summary": payload["summary"],
                "json_output": str(args.json_output),
                "markdown_output": str(args.markdown_output),
            },
            indent=2 if args.pretty else None,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
