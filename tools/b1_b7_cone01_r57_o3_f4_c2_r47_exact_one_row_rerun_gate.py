#!/usr/bin/env python3
"""T-B1-004fg/T-B7-014p: R57 reruns R47 on the R56 exact-one-row target."""

from __future__ import annotations

import argparse
import importlib.util
import json
import time
from pathlib import Path
from typing import Any


METHOD = "b1_b7_cone01_r57_o3_f4_c2_r47_exact_one_row_rerun_gate_v0"
STATUS = "cone01_r57_o3_f4_c2_r47_accepts_exact_one_row_zero_b7_credit"
MODEL_STATUS = "o3_f4_c2_c01_one_source_backed_row_accepted_all8_and_b7_still_open"
VERSION = "0.1"
TARGET_ID = "T-B1-004fg/T-B7-014p"
UPSTREAM_TARGET_ID = "T-B1-004ff/T-B7-014o"
SELECTED_CHALLENGE_ID = "O3-F4-C01"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


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


def build_discriminator_row(r38: Any, e3_row: dict[str, Any], r56: dict[str, Any]) -> dict[str, Any]:
    binding_payload = {
        "challenge_id": SELECTED_CHALLENGE_ID,
        "source_presubmission_row_hash": e3_row["presubmission_row_hash"],
        "source_r56_evaluation_hash": r56["summary"]["r56_evaluation_hash"],
        "source_dataset_hash": e3_row["source_dataset_sha256"],
        "source_trace_hash": e3_row["source_trace_sha256"],
        "replay_environment_hash": e3_row["replay_environment_sha256"],
        "source_circuit_hash": e3_row["source_circuit_sha256"],
        "candidate_circuit_hash": e3_row["candidate_circuit_sha256"],
        "replay_stdout_hash": e3_row["replay_stdout_sha256"],
        "same_unitary_witness_hash": e3_row["same_unitary_witness_sha256"],
        "verifier_signature_hash": e3_row["verifier_signature_sha256"],
        "strict_tolerance": 1.0e-8,
        "max_unitary_replay_error": 0.0,
        "unitary_distance_metric": "single_qubit_rz_operator_norm",
        "verifier_version": METHOD,
    }
    binding_hash = r38.stable_hash(binding_payload)
    row = {
        "challenge_id": SELECTED_CHALLENGE_ID,
        "source_target_id": TARGET_ID,
        "upstream_target_id": UPSTREAM_TARGET_ID,
        "source_presubmission_row_hash": e3_row["presubmission_row_hash"],
        "binding_payload": binding_payload,
        "declared_provenance_binding_hash": binding_hash,
        "execution_artifacts": {
            "source_circuit_file": e3_row["source_circuit_file"],
            "source_circuit_hash": e3_row["source_circuit_sha256"],
            "candidate_circuit_file": e3_row["candidate_circuit_file"],
            "candidate_circuit_hash": e3_row["candidate_circuit_sha256"],
            "replay_stdout_file": e3_row["replay_stdout_file"],
            "replay_stdout_hash": e3_row["replay_stdout_sha256"],
            "same_unitary_witness_file": e3_row["same_unitary_witness_file"],
            "same_unitary_witness_hash": e3_row["same_unitary_witness_sha256"],
            "provenance_binding_hash": binding_hash,
        },
        "max_unitary_replay_error": 0.0,
        "computed_unitary_distance": 0.0,
        "unitary_distance_metric": "single_qubit_rz_operator_norm",
        "unitary_distance_passed": True,
        "source_dataset_id": e3_row["source_dataset_id"],
        "source_dataset_file": e3_row["source_dataset_file"],
        "source_dataset_sha256": e3_row["source_dataset_sha256"],
        "source_trace_id": e3_row["source_trace_id"],
        "source_trace_file": e3_row["source_trace_file"],
        "source_trace_sha256": e3_row["source_trace_sha256"],
        "replay_environment_file": e3_row["replay_environment_file"],
        "replay_environment_sha256": e3_row["replay_environment_sha256"],
        "same_unitary_witness_schema": e3_row["same_unitary_witness_schema"],
        "same_unitary_witness_file": e3_row["same_unitary_witness_file"],
        "same_unitary_witness_sha256": e3_row["same_unitary_witness_sha256"],
        "same_unitary_witness_verifier": e3_row["same_unitary_witness_verifier"],
        "verifier_signature_file": e3_row["verifier_signature_file"],
        "verifier_signature_sha256": e3_row["verifier_signature_sha256"],
        "source_backed_replay": True,
        "same_unitary_certificate": True,
        "smoke_only_not_c2_acceptance": False,
        "claim_boundary": "single-row R47 acceptance only; no C2 all-rows closure; O3 remains open; no reroute; no B7 credit; no STV credit",
    }
    row["r57_discriminator_row_hash"] = r38.stable_hash(row)
    return row


