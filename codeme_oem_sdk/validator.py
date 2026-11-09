"""Schema validation utility for Codeme OEM invocation and diagnostic contracts."""

import json
from pathlib import Path
from typing import Any, Dict, List, Tuple


class ContractValidator:
    """Validates contract payloads against JSON schema definitions."""

    def __init__(self, schemas_dir: Path | None = None):
        self.schemas_dir = schemas_dir or (Path(__file__).parent.parent / "schemas")
        self.invocation_schema = self._load_schema("invocation-contract.v1.json")
        self.diagnostic_schema = self._load_schema("diagnostic-contract.v1.json")

    def _load_schema(self, filename: str) -> Dict[str, Any]:
        p = self.schemas_dir / filename
        if p.is_file():
            with open(p, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def validate_invocation(self, payload: Dict[str, Any]) -> Tuple[bool, List[str]]:
        errors: List[str] = []
        if payload.get("version") != "1.0.0":
            errors.append("Invalid or missing version. Expected '1.0.0'.")
        if payload.get("command") not in {"syntax", "quality", "verify", "invariant", "toolchain"}:
            errors.append(f"Invalid command '{payload.get('command')}'.")
        if not payload.get("target_path"):
            errors.append("Missing required field 'target_path'.")
        return len(errors) == 0, errors

    def validate_diagnostic(self, payload: Dict[str, Any]) -> Tuple[bool, List[str]]:
        errors: List[str] = []
        for req in ["run_id", "status", "exit_code", "diagnostics", "token_metrics"]:
            if req not in payload:
                errors.append(f"Missing required field '{req}'.")
        if payload.get("status") not in {"success", "violation", "configuration_error", "licensing_error", "fatal"}:
            errors.append(f"Invalid status '{payload.get('status')}'.")
        return len(errors) == 0, errors
