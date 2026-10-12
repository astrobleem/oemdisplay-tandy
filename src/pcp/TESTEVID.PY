#!/usr/bin/env python3
"""Host regressions for retry exhaustion and capture provenance; no guest."""
import contextlib
import copy
import importlib.machinery
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
E = importlib.machinery.SourceFileLoader("test_evid", str(HERE / "PCPEVID.PY")).load_module()
W = importlib.machinery.SourceFileLoader("test_win", str(HERE / "PCPWIN.PY")).load_module()
S = importlib.machinery.SourceFileLoader("test_dec", str(HERE / "SHOTDEC.PY")).load_module()


class RetryTests(unittest.TestCase):
    def exercise(self, width, reused, outcomes):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            run = W.Run(root, None, None, width=width)
            hx, hy = W.PAL_X0, W.PAL_Y[0]
            ref = bytes(width * 200)
            glyph = [(0, 0, 15), (1, 0, 15), (0, 1, 15)]
            accepted = bytearray(ref)
            for dx, dy, value in glyph:
                accepted[(hy + dy) * width + hx + dx] = value
            alias = run.b.out / "arrow_00.png"
            stale = run.b.out / "arrow_00_t99.png"
            if reused:
                S.save(accepted, str(alias), width)
                S.save(accepted, str(stale), width)
            shots = []
            def capture(name, **kw):
                shots.append(name)
                S.save(accepted if outcomes[len(shots) - 1] else ref,
                       str(run.b.out / (name + ".png")), width)
            with patch.object(run, "rehome"), patch.object(run, "shot", side_effect=capture), \
                    patch.object(run, "log"), patch.object(W.time, "sleep"):
                row = run.palette_case("arrow_00", hx, hy, ref, glyph)
            self.assertFalse(stale.exists())
            self.assertEqual(len(shots), len(set(shots)))
            if any(outcomes):
                count = outcomes.index(True) + 1
                self.assertEqual(row["attempts"], count)
                self.assertEqual(row["accepted_from"], f"arrow_00_t{count}")
                self.assertEqual(alias.read_bytes(), (run.b.out / (row["accepted_from"] + ".png")).read_bytes())
            else:
                self.assertIsNone(row["attempts"])
                self.assertIsNone(row["accepted_from"])
                self.assertFalse(alias.exists())
                self.assertEqual(row["attempt_count"], W.LANDING_TRIES)
                self.assertEqual(len(row["misses"]), W.LANDING_TRIES)
                self.assertEqual(shots, [f"arrow_00_t{i}" for i in range(1, W.LANDING_TRIES + 1)])

    def test_exhaustion_fresh_and_reused_directories(self):
        for width in (320, 640):
            for reused in (False, True):
                with self.subTest(width=width, reused=reused):
                    self.exercise(width, reused, [False] * W.LANDING_TRIES)

    def test_only_successful_current_attempt_becomes_alias(self):
        for width in (320, 640):
            for outcomes in ([True], [False, True]):
                with self.subTest(width=width, outcomes=outcomes):
                    self.exercise(width, True, outcomes)

    def test_session_reset_invalidates_old_landing_and_all_aliases(self):
        with tempfile.TemporaryDirectory() as temp:
            run = W.Run(temp, None, None, width=640)
            (Path(temp) / "LANDING.JSN").write_text('[{"attempts":1}]')
            for c in range(16):
                (run.b.out / f"arrow_{c:02d}.png").write_bytes(b"old accepted frame")
            run.reset_palette()
            self.assertEqual(json.loads((Path(temp) / "LANDING.JSN").read_text()), [])
            self.assertEqual(list(run.b.out.glob("arrow_*.png")), [])

    def test_palette_run_stops_on_exhaustion_and_records_failure(self):
        with tempfile.TemporaryDirectory() as temp:
            run = W.Run(temp, None, None, width=640)
            ref = bytes(640 * 200)
            def capture(name, **kw):
                S.save(ref, str(run.b.out / (name + ".png")), 640)
            with patch.object(run, "wall_glyph", return_value=[(0, 0, 15)]), \
                    patch.object(run, "frame", return_value=ref), patch.object(run, "landed", return_value=False), \
                    patch.object(run, "describe_miss", return_value={"classified": "no changed pixels"}), \
                    patch.object(run, "shot", side_effect=capture), patch.object(run, "rehome"), \
                    patch.object(run, "log"), patch.object(W.time, "sleep"):
                with self.assertRaisesRegex(SystemExit, "no accepted palette attempt"):
                    run.palette_arrows()
            rows = json.loads((Path(temp) / "LANDING.JSN").read_text())
            self.assertEqual(len(rows), 1)
            self.assertIsNone(rows[0]["accepted_from"])
            self.assertFalse((run.b.out / "arrow_00.png").exists())

    def test_paint_damage_is_not_classified_as_a_cursor(self):
        with tempfile.TemporaryDirectory() as temp:
            run = W.Run(temp, None, None, width=640)
            ref = bytes(640 * 200)
            damaged = bytearray(ref)
            damaged[186 * 640 + 222] = 15
            S.save(damaged, str(run.b.out / "damage.png"), 640)
            report = run.describe_miss("damage", ref, 222, 186)
            self.assertEqual(report["changed_pixels"], 1)
            self.assertEqual(report["classified"], "changes surround requested hotspot; shape/origin unverified")


class IndexTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.index = {"frames": []}
        for c in range(16):
            name = f"arrow_{c:02d}"
            image = bytearray(320 * 200)
            image[c] = 15
            path = f"C{c:02d}.PNG"
            S.save(image, str(self.root / path), 320)
            self.index["frames"].extend([
                dict(frame=name + "_t1", source=f"raw{c}.png", decoded=True, repo_file=path),
                dict(frame=name, accepted_from=name + "_t1", repo_file=path)])

    def validate(self, index=None):
        return E.validate_index(self.index if index is None else index, self.root, 320)

    def test_valid_unique_captures_and_aliases(self):
        self.assertEqual(len(self.validate()), 32)

    def test_duplicate_identifiers_rejected(self):
        self.index["frames"].append(copy.deepcopy(self.index["frames"][0]))
        with self.assertRaisesRegex(ValueError, "duplicate frame"):
            self.validate()

    def test_duplicate_raw_sources_rejected(self):
        self.index["frames"][2]["source"] = self.index["frames"][0]["source"]
        with self.assertRaisesRegex(ValueError, "duplicate raw"):
            self.validate()

    def test_unsourced_capture_and_missing_entire_palette_case_rejected(self):
        index = copy.deepcopy(self.index)
        del index["frames"][0]["source"]
        with self.assertRaisesRegex(ValueError, "missing or duplicate raw"):
            self.validate(index)
        index = copy.deepcopy(self.index)
        index["frames"] = index["frames"][:-2]
        with self.assertRaisesRegex(ValueError, "all 16 accepted"):
            self.validate(index)

    def test_cross_case_and_missing_accepted_from_rejected(self):
        for origin in ("arrow_01_t1", "arrow_00_t2", None):
            index = copy.deepcopy(self.index)
            index["frames"][1]["accepted_from"] = origin
            with self.subTest(origin=origin), self.assertRaises(ValueError):
                self.validate(index)

    def test_alias_pixels_must_match_accepted_capture(self):
        self.index["frames"][1]["repo_file"] = "C01.PNG"
        with self.assertRaisesRegex(ValueError, "alias differs"):
            self.validate()

    def test_missing_earlier_attempt_rejected(self):
        self.index["frames"][0]["frame"] = "arrow_00_t2"
        self.index["frames"][1]["accepted_from"] = "arrow_00_t2"
        with self.assertRaisesRegex(ValueError, "contiguous"):
            self.validate()

    def test_alias_cannot_claim_an_independent_capture(self):
        self.index["frames"][1]["source"] = "invented.png"
        with self.assertRaisesRegex(ValueError, "alias must not claim"):
            self.validate()

    def test_missing_file_and_wrong_geometry_rejected(self):
        (self.root / "C00.PNG").unlink()
        with self.assertRaises(OSError):
            self.validate()
        Image.new("P", (1, 1)).save(self.root / "C00.PNG")
        with self.assertRaisesRegex(ValueError, "exact IRGB"):
            self.validate()

    def test_raw_copy_with_other_pixels_rejected(self):
        with Image.open(self.root / "C01.PNG") as im:
            rgb = im.convert("RGB").resize((640, 400), Image.Resampling.NEAREST)
        border = Image.new("RGB", (656, 416))
        border.paste(rgb, (8, 8))
        border.resize((1368, 868), Image.Resampling.NEAREST).save(self.root / "RAW.PNG")
        self.index["frames"][0]["raw_copy"] = "RAW.PNG"
        with self.assertRaisesRegex(ValueError, "raw_copy differs"):
            self.validate()


