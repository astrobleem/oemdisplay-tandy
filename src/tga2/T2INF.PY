"""Host checks for the single experimental SL/2 Windows 3.0 OEM selector."""
import csv
import io
from pathlib import Path

LABEL = "EXPERIMENTAL TANDY SL/2 FAMILY ONLY 640x200x16"
BUNDLED = {"CGA.GR2", "XTCSYS.FON", "XTCFIX.FON", "XTCOEM.FON",
           "XTSTATIC.LGO", "WXTSPL01.RLE"}


def fields(line):
    return [v.strip() for v in next(csv.reader(io.StringIO(line), skipinitialspace=True))]


def verify(raw):
    if b"\n" in raw.replace(b"\r\n", b""):
        raise ValueError("OEM source must retain CRLF")
    sections, current = {}, None
    for line in raw.decode("ascii").splitlines():
        line = line.strip()
        if not line or line.startswith(";"):
            continue
        if line.startswith("[") and line.endswith("]"):
            current = line[1:-1].lower()
            if current in sections:
                raise ValueError("Duplicate section")
            sections[current] = []
        elif current:
            sections[current].append(line)
        else:
            raise ValueError("Entry outside a section")
    if set(sections) != {"data", "disks", "display", "sysfonts", "fixedfonts", "oemfonts"}:
        raise ValueError("Unexpected selector sections")
    if sections["data"] != ['Version = "3.0"'] or len(sections["display"]) != 1:
        raise ValueError("Only one Windows 3.0 selector is allowed")
    key, row = sections["display"][0].split("=", 1)
    values = fields(row)
    if key.strip() != "TNDYV2" or len(values) != 9:
        raise ValueError("Wrong driver key or nine-field Setup tuple")
    if len(values[1]) > 47 or values[1] != LABEL:
        raise ValueError("Selector must retain the full experimental SL/2-only label within 47 characters")
    expected = ["a:TNDYV2.DRV", LABEL, "200,96,48", "a:CGA.GR2", "a:XTSTATIC.LGO", "", "", "", "a:WXTSPL01.RLE"]
    if values != expected:
        raise ValueError("Driver, geometry or support tuple changed")
    if len(sections["disks"]) != 1:
        raise ValueError("Only one OEM disk is allowed")
    disk_key, disk_row = sections["disks"][0].split("=", 1)
    if disk_key.strip() != "a" or fields(disk_row) != [r"C:\T2EXP", "EXPERIMENTAL TANDY SL/2 FAMILY ONLY", "OEMSETUP.INF"]:
        raise ValueError("Absolute OEM disk path or warning changed")
    for section, name, count in (("sysfonts", "XTCSYS.FON", 3), ("fixedfonts", "XTCFIX.FON", 3), ("oemfonts", "XTCOEM.FON", 4)):
        if len(sections[section]) != 1:
            raise ValueError("One matching font row required")
        row = fields(sections[section][0])
        if len(row) != count or row[0] != "a:" + name or row[2] != "200,96,48" or (count == 4 and row[3] != "1"):
            raise ValueError("Original font source/geometry changed")
    return {"status": "PASS", "label": LABEL, "description_chars": len(LABEL), "limit": 47, "bundled_support_files": sorted(BUNDLED)}


if __name__ == "__main__":
    import json
    print(json.dumps(verify((Path(__file__).parent / "OEMSETUP.INF").read_bytes()), indent=2))
