#!/usr/bin/env python3
"""T-B1-004dg/T-B7-012p: R5 exit-route priority selector."""

from __future__ import annotations

import argparse
import hashlib
import json
import time
from pathlib import Path
from typing import Any


METHOD = "b1_b7_cone01_r5_exit_route_priority_selector_v0"
STATUS = "cone01_r5_exit_route_priority_selector_ready_zero_credit"
MODEL_STATUS = "r1_selected_as_lowest_burden_exit_route_before_r4_replay"
VERSION = "0.1"
SELECTOR_ID = "B1-B7-cone01-R5-exit-route-priority-selector"

EXPECTED_METHODS = {
    "triage": "b1_b7_cone01_post_boundary_submission_triage_v0",
    "boundary": "b7_b1_cone01_resource_escape_boundary_v0",
    "r1": "b1_b7_cone01_r1_line1381_resolution_packet_gate_v0",
    "r2": "b1_b7_cone01_r2_line1378_overlap_recovery_packet_gate_v0",
    "r3": "b1_b7_cone01_r3_occurrence_certificate_batch_gate_v0",
    "r4": "b1_b7_cone01_r4_b7_ledger_replay_blocked_gate_v0",
}

ROUTE_STATIC = {
    "R1": {
        "packet_id": "B1-B7-cone01-R1-line1381-resolution",
        "task_id": "T-B1-004dc/T-B7-012l",
        "primary_blocker": "line1381 still has five off-grid local-U3 parameters and 100 proxy-T pressure",
        "required_keys": 17,
        "production_required_keys": 9,
        "evidence_file_classes": 8,
        "domain_penalty": 5,
        "route_value": "directly clears the explicit line-1381 blocker named by the seeded resource boundary",
        "first_pr": (
            "Submit a source-backed line1381 resolution manifest with a patch or parameter-elimination "
            "artifact, full replay or symbolic equivalence, physical pricing replay, resource-delta ledger, "
            "no-double-counting ledger, and claim boundary."
        ),
    },
    "R2": {
        "packet_id": "B1-B7-cone01-R2-line1378-overlap-recovery",
        "task_id": "T-B1-004dd/T-B7-012m",
        "primary_blocker": "line1378 overlap delta remains dropped and unrecovered",
        "required_keys": 18,
        "production_required_keys": 9,
        "evidence_file_classes": 9,
        "domain_penalty": 7,
        "route_value": "recovers a dropped overlap delta only if the merged line1378/line1381 region replays cleanly",
        "first_pr": (
            "Submit a merged line1378/line1381 source-bound rewrite artifact with overlap-additivity "
            "evidence, replay or symbolic equivalence, resource ledger, no-double-counting ledger, and "
            "claim boundary."
        ),
    },
    "R3": {
        "packet_id": "B1-B7-cone01-R3-thirty-occurrence-certificates",
        "task_id": "T-B1-004de/T-B7-012n",
        "primary_blocker": "thirty source-backed occurrence-removal certificates are still absent",
        "required_keys": 19,
        "production_required_keys": 12,
        "evidence_file_classes": 10,
        "domain_penalty": 30,
        "route_value": "would clear the B7 30-occurrence / 600 proxy-T threshold if a full certificate batch exists",
        "first_pr": (
            "Submit at least thirty stable occurrence certificates with replay bundle, full-circuit or "
            "local-equivalence replay, resource ledger, B7 ledger replay, no-double-counting ledger, "
            "source-lineage map, failure-mode coverage, and claim boundary."
        ),
    },
}


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


def requirement(requirement_id: str, label: str, passed: bool, evidence: dict[str, Any]) -> dict[str, Any]:
    return {
        "requirement_id": requirement_id,
        "label": label,
        "passed": bool(passed),
        "evidence": evidence,
    }


def route_row(route: str, payload: dict[str, Any]) -> dict[str, Any]:
    summary = payload["summary"]
    static = ROUTE_STATIC[route]
    submitted_key = {
        "R1": "submitted_r1_artifact_exists",
        "R2": "submitted_r2_artifact_exists",
        "R3": "submitted_r3_artifact_exists",
    }[route]
    failed_ids = summary.get("failed_requirement_ids", [])
    effort_score = (
        static["required_keys"]
        + 2 * static["production_required_keys"]
        + 2 * static["evidence_file_classes"]
        + static["domain_penalty"]
        + 10 * int(summary.get("accepted_exit_route_count", 0) == 0)
        + 3 * len(failed_ids)
    )
    return {
        "route": route,
        "task_id": static["task_id"],
        "packet_id": static["packet_id"],
        "method": payload.get("method"),
        "status": payload.get("status"),
        "requirements_passed": summary.get("requirements_passed"),
        "requirements_failed": summary.get("requirements_failed"),
        "failed_requirement_ids": failed_ids,
        "submitted_artifact_exists": summary.get(submitted_key),
        "accepted_exit_route_count": summary.get("accepted_exit_route_count"),
        "accepted_occurrence_removal": summary.get("accepted_occurrence_removal"),
        "accepted_proxy_t_reduction": summary.get("accepted_proxy_t_reduction"),
        "b7_credit_delta": summary.get("b7_credit_delta"),
        "required_keys": static["required_keys"],
        "production_required_keys": static["production_required_keys"],
        "evidence_file_classes": static["evidence_file_classes"],
        "domain_penalty": static["domain_penalty"],
        "effort_score": effort_score,
        "primary_blocker": static["primary_blocker"],
        "route_value": static["route_value"],
        "first_pr": static["first_pr"],
    }


