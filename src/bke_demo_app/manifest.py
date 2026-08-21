from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .version import APP_VERSION


class ManifestError(ValueError):
    """Raised when the product manifest is missing, malformed, or inconsistent."""


@dataclass(frozen=True)
class ProductManifest:
    schema_version: int
    product_id: str
    display_name: str
    version: str
    entry_point: str
    update_channel: str
    minimum_agent_version: str
    platform: str
    architecture: str


_REQUIRED_FIELDS: dict[str, type] = {
    "schemaVersion": int,
    "productId": str,
    "displayName": str,
    "version": str,
    "entryPoint": str,
    "updateChannel": str,
    "minimumAgentVersion": str,
    "platform": str,
    "architecture": str,
}


def _require_nonempty_string(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ManifestError(f"manifest field {field!r} must be a non-empty string")
    return value


def load_manifest(path: str | Path) -> ProductManifest:
    manifest_path = Path(path)
    try:
        raw = manifest_path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise ManifestError(f"manifest not found: {manifest_path}") from exc
    except OSError as exc:
        raise ManifestError(f"manifest unreadable: {manifest_path}") from exc

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ManifestError("manifest is not valid JSON") from exc

    if not isinstance(data, dict):
        raise ManifestError("manifest root must be a JSON object")

    missing = [field for field in _REQUIRED_FIELDS if field not in data]
    if missing:
        raise ManifestError(f"manifest missing required fields: {', '.join(missing)}")

    unexpected = sorted(set(data) - set(_REQUIRED_FIELDS))
    if unexpected:
        raise ManifestError(f"manifest contains unsupported fields: {', '.join(unexpected)}")

    for field, expected_type in _REQUIRED_FIELDS.items():
        value = data[field]
        if expected_type is int:
            if not isinstance(value, int) or isinstance(value, bool):
                raise ManifestError(f"manifest field {field!r} must be an integer")
        else:
            _require_nonempty_string(value, field)

    if data["schemaVersion"] != 1:
        raise ManifestError("unsupported manifest schemaVersion")
    if data["version"] != APP_VERSION:
        raise ManifestError(
            f"application version {APP_VERSION} does not match manifest version {data['version']}"
        )
    if data["entryPoint"] != "bke_demo_app":
        raise ManifestError("manifest entryPoint must be bke_demo_app")

    return ProductManifest(
        schema_version=data["schemaVersion"],
        product_id=data["productId"],
        display_name=data["displayName"],
        version=data["version"],
        entry_point=data["entryPoint"],
        update_channel=data["updateChannel"],
        minimum_agent_version=data["minimumAgentVersion"],
        platform=data["platform"],
        architecture=data["architecture"],
    )
