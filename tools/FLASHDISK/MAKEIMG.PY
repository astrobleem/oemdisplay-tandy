#!/usr/bin/env python3
"""Build reproducible 720 KB WINXT data disks from the accepted runtime.

Public builds exclude Windows support files. --windows-files makes a private,
own-media install disk; never upload that output to GitHub or other people.
This packages pinned binaries. It does not compile or qualify new drivers.
"""
import argparse
import csv
import hashlib
import importlib.machinery
import importlib.util
import json
from pathlib import Path
import re
import tempfile
import zipfile

HERE = Path(__file__).resolve().parent
PUBLIC_NAMES = ('HOLD14.TXT', 'HOLD160.PNG', 'HOLD640.PNG', 'INSTALL.BAT',
    'MATRIX.EXE', 'MAZE.EXE', 'PINBALL.EXE', 'NAMES11.TXT', 'OEMSETUP.INF', 'README.TXT',
    'RESERVE.COM', 'SHELL14.TXT', 'SHELLSEL.EXE', 'SHFULL.TXT', 'STARFLD.EXE',
    'TABOUT.EXE', 'TCHIME.EXE', 'TESTS.TXT', 'TESTS14.TXT', 'TEXIT.EXE',
    'TEXTMODE.TXT', 'TINST.EXE', 'TR51616.DRV', 'TR53204.DRV', 'TR53216.DRV',
    'TR56402.DRV', 'TR56404.DRV', 'TSCHECK.EXE', 'TSHELL.EXE', 'TSHELL.INI',
    'TSINPUT.DLL', 'TSREADY.TXT', 'TSSETUP.BAT', 'TSTART.BAT', 'TXTMODE.DRV',
    'WAVEXT.EXE', 'XTCLEAN.COM', 'XTWAVE.DAT', 'WXTSPL01.RLE', 'XPCHIME.EXE')

SPLASH_NAME = 'WXTSPL01.RLE'
SPLASH_SHA = 'eec3a413bb776bea8eccb19a379428d15f06cbdc0ac41b0871345ff9c24caf1c'
SPLASH_BYTES = 4062

WINDOWS_NAMES = ('CGA.GR2', 'CGALOGO.LGO', 'CGAFIX.FON', 'CGAOEM.FON',
    'CGASYS.FON', 'EGAFIX.FON', 'EGAOEM.FON', 'EGASYS.FON', 'TXTSYS.FON')


class PackageError(Exception):
    pass


def load(name, path):
    loader = importlib.machinery.SourceFileLoader(name, str(path))
    spec = importlib.util.spec_from_loader(name, loader)
    module = importlib.util.module_from_spec(spec)
    import sys
    sys.modules[name] = module
    loader.exec_module(module)
    return module


def sha(data):
    return hashlib.sha256(data).hexdigest()


def dos(text):
    return text.replace('\r\n', '\n').replace('\n', '\r\n').encode('ascii')


def read_file(path):
    if path.is_symlink() or not path.is_file() or path.stat().st_size > 1048576:
        raise PackageError('Missing, linked or oversized input: ' + str(path))
    return path.read_bytes()



def verify_default_splash(payload):
    """Current installs have one approved XT image, never a splash menu."""
    art = payload.get(SPLASH_NAME, b'')
    if len(art) != SPLASH_BYTES or hashlib.sha256(art).hexdigest() != SPLASH_SHA:
        raise PackageError('Current default requires the approved Windows XT splash')
    section = ''; profiles = set()
    try:
        for line in payload['OEMSETUP.INF'].decode('ascii').splitlines():
            line = line.strip()
            if not line or line.startswith(';'): continue
            if line.startswith('['): section = line.lower(); continue
            if section != '[display]': continue
            name, separator, value = line.partition('=')
            name = name.strip().upper()
            row = next(csv.reader([value], skipinitialspace=True, strict=True))
            if not separator or name in profiles or len(row) != 9 or row[8].strip().upper() != 'A:' + SPLASH_NAME:
                raise PackageError('Every current Setup profile must select Windows XT')
            profiles.add(name)
    except (KeyError, UnicodeError, csv.Error, StopIteration) as error:
        raise PackageError('Invalid Windows XT splash selection: ' + str(error))
    if profiles != {'TR53216', 'TR56404', 'TR51616', 'TR53204', 'TR56402', 'TXTMODE'}:
        raise PackageError('Expected all six current Windows XT display profiles')

