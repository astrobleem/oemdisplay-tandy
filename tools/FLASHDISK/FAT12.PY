#!/usr/bin/env python3
"""Deterministic, nonbootable 720/360 KiB FAT12 release images (Python 3.8+).

Only uppercase ASCII DOS 8.3 names are accepted. No long-name aliases,
symlinks, hard links, reparse points, device files or DOS boot files are copied.
The verifier is deliberately strict: it checks this tool's release-image
profile, not arbitrary disks modified by DOS. All timestamps are 1980-01-01.
"""

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import struct
import sys
from dataclasses import dataclass, field


class ImageError(ValueError):
    """Invalid source tree or damaged/unsupported release image."""


@dataclass(frozen=True)
class Geometry:
    size_kb: int
    cylinders: int
    sectors_per_fat: int
    media: int
    sector_size: int = 512
    sectors_per_cluster: int = 2
    reserved: int = 1
    fats: int = 2
    root_entries: int = 112
    heads: int = 2
    sectors_per_track: int = 9

    @property
    def sectors(self):
        return self.size_kb * 2

    @property
    def root_sectors(self):
        return (self.root_entries * 32 + 511) // 512

    @property
    def root_offset(self):
        return (self.reserved + self.fats * self.sectors_per_fat) * 512

    @property
    def data_offset(self):
        return self.root_offset + self.root_sectors * 512

    @property
    def cluster_bytes(self):
        return self.sectors_per_cluster * self.sector_size

    @property
    def clusters(self):
        return (self.size_kb * 1024 - self.data_offset) // self.cluster_bytes


GEOMETRIES = {720: Geometry(720, 80, 3, 0xF9),
              360: Geometry(360, 40, 2, 0xFD)}
NAME_RE = re.compile(r"[A-Z0-9!#$%&'()@^_`{}~\-]{1,8}(?:\.[A-Z0-9!#$%&'()@^_`{}~\-]{1,3})?\Z")
DEVICE_NAMES = {"CON", "PRN", "AUX", "NUL", "CLOCK$"}
DEVICE_NAMES.update("COM%d" % n for n in range(1, 10))
DEVICE_NAMES.update("LPT%d" % n for n in range(1, 10))
BOOT_FILES = {"IO.SYS", "MSDOS.SYS", "IBMBIO.COM", "IBMDOS.COM",
              "COMMAND.COM", "KERNEL.SYS", "DRBIO.SYS", "DRDOS.SYS",
              "BOOTSECT.DOS"}
FIXED_DATE = 0x0021  # 1980-01-01, 00:00:00; source mtimes are ignored.
# Original 8086-only message stub, not an operating-system boot loader.
# Set DS/SS:SP, print through BIOS INT 10h, then halt until reset.
BOOT_CODE = bytes.fromhex(
    "FA 31 C0 8E D8 8E D0 BC 00 7C FB BE 5F 7C FC AC 84 C0 74 09 "
    "B4 0E BB 07 00 CD 10 EB F2 FA F4 EB FD")
BOOT_MESSAGE = b"Data disk only. Boot DOS from another drive.\r\n\0"


@dataclass
class Node:
    name: str
    relative: str
    is_dir: bool
    data: bytes = b""
    children: list = field(default_factory=list)
    clusters: list = field(default_factory=list)


def _require(condition, message):
    if not condition:
        raise ImageError(message)


def _short_name(name):
    _require(bool(NAME_RE.fullmatch(name)),
             "Not an uppercase ASCII DOS 8.3 name: %r" % name)
    _require(name.split(".")[0] not in DEVICE_NAMES,
             "Reserved DOS device name: %s" % name)
    _require(name not in BOOT_FILES, "DOS boot file is not allowed: %s" % name)
    base, separator, extension = name.partition(".")
    return (base.ljust(8) + extension.ljust(3)).encode("ascii")


def _label_bytes(label):
    _require(isinstance(label, str) and
             re.fullmatch(r"[A-Z0-9][A-Z0-9 _-]{0,10}", label) is not None and
             label == label.rstrip(),
             "Label must be 1-11 uppercase ASCII letters/digits/spaces/_/-")
    return label.ljust(11).encode("ascii")


def _safe_path(path):
    """Reject links/reparse points in the path, including its ancestors."""
    path = Path(path).absolute()
    _require(".." not in path.parts, "Parent traversal is not allowed: %s" % path)
    for item in reversed((path,) + tuple(path.parents)):
        info = item.lstat()
        _require(not stat.S_ISLNK(info.st_mode) and
                 not (getattr(info, "st_file_attributes", 0) & 0x400),
                 "Links/reparse points are not allowed: %s" % item)
    return path


