"""Tests for the data ingestion and normalization pipeline."""

from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent


def test_data_directories_exist():
    """Verify required data directories are present."""
    assert (PROJECT_ROOT / "data" / "raw").exists()
    assert (PROJECT_ROOT / "data" / "sample").exists()
    assert (PROJECT_ROOT / "data" / "processed").exists()
    assert (PROJECT_ROOT / "data" / "schemas").exists()


def test_schema_file_exists():
    """Verify WO field schema is defined."""
    assert (PROJECT_ROOT / "data" / "schemas" / "wo_fields.yaml").exists()
