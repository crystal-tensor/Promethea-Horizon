#!/usr/bin/env python3
"""Standard-library-only oracle for the dual-platform R186 evidence."""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import math
import statistics
from pathlib import Path
from typing import Any


METHOD = "b4_b8_r186_independent_oracle_v0"
PROTOCOL_PATH = "results/B4_B8_R186_full_vf2_workflow_protocol_v0.json"
DESIGN_CONTRACT_PATH = "benchmarks/B4_B8_R186_full_vf2_workflow_contract_v0.json"
EXECUTION_CONTRACT_PATH = (
    "benchmarks/B4_B8_R186_full_vf2_workflow_execution_contract_v0.json"
)
RESULT_PATHS = {
    "linux_x86_64": "results/B4_B8_R186_full_vf2_workflow_linux_x86_64_v0.json",
    "macos_arm64": "results/B4_B8_R186_full_vf2_workflow_macos_arm64_v0.json",
}
ORACLE_PATH = "results/B4_B8_R186_independent_oracle_v0.json"
REPORT_PATH = "research/B4_B8_R186_independent_oracle.md"
ARMS = ("baseline", "reference", "candidate")
SURFACES = ("accelerator_entrypoint", "python_passmanager")


def canonical_hash(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def validate_hash(payload: dict[str, Any], field: str, label: str) -> str:
    body = dict(payload)
    observed = body.pop(field, None)
    if not observed or observed != canonical_hash(body):
        raise ValueError(f"R186 oracle {label} hash mismatch")
    return str(observed)


def close(left: float, right: float) -> bool:
    return math.isclose(left, right, rel_tol=1e-12, abs_tol=1e-15)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def load_payload(root: Path, relative: str, field: str = "payload_hash") -> dict[str, Any]:
    payload = json.loads((root / relative).read_text(encoding="utf-8"))
    validate_hash(payload, field, relative)
    return payload


def recompute_platform(
    root: Path,
    platform_id: str,
    result: dict[str, Any],
    protocol: dict[str, Any],
) -> dict[str, Any]:
    manifests = []
    rows = []
    manifest_hash_count = 0
    row_hash_count = 0
    for relative in result["worker_manifest_paths"]:
        manifest = load_payload(root, relative, "manifest_hash")
        manifest_hash_count += 1
        if manifest["platform_id"] != platform_id:
            raise ValueError("R186 oracle platform manifest mismatch")
        for row in manifest["replay_rows"]:
            validate_hash(row, "row_hash", f"{relative} row")
            row_hash_count += 1
            rows.append(row)
        manifests.append(manifest)

    ratios: dict[str, dict[str, float]] = {}
    for surface in SURFACES:
        ratios[surface] = {
            "candidate_to_baseline_paired_median": statistics.median(
                row["measurements"][surface]["candidate"]["elapsed_nanoseconds"]
                / row["measurements"][surface]["baseline"]["elapsed_nanoseconds"]
                for row in rows
            ),
            "candidate_to_reference_paired_median": statistics.median(
                row["measurements"][surface]["candidate"]["elapsed_nanoseconds"]
                / row["measurements"][surface]["reference"]["elapsed_nanoseconds"]
                for row in rows
            ),
        }
    direct = ratios["accelerator_entrypoint"][
        "candidate_to_baseline_paired_median"
    ]
    workflow = ratios["python_passmanager"][
        "candidate_to_baseline_paired_median"
    ]
    retention = (1.0 - workflow) / (1.0 - direct) if direct < 1.0 else None
    mapping_checks = len(rows) * len(ARMS) * len(SURFACES)
    mapping_matches = sum(
        row["measurements"][surface][arm]["mapping_vector"]
        == row["expected_mapping_vector"]
        for row in rows
        for surface in SURFACES
        for arm in ARMS
    )
    cross_surface_matches = sum(
        all(
            row["measurements"][SURFACES[0]][arm]["mapping_vector"]
            == row["measurements"][SURFACES[1]][arm]["mapping_vector"]
            for arm in ARMS
        )
        for row in rows
    )
    hypotheses = {
        "H1-full-boundary-integrity": (
            mapping_matches == mapping_checks
            and cross_surface_matches == len(rows)
        ),
        "H2-direct-window-competitiveness": direct <= 1.0,
        "H3-passmanager-window-competitiveness": workflow <= 1.0,
        "H4-relative-saving-retention": retention is not None and retention >= 0.1,
    }
    workload = protocol["frozen_workload"]
    schedule_counts_match = all(
        len(manifest["schedule_counts"]) == workload["schedule_count"]
        and set(manifest["schedule_counts"].values())
        == {workload["repetitions_per_schedule_per_cell"]}
        for manifest in manifests
    )
    stored_ratios_match = all(
        close(
            ratios[surface][key],
            result["aggregate_surface_ratios"][surface][key],
        )
        for surface in SURFACES
        for key in (
            "candidate_to_baseline_paired_median",
            "candidate_to_reference_paired_median",
        )
    )
    if retention is None:
        retention_matches = result["relative_saving_retention_fraction"] is None
    else:
        retention_matches = close(
            retention, result["relative_saving_retention_fraction"]
        )
    return {
        "platform_id": platform_id,
        "result_payload_hash": result["payload_hash"],
        "worker_manifest_count": len(manifests),
        "worker_manifest_hash_count": manifest_hash_count,
        "row_count": len(rows),
        "row_hash_count": row_hash_count,
        "mapping_check_count": mapping_checks,
        "mapping_match_count": mapping_matches,
        "cross_surface_mapping_match_count": cross_surface_matches,
        "measured_timing_call_count": sum(
            manifest["timing_call_count"] for manifest in manifests
        ),
        "warmup_call_count": sum(
            manifest["warmup_call_count"] for manifest in manifests
        ),
        "aggregate_surface_ratios": ratios,
        "relative_saving_retention_fraction": retention,
        "stored_ratios_match": stored_ratios_match,
        "stored_retention_matches": retention_matches,
        "schedule_counts_match": schedule_counts_match,
        "hypothesis_support": hypotheses,
        "stored_hypotheses_match": hypotheses == result["hypothesis_support"],
        "zero_simulation_and_hardware_rows": all(
            row["simulation_execution_count"] == 0
            and row["total_simulated_shots"] == 0
            and row["real_backend_row_count"] == 0
            for row in rows
        ),
    }


def render_report(oracle: dict[str, Any]) -> str:
    lines = [
        "# B4/B8/B10 R186 Independent Oracle",
        "",
        f"- Status: `{oracle['status']}`",
        f"- Oracle payload hash: `{oracle['payload_hash']}`",
        f"- Requirements: `{oracle['requirements_passed']}/{oracle['requirements_passed'] + oracle['requirements_failed']}`",
        f"- Worker manifests: `{oracle['worker_manifest_hash_count']}/{oracle['worker_manifest_count']}`",
        f"- Row hashes: `{oracle['row_hash_count']}/{oracle['row_count']}`",
        f"- Mapping checks: `{oracle['mapping_match_count']}/{oracle['mapping_check_count']}`",
        "",
        "## Cross-Architecture Question",
        "",
        "Does the exact-window gain survive the Python VF2Layout/PassManager boundary on both architectures under one unchanged protocol?",
        "",
        "## Recomputed Results",
        "",
    ]
    for platform_id, summary in oracle["platform_summaries"].items():
        direct = summary["aggregate_surface_ratios"]["accelerator_entrypoint"][
            "candidate_to_baseline_paired_median"
        ]
        workflow = summary["aggregate_surface_ratios"]["python_passmanager"][
            "candidate_to_baseline_paired_median"
        ]
        lines.extend(
            [
                f"### {platform_id}",
                "",
                f"- Direct window/BigUint: `{direct:.9f}x`",
                f"- PassManager window/BigUint: `{workflow:.9f}x`",
                f"- Relative saving retained: `{summary['relative_saving_retention_fraction']:.9f}`",
                "",
            ]
        )
    lines.extend(
        [
            "## Hypotheses",
            "",
        ]
    )
    lines.extend(
        f"- `{key}`: `{value}`" for key, value in oracle["hypothesis_support"].items()
    )
    lines.extend(
        [
            "",
            "## Claim Boundary",
            "",
            "The oracle uses only the Python standard library and imports neither Qiskit nor the R186 executor. This validates the committed hashes, mapping decisions, timing arithmetic, and frozen classifications. It does not turn the external monkeypatch harness into an upstream integration, full transpilation result, hardware result, quantum advantage, BQP separation, solved frontier, or new credit.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path)
    parser.add_argument("--preregistration-commit", required=True)
    parser.add_argument("--preregistration-discussion", required=True)
    args = parser.parse_args()
    root = (args.root or Path(__file__).resolve().parents[1]).resolve()
    if (root / ORACLE_PATH).exists() or (root / REPORT_PATH).exists():
        raise ValueError("R186 oracle output already exists")

    protocol = load_payload(root, PROTOCOL_PATH)
    design = load_payload(root, DESIGN_CONTRACT_PATH)
    execution = load_payload(root, EXECUTION_CONTRACT_PATH)
    if design["protocol_payload_hash"] != protocol["payload_hash"]:
        raise ValueError("R186 oracle design binding mismatch")
    if execution["protocol_payload_hash"] != protocol["payload_hash"]:
        raise ValueError("R186 oracle execution binding mismatch")
    public = execution["public_preregistration"]
    if args.preregistration_discussion != public["discussion"]:
        raise ValueError("R186 oracle Discussion mismatch")

    results = {
        platform_id: load_payload(root, relative)
        for platform_id, relative in RESULT_PATHS.items()
    }
    platform_summaries = {
        platform_id: recompute_platform(
            root, platform_id, results[platform_id], protocol
        )
        for platform_id in RESULT_PATHS
    }
    local_hypotheses = [
        "H1-full-boundary-integrity",
        "H2-direct-window-competitiveness",
        "H3-passmanager-window-competitiveness",
        "H4-relative-saving-retention",
    ]
    hypotheses = {
        hypothesis: all(
            summary["hypothesis_support"][hypothesis]
            for summary in platform_summaries.values()
        )
        for hypothesis in local_hypotheses
    }
    hypotheses["H5-cross-architecture-workflow-transfer"] = all(
        hypotheses.values()
    )
    workload = protocol["frozen_workload"]
    worker_count = sum(
        summary["worker_manifest_count"]
        for summary in platform_summaries.values()
    )
    row_count = sum(summary["row_count"] for summary in platform_summaries.values())
    mapping_count = sum(
        summary["mapping_check_count"] for summary in platform_summaries.values()
    )
    mapping_matches = sum(
        summary["mapping_match_count"] for summary in platform_summaries.values()
    )
    tool_source = Path(__file__).read_text(encoding="utf-8")
    imported_modules = []
    for node in ast.walk(ast.parse(tool_source)):
        if isinstance(node, ast.Import):
            imported_modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_modules.append(node.module)
    requirements = {
        "Q1_protocol_design_execution_hashes_validate": True,
        "Q2_both_platform_result_hashes_validate": len(results) == 2,
        "Q3_all_worker_manifest_hashes_validate": worker_count
        == 2 * workload["workload_cell_count"],
        "Q4_all_row_hashes_validate": row_count
        == 2 * workload["measured_row_count"],
        "Q5_all_mapping_outputs_match": mapping_matches == mapping_count,
        "Q6_all_schedule_counts_match": all(
            summary["schedule_counts_match"]
            for summary in platform_summaries.values()
        ),
        "Q7_all_call_counts_match": all(
            summary["measured_timing_call_count"]
            == workload["measured_timing_call_count_per_platform"]
            and summary["warmup_call_count"]
            == workload["warmup_call_count_per_platform"]
            for summary in platform_summaries.values()
        ),
        "Q8_stored_ratios_and_retention_match": all(
            summary["stored_ratios_match"]
            and summary["stored_retention_matches"]
            for summary in platform_summaries.values()
        ),
        "Q9_stored_platform_hypotheses_match": all(
            summary["stored_hypotheses_match"]
            for summary in platform_summaries.values()
        ),
        "Q10_h1_through_h4_pass_both_platforms": all(
            hypotheses[key] for key in local_hypotheses
        ),
        "Q11_h5_cross_architecture_transfer_passes": hypotheses[
            "H5-cross-architecture-workflow-transfer"
        ],
        "Q12_zero_simulation_shots_and_real_backend_rows": all(
            summary["zero_simulation_and_hardware_rows"]
            for summary in platform_summaries.values()
        ),
        "Q13_oracle_imports_neither_qiskit_nor_executor": not any(
            name == "qiskit"
            or name.startswith("qiskit.")
            or name.endswith("r186_full_vf2_workflow_replay")
            for name in imported_modules
        ),
    }
    passed = sum(requirements.values())
    oracle: dict[str, Any] = {
        "title": "B4/B8/B10 R186 independent full-workflow oracle",
        "version": 0,
        "method": METHOD,
        "status": "independent_oracle_complete",
        "source_target_id": "T-B4-002eh/T-B8-003el/T-B10-009dx-r186-oracle",
        "preregistration": {
            "commit": args.preregistration_commit,
            "discussion": args.preregistration_discussion,
        },
        "protocol_payload_hash": protocol["payload_hash"],
        "design_contract_payload_hash": design["payload_hash"],
        "execution_contract_payload_hash": execution["payload_hash"],
        "platform_result_payload_hashes": {
            platform_id: result["payload_hash"]
            for platform_id, result in results.items()
        },
        "platform_summaries": platform_summaries,
        "worker_manifest_count": worker_count,
        "worker_manifest_hash_count": sum(
            summary["worker_manifest_hash_count"]
            for summary in platform_summaries.values()
        ),
        "row_count": row_count,
        "row_hash_count": sum(
            summary["row_hash_count"] for summary in platform_summaries.values()
        ),
        "mapping_check_count": mapping_count,
        "mapping_match_count": mapping_matches,
        "hypothesis_support": hypotheses,
        "requirements": requirements,
        "requirements_passed": passed,
        "requirements_failed": len(requirements) - passed,
        "simulation_execution_count": 0,
        "total_simulated_shots": 0,
        "real_backend_row_count": 0,
        "claim_boundary": {
            "independent_arithmetic_and_hash_recomputation": True,
            "imports_qiskit": False,
            "imports_executor": False,
            "external_monkeypatch_harness": True,
            "upstream_patch_accepted": False,
            "full_transpilation_pipeline_benchmarked": False,
            "production_qiskit_remedy_claimed": False,
            "hardware_result_claimed": False,
            "quantum_advantage_claimed": False,
            "bqp_separation_claimed": False,
            "solved_frontier_claimed": False,
            "new_credit_delta": 0,
        },
    }
    oracle["payload_hash"] = canonical_hash(oracle)
    write_json(root / ORACLE_PATH, oracle)
    (root / REPORT_PATH).write_text(render_report(oracle), encoding="utf-8")
    print(
        json.dumps(
            {
                "status": oracle["status"],
                "requirements": [passed, len(requirements) - passed],
                "hypothesis_support": hypotheses,
                "payload_hash": oracle["payload_hash"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if not oracle["requirements_failed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
