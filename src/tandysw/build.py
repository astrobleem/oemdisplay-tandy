#!/usr/bin/env python3
"""Rebuild the GUI-tested V1 from this source and the repository's tracked DDK."""
from pathlib import Path
import argparse, hashlib, json, os, re, shutil, subprocess, sys

HERE = Path(__file__).resolve().parent
DRIVER_SHA = "995d0079278a42254d997684fb51bd4285bd19bedc2e32cca3bf5065d3cfc61a"
RESOURCE_SHA = "0b61538aa777b0ceafacb54669ab6a8ff7b63e703f01eeb39c2e789b621b11ee"
SOURCE_EXTS = {".ASM", ".INC", ".BLT", ".PUB", ".MAC", ".DEF", ".LNK", ".RC", ".BAT"}

def normalized(path):
    return path.read_bytes().replace(b"\r\n", b"\n").replace(b"\x1a", b"").decode("latin1")

def write_dos(path, text):
    path.write_bytes(text.replace("\r\n", "\n").replace("\n", "\r\n").encode("latin1"))

def replace_once(path, old, new, count=1):
    text = normalized(path)
    found = text.count(old)
    if found != count:
        raise RuntimeError(f"Unexpected DDK input {path.name}: {old!r} found {found} times, expected {count}")
    write_dos(path, text.replace(old, new))

