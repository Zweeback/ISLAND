from __future__ import annotations

#!/usr/bin/env python3
"""Minimal gatekeeper for the Zentrale Insel.

This script validates JSONL manifests and service status records. It is small on
purpose: the first enforcement layer should be boring, local, and auditable.
"""


import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "03_MANIFESTE_INVENTAR" / "island_manifest.jsonl"
DEFAULT_STATUS = ROOT / "06_GATEWAY_LIVEFEED" / "service_status.jsonl"

REQUIRED_MANIFEST_FIELDS = {
    "schema_version",
    "id",
    "artifact_family",
    "object_kind",
    "discovered_at",
    "source_path",
    "source_zone",
    "origin_type",
    "risk_class",
    "trust_level",
    "target_lane",
    "lifecycle_state",
    "owner",
    "depends_on",
    "used_by",
    "rag_allowed",
    "livefeed_allowed",
    "verification_method",
    "next_action",
}

SAFE_RAG_RISK = {"safe"}
SAFE_RAG_TRUST = {"verified", "semi_verified"}
BLOCKED_RISK = {"private", "secret_risk", "binary_unknown", "compromised"}
ACTIVE_STATES = {"VERIFIED", "MIGRATED", "INDEXED", "ACTIVE"}

REQUIRED_STATUS_FIELDS = {
    "schema_version",
    "service_id",
    "status",
    "process",
    "port_or_endpoint",
    "healthcheck",
    "last_telemetry_timestamp",
    "last_successful_action",
    "last_error",
    "source_log",
    "start_command",
    "stop_command",
    "depends_on",
    "e2e_test_id",
    "verified_by",
    "claim_registry_refs",
    "expires_at",
}

VALID_STATUS = {
    "online_verified",
    "degraded",
    "unverified",
    "offline",
    "broken",
    "unknown",
    "quota_limited",
    "manual_only",
}


def parse_time(value: Any) -> datetime | None:
    if not value:
        return None
    if not isinstance(value, str):
        return None
    try:
        fixed = value.replace("Z", "+00:00")
        return datetime.fromisoformat(fixed)
    except ValueError:
        return None


def iter_jsonl(path: Path) -> tuple[list[dict[str, Any]], list[str]]:
    errors: list[str] = []
    records: list[dict[str, Any]] = []
    if not path.exists():
        return records, [f"missing file: {path}"]
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        stripped = line.strip()
        if not stripped:
            continue
        try:
            item = json.loads(stripped)
        except json.JSONDecodeError as exc:
            errors.append(f"{path}:{line_no}: invalid json: {exc}")
            continue
        if not isinstance(item, dict):
            errors.append(f"{path}:{line_no}: record is not an object")
            continue
        records.append(item)
    return records, errors


def validate_manifest(path: Path) -> list[str]:
    records, errors = iter_jsonl(path)
    seen_ids: set[str] = set()
    state_by_id: dict[str, str] = {}
    for idx, item in enumerate(records, 1):
        record_id = item.get("id", f"line-{idx}")
        missing = sorted(REQUIRED_MANIFEST_FIELDS - set(item))
        if missing:
            errors.append(f"{record_id}: missing manifest fields: {', '.join(missing)}")
        if record_id in seen_ids:
            errors.append(f"{record_id}: duplicate id")
        seen_ids.add(str(record_id))
        state_by_id[str(record_id)] = str(item.get("lifecycle_state", ""))

        if item.get("rag_allowed") is True:
            if item.get("risk_class") not in SAFE_RAG_RISK:
                errors.append(
                    f"{record_id}: rag_allowed=true with unsafe risk_class={item.get('risk_class')}"
                )
            if item.get("trust_level") not in SAFE_RAG_TRUST:
                errors.append(
                    f"{record_id}: rag_allowed=true with insufficient trust_level={item.get('trust_level')}"
                )
            if item.get("lifecycle_state") not in ACTIVE_STATES:
                errors.append(
                    f"{record_id}: rag_allowed=true before verified lifecycle state"
                )
            if item.get("verification_method") in (None, "", "not_verified"):
                errors.append(
                    f"{record_id}: rag_allowed=true without verification_method"
                )

        if (
            item.get("livefeed_allowed") is True
            and item.get("risk_class") in BLOCKED_RISK
        ):
            errors.append(
                f"{record_id}: livefeed_allowed=true with blocked risk_class={item.get('risk_class')}"
            )

        if item.get("lifecycle_state") == "ACTIVE":
            if not item.get("last_verified") or not item.get("verification_evidence"):
                errors.append(
                    f"{record_id}: ACTIVE requires last_verified and verification_evidence"
                )
            expiry = parse_time(item.get("verification_expiry"))
            if expiry and expiry < datetime.now(expiry.tzinfo or timezone.utc):
                errors.append(f"{record_id}: ACTIVE verification is expired")

    for item in records:
        record_id = str(item.get("id"))
        needs_verified_deps = (
            item.get("lifecycle_state") in ACTIVE_STATES
            or item.get("rag_allowed") is True
            or item.get("livefeed_allowed") is True
        )
        if not needs_verified_deps:
            continue
        for dep in item.get("depends_on") or []:
            dep_state = state_by_id.get(str(dep))
            if dep_state is None:
                errors.append(f"{record_id}: dependency not found: {dep}")
            elif dep_state not in ACTIVE_STATES:
                errors.append(
                    f"{record_id}: dependency {dep} is not verified/active: {dep_state}"
                )
    return errors


def validate_status(path: Path) -> list[str]:
    records, errors = iter_jsonl(path)
    for idx, item in enumerate(records, 1):
        service_id = item.get("service_id", f"line-{idx}")
        missing = sorted(REQUIRED_STATUS_FIELDS - set(item))
        if missing:
            errors.append(f"{service_id}: missing status fields: {', '.join(missing)}")
        status = item.get("status")
        if status not in VALID_STATUS:
            errors.append(f"{service_id}: invalid status={status}")
        if status == "online_partial":
            errors.append(
                f"{service_id}: online_partial is forbidden; use unverified or degraded"
            )
        if status == "online_verified":
            required_for_online = [
                "process",
                "port_or_endpoint",
                "healthcheck",
                "last_telemetry_timestamp",
                "last_successful_action",
                "source_log",
                "start_command",
                "stop_command",
                "e2e_test_id",
                "verified_by",
                "expires_at",
            ]
            for field in required_for_online:
                if item.get(field) in (None, "", []):
                    errors.append(f"{service_id}: online_verified requires {field}")
        expiry = parse_time(item.get("expires_at"))
        if (
            status == "online_verified"
            and expiry
            and expiry < datetime.now(expiry.tzinfo or timezone.utc)
        ):
            errors.append(f"{service_id}: online_verified status is expired")
    return errors


def handle_register(manifest_path: Path) -> int:
    """Validate and register a manifest JSONL file."""
    errors = validate_manifest(manifest_path)
    if errors:
        print("REGISTER FAILED")
        for e in errors:
            print(f"- {e}")
        return 1
    print("REGISTER PASSED")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate Zentrale Insel manifest/status gates."
    )
    parser.add_argument("mode", choices=["manifest", "status", "all", "register"])
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--status", type=Path, default=DEFAULT_STATUS)
    args = parser.parse_args()

    errors: list[str] = []
    if args.mode in {"manifest", "all"}:
        errors.extend(validate_manifest(args.manifest))
    if args.mode in {"status", "all"}:
        errors.extend(validate_status(args.status))
    if args.mode == "register":
        return handle_register(args.manifest)

    if errors:
        print("GATE FAILED")
        for error in errors:
            print(f"- {error}")
        return 1
    print("GATE PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
