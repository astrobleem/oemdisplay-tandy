#!/usr/bin/env python3
"""Deterministic experimental driver packets; no native build or network.
MIT, Copyright (c) 2026 Windows XT contributors.

Private binary/build inputs are read only. Only explicitly named pinned
drivers, the guard and first-party launcher enter runtime ZIPs. Source is
an allowlisted adaptation companion, never a toolchain/OS/ROM archive.
"""
import argparse
import hashlib
import json
import os
import re
import subprocess
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
PINS = json.loads((HERE / "PINS.JSN").read_bytes())
SOURCE_DIRS = ("src/pc1512", "src/pcp", "docs/pc1512", "docs/pcp", "docs/pcjr")
SOURCE_FILES = (
    "src/pcjr/BUILDJR.PY", "src/pcjr/JRPATCH.PY", "src/pcjr/JRGUARD.ASM",
    "src/pcjr/JRPROBE.ASM", "src/pcjr/JRCHECK.PY", "src/pcjr/JRRUN.PY",
    "src/pcjr/BUILDCOM.PY", "src/pcjr/PCJSIMG.PY",
    "docs/PC1512.MD", "docs/PCP.MD", "docs/PCJR.MD", "src/tandysw/PROVENANCE.md",
    "tools/BUILDDEPS/DEPS.PY", "tools/BUILDDEPS/LOCK.JSON", "tools/BUILDDEPS/README.MD")
SOURCE_SUFFIXES = {".PY", ".ASM", ".MD", ".TXT", ".JSN", ".JSON", ".BAT", ".PNG", ".BMP"}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def js(data):
    return (json.dumps(data, sort_keys=True, indent=1) + "\n").replace("\n", "\r\n").encode("ascii")


def git(repo, *args):
    env = dict(os.environ, GIT_NO_REPLACE_OBJECTS="1", GIT_TERMINAL_PROMPT="0")
    return subprocess.run(["git", "-c", "protocol.allow=never", "-C", str(repo), *args],
                          env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                          check=True).stdout


def read_blob(repo, commit, path):
    if not re.fullmatch(r"[0-9a-f]{40}", commit):
        raise ValueError("source commit must be a complete SHA")
    return git(repo, "show", commit + ":" + path)


def read_file(path, limit=1048576):
    path = Path(path)
    if path.is_symlink() or not path.is_file() or path.stat().st_size > limit:
        raise ValueError("missing/linked/oversized input: " + str(path))
    return path.read_bytes()


def pinned_file(root, pin):
    data = read_file(Path(root) / pin["file"])
    if len(data) != pin["bytes"] or sha(data) != pin["sha256"]:
        raise ValueError("qualified binary identity mismatch: " + pin["file"])
    return data


def safe_archive_name(name):
    if not re.fullmatch(r"[A-Za-z0-9_.\-/]+", name) or any(
            part in {"", ".", ".."} for part in name.split("/")):
        raise ValueError("unsafe archive path: " + name)


def zip_bytes(path, members):
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_STORED) as archive:
        for name, data in sorted(members.items()):
            safe_archive_name(name)
            info = zipfile.ZipInfo(name, (1980, 1, 1, 0, 0, 0))
            info.create_system, info.external_attr = 0, 0x20
            archive.writestr(info, data)


def zip_members(path):
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        if names != sorted(set(names)) or archive.comment:
            raise ValueError("archive duplicate/order/comment")
        for info in archive.infolist():
            # zipfile may normalize native separators or truncate a NUL name.
            safe_archive_name(info.orig_filename)
            safe_archive_name(info.filename)
            if info.date_time != (1980, 1, 1, 0, 0, 0) or info.create_system != 0 or \
                    info.external_attr != 0x20 or info.compress_type != zipfile.ZIP_STORED or \
                    info.extra or info.comment or info.flag_bits:
                raise ValueError("archive metadata mismatch")
        return {n: archive.read(n) for n in names}


