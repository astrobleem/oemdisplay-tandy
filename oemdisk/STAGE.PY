#!/usr/bin/env python3
"""Historical TANDY88 completion utility; the Tandy picture is retired.
Current Windows XT staging is distributions/WINXT/STAGE.PY.

Current installs use the Windows XT distribution; this is archival reproduction.
Python 3.8+, standard library only. This utility never creates an archive.
"""
import argparse
import csv
import hashlib
from pathlib import Path
import re
import shutil
import struct
import sys

DRIVER_SHA = "ac1aadce894058ab6dbdeab2d2a3fd8673a8b4e78d8798198d295f61f32dafee"
RESERVE_SHA = "644290e234cab9a6ac3799fa32959bb493d82d566501a8925720bb5a28c6afa8"
# Each Setup choice has a distinct file; the accepted default remains untouched.
DISPLAY_PROFILES = (
    ("TANDY88", "TANDY88.DRV", "133,96,72"),
    ("TNDY6404", "TNDY6404.DRV", "200,96,48"),
    ("TNDY160", "TNDY160.DRV", "200,96,48"),
    ("TNDY3204", "TNDY3204.DRV", "200,96,48"),
    ("TNDY6402", "TNDY6402.DRV", "200,96,48"),
)
DRIVER_NAMES = frozenset(profile[1] for profile in DISPLAY_PROFILES)
BINARY_HASHES = {
    "TANDY88.DRV": DRIVER_SHA,
    "TNDY6404.DRV": "5ab225f6e93d53f39d092b8db81fd0129a0fe473cf30eef880ddaeaaa0a8d306",
    "TNDY160.DRV": "124a07c38c13922a4cbd58452d39108755f632abe01e4dd17780c32140d2aedd",
    "TNDY3204.DRV": "c90526efb90f4434e8aa567d439e9cdf7f81c096968a362806a992052a81e9e9",
    "TNDY6402.DRV": "b0c95515462ba27ce208963dd94957019995e3e6085d147771ef037b39967652",
    "RESERVE.COM": RESERVE_SHA,
}
SPLASH_NAME = "TNDYLOGO.RLE"
SPLASH_SHA = "e7a9c043ce3b9f9c78f7ff38bc68d211a0da32462e036abb7135f0602194f083"
SPLASH_BYTES = 5930
BINARY_NAMES = frozenset(BINARY_HASHES) | {SPLASH_NAME}
SUPPORT_HASHES = {
    "CGASYS.FON": "baf8fa607806d949dfb6992113ce93494678abdef07783b22222b62e5de28ef4",
    "CGAFIX.FON": "b0c043a65e2b551bce3c77d25921394dfd2533f50633bc129abd240c7aeb5f89",
    "CGAOEM.FON": "1a86d9e42c73ccefcbc82c822abe8dbcd61cf0116454f213c3a95f4d7436cd0d",
    "EGASYS.FON": "8bd307d7886d0f2fdfc1de3da8253e294233d1c757fd9131a66405fca5825b09",
    "EGAFIX.FON": "6df45a74e5756dd0746bcee593be9ac4df4a35458c26bf4570b748def2d394cb",
    "EGAOEM.FON": "05bd6ef11802bbca20473b0e409116fd8919c5bbcbbbc26b7ee2ea1f33ad23be",
    "CGA.GR2": "1fc24254a1b76c2030a0ae60e25a17d6df4730c2a99d293ca22886059d8be067",
    "CGALOGO.LGO": "d9609adff83a63fda7a67e5e8cd7ed3dfb73f42e4d9971697fd43465231da807",
}
PAYLOAD_NAMES = DRIVER_NAMES | frozenset(("RESERVE.COM", "OEMSETUP.INF",
                           "INSTALL.BAT", "TANDY88.BAT", "README.TXT", "FILE_ID.DIZ",
                           SPLASH_NAME))
