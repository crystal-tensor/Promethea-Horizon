#!/usr/bin/env python3
"""Build a line-stable QASM2/OpenQASM 3 source map for the cone_01 patch chain."""

from __future__ import annotations

import hashlib
import json
import re
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
RESEARCH = ROOT / "research"

METHOD = "b1_b7_cone01_openqasm3_source_map_gate_v0"
STATUS = "cone01_openqasm3_source_map_passed_without_b7_resource_credit"
MODEL_STATUS = "openqasm3_patch_lift_instruction_source_map_is_stable_without_b7_credit"

QASM2_PATH = RESULTS / "B1_B7_cone01_qasm2_candidate_rewrite_gate" / "gcm_h6_line268_line1381_candidate.qasm"
QASM3_PATH = (
    RESULTS
    / "B1_B7_cone01_openqasm3_candidate_export_gate"
    / "gcm_h6_line268_line1381_candidate_openqasm3.qasm"
)
SEAL_PATH = RESULTS / "B1_B7_cone01_openqasm3_provenance_seal_gate_v0.json"
LIFT_PATH = RESULTS / "B1_B7_cone01_openqasm3_composable_patch_lift_gate_v0.json"
OUT_JSON = RESULTS / "B1_B7_cone01_openqasm3_source_map_gate_v0.json"
OUT_MD = RESEARCH / "B1_B7_cone01_openqasm3_source_map_gate.md"

QASM2_SKIP_RE = re.compile(
    r'^(?:OPENQASM 2\.0;|include "qelib1\.inc";|qreg\s+q\[\d+\];|creg\s+c\[\d+\];)$'
)
QASM3_SKIP_RE = re.compile(
    r'^(?:OPENQASM 3\.0;|include "stdgates\.inc";|qubit\[\d+\]\s+q;|bit\[\d+\]\s+c;)$'
)
U_RE = re.compile(r"^(?:u3|U)\(([^()]*)\)\s+q\[(\d+)\];$", re.IGNORECASE)
RZ_RE = re.compile(r"^rz\(([^()]*)\)\s+q\[(\d+)\];$", re.IGNORECASE)
CX_RE = re.compile(r"^cx\s+q\[(\d+)\]\s*,\s*q\[(\d+)\];$", re.IGNORECASE)
MEASURE_ARROW_RE = re.compile(r"^measure\s+q\[(\d+)\]\s*->\s*c\[(\d+)\];$", re.IGNORECASE)
MEASURE_ASSIGN_RE = re.compile(r"^c\[(\d+)\]\s*=\s*measure\s+q\[(\d+)\];$", re.IGNORECASE)


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def load_json(path: Path) -> dict:
    return json.loads(read_text(path))


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def normalize_args(args: str) -> str:
    return ",".join(part.strip().replace(" ", "") for part in args.split(","))


def normalize_line(line: str, dialect: str, line_number: int) -> str | None:
    stripped = line.strip()
    if not stripped or stripped.startswith("//"):
        return None
    if dialect == "qasm2" and QASM2_SKIP_RE.match(stripped):
        return None
    if dialect == "qasm3" and QASM3_SKIP_RE.match(stripped):
        return None

    u_match = U_RE.match(stripped)
    if u_match:
        return f"U({normalize_args(u_match.group(1))})|q[{u_match.group(2)}]"

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


def normalize_qasm_with_lines(text: str, dialect: str) -> list[dict]:
    rows: list[dict] = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        normalized = normalize_line(line, dialect, line_number)
        if normalized is None:
            continue
        rows.append(
            {
                "raw_line_number": line_number,
                "raw_line": line.strip(),
                "normalized": normalized,
            }
        )
    return rows


def operation_name(row: str) -> str:
    return row.split("(", 1)[0] if row.startswith(("U(", "rz(")) else row.split("|", 1)[0]


def source_map_hash(rows: list[dict]) -> str:
    material = json.dumps(rows, sort_keys=True, separators=(",", ":"))
    return sha256_text(material)