def notice(rights):
    basis = rights.get("record", "No release-owner record provided.")
    return ("EXPERIMENTAL DISPLAY DRIVER - NOT A WINDOWS/DOS DISTRIBUTION\r\n\r\n"
            "This driver reuses Microsoft Windows DDK renderer code/resources.\r\n"
            "Microsoft Corporation copyright notices, including 1983-1987\r\n"
            "notices in reused renderer sources, remain applicable. The new\r\n"
            "packaging/launcher MIT license does not relicense this material.\r\n"
            "Release-owner record (not a blanket third-party license grant):\r\n" + basis + "\r\n\r\n"
            "Windows, DOS, system fonts/grabbers, ROMs, compiler, libraries and\r\n"
            "original DDK inputs are excluded. Use authorized owned inputs.\r\n"
            "Physical hardware and fresh Setup integration remain unqualified.\r\n").encode("ascii")


def source_members(runtime_repo, release_repo, release_commit):
    runtime_commit = PINS["runtime_source_commit"]
    names = set(SOURCE_FILES)
    for folder in SOURCE_DIRS:
        names.update(git(runtime_repo, "ls-tree", "-r", "--name-only", runtime_commit,
                         "--", folder).decode("utf-8").splitlines())
    members = {}
    for name in sorted(names):
        if Path(name).suffix.upper() not in SOURCE_SUFFIXES or any(
                part.lower() in {"txt40", "tga2", "bin", "ddk", "include", "lib"} for part in name.split("/")):
            raise ValueError("private/unapproved source member: " + name)
        members[name] = read_blob(runtime_repo, runtime_commit, name)
    for name in git(release_repo, "ls-tree", "-r", "--name-only", release_commit,
                    "--", "experiments/DISPLAY3").decode().splitlines():
        if Path(name).suffix.upper() in {".PY", ".ASM", ".C", ".PS1", ".TXT", ".JSN", ".MD"}:
            members[name] = read_blob(release_repo, release_commit, name)
    members["SOURCE.JSN"] = js(dict(runtime_source_commit=runtime_commit,
        release_source_commit=release_commit, files={n: sha(d) for n, d in sorted(members.items())},
        scope="Adaptation/build/test source only. Generic renderer/DDK inputs are separate authorized dependencies."))
    members["README.TXT"] = (
        "EXPERIMENTAL DISPLAY ADAPTATION SOURCE\r\n\r\n"
        "Runtime code/evidence pin: " + runtime_commit + "\r\n"
        "Packaging/launcher pin: " + release_commit + "\r\n\r\n"
        "This companion preserves the three adaptations, tests and evidence.\r\n"
        "It is not a complete generic renderer/DDK/compiler bundle. Clone the\r\n"
        "public repository at the runtime pin, then follow BUILDDEPS/README.MD\r\n"
        "with authorized original inputs. Reproduce only the documented exact\r\n"
        "driver hashes; a successful different build is not acceptance.\r\n"
        "Use BUILDCOM --src src/pcjr/JRGUARD.ASM explicitly for the guard.\r\n"
        "No TXT40 or TGA-II implementation is included. Negative-test probes\r\n"
        "and their source are not end-user startup programs.\r\n"
        "Existing notices remain applicable; LICENSE.TXT covers only the new\r\n"
        "DISPLAY3 packaging/launcher code. No Windows/DOS/ROM/toolchain input\r\n"
        "bytes or generic Microsoft DDK source are in this archive.\r\n").encode("ascii")
    return members


