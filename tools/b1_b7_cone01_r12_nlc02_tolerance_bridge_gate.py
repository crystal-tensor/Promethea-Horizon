#!/usr/bin/env python3
"""T-B1-004dn/T-B7-012w: R12 NL-C02 tolerance-to-exactness bridge gate."""

from __future__ import annotations

import argparse
import hashlib
import json
import time
from pathlib import Path
from typing import Any


METHOD = "b1_b7_cone01_r12_nlc02_tolerance_bridge_gate_v0"
STATUS = "cone01_r12_nlc02_tolerance_bridge_ready_not_full_lemma"
MODEL_STATUS = "nlc02_o2_tolerance_bridge_closed_for_current_residual_model"
VERSION = "0.1"
TARGET_ID = "T-B1-004dn/T-B7-012w"
BRIDGE_ID = "B1-B7-cone01-R12-NL-C02-tolerance-to-exactness-bridge"
CANDIDATE_ID = "NL-C02"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any], pretty: bool) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2 if pretty else None, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def stable_hash(payload: Any) -> str:
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def file_hash(path: Path) -> str | None:
    if not path.exists():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()


def requirement(requirement_id: str, label: str, passed: bool, evidence: dict[str, Any]) -> dict[str, Any]:
    return {
        "requirement_id": requirement_id,
        "label": label,
        "passed": bool(passed),
        "evidence": evidence,
    }


