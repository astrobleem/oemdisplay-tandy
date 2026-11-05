"""Verify historical Yamaha preservation and qualified B800 overlay refusals."""
import copy
import importlib.machinery
import json
from pathlib import Path
import tempfile
import time
import unittest
from unittest import mock
import zipfile

HERE = Path(__file__).resolve().parent
P = importlib.machinery.SourceFileLoader('yampack_tests', str(HERE / 'PACK.PY')).load_module()



def compressed_grabber():
    raw = (P.ROOT / 'distributions/WINXT/CGA.GR2').read_bytes()
    body = b''.join(bytes([(1 << len(raw[i:i+8])) - 1]) + raw[i:i+8]
                    for i in range(0, len(raw), 8))
    return b'SZDD\x88\xf0\x27\x33A\x00' + len(raw).to_bytes(4, 'little') + body

class Packets(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Bind real evidence once for isolated packet/refusal fixtures. Production
        # PACK.PY remains uncached and is exercised separately below.
        cls.production_binding = staticmethod(P.native_binding)
        started = time.monotonic()
        cls.binding = cls.production_binding()
        print('REAL_BINDING_SECONDS=%.3f' % (time.monotonic() - started), flush=True)

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='yampack-')
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        binding = mock.patch.object(P, 'native_binding',
                                    side_effect=lambda: copy.deepcopy(self.binding))
        binding.start()
        self.addCleanup(binding.stop)

    def build(self, profile='pc1', name='packet', accepted=None, grabber=None):
        out = self.base / name
        P.build(profile, out, accepted, grabber)
        return out / P.PROFILES[profile][2]

    def test_unmocked_production_build_rechecks_current_evidence(self):
        started = time.monotonic()
        with mock.patch.object(P, 'native_binding', self.production_binding):
            path = self.build('b800', 'unmocked-production')
        with zipfile.ZipFile(path) as z:
            self.assertEqual(P.identity(z.read('YAM160.DRV')), self.binding['driver'])
        print('UNMOCKED_BUILD_SECONDS=%.3f' % (time.monotonic() - started), flush=True)

    def test_both_packets_include_exact_support_and_bound_driver(self):
        for profile in P.PROFILES:
            path = self.build(profile, profile)
            record = P.verify(profile, path.read_bytes())
            self.assertEqual(record['external_support_inputs'], [])
            self.assertIn('XTSTATIC.LGO', record['files'])
            self.assertNotIn('CGALOGO.LGO', record['files'])
            self.assertEqual(record['native_test'], 'not asserted by host packaging')
            self.assertEqual(record['files'][P.PROFILES[profile][0]], P.driver_pin(profile))

    def test_reproducible_packet_and_expanded_grabber_match(self):
        compressed = compressed_grabber()
        expanded = self.base / 'CGA.GR2'
        expanded.write_bytes(P.MEDIA.expanded_file(compressed, 'CGA.GR2'))
        for profile in P.PROFILES:
            a = self.build(profile, profile + 'a')
            b = self.build(profile, profile + 'b', grabber=expanded)
            self.assertEqual(a.read_bytes(), b.read_bytes())

    def test_mismatched_profile_and_wrong_driver_refused(self):
        for profile in P.PROFILES:
            path = self.build(profile, profile)
            other = 'b800' if profile == 'pc1' else 'pc1'
            with self.assertRaises(ValueError):
                P.verify(other, path.read_bytes())
        old = P.ROOT / 'downloads/experimental/yamaha-candidate03' / P.PROFILES['pc1'][3]
        with zipfile.ZipFile(old) as z:
            files = {n: z.read(n) for n in z.namelist()}
        files['PC1YAMA.DRV'] += b'changed'
        altered = self.base / 'BAD.ZIP'
        altered.write_bytes(P.archive(files))
        with self.assertRaisesRegex(ValueError, 'Accepted bytes differ'):
            self.build(name='bad-driver', accepted=altered)
        self.assertFalse((self.base / 'bad-driver').exists())

    def test_existing_output_refused_without_changes(self):
        path = self.build()
        before = path.read_bytes()
        with self.assertRaisesRegex(ValueError, 'must be new'):
            self.build()
        self.assertEqual(before, path.read_bytes())

    def test_malformed_grabber_refused_before_output(self):
        good = compressed_grabber()
        for index, data in enumerate([good[:13], good[:-1], good + b'trailing', b'wrong']):
            bad = self.base / ('BAD' + str(index))
            bad.write_bytes(data)
            name = 'bad-grabber' + str(index)
            with self.assertRaises(ValueError):
                self.build(name=name, grabber=bad)
            self.assertFalse((self.base / name).exists())

    def test_changed_selector_and_forged_native_claim_refused(self):
        path = self.build()
        with zipfile.ZipFile(path) as z:
            original = {n: z.read(n) for n in z.namelist()}
        for name, data in [('OEMSETUP.INF', original['OEMSETUP.INF'].replace(b'XTSTATIC.LGO', b'CGALOGO.LGO')),
                           ('MANIFEST.JSN', original['MANIFEST.JSN'].replace(b'not asserted by host packaging', b'PASS'))]:
            altered = dict(original)
            altered[name] = data
            altered['SHA256.SUM'] = P.checksum({n: b for n, b in altered.items() if n != 'SHA256.SUM'})
            with self.assertRaises(ValueError):
                P.verify('pc1', P.archive(altered))

    def test_extra_or_duplicate_members_refused(self):
        path = self.build()
        with zipfile.ZipFile(path) as z:
            files = {n: z.read(n) for n in z.namelist()}
        files['EXTRA.TXT'] = b'extra'
        with self.assertRaises(ValueError):
            P.verify('pc1', P.archive(files))
        with zipfile.ZipFile(path, 'a') as z:
            z.writestr('PC1YAMA.DRV', b'duplicate')
        with self.assertRaises(ValueError):
            P.verify('pc1', path.read_bytes())

    def test_historical_packets_remain_byte_exact(self):
        report = json.loads((P.ROOT / 'docs/yamaha/SUPPORT.JSN').read_bytes())
        with mock.patch.object(P, 'native_binding', side_effect=AssertionError('Historical path must not use optimized binding')):
            for profile, entry in report['profiles'].items():
                old = P.packet_bytes(profile, P.historical_files(profile))
                self.assertEqual(P.identity(old), entry['packet'])
                if profile == 'pc1':
                    current = self.build('pc1', 'pc1-byte-identity').read_bytes()
                    self.assertEqual(current, old)
                    self.assertEqual(current, (P.ROOT / entry['packet_path']).read_bytes())

    def test_b800_changes_only_driver_and_existing_generated_records(self):
        old = P.read_archive(P.packet_bytes('b800', P.historical_files('b800')),
                             P.SUPPORT | P.LICENSES | {'YAM160.DRV', 'OEMSETUP.INF', 'README.TXT',
                                                       'NOTICE.TXT', 'MANIFEST.JSN', 'SHA256.SUM'})
        current = P.read_archive(self.build('b800').read_bytes(), set(old))
        self.assertEqual({name for name in old if old[name] != current[name]},
                         {'YAM160.DRV', 'MANIFEST.JSN', 'SHA256.SUM'})
        self.assertEqual(P.identity(current['YAM160.DRV']), P.native_binding()['driver'])
        self.assertEqual(current['YAM160.DRV'], P.B800_PAYLOAD.read_bytes())

    def test_b800_historical_driver_checked_before_overlay(self):
        source = P.ROOT / 'downloads/experimental/yamaha-candidate03' / P.PROFILES['b800'][3]
        before = source.read_bytes()
        with zipfile.ZipFile(source) as z:
            files = {name: z.read(name) for name in z.namelist()}
        files['YAM160.DRV'] += b'changed'
        altered = self.base / 'BADBASE.ZIP'
        altered.write_bytes(P.archive(files))
        with mock.patch.object(P, 'qualified_b800', side_effect=AssertionError('Overlay must follow historical validation')):
            with self.assertRaisesRegex(ValueError, 'Accepted bytes differ: YAM160.DRV'):
                self.build('b800', 'bad-base', accepted=altered)
        self.assertFalse((self.base / 'bad-base').exists())
        self.assertEqual(source.read_bytes(), before)

    def test_missing_wrong_and_historical_overlay_refused_before_output(self):
        old = P.historical_files('b800')['YAM160.DRV']
        current = P.B800_PAYLOAD.read_bytes()
        for number, data in enumerate((None, old, bytes([current[0] ^ 1]) + current[1:], current + b'changed')):
            payload = self.base / ('BADOVER' + str(number) + '.DRV')
            if data is not None:
                payload.write_bytes(data)
            output = 'bad-overlay-' + str(number)
            with mock.patch.object(P, 'B800_PAYLOAD', payload):
                with self.assertRaises((OSError, ValueError)):
                    self.build('b800', output)
            self.assertFalse((self.base / output).exists())

    def test_unqualified_binding_refused_without_affecting_pc1(self):
        with mock.patch.object(P, 'native_binding', side_effect=ValueError('Unqualified optimized driver')):
            with self.assertRaisesRegex(ValueError, 'Unqualified optimized driver'):
                self.build('b800', 'unqualified')
            self.assertFalse((self.base / 'unqualified').exists())
            P.verify('pc1', self.build('pc1', 'independent-pc1').read_bytes())

    def test_rehashed_old_b800_driver_cannot_replace_optimized_payload(self):
        with zipfile.ZipFile(self.build('b800')) as z:
            files = {name: z.read(name) for name in z.namelist()}
        files['YAM160.DRV'] = P.historical_files('b800')['YAM160.DRV']
        record = json.loads(files['MANIFEST.JSN'])
        record['files']['YAM160.DRV'] = P.identity(files['YAM160.DRV'])
        files['MANIFEST.JSN'] = P.dos(json.dumps(record, indent=2, sort_keys=True) + '\n')
        files['SHA256.SUM'] = P.checksum({name: data for name, data in files.items() if name != 'SHA256.SUM'})
        with self.assertRaisesRegex(ValueError, 'Accepted bytes differ: YAM160.DRV'):
            P.verify('b800', P.archive(files))

    def test_recorded_native_setup_and_software_startup_remain_historical(self):
        report = json.loads((P.ROOT / 'docs/yamaha/SUPPORT.JSN').read_bytes())
        self.assertEqual(report['status'], 'PASS_NATIVE_SETUP_AND_SOFTWARE_STARTUP')
        self.assertFalse(report['physical_hardware_qualified'])
        self.assertFalse(report['actual_yamaha_scanout_qualified'])
        for name, pin in report['integration_sources'].items():
            relocation = report.get('source_relocations', {}).get(name)
            if relocation:
                self.assertEqual(relocation['native_snapshot'], pin)
                pin = relocation['current_source']
            if name == 'tools/YAMPACK/PACK.PY':
                # This record binds the old producer, not the newly qualified overlay.
                self.assertEqual(report['integration_sources'][name], {
                    'bytes': 6745, 'sha256': '3ab5d616f608de2bcc062cd37f4880a3053c32d8e23775a1988f336c3c06f101'})
                self.assertEqual(pin, {
                    'bytes': 6769, 'sha256': '57e3aef79b969d3e03e3328b467a6388018ae1e7fd87d012f01df629ccd8a1a8'})
            else:
                self.assertEqual(P.identity((P.ROOT / name).read_bytes()), pin, name)
        for profile, entry in report['profiles'].items():
            historical = P.packet_bytes(profile, P.historical_files(profile))
            self.assertEqual(P.identity(historical), entry['packet'])
            if profile == 'pc1':
                self.assertEqual(P.identity((P.ROOT / entry['packet_path']).read_bytes()), entry['packet'])
            self.assertEqual(entry['native_setup']['installed_support'][P.PROFILES[profile][0]],
                             {'bytes': P.PROFILES[profile][5], 'sha256': P.PROFILES[profile][4]})
            self.assertTrue(entry['source_fixture_unchanged_after_test'])
            for stage in ('native_setup', 'software_startup'):
                self.assertTrue(entry[stage]['complete'])
                self.assertTrue(entry[stage]['owned_stopped'])
                self.assertTrue(entry[stage]['lease_released'])
            self.assertTrue(all(entry['native_setup']['startup_logo_in_wincom'].values()))
            self.assertTrue(entry['software_startup']['returned_to_dos'])
            self.assertIn('SM_0=160\nSM_1=200\n', entry['software_startup']['metrics'])
            self.assertEqual(entry['native_setup']['selected_boot']['display.drv'], P.PROFILES[profile][0])

if __name__ == '__main__':
    unittest.main()
