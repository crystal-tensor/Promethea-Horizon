#!/usr/bin/env python3
"""Gate the B9 transition from offline proof bundle to checked Lean/Lake run."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import socket
import subprocess
import time
from pathlib import Path
from typing import Any


METHOD = "b9_checked_run_acquisition_gate_v0"
STATUS = "checked_run_acquisition_open_toolchain_not_cached"
MODEL_STATUS = "elan_installed_lean_lake_wrappers_timeout_before_checked_output"
VERSION = "0.1"
EXPECTED_FAILED_IDS = ["A3", "A4", "A6"]


def scrub_home(value: str) -> str:
    return value.replace(str(Path.home()), "~")


def scrub_command(cmd: list[str]) -> list[str]:
    return [scrub_home(part) for part in cmd]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, payload: dict[str, Any], pretty: bool) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(payload, indent=2 if pretty else None, sort_keys=True)
    path.write_text(text + "\n", encoding="utf-8")


def run_probe(cmd: list[str], timeout_seconds: int) -> dict[str, Any]:
    started = time.time()
    executable = shutil.which(cmd[0]) if not Path(cmd[0]).is_absolute() else cmd[0]
    if executable is None or not Path(executable).exists():
        return {
            "command": scrub_command(cmd),
            "executable": executable,
            "available": False,
            "timed_out": False,
            "returncode": None,
            "stdout": "",
            "stderr": "",
            "runtime_seconds": 0.0,
        }
    try:
        completed = subprocess.run(
            cmd,
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
        )
        return {
            "command": scrub_command(cmd),
            "executable": scrub_home(executable),
            "available": True,
            "timed_out": False,
            "returncode": completed.returncode,
            "stdout": scrub_home(completed.stdout.strip()),
            "stderr": scrub_home(completed.stderr.strip()),
            "runtime_seconds": time.time() - started,
        }
    except subprocess.TimeoutExpired as exc:
        return {
            "command": scrub_command(cmd),
            "executable": scrub_home(executable),
            "available": True,
            "timed_out": True,
            "returncode": None,
            "stdout": scrub_home((exc.stdout or "").strip()) if isinstance(exc.stdout, str) else "",
            "stderr": scrub_home((exc.stderr or "").strip()) if isinstance(exc.stderr, str) else "",
            "runtime_seconds": time.time() - started,
        }


def socket_probe(host: str, port: int, timeout_seconds: int) -> dict[str, Any]:
    started = time.time()
    try:
        with socket.create_connection((host, port), timeout=timeout_seconds):
            return {
                "host": host,
                "port": port,
                "reachable": True,
                "error": None,
                "runtime_seconds": time.time() - started,
            }
    except OSError as exc:
        return {
            "host": host,
            "port": port,
            "reachable": False,
            "error": repr(exc),
            "runtime_seconds": time.time() - started,
        }


def requirement(requirement_id: str, label: str, passed: bool, evidence: dict[str, Any]) -> dict[str, Any]:
    return {
        "requirement_id": requirement_id,
        "label": label,
        "passed": bool(passed),
        "evidence": evidence,
    }


def build_payload(args: argparse.Namespace) -> dict[str, Any]:
    started = time.time()
    bundle = load_json(args.offline_bundle)
    toolchain_path = args.lean_toolchain
    toolchain_text = toolchain_path.read_text(encoding="utf-8").strip() if toolchain_path.exists() else ""
    module_path = args.lean_module
    transcript_path = args.checked_transcript

    home = Path.home()
    elan_bin = home / ".elan" / "bin"
    lean_candidates = [
        str(elan_bin / "lean"),
        shutil.which("lean") or "lean",
    ]
    lake_candidates = [
        str(elan_bin / "lake"),
        shutil.which("lake") or "lake",
    ]
    elan_candidates = [
        str(elan_bin / "elan"),
        shutil.which("elan") or "elan",
    ]

    lean_probes = [run_probe([candidate, "--version"], args.command_timeout) for candidate in lean_candidates]
    lake_probes = [run_probe([candidate, "--version"], args.command_timeout) for candidate in lake_candidates]
    elan_probes = [run_probe([candidate, "--version"], args.command_timeout) for candidate in elan_candidates]
    release_probe = socket_probe(args.release_host, 443, args.network_timeout)

    lean4_probe = next(
        (
            probe
            for probe in lean_probes
            if probe["returncode"] == 0
            and "Lean" in probe["stdout"]
            and "version" in probe["stdout"].lower()
        ),
        None,
    )
    lake_probe = next(
        (
            probe
            for probe in lake_probes
            if probe["returncode"] == 0 and "Lake" in (probe["stdout"] + probe["stderr"])
        ),
        None,
    )
    local_toolchain_cache = any(
        (home / ".elan" / "toolchains" / name).exists()
        for name in [
            "leanprover--lean4---v4.12.0",
            "leanprover-lean4-v4.12.0",
        ]
    )
    checked_transcript_present = transcript_path.exists()

    requirements = [
        requirement(
            "A1",
            "Offline proof bundle remains valid and hashable",
            bundle.get("method") == "b9_offline_proof_artifact_bundle_gate_v0"
            and bundle["summary"].get("validation_error_count") == 0
            and bundle["summary"].get("failed_bundle_requirement_ids") == ["B6", "B7", "B8"],
            {
                "offline_bundle_status": bundle.get("status"),
                "offline_bundle_failed_ids": bundle["summary"].get("failed_bundle_requirement_ids"),
                "offline_bundle_hash": bundle["summary"].get("bundle_hash"),
            },
        ),
        requirement(
            "A2",
            "Pinned Lean toolchain declaration is present",
            toolchain_text == "leanprover/lean4:v4.12.0",
            {
                "lean_toolchain_path": str(toolchain_path),
                "lean_toolchain_exists": toolchain_path.exists(),
                "lean_toolchain_sha256": sha256_file(toolchain_path) if toolchain_path.exists() else None,
                "lean_toolchain_text": toolchain_text,
            },
        ),
        requirement(
            "A3",
            "Real Lean 4 executable is available without triggering an acquisition timeout",
            lean4_probe is not None,
            {"lean_probes": lean_probes},
        ),
        requirement(
            "A4",
            "Lake executable is available without triggering an acquisition timeout",
            lake_probe is not None,
            {"lake_probes": lake_probes},
        ),
        requirement(
            "A5",
            "Pinned Lean toolchain can be acquired or is already cached",
            local_toolchain_cache or release_probe["reachable"],
            {
                "local_toolchain_cache_present": local_toolchain_cache,
                "release_host_probe": release_probe,
                "elan_probes": elan_probes,
            },
        ),
        requirement(
            "A6",
            "Checked Lean module transcript is present",
            checked_transcript_present,
            {
                "lean_module": str(module_path),
                "lean_module_exists": module_path.exists(),
                "lean_module_sha256": sha256_file(module_path) if module_path.exists() else None,
                "checked_transcript": str(transcript_path),
                "checked_transcript_present": checked_transcript_present,
            },
        ),
        requirement(
            "A7",
            "Forbidden B9 theorem and Quantum PCP claims remain false",
            bundle["claim_boundary"].get("formal_theorem_proved") is False
            and bundle["claim_boundary"].get("proof_assistant_checked") is False
            and bundle["claim_boundary"].get("explicit_not_quantum_pcp_proof") is True
            and bundle["claim_boundary"].get("nlts_theorem_claimed") is False,
            {
                "formal_theorem_proved": bundle["claim_boundary"].get("formal_theorem_proved"),
                "proof_assistant_checked": bundle["claim_boundary"].get("proof_assistant_checked"),
                "explicit_not_quantum_pcp_proof": bundle["claim_boundary"].get("explicit_not_quantum_pcp_proof"),
                "nlts_theorem_claimed": bundle["claim_boundary"].get("nlts_theorem_claimed"),
            },
        ),
    ]

    passed = sum(row["passed"] for row in requirements)
    failed_ids = [row["requirement_id"] for row in requirements if not row["passed"]]
    validation_errors: list[str] = []
    if failed_ids != EXPECTED_FAILED_IDS:
        validation_errors.append(f"unexpected checked-run acquisition failures: {failed_ids}")

    summary = {
        "acquisition_requirement_count": len(requirements),
        "acquisition_requirements_passed": passed,
        "acquisition_requirements_failed": len(requirements) - passed,
        "failed_acquisition_requirement_ids": failed_ids,
        "lean4_available": lean4_probe is not None,
        "lake_available": lake_probe is not None,
        "elan_probe_count": len(elan_probes),
        "release_host_reachable": release_probe["reachable"],
        "local_toolchain_cache_present": local_toolchain_cache,
        "checked_transcript_present": checked_transcript_present,
        "proof_assistant_checked": False,
        "formal_theorem_proved": False,
        "explicit_not_quantum_pcp_proof": True,
        "nlts_theorem_claimed": False,
        "validation_error_count": len(validation_errors),
    }

    return {
        "benchmark_id": "B9",
        "linked_benchmark_id": "B10",
        "problem_id": 17,
        "title": "B9 Checked-Run Acquisition Gate",
        "version": VERSION,
        "last_updated": args.last_updated,
        "method": METHOD,
        "status": STATUS,
        "model_status": MODEL_STATUS,
        "source_offline_bundle_result": str(args.offline_bundle),
        "summary": summary,
        "requirements": requirements,
        "probes": {
            "lean": lean_probes,
            "lake": lake_probes,
            "elan": elan_probes,
            "release_host": release_probe,
        },
        "claim_boundary": {
            "what_is_supported": (
                "The B9 proof-run acquisition blocker is now explicit: the offline bundle is valid, "
                "the pinned Lean 4.12.0 declaration exists, but this environment does not yet provide "
                "a usable Lean 4/Lake checked run transcript."
            ),
            "what_is_not_supported": (
                "No proof-assistant checked theorem, Quantum PCP proof, NLTS theorem, or global "
                "gap-amplification impossibility theorem is established."
            ),
            "next_gate": (
                "Provide an accepted transcript for lean --version, lake --version, and "
                "lake env lean B9/ClusterStabilizer/WidthLocality.lean, using either a reachable "
                "Lean release host, a trusted mirror/cache, or the reviewed GitHub workflow."
            ),
            "proof_assistant_checked": False,
            "formal_theorem_proved": False,
            "explicit_not_quantum_pcp_proof": True,
            "nlts_theorem_claimed": False,
        },
        "validation_errors": validation_errors,
        "runtime_seconds": time.time() - started,
    }


def write_markdown(payload: dict[str, Any], path: Path) -> None:
    summary = payload["summary"]
    lines = [
        "# B9 Checked-Run Acquisition Gate",
        "",
        f"Status: **{payload['status']}**",
        "",
        "## Summary",
        "",
        f"- Method: `{payload['method']}`",
        f"- Acquisition requirements passed/failed: {summary['acquisition_requirements_passed']} / {summary['acquisition_requirements_failed']}",
        f"- Failed acquisition requirement IDs: {summary['failed_acquisition_requirement_ids']}",
        f"- Lean 4 available: {summary['lean4_available']}",
        f"- Lake available: {summary['lake_available']}",
        f"- Release host reachable: {summary['release_host_reachable']}",
        f"- Local toolchain cache present: {summary['local_toolchain_cache_present']}",
        f"- Checked transcript present: {summary['checked_transcript_present']}",
        "",
        "## Requirement Results",
        "",
    ]
    for row in payload["requirements"]:
        status = "PASS" if row["passed"] else "FAIL"
        lines.append(f"- {row['requirement_id']} [{status}]: {row['label']}")
    lines.extend(
        [
            "",
            "## Toolchain Probe",
            "",
            f"- Lean probes: `{json.dumps(payload['probes']['lean'], sort_keys=True)}`",
            f"- Lake probes: `{json.dumps(payload['probes']['lake'], sort_keys=True)}`",
            f"- Elan probes: `{json.dumps(payload['probes']['elan'], sort_keys=True)}`",
            f"- Release host probe: `{json.dumps(payload['probes']['release_host'], sort_keys=True)}`",
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
        "--offline-bundle",
        type=Path,
        default=Path("results/B9_offline_proof_artifact_bundle_gate_v0.json"),
    )
    parser.add_argument("--lean-toolchain", type=Path, default=Path("lean-toolchain"))
    parser.add_argument(
        "--lean-module",
        type=Path,
        default=Path("B9/ClusterStabilizer/WidthLocality.lean"),
    )
    parser.add_argument(
        "--checked-transcript",
        type=Path,
        default=Path("results/B9_checked_run_width_locality_transcript_v0.txt"),
    )
    parser.add_argument(
        "--json-output",
        type=Path,
        default=Path("results/B9_checked_run_acquisition_gate_v0.json"),
    )
    parser.add_argument(
        "--markdown-output",
        type=Path,
        default=Path("research/B9_checked_run_acquisition_gate.md"),
    )
    parser.add_argument("--release-host", default="release.lean-lang.org")
    parser.add_argument("--command-timeout", type=int, default=10)
    parser.add_argument("--network-timeout", type=int, default=8)
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
