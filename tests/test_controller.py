import json
import tempfile
import unittest
from pathlib import Path

from bke_demo_app.agent import AgentError, AuthorizationDecision, UpdateState
from bke_demo_app.controller import AppState, DemoController


MANIFEST = {
    "schemaVersion": 1,
    "productId": "bke-demo-app",
    "displayName": "BKE Demo App",
    "version": "1.0.0",
    "entryPoint": "bke_demo_app",
    "updateChannel": "stable",
    "minimumAgentVersion": "1.0.0",
    "platform": "linux",
    "architecture": "x64",
}


class FakeAgent:
    def __init__(self, result=None, error=None):
        self.result = result
        self.error = error
    def authorize(self, manifest, installation_id):
        if self.error:
            raise self.error
        return self.result


class ControllerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.manifest_path = Path(self.tmp.name) / "bke.manifest.json"
        self.manifest_path.write_text(json.dumps(MANIFEST), encoding="utf-8")

    def controller(self, result=None, error=None):
        return DemoController(str(self.manifest_path), "install-1", FakeAgent(result, error))

    def test_allow_enables_and_runs_protected_action(self):
        controller = self.controller(AuthorizationDecision(True, "ok", UpdateState.CURRENT))
        self.assertEqual(controller.refresh().state, AppState.AUTHORIZED)
        ran = []
        self.assertTrue(controller.run_protected(lambda: ran.append(True)))
        self.assertEqual(ran, [True])

    def test_deny_never_runs_protected_action(self):
        controller = self.controller(AuthorizationDecision(False, "license_denied", UpdateState.CURRENT))
        self.assertEqual(controller.refresh().state, AppState.DENIED)
        ran = []
        self.assertFalse(controller.run_protected(lambda: ran.append(True)))
        self.assertEqual(ran, [])

    def test_activation_required_stays_blocked(self):
        controller = self.controller(AuthorizationDecision(False, "activation_required", UpdateState.CURRENT, "http://127.0.0.1:8765/license-center"))
        self.assertEqual(controller.refresh().state, AppState.ACTIVATION_REQUIRED)
        self.assertFalse(controller.status.protected_enabled)

    def test_agent_unavailable_stays_blocked(self):
        controller = self.controller(error=AgentError("offline"))
        self.assertEqual(controller.refresh().state, AppState.AGENT_UNAVAILABLE)
        self.assertFalse(controller.status.protected_enabled)

    def test_unsupported_stays_blocked_even_if_authorized_boolean_is_true(self):
        controller = self.controller(AuthorizationDecision(True, "unsupported", UpdateState.UNSUPPORTED))
        self.assertEqual(controller.refresh().state, AppState.UNSUPPORTED)
        self.assertFalse(controller.status.protected_enabled)

    def test_unverifiable_stays_blocked_even_if_authorized_boolean_is_true(self):
        controller = self.controller(AuthorizationDecision(True, "bad-update", UpdateState.UNVERIFIABLE))
        self.assertEqual(controller.refresh().state, AppState.UNVERIFIABLE)
        self.assertFalse(controller.status.protected_enabled)


if __name__ == "__main__":
    unittest.main()
