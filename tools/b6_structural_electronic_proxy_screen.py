#!/usr/bin/env python3
"""Structural/electronic proxy screen for B6 high-Tc ranking."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

sys.path.append(str(Path(__file__).resolve().parent))

from b6_formula_descriptor_screen import (  # noqa: E402
    average_precision,
    enrich_records,
    family_prior_score,
    precision_at_k,
)


METHOD = "b6_structural_electronic_proxy_screen_v0"
STATUS = "structural_electronic_proxy_boundary_not_material_discovery_claim"


def infer_dimensionality(record: dict[str, Any]) -> float:
    if record.get("dimensionality") is not None:
        return float(record["dimensionality"])
    if record["hydrogen_fraction"] > 0.5:
        return 3.0
    if record["anion_layer_fraction"] > 0.45 and record["active_pairing_element_fraction"] > 0:
        return 2.0
    if record["oxygen_fraction"] > 0.4:
        return 2.4
    return 3.0


def value_or_proxy(record: dict[str, Any], key: str, proxy: float) -> float:
    value = record.get(key)
    if value is None:
        return proxy
    return float(value)


def structural_electronic_descriptors(record: dict[str, Any]) -> dict[str, Any]:
    dimensionality = infer_dimensionality(record)
    layered_anisotropy_proxy = 1.0 / (1.0 + abs(dimensionality - 2.0))
    correlation = value_or_proxy(
        record,
        "correlation_strength",
        min(1.0, 1.5 * record["b5_correlation_pressure_proxy"]),
    )
    spin_fluctuation = value_or_proxy(
        record,
        "spin_fluctuation",
        min(
            1.0,
            1.3 * record["active_pairing_element_fraction"]
            + 0.2 * record["b5_hubbard_screening_proxy"],
        ),
    )
    phonon_lambda = value_or_proxy(
        record,
        "phonon_lambda",
        min(1.0, 0.7 * record["light_element_fraction"] + 0.4 * record["hydrogen_fraction"]),
    )
    carrier_tunability = value_or_proxy(
        record,
        "carrier_tunability",
        min(1.0, record["valence_std_proxy"] / 3.0),
    )
    disorder_risk = value_or_proxy(
        record,
        "disorder_risk",
        0.6 if record["unknown_formula_tokens"] else 0.25,
    )
    competing_order = value_or_proxy(
        record,
        "competing_order",
        min(1.0, 0.8 * correlation * spin_fluctuation),
    )
    pressure_penalty = min(1.0, float(record.get("pressure_gpa", 0.0)) / 80.0)
    b5_structural_response_proxy = (
        0.45 * correlation
        + 0.30 * spin_fluctuation
        + 0.15 * carrier_tunability
        + 0.10 * layered_anisotropy_proxy
    )
    structure_electronic_score = (
        1.10 * correlation
        + 0.90 * spin_fluctuation
        + 0.75 * carrier_tunability
        + 0.65 * layered_anisotropy_proxy
        + 0.40 * phonon_lambda
        - 0.70 * disorder_risk
        - 0.55 * competing_order
        - 0.80 * pressure_penalty
    )
    return {
        "inferred_dimensionality": dimensionality,
        "layered_anisotropy_proxy": layered_anisotropy_proxy,
        "electronic_correlation_proxy": correlation,
        "spin_fluctuation_proxy": spin_fluctuation,
        "phonon_lambda_proxy": phonon_lambda,
        "carrier_tunability_proxy": carrier_tunability,
        "disorder_risk_proxy": disorder_risk,
        "competing_order_proxy": competing_order,
        "pressure_penalty": pressure_penalty,
        "b5_structural_response_proxy": b5_structural_response_proxy,
        "structure_electronic_score": structure_electronic_score,
    }


def family_holdout_ap(records: list[dict[str, Any]], top_k: int) -> dict[str, Any]:
    families = sorted({row["family"] for row in records})
    rows = []
    for family in families:
        train = [row for row in records if row["family"] != family]
        test = [row for row in records if row["family"] == family]
        if not test or not any(row["is_high_tc"] for row in test):
            continue
        train_mean = sum(row["structure_electronic_score"] for row in train) / len(train)
        ranked = sorted(
            test,
            key=lambda row: (
                row["structure_electronic_score"] - train_mean,
                row["structure_electronic_score"],
            ),
            reverse=True,
        )
        rows.append(
            {
                "held_out_family": family,
                "test_count": len(test),
                "positive_count": sum(1 for row in test if row["is_high_tc"]),
                "ap_at_k": average_precision(ranked, min(top_k, len(ranked))),
                "precision_at_k": precision_at_k(ranked, min(top_k, len(ranked))),
            }
        )
    mean_ap = sum(row["ap_at_k"] for row in rows) / len(rows) if rows else 0.0
    return {"rows": rows, "mean_ap": mean_ap}


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    records = enrich_records(args.high_tc_threshold)
    for record in records:
        record.update(structural_electronic_descriptors(record))
    ranked = sorted(records, key=lambda row: row["structure_electronic_score"], reverse=True)
    formula_ranked = sorted(records, key=lambda row: row["formula_descriptor_score"], reverse=True)
    priors = family_prior_score(records)
    family_ranked = sorted(records, key=lambda row: priors[row["family"]], reverse=True)
    post_split = [row for row in records if int(row["discovery_year"]) > args.split_year]
    post_ranked = sorted(post_split, key=lambda row: row["structure_electronic_score"], reverse=True)
    post_formula_ranked = sorted(post_split, key=lambda row: row["formula_descriptor_score"], reverse=True)
    post_family_ranked = sorted(post_split, key=lambda row: priors[row["family"]], reverse=True)
    holdout = family_holdout_ap(records, args.top_k)
    negative_top_k_count = sum(1 for row in ranked[: args.top_k] if not row["is_high_tc"])
    post_k = min(args.top_k, len(post_split))
    metrics = {
        "structural_precision_at_k": precision_at_k(ranked, args.top_k),
        "structural_average_precision_at_k": average_precision(ranked, args.top_k),
        "formula_average_precision_at_k": average_precision(formula_ranked, args.top_k),
        "family_prior_average_precision_at_k": average_precision(family_ranked, args.top_k),
        "post_split_structural_average_precision_at_k": average_precision(post_ranked, post_k),
        "post_split_formula_average_precision_at_k": average_precision(post_formula_ranked, post_k),
        "post_split_family_prior_average_precision_at_k": average_precision(post_family_ranked, post_k),
        "family_holdout_structural_mean_ap": holdout["mean_ap"],
        "top_k_negative_control_count": negative_top_k_count,
        "structural_minus_formula_ap": average_precision(ranked, args.top_k)
        - average_precision(formula_ranked, args.top_k),
        "structural_minus_family_prior_ap": average_precision(ranked, args.top_k)
        - average_precision(family_ranked, args.top_k),
    }
    validation_errors = []
    if metrics["structural_average_precision_at_k"] <= metrics["formula_average_precision_at_k"]:
        validation_errors.append("structural proxy should improve over formula-only AP in this boundary run")
    if metrics["structural_average_precision_at_k"] >= metrics["family_prior_average_precision_at_k"]:
        validation_errors.append("structural proxy unexpectedly beats family-prior leakage baseline")
    if negative_top_k_count <= 0:
        validation_errors.append("expected negative-control pressure in top-k rows")
    return {
        "benchmark_id": "B6",
        "problem_id": 37,
        "title": "B6 structural/electronic proxy screen",
        "status": STATUS,
        "method": METHOD,
        "model_status": "curated_structural_electronic_proxies_not_dft_or_crystallographic_database",
        "high_tc_threshold_k": args.high_tc_threshold,
        "split_year": args.split_year,
        "top_k": args.top_k,
        "record_count": len(records),
        "curated_record_count": sum(1 for row in records if row["source_subset"] == "curated"),
        "expanded_negative_control_count": sum(
            1 for row in records if row["source_subset"] == "negative_control"
        ),
        "family_count": len({row["family"] for row in records}),
        "post_split_record_count": len(post_split),
        "post_split_positive_count": sum(1 for row in post_split if row["is_high_tc"]),
        "descriptor_channels": [
            "inferred_dimensionality",
            "layered_anisotropy_proxy",
            "electronic_correlation_proxy",
            "spin_fluctuation_proxy",
            "phonon_lambda_proxy",
            "carrier_tunability_proxy",
            "disorder_risk_proxy",
            "competing_order_proxy",
            "b5_structural_response_proxy",
            "structure_electronic_score",
        ],
        "metrics": metrics,
        "family_holdout": holdout,
        "claim_boundary": {
            "material_discovery_claimed": False,
            "mechanism_solved": False,
            "complete_materials_database": False,
            "computed_quantum_observable_claimed": False,
            "real_dft_claimed": False,
            "real_crystallographic_database_claimed": False,
            "uses_formula_derived_descriptors": False,
            "uses_structural_electronic_proxies": True,
            "uses_b5_linked_proxy": True,
            "what_is_supported": (
                "Curated structural/electronic proxy channels improve over formula-only ranking, "
                "while exposing remaining family-prior leakage and top-k negative-control pressure."
            ),
            "what_is_not_supported": (
                "This is not a material discovery, solved high-Tc mechanism, complete database, "
                "real DFT calculation, crystallographic database pull, or computed quantum observable."
            ),
        },
        "top_structural_rows": ranked[: args.top_k],
        "top_post_split_structural_rows": post_ranked[:post_k],
        "records": records,
        "validation_errors": validation_errors,
    }


def markdown(report: dict[str, Any]) -> str:
    metrics = report["metrics"]
    lines = [
        "# B6 Structural/Electronic Proxy Screen v0.1",
        "",
        f"- Status: {report['status']}",
        f"- Method: {report['method']}",
        f"- Model status: {report['model_status']}",
        f"- Records: {report['record_count']}",
        f"- Expanded negative controls: {report['expanded_negative_control_count']}",
        f"- Families: {report['family_count']}",
        f"- Structural AP@{report['top_k']}: {metrics['structural_average_precision_at_k']}",
        f"- Formula AP@{report['top_k']}: {metrics['formula_average_precision_at_k']}",
        f"- Family-prior AP@{report['top_k']}: {metrics['family_prior_average_precision_at_k']}",
        f"- Post-split structural AP: {metrics['post_split_structural_average_precision_at_k']}",
        f"- Post-split family-prior AP: {metrics['post_split_family_prior_average_precision_at_k']}",
        f"- Family-holdout structural mean AP: {metrics['family_holdout_structural_mean_ap']}",
        f"- Top-k negative-control count: {metrics['top_k_negative_control_count']}",
        f"- Validation errors: {report['validation_errors']}",
        "",
        "## Interpretation",
        "",
        "The structural/electronic proxy improves over formula-only ranking, but it still",
        "does not beat the family-prior baseline and it promotes several negative controls.",
        "This makes the artifact a useful leakage boundary rather than a discovery claim.",
        "",
        "## Top Structural/Electronic Rows",
        "",
        "| rank | material | formula | family | Tc K | source | score | dim | corr | spin | B5 response |",
        "|---:|---|---|---|---:|---|---:|---:|---:|---:|---:|",
    ]
    for index, row in enumerate(report["top_structural_rows"], start=1):
        lines.append(
            f"| {index} | {row['material_id']} | {row['formula']} | {row['family']} | "
            f"{row['tc_k']} | {row['source_subset']} | {row['structure_electronic_score']:.4f} | "
            f"{row['inferred_dimensionality']:.2f} | {row['electronic_correlation_proxy']:.3f} | "
            f"{row['spin_fluctuation_proxy']:.3f} | {row['b5_structural_response_proxy']:.3f} |"
        )
    lines.extend(["", "## Claim Boundary", ""])
    for key, value in report["claim_boundary"].items():
        lines.append(f"- {key}: {value}")
    lines.extend(
        [
            "",
            "## Next Gate",
            "",
            "Replace these curated proxy channels with actual crystallographic, DFT, or",
            "B5-computed structural/electronic observables, then expand post-2008 negatives",
            "until family priors and random baselines can no longer saturate the audit.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--high-tc-threshold", type=float, default=30.0)
    parser.add_argument("--split-year", type=int, default=2008)
    parser.add_argument("--top-k", type=int, default=12)
    parser.add_argument(
        "--json-output",
        type=Path,
        default=Path("results/B6_structural_electronic_proxy_screen_v0.json"),
    )
    parser.add_argument(
        "--markdown-output",
        type=Path,
        default=Path("research/B6_structural_electronic_proxy_screen.md"),
    )
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()
    report = build_report(args)
    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
    args.json_output.write_text(
        json.dumps(report, indent=2 if args.pretty else None, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    args.markdown_output.write_text(markdown(report), encoding="utf-8")
    print(
        json.dumps(
            {
                "status": report["status"],
                "method": report["method"],
                "record_count": report["record_count"],
                **report["metrics"],
                "validation_errors": report["validation_errors"],
            },
            indent=2 if args.pretty else None,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
