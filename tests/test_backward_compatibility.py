"""Tests ensuring backwards compatibility of OEM SDK contracts."""

from codeme_oem_sdk.client import CodemeEngineClient


def test_schema_version_locking():
    client = CodemeEngineClient()
    # Contract v1.0.0 must be accepted
    res = client.invoke("syntax", "repos/codeme-community/src/codeme/syntax/__init__.py")
    assert res.status == "success"

    # Future major version breaking change must be flagged as configuration_error
    v2_client = CodemeEngineClient()
    # Direct validation of v2 payload
    valid, errors = v2_client.validator.validate_invocation({
        "version": "2.0.0",
        "command": "syntax",
        "target_path": "test",
    })
    assert valid is False
    assert any("version" in e for e in errors)
