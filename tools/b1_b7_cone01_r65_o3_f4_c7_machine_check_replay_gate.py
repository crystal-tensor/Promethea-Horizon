#!/usr/bin/env python3
"""T-B1-004fo/T-B7-014x: R65 C7 machine-check replay gate."""

from __future__ import annotations

import argparse
import hashlib
import json
import shlex
import subprocess
import sys
import time
from pathlib import Path
from typing import Any


METHOD = "b1_b7_cone01_r65_o3_f4_c7_machine_check_replay_gate_v0"
STATUS = "cone01_r65_c7_machine_check_replay_passed_zero_b7_credit"
MODEL_STATUS = "r63_r64_rows_have_machine_checked_replay_verdicts"
VERSION = "0.1"
TARGET_ID = "T-B1-004fo/T-B7-014x"
UPSTREAM_TARGET_ID = "T-B1-004fn/T-B7-014w"
DENOMINATOR_VERIFIER = "tools/b1_b7_o3_f4_same_access_rz_denominator_verifier.py"
ROW_DIR = "results/B1_B7_cone01_o3_f4_numerical_refit_submissions/source_backed_rows"

SEMANTIC_TRANSCRIPT_FIELDS = [
    "access_model_hash",
    "candidate_circuit_file",
    "candidate_circuit_sha256",
    "candidate_theta",
    "challenge_id",
    "claim_boundary",
    "denominator_distance",
    "forbidden_inputs_used",
    "method",
    "negative_control_distance",
    "negative_control_file",
    "negative_control_rejected",
    "negative_control_sha256",
    "positive_distance_met_or_equal",
    "pressure_flags_transcript_bound",
    "r59_certificate_file",
    "r59_certificate_hash",
    "r59_certificate_sha256",
    "r59_positive_replay_distance",
    "same_access_inputs_used",
    "source_circuit_file",
    "source_circuit_sha256",
    "source_theta",
    "strict_tolerance",
    "unitary_distance_metric",
]


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


def semantic_digest(transcript: dict[str, Any]) -> dict[str, Any]:
    return {field: transcript.get(field) for field in SEMANTIC_TRANSCRIPT_FIELDS}


def parse_command(command: str) -> tuple[str, list[str], dict[str, str]]:
    parts = shlex.split(command)
    if len(parts) < 2:
        raise ValueError(f"invalid replay command: {command}")
    args: dict[str, str] = {}
    index = 2
    while index < len(parts):
        key = parts[index]
        if key.startswith("--") and index + 1 < len(parts):
            args[key[2:].replace("-", "_")] = parts[index + 1]
            index += 2
        else:
            index += 1
    return parts[1], parts[2:], args


def replace_output_arg(raw_args: list[str], output_path: str) -> list[str]:
    rewritten = list(raw_args)
    for index, value in enumerate(rewritten):
        if value == "--output" and index + 1 < len(rewritten):
            rewritten[index + 1] = output_path
            return rewritten
    return rewritten + ["--output", output_path]


