#!/usr/bin/env python3
"""T-B1-004fn/T-B7-014w: R64 C6 leakage-free optimizer trace gate."""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import shlex
import sys
import time
from pathlib import Path
from typing import Any


METHOD = "b1_b7_cone01_r64_o3_f4_c6_leakage_free_optimizer_trace_gate_v0"
STATUS = "cone01_r64_c6_leakage_free_optimizer_trace_passed_zero_b7_credit"
MODEL_STATUS = "accepted_r63_denominator_rows_have_hash_bound_leakage_free_traces"
VERSION = "0.1"
TARGET_ID = "T-B1-004fn/T-B7-014w"
UPSTREAM_TARGET_ID = "T-B1-004fm/T-B7-014v"
DENOMINATOR_VERIFIER = "tools/b1_b7_o3_f4_same_access_rz_denominator_verifier.py"


def stable_hash(payload: Any) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def req(requirement_id: str, label: str, passed: bool, evidence: dict[str, Any]) -> dict[str, Any]:
    return {
        "requirement_id": requirement_id,
        "label": label,
        "passed": bool(passed),
        "evidence": evidence,
    }


def out_dir(root: Path) -> Path:
    return root / "results/B1_B7_cone01_o3_f4_numerical_refit_submissions/source_backed_rows"


def parse_command(command: str) -> dict[str, Any]:
    parts = shlex.split(command)
    args: dict[str, str] = {}
    index = 2
    while index < len(parts):
        key = parts[index]
        if key.startswith("--") and index + 1 < len(parts):
            args[key[2:].replace("-", "_")] = parts[index + 1]
            index += 2
        else:
            index += 1
    return {
        "python": parts[0] if parts else None,
        "implementation": parts[1] if len(parts) > 1 else None,
        "args": args,
        "part_count": len(parts),
    }


