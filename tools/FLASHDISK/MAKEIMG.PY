#!/usr/bin/env python3
"""Build reproducible 720 KB WINXT data disks from the accepted runtime.

Public builds exclude Windows support files. The complete private own-media
payload does not fit 720 KB; --windows-files is refused. Use PREPXT to prepare
the complete folder on your DOS hard disk from your own matching media.
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
PUBLIC_NAMES = ('XTMODE.EXE', 'MODELIC.TXT', 'MODEINFO.TXT', 'XTSTATIC.LGO', 'LOGOLIC.TXT', 'LOGOINFO.TXT', 'XTCSYS.FON', 'XTCFIX.FON', 'XTCOEM.FON', 'XTESYS.FON', 'XTEFIX.FON', 'XTEOEM.FON', 'XTTSYS.FON', 'FONTLIC.TXT', 'FONTINFO.TXT', 'CPSET.EXE', 'CPSET.TXT', 'HOLD14.TXT', 'HOLD160.PNG', 'HOLD640.PNG', 'INSTALL.BAT',
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

WINDOWS_NAMES = ('CGA.GR2',)


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
    logo=payload.get('XTSTATIC.LGO', b'')
    if len(logo)!=361 or hashlib.sha256(logo).hexdigest()!='995d71e3626de64c8fe21bc1f037e0dece0853d4f0d09082bf607b2d237b37ef':
        raise PackageError('Original static logo pin mismatch')
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
            if not separator or name in profiles or len(row) != 9 or row[8].strip().upper() != 'A:' + SPLASH_NAME or row[3].strip().upper() != 'A:CGA.GR2' or row[4].strip().upper() != 'A:XTSTATIC.LGO':
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
    return dos(r"""WINDOWS XT - DOS MODE SWITCHER TEST CANDIDATE - NOT PUBLISHED

This is a 720 KB DATA disk, not a DOS boot disk or a Windows installation.
Requires DOS 3.3+, Windows 3.0 real mode, a compatible Tandy and writable CF.
Back up Windows first. No Python/compiler is required on the vintage machine.
Fonts are original XT Pixels, MIT licensed: WINXT\FONTLIC.TXT and FONTINFO.TXT.
Only CGA.GR2 requires a matching owned support file. Static logo and fonts are original.
This does not remove Windows itself or other non-font Windows dependencies.

1. At plain DOS with the disk selected, run INSTALL from the disk root.
2. PREPXT searches Windows and SYSTEM for the owned non-font grabber.
   If missing, supply a media directory: INSTALL D:\WIN30SRC
   Seven original fonts, four drivers, XTMODE and the unchanged shell are expanded
   by the bounded DOS helper. No Windows font files or local derivation are
   needed. Up to four owned-media directories may be supplied.
3. After source checks, confirm the helper prompt. It creates fresh C:\WINXT.
   It refuses existing output, wrong sizes, malformed compression, missing
   inputs and insufficient free space. Source Windows/media remain read-only.
   Default uses size/I/O/structural checks. Source-coupled diagnostic default
   measured zero SHA blocks in both phases and zero output readback. Production
   default separately passed exact native output checks. Emulator times were
   about 42 seconds default and 139 seconds /VERIFY, not hardware estimates.
   /VERIFY stays explicit, expensive developer diagnostics.
4. C: then CD \WINXT then INSTALL. In Windows Setup select Display -> Other
   display and source C:\WINXT; choose the mode and Complete Changes.
   For CONFIG.SYS choose option 3 (no changes). The optional Computer choice
   preserves the active Computer/keyboard. Read CPSET.TXT before changing it.
5. Start with C:\WINXT\WINXT. Its video/recovery guards remain mandatory.
   Optional desktop: C:\WINXT\TSSETUP. Existing Program Manager groups remain
   read-only. To switch later, exit Windows fully and use C:\WINXT\MODES.
   Run MODES and choose U to undo one prior mode. Read MODEINFO.TXT for recovery/limits.
   Windows Setup remains available via WINXT SETUP.

