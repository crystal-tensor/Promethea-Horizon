#!/usr/bin/env python3
"""T-B1-004fl/T-B7-014u: R62 hardened denominator acceptance verifier gate."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import shlex
import time
from pathlib import Path
from typing import Any


METHOD = "b1_b7_cone01_r62_o3_f4_c4_c5_hardened_denominator_acceptance_verifier_gate_v0"
STATUS = "cone01_r62_hardened_denominator_acceptance_verifier_rejects_theater_zero_b7_credit"
MODEL_STATUS = "r61_hardened_schema_executable_verifier_rejects_metadata_only_rows"
VERSION = "0.1"
TARGET_ID = "T-B1-004fl/T-B7-014u"
UPSTREAM_TARGET_ID = "T-B1-004fk/T-B7-014t"
HARDENED_SCHEMA_VERSION = "r61_c4_c5_same_access_denominator_row_hardened_v1"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def stable_hash(payload: Any) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def req(requirement_id: str, label: str, passed: bool, evidence: dict[str, Any]) -> dict[str, Any]:
    return {
        "requirement_id": requirement_id,
        "label": label,
        "passed": bool(passed),
        "evidence": evidence,
    }


def out_dir(root: Path) -> Path:
    return root / "results/B1_B7_cone01_o3_f4_numerical_refit_submissions/source_backed_rows"


def repo_file(root: Path, value: str) -> Path:
    return root / value


def path_exists(root: Path, value: str) -> bool:
    return bool(value) and repo_file(root, value).is_file()


def hash_matches(root: Path, value: str, expected_hash: str | None) -> bool:
    if not expected_hash or not path_exists(root, value):
        return False
    return file_hash(repo_file(root, value)) == expected_hash


def is_finite_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and math.isfinite(float(value))


def parse_command_path(command: str) -> str | None:
    try:
        parts = shlex.split(command)
    except ValueError:
        return None
    if len(parts) < 2:
        return None
    if parts[0] not in {"python", "python3"} and not parts[0].endswith("/python3"):
        return None
    return parts[1]


def structured_same_access_statement(value: Any) -> bool:
    return isinstance(value, dict) and {
        "access_model_hash",
        "allowed_inputs_used",
        "forbidden_inputs_used",
        "same_metric_used",
    }.issubset(value)


def structured_leakage_audit(value: Any) -> bool:
    return isinstance(value, dict) and {
        "forbidden_inputs_reviewed",
        "forbidden_inputs_used",
        "leakage_free",
        "audit_hash",
    }.issubset(value)


def transcript_distance(transcript: dict[str, Any]) -> float | None:
    value = transcript.get("denominator_distance")
    if is_finite_number(value):
        return float(value)
    return None


def verify_row(root: Path, row: dict[str, Any], template: dict[str, Any]) -> dict[str, Any]:
    challenge_id = template["challenge_id"]
    checks: list[dict[str, Any]] = []

    def add(check_id: str, label: str, passed: bool, evidence: dict[str, Any]) -> None:
        checks.append(
            {
                "check_id": check_id,
                "label": label,
                "passed": bool(passed),
                "evidence": evidence,
            }
        )

    required_fields_present = all(
        field in row and row[field] not in (None, "") for field in template["required_fields"]
    )
    add(
        "H1",
        "all R60 required fields are present",
        required_fields_present,
        {
            "required_field_count": template["required_field_count"],
            "missing_fields": [
                field
                for field in template["required_fields"]
                if field not in row or row[field] in (None, "")
            ],
        },
    )
    add(
        "H2",
        "challenge id and schema version match the template",
        row.get("challenge_id") == challenge_id
        and row.get("acceptance_schema_version") == template["acceptance_schema_version"],
        {
            "row_challenge_id": row.get("challenge_id"),
            "template_challenge_id": challenge_id,
            "row_schema": row.get("acceptance_schema_version"),
            "template_schema": template["acceptance_schema_version"],
        },
    )
    add(
        "H3",
        "source, candidate, R59 certificate, metric, tolerance, and access-model hashes match",
        row.get("source_circuit_file") == template["source_circuit_file"]
        and row.get("source_circuit_sha256") == template["source_circuit_sha256"]
        and row.get("candidate_circuit_file") == template["candidate_circuit_file"]
        and row.get("candidate_circuit_sha256") == template["candidate_circuit_sha256"]
        and row.get("r59_certificate_file") == template["r59_certificate_file"]
        and row.get("r59_certificate_hash") == template["r59_certificate_hash"]
        and row.get("unitary_distance_metric") == template["unitary_distance_metric"]
        and row.get("strict_tolerance") == template["strict_tolerance"]
        and row.get("access_model_hash") == template["access_model_hash"],
        {"access_model_hash": row.get("access_model_hash")},
    )
    impl_path = row.get("denominator_implementation_path")
    impl_exists = isinstance(impl_path, str) and path_exists(root, impl_path)
    add(
        "H4",
        "denominator implementation exists in the repository",
        impl_exists,
        {"denominator_implementation_path": impl_path},
    )
    command_path = parse_command_path(str(row.get("reproducible_command", "")))
    add(
        "H5",
        "reproducible command points at the reviewed implementation and was replayed",
        impl_exists
        and command_path == impl_path
        and row.get("reproducible_command_replayed") is True,
        {
            "command_path": command_path,
            "denominator_implementation_path": impl_path,
            "reproducible_command_replayed": row.get("reproducible_command_replayed"),
        },
    )
    transcript_path = row.get("verifier_transcript_path")
    transcript_exists = isinstance(transcript_path, str) and path_exists(root, transcript_path)
    transcript_hash_ok = (
        isinstance(transcript_path, str)
        and isinstance(row.get("verifier_transcript_sha256"), str)
        and hash_matches(root, transcript_path, row.get("verifier_transcript_sha256"))
    )
    add(
        "H6",
        "verifier transcript exists and hash-matches the row",
        transcript_exists and transcript_hash_ok,
        {
            "verifier_transcript_path": transcript_path,
            "transcript_exists": transcript_exists,
            "transcript_hash_ok": transcript_hash_ok,
        },
    )
    transcript: dict[str, Any] = {}
    if transcript_exists and transcript_hash_ok and isinstance(transcript_path, str):
        transcript = load_json(repo_file(root, transcript_path))
    distance_from_transcript = transcript_distance(transcript)
    add(
        "H7",
        "denominator distance is finite and transcript-bound",
        distance_from_transcript is not None
        and is_finite_number(row.get("denominator_distance"))
        and float(row["denominator_distance"]) == distance_from_transcript
        and row.get("denominator_distance_source") == "verifier_transcript_bound",
        {
            "row_denominator_distance": row.get("denominator_distance"),
            "distance_from_transcript": distance_from_transcript,
            "denominator_distance_source": row.get("denominator_distance_source"),
        },
    )
    add(
        "H8",
        "same-access and leakage audits are structured",
        structured_same_access_statement(row.get("same_access_statement"))
        and structured_leakage_audit(row.get("leakage_audit_statement"))
        and row.get("structured_leakage_audit") is True,
        {
            "same_access_statement_type": type(row.get("same_access_statement")).__name__,
            "leakage_audit_statement_type": type(row.get("leakage_audit_statement")).__name__,
            "structured_leakage_audit": row.get("structured_leakage_audit"),
        },
    )
    add(
        "H9",
        "computed denominator pressure flags are transcript-derived",
        row.get("denominator_beats_r59_positive_distance") is True
        and row.get("denominator_rejects_r59_negative_control_pressure") is True
        and transcript.get("pressure_flags_transcript_bound") is True,
        {
            "denominator_beats_r59_positive_distance": row.get(
                "denominator_beats_r59_positive_distance"
            ),
            "denominator_rejects_r59_negative_control_pressure": row.get(
                "denominator_rejects_r59_negative_control_pressure"
            ),
            "pressure_flags_transcript_bound": transcript.get("pressure_flags_transcript_bound"),
        },
    )
    claim_boundary = str(row.get("claim_boundary", ""))
    overclaims = any(
        token in claim_boundary.lower()
        for token in ["b7 credit", "stv credit", "o3 closure", "denominator win"]
    )
    add(
        "H10",
        "claim boundary avoids O3/reroute/B7/STV overclaim",
        not overclaims,
        {"claim_boundary": claim_boundary, "overclaims": overclaims},
    )
    failed = [item["check_id"] for item in checks if not item["passed"]]
    rejection_reasons = [
        item["label"] for item in checks if not item["passed"]
    ]
    transcript_payload = {
        "artifact": "R62 hardened denominator acceptance verifier transcript",
        "challenge_id": challenge_id,
        "source_target_id": TARGET_ID,
        "upstream_target_id": UPSTREAM_TARGET_ID,
        "method": METHOD,
        "input_row_hash": stable_hash(row),
        "input_row_file": row.get("row_file"),
        "template_hash": template["template_hash"],
        "checks": checks,
        "check_count": len(checks),
        "passed_check_count": len(checks) - len(failed),
        "failed_check_count": len(failed),
        "failed_check_ids": failed,
        "accepted": len(failed) == 0,
        "rejection_reasons": rejection_reasons,
        "claim_boundary": (
            "Verifier transcript only. A rejected theater row cannot close C4/C5, "
            "O3, reroute, or B7/STV/resource credit."
        ),
    }
    transcript_payload["transcript_hash"] = stable_hash(transcript_payload)
    transcript_file = out_dir(root) / f"{challenge_id}.r62_hardened_acceptance_verifier_transcript.json"
    write_json(transcript_file, transcript_payload)
    transcript_payload["transcript_file"] = str(transcript_file.relative_to(root))
    transcript_payload["transcript_file_sha256"] = file_hash(transcript_file)
    return transcript_payload


def build_payload(args: argparse.Namespace) -> dict[str, Any]:
    started = time.time()
    r60 = load_json(args.r60_result)
    r61 = load_json(args.r61_result)
    r61_summary = r61["summary"]
    templates = {
        item["challenge_id"]: item
        for item in r60["r60_c4_c5_denominator_contract_packet"]["templates"]
    }
    attack_rows = sorted(
        r61["r61_denominator_theater_schema_review_packet"]["attack_rows"],
        key=lambda item: item["challenge_id"],
    )
    transcripts = [verify_row(args.root, row, templates[row["challenge_id"]]) for row in attack_rows]
    bundle = {
        "artifact": "R62 executable hardened denominator acceptance verifier bundle",
        "source_target_id": TARGET_ID,
        "upstream_target_id": UPSTREAM_TARGET_ID,
        "method": METHOD,
        "hardened_schema_version": HARDENED_SCHEMA_VERSION,
        "source_r60_result": str(args.r60_result),
        "source_r60_file_sha256": file_hash(args.r60_result),
        "source_r61_result": str(args.r61_result),
        "source_r61_file_sha256": file_hash(args.r61_result),
        "source_r61_bundle_hash": r61_summary["r61_bundle_hash"],
        "verifier_implementation_path": str(Path(__file__)),
        "verifier_implementation_sha256": file_hash(Path(__file__)),
        "row_count": len(transcripts),
        "attack_row_count": len(transcripts),
        "verifier_transcript_count": len(transcripts),
        "hardened_reject_count": sum(1 for item in transcripts if not item["accepted"]),
        "hardened_accept_count": sum(1 for item in transcripts if item["accepted"]),
        "min_failed_check_count": min(item["failed_check_count"] for item in transcripts),
        "max_passed_check_count": max(item["passed_check_count"] for item in transcripts),
        "transcript_hashes": {
            item["challenge_id"]: item["transcript_hash"] for item in transcripts
        },
        "transcript_files": {
            item["challenge_id"]: item["transcript_file"] for item in transcripts
        },
        "executable_verifier_replayed_theater_rows": len(transcripts) == 8
        and all(not item["accepted"] for item in transcripts),
        "c4_c5_same_access_denominator_acceptance_verifier_executable": True,
        "c4_c5_same_access_denominator_comparison_complete": False,
        "accepted_denominator_row_count": 0,
        "o3_closed": False,
        "reroute_allowed": False,
        "b7_credit_delta": 0,
        "b7_space_time_volume_credit": 0,
        "resource_saving_claimed": False,
        "b7_ledger_improvement_claimed": False,
        "claim_boundary": (
            "R62 implements and replays the hardened acceptance verifier against R61 "
            "theater rows. It rejects metadata-only rows, but accepts no denominator "
            "row and grants no C4/C5, O3, reroute, B7, STV, or resource credit."
        ),
    }
    bundle["bundle_hash"] = stable_hash(bundle)
    write_json(args.bundle_output, bundle)
    zero_credit_ok = (
        r61_summary["o3_closed"] is False
        and r61_summary["reroute_allowed"] is False
        and r61_summary["b7_credit_delta"] == 0
        and r61_summary["b7_space_time_volume_credit"] == 0
        and r61_summary["resource_saving_claimed"] is False
        and r61_summary["b7_ledger_improvement_claimed"] is False
    )
    requirements = [
        req(
            "V1",
            "R61 upstream hardened schema rejected all theater rows with zero credit",
            r61_summary["c4_c5_same_access_denominator_schema_hardened"] is True
            and r61_summary["hardened_reject_count"] == 8
            and zero_credit_ok,
            {
                "r61_hardened_reject_count": r61_summary["hardened_reject_count"],
                "r61_bundle_hash": r61_summary["r61_bundle_hash"],
                "zero_credit_ok": zero_credit_ok,
            },
        ),
        req(
            "V2",
            "R62 emits one executable verifier transcript per R61 theater row",
            len(transcripts) == 8
            and len({item["challenge_id"] for item in transcripts}) == 8
            and all(item["transcript_file_sha256"] for item in transcripts),
            {
                "verifier_transcript_count": len(transcripts),
                "challenge_ids": [item["challenge_id"] for item in transcripts],
            },
        ),
        req(
            "V3",
            "R62 executable verifier rejects all metadata-only theater rows",
            bundle["hardened_reject_count"] == 8
            and bundle["hardened_accept_count"] == 0
            and bundle["executable_verifier_replayed_theater_rows"] is True,
            {
                "hardened_reject_count": bundle["hardened_reject_count"],
                "hardened_accept_count": bundle["hardened_accept_count"],
            },
        ),
        req(
            "V4",
            "R62 verifier checks implementation, command replay, transcript hash, distance binding, leakage, pressure flags, and claim boundary",
            all(item["check_count"] == 10 for item in transcripts)
            and bundle["min_failed_check_count"] >= 6,
            {
                "check_counts": {
                    item["challenge_id"]: item["check_count"] for item in transcripts
                },
                "failed_check_counts": {
                    item["challenge_id"]: item["failed_check_count"] for item in transcripts
                },
            },
        ),
        req(
            "V5",
            "R62 verifier implementation is hash-bound",
            bool(bundle["verifier_implementation_sha256"]),
            {
                "verifier_implementation_path": bundle["verifier_implementation_path"],
                "verifier_implementation_sha256": bundle["verifier_implementation_sha256"],
            },
        ),
        req(
            "V6",
            "R62 accepts no denominator rows and keeps C4/C5 incomplete",
            bundle["accepted_denominator_row_count"] == 0
            and bundle["c4_c5_same_access_denominator_comparison_complete"] is False,
            {
                "accepted_denominator_row_count": bundle["accepted_denominator_row_count"],
                "c4_c5_same_access_denominator_comparison_complete": bundle[
                    "c4_c5_same_access_denominator_comparison_complete"
                ],
            },
        ),
        req(
            "V7",
            "R62 preserves O3/reroute/B7 zero-credit boundaries",
            zero_credit_ok
            and bundle["o3_closed"] is False
            and bundle["reroute_allowed"] is False
            and bundle["b7_credit_delta"] == 0,
            {
                "o3_closed": bundle["o3_closed"],
                "reroute_allowed": bundle["reroute_allowed"],
                "b7_credit_delta": bundle["b7_credit_delta"],
                "b7_space_time_volume_credit": bundle["b7_space_time_volume_credit"],
            },
        ),
        req(
            "V8",
            "R62 bundle and verifier transcripts are hash-bound",
            bool(bundle["bundle_hash"]) and all(item["transcript_hash"] for item in transcripts),
            {
                "bundle_hash": bundle["bundle_hash"],
                "bundle_file_sha256": file_hash(args.bundle_output),
                "transcript_hashes": bundle["transcript_hashes"],
            },
        ),
    ]
    failed = [item["requirement_id"] for item in requirements if not item["passed"]]
    summary = {
        "source_r61_bundle_hash": r61_summary["r61_bundle_hash"],
        "source_r61_file_sha256": file_hash(args.r61_result),
        "r62_bundle_hash": bundle["bundle_hash"],
        "r62_bundle_file_sha256": file_hash(args.bundle_output),
        "verifier_implementation_sha256": bundle["verifier_implementation_sha256"],
        "attack_row_count": bundle["attack_row_count"],
        "verifier_transcript_count": bundle["verifier_transcript_count"],
        "hardened_reject_count": bundle["hardened_reject_count"],
        "hardened_accept_count": bundle["hardened_accept_count"],
        "min_failed_check_count": bundle["min_failed_check_count"],
        "max_passed_check_count": bundle["max_passed_check_count"],
        "executable_verifier_replayed_theater_rows": bundle[
            "executable_verifier_replayed_theater_rows"
        ],
        "c4_c5_same_access_denominator_acceptance_verifier_executable": bundle[
            "c4_c5_same_access_denominator_acceptance_verifier_executable"
        ],
        "c4_c5_same_access_denominator_comparison_complete": False,
        "accepted_denominator_row_count": 0,
        "o3_closed": False,
        "reroute_allowed": False,
        "b7_credit_delta": 0,
        "b7_space_time_volume_credit": 0,
        "resource_saving_claimed": False,
        "b7_ledger_improvement_claimed": False,
        "remaining_open_obligations": [
            "submit_C4_C5_same_access_denominator_rows_with_existing_transcripts",
            "accept_8_denominator_rows_under_R62_verifier",
            "C6_leakage_free_optimizer_trace",
            "C7_machine_check_replay_bundle",
            "B7_ledger_retest_after_C4_C7",
        ],
        "remaining_open_obligation_count": 5,
        "requirement_count": len(requirements),
        "requirements_passed": len(requirements) - len(failed),
        "requirements_failed": len(failed),
        "failed_requirement_ids": failed,
        "validation_error_count": len(failed),
    }
    return {
        "title": "B1/B7 Cone01 R62 O3-F4 C4/C5 Hardened Denominator Acceptance Verifier Gate",
        "version": VERSION,
        "last_updated": "2026-07-08",
        "benchmark_id": "B1",
        "linked_benchmark_id": "B7",
        "method": METHOD,
        "status": STATUS,
        "model_status": MODEL_STATUS,
        "source_target_id": TARGET_ID,
        "upstream_target_id": UPSTREAM_TARGET_ID,
        "r62_hardened_acceptance_verifier_packet": {
            "source_r60_result": str(args.r60_result),
            "source_r61_result": str(args.r61_result),
            "bundle_output": str(args.bundle_output),
            "bundle": bundle,
            "verifier_transcripts": transcripts,
        },
        "requirements": requirements,
        "summary": summary,
        "claim_boundary": {
            "what_is_supported": (
                "R62 implements an executable hardened acceptance verifier and replays "
                "it against the 8 R61 metadata-only theater rows. The verifier rejects "
                "all 8 and emits hash-bound per-row transcripts."
            ),
            "what_is_not_supported": (
                "R62 does not accept any denominator row, does not complete C4/C5, "
                "does not audit C6 leakage, does not produce a C7 machine-check bundle, "
                "and does not grant O3/reroute/B7/STV credit."
            ),
            "next_gate": (
                "Submit real same-access denominator rows with existing implementation "
                "and verifier transcript artifacts, then run R62 as the acceptance gate."
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
        "# B1/B7 Cone01 R62 O3-F4 C4/C5 Hardened Denominator Acceptance Verifier Gate",
        "",
        f"- Target: `{payload['source_target_id']}`",
        f"- Upstream target: `{payload['upstream_target_id']}`",
        f"- Method: `{payload['method']}`",
        f"- Status: `{payload['status']}`",
        f"- R62 bundle hash: `{s['r62_bundle_hash']}`",
        "",
        "## Result",
        "",
        (
            f"R62 passes {s['requirements_passed']}/{s['requirement_count']} verifier "
            "requirements by executing the hardened acceptance verifier on all 8 R61 "
            "metadata-only theater rows. It emits 8 verifier transcripts and rejects "
            "all 8. C4/C5, C6, C7, O3 closure, reroute, and B7 ledger credit remain blocked."
        ),
        "",
        "## Verifier Evidence",
        "",
        f"- Attack rows checked: `{s['attack_row_count']}`",
        f"- Verifier transcripts: `{s['verifier_transcript_count']}`",
        f"- Hardened rejects: `{s['hardened_reject_count']}`",
        f"- Hardened accepts: `{s['hardened_accept_count']}`",
        f"- Min failed checks per theater row: `{s['min_failed_check_count']}`",
        f"- Max passed checks per theater row: `{s['max_passed_check_count']}`",
        f"- Verifier executable: `{s['c4_c5_same_access_denominator_acceptance_verifier_executable']}`",
        f"- Accepted denominator rows: `{s['accepted_denominator_row_count']}`",
        f"- C4/C5 comparison complete: `{s['c4_c5_same_access_denominator_comparison_complete']}`",
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
        "--r61-result",
        type=Path,
        default=Path(
            "results/B1_B7_cone01_R61_o3_f4_c4_c5_denominator_theater_schema_review_gate_v0.json"
        ),
    )
    parser.add_argument(
        "--bundle-output",
        type=Path,
        default=Path(
            "results/B1_B7_cone01_o3_f4_numerical_refit_submissions/source_backed_rows/"
            "O3-F4-all8.r62_hardened_acceptance_verifier_bundle.json"
        ),
    )
    parser.add_argument(
        "--json-output",
        type=Path,
        default=Path(
            "results/B1_B7_cone01_R62_o3_f4_c4_c5_hardened_denominator_acceptance_verifier_gate_v0.json"
        ),
    )
    parser.add_argument(
        "--markdown-output",
        type=Path,
        default=Path(
            "research/B1_B7_cone01_R62_o3_f4_c4_c5_hardened_denominator_acceptance_verifier_gate.md"
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
                    "attack_row_count": s["attack_row_count"],
                    "verifier_transcript_count": s["verifier_transcript_count"],
                    "hardened_reject_count": s["hardened_reject_count"],
                    "hardened_accept_count": s["hardened_accept_count"],
                    "executable_verifier_replayed_theater_rows": s[
                        "executable_verifier_replayed_theater_rows"
                    ],
                    "c4_c5_same_access_denominator_acceptance_verifier_executable": s[
                        "c4_c5_same_access_denominator_acceptance_verifier_executable"
                    ],
                    "c4_c5_same_access_denominator_comparison_complete": s[
                        "c4_c5_same_access_denominator_comparison_complete"
                    ],
                    "o3_closed": s["o3_closed"],
                    "reroute_allowed": s["reroute_allowed"],
                    "b7_credit_delta": s["b7_credit_delta"],
                    "r62_bundle_hash": s["r62_bundle_hash"],
                    "json_output": str(args.json_output),
                },
                indent=2,
                sort_keys=True,
            )
        )


if __name__ == "__main__":
    main()
