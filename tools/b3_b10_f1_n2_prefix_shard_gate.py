#!/usr/bin/env python3
"""T-B3-028/T-B10-015o: record the N2 F1 covariance shard prefix."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


METHOD = "b3_b10_f1_n2_prefix_shard_gate_v0"
STATUS = "n2_full_covariance_shard_prefix_recorded_zero_credit"
MODEL_STATUS = "n2_prefix_five_of_nineteen_shards_produced_no_row_credit"
SOURCE_TARGET_ID = "T-B3-028/T-B10-015o"
EXPECTED_WORK_ORDER_METHOD = "b3_b10_f1_full_covariance_work_order_gate_v0"
EXPECTED_WORKER_METHOD = "b3_b10_f1_full_covariance_row_worker_v0"
EXPECTED_MOLECULE = "n2_bond_stretch"
EXPECTED_N2_PREFIX_SHARDS = 5
EXPECTED_N2_TOTAL_SHARDS = 19
EXPECTED_TOTAL_SHARDS = 65
EXPECTED_PREFIX_GROUP_COUNT = 2560
EXPECTED_N2_COMPILED_COVER_GROUP_COUNT = 9476
EXPECTED_PREFIX_HASHES = [
    "3b476a43fe26c2f58b8283981656fcae378b0ad38646872cdeb42830e6078a4a",
    "a3d5d5a495740cb1a153bbd0f153cadbc17d926dab8b4bd8af1da0044fbc5c8f",
    "0da9c214951b193c08d79c71251403001c5837ec3b6a262f7edef7a66463d55d",
    "6f8048f1af6f153d01f118224d25b80f897f59bbde75e474e23ba28cea88bdba",
    "02ecdb8f6605607dfd2b98b8fd83f92510872f6c5ceab3fa350102f7d8605bff",
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


def expected_prefix_paths(shard_dir: Path) -> list[Path]:
    return [shard_dir / f"shard_{index:03d}.json" for index in range(1, EXPECTED_N2_PREFIX_SHARDS + 1)]


def summarize_shard(path: Path) -> dict[str, Any]:
    shard = load_json(path)
    summary = shard.get("full_covariance_matrix_shard", {}).get("summary", {})
    manifest = shard.get("qwc_group_manifest", {})
    return {
        "path": str(path),
        "file_hash": file_hash(path),
        "shard_id": shard.get("shard_id"),
        "method": shard.get("method"),
        "status": shard.get("status"),
        "molecule": shard.get("molecule"),
        "group_start_inclusive": shard.get("group_start_inclusive"),
        "group_end_exclusive": shard.get("group_end_exclusive"),
        "compiled_qwc_group_count": manifest.get("compiled_qwc_group_count"),
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


def count_existing_global_shards(root: Path) -> int:
    return sum(1 for _ in root.glob("*/*.json"))


def find_n2_work_order(work_order: dict[str, Any]) -> dict[str, Any]:
    for order in work_order.get("work_orders", []):
        if order.get("molecule") == EXPECTED_MOLECULE:
            return order
    return {}


def build_payload(args: argparse.Namespace) -> dict[str, Any]:
    work_order = load_json(args.work_order_gate)
    paths = expected_prefix_paths(args.shard_dir)
    existing_paths = [path for path in paths if path.exists()]
    shards = [summarize_shard(path) for path in existing_paths]
    n2_order = find_n2_work_order(work_order)
    shard_hashes = [item["full_covariance_matrix_shard_hash"] for item in shards]
    starts = [item["group_start_inclusive"] for item in shards]
    ends = [item["group_end_exclusive"] for item in shards]
    group_counts = [item["group_count"] for item in shards]
    produced_prefix_count = len(shards)
    produced_global_count = count_existing_global_shards(args.shard_root)
    prefix_hash = canonical_hash(
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
    actual_prefix_group_count = sum(item for item in group_counts if isinstance(item, int))
    total_variance_sum = sum(float(item["variance_sum"]) for item in shards)
    total_nonzero_pairs = sum(int(item["nonzero_covariance_pair_count"]) for item in shards)
    compiled_cover_counts = sorted({item["compiled_qwc_group_count"] for item in shards})

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
            produced_prefix_count == EXPECTED_N2_PREFIX_SHARDS,
            "All expected N2 prefix shard files exist",
            {
                "produced_n2_prefix_shard_count": produced_prefix_count,
                "expected_n2_prefix_shard_count": EXPECTED_N2_PREFIX_SHARDS,
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
            "Every N2 prefix shard was produced by the full-covariance worker",
            {
                "worker_method": EXPECTED_WORKER_METHOD,
                "validation_error_counts": [item["validation_error_count"] for item in shards],
            },
        ),
        requirement(
            "P4",
            contiguous
            and starts == [0, 512, 1024, 1536, 2048]
            and ends == [512, 1024, 1536, 2048, EXPECTED_PREFIX_GROUP_COUNT]
            and actual_prefix_group_count == EXPECTED_PREFIX_GROUP_COUNT
            and compiled_cover_counts == [EXPECTED_N2_COMPILED_COVER_GROUP_COUNT],
            "N2 prefix shards form one contiguous compiled QWC prefix",
            {
                "starts": starts,
                "ends": ends,
                "actual_prefix_group_count": actual_prefix_group_count,
                "compiled_cover_counts": compiled_cover_counts,
                "planning_proxy_group_count": n2_order.get("full_cover_group_count_proxy"),
            },
        ),
        requirement(
            "P5",
            shard_hashes == EXPECTED_PREFIX_HASHES,
            "N2 prefix shard hashes are stable",
            {"shard_hashes": shard_hashes, "n2_prefix_shard_batch_hash": prefix_hash},
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
            "Required worker hashes are present on every prefix shard",
            {"shard_count_checked": produced_prefix_count, "batch_hash": prefix_hash},
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
            produced_global_count == EXPECTED_TOTAL_SHARDS,
            "All 65 global F1 shard outputs have been produced",
            {
                "produced_global_shard_count": produced_global_count,
                "required_total_shard_count": EXPECTED_TOTAL_SHARDS,
                "remaining_global_shard_count": EXPECTED_TOTAL_SHARDS - produced_global_count,
            },
        ),
        requirement(
            "P9",
            False,
            "LiH/H2O/N2 rows are assembled from all shards",
            {"assembled_row_count": 0, "n2_row_assembled": False},
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
        "produced_n2_prefix_shard_count": produced_prefix_count,
        "required_n2_prefix_shard_count": EXPECTED_N2_PREFIX_SHARDS,
        "produced_n2_total_shard_count": produced_prefix_count,
        "required_n2_total_shard_count": EXPECTED_N2_TOTAL_SHARDS,
        "remaining_n2_shard_count": EXPECTED_N2_TOTAL_SHARDS - produced_prefix_count,
        "produced_global_shard_count": produced_global_count,
        "required_total_shard_count": EXPECTED_TOTAL_SHARDS,
        "remaining_global_shard_count": EXPECTED_TOTAL_SHARDS - produced_global_count,
        "n2_prefix_group_count": actual_prefix_group_count,
        "n2_compiled_cover_group_count": EXPECTED_N2_COMPILED_COVER_GROUP_COUNT,
        "n2_planning_proxy_group_count": n2_order.get("full_cover_group_count_proxy"),
        "n2_prefix_shard_batch_hash": prefix_hash,
        "n2_prefix_nonzero_covariance_pair_count": total_nonzero_pairs,
        "n2_prefix_variance_sum": total_variance_sum,
        "requirements_passed": len(requirements) - len(failed),
        "requirements_failed": len(failed),
        "failed_requirement_ids": failed,
        "assembled_row_count": 0,
        "n2_row_assembled": False,
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
        "title": "B3/B10 F1 N2 Prefix Shard Gate",
        "version": "0.1",
        "last_updated": args.last_updated,
        "status": STATUS,
        "method": METHOD,
        "model_status": MODEL_STATUS,
        "source_work_order_gate": str(args.work_order_gate),
        "source_shard_dir": str(args.shard_dir),
        "n2_work_order": n2_order,
        "n2_prefix_shards": shards,
        "requirements": requirements,
        "summary": summary,
        "validation_errors": validation_errors,
        "claim_boundary": {
            "what_is_supported": "The first five N2 compiled-state full-covariance shard outputs exist and form a contiguous compiled QWC prefix.",
            "what_is_not_supported": "This is not a complete N2 shard batch, not an assembled F1 row, not a LiH result, not a four-row F1 artifact, not a denominator win, not B3/B10 credit, and not quantum advantage.",
        },
    }


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    summary = payload["summary"]
    lines = [
        "# B3/B10 F1 N2 Prefix Shard Gate",
        "",
        f"- Target: `{payload['source_target_id']}`",
        f"- Method: `{payload['method']}`",
        f"- Status: `{payload['status']}`",
        f"- N2 prefix batch hash: `{summary['n2_prefix_shard_batch_hash']}`",
        f"- N2 prefix shards: {summary['produced_n2_prefix_shard_count']}/{summary['required_n2_total_shard_count']}",
        f"- Global shards: {summary['produced_global_shard_count']}/{summary['required_total_shard_count']}",
        "",
        "## Result",
        "",
        (
            "The gate records the first five N2 shard outputs for the F1 route. "
            f"It passes {summary['requirements_passed']}/10 requirements and intentionally fails "
            f"{summary['failed_requirement_ids']} because the rest of N2, all LiH shards, assembled rows, "
            "and the accepted four-row F1 artifact do not exist yet."
        ),
        "",
        "## N2 Prefix Metrics",
        "",
        f"- Prefix groups: {summary['n2_prefix_group_count']}",
        f"- Compiled cover groups: {summary['n2_compiled_cover_group_count']}",
        f"- Planning proxy groups: {summary['n2_planning_proxy_group_count']}",
        f"- Nonzero covariance pairs: {summary['n2_prefix_nonzero_covariance_pair_count']}",
        f"- Variance sum: {summary['n2_prefix_variance_sum']}",
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
        "--shard-root",
        type=Path,
        default=Path("results/B3_B10_F1_full_covariance_shards"),
    )
    parser.add_argument(
        "--shard-dir",
        type=Path,
        default=Path("results/B3_B10_F1_full_covariance_shards/n2_bond_stretch"),
    )
    parser.add_argument(
        "--json-output",
        type=Path,
        default=Path("results/B3_B10_F1_n2_prefix_shard_gate_v0.json"),
    )
    parser.add_argument(
        "--markdown-output",
        type=Path,
        default=Path("research/B3_B10_F1_n2_prefix_shard_gate.md"),
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