160-pixel menus can wrap and wide dialogs clip. Preserved font metrics do not
make every Windows dialog fit. Full native font and installation/rollback
acceptance passed; docs/QUAL/RC6.JSON binds native evidence and this release.
Documentation pins were refreshed on the host; measured executable code is unchanged.
Experimental TXTMODE is opt-in and retains its known renderer limitations.
The fixed TXTSYS font is original; font and renderer tests are separate.

The IMG is FAT12 720 KB: 737280 bytes, 80 cylinders, 2 heads, 9 sectors/track.
Use compatible GoTek/emulator/physical double-density media. A 360 KB-only
physical drive cannot read it. DOSBox-X: IMGMOUNT A WINXT720.IMG -T FLOPPY.
Do not run WINXT\INSTALL directly from a small/read-only floppy; PREPXT stages
it to writable C:\WINXT. Keep the source mounted throughout Setup.

Rollback: exit Windows and run the numbered WINXT\BACKUP\B001\RESTORE YES
path printed by INSTALL. It restores Computer metadata, disables the wave,
restores prior Windows files and verifies the restored originals. Added driver
files/helpers remain inactive. Do not redistribute a completed owned-media
folder containing CGA.GR2.
""")


def helper_payload():
    raw = read_file(HERE / 'HELPER.SHA').decode('ascii')
    expected = {}
    for line in raw.splitlines():
        digest, name = line.split()
        if not re.fullmatch('[a-f0-9]{64}', digest) or name in expected or '/' in name or '\\' in name:
            raise PackageError('Invalid helper manifest')
        expected[name] = digest
    if set(expected) != {'PREPXT.EXE', 'PREPXT.C', 'XTPINS.H', 'BUILD.BAT', 'SZSTREAM.H', 'PACKPINS.H', 'SZPACK.PY'}:
        raise PackageError('Helper manifest changed; review the explicit publication allowlist')
    data = {}
    for name, digest in expected.items():
        data[name] = read_file(HERE / name)
        if sha(data[name]) != digest:
            raise PackageError('Helper source/binary mismatch: ' + name)
    # Replay the document binding before carrying forward native acceptance.
    rebinder = load('verified_document_rebinding', HERE / 'DOCPINS' / 'REBIND.PY')
    rebuilt, proof = rebinder.bind(HERE / 'XTPINS.H')
    if rebuilt != data['PREPXT.EXE']:
        raise PackageError('Document binding differs from helper binary')
    if proof != json.loads(read_file(HERE / 'DOCPINS' / 'BIND.JSON')):
        raise PackageError('Document binding report differs from replay')
    native = json.loads(read_file(HERE / 'DOCPINS' / 'NATIVE.BIND.JSON'))
    for name in ('PREPXT.C', 'SZSTREAM.H', 'PACKPINS.H'):
        if sha(data[name]) != native['compiled_source_pins'][name]:
            raise PackageError('Measured native source changed: ' + name)
    return data


def document_pin_source_payload():
    """Include the reproducible host data binding and its measured base."""
    names = ('REBIND.PY', 'BASE.EXE', 'BASEPINS.H', 'BASE.MAP', 'BIND.JSON', 'NATIVE.BIND.JSON')
    return {'DOCPINS/' + n: read_file(HERE / 'DOCPINS' / n) for n in names}


def validate_helper_pins(payload, helper):
    entries = re.findall(r'\{"([A-Z0-9_.]+)","([0-9a-f]{64})",([0-9]+)UL,([012])\}',
                         helper['XTPINS.H'].decode('ascii'))
    expected = {n: h for h, n in (line.split() for line in payload['MANIFEST.SHA'].decode('ascii').splitlines())}
    expected['MANIFEST.SHA'] = sha(payload['MANIFEST.SHA'])
    if len(entries) != len(expected) or {e[0] for e in entries} != set(expected):
        raise PackageError('DOS helper pins do not cover the exact runtime')
    for name, digest, size, kind in entries:
        expected_kind = '1' if name in WINDOWS_NAMES else '0'
        if digest != expected[name] or kind != expected_kind:
            raise PackageError('DOS helper pin differs from runtime manifest: ' + name)
        if name in payload and int(size) != len(payload[name]):
            raise PackageError('DOS helper size differs from runtime: ' + name)


def disk_payload(payload, helper):
    """Transport packing only: installed names/expanded release pins stay exact."""
    packer = load('winxt_szpack', HERE / 'SZPACK.PY')
    rows = re.findall(r'\{"([A-Z0-9_.]+)","([A-Z0-9_.]+)","([0-9a-f]{64})",([0-9]+)UL\}',
                      helper['PACKPINS.H'].decode('ascii'))
    if len(rows) != 13 or {n:s for n,s,h,z in rows} != packer.PACKED_NAMES:
        raise PackageError('Packed transport allowlist changed')
    staged = dict(payload)
    for name, stored, digest, size in rows:
        packed = packer.pack(payload[name])
        if len(packed) != int(size) or sha(packed) != digest or stored in staged:
            raise PackageError('Packed transport differs from its reviewed pin: ' + name)
        del staged[name]
        staged[stored] = packed
    return staged

def transport_report(public, stored):
    packer = load('winxt_szreport', HERE / 'SZPACK.PY')
    return {name: {'stored_name': target, 'stored_bytes': len(stored[target]),
                  'stored_sha256': sha(stored[target]), 'expanded_bytes': len(public[name]),
                  'expanded_sha256': sha(public[name])}
            for name,target in packer.PACKED_NAMES.items()}


def install_batch():
    return dos('@ECHO OFF\nIF NOT EXIST WINXT\\TINST.EXE GOTO ROOT\n'
               'IF NOT EXIST PREPXT.EXE GOTO ROOT\n'
               'PREPXT WINXT C:\\WINDOWS %1 %2 %3 %4 %5\n'
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


CP_SOURCE_NAMES = {'BUILD.BAT', 'BUILD.TXT', 'CPSET.C', 'CPSET.TXT'}

def computer_source_payload():
    source = HERE / 'CPSET' if (HERE / 'CPSET').is_dir() else HERE.parent / 'CPSET'
    raw = read_file(source / 'FILES.SHA')
    manifest = {}
    for line in raw.decode('ascii').splitlines():
        digest, name = line.split()
        if name in manifest or not re.fullmatch('[a-f0-9]{64}', digest):
            raise PackageError('Invalid Computer source manifest')
        manifest[name] = digest
    if set(manifest) != CP_SOURCE_NAMES:
        raise PackageError('Computer source allowlist changed')
    data = {name:read_file(source / name) for name in sorted(manifest)}
    if any(sha(data[n]) != manifest[n] for n in data):
        raise PackageError('Computer source pin mismatch')
    data['FILES.SHA'] = raw
    return {'CPSET/' + name:content for name,content in data.items()}


MODE_SOURCE_NAMES = {'BUILD.BAT', 'GENPINS.PY', 'LICENSE.TXT', 'PAYLOADS.JSN',
    'README.TXT', 'TESTCOPY.PY', 'TESTHOST.PY', 'TESTLAUN.PY', 'XTMODE.C',
    'XTPINS.H', 'QUERY.ASM', 'WINQUERY.C', 'WINQUERY.DEF', 'DOSGUARD.C',
    'WINGUARD.C', 'WINGUARD.DEF'}

def mode_source_payload():
    source = HERE / 'XTMODE' if (HERE / 'XTMODE').is_dir() else HERE.parent / 'XTMODE'
    raw = read_file(source / 'FILES.SHA')
    manifest = {}
    for line in raw.decode('ascii').splitlines():
        digest, name = line.split()
        if name in manifest or not re.fullmatch('[a-f0-9]{64}', digest):
            raise PackageError('Invalid mode source manifest')
        manifest[name] = digest
    if set(manifest) != MODE_SOURCE_NAMES:
        raise PackageError('Mode source allowlist changed')
    data = {name:read_file(source / name) for name in sorted(manifest)}
    if any(sha(data[n]) != manifest[n] for n in data):
        raise PackageError('Mode source pin mismatch')
    data['FILES.SHA'] = raw
    return {'XTMODE/' + name:content for name,content in data.items()}


FONT_SOURCE_NAMES = {'BUILD.PY', 'GLYPHS.PY', 'CONTRACT.JSON', 'INSPECT.PY',
    'ALIAS.PY', 'HOST.PY', 'LICENSE', 'README.MD'}

def font_source_payload():
    source = HERE / 'XTFONTS' if (HERE / 'XTFONTS').is_dir() else HERE.parent / 'XTFONTS'
    raw = read_file(source / 'FILES.SHA')
    manifest = {}
    for line in raw.decode('ascii').splitlines():
        digest, name = line.split()
        if name in manifest or not re.fullmatch('[a-f0-9]{64}', digest):
            raise PackageError('Invalid font source manifest')
        manifest[name] = digest
    if set(manifest) != FONT_SOURCE_NAMES:
        raise PackageError('Font source allowlist changed')
    data = {name:read_file(source / name) for name in sorted(manifest)}
    if any(sha(data[n]) != manifest[n] for n in data):
        raise PackageError('Font source pin mismatch')
    data['FILES.SHA'] = raw
    return {'XTFONTS/' + name:content for name,content in data.items()}


def build(runtime, out, windows_files=None):
    if windows_files is not None:
        raise PackageError('Complete own-media payload does not fit the 720 KB disk; '
                           '--windows-files is unsupported. Build the public image and '
                           'use PREPXT with your matching Windows media to prepare C:\\WINXT '
                           'on the DOS hard disk. No output was created.')
    if out.exists():
        raise PackageError('Output exists; choose a fresh directory')
    wave = wave_payload()
    computer_source = computer_source_payload()
    mode_source = mode_source_payload()
    font_source = font_source_payload()
    payload = public_payload(runtime)
    public = dict(payload)
    private = windows_files is not None
    helper = helper_payload()
    validate_helper_pins(public, helper)
    payload = disk_payload(public, helper)
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
            entries.update(computer_source)
            entries.update(mode_source)
            entries.update(font_source)
            entries.update(document_pin_source_payload())
            entries.update(helper)
            entries['HELPER.SHA'] = read_file(HERE / 'HELPER.SHA')
            entries['README.TXT'] = guide
            write_zip(out / 'WXTTOOLS.ZIP', entries)
        metadata = {'schema': 1, 'fonts_are_original': True, 'native_package_qualified': False, 'publication_allowed': False,
            'native_implementation_qualified': True, 'documentation_pin_refresh_verified': True,
            'refreshed_binary_rerun_in_guest': False,
            'qualification_scope': 'Measured native implementation; host-verified document pin refresh. See QUALIFICATION.JSON.',
            'documentation_binding_sha256': sha(read_file(HERE / 'DOCPINS' / 'BIND.JSON')),
            'kind': 'private-own-media' if private else 'dos-mode-switcher-test-candidate',
            'binary_policy': 'accepted base payloads plus reviewed rebuilt helper/installer and original fonts',
            'independent_startup_default': 'slow-flag-wave',
            'disk_setup_startup': 'guarded-color-wave-static-fallback',
            'wave_payload_sha256': {n: sha(b) for n,b in wave.items()},
            'computer_source_sha256': {n: sha(b) for n,b in computer_source.items()},
            'mode_source_sha256': {n: sha(b) for n,b in mode_source.items()},
            'font_source_sha256': {n: sha(b) for n,b in font_source.items()},
            'runtime_manifest_sha256': sha(public['MANIFEST.SHA']),
            'packed_transport': transport_report(public, payload),
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
    parser.add_argument('--windows-files', type=Path, help='Unsupported complete private 720 KB image; use public image + DOS PREPXT instead')
    args = parser.parse_args()
    try:
        report = build(args.runtime, args.out, args.windows_files)
    except (PackageError, OSError, ValueError) as error:
        parser.exit(1, 'Refused: ' + str(error) + '\n')
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == '__main__':
    main()
