"""Data models for Codeme OEM SDK."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class DiagnosticItem:
    code: str
    file: str
    line: int
    column: int
    message: str
    remediation: str
    severity: str = "error"  # "error", "warning", "info"
    rule_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {
            "code": self.code,
            "file": self.file,
            "line": self.line,
            "column": self.column,
            "severity": self.severity,
            "message": self.message,
            "remediation": self.remediation,
        }
        if self.rule_id:
            d["rule_id"] = self.rule_id
        return d


@dataclass
class TokenMetrics:
    raw_output_bytes: int = 0
    diagnostic_bytes: int = 0
    suppressed_bytes: int = 0
    estimated_tokens_saved: int = 0

    def to_dict(self) -> Dict[str, int]:
        return {
            "raw_output_bytes": self.raw_output_bytes,
            "diagnostic_bytes": self.diagnostic_bytes,
            "suppressed_bytes": self.suppressed_bytes,
            "estimated_tokens_saved": self.estimated_tokens_saved,
        }


@dataclass
class InvocationResult:
    run_id: str
    status: str  # "success", "violation", "configuration_error", "licensing_error", "fatal"
    exit_code: int
    duration_ms: float
    diagnostics: List[DiagnosticItem] = field(default_factory=list)
    token_metrics: TokenMetrics = field(default_factory=TokenMetrics)
    raw_stdout: str = ""
    raw_stderr: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "run_id": self.run_id,
            "status": self.status,
            "exit_code": self.exit_code,
            "duration_ms": self.duration_ms,
            "diagnostics": [d.to_dict() for d in self.diagnostics],
            "token_metrics": self.token_metrics.to_dict(),
        }
