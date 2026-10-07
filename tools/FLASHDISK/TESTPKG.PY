#!/usr/bin/env python3
"""Verify the public release allowlist, pinned bytes, FAT12 and reproducibility."""
import argparse
import importlib.machinery
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
import zipfile

HERE = Path(__file__).resolve().parent
loader = importlib.machinery.SourceFileLoader('winxt_package', str(HERE / 'MAKEIMG.PY'))
spec = importlib.util.spec_from_loader(loader.name, loader)
package = importlib.util.module_from_spec(spec)
loader.exec_module(package)
RUNTIME = HERE.parents[1] / 'distributions' / 'WINXT'
OUTPUT_NAMES = {'WINXT720.IMG', 'WINXT720.ZIP', 'WXTTOOLS.ZIP',
                'README.TXT', 'BUILD.JSON', 'SHA256SUMS'}


def check(condition, message):
    if not condition:
        raise package.PackageError(message)


def zip_entries(path):
    with zipfile.ZipFile(path) as archive:
        entries = archive.infolist()
        names = [p.filename for p in entries]
        check(names == sorted(set(names)) and not archive.comment, 'ZIP order/duplicates/comment')
        for info in entries:
            check(info.date_time == (1980, 1, 1, 0, 0, 0) and info.create_system == 0
                  and info.external_attr == 0x20 and info.compress_type == zipfile.ZIP_STORED
                  and not info.extra and not info.comment and not info.flag_bits
                  and info.file_size <= 1048576, 'ZIP metadata or oversized entry')
        return {i.filename: archive.read(i) for i in entries}


def verify(out, runtime=RUNTIME):
    check(out.is_dir() and not out.is_symlink(), 'Invalid artifact directory')
    check({p.name for p in out.iterdir()} == OUTPUT_NAMES, 'Unexpected public output files')
    data = {p.name: package.read_file(p) for p in out.iterdir()}
    expected_sha = ''.join(package.sha(data[n]) + '  ' + n + '\n'
                           for n in sorted(OUTPUT_NAMES - {'SHA256SUMS'}))
    check(data['SHA256SUMS'] == expected_sha.encode(), 'Artifact SHA256 list mismatch')
    expected = {'WINXT/' + name: content for name, content in package.public_payload(runtime).items()}
    helper = package.helper_payload()
    package.validate_helper_pins(package.public_payload(runtime), helper)
    guide = package.readme(False)
    expected.update({'README.TXT': guide, 'INSTALL.BAT': package.install_batch(),
                     'PREPXT.EXE': helper['PREPXT.EXE']})
    fat = package.load('verify_public_fat', HERE / 'FAT12.PY')
    actual = fat.verify_image(out / 'WINXT720.IMG')
    check(actual['size_kb'] == 720 and actual['directories'] == ['WINXT'], 'Wrong disk geometry/layout')
    check(actual['files'] == {n: {'size': len(b), 'sha256': package.sha(b)}
                              for n, b in sorted(expected.items())}, 'Disk bytes/allowlist mismatch')
    check(data['README.TXT'] == guide, 'Release instructions mismatch')
    check(zip_entries(out / 'WINXT720.ZIP') == {'WINXT720.IMG': data['WINXT720.IMG'],
                                               'README.TXT': guide}, 'Download ZIP mismatch')
    toolkit = {'WINXT/' + n: b for n, b in package.public_payload(runtime).items()}
    toolkit['WINXT/STAGE.PY'] = package.read_file(runtime / 'STAGE.PY')
    toolkit.update({n: package.read_file(HERE / n) for n in ('MAKEIMG.PY', 'FAT12.PY')})
    toolkit.update(helper)
    toolkit['HELPER.SHA'] = package.read_file(HERE / 'HELPER.SHA')
    toolkit['README.TXT'] = guide
    check(zip_entries(out / 'WXTTOOLS.ZIP') == toolkit, 'Portable toolkit mismatch')
    metadata = json.loads(data['BUILD.JSON'])
    check(metadata['publication_allowed'] is True and metadata['windows_support_included'] is False
          and metadata['kind'] == 'public-support-free', 'PRIVATE OUTPUT MUST NOT BE PUBLISHED')
    check(metadata['fat_verification'] == actual, 'Build report differs from verified disk')
    check(metadata['runtime_manifest_sha256'] == package.sha(package.public_payload(runtime)['MANIFEST.SHA']),
          'Runtime provenance mismatch')
    check(metadata['helper_sha256'] == package.sha(helper['PREPXT.EXE']), 'Helper provenance mismatch')
    return actual


class PackageTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='winxt-package-test-')
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)

    def test_windowsxt_is_the_only_current_splash(self):
        payload = package.public_payload(RUNTIME)
        expected = 'eec3a413bb776bea8eccb19a379428d15f06cbdc0ac41b0871345ff9c24caf1c'
        self.assertEqual(package.sha(payload['WXTSPL01.RLE']), expected)
        self.assertEqual(len(payload['WXTSPL01.RLE']), 4062)
        self.assertNotIn('TNDYLOGO.RLE', payload)
        self.assertIn(b'WXTSPL01.RLE', payload['TINST.EXE'])
        self.assertNotIn(b'TNDYLOGO.RLE', payload['TINST.EXE'])
        for source in ['WXTSPL01.RLE', 'ART/assets/WXTSPL01.RLE']:
            self.assertEqual((HERE.parents[1] / 'examples/WXTSPL' / source).read_bytes(), payload['WXTSPL01.RLE'])
        stage = package.load('xt_default_stage', RUNTIME / 'STAGE.PY')
        stage.verify_default_splash(payload)
        self.assertEqual(stage.SPLASH_SHA, expected)

    def test_retired_art_rejected_despite_repaired_manifest(self):
        runtime = self.base / 'runtime'
        shutil.copytree(RUNTIME, runtime)
        (runtime / 'WXTSPL01.RLE').write_bytes((HERE.parents[1] / 'src/splash/assets/TNDYLOGO.RLE').read_bytes())
        manifest = []
        for line in (runtime / 'MANIFEST.SHA').read_text().splitlines():
            digest, name = line.split()
            if name == 'WXTSPL01.RLE': digest = package.sha((runtime / name).read_bytes())
            manifest.append(digest + '  ' + name)
        (runtime / 'MANIFEST.SHA').write_bytes(package.dos('\n'.join(manifest) + '\n'))
        with self.assertRaisesRegex(package.PackageError, 'approved Windows XT'):
            package.build(runtime, self.base / 'out')
        self.assertFalse((self.base / 'out').exists())

    def test_setup_cannot_select_retired_or_missing_splash(self):
        payload = package.public_payload(RUNTIME)
        stage = package.load('xt_selection_stage', RUNTIME / 'STAGE.PY')
        original = payload['OEMSETUP.INF']
        display = [line for line in original.splitlines(keepends=True) if b'= a:' in line]
        self.assertEqual(len(display), 6)
        bad = [original.replace(b'a:WXTSPL01.RLE', b'a:TNDYLOGO.RLE', 1),
               original.replace(display[0], b''), original + b'\r\n[display]\r\n' + display[0]]
        for inf in bad:
            changed = dict(payload); changed['OEMSETUP.INF'] = inf
            with self.assertRaises(package.PackageError): package.verify_default_splash(changed)
            with self.assertRaises(stage.DiskError): stage.verify_default_splash(changed)
        for art in [b'', (HERE.parents[1] / 'src/splash/assets/TNDYLOGO.RLE').read_bytes()]:
            changed = dict(payload); changed['WXTSPL01.RLE'] = art
            with self.assertRaises(stage.DiskError): stage.verify_default_splash(changed)

    def test_reproducible_public_disk_and_exact_allowlist(self):
        a, b = self.base / 'one', self.base / 'two'
        package.build(RUNTIME, a)
        package.build(RUNTIME, b)
        verified = verify(a)
        verify(b)
        for name in OUTPUT_NAMES:
            self.assertEqual((a / name).read_bytes(), (b / name).read_bytes(), name)
        self.assertEqual(verified['image_bytes'], 737280)
        for forbidden in package.WINDOWS_NAMES:
            self.assertNotIn('WINXT/' + forbidden, verified['files'])

    def test_portable_toolkit_reproduces_public_outputs(self):
        a, portable, b = self.base / 'one', self.base / 'toolkit', self.base / 'two'
        package.build(RUNTIME, a)
        portable.mkdir()
        entries = zip_entries(a / 'WXTTOOLS.ZIP')
        for name, data in entries.items():
            path = portable / name
            path.parent.mkdir(exist_ok=True)
            path.write_bytes(data)
        subprocess.run([sys.executable, str(portable / 'MAKEIMG.PY'), '--out', str(b)],
                       check=True, capture_output=True, timeout=60)
        for name in OUTPUT_NAMES:
            self.assertEqual((a / name).read_bytes(), (b / name).read_bytes(), name)

    def test_preexisting_output_is_preserved(self):
        out = self.base / 'existing'
        out.mkdir()
        (out / 'USER.TXT').write_bytes(b'keep me')
        with self.assertRaises(package.PackageError):
            package.build(RUNTIME, out)
        self.assertEqual((out / 'USER.TXT').read_bytes(), b'keep me')

    def test_corrupt_runtime_refused_before_output(self):
        runtime = self.base / 'runtime'
        shutil.copytree(RUNTIME, runtime)
        (runtime / 'TR53216.DRV').write_bytes(b'wrong binary')
        with self.assertRaises(package.PackageError):
            package.build(runtime, self.base / 'out')
        self.assertFalse((self.base / 'out').exists())

    def test_added_manifest_entry_is_not_auto_published(self):
        runtime = self.base / 'runtime'
        shutil.copytree(RUNTIME, runtime)
        with (runtime / 'MANIFEST.SHA').open('ab') as output:
            output.write(b'0' * 64 + b'  PRIVATE.FON\r\n')
        with self.assertRaises(package.PackageError):
            package.build(runtime, self.base / 'out')
        self.assertFalse((self.base / 'out').exists())

    def test_extra_file_refused_by_publication_verifier(self):
        out = self.base / 'out'
        package.build(RUNTIME, out)
        (out / 'PRIVATE.IMG').write_bytes(b'do not publish')
        with self.assertRaises(package.PackageError):
            verify(out)

    def test_mutated_image_refused(self):
        out = self.base / 'out'
        package.build(RUNTIME, out)
        p = out / 'WINXT720.IMG'
        data = bytearray(p.read_bytes())
        data[-1] ^= 1
        p.write_bytes(data)
        with self.assertRaises(package.PackageError):
            verify(out)

    def test_private_metadata_refused_even_with_repaired_checksums(self):
        out = self.base / 'out'
        package.build(RUNTIME, out)
        p = out / 'BUILD.JSON'
        metadata = json.loads(p.read_bytes())
        metadata['publication_allowed'] = False
        metadata['windows_support_included'] = True
        p.write_bytes((json.dumps(metadata, sort_keys=True) + '\n').encode())
        hashes = ''.join(package.sha((out / n).read_bytes()) + '  ' + n + '\n'
                         for n in sorted(OUTPUT_NAMES - {'SHA256SUMS'}))
        (out / 'SHA256SUMS').write_bytes(hashes.encode())
        with self.assertRaisesRegex(package.PackageError, 'PRIVATE'):
            verify(out)

    def test_extra_helper_manifest_entry_refused(self):
        fake = self.base / 'helper'
        fake.mkdir()
        raw = package.read_file(HERE / 'HELPER.SHA') + b'0' * 64 + b'  PRIVATE.FON\r\n'
        (fake / 'HELPER.SHA').write_bytes(raw)
        with mock.patch.object(package, 'HERE', fake):
            with self.assertRaisesRegex(package.PackageError, 'allowlist'):
                package.helper_payload()

    def test_stale_dos_pins_refused(self):
        helper = package.helper_payload()
        helper['XTPINS.H'] = helper['XTPINS.H'].replace(b'651008UL', b'1UL')
        # Mutate one public runtime size without changing its filename/hash.
        old_size = str(len(package.public_payload(RUNTIME)['TINST.EXE'])).encode() + b'UL,0'
        self.assertIn(old_size, helper['XTPINS.H'])
        helper['XTPINS.H'] = helper['XTPINS.H'].replace(old_size, b'1UL,0')
        with self.assertRaisesRegex(package.PackageError, 'size differs'):
            package.validate_helper_pins(package.public_payload(RUNTIME), helper)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--verify', type=Path)
    args, remaining = parser.parse_known_args()
    if args.verify:
        result = verify(args.verify)
        print('Verified PUBLIC 720 KB image, exact files, ZIPs, pins and checksums.')
        print('Free bytes:', result['free_bytes'])
    else:
        unittest.main(argv=[sys.argv[0]] + remaining)
