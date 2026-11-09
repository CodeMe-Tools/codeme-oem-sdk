"""Tests validating OEM SDK contracts against JSON Schema specifications."""

import json
from pathlib import Path
from codeme_oem_sdk.client import CodemeEngineClient
from codeme_oem_sdk.validator import ContractValidator


def test_invocation_contract_validation():
    validator = ContractValidator()

    # Valid payload
    valid_payload = {
        "version": "1.0.0",
        "command": "syntax",
        "target_path": "repos/codeme-community",
        "fix": False,
        "format": "text",
        "sandbox": False,
        "options": {},
    }
    is_valid, errors = validator.validate_invocation(valid_payload)
    assert is_valid is True
    assert len(errors) == 0

    # Invalid version
    invalid_ver = dict(valid_payload, version="2.0.0")
    is_valid, errors = validator.validate_invocation(invalid_ver)
    assert is_valid is False
    assert any("version" in e for e in errors)

    # Invalid command
    invalid_cmd = dict(valid_payload, command="unknown_engine")
    is_valid, errors = validator.validate_invocation(invalid_cmd)
    assert is_valid is False
    assert any("command" in e for e in errors)


def test_diagnostic_contract_conformance():
    validator = ContractValidator()
    client = CodemeEngineClient()

    target = Path("repos/codeme-community/src/codeme/syntax/__init__.py").resolve()
    res = client.syntax(target)
    diag_dict = res.to_dict()

    is_valid, errors = validator.validate_diagnostic(diag_dict)
    assert is_valid is True
    assert len(errors) == 0
    assert "token_metrics" in diag_dict
    assert diag_dict["token_metrics"]["estimated_tokens_saved"] >= 0
