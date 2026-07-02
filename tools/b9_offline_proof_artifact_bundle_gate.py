#!/usr/bin/env python3
"""Build an offline proof-artifact bundle gate for the blocked B9 Lean route."""

from __future__ import annotations

import argparse
import hashlib
import json
import time
from pathlib import Path
from typing import Any


METHOD = "b9_offline_proof_artifact_bundle_gate_v0"
STATUS = "offline_proof_artifact_bundle_open_missing_checked_run"
MODEL_STATUS = "lean_scaffold_and_local_verifier_hash_bundle_ready_no_checked_output"
VERSION = "0.1"
EXPECTED_FAILED_IDS = ["B6", "B7", "B8"]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def stable_hash(payload: Any) -> str:
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def write_json(path: Path, payload: dict[str, Any], pretty: bool) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(payload, indent=2 if pretty else None, sort_keys=True)
    path.write_text(text + "\n", encoding="utf-8")


def requirement(requirement_id: str, label: str, passed: bool, evidence: dict[str, Any]) -> dict[str, Any]:
    return {
        "requirement_id": requirement_id,
        "label": label,
        "passed": bool(passed),
        "evidence": evidence,
    }


def artifact(path: Path, role: str) -> dict[str, Any]:
    return {
        "path": str(path),
        "role": role,
        "exists": path.exists(),
        "sha256": sha256_file(path) if path.exists() else None,
    }