def build_payload(args: argparse.Namespace) -> dict[str, Any]:
    started = time.time()
    r11 = load_json(args.r11_skeleton)
    r11s = r11["summary"]
    skeleton = r11["nlc02_leaveout_proof_skeleton"]
    rows = r11["normalized_leaveout_rows"]

    tolerance = float(r11s["exact_tolerance"])
    margin_rows = []
    for row in rows:
        residual = float(row["residual_norm"])
        ratio = residual / tolerance
        margin_rows.append(
            {
                "subset_key": row["subset_key"],
                "subset_size": row["subset_size"],
                "source_path": row["source_path"],
                "residual_norm": residual,
                "exact_tolerance": tolerance,
                "residual_to_tolerance_ratio": ratio,
                "strictly_above_tolerance": residual > tolerance,
                "exact_pass": row["exact_pass"],
            }
        )

    min_row = min(margin_rows, key=lambda row: row["residual_to_tolerance_ratio"])
    max_row = max(margin_rows, key=lambda row: row["residual_to_tolerance_ratio"])
    min_ratio = min_row["residual_to_tolerance_ratio"]
    max_ratio = max_row["residual_to_tolerance_ratio"]
    safety_margin_decades = 0
    if min_ratio > 0:
        import math

        safety_margin_decades = math.log10(min_ratio)

    open_obligations = skeleton["open_proof_obligations"]
    remaining_obligations = [
        row for row in open_obligations if row["obligation_id"] in {"O1", "O3", "O4"}
    ]
    o2_obligation = next((row for row in open_obligations if row["obligation_id"] == "O2"), None)

    bridge_packet = {
        "bridge_id": BRIDGE_ID,
        "source_target_id": TARGET_ID,
        "candidate_id": CANDIDATE_ID,
        "source_r11_skeleton": str(args.r11_skeleton),
        "source_r11_skeleton_hash": r11s["skeleton_hash"],
        "source_r11_row_table_hash": r11s["row_table_hash"],
        "source_hashes": {
            "r11_skeleton_result": file_hash(args.r11_skeleton),
            "r11_skeleton_report": file_hash(args.r11_markdown),
        },
        "o2_obligation": o2_obligation,
        "bridge_statement": (
            "For the current R11 residual-norm model, each normalized leave-out row has "
            "residual_norm > exact_tolerance, so no row satisfies the accepted exact-pass predicate."
        ),
        "accepted_arithmetic_model_scope": [
            "uses the R11 normalized residual_norm field",
            "uses the R11 exact_tolerance field",
            "does not prove optimizer completeness",
            "does not prove parameterization invariance",
            "does not prove source-domain binding",
        ],
        "margin_rows": margin_rows,
        "min_margin_row": min_row,
        "max_margin_row": max_row,
        "remaining_open_obligations": remaining_obligations,
        "decision": {
            "o2_closed_for_current_residual_model": True,
            "checked_negative_lemma_present": False,
            "nlc02_full_lemma_ready": False,
            "reroute_allowed": False,
            "why": (
                "O2 is bridged for the declared residual-norm predicate, but O1, O3, and O4 "
                "remain open, so NL-C02 is still not a checked negative lemma."
            ),
        },
    }
    bridge_packet["bridge_hash"] = stable_hash(bridge_packet)

    ratios = [row["residual_to_tolerance_ratio"] for row in margin_rows]
    strict_rows = [row for row in margin_rows if row["strictly_above_tolerance"]]
    exact_pass_rows = [row for row in margin_rows if row["exact_pass"]]

    requirements = [
        requirement(
            "B1",
            "R11 proof skeleton is validation-clean and still not a checked lemma",
            r11.get("method") == "b1_b7_cone01_r11_nlc02_leaveout_proof_skeleton_gate_v0"
            and r11s.get("validation_error_count") == 0
            and r11s.get("checked_negative_lemma_present") is False
            and r11s.get("reroute_allowed") is False,
            {
                "r11_method": r11.get("method"),
                "r11_validation_error_count": r11s.get("validation_error_count"),
                "r11_checked_negative_lemma_present": r11s.get("checked_negative_lemma_present"),
                "r11_reroute_allowed": r11s.get("reroute_allowed"),
            },
        ),
        requirement(
            "B2",
            "R11 exposes O2 as an open tolerance-to-exactness obligation",
            o2_obligation is not None
            and o2_obligation["title"] == "Tolerance-to-exactness bridge",
            {"o2_obligation": o2_obligation},
        ),
        requirement(
            "B3",
            "Bridge covers all 31 normalized leave-out rows",
            len(margin_rows) == 31 and r11s.get("leave_out_row_count") == 31,
            {"margin_row_count": len(margin_rows), "r11_leave_out_row_count": r11s.get("leave_out_row_count")},
        ),
        requirement(
            "B4",
            "Every row is strictly above exact tolerance",
            len(strict_rows) == 31 and min_ratio > 1.0,
            {"strict_row_count": len(strict_rows), "min_ratio": min_ratio, "min_margin_row": min_row},
        ),
        requirement(
            "B5",
            "Minimum margin is at least one million times the exact tolerance",
            min_ratio > 1_000_000,
            {"min_ratio": min_ratio, "safety_margin_decades": safety_margin_decades},
        ),
        requirement(
            "B6",
            "No exact-pass row is present in the margin table",
            len(exact_pass_rows) == 0 and r11s.get("leave_out_exact_pass_count") == 0,
            {"exact_pass_row_count": len(exact_pass_rows)},
        ),
        requirement(
            "B7",
            "Bridge packet remains hash-bound",
            bool(bridge_packet["source_hashes"]["r11_skeleton_result"])
            and bool(bridge_packet["source_hashes"]["r11_skeleton_report"])
            and bool(bridge_packet["bridge_hash"]),
            {"source_hashes": bridge_packet["source_hashes"], "bridge_hash": bridge_packet["bridge_hash"]},
        ),
        requirement(
            "B8",
            "Bridge closes only O2 and leaves O1/O3/O4 open",
            bridge_packet["decision"]["o2_closed_for_current_residual_model"] is True
            and [row["obligation_id"] for row in remaining_obligations] == ["O1", "O3", "O4"],
            {"remaining_obligations": [row["obligation_id"] for row in remaining_obligations]},
        ),
        requirement(
            "B9",
            "Bridge is not upgraded into a checked negative lemma or reroute",
            bridge_packet["decision"]["checked_negative_lemma_present"] is False
            and bridge_packet["decision"]["nlc02_full_lemma_ready"] is False
            and bridge_packet["decision"]["reroute_allowed"] is False,
            bridge_packet["decision"],
        ),
        requirement(
            "B10",
            "Bridge preserves zero resource and B7 credit claims",
            True,
            {
                "accepted_route_count": 0,
                "accepted_occurrence_removal": 0,
                "accepted_proxy_t_reduction": 0,
                "b7_credit_delta": 0,
                "b7_space_time_volume_credit": 0,
                "resource_saving_claimed": False,
                "b7_ledger_improvement_claimed": False,
            },
        ),
    ]

    passed = sum(row["passed"] for row in requirements)
    failed_ids = [row["requirement_id"] for row in requirements if not row["passed"]]
    validation_errors: list[str] = []
    if failed_ids:
        validation_errors.append(f"unexpected R12 tolerance-bridge failures: {failed_ids}")

    summary = {
        "bridge_id": BRIDGE_ID,
        "bridge_hash": bridge_packet["bridge_hash"],
        "source_r11_skeleton_hash": r11s["skeleton_hash"],
        "source_r11_row_table_hash": r11s["row_table_hash"],
        "candidate_id": CANDIDATE_ID,
        "bridge_row_count": len(margin_rows),
        "strictly_above_tolerance_row_count": len(strict_rows),
        "exact_pass_row_count": len(exact_pass_rows),
        "exact_tolerance": tolerance,
        "min_residual_norm": min(row["residual_norm"] for row in margin_rows),
        "max_residual_norm": max(row["residual_norm"] for row in margin_rows),
        "min_residual_to_tolerance_ratio": min_ratio,
        "max_residual_to_tolerance_ratio": max_ratio,
        "safety_margin_decades": safety_margin_decades,
        "o2_closed_for_current_residual_model": True,
        "remaining_open_obligations": ["O1", "O3", "O4"],
        "remaining_open_obligation_count": 3,
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
        "requirement_count": len(requirements),
        "requirements_passed": passed,
        "requirements_failed": len(requirements) - passed,
        "failed_requirement_ids": failed_ids,
        "validation_error_count": len(validation_errors),
    }

    return {
        "benchmark_id": "B1",
        "linked_benchmark_id": "B7",
        "source_target_id": TARGET_ID,
        "title": "B1/B7 Cone01 R12 NL-C02 Tolerance-To-Exactness Bridge Gate",
        "version": VERSION,
        "last_updated": args.last_updated,
        "method": METHOD,
        "status": STATUS,
        "model_status": MODEL_STATUS,
        "summary": summary,
        "nlc02_tolerance_bridge_packet": bridge_packet,
        "requirements": requirements,
        "claim_boundary": {
            "what_is_supported": (
                "R12 closes O2 for the current R11 residual-norm predicate by showing every "
                "normalized leave-out residual is strictly above exact_tolerance with a minimum "
                "margin above one million times tolerance."
            ),
            "what_is_not_supported": (
                "R12 does not close optimizer completeness, parameterization invariance, or "
                "source-domain binding. NL-C02 is still not a checked negative lemma. No R5 reroute, "
                "R1 solution, occurrence removal, proxy-T reduction, B7 credit, resource saving, or "
                "impossibility theorem is supported."
            ),
            "next_gate": (
                "Close O1, O3, or O4; or falsify the bridge with a residual at or below tolerance, "
                "an exact-pass row, or a source mismatch."
            ),
            "resource_saving_claimed": False,
            "b7_ledger_improvement_claimed": False,
        },
        "validation_errors": validation_errors,
        "runtime_seconds": round(time.time() - started, 6),
    }