DEFAULT_WINDOWS = r"C:\WINDOWS"
HELPER_DIR = r"C:\TANDY88"
DOS_NAME = r"[A-Z0-9_!#$%&'()@^`{}~-]{1,8}(?:\.[A-Z0-9_!#$%&'()@^`{}~-]{1,3})?"


class DiskError(Exception):
    """A refused unsafe, incomplete, or unverified input."""


def sha(data):
    return hashlib.sha256(data).hexdigest()


def dos_text(text):
    return text.replace("\r\n", "\n").replace("\n", "\r\n").encode("ascii")


def checked_text(data, name):
    try:
        text = data.decode("ascii")
    except UnicodeDecodeError:
        raise DiskError(name + " must contain ASCII text")
    if b"\n" in data.replace(b"\r\n", b"") or b"\r" in data.replace(b"\r\n", b""):
        raise DiskError(name + " must use CRLF line endings")
    if "\x00" in text or "\x1a" in text:
        raise DiskError(name + " contains a DOS text terminator or NUL")
    return text


def single_file(directory, name):
    if not directory.is_dir():
        raise DiskError("Directory not found: " + str(directory))
    matches = [p for p in directory.iterdir() if p.name.casefold() == name.casefold()]
    if len(matches) != 1 or not matches[0].is_file() or matches[0].is_symlink():
        raise DiskError("Missing, ambiguous, or nonregular file: " + str(directory / name))
    return matches[0]


def verify_binaries(payload):
    for name, expected in BINARY_HASHES.items():
        if name not in payload or sha(payload[name]) != expected:
            actual = sha(payload[name]) if name in payload else "missing"
            raise DiskError("Unverified " + name + ": SHA256=" + actual +
                            "; use the accepted 8088 build, never root TNDY16.DRV")


def splash_rle(data, name=SPLASH_NAME):
    """Validate the exact safe BMP/RLE subset accepted by the stock CGA loader.

    The legacy format uses a one-bit header with RLE4 encoded monochrome runs.
    Keep this parser self-contained so extracted toolkits need only Python.
    """
    def refuse(reason):
        raise DiskError(name + ": " + reason)
    # WIN.CNF (3456) + unchanged CGALOGO.LGO (880) precede the bitmap.
    if not 62 <= len(data) <= 65280 - 4336:
        refuse("invalid RLE size for the stock 64 KiB COM loader")
    signature, declared, reserved1, reserved2, offset = struct.unpack_from("<2sIHHI", data)
    if (signature, reserved1, reserved2, offset) != (b"BM", 0, 0, 62):
        refuse("invalid BMP file header")
    header = struct.unpack_from("<IiiHHIIiiII", data, 14)
    size, width, height, planes, bpp, compression, image_bytes, xppm, yppm, used, important = header
    if (size, width, height, planes, bpp, compression) != (40, 640, 200, 1, 1, 2):
        refuse("expected 640x200 monochrome legacy RLE4 bitmap")
    if (xppm, yppm, used, important) != (0, 0, 2, 0):
        refuse("unexpected bitmap resolution or palette fields")
    if data[54:62] != b"\0\0\0\0\xff\xff\xff\0":
        refuse("expected the two-entry black/white palette")
    if declared != len(data) or image_bytes != len(data) - offset:
        refuse("bitmap file/image size fields do not match the exact stream")
    x = y = runs = 0
    pos = offset
    while pos + 2 <= len(data):
        count, value = data[pos:pos + 2]
        pos += 2
        if count:
            if count > 254 or value not in (0x00, 0x11):
                refuse("unsupported monochrome encoded run")
            if y >= height or x + count > width:
                refuse("encoded run exceeds bitmap row or height")
            x += count
            runs += 1
        elif value == 0:
            if y >= height or x != width:
                refuse("each row must contain exactly 640 pixels before EOL")
            x = 0
            y += 1
        elif value == 1:
            if x or y != height or pos != len(data):
                refuse("EOB must follow exactly 200 complete rows with no trailing data")
            return {"width": width, "height": height, "encoded_runs": runs,
                    "eol_commands": y, "file_bytes": len(data), "image_bytes": image_bytes}
        else:
            refuse("delta and absolute RLE commands are outside the safe encoding subset")
    refuse("missing or truncated end-of-bitmap command")


