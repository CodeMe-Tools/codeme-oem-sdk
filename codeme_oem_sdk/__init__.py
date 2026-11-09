"""
Codeme OEM SDK - Version 1.0.0
Stable, versioned embedding interface for embedding Codeme verification engines into third-party IDEs, toolchains, and CI agents.
"""
from typing import Dict, Any, List, Optional
import subprocess
import json
import shutil
import os

class CodemeEngineClient:
    def __init__(self, cli_path: Optional[str] = None):
        self.cli_path = cli_path or shutil.which("codeme-toolchain") or "codeme-toolchain"

    def invoke(
        self,
        command: str,
        target_path: str,
        fix: bool = False,
        format_type: str = "json",
        sandbox: bool = False,
        extra_args: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Executes a Codeme engine command using the standard OEM contract.
        Returns the parsed diagnostic dictionary.
        """
        subcommand_map = {
            "syntax": "codeme-syntax",
            "quality": "codeme-quality",
            "verify": "codeme-verify",
            "invariant": "codeme-invariant",
            "toolchain": "codeme-toolchain"
        }
        bin_name = subcommand_map.get(command, command)
        cmd = [bin_name, "run", "--repo", target_path, "--format", format_type]
        if fix:
            cmd.append("--fix")
        if sandbox:
            cmd.append("--sandbox")
        if extra_args:
            cmd.extend(extra_args)

        proc = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        if proc.returncode == 0 and not proc.stdout.strip():
            # Universal silent success contract
            return {
                "status": "success",
                "exit_code": 0,
                "diagnostics": [],
                "token_metrics": {
                    "raw_output_bytes": 0,
                    "diagnostic_bytes": 0,
                    "suppressed_bytes": 0,
                    "estimated_tokens_saved": 0
                }
            }

        # Parse JSON diagnostic
        try:
            return json.loads(proc.stdout)
        except Exception:
            return {
                "status": "violation" if proc.returncode != 0 else "success",
                "exit_code": proc.returncode,
                "stderr": proc.stderr,
                "stdout": proc.stdout,
                "diagnostics": [
                    {
                        "code": f"CDM-{proc.returncode}",
                        "message": proc.stderr.strip() or proc.stdout.strip()
                    }
                ]
            }