def build(binary_dir, runtime_repo, release_repo, release_commit, native, rights, out):
    out = Path(out)
    if out.exists():
        raise ValueError("output must be fresh")
    payloads = {key: pinned_file(binary_dir, pin) for key, pin in PINS["drivers"].items()}
    guard = pinned_file(binary_dir, PINS["drivers"]["PCJR"]["guard"])
    launcher = pinned_file(binary_dir, PINS["drivers"]["PCJR"]["launcher"])
    if sha(launcher) != native.get("launcher_sha256") or native.get("launcher_source_sha256") != \
            sha(read_blob(release_repo, release_commit, "experiments/DISPLAY3/JRWIN.ASM")):
        raise ValueError("launcher binary/source qualification mismatch")
    out.mkdir(parents=True)
    common_notice = notice(rights)
    for key, pin in PINS["drivers"].items():
        guide = read_blob(release_repo, release_commit, "experiments/DISPLAY3/" + key + ".TXT")
        metadata = dict(pin, runtime_source_commit=PINS["runtime_source_commit"],
                        release_source_commit=release_commit, physical_hardware_qualified=False)
        members = {pin["file"]: payloads[key], "README.TXT": guide,
                   "LICENSE.TXT": read_blob(release_repo, release_commit, "experiments/DISPLAY3/LICENSE.TXT"),
                   "NOTICE.TXT": common_notice, "PINS.JSN": js(metadata)}
        if key == "PCJR":
            members.update({"JRGUARD.COM": guard, "JRWIN.COM": launcher})
            metadata["launcher_sha256"] = sha(launcher)
            members["PINS.JSN"] = js(metadata)
        members["SHA256.SUM"] = "".join(sha(d) + "  " + n + "\r\n"
                                         for n, d in sorted(members.items())).encode("ascii")
        zip_bytes(out / pin["archive"], members)
    zip_bytes(out / "DISP3SRC.ZIP", source_members(runtime_repo, release_repo, release_commit))
    qualified = dict(runtime_source_commit=PINS["runtime_source_commit"],
        release_source_commit=release_commit, release_tag=PINS["release_tag"], native=native,
        rights=rights, physical_hardware_qualified=False,
        publication_allowed=bool(native.get("verdict") == "PASS" and native.get("real_windows_cycles") == 2
                                 and rights.get("publication_owner_authorized") is True
                                 and rights.get("component_notices_preserved") is True),
        scope="Separate experimental drivers; Tandy rc.6 and TXT40 unchanged. No new full GDI/hardware qualification.")
    (out / "QUALIFY.JSON").write_bytes(js(qualified))
    (out / "SHA256SUMS").write_bytes("".join(sha(p.read_bytes()) + "  " + p.name + "\n"
                                            for p in sorted(out.iterdir())).encode("ascii"))
    verify(out)
    return qualified