def verify_dos_wave(payload):
    """The DOS updater must expand the exact already-qualified original module."""
    expected_wrapper = 'be8daca3153969921238b04307cdb4f75698086d12f74a024e4c198e95ce43ad'
    expected_logo = '8b2fc40b8c6cc3a231686f8c1337943450a1a976a5fc47dd02ed8859cbe72b2c'
    if sha(payload.get('XTCLEAN.COM', b'')) != expected_wrapper:
        raise PackageError('Qualified DOS wrapper changed')
    packed = payload.get('XTWAVE.DAT', b''); expanded = bytearray(); i = 0
    while i < len(packed):
        c = packed[i]; i += 1
        count = c + 1 if c < 128 else c - 128 + 3
        if c < 128:
            if i + count > len(packed): raise PackageError('Truncated wave payload')
            expanded.extend(packed[i:i+count]); i += count
        else:
            if i == len(packed): raise PackageError('Truncated wave run')
            expanded.extend(bytes([packed[i]]) * count); i += 1
        if len(expanded) > 35971: raise PackageError('Oversized wave payload')
    if len(expanded) != 35971 or sha(expanded) != expected_logo:
        raise PackageError('Qualified DOS logo changed')


def public_payload(runtime):
    raw = read_file(runtime / 'MANIFEST.SHA')
    manifest = {}
    for line in raw.decode('ascii').splitlines():
        fields = line.split()
        if len(fields) != 2:
            raise PackageError('Malformed runtime manifest')
        digest, name = fields
        if not re.fullmatch('[a-f0-9]{64}', digest) or name in manifest:
            raise PackageError('Invalid or duplicate manifest entry: ' + name)
        manifest[name] = digest
    if set(manifest) != set(PUBLIC_NAMES) | set(WINDOWS_NAMES):
        raise PackageError('Runtime manifest changed; review the explicit publication allowlist')
    payload = {}
    for name in PUBLIC_NAMES:
        data = read_file(runtime / name)
        if sha(data) != manifest[name]:
            raise PackageError('Runtime hash mismatch: ' + name)
        payload[name] = data
    verify_default_splash(payload)
    verify_dos_wave(payload)
    payload['MANIFEST.SHA'] = raw
    return payload


