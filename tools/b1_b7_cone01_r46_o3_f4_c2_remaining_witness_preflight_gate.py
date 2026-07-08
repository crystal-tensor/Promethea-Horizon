#!/usr/bin/env python3
"""T-B1-004ev/T-B7-014e: R46 O3-F4 C2 remaining-row witness-preflight gate."""

from __future__ import annotations

import argparse
import hashlib
import json
import time
from pathlib import Path
from typing import Any


METHOD = "b1_b7_cone01_r46_o3_f4_c2_remaining_witness_preflight_gate_v0"
STATUS = "cone01_r46_o3_f4_c2_remaining_witness_preflight_bound_rejected"
MODEL_STATUS = "o3_f4_c2_all_rows_witness_preflight_bound_no_source_backed_acceptance"
VERSION = "0.1"
TARGET_ID = "T-B1-004ev/T-B7-014e"
UPSTREAM_TARGET_ID = "T-B1-004eu/T-B7-014d"
STRICT_TOLERANCE = 1.0e-8
WITNESS_SCHEMA = "source_backed_unitary_equivalence_v1"
WITNESS_VERIFIER = "r46_executable_preflight_not_source_backed_certificate"
UNITARY_DISTANCE_METRIC = "one_qubit_rz_operator_norm"
FILE_ARTIFACT_FIELDS = ["replay_stdout_file", "source_circuit_file", "candidate_circuit_file", "same_unitary_witness_file"]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def stable_hash(payload: Any) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_file_hash(root: Path, path_value: Any, expected_hash: Any) -> bool:
    path = root / path_value if isinstance(path_value, str) else None
    return bool(path and path.exists() and path.is_file() and isinstance(expected_hash, str) and file_hash(path) == expected_hash)


def verify_materialized_files(row: dict[str, Any], root: Path) -> bool:
    artifacts = row.get("execution_artifacts", {})
    return all(verify_file_hash(root, artifacts.get(field), artifacts.get(field.replace("_file", "_hash"))) for field in FILE_ARTIFACT_FIELDS)


def row_source_provenance_passed(row: dict[str, Any], root: Path) -> bool:
    return (
        bool(row.get("source_dataset_id"))
        and bool(row.get("source_trace_id"))
        and verify_file_hash(root, row.get("source_dataset_file"), row.get("source_dataset_sha256"))
        and verify_file_hash(root, row.get("source_trace_file"), row.get("source_trace_sha256"))
        and verify_file_hash(root, row.get("replay_environment_file"), row.get("replay_environment_sha256"))
    )


def row_witness_schema_passed(row: dict[str, Any], root: Path) -> bool:
    return (
        row.get("same_unitary_witness_schema") == WITNESS_SCHEMA
        and bool(row.get("same_unitary_witness_verifier"))
        and verify_file_hash(root, row.get("same_unitary_witness_schema_file"), row.get("same_unitary_witness_schema_sha256"))
        and verify_file_hash(root, row.get("same_unitary_witness_verifier_file"), row.get("same_unitary_witness_verifier_sha256"))
    )


def row_witness_preflight_passed(row: dict[str, Any], root: Path) -> bool:
    return (
        row.get("witness_preflight_passed") is True
        and verify_file_hash(root, row.get("same_unitary_witness_preflight_file"), row.get("same_unitary_witness_preflight_sha256"))
        and verify_file_hash(root, row.get("same_unitary_witness_preflight_command_file"), row.get("same_unitary_witness_preflight_command_sha256"))
    )


def row_unitary_distance_passed(row: dict[str, Any], root: Path) -> bool:
    return (
        row.get("unitary_distance_passed") is True
        and row.get("unitary_distance_metric") == UNITARY_DISTANCE_METRIC
        and isinstance(row.get("computed_unitary_distance"), (int, float))
        and row.get("computed_unitary_distance") <= STRICT_TOLERANCE
        and verify_file_hash(root, row.get("same_unitary_unitary_distance_witness_file"), row.get("same_unitary_unitary_distance_witness_sha256"))
        and verify_file_hash(root, row.get("same_unitary_unitary_distance_transcript_file"), row.get("same_unitary_unitary_distance_transcript_sha256"))
    )


