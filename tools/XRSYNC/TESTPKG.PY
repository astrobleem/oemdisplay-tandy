"""Closed public archive and own-media OEM preparation regression checks."""
import importlib.util
from importlib.machinery import SourceFileLoader
import io
import json
from pathlib import Path
import shutil
import tempfile
import unittest
import zipfile

HERE = Path(__file__).resolve().parent
def load(name):
    loader = SourceFileLoader(name.lower(), str(HERE / (name + ".PY")))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module
prepare = load("PREPARE")
publish = load("PUBLISH")


class PackageTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.media = self.root / "media"
        self.media.mkdir()
        self.payload = self.root / "payload"
        shutil.copytree(HERE / "PAYLOAD", self.payload)
        self.spec = json.loads((HERE / "INPUTS.JSN").read_bytes())
        self.fixture = b"first-party synthetic grabber input; no Windows bytes"
        self.spec["grabber"] = publish.pub.identity(self.fixture)
        (self.media / "CGA.GR2").write_bytes(self.fixture)
        self.out = self.root / "prepared"

    def run_prepare(self):
        return prepare.prepare(self.media, self.payload, self.out, self.spec)

    def test_complete_prepared_disk(self):
        report = self.run_prepare()
        self.assertEqual(set(report["files"]), set(self.spec["payload"]) | {"CGA.GR2"})
        self.assertEqual((self.out / "CGA.GR2").read_bytes(), self.fixture)
        for name, pin in report["files"].items():
            self.assertEqual(publish.pub.identity((self.out / name).read_bytes()), pin)

    def test_wrong_owned_input_creates_nothing(self):
        (self.media / "CGA.GR2").write_bytes(b"wrong")
        with self.assertRaises(ValueError):
            self.run_prepare()
        self.assertFalse(self.out.exists())

    def test_changed_runtime_creates_nothing(self):
        (self.payload / "XRSYNC.DRV").write_bytes(b"wrong")
        with self.assertRaises(ValueError):
            self.run_prepare()
        self.assertFalse(self.out.exists())

    def test_existing_output_preserved(self):
        self.out.mkdir()
        (self.out / "KEEP").write_bytes(b"saved")
        with self.assertRaises(ValueError):
            self.run_prepare()
        self.assertEqual((self.out / "KEEP").read_bytes(), b"saved")

    def test_output_cannot_overlap_input(self):
        self.out = self.media / "nested"
        with self.assertRaises(ValueError):
            self.run_prepare()
        self.assertFalse(self.out.exists())

    def test_public_zip_exact_and_deterministic(self):
        entries = publish.collect()
        first = publish.pub.zip_bytes(entries)
        self.assertEqual(first, publish.pub.zip_bytes(entries))
        publish.pub.check_zip(first, entries, "test")
        with zipfile.ZipFile(io.BytesIO(first)) as archive:
            self.assertEqual(set(archive.namelist()), set(entries))
            self.assertNotIn("PAYLOAD/CGA.GR2", archive.namelist())
            self.assertEqual(publish.pub.identity(archive.read("PAYLOAD/XRSYNC.DRV")), publish.DRIVER)

    def test_published_assets_verify_and_reject_tamper(self):
        release = self.root / "release"
        publish.build(release, "e84a17d1562a3f938b5268b8a92fc5e47b176deb")
        publish.build(release, "e84a17d1562a3f938b5268b8a92fc5e47b176deb")
        with (release / "XRSYNC.ZIP").open("ab") as stream:
            stream.write(b"tamper")
        with self.assertRaises(ValueError):
            publish.build(release, "e84a17d1562a3f938b5268b8a92fc5e47b176deb")


if __name__ == "__main__":
    unittest.main()