def readme(private):
    title = ('PRIVATE OWN-MEDIA DISK - DO NOT REDISTRIBUTE' if private else
             'PUBLIC DISK - REUSES YOUR OWN WINDOWS SUPPORT FILES')
    return dos("WINDOWS XT - 720 KB TANDY / GOTEK / EMULATOR DATA DISK\n"
               + title + r"""

This is a DATA disk, not a DOS boot disk or a Windows installation disk.
Boot your existing DOS 3.3+ system first. Requires Windows 3.0 real mode,
an original-compatible Tandy graphics setup and a writable hard disk/CF.
Back up Windows before using any experimental driver. No Python or compiler
is needed to install this disk. The simple path uses C:\WINDOWS and C:\WINXT.
The disk keeps the five TR5 graphics modes and Tandy Start desktop.
This first-run update adds the Windows XT Programs group and Pinball v2;
Matrix, Maze and Starfield entries launch /S saver previews. Existing
Program Manager groups stay read-only. The installer preserves its source
INF as OEMBASE.INF and localizes the OEM disk path to the actual source.
Exit initially focuses Cancel: Enter/Escape cancel, E selects Exit.
Existing long-name labels in Browse require DOS 6.22, Win3 real mode, fixed
uncompressed FAT12/FAT16 and 512-byte sectors; actions use DOS short aliases.
TRIAL7, newer test apps and sound drivers remain separate opt-in packages.

GOTEK / EMULATOR / REAL FLOPPY
The IMG is standard 720 KB double-density: 737280 bytes; FAT12; 80 cylinders;
2 heads; 9 sectors/track; 512-byte sectors. No 1.44 MB support is required.
GoTek firmware and controller must support this geometry; a 360 KB-only
physical drive cannot read a 720 KB floppy. Verify your own hardware setup.
FlashFloppy: copy the IMG to USB, select it, then access DOS drive A:.
Other firmware may use its own image-selection or filename convention.
Emulators: mount as a 720 KB floppy, not a hard disk or directory.
DOSBox-X example: IMGMOUNT A WINXT720.IMG -T FLOPPY
Real media: write the raw IMG to compatible double-density media with an
image writer. Copying the IMG as an ordinary file is not a disk write.
Keep the floppy image write-protected where practical.

INSTALL (OUTSIDE WINDOWS)
1. Mount the image, then at a plain DOS prompt:
     A:
     CD \
     INSTALL
2. PREPXT looks for matching support files in your existing Windows folder
   and SYSTEM. If some are missing, it tells you which ones and stops.
   Run again with a directory holding your own Windows 3.0 media files:
     INSTALL D:\WIN30SRC
   Up to four media directories can be supplied. Original SZDD compressed
   files are accepted. Use directories copied from your own media if you
   have only one floppy drive. No Internet or Python is needed on the Tandy.
3. After all inputs verify, confirm the helper's prompt. It creates a NEW
   C:\WINXT, gathers/expands only the matching owned support files, derives
   the text font locally, copies our pinned runtime and verifies the result.
   Existing C:\WINXT, wrong files, missing inputs and insufficient free
   space stop preparation. Windows files and boot configuration are untouched.
4. Then run:
     C:
     CD \WINXT
     INSTALL
   In Windows Setup choose Display -> Other display, enter C:\WINXT,
   choose your mode and accept Complete Changes. If asked about CONFIG.SYS,
   choose option 3 (make no changes). Optional desktop: C:\WINXT\TSSETUP.
5. Start Windows with C:\WINXT\WINXT. Never bypass its video-memory or
   recovery guards. Use WINXT\README.TXT for switching, backup and rollback.

The disk itself remains unchanged. Backup/helper writes happen on hard
disk/CF, never on the mounted floppy. Do not run WINXT\INSTALL directly
from the floppy. The original guarded installer creates numbered backups.
Advanced: PREPXT WINXT D:\WIN30 [media directories] prepares the same fresh
C:\WINXT for a different Windows path; then run INSTALL D:\WIN30 from
C:\WINXT. The optional desktop remains qualified only at C:\WINDOWS.

SUPPORTED OWNED FILES
The exact supported English Windows 3.0 files are CGA.GR2, CGALOGO.LGO,
CGASYS.FON, CGAFIX.FON, CGAOEM.FON, EGASYS.FON, EGAFIX.FON and EGAOEM.FON.
Wrong versions are refused. PREPXT makes TXTSYS.FON privately from your
CGA fonts; that is used only by the experimental hardware-text choice.
Do not redistribute the completed C:\WINXT folder or private own-media disk.

PUBLICATION / TEST LIMITS
GitHub builds the image from exact hash-pinned, already-built runtime files.
It does not recompile the legacy MASM/DDK source or certify physical hardware.
The FAT12 layout and emulator file access are tested. Physical GoTek and
controller behavior still require hardware qualification. Experimental text
has known character damage; use graphics modes for ordinary work.
Public outputs contain no Microsoft support files, fonts, OS boot files or
compiler/DDK toolchain. Existing project/DDK licensing notices are unchanged.
The guarded DOS installer enables the short slow flag wave in qualified
Color mode. A pending key skips it. Mono/other modes retain static startup.
It privately combines your matching SYSTEM\WIN.CNF with the original logo;
the updater changes guarded starters, never installed WIN.COM or settings.
This is a pre-load animation, not simultaneous loading. Wrong loader bytes
or altered starters/wrapper refuse safely; never bypass the guard.
To restore only the original static starters at plain DOS:
  C:\WINXT\WAVEXT RESTORE C:\WINDOWS C:\WINXT
To re-enable, use APPLY with the same arguments. Full rollback uses the
numbered WINXT\BACKUP\B001\RESTORE YES path printed by INSTALL. It disables
the wave first and verifies restored original Windows resources. Added
helpers remain inactive; do not redistribute the completed own-media folder.
WXTTOOLS.ZIP is an optional developer/reproduction toolkit; normal users need
only WINXT720.IMG (or the same image inside WINXT720.ZIP) and their own Windows.
""")