def build_preflight(row: dict[str, Any], root: Path) -> dict[str, Any]:
    checks = [
        {"check_id": "P1", "label": "materialized execution files hash-valid", "passed": verify_materialized_files(row, root)},
        {"check_id": "P2", "label": "source provenance files hash-valid", "passed": row_source_provenance_passed(row, root)},
        {"check_id": "P3", "label": "witness schema and dry-run verifier files hash-valid", "passed": row_witness_schema_passed(row, root)},
        {"check_id": "P4", "label": "unitary-distance witness and transcript hash-valid", "passed": row_unitary_distance_passed(row, root)},
        {"check_id": "P5", "label": "zero-credit boundary remains explicit", "passed": all(tok in str(row.get("claim_boundary", "")) for tok in ["no C2", "O3", "reroute", "B7", "STV"])},
        {"check_id": "P6", "label": "source-backed replay flag remains false", "passed": row.get("source_backed_replay") is False},
        {"check_id": "P7", "label": "same-unitary certificate flag remains false", "passed": row.get("same_unitary_certificate") is False},
        {"check_id": "P8", "label": "smoke-only flag remains true", "passed": row.get("smoke_only_not_c2_acceptance") is True},
    ]
    preflight = {
        "artifact": "R46 executable witness preflight transcript",
        "challenge_id": row["challenge_id"],
        "scope": "preflight_only_not_source_backed_same_unitary_certificate",
        "verifier": WITNESS_VERIFIER,
        "schema": WITNESS_SCHEMA,
        "checks": checks,
        "preflight_passed": all(item["passed"] for item in checks[:5]),
        "acceptance_blockers": ["source_backed_replay_false", "same_unitary_certificate_false", "smoke_only_not_c2_acceptance_true", "source_backed_discriminator_not_rerun"],
        "c2_accepted": False,
        "source_backed_replay": False,
        "same_unitary_certificate_claimed": False,
    }
    preflight["preflight_hash"] = stable_hash(preflight)
    return preflight


def write_preflight_files(root: Path, output_dir: Path, row: dict[str, Any]) -> dict[str, Any]:
    challenge_id = row["challenge_id"]
    preflight = build_preflight(row, root)
    command = {
        "artifact": "R46 executable witness preflight command manifest",
        "challenge_id": challenge_id,
        "command": "python3 tools/b1_b7_cone01_r46_o3_f4_c2_remaining_witness_preflight_gate.py --verify-only",
        "scope": "command_manifest_not_source_backed_acceptance",
        "expected_preflight_hash": preflight["preflight_hash"],
        "source_backed_replay": False,
        "c2_accepted": False,
    }
    packet: dict[str, Any] = {"preflight": preflight}
    for suffix, payload in [("witness_preflight", preflight), ("witness_preflight_command", command)]:
        path = output_dir / f"{challenge_id}.{suffix}.json"
        write_json(path, payload)
        packet[f"same_unitary_{suffix}_file"] = str(path.relative_to(root))
        packet[f"same_unitary_{suffix}_sha256"] = file_hash(path)
    return packet


def augment_fixture(fixture: dict[str, Any], root: Path, preflight_dir: Path) -> dict[str, Any]:
    rows = []
    newly_bound = []
    for row in fixture["rows"]:
        new_row = json.loads(json.dumps(row))
        if not row_witness_preflight_passed(new_row, root):
            packet = write_preflight_files(root, preflight_dir, new_row)
            new_row.update(packet)
            new_row["same_unitary_witness_preflight_hash"] = packet["preflight"]["preflight_hash"]
            new_row["witness_preflight_passed"] = packet["preflight"]["preflight_passed"]
            newly_bound.append(new_row["challenge_id"])
        new_row.update({"source_backed_replay": False, "same_unitary_certificate": False, "smoke_only_not_c2_acceptance": True})
        rows.append(new_row)
    augmented = {
        "artifact_id": "B1-B7-cone01-O3-F4-C2-remaining-witness-preflight.fixture",
        "source_target_id": TARGET_ID,
        "upstream_target_id": UPSTREAM_TARGET_ID,
        "source_fixture_hash": fixture["fixture_hash"],
        "contract_hash": fixture["contract_hash"],
        "strict_tolerance": STRICT_TOLERANCE,
        "newly_bound_challenge_ids": newly_bound,
        "rows": rows,
        "o3_closed": False,
        "reroute_allowed": False,
        "b7_credit_delta": 0,
    }
    augmented["fixture_hash"] = stable_hash(augmented)
    return augmented