def build_payload(args: argparse.Namespace) -> dict[str, Any]:
    started = time.time()
    root = Path(".")
    ci = load_json(args.ci_contract)
    scaffold = load_json(args.scaffold_gate)
    verifier = load_json(args.parametric_certificate)

    bundle_artifacts = [
        artifact(root / "lean-toolchain", "pinned Lean toolchain"),
        artifact(root / "lakefile.lean", "Lake project definition"),
        artifact(root / "B9/ClusterStabilizer/WidthLocality.lean", "Lake module theorem interface"),
        artifact(
            root / "research/proof_skeletons/B9_cluster_stabilizer_width_locality_bound.lean",
            "research skeleton theorem interface",
        ),
        artifact(root / "research/ci/b9-lean-proof-scaffold.yml", "reviewed CI workflow template"),
        artifact(
            root / "results/B9_cluster_stabilizer_parametric_certificate_v0.json",
            "local exact-rational verifier result",
        ),
        artifact(root / "results/B9_proof_project_scaffold_gate_v0.json", "scaffold gate result"),
        artifact(root / "results/B9_toolchain_ci_contract_gate_v0.json", "CI contract result"),
    ]
    bundle_hash = stable_hash(bundle_artifacts)
    present_count = sum(row["exists"] for row in bundle_artifacts)
    checked_run_artifacts: list[dict[str, Any]] = []
    checked_run_artifact_count = len(checked_run_artifacts)

    requirements = [
        requirement(
            "B1",
            "CI contract is blocked only by workflow activation and remote checked output",
            ci.get("method") == "b9_toolchain_ci_contract_gate_v0"
            and ci.get("failed_ci_contract_requirement_ids") == ["C2", "C3", "C10"],
            {
                "source_status": ci.get("status"),
                "failed_ci_contract_requirement_ids": ci.get(
                    "failed_ci_contract_requirement_ids"
                ),
                "workflow_activation_blocked_by_oauth_scope": ci["claim_boundary"].get(
                    "workflow_activation_blocked_by_oauth_scope"
                ),
            },
        ),
        requirement(
            "B2",
            "Proof scaffold has non-placeholder theorem interfaces",
            scaffold.get("method") == "b9_proof_project_scaffold_gate_v0"
            and scaffold["project_probe"]["contains_sorry"] is False
            and scaffold["project_probe"]["contains_placeholder_true_theorem"] is False
            and scaffold["project_probe"]["theorem_present"] is True,
            {
                "source_status": scaffold.get("status"),
                "failed_scaffold_requirement_ids": scaffold.get("failed_scaffold_requirement_ids"),
                "project_probe": scaffold.get("project_probe"),
            },
        ),
        requirement(
            "B3",
            "Local exact-rational verifier evidence remains checked",
            verifier.get("method") == "b9_cluster_stabilizer_parametric_certificate_v0"
            and verifier["claim_boundary"].get("local_verifier_checked") is True
            and verifier.get("validation_error_count") == 0,
            {
                "source_status": verifier.get("status"),
                "local_verifier_checked": verifier["claim_boundary"].get("local_verifier_checked"),
                "finite_rows_checked": verifier.get("finite_rows_checked"),
                "validation_error_count": verifier.get("validation_error_count"),
            },
        ),
        requirement(
            "B4",
            "All offline bundle source artifacts exist and are hashable",
            present_count == len(bundle_artifacts) and all(row["sha256"] for row in bundle_artifacts),
            {
                "bundle_artifact_count": len(bundle_artifacts),
                "present_artifact_count": present_count,
                "bundle_hash": bundle_hash,
            },
        ),
        requirement(
            "B5",
            "Forbidden theorem and Quantum PCP claims remain false",
            all(
                ci["claim_boundary"].get(key) is False
                for key in [
                    "formal_theorem_proved",
                    "proof_assistant_checked",
                    "global_gap_amplification_impossibility_claimed",
                    "nlts_theorem_claimed",
                ]
            )
            and ci["claim_boundary"].get("explicit_not_quantum_pcp_proof") is True,
            {
                "formal_theorem_proved": ci["claim_boundary"].get("formal_theorem_proved"),
                "proof_assistant_checked": ci["claim_boundary"].get("proof_assistant_checked"),
                "explicit_not_quantum_pcp_proof": ci["claim_boundary"].get(
                    "explicit_not_quantum_pcp_proof"
                ),
                "nlts_theorem_claimed": ci["claim_boundary"].get("nlts_theorem_claimed"),
            },
        ),
        requirement(
            "B6",
            "Lean/Lake checked run artifact is present",
            checked_run_artifact_count > 0,
            {"checked_run_artifact_count": checked_run_artifact_count},
        ),
        requirement(
            "B7",
            "Proof assistant checked theorem output is present",
            scaffold["claim_boundary"].get("proof_assistant_checked") is True
            and scaffold["claim_boundary"].get("formal_theorem_proved") is True,
            {
                "proof_assistant_checked": scaffold["claim_boundary"].get(
                    "proof_assistant_checked"
                ),
                "formal_theorem_proved": scaffold["claim_boundary"].get("formal_theorem_proved"),
            },
        ),
        requirement(
            "B8",
            "Active remote CI artifact or equivalent offline attestation is accepted",
            ci["claim_boundary"].get("remote_ci_run_artifact_present") is True
            or checked_run_artifact_count > 0,
            {
                "remote_ci_run_artifact_present": ci["claim_boundary"].get(
                    "remote_ci_run_artifact_present"
                ),
                "offline_checked_run_artifact_count": checked_run_artifact_count,
            },
        ),
    ]

    passed = sum(row["passed"] for row in requirements)
    failed_ids = [row["requirement_id"] for row in requirements if not row["passed"]]
    validation_errors: list[str] = []
    if failed_ids != EXPECTED_FAILED_IDS:
        validation_errors.append(f"unexpected offline bundle failures: {failed_ids}")

    summary = {
        "source_ci_contract_status": ci.get("status"),
        "source_scaffold_status": scaffold.get("status"),
        "source_parametric_certificate_status": verifier.get("status"),
        "bundle_requirement_count": len(requirements),
        "bundle_requirements_passed": passed,
        "bundle_requirements_failed": len(requirements) - passed,
        "failed_bundle_requirement_ids": failed_ids,
        "bundle_artifact_count": len(bundle_artifacts),
        "present_artifact_count": present_count,
        "bundle_hash": bundle_hash,
        "checked_run_artifact_count": checked_run_artifact_count,
        "proof_assistant_checked": False,
        "formal_theorem_proved": False,
        "explicit_not_quantum_pcp_proof": True,
        "global_gap_amplification_impossibility_claimed": False,
        "nlts_theorem_claimed": False,
        "validation_error_count": len(validation_errors),
    }

    return {
        "benchmark_id": "B9",
        "linked_benchmark_id": "B10",
        "problem_id": 17,
        "title": "B9 Offline Proof Artifact Bundle Gate",
        "version": VERSION,
        "last_updated": args.last_updated,
        "method": METHOD,
        "status": STATUS,
        "model_status": MODEL_STATUS,
        "source_ci_contract_result": str(args.ci_contract),
        "source_scaffold_gate_result": str(args.scaffold_gate),
        "source_parametric_certificate_result": str(args.parametric_certificate),
        "summary": summary,
        "requirements": requirements,
        "bundle_artifacts": bundle_artifacts,
        "required_checked_run_artifacts": [
            "lean --version output showing Lean 4",
            "lake --version output",
            "lake env lean B9/ClusterStabilizer/WidthLocality.lean transcript",
            "hash of checked Lean module and lake manifest used for the run",
        ],
        "claim_boundary": {
            "what_is_supported": (
                "The current B9 Lean scaffold, CI template, and local exact-rational verifier "
                "artifacts are bundled with stable hashes for offline proof-run PRs."
            ),
            "what_is_not_supported": (
                "No Lean/Lake checked run artifact, proof-assistant checked theorem, Quantum PCP "
                "proof, NLTS theorem, or global gap-amplification impossibility theorem is established."
            ),
            "next_gate": (
                "Submit Lean 4/Lake checked output for B9/ClusterStabilizer/WidthLocality.lean "
                "or install the reviewed GitHub workflow with a token that has workflow scope."
            ),
            "proof_assistant_checked": False,
            "formal_theorem_proved": False,
            "explicit_not_quantum_pcp_proof": True,
            "global_gap_amplification_impossibility_claimed": False,
            "nlts_theorem_claimed": False,
        },
        "validation_errors": validation_errors,
        "runtime_seconds": time.time() - started,
    }


