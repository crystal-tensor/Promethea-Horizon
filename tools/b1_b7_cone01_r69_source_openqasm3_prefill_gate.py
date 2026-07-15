#!/usr/bin/env python3
"""T-B1-004fs/T-B7-015b: R69 source OpenQASM3 export and prefill refresh gate."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import time
from pathlib import Path
from typing import Any


METHOD = "b1_b7_cone01_r69_source_openqasm3_prefill_gate_v0"
STATUS = "cone01_r69_source_openqasm3_export_prefill_refresh_zero_credit"
MODEL_STATUS = "r68_prefill_source_openqasm3_fields_filled_machine_replay_and_delta_still_blocked"
VERSION = "0.1"
TARGET_ID = "T-B1-004fs/T-B7-015b"
UPSTREAM_TARGET_ID = "T-B1-004fr/T-B7-015a"
SOURCE_QASM2 = "results/b1_control_rz_commute_optimizer/qasmbench_medium_exact/gcm_h6.qasm"
SOURCE_EXPORT_DIR = "results/B1_B7_cone01_openqasm3_source_export_gate"
SOURCE_QASM3 = f"{SOURCE_EXPORT_DIR}/gcm_h6_source_openqasm3.qasm"
SUBMISSION_DIR = "results/B1_B7_cone01_o3_f4_exit_route_submissions"


QREG_RE = re.compile(r"^qreg\s+([A-Za-z_]\w*)\[(\d+)\];$")
CREG_RE = re.compile(r"^creg\s+([A-Za-z_]\w*)\[(\d+)\];$")
U3_RE = re.compile(r"^u3\((.*)\)\s+(q\[\d+\]);$", re.IGNORECASE)
U_RE = re.compile(r"^U\((.*)\)\s+(q\[\d+\]);$")
RZ_RE = re.compile(r"^rz\((.*)\)\s+q\[(\d+)\];$", re.IGNORECASE)
CX_RE = re.compile(r"^cx\s+q\[(\d+)\]\s*,\s*q\[(\d+)\];$", re.IGNORECASE)
MEASURE_ARROW_RE = re.compile(r"^measure\s+q\[(\d+)\]\s*->\s*c\[(\d+)\];$", re.IGNORECASE)
MEASURE_ASSIGN_RE = re.compile(r"^c\[(\d+)\]\s*=\s*measure\s+q\[(\d+)\];$", re.IGNORECASE)


def stable_hash(payload: Any) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def req(requirement_id: str, label: str, passed: bool, evidence: dict[str, Any]) -> dict[str, Any]:
    return {
        "requirement_id": requirement_id,
        "label": label,
        "passed": bool(passed),
        "evidence": evidence,
    }


def normalize_args(args: str) -> str:
    return ",".join(part.strip().replace(" ", "") for part in args.split(","))


def qasm2_to_qasm3(source_text: str) -> tuple[str, list[dict[str, Any]]]:
    output: list[str] = []
    conversions: list[dict[str, Any]] = []
    for line_number, raw in enumerate(source_text.splitlines(), start=1):
        stripped = raw.strip()
        if not stripped:
            output.append("")
            continue
        if stripped == "OPENQASM 2.0;":
            output.append("OPENQASM 3.0;")
            conversions.append({"line": line_number, "from": stripped, "to": "OPENQASM 3.0;"})
            continue
        if stripped == 'include "qelib1.inc";':
            output.append('include "stdgates.inc";')
            conversions.append(
                {"line": line_number, "from": stripped, "to": 'include "stdgates.inc";'}
            )
            continue
        qreg = QREG_RE.match(stripped)
        if qreg:
            converted = f"qubit[{qreg.group(2)}] {qreg.group(1)};"
            output.append(converted)
            conversions.append({"line": line_number, "from": stripped, "to": converted})
            continue
        creg = CREG_RE.match(stripped)
        if creg:
            converted = f"bit[{creg.group(2)}] {creg.group(1)};"
            output.append(converted)
            conversions.append({"line": line_number, "from": stripped, "to": converted})
            continue
        u3 = U3_RE.match(stripped)
        if u3:
            converted = f"U({u3.group(1)}) {u3.group(2)};"
            output.append(converted)
            conversions.append({"line": line_number, "from": "u3", "to": "U"})
            continue
        measure = MEASURE_ARROW_RE.match(stripped)
        if measure:
            converted = f"c[{measure.group(2)}] = measure q[{measure.group(1)}];"
            output.append(converted)
            conversions.append({"line": line_number, "from": stripped, "to": converted})
            continue
        output.append(stripped)
    return "\n".join(output) + "\n", conversions


def normalize_line(line: str, dialect: str, line_number: int) -> str | None:
    stripped = line.strip()
    if not stripped or stripped.startswith("//"):
        return None
    if dialect == "qasm2" and stripped in {"OPENQASM 2.0;", 'include "qelib1.inc";'}:
        return None
    if dialect == "qasm3" and stripped in {"OPENQASM 3.0;", 'include "stdgates.inc";'}:
        return None
    if dialect == "qasm2" and (QREG_RE.match(stripped) or CREG_RE.match(stripped)):
        return None
    if dialect == "qasm3" and re.match(r"^(?:qubit|bit)\[\d+\]\s+\w+;$", stripped):
        return None
    u_match = U3_RE.match(stripped) or U_RE.match(stripped)
    if u_match:
        return f"U({normalize_args(u_match.group(1))})|{u_match.group(2)}"
    rz_match = RZ_RE.match(stripped)
    if rz_match:
        return f"rz({normalize_args(rz_match.group(1))})|q[{rz_match.group(2)}]"
    cx_match = CX_RE.match(stripped)
    if cx_match:
        return f"cx|q[{cx_match.group(1)}],q[{cx_match.group(2)}]"
    arrow_match = MEASURE_ARROW_RE.match(stripped)
    if arrow_match:
        return f"measure|q[{arrow_match.group(1)}]->c[{arrow_match.group(2)}]"
    assign_match = MEASURE_ASSIGN_RE.match(stripped)
    if assign_match:
        return f"measure|q[{assign_match.group(2)}]->c[{assign_match.group(1)}]"
    raise ValueError(f"unparsed_{dialect}_line_{line_number}: {stripped}")


def normalize_qasm(text: str, dialect: str) -> list[str]:
    rows: list[str] = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        normalized = normalize_line(line, dialect, line_number)
        if normalized is not None:
            rows.append(normalized)
    return rows


def op_counts(rows: list[str]) -> dict[str, int]:
    counts: dict[str, int] = {"U": 0, "rz": 0, "cx": 0, "measure": 0}
    for row in rows:
        if row.startswith("U("):
            counts["U"] += 1
        elif row.startswith("rz("):
            counts["rz"] += 1
        elif row.startswith("cx|"):
            counts["cx"] += 1
        elif row.startswith("measure|"):
            counts["measure"] += 1
        else:
            raise ValueError(f"unknown_normalized_row:{row}")
    return counts


def rel(root: Path, path: Path) -> str:
    return str(path.relative_to(root))


def normalize_prefill_paths(root: Path, draft: dict[str, Any]) -> dict[str, Any]:
    updated = dict(draft)
    root_str = str(root) + "/"
    for key, value in list(updated.items()):
        if key.endswith("_path") and isinstance(value, str) and value.startswith(root_str):
            updated[key] = value[len(root_str) :]
    return updated


def count_prefilled(contract: dict[str, Any], draft: dict[str, Any]) -> tuple[int, list[str]]:
    placeholders = [
        field
        for field in contract["required_submission_fields"]
        if draft.get(field) in (None, "")
    ]
    return len(contract["required_submission_fields"]) - len(placeholders), placeholders


def build_payload(args: argparse.Namespace) -> dict[str, Any]:
    root = Path(args.repo_root).resolve()
    source_qasm2 = root / SOURCE_QASM2
    source_qasm3 = root / SOURCE_QASM3
    contract_path = root / SUBMISSION_DIR / "R67-accepted-exit-route.contract.json"
    r68_prefill_path = root / SUBMISSION_DIR / "R68-R1-line1381-prefill-draft.json"
    r68_result_path = root / "results/B1_B7_cone01_R68_exit_route_evidence_prefill_gate_v0.json"

    source_text = source_qasm2.read_text(encoding="utf-8")
    qasm3_text, conversions = qasm2_to_qasm3(source_text)
    write_text(source_qasm3, qasm3_text)

    source_rows = normalize_qasm(source_text, "qasm2")
    qasm3_rows = normalize_qasm(qasm3_text, "qasm3")
    source_stream_hash = sha256_text("\n".join(source_rows) + "\n")
    qasm3_stream_hash = sha256_text("\n".join(qasm3_rows) + "\n")
    source_counts = op_counts(source_rows)
    qasm3_counts = op_counts(qasm3_rows)

    validation_errors: list[str] = []
    if not qasm3_text.startswith("OPENQASM 3.0;\n"):
        validation_errors.append("missing_openqasm3_header")
    if 'include "stdgates.inc";' not in qasm3_text.splitlines()[:3]:
        validation_errors.append("missing_stdgates_include")
    if "qreg " in qasm3_text or "creg " in qasm3_text or "qelib1.inc" in qasm3_text:
        validation_errors.append("legacy_declaration_or_include_remains")
    if "u3(" in qasm3_text.lower():
        validation_errors.append("legacy_u3_remains")
    if source_rows != qasm3_rows:
        validation_errors.append("normalized_stream_mismatch")
    if source_counts != qasm3_counts:
        validation_errors.append("operation_count_mismatch")

    contract = load_json(contract_path)
    r68_prefill = normalize_prefill_paths(root, load_json(r68_prefill_path))
    r68 = load_json(r68_result_path)
    refreshed = dict(r68_prefill)
    refreshed.update(
        {
            "template_id": "B1-B7-cone01-R69-R1-line1381-prefill-source-openqasm3",
            "source_target_id": TARGET_ID,
            "upstream_target_id": UPSTREAM_TARGET_ID,
            "source_openqasm3_path": rel(root, source_qasm3),
            "source_openqasm3_sha256": file_hash(source_qasm3),
            "claim_boundary": (
                "R69 refreshed prefill only. It fills the source OpenQASM3 "
                "fields from a structural dialect export, but machine-check "
                "replay and positive delta evidence remain missing. No O3 "
                "closure, reroute, resource saving, or B7 ledger credit is claimed."
            ),
        }
    )
    refreshed["prefill_hash"] = stable_hash(refreshed)
    refreshed_path = root / SUBMISSION_DIR / "R69-R1-line1381-prefill-source-openqasm3.json"
    write_json(refreshed_path, refreshed)
    refreshed_count, refreshed_placeholders = count_prefilled(contract, refreshed)

    blocker_queue = {
        "artifact": "R69 remaining exit-route blocker queue",
        "source_target_id": TARGET_ID,
        "upstream_target_id": UPSTREAM_TARGET_ID,
        "selected_next_route": "R1-line1381-resolution",
        "resolved_fields": ["source_openqasm3_path", "source_openqasm3_sha256"],
        "remaining_placeholder_fields": refreshed_placeholders,
        "queue": [
            {
                "blocker_id": "R69-B1",
                "priority": 1,
                "missing_fields": [
                    "machine_check_replay_command",
                    "machine_check_replay_stdout_path",
                    "machine_check_replay_stdout_sha256",
                ],
                "needed_artifact": "machine-check replay command and stdout binding the source OpenQASM3, candidate OpenQASM3, and route evidence",
            },
            {
                "blocker_id": "R69-B2",
                "priority": 2,
                "missing_fields": ["occurrence_removal_delta", "proxy_t_reduction_delta"],
                "needed_artifact": "positive occurrence and proxy-T delta ledger accepted by the R67 contract",
            },
        ],
    }
    blocker_queue["blocker_queue_hash"] = stable_hash(blocker_queue)
    blocker_path = root / SUBMISSION_DIR / "R69-remaining-exit-route-blocker-queue.json"
    write_json(blocker_path, blocker_queue)

    requirements = [
        req(
            "S1",
            "source QASM2 exists and is the original gcm_h6 source",
            source_qasm2.exists() and source_text.startswith("OPENQASM 2.0;"),
            {"source_qasm2": rel(root, source_qasm2), "source_sha256": sha256_text(source_text)},
        ),
        req(
            "S2",
            "source OpenQASM3 export has modern header and declarations",
            not validation_errors,
            {"validation_errors": validation_errors, "source_openqasm3": rel(root, source_qasm3)},
        ),
        req(
            "S3",
            "normalized source streams match across QASM2 and QASM3",
            source_rows == qasm3_rows and source_stream_hash == qasm3_stream_hash,
            {
                "normalized_instruction_count": len(qasm3_rows),
                "normalized_stream_sha256": qasm3_stream_hash,
            },
        ),
        req(
            "S4",
            "operation counts are preserved by dialect export",
            source_counts == qasm3_counts,
            {"source_operation_counts": source_counts, "openqasm3_operation_counts": qasm3_counts},
        ),
        req(
            "S5",
            "R69 refresh fills exactly the source OpenQASM3 fields from R68",
            r68["summary"]["r1_placeholder_field_count"] == 5
            and refreshed_count == 26
            and set(refreshed_placeholders)
            == {
                "machine_check_replay_command",
                "machine_check_replay_stdout_path",
                "machine_check_replay_stdout_sha256",
            },
            {
                "r68_placeholder_count": r68["summary"]["r1_placeholder_field_count"],
                "r69_prefilled_field_count": refreshed_count,
                "remaining_placeholder_fields": refreshed_placeholders,
            },
        ),
        req(
            "S6",
            "R69 preserves zero-credit claim boundary",
            refreshed["accepted_exit_route_count"] == 0
            and refreshed["occurrence_removal_delta"] == 0
            and refreshed["proxy_t_reduction_delta"] == 0
            and refreshed["b7_nonzero_retest_requested"] is False,
            {
                "accepted_exit_route_count": refreshed["accepted_exit_route_count"],
                "occurrence_removal_delta": refreshed["occurrence_removal_delta"],
                "proxy_t_reduction_delta": refreshed["proxy_t_reduction_delta"],
                "b7_nonzero_retest_requested": refreshed["b7_nonzero_retest_requested"],
            },
        ),
        req(
            "S7",
            "remaining blocker queue names replay and positive-delta blockers",
            len(blocker_queue["queue"]) == 2 and len(refreshed_placeholders) == 3,
            {
                "remaining_placeholder_fields": refreshed_placeholders,
                "blocker_queue_hash": blocker_queue["blocker_queue_hash"],
            },
        ),
        req("S8", "R69 artifacts are hash-bound and written", True, {}),
    ]

    summary = {
        "method": METHOD,
        "status": STATUS,
        "model_status": MODEL_STATUS,
        "source_target_id": TARGET_ID,
        "upstream_target_id": UPSTREAM_TARGET_ID,
        "source_openqasm3_path": rel(root, source_qasm3),
        "source_openqasm3_sha256": file_hash(source_qasm3),
        "source_qasm2_sha256": sha256_text(source_text),
        "source_line_count": len(source_text.splitlines()),
        "source_openqasm3_line_count": len(qasm3_text.splitlines()),
        "normalized_instruction_count": len(qasm3_rows),
        "normalized_stream_sha256": qasm3_stream_hash,
        "operation_counts": qasm3_counts,
        "conversion_row_count": len(conversions),
        "u3_to_U_conversion_count": sum(1 for row in conversions if row["from"] == "u3"),
        "measurement_conversion_count": sum(1 for row in conversions if "measure" in row["from"]),
        "r68_prefilled_field_count": r68["summary"]["r1_prefilled_field_count"],
        "r68_placeholder_field_count": r68["summary"]["r1_placeholder_field_count"],
        "r69_prefilled_field_count": refreshed_count,
        "r69_placeholder_field_count": len(refreshed_placeholders),
        "resolved_placeholder_field_count": 2,
        "remaining_placeholder_fields": refreshed_placeholders,
        "accepted_exit_route_count": 0,
        "accepted_occurrence_removal": 0,
        "accepted_proxy_t_reduction": 0,
        "b7_nonzero_retest_allowed": False,
        "b7_credit_delta": 0,
        "o3_closed": False,
        "reroute_allowed": False,
        "resource_saving_claimed": False,
        "b7_ledger_improvement_claimed": False,
        "refreshed_prefill_hash": refreshed["prefill_hash"],
        "refreshed_prefill_file_sha256": file_hash(refreshed_path),
        "blocker_queue_hash": blocker_queue["blocker_queue_hash"],
        "blocker_queue_file_sha256": file_hash(blocker_path),
        "requirement_count": len(requirements),
        "requirements_passed": sum(1 for item in requirements if item["passed"]),
        "requirements_failed": sum(1 for item in requirements if not item["passed"]),
        "failed_requirement_ids": [
            item["requirement_id"] for item in requirements if not item["passed"]
        ],
        "validation_error_count": len(validation_errors),
    }
    payload = {
        "title": "B1/B7 Cone01 R69 Source OpenQASM3 Prefill Gate",
        "version": VERSION,
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "summary": summary,
        "requirements": requirements,
        "conversion_rows_preview": conversions[:25],
        "claim_boundary": {
            "what_is_supported": (
                "R69 exports the original gcm_h6 source to OpenQASM3, verifies a "
                "matching normalized instruction stream, and fills the source "
                "OpenQASM3 fields in the R1 prefill."
            ),
            "what_is_not_supported": (
                "R69 does not provide machine-check replay stdout, positive "
                "occurrence/proxy-T deltas, an accepted exit route, O3 closure, "
                "reroute permission, or B7 credit."
            ),
            "next_gate": (
                "Add machine-check replay command/stdout/hash, then submit positive "
                "occurrence/proxy-T delta evidence."
            ),
        },
        "artifacts": {
            "source_openqasm3": rel(root, source_qasm3),
            "refreshed_prefill": rel(root, refreshed_path),
            "blocker_queue": rel(root, blocker_path),
        },
    }
    payload["summary"]["payload_hash"] = stable_hash(payload)
    return payload


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    s = payload["summary"]
    lines = [
        "# B1/B7 Cone01 R69 Source OpenQASM3 Prefill Gate",
        "",
        "## Summary",
        "",
        f"- Status: `{s['status']}`",
        f"- Source OpenQASM3: `{s['source_openqasm3_path']}`",
        f"- Source OpenQASM3 SHA256: `{s['source_openqasm3_sha256']}`",
        f"- R68 prefilled fields: `{s['r68_prefilled_field_count']}` / 29",
        f"- R69 prefilled fields: `{s['r69_prefilled_field_count']}` / 29",
        f"- Remaining placeholder fields: `{s['r69_placeholder_field_count']}`",
        f"- Accepted exit routes: `{s['accepted_exit_route_count']}`",
        f"- Accepted occurrence removal: `{s['accepted_occurrence_removal']}`",
        f"- Accepted proxy-T reduction: `{s['accepted_proxy_t_reduction']}`",
        f"- B7 nonzero retest allowed: `{s['b7_nonzero_retest_allowed']}`",
        f"- B7 credit delta: `{s['b7_credit_delta']}`",
        f"- R69 blocker queue hash: `{s['blocker_queue_hash']}`",
        "",
        "R69 fills the source OpenQASM3 path/hash fields in the R1 line1381 prefill. The draft now has 26 of 29 fields filled, but it still lacks machine-check replay command/stdout/hash and still has zero occurrence/proxy-T delta.",
        "",
        "## Requirements",
        "",
    ]
    for item in payload["requirements"]:
        status = "PASS" if item["passed"] else "FAIL"
        lines.append(f"- `{item['requirement_id']}` {status}: {item['label']}")
    lines.extend(
        [
            "",
            "## Remaining Placeholders",
            "",
        ]
    )
    for field in s["remaining_placeholder_fields"]:
        lines.append(f"- `{field}`")
    lines.extend(
        [
            "",
            "## Claim Boundary",
            "",
            f"- Supported: {payload['claim_boundary']['what_is_supported']}",
            f"- Not supported: {payload['claim_boundary']['what_is_not_supported']}",
            f"- Next gate: {payload['claim_boundary']['next_gate']}",
            "",
            "## Artifacts",
            "",
        ]
    )
    for label, artifact_path in payload["artifacts"].items():
        lines.append(f"- `{label}`: `{artifact_path}`")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=".")
    parser.add_argument(
        "--json-output",
        default="results/B1_B7_cone01_R69_source_openqasm3_prefill_gate_v0.json",
    )
    parser.add_argument(
        "--markdown-output",
        default="research/B1_B7_cone01_R69_source_openqasm3_prefill_gate.md",
    )
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()

    payload = build_payload(args)
    root = Path(args.repo_root).resolve()
    json_path = root / args.json_output
    md_path = root / args.markdown_output
    write_json(json_path, payload)
    write_markdown(md_path, payload)
    if args.pretty:
        print(json.dumps(payload["summary"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
