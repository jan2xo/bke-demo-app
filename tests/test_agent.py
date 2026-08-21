import io
import json
import unittest
from unittest.mock import patch

from bke_demo_app.agent import AgentError, LicensingAgentClient, UpdateState
from bke_demo_app.manifest import ProductManifest


MANIFEST = ProductManifest(1, "bke-demo-app", "BKE Demo App", "1.0.0", "bke_demo_app", "stable", "1.0.0", "linux", "x64")


class FakeResponse:
    def __init__(self, payload):
        self._io = io.BytesIO(payload)
    def __enter__(self):
        return self
    def __exit__(self, *args):
        return False
    def read(self):
        return self._io.read()


class AgentTests(unittest.TestCase):
    def test_allow(self):
        payload = json.dumps({"authorized": True, "reason": "ok", "update_state": "current"}).encode()
        with patch("urllib.request.urlopen", return_value=FakeResponse(payload)):
            decision = LicensingAgentClient().authorize(MANIFEST, "install-1")
        self.assertTrue(decision.authorized)
        self.assertEqual(decision.update_state, UpdateState.CURRENT)

    def test_activation_required_uses_agent_license_center(self):
        payload = json.dumps({"authorized": False, "reason": "activation_required"}).encode()
        with patch("urllib.request.urlopen", return_value=FakeResponse(payload)):
            decision = LicensingAgentClient().authorize(MANIFEST, "install-1")
        self.assertFalse(decision.authorized)
        self.assertEqual(decision.license_center_url, "http://127.0.0.1:8765/license-center")

    def test_malformed_response_fails_closed(self):
        with patch("urllib.request.urlopen", return_value=FakeResponse(b"not-json")):
            with self.assertRaises(AgentError):
                LicensingAgentClient().authorize(MANIFEST, "install-1")

    def test_missing_authorized_fails_closed(self):
        payload = json.dumps({"reason": "ok"}).encode()
        with patch("urllib.request.urlopen", return_value=FakeResponse(payload)):
            with self.assertRaises(AgentError):
                LicensingAgentClient().authorize(MANIFEST, "install-1")

    def test_non_local_license_center_is_rejected(self):
        payload = json.dumps({"authorized": False, "reason": "activation_required", "license_center_url": "https://example.com"}).encode()
        with patch("urllib.request.urlopen", return_value=FakeResponse(payload)):
            with self.assertRaises(AgentError):
                LicensingAgentClient().authorize(MANIFEST, "install-1")

    def test_unknown_update_state_becomes_unverifiable(self):
        payload = json.dumps({"authorized": True, "reason": "ok", "update_state": "mystery"}).encode()
        with patch("urllib.request.urlopen", return_value=FakeResponse(payload)):
            decision = LicensingAgentClient().authorize(MANIFEST, "install-1")
        self.assertEqual(decision.update_state, UpdateState.UNVERIFIABLE)


if __name__ == "__main__":
    unittest.main()
