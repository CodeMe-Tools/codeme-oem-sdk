"""Codeme OEM SDK - Version 1.0.0.

Stable, versioned embedding interface for embedding Codeme verification engines
into third-party IDEs, toolchains, CI agents, and external applications.
"""

from codeme_oem_sdk.client import CodemeEngineClient
from codeme_oem_sdk.models import DiagnosticItem, InvocationResult, TokenMetrics
from codeme_oem_sdk.validator import ContractValidator

__all__ = [
    "CodemeEngineClient",
    "DiagnosticItem",
    "InvocationResult",
    "TokenMetrics",
    "ContractValidator",
]

__version__ = "1.0.0"
