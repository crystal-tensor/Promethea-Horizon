#!/usr/bin/env python3
"""Qiskit-loader support gate for the B1/B7 OpenQASM 3 composable patch lift."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
RESEARCH = ROOT / "research"

METHOD = "b1_b7_cone01_openqasm3_qiskit_loader_composable_patch_lift_gate_v0"
STATUS = "cone01_openqasm3_qiskit_loader_composable_patch_lift_supported_without_b7_credit"
MODEL_STATUS = (
    "qiskit_loader_openqasm3_candidate_supports_composable_patch_lift_via_finite_span_"
    "without_b7_credit"
)

OPENQASM3_PATCH_LIFT_PATH = RESULTS / "B1_B7_cone01_openqasm3_composable_patch_lift_gate_v0.json"
QISKIT_LOADER_SPAN_PATH = (
    RESULTS / "B1_B7_cone01_openqasm3_qiskit_loader_linear_span_replay_certificate_gate_v0.json"
)
QISKIT_LOADER_GLOBAL_PHASE_PATH = (
    RESULTS / "B1_B7_cone01_openqasm3_qiskit_loader_global_phase_subspace_replay_gate_v0.json"
)
OUT_JSON = (
    RESULTS / "B1_B7_cone01_openqasm3_qiskit_loader_composable_patch_lift_gate_v0.json"
)
OUT_MD = RESEARCH / "B1_B7_cone01_openqasm3_qiskit_loader_composable_patch_lift_gate.md"


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def require(errors: list[str], condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def build_payload() -> dict[str, Any]:
    patch_lift = load_json(OPENQASM3_PATCH_LIFT_PATH)
    qiskit_span = load_json(QISKIT_LOADER_SPAN_PATH)
    qiskit_global = load_json(QISKIT_LOADER_GLOBAL_PHASE_PATH)

    patch_summary = patch_lift.get("summary", {})
    span_summary = qiskit_span.get("summary", {})
    global_summary = qiskit_global.get("summary", {})
    errors: list[str] = []

    require(
        errors,
        patch_lift.get("status") == "cone01_openqasm3_composable_patch_lift_passed_without_b7_resource_credit",
        "source OpenQASM3 composable patch-lift gate did not pass",
    )
    require(
        errors,
        qiskit_span.get("status") == "cone01_openqasm3_qiskit_loader_linear_span_replay_certificate_passed",
        "source Qiskit-loader finite-span certificate did not pass",
    )
    require(
        errors,
        qiskit_global.get("status") == "cone01_openqasm3_qiskit_loader_global_phase_subspace_replay_passed",
        "source Qiskit-loader global-phase gate did not pass",
    )
    require(errors, patch_summary.get("selected_line_numbers") == [268, 1381], "selected lines changed")
    require(
        errors,
        patch_summary.get("dropped_overlap_candidate_line_numbers") == [1378],
        "dropped overlap line changed",
    )
    require(errors, patch_summary.get("selected_patch_count") == 2, "selected patch count changed")
    require(
        errors,
        patch_summary.get("all_selected_windows_nonoverlap") is True,
        "selected patch windows overlap",
    )
    require(
        errors,
        patch_summary.get("all_local_unitary_certificates_passed") is True,
        "source local-unitary patch certificates did not pass",
    )
    require(
        errors,
        float(patch_summary.get("max_selected_patch_residual_norm", 1.0)) <= 1e-10,
        "selected patch residual too large",
    )
    require(
        errors,
        float(patch_summary.get("max_selected_patch_entry_error", 1.0)) <= 1e-10,
        "selected patch entry error too large",
    )
    require(
        errors,
        patch_summary.get("openqasm3_composable_patch_lift_passed") is True,
        "OpenQASM3 composable patch lift was not accepted",
    )
    require(
        errors,
        patch_summary.get("openqasm3_candidate_path") == span_summary.get("openqasm3_candidate_path"),
        "Qiskit-loader finite-span path differs from OpenQASM3 patch-lift path",
    )
    require(
        errors,
        span_summary.get("qiskit_loader_linear_span_certificate_passed") is True,
        "Qiskit-loader finite-span certificate flag is false",
    )
    require(
        errors,
        global_summary.get("qiskit_loader_global_phase_subspace_replay_passed") is True,
        "Qiskit-loader global-phase replay flag is false",
    )
    require(
        errors,
        int(span_summary.get("accepted_qiskit_loader_parse_artifact_count", 0)) == 1,
        "Qiskit-loader parse artifact count changed",
    )
    require(
        errors,
        int(span_summary.get("accepted_qiskit_loader_linear_span_certificate_count", 0)) == 1,
        "Qiskit-loader finite-span certificate count changed",
    )
    require(
        errors,
        float(span_summary.get("linear_span_error_spectral_norm", 1.0)) <= 1e-10,
        "Qiskit-loader finite-span spectral error too large",
    )

    passed = not errors
    summary = {
        "source_openqasm3_patch_lift_gate": rel(OPENQASM3_PATCH_LIFT_PATH),
        "source_qiskit_loader_linear_span_gate": rel(QISKIT_LOADER_SPAN_PATH),
        "source_qiskit_loader_global_phase_gate": rel(QISKIT_LOADER_GLOBAL_PHASE_PATH),
        "qasm2_candidate_path": patch_summary.get("qasm2_candidate_path"),
        "openqasm3_candidate_path": patch_summary.get("openqasm3_candidate_path"),
        "qiskit_loader_openqasm3_candidate_path": span_summary.get("openqasm3_candidate_path"),
        "normalized_streams_match": patch_summary.get("normalized_streams_match"),
        "stream_mismatch_count": patch_summary.get("stream_mismatch_count"),
        "stream_length_delta": patch_summary.get("stream_length_delta"),
        "normalized_instruction_count": patch_summary.get("normalized_instruction_count"),
        "normalized_stream_sha256": patch_summary.get("normalized_stream_sha256"),
        "selected_patch_count": patch_summary.get("selected_patch_count"),
        "selected_line_numbers": patch_summary.get("selected_line_numbers"),
        "dropped_overlap_candidate_line_numbers": patch_summary.get(
            "dropped_overlap_candidate_line_numbers"
        ),
        "all_selected_windows_nonoverlap": patch_summary.get("all_selected_windows_nonoverlap"),
        "all_local_unitary_certificates_passed": patch_summary.get(
            "all_local_unitary_certificates_passed"
        ),
        "max_selected_patch_residual_norm": patch_summary.get("max_selected_patch_residual_norm"),
        "max_selected_patch_entry_error": patch_summary.get("max_selected_patch_entry_error"),
        "qiskit_version": span_summary.get("qiskit_version"),
        "qiskit_qasm3_import_version": span_summary.get("qiskit_qasm3_import_version"),
        "openqasm3_package_version": span_summary.get("openqasm3_package_version"),
        "qiskit_num_qubits": span_summary.get("qiskit_num_qubits"),
        "qiskit_num_clbits": span_summary.get("qiskit_num_clbits"),
        "qiskit_depth": span_summary.get("qiskit_depth"),
        "qiskit_count_ops": span_summary.get("qiskit_count_ops"),
        "source_cnot_count": span_summary.get("source_cnot_count"),
        "qiskit_cnot_count": span_summary.get("qiskit_cnot_count"),
        "qiskit_cnot_delta": span_summary.get("qiskit_cnot_delta"),
        "qiskit_loader_global_phase_subspace_replay_passed": global_summary.get(
            "qiskit_loader_global_phase_subspace_replay_passed"
        ),
        "qiskit_loader_linear_span_certificate_passed": span_summary.get(
            "qiskit_loader_linear_span_certificate_passed"
        ),
        "qiskit_loader_certified_input_subspace_dimension": span_summary.get(
            "certified_input_subspace_dimension"
        ),
        "qiskit_loader_full_input_space_dimension": span_summary.get("full_input_space_dimension"),
        "qiskit_loader_certified_input_subspace_fraction": span_summary.get(
            "certified_input_subspace_fraction"
        ),
        "qiskit_loader_linear_span_error_spectral_norm": span_summary.get(
            "linear_span_error_spectral_norm"
        ),
        "qiskit_loader_max_basis_l2_error": span_summary.get("max_basis_l2_error"),
        "qiskit_loader_max_basis_probability_delta": span_summary.get(
            "max_basis_probability_delta"
        ),
        "qiskit_loader_max_cross_gram_delta": span_summary.get("max_cross_gram_delta"),
        "openqasm3_qiskit_loader_composable_patch_lift_supported": passed,
        "accepted_project_local_openqasm3_composable_patch_lift_count": patch_summary.get(
            "accepted_project_local_openqasm3_composable_patch_lift_count"
        ),
        "accepted_qiskit_loader_parse_artifact_count": span_summary.get(
            "accepted_qiskit_loader_parse_artifact_count"
        ),
        "accepted_qiskit_loader_global_phase_subspace_replay_artifact_count": span_summary.get(
            "accepted_qiskit_loader_global_phase_subspace_replay_artifact_count"
        ),
        "accepted_qiskit_loader_linear_span_certificate_count": span_summary.get(
            "accepted_qiskit_loader_linear_span_certificate_count"
        ),
        "accepted_qiskit_loader_composable_patch_lift_support_count": 1 if passed else 0,
        "accepted_full_circuit_replay_certificate_count": 0,
        "accepted_symbolic_unitary_equivalence_count": 0,
        "accepted_local_u3_pricing_certificate_count": 0,
        "accepted_occurrence_removal": 0,
        "accepted_proxy_t_reduction": 0,
        "missing_occurrences_after_gate": 30,
        "missing_proxy_t_after_gate": 600,
        "qiskit_loader_parse_claimed": True,
        "qiskit_loader_linear_span_certificate_claimed": True,
        "qiskit_loader_composable_patch_lift_support_claimed": passed,
        "symbolic_unitary_equivalence_claimed": False,
        "arbitrary_input_equivalence_claimed": False,
        "full_hilbert_space_certificate_claimed": False,
        "local_u3_pricing_accepted": False,
        "resource_saving_claimed": False,
        "b7_ledger_improvement_claimed": False,
        "validation_error_count": len(errors),
    }
    return {
        "benchmark_id": "B1",
        "linked_b7_problem_id": 21,
        "method": METHOD,
        "status": STATUS if passed else "cone01_openqasm3_qiskit_loader_composable_patch_lift_rejected",
        "model_status": MODEL_STATUS if passed else "qiskit_loader_composable_patch_lift_support_rejected",
        "workload": "qasmbench_medium_exact/gcm_h6.qasm",
        "claim_boundary": {
            "supported_claim": (
                "The OpenQASM 3 composable patch-lift artifact is supported on the "
                "Qiskit-loader path by a passing loader parse, global-phase subspace replay, "
                "and six-dimensional finite linear-span certificate for the same candidate."
            ),
            "qiskit_loader_parse_claimed": True,
            "qiskit_loader_linear_span_certificate_claimed": True,
            "qiskit_loader_composable_patch_lift_support_claimed": passed,
            "symbolic_unitary_equivalence_claimed": False,
            "arbitrary_input_equivalence_claimed": False,
            "full_hilbert_space_certificate_claimed": False,
            "local_u3_pricing_accepted": False,
            "resource_saving_claimed": False,
            "b7_ledger_improvement_claimed": False,
            "unsupported_claims": [
                "This is support for the composable patch lift, not a full-space symbolic unitary proof.",
                "This is not arbitrary-input or full-Hilbert-space coverage.",
                "This does not recover the dropped line-1378 overlap delta.",
                "This does not price or eliminate the remaining line-1381 off-grid local-U3 parameters.",
                "This does not improve the B7 resource ledger.",
            ],
        },
        "summary": summary,
        "validation_errors": errors,
    }


def render_markdown(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    claims = payload["claim_boundary"]
    lines = [
        "# B1/B7 cone_01 OpenQASM 3 Qiskit-Loader Composable Patch Lift Support Gate",
        "",
        f"- Method: `{payload['method']}`",
        f"- Status: `{payload['status']}`",
        f"- Model status: `{payload['model_status']}`",
        f"- Workload: `{payload['workload']}`",
        f"- Supported claim: {claims['supported_claim']}",
        "",
        "## Evidence Chain",
        "",
        f"- OpenQASM 3 patch-lift gate: `{summary['source_openqasm3_patch_lift_gate']}`",
        f"- Qiskit-loader finite-span gate: `{summary['source_qiskit_loader_linear_span_gate']}`",
        f"- Qiskit-loader global-phase gate: `{summary['source_qiskit_loader_global_phase_gate']}`",
        f"- OpenQASM 3 candidate: `{summary['openqasm3_candidate_path']}`",
        "",
        "## Patch-Lift Evidence",
        "",
        f"- Normalized stream match / mismatches / length delta: {summary['normalized_streams_match']} / {summary['stream_mismatch_count']} / {summary['stream_length_delta']}",
        f"- Selected patches / lines / dropped-overlap lines: {summary['selected_patch_count']} / {summary['selected_line_numbers']} / {summary['dropped_overlap_candidate_line_numbers']}",
        f"- Non-overlap / local-unitary certificates: {summary['all_selected_windows_nonoverlap']} / {summary['all_local_unitary_certificates_passed']}",
        f"- Max selected patch residual / entry error: {summary['max_selected_patch_residual_norm']} / {summary['max_selected_patch_entry_error']}",
        "",
        "## Qiskit-Loader Evidence",
        "",
        f"- Qiskit / qiskit-qasm3-import / openqasm3 versions: {summary['qiskit_version']} / {summary['qiskit_qasm3_import_version']} / {summary['openqasm3_package_version']}",
        f"- Qubits / clbits / depth / ops: {summary['qiskit_num_qubits']} / {summary['qiskit_num_clbits']} / {summary['qiskit_depth']} / {summary['qiskit_count_ops']}",
        f"- Global-phase subspace replay passed: {summary['qiskit_loader_global_phase_subspace_replay_passed']}",
        f"- Linear-span certificate passed: {summary['qiskit_loader_linear_span_certificate_passed']}",
        f"- Certified subspace / full input space: {summary['qiskit_loader_certified_input_subspace_dimension']} / {summary['qiskit_loader_full_input_space_dimension']}",
        f"- Linear-span spectral error / max L2 / max probability delta: {summary['qiskit_loader_linear_span_error_spectral_norm']} / {summary['qiskit_loader_max_basis_l2_error']} / {summary['qiskit_loader_max_basis_probability_delta']}",
        f"- Accepted parse / global-phase / finite-span / patch-lift-support artifacts: {summary['accepted_qiskit_loader_parse_artifact_count']} / {summary['accepted_qiskit_loader_global_phase_subspace_replay_artifact_count']} / {summary['accepted_qiskit_loader_linear_span_certificate_count']} / {summary['accepted_qiskit_loader_composable_patch_lift_support_count']}",
        f"- Accepted occurrence / proxy-T reduction / B7 claim: {summary['accepted_occurrence_removal']} / {summary['accepted_proxy_t_reduction']} / {summary['b7_ledger_improvement_claimed']}",
        "",
        "## Claim Boundary",
        "",
        *[f"- {claim}" for claim in claims["unsupported_claims"]],
        "",
        "## Validation",
        "",
        f"- Qiskit-loader patch-lift support passed: {summary['openqasm3_qiskit_loader_composable_patch_lift_supported']}",
        f"- Validation errors: {summary['validation_error_count']}",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    payload = build_payload()
    OUT_JSON.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    OUT_MD.write_text(render_markdown(payload), encoding="utf-8")
    if payload["validation_errors"]:
        raise SystemExit(
            "Qiskit-loader composable patch-lift support gate failed: "
            + "; ".join(payload["validation_errors"])
        )


if __name__ == "__main__":
    main()
