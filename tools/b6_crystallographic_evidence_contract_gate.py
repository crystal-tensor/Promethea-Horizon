#!/usr/bin/env python3
"""T-B6-005: turn failed crystallographic reproducibility gates into PR contracts."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


METHOD = "b6_crystallographic_evidence_contract_gate_v0"
STATUS = "crystallographic_evidence_contract_open_not_material_discovery_claim"
SOURCE_METHOD = "b6_crystallographic_reproducibility_gate_v0"
SOURCE_STATUS = "crystallographic_reproducibility_gate_failed_not_material_discovery_claim"
EXPECTED_FAILED = ["R6", "R7", "R8", "R9", "R10"]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def requirement(
    req_id: str,
    label: str,
    passed: bool,
    evidence: str,
    missing_to_promote: str,
) -> dict[str, Any]:
    row = {
        "id": req_id,
        "label": label,
        "passed": bool(passed),
        "evidence": evidence,
        "missing_to_promote": missing_to_promote,
    }
    return row


def packet(packet_id: str, source_gate: str, title: str, acceptance: list[str]) -> dict[str, Any]:
    return {
        "id": packet_id,
        "source_gate": source_gate,
        "title": title,
        "acceptance_criteria": acceptance,
        "claim_boundary": (
            "Packet evidence may support B6 descriptor reproducibility only after audit; "
            "it must not claim material discovery, solved mechanism, complete database, "
            "DFT observables, B5 observables, or superconductivity solution unless the "
            "corresponding contract gate passes."
        ),
    }


def build_contract(source_path: Path) -> dict[str, Any]:
    source = load_json(source_path)
    metrics = source.get("metrics", {})
    claims = source.get("claim_boundary", {})
    source_failed = source.get("failed_requirement_ids", [])

    no_forbidden_claims = all(
        claims.get(key) is False
        for key in [
            "material_discovery_claimed",
            "mechanism_solved",
            "complete_materials_database",
            "reproducible_crystallographic_descriptor_claim",
            "dft_observable_claimed",
            "b5_computed_observable_claimed",
            "solution_claimed",
        ]
    )

    requirements = [
        requirement(
            "K1",
            "source reproducibility gate is present and bounded",
            source.get("benchmark_id") == "B6"
            and source.get("method") == SOURCE_METHOD
            and source.get("status") == SOURCE_STATUS
            and source_failed == EXPECTED_FAILED,
            (
                f"benchmark_id={source.get('benchmark_id')}; method={source.get('method')}; "
                f"status={source.get('status')}; failed={source_failed}"
            ),
            "Keep the contract tied to the failed T-B6-004 gate.",
        ),
        requirement(
            "K2",
            "table size and holdout scope are contract-ready",
            metrics.get("record_count") == 56
            and metrics.get("family_count") == 28
            and metrics.get("negative_control_count") == 18
            and metrics.get("post_split_record_count") == 27,
            (
                f"records={metrics.get('record_count')}; families={metrics.get('family_count')}; "
                f"negatives={metrics.get('negative_control_count')}; "
                f"post_split={metrics.get('post_split_record_count')}"
            ),
            "Preserve the same audited B6 crystallographic row scope.",
        ),
        requirement(
            "K3",
            "forbidden discovery and mechanism claims are absent",
            no_forbidden_claims,
            f"no_forbidden_claims={no_forbidden_claims}",
            "Keep all claims bounded until reproducibility, baselines, and observables pass.",
        ),
        requirement(
            "K4",
            "reproducible crystallographic backend is available",
            source.get("runtime", {}).get("pymatgen_available") is True,
            f"pymatgen_available={source.get('runtime', {}).get('pymatgen_available')}",
            "Pin pymatgen or an equivalent descriptor backend with deterministic version metadata.",
        ),
        requirement(
            "K5",
            "source validation blockers are removed",
            metrics.get("source_validation_error_count") == 0,
            f"source_validation_error_count={metrics.get('source_validation_error_count')}",
            "Remove source validation blockers and rerun the crystallographic screen.",
        ),
        requirement(
            "K6",
            "post-split crystallographic AP beats family prior",
            float(metrics.get("post_split_crystallo_ap", 0.0))
            > float(metrics.get("post_split_family_prior_ap", 0.0)),
            (
                f"post_split_crystallo_ap={metrics.get('post_split_crystallo_ap')}; "
                f"post_split_family_prior_ap={metrics.get('post_split_family_prior_ap')}"
            ),
            "Beat the family-prior denominator on the post-split holdout.",
        ),
        requirement(
            "K7",
            "DFT observable channel is attached",
            claims.get("dft_observable_claimed") is True,
            f"dft_observable_claimed={claims.get('dft_observable_claimed')}",
            "Attach computed DFT observables or keep the descriptor as non-DFT proxy evidence.",
        ),
        requirement(
            "K8",
            "B5 computed observable channel is attached",
            claims.get("b5_computed_observable_claimed") is True,
            f"b5_computed_observable_claimed={claims.get('b5_computed_observable_claimed')}",
            "Attach B5-computed response observables or keep B6 disconnected from B5 mechanisms.",
        ),
    ]

    packets = [
        packet(
            "B6-R6-reproducible-crystallographic-backend",
            "R6",
            "Pin a reproducible crystallographic descriptor backend",
            [
                "record pymatgen or equivalent package version",
                "rerun descriptor extraction deterministically",
                "preserve the 56-record / 28-family / 18-negative-control scope",
            ],
        ),
        packet(
            "B6-R7-source-validation-cleanup",
            "R7",
            "Remove source validation blockers",
            [
                "validation_error_count is 0",
                "negative controls are not silently excluded from top-k analysis",
                "family-prior dominance is reported and addressed",
            ],
        ),
        packet(
            "B6-R8-family-prior-denominator",
            "R8",
            "Beat the post-split family-prior denominator",
            [
                "post_split_crystallo_ap is greater than post_split_family_prior_ap",
                "same post-2008 holdout rows are used",
                "no family leakage or post-hoc reranking is introduced",
            ],
        ),
        packet(
            "B6-R9-dft-observable-channel",
            "R9",
            "Attach DFT observables",
            [
                "DFT feature definitions and units are stored",
                "source structures are traceable",
                "claim boundary states whether DFT is computed or absent",
            ],
        ),
        packet(
            "B6-R10-b5-observable-channel",
            "R10",
            "Attach B5-computed observables",
            [
                "B5 observable source artifact is named",
                "observable units and row alignment are stored",
                "B6 ranking does not claim mechanism without B5 support",
            ],
        ),
    ]

    failed = [row for row in requirements if not row["passed"]]
    return {
        "benchmark_id": "B6",
        "title": "B6 crystallographic evidence contract gate",
        "method": METHOD,
        "status": STATUS,
        "model_status": "crystallographic_reproducibility_blockers_decomposed_for_prs",
        "source_gate": str(source_path),
        "source_method": source.get("method"),
        "source_status": source.get("status"),
        "source_failed_requirement_ids": source_failed,
        "record_count": metrics.get("record_count"),
        "family_count": metrics.get("family_count"),
        "negative_control_count": metrics.get("negative_control_count"),
        "post_split_record_count": metrics.get("post_split_record_count"),
        "post_split_crystallo_ap": metrics.get("post_split_crystallo_ap"),
        "post_split_family_prior_ap": metrics.get("post_split_family_prior_ap"),
        "source_validation_error_count": metrics.get("source_validation_error_count"),
        "pymatgen_available": source.get("runtime", {}).get("pymatgen_available"),
        "contract_requirement_count": len(requirements),
        "passed_contract_requirement_count": len(requirements) - len(failed),
        "failed_contract_requirement_count": len(failed),
        "failed_contract_requirement_ids": [row["id"] for row in failed],
        "contract_packet_count": len(packets),
        "contract_packet_ids": [row["id"] for row in packets],
        "requirements": requirements,
        "contract_packets": packets,
        "claim_boundary": {
            "crystallographic_evidence_contract_built": True,
            "material_discovery_claimed": False,
            "mechanism_solved": False,
            "complete_materials_database": False,
            "reproducible_crystallographic_descriptor_claim": False,
            "dft_observable_claimed": False,
            "b5_computed_observable_claimed": False,
            "solution_claimed": False,
        },
        "validation_errors": [],
    }


def write_markdown(payload: dict[str, Any], path: Path) -> None:
    lines = [
        "# B6 Crystallographic Evidence Contract Gate",
        "",
        f"Status: **{payload['status']}**",
        "",
        "## Summary",
        "",
        (
            "T-B6-005 converts the failed T-B6-004 crystallographic reproducibility "
            "gate into five PR-sized evidence packets. This is a handoff contract, "
            "not a material-discovery, solved-mechanism, DFT-observable, B5-observable, "
            "or superconductivity-solution claim."
        ),
        "",
        "## Contract Metrics",
        "",
        f"- Source failed requirements: {', '.join(payload['source_failed_requirement_ids'])}",
        (
            f"- Records / families / negative controls: {payload['record_count']} / "
            f"{payload['family_count']} / {payload['negative_control_count']}"
        ),
        f"- Post-split records: {payload['post_split_record_count']}",
        (
            f"- Post-split crystallographic AP / family-prior AP: "
            f"{payload['post_split_crystallo_ap']} / {payload['post_split_family_prior_ap']}"
        ),
        f"- Source validation error count: {payload['source_validation_error_count']}",
        f"- pymatgen available: {payload['pymatgen_available']}",
        (
            f"- Contract requirements passed / failed: "
            f"{payload['passed_contract_requirement_count']} / "
            f"{payload['failed_contract_requirement_count']}"
        ),
        f"- Contract packets: {payload['contract_packet_count']}",
        "",
        "## Requirements",
        "",
        "| ID | Pass | Requirement | Evidence | Missing to promote |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in payload["requirements"]:
        passed = "yes" if row["passed"] else "no"
        lines.append(
            f"| {row['id']} | {passed} | {row['label']} | {row['evidence']} | {row['missing_to_promote']} |"
        )
    lines.extend(["", "## PR Packets", ""])
    for row in payload["contract_packets"]:
        lines.append(f"### {row['id']}")
        lines.append("")
        lines.append(f"- Source gate: {row['source_gate']}")
        lines.append(f"- Title: {row['title']}")
        for criterion in row["acceptance_criteria"]:
            lines.append(f"- Acceptance: {criterion}")
        lines.append(f"- Claim boundary: {row['claim_boundary']}")
        lines.append("")
    lines.extend(
        [
            "## Claim Boundary",
            "",
            "- No material discovery is claimed.",
            "- No high-temperature superconductivity mechanism is claimed solved.",
            "- No complete materials database is claimed.",
            "- No reproducible crystallographic descriptor claim is made yet.",
            "- No DFT or B5-computed observable claim is made yet.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--source",
        type=Path,
        default=Path("results/B6_crystallographic_reproducibility_gate_v0.json"),
    )
    parser.add_argument(
        "--json-output",
        type=Path,
        default=Path("results/B6_crystallographic_evidence_contract_gate_v0.json"),
    )
    parser.add_argument(
        "--markdown-output",
        type=Path,
        default=Path("research/B6_crystallographic_evidence_contract_gate.md"),
    )
    args = parser.parse_args()
    payload = build_contract(args.source)
    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
    args.json_output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(payload, args.markdown_output)


if __name__ == "__main__":
    main()