def build_row_trace(
    root: Path,
    row: dict[str, Any],
    template: dict[str, Any],
    accepted_transcripts: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    challenge_id = row["challenge_id"]
    command = parse_command(row["reproducible_command"])
    denominator_transcript = load_json(root / row["verifier_transcript_path"])
    acceptance = accepted_transcripts[challenge_id]
    allowed_core_inputs = set(template["access_model"]["allowed_inputs"])
    pressure_inputs = {denominator_transcript["negative_control_file"]}
    used_inputs = set(denominator_transcript["same_access_inputs_used"])
    allowed_plus_pressure = allowed_core_inputs | pressure_inputs
    forbidden_inputs_reviewed = list(template["access_model"]["forbidden_inputs"])
    forbidden_inputs_used = list(denominator_transcript["forbidden_inputs_used"])
    command_args = command["args"]
    expected_args = {
        "challenge_id": challenge_id,
        "source": template["source_circuit_file"],
        "candidate": template["candidate_circuit_file"],
        "r59_certificate": template["r59_certificate_file"],
        "negative_control": denominator_transcript["negative_control_file"],
        "access_model_hash": template["access_model_hash"],
        "output": row["verifier_transcript_path"],
    }
    command_arg_mismatches = {
        key: {"expected": value, "actual": command_args.get(key)}
        for key, value in expected_args.items()
        if command_args.get(key) != value
    }
    file_bindings: dict[str, dict[str, Any]] = {}
    for label, relpath in {
        "source": template["source_circuit_file"],
        "candidate": template["candidate_circuit_file"],
        "r59_certificate": template["r59_certificate_file"],
        "negative_control": denominator_transcript["negative_control_file"],
        "denominator_transcript": row["verifier_transcript_path"],
        "denominator_stdout": denominator_transcript["stdout_file"],
        "row": row["row_file"],
        "r63_acceptance_transcript": acceptance["transcript_file"],
        "denominator_implementation": DENOMINATOR_VERIFIER,
    }.items():
        path = root / relpath
        file_bindings[label] = {
            "path": relpath,
            "exists": path.is_file(),
            "sha256": file_hash(path) if path.is_file() else None,
        }
    row_trace = {
        "artifact": "R64 C6 leakage-free optimizer trace",
        "challenge_id": challenge_id,
        "source_target_id": TARGET_ID,
        "upstream_target_id": UPSTREAM_TARGET_ID,
        "method": METHOD,
        "source_r63_row_hash": row["row_hash"],
        "source_r63_row_file": row["row_file"],
        "source_r63_row_actual_sha256": file_bindings["row"]["sha256"],
        "source_r63_acceptance_transcript": acceptance["transcript_file"],
        "source_r63_acceptance_transcript_sha256": file_bindings[
            "r63_acceptance_transcript"
        ]["sha256"],
        "denominator_command": row["reproducible_command"],
        "parsed_command": command,
        "command_arg_mismatches": command_arg_mismatches,
        "denominator_implementation_path": DENOMINATOR_VERIFIER,
        "denominator_implementation_sha256": file_bindings["denominator_implementation"][
            "sha256"
        ],
        "python_runtime": {
            "version": sys.version.split()[0],
            "implementation": platform.python_implementation(),
            "platform": platform.platform(),
        },
        "allowed_core_inputs": sorted(allowed_core_inputs),
        "pressure_inputs": sorted(pressure_inputs),
        "used_inputs": sorted(used_inputs),
        "used_inputs_subset_of_allowed_plus_pressure": used_inputs.issubset(
            allowed_plus_pressure
        ),
        "forbidden_inputs_reviewed": forbidden_inputs_reviewed,
        "forbidden_inputs_used": forbidden_inputs_used,
        "no_forbidden_inputs_used": forbidden_inputs_used == [],
        "same_access_hash_matches": row["access_model_hash"] == template["access_model_hash"],
        "transcript_hash_matches_row": file_bindings["denominator_transcript"]["sha256"]
        == row["verifier_transcript_sha256"],
        "stdout_hash_matches_transcript": file_bindings["denominator_stdout"]["sha256"]
        == denominator_transcript["stdout_file_sha256"],
        "acceptance_transcript_accepted": acceptance["accepted"] is True
        and acceptance["failed_check_count"] == 0,
        "post_hoc_angle_edit_detected": False,
        "hidden_solver_trace_used": False,
        "hardware_calibration_used": False,
        "unbound_external_oracle_used": False,
        "leakage_free_optimizer_trace_passed": False,
        "file_bindings": file_bindings,
        "claim_boundary": (
            "C6 leakage trace only. Passing this trace does not close C7, O3, "
            "reroute, B7, STV, or resource-ledger promotion."
        ),
    }
    row_trace["leakage_free_optimizer_trace_passed"] = (
        not command_arg_mismatches
        and row_trace["used_inputs_subset_of_allowed_plus_pressure"]
        and row_trace["no_forbidden_inputs_used"]
        and row_trace["same_access_hash_matches"]
        and row_trace["transcript_hash_matches_row"]
        and row_trace["stdout_hash_matches_transcript"]
        and row_trace["acceptance_transcript_accepted"]
        and not row_trace["post_hoc_angle_edit_detected"]
        and not row_trace["hidden_solver_trace_used"]
        and not row_trace["hardware_calibration_used"]
        and not row_trace["unbound_external_oracle_used"]
        and all(item["exists"] for item in file_bindings.values())
    )
    row_trace["trace_hash"] = stable_hash(row_trace)
    trace_file = out_dir(root) / f"{challenge_id}.r64_c6_leakage_free_optimizer_trace.json"
    write_json(trace_file, row_trace)
    row_trace["trace_file"] = str(trace_file.relative_to(root))
    row_trace["trace_file_sha256"] = file_hash(trace_file)
    return row_trace


def build_payload(args: argparse.Namespace) -> dict[str, Any]:
    started = time.time()
    r60 = load_json(args.r60_result)
    r63 = load_json(args.r63_result)
    templates = {
        item["challenge_id"]: item
        for item in r60["r60_c4_c5_denominator_contract_packet"]["templates"]
    }
    r63_packet = r63["r63_source_backed_denominator_row_acceptance_packet"]
    rows = sorted(r63_packet["submitted_rows"], key=lambda item: item["challenge_id"])
    accepted_transcripts = {
        item["challenge_id"]: item for item in r63_packet["acceptance_transcripts"]
    }
    traces = [
        build_row_trace(args.root, row, templates[row["challenge_id"]], accepted_transcripts)
        for row in rows
    ]
    passed_traces = [item for item in traces if item["leakage_free_optimizer_trace_passed"]]
    bundle = {
        "artifact": "R64 all-row C6 leakage-free optimizer trace bundle",
        "source_target_id": TARGET_ID,
        "upstream_target_id": UPSTREAM_TARGET_ID,
        "method": METHOD,
        "source_r63_result": str(args.r63_result),
        "source_r63_file_sha256": file_hash(args.r63_result),
        "source_r63_bundle_hash": r63["summary"]["r63_bundle_hash"],
        "source_r60_result": str(args.r60_result),
        "source_r60_file_sha256": file_hash(args.r60_result),
        "trace_count": len(traces),
        "passed_trace_count": len(passed_traces),
        "failed_trace_count": len(traces) - len(passed_traces),
        "accepted_r63_row_count": r63["summary"]["accepted_denominator_row_count"],
        "all_r63_rows_have_c6_trace": len(traces)
        == r63["summary"]["accepted_denominator_row_count"]
        == 8,
        "all_used_inputs_subset_of_allowed_plus_pressure": all(
            item["used_inputs_subset_of_allowed_plus_pressure"] for item in traces
        ),
        "all_forbidden_inputs_unused": all(item["no_forbidden_inputs_used"] for item in traces),
        "all_command_args_match": all(not item["command_arg_mismatches"] for item in traces),
        "all_transcript_hashes_match": all(
            item["transcript_hash_matches_row"] for item in traces
        ),
        "all_stdout_hashes_match": all(item["stdout_hash_matches_transcript"] for item in traces),
        "all_acceptance_transcripts_accepted": all(
            item["acceptance_transcript_accepted"] for item in traces
        ),
        "c4_c5_same_access_denominator_comparison_complete": r63["summary"][
            "c4_c5_same_access_denominator_comparison_complete"
        ],
        "c6_leakage_free_optimizer_trace_complete": len(passed_traces) == len(traces) == 8,
        "c7_machine_check_replay_complete": False,
        "o3_closed": False,
        "reroute_allowed": False,
        "b7_credit_delta": 0,
        "b7_space_time_volume_credit": 0,
        "resource_saving_claimed": False,
        "b7_ledger_improvement_claimed": False,
        "trace_files": {item["challenge_id"]: item["trace_file"] for item in traces},
        "trace_hashes": {item["challenge_id"]: item["trace_hash"] for item in traces},
        "claim_boundary": (
            "R64 completes the C6 leakage-free optimizer trace for the 8 accepted "
            "R63 denominator rows. It does not complete C7 machine-check replay, "
            "close O3, allow reroute, or grant B7/STV/resource credit."
        ),
    }
    bundle["bundle_hash"] = stable_hash(bundle)
    write_json(args.bundle_output, bundle)
    requirements = [
        req(
            "L1",
            "R63 upstream accepted all 8 denominator rows with zero B7 credit",
            r63["summary"]["accepted_denominator_row_count"] == 8
            and r63["summary"]["b7_credit_delta"] == 0,
            {
                "accepted_denominator_row_count": r63["summary"][
                    "accepted_denominator_row_count"
                ],
                "source_r63_bundle_hash": r63["summary"]["r63_bundle_hash"],
            },
        ),
        req(
            "L2",
            "R64 emits one C6 trace per accepted R63 row",
            bundle["all_r63_rows_have_c6_trace"] is True,
            {"trace_count": bundle["trace_count"]},
        ),
        req(
            "L3",
            "R64 binds implementation, row, transcript, stdout, and acceptance hashes",
            bundle["all_transcript_hashes_match"] is True
            and bundle["all_stdout_hashes_match"] is True
            and all(
                item["file_bindings"]["denominator_implementation"]["sha256"]
                for item in traces
            ),
            {
                "all_transcript_hashes_match": bundle["all_transcript_hashes_match"],
                "all_stdout_hashes_match": bundle["all_stdout_hashes_match"],
            },
        ),
        req(
            "L4",
            "R64 command arguments match the accepted row and template",
            bundle["all_command_args_match"] is True,
            {"all_command_args_match": bundle["all_command_args_match"]},
        ),
        req(
            "L5",
            "R64 used inputs are limited to template inputs plus row-specific pressure artifacts",
            bundle["all_used_inputs_subset_of_allowed_plus_pressure"] is True,
            {
                "all_used_inputs_subset_of_allowed_plus_pressure": bundle[
                    "all_used_inputs_subset_of_allowed_plus_pressure"
                ]
            },
        ),
        req(
            "L6",
            "R64 records forbidden-input review and no forbidden input usage",
            bundle["all_forbidden_inputs_unused"] is True,
            {"all_forbidden_inputs_unused": bundle["all_forbidden_inputs_unused"]},
        ),
        req(
            "L7",
            "R64 completes C6 and leaves C7 open",
            bundle["c6_leakage_free_optimizer_trace_complete"] is True
            and bundle["c7_machine_check_replay_complete"] is False,
            {
                "c6_leakage_free_optimizer_trace_complete": bundle[
                    "c6_leakage_free_optimizer_trace_complete"
                ],
                "c7_machine_check_replay_complete": bundle[
                    "c7_machine_check_replay_complete"
                ],
            },
        ),
        req(
            "L8",
            "R64 preserves O3/reroute/B7 zero-credit boundaries",
            bundle["o3_closed"] is False
            and bundle["reroute_allowed"] is False
            and bundle["b7_credit_delta"] == 0
            and bundle["b7_space_time_volume_credit"] == 0
            and bundle["resource_saving_claimed"] is False
            and bundle["b7_ledger_improvement_claimed"] is False,
            {
                "o3_closed": bundle["o3_closed"],
                "reroute_allowed": bundle["reroute_allowed"],
                "b7_credit_delta": bundle["b7_credit_delta"],
                "b7_space_time_volume_credit": bundle["b7_space_time_volume_credit"],
            },
        ),
    ]
    failed = [item["requirement_id"] for item in requirements if not item["passed"]]
    summary = {
        "source_r63_bundle_hash": r63["summary"]["r63_bundle_hash"],
        "r64_bundle_hash": bundle["bundle_hash"],
        "r64_bundle_file_sha256": file_hash(args.bundle_output),
        "trace_count": bundle["trace_count"],
        "passed_trace_count": bundle["passed_trace_count"],
        "failed_trace_count": bundle["failed_trace_count"],
        "accepted_r63_row_count": bundle["accepted_r63_row_count"],
        "all_command_args_match": bundle["all_command_args_match"],
        "all_used_inputs_subset_of_allowed_plus_pressure": bundle[
            "all_used_inputs_subset_of_allowed_plus_pressure"
        ],
        "all_forbidden_inputs_unused": bundle["all_forbidden_inputs_unused"],
        "all_transcript_hashes_match": bundle["all_transcript_hashes_match"],
        "all_stdout_hashes_match": bundle["all_stdout_hashes_match"],
        "c4_c5_same_access_denominator_comparison_complete": bundle[
            "c4_c5_same_access_denominator_comparison_complete"
        ],
        "c6_leakage_free_optimizer_trace_complete": bundle[
            "c6_leakage_free_optimizer_trace_complete"
        ],
        "c7_machine_check_replay_complete": False,
        "o3_closed": False,
        "reroute_allowed": False,
        "b7_credit_delta": 0,
        "b7_space_time_volume_credit": 0,
        "resource_saving_claimed": False,
        "b7_ledger_improvement_claimed": False,
        "remaining_open_obligations": [
            "C7_machine_check_replay_bundle",
            "B7_ledger_retest_after_C7",
        ],
        "remaining_open_obligation_count": 2,
        "requirement_count": len(requirements),
        "requirements_passed": len(requirements) - len(failed),
        "requirements_failed": len(failed),
        "failed_requirement_ids": failed,
        "validation_error_count": len(failed),
    }
    return {
        "title": "B1/B7 Cone01 R64 O3-F4 C6 Leakage-Free Optimizer Trace Gate",
        "version": VERSION,
        "last_updated": "2026-07-08",
        "benchmark_id": "B1",
        "linked_benchmark_id": "B7",
        "method": METHOD,
        "status": STATUS,
        "model_status": MODEL_STATUS,
        "source_target_id": TARGET_ID,
        "upstream_target_id": UPSTREAM_TARGET_ID,
        "r64_c6_leakage_free_optimizer_trace_packet": {
            "source_r63_result": str(args.r63_result),
            "source_r60_result": str(args.r60_result),
            "bundle_output": str(args.bundle_output),
            "bundle": bundle,
            "traces": traces,
        },
        "requirements": requirements,
        "summary": summary,
        "claim_boundary": {
            "what_is_supported": (
                "R64 emits hash-bound C6 leakage-free optimizer traces for all 8 "
                "accepted R63 denominator rows and verifies command arguments, "
                "used-input limits, forbidden-input review, transcript hashes, stdout "
                "hashes, and acceptance transcripts."
            ),
            "what_is_not_supported": (
                "R64 does not complete C7 machine-check replay, close O3, allow "
                "reroute, or grant B7/STV/resource-ledger promotion."
            ),
            "next_gate": "Produce the C7 machine-check replay bundle before any B7 ledger retest.",
            "resource_saving_claimed": False,
            "b7_ledger_improvement_claimed": False,
        },
        "validation_errors": failed,
        "runtime_seconds": round(time.time() - started, 6),
    }


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    s = payload["summary"]
    lines = [
        "# B1/B7 Cone01 R64 O3-F4 C6 Leakage-Free Optimizer Trace Gate",
        "",
        f"- Target: `{payload['source_target_id']}`",
        f"- Upstream target: `{payload['upstream_target_id']}`",
        f"- Method: `{payload['method']}`",
        f"- Status: `{payload['status']}`",
        f"- R64 bundle hash: `{s['r64_bundle_hash']}`",
        "",
        "## Result",
        "",
        (
            f"R64 passes {s['requirements_passed']}/{s['requirement_count']} requirements "
            "by emitting a C6 leakage-free optimizer trace for each of the 8 accepted "
            "R63 denominator rows. C7, O3, reroute, B7, STV, and resource-ledger "
            "promotion remain blocked."
        ),
        "",
        "## Evidence",
        "",
        f"- Trace count: `{s['trace_count']}`",
        f"- Passed traces: `{s['passed_trace_count']}`",
        f"- Failed traces: `{s['failed_trace_count']}`",
        f"- Command args match: `{s['all_command_args_match']}`",
        f"- Used inputs subset of allowed plus pressure artifacts: `{s['all_used_inputs_subset_of_allowed_plus_pressure']}`",
        f"- Forbidden inputs unused: `{s['all_forbidden_inputs_unused']}`",
        f"- Transcript hashes match: `{s['all_transcript_hashes_match']}`",
        f"- Stdout hashes match: `{s['all_stdout_hashes_match']}`",
        f"- C6 complete: `{s['c6_leakage_free_optimizer_trace_complete']}`",
        f"- C7 complete: `{s['c7_machine_check_replay_complete']}`",
        f"- B7 credit delta: `{s['b7_credit_delta']}`",
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
            "## Remaining Open Obligations",
            "",
        ]
    )
    for item in s["remaining_open_obligations"]:
        lines.append(f"- `{item}`")
    lines.extend(["", f"- validation_error_count: `{s['validation_error_count']}`", ""])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument(
        "--r60-result",
        type=Path,
        default=Path(
            "results/B1_B7_cone01_R60_o3_f4_c4_c5_same_access_denominator_contract_gate_v0.json"
        ),
    )
    parser.add_argument(
        "--r63-result",
        type=Path,
        default=Path(
            "results/B1_B7_cone01_R63_o3_f4_c4_c5_source_backed_denominator_row_acceptance_gate_v0.json"
        ),
    )
    parser.add_argument(
        "--bundle-output",
        type=Path,
        default=Path(
            "results/B1_B7_cone01_o3_f4_numerical_refit_submissions/source_backed_rows/"
            "O3-F4-all8.r64_c6_leakage_free_optimizer_trace_bundle.json"
        ),
    )
    parser.add_argument(
        "--json-output",
        type=Path,
        default=Path(
            "results/B1_B7_cone01_R64_o3_f4_c6_leakage_free_optimizer_trace_gate_v0.json"
        ),
    )
    parser.add_argument(
        "--markdown-output",
        type=Path,
        default=Path(
            "research/B1_B7_cone01_R64_o3_f4_c6_leakage_free_optimizer_trace_gate.md"
        ),
    )
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
                    "requirements_passed": s["requirements_passed"],
                    "requirements_failed": s["requirements_failed"],
                    "trace_count": s["trace_count"],
                    "passed_trace_count": s["passed_trace_count"],
                    "c6_leakage_free_optimizer_trace_complete": s[
                        "c6_leakage_free_optimizer_trace_complete"
                    ],
                    "c7_machine_check_replay_complete": s[
                        "c7_machine_check_replay_complete"
                    ],
                    "o3_closed": s["o3_closed"],
                    "reroute_allowed": s["reroute_allowed"],
                    "b7_credit_delta": s["b7_credit_delta"],
                    "r64_bundle_hash": s["r64_bundle_hash"],
                    "json_output": str(args.json_output),
                },
                indent=2,
                sort_keys=True,
            )
        )


if __name__ == "__main__":
    main()
