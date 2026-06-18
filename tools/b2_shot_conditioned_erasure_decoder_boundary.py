#!/usr/bin/env python3
"""Build a shot-conditioned leakage-calibration boundary for B2."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


METHOD = "b2_shot_conditioned_erasure_decoder_boundary_v0"
STATUS = "shot_conditioned_calibrated_leakage_boundary_partial_survival_not_threshold"


DEFAULT_PROFILES = [
    {
        "name": "field_detector_0p80",
        "detection_efficiency": 0.80,
        "posterior_threshold": 0.75,
        "max_missed_leakage_rate_per_tick": 0.001,
        "max_false_positive_rate_per_tick": 0.001,
    },
    {
        "name": "nominal_lab_detector_0p90",
        "detection_efficiency": 0.90,
        "posterior_threshold": 0.75,
        "max_missed_leakage_rate_per_tick": 0.001,
        "max_false_positive_rate_per_tick": 0.001,
    },
    {
        "name": "high_purity_detector_0p95",
        "detection_efficiency": 0.95,
        "posterior_threshold": 0.75,
        "max_missed_leakage_rate_per_tick": 0.0005,
        "max_false_positive_rate_per_tick": 0.001,
    },
    {
        "name": "strict_high_purity_0p95",
        "detection_efficiency": 0.95,
        "posterior_threshold": 0.90,
        "max_missed_leakage_rate_per_tick": 0.0005,
        "max_false_positive_rate_per_tick": 0.001,
    },
]


def posterior_leakage_probability(
    leakage_rate: float,
    false_positive_rate: float,
    detection_efficiency: float,
) -> float | None:
    if false_positive_rate <= 0:
        return None
    true_flag_rate = detection_efficiency * leakage_rate
    false_flag_rate = false_positive_rate * max(0.0, 1.0 - leakage_rate)
    denominator = true_flag_rate + false_flag_rate
    if denominator <= 0:
        return None
    return true_flag_rate / denominator


def evaluate_row(row: dict[str, Any], profile: dict[str, Any]) -> dict[str, Any]:
    leakage_rate = float(row["leakage_rate_per_tick"])
    false_positive_rate = float(row["false_positive_rate_per_tick"])
    detection_efficiency = float(profile["detection_efficiency"])
    posterior = posterior_leakage_probability(
        leakage_rate=leakage_rate,
        false_positive_rate=false_positive_rate,
        detection_efficiency=detection_efficiency,
    )
    missed_leakage_rate = (1.0 - detection_efficiency) * leakage_rate
    positive_flag_profile = false_positive_rate > 0.0
    posterior_pass = (
        posterior is not None and posterior >= float(profile["posterior_threshold"])
    )
    missed_pass = missed_leakage_rate <= float(profile["max_missed_leakage_rate_per_tick"])
    false_positive_pass = false_positive_rate <= float(profile["max_false_positive_rate_per_tick"])
    accepted = positive_flag_profile and posterior_pass and missed_pass and false_positive_pass
    surviving_improvement = bool(
        accepted and row["improved_volume"] and row["candidate_distance_5_or_7"]
    )
    return {
        "profile": profile["name"],
        "detection_efficiency": detection_efficiency,
        "posterior_threshold": profile["posterior_threshold"],
        "max_missed_leakage_rate_per_tick": profile["max_missed_leakage_rate_per_tick"],
        "max_false_positive_rate_per_tick": profile["max_false_positive_rate_per_tick"],
        "memory_basis": row["memory_basis"],
        "physical_error": row["physical_error"],
        "leakage_rate_per_tick": leakage_rate,
        "false_positive_rate_per_tick": false_positive_rate,
        "target_logical_error": row["target_logical_error"],
        "baseline_distance": row["baseline_distance"],
        "candidate_distance": row["candidate_distance"],
        "candidate_distance_5_or_7": row["candidate_distance_5_or_7"],
        "candidate_met": row["candidate_met"],
        "improved_volume": row["improved_volume"],
        "baseline_space_time_volume": row["baseline_space_time_volume"],
        "candidate_space_time_volume": row["candidate_space_time_volume"],
        "volume_reduction_vs_baseline": row["volume_reduction_vs_baseline"],
        "posterior_leakage_probability_given_flag": posterior,
        "missed_leakage_rate_per_tick": missed_leakage_rate,
        "positive_flag_profile": positive_flag_profile,
        "posterior_pass": posterior_pass,
        "missed_leakage_pass": missed_pass,
        "false_positive_pass": false_positive_pass,
        "shot_conditioned_accept": accepted,
        "surviving_d5_d7_improvement": surviving_improvement,
    }


def summarize_profile(rows: list[dict[str, Any]]) -> dict[str, Any]:
    accepted = [row for row in rows if row["shot_conditioned_accept"]]
    surviving = [row for row in rows if row["surviving_d5_d7_improvement"]]
    reductions = [
        row["volume_reduction_vs_baseline"]
        for row in surviving
        if row["volume_reduction_vs_baseline"] is not None
    ]
    posterior_values = [
        row["posterior_leakage_probability_given_flag"]
        for row in accepted
        if row["posterior_leakage_probability_given_flag"] is not None
    ]
    return {
        "evaluated_rows": len(rows),
        "accepted_rows": len(accepted),
        "surviving_d5_d7_improved_rows": len(surviving),
        "max_volume_reduction_on_survivors": max(reductions) if reductions else None,
        "mean_volume_reduction_on_survivors": (
            sum(reductions) / len(reductions) if reductions else None
        ),
        "min_posterior_on_accepted_rows": min(posterior_values) if posterior_values else None,
        "max_missed_leakage_rate_on_accepted_rows": (
            max(row["missed_leakage_rate_per_tick"] for row in accepted) if accepted else None
        ),
    }


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    source_payload = json.loads(args.source_result.read_text(encoding="utf-8"))
    comparisons = source_payload["comparisons"]
    positive_fp_improved = [
        row
        for row in comparisons
        if row["improved_volume"]
        and row["candidate_distance_5_or_7"]
        and float(row["false_positive_rate_per_tick"]) > 0.0
    ]
    evaluations = []
    for profile in DEFAULT_PROFILES:
        for row in comparisons:
            evaluations.append(evaluate_row(row, profile))
    by_profile = {}
    for profile in DEFAULT_PROFILES:
        profile_rows = [row for row in evaluations if row["profile"] == profile["name"]]
        by_profile[profile["name"]] = summarize_profile(profile_rows)
    survivor_rows = [row for row in evaluations if row["surviving_d5_d7_improvement"]]
    strict_rows = [
        row for row in survivor_rows if row["profile"] == "strict_high_purity_0p95"
    ]
    summary = {
        "source_method": source_payload["method"],
        "source_status": source_payload["status"],
        "source_target_comparisons": len(comparisons),
        "source_positive_fp_d5_d7_improved_rows": len(positive_fp_improved),
        "calibration_profile_count": len(DEFAULT_PROFILES),
        "evaluated_profile_rows": len(evaluations),
        "profiles_with_surviving_rows": sum(
            1 for row in by_profile.values() if row["surviving_d5_d7_improved_rows"] > 0
        ),
        "max_surviving_d5_d7_improved_rows_in_profile": max(
            row["surviving_d5_d7_improved_rows"] for row in by_profile.values()
        ),
        "strict_high_purity_surviving_rows": len(strict_rows),
        "robust_all_profile_survival": all(
            row["surviving_d5_d7_improved_rows"] > 0 for row in by_profile.values()
        ),
        "by_profile": by_profile,
    }
    report = {
        "benchmark_id": "B2",
        "problem_id": 22,
        "title": "B2 shot-conditioned erasure decoder boundary",
        "version": "0.1",
        "last_updated": args.last_updated,
        "status": STATUS,
        "method": METHOD,
        "model_status": "posterior_calibrated_flag_model_not_hardware_calibrated_decoder",
        "toolchain": (
            "Post-processes B2 false-positive Stim/PyMatching target comparisons with "
            "Bayes posterior flag calibration and shot-conditioned accept/reject gates"
        ),
        "source_result": str(args.source_result),
        "summary": summary,
        "calibration_profiles": DEFAULT_PROFILES,
        "claim_boundary": {
            "new_code_claimed": False,
            "threshold_claimed": False,
            "calibrated_device_claimed": False,
            "full_physical_leakage_decoder_claimed": False,
            "production_decoder_claimed": False,
            "shot_conditioned_calibration_model_performed": True,
            "shot_conditioned_erasure_decoder_claimed": False,
            "hardware_result_claimed": False,
            "reduced_rounds_used": False,
            "distance_3_candidate_used": False,
            "what_is_supported": (
                "A posterior-calibrated flag model can preserve some positive-false-positive "
                "d=5/d=7 target-volume rows under explicit detector-calibration assumptions."
            ),
            "what_is_not_supported": (
                "This is not a production shot-conditioned decoder, hardware-calibrated leakage "
                "model, threshold result, new code, or hardware QEC claim."
            ),
        },
        "evaluations": evaluations,
    }
    report["validation_errors"] = validate(report)
    return report


def validate(report: dict[str, Any]) -> list[str]:
    errors = []
    summary = report["summary"]
    claims = report["claim_boundary"]
    if summary["source_positive_fp_d5_d7_improved_rows"] != 5:
        errors.append("expected five source positive-fp d5/d7 improved rows")
    if summary["calibration_profile_count"] != 4:
        errors.append("expected four calibration profiles")
    if summary["max_surviving_d5_d7_improved_rows_in_profile"] <= 0:
        errors.append("expected at least one calibrated profile to preserve a d5/d7 row")
    if summary["robust_all_profile_survival"] is not False:
        errors.append("boundary should not be robust across all calibration profiles")
    if claims.get("shot_conditioned_calibration_model_performed") is not True:
        errors.append("must disclose shot-conditioned calibration modeling")
    for key in [
        "new_code_claimed",
        "threshold_claimed",
        "calibrated_device_claimed",
        "full_physical_leakage_decoder_claimed",
        "production_decoder_claimed",
        "shot_conditioned_erasure_decoder_claimed",
        "hardware_result_claimed",
        "reduced_rounds_used",
        "distance_3_candidate_used",
    ]:
        if claims.get(key) is not False:
            errors.append(f"{key} must remain False")
    return errors


def format_optional_float(value: float | None, digits: int = 3) -> str:
    if value is None:
        return "n/a"
    return f"{value:.{digits}f}"


def write_markdown(report: dict[str, Any], path: Path) -> None:
    summary = report["summary"]
    lines = [
        "# B2 Shot-Conditioned Erasure Decoder Boundary v0.1",
        "",
        f"Status: **{report['status']}**",
        "",
        "## Summary",
        "",
        f"- Method: {report['method']}",
        f"- Model status: {report['model_status']}",
        f"- Source result: {report['source_result']}",
        f"- Source positive-false-positive d=5/d=7 improved rows: {summary['source_positive_fp_d5_d7_improved_rows']}",
        f"- Calibration profiles: {summary['calibration_profile_count']}",
        f"- Evaluated profile rows: {summary['evaluated_profile_rows']}",
        f"- Profiles with surviving rows: {summary['profiles_with_surviving_rows']}",
        f"- Max surviving d=5/d=7 improved rows in one profile: {summary['max_surviving_d5_d7_improved_rows_in_profile']}",
        f"- Strict high-purity surviving rows: {summary['strict_high_purity_surviving_rows']}",
        f"- Robust all-profile survival: {summary['robust_all_profile_survival']}",
        f"- Validation errors: {report['validation_errors']}",
        "",
        "## Calibration Profile Breakdown",
        "",
        "| profile | accepted rows | surviving d=5/7 rows | max reduction | mean reduction | min posterior | max missed leakage/tick |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for profile, row in summary["by_profile"].items():
        lines.append(
            f"| {profile} | {row['accepted_rows']} | {row['surviving_d5_d7_improved_rows']} | "
            f"{format_optional_float(row['max_volume_reduction_on_survivors'])} | "
            f"{format_optional_float(row['mean_volume_reduction_on_survivors'])} | "
            f"{format_optional_float(row['min_posterior_on_accepted_rows'])} | "
            f"{format_optional_float(row['max_missed_leakage_rate_on_accepted_rows'], 6)} |"
        )
    survivors = [row for row in report["evaluations"] if row["surviving_d5_d7_improvement"]]
    survivors.sort(
        key=lambda row: (
            row["profile"],
            -(row["volume_reduction_vs_baseline"] or 0.0),
            row["physical_error"],
            row["leakage_rate_per_tick"],
            row["target_logical_error"],
        )
    )
    lines.extend(
        [
            "",
            "## Surviving Rows",
            "",
            "| profile | basis | p | leakage/tick | fp/tick | target | candidate d | posterior | missed leakage/tick | reduction |",
            "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for row in survivors:
        lines.append(
            f"| {row['profile']} | {row['memory_basis']} | {row['physical_error']:.4g} | "
            f"{row['leakage_rate_per_tick']:.4g} | {row['false_positive_rate_per_tick']:.4g} | "
            f"{row['target_logical_error']:.4g} | {row['candidate_distance']} | "
            f"{row['posterior_leakage_probability_given_flag']:.3f} | "
            f"{row['missed_leakage_rate_per_tick']:.6f} | "
            f"{row['volume_reduction_vs_baseline']:.3f}x |"
        )
    if not survivors:
        lines.append("| n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a |")
    lines.extend(["", "## Claim Boundary", ""])
    for key, value in report["claim_boundary"].items():
        lines.append(f"- {key}: {value}")
    lines.extend(
        [
            "",
            "## Next Gate",
            "",
            "The surviving rows depend on detector-purity assumptions and do not survive",
            "all calibration profiles. The next B2 step should either integrate these",
            "posterior probabilities directly into a circuit-level decoder or demote the",
            "heralded-erasure route if calibrated leakage and flag data cannot support",
            "the required posterior and missed-leakage gates.",
            "",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source-result",
        type=Path,
        default=Path("results/B2_heralded_erasure_false_positive_stress_v0.json"),
    )
    parser.add_argument("--last-updated", default="2026-06-18")
    parser.add_argument(
        "--json-output",
        type=Path,
        default=Path("results/B2_shot_conditioned_erasure_decoder_boundary_v0.json"),
    )
    parser.add_argument(
        "--markdown-output",
        type=Path,
        default=Path("research/B2_shot_conditioned_erasure_decoder_boundary.md"),
    )
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()

    report = build_report(args)
    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    args.json_output.write_text(
        json.dumps(report, indent=2 if args.pretty else None, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    write_markdown(report, args.markdown_output)
    print(
        json.dumps(
            {
                "status": report["status"],
                "method": report["method"],
                **report["summary"],
                "validation_errors": report["validation_errors"],
            },
            indent=2 if args.pretty else None,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
