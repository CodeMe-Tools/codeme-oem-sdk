"""Codeme OEM SDK Engine Client.

Provides stable, versioned, programmatic embedding of Codeme verification engines
into third-party IDEs, toolchains, CI agents, and external applications.
Conforms to schemas/invocation-contract.v1.json and schemas/diagnostic-contract.v1.json.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

from codeme_oem_sdk.models import DiagnosticItem, InvocationResult, TokenMetrics
from codeme_oem_sdk.validator import ContractValidator


class CodemeEngineClient:
    """Client for embedding Codeme verification engines without CLI presentation dependencies."""

    def __init__(
        self,
        bin_dir: Optional[str | Path] = None,
        working_dir: Optional[str | Path] = None,
    ):
        self.bin_dir = Path(bin_dir).resolve() if bin_dir else Path(sys.executable).parent
        self.working_dir = Path(working_dir).resolve() if working_dir else Path.cwd().resolve()
        self.validator = ContractValidator()

    def _resolve_binary(self, binary_name: str) -> str:
        # Check custom bin_dir or venv
        candidate = self.bin_dir / binary_name
        if candidate.is_file() and os.access(candidate, os.X_OK):
            return str(candidate)
        # Check PATH
        which = shutil.which(binary_name)
        if which:
            return which
        return binary_name

    def _parse_diagnostics_from_text(self, text: str) -> List[DiagnosticItem]:
        """Parses standard Codeme CDM diagnostic text into structured DiagnosticItems."""
        diagnostics: List[DiagnosticItem] = []
        pattern = re.compile(
            r"\[(CDM-[A-Z0-9-]+)\]\s*(?:\[([A-Z]+)\]\s*)?(?:([^:]+):(\d+):(\d+):\s*)?(.*)"
        )
        for line in text.splitlines():
            line = line.strip()
            if not line:
                continue
            m = pattern.match(line)
            if m:
                code, sev, file_p, line_n, col_n, msg = m.groups()
                diagnostics.append(
                    DiagnosticItem(
                        code=code,
                        severity=(sev.lower() if sev else "error"),
                        file=file_p or "<unknown>",
                        line=int(line_n) if line_n else 1,
                        column=int(col_n) if col_n else 1,
                        message=msg.strip() if msg else line,
                        remediation="Address detected violation and re-verify.",
                    )
                )
        return diagnostics

    def invoke(
        self,
        command: str,
        target_path: str | Path,
        fix: bool = False,
        verbose: bool = False,
        format_type: str = "text",
        sandbox: bool = False,
        options: Optional[Dict[str, Any]] = None,
    ) -> InvocationResult:
        """Executes a verification engine command via the standard OEM invocation contract."""
        start_time = time.perf_counter()
        run_id = f"run_{uuid.uuid4().hex[:12]}"

        # Validate invocation parameters
        inv_payload = {
            "version": "1.0.0",
            "command": command,
            "target_path": str(target_path),
            "fix": fix,
            "verbose": verbose,
            "format": format_type,
            "sandbox": sandbox,
            "options": options or {},
        }
        valid_inv, inv_errors = self.validator.validate_invocation(inv_payload)
        if not valid_inv:
            return InvocationResult(
                run_id=run_id,
                status="configuration_error",
                exit_code=2,
                duration_ms=0.0,
                diagnostics=[
                    DiagnosticItem(
                        code="CDM-OEM-001",
                        file=str(target_path),
                        line=1,
                        column=1,
                        message=f"Invalid invocation contract: {'; '.join(inv_errors)}",
                        remediation="Ensure required parameters match invocation-contract.v1.json.",
                    )
                ],
            )

        binary_map = {
            "syntax": "codeme-syntax",
            "quality": "codeme-quality",
            "verify": "codeme-verify",
            "invariant": "codeme-invariant",
            "toolchain": "codeme-toolchain",
        }
        bin_name = binary_map.get(command, command)
        bin_path = self._resolve_binary(bin_name)

        target = Path(target_path)
        is_file = target.is_file()

        # Build command args
        cmd: List[str] = [bin_path, "run"]
        if command in ("syntax", "quality"):
            if is_file:
                cmd.extend(["--file", str(target)])
            else:
                cmd.extend(["--repo", str(target)])
        elif command in ("verify", "invariant"):
            cmd.extend(["--repo", str(target)])

        if fix and command in ("syntax", "quality", "verify"):
            cmd.append("--fix")
        if verbose:
            cmd.append("--verbose")

        # Command-specific options
        opts = options or {}
        if command == "invariant" and "class" in opts:
            cmd.extend(["--class", str(opts["class"])])
        if command == "invariant" and opts.get("promote_baseline"):
            cmd.append("--promote-baseline")
        if command == "verify" and "test" in opts:
            cmd.extend(["--test", str(opts["test"])])

        proc = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=str(self.working_dir),
        )

        elapsed_ms = round((time.perf_counter() - start_time) * 1000.0, 2)
        raw_stdout = proc.stdout
        raw_stderr = proc.stderr
        total_raw_bytes = len(raw_stdout.encode("utf-8")) + len(raw_stderr.encode("utf-8"))

        # Success case: Universal Silent Success Contract
        if proc.returncode == 0:
            token_metrics = TokenMetrics(
                raw_output_bytes=total_raw_bytes,
                diagnostic_bytes=0,
                suppressed_bytes=total_raw_bytes,
                estimated_tokens_saved=max(0, (total_raw_bytes // 4)),
            )
            return InvocationResult(
                run_id=run_id,
                status="success",
                exit_code=0,
                duration_ms=elapsed_ms,
                diagnostics=[],
                token_metrics=token_metrics,
                raw_stdout=raw_stdout,
                raw_stderr=raw_stderr,
            )

        # Failure / Violation case
        diagnostics = self._parse_diagnostics_from_text(raw_stderr or raw_stdout)
        if not diagnostics:
            diagnostics.append(
                DiagnosticItem(
                    code=f"CDM-{command.upper()[:3]}-ERR",
                    file=str(target_path),
                    line=1,
                    column=1,
                    message=(raw_stderr.strip() or raw_stdout.strip() or f"Engine {command} failed."),
                    remediation="Inspect engine output and fix underlying condition.",
                )
            )

        diag_bytes = sum(len(d.message.encode("utf-8")) for d in diagnostics)
        token_metrics = TokenMetrics(
            raw_output_bytes=total_raw_bytes,
            diagnostic_bytes=diag_bytes,
            suppressed_bytes=max(0, total_raw_bytes - diag_bytes),
            estimated_tokens_saved=max(0, (total_raw_bytes - diag_bytes) // 4),
        )

        status = "violation"
        if proc.returncode == 3:
            status = "licensing_error"
        elif proc.returncode >= 128:
            status = "fatal"

        return InvocationResult(
            run_id=run_id,
            status=status,
            exit_code=proc.returncode,
            duration_ms=elapsed_ms,
            diagnostics=diagnostics,
            token_metrics=token_metrics,
            raw_stdout=raw_stdout,
            raw_stderr=raw_stderr,
        )

    # Programmatic Convenience APIs
    def syntax(self, target_path: str | Path, fix: bool = False, verbose: bool = False) -> InvocationResult:
        return self.invoke("syntax", target_path, fix=fix, verbose=verbose)

    def quality(self, target_path: str | Path, fix: bool = False, verbose: bool = False) -> InvocationResult:
        return self.invoke("quality", target_path, fix=fix, verbose=verbose)

    def verify(self, target_path: str | Path, fix: bool = False, test: Optional[str] = None) -> InvocationResult:
        opts = {"test": test} if test else {}
        return self.invoke("verify", target_path, fix=fix, options=opts)

    def invariant(self, target_path: str | Path, invariant_class: str = "all", promote_baseline: bool = False) -> InvocationResult:
        opts = {"class": invariant_class, "promote_baseline": promote_baseline}
        return self.invoke("invariant", target_path, options=opts)
