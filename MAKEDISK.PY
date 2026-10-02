#!/usr/bin/env python3
"""Developer builder/verifier for the ready-to-use TANDY88 OEM disk ZIP."""
import argparse
import importlib.machinery
import importlib.util
from pathlib import Path
import re
import sys
import zipfile

HERE = Path(__file__).resolve().parent
# Uppercase .PY preserves DOS source naming on case-sensitive hosts too.
_loader = importlib.machinery.SourceFileLoader("oem_stage", str(HERE / "STAGE.PY"))
_spec = importlib.util.spec_from_loader(_loader.name, _loader)
stage = importlib.util.module_from_spec(_spec)
_loader.exec_module(stage)


def source_payload(repo):
    payload = {}
    for name in sorted(stage.PAYLOAD_NAMES):
        if name in stage.BINARY_HASHES:
            source = repo / "src" / "tandysw" / "bin"
        elif name in ("INSTALL.BAT", "TANDY88.BAT"):
            source = repo / "oemdisk"
        else:
            source = repo
        payload[name] = stage.single_file(source, name).read_bytes()
    stage.verify_binaries(payload)
    stage.inf_support_files(payload["OEMSETUP.INF"])
    for name in stage.PAYLOAD_NAMES - stage.BINARY_HASHES.keys():
        stage.checked_text(payload[name], name)
    return payload


def write_zip(entries, out):
    stage.fresh_output(out)
    created = False
    try:
        with out.open("xb") as stream:
            created = True
            with zipfile.ZipFile(stream, "w", compression=zipfile.ZIP_STORED) as archive:
                for name in sorted(entries):
                    info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
                    info.create_system = 0
                    info.external_attr = 0x20
                    info.compress_type = zipfile.ZIP_STORED
                    archive.writestr(info, entries[name])
    except BaseException:
        if created:
            out.unlink()
        raise


def disk_entries(payload):
    entries = {"DISK1/" + name: data for name, data in payload.items()}
    entries["README.TXT"] = payload["README.TXT"]
    return entries