def build_payload(args: argparse.Namespace) -> dict[str, Any]:
    started = time.time()
    triage = load_json(args.post_boundary_triage)
    boundary = load_json(args.b7_resource_boundary)
    r1 = load_json(args.r1_gate)
    r2 = load_json(args.r2_gate)
    r3 = load_json(args.r3_gate)
    r4 = load_json(args.r4_gate)

    triage_summary = triage["summary"]
    boundary_summary = boundary["summary"]
    r4_summary = r4["summary"]

    routes = [route_row("R1", r1), route_row("R2", r2), route_row("R3", r3)]
    ranked_routes = sorted(routes, key=lambda row: (row["effort_score"], row["route"]))
    selected = ranked_routes[0]
    selector_table_hash = stable_hash(ranked_routes)

    accepted_exit_route_count = sum(row["accepted_exit_route_count"] or 0 for row in routes)
    accepted_occurrence_removal = sum(row["accepted_occurrence_removal"] or 0 for row in routes)
    accepted_proxy_t_reduction = sum(row["accepted_proxy_t_reduction"] or 0 for row in routes)
    submitted_route_count = sum(1 for row in routes if row["submitted_artifact_exists"] is True)

    selector_packet = {
        "selector_id": SELECTOR_ID,
        "source_post_boundary_triage": str(args.post_boundary_triage),
        "source_b7_resource_boundary": str(args.b7_resource_boundary),
        "source_r1_gate": str(args.r1_gate),
        "source_r2_gate": str(args.r2_gate),
        "source_r3_gate": str(args.r3_gate),
        "source_r4_gate": str(args.r4_gate),
        "triage_hash": triage_summary.get("triage_hash"),
        "boundary_hash": boundary_summary.get("boundary_hash"),
        "r4_block_packet_hash": r4_summary.get("r4_block_packet_hash"),
        "selector_table_hash": selector_table_hash,
        "ranked_routes": ranked_routes,
        "selected_route": selected["route"],
        "selected_packet_id": selected["packet_id"],
        "selected_next_pr": selected["first_pr"],
        "rejected_for_direct_b7_replay": [
            "accepted_exit_route_count remains 0",
            "accepted_occurrence_removal remains 0",
            "accepted_proxy_t_reduction remains 0",
            "R4 replay is still blocked",
        ],
    }
    selector_packet["selector_hash"] = stable_hash(selector_packet)

    requirements = [
        requirement(
            "S1",
            "Post-boundary triage is current and exposes R1/R2/R3 as ready",
            triage.get("method") == EXPECTED_METHODS["triage"]
            and all(route in triage_summary.get("ready_packet_ids", []) for route in ["R1", "R2", "R3"])
            and triage_summary.get("validation_error_count") == 0,
            {
                "method": triage.get("method"),
                "ready_packet_ids": triage_summary.get("ready_packet_ids"),
                "validation_error_count": triage_summary.get("validation_error_count"),
            },
        ),
        requirement(
            "S2",
            "B7 boundary still has zero credit",
            boundary.get("method") == EXPECTED_METHODS["boundary"]
            and boundary_summary.get("b7_resource_credit_allowed") is False
            and boundary_summary.get("b7_ft_ledger_credit_allowed") is False
            and boundary_summary.get("b7_space_time_volume_credit") == 0,
            {
                "method": boundary.get("method"),
                "b7_resource_credit_allowed": boundary_summary.get("b7_resource_credit_allowed"),
                "b7_ft_ledger_credit_allowed": boundary_summary.get("b7_ft_ledger_credit_allowed"),
                "b7_space_time_volume_credit": boundary_summary.get("b7_space_time_volume_credit"),
            },
        ),
        requirement(
            "S3",
            "R4 replay remains blocked before exit-route acceptance",
            r4.get("method") == EXPECTED_METHODS["r4"]
            and r4_summary.get("r4_replay_allowed") is False
            and r4_summary.get("accepted_exit_route_count") == 0,
            {
                "method": r4.get("method"),
                "r4_replay_allowed": r4_summary.get("r4_replay_allowed"),
                "accepted_exit_route_count": r4_summary.get("accepted_exit_route_count"),
                "r4_block_packet_hash": r4_summary.get("r4_block_packet_hash"),
            },
        ),
        requirement(
            "S4",
            "R1/R2/R3 route gates are all still open on missing artifacts",
            all(row["submitted_artifact_exists"] is False for row in routes)
            and all(row["accepted_exit_route_count"] == 0 for row in routes)
            and all(row["failed_requirement_ids"] == ["P6", "P7", "P8"] for row in routes),
            {
                "routes": [
                    {
                        "route": row["route"],
                        "submitted_artifact_exists": row["submitted_artifact_exists"],
                        "accepted_exit_route_count": row["accepted_exit_route_count"],
                        "failed_requirement_ids": row["failed_requirement_ids"],
                    }
                    for row in routes
                ],
            },
        ),
        requirement(
            "S5",
            "Selector ranks exactly three exit routes",
            [row["route"] for row in ranked_routes] == ["R1", "R2", "R3"]
            and bool(selector_table_hash),
            {
                "ranked_routes": [row["route"] for row in ranked_routes],
                "selector_table_hash": selector_table_hash,
            },
        ),
        requirement(
            "S6",
            "R1 is selected as the lowest-burden next PR",
            selected["route"] == "R1"
            and selected["effort_score"] < ranked_routes[1]["effort_score"],
            {
                "selected_route": selected["route"],
                "selected_effort_score": selected["effort_score"],
                "next_route": ranked_routes[1]["route"],
                "next_effort_score": ranked_routes[1]["effort_score"],
            },
        ),
        requirement(
            "S7",
            "No accepted occurrence or proxy-T delta exists",
            accepted_exit_route_count == 0
            and accepted_occurrence_removal == 0
            and accepted_proxy_t_reduction == 0
            and submitted_route_count == 0,
            {
                "submitted_route_count": submitted_route_count,
                "accepted_exit_route_count": accepted_exit_route_count,
                "accepted_occurrence_removal": accepted_occurrence_removal,
                "accepted_proxy_t_reduction": accepted_proxy_t_reduction,
            },
        ),
        requirement(
            "S8",
            "Forbidden resource claims remain false",
            boundary_summary.get("resource_saving_claimed") is False
            and boundary_summary.get("b7_ledger_improvement_claimed") is False,
            {
                "resource_saving_claimed": boundary_summary.get("resource_saving_claimed"),
                "b7_ledger_improvement_claimed": boundary_summary.get(
                    "b7_ledger_improvement_claimed"
                ),
            },
        ),
    ]

    passed = sum(row["passed"] for row in requirements)
    failed_ids = [row["requirement_id"] for row in requirements if not row["passed"]]
    validation_errors: list[str] = []
    if failed_ids:
        validation_errors.append(f"unexpected R5 selector failures: {failed_ids}")

    summary = {
        "selector_id": SELECTOR_ID,
        "selector_hash": selector_packet["selector_hash"],
        "selector_table_hash": selector_table_hash,
        "triage_hash": triage_summary.get("triage_hash"),
        "boundary_hash": boundary_summary.get("boundary_hash"),
        "r4_block_packet_hash": r4_summary.get("r4_block_packet_hash"),
        "requirement_count": len(requirements),
        "requirements_passed": passed,
        "requirements_failed": len(requirements) - passed,
        "failed_requirement_ids": failed_ids,
        "ranked_route_ids": [row["route"] for row in ranked_routes],
        "selected_route_id": selected["route"],
        "selected_packet_id": selected["packet_id"],
        "selected_effort_score": selected["effort_score"],
        "second_route_id": ranked_routes[1]["route"],
        "second_effort_score": ranked_routes[1]["effort_score"],
        "submitted_route_count": submitted_route_count,
        "accepted_exit_route_count": accepted_exit_route_count,
        "accepted_occurrence_removal": accepted_occurrence_removal,
        "accepted_proxy_t_reduction": accepted_proxy_t_reduction,
        "b7_credit_delta": 0,
        "b7_space_time_volume_credit": 0,
        "r4_replay_allowed": False,
        "resource_saving_claimed": False,
        "b7_ledger_improvement_claimed": False,
        "validation_error_count": len(validation_errors),
    }

    return {
        "benchmark_id": "B1",
        "linked_benchmark_id": "B7",
        "source_target_id": "T-B1-004dg/T-B7-012p",
        "title": "B1/B7 Cone01 R5 Exit-Route Priority Selector",
        "version": VERSION,
        "last_updated": args.last_updated,
        "method": METHOD,
        "status": STATUS,
        "model_status": MODEL_STATUS,
        "source_post_boundary_triage": str(args.post_boundary_triage),
        "source_b7_resource_boundary": str(args.b7_resource_boundary),
        "source_r1_gate": str(args.r1_gate),
        "source_r2_gate": str(args.r2_gate),
        "source_r3_gate": str(args.r3_gate),
        "source_r4_gate": str(args.r4_gate),
        "summary": summary,
        "exit_route_selector_packet": selector_packet,
        "requirements": requirements,
        "claim_boundary": {
            "what_is_supported": (
                "R5 ranks R1 as the lowest-burden next exit-route PR before any R4/B7 ledger replay."
            ),
            "what_is_not_supported": (
                "No R1 artifact, accepted exit route, occurrence removal, proxy-T reduction, B7 ledger "
                "credit, or resource saving is supported."
            ),
            "next_gate": selected["first_pr"],
            "resource_saving_claimed": False,
            "b7_ledger_improvement_claimed": False,
            "r4_replay_allowed": False,
        },
        "validation_errors": validation_errors,
        "runtime_seconds": round(time.time() - started, 6),
    }