def replay_one(root: Path, row: dict[str, Any], r64_trace: dict[str, Any]) -> dict[str, Any]:
    challenge_id = row["challenge_id"]
    implementation, raw_args, parsed_args = parse_command(row["reproducible_command"])
    if implementation != DENOMINATOR_VERIFIER:
        raise ValueError(f"{challenge_id}: unexpected implementation {implementation}")

    replay_transcript = f"{ROW_DIR}/{challenge_id}.r65_c7_machine_check_replay_transcript.json"
    replay_stdout = f"{ROW_DIR}/{challenge_id}.r65_c7_machine_check_replay.stdout.txt"
    replay_args = replace_output_arg(raw_args, replay_transcript)
    command = [sys.executable, implementation, *replay_args]
    started = time.time()
    proc = subprocess.run(
        command,
        cwd=root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    runtime = round(time.time() - started, 6)
    stdout_path = root / replay_stdout
    stdout_path.parent.mkdir(parents=True, exist_ok=True)
    stdout_path.write_text(proc.stdout, encoding="utf-8")

    original_transcript_path = root / row["verifier_transcript_path"]
    original_transcript = load_json(original_transcript_path)
    replay_transcript_payload = (
        load_json(root / replay_transcript) if (root / replay_transcript).is_file() else {}
    )
    original_digest = semantic_digest(original_transcript)
    replay_digest = semantic_digest(replay_transcript_payload)
    digest_mismatches = {
        key: {"original": original_digest.get(key), "replay": replay_digest.get(key)}
        for key in SEMANTIC_TRANSCRIPT_FIELDS
        if original_digest.get(key) != replay_digest.get(key)
    }
    file_checks = {
        "r63_row": {
            "path": row["row_file"],
            "sha256": file_hash(root / row["row_file"]),
            "expected_sha256": r64_trace["source_r63_row_actual_sha256"],
        },
        "r64_trace": {
            "path": r64_trace["trace_file"],
            "sha256": file_hash(root / r64_trace["trace_file"]),
            "expected_sha256": r64_trace["trace_file_sha256"],
        },
        "original_transcript": {
            "path": row["verifier_transcript_path"],
            "sha256": file_hash(original_transcript_path),
            "expected_sha256": row["verifier_transcript_sha256"],
        },
        "replay_transcript": {
            "path": replay_transcript,
            "sha256": file_hash(root / replay_transcript)
            if (root / replay_transcript).is_file()
            else None,
        },
        "replay_stdout": {
            "path": replay_stdout,
            "sha256": file_hash(stdout_path),
        },
        "implementation": {
            "path": DENOMINATOR_VERIFIER,
            "sha256": file_hash(root / DENOMINATOR_VERIFIER),
            "expected_sha256": r64_trace["file_bindings"]["denominator_implementation"][
                "sha256"
            ],
        },
    }
    file_hashes_match = all(
        item.get("expected_sha256") in (None, item.get("sha256"))
        for item in file_checks.values()
    )
    replay_passed = (
        proc.returncode == 0
        and not digest_mismatches
        and file_hashes_match
        and r64_trace["leakage_free_optimizer_trace_passed"] is True
        and replay_digest.get("denominator_distance") == 0.0
        and replay_digest.get("positive_distance_met_or_equal") is True
        and replay_digest.get("negative_control_rejected") is True
        and replay_digest.get("forbidden_inputs_used") == []
    )
    verdict = {
        "artifact": "R65 C7 machine-check replay verdict",
        "challenge_id": challenge_id,
        "source_target_id": TARGET_ID,
        "upstream_target_id": UPSTREAM_TARGET_ID,
        "method": METHOD,
        "source_r64_trace_file": r64_trace["trace_file"],
        "source_r64_trace_hash": r64_trace["trace_hash"],
        "source_r64_trace_file_sha256": r64_trace["trace_file_sha256"],
        "source_r63_row_file": row["row_file"],
        "source_r63_row_hash": row["row_hash"],
        "source_r63_transcript": row["verifier_transcript_path"],
        "replay_command": " ".join(shlex.quote(part) for part in command),
        "replay_returncode": proc.returncode,
        "replay_stderr": proc.stderr,
        "replay_runtime_seconds": runtime,
        "original_semantic_digest": original_digest,
        "replay_semantic_digest": replay_digest,
        "semantic_digest_hash": stable_hash(replay_digest),
        "semantic_digest_mismatches": digest_mismatches,
        "file_checks": file_checks,
        "file_hashes_match": file_hashes_match,
        "replay_denominator_distance_zero": replay_digest.get("denominator_distance") == 0.0,
        "replay_positive_distance_met_or_equal": replay_digest.get(
            "positive_distance_met_or_equal"
        )
        is True,
        "replay_negative_control_rejected": replay_digest.get("negative_control_rejected")
        is True,
        "replay_forbidden_inputs_unused": replay_digest.get("forbidden_inputs_used") == [],
        "machine_check_replay_passed": replay_passed,
        "claim_boundary": (
            "C7 machine-check replay only. Passing this gate replays the accepted "
            "R63/R64 denominator evidence under a stable semantic digest; it does "
            "not close O3, allow reroute, or grant B7/STV/resource credit."
        ),
    }
    verdict["verdict_hash"] = stable_hash(verdict)
    verdict_path = root / ROW_DIR / f"{challenge_id}.r65_c7_machine_check_replay_verdict.json"
    write_json(verdict_path, verdict)
    verdict["verdict_file"] = str(verdict_path.relative_to(root))
    verdict["verdict_file_sha256"] = file_hash(verdict_path)
    return verdict


def build_payload(args: argparse.Namespace) -> dict[str, Any]:
    started = time.time()
    r63 = load_json(args.r63_result)
    r64 = load_json(args.r64_result)
    r64_bundle = load_json(args.r64_bundle)
    rows = sorted(
        r63["r63_source_backed_denominator_row_acceptance_packet"]["submitted_rows"],
        key=lambda item: item["challenge_id"],
    )
    traces = {
        item["challenge_id"]: item
        for item in r64["r64_c6_leakage_free_optimizer_trace_packet"]["traces"]
    }
    verdicts = [replay_one(args.root, row, traces[row["challenge_id"]]) for row in rows]
    passed = [item for item in verdicts if item["machine_check_replay_passed"]]
    bundle = {
        "artifact": "R65 all-row C7 machine-check replay bundle",
        "source_target_id": TARGET_ID,
        "upstream_target_id": UPSTREAM_TARGET_ID,
        "method": METHOD,
        "source_r63_result": str(args.r63_result),
        "source_r63_file_sha256": file_hash(args.r63_result),
        "source_r63_bundle_hash": r63["summary"]["r63_bundle_hash"],
        "source_r64_result": str(args.r64_result),
        "source_r64_file_sha256": file_hash(args.r64_result),
        "source_r64_bundle_hash": r64["summary"]["r64_bundle_hash"],
        "source_r64_bundle_file": str(args.r64_bundle),
        "source_r64_bundle_file_sha256": file_hash(args.r64_bundle),
        "source_r64_bundle_hash_matches": r64_bundle["bundle_hash"]
        == r64["summary"]["r64_bundle_hash"],
        "verdict_count": len(verdicts),
        "passed_verdict_count": len(passed),
        "failed_verdict_count": len(verdicts) - len(passed),
        "all_r64_traces_replayed": len(verdicts) == r64["summary"]["trace_count"] == 8,
        "all_replay_semantic_digests_match": all(
            not item["semantic_digest_mismatches"] for item in verdicts
        ),
        "all_replay_commands_exit_zero": all(item["replay_returncode"] == 0 for item in verdicts),
        "all_replay_file_hashes_match": all(item["file_hashes_match"] for item in verdicts),
        "all_replay_denominator_distances_zero": all(
            item["replay_denominator_distance_zero"] for item in verdicts
        ),
        "all_replay_negative_controls_rejected": all(
            item["replay_negative_control_rejected"] for item in verdicts
        ),
        "all_replay_forbidden_inputs_unused": all(
            item["replay_forbidden_inputs_unused"] for item in verdicts
        ),
        "c4_c5_same_access_denominator_comparison_complete": r64["summary"][
            "c4_c5_same_access_denominator_comparison_complete"
        ],
        "c6_leakage_free_optimizer_trace_complete": r64["summary"][
            "c6_leakage_free_optimizer_trace_complete"
        ],
        "c7_machine_check_replay_complete": len(passed) == len(verdicts) == 8,
        "o3_closed": False,
        "reroute_allowed": False,
        "b7_credit_delta": 0,
        "b7_space_time_volume_credit": 0,
        "resource_saving_claimed": False,
        "b7_ledger_improvement_claimed": False,
        "verdict_files": {item["challenge_id"]: item["verdict_file"] for item in verdicts},
        "verdict_hashes": {item["challenge_id"]: item["verdict_hash"] for item in verdicts},
        "claim_boundary": (
            "R65 completes C7 machine-check replay for the R63/R64 denominator "
            "evidence by rerunning the verifier and comparing stable semantic "
            "digests. It does not close O3, allow reroute, or grant B7/STV/resource credit."
        ),
    }
    bundle["bundle_hash"] = stable_hash(bundle)
    write_json(args.bundle_output, bundle)
    requirements = [
        req(
            "M1",
            "R64 upstream completed C6 and preserved zero B7 credit",
            r64["summary"]["c6_leakage_free_optimizer_trace_complete"] is True
            and r64["summary"]["b7_credit_delta"] == 0,
            {
                "source_r64_bundle_hash": r64["summary"]["r64_bundle_hash"],
                "source_r64_b7_credit_delta": r64["summary"]["b7_credit_delta"],
            },
        ),
        req(
            "M2",
            "R65 reruns one verifier command per accepted R64 trace",
            bundle["all_r64_traces_replayed"] and bundle["all_replay_commands_exit_zero"],
            {
                "verdict_count": bundle["verdict_count"],
                "all_replay_commands_exit_zero": bundle["all_replay_commands_exit_zero"],
            },
        ),
        req(
            "M3",
            "R65 replay semantic digests match the original R63 transcripts",
            bundle["all_replay_semantic_digests_match"],
            {
                "failed_verdict_count": bundle["failed_verdict_count"],
                "mismatch_counts": {
                    item["challenge_id"]: len(item["semantic_digest_mismatches"])
                    for item in verdicts
                },
            },
        ),
        req(
            "M4",
            "R65 replay file hashes bind R63 rows, R64 traces, transcripts, and implementation",
            bundle["all_replay_file_hashes_match"],
            {"all_replay_file_hashes_match": bundle["all_replay_file_hashes_match"]},
        ),
        req(
            "M5",
            "R65 replay keeps denominator distances at zero and rejects negative controls",
            bundle["all_replay_denominator_distances_zero"]
            and bundle["all_replay_negative_controls_rejected"],
            {
                "all_replay_denominator_distances_zero": bundle[
                    "all_replay_denominator_distances_zero"
                ],
                "all_replay_negative_controls_rejected": bundle[
                    "all_replay_negative_controls_rejected"
                ],
            },
        ),
        req(
            "M6",
            "R65 replay uses no forbidden inputs",
            bundle["all_replay_forbidden_inputs_unused"],
            {
                "all_replay_forbidden_inputs_unused": bundle[
                    "all_replay_forbidden_inputs_unused"
                ]
            },
        ),
        req(
            "M7",
            "R65 completes C7 after C4/C5 and C6",
            bundle["c4_c5_same_access_denominator_comparison_complete"] is True
            and bundle["c6_leakage_free_optimizer_trace_complete"] is True
            and bundle["c7_machine_check_replay_complete"] is True,
            {
                "c4_c5_same_access_denominator_comparison_complete": bundle[
                    "c4_c5_same_access_denominator_comparison_complete"
                ],
                "c6_leakage_free_optimizer_trace_complete": bundle[
                    "c6_leakage_free_optimizer_trace_complete"
                ],
                "c7_machine_check_replay_complete": bundle[
                    "c7_machine_check_replay_complete"
                ],
            },
        ),
        req(
            "M8",
            "R65 preserves O3/reroute/B7 zero-credit boundaries",
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
        "source_r64_bundle_hash": r64["summary"]["r64_bundle_hash"],
        "r65_bundle_hash": bundle["bundle_hash"],
        "r65_bundle_file_sha256": file_hash(args.bundle_output),
        "verdict_count": bundle["verdict_count"],
        "passed_verdict_count": bundle["passed_verdict_count"],
        "failed_verdict_count": bundle["failed_verdict_count"],
        "all_replay_semantic_digests_match": bundle["all_replay_semantic_digests_match"],
        "all_replay_commands_exit_zero": bundle["all_replay_commands_exit_zero"],
        "all_replay_file_hashes_match": bundle["all_replay_file_hashes_match"],
        "all_replay_denominator_distances_zero": bundle[
            "all_replay_denominator_distances_zero"
        ],
        "all_replay_negative_controls_rejected": bundle[
            "all_replay_negative_controls_rejected"
        ],
        "all_replay_forbidden_inputs_unused": bundle["all_replay_forbidden_inputs_unused"],
        "c4_c5_same_access_denominator_comparison_complete": bundle[
            "c4_c5_same_access_denominator_comparison_complete"
        ],
        "c6_leakage_free_optimizer_trace_complete": bundle[
            "c6_leakage_free_optimizer_trace_complete"
        ],
        "c7_machine_check_replay_complete": bundle[
            "c7_machine_check_replay_complete"
        ],
        "o3_closed": False,
        "reroute_allowed": False,
        "b7_credit_delta": 0,
        "b7_space_time_volume_credit": 0,
        "resource_saving_claimed": False,
        "b7_ledger_improvement_claimed": False,
        "remaining_open_obligations": ["B7_ledger_retest_after_C7"],
        "remaining_open_obligation_count": 1,
        "requirement_count": len(requirements),
        "requirements_passed": len(requirements) - len(failed),
        "requirements_failed": len(failed),
        "failed_requirement_ids": failed,
        "validation_error_count": len(failed),
    }
    return {
        "title": "B1/B7 Cone01 R65 O3-F4 C7 Machine-Check Replay Gate",
        "version": VERSION,
        "last_updated": "2026-07-08",
        "benchmark_id": "B1",
        "linked_benchmark_id": "B7",
        "method": METHOD,
        "status": STATUS,
        "model_status": MODEL_STATUS,
        "source_target_id": TARGET_ID,
        "upstream_target_id": UPSTREAM_TARGET_ID,
        "r65_c7_machine_check_replay_packet": {
            "source_r63_result": str(args.r63_result),
            "source_r64_result": str(args.r64_result),
            "source_r64_bundle": str(args.r64_bundle),
            "bundle_output": str(args.bundle_output),
            "bundle": bundle,
            "verdicts": verdicts,
        },
        "requirements": requirements,
        "summary": summary,
        "claim_boundary": {
            "what_is_supported": (
                "R65 reruns the same-access denominator verifier for all 8 accepted "
                "R63/R64 rows and confirms stable semantic replay digests, file "
                "hash bindings, zero denominator distances, rejected negative controls, "
                "and no forbidden input usage."
            ),
            "what_is_not_supported": (
                "R65 does not close O3, prove a general circuit optimization theorem, "
                "allow reroute, or grant B7/STV/resource-ledger promotion."
            ),
            "next_gate": "Run a zero-credit B7 ledger retest boundary before any promotion.",
            "resource_saving_claimed": False,
            "b7_ledger_improvement_claimed": False,
        },
        "validation_errors": failed,
        "runtime_seconds": round(time.time() - started, 6),
    }


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    s = payload["summary"]
    lines = [
        "# B1/B7 Cone01 R65 O3-F4 C7 Machine-Check Replay Gate",
        "",
        f"- Target: `{payload['source_target_id']}`",
        f"- Upstream target: `{payload['upstream_target_id']}`",
        f"- Method: `{payload['method']}`",
        f"- Status: `{payload['status']}`",
        f"- R65 bundle hash: `{s['r65_bundle_hash']}`",
        "",
        "## Result",
        "",
        (
            f"R65 passes {s['requirements_passed']}/{s['requirement_count']} "
            "requirements by rerunning the same-access denominator verifier for all "
            "8 accepted R63/R64 rows and comparing stable semantic replay digests. "
            "C7 is now complete for this row set, while O3, reroute, B7, STV, and "
            "resource-ledger promotion remain blocked or 0/false."
        ),
        "",
        "## Evidence",
        "",
        f"- Verdict count: `{s['verdict_count']}`",
        f"- Passed verdicts: `{s['passed_verdict_count']}`",
        f"- Failed verdicts: `{s['failed_verdict_count']}`",
        f"- Replay commands exit zero: `{s['all_replay_commands_exit_zero']}`",
        f"- Semantic digests match: `{s['all_replay_semantic_digests_match']}`",
        f"- File hashes match: `{s['all_replay_file_hashes_match']}`",
        f"- Denominator distances zero: `{s['all_replay_denominator_distances_zero']}`",
        f"- Negative controls rejected: `{s['all_replay_negative_controls_rejected']}`",
        f"- Forbidden inputs unused: `{s['all_replay_forbidden_inputs_unused']}`",
        f"- C4/C5 complete: `{s['c4_c5_same_access_denominator_comparison_complete']}`",
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
        "--r63-result",
        type=Path,
        default=Path(
            "results/B1_B7_cone01_R63_o3_f4_c4_c5_source_backed_denominator_row_acceptance_gate_v0.json"
        ),
    )
    parser.add_argument(
        "--r64-result",
        type=Path,
        default=Path(
            "results/B1_B7_cone01_R64_o3_f4_c6_leakage_free_optimizer_trace_gate_v0.json"
        ),
    )
    parser.add_argument(
        "--r64-bundle",
        type=Path,
        default=Path(
            f"{ROW_DIR}/O3-F4-all8.r64_c6_leakage_free_optimizer_trace_bundle.json"
        ),
    )
    parser.add_argument(
        "--bundle-output",
        type=Path,
        default=Path(f"{ROW_DIR}/O3-F4-all8.r65_c7_machine_check_replay_bundle.json"),
    )
    parser.add_argument(
        "--json-output",
        type=Path,
        default=Path(
            "results/B1_B7_cone01_R65_o3_f4_c7_machine_check_replay_gate_v0.json"
        ),
    )
    parser.add_argument(
        "--markdown-output",
        type=Path,
        default=Path(
            "research/B1_B7_cone01_R65_o3_f4_c7_machine_check_replay_gate.md"
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
                    "verdict_count": s["verdict_count"],
                    "passed_verdict_count": s["passed_verdict_count"],
                    "c7_machine_check_replay_complete": s[
                        "c7_machine_check_replay_complete"
                    ],
                    "o3_closed": s["o3_closed"],
                    "reroute_allowed": s["reroute_allowed"],
                    "b7_credit_delta": s["b7_credit_delta"],
                    "r65_bundle_hash": s["r65_bundle_hash"],
                    "json_output": str(args.json_output),
                },
                indent=2,
                sort_keys=True,
            )
        )


if __name__ == "__main__":
    main()