def verify_splash(payload):
    if SPLASH_NAME not in payload:
        raise DiskError("Missing first-party splash: " + SPLASH_NAME)
    data = payload[SPLASH_NAME]
    splash_rle(data)
    if len(data) != SPLASH_BYTES or sha(data) != SPLASH_SHA:
        raise DiskError("Unverified first-party splash: " + SPLASH_NAME +
                        " bytes=" + str(len(data)) + " SHA256=" + sha(data))


def inf_support_files(data):
    """Check the bounded disk contract; Windows Setup performs the full parse."""
    text = checked_text(data, "OEMSETUP.INF")
    sections = {}
    section = None
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith(";"):
            continue
        if line.startswith("[") and line.endswith("]"):
            section = line[1:-1].casefold()
            if section in sections:
                raise DiskError("Duplicate OEMSETUP.INF section: " + section)
            sections[section] = []
        elif section is None:
            raise DiskError("OEMSETUP.INF data before any section")
        else:
            sections[section].append(line)
    allowed = {"disks", "display", "sysfonts", "fixedfonts", "oemfonts", "fonts", "data"}
    if set(sections) - allowed:
        raise DiskError("Unsupported OEM sections; optional sections cannot install DOS helpers")
    for required in ("disks", "display", "sysfonts", "fixedfonts", "oemfonts"):
        if not sections.get(required):
            raise DiskError("OEMSETUP.INF missing [" + required + "]")
    disks = sections["disks"]
    if len(disks) != 1 or not re.match(r'^a\s*=\s*\.\s*,', disks[0], re.I):
        raise DiskError("OEM disk must use the single root disk identifier a")
    if len(sections["display"]) != len(DISPLAY_PROFILES):
        raise DiskError("Expected exactly five accepted display profiles")
    for display, (profile, driver, resolution) in zip(sections["display"], DISPLAY_PROFILES):
        # Preserve the original default first; reject aliases, duplicates, and
        # reordered choices as well as accidental cross-wiring of driver files.
        if not re.match(r'^' + profile + r'\s*=\s*a:' + re.escape(driver) + r'\s*,',
                        display, re.I):
            raise DiskError("OEM display must reference " + profile + " = a:" + driver +
                            " in accepted profile order")
        try:
            fields = next(csv.reader([display.split("=", 1)[1]], skipinitialspace=True))
        except (csv.Error, StopIteration):
            raise DiskError("Malformed OEM display fields")
        if len(fields) != 9 or not fields[3].strip() or not fields[4].strip() or not fields[8].strip():
            raise DiskError("OEM display requires grabber and logo code/data to build WIN.COM")
        if not fields[1].strip():
            raise DiskError("OEM display requires a visible description")
        # A distinct bitmap name prevents Setup reusing cached stock CGALOGO.RLE.
        if fields[8].strip().upper() != "A:" + SPLASH_NAME:
            raise DiskError("OEM logo bitmap must reference a:" + SPLASH_NAME +
                            "; CGALOGO.RLE can reuse the cached stock splash")
        if [field.strip().upper() for field in fields[3:8]] != [
                "A:CGA.GR2", "A:CGALOGO.LGO", "", "", ""]:
            raise DiskError("OEM display must preserve the accepted grabber and logo loader")
        if fields[2].strip() != resolution:
            raise DiskError("OEM display " + profile + " must use font resolution " + resolution)
    # The Windows 3.0 parser treats no-data comma fields as inherited defaults.
    # Any driver files actually named in the record must be on our allowlist.
    refs = []
    for section, lines in sections.items():
        for line in lines:
            refs.extend((section, disk, filename) for disk, filename in
                        re.findall(r'\b([A-Za-z0-9]):([^,\s"]+)', line))
    support = set()
    for section, disk, filename in refs:
        name = filename.upper()
        if disk.lower() != "a" or not re.fullmatch(DOS_NAME, name):
            raise DiskError("Unsupported disk/file reference: " + disk + ":" + filename)
        if name in DRIVER_NAMES:
            if section != "display":
                raise DiskError("Display drivers may only appear in [display]; Setup selects one")
            continue
        if Path(name).suffix not in {".FON", ".LGO", ".RLE", ".GR2", ".GR3", ".386", ".SYS"}:
            raise DiskError("Unapproved Windows support-file reference: " + name)
        support.add(name)
    for section, suffix in (("sysfonts", "SYS"), ("fixedfonts", "FIX"), ("oemfonts", "OEM")):
        if len(sections[section]) != 2:
            raise DiskError("Expected exactly two font resolutions in [" + section + "]")
        for line, family, resolution in zip(sections[section], ("EGA", "CGA"),
                                            ("133,96,72", "200,96,48")):
            expected = family + suffix + ".FON"
            try:
                fields = [field.strip() for field in next(csv.reader([line], skipinitialspace=True))]
            except (csv.Error, StopIteration):
                raise DiskError("Malformed OEM font fields")
            count = 4 if section == "oemfonts" else 3
            if (len(fields) != count or fields[0].upper() != "A:" + expected or
                    not fields[1] or fields[2] != resolution or
                    (count == 4 and fields[3] != "1")):
                raise DiskError("Expected " + expected + " with resolution " + resolution +
                                " in [" + section + "]")
    if support != set(SUPPORT_HASHES) | {SPLASH_NAME}:
        raise DiskError("OEM INF must name exactly eight accepted Windows support files "
                        "and the first-party " + SPLASH_NAME)
    return sorted(support - {SPLASH_NAME})