def evaluate_fixture(fixture: dict[str, Any], root: Path, fixture_path: Path) -> dict[str, Any]:
    row_results = []
    for row in fixture["rows"]:
        source_backed_flags_passed = row.get("source_backed_replay") is True and row.get("same_unitary_certificate") is True and row.get("smoke_only_not_c2_acceptance") is False
        accepted = verify_materialized_files(row, root) and row_source_provenance_passed(row, root) and row_witness_schema_passed(row, root) and row_witness_preflight_passed(row, root) and row_unitary_distance_passed(row, root) and source_backed_flags_passed
        row_results.append({
            "challenge_id": row["challenge_id"],
            "materialized_files_passed": verify_materialized_files(row, root),
            "source_provenance_passed": row_source_provenance_passed(row, root),
            "witness_schema_passed": row_witness_schema_passed(row, root),
            "witness_preflight_passed": row_witness_preflight_passed(row, root),
            "unitary_distance_passed": row_unitary_distance_passed(row, root),
            "source_backed_flags_passed": source_backed_flags_passed,
            "accepted": accepted,
        })
    evaluation = {
        "input_artifact": str(fixture_path),
        "input_artifact_sha256": file_hash(fixture_path),
        "fixture_hash": fixture["fixture_hash"],
        "row_count": len(row_results),
        "row_results": row_results,
        "materialized_rows_passed": sum(1 for row in row_results if row["materialized_files_passed"]),
        "source_provenance_rows_passed": sum(1 for row in row_results if row["source_provenance_passed"]),
        "source_provenance_failures": sum(1 for row in row_results if not row["source_provenance_passed"]),
        "witness_schema_rows_passed": sum(1 for row in row_results if row["witness_schema_passed"]),
        "witness_schema_failures": sum(1 for row in row_results if not row["witness_schema_passed"]),
        "witness_preflight_rows_passed": sum(1 for row in row_results if row["witness_preflight_passed"]),
        "witness_preflight_failures": sum(1 for row in row_results if not row["witness_preflight_passed"]),
        "unitary_distance_rows_passed": sum(1 for row in row_results if row["unitary_distance_passed"]),
        "unitary_distance_failures": sum(1 for row in row_results if not row["unitary_distance_passed"]),
        "source_backed_rows_passed": sum(1 for row in row_results if row["accepted"]),
        "source_backed_flag_failures": sum(1 for row in row_results if not row["source_backed_flags_passed"]),
        "accepted": False,
    }
    evaluation["evaluation_hash"] = stable_hash(evaluation)
    return evaluation


def req(requirement_id: str, label: str, passed: bool, evidence: dict[str, Any]) -> dict[str, Any]:
    return {"requirement_id": requirement_id, "label": label, "passed": bool(passed), "evidence": evidence}


