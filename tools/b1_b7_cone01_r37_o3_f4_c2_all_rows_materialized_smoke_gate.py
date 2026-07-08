#!/usr/bin/env python3
"""T-B1-004em/T-B7-013v: R37 O3-F4 C2 all-row materialized smoke gate."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import time
from pathlib import Path
from typing import Any


METHOD = "b1_b7_cone01_r37_o3_f4_c2_all_rows_materialized_smoke_gate_v0"
STATUS = "cone01_r37_o3_f4_c2_all_rows_materialized_smoke_rejected"
MODEL_STATUS = "o3_f4_c2_all_rows_materialized_smoke_no_source_backed_acceptance"
VERSION = "0.1"
TARGET_ID = "T-B1-004em/T-B7-013v"
UPSTREAM_TARGET_ID = "T-B1-004el/T-B7-013u"
FAMILY_ID = "O3-F4"
CANDIDATE_ID = "NL-C02"
STRICT_TOLERANCE = 1.0e-8
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
FILE_ARTIFACT_FIELDS = [
    "replay_stdout_file",
    "source_circuit_file",
    "candidate_circuit_file",
    "same_unitary_witness_file",
]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any], pretty: bool = True) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2 if pretty else None, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def stable_hash(payload: Any) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def is_sha256(value: Any) -> bool:
    return isinstance(value, str) and bool(SHA256_RE.fullmatch(value))


def requirement(
    requirement_id: str, label: str, passed: bool, evidence: dict[str, Any]
) -> dict[str, Any]:
    return {
        "requirement_id": requirement_id,
        "label": label,
        "passed": bool(passed),
        "evidence": evidence,
    }


def challenge_id(index: int) -> str:
    return f"O3-F4-C{index + 1:02d}"


def write_row_artifacts(root: Path, artifact_dir: Path, cid: str, index: int) -> dict[str, str]:
    artifact_dir.mkdir(parents=True, exist_ok=True)
    angle = f"0.{125 + index:03d}"
    files = {
        f"{cid}.stdout.txt": "\n".join(
            [
                "R37 C2 all-row materialized smoke artifact",
                "scope: materialization-only; not an accepted C2 replay",
                f"challenge_id: {cid}",
                "max_unitary_replay_error: 1e-10",
                "claim_boundary: no C2/O3/reroute/B7/STV credit",
                "",
            ]
        ),
        f"{cid}.source.qasm": "\n".join(
            [
                "OPENQASM 3.0;",
                f"// R37 smoke source circuit for {cid}.",
                "// Materialized file/hash surface only; not source-backed C2 proof.",
                "qubit[1] q;",
                f"rz({angle}) q[0];",
                "",
            ]
        ),
        f"{cid}.candidate.qasm": "\n".join(
            [
                "OPENQASM 3.0;",
                f"// R37 smoke candidate circuit for {cid}.",
                "// Materialized file/hash surface only; not source-backed C2 proof.",
                "qubit[1] q;",
                f"rz({angle}) q[0];",
                "",
            ]
        ),
        f"{cid}.witness.json": json.dumps(
            {
                "artifact": "R37 C2 all-row materialized smoke witness",
                "challenge_id": cid,
                "scope": "materialization_only_not_same_unitary_certificate",
                "max_unitary_replay_error": 1.0e-10,
                "claim_boundary": "no C2/O3/reroute/B7/STV credit",
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
    }
    paths = {}
    for name, text in files.items():
        path = artifact_dir / name
        path.write_text(text, encoding="utf-8")
        paths[name] = str(path.relative_to(root))
    return paths


def build_row(contract: dict[str, Any], root: Path, artifact_dir: Path, index: int) -> dict[str, Any]:
    cid = challenge_id(index)
    paths = write_row_artifacts(root, artifact_dir, cid, index)
    replay_stdout_file = paths[f"{cid}.stdout.txt"]
    source_circuit_file = paths[f"{cid}.source.qasm"]
    candidate_circuit_file = paths[f"{cid}.candidate.qasm"]
    witness_file = paths[f"{cid}.witness.json"]
    replay_stdout_hash = file_hash(root / replay_stdout_file)
    source_hash = file_hash(root / source_circuit_file)
    candidate_hash = file_hash(root / candidate_circuit_file)
    witness_hash = file_hash(root / witness_file)
    replay_error = 1.0e-10
    binding_payload = {
        "challenge_id": cid,
        "parameter_indices": [1381, index + 1],
        "submitted_parameter_values": [f"theta_{cid}_a", f"theta_{cid}_b"],
        "strict_tolerance": STRICT_TOLERANCE,
        "max_unitary_replay_error": replay_error,
        "unitary_distance_metric": "operator_norm",
        "source_circuit_hash": source_hash,
        "candidate_circuit_hash": candidate_hash,
        "replay_command": (
            "python3 tools/b1_b7_cone01_c2_replay.py "
            f"--challenge-id {cid}"
        ),
        "replay_stdout_hash": replay_stdout_hash,
        "verifier_version": METHOD,
    }
    provenance_binding_hash = stable_hash(binding_payload)
    return {
        "challenge_id": cid,
        "binding_payload": binding_payload,
        "declared_provenance_binding_hash": provenance_binding_hash,
        "execution_artifacts": {
            "replay_stdout_file": replay_stdout_file,
            "replay_stdout_hash": replay_stdout_hash,
            "source_circuit_file": source_circuit_file,
            "source_circuit_hash": source_hash,
            "candidate_circuit_file": candidate_circuit_file,
            "candidate_circuit_hash": candidate_hash,
            "same_unitary_witness_file": witness_file,
            "same_unitary_witness_hash": witness_hash,
            "provenance_binding_hash": provenance_binding_hash,
        },
        "max_unitary_replay_error": replay_error,
        "claim_boundary": "no C2/O3/reroute/B7/STV credit before acceptance",
        "smoke_only_not_c2_acceptance": True,
        "source_backed_replay": False,
        "same_unitary_certificate": False,
    }


def build_fixture(contract: dict[str, Any], root: Path, artifact_dir: Path) -> dict[str, Any]:
    rows = [build_row(contract, root, artifact_dir, index) for index in range(8)]
    fixture = {
        "artifact_id": "B1-B7-cone01-O3-F4-C2-all-rows-materialized-smoke.fixture",
        "source_target_id": TARGET_ID,
        "upstream_target_id": UPSTREAM_TARGET_ID,
        "contract_hash": contract["contract_hash"],
        "strict_tolerance": STRICT_TOLERANCE,
        "rows": rows,
        "o3_closed": False,
        "reroute_allowed": False,
        "b7_credit_delta": 0,
    }
    fixture["fixture_hash"] = stable_hash(fixture)
    return fixture


def verify_row(row: dict[str, Any], contract: dict[str, Any], root: Path) -> dict[str, Any]:
    binding_payload = row.get("binding_payload", {})
    execution_artifacts = row.get("execution_artifacts", {})
    missing_binding_fields = [
        field for field in contract["binding_fields"] if field not in binding_payload
    ]
    missing_execution_artifacts = [
        field
        for field in contract["required_execution_artifacts"]
        if field not in execution_artifacts
    ]
    hash_cells = {
        "declared_provenance_binding_hash": row.get("declared_provenance_binding_hash"),
        "source_circuit_hash": binding_payload.get("source_circuit_hash"),
        "candidate_circuit_hash": binding_payload.get("candidate_circuit_hash"),
        "replay_stdout_hash": binding_payload.get("replay_stdout_hash"),
        "witness_hash": execution_artifacts.get("same_unitary_witness_hash"),
    }
    invalid_hash_cells = [key for key, value in hash_cells.items() if not is_sha256(value)]
    binding_hash_matches = (
        row.get("declared_provenance_binding_hash") == stable_hash(binding_payload)
        and execution_artifacts.get("provenance_binding_hash")
        == row.get("declared_provenance_binding_hash")
    )
    try:
        replay_error = float(row.get("max_unitary_replay_error"))
        replay_error_within_tolerance = replay_error <= STRICT_TOLERANCE
    except (TypeError, ValueError):
        replay_error = None
        replay_error_within_tolerance = False
    file_results = []
    for field in FILE_ARTIFACT_FIELDS:
        path_value = execution_artifacts.get(field)
        expected_hash = execution_artifacts.get(field.replace("_file", "_hash"))
        path = root / path_value if isinstance(path_value, str) else None
        exists = bool(path and path.exists() and path.is_file())
        actual_hash = file_hash(path) if exists else None
        file_results.append(
            {
                "field": field,
                "path": path_value,
                "exists": exists,
                "expected_hash": expected_hash,
                "actual_hash": actual_hash,
                "hash_matches": exists and actual_hash == expected_hash,
            }
        )
    materialized_passed = all(item["exists"] and item["hash_matches"] for item in file_results)
    surface_passed = (
        not missing_binding_fields
        and not missing_execution_artifacts
        and not invalid_hash_cells
        and binding_hash_matches
        and replay_error_within_tolerance
    )
    return {
        "challenge_id": row.get("challenge_id"),
        "surface_passed": surface_passed,
        "materialized_passed": materialized_passed,
        "missing_binding_fields": missing_binding_fields,
        "missing_execution_artifacts": missing_execution_artifacts,
        "invalid_hash_cells": invalid_hash_cells,
        "binding_hash_matches": binding_hash_matches,
        "replay_error_within_tolerance": replay_error_within_tolerance,
        "file_results": file_results,
        "missing_file_count": sum(1 for item in file_results if not item["exists"]),
        "hash_mismatch_count": sum(
            1 for item in file_results if item["exists"] and not item["hash_matches"]
        ),
        "source_backed_replay": row.get("source_backed_replay") is True,
        "same_unitary_certificate": row.get("same_unitary_certificate") is True,
        "smoke_only_not_c2_acceptance": row.get("smoke_only_not_c2_acceptance") is True,
    }


def evaluate_fixture(
    fixture: dict[str, Any], contract: dict[str, Any], root: Path, fixture_path: Path
) -> dict[str, Any]:
    row_results = [verify_row(row, contract, root) for row in fixture.get("rows", [])]
    evaluation = {
        "input_artifact": str(fixture_path),
        "input_artifact_sha256": file_hash(fixture_path),
        "fixture_hash": fixture["fixture_hash"],
        "contract_hash": contract["contract_hash"],
        "row_count": len(row_results),
        "required_row_count": contract["required_row_count"],
        "row_results": row_results,
        "surface_rows_passed": sum(1 for row in row_results if row["surface_passed"]),
        "materialized_rows_passed": sum(
            1 for row in row_results if row["materialized_passed"]
        ),
        "source_backed_rows_passed": sum(
            1
            for row in row_results
            if row["source_backed_replay"] and row["same_unitary_certificate"]
        ),
        "smoke_only_row_count": sum(
            1 for row in row_results if row["smoke_only_not_c2_acceptance"]
        ),
        "missing_materialized_file_count": sum(
            row["missing_file_count"] for row in row_results
        ),
        "materialized_hash_mismatch_count": sum(
            row["hash_mismatch_count"] for row in row_results
        ),
        "accepted": False,
    }
    evaluation["accepted"] = (
        evaluation["row_count"] == evaluation["required_row_count"]
        and evaluation["surface_rows_passed"] == evaluation["required_row_count"]
        and evaluation["materialized_rows_passed"] == evaluation["required_row_count"]
        and evaluation["source_backed_rows_passed"] == evaluation["required_row_count"]
        and fixture.get("o3_closed") is False
        and fixture.get("reroute_allowed") is False
        and fixture.get("b7_credit_delta") == 0
    )
    evaluation["failed_reasons"] = []
    if evaluation["source_backed_rows_passed"] != evaluation["required_row_count"]:
        evaluation["failed_reasons"].append("materialized_rows_are_smoke_not_source_backed")
    evaluation["preflight_hash"] = stable_hash(evaluation)
    return evaluation


def build_payload(args: argparse.Namespace) -> tuple[dict[str, Any], dict[str, Any]]:
    started = time.time()
    r36 = load_json(args.r36_smoke)
    r33 = load_json(args.r33_contract)
    contract = r33["o3_f4_c2_provenance_binding_contract_packet"]["contract"]
    fixture = build_fixture(contract, args.root, args.artifact_dir)
    write_json(args.fixture_output, fixture, pretty=True)
    evaluation = evaluate_fixture(fixture, contract, args.root, args.fixture_output)
    requirements = [
        requirement(
            "S1",
            "R36 source smoke gate is validation-clean with exactly one materialized row",
            r36["summary"].get("validation_error_count") == 0
            and r36["summary"].get("materialized_rows_passed") == 1
            and r36["summary"].get("missing_materialized_file_count") == 28,
            {
                "r36_validation_error_count": r36["summary"].get("validation_error_count"),
                "r36_materialized_rows_passed": r36["summary"].get(
                    "materialized_rows_passed"
                ),
                "r36_missing_materialized_file_count": r36["summary"].get(
                    "missing_materialized_file_count"
                ),
            },
        ),
        requirement(
            "S2",
            "R37 materializes all 8 rows with hash-matched files",
            evaluation["materialized_rows_passed"] == 8
            and evaluation["missing_materialized_file_count"] == 0
            and evaluation["materialized_hash_mismatch_count"] == 0,
            {
                "materialized_rows_passed": evaluation["materialized_rows_passed"],
                "missing_materialized_file_count": evaluation[
                    "missing_materialized_file_count"
                ],
                "materialized_hash_mismatch_count": evaluation[
                    "materialized_hash_mismatch_count"
                ],
            },
        ),
        requirement(
            "S3",
            "All 8 rows pass the metadata surface",
            evaluation["surface_rows_passed"] == 8,
            {"surface_rows_passed": evaluation["surface_rows_passed"]},
        ),
        requirement(
            "S4",
            "All 8 rows remain smoke-only and therefore are not C2 accepted",
            evaluation["smoke_only_row_count"] == 8
            and evaluation["source_backed_rows_passed"] == 0
            and evaluation["accepted"] is False,
            {
                "smoke_only_row_count": evaluation["smoke_only_row_count"],
                "source_backed_rows_passed": evaluation["source_backed_rows_passed"],
                "accepted": evaluation["accepted"],
                "failed_reasons": evaluation["failed_reasons"],
            },
        ),
        requirement(
            "S5",
            "Fixture and preflight are hash-bound",
            bool(fixture["fixture_hash"]) and bool(evaluation["preflight_hash"]),
            {
                "fixture_hash": fixture["fixture_hash"],
                "preflight_hash": evaluation["preflight_hash"],
            },
        ),
        requirement(
            "S6",
            "R37 preserves zero-credit B1/B7 boundaries",
            fixture.get("o3_closed") is False
            and fixture.get("reroute_allowed") is False
            and fixture.get("b7_credit_delta") == 0,
            {
                "o3_closed": fixture.get("o3_closed"),
                "reroute_allowed": fixture.get("reroute_allowed"),
                "b7_credit_delta": fixture.get("b7_credit_delta"),
            },
        ),
        requirement(
            "S7",
            "R37 does not claim same-unitary or source-backed replay evidence",
            evaluation["source_backed_rows_passed"] == 0,
            {"source_backed_rows_passed": evaluation["source_backed_rows_passed"]},
        ),
        requirement(
            "S8",
            "R37 remains scoped to materialization plumbing and claims no C3-C7 progress",
            True,
            {
                "scope": "all-row materialized smoke artifact",
                "c3_c7_progress_claimed": False,
            },
        ),
    ]
    failed_requirements = [
        item["requirement_id"] for item in requirements if not item["passed"]
    ]
    summary = {
        "candidate_id": CANDIDATE_ID,
        "family_id": FAMILY_ID,
        "source_r36_preflight_hash": r36["summary"]["preflight_hash"],
        "source_r36_file_sha256": file_hash(args.r36_smoke),
        "source_r33_contract_hash": contract["contract_hash"],
        "fixture_hash": fixture["fixture_hash"],
        "fixture_file_sha256": file_hash(args.fixture_output),
        "preflight_hash": evaluation["preflight_hash"],
        "strict_tolerance": STRICT_TOLERANCE,
        "template_row_count": evaluation["row_count"],
        "surface_rows_passed": evaluation["surface_rows_passed"],
        "materialized_rows_passed": evaluation["materialized_rows_passed"],
        "materialized_rows_failed": evaluation["required_row_count"]
        - evaluation["materialized_rows_passed"],
        "missing_materialized_file_count": evaluation["missing_materialized_file_count"],
        "materialized_hash_mismatch_count": evaluation[
            "materialized_hash_mismatch_count"
        ],
        "smoke_only_row_count": evaluation["smoke_only_row_count"],
        "source_backed_rows_passed": evaluation["source_backed_rows_passed"],
        "all_rows_materialized_smoke_ready": True,
        "single_row_materialized_smoke_ready": True,
        "artifact_materialization_gate_ready": True,
        "binding_preflight_verifier_ready": True,
        "c2_provenance_binding_contract_ready": True,
        "c2_provenance_submission_accepted": False,
        "c2_strict_replay_rows_accepted": False,
        "o3_f4_artifact_accepted": False,
        "same_unitary_replay_certificate_complete": False,
        "same_access_denominator_comparison_complete": False,
        "leakage_free_optimizer_trace_complete": False,
        "machine_check_replay_complete": False,
        "o3_closed": False,
        "checked_negative_lemma_present": False,
        "nlc02_full_lemma_ready": False,
        "reroute_allowed": False,
        "accepted_route_count": 0,
        "accepted_occurrence_removal": 0,
        "accepted_proxy_t_reduction": 0,
        "b7_credit_delta": 0,
        "b7_space_time_volume_credit": 0,
        "resource_saving_claimed": False,
        "b7_ledger_improvement_claimed": False,
        "remaining_open_obligations": [
            "C2_replace_8_smoke_rows_with_source_backed_replay_outputs",
            "C2_same_unitary_witnesses_for_all_rows",
            "C2_file_hashes_match_declared_hashes_for_source_backed_files",
            "C3_same_unitary_replay_certificate",
            "C4_C5_same_access_denominator_comparison",
            "C6_leakage_free_optimizer_trace",
            "C7_machine_check_replay_bundle",
        ],
        "remaining_open_obligation_count": 7,
        "requirement_count": len(requirements),
        "requirements_passed": len(requirements) - len(failed_requirements),
        "requirements_failed": len(failed_requirements),
        "failed_requirement_ids": failed_requirements,
        "validation_error_count": len(failed_requirements),
    }
    payload = {
        "title": "B1/B7 Cone01 R37 O3-F4 C2 All-Row Materialized Smoke Gate",
        "version": VERSION,
        "last_updated": "2026-07-08",
        "benchmark_id": "B1",
        "linked_benchmark_id": "B7",
        "method": METHOD,
        "status": STATUS,
        "model_status": MODEL_STATUS,
        "source_target_id": TARGET_ID,
        "upstream_target_id": UPSTREAM_TARGET_ID,
        "o3_f4_c2_all_rows_materialized_smoke_packet": {
            "source_r36_smoke": str(args.r36_smoke),
            "source_r33_contract": str(args.r33_contract),
            "artifact_dir": str(args.artifact_dir),
            "fixture_output": str(args.fixture_output),
            "evaluation": evaluation,
        },
        "requirements": requirements,
        "summary": summary,
        "claim_boundary": {
            "what_is_supported": (
                "R37 materializes all 8 C2 smoke rows with hash-matched files, "
                "closing the pure file-existence blocker."
            ),
            "what_is_not_supported": (
                "R37 does not accept C2, does not provide source-backed replay "
                "outputs or same-unitary certificates, does not close O3, and "
                "does not permit reroute, B7 credit, STV credit, or resource-saving claims."
            ),
            "next_gate": (
                "Replace each smoke row with source-backed replay output and "
                "same-unitary witness files before rerunning C2/C3-C7."
            ),
            "resource_saving_claimed": False,
            "b7_ledger_improvement_claimed": False,
        },
        "validation_errors": failed_requirements,
        "runtime_seconds": round(time.time() - started, 6),
    }
    return payload, fixture


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    summary = payload["summary"]
    lines = [
        "# B1/B7 Cone01 R37 O3-F4 C2 All-Row Materialized Smoke Gate",
        "",
        f"- Target: `{payload['source_target_id']}`",
        f"- Upstream target: `{payload['upstream_target_id']}`",
        f"- Method: `{payload['method']}`",
        f"- Status: `{payload['status']}`",
        f"- Fixture hash: `{summary['fixture_hash']}`",
        f"- Preflight hash: `{summary['preflight_hash']}`",
        "",
        "## Result",
        "",
        (
            f"R37 passes {summary['requirements_passed']}/"
            f"{summary['requirement_count']} requirements by materializing all 8 "
            "smoke rows while rejecting the bundle because 0 rows are source-backed."
        ),
        "",
        "## Rejection Surface",
        "",
        f"- Surface rows passed: `{summary['surface_rows_passed']}`",
        f"- Materialized rows passed / failed: `{summary['materialized_rows_passed']}` / `{summary['materialized_rows_failed']}`",
        f"- Missing materialized files: `{summary['missing_materialized_file_count']}`",
        f"- Smoke-only rows: `{summary['smoke_only_row_count']}`",
        f"- Source-backed rows passed: `{summary['source_backed_rows_passed']}`",
        f"- C2 accepted: `{summary['c2_strict_replay_rows_accepted']}`",
        "",
        "## Requirement Results",
        "",
    ]
    for item in payload["requirements"]:
        mark = "PASS" if item["passed"] else "FAIL"
        lines.append(f"- `{item['requirement_id']}` {mark}: {item['label']}")
    lines.extend(
        [
            "",
            "## Claim Boundary",
            "",
            f"- Supported: {payload['claim_boundary']['what_is_supported']}",
            f"- Not supported: {payload['claim_boundary']['what_is_not_supported']}",
            f"- Next gate: {payload['claim_boundary']['next_gate']}",
            "",
            f"- validation_error_count: `{summary['validation_error_count']}`",
            "",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument(
        "--r36-smoke",
        type=Path,
        default=Path(
            "results/B1_B7_cone01_R36_o3_f4_c2_single_row_materialized_smoke_gate_v0.json"
        ),
    )
    parser.add_argument(
        "--r33-contract",
        type=Path,
        default=Path(
            "results/B1_B7_cone01_R33_o3_f4_c2_provenance_binding_contract_gate_v0.json"
        ),
    )
    parser.add_argument(
        "--artifact-dir",
        type=Path,
        default=Path(
            "results/B1_B7_cone01_o3_f4_numerical_refit_submissions/"
            "materialized_artifacts/r37_smoke"
        ),
    )
    parser.add_argument(
        "--fixture-output",
        type=Path,
        default=Path(
            "results/B1_B7_cone01_o3_f4_numerical_refit_submissions/"
            "B1-B7-cone01-O3-F4-C2-all-rows-materialized-smoke.fixture.json"
        ),
    )
    parser.add_argument(
        "--json-output",
        type=Path,
        default=Path(
            "results/B1_B7_cone01_R37_o3_f4_c2_all_rows_materialized_smoke_gate_v0.json"
        ),
    )
    parser.add_argument(
        "--markdown-output",
        type=Path,
        default=Path(
            "research/B1_B7_cone01_R37_o3_f4_c2_all_rows_materialized_smoke_gate.md"
        ),
    )
    parser.add_argument("--pretty", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    payload, _fixture = build_payload(args)
    write_json(args.json_output, payload, pretty=True)
    write_markdown(args.markdown_output, payload)
    if args.pretty:
        print(
            json.dumps(
                {
                    "status": payload["status"],
                    "requirements_passed": payload["summary"]["requirements_passed"],
                    "requirements_failed": payload["summary"]["requirements_failed"],
                    "fixture_hash": payload["summary"]["fixture_hash"],
                    "preflight_hash": payload["summary"]["preflight_hash"],
                    "materialized_rows_passed": payload["summary"][
                        "materialized_rows_passed"
                    ],
                    "missing_materialized_file_count": payload["summary"][
                        "missing_materialized_file_count"
                    ],
                    "smoke_only_row_count": payload["summary"]["smoke_only_row_count"],
                    "source_backed_rows_passed": payload["summary"][
                        "source_backed_rows_passed"
                    ],
                    "c2_strict_replay_rows_accepted": payload["summary"][
                        "c2_strict_replay_rows_accepted"
                    ],
                    "o3_closed": payload["summary"]["o3_closed"],
                    "reroute_allowed": payload["summary"]["reroute_allowed"],
                    "b7_credit_delta": payload["summary"]["b7_credit_delta"],
                    "json_output": str(args.json_output),
                    "fixture_output": str(args.fixture_output),
                    "markdown_output": str(args.markdown_output),
                },
                indent=2,
                sort_keys=True,
            )
        )


if __name__ == "__main__":
    main()