def read_source(source, max_bytes=720 * 1024):
    """Read a bounded immutable snapshot of a validated DOS source tree."""
    root = _safe_path(source)
    _require(root.is_dir(), "Source is not a directory: %s" % root)
    seen_ids = set()
    budget = [max_bytes]
    node_count = [0]

    def walk(directory, relative, depth):
        _require(depth <= 64, "Directory nesting exceeds 64 levels")
        info = directory.lstat()
        identity = (info.st_dev, info.st_ino)
        _require(identity not in seen_ids, "Directory alias/cycle: %s" % directory)
        seen_ids.add(identity)
        names = sorted(directory.iterdir(), key=lambda p: p.name)
        folded = [p.name.upper() for p in names]
        _require(len(folded) == len(set(folded)),
                 "DOS case-insensitive name collision in %s" % directory)
        result = []
        for path in names:
            node_count[0] += 1
            _require(node_count[0] <= 23000, "Too many directory entries")
            _short_name(path.name)
            info = path.lstat()
            _require(not stat.S_ISLNK(info.st_mode) and
                     not (getattr(info, "st_file_attributes", 0) & 0x400),
                     "Links/reparse points are not allowed: %s" % path)
            rel = relative + path.name
            if stat.S_ISDIR(info.st_mode):
                node = Node(path.name, rel, True)
                node.children = walk(path, rel + "/", depth + 1)
            else:
                _require(stat.S_ISREG(info.st_mode),
                         "Only regular files/directories are allowed: %s" % path)
                _require(info.st_nlink == 1, "Hard links are not allowed: %s" % path)
                _require(info.st_size <= budget[0], "Source payload exceeds image capacity")
                # O_NOFOLLOW guards replacement of the final component on POSIX.
                flags = os.O_RDONLY | getattr(os, "O_BINARY", 0) | getattr(os, "O_NOFOLLOW", 0)
                fd = os.open(str(path), flags)
                with os.fdopen(fd, "rb") as stream:
                    actual = os.fstat(stream.fileno())
                    _require(stat.S_ISREG(actual.st_mode) and actual.st_nlink == 1 and
                             (actual.st_dev, actual.st_ino) == (info.st_dev, info.st_ino),
                             "Source changed while reading: %s" % path)
                    data = stream.read(budget[0] + 1)
                    after = os.fstat(stream.fileno())
                _require(len(data) == info.st_size and
                         after.st_size == info.st_size and
                         after.st_mtime_ns == info.st_mtime_ns,
                         "Source changed while reading: %s" % path)
                budget[0] -= len(data)
                _require(budget[0] >= 0, "Source payload exceeds image capacity")
                node = Node(path.name, rel, False, data)
            result.append(node)
        return result

    return Node("", "", True, children=walk(root, "", 0))


def _flatten(root):
    for child in root.children:
        yield child
        if child.is_dir:
            yield from _flatten(child)


def _snapshot(root):
    return {n.relative: None if n.is_dir else n.data for n in _flatten(root)}


def _serial(root, geometry, label):
    digest = hashlib.sha256(b"FAT12 release image v1\0")
    digest.update(struct.pack("<H", geometry.size_kb) + label)
    for path, data in sorted(_snapshot(root).items()):
        raw = path.encode("ascii")
        digest.update(struct.pack("<I", len(raw)) + raw)
        digest.update(b"D" if data is None else b"F")
        if data is not None:
            digest.update(struct.pack("<I", len(data)) + data)
    return int.from_bytes(digest.digest()[:4], "little")


def _directory_entry(raw_name, attribute, first_cluster=0, size=0):
    entry = bytearray(32)
    entry[:11] = raw_name
    entry[11] = attribute
    # DOS 2.x write date/time plus zero reserved/create/access fields.
    struct.pack_into("<HHHI", entry, 22, 0, FIXED_DATE, first_cluster, size)
    return bytes(entry)


def _set_fat(fat, cluster, value):
    offset = cluster + cluster // 2
    if cluster & 1:
        fat[offset] = (fat[offset] & 0x0F) | ((value & 0xF) << 4)
        fat[offset + 1] = value >> 4
    else:
        fat[offset] = value & 0xFF
        fat[offset + 1] = (fat[offset + 1] & 0xF0) | (value >> 8)


