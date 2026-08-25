import json
import tempfile
import unittest
from pathlib import Path

from bke_demo_app.manifest import ManifestError, load_manifest


VALID = {
    "schemaVersion": 1,
    "productId": "bke-institution-suite",
    "displayName": "BKE Institution Suite",
    "version": "1.0.0",
    "entryPoint": "BKE Institution Suite",
    "updateChannel": "stable",
    "minimumAgentVersion": "0.1.0",
    "platform": "macos",
    "architecture": "x64",
}


class ManifestTests(unittest.TestCase):
    def write(self, value):
        tmp = tempfile.TemporaryDirectory()
        path = Path(tmp.name) / "bke.manifest.json"
        path.write_text(json.dumps(value), encoding="utf-8")
        self.addCleanup(tmp.cleanup)
        return path

    def test_valid_manifest(self):
        manifest = load_manifest(self.write(VALID))
        self.assertEqual(manifest.product_id, "bke-institution-suite")
        self.assertEqual(manifest.version, "1.0.0")
        self.assertEqual(manifest.entry_point, "BKE Institution Suite")

    def test_missing_manifest(self):
        with self.assertRaises(ManifestError):
            load_manifest("/definitely/missing/bke.manifest.json")

    def test_invalid_json(self):
        tmp = tempfile.TemporaryDirectory()
        path = Path(tmp.name) / "bke.manifest.json"
        path.write_text("{broken", encoding="utf-8")
        self.addCleanup(tmp.cleanup)
        with self.assertRaises(ManifestError):
            load_manifest(path)

    def test_missing_required_field(self):
        data = dict(VALID)
        data.pop("productId")
        with self.assertRaises(ManifestError):
            load_manifest(self.write(data))

    def test_version_mismatch_is_rejected(self):
        data = dict(VALID)
        data["version"] = "9.9.9"
        with self.assertRaisesRegex(ManifestError, "does not match"):
            load_manifest(self.write(data))

    def test_unknown_field_is_rejected(self):
        data = dict(VALID)
        data["licenseKey"] = "must-not-live-here"
        with self.assertRaises(ManifestError):
            load_manifest(self.write(data))


if __name__ == "__main__":
    unittest.main()
