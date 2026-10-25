"""Assemble TGA2 with existing original fonts, startup art and supplied CGA grabber.

No native build, installer, emulator, download or installed-Windows write occurs.
All driver support ships in the packet; installed DOS/Windows is required.
"""
import argparse
import hashlib
import importlib.machinery
import io
import json
from pathlib import Path
import zipfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
INF = importlib.machinery.SourceFileLoader("t2pack_inf", str(HERE / "T2INF.PY")).load_module()
MEDIA = importlib.machinery.SourceFileLoader(
    "t2pack_media", str(ROOT / "tools/XR1PACK/PREPARE.PY")).load_module()
STAMP = (1980, 1, 1, 0, 0, 0)
SOURCE_NAMES = {"OEMSETUP.INF", "PREPINF.BAT", "README.TXT", "FONTLIC.TXT", "NOTICE.TXT"}


def identity(data):
    return {"bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}


def exact(data, pin, name):
    if identity(data) != pin:
        raise ValueError("Qualified bytes differ: " + name)
    return data


def specs():
    return json.loads((HERE / "T2PINS.JSN").read_bytes())


def dos(text):
    return text.replace("\r\n", "\n").replace("\n", "\r\n").encode("ascii")


def manifest(files):
    return dos("".join(hashlib.sha256(data).hexdigest() + "  " + name + "\n"
                       for name, data in sorted(files.items())))


def archive(files):
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w", compression=zipfile.ZIP_STORED) as z:
        for name, data in sorted(files.items()):
            info = zipfile.ZipInfo(name, STAMP)
            info.create_system = 0
            info.external_attr = 0x20
            z.writestr(info, data)
    return stream.getvalue()


def source_files():
    return {"OEMSETUP.INF": (HERE / "OEMSETUP.INF").read_bytes(),
            "PREPINF.BAT": (HERE / "PREPINF.BAT").read_bytes(),
            "README.TXT": (HERE / "INSTALL.TXT").read_bytes(),
            "FONTLIC.TXT": (ROOT / "distributions/WINXT/FONTLIC.TXT").read_bytes(),
            "NOTICE.TXT": (HERE / "NOTICE.TXT").read_bytes()}


def read_archive(data, allowed):
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        names = z.namelist()
        if len(names) != len(set(names)) or set(names) != allowed:
            raise ValueError("Unexpected or duplicate archive members")
        if any(i.file_size > 1048576 for i in z.infolist()) or z.testzip() is not None:
            raise ValueError("Oversized or corrupt archive member")
        return {name: z.read(name) for name in names}


def prepare(accepted, output, grabber=None):
    """Copy exact accepted runtime; change only integration metadata/support."""
    output = Path(output)
    if output.exists():
        raise ValueError("Output must be new")
    pins = specs()
    original_names = set(pins["runtime"]) | set(pins["accepted_metadata"]) | {"OEMSETUP.INF", "PREPINF.BAT",
                                             "README.TXT", "PINS.JSN", "SHA256.SUM"}
    if Path(accepted).stat().st_size > 1048576:
        raise ValueError("Accepted archive exceeds 1 MiB")
    old = read_archive(Path(accepted).read_bytes(), original_names)
    files = {n: exact(old[n], pin, n) for n, pin in pins["runtime"].items()}
    for name, pin in pins["accepted_metadata"].items():
        exact(old[name], pin, name)
    source = source_files()
    INF.verify(source["OEMSETUP.INF"])
    files.update(source)
    for name, pin in pins["support"].items():
        if name == "CGA.GR2":
            path = Path(grabber) if grabber else ROOT / name
            if path.stat().st_size > 1048576:
                raise ValueError("Grabber input exceeds 1 MiB")
            raw = path.read_bytes()
            data = MEDIA.expanded_file(raw, name)
        else:
            data = (ROOT / "distributions/WINXT" / name).read_bytes()
        files[name] = exact(data, pin, name)
    receipt = {
        "schema": 1,
        "scope": "original fonts/logo/support integration; driver and DOS helpers unchanged",
        "files": {n: identity(b) for n, b in sorted(files.items())},
        "selected_fonts": {"fonts.fon": "XTCSYS.FON", "fixedfon.fon": "XTCFIX.FON",
                           "oemfonts.fon": "XTCOEM.FON"},
        "external_support_inputs": [],
        "native_setup_test": "not asserted by host packaging"
    }
    files["PINS.JSN"] = dos(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    files["SHA256.SUM"] = manifest(files)
    packed = archive(files)
    verify_bytes(packed)
    output.mkdir(parents=True)
    stage = output / "T2EXP"
    stage.mkdir()
    for name, data in files.items():
        (stage / name).write_bytes(data)
    (output / "TNDYV2.ZIP").write_bytes(packed)
    (output / "SHA256SUMS").write_bytes(manifest({"TNDYV2.ZIP": packed}))
    return {"status": "PASS_HOST_PACKET", "zip": identity(packed),
            "fonts": receipt["selected_fonts"], "external_support_inputs": [],
            "native_setup_selected_fonts_verified": False}


def verify_bytes(data):
    pins = specs()
    wanted = set(pins["runtime"]) | set(pins["support"]) | SOURCE_NAMES | {"PINS.JSN", "SHA256.SUM"}
    files = read_archive(data, wanted)
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        if z.namelist() != sorted(wanted) or z.comment:
            raise ValueError("Noncanonical archive order/comment")
        for info in z.infolist():
            if (info.date_time != STAMP or info.compress_type != zipfile.ZIP_STORED
                    or info.create_system != 0 or info.external_attr != 0x20
                    or info.extra or info.comment or info.flag_bits):
                raise ValueError("Noncanonical archive metadata")
    for group in ("runtime", "support"):
        for name, pin in pins[group].items():
            exact(files[name], pin, name)
    for name, source in source_files().items():
        if files[name] != source:
            raise ValueError("Current integration source differs: " + name)
    INF.verify(files["OEMSETUP.INF"])
    if files["SHA256.SUM"] != manifest({n: b for n, b in files.items() if n != "SHA256.SUM"}):
        raise ValueError("Internal manifest differs")
    record = json.loads(files["PINS.JSN"])
    if set(record) != {"schema", "scope", "files", "selected_fonts",
                       "external_support_inputs", "native_setup_test"} or record["schema"] != 1:
        raise ValueError("Unexpected packet record schema")
    if record["selected_fonts"] != {"fonts.fon": "XTCSYS.FON", "fixedfon.fon": "XTCFIX.FON",
                                    "oemfonts.fon": "XTCOEM.FON"}:
        raise ValueError("Selected font contract differs")
    if record["native_setup_test"] != "not asserted by host packaging":
        raise ValueError("Host packaging cannot assert a native Setup result")
    if record["files"] != {n: identity(b) for n, b in files.items()
                           if n not in {"PINS.JSN", "SHA256.SUM"}}:
        raise ValueError("Packet identities differ")
    if record["external_support_inputs"] != []:
        raise ValueError("Packet must include all driver support")
    return record


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--accepted", type=Path, help="Existing qualified TNDYV2.ZIP")
    parser.add_argument("--grabber", type=Path, help="Expanded or mode-A SZDD CGA.GR2; default root file")
    parser.add_argument("--out", type=Path, help="New packet/staging directory")
    parser.add_argument("--verify", type=Path, help="Verify the newly assembled ZIP")
    args = parser.parse_args()
    if args.verify:
        record = verify_bytes(args.verify.read_bytes())
        print(json.dumps({"status": "PASS_HOST_PACKET", "fonts": record["selected_fonts"]}, indent=2))
    elif args.accepted and args.out:
        print(json.dumps(prepare(args.accepted, args.out, args.grabber), indent=2))
    else:
        parser.error("use --accepted and --out, or --verify")


if __name__ == "__main__":
    main()