def make_image(source, size_kb=720, label="TANDY88"):
    """Return image bytes; fail before writing if names/capacity are invalid."""
    _require(size_kb in GEOMETRIES, "Only 720 KB and 360 KB images are supported")
    geometry = GEOMETRIES[size_kb]
    label = _label_bytes(label)
    root = read_source(source, geometry.size_kb * 1024)
    _require(len(root.children) + 1 <= geometry.root_entries,
             "Root directory is full (111 source entries plus volume label)")
    next_cluster = 2
    for node in _flatten(root):
        size = (len(node.children) + 2) * 32 if node.is_dir else len(node.data)
        count = (size + geometry.cluster_bytes - 1) // geometry.cluster_bytes
        _require(next_cluster + count <= geometry.clusters + 2,
                 "Source does not fit: FAT12 allocation/directory overhead exceeds %d KB" % size_kb)
        node.clusters = list(range(next_cluster, next_cluster + count))
        next_cluster += count

    image = bytearray(geometry.size_kb * 1024)
    image[:11] = b"\xEB\x3C\x90TANDY88 "
    struct.pack_into("<HBHBHHBHHHII", image, 11,
                     512, 2, 1, 2, 112, geometry.sectors, geometry.media,
                     geometry.sectors_per_fat, 9, 2, 0, 0)
    struct.pack_into("<BBBI", image, 36, 0, 0, 0x29, _serial(root, geometry, label))
    image[43:54] = label
    image[54:62] = b"FAT12   "
    image[62:62 + len(BOOT_CODE)] = BOOT_CODE
    image[62 + len(BOOT_CODE):62 + len(BOOT_CODE) + len(BOOT_MESSAGE)] = BOOT_MESSAGE
    image[510:512] = b"\x55\xAA"
    fat = bytearray(geometry.sectors_per_fat * 512)
    fat[:3] = bytes((geometry.media, 0xFF, 0xFF))
    for node in _flatten(root):
        for index, cluster in enumerate(node.clusters):
            _set_fat(fat, cluster, node.clusters[index + 1]
                     if index + 1 < len(node.clusters) else 0xFFF)
    for index in range(2):
        offset = 512 + index * len(fat)
        image[offset:offset + len(fat)] = fat

    def directory_data(node, parent_cluster):
        first = node.clusters[0] if node.clusters else 0
        if node is root:
            entries = [_directory_entry(label, 0x08)]
        else:
            entries = [_directory_entry(b".          ", 0x10, first),
                       _directory_entry(b"..         ", 0x10, parent_cluster)]
        for child in node.children:
            entries.append(_directory_entry(
                _short_name(child.name), 0x10 if child.is_dir else 0x20,
                child.clusters[0] if child.clusters else 0,
                0 if child.is_dir else len(child.data)))
        payload = b"".join(entries)
        if node is root:
            image[geometry.root_offset:geometry.root_offset + len(payload)] = payload
        else:
            offset = geometry.data_offset + (first - 2) * geometry.cluster_bytes
            image[offset:offset + len(payload)] = payload
        for child in node.children:
            if child.is_dir:
                directory_data(child, first)
            elif child.clusters:
                offset = geometry.data_offset + (child.clusters[0] - 2) * geometry.cluster_bytes
                image[offset:offset + len(child.data)] = child.data

    directory_data(root, 0)
    result = bytes(image)
    # Independent parser checks chains, geometry, names and exact source bytes.
    _verify_bytes(result, expected=_snapshot(root))
    return result


def build_image(source, output, size_kb=720, label="TANDY88"):
    """Write a new image, never overwrite. Return a verified JSON-safe report."""
    source = _safe_path(source)
    output = Path(output).absolute()
    _require(".." not in output.parts, "Parent traversal is not allowed in output path")
    _safe_path(output.parent)
    _require(source != output and source not in output.parents,
             "Output must be outside the source tree")
    _require(not output.exists() and not output.is_symlink(),
             "Output already exists: %s" % output)
    data = make_image(source, size_kb, label)
    with output.open("xb") as stream:
        stream.write(data)
    return verify_image(output, source)


