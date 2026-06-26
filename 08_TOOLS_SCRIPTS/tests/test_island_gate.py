import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Add directory to sys.path to import island_gate
sys.path.append(os.path.abspath("08_TOOLS_SCRIPTS"))

from island_gate import (
    REQUIRED_MANIFEST_FIELDS,
    validate_manifest,
)


def valid_manifest_item(record_id="test-1"):
    """Returns a valid manifest item that passes all basic validations."""
    item = {field: f"dummy_{field}" for field in REQUIRED_MANIFEST_FIELDS}

    # Overwrite specific fields that have validation rules
    item.update(
        {
            "id": record_id,
            "rag_allowed": False,
            "livefeed_allowed": False,
            "lifecycle_state": "MIGRATED",
            "depends_on": [],
        }
    )
    return item


def create_manifest(tmp_path: Path, items: list[dict]):
    """Creates a temporary JSONL manifest file and returns its path."""
    manifest_path = tmp_path / "test_manifest.jsonl"
    with open(manifest_path, "w", encoding="utf-8") as f:
        for item in items:
            f.write(json.dumps(item) + "\n")
    return manifest_path


def test_validate_manifest_happy_path(tmp_path: Path):
    """Test that a valid manifest returns no errors."""
    manifest_path = create_manifest(tmp_path, [valid_manifest_item()])
    errors = validate_manifest(manifest_path)
    assert errors == []


def test_validate_manifest_missing_fields(tmp_path: Path):
    """Test that missing fields trigger an error."""
    item = valid_manifest_item()
    del item["rag_allowed"]
    del item["origin_type"]
    manifest_path = create_manifest(tmp_path, [item])
    errors = validate_manifest(manifest_path)
    assert len(errors) == 1
    assert "missing manifest fields: origin_type, rag_allowed" in errors[0]


def test_validate_manifest_duplicate_ids(tmp_path: Path):
    """Test that duplicate IDs are rejected."""
    item1 = valid_manifest_item("test-1")
    item2 = valid_manifest_item("test-1")
    manifest_path = create_manifest(tmp_path, [item1, item2])
    errors = validate_manifest(manifest_path)
    assert len(errors) == 1
    assert "test-1: duplicate id" in errors[0]


def test_validate_manifest_rag_constraints(tmp_path: Path):
    """Test constraints when rag_allowed=True."""
    item = valid_manifest_item()
    item["rag_allowed"] = True

    # 1. Unsafe risk_class
    item["risk_class"] = "unsafe_risk"
    item["trust_level"] = "verified"
    item["lifecycle_state"] = "ACTIVE"
    item["verification_method"] = "manual"
    item["last_verified"] = "2023-01-01T00:00:00Z"
    item["verification_evidence"] = "doc-123"

    manifest_path = create_manifest(tmp_path, [item])
    errors = validate_manifest(manifest_path)
    assert any("rag_allowed=true with unsafe risk_class" in e for e in errors)

    # 2. Insufficient trust_level
    item["risk_class"] = "safe"
    item["trust_level"] = "unverified"
    manifest_path = create_manifest(tmp_path, [item])
    errors = validate_manifest(manifest_path)
    assert any("rag_allowed=true with insufficient trust_level" in e for e in errors)

    # 3. Not in ACTIVE_STATES
    item["trust_level"] = "verified"
    item["lifecycle_state"] = "DRAFT"
    manifest_path = create_manifest(tmp_path, [item])
    errors = validate_manifest(manifest_path)
    assert any("rag_allowed=true before verified lifecycle state" in e for e in errors)

    # 4. Missing/invalid verification_method
    item["lifecycle_state"] = "ACTIVE"
    for invalid_method in [None, "", "not_verified"]:
        item["verification_method"] = invalid_method
        manifest_path = create_manifest(tmp_path, [item])
        errors = validate_manifest(manifest_path)
        assert any("rag_allowed=true without verification_method" in e for e in errors)


def test_validate_manifest_livefeed_constraints(tmp_path: Path):
    """Test constraints when livefeed_allowed=True."""
    item = valid_manifest_item()
    item["livefeed_allowed"] = True
    item["risk_class"] = "private"  # In BLOCKED_RISK

    manifest_path = create_manifest(tmp_path, [item])
    errors = validate_manifest(manifest_path)
    assert len(errors) == 1
    assert "livefeed_allowed=true with blocked risk_class" in errors[0]


def test_validate_manifest_active_state_constraints(tmp_path: Path):
    """Test constraints when lifecycle_state is ACTIVE."""
    item = valid_manifest_item()
    item["lifecycle_state"] = "ACTIVE"

    # Missing verification details
    item["last_verified"] = ""
    item["verification_evidence"] = ""
    manifest_path = create_manifest(tmp_path, [item])
    errors = validate_manifest(manifest_path)
    assert any(
        "ACTIVE requires last_verified and verification_evidence" in e for e in errors
    )

    # Verification expired
    item["last_verified"] = "2023-01-01T00:00:00Z"
    item["verification_evidence"] = "doc-123"
    past_date = datetime.now(timezone.utc) - timedelta(days=1)
    item["verification_expiry"] = past_date.isoformat()
    manifest_path = create_manifest(tmp_path, [item])
    errors = validate_manifest(manifest_path)
    assert any("ACTIVE verification is expired" in e for e in errors)


def test_validate_manifest_dependency_checks(tmp_path: Path):
    """Test that dependencies are validated correctly."""
    # Item requiring verified deps
    item = valid_manifest_item("test-1")
    item["lifecycle_state"] = "ACTIVE"
    item["last_verified"] = "2023-01-01T00:00:00Z"
    item["verification_evidence"] = "doc-123"
    future_date = datetime.now(timezone.utc) + timedelta(days=1)
    item["verification_expiry"] = future_date.isoformat()
    item["depends_on"] = ["dep-1"]

    # Dependency is missing entirely
    manifest_path = create_manifest(tmp_path, [item])
    errors = validate_manifest(manifest_path)
    assert len(errors) == 1
    assert "dependency not found: dep-1" in errors[0]

    # Dependency exists but not in ACTIVE_STATES
    dep = valid_manifest_item("dep-1")
    dep["lifecycle_state"] = "DRAFT"
    manifest_path = create_manifest(tmp_path, [item, dep])
    errors = validate_manifest(manifest_path)
    assert len(errors) == 1
    assert "dependency dep-1 is not verified/active: DRAFT" in errors[0]
