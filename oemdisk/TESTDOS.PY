#!/usr/bin/env python3
"""Run DOS helper control-flow checks in disposable guests; no Windows media."""
import argparse
import importlib.machinery
import importlib.util
import json
from pathlib import Path
import shutil
import struct
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def load(name, path):
    loader = importlib.machinery.SourceFileLoader(name, str(path))
    spec = importlib.util.spec_from_loader(name, loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


host = load("disk_host_tests", ROOT / "oemdisk/TESTDISK.PY")
reserve = load("reserve_tests", ROOT / "src/tandysw/RESERVE.PY")
s = host.s


def sentinel(filename, exe=False):
    """8086 executable: create marker and write raw PSP command tail into it."""
    code = bytearray(b"\xba\x00\x00\x31\xc9\xb4\x3c\xcd\x21")
    code += b"\x72\x13\x89\xc3\xba\x81\x00\x31\xc9\x8a\x0e\x80\x00"
    code += b"\xb4\x40\xcd\x21\xb4\x3e\xcd\x21\xb8\x00\x4c\xcd\x21"
    struct.pack_into("<H", code, 1, 0x100 + len(code))
    code.extend(filename.encode("ascii") + b"\x00")
    if not exe:
        return bytes(code)
    total = 32 + len(code)
    # MZ executable code starts at PSP:0100. DS still refers to the PSP.
    header = struct.pack("<14H", 0x5a4d, total % 512, (total + 511) // 512,
                         0, 2, 0x100, 0xffff, 0, 0x1000, 0, 0, 0, 0x1c, 0)
    return header + b"\x00" * 4 + bytes(code)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dosbox", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    out = args.out.resolve()
    if out.exists():
        parser.error("--out must be a new directory")
    out.mkdir(parents=True)
    archive_path = out / "T88TOOLS.ZIP"
    host.builder.build_toolkit(ROOT, archive_path)
    with zipfile.ZipFile(archive_path) as archive:
        archive.extractall(out / "clean")
    owned = out / "synthetic"
    owned.mkdir()
    for name in s.inf_support_files((out / "clean/DISK1/OEMSETUP.INF").read_bytes()):
        (owned / name).write_bytes(host.font_fixture() if name.endswith(".FON")
                                  else b"Synthetic test fixture; not Windows content")
    # Isolated synthetic test inputs get explicit test-only pins. No real
    # Windows media is needed, and production source hashes remain untouched.
    s.SUPPORT_HASHES = {p.name: s.sha(p.read_bytes()) for p in owned.iterdir()}
    results = []
    if set(s.SUPPORT_HASHES) & {"TNDYLOGO.RLE", "CGALOGO.RLE"}:
        raise AssertionError("Synthetic Windows support fixtures must exclude splash artwork")
    s.verify_splash({s.SPLASH_NAME: (out / "clean/DISK1" / s.SPLASH_NAME).read_bytes()})

    def check(description, condition):
        if not condition:
            raise AssertionError(description)
        results.append(description)

    check("OEM disk contains exactly five selectable driver binaries",
          {p.name for p in (out / "clean/DISK1").glob("*.DRV")} == s.DRIVER_NAMES)
    check("OEM disk requests exactly eight Microsoft support files", len(s.SUPPORT_HASHES) == 8)

    def case(name, commands, machine="tandy", installed=False, missing=(),
             existing=False, windows_dir=r"C:\WINDOWS"):
        directory = out / name
        directory.mkdir()
        cdrive = directory / "cdrive"
        cdrive.mkdir()
        ddrive = directory / "ddrive"
        ddrive.mkdir()
        winroot = cdrive if windows_dir.startswith("C:") else ddrive
        win = winroot.joinpath(*windows_dir[3:].split("\\"))
        win.mkdir(parents=True)
        (win / "WIN.COM").write_bytes(sentinel("WIN.RAN"))
        (win / "SETUP.EXE").write_bytes(sentinel("SETUP.RAN", exe=True))
        disk = directory / "disk"
        s.stage(out / "clean/DISK1", owned, disk, windows_dir)
        helper = cdrive / "TANDY88"
        if installed or existing:
            helper.mkdir()
        if installed:
            for filename in ("RESERVE.COM", "TANDY88.BAT"):
                shutil.copyfile(disk / filename, helper / filename)
        if existing:
            (helper / "KEEP.TXT").write_bytes(b"preserve\r\n")
        for filename in missing:
            targets = {"local": disk / "LOCAL.TXT", "source": disk / "RESERVE.COM",
                       "helper": helper / "RESERVE.COM", "win": win / "WIN.COM",
                       "setup": win / "SETUP.EXE"}
            targets[filename].unlink()
        text = ("@ECHO OFF\n" + 'MOUNT A "' + str(disk) + '"\n' +
                'MOUNT D "' + str(ddrive) + '"\nA:\n' + commands + "\nEXIT\n")
        reserve.dos_text(directory / "TEST.BAT", text)
        reserve.run_dos(args.dosbox.resolve(), cdrive, directory, "TEST.BAT",
                        machine=machine, cpu="8086_prefetch")
        return directory, win, helper

    directory, win, helper = case("install_only", "COMMAND /C INSTALL > R:\\INSTALL.TXT")
    check("installer copies the accepted reservation helper", s.sha((helper / "RESERVE.COM").read_bytes()) == s.RESERVE_SHA)
    check("installer copies the guarded launcher", (helper / "TANDY88.BAT").is_file())
    check("DOS installer copies only the two shared helpers",
          {p.name for p in helper.iterdir()} == {"RESERVE.COM", "TANDY88.BAT"})
    check("DOS installer leaves driver and font selection to Windows Setup",
          not list(win.rglob("*.DRV")) and not list(win.rglob("*.FON")))
    check("installer never auto-starts Windows or Setup", not (win / "WIN.RAN").exists() and not (win / "SETUP.RAN").exists())

    commands = ("COMMAND /C INSTALL > R:\\INSTALL.TXT\n"
                "COMMAND /C C:\\TANDY88\\TANDY88 setup > R:\\SETUP.TXT\n"
                "IF EXIST C:\\WINDOWS\\SETUP.RAN ECHO YES>R:\\LOWER.OK\n"
                "COMMAND /C C:\\TANDY88\\TANDY88 SETUP > R:\\SETUP2.TXT\n"
                "COMMAND /C C:\\TANDY88\\TANDY88 > R:\\WIN1.TXT\n"
                "COMMAND /C C:\\TANDY88\\TANDY88 > R:\\WIN2.TXT\n"
                "A:\nCOMMAND /C INSTALL > R:\\REPEAT.TXT")
    directory, win, helper = case("normal", commands)
    check("lowercase setup reaches Setup only after reservation", (directory / "LOWER.OK").is_file())
    check("uppercase SETUP reaches Setup", (win / "SETUP.RAN").exists())
    check("safe Windows launch passes /R to WIN.COM", (win / "WIN.RAN").read_text().strip() == "/R")
    check("repeated launch validates existing reservation", "already installed" in (directory / "WIN2.TXT").read_text())
    check("repeat install preserves existing helper directory", "already exists" in (directory / "REPEAT.TXT").read_text())

    directory, win, helper = case("cga_install", "COMMAND /C INSTALL > R:\\INSTALL.TXT", machine="cga")
    check("unsupported machine blocks helper installation", not helper.exists())
    check("failed install starts no Windows or Setup", not (win / "WIN.RAN").exists() and not (win / "SETUP.RAN").exists())

    launch_both = ("COMMAND /C C:\\TANDY88\\TANDY88 > R:\\WIN.TXT\n"
                   "COMMAND /C C:\\TANDY88\\TANDY88 setup > R:\\SETUP.TXT")
    directory, win, helper = case("cga_launch", launch_both, machine="cga", installed=True)
    check("reservation failure blocks WIN and Setup", not (win / "WIN.RAN").exists() and not (win / "SETUP.RAN").exists())
    check("failed reservation is explained", "Video reservation failed" in (directory / "WIN.TXT").read_text())

    directory, win, helper = case("missing_helper", launch_both, installed=True, missing=("helper",))
    check("missing RESERVE blocks WIN and Setup", not (win / "WIN.RAN").exists() and not (win / "SETUP.RAN").exists())
    check("missing helper is explained", "RESERVE.COM missing" in (directory / "WIN.TXT").read_text())

    for name, missing in (("missing_local", "local"), ("missing_source", "source"), ("missing_win", "win")):
        directory, win, helper = case(name, "COMMAND /C INSTALL > R:\\INSTALL.TXT", missing=(missing,))
        check(name + " blocks installation without a partial target", not helper.exists())

    directory, win, helper = case("existing_target", "COMMAND /C INSTALL > R:\\INSTALL.TXT", existing=True)
    check("existing helper directory contents preserved", (helper / "KEEP.TXT").read_bytes() == b"preserve\r\n" and not (helper / "RESERVE.COM").exists())

    directory, win, helper = case("missing_setup", "COMMAND /C C:\\TANDY88\\TANDY88 setup > R:\\SETUP.TXT", installed=True, missing=("setup",))
    check("missing Setup executable is refused", "Nothing started" in (directory / "SETUP.TXT").read_text() and not (win / "SETUP.RAN").exists())

    directory, win, helper = case("alternate_drive", "COMMAND /C INSTALL > R:\\INSTALL.TXT\n" + launch_both, windows_dir=r"D:\WIN30")
    check("alternate Windows drive and directory launches /R", (win / "WIN.RAN").read_text().strip() == "/R")
    check("alternate Windows drive and directory launches Setup", (win / "SETUP.RAN").is_file())
    check("alternate Windows path keeps helper on C outside Windows", (helper / "RESERVE.COM").is_file())

    summary = {"result": "PASS", "checks": results, "check_count": len(results),
               "guest": "DOSBox-X disposable DOS, 8086_prefetch, normal 640K layout",
               "windows": "NOT RUN; synthetic WIN.COM and SETUP.EXE sentinels only"}
    (out / "RESULT.JSON").write_bytes(s.dos_text(json.dumps(summary, indent=2) + "\n"))
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