def write_markdown(payload: dict[str, Any], path: Path) -> None:
    summary = payload["summary"]
    lines = [
        "# B9 Offline Proof Artifact Bundle Gate",
        "",
        f"Status: **{payload['status']}**",
        "",
        "## Summary",
        "",
        f"- Method: `{payload['method']}`",
        f"- Bundle requirements passed/failed: {summary['bundle_requirements_passed']} / {summary['bundle_requirements_failed']}",
        f"- Failed bundle requirement IDs: {summary['failed_bundle_requirement_ids']}",
        f"- Bundle artifacts present: {summary['present_artifact_count']} / {summary['bundle_artifact_count']}",
        f"- Bundle hash: `{summary['bundle_hash']}`",
        f"- Checked run artifacts: {summary['checked_run_artifact_count']}",
        "",
        "## Bundle Artifacts",
        "",
        "| Role | Path | Exists | SHA-256 |",
        "|---|---|---|---|",
    ]
    for row in payload["bundle_artifacts"]:
        lines.append(f"| {row['role']} | `{row['path']}` | {row['exists']} | `{row['sha256']}` |")
    lines.extend(["", "## Required Checked Run Artifacts", ""])
    for item in payload["required_checked_run_artifacts"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Requirement Results", ""])
    for row in payload["requirements"]:
        status = "PASS" if row["passed"] else "FAIL"
        lines.append(f"- {row['requirement_id']} [{status}]: {row['label']}")
    lines.extend(
        [
            "",
            "## Claim Boundary",
            "",
            f"- Supported: {payload['claim_boundary']['what_is_supported']}",
            f"- Not supported: {payload['claim_boundary']['what_is_not_supported']}",
            f"- Next gate: {payload['claim_boundary']['next_gate']}",
            f"- proof_assistant_checked: {payload['claim_boundary']['proof_assistant_checked']}",
            f"- formal_theorem_proved: {payload['claim_boundary']['formal_theorem_proved']}",
            f"- explicit_not_quantum_pcp_proof: {payload['claim_boundary']['explicit_not_quantum_pcp_proof']}",
            "",
            "## Validation",
            "",
            f"- validation_error_count: {summary['validation_error_count']}",
        ]
    )
    if payload["validation_errors"]:
        for error in payload["validation_errors"]:
            lines.append(f"- {error}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--ci-contract",
        type=Path,
        default=Path("results/B9_toolchain_ci_contract_gate_v0.json"),
    )
    parser.add_argument(
        "--scaffold-gate",
        type=Path,
        default=Path("results/B9_proof_project_scaffold_gate_v0.json"),
    )
    parser.add_argument(
        "--parametric-certificate",
        type=Path,
        default=Path("results/B9_cluster_stabilizer_parametric_certificate_v0.json"),
    )
    parser.add_argument(
        "--json-output",
        type=Path,
        default=Path("results/B9_offline_proof_artifact_bundle_gate_v0.json"),
    )
    parser.add_argument(
        "--markdown-output",
        type=Path,
        default=Path("research/B9_offline_proof_artifact_bundle_gate.md"),
    )
    parser.add_argument("--last-updated", default="2026-07-02")
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()

    payload = build_payload(args)
    write_json(args.json_output, payload, pretty=args.pretty)
    write_markdown(payload, args.markdown_output)
    print(json.dumps(payload["summary"], indent=2 if args.pretty else None, sort_keys=True))
    if payload["validation_errors"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
