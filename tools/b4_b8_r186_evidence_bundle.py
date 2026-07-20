#!/usr/bin/env python3
"""Seal the complete R186 dual-platform evidence inventory."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


METHOD = "b4_b8_r186_full_vf2_workflow_bundle_v0"
OUTPUT_PATH = "results/B4_B8_R186_full_vf2_workflow_bundle_v0.json"
FIXED_PATHS = [
    "results/B4_B8_R186_full_vf2_workflow_protocol_v0.json",
    "benchmarks/B4_B8_R186_full_vf2_workflow_contract_v0.json",
    "benchmarks/B4_B8_R186_full_vf2_workflow_execution_contract_v0.json",
    "results/B4_B8_R186_full_vf2_workflow_linux_x86_64_v0.json",
    "results/B4_B8_R186_full_vf2_workflow_macos_arm64_v0.json",
    "results/B4_B8_R186_independent_oracle_v0.json",
    "research/B4_B8_R186_full_vf2_workflow_protocol.md",
    "research/B4_B8_R186_full_vf2_workflow_execution_contract.md",
    "research/B4_B8_R186_full_vf2_workflow_linux_x86_64.md",
    "research/B4_B8_R186_full_vf2_workflow_macos_arm64.md",
    "research/B4_B8_R186_independent_oracle.md",
    "tools/b4_b8_r186_full_vf2_workflow_preregister.py",
    "tools/b4_b8_r186_execution_contract.py",
    "tools/b4_b8_r186_full_vf2_workflow_replay.py",
    "tools/b4_b8_r186_independent_oracle.py",
    "tools/b4_b8_r186_evidence_bundle.py",
    ".github/workflows/r186-full-vf2-workflow-linux-x86-64.yml",
    "research/source_lineage/Qiskit_2_4_1_R184_window_exact_score.patch",
    "research/source_lineage/Qiskit_2_4_1_R184_window_exact_pyext.x86_64-linux-gnu.so",
    "research/source_lineage/Qiskit_2_4_1_R185_window_exact_pyext.arm64-darwin.so",
    "research/axiom_horizon_landing.html",
]
WORKER_DIRS = [
    "results/B4_B8_R186_full_vf2_workflow_linux_x86_64_replay",
    "results/B4_B8_R186_full_vf2_workflow_macos_arm64_replay",
]


def canonical_hash(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    output = root / OUTPUT_PATH
    if output.exists():
        raise ValueError("R186 evidence bundle already exists")
    paths = list(FIXED_PATHS)
    for directory in WORKER_DIRS:
        worker_dir = root / directory
        workers = sorted(worker_dir.glob("*.json"))
        if len(workers) != 13:
            raise ValueError(f"R186 expected 13 workers in {directory}")
        paths.extend(str(path.relative_to(root)) for path in workers)
    artifacts = []
    for relative in sorted(set(paths)):
        path = root / relative
        if not path.is_file():
            raise ValueError(f"R186 bundle artifact missing: {relative}")
        artifacts.append(
            {
                "path": relative,
                "sha256": file_sha256(path),
                "size_bytes": path.stat().st_size,
            }
        )
    oracle = json.loads(
        (root / "results/B4_B8_R186_independent_oracle_v0.json").read_text(
            encoding="utf-8"
        )
    )
    payload: dict[str, Any] = {
        "title": "B4/B8/B10 R186 dual-platform evidence bundle",
        "version": 0,
        "method": METHOD,
        "status": "dual_platform_bundle_complete",
        "artifact_count": len(artifacts),
        "worker_artifact_count": 26,
        "artifacts": artifacts,
        "oracle_payload_hash": oracle["payload_hash"],
        "requirements_failed": oracle["requirements_failed"],
        "simulation_execution_count": 0,
        "total_simulated_shots": 0,
        "real_backend_row_count": 0,
        "claim_boundary": oracle["claim_boundary"],
    }
    payload["payload_hash"] = canonical_hash(payload)
    output.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "status": payload["status"],
                "artifact_count": payload["artifact_count"],
                "worker_artifact_count": payload["worker_artifact_count"],
                "payload_hash": payload["payload_hash"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
