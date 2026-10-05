# FAT12 release data disks

`FAT12.PY` builds real, raw, unpartitioned FAT12 floppy images using only the
Python 3.8+ standard library. It supports two PC formats:

| Format | Bytes | Cylinders/heads/sectors | Media | Sectors/FAT | Data clusters |
| --- | ---: | --- | --- | ---: | ---: |
| 720 KB (default) | 737,280 | 80/2/9 | F9 | 3 | 713 |
| 360 KB (optional) | 368,640 | 40/2/9 | FD | 2 | 354 |

Both use 512-byte sectors, two sectors per cluster, one reserved sector,
two identical FATs, and 112 root directory slots. The volume label uses one
root slot, leaving 111 root files/directories. Subdirectories can span multiple
clusters. Nested and empty directories are preserved. No 1.44 MB image is
created or supported.

## Commands

```text
python FAT12.PY build STAGEDIR TANDY720.IMG --size 720 --label TANDY88
python FAT12.PY verify TANDY720.IMG --source STAGEDIR
python FAT12.PY build STAGEDIR TANDY360.IMG --size 360 --label TANDY88
python TESTFAT.PY -v
```

The output must be a new file outside the source directory. Existing output
files are never overwritten. Each command prints a JSON verification report;
failures exit nonzero. The optional `--source` compares all paths, directory
kinds, file lengths and file bytes against the staging tree. Without it, the
verifier still checks the filesystem and the content-derived volume serial.

Python APIs:

```python
make_image(source, size_kb=720, label="TANDY88")             # bytes
build_image(source, output, size_kb=720, label="TANDY88")    # JSON-safe dict
verify_image(image, source=None)                          # JSON-safe dict
```

The uppercase `.PY` filename can be imported with
`importlib.machinery.SourceFileLoader` on case-sensitive hosts.

## Reproducibility and validation

Names must already be uppercase ASCII DOS 8.3 names. The tool never silently
renames files or invents long-filename aliases. It rejects DOS device names,
case-insensitive collisions, symbolic/hard links, Windows reparse points,
special files, parent traversal, and payload/allocation/root-directory
capacity overflow. It rejects common DOS system/boot filenames, including
IO.SYS, MSDOS.SYS, IBMBIO.COM, IBMDOS.COM, COMMAND.COM and KERNEL.SYS.

Directory entries are sorted, all write dates are 1980-01-01 at 00:00:00,
reserved metadata and unused storage are zero, and the serial is derived
from the geometry, label, paths and payload bytes. Source mtimes, creation
order, host paths and current time do not affect the output. Identical source
content produces identical image bytes. The verifier report likewise has no
host paths or clock-dependent fields.

The strict verifier parses the result independently of the writer and checks
the BPB, boot sector, both FATs, allocation chains, cycles/cross-links, file
sizes, dot/parent references, DOS names, metadata, unused storage and orphan
clusters. It is a release-artifact verifier, not a general-purpose repair or
validation utility for disks later modified by DOS.

## Using an image

Mount the `.IMG` as a floppy data disk in a compatible emulator or configure
Gotek/FlashFloppy for the matching PC floppy geometry. The machine still needs
its separately owned DOS/Windows installation. The image has a small original
8086 message stub that says to boot DOS from another drive; it contains no DOS
boot loader or system files. The image is a data disk, not an operating-system
boot disk.

These formats describe the on-disk layout, not a promise that any particular
physical drive/controller supports both sizes. Hardware/controller geometry
and any Gotek setup must match the chosen image.

## Tests

`TESTFAT.PY` includes a separate generic FAT12 reader and covers nested and
multi-cluster directories, exact full capacity, zero-byte files, deterministic
builds, invalid source trees and deliberate FAT/directory/data corruption.
It also runs `fsck.fat -vn` and mtools read/extraction tests if those tools are
already installed.

Set `FAT12_DOSBOX` to an installed DOSBox-X executable (or wrapper) to enable
an additional emulator test. It mounts both geometries, lists a three-level
path, reads a multi-cluster directory, and copies binary data back for exact
comparison. It does not boot an operating system or perform Windows Setup.

The implementation follows standard PC FAT12 layout. Useful primary references:

- [dosfstools PC floppy geometry definitions](https://github.com/dosfstools/dosfstools/blob/master/src/mkfs.fat.c)
- [Microsoft FAT on-disk format specification](https://www.cs.fsu.edu/~cop4610t/assignments/project3/spec/fatspec.pdf)
