from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import dataclass
from enum import Enum
from typing import Any

from .manifest import ProductManifest

AGENT_AUTHORIZE_URL = "http://127.0.0.1:8765/v1/authorize"
AGENT_LICENSE_CENTER_URL = "http://127.0.0.1:8765/license-center"


class AgentError(RuntimeError):
    """Raised when the local Licensing Agent cannot provide a trustworthy decision."""


class UpdateState(str, Enum):
    CURRENT = "current"
    AVAILABLE = "available"
    REQUIRED = "required"
    UNSUPPORTED = "unsupported"
    UNVERIFIABLE = "unverifiable"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class AuthorizationDecision:
    authorized: bool
    reason: str
    update_state: UpdateState = UpdateState.UNKNOWN
    license_center_url: str | None = None

    @property
    def activation_required(self) -> bool:
        return not self.authorized and self.reason == "activation_required"


class LicensingAgentClient:
    def __init__(self, authorize_url: str = AGENT_AUTHORIZE_URL, timeout_seconds: float = 2.0) -> None:
        if authorize_url != AGENT_AUTHORIZE_URL:
            raise ValueError("Demo App authorization endpoint is fixed to the localhost Licensing Agent")
        self._authorize_url = authorize_url
        self._timeout_seconds = timeout_seconds

    def authorize(self, manifest: ProductManifest, installation_id: str) -> AuthorizationDecision:
        if not installation_id.strip():
            raise ValueError("installation_id must be non-empty")

        body = json.dumps(
            {
                "product_id": manifest.product_id,
                "version": manifest.version,
                "installation_id": installation_id,
            }
        ).encode("utf-8")
        request = urllib.request.Request(
            self._authorize_url,
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urllib.request.urlopen(request, timeout=self._timeout_seconds) as response:
                payload = response.read()
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            raise AgentError("Licensing Agent is unavailable") from exc

        try:
            data: Any = json.loads(payload.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise AgentError("Licensing Agent returned malformed JSON") from exc

        if not isinstance(data, dict):
            raise AgentError("Licensing Agent response must be an object")
        if type(data.get("authorized")) is not bool:
            raise AgentError("Licensing Agent response is missing boolean authorized")
        if not isinstance(data.get("reason"), str) or not data["reason"].strip():
            raise AgentError("Licensing Agent response is missing reason")

        raw_update = data.get("update_state", UpdateState.UNKNOWN.value)
        try:
            update_state = UpdateState(raw_update)
        except (TypeError, ValueError):
            update_state = UpdateState.UNVERIFIABLE

        license_center_url = data.get("license_center_url")
        if license_center_url is not None:
            if not isinstance(license_center_url, str) or not license_center_url.startswith(
                "http://127.0.0.1:8765/"
            ):
                raise AgentError("Licensing Agent returned an invalid License Center URL")

        decision = AuthorizationDecision(
            authorized=data["authorized"],
            reason=data["reason"],
            update_state=update_state,
            license_center_url=license_center_url,
        )
        if decision.activation_required and decision.license_center_url is None:
            decision = AuthorizationDecision(
                authorized=False,
                reason=decision.reason,
                update_state=decision.update_state,
                license_center_url=AGENT_LICENSE_CENTER_URL,
            )
        return decision