def expanded_file(data, name):
    """Decode bounded SZDD mode-A files from Windows 3.0 media, when needed."""
    signature = b"SZDD\x88\xf0\x27\x33"
    if not data.startswith(signature):
        if not data or len(data) > 1024 * 1024:
            raise DiskError(name + ": empty or oversized Windows support file")
        return data
    if len(data) < 14 or data[8] != ord("A"):
        raise DiskError(name + ": unsupported or truncated SZDD header")
    expected = struct.unpack_from("<I", data, 10)[0]
    if not 1 <= expected <= 1024 * 1024:
        raise DiskError(name + ": invalid expanded size (limit 1 MiB)")
    ring = bytearray(b" " * 4096)
    cursor, pos = 4096 - 16, 14
    result = bytearray()
    while len(result) < expected:
        if pos >= len(data):
            raise DiskError(name + ": truncated SZDD flags")
        flags = data[pos]
        pos += 1
        for bit in range(8):
            if len(result) == expected:
                break
            if flags & (1 << bit):
                if pos >= len(data):
                    raise DiskError(name + ": truncated SZDD literal")
                chunk = bytes((data[pos],))
                pos += 1
                result.extend(chunk)
                ring[cursor] = chunk[0]
                cursor = (cursor + 1) & 4095
            else:
                if pos + 2 > len(data):
                    raise DiskError(name + ": truncated SZDD reference")
                offset = data[pos] | ((data[pos + 1] & 0xf0) << 4)
                length = (data[pos + 1] & 0x0f) + 3
                pos += 2
                if len(result) + length > expected:
                    raise DiskError(name + ": SZDD reference exceeds declared size")
                for index in range(length):
                    value = ring[(offset + index) & 4095]
                    result.append(value)
                    ring[cursor] = value
                    cursor = (cursor + 1) & 4095
    if pos != len(data):
        raise DiskError(name + ": unexpected data after SZDD stream")
    return bytes(result)


