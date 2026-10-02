from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Callable

from .agent import AgentError, AuthorizationDecision, LicensingAgentClient, UpdateState
from .manifest import ManifestError, ProductManifest, load_manifest


class AppState(str, Enum):
    STARTING = "starting"
    AGENT_UNAVAILABLE = "agent_unavailable"
    ACTIVATION_REQUIRED = "activation_required"
    AUTHORIZED = "authorized"
    DENIED = "denied"
    UNSUPPORTED = "unsupported"
    UNVERIFIABLE = "unverifiable"
    MANIFEST_ERROR = "manifest_error"


@dataclass(frozen=True)
class AppStatus:
    state: AppState
    message: str
    manifest: ProductManifest | None = None
    decision: AuthorizationDecision | None = None

    @property
    def protected_enabled(self) -> bool:
        return self.state == AppState.AUTHORIZED


class DemoController:
    def __init__(
        self,
        manifest_path: str,
        installation_id: str,
        agent_client: LicensingAgentClient | None = None,
    ) -> None:
        self._manifest_path = manifest_path
        self._installation_id = installation_id
        self._agent = agent_client or LicensingAgentClient()
        self.status = AppStatus(AppState.STARTING, "Starting")

    def refresh(self) -> AppStatus:
        try:
            manifest = load_manifest(self._manifest_path)
        except ManifestError as exc:
            self.status = AppStatus(AppState.MANIFEST_ERROR, str(exc))
            return self.status

        try:
            decision = self._agent.authorize(manifest, self._installation_id)
        except AgentError as exc:
            self.status = AppStatus(AppState.AGENT_UNAVAILABLE, str(exc), manifest=manifest)
            return self.status
        except (TypeError, ValueError) as exc:
            self.status = AppStatus(AppState.UNVERIFIABLE, str(exc), manifest=manifest)
            return self.status

        if decision.update_state == UpdateState.UNSUPPORTED:
            state = AppState.UNSUPPORTED
        elif decision.update_state == UpdateState.UNVERIFIABLE:
            state = AppState.UNVERIFIABLE
        elif decision.authorized:
            state = AppState.AUTHORIZED
        elif decision.activation_required:
            state = AppState.ACTIVATION_REQUIRED
        else:
            state = AppState.DENIED

        self.status = AppStatus(
            state=state,
            message=decision.reason,
            manifest=manifest,
            decision=decision,
        )
        return self.status

    def run_protected(self, action: Callable[[], None]) -> bool:
        """Run protected product functionality only after a current ALLOW decision."""
        if not self.status.protected_enabled:
            return False
        action()
        return True