def helper_payload():
    raw = read_file(HERE / 'HELPER.SHA').decode('ascii')
    expected = {}
    for line in raw.splitlines():
        digest, name = line.split()
        if not re.fullmatch('[a-f0-9]{64}', digest) or name in expected or '/' in name or '\\' in name:
            raise PackageError('Invalid helper manifest')
        expected[name] = digest
    if set(expected) != {'PREPXT.EXE', 'PREPXT.C', 'XTPINS.H', 'BUILD.BAT'}:
        raise PackageError('Helper manifest changed; review the explicit publication allowlist')
    data = {}
    for name, digest in expected.items():
        data[name] = read_file(HERE / name)
        if sha(data[name]) != digest:
            raise PackageError('Helper source/binary mismatch: ' + name)
    return data


def validate_helper_pins(payload, helper):
    entries = re.findall(r'\{"([A-Z0-9_.]+)","([0-9a-f]{64})",([0-9]+)UL,([012])\}',
                         helper['XTPINS.H'].decode('ascii'))
    expected = {n: h for h, n in (line.split() for line in payload['MANIFEST.SHA'].decode('ascii').splitlines())}
    expected['MANIFEST.SHA'] = sha(payload['MANIFEST.SHA'])
    if len(entries) != len(expected) or {e[0] for e in entries} != set(expected):
        raise PackageError('DOS helper pins do not cover the exact runtime')
    for name, digest, size, kind in entries:
        expected_kind = '2' if name == 'TXTSYS.FON' else ('1' if name in WINDOWS_NAMES else '0')
        if digest != expected[name] or kind != expected_kind:
            raise PackageError('DOS helper pin differs from runtime manifest: ' + name)
        if name in payload and int(size) != len(payload[name]):
            raise PackageError('DOS helper size differs from runtime: ' + name)


def install_batch():
    return dos('@ECHO OFF\nIF NOT EXIST WINXT\\TINST.EXE GOTO ROOT\n'
               'IF NOT EXIST PREPXT.EXE GOTO ROOT\n'
               'PREPXT WINXT C:\\WINDOWS %1 %2 %3 %4\n'
               'IF ERRORLEVEL 1 GOTO STOP\n'
               'ECHO Next: C: then CD \\WINXT then INSTALL\nGOTO DONE\n'
               ':ROOT\nECHO Select the mounted floppy and CD \\ before INSTALL.\n'
               'GOTO DONE\n:STOP\nECHO Preparation stopped. Read the message above.\n:DONE\n')


def write_zip(path, entries):
    with path.open('xb') as output:
        with zipfile.ZipFile(output, 'w', compression=zipfile.ZIP_STORED) as archive:
            for name, data in sorted(entries.items()):
                info = zipfile.ZipInfo(name, (1980, 1, 1, 0, 0, 0))
                info.create_system = 0
                info.external_attr = 0x20
                archive.writestr(info, data)


WAVE_NAMES = {'DEFAULT.JSON', 'FRAME.INC', 'MKSTART.PY', 'QUALIFY.JSON',
              'README.MD', 'RESERVE.COM', 'WAVE.INC', 'XTCLEAN.ASM',
              'XTCLEAN.COM', 'XTLOGO.ASM', 'XTLOGO.LGO'}

def wave_payload():
    source = HERE / 'WAVE' if (HERE / 'WAVE').is_dir() else HERE.parents[1] / 'examples/WXTSPL/WAVE'
    manifest = json.loads(read_file(source / 'FILES.JSON'))
    if set(manifest) != WAVE_NAMES or {p.name for p in source.iterdir() if p.is_file()} != WAVE_NAMES | {'FILES.JSON'}:
        raise PackageError('Independent wave allowlist changed')
    data = {name: read_file(source / name) for name in sorted(WAVE_NAMES)}
    if any(sha(data[n]) != manifest[n] for n in data):
        raise PackageError('Independent wave file pin mismatch')
    pins = {'XTLOGO.LGO': '8b2fc40b8c6cc3a231686f8c1337943450a1a976a5fc47dd02ed8859cbe72b2c',
            'XTCLEAN.COM': 'be8daca3153969921238b04307cdb4f75698086d12f74a024e4c198e95ce43ad',
            'RESERVE.COM': '644290e234cab9a6ac3799fa32959bb493d82d566501a8925720bb5a28c6afa8'}
    if any(sha(data[n]) != h for n,h in pins.items()):
        raise PackageError('Native-qualified wave binary changed; requalification required')
    policy = json.loads(data['DEFAULT.JSON'])
    if policy['startup_default'] != 'slow-flag-wave' or {n:p['sha256'] for n,p in policy['payload'].items()} != pins:
        raise PackageError('Independent startup default/pins mismatch')
    data['FILES.JSON'] = read_file(source / 'FILES.JSON')
    return {'WAVE/' + n: b for n,b in data.items()}


