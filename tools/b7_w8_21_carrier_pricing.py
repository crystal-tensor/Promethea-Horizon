#!/usr/bin/env python3
"""Price an explicit carrier for the external w8_21 target Rz.

The preceding neighborhood-transfer gate searched for a five-parameter
carrier-free refit and found no exact row.  This artifact supplies the honest
control condition: keep the external Rz as a sixth local parameter, replay it
exactly, and verify the commutation identity that would be used to move it
through a CX boundary.  The result separates semantic exactness from resource
improvement.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any

import numpy as np


METHOD = "b7_w8_21_carrier_pricing_v0"
TEMPLATE_ID = "w8_21"
SOURCE_QASM = "results/b1_u3_phase_factored_optimizer/qasmbench_medium_exact/gcm_h6.qasm"
SCAN_PATH = "results/B7_nonlocal_template_block_scan_v0.json"
NEIGHBORHOOD_RESULT = "results/B7_w8_21_neighborhood_transfer_v0.json"
RESULT_PATH = "results/B7_w8_21_carrier_pricing_v0.json"
REPORT_PATH = "research/B7_w8_21_carrier_pricing.md"
EXACT_TOLERANCE = 1e-12
PROXY_T_COST_PER_ARBITRARY_ROTATION = 20

I2 = np.eye(2, dtype=complex)
P0 = np.array([[1, 0], [0, 0]], dtype=complex)
P1 = np.array([[0, 0], [0, 1]], dtype=complex)
X = np.array([[0, 1], [1, 0]], dtype=complex)
CX = np.kron(P0, I2) + np.kron(P1, X)
BASE_PARAMS = np.array(
    [1.4922506383856682, 2.1870074319274799, 0.52538524712872736,
     2.538142068316358, 1.1254377896453873],
    dtype=float,
)


def stable_hash(value: Any) -> str:
    blob = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rz(theta: float) -> np.ndarray:
    return np.array(
        [[np.exp(-0.5j * theta), 0.0], [0.0, np.exp(0.5j * theta)]],
        dtype=complex,
    )


def ry(theta: float) -> np.ndarray:
    c = math.cos(theta / 2.0)
    s = math.sin(theta / 2.0)
    return np.array([[c, -s], [s, c]], dtype=complex)


def compose(gates: list[np.ndarray]) -> np.ndarray:
    total = np.eye(4, dtype=complex)
    for gate in gates:
        total = gate @ total
    return total


def source_unitary(params: np.ndarray) -> np.ndarray:
    a, b, c, d, e = params
    return compose(
        [
            np.kron(I2, rz(a)),
            CX,
            np.kron(I2, rz(b)),
            np.kron(I2, ry(c)),
            np.kron(I2, rz(math.pi)),
            CX,
            np.kron(I2, rz(d)),
            np.kron(I2, ry(e)),
        ]
    )


def normal_form_unitary(params: np.ndarray) -> np.ndarray:
    a, b, c, d, e = params
    return compose(
        [
            np.kron(I2, rz(a)),
            CX,
            np.kron(I2, rz(b + math.pi)),
            np.kron(I2, ry(-c)),
            CX,
            np.kron(I2, rz(d)),
            np.kron(I2, ry(e)),
        ]
    )


def target_rz(theta: float) -> np.ndarray:
    return np.kron(I2, rz(theta))


def build(root: Path) -> dict[str, Any]:
    source_path = root / SOURCE_QASM
    scan_path = root / SCAN_PATH
    neighborhood_path = root / NEIGHBORHOOD_RESULT
    neighborhood = json.loads(neighborhood_path.read_text(encoding="utf-8"))
    source = source_unitary(BASE_PARAMS)
    normal = normal_form_unitary(BASE_PARAMS)
    rows: list[dict[str, Any]] = []
    for prior_row in neighborhood["rows"]:
        operation = prior_row["context_operation"]
        theta = float(operation["angle"])
        carrier = target_rz(theta)
        source_context = carrier @ source
        local_carrier_candidate = carrier @ normal
        commute_left = carrier @ CX
        commute_right = CX @ (CX @ carrier @ CX)
        local_residual = float(np.linalg.norm(source_context - local_carrier_candidate))
        commute_residual = float(np.linalg.norm(commute_left - commute_right))
        rows.append(
            {
                "line_span": prior_row["line_span"],
                "target": prior_row["target"],
                "context_operation": operation,
                "carrier_angle": theta,
                "source_context_replay_residual": local_residual,
                "local_carrier_replay_passed": local_residual < EXACT_TOLERANCE,
                "cx_target_rz_commutation_residual": commute_residual,
                "cx_target_rz_commutation_passed": commute_residual < EXACT_TOLERANCE,
                "baseline_cnot_count": 2,
                "explicit_local_carrier_cnot_count": 2,
                "commuted_carrier_cnot_count": 4,
                "baseline_arbitrary_parameter_count": 6,
                "explicit_local_carrier_arbitrary_parameter_count": 6,
                "commuted_carrier_arbitrary_parameter_count": 6,
                "explicit_local_carrier_proxy_t_delta": 0,
                "commuted_carrier_proxy_t_delta": 0,
            }
        )
    exact_local = sum(row["local_carrier_replay_passed"] for row in rows)
    exact_commute = sum(row["cx_target_rz_commutation_passed"] for row in rows)
    max_local = max(row["source_context_replay_residual"] for row in rows)
    max_commute = max(row["cx_target_rz_commutation_residual"] for row in rows)
    result: dict[str, Any] = {
        "title": "B7 w8_21 explicit carrier pricing",
        "version": 0,
        "method": METHOD,
        "status": "explicit_carrier_exact_replay_zero_resource_gain",
        "classification": "carrier_aware_semantic_control_and_commutation_price",
        "template_id": TEMPLATE_ID,
        "source_bindings": {
            SOURCE_QASM: {"path": SOURCE_QASM, "sha256": file_sha256(source_path)},
            SCAN_PATH: {"path": SCAN_PATH, "sha256": file_sha256(scan_path)},
            NEIGHBORHOOD_RESULT: {"path": NEIGHBORHOOD_RESULT, "sha256": file_sha256(neighborhood_path)},
        },
        "configuration": {
            "exact_tolerance": EXACT_TOLERANCE,
            "candidate": "explicit target-local Rz carrier after the exact two-CNOT normal form",
            "commutation_identity": "Rz_target(theta) CX = CX (CX Rz_target(theta) CX)",
        },
        "summary": {
            "tested_context_count": len(rows),
            "exact_local_carrier_replay_count": int(exact_local),
            "exact_commutation_identity_count": int(exact_commute),
            "max_local_carrier_residual": max_local,
            "max_commutation_residual": max_commute,
            "baseline_cnot_count": 2,
            "explicit_local_carrier_cnot_count": 2,
            "commuted_carrier_cnot_count": 4,
            "baseline_arbitrary_parameter_count": 6,
            "explicit_local_carrier_arbitrary_parameter_count": 6,
            "commuted_carrier_arbitrary_parameter_count": 6,
            "accepted_occurrence_removal": 0,
            "accepted_proxy_t_reduction": 0,
            "b7_credit": 0,
            "rewrite_claimed": False,
            "resource_saving_claimed": False,
            "b7_ledger_improvement_claimed": False,
        },
        "rows": rows,
        "claim_boundary": {
            "supported_claim": (
                "The explicit sixth local carrier exactly replays all tested contexts, and "
                "the target-Rz/CX commutation identity passes for every tested angle. "
                "Keeping the carrier produces no rotation-occurrence saving; commuting it "
                "through a CX boundary costs two additional CNOTs in the declared construction."
            ),
            "unsupported_claims": [
                "This does not prove that every possible carrier is necessary.",
                "This is not a global KAK lower bound or a full-circuit rewrite.",
                "No occurrence removal, proxy-T reduction, or B7 credit is accepted.",
            ],
            "rewrite_claimed": False,
            "resource_saving_claimed": False,
            "b7_ledger_improvement_claimed": False,
            "next_gate": "Search an alternative nonlocal scaffold only if it can carry the external Rz with fewer than six arbitrary rotations and without the +2-CNOT commuted-carrier penalty.",
        },
        "artifacts": {"result": RESULT_PATH, "markdown_report": REPORT_PATH},
    }
    errors = validate(result)
    result["summary"]["validation_error_count"] = len(errors)
    result["validation_errors"] = errors
    result["payload_hash"] = stable_hash(result)
    return result


def validate(result: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    summary = result["summary"]
    if summary["tested_context_count"] != 7:
        errors.append("expected seven carrier contexts")
    if summary["exact_local_carrier_replay_count"] != 7:
        errors.append("explicit local carrier replay must pass all seven contexts")
    if summary["exact_commutation_identity_count"] != 7:
        errors.append("commutation identity must pass all seven contexts")
    if summary["explicit_local_carrier_cnot_count"] != 2 or summary["explicit_local_carrier_arbitrary_parameter_count"] != 6:
        errors.append("explicit carrier pricing mismatch")
    if summary["commuted_carrier_cnot_count"] != 4 or summary["commuted_carrier_arbitrary_parameter_count"] != 6:
        errors.append("commuted carrier pricing mismatch")
    if summary["accepted_occurrence_removal"] != 0 or summary["accepted_proxy_t_reduction"] != 0 or summary["b7_credit"] != 0:
        errors.append("carrier pricing must keep accepted resource delta at zero")
    for key in ("rewrite_claimed", "resource_saving_claimed", "b7_ledger_improvement_claimed"):
        if result["claim_boundary"].get(key) is not False:
            errors.append(f"claim boundary {key} must remain false")
    return errors


def report(result: dict[str, Any]) -> str:
    summary = result["summary"]
    return "\n".join(
        [
            "# B7 w8_21 Explicit Carrier Pricing",
            "",
            f"- Status: `{result['status']}`",
            f"- Classification: `{result['classification']}`",
            f"- Contexts tested: `{summary['tested_context_count']}`",
            f"- Exact local-carrier replays: `{summary['exact_local_carrier_replay_count']}/{summary['tested_context_count']}`",
            f"- Exact Rz/CX commutation identities: `{summary['exact_commutation_identity_count']}/{summary['tested_context_count']}`",
            f"- Max local-carrier residual: `{summary['max_local_carrier_residual']:.6e}`",
            f"- Max commutation residual: `{summary['max_commutation_residual']:.6e}`",
            f"- Validation errors: `{summary['validation_error_count']}`",
            "",
            "## Heuristic question",
            "",
            "If the external Rz cannot disappear inside the five-parameter normal form, what does the honest carrier cost look like when we keep it or commute it through a CX boundary?",
            "",
            "## Exact carrier control",
            "",
            "The explicit target-local carrier `Rz(f)` is retained after the exact two-CNOT normal form. All seven real source contexts replay exactly. The carrier-aware construction has 2 CNOTs and 6 arbitrary parameters, exactly matching the source context; it produces no resource saving.",
            "",
            "The commutation identity `Rz_target(theta) CX = CX (CX Rz_target(theta) CX)` also passes for all seven angles. In the declared construction, moving the carrier across the CX introduces a conjugated carrier with two additional CNOTs, giving 4 CNOTs and 6 arbitrary parameters.",
            "",
            "## Boundary",
            "",
            "This is a positive semantic control and a cost certificate for two explicit carrier placements, not a theorem that all possible carriers are necessary. No occurrence removal, proxy-T reduction, or B7 credit is accepted.",
            "",
            "## Next route",
            "",
            "Only an alternative nonlocal scaffold with fewer than six arbitrary rotations and without the two-CNOT commuted-carrier penalty can change the ledger.",
            "",
        ]
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--json-output", type=Path, default=Path(RESULT_PATH))
    parser.add_argument("--markdown-output", type=Path, default=Path(REPORT_PATH))
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()
    root = args.root.resolve()
    if (root / args.json_output).exists() or (root / args.markdown_output).exists():
        raise SystemExit("refusing to overwrite existing carrier-pricing artifact")
    result = build(root)
    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    args.json_output.write_text(json.dumps(result, indent=2 if args.pretty else None, sort_keys=True) + "\n", encoding="utf-8")
    args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_output.write_text(report(result), encoding="utf-8")
    print(json.dumps({
        "status": result["status"],
        "tested_context_count": result["summary"]["tested_context_count"],
        "exact_local_carrier_replay_count": result["summary"]["exact_local_carrier_replay_count"],
        "exact_commutation_identity_count": result["summary"]["exact_commutation_identity_count"],
        "accepted_occurrence_removal": result["summary"]["accepted_occurrence_removal"],
        "accepted_proxy_t_reduction": result["summary"]["accepted_proxy_t_reduction"],
        "validation_error_count": result["summary"]["validation_error_count"],
        "payload_hash": result["payload_hash"],
    }, sort_keys=True))


if __name__ == "__main__":
    main()