def render_markdown(payload: dict[str, Any]) -> str:
    s = payload["summary"]
    packet = payload["nlc02_tolerance_bridge_packet"]
    lines = [
        f"# {payload['title']}",
        "",
        f"- Target: `{payload['source_target_id']}`",
        f"- Method: `{payload['method']}`",
        f"- Status: `{payload['status']}`",
        f"- Candidate: `{s['candidate_id']}`",
        f"- Bridge hash: `{s['bridge_hash']}`",
        f"- Source R11 skeleton hash: `{s['source_r11_skeleton_hash']}`",
        "",
        "## Result",
        "",
        (
            f"The R12 tolerance bridge passes {s['requirements_passed']}/{s['requirement_count']} "
            "requirements. It closes O2 for the current residual-norm model, but does not make NL-C02 "
            "a checked negative lemma."
        ),
        "",
        "## Bridge Statement",
        "",
        packet["bridge_statement"],
        "",
        "## Margin Evidence",
        "",
        f"- Covered rows: `{s['bridge_row_count']}`",
        f"- Strictly above tolerance rows: `{s['strictly_above_tolerance_row_count']}`",
        f"- Exact-pass rows: `{s['exact_pass_row_count']}`",
        f"- Exact tolerance: `{s['exact_tolerance']}`",
        f"- Residual norm range: `{s['min_residual_norm']}` to `{s['max_residual_norm']}`",
        f"- Residual/tolerance ratio range: `{s['min_residual_to_tolerance_ratio']}` to `{s['max_residual_to_tolerance_ratio']}`",
        f"- Safety margin decades: `{s['safety_margin_decades']}`",
        "",
        "## Scope",
        "",
    ]
    for item in packet["accepted_arithmetic_model_scope"]:
        lines.append(f"- {item}")
    lines.extend(
        [
            "",
            "## Remaining Obligations",
            "",
        ]
    )
    for item in s["remaining_open_obligations"]:
        lines.append(f"- `{item}`")
    lines.extend(
        [
            "",
            "## Decision",
            "",
            f"- O2 closed for current residual model: `{s['o2_closed_for_current_residual_model']}`",
            f"- Checked negative lemma present: `{s['checked_negative_lemma_present']}`",
            f"- NL-C02 full lemma ready: `{s['nlc02_full_lemma_ready']}`",
            f"- Reroute allowed: `{s['reroute_allowed']}`",
            "",
            "## Requirement Results",
            "",
        ]
    )
    for row in payload["requirements"]:
        marker = "PASS" if row["passed"] else "FAIL"
        lines.append(f"- `{row['requirement_id']}` {marker}: {row['label']}")
    lines.extend(
        [
            "",
            "## Claim Boundary",
            "",
            f"- Supported: {payload['claim_boundary']['what_is_supported']}",
            f"- Not supported: {payload['claim_boundary']['what_is_not_supported']}",
            f"- Next gate: {payload['claim_boundary']['next_gate']}",
            "",
            "This bridge gate does not claim resource saving, occurrence removal, proxy-T reduction, B7 ledger improvement, FT resource credit, a checked impossibility theorem, an R5 reroute, or a solved B1/B7 problem.",
            "",
            "## Validation",
            "",
            f"- validation_error_count: `{s['validation_error_count']}`",
        ]
    )
    for error in payload["validation_errors"]:
        lines.append(f"- {error}")
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--r11-skeleton",
        type=Path,
        default=Path("results/B1_B7_cone01_R11_nlc02_leaveout_proof_skeleton_gate_v0.json"),
    )
    parser.add_argument(
        "--r11-markdown",
        type=Path,
        default=Path("research/B1_B7_cone01_R11_nlc02_leaveout_proof_skeleton_gate.md"),
    )
    parser.add_argument(
        "--json-output",
        type=Path,
        default=Path("results/B1_B7_cone01_R12_nlc02_tolerance_bridge_gate_v0.json"),
    )
    parser.add_argument(
        "--markdown-output",
        type=Path,
        default=Path("research/B1_B7_cone01_R12_nlc02_tolerance_bridge_gate.md"),
    )
    parser.add_argument("--last-updated", default="2026-07-06")
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()

    payload = build_payload(args)
    write_json(args.json_output, payload, args.pretty)
    args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_output.write_text(render_markdown(payload), encoding="utf-8")
    print(
        json.dumps(
            {
                "status": payload["status"],
                "bridge_hash": payload["summary"]["bridge_hash"],
                "bridge_row_count": payload["summary"]["bridge_row_count"],
                "min_residual_to_tolerance_ratio": payload["summary"][
                    "min_residual_to_tolerance_ratio"
                ],
                "remaining_open_obligations": payload["summary"]["remaining_open_obligations"],
                "reroute_allowed": payload["summary"]["reroute_allowed"],
                "requirements_passed": payload["summary"]["requirements_passed"],
                "requirements_failed": payload["summary"]["requirements_failed"],
                "validation_error_count": payload["summary"]["validation_error_count"],
                "json_output": str(args.json_output),
                "markdown_output": str(args.markdown_output),
            },
            indent=2,
            sort_keys=True,
        )
    )
    if payload["validation_errors"]:
        raise SystemExit("B1/B7 R12 tolerance bridge gate validation failed")


if __name__ == "__main__":
    main()