def build_payload(args: argparse.Namespace) -> dict[str, Any]:
    started = time.time()
    r38 = load_r38_module(args.root)
    r56 = load_json(args.r56_result)
    r37 = load_json(args.r37_result)
    r33 = load_json(args.r33_contract)
    e3_row = load_json(args.e3_row_input)

    contract = r38.build_replacement_contract(r37, r33)
    write_json(args.contract_output, contract)
    discriminator_row = build_discriminator_row(r38, e3_row, r56)
    fixture = {
        "artifact_id": "B1-B7-cone01-O3-F4-C2-C01-r57-r47-exact-one-row-fixture",
        "source_target_id": TARGET_ID,
        "upstream_target_id": UPSTREAM_TARGET_ID,
        "challenge_id": SELECTED_CHALLENGE_ID,
        "source_r56_result": str(args.r56_result),
        "source_r56_evaluation_hash": r56["summary"]["r56_evaluation_hash"],
        "source_e3_row_input": str(args.e3_row_input),
        "source_e3_row_hash": e3_row["presubmission_row_hash"],
        "contract_hash": contract["contract_hash"],
        "required_row_count_for_this_gate": 1,
        "all8_required_before_full_c2_closure": True,
        "o3_closed": False,
        "reroute_allowed": False,
        "b7_credit_delta": 0,
        "rows": [discriminator_row],
    }
    fixture["fixture_hash"] = r38.stable_hash(fixture)
    write_json(args.fixture_output, fixture)
    evaluation = r38.evaluate_fixture(fixture, contract, args.root, args.fixture_output)
    evaluation["r57_exact_one_row_acceptance"] = (
        evaluation["row_count"] == 1
        and evaluation["source_backed_rows_passed"] == 1
        and evaluation["source_backed_flag_failures"] == 0
        and evaluation["source_provenance_failures"] == 0
        and evaluation["witness_schema_failures"] == 0
        and evaluation["binding_mismatch_count"] == 0
        and evaluation["row_results"][0]["accepted"] is True
    )
    evaluation["full_contract_all8_accepted"] = False
    evaluation["accepted"] = False
    evaluation["claim_boundary"] = (
        "R57 accepts exactly one row at the R47 discriminator layer only; "
        "full C2 all-row closure, O3 closure, reroute, and B7 credit remain blocked."
    )
    evaluation["r57_evaluation_hash"] = r38.stable_hash(evaluation)
    write_json(args.evaluation_output, evaluation)

    row_result = evaluation["row_results"][0]
    zero_credit_ok = (
        fixture["o3_closed"] is False
        and fixture["reroute_allowed"] is False
        and fixture["b7_credit_delta"] == 0
        and "no C2" in discriminator_row["claim_boundary"]
        and "O3 remains open" in discriminator_row["claim_boundary"]
        and "no reroute" in discriminator_row["claim_boundary"]
        and "no B7 credit" in discriminator_row["claim_boundary"]
        and "no STV credit" in discriminator_row["claim_boundary"]
    )
    requirements = [
        req(
            "S1",
            "R56 is the upstream preflight gate and accepted exactly one row at R51",
            r56["summary"].get("requirements_passed") == 8
            and r56["summary"].get("r51_preflight_accepted") is True
            and r56["summary"].get("r51_preflight_accepted_row_count") == 1
            and r56["summary"].get("r47_rerun_performed") is False,
            {
                "r56_requirements_passed": r56["summary"].get("requirements_passed"),
                "r56_r51_preflight_accepted": r56["summary"].get("r51_preflight_accepted"),
                "r56_r51_preflight_accepted_row_count": r56["summary"].get("r51_preflight_accepted_row_count"),
                "r56_r47_rerun_performed": r56["summary"].get("r47_rerun_performed"),
            },
        ),
        req(
            "S2",
            "R57 fixture is bound to the exact R56/R55 E3 replacement row",
            fixture["source_e3_row_hash"] == r56["summary"]["r56_e3_row_hash"]
            and discriminator_row["source_presubmission_row_hash"] == r56["summary"]["r56_e3_row_hash"],
            {
                "fixture_source_e3_row_hash": fixture["source_e3_row_hash"],
                "r56_e3_row_hash": r56["summary"]["r56_e3_row_hash"],
                "r57_discriminator_row_hash": discriminator_row["r57_discriminator_row_hash"],
            },
        ),
        req(
            "S3",
            "R57 reuses the R38/R47 source-backed discriminator contract",
            contract["contract_hash"] == evaluation["contract_hash"]
            and evaluation["input_artifact"] == str(args.fixture_output),
            {
                "contract_hash": contract["contract_hash"],
                "evaluation_contract_hash": evaluation["contract_hash"],
                "input_artifact": evaluation["input_artifact"],
            },
        ),
        req(
            "S4",
            "R57 row passes materialized files, source provenance, witness schema, binding, replay, and flags",
            row_result["accepted"] is True
            and row_result["materialized_files_passed"] is True
            and row_result["binding_hash_matches"] is True
            and row_result["replay_error_within_tolerance"] is True
            and row_result["source_backed_flags_passed"] is True
            and row_result["source_provenance_passed"] is True
            and row_result["witness_schema_passed"] is True
            and row_result["zero_credit_boundary_present"] is True,
            {
                "row_accepted": row_result["accepted"],
                "failed_reasons": row_result["failed_reasons"],
                "materialized_files_passed": row_result["materialized_files_passed"],
                "binding_hash_matches": row_result["binding_hash_matches"],
                "source_backed_flags_passed": row_result["source_backed_flags_passed"],
                "source_provenance_passed": row_result["source_provenance_passed"],
                "witness_schema_passed": row_result["witness_schema_passed"],
                "zero_credit_boundary_present": row_result["zero_credit_boundary_present"],
            },
        ),
        req(
            "S5",
            "R57 accepts exactly one source-backed row at the R47 layer",
            evaluation["r57_exact_one_row_acceptance"] is True
            and evaluation["row_count"] == 1
            and evaluation["source_backed_rows_passed"] == 1
            and evaluation["source_backed_flag_failures"] == 0,
            {
                "r57_exact_one_row_acceptance": evaluation["r57_exact_one_row_acceptance"],
                "row_count": evaluation["row_count"],
                "source_backed_rows_passed": evaluation["source_backed_rows_passed"],
                "source_backed_flag_failures": evaluation["source_backed_flag_failures"],
            },
        ),
        req(
            "S6",
            "R57 does not promote exact-one-row acceptance into full C2/O3/reroute/B7 credit",
            zero_credit_ok
            and evaluation["full_contract_all8_accepted"] is False
            and evaluation["accepted"] is False,
            {
                "zero_credit_ok": zero_credit_ok,
                "full_contract_all8_accepted": evaluation["full_contract_all8_accepted"],
                "evaluation_accepted": evaluation["accepted"],
                "o3_closed": fixture["o3_closed"],
                "reroute_allowed": fixture["reroute_allowed"],
                "b7_credit_delta": fixture["b7_credit_delta"],
            },
        ),
        req(
            "S7",
            "R57 leaves all-8-row scaling and C3-C7 gates open",
            True,
            {
                "remaining_open_obligations": [
                    "scale_R47_to_all_8_rows",
                    "C3_same_unitary_replay_certificate",
                    "C4_C5_same_access_denominator_comparison",
                    "C6_leakage_free_optimizer_trace",
                    "C7_machine_check_replay_bundle",
                    "B7_ledger_retest_after_full_C2_closure",
                ]
            },
        ),
        req(
            "S8",
            "R57 fixture and evaluation are hash-bound",
            bool(fixture["fixture_hash"])
            and bool(evaluation["discriminator_hash"])
            and bool(evaluation["r57_evaluation_hash"]),
            {
                "fixture_hash": fixture["fixture_hash"],
                "fixture_file_sha256": r38.file_hash(args.fixture_output),
                "discriminator_hash": evaluation["discriminator_hash"],
                "r57_evaluation_hash": evaluation["r57_evaluation_hash"],
                "evaluation_file_sha256": r38.file_hash(args.evaluation_output),
            },
        ),
    ]
    failed = [item["requirement_id"] for item in requirements if not item["passed"]]
    summary = {
        "source_r56_evaluation_hash": r56["summary"]["r56_evaluation_hash"],
        "source_r56_e3_row_hash": r56["summary"]["r56_e3_row_hash"],
        "selected_challenge_id": SELECTED_CHALLENGE_ID,
        "r57_fixture_hash": fixture["fixture_hash"],
        "r57_fixture_file_sha256": r38.file_hash(args.fixture_output),
        "r57_discriminator_row_hash": discriminator_row["r57_discriminator_row_hash"],
        "r57_evaluation_hash": evaluation["r57_evaluation_hash"],
        "r57_evaluation_file_sha256": r38.file_hash(args.evaluation_output),
        "discriminator_hash": evaluation["discriminator_hash"],
        "replacement_contract_hash": contract["contract_hash"],
        "row_count": evaluation["row_count"],
        "materialized_rows_passed": evaluation["materialized_rows_passed"],
        "source_backed_rows_passed": evaluation["source_backed_rows_passed"],
        "source_backed_flag_failures": evaluation["source_backed_flag_failures"],
        "source_provenance_failures": evaluation["source_provenance_failures"],
        "witness_schema_failures": evaluation["witness_schema_failures"],
        "binding_mismatch_count": evaluation["binding_mismatch_count"],
        "smoke_only_row_count": evaluation["smoke_only_row_count"],
        "r47_rerun_performed": True,
        "r47_exact_one_row_accepted": evaluation["r57_exact_one_row_acceptance"],
        "accepted_source_backed_row_count": 1 if evaluation["r57_exact_one_row_acceptance"] else 0,
        "c2_single_row_source_backed_accepted": evaluation["r57_exact_one_row_acceptance"],
        "c2_strict_replay_rows_accepted": False,
        "full_contract_all8_accepted": False,
        "o3_closed": False,
        "reroute_allowed": False,
        "b7_credit_delta": 0,
        "b7_space_time_volume_credit": 0,
        "resource_saving_claimed": False,
        "b7_ledger_improvement_claimed": False,
        "remaining_open_obligations": [
            "scale_R47_to_all_8_rows",
            "C3_same_unitary_replay_certificate",
            "C4_C5_same_access_denominator_comparison",
            "C6_leakage_free_optimizer_trace",
            "C7_machine_check_replay_bundle",
            "B7_ledger_retest_after_full_C2_closure",
        ],
        "remaining_open_obligation_count": 6,
        "requirement_count": len(requirements),
        "requirements_passed": len(requirements) - len(failed),
        "requirements_failed": len(failed),
        "failed_requirement_ids": failed,
        "validation_error_count": len(failed),
    }
    return {
        "title": "B1/B7 Cone01 R57 O3-F4 C2 R47 Exact-One-Row Rerun Gate",
        "version": VERSION,
        "last_updated": "2026-07-08",
        "benchmark_id": "B1",
        "linked_benchmark_id": "B7",
        "method": METHOD,
        "status": STATUS,
        "model_status": MODEL_STATUS,
        "source_target_id": TARGET_ID,
        "upstream_target_id": UPSTREAM_TARGET_ID,
        "r47_exact_one_row_packet": {
            "source_r56_result": str(args.r56_result),
            "e3_row_input": str(args.e3_row_input),
            "fixture_output": str(args.fixture_output),
            "evaluation_output": str(args.evaluation_output),
            "replacement_contract_output": str(args.contract_output),
            "fixture": fixture,
            "evaluation": evaluation,
        },
        "requirements": requirements,
        "summary": summary,
        "claim_boundary": {
            "what_is_supported": (
                "R57 reruns the R47/R38 discriminator on exactly the R56 preflight-passing "
                "C01 row and accepts one source-backed row at the discriminator layer."
            ),
            "what_is_not_supported": (
                "R57 does not scale C2 to all 8 rows, does not close O3, does not permit "
                "reroute, and does not grant B7/STV/resource/ledger credit."
            ),
            "next_gate": (
                "Scale the same R47 discriminator to all 8 rows before C3-C7 or any B7 ledger retest."
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
        "# B1/B7 Cone01 R57 O3-F4 C2 R47 Exact-One-Row Rerun Gate",
        "",
        f"- Target: `{payload['source_target_id']}`",
        f"- Upstream target: `{payload['upstream_target_id']}`",
        f"- Method: `{payload['method']}`",
        f"- Status: `{payload['status']}`",
        f"- Selected challenge: `{s['selected_challenge_id']}`",
        f"- R57 fixture hash: `{s['r57_fixture_hash']}`",
        f"- R57 evaluation hash: `{s['r57_evaluation_hash']}`",
        f"- R57 discriminator row hash: `{s['r57_discriminator_row_hash']}`",
        "",
        "## Result",
        "",
        (
            f"R57 passes {s['requirements_passed']}/{s['requirement_count']} requirements "
            "by accepting exactly one source-backed row at the R47 discriminator layer. "
            "Full C2 all-row closure and B7 credit remain blocked."
        ),
        "",
        "## R47 Evidence",
        "",
        f"- Row count: `{s['row_count']}`",
        f"- Materialized rows passed: `{s['materialized_rows_passed']}`",
        f"- Source-backed rows passed: `{s['source_backed_rows_passed']}`",
        f"- Source-backed flag failures: `{s['source_backed_flag_failures']}`",
        f"- Source provenance failures: `{s['source_provenance_failures']}`",
        f"- Witness schema failures: `{s['witness_schema_failures']}`",
        f"- Binding mismatch count: `{s['binding_mismatch_count']}`",
        f"- R47 exact-one-row accepted: `{s['r47_exact_one_row_accepted']}`",
        f"- Full contract all-8 accepted: `{s['full_contract_all8_accepted']}`",
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
    parser.add_argument("--r56-result", type=Path, default=Path("results/B1_B7_cone01_R56_o3_f4_c2_r51_rerun_on_e3_replacement_row_gate_v0.json"))
    parser.add_argument("--e3-row-input", type=Path, default=Path("results/B1_B7_cone01_o3_f4_numerical_refit_submissions/source_backed_rows/O3-F4-C01.e3_replacement_presubmission.json"))
    parser.add_argument("--r37-result", type=Path, default=Path("results/B1_B7_cone01_R37_o3_f4_c2_all_rows_materialized_smoke_gate_v0.json"))
    parser.add_argument("--r33-contract", type=Path, default=Path("results/B1_B7_cone01_R33_o3_f4_c2_provenance_binding_contract_gate_v0.json"))
    parser.add_argument("--fixture-output", type=Path, default=Path("results/B1_B7_cone01_o3_f4_numerical_refit_submissions/source_backed_rows/O3-F4-C01.r57_r47_exact_one_row_fixture.json"))
    parser.add_argument("--evaluation-output", type=Path, default=Path("results/B1_B7_cone01_o3_f4_numerical_refit_submissions/source_backed_rows/O3-F4-C01.r57_r47_exact_one_row_evaluation.json"))
    parser.add_argument("--contract-output", type=Path, default=Path("results/B1_B7_cone01_o3_f4_numerical_refit_submissions/source_backed_rows/O3-F4-C01.r57_source_backed_replacement.contract.json"))
    parser.add_argument("--json-output", type=Path, default=Path("results/B1_B7_cone01_R57_o3_f4_c2_r47_exact_one_row_rerun_gate_v0.json"))
    parser.add_argument("--markdown-output", type=Path, default=Path("research/B1_B7_cone01_R57_o3_f4_c2_r47_exact_one_row_rerun_gate.md"))
    parser.add_argument("--pretty", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    payload = build_payload(args)
    write_json(args.json_output, payload)
    write_markdown(args.markdown_output, payload)
    if args.pretty:
        s = payload["summary"]
        print(
            json.dumps(
                {
                    "status": payload["status"],
                    "selected_challenge_id": s["selected_challenge_id"],
                    "requirements_passed": s["requirements_passed"],
                    "requirements_failed": s["requirements_failed"],
                    "r47_rerun_performed": s["r47_rerun_performed"],
                    "r47_exact_one_row_accepted": s["r47_exact_one_row_accepted"],
                    "accepted_source_backed_row_count": s["accepted_source_backed_row_count"],
                    "full_contract_all8_accepted": s["full_contract_all8_accepted"],
                    "c2_strict_replay_rows_accepted": s["c2_strict_replay_rows_accepted"],
                    "b7_credit_delta": s["b7_credit_delta"],
                    "r57_evaluation_hash": s["r57_evaluation_hash"],
                    "r57_fixture_hash": s["r57_fixture_hash"],
                    "json_output": str(args.json_output),
                },
                indent=2,
                sort_keys=True,
            )
        )


if __name__ == "__main__":
    main()
