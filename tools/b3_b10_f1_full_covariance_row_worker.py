#!/usr/bin/env python3
"""Compute one B3/B10 F1 compiled-state covariance shard."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import resource
import sys
import time
from pathlib import Path
from typing import Any

from b3_compiled_ucc_adapt_covariance_pilot import (
    ANSATZ_THETA,
    build_ucc_terms,
    hf_mask,
    selected_double_excitation_mask,
    ucc_group_variance,
)
from b3_grouped_covariance_shot_floor import grouped_qwc_cover
from b3_hamiltonian_pauli_mapper_comparison import mapped_pauli_terms


METHOD = "b3_b10_f1_full_covariance_row_worker_v0"
STATUS = "full_covariance_shard_computed_zero_credit"
SUPPORTED_STATE_SOURCE = "compiled_ucc_adapt"


def canonical_hash(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def write_json(path: Path, payload: dict[str, Any], pretty: bool) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(
        payload,
        indent=2 if pretty else None,
        sort_keys=True,
        separators=None if pretty else (",", ":"),
    )
    path.write_text(text + "\n", encoding="utf-8")


def load_row_metadata(path: Path, pressure_path: Path, molecule: str) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    pressure = json.loads(pressure_path.read_text(encoding="utf-8"))
    pressure_rows = {row.get("molecule"): row for row in pressure.get("rows", [])}
    for row in data.get("extension_rows", []):
        if row.get("molecule") == molecule:
            merged = dict(pressure_rows.get(molecule, {}))
            merged.update(row)
            return merged
    raise ValueError(f"molecule {molecule!r} not found in {path}")


def build_compiled_groups(row: dict[str, Any]) -> dict[str, Any]:
    qubits, _particles, terms = mapped_pauli_terms(
        molecule=row["molecule"],
        coordinate_center=float(row["coordinate_center"]),
        basis=row["selected_ci_basis"],
    )
    occupied = int(row["electrons"])
    hf = hf_mask(qubits, occupied)
    excited = selected_double_excitation_mask(qubits, occupied)
    determinants = {
        hf: math.cos(ANSATZ_THETA),
        excited: math.sin(ANSATZ_THETA),
    }
    random_terms = build_ucc_terms(terms, determinants, qubits)
    cover = grouped_qwc_cover(random_terms)
    return {
        "qubits": qubits,
        "occupied": occupied,
        "hf_determinant_mask": hf,
        "excited_determinant_mask": excited,
        "determinants": determinants,
        "random_terms": random_terms,
        "cover": cover,
    }


def group_record(global_index: int, group: dict[str, Any], determinants: dict[int, float], qubits: int) -> dict[str, Any]:
    variance = ucc_group_variance(group, determinants, qubits)
    terms = group["terms"]
    term_refs = [
        {
            "pauli": term["pauli"],
            "coefficient": term["coefficient"],
            "weight": term["weight"],
            "expectation": term["expectation"],
        }
        for term in terms
    ]
    record = {
        "group_index": global_index,
        "size": variance["size"],
        "basis_weight": variance["basis_weight"],
        "representative_pauli": variance["representative_pauli"],
        "mean": variance["mean"],
        "group_variance": variance["group_variance"],
        "sqrt_group_variance": variance["sqrt_group_variance"],
        "covariance_shift": variance["covariance_shift"],
        "nonzero_covariance_pairs": variance["nonzero_covariance_pairs"],
        "terms_hash": canonical_hash(term_refs),
        "term_count": len(term_refs),
    }
    record["group_covariance_hash"] = canonical_hash(record)
    return record


def build_payload(args: argparse.Namespace) -> dict[str, Any]:
    started = time.perf_counter()
    row = load_row_metadata(args.remaining_row_scout, args.cross_molecule_pressure, args.molecule)
    compiled = build_compiled_groups(row)
    cover = compiled["cover"]
    groups = cover["groups"]
    if args.group_start < 0 or args.group_end <= args.group_start:
        raise ValueError("invalid group range")
    if args.group_end > len(groups):
        raise ValueError(f"group_end {args.group_end} exceeds cover size {len(groups)}")

    selected = groups[args.group_start : args.group_end]
    group_records = [
        group_record(args.group_start + idx, group, compiled["determinants"], compiled["qubits"])
        for idx, group in enumerate(selected)
    ]
    matrix_summary = {
        "group_count": len(group_records),
        "nonzero_covariance_pair_count": sum(item["nonzero_covariance_pairs"] for item in group_records),
        "variance_sum": sum(item["group_variance"] for item in group_records),
        "sqrt_variance_sum": sum(item["sqrt_group_variance"] for item in group_records),
        "max_group_size": max((item["size"] for item in group_records), default=0),
        "max_basis_weight": max((item["basis_weight"] for item in group_records), default=0),
    }
    qwc_manifest = {
        "qwc_grouping_algorithm": "bitmask_first_fit_qwc_cover_weight_ascending",
        "compiled_qwc_group_count": len(groups),
        "compiled_random_term_count": len(compiled["random_terms"]),
        "qwc_grouping_wall_time_seconds": cover["qwc_grouping_wall_time_seconds"],
        "group_start_inclusive": args.group_start,
        "group_end_exclusive": args.group_end,
        "group_hashes": [item["group_covariance_hash"] for item in group_records],
    }
    measurement_manifest = {
        "measurement_basis_mode": "qwc_group_basis_from_compiled_cover",
        "state_source": args.state_source,
        "exact_or_shot_mode": "exact_two_determinant_state_covariance",
        "ansatz_theta": ANSATZ_THETA,
    }
    wall_time_seconds = time.perf_counter() - started
    rss_kb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    payload = {
        "benchmark_id": "B3_B10",
        "title": "B3/B10 F1 Full Covariance Shard",
        "version": "0.1",
        "last_updated": args.last_updated,
        "status": STATUS,
        "method": METHOD,
        "molecule": args.molecule,
        "coordinate": row["coordinate"],
        "selected_ci_basis": row["selected_ci_basis"],
        "state_source": args.state_source,
        "shard_id": f"{args.molecule}-full-covariance-shard-{(args.group_start // max(1, args.groups_per_shard)) + 1:03d}",
        "group_start_inclusive": args.group_start,
        "group_end_exclusive": args.group_end,
        "compiled_state_replay": {
            "total_qubits": compiled["qubits"],
            "electrons": compiled["occupied"],
            "hf_determinant_mask": compiled["hf_determinant_mask"],
            "excited_determinant_mask": compiled["excited_determinant_mask"],
            "ansatz_theta": ANSATZ_THETA,
        },
        "qwc_group_manifest": qwc_manifest,
        "measurement_basis_manifest": measurement_manifest,
        "full_covariance_matrix_shard": {
            "matrix_representation": "group_observable_variance_and_pair_covariance_summary",
            "groups": group_records,
            "summary": matrix_summary,
        },
        "worker_ledger": {
            "argv": sys.argv,
            "wall_time_seconds": wall_time_seconds,
            "max_rss_kb": rss_kb,
            "returncode": 0,
        },
        "claim_boundary": {
            "what_is_supported": "One exact two-determinant compiled-state covariance shard was computed for the requested group range.",
            "what_is_not_supported": "This is not a full row, not an assembled F1 artifact, not a denominator win, not B3/B10 credit, and not quantum advantage.",
        },
    }
    payload["compiled_state_replay_hash"] = canonical_hash(payload["compiled_state_replay"])
    payload["qwc_group_manifest_hash"] = canonical_hash(qwc_manifest)
    payload["measurement_basis_manifest_hash"] = canonical_hash(measurement_manifest)
    payload["full_covariance_matrix_shard_hash"] = canonical_hash(payload["full_covariance_matrix_shard"])
    payload["stdout_stderr_returncode_hash"] = canonical_hash(
        {"stdout": "", "stderr": "", "returncode": 0}
    )
    payload["wall_time_memory_ledger_hash"] = canonical_hash(payload["worker_ledger"])
    payload["claim_boundary_hash"] = canonical_hash(payload["claim_boundary"])
    payload["validation_errors"] = []
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--molecule", required=True)
    parser.add_argument("--group-start", type=int, required=True)
    parser.add_argument("--group-end", type=int, required=True)
    parser.add_argument("--groups-per-shard", type=int, default=512)
    parser.add_argument("--state-source", default=SUPPORTED_STATE_SOURCE)
    parser.add_argument(
        "--remaining-row-scout",
        type=Path,
        default=Path("results/B3_B10_F1_remaining_row_extension_scout_v0.json"),
    )
    parser.add_argument(
        "--cross-molecule-pressure",
        type=Path,
        default=Path("results/B3_cross_molecule_ucc_adapt_pressure_v0.json"),
    )
    parser.add_argument("--output", type=Path)
    parser.add_argument("--last-updated", default="2026-07-03")
    parser.add_argument("--pretty", action="store_true")
    parser.add_argument("--emit-shard-json", action="store_true")
    args = parser.parse_args()
    if args.state_source != SUPPORTED_STATE_SOURCE:
        raise SystemExit(f"unsupported state source: {args.state_source}")
    if args.output is None:
        shard_id = (args.group_start // max(1, args.groups_per_shard)) + 1
        args.output = Path(
            f"results/B3_B10_F1_full_covariance_shards/{args.molecule}/shard_{shard_id:03d}.json"
        )
    payload = build_payload(args)
    write_json(args.output, payload, args.pretty)
    print(
        json.dumps(
            {
                "status": payload["status"],
                "molecule": payload["molecule"],
                "shard_id": payload["shard_id"],
                "group_count": payload["full_covariance_matrix_shard"]["summary"]["group_count"],
                "full_covariance_matrix_shard_hash": payload["full_covariance_matrix_shard_hash"],
                "output": str(args.output),
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