def disk_allocation(payload):
    """Standard 360 KB FAT12: 2 sectors/cluster, 2 FATs, 112 root entries."""
    sector = 512
    total = 720 * sector
    overhead = (1 + 2 * 2 + 7) * sector
    cluster = 1024
    allocated = sum(((len(data) + cluster - 1) // cluster) * cluster for data in payload.values())
    if len(payload) > 112 or allocated > total - overhead:
        raise stage.DiskError("Extracted OEM disk exceeds standard 360 KB FAT12 capacity")
    return {"files": len(payload), "logical_bytes": sum(map(len, payload.values())),
            "allocated_file_bytes": allocated, "filesystem_overhead_bytes": overhead,
            "total_used_bytes": allocated + overhead, "capacity_bytes": total,
            "free_data_bytes": total - overhead - allocated}


def build_toolkit(repo, out):
    """Explicit support-free developer alternative, never the normal download."""
    if out.name.upper() == "TANDY88.ZIP":
        raise stage.DiskError("Toolkit output must be distinctly named, for example T88TOOLS.ZIP")
    stage.fresh_output(out)
    payload = source_payload(repo)
    payload["MANIFEST.SHA"] = stage.manifest(payload)
    entries = disk_entries(payload)
    entries["STAGE.PY"] = stage.single_file(repo, "STAGE.PY").read_bytes()
    stage.checked_text(entries["STAGE.PY"], "STAGE.PY")
    entries["TOOLKIT.TXT"] = stage.dos_text(
        "DEVELOPER TOOLKIT - NOT AN INSTALL-READY DISK\n"
        "Normal users should download the complete TANDY88.ZIP instead.\n"
        "This alternative omits the six Windows support files and LOCAL.TXT.\n"
        "Developer command: python STAGE.PY --windows-files MEDIA --out NEWDISK\n")
    write_zip(entries, out)
    return sorted(stage.SUPPORT_HASHES)


def build(repo, out, windows_files=None, local_out=None, windows_dir=stage.DEFAULT_WINDOWS):
    """Build the complete release from a fixed allowlist, never a directory glob."""
    if windows_files is None:
        raise stage.DiskError("Developer rebuild requires --windows-files MEDIA; "
                              "normal users should download the ready-to-use TANDY88.ZIP. "
                              "Use --toolkit-only only for a support-free developer toolkit")
    stage.fresh_output(out)
    if local_out is not None:
        stage.fresh_output(local_out)
        if out.resolve() == local_out.resolve():
            raise stage.DiskError("Archive and extracted disk must have different paths")
    payload = stage.prepare_complete(source_payload(repo), windows_files, windows_dir)
    disk_allocation(payload)
    write_zip(disk_entries(payload), out)
    if local_out is not None:
        try:
            stage.write_directory(payload, local_out)
        except BaseException:
            out.unlink()
            raise
    return sorted(stage.SUPPORT_HASHES)


def build_with_local(repo, out, windows_files, local_out, windows_dir=stage.DEFAULT_WINDOWS):
    return build(repo, out, windows_files, local_out, windows_dir)


def verify_archive(repo, path):
    """Verify complete release, exact dependencies and current sources; no media needed."""
    expected_names = {"DISK1/" + name for name in stage.PAYLOAD_NAMES | set(stage.SUPPORT_HASHES)
                      | {"LOCAL.TXT", "MANIFEST.SHA"}} | {"README.TXT"}
    with zipfile.ZipFile(path) as archive:
        infos = archive.infolist()
        names = [info.filename for info in infos]
        if len(names) != len(expected_names) or set(names) != expected_names:
            raise stage.DiskError("Complete ZIP has missing, extra, or duplicate files")
        if names != sorted(names) or archive.comment:
            raise stage.DiskError("Complete ZIP has noncanonical order or comment")
        for info in infos:
            if (info.file_size > 1024 * 1024 or info.compress_type != zipfile.ZIP_STORED or
                    info.date_time != (1980, 1, 1, 0, 0, 0) or info.create_system != 0 or
                    info.external_attr != 0x20 or info.extra or info.comment):
                raise stage.DiskError("Noncanonical or oversized ZIP member: " + info.filename)
        entries = {name: archive.read(name) for name in names}
    payload = {name[6:]: data for name, data in entries.items() if name.startswith("DISK1/")}
    stage.verify_binaries(payload)
    support = {name: payload[name] for name in stage.SUPPORT_HASHES}
    stage.verify_support(support)
    marker = stage.checked_text(payload["LOCAL.TXT"], "LOCAL.TXT")
    match = re.search(r"^Windows directory: ([^\r\n]+)\r?$", marker, re.M)
    if not match:
        raise stage.DiskError("Complete ZIP has no valid Windows directory marker")
    disk_allocation(payload)
    expected = stage.completed_payload(source_payload(repo), support, match.group(1))
    if entries != disk_entries(expected):
        raise stage.DiskError("Complete ZIP differs from current source or manifest; rebuild it")
    return sorted(stage.SUPPORT_HASHES)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, help="New ZIP (default TANDY88.ZIP; toolkit T88TOOLS.ZIP)")
    parser.add_argument("--windows-files", type=Path,
                        help="Developer rebuild source: accepted expanded files or Windows 3.0 SZDD media")
    parser.add_argument("--local-out", type=Path, help="Also write the ready-to-use extracted DISK1 directory")
    parser.add_argument("--windows-dir", default=stage.DEFAULT_WINDOWS,
                        help="Guest absolute DOS Windows path (default C:\\WINDOWS)")
    parser.add_argument("--toolkit-only", action="store_true",
                        help="Explicitly build support-free developer T88TOOLS.ZIP instead")
    parser.add_argument("--verify", type=Path, help="Validate a complete ZIP against current source without media")
    args = parser.parse_args(argv)
    if args.verify and (args.out or args.windows_files or args.local_out or args.toolkit_only or
                        args.windows_dir != stage.DEFAULT_WINDOWS):
        parser.error("--verify cannot be combined with build options")
    if args.toolkit_only and (args.windows_files or args.local_out or args.windows_dir != stage.DEFAULT_WINDOWS):
        parser.error("--toolkit-only cannot be combined with media, local disk, or Windows-path options")
    out = args.out or HERE / ("T88TOOLS.ZIP" if args.toolkit_only else "TANDY88.ZIP")
    try:
        if args.verify:
            verify_archive(HERE, args.verify)
            print("Verified complete OEM ZIP and current source:", args.verify)
            return 0
        if args.toolkit_only:
            build_toolkit(HERE, out)
            print("Created developer toolkit (not install-ready):", out)
            print("Normal users should download the complete TANDY88.ZIP.")
            return 0
        support = build(HERE, out, args.windows_files, args.local_out, args.windows_dir)
    except (stage.DiskError, OSError, zipfile.BadZipFile) as error:
        parser.exit(1, "ERROR: " + str(error) + "\n")
    print("Created ready-to-use OEM package:", out)
    print("Included and verified:", ", ".join(support))
    print("Users can extract DISK1 and run INSTALL from DOS; no Python or media staging needed.")
    if args.local_out:
        print("Ready-to-use extracted disk:", args.local_out)
    with zipfile.ZipFile(out) as archive:
        payload = {n[6:]: archive.read(n) for n in archive.namelist() if n.startswith("DISK1/")}
    budget = disk_allocation(payload)
    print("360 KB floppy:", budget["allocated_file_bytes"], "bytes allocated to files +",
          budget["filesystem_overhead_bytes"], "bytes FAT/root/reserved =",
          budget["total_used_bytes"], "of", budget["capacity_bytes"], "bytes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