def font_ne(data, name):
    """Reject renamed/compressed/truncated files; do not claim license or version proof."""
    def word(offset):
        if offset < 0 or offset + 2 > len(data):
            raise DiskError(name + ": truncated NE font")
        return struct.unpack_from("<H", data, offset)[0]
    if len(data) < 64 or data[:2] != b"MZ":
        raise DiskError(name + ": need an expanded Windows 3.0 .FON, not compressed media")
    ne = struct.unpack_from("<I", data, 0x3c)[0]
    if ne + 0x28 > len(data) or data[ne:ne+2] != b"NE":
        raise DiskError(name + ": missing NE font header")
    resource = ne + word(ne + 0x24)
    end = ne + word(ne + 0x26)
    if not ne + 0x28 <= resource < end <= len(data):
        raise DiskError(name + ": invalid NE resource bounds")
    shift = word(resource)
    if shift > 16:
        raise DiskError(name + ": invalid resource alignment")
    pos, found = resource + 2, False
    while pos + 2 <= end:
        kind = word(pos)
        if not kind:
            if not found:
                raise DiskError(name + ": no FONT resource")
            return
        count = word(pos + 2)
        if not count or pos + 8 + count * 12 > end:
            raise DiskError(name + ": invalid resource table")
        pos += 8
        for _ in range(count):
            offset, length = word(pos) << shift, word(pos + 2) << shift
            if not length or offset + length > len(data):
                raise DiskError(name + ": resource outside file")
            if kind == 0x8008:
                found = True
            pos += 12
    raise DiskError(name + ": unterminated resource table")


def manifest(payload):
    return dos_text("".join(sha(payload[n]) + "  " + n + "\n" for n in sorted(payload)))


def clean_payload(directory):
    names = {p.name.upper() for p in directory.iterdir()} if directory.is_dir() else set()
    if names != PAYLOAD_NAMES | {"MANIFEST.SHA"}:
        raise DiskError("Use untouched toolkit DISK1 from T88TOOLS.ZIP; unexpected/missing files")
    payload = {n: single_file(directory, n).read_bytes() for n in PAYLOAD_NAMES}
    expected = single_file(directory, "MANIFEST.SHA").read_bytes()
    if expected != manifest(payload):
        raise DiskError("DISK1 manifest mismatch; package is stale or modified")
    verify_binaries(payload)
    verify_splash(payload)
    inf_support_files(payload["OEMSETUP.INF"])
    for name in PAYLOAD_NAMES - BINARY_NAMES:
        checked_text(payload[name], name)
    return payload


def windows_path(value):
    value = value.upper()
    # Restrict command metacharacters too, even though some are legal DOS names.
    if not re.fullmatch(r'[A-Z]:\\[A-Z0-9_~-]{1,8}(?:\.[A-Z0-9_~-]{1,3})?'
                        r'(?:\\[A-Z0-9_~-]{1,8}(?:\.[A-Z0-9_~-]{1,3})?)*', value):
        raise DiskError("--windows-dir must be an absolute DOS 8.3 directory without spaces")
    if value == HELPER_DIR or value.startswith(HELPER_DIR + "\\"):
        raise DiskError("Windows directory must be outside " + HELPER_DIR)
    return value



def verify_support(payload):
    if set(payload) != set(SUPPORT_HASHES):
        raise DiskError("Expected exactly the eight accepted Windows support files")
    for name, data in payload.items():
        if name.endswith(".FON"):
            font_ne(data, name)
        if sha(data) != SUPPORT_HASHES[name]:
            raise DiskError("Unverified Windows support file: " + name + " SHA256=" + sha(data))