class LandingTests(unittest.TestCase):
    def setUp(self):
        self.hotspots = {f"arrow_{c:02d}": (c, 100) for c in range(16)}
        self.rows = [dict(frame=n, hotspot=list(h), attempts=1, accepted_from=n + "_t1")
                     for n, h in self.hotspots.items()]
        self.frames = {n: bytes([i]) for i, n in enumerate(self.hotspots)}
        self.frames.update({n + "_t1": value for n, value in list(self.frames.items())})

    def report(self):
        return E.landing_report(self.rows, self.frames.__getitem__, self.hotspots,
                                lambda n, x, y: self.frames[n] == self.frames[n.split("_t")[0]])

    def test_valid_current_acceptance(self):
        report = self.report()
        self.assertTrue(report["valid"])
        self.assertEqual(report["first_try"], 16)

    def test_malformed_case_records_fail_without_a_type_error(self):
        for row in (None, {"frame": []}, {"frame": 1}):
            with self.subTest(row=row):
                report = E.landing_report([row], self.frames.__getitem__, self.hotspots,
                                          lambda n, x, y: True)
                self.assertFalse(report["valid"])

    def test_stale_aliases_do_not_validate_exhausted_attempts(self):
        for count in (None, 0, False, 9):
            self.rows[0]["attempts"] = count
            with self.subTest(count=count):
                self.assertFalse(self.report()["valid"])

    def test_missing_duplicate_case_and_wrong_hotspot_rejected(self):
        self.rows.pop()
        self.assertFalse(self.report()["valid"])
        self.rows.append(copy.deepcopy(self.rows[0]))
        self.assertFalse(self.report()["valid"])
        self.rows = self.rows[:-1]
        self.rows[0]["hotspot"] = [999, 999]
        self.assertFalse(self.report()["valid"])

    def test_alias_mismatch_missing_attempt_and_rejected_acceptance(self):
        self.frames["arrow_00_t1"] = b"different pixels"
        self.assertFalse(self.report()["valid"])
        del self.frames["arrow_00_t1"]
        self.assertFalse(self.report()["valid"])
        self.frames["arrow_00_t1"] = self.frames["arrow_00"]
        report = E.landing_report(self.rows, self.frames.__getitem__, self.hotspots,
                                  lambda n, x, y: False)
        self.assertFalse(report["valid"])

    def test_retry_count_cannot_hide_an_earlier_success(self):
        self.rows[0].update(attempts=2, accepted_from="arrow_00_t2")
        self.frames["arrow_00_t2"] = self.frames["arrow_00"]
        self.assertFalse(self.report()["valid"])
        self.frames["arrow_00_t1"] = b"rejected"
        report = self.report()
        self.assertTrue(report["valid"])
        self.assertEqual(report["first_try"], 15)
        self.assertEqual(report["recovered_by_retry"][0]["attempts"], 2)

    def test_historical_attempt_name_is_inferred_and_verified(self):
        for row in self.rows:
            del row["accepted_from"]
        self.assertTrue(self.report()["valid"])
        del self.frames["arrow_00_t1"]
        self.assertFalse(self.report()["valid"])


class CheckerTests(unittest.TestCase):
    def test_recorded_miss_matches_exact_translated_crosshair(self):
        doc = ROOT / "docs" / "pc1512"
        index = json.loads((doc / "P86RAW.JSN").read_bytes())
        files = {r["frame"]: r["repo_file"] for r in index["frames"] if "repo_file" in r}
        def read(name):
            with Image.open(doc / files[name]) as im:
                return im.tobytes()
        W.use_width(640)
        x0, y0, x1, y1 = W.rect(12)
        cx, cy = (x0 + x1) // 2, (y0 + y1) // 2
        before, cross = read("cross_parked"), read("cross_12")
        offsets = [(i % 640 - cx, i // 640 - cy) for i in range(128000)
                   if before[i] != cross[i] and not (i % 640 >= 636 and i // 640 >= 196)]
        expected = bytearray(read("pb_drawn"))
        for dx, dy in offsets:
            expected[(186 + dy) * 640 + 222 + dx] ^= 15
        miss = read("arrow_12_t1")
        self.assertEqual(len(offsets), 46)
        self.assertTrue(all(miss[i] == expected[i] for i in range(128000)
                            if not (i % 640 >= 636 and i // 640 >= 196)))

    def test_recorded_frames_pass_but_exhausted_or_missing_landing_fails(self):
        """The previous 88/88 stale-alias false pass must fail qualification."""
        doc = ROOT / "docs" / "pc1512"
        index = json.loads((doc / "P86RAW.JSN").read_bytes())
        frames = {}
        for row in index["frames"]:
            if "repo_file" in row:
                with Image.open(doc / row["repo_file"]) as im:
                    frames[row["frame"]] = im.tobytes()
        check = importlib.machinery.SourceFileLoader("test_check", str(HERE / "PCPCHK.PY")).load_module()
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "DRIFT.JSN").write_bytes((doc / "P86DRIFT.JSN").read_bytes())
            rows = json.loads((doc / "P86LAND.JSN").read_bytes())
            for variant in ("recorded", "exhausted", "partial", "missing"):
                changed = copy.deepcopy(rows)
                if variant == "exhausted":
                    for row in changed:
                        row["attempts"] = None
                if variant == "partial":
                    changed.pop()
                landing = root / "LANDING.JSN"
                if variant == "missing":
                    landing.unlink()
                else:
                    landing.write_text(json.dumps(changed))
                output = io.StringIO()
                with patch.object(check.Frames, "__getitem__", side_effect=frames.__getitem__), \
                        patch.object(sys, "argv", [str(HERE / "PCPCHK.PY"), "--vm", temp,
                                                   "--width", "640", "--target", "pc1512", "--no-disk"]), \
                        contextlib.redirect_stdout(output):
                    rc = check.main()
                result = json.loads(output.getvalue())
                with self.subTest(variant=variant):
                    self.assertEqual(result["failed"], 0)
                    self.assertEqual(result["total"], 88)
                    self.assertEqual(rc, 0 if variant == "recorded" else 1)
                    self.assertEqual(bool(result["evidence_errors"]), variant != "recorded")


if __name__ == "__main__":
    unittest.main(verbosity=2)
