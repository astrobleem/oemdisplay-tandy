#!/usr/bin/env python3
"""Verify supplementary evidence; optional --decode checks exact video frames."""
from pathlib import Path
import hashlib, json, subprocess, sys, tempfile
P = Path(__file__).resolve().parent
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
for line in (P / "MANIFEST.SHA").read_text().splitlines():
    expected, name = line.split("  ", 1)
    assert Path(name).name == name and sha(P / name) == expected, name
r = json.loads((P / "RESULT.JSN").read_text())
pins = json.loads((P.parent.parent / "RUNTIME.JSN").read_text())
assert r["complete"] and r["app_checks_pass"]
assert "PASS_COUNT=41\nFAIL_COUNT=0\nCOMPLETE=1\n" in r["log"]
assert sha(P / "APP3204.AVI") == r["video_sha256"]
assert (P / "APP3204.AVI").stat().st_size == r["video_bytes"]
assert all(pins[k]["sha256"] == v for k, v in r["runtime_hashes"].items())
assert len(r["runtime_hashes"]) == 7
assert sha(P.parent.parent / "APPUI01.ZIP") == "7577dc90975dbe28e6bea0805a50b9c27676e53b0edc132d9c5d2b3be3c1c310"
for e in r["selected_frames"]:
    assert sha(P / e["file"]) == e["sha256"]
if "--decode" in sys.argv:
    from PIL import Image
    with tempfile.TemporaryDirectory() as tmp:
        for e in r["selected_frames"]:
            out = Path(tmp) / e["file"]
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(P / "APP3204.AVI"), "-vf", "select=eq(n\\,%d)" % e["frame_index"], "-frames:v", "1", str(out)], check=True)
            assert Image.open(out).convert("RGB").tobytes() == Image.open(P / e["file"]).convert("RGB").tobytes(), e["file"]
    assert Image.open(P / "ABOUTRAW.PNG").convert("RGB").tobytes() == Image.open(P / "TABOUT.PNG").convert("RGB").tobytes()
print("PASS supplementary evidence hashes, unchanged runtime pins and 41 observer checks" + ("; seven video frames decoded and matched" if "--decode" in sys.argv else ""))