def disk_allocation(payload):
    """Standard 360 KB FAT12: 2 sectors/cluster, 2 FATs, 112 root entries."""
    sector = 512
    total = 720 * sector
    overhead = (1 + 2 * 2 + 7) * sector
    cluster = 1024
    allocated = sum(((len(data) + cluster - 1) // cluster) * cluster for data in payload.values())
    if len(payload) > 112 or allocated > total - overhead:
        raise DiskError("Extracted OEM disk exceeds standard 360 KB FAT12 capacity")
    return {"files": len(payload), "logical_bytes": sum(map(len, payload.values())),
            "allocated_file_bytes": allocated, "filesystem_overhead_bytes": overhead,
            "total_used_bytes": allocated + overhead, "capacity_bytes": total,
            "free_data_bytes": total - overhead - allocated}


def completed_payload(source, support, windows_dir=DEFAULT_WINDOWS):
    """Assemble the source payload plus eight exact Windows support inputs."""
    windows_dir = windows_path(windows_dir)
    if set(source) != PAYLOAD_NAMES:
        raise DiskError("Unexpected or missing base OEM payload files")
    payload = dict(source)
    verify_binaries(payload)
    verify_splash(payload)
    inf_support_files(payload["OEMSETUP.INF"])
    verify_support(support)
    payload.update(support)
    for name in ("INSTALL.BAT", "TANDY88.BAT"):
        if DEFAULT_WINDOWS.encode("ascii") not in payload[name]:
            raise DiskError("Missing Windows-path template in " + name)
        payload[name] = payload[name].replace(DEFAULT_WINDOWS.encode("ascii"), windows_dir.encode("ascii"))
        payload[name] = payload[name].replace(b"REM WINDOWSDRIVE\r\nC:\r\n",
                                              b"REM WINDOWSDRIVE\r\n" + windows_dir[:2].encode("ascii") + b"\r\n")
    payload["LOCAL.TXT"] = dos_text(
        "COMPLETE TANDY88 OEM DISK\n"
        "Eight required Windows support files and the custom Tandy splash are verified.\n"
        "Run INSTALL from this disk at a DOS prompt; read README.TXT first.\n"
        "Windows directory: " + windows_dir + "\n"
        "DOS helper directory: " + HELPER_DIR + "\n")
    payload["MANIFEST.SHA"] = manifest(payload)
    disk_allocation(payload)
    return payload


def prepare_complete(source, windows_files, windows_dir=DEFAULT_WINDOWS):
    support = {name: expanded_file(single_file(windows_files, name).read_bytes(), name)
               for name in inf_support_files(source["OEMSETUP.INF"])}
    return completed_payload(source, support, windows_dir)


def fresh_output(out):
    if out.exists() or out.is_symlink():
        raise DiskError("Choose a new output path; existing paths are never overwritten: " + str(out))
    if not out.parent.is_dir():
        raise DiskError("Output parent directory must already exist: " + str(out.parent))


def write_directory(payload, out):
    fresh_output(out)
    out.mkdir()
    try:
        for name in sorted(payload):
            (out / name).write_bytes(payload[name])
    except BaseException:
        shutil.rmtree(out)
        raise


def stage(disk, windows_files, out, windows_dir=DEFAULT_WINDOWS):
    fresh_output(out)
    payload = prepare_complete(clean_payload(disk), windows_files, windows_dir)
    write_directory(payload, out)
    return sorted(SUPPORT_HASHES)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--disk", type=Path, default=Path(__file__).resolve().parent / "DISK1",
                        help="Untouched base DISK1 extracted from developer T88TOOLS.ZIP")
    parser.add_argument("--windows-files", "--fonts", dest="windows_files", type=Path, required=True,
                        help="Your Windows 3.0 media or directory of expanded support files")
    parser.add_argument("--out", type=Path, required=True, help="New complete OEM disk directory")
    parser.add_argument("--windows-dir", default=DEFAULT_WINDOWS,
                        help="Guest absolute DOS Windows directory (default C:\\WINDOWS)")
    args = parser.parse_args(argv)
    try:
        support = stage(args.disk, args.windows_files, args.out, args.windows_dir)
    except (DiskError, OSError) as error:
        parser.exit(1, "ERROR: " + str(error) + "\nNo completed disk was produced.\n")
    print("Ready-to-use OEM disk:", args.out)
    print("Verified Windows support files:", ", ".join(support))
    print("Read README.TXT, then run INSTALL from this disk at a DOS prompt.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
