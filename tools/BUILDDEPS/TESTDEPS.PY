"""Host-only integrity/refusal tests; no network, emulator or installer."""
import importlib.machinery
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest import mock

deps = importlib.machinery.SourceFileLoader(
    "builddeps", str(Path(__file__).with_name("DEPS.PY"))).load_module()


class DependencyTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="builddeps-test-")
        self.root = Path(self.temp.name).resolve()
        self.repo = self.root / "repo"
        self.repo.mkdir()
        subprocess.run(["git", "init", str(self.repo)], check=True,
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.original = {"BIN/MASM.EXE": b"\x00\x01fake\r\n",
                         "DDK/286/INC/CMACROS.INC": b".8086\r\n",
                         "INCLUDE/STDIO.H": b"header\n",
                         "LIB/LIBW.LIB": b"library"}
        for name, content in self.original.items():
            path = self.repo / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)
        source = self.repo / "src/tandysw/V1.ASM"
        source.parent.mkdir(parents=True)
        source.write_bytes(b"first-party source\r\n")
        subprocess.run(["git", "-C", str(self.repo), "-c", "core.autocrlf=false",
                        "add", "."], check=True, stdout=subprocess.PIPE)
        subprocess.run(["git", "-C", str(self.repo), "-c", "user.name=Fixture",
                        "-c", "user.email=fixture@example.invalid", "commit", "-m", "fixture"],
                       check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.commit = deps.git(self.repo, "rev-parse", "HEAD").decode().strip()
        self.lock = deps.make_lock(self.repo, self.commit)
        self.lockfile = self.root / "LOCK.JSON"
        self.lockfile.write_text(json.dumps(self.lock))

    def tearDown(self):
        self.temp.cleanup()

    def materialize(self):
        out = self.root / "inputs"
        deps.main(["materialize", "--repo", str(self.repo), "--lock", str(self.lockfile),
                   "--out", str(out), "--allow-provisional"])
        return out

    def test_git_bytes_preserved_and_checkout_edits_ignored(self):
        (self.repo / "BIN/MASM.EXE").write_bytes(b"local edit")
        actual = deps.dependency_payload(self.repo, self.lock)
        self.assertEqual(actual, self.original)
        self.assertEqual(deps.verified_directory(self.materialize(), self.lock), self.original)

    def test_corrupt_lock_refused_before_output(self):
        self.lock["files"]["BIN/MASM.EXE"]["sha256"] = "0" * 64
        self.lockfile.write_text(json.dumps(self.lock))
        with self.assertRaisesRegex(deps.Refusal, "SHA256"):
            self.materialize()
        self.assertFalse((self.root / "inputs").exists())

    def test_tampered_and_extra_cache_files_refused(self):
        out = self.materialize()
        (out / "BIN/MASM.EXE").write_bytes(b"tampered")
        with self.assertRaisesRegex(deps.Refusal, "SHA256"):
            deps.verified_directory(out, self.lock)
        (out / "BIN/MASM.EXE").write_bytes(self.original["BIN/MASM.EXE"])
        (out / "EXTRA.TXT").write_bytes(b"extra")
        with self.assertRaisesRegex(deps.Refusal, "extra"):
            deps.verified_directory(out, self.lock)

    def test_existing_output_preserved(self):
        out = self.materialize()
        with self.assertRaisesRegex(deps.Refusal, "exists"):
            self.materialize()
        self.assertEqual((out / "BIN/MASM.EXE").read_bytes(), self.original["BIN/MASM.EXE"])

    def test_provisional_requires_explicit_opt_in(self):
        with self.assertRaisesRegex(deps.Refusal, "allow-provisional"):
            deps.load_lock(self.lockfile)
        self.assertEqual(deps.load_lock(self.lockfile, True)["commit"], self.commit)

    def test_settled_requires_preserved_ref_at_exact_commit(self):
        with self.assertRaises(subprocess.CalledProcessError):
            deps.make_lock(self.repo, self.commit, "settled-dev")
        subprocess.run(["git", "-C", str(self.repo), "update-ref",
                        "refs/remotes/origin/DEV", self.commit], check=True)
        self.assertEqual(deps.make_lock(self.repo, self.commit, "settled-dev")["status"],
                         "settled-dev")

    def test_floating_refs_and_traversal_refused(self):
        for ref in ("DEV", "main", "HEAD", self.commit[:8]):
            with self.assertRaises(deps.Refusal):
                deps.exact_commit(ref)
        for path in ("../BIN/x", "/BIN/x", "BIN/../x", "BIN//x", "C:/BIN/x", "BIN\\x"):
            with self.assertRaises(deps.Refusal):
                deps.check_paths([path], False)

    def test_case_collisions_preserve_distinct_paths(self):
        names = ["examples/TSHELL/IDLE/TESTS/A.C", "examples/TSHELL/IDLE/tests/B.C"]
        with self.assertRaisesRegex(deps.Refusal, "Case-sensitive"):
            deps.check_paths(names, False)
        deps.check_paths(names, True)

    def test_outputs_inside_source_refused(self):
        with self.assertRaisesRegex(deps.Refusal, "outside"):
            deps.fresh_out(self.repo / "new", (self.repo,))

    def test_relative_parent_components_are_canonicalized(self):
        self.assertEqual(deps.fresh_out(self.repo / "../new", (self.repo,)),
                         self.root / "new")

    def test_verify_never_fetches(self):
        out = self.materialize()
        with mock.patch.object(deps.subprocess, "run", side_effect=AssertionError("network/process")):
            deps.main(["verify", "--deps", str(out), "--lock", str(self.lockfile),
                       "--allow-provisional"])

    def test_build_view_preserves_pinned_source_and_inputs(self):
        inputs = self.materialize()
        (self.repo / "src/tandysw/V1.ASM").write_bytes(b"uncommitted")
        out = self.root / "display"
        deps.main(["view", "--deps", str(inputs), "--lock", str(self.lockfile),
                   "--allow-provisional", "--source-repo", str(self.repo),
                   "--source-commit", self.commit, "--profile", "display", "--out", str(out)])
        self.assertEqual((out / "src/tandysw/V1.ASM").read_bytes(), b"first-party source\r\n")
        for name, content in self.original.items():
            self.assertEqual((out / name).read_bytes(), content)

    def test_build_view_rejects_bad_inputs_before_creating_output(self):
        inputs = self.materialize()
        (inputs / "LIB/LIBW.LIB").write_bytes(b"wrong")
        out = self.root / "display"
        with self.assertRaisesRegex(deps.Refusal, "SHA256"):
            deps.main(["view", "--deps", str(inputs), "--lock", str(self.lockfile),
                       "--allow-provisional", "--source-repo", str(self.repo),
                       "--source-commit", self.commit, "--profile", "display", "--out", str(out)])
        self.assertFalse(out.exists())


if __name__ == "__main__":
    unittest.main()
