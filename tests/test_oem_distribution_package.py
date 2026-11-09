"""Tests for OEM SDK distribution package validation and bundling."""

import pytest
from pathlib import Path
from codeme_oem_sdk.bundler import OEMPackageBundler


def test_oem_package_structure_and_bundler(tmp_path):
    bundler = OEMPackageBundler()
    report = bundler.build_oem_distribution_archive(output_dir=tmp_path)

    assert report.valid is True
    assert len(report.errors) == 0
    assert any("JSON schema contracts" in c for c in report.checks_passed)
    assert any("TypeScript client" in c for c in report.checks_passed)
    assert any("Python OEM SDK client" in c for c in report.checks_passed)
    assert any("Zero proprietary" in c for c in report.checks_passed)
    assert any("Token savings" in c for c in report.checks_passed)

    # Check generated archive
    archive_file = Path(report.artifact_path)
    assert archive_file.is_file()
    assert archive_file.stat().st_size > 0
    assert report.artifact_sha256 is not None