def verify(out, publication=False):
    out = Path(out)
    expected = {p["archive"] for p in PINS["drivers"].values()} | {"DISP3SRC.ZIP", "QUALIFY.JSON", "SHA256SUMS"}
    if {p.name for p in out.iterdir()} != expected:
        raise ValueError("unexpected release files")
    sums = "".join(sha(read_file(out / n, 16777216)) + "  " + n + "\n"
                   for n in sorted(expected - {"SHA256SUMS"})).encode()
    if read_file(out / "SHA256SUMS") != sums:
        raise ValueError("release checksums mismatch")
    qualification = json.loads(read_file(out / "QUALIFY.JSON"))
    runtime_packets = {}
    for key, pin in PINS["drivers"].items():
        members = zip_members(out / pin["archive"])
        runtime_packets[key] = members
        wanted = {pin["file"], "README.TXT", "LICENSE.TXT", "NOTICE.TXT", "PINS.JSN", "SHA256.SUM"}
        if key == "PCJR":
            wanted |= {"JRGUARD.COM", "JRWIN.COM"}
        if set(members) != wanted or len(members[pin["file"]]) != pin["bytes"] or sha(members[pin["file"]]) != pin["sha256"]:
            raise ValueError("runtime allowlist/pin mismatch: " + key)
        inner = "".join(sha(d) + "  " + n + "\r\n" for n, d in sorted(members.items()) if n != "SHA256.SUM").encode()
        if members["SHA256.SUM"] != inner:
            raise ValueError("runtime checksums mismatch: " + key)
        metadata = dict(pin, runtime_source_commit=PINS["runtime_source_commit"],
            release_source_commit=qualification["release_source_commit"], physical_hardware_qualified=False)
        if key == "PCJR":
            metadata["launcher_sha256"] = pin["launcher"]["sha256"]
        if json.loads(members["PINS.JSN"]) != metadata:
            raise ValueError("runtime metadata identity mismatch: " + key)
        if key == "PCJR":
            g, launcher = pin["guard"], pin["launcher"]
            if sha(members["JRGUARD.COM"]) != g["sha256"] or len(members["JRGUARD.COM"]) != g["bytes"] or \
                    sha(members["JRWIN.COM"]) != launcher["sha256"] or len(members["JRWIN.COM"]) != launcher["bytes"] or \
                    launcher["sha256"] != qualification["native"].get("launcher_sha256"):
                raise ValueError("PCjr guard/launcher identity mismatch")
    source = zip_members(out / "DISP3SRC.ZIP")
    if any(Path(n).suffix.upper() in {".DRV", ".COM", ".EXE", ".DLL", ".FON", ".FNT", ".CUR", ".IMG", ".ROM"}
           or any(p.lower() in {"txt40", "tga2", "ddk", "include", "lib", "bin"} for p in n.split("/")) for n in source):
        raise ValueError("private/unapproved source payload")
    manifest = json.loads(source["SOURCE.JSN"])
    if set(manifest["files"]) != set(source) - {"SOURCE.JSN", "README.TXT"} or any(
            sha(source[n]) != digest for n, digest in manifest["files"].items()):
        raise ValueError("source manifest mismatch")
    if any(manifest.get(k) != qualification.get(k) for k in ("runtime_source_commit", "release_source_commit")):
        raise ValueError("source qualification identity mismatch")
    if qualification.get("runtime_source_commit") != PINS["runtime_source_commit"] or \
            qualification.get("release_tag") != PINS["release_tag"] or \
            not re.fullmatch(r"[0-9a-f]{40}", qualification.get("release_source_commit", "")):
        raise ValueError("qualification source/tag identity mismatch")
    native, rights = qualification.get("native", {}), qualification.get("rights", {})
    own = "experiments/DISPLAY3/"
    if json.loads(source[own + "NATIVE.JSN"]) != native or json.loads(source[own + "RIGHTS.JSN"]) != rights or \
            sha(source[own + "JRWIN.ASM"]) != native.get("launcher_source_sha256"):
        raise ValueError("committed qualification/source binding mismatch")
    for key, members in runtime_packets.items():
        if members["README.TXT"] != source[own + key + ".TXT"] or \
                members["LICENSE.TXT"] != source[own + "LICENSE.TXT"] or members["NOTICE.TXT"] != notice(rights):
            raise ValueError("runtime guide/license/notice binding mismatch: " + key)
    ready = bool(native.get("verdict") == "PASS" and native.get("real_windows_cycles") == 2
                 and rights.get("publication_owner_authorized") is True
                 and rights.get("component_notices_preserved") is True)
    if qualification.get("publication_allowed") != ready or qualification.get("physical_hardware_qualified") is not False:
        raise ValueError("qualification scope/permission flag mismatch")
    if publication and not ready:
        raise ValueError("native qualification, owner authorization or notices are unresolved")
    return qualification


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="command", required=True)
    b = sub.add_parser("build")
    for name in ("binary-dir", "runtime-repo", "release-repo", "release-commit", "native", "rights", "out"):
        b.add_argument("--" + name, required=True)
    v = sub.add_parser("verify")
    v.add_argument("--out", required=True)
    v.add_argument("--publication", action="store_true")
    a = ap.parse_args()
    if a.command == "build":
        result = build(a.binary_dir, a.runtime_repo, a.release_repo, a.release_commit,
                       json.loads(read_file(a.native)), json.loads(read_file(a.rights)), a.out)
    else:
        result = verify(a.out, a.publication)
    print(json.dumps(result, indent=1))


if __name__ == "__main__":
    main()
