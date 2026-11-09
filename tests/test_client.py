"""Tests for Codeme OEM SDK client."""

import pytest
from pathlib import Path
from codeme_oem_sdk.client import CodemeEngineClient


@pytest.fixture
def client():
    return CodemeEngineClient()


def test_client_syntax_clean_pass(client):
    target = Path("repos/codeme-community/src/codeme/syntax/__init__.py").resolve()
    res = client.syntax(target)
    assert res.status == "success"
    assert res.exit_code == 0
    assert len(res.diagnostics) == 0
    assert res.token_metrics.raw_output_bytes >= 0
    assert res.token_metrics.estimated_tokens_saved >= 0


def test_client_invariant_clean_pass(client):
    target = Path("repos/codeme-core").resolve()
    res = client.invariant(target, invariant_class="all")
    assert res.status == "success"
    assert res.exit_code == 0
    assert len(res.diagnostics) == 0


def test_client_syntax_violation_diagnostics(client, tmp_path):
    bad_file = tmp_path / "broken.py"
    bad_file.write_text("def broken(\n    return 42\n", encoding="utf-8")

    res = client.syntax(bad_file)
    assert res.status == "violation"
    assert res.exit_code != 0
    assert len(res.diagnostics) > 0
    assert any("CDM-" in d.code for d in res.diagnostics)


def test_client_quality_violation_diagnostics(client, tmp_path):
    bad_file = tmp_path / "complex.py"
    # Create deeply nested code violating depth threshold
    bad_file.write_text(
        "def nested():\n"
        "    if True:\n"
        "        if True:\n"
        "            if True:\n"
        "                if True:\n"
        "                    if True:\n"
        "                        return 1\n",
        encoding="utf-8",
    )

    res = client.quality(bad_file)
    assert res.status == "violation"
    assert res.exit_code != 0
    assert len(res.diagnostics) > 0
