#!/usr/bin/env python3
"""Bind the public R186 preregistration to its execution tooling."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


PROTOCOL_PATH = "results/B4_B8_R186_full_vf2_workflow_protocol_v0.json"
DESIGN_PATH = "benchmarks/B4_B8_R186_full_vf2_workflow_contract_v0.json"
CONTRACT_PATH = "benchmarks/B4_B8_R186_full_vf2_workflow_execution_contract_v0.json"
REPORT_PATH = "research/B4_B8_R186_full_vf2_workflow_execution_contract.md"
SOURCE_PATHS = [
    PROTOCOL_PATH,
    DESIGN_PATH,
    "results/B4_B8_R184_window_exact_score_v0.json",
    "results/B4_B8_R184_independent_oracle_v0.json",
    "results/B4_B8_R185_macos_arm64_replication_v0.json",
    "results/B4_B8_R185_independent_oracle_v0.json",
    "research/source_lineage/Qiskit_2_4_1_R184_window_exact_score.patch",
    "research/source_lineage/Qiskit_2_4_1_R184_window_exact_pyext.x86_64-linux-gnu.so",
    "research/source_lineage/Qiskit_2_4_1_R185_window_exact_pyext.arm64-darwin.so",
    "research/source_lineage/Qiskit_2_4_1_vf2_source_manifest.json",
]
TOOL_PATHS = [
    "tools/b4_b8_r186_full_vf2_workflow_replay.py",
    "tools/b4_b8_r186_independent_oracle.py",
    "tools/b4_b8_r186_evidence_bundle.py",
    ".github/workflows/r186-full-vf2-workflow-linux-x86-64.yml",
    "research/axiom_horizon_landing.html",
]


def canonical_hash(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_hash(payload: dict[str, Any], label: str) -> str:
    body = dict(payload)
    observed = body.pop("payload_hash", None)
    if not observed or observed != canonical_hash(body):
        raise ValueError(f"R186 {label} hash mismatch")
    return str(observed)


def binding(root: Path, relative: str) -> dict[str, Any]:
    path = root / relative
    if not path.is_file():
        raise ValueError(f"R186 execution binding is missing: {relative}")
    output: dict[str, Any] = {
        "path": relative,
        "sha256": file_sha256(path),
        "size_bytes": path.stat().st_size,
    }
    if path.suffix == ".json":
        payload = json.loads(path.read_text(encoding="utf-8"))
        for field in ("payload_hash", "manifest_hash"):
            if field in payload:
                output[field] = payload[field]
    return output


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def render_report(contract: dict[str, Any]) -> str:
    public = contract["public_preregistration"]
    return "\n".join(
        [
            "# B4/B8/B10 R186 Full VF2 Workflow Execution Contract",
            "",
            "- Status: `execution_bound_unopened`",
            f"- Contract payload hash: `{contract['payload_hash']}`",
            f"- Public design commit: `{public['public_design_commit']}`",
            f"- Discussion: {public['discussion']}",
            f"- Discussion created: `{public['created_at']}`",
            "- Scientific execution: unopened",
            "",
            "## Bound Execution",
            "",
            "The contract binds the unchanged R184 patch, the Linux x86-64 and macOS arm64 extension binaries, the dual-surface replay executor, the standard-library oracle, the evidence bundler, the Linux workflow, and the content-only landing-page update. Both platform runs must start from this contract's clean public-main descendant.",
            "",
            "## Claim Boundary",
            "",
            "No mapping row or timing classification exists at contract time. The experiment remains an external source-faithful Qiskit 2.4.1 monkeypatch harness with zero simulations, zero quantum shots, zero real-backend rows, and zero new credit.",
            "",
        ]
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--public-design-commit", required=True)
    parser.add_argument("--discussion", required=True)
    parser.add_argument("--created-at", required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    for relative in (CONTRACT_PATH, REPORT_PATH):
        if (root / relative).exists():
            raise ValueError(f"R186 execution output already exists: {relative}")
    protocol = json.loads((root / PROTOCOL_PATH).read_text(encoding="utf-8"))
    design = json.loads((root / DESIGN_PATH).read_text(encoding="utf-8"))
    validate_hash(protocol, "protocol")
    validate_hash(design, "design contract")
    if design["protocol_payload_hash"] != protocol["payload_hash"]:
        raise ValueError("R186 execution design binding mismatch")
    if not args.discussion.startswith(
        "https://github.com/crystal-tensor/Prometheus-plan/discussions/"
    ):
        raise ValueError("R186 Discussion must belong to Prometheus-plan")

    contract: dict[str, Any] = {
        "contract_id": "B4-B8-R186-full-vf2-workflow-execution-contract-v0",
        "status": "execution_bound_unopened",
        "execution_started": False,
        "protocol_path": PROTOCOL_PATH,
        "protocol_payload_hash": protocol["payload_hash"],
        "design_contract_path": DESIGN_PATH,
        "design_contract_payload_hash": design["payload_hash"],
        "public_preregistration": {
            "public_design_commit": args.public_design_commit,
            "discussion": args.discussion,
            "created_at": args.created_at,
        },
        "source_bindings": {
            f"source_{index:02d}": binding(root, relative)
            for index, relative in enumerate(SOURCE_PATHS, start=1)
        },
        "tool_bindings": {
            f"tool_{index:02d}": binding(root, relative)
            for index, relative in enumerate(TOOL_PATHS, start=1)
        },
        "contract_generator_binding": binding(
            root, str(Path(__file__).resolve().relative_to(root))
        ),
        "platform_execution_order": "linux_and_macos_may_run_independently_from_the_same_clean_public_commit",
        "required_platforms": ["linux_x86_64", "macos_arm64"],
        "required_result_paths": [
            "results/B4_B8_R186_full_vf2_workflow_linux_x86_64_v0.json",
            "results/B4_B8_R186_full_vf2_workflow_macos_arm64_v0.json",
        ],
        "required_worker_directories": [
            "results/B4_B8_R186_full_vf2_workflow_linux_x86_64_replay",
            "results/B4_B8_R186_full_vf2_workflow_macos_arm64_replay",
        ],
        "required_oracle_path": "results/B4_B8_R186_independent_oracle_v0.json",
        "required_bundle_path": "results/B4_B8_R186_full_vf2_workflow_bundle_v0.json",
        "runtime_guards": {
            "head_equals_supplied_preregistration_commit": True,
            "public_design_is_ancestor": True,
            "worktree_clean_before_platform_execution": True,
            "remote_main_equals_platform_execution_commit": True,
            "platform_identity_matches_selected_binary": True,
            "python_vf2_layout_hash_matches_protocol": True,
            "discussion_url_and_timestamp_match": True,
        },
        "claim_boundary": protocol["claim_boundary"],
    }
    contract["payload_hash"] = canonical_hash(contract)
    write_json(root / CONTRACT_PATH, contract)
    (root / REPORT_PATH).write_text(render_report(contract), encoding="utf-8")
    print(
        json.dumps(
            {
                "contract": CONTRACT_PATH,
                "payload_hash": contract["payload_hash"],
                "status": contract["status"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