def require(errors: list[str], condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def build_source_map(qasm2_rows: list[dict], qasm3_rows: list[dict]) -> list[dict]:
    source_map: list[dict] = []
    for index, (qasm2_row, qasm3_row) in enumerate(zip(qasm2_rows, qasm3_rows), start=1):
        normalized = qasm2_row["normalized"]
        source_map.append(
            {
                "instruction_index": index,
                "operation": operation_name(normalized),
                "qasm2_line_number": qasm2_row["raw_line_number"],
                "openqasm3_line_number": qasm3_row["raw_line_number"],
                "normalized_instruction_sha256": sha256_text(normalized),
            }
        )
    return source_map


def line_lookup(source_map: list[dict]) -> dict[int, dict]:
    return {row["qasm2_line_number"]: row for row in source_map}


def main() -> None:
    qasm2_text = read_text(QASM2_PATH)
    qasm3_text = read_text(QASM3_PATH)
    qasm2_rows = normalize_qasm_with_lines(qasm2_text, "qasm2")
    qasm3_rows = normalize_qasm_with_lines(qasm3_text, "qasm3")
    seal = load_json(SEAL_PATH)
    lift = load_json(LIFT_PATH)
    seal_summary = seal.get("summary", {})
    lift_summary = lift.get("summary", {})
    expected_stream_sha = "7cd50bea1f5a3c191c5735c0891d3f70f8c07a9cfca9d6e93724e6d49cb36343"

    source_map = build_source_map(qasm2_rows, qasm3_rows)
    mapped_lines = line_lookup(source_map)
    selected_lines = lift_summary.get("selected_line_numbers", [])
    dropped_overlap_lines = lift_summary.get("dropped_overlap_candidate_line_numbers", [])
    patch_line_numbers = selected_lines + dropped_overlap_lines
    patch_line_map = [mapped_lines[line] for line in patch_line_numbers if line in mapped_lines]
    source_map_sha = source_map_hash(source_map)
    operation_counts = dict(Counter(row["operation"] for row in source_map))
    raw_line_delta_count = sum(
        1 for row in source_map if row["qasm2_line_number"] != row["openqasm3_line_number"]
    )
    normalized_rows_match = [a["normalized"] for a in qasm2_rows] == [
        b["normalized"] for b in qasm3_rows
    ]

    errors: list[str] = []
    require(errors, len(qasm2_text.splitlines()) == 1884, "qasm2 raw line count changed")
    require(errors, len(qasm3_text.splitlines()) == 1884, "qasm3 raw line count changed")
    require(errors, len(qasm2_rows) == 1878, "qasm2 normalized instruction count changed")
    require(errors, len(qasm3_rows) == 1878, "qasm3 normalized instruction count changed")
    require(errors, normalized_rows_match, "qasm2/openqasm3 normalized rows differ")
    require(errors, len(source_map) == 1878, "source map row count changed")
    require(errors, raw_line_delta_count == 0, "qasm2/openqasm3 raw line numbers drifted")
    require(errors, operation_counts == {"U": 487, "rz": 601, "cx": 789, "measure": 1}, "operation counts changed")
    require(errors, seal.get("status") == "cone01_openqasm3_provenance_seal_passed_without_b7_resource_credit", "provenance seal status changed")
    require(errors, lift.get("status") == "cone01_openqasm3_composable_patch_lift_passed_without_b7_resource_credit", "patch lift status changed")
    require(errors, seal_summary.get("normalized_stream_sha256") == expected_stream_sha, "sealed stream hash changed")
    require(errors, lift_summary.get("normalized_stream_sha256") == expected_stream_sha, "lift stream hash changed")
    require(errors, selected_lines == [268, 1381], "selected patch lines changed")
    require(errors, dropped_overlap_lines == [1378], "dropped overlap lines changed")
    require(errors, [row["instruction_index"] for row in patch_line_map] == [263, 1375, 1372], "patch instruction indices changed")
    require(errors, [row["operation"] for row in patch_line_map] == ["rz", "U", "U"], "patch operation kinds changed")

    passed = not errors
    summary = {
        "qasm2_candidate_path": rel(QASM2_PATH),
        "openqasm3_candidate_path": rel(QASM3_PATH),
        "source_provenance_seal_gate": rel(SEAL_PATH),
        "source_openqasm3_composable_patch_lift_gate": rel(LIFT_PATH),
        "qasm2_raw_line_count": len(qasm2_text.splitlines()),
        "openqasm3_raw_line_count": len(qasm3_text.splitlines()),
        "normalized_instruction_count": len(source_map),
        "normalized_streams_match": normalized_rows_match,
        "normalized_stream_sha256": expected_stream_sha,
        "operation_counts": operation_counts,
        "source_map_row_count": len(source_map),
        "raw_line_delta_count": raw_line_delta_count,
        "source_map_sha256": source_map_sha,
        "selected_line_numbers": selected_lines,
        "dropped_overlap_candidate_line_numbers": dropped_overlap_lines,
        "patch_line_map": patch_line_map,
        "max_selected_patch_residual_norm": lift_summary.get("max_selected_patch_residual_norm"),
        "max_selected_patch_entry_error": lift_summary.get("max_selected_patch_entry_error"),
        "openqasm3_linear_span_error_spectral_norm": lift_summary.get(
            "openqasm3_linear_span_error_spectral_norm"
        ),
        "openqasm3_source_map_passed": passed,
        "accepted_project_local_openqasm3_source_map_count": 1 if passed else 0,
        "accepted_qiskit_loader_parse_artifact_count": 0,
        "accepted_symbolic_unitary_equivalence_count": 0,
        "accepted_local_u3_pricing_certificate_count": 0,
        "accepted_occurrence_removal": 0,
        "accepted_proxy_t_reduction": 0,
        "missing_occurrences_after_gate": 30,
        "missing_proxy_t_after_gate": 600,
        "qiskit_loader_parse_claimed": False,
        "symbolic_unitary_equivalence_claimed": False,
        "arbitrary_input_equivalence_claimed": False,
        "full_hilbert_space_certificate_claimed": False,
        "local_u3_pricing_accepted": False,
        "resource_saving_claimed": False,
        "b7_ledger_improvement_claimed": False,
        "validation_error_count": len(errors),
    }
    payload = {
        "benchmark_id": "B1",
        "linked_b7_problem_id": 21,
        "method": METHOD,
        "status": STATUS if passed else "cone01_openqasm3_source_map_failed",
        "model_status": MODEL_STATUS if passed else "openqasm3_patch_lift_instruction_source_map_failed",
        "workload": "qasmbench_medium_exact/gcm_h6.qasm",
        "claim_boundary": {
            "supported_claim": (
                "The QASM2 and OpenQASM 3 candidate artifacts have a stable one-to-one "
                "instruction source map over 1,878 normalized instructions, including the "
                "selected patch lines and the dropped overlap line."
            ),
            "qiskit_loader_parse_claimed": False,
            "symbolic_unitary_equivalence_claimed": False,
            "arbitrary_input_equivalence_claimed": False,
            "full_hilbert_space_certificate_claimed": False,
            "local_u3_pricing_accepted": False,
            "resource_saving_claimed": False,
            "b7_ledger_improvement_claimed": False,
            "unsupported_claims": [
                "This is not a Qiskit OpenQASM 3 loader parse.",
                "This is not a symbolic exact full-circuit unitary proof.",
                "This is not arbitrary-input or full-Hilbert-space coverage.",
                "This does not price or eliminate the remaining local-U3 parameters.",
                "This does not improve the B7 resource ledger.",
            ],
        },
        "summary": summary,
        "source_map": source_map,
        "validation_errors": errors,
    }
    OUT_JSON.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    OUT_MD.write_text(render_markdown(payload), encoding="utf-8")
    if errors:
        raise SystemExit("OpenQASM3 source-map gate failed: " + "; ".join(errors))


def render_markdown(payload: dict) -> str:
    summary = payload["summary"]
    return "\n".join(
        [
            "# B1/B7 cone_01 OpenQASM 3 Source-Map Gate",
            "",
            f"- Method: `{payload['method']}`",
            f"- Status: `{payload['status']}`",
            f"- Model status: `{payload['model_status']}`",
            f"- Workload: `{payload['workload']}`",
            f"- QASM2 candidate: `{summary['qasm2_candidate_path']}`",
            f"- OpenQASM 3 artifact: `{summary['openqasm3_candidate_path']}`",
            "",
            "## Evidence",
            "",
            f"- Raw QASM2 / OpenQASM 3 line counts: {summary['qasm2_raw_line_count']} / {summary['openqasm3_raw_line_count']}",
            f"- Normalized stream match / instruction count: {summary['normalized_streams_match']} / {summary['normalized_instruction_count']}",
            f"- Normalized stream SHA-256: `{summary['normalized_stream_sha256']}`",
            f"- Source-map rows / raw-line drift count: {summary['source_map_row_count']} / {summary['raw_line_delta_count']}",
            f"- Source-map SHA-256: `{summary['source_map_sha256']}`",
            f"- Selected lines / dropped overlap lines: {summary['selected_line_numbers']} / {summary['dropped_overlap_candidate_line_numbers']}",
            "",
            "## Patch Line Map",
            "",
            "| QASM2 line | OpenQASM 3 line | Instruction index | Operation | Instruction hash |",
            "| ---: | ---: | ---: | --- | --- |",
            *[
                "| {qasm2_line_number} | {openqasm3_line_number} | {instruction_index} | {operation} | `{normalized_instruction_sha256}` |".format(
                    **row
                )
                for row in summary["patch_line_map"]
            ],
            "",
            "## Claim Boundary",
            "",
            payload["claim_boundary"]["supported_claim"],
            "",
            "Unsupported claims:",
            "",
            *[f"- {item}" for item in payload["claim_boundary"]["unsupported_claims"]],
            "",
        ]
    )


if __name__ == "__main__":
    main()
