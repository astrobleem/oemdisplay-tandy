"""Verify both real accepted packets and support-integration refusals."""
import importlib.machinery
from pathlib import Path
import tempfile
import unittest
import zipfile

HERE = Path(__file__).resolve().parent
P = importlib.machinery.SourceFileLoader('yampack_tests', str(HERE / 'PACK.PY')).load_module()

class Packets(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='yampack-')
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)

    def build(self, profile='pc1', name='packet', accepted=None, grabber=None):
        out = self.base / name
        P.build(profile, out, accepted, grabber)
        return out / P.PROFILES[profile][2]

    def test_both_packets_include_exact_support_and_unchanged_driver(self):
        for profile in P.PROFILES:
            path = self.build(profile, profile)
            record = P.verify(profile, path.read_bytes())
            self.assertEqual(record['external_support_inputs'], [])
            self.assertIn('XTSTATIC.LGO', record['files'])
            self.assertNotIn('CGALOGO.LGO', record['files'])
            self.assertEqual(record['native_test'], 'not asserted by host packaging')

    def test_reproducible_packet_and_expanded_grabber_match(self):
        compressed = (P.ROOT / 'CGA.GR2').read_bytes()
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
        good = (P.ROOT / 'CGA.GR2').read_bytes()
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

if __name__ == '__main__':
    unittest.main()