def render_markdown(payload: dict[str, Any]) -> str:
    s = payload["summary"]
    packet = payload["exit_route_selector_packet"]
    lines = [
        f"# {payload['title']}",
        "",
        f"- Target: `{payload['source_target_id']}`",
        f"- Method: `{payload['method']}`",
        f"- Status: `{payload['status']}`",
        f"- Selector: `{s['selector_id']}`",
        f"- Selector hash: `{s['selector_hash']}`",
        f"- Selector table hash: `{s['selector_table_hash']}`",
        "",
        "## Result",
        "",
        (
            f"The R5 selector passes {s['requirements_passed']}/{s['requirement_count']} requirements "
            f"and ranks `{s['selected_route_id']}` as the next PR before any refreshed B7 ledger replay."
        ),
        "",
        "## Ranked Routes",
        "",
    ]
    for row in packet["ranked_routes"]:
        lines.extend(
            [
                f"### {row['route']} - {row['packet_id']}",
                "",
                f"- Effort score: `{row['effort_score']}`",
                f"- Status: `{row['status']}`",
                f"- Failed requirements: `{row['failed_requirement_ids']}`",
                f"- Primary blocker: {row['primary_blocker']}",
                f"- Route value: {row['route_value']}",
                f"- First PR: {row['first_pr']}",
                "",
            ]
        )
    lines.extend(["## Requirement Results", ""])
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
            "This selector does not claim resource saving, occurrence removal, proxy-T reduction, B7 ledger improvement, FT resource credit, or a solved B1/B7 problem.",
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
        "--post-boundary-triage",
        type=Path,
        default=Path("results/B1_B7_cone01_post_boundary_submission_triage_v0.json"),
    )
    parser.add_argument(
        "--b7-resource-boundary",
        type=Path,
        default=Path("results/B7_B1_cone01_resource_escape_boundary_v0.json"),
    )
    parser.add_argument(
        "--r1-gate",
        type=Path,
        default=Path("results/B1_B7_cone01_R1_line1381_resolution_packet_gate_v0.json"),
    )
    parser.add_argument(
        "--r2-gate",
        type=Path,
        default=Path("results/B1_B7_cone01_R2_line1378_overlap_recovery_packet_gate_v0.json"),
    )
    parser.add_argument(
        "--r3-gate",
        type=Path,
        default=Path("results/B1_B7_cone01_R3_occurrence_certificate_batch_gate_v0.json"),
    )
    parser.add_argument(
        "--r4-gate",
        type=Path,
        default=Path("results/B1_B7_cone01_R4_b7_ledger_replay_blocked_gate_v0.json"),
    )
    parser.add_argument(
        "--json-output",
        type=Path,
        default=Path("results/B1_B7_cone01_R5_exit_route_priority_selector_v0.json"),
    )
    parser.add_argument(
        "--markdown-output",
        type=Path,
        default=Path("research/B1_B7_cone01_R5_exit_route_priority_selector.md"),
    )
    parser.add_argument("--last-updated", default="2026-07-03")
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
                "selector_hash": payload["summary"]["selector_hash"],
                "selected_route_id": payload["summary"]["selected_route_id"],
                "selected_effort_score": payload["summary"]["selected_effort_score"],
                "requirements_passed": payload["summary"]["requirements_passed"],
                "requirements_failed": payload["summary"]["requirements_failed"],
                "accepted_exit_route_count": payload["summary"]["accepted_exit_route_count"],
                "validation_error_count": payload["summary"]["validation_error_count"],
                "json_output": str(args.json_output),
                "markdown_output": str(args.markdown_output),
            },
            indent=2,
            sort_keys=True,
        )
    )
    if payload["validation_errors"]:
        raise SystemExit("B1/B7 R5 exit-route priority selector validation failed")


if __name__ == "__main__":
    main()