def build(runtime, out, windows_files=None):
    if out.exists():
        raise PackageError('Output exists; choose a fresh directory')
    wave = wave_payload()
    payload = public_payload(runtime)
    public = dict(payload)
    private = windows_files is not None
    helper = helper_payload()
    validate_helper_pins(public, helper)
    fat = load('winxt_fat12', HERE / 'FAT12.PY')
    with tempfile.TemporaryDirectory(prefix='winxt-disk-') as temporary:
        temp = Path(temporary).resolve()
        if private:
            stage = load('winxt_owned_stage', runtime / 'STAGE.PY')
            try:
                stage.stage(windows_files, temp / 'owned')
            except stage.DiskError as error:
                raise PackageError(str(error)) from error
            payload = {p.name: read_file(p) for p in (temp / 'owned').iterdir()}
        root = temp / 'disk'
        (root / 'WINXT').mkdir(parents=True)
        for name, data in payload.items():
            (root / 'WINXT' / name).write_bytes(data)
        guide = readme(private)
        (root / 'README.TXT').write_bytes(guide)
        (root / 'INSTALL.BAT').write_bytes(install_batch())
        (root / 'PREPXT.EXE').write_bytes(helper['PREPXT.EXE'])
        out.mkdir(parents=False)
        stem = 'WXTP720' if private else 'WINXT720'
        image = out / (stem + '.IMG')
        fat.build_image(root, image, size_kb=720, label='WINXT OWNED' if private else 'WINXT SETUP')
        report = fat.verify_image(image, source=root)
        (out / 'README.TXT').write_bytes(guide)
        write_zip(out / (stem + '.ZIP'), {stem + '.IMG': image.read_bytes(), 'README.TXT': guide})
        if not private:
            entries = {'WINXT/' + n: b for n, b in public.items()}
            entries['WINXT/STAGE.PY'] = read_file(runtime / 'STAGE.PY')
            entries.update({n: read_file(HERE / n) for n in ('MAKEIMG.PY', 'FAT12.PY')})
            entries.update(wave)
            entries.update(helper)
            entries['HELPER.SHA'] = read_file(HERE / 'HELPER.SHA')
            entries['README.TXT'] = guide
            write_zip(out / 'WXTTOOLS.ZIP', entries)
        metadata = {'schema': 1, 'publication_allowed': not private,
            'kind': 'private-own-media' if private else 'public-support-free',
            'binary_policy': 'package accepted pinned binaries; no recompilation',
            'independent_startup_default': 'slow-flag-wave',
            'disk_setup_startup': 'guarded-color-wave-static-fallback',
            'wave_payload_sha256': {n: sha(b) for n,b in wave.items()},
            'runtime_manifest_sha256': sha(public['MANIFEST.SHA']),
            'helper_sha256': sha(helper['PREPXT.EXE']),
            'windows_support_included': private, 'image_bytes': image.stat().st_size,
            'geometry': {'cylinders': 80, 'heads': 2, 'sectors_per_track': 9,
                         'sector_bytes': 512}, 'fat_verification': report}
        (out / 'BUILD.JSON').write_bytes((json.dumps(metadata, indent=2, sort_keys=True) + '\n').encode('ascii'))
        checksums = ''.join(sha(p.read_bytes()) + '  ' + p.name + '\n'
                            for p in sorted(out.iterdir()))
        (out / 'SHA256SUMS').write_bytes(checksums.encode('ascii'))
    return metadata


def main():
    default = HERE / 'WINXT' if (HERE / 'WINXT').is_dir() else HERE.parents[1] / 'distributions' / 'WINXT'
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runtime', type=Path, default=default)
    parser.add_argument('--out', type=Path, required=True, help='New output directory')
    parser.add_argument('--windows-files', type=Path, help='Own media only; output is PRIVATE and must not be shared')
    args = parser.parse_args()
    try:
        report = build(args.runtime, args.out, args.windows_files)
    except (PackageError, OSError, ValueError) as error:
        parser.exit(1, 'Refused: ' + str(error) + '\n')
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == '__main__':
    main()
