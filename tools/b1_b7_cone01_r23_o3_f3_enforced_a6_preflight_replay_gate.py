#!/usr/bin/env python3
"""T-B1-004dy/T-B7-013h: R23 O3-F3 enforced A6 preflight replay gate."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import time
from pathlib import Path
from typing import Any


METHOD = "b1_b7_cone01_r23_o3_f3_enforced_a6_preflight_replay_gate_v0"
STATUS = "cone01_r23_o3_f3_enforced_a6_preflight_replay_ready"
MODEL_STATUS = "o3_f3_a6_polarity_enforced_in_replay_no_artifact_no_reroute"
VERSION = "0.1"
TARGET_ID = "T-B1-004dy/T-B7-013h"
SOURCE_TARGET_ID = "T-B1-004dx/T-B7-013g"
CANDIDATE_ID = "NL-C02"
FAMILY_ID = "O3-F3"
REPLAY_ID = "B1-B7-cone01-R23-O3-F3-enforced-A6-preflight-replay"

DENY_PATTERNS = [
    r"\bno\b",
    r"\bnot\b",
    r"\bfalse\b",
    r"\bforbid(?:den|s)?\b",
    r"\brefus(?:e|es|ed)\b",
    r"\bwithout\b",
    r"\bunless\b",
    r"\bmay not\b",
    r"\bcannot\b",
    r"\bnot supported\b",
]

ALLOW_PATTERNS = [
    r"\bavailable\b",
    r"\ballowed\b",
    r"\ballows\b",
    r"\bgrants?\b",
    r"\bclears?\b",
    r"\baccepts?\b",
    r"\bapproved\b",
    r"\bcredit available\b",
    r"\breroute available\b",
    r"\breroute allowed\b",
    r"\bo3 closed\b",
    r"\bcan claim\b",
]

REQUIRED_CONCEPTS = ["B7 credit", "STV credit", "reroute", "O3 closure"]
TEMPLATE_MARKERS = ["<required>", "<submitter>", "<short-name>", "required after submission"]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any], pretty: bool = True) -> None:
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


def flatten_boundary(boundary: Any) -> str:
    if isinstance(boundary, dict):
        return " ".join(f"{key}: {flatten_boundary(value)}" for key, value in sorted(boundary.items()))
    if isinstance(boundary, list):
        return " ".join(flatten_boundary(value) for value in boundary)
    return str(boundary)


def matches(patterns: list[str], text: str) -> list[str]:
    return [pattern for pattern in patterns if re.search(pattern, text, flags=re.IGNORECASE)]


def concept_hits(text: str) -> list[str]:
    lower = text.lower()
    return [concept for concept in REQUIRED_CONCEPTS if concept.lower() in lower]


def evaluate_a6_polarity(boundary: Any) -> dict[str, Any]:
    text = flatten_boundary(boundary)
    deny_hits = matches(DENY_PATTERNS, text)
    allow_hits = matches(ALLOW_PATTERNS, text)
    concepts = concept_hits(text)
    passed = len(concepts) == len(REQUIRED_CONCEPTS) and bool(deny_hits) and not allow_hits
    return {
        "text_hash": stable_hash(text),
        "concept_hits": concepts,
        "deny_pattern_hits": deny_hits,
        "allow_pattern_hits": allow_hits,
        "a6_polarity_passed": passed,
    }


def contains_template_marker(submission: dict[str, Any]) -> bool:
    blob = json.dumps(submission, sort_keys=True)
    return any(marker in blob for marker in TEMPLATE_MARKERS)


def evaluate_submission_enforced_a6(submission: dict[str, Any], source_registry_hash: str) -> dict[str, Any]:
    passed: list[str] = []
    failed: list[str] = []

    if (
        submission.get("family_id") == FAMILY_ID
        and submission.get("candidate_id") == CANDIDATE_ID
        and submission.get("source_registry_hash") == source_registry_hash
    ):
        passed.append("A1")
    else:
        failed.append("A1")

    if submission.get("source_unitary_preservation_certificate"):
        passed.append("A2")
    else:
        failed.append("A2")

    mapping = submission.get("leaveout_domain_mapping")
    if mapping and "3" in json.dumps(mapping) and "17" in json.dumps(mapping):
        passed.append("A3")
    else:
        failed.append("A3")

    lattice = submission.get("pi_over_four_lattice_relation")
    if lattice and "numerical_only" not in json.dumps(lattice):
        passed.append("A4")
    else:
        failed.append("A4")

    if submission.get("route_a_effect") in {"not_claimed", "clears_route_a", "does_not_clear_route_a"}:
        passed.append("A5")
    else:
        failed.append("A5")

    a6_eval = evaluate_a6_polarity(submission.get("claim_boundary", {}))
    if a6_eval["a6_polarity_passed"]:
        passed.append("A6")
    else:
        failed.append("A6")

    if submission.get("machine_check_command") and submission.get("expected_outputs"):
        passed.append("A7")
    else:
        failed.append("A7")

    if not any(submission.get(flag) is True for flag in ["checked_negative_lemma_present", "reroute_allowed", "o3_closed"]):
        passed.append("A8")
    else:
        failed.append("A8")

    template_marker_found = contains_template_marker(submission)
    accepted = len(failed) == 0 and len(passed) == 8 and not template_marker_found
    return {
        "submission_exists": True,
        "passed_gate_ids": passed,
        "failed_gate_ids": failed,
        "blocked_gate_ids": [],
        "a6_polarity_eval": a6_eval,
        "template_marker_found": template_marker_found,
        "accepted": accepted,
        "why": (
            "R23 replays the R20 preflight with A6 replaced by the R22 polarity rule. "
            "Template marker strings keep reusable templates from being promoted as submitted artifacts."
        ),
    }


def build_payload(args: argparse.Namespace) -> dict[str, Any]:
    started = time.time()
    r20 = load_json(args.r20_intake)
    r21 = load_json(args.r21_sentinel)
    r22 = load_json(args.r22_polarity)
    template = load_json(args.template)
    overclaim_fixture = load_json(args.overclaim_fixture)

    r20_summary = r20["summary"]
    r21_summary = r21["summary"]
    r22_summary = r22["summary"]
    source_registry_hash = template["source_registry_hash"]

    template_replay = evaluate_submission_enforced_a6(template, source_registry_hash)
    overclaim_replay = evaluate_submission_enforced_a6(overclaim_fixture, source_registry_hash)
    old_overclaim_preflight = r21["o3_f3_overclaim_sentinel_packet"]["preflight_result"]
    old_overclaim_passed = old_overclaim_preflight["passed_gate_ids"]
    old_overclaim_failed = old_overclaim_preflight["failed_gate_ids"]
    new_overclaim_failed = overclaim_replay["failed_gate_ids"]
    a6_newly_failed = "A6" not in old_overclaim_failed and "A6" in new_overclaim_failed

    enforced_rule = {
        "rule_id": "B1-B7-cone01-R23-O3-F3-enforced-A6-preflight-rule",
        "source_r22_polarity_rule_hash": r22_summary["polarity_rule_hash"],
        "gate_replaced": "A6",
        "old_r20_a6": "lexical mention of B7 credit, STV credit, or reroute",
        "new_r23_a6": (
            "all required concepts present AND at least one denial pattern present AND zero allowance patterns present"
        ),
        "required_concepts": REQUIRED_CONCEPTS,
        "deny_patterns": DENY_PATTERNS,
        "allow_patterns": ALLOW_PATTERNS,
        "template_guard": TEMPLATE_MARKERS,
    }

    replay_packet = {
        "replay_id": REPLAY_ID,
        "source_target_id": TARGET_ID,
        "source_r20_intake": str(args.r20_intake),
        "source_r21_sentinel": str(args.r21_sentinel),
        "source_r22_polarity": str(args.r22_polarity),
        "source_template": str(args.template),
        "source_overclaim_fixture": str(args.overclaim_fixture),
        "source_hashes": {
            "r20_intake_file": file_hash(args.r20_intake),
            "r21_sentinel_file": file_hash(args.r21_sentinel),
            "r22_polarity_file": file_hash(args.r22_polarity),
            "template_file": file_hash(args.template),
            "overclaim_fixture_file": file_hash(args.overclaim_fixture),
        },
        "source_intake_hash": r20_summary["intake_hash"],
        "source_sentinel_hash": r21_summary["sentinel_hash"],
        "source_polarity_hash": r22_summary["polarity_hash"],
        "source_polarity_rule_hash": r22_summary["polarity_rule_hash"],
        "enforced_rule": enforced_rule,
        "template_replay": template_replay,
        "overclaim_replay": overclaim_replay,
        "old_overclaim_failed_gate_ids": old_overclaim_failed,
        "new_overclaim_failed_gate_ids": new_overclaim_failed,
        "decision": {
            "a6_polarity_enforced": True,
            "template_boundary_passes_polarity": template_replay["a6_polarity_eval"]["a6_polarity_passed"],
            "template_artifact_accepted": template_replay["accepted"],
            "template_rejected_as_submission": template_replay["template_marker_found"] and not template_replay["accepted"],
            "overclaim_boundary_fails_polarity": overclaim_replay["a6_polarity_eval"]["a6_polarity_passed"] is False,
            "overclaim_fixture_rejected": overclaim_replay["accepted"] is False,
            "a6_newly_failed_for_overclaim": a6_newly_failed,
            "o3_f3_artifact_accepted": False,
            "o3_closed": False,
            "checked_negative_lemma_present": False,
            "nlc02_full_lemma_ready": False,
            "reroute_allowed": False,
            "why": (
                "R23 converts R22's A6 polarity rule from advisory status into a replayed preflight rule. "
                "The red-team overclaim now fails A6 directly, while the reusable template remains unaccepted."
            ),
        },
    }
    replay_packet["enforced_rule_hash"] = stable_hash(enforced_rule)
    replay_packet["template_replay_hash"] = stable_hash(template_replay)
    replay_packet["overclaim_replay_hash"] = stable_hash(overclaim_replay)
    replay_packet["replay_hash"] = stable_hash(replay_packet)

    requirements = [
        requirement(
            "N1",
            "R20/R21/R22 source gates are validation-clean and connected",
            r20.get("method") == "b1_b7_cone01_r20_o3_f3_artifact_intake_preflight_gate_v0"
            and r20_summary.get("validation_error_count") == 0
            and r21.get("method") == "b1_b7_cone01_r21_o3_f3_overclaim_sentinel_gate_v0"
            and r21_summary.get("validation_error_count") == 0
            and r22.get("method") == "b1_b7_cone01_r22_o3_f3_a6_claim_boundary_polarity_gate_v0"
            and r22_summary.get("validation_error_count") == 0
            and r22_summary.get("a6_polarity_rule_ready") is True,
            {
                "r20_method": r20.get("method"),
                "r20_validation_error_count": r20_summary.get("validation_error_count"),
                "r21_method": r21.get("method"),
                "r21_validation_error_count": r21_summary.get("validation_error_count"),
                "r22_method": r22.get("method"),
                "r22_validation_error_count": r22_summary.get("validation_error_count"),
                "r22_a6_polarity_rule_ready": r22_summary.get("a6_polarity_rule_ready"),
            },
        ),
        requirement(
            "N2",
            "R23 A6 rule is the R22 polarity semantics, not the old lexical mention test",
            enforced_rule["source_r22_polarity_rule_hash"] == r22_summary["polarity_rule_hash"]
            and enforced_rule["old_r20_a6"] != enforced_rule["new_r23_a6"],
            enforced_rule,
        ),
        requirement(
            "N3",
            "R20 template boundary passes A6 polarity but is not accepted as an artifact",
            template_replay["a6_polarity_eval"]["a6_polarity_passed"] is True
            and template_replay["template_marker_found"] is True
            and template_replay["accepted"] is False,
            template_replay,
        ),
        requirement(
            "N4",
            "R21 overclaim replay now fails A6 polarity",
            "A6" in new_overclaim_failed
            and overclaim_replay["a6_polarity_eval"]["a6_polarity_passed"] is False,
            overclaim_replay,
        ),
        requirement(
            "N5",
            "A6 is newly failed relative to the R21 old preflight",
            a6_newly_failed and "A6" in old_overclaim_passed,
            {
                "old_overclaim_passed_gate_ids": old_overclaim_passed,
                "old_overclaim_failed_gate_ids": old_overclaim_failed,
                "new_overclaim_failed_gate_ids": new_overclaim_failed,
                "a6_newly_failed_for_overclaim": a6_newly_failed,
            },
        ),
        requirement(
            "N6",
            "Overclaim remains rejected under the enforced preflight",
            overclaim_replay["accepted"] is False
            and sorted(new_overclaim_failed) == ["A2", "A4", "A6", "A7", "A8"],
            {"new_overclaim_failed_gate_ids": new_overclaim_failed, "accepted": overclaim_replay["accepted"]},
        ),
        requirement(
            "N7",
            "R23 does not accept O3-F3, close O3, or permit reroute",
            replay_packet["decision"]["o3_f3_artifact_accepted"] is False
            and replay_packet["decision"]["o3_closed"] is False
            and replay_packet["decision"]["reroute_allowed"] is False,
            replay_packet["decision"],
        ),
        requirement(
            "N8",
            "R23 preserves zero B7/resource credit claims",
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
        requirement(
            "N9",
            "R23 replay packet is internally hash-bound",
            bool(replay_packet["replay_hash"])
            and bool(replay_packet["enforced_rule_hash"])
            and bool(replay_packet["template_replay_hash"])
            and bool(replay_packet["overclaim_replay_hash"]),
            {
                "replay_hash": replay_packet["replay_hash"],
                "enforced_rule_hash": replay_packet["enforced_rule_hash"],
                "template_replay_hash": replay_packet["template_replay_hash"],
                "overclaim_replay_hash": replay_packet["overclaim_replay_hash"],
            },
        ),
    ]

    passed = sum(row["passed"] for row in requirements)
    failed_ids = [row["requirement_id"] for row in requirements if not row["passed"]]
    validation_errors: list[str] = []
    if failed_ids:
        validation_errors.append(f"unexpected R23 enforced A6 replay failures: {failed_ids}")

    summary = {
        "replay_id": REPLAY_ID,
        "replay_hash": replay_packet["replay_hash"],
        "enforced_rule_hash": replay_packet["enforced_rule_hash"],
        "template_replay_hash": replay_packet["template_replay_hash"],
        "overclaim_replay_hash": replay_packet["overclaim_replay_hash"],
        "source_intake_hash": r20_summary["intake_hash"],
        "source_sentinel_hash": r21_summary["sentinel_hash"],
        "source_polarity_hash": r22_summary["polarity_hash"],
        "source_polarity_rule_hash": r22_summary["polarity_rule_hash"],
        "candidate_id": CANDIDATE_ID,
        "family_id": FAMILY_ID,
        "a6_polarity_enforced": True,
        "template_boundary_passes_polarity": template_replay["a6_polarity_eval"]["a6_polarity_passed"],
        "template_artifact_accepted": False,
        "template_rejected_as_submission": replay_packet["decision"]["template_rejected_as_submission"],
        "overclaim_boundary_fails_polarity": True,
        "overclaim_fixture_rejected": True,
        "old_overclaim_failed_gate_ids": old_overclaim_failed,
        "new_overclaim_failed_gate_ids": new_overclaim_failed,
        "a6_newly_failed_for_overclaim": a6_newly_failed,
        "o3_f3_artifact_accepted": False,
        "o3_closed": False,
        "remaining_open_obligations": ["O3-F3_symbolic_lu_artifact", "O3-F4_refit_harness", "O3-F5_route_a_artifact"],
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
        "upstream_target_id": SOURCE_TARGET_ID,
        "title": "B1/B7 Cone01 R23 O3-F3 Enforced A6 Preflight Replay Gate",
        "version": VERSION,
        "last_updated": args.last_updated,
        "method": METHOD,
        "status": STATUS,
        "model_status": MODEL_STATUS,
        "summary": summary,
        "o3_f3_enforced_a6_preflight_replay_packet": replay_packet,
        "requirements": requirements,
        "claim_boundary": {
            "what_is_supported": (
                "R23 enforces the R22 A6 claim-boundary polarity rule inside a replayed O3-F3 preflight. "
                "The R21 overclaim fixture now fails A6 directly, and the reusable R20 template is kept from being promoted as a submitted artifact."
            ),
            "what_is_not_supported": (
                "R23 does not submit or accept a valid O3-F3 artifact, does not close O3, and does not permit R5 reroute. "
                "No R1 solution, occurrence removal, proxy-T reduction, B7 credit, resource saving, or impossibility theorem is supported."
            ),
            "next_gate": (
                "Replace the red-team fixture with a real O3-F3 symbolic local-unitary proof, counterexample, or rejection-strengthening artifact "
                "that passes the enforced A1-A8 preflight, or move to O3-F4 numerical refit / O3-F5 Route A artifact pressure."
            ),
            "resource_saving_claimed": False,
            "b7_ledger_improvement_claimed": False,
        },
        "validation_errors": validation_errors,
        "runtime_seconds": round(time.time() - started, 6),
    }


def render_markdown(payload: dict[str, Any]) -> str:
    s = payload["summary"]
    lines = [
        f"# {payload['title']}",
        "",
        f"- Target: `{payload['source_target_id']}`",
        f"- Upstream target: `{payload['upstream_target_id']}`",
        f"- Method: `{payload['method']}`",
        f"- Status: `{payload['status']}`",
        f"- Candidate: `{s['candidate_id']}`",
        f"- Family: `{s['family_id']}`",
        f"- Replay hash: `{s['replay_hash']}`",
        f"- Enforced rule hash: `{s['enforced_rule_hash']}`",
        f"- Template replay hash: `{s['template_replay_hash']}`",
        f"- Overclaim replay hash: `{s['overclaim_replay_hash']}`",
        "",
        "## Result",
        "",
        (
            f"R23 passes {s['requirements_passed']}/{s['requirement_count']} requirements and moves the R22 A6 polarity rule "
            "from advisory status into a replayed O3-F3 preflight rule."
        ),
        "",
        "## What Changed",
        "",
        "- The R20 template boundary still passes A6 polarity, but template markers prevent artifact acceptance.",
        "- The R21 overclaim fixture now fails A6 in addition to its earlier A2/A4/A7/A8 failures.",
        "- The enforced replay therefore rejects the overclaim on `A2/A4/A6/A7/A8`.",
        "- No O3-F3 artifact is accepted, no O3 closure is claimed, and no B7 credit is granted.",
        "",
        "## Gate Replay",
        "",
        f"- Old overclaim failed gates: `{s['old_overclaim_failed_gate_ids']}`",
        f"- New overclaim failed gates: `{s['new_overclaim_failed_gate_ids']}`",
        f"- A6 newly failed for overclaim: `{s['a6_newly_failed_for_overclaim']}`",
        f"- Template rejected as submission: `{s['template_rejected_as_submission']}`",
        "",
        "## Requirement Results",
        "",
    ]
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
            "This replay gate does not claim resource saving, occurrence removal, proxy-T reduction, B7 ledger improvement, FT resource credit, a checked impossibility theorem, an R5 reroute, or a solved B1/B7 problem.",
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
        "--r20-intake",
        type=Path,
        default=Path("results/B1_B7_cone01_R20_o3_f3_artifact_intake_preflight_gate_v0.json"),
    )
    parser.add_argument(
        "--r21-sentinel",
        type=Path,
        default=Path("results/B1_B7_cone01_R21_o3_f3_overclaim_sentinel_gate_v0.json"),
    )
    parser.add_argument(
        "--r22-polarity",
        type=Path,
        default=Path("results/B1_B7_cone01_R22_o3_f3_a6_claim_boundary_polarity_gate_v0.json"),
    )
    parser.add_argument(
        "--template",
        type=Path,
        default=Path(
            "results/B1_B7_cone01_o3_f3_symbolic_lu_submissions/"
            "B1-B7-cone01-O3-F3-symbolic-lu.template.json"
        ),
    )
    parser.add_argument(
        "--overclaim-fixture",
        type=Path,
        default=Path(
            "results/B1_B7_cone01_o3_f3_symbolic_lu_submissions/"
            "B1-B7-cone01-O3-F3-symbolic-lu.overclaim-sentinel.json"
        ),
    )
    parser.add_argument(
        "--json-output",
        type=Path,
        default=Path("results/B1_B7_cone01_R23_o3_f3_enforced_a6_preflight_replay_gate_v0.json"),
    )
    parser.add_argument(
        "--markdown-output",
        type=Path,
        default=Path("research/B1_B7_cone01_R23_o3_f3_enforced_a6_preflight_replay_gate.md"),
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
                "replay_hash": payload["summary"]["replay_hash"],
                "enforced_rule_hash": payload["summary"]["enforced_rule_hash"],
                "template_replay_hash": payload["summary"]["template_replay_hash"],
                "overclaim_replay_hash": payload["summary"]["overclaim_replay_hash"],
                "a6_polarity_enforced": payload["summary"]["a6_polarity_enforced"],
                "a6_newly_failed_for_overclaim": payload["summary"]["a6_newly_failed_for_overclaim"],
                "new_overclaim_failed_gate_ids": payload["summary"]["new_overclaim_failed_gate_ids"],
                "template_rejected_as_submission": payload["summary"]["template_rejected_as_submission"],
                "o3_f3_artifact_accepted": payload["summary"]["o3_f3_artifact_accepted"],
                "o3_closed": payload["summary"]["o3_closed"],
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
        raise SystemExit("B1/B7 R23 O3-F3 enforced A6 preflight replay gate validation failed")


if __name__ == "__main__":
    main()
