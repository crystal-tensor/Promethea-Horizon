#!/usr/bin/env python3
"""Test larger-neighborhood parameter transfer for the w8_21 normal form.

The existing context gate only replayed the fixed five-parameter normal form
and observed that seven selected occurrences are followed by a same-target
arbitrary Rz.  This gate asks the stronger local question: can the whole
``w8_21 + following Rz`` context be refit into the same two-CNOT, five-
parameter normal form, thereby removing the extra rotation without adding a
parameter carrier?

This is a bounded numerical refit, not a global lower bound. A passing row
would still require a source-backed semantic replay and a full-circuit
resource certificate before any B7 credit could be counted.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
from pathlib import Path
from typing import Any

import numpy as np
from scipy.optimize import least_squares


METHOD = "b7_w8_21_neighborhood_transfer_v0"
TEMPLATE_ID = "w8_21"
SOURCE_QASM = "results/b1_u3_phase_factored_optimizer/qasmbench_medium_exact/gcm_h6.qasm"
SCAN_PATH = "results/B7_nonlocal_template_block_scan_v0.json"
RESULT_PATH = "results/B7_w8_21_neighborhood_transfer_v0.json"
REPORT_PATH = "research/B7_w8_21_neighborhood_transfer.md"
EXACT_TOLERANCE = 1e-10
PROXY_T_COST_PER_ARBITRARY_ROTATION = 20
SEED_COUNT = 12
MAX_NFEV = 2500

I2 = np.eye(2, dtype=complex)
P0 = np.array([[1, 0], [0, 0]], dtype=complex)
P1 = np.array([[0, 0], [0, 1]], dtype=complex)
X = np.array([[0, 1], [1, 0]], dtype=complex)
CX = np.kron(P0, I2) + np.kron(P1, X)
GATE_RE = re.compile(
    r"^(?P<gate>rz|ry)\((?P<angle>[^)]*)\) q\[(?P<q0>\d+)\];$"
)
CX_RE = re.compile(r"^cx q\[(?P<q0>\d+)\],q\[(?P<q1>\d+)\];$")

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


def parse_angle(text: str) -> float:
    expression = text.strip().replace("pi", "math.pi")
    return float(eval(expression, {"__builtins__": {}, "math": math}))


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


def parse_operation(line: str, line_number: int) -> dict[str, Any] | None:
    stripped = line.strip()
    match = CX_RE.match(stripped)
    if match:
        return {
            "line": line_number,
            "text": stripped,
            "gate": "cx",
            "qubits": [int(match.group("q0")), int(match.group("q1"))],
            "angle": None,
        }
    match = GATE_RE.match(stripped)
    if match:
        return {
            "line": line_number,
            "text": stripped,
            "gate": match.group("gate"),
            "qubits": [int(match.group("q0"))],
            "angle": parse_angle(match.group("angle")),
        }
    return None


def target_local_matrix(operation: dict[str, Any], target: int) -> np.ndarray | None:
    if operation["qubits"] != [target] or operation["gate"] not in {"rz", "ry"}:
        return None
    local = rz(operation["angle"]) if operation["gate"] == "rz" else ry(operation["angle"])
    return np.kron(I2, local)


def residual_vector(candidate: np.ndarray, target: np.ndarray) -> np.ndarray:
    diff = candidate - target
    return np.concatenate([diff.real.ravel(), diff.imag.ravel()])


def projective_residual(candidate: np.ndarray, target: np.ndarray) -> float:
    overlap = np.vdot(target, candidate)
    phase = overlap / abs(overlap) if abs(overlap) > 1e-15 else 1.0 + 0.0j
    return float(np.linalg.norm(candidate - phase * target))


def deterministic_seeds() -> list[np.ndarray]:
    seeds = [BASE_PARAMS.copy()]
    for index in range(1, SEED_COUNT):
        offsets = np.array(
            [
                ((17 * index + 3) % 19 - 9) * math.pi / 19.0,
                ((29 * index + 5) % 23 - 11) * math.pi / 23.0,
                ((11 * index + 7) % 17 - 8) * math.pi / 17.0,
                ((37 * index + 2) % 29 - 14) * math.pi / 29.0,
                ((43 * index + 9) % 31 - 15) * math.pi / 31.0,
            ]
        )
        seeds.append(BASE_PARAMS + offsets)
    return seeds


def fit_context(target_matrix: np.ndarray) -> dict[str, Any]:
    best: dict[str, Any] | None = None
    for seed_index, seed in enumerate(deterministic_seeds()):
        fit = least_squares(
            lambda params: residual_vector(normal_form_unitary(params), target_matrix),
            seed,
            bounds=(-2.0 * math.pi, 2.0 * math.pi),
            method="trf",
            max_nfev=MAX_NFEV,
            xtol=1e-13,
            ftol=1e-13,
            gtol=1e-13,
        )
        candidate = normal_form_unitary(fit.x)
        row = {
            "seed_index": seed_index,
            "optimizer_success": bool(fit.success),
            "optimizer_status": int(fit.status),
            "optimizer_nfev": int(fit.nfev),
            "objective_residual": float(np.linalg.norm(candidate - target_matrix)),
            "projective_residual": projective_residual(candidate, target_matrix),
            "fitted_parameters": [float(value) for value in fit.x],
        }
        if best is None or (
            row["objective_residual"], row["seed_index"]
        ) < (best["objective_residual"], best["seed_index"]):
            best = row
    assert best is not None
    best["exact_fit_passed"] = bool(best["objective_residual"] < EXACT_TOLERANCE)
    return best


def context_rows(root: Path) -> list[dict[str, Any]]:
    qasm_lines = (root / SOURCE_QASM).read_text(encoding="utf-8").splitlines()
    operations = [
        operation
        for index, line in enumerate(qasm_lines, start=1)
        if (operation := parse_operation(line, index)) is not None
    ]
    by_line = {operation["line"]: operation for operation in operations}
    scan = json.loads((root / SCAN_PATH).read_text(encoding="utf-8"))
    rows = []
    for start, end in scan["best_template"]["selected_line_spans"]:
        block = [by_line[line] for line in range(start, end + 1)]
        target = block[0]["qubits"][0]
        control = block[1]["qubits"][0]
        if [operation["gate"] for operation in block] != ["rz", "cx", "rz", "ry", "rz", "cx", "rz", "ry"]:
            raise ValueError(f"unexpected w8_21 block at {start}-{end}")
        before = by_line.get(start - 1)
        after = by_line.get(end + 1)
        before_matrix = target_local_matrix(before, target) if before else None
        after_matrix = target_local_matrix(after, target) if after else None
        if before_matrix is not None:
            context_matrix = source_unitary(BASE_PARAMS) @ before_matrix
            direction = "before"
            context_operation = before
        elif after_matrix is not None:
            context_matrix = after_matrix @ source_unitary(BASE_PARAMS)
            direction = "after"
            context_operation = after
        else:
            continue
        fit = fit_context(context_matrix)
        baseline_arbitrary_count = 5 + int(
            context_operation["gate"] in {"rz", "ry"}
            and abs(context_operation["angle"] / (math.pi / 4.0) - round(context_operation["angle"] / (math.pi / 4.0))) > 1e-10
        )
        rows.append(
            {
                "line_span": [start, end],
                "target": target,
                "control": control,
                "direction": direction,
                "context_operation": context_operation,
                "baseline_cnot_count": 2,
                "candidate_cnot_count": 2,
                "baseline_arbitrary_parameter_count": baseline_arbitrary_count,
                "candidate_arbitrary_parameter_count": 5,
                "candidate_arbitrary_rotation_saving_if_exact": baseline_arbitrary_count - 5,
                "fit": fit,
                "accepted_occurrence_removal": int(fit["exact_fit_passed"]),
                "accepted_proxy_t_reduction": int(fit["exact_fit_passed"]) * PROXY_T_COST_PER_ARBITRARY_ROTATION,
            }
        )
    return rows


def validate(result: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    summary = result["summary"]
    if summary["selected_occurrence_count"] != 16:
        errors.append("selected occurrence count mismatch")
    if summary["tested_context_count"] != 7:
        errors.append("expected seven immediate same-target contexts")
    if summary["exact_fit_count"] != 0:
        errors.append("a source-backed exact fit unexpectedly appeared; promote it to replay review")
    if summary["accepted_occurrence_removal"] != 0:
        errors.append("accepted occurrence removal must remain zero")
    if summary["accepted_proxy_t_reduction"] != 0:
        errors.append("accepted proxy-T reduction must remain zero")
    for key in ("rewrite_claimed", "resource_saving_claimed", "b7_ledger_improvement_claimed"):
        if result["claim_boundary"].get(key) is not False:
            errors.append(f"claim boundary {key} must remain false")
    return errors


def build(root: Path) -> dict[str, Any]:
    source_qasm = root / SOURCE_QASM
    scan_path = root / SCAN_PATH
    scan = json.loads(scan_path.read_text(encoding="utf-8"))
    rows = context_rows(root)
    exact_fit_count = sum(row["fit"]["exact_fit_passed"] for row in rows)
    accepted_removal = sum(row["accepted_occurrence_removal"] for row in rows)
    best_residual = min((row["fit"]["objective_residual"] for row in rows), default=None)
    result: dict[str, Any] = {
        "title": "B7 w8_21 larger-neighborhood parameter transfer",
        "version": 0,
        "method": METHOD,
        "status": "larger_neighborhood_refit_complete_no_resource_reduction",
        "classification": "bounded_same_skeleton_context_refit_boundary",
        "template_id": TEMPLATE_ID,
        "source_bindings": {
            SOURCE_QASM: {"path": SOURCE_QASM, "sha256": file_sha256(source_qasm)},
            SCAN_PATH: {"path": SCAN_PATH, "sha256": file_sha256(scan_path)},
        },
        "fit_configuration": {
            "seed_count": SEED_COUNT,
            "max_nfev": MAX_NFEV,
            "exact_tolerance": EXACT_TOLERANCE,
            "optimizer": "scipy.optimize.least_squares",
            "candidate_family": "same_two_cnot_w8_21_normal_form_with_five_free_angles",
        },
        "summary": {
            "selected_occurrence_count": len(scan["best_template"]["selected_line_spans"]),
            "tested_context_count": len(rows),
            "after_context_count": sum(row["direction"] == "after" for row in rows),
            "before_context_count": sum(row["direction"] == "before" for row in rows),
            "exact_fit_count": int(exact_fit_count),
            "best_objective_residual": best_residual,
            "accepted_occurrence_removal": int(accepted_removal),
            "accepted_proxy_t_reduction": int(accepted_removal) * PROXY_T_COST_PER_ARBITRARY_ROTATION,
            "b7_credit": 0,
            "rewrite_claimed": False,
            "resource_saving_claimed": False,
            "b7_ledger_improvement_claimed": False,
        },
        "rows": rows,
        "claim_boundary": {
            "supported_claim": (
                "The seven selected immediate same-target contexts were refit against the same "
                "two-CNOT, five-parameter normal form; no exact fit was found under the declared "
                "deterministic bounded numerical search."
            ),
            "unsupported_claims": [
                "This is not a global KAK or circuit lower bound.",
                "It does not exclude other CNOT placements, Euler scaffolds, commutation routes, or ancillas.",
                "It does not provide a full-circuit rewrite or physical-layout result.",
                "No occurrence removal, proxy-T reduction, or B7 credit is accepted.",
            ],
            "rewrite_claimed": False,
            "resource_saving_claimed": False,
            "b7_ledger_improvement_claimed": False,
            "next_gate": "Try a commutation-aware candidate that explicitly carries the external Rz, then price the carrier before replay.",
        },
        "artifacts": {"result": RESULT_PATH, "markdown_report": REPORT_PATH},
    }
    result["summary"]["validation_error_count"] = len(validate(result))
    result["validation_errors"] = validate(result)
    result["payload_hash"] = stable_hash(result)
    return result


def report(result: dict[str, Any]) -> str:
    summary = result["summary"]
    lines = [
        "# B7 w8_21 Larger-Neighborhood Parameter Transfer",
        "",
        f"- Status: `{result['status']}`",
        f"- Classification: `{result['classification']}`",
        f"- Selected w8_21 occurrences: `{summary['selected_occurrence_count']}`",
        f"- Same-target contexts tested: `{summary['tested_context_count']}`",
        f"- Exact five-parameter refits: `{summary['exact_fit_count']}`",
        f"- Best objective residual: `{summary['best_objective_residual']:.6e}`",
        f"- Accepted occurrence removal: `{summary['accepted_occurrence_removal']}`",
        f"- Accepted proxy-T reduction: `{summary['accepted_proxy_t_reduction']}`",
        f"- Validation errors: `{summary['validation_error_count']}`",
        "",
        "## Heuristic question",
        "",
        "Can the exact w8_21 invariant absorb an adjacent arbitrary Rz by refitting the same two-CNOT, five-parameter normal form, or does the extra local degree of freedom require a new carrier?",
        "",
        "## Experiment",
        "",
        "The upstream real-circuit replay found seven selected non-overlapping w8_21 spans immediately followed by the same-target arbitrary rotation `rz(0.28861107553559073)`. For each row, the complete context was formed as `Rz(f) * S(a,b,c,d,e)` and fit to the existing five-parameter two-CNOT normal form using 12 deterministic seeds and a declared least-squares tolerance of `1e-10`.",
        "",
        f"No exact fit was found in `{summary['exact_fit_count']}/{summary['tested_context_count']}` contexts. The best residual was `{summary['best_objective_residual']:.6e}`. This closes only the declared same-skeleton refit route; it is not a global obstruction theorem.",
        "",
        "## Resource boundary",
        "",
        "Because no exact source-backed refit exists, the candidate cannot remove the external arbitrary rotation. Accepted occurrence removal, proxy-T reduction, and B7 credit remain zero.",
        "",
        "## Next route",
        "",
        "The next experiment must carry the external Rz through a commutation-aware scaffold and price every new local parameter before any semantic replay or ledger claim.",
    ]
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--json-output", type=Path, default=Path(RESULT_PATH))
    parser.add_argument("--markdown-output", type=Path, default=Path(REPORT_PATH))
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()
    root = args.root.resolve()
    if (root / args.json_output).exists() or (root / args.markdown_output).exists():
        raise SystemExit("refusing to overwrite existing neighborhood-transfer artifact")
    result = build(root)
    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    args.json_output.write_text(json.dumps(result, indent=2 if args.pretty else None, sort_keys=True) + "\n", encoding="utf-8")
    args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_output.write_text(report(result), encoding="utf-8")
    print(json.dumps({
        "status": result["status"],
        "tested_context_count": result["summary"]["tested_context_count"],
        "exact_fit_count": result["summary"]["exact_fit_count"],
        "best_objective_residual": result["summary"]["best_objective_residual"],
        "accepted_occurrence_removal": result["summary"]["accepted_occurrence_removal"],
        "accepted_proxy_t_reduction": result["summary"]["accepted_proxy_t_reduction"],
        "validation_error_count": result["summary"]["validation_error_count"],
        "payload_hash": result["payload_hash"],
    }, sort_keys=True))


if __name__ == "__main__":
    main()