def _verify_bytes(image, expected=None):
    """Parse independently of the writer; reject malformed release images."""
    _require(len(image) in (360 * 1024, 720 * 1024), "Wrong image length")
    geometry = GEOMETRIES[len(image) // 1024]
    bp = struct.unpack_from("<HBHBHHBHHHII", image, 11)
    _require(bp == (512, 2, 1, 2, 112, geometry.sectors, geometry.media,
                    geometry.sectors_per_fat, 9, 2, 0, 0),
             "Invalid BPB/geometry for a standard %d KB floppy" % geometry.size_kb)
    _require(image[:11] == b"\xEB\x3C\x90TANDY88 " and
             image[36:39] == b"\0\0\x29" and image[54:62] == b"FAT12   " and
             image[510:512] == b"\x55\xAA", "Invalid boot-sector identifiers")
    _require(image[62:62 + len(BOOT_CODE)] == BOOT_CODE and
             image[62 + len(BOOT_CODE):62 + len(BOOT_CODE) + len(BOOT_MESSAGE)] == BOOT_MESSAGE and
             not any(image[62 + len(BOOT_CODE) + len(BOOT_MESSAGE):510]),
             "Boot sector is not the expected nonbootable data-disk stub")
    try:
        label = image[43:54].decode("ascii").rstrip()
        _require(_label_bytes(label) == image[43:54], "Invalid volume label padding")
    except UnicodeDecodeError as error:
        raise ImageError("Non-ASCII volume label") from error
    fat_size = geometry.sectors_per_fat * 512
    fat = image[512:512 + fat_size]
    _require(fat == image[512 + fat_size:512 + 2 * fat_size], "FAT copies differ")
    _require(fat[:3] == bytes((geometry.media, 255, 255)), "Bad FAT media/reserved entries")
    # Decode pairs as 24-bit words, independently of the writer's nibble setter.
    values = []
    for offset in range(0, len(fat) - 2, 3):
        pair = int.from_bytes(fat[offset:offset + 3], "little")
        values.extend((pair & 0xFFF, pair >> 12))
    _require(len(values) >= geometry.clusters + 2, "FAT is too short")
    used = {}
    paths = {}
    label_count = [0]

    def chain(first, owner):
        result = []
        cluster = first
        while True:
            _require(2 <= cluster < geometry.clusters + 2,
                     "Invalid cluster %d for %s" % (cluster, owner))
            _require(cluster not in used, "Cluster cycle/cross-link at %s" % owner)
            used[cluster] = owner
            result.append(cluster)
            value = values[cluster]
            if 0xFF8 <= value <= 0xFFF:
                break
            _require(2 <= value < geometry.clusters + 2,
                     "Broken/reserved/bad cluster chain for %s" % owner)
            cluster = value
        return result

    def content(clusters):
        return b"".join(image[geometry.data_offset + (c - 2) * 1024:
                              geometry.data_offset + (c - 1) * 1024] for c in clusters)

    def directory(data, path, self_cluster, parent_cluster, depth):
        _require(depth <= 64, "Directory nesting exceeds 64 levels")
        names = set()
        seen_end = False
        previous = None
        for offset in range(0, len(data), 32):
            entry = data[offset:offset + 32]
            if not entry[0]:
                seen_end = True
            if seen_end:
                _require(not any(entry), "Nonzero unused directory space in %s" % path)
                continue
            raw, attr = entry[:11], entry[11]
            _require(entry[12:22] == bytes(10) and
                     struct.unpack_from("<HH", entry, 22) == (0, FIXED_DATE),
                     "Nondeterministic/reserved directory metadata in %s" % path)
            first, size = struct.unpack_from("<HI", entry, 26)
            if path and offset in (0, 32):
                wanted = b".          " if offset == 0 else b"..         "
                target = self_cluster if offset == 0 else parent_cluster
                _require(raw == wanted and attr == 0x10 and first == target and size == 0,
                         "Invalid dot/parent entry in %s" % path)
                continue
            if attr == 0x08:
                label_count[0] += 1
                _require(not path and offset == 0 and raw == image[43:54] and first == 0 and size == 0,
                         "Invalid volume-label directory entry")
                continue
            _require(attr in (0x10, 0x20), "Unsupported directory attributes in %s" % path)
            try:
                base, ext = raw[:8].decode("ascii").rstrip(), raw[8:].decode("ascii").rstrip()
            except UnicodeDecodeError as error:
                raise ImageError("Non-ASCII directory name") from error
            name = base + ("." + ext if ext else "")
            _require(_short_name(name) == raw, "Invalid short-name padding in %s" % path)
            _require(name not in names, "Duplicate DOS name in %s" % path)
            names.add(name)
            _require(previous is None or previous < name, "Unsorted directory entries in %s" % path)
            previous = name
            full = path + name
            _require(full not in paths, "Duplicate path: %s" % full)
            if attr == 0x10:
                _require(size == 0, "Nonzero directory file size: %s" % full)
                clusters = chain(first, full)
                sub = content(clusters)
                _require(len(sub) >= 64 and sub[:1] == b"." and sub[32:34] == b"..",
                         "Missing dot entries: %s" % full)
                paths[full] = None
                directory(sub, full + "/", first, self_cluster, depth + 1)
            else:
                if size == 0:
                    _require(first == 0, "Empty file has allocated clusters: %s" % full)
                    payload = b""
                else:
                    clusters = chain(first, full)
                    _require(len(clusters) == (size + 1023) // 1024,
                             "File size/cluster-chain mismatch: %s" % full)
                    allocated = content(clusters)
                    _require(not any(allocated[size:]), "Nonzero file slack: %s" % full)
                    payload = allocated[:size]
                paths[full] = payload
        if path:
            _require(len(data) >= 64 and data[:11] == b".          " and
                     data[32:43] == b"..         ", "Missing dot entries in %s" % path)

    directory(image[geometry.root_offset:geometry.data_offset], "", 0, 0, 0)
    _require(label_count[0] == 1, "Missing or duplicate volume label")
    for cluster in range(2, geometry.clusters + 2):
        if cluster not in used:
            _require(values[cluster] == 0, "Orphan allocated cluster: %d" % cluster)
            start = geometry.data_offset + (cluster - 2) * 1024
            _require(not any(image[start:start + 1024]), "Nonzero free cluster: %d" % cluster)
    _require(not any(values[geometry.clusters + 2:]), "Nonzero FAT tail")
    # FAT bytes outside the decodable cluster pairs must also be zero.
    meaningful_bits = (geometry.clusters + 2) * 12
    tail_integer = int.from_bytes(fat, "little") >> meaningful_bits
    _require(tail_integer == 0, "Nonzero FAT padding")
    _require(not any(image[geometry.data_offset + geometry.clusters * 1024:]),
             "Nonzero trailing data-sector padding")
    if expected is not None:
        _require(set(paths) == set(expected), "Image/source paths differ")
        for path, payload in paths.items():
            _require(payload == expected[path], "Image/source content differs: %s" % path)
    # Serial is content-derived, so verify it from the decoded tree too.
    digest = hashlib.sha256(b"FAT12 release image v1\0")
    digest.update(struct.pack("<H", geometry.size_kb) + image[43:54])
    for path, payload in sorted(paths.items()):
        raw = path.encode("ascii")
        digest.update(struct.pack("<I", len(raw)) + raw)
        digest.update(b"D" if payload is None else b"F")
        if payload is not None:
            digest.update(struct.pack("<I", len(payload)) + payload)
    _require(image[39:43] == digest.digest()[:4], "Content-derived volume serial mismatch")
    files = {p: {"size": len(v), "sha256": hashlib.sha256(v).hexdigest()}
             for p, v in sorted(paths.items()) if v is not None}
    return {"format": "FAT12", "size_kb": geometry.size_kb,
            "image_bytes": len(image), "label": label, "bootable": False,
            "cylinders": geometry.cylinders, "heads": 2, "sectors_per_track": 9,
            "cluster_bytes": 1024, "total_clusters": geometry.clusters,
            "used_clusters": len(used), "free_bytes": (geometry.clusters - len(used)) * 1024,
            "file_count": len(files), "directory_count": len(paths) - len(files),
            "directories": sorted(p for p, v in paths.items() if v is None),
            "files": files, "sha256": hashlib.sha256(image).hexdigest()}


def verify_image(image, source=None):
    """Verify a release image, optionally compare every path and file byte."""
    path = _safe_path(image)
    _require(path.is_file(), "Image is not a regular file")
    _require(path.stat().st_size in (360 * 1024, 720 * 1024), "Wrong image length")
    expected = _snapshot(read_source(source)) if source is not None else None
    return _verify_bytes(path.read_bytes(), expected)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    actions = parser.add_subparsers(dest="action", required=True)
    build = actions.add_parser("build", help="Create a new deterministic data-disk image")
    build.add_argument("source", type=Path)
    build.add_argument("output", type=Path)
    build.add_argument("--size", dest="size_kb", type=int, choices=(720, 360), default=720)
    build.add_argument("--label", default="TANDY88")
    verify = actions.add_parser("verify", help="Verify geometry, FATs, paths and source bytes")
    verify.add_argument("image", type=Path)
    verify.add_argument("--source", type=Path)
    args = parser.parse_args(argv)
    try:
        if args.action == "build":
            result = build_image(args.source, args.output, args.size_kb, args.label)
        else:
            result = verify_image(args.image, args.source)
    except (ImageError, OSError) as error:
        parser.exit(1, "FAT12: %s\n" % error)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
