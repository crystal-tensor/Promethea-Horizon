#!/usr/bin/env python3
"""T-B1-004ew/T-B7-014f: R47 O3-F4 C2 source-backed discriminator rerun gate."""

from __future__ import annotations

import argparse
import importlib.util
import json
import time
from pathlib import Path
from typing import Any


METHOD = "b1_b7_cone01_r47_o3_f4_c2_source_backed_discriminator_rerun_gate_v0"
STATUS = "cone01_r47_o3_f4_c2_source_backed_discriminator_rerun_rejects_flags_only"
MODEL_STATUS = "o3_f4_c2_evidence_complete_but_source_backed_flags_absent"
VERSION = "0.1"
TARGET_ID = "T-B1-004ew/T-B7-014f"
UPSTREAM_TARGET_ID = "T-B1-004ev/T-B7-014e"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_r38_module(root: Path) -> Any:
    module_path = root / "tools/b1_b7_cone01_r38_o3_f4_c2_source_backed_discriminator_gate.py"
    spec = importlib.util.spec_from_file_location("r38_source_backed_discriminator", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load R38 discriminator module from {module_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def req(requirement_id: str, label: str, passed: bool, evidence: dict[str, Any]) -> dict[str, Any]:
    return {
        "requirement_id": requirement_id,
        "label": label,
        "passed": bool(passed),
        "evidence": evidence,
    }


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def build_payload(args: argparse.Namespace) -> dict[str, Any]:
    started = time.time()
    r38 = load_r38_module(args.root)
    r46 = load_json(args.r46_result)
    r37 = load_json(args.r37_result)
    r33 = load_json(args.r33_contract)
    fixture = load_json(args.fixture_input)
    contract = r38.build_replacement_contract(r37, r33)
    write_json(args.contract_output, contract)
    evaluation = r38.evaluate_fixture(fixture, contract, args.root, args.fixture_input)
    row_results = evaluation["row_results"]
    flags_only_rows = [
        row["challenge_id"]
        for row in row_results
        if row["failed_reasons"] == ["source_backed_flags_not_satisfied"]
    ]
    prerequisite_clean_rows = [
        row["challenge_id"]
        for row in row_results
        if row["materialized_files_passed"]
        and row["binding_hash_matches"]
        and row["replay_error_within_tolerance"]
        and row["source_provenance_passed"]
        and row["witness_schema_passed"]
        and row["zero_credit_boundary_present"]
    ]
    requirements = [
        req(
            "S1",
            "R46 source bundle is validation-clean and all-row preflight complete",
            r46["summary"].get("validation_error_count") == 0
            and r46["summary"].get("witness_preflight_rows_passed") == 8
            and r46["summary"].get("unitary_distance_rows_passed") == 8
            and r46["summary"].get("source_backed_rows_passed") == 0,
            {
                "r46_validation_error_count": r46["summary"].get("validation_error_count"),
                "r46_witness_preflight_rows_passed": r46["summary"].get("witness_preflight_rows_passed"),
                "r46_unitary_distance_rows_passed": r46["summary"].get("unitary_distance_rows_passed"),
                "r46_source_backed_rows_passed": r46["summary"].get("source_backed_rows_passed"),
            },
        ),
        req(
            "S2",
            "R47 reruns the source-backed discriminator on the R46 all-row fixture",
            evaluation["row_count"] == 8 and evaluation["input_artifact"] == str(args.fixture_input),
            {
                "input_artifact": evaluation["input_artifact"],
                "fixture_hash": evaluation["fixture_hash"],
                "contract_hash": evaluation["contract_hash"],
                "discriminator_hash": evaluation["discriminator_hash"],
            },
        ),
        req(
            "S3",
            "All prerequisite evidence classes now pass before the final source-backed flags",
            evaluation["materialized_rows_passed"] == 8
            and evaluation["source_provenance_failures"] == 0
            and evaluation["witness_schema_failures"] == 0
            and evaluation["binding_mismatch_count"] == 0
            and len(prerequisite_clean_rows) == 8,
            {
                "materialized_rows_passed": evaluation["materialized_rows_passed"],
                "source_provenance_failures": evaluation["source_provenance_failures"],
                "witness_schema_failures": evaluation["witness_schema_failures"],
                "binding_mismatch_count": evaluation["binding_mismatch_count"],
                "prerequisite_clean_rows": prerequisite_clean_rows,
            },
        ),
        req(
            "S4",
            "Every row is rejected only at the source-backed replay and acceptance flag layer",
            evaluation["source_backed_rows_passed"] == 0
            and evaluation["source_backed_flag_failures"] == 8
            and evaluation["smoke_only_row_count"] == 8
            and len(flags_only_rows) == 8
            and evaluation["accepted"] is False,
            {
                "source_backed_rows_passed": evaluation["source_backed_rows_passed"],
                "source_backed_flag_failures": evaluation["source_backed_flag_failures"],
                "smoke_only_row_count": evaluation["smoke_only_row_count"],
                "flags_only_rows": flags_only_rows,
                "accepted": evaluation["accepted"],
            },
        ),
        req(
            "S5",
            "R47 preserves C2/O3/reroute/B7 zero-credit boundaries",
            fixture.get("o3_closed") is False
            and fixture.get("reroute_allowed") is False
            and fixture.get("b7_credit_delta") == 0,
            {
                "o3_closed": fixture.get("o3_closed"),
                "reroute_allowed": fixture.get("reroute_allowed"),
                "b7_credit_delta": fixture.get("b7_credit_delta"),
            },
        ),
        req(
            "S6",
            "R47 declares the exact evidence needed before any smoke flag can flip",
            True,
            {
                "required_before_flag_flip": [
                    "independent_source_dataset_or_trace_with_external_lineage",
                    "replay_environment_not_derived_from_smoke_fixture",
                    "same_unitary_certificate_claim_signed_by_verifier",
                    "discriminator_pass_for_all_8_rows",
                    "zero_credit_claim_boundary_retained_after_acceptance",
                ]
            },
        ),
        req(
            "S7",
            "R47 claims no C3-C7, reroute, occurrence-removal, or B7 ledger progress",
            True,
            {
                "c3_c7_progress_claimed": False,
                "reroute_claimed": False,
                "occurrence_removal_claimed": False,
                "b7_ledger_credit_claimed": False,
            },
        ),
        req(
            "S8",
            "R47 output is hash-bound",
            bool(evaluation["discriminator_hash"]) and bool(contract["contract_hash"]),
            {
                "contract_hash": contract["contract_hash"],
                "contract_file_sha256": r38.file_hash(args.contract_output),
                "discriminator_hash": evaluation["discriminator_hash"],
            },
        ),
    ]
    failed = [item["requirement_id"] for item in requirements if not item["passed"]]
    summary = {
        "source_r46_evaluation_hash": r46["summary"]["evaluation_hash"],
        "source_r46_fixture_hash": r46["summary"]["remaining_witness_preflight_fixture_hash"],
        "source_r46_file_sha256": r38.file_hash(args.r46_result),
        "fixture_input": str(args.fixture_input),
        "fixture_input_sha256": r38.file_hash(args.fixture_input),
        "fixture_hash": evaluation["fixture_hash"],
        "replacement_contract_hash": contract["contract_hash"],
        "replacement_contract_file_sha256": r38.file_hash(args.contract_output),
        "discriminator_hash": evaluation["discriminator_hash"],
        "template_row_count": evaluation["row_count"],
        "materialized_rows_passed": evaluation["materialized_rows_passed"],
        "source_provenance_failures": evaluation["source_provenance_failures"],
        "witness_schema_failures": evaluation["witness_schema_failures"],
        "binding_mismatch_count": evaluation["binding_mismatch_count"],
        "prerequisite_clean_rows_passed": len(prerequisite_clean_rows),
        "source_backed_rows_passed": evaluation["source_backed_rows_passed"],
        "source_backed_flag_failures": evaluation["source_backed_flag_failures"],
        "smoke_only_row_count": evaluation["smoke_only_row_count"],
        "flags_only_rejection_rows": len(flags_only_rows),
        "c2_strict_replay_rows_accepted": False,
        "o3_closed": False,
        "reroute_allowed": False,
        "accepted_route_count": 0,
        "accepted_occurrence_removal": 0,
        "accepted_proxy_t_reduction": 0,
        "b7_credit_delta": 0,
        "b7_space_time_volume_credit": 0,
        "resource_saving_claimed": False,
        "b7_ledger_improvement_claimed": False,
        "remaining_open_obligations": [
            "replace_smoke_only_flags_with_external_source_backed_replay_evidence",
            "produce_same_unitary_certificate_claims_from_a_real_verifier",
            "rerun_discriminator_until_all_8_rows_pass",
            "C3_same_unitary_replay_certificate",
            "C4_C5_same_access_denominator_comparison",
            "C6_leakage_free_optimizer_trace",
            "C7_machine_check_replay_bundle",
        ],
        "remaining_open_obligation_count": 7,
        "requirement_count": len(requirements),
        "requirements_passed": len(requirements) - len(failed),
        "requirements_failed": len(failed),
        "failed_requirement_ids": failed,
        "validation_error_count": len(failed),
    }
    return {
        "title": "B1/B7 Cone01 R47 O3-F4 C2 Source-Backed Discriminator Rerun Gate",
        "version": VERSION,
        "last_updated": "2026-07-08",
        "benchmark_id": "B1",
        "linked_benchmark_id": "B7",
        "method": METHOD,
        "status": STATUS,
        "model_status": MODEL_STATUS,
        "source_target_id": TARGET_ID,
        "upstream_target_id": UPSTREAM_TARGET_ID,
        "o3_f4_c2_source_backed_discriminator_rerun_packet": {
            "source_r46_result": str(args.r46_result),
            "source_r37_result": str(args.r37_result),
            "source_r33_contract": str(args.r33_contract),
            "fixture_input": str(args.fixture_input),
            "replacement_contract_output": str(args.contract_output),
            "replacement_contract": contract,
            "evaluation": evaluation,
            "flags_only_rows": flags_only_rows,
            "prerequisite_clean_rows": prerequisite_clean_rows,
        },
        "requirements": requirements,
        "summary": summary,
        "claim_boundary": {
            "what_is_supported": (
                "R47 reruns the source-backed discriminator on the R46 all-row fixture "
                "and shows that materialization, provenance, witness schema, replay "
                "distance, binding, and zero-credit boundary checks are now clean for "
                "all 8 rows."
            ),
            "what_is_not_supported": (
                "R47 still rejects every row because source-backed replay and same-"
                "unitary acceptance flags remain false while smoke-only flags remain "
                "true. It does not accept C2, close O3, allow reroute, or grant B7/STV "
                "credit."
            ),
            "next_gate": (
                "Replace smoke-only flags with externally source-backed replay evidence "
                "and real verifier-backed same-unitary certificates for all 8 rows, then "
                "rerun this discriminator before C3-C7."
            ),
            "resource_saving_claimed": False,
            "b7_ledger_improvement_claimed": False,
        },
        "validation_errors": failed,
        "runtime_seconds": round(time.time() - started, 6),
    }


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    s = payload["summary"]
    lines = [
        "# B1/B7 Cone01 R47 O3-F4 C2 Source-Backed Discriminator Rerun Gate",
        "",
        f"- Target: `{payload['source_target_id']}`",
        f"- Upstream target: `{payload['upstream_target_id']}`",
        f"- Method: `{payload['method']}`",
        f"- Status: `{payload['status']}`",
        f"- Fixture hash: `{s['fixture_hash']}`",
        f"- Discriminator hash: `{s['discriminator_hash']}`",
        "",
        "## Result",
        "",
        (
            f"R47 passes {s['requirements_passed']}/{s['requirement_count']} "
            "requirements by rerunning the source-backed discriminator after R46. "
            "All 8 rows now clear the prerequisite evidence layers, but all 8 remain "
            "rejected at the final source-backed flag layer."
        ),
        "",
        "## Rejection Surface",
        "",
        f"- Prerequisite-clean rows: `{s['prerequisite_clean_rows_passed']}`",
        f"- Source-provenance failures: `{s['source_provenance_failures']}`",
        f"- Witness-schema failures: `{s['witness_schema_failures']}`",
        f"- Binding mismatch count: `{s['binding_mismatch_count']}`",
        f"- Source-backed rows passed: `{s['source_backed_rows_passed']}`",
        f"- Source-backed flag failures: `{s['source_backed_flag_failures']}`",
        f"- Flags-only rejection rows: `{s['flags_only_rejection_rows']}`",
        f"- C2 accepted: `{s['c2_strict_replay_rows_accepted']}`",
        "",
        "## Requirement Results",
        "",
    ]
    for item in payload["requirements"]:
        lines.append(f"- `{item['requirement_id']}` {'PASS' if item['passed'] else 'FAIL'}: {item['label']}")
    lines.extend(
        [
            "",
            "## Claim Boundary",
            "",
            f"- Supported: {payload['claim_boundary']['what_is_supported']}",
            f"- Not supported: {payload['claim_boundary']['what_is_not_supported']}",
            f"- Next gate: {payload['claim_boundary']['next_gate']}",
            "",
            f"- validation_error_count: `{s['validation_error_count']}`",
            "",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--r46-result", type=Path, default=Path("results/B1_B7_cone01_R46_o3_f4_c2_remaining_witness_preflight_gate_v0.json"))
    parser.add_argument("--r37-result", type=Path, default=Path("results/B1_B7_cone01_R37_o3_f4_c2_all_rows_materialized_smoke_gate_v0.json"))
    parser.add_argument("--r33-contract", type=Path, default=Path("results/B1_B7_cone01_R33_o3_f4_c2_provenance_binding_contract_gate_v0.json"))
    parser.add_argument("--fixture-input", type=Path, default=Path("results/B1_B7_cone01_o3_f4_numerical_refit_submissions/B1-B7-cone01-O3-F4-C2-remaining-witness-preflight.fixture.json"))
    parser.add_argument("--contract-output", type=Path, default=Path("results/B1_B7_cone01_o3_f4_numerical_refit_submissions/B1-B7-cone01-O3-F4-C2-r47-source-backed-discriminator-rerun.contract.json"))
    parser.add_argument("--json-output", type=Path, default=Path("results/B1_B7_cone01_R47_o3_f4_c2_source_backed_discriminator_rerun_gate_v0.json"))
    parser.add_argument("--markdown-output", type=Path, default=Path("research/B1_B7_cone01_R47_o3_f4_c2_source_backed_discriminator_rerun_gate.md"))
    parser.add_argument("--pretty", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    payload = build_payload(args)
    write_json(args.json_output, payload)
    write_markdown(args.markdown_output, payload)
    if args.pretty:
        s = payload["summary"]
        print(json.dumps({
            "status": payload["status"],
            "fixture_hash": s["fixture_hash"],
            "discriminator_hash": s["discriminator_hash"],
            "requirements_passed": s["requirements_passed"],
            "requirements_failed": s["requirements_failed"],
            "prerequisite_clean_rows_passed": s["prerequisite_clean_rows_passed"],
            "source_backed_rows_passed": s["source_backed_rows_passed"],
            "source_backed_flag_failures": s["source_backed_flag_failures"],
            "flags_only_rejection_rows": s["flags_only_rejection_rows"],
            "json_output": str(args.json_output),
        }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