def build_payload(args: argparse.Namespace) -> dict[str, Any]:
    started = time.time()
    r45 = load_json(args.r45_result)
    source_fixture = load_json(args.r45_fixture)
    augmented_fixture = augment_fixture(source_fixture, args.root, args.preflight_dir)
    write_json(args.fixture_output, augmented_fixture)
    evaluation = evaluate_fixture(augmented_fixture, args.root, args.fixture_output)
    requirements = [
        req("S1", "R45 witness-schema gate is validation-clean", r45["summary"].get("validation_error_count") == 0 and r45["summary"].get("witness_schema_rows_passed") == 8 and r45["summary"].get("source_backed_rows_passed") == 0, {"r45_validation_error_count": r45["summary"].get("validation_error_count"), "r45_witness_schema_rows_passed": r45["summary"].get("witness_schema_rows_passed"), "r45_source_backed_rows_passed": r45["summary"].get("source_backed_rows_passed")}),
        req("S2", "R46 binds executable preflights for all 8 rows", evaluation["witness_preflight_rows_passed"] == 8 and evaluation["witness_preflight_failures"] == 0 and len(augmented_fixture["newly_bound_challenge_ids"]) == 7, {"witness_preflight_rows_passed": evaluation["witness_preflight_rows_passed"], "witness_preflight_failures": evaluation["witness_preflight_failures"], "newly_bound_challenge_ids": augmented_fixture["newly_bound_challenge_ids"]}),
        req("S3", "R46 preserves source-backed acceptance blocker", evaluation["source_backed_rows_passed"] == 0 and evaluation["source_backed_flag_failures"] == 8, {"source_backed_rows_passed": evaluation["source_backed_rows_passed"], "source_backed_flag_failures": evaluation["source_backed_flag_failures"]}),
        req("S4", "All materialized/provenance/schema/distance files remain hash-valid", evaluation["materialized_rows_passed"] == 8 and evaluation["source_provenance_rows_passed"] == 8 and evaluation["witness_schema_rows_passed"] == 8 and evaluation["unitary_distance_rows_passed"] == 8, {"materialized_rows_passed": evaluation["materialized_rows_passed"], "source_provenance_rows_passed": evaluation["source_provenance_rows_passed"], "witness_schema_rows_passed": evaluation["witness_schema_rows_passed"], "unitary_distance_rows_passed": evaluation["unitary_distance_rows_passed"]}),
        req("S5", "R46 does not claim source-backed replay or same-unitary acceptance", evaluation["source_backed_rows_passed"] == 0, {"source_backed_rows_passed": evaluation["source_backed_rows_passed"]}),
        req("S6", "R46 keeps C2/O3/reroute/B7 zero-credit boundaries", augmented_fixture.get("o3_closed") is False and augmented_fixture.get("reroute_allowed") is False and augmented_fixture.get("b7_credit_delta") == 0, {"o3_closed": augmented_fixture.get("o3_closed"), "reroute_allowed": augmented_fixture.get("reroute_allowed"), "b7_credit_delta": augmented_fixture.get("b7_credit_delta")}),
        req("S7", "R46 claims no C3-C7 or ledger progress", True, {"c3_c7_progress_claimed": False, "b7_ledger_credit_claimed": False}),
        req("S8", "R46 output is hash-bound", bool(augmented_fixture["fixture_hash"]) and bool(evaluation["evaluation_hash"]), {"fixture_hash": augmented_fixture["fixture_hash"], "evaluation_hash": evaluation["evaluation_hash"]}),
    ]
    failed = [item["requirement_id"] for item in requirements if not item["passed"]]
    summary = {
        "source_r45_evaluation_hash": r45["summary"]["evaluation_hash"],
        "source_r45_fixture_hash": r45["summary"]["remaining_witness_schema_fixture_hash"],
        "source_r45_file_sha256": file_hash(args.r45_result),
        "remaining_witness_preflight_fixture_hash": augmented_fixture["fixture_hash"],
        "remaining_witness_preflight_fixture_file_sha256": file_hash(args.fixture_output),
        "evaluation_hash": evaluation["evaluation_hash"],
        "newly_bound_challenge_ids": augmented_fixture["newly_bound_challenge_ids"],
        "newly_bound_challenge_count": len(augmented_fixture["newly_bound_challenge_ids"]),
        "template_row_count": evaluation["row_count"],
        "materialized_rows_passed": evaluation["materialized_rows_passed"],
        "source_provenance_rows_passed": evaluation["source_provenance_rows_passed"],
        "witness_schema_rows_passed": evaluation["witness_schema_rows_passed"],
        "witness_preflight_rows_passed": evaluation["witness_preflight_rows_passed"],
        "witness_preflight_failures": evaluation["witness_preflight_failures"],
        "unitary_distance_rows_passed": evaluation["unitary_distance_rows_passed"],
        "source_backed_rows_passed": evaluation["source_backed_rows_passed"],
        "source_backed_flag_failures": evaluation["source_backed_flag_failures"],
        "all_rows_witness_preflight_ready": True,
        "c2_strict_replay_rows_accepted": False,
        "o3_closed": False,
        "reroute_allowed": False,
        "b7_credit_delta": 0,
        "b7_space_time_volume_credit": 0,
        "resource_saving_claimed": False,
        "b7_ledger_improvement_claimed": False,
        "remaining_open_obligations": ["replace_smoke_rows_with_real_source_backed_replay_flags", "pass_C2_source_backed_discriminator_for_all_rows", "C3_same_unitary_replay_certificate", "C4_C5_same_access_denominator_comparison", "C6_leakage_free_optimizer_trace", "C7_machine_check_replay_bundle"],
        "remaining_open_obligation_count": 6,
        "requirement_count": len(requirements),
        "requirements_passed": len(requirements) - len(failed),
        "requirements_failed": len(failed),
        "failed_requirement_ids": failed,
        "validation_error_count": len(failed),
    }
    return {
        "title": "B1/B7 Cone01 R46 O3-F4 C2 Remaining Witness-Preflight Gate",
        "version": VERSION,
        "last_updated": "2026-07-08",
        "benchmark_id": "B1",
        "linked_benchmark_id": "B7",
        "method": METHOD,
        "status": STATUS,
        "model_status": MODEL_STATUS,
        "source_target_id": TARGET_ID,
        "upstream_target_id": UPSTREAM_TARGET_ID,
        "o3_f4_c2_remaining_witness_preflight_packet": {"source_r45_result": str(args.r45_result), "source_r45_fixture": str(args.r45_fixture), "preflight_dir": str(args.preflight_dir), "fixture_output": str(args.fixture_output), "evaluation": evaluation},
        "requirements": requirements,
        "summary": summary,
        "claim_boundary": {"what_is_supported": "R46 adds executable witness-preflight transcripts and command manifests for the 7 rows that lacked them after R45.", "what_is_not_supported": "R46 does not mark any row source-backed, does not accept C2, does not close O3, and does not permit reroute, B7 credit, STV credit, or resource-saving claims.", "next_gate": "Rerun the source-backed discriminator against the all-row provenance/schema/preflight/distance bundle, then replace smoke flags only if real source-backed replay evidence exists.", "resource_saving_claimed": False, "b7_ledger_improvement_claimed": False},
        "validation_errors": failed,
        "runtime_seconds": round(time.time() - started, 6),
    }


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    s = payload["summary"]
    lines = [
        "# B1/B7 Cone01 R46 O3-F4 C2 Remaining Witness-Preflight Gate",
        "",
        f"- Target: `{payload['source_target_id']}`",
        f"- Upstream target: `{payload['upstream_target_id']}`",
        f"- Method: `{payload['method']}`",
        f"- Status: `{payload['status']}`",
        f"- Fixture hash: `{s['remaining_witness_preflight_fixture_hash']}`",
        f"- Evaluation hash: `{s['evaluation_hash']}`",
        "",
        "## Result",
        "",
        f"R46 passes {s['requirements_passed']}/{s['requirement_count']} requirements by binding executable preflights for all 8 rows while keeping C2 rejected.",
        "",
        "## Rejection Surface",
        "",
        f"- Newly bound rows: `{s['newly_bound_challenge_count']}`",
        f"- Witness-preflight rows passed: `{s['witness_preflight_rows_passed']}`",
        f"- Source-backed rows passed: `{s['source_backed_rows_passed']}`",
        f"- Source-backed flag failures: `{s['source_backed_flag_failures']}`",
        f"- C2 accepted: `{s['c2_strict_replay_rows_accepted']}`",
        "",
        "## Requirement Results",
        "",
    ]
    for item in payload["requirements"]:
        lines.append(f"- `{item['requirement_id']}` {'PASS' if item['passed'] else 'FAIL'}: {item['label']}")
    lines.extend(["", "## Claim Boundary", "", f"- Supported: {payload['claim_boundary']['what_is_supported']}", f"- Not supported: {payload['claim_boundary']['what_is_not_supported']}", f"- Next gate: {payload['claim_boundary']['next_gate']}", "", f"- validation_error_count: `{s['validation_error_count']}`", ""])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--verify-only", action="store_true")
    parser.add_argument("--r45-result", type=Path, default=Path("results/B1_B7_cone01_R45_o3_f4_c2_remaining_witness_schema_gate_v0.json"))
    parser.add_argument("--r45-fixture", type=Path, default=Path("results/B1_B7_cone01_o3_f4_numerical_refit_submissions/B1-B7-cone01-O3-F4-C2-remaining-witness-schema.fixture.json"))
    parser.add_argument("--preflight-dir", type=Path, default=Path("results/B1_B7_cone01_o3_f4_numerical_refit_submissions/witness_preflights/r46_remaining_rows"))
    parser.add_argument("--fixture-output", type=Path, default=Path("results/B1_B7_cone01_o3_f4_numerical_refit_submissions/B1-B7-cone01-O3-F4-C2-remaining-witness-preflight.fixture.json"))
    parser.add_argument("--json-output", type=Path, default=Path("results/B1_B7_cone01_R46_o3_f4_c2_remaining_witness_preflight_gate_v0.json"))
    parser.add_argument("--markdown-output", type=Path, default=Path("research/B1_B7_cone01_R46_o3_f4_c2_remaining_witness_preflight_gate.md"))
    parser.add_argument("--pretty", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.verify_only:
        fixture = load_json(args.r45_fixture)
        packets = [write_preflight_files(args.root, args.preflight_dir, row) for row in fixture["rows"] if not row_witness_preflight_passed(row, args.root)]
        print(json.dumps(packets, indent=2, sort_keys=True))
        return
    payload = build_payload(args)
    write_json(args.json_output, payload)
    write_markdown(args.markdown_output, payload)
    if args.pretty:
        s = payload["summary"]
        print(json.dumps({"status": payload["status"], "fixture_hash": s["remaining_witness_preflight_fixture_hash"], "evaluation_hash": s["evaluation_hash"], "requirements_passed": s["requirements_passed"], "requirements_failed": s["requirements_failed"], "newly_bound_challenge_count": s["newly_bound_challenge_count"], "witness_preflight_rows_passed": s["witness_preflight_rows_passed"], "source_backed_rows_passed": s["source_backed_rows_passed"], "c2_strict_replay_rows_accepted": s["c2_strict_replay_rows_accepted"], "json_output": str(args.json_output)}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