def prepare(repo, out):
    renderer = out / "renderer"
    resources = out / "resources"
    shutil.copytree(repo / "DDK/286/DISPLAY/4PLANE", renderer)
    for path in renderer.rglob("*"):
        if path.is_file() and path.suffix.upper() in SOURCE_EXTS:
            write_dos(path, normalized(path))
    for name in ("CHARWDTH.ASM", "PIXEL.ASM", "ROBJECT.ASM"):
        replace_once(renderer / name, ".286", ".8086")
    path = renderer / "DISPLAY.INC"
    text, count = re.subn(r"^EXCLUSION.*$", "; EXCLUSION is deliberately undefined for memory-only backend",
                          normalized(path), flags=re.M)
    assert count == 1
    write_dos(path, text)
    path = renderer / "FB.ASM"
    text, count = re.subn(r"\bBitBlt\b", "TBitBlt", normalized(path))
    assert count == 5
    write_dos(path, text)
    replace_once(renderer / "POLYLINE.ASM", "externFP LineSeg_check_stack", "externNP LineSeg_check_stack")
    replace_once(renderer / "RLSTRBLT.ASM", "externFP  rCode_check_stack", "externNP  rCode_check_stack")
    for name in ("RLSTRBLT.ASM", "RLBLDSTR.ASM"):
        replace_once(renderer / name, "\tinclude display.inc\n",
                     "\tinclude display.inc\n\tinclude mflags.inc\n")
    # Retain the harmless duplicate includes present in the frozen V1 build.
    replace_once(renderer / "REALFIX.ASM", "\tinclude rlstrblt.inc\n",
                 "\tinclude rlstrblt.inc\n" + "\tinclude mflags.inc\n" * 5)
    replace_once(renderer / "REALPRO.ASM", "\tinclude\tdisplay.inc\n",
                 "\tinclude\tdisplay.inc\n" + "\tinclude mflags.inc\n" * 5)
    for src, dst in (("V1.ASM", "EGA/TSOFT.ASM"), ("TCURSOR.ASM", "EGA/TCURSOR.ASM"),
                     ("TSOFT.DEF", "EGA/TSOFT.DEF"), ("TSOFT.LNK", "EGA/TSOFT.LNK"),
                     ("BLDCOR.BAT", "BLDCOR.BAT"), ("BLDCUR.BAT", "BLDCUR.BAT")):
        shutil.copyfile(HERE / src, renderer / dst)
    low = repo / "DDK/286/DISPLAY/1PLANE/RC_LOW"
    medium = repo / "DDK/286/DISPLAY/4PLANE/RC_MED"
    shutil.copytree(low, resources)
    for path in resources.rglob("*"):
        if path.is_file() and path.suffix.upper() in SOURCE_EXTS:
            write_dos(path, normalized(path))
    write_dos(resources / "FONTS.ASM", normalized(medium / "FONTS.ASM"))
    write_dos(resources / "COLORTAB.ASM", normalized(medium / "COLORTAB.ASM"))
    replace_once(resources / "COLORTAB.ASM", "RGB 082h 082h,082h", "RGB 082h,082h,082h")
    config = normalized(low / "CONFIG.ASM")
    colors = normalized(medium / "CONFIG.ASM")
    begin = ";\tDefault system color values\n"
    end = ";\tdw\t0\t\t\t;Unused words"
    config = config[:config.index(begin)] + colors[colors.index(begin):colors.index(end)] + config[config.index(end):]
    config = config.replace("\tdw\t2\t\t\t;cxBorder", "\tdw\t1\t\t\t;cxBorder")
    write_dos(resources / "CONFIG.ASM", config)
    shutil.copyfile(HERE / "BLDRES.BAT", resources / "BUILD.BAT")
    shutil.copyfile(HERE / "PACKRES.PY", resources / "PACKRES.PY")
    return renderer, resources

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=HERE.parents[1])
    parser.add_argument("--dosbox", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    repo, dosbox, out = args.repo.resolve(), args.dosbox.resolve(), args.out.resolve()
    for name in ("BIN/MASM.EXE", "BIN/LINK4.EXE", "BIN/LINK.EXE",
                 "DDK/TOOLS/EXE2BIN.EXE", "DDK/286/INC/CMACROS.INC", "LIB"):
        if not (repo / name).exists():
            raise SystemExit("Missing tracked build input: " + str(repo / name))
    if out.exists():
        raise SystemExit("Output directory already exists; choose a fresh --out directory")
    out.mkdir(parents=True)
    renderer, resources = prepare(repo, out)
    cfg = out / "build.conf"
    cfg.write_text("[sdl]\nfullscreen=false\noutput=surface\n[dosbox]\nmachine=tandy\nmemsize=16\n"
                   "working directory option=force\nworking directory default=" + str(out) +
                   "\n[cpu]\ncore=normal\ncputype=386\ncycles=fixed 200000\n[mixer]\nnosound=true\n"
                   "[midi]\nmididevice=none\n[autoexec]\n@echo off\n"
                   'mount C "' + str(repo) + '"\nmount R "' + str(renderer) +
                   '"\nmount D "' + str(resources) + '"\nR:\n')
    env = os.environ.copy()
    env.update(SDL_VIDEODRIVER="dummy", SDL_AUDIODRIVER="dummy", TANDY_REPO=str(repo))
    for label, commands in (("core", ["R:", "BLDCOR.BAT"]),
                            ("cursor-link", ["R:", "BLDCUR.BAT"]),
                            ("resources", ["D:", "BUILD.BAT", "exit"])):
        command = [str(dosbox), "-nopromptfolder", "-conf", str(cfg)]
        for line in commands:
            command.extend(["-c", line])
        with (out / (label + "-host.log")).open("wb") as log:
            subprocess.run(command, stdout=log, stderr=subprocess.STDOUT,
                           env=env, timeout=120, check=True)
    for path in (renderer / "EGA/BUILD0.LOG", renderer / "EGA/CURSOR.LOG", renderer / "EGA/LINK.LOG",
                 resources / "BUILD.LOG"):
        text = path.read_text(errors="replace")
        errors = [int(n) for n in re.findall(r"(\d+)\s+Severe\s+Errors", text)]
        if any(errors) or re.search(r"error L\d+|fatal error", text, re.I):
            raise SystemExit("Build failed; inspect " + str(path))
    subprocess.run([sys.executable, str(resources / "PACKRES.PY"), "build"], env=env, check=True)
    resource_file = resources / "TANDY.RES"
    assert hashlib.sha256(resource_file.read_bytes()).hexdigest() == RESOURCE_SHA, "Resource mismatch"
    binary = out / "TANDYV1.DRV"
    subprocess.run([sys.executable, str(resources / "PACKRES.PY"), "attach", str(resource_file),
                    str(renderer / "EGA/TSOFT.DRV"), str(binary)], env=env, check=True)
    actual = hashlib.sha256(binary.read_bytes()).hexdigest()
    if actual != DRIVER_SHA:
        raise SystemExit("Rebuilt binary differs from tested V1: " + actual)
    report = {"result": "PASS", "driver_bytes": binary.stat().st_size, "driver_sha256": actual,
              "resource_sha256": RESOURCE_SHA, "variant": "GUI-tested V1; 386 real-mode configuration"}
    (out / "RESULT.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report))
    print("Byte-identical tested driver:", binary)

if __name__ == "__main__":
    main()
