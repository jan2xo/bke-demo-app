from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "src" / "bke_demo_app"


class BoundaryTests(unittest.TestCase):
    def test_no_direct_updater_core_dependency_or_import(self):
        files = [ROOT / "pyproject.toml", *SOURCE.glob("*.py")]
        text = "\n".join(path.read_text(encoding="utf-8") for path in files)
        self.assertNotIn("bke-updater-core", text.lower())
        self.assertNotRegex(text, r"(?m)^\s*(from|import)\s+.*updater")

    def test_no_duplicated_lease_signature_or_update_verification_logic(self):
        text = "\n".join(path.read_text(encoding="utf-8") for path in SOURCE.glob("*.py"))
        forbidden = [
            r"verify_lease",
            r"verify_signature",
            r"public_key",
            r"ed25519",
            r"rsa",
            r"ecdsa",
            r"jwt",
            r"lease_token",
        ]
        for pattern in forbidden:
            with self.subTest(pattern=pattern):
                self.assertIsNone(re.search(pattern, text, flags=re.IGNORECASE))

    def test_agent_authorization_boundary_is_loopback_only(self):
        agent_text = (SOURCE / "agent.py").read_text(encoding="utf-8")
        self.assertIn('AGENT_AUTHORIZE_URL = "http://127.0.0.1:8765/v1/authorize"', agent_text)
        self.assertNotIn("0.0.0.0", agent_text)


if __name__ == "__main__":
    unittest.main()
