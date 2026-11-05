"""Test current ColorPlus composition with isolated historical/native fixtures."""
from pathlib import Path
import hashlib
import importlib.machinery
import io
import json
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock
import zipfile

M = importlib.machinery.SourceFileLoader('current_overlay_test', str(Path(__file__).with_name('CURRENT.PY'))).load_module()


def identity(data):
    return {'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}


def archive(files):
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, 'w', zipfile.ZIP_STORED) as zipped:
        for name, data in sorted(files.items()):
            info = zipfile.ZipInfo(name, (1980, 1, 1, 0, 0, 0))
            info.create_system = 0
            info.external_attr = 0x20
            zipped.writestr(info, data)
    return stream.getvalue()


def members(data):
    with zipfile.ZipFile(io.BytesIO(data)) as zipped:
        return {name: zipped.read(name) for name in zipped.namelist()}


class Composition(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / 'tools/CPPACK').mkdir(parents=True)
        self.guide = (b'Installation instructions.\r\n'
                      b'Existing fixed-driver and grabber bytes remain intact.\r\n'
                      b'Keep the whole packet and its notices.\r\nEnd of guide.\r\n')
        self.expected_guide = (b'Installation instructions.\r\n'
            b'Existing panning-driver and grabber bytes remain intact.\r\n'
            b'The fixed 320x200 driver includes the qualified ellipse/COPY optimization.\r\n'
            b'One narrow-drawing test measured 110 ms over 20,000 calls (about 0.14%)\r\n'
            b'slower than the prior fixed driver. Panning helpers are unchanged.\r\n'
            b'Keep the whole packet and its notices.\r\nEnd of guide.\r\n')
        names = ('CGA.GR2 CGACTL.EXE CPPAN.DRV CPWIN.BAT FONTLIC.TXT INSTALL.BAT '
                 'LICENSE.TXT LOGOLIC.TXT NOTICE.TXT OEMSETUP.INF OWATCOM.TXT '
                 'PAN.EXE PANCFG.EXE PANCTL.EXE PANINST.EXE PANKEY.DLL WXTSPL01.RLE '
                 'XTEFIX.FON XTEOEM.FON XTESYS.FON XTPAN.EXE XTSTATIC.LGO XYCTL.EXE').split()
        self.before = {name: ('unchanged ' + name).encode('ascii') for name in names}
        self.before.update({'PCP3216.DRV': b'accepted prior fixed driver', 'INSTALL.TXT': self.guide})
        self.driver = b'qualified optimized fixed driver'
        self.proof = {'driver': identity(self.driver), 'physical_hardware_qualified': False}
        self.fixed = SimpleNamespace(verify_profile=mock.Mock(return_value=self.proof),
                                     exact=mock.Mock(return_value=self.driver))
        self.prior = SimpleNamespace(identity=identity, C=SimpleNamespace(members=members, archive=archive),
                                     products=mock.Mock())
        self.record = {'optimized': {'profiles': {'colorplus32016': {'driver': {
            'path': 'PAYLOAD/CPFAST.DRV', 'identity': identity(self.driver)}}}}}
        self.set_base(self.before)

    def save_record(self):
        (self.root / 'tools/CPPACK/QUALIFY.JSN').write_bytes(json.dumps(self.record).encode('ascii'))

    def set_base(self, files):
        self.base = archive(files)
        self.prior.products.return_value = ({'historical': True}, {'CPPAN.ZIP': self.base})
        self.record['optimized']['colorplus_panning_base'] = identity(self.base)
        self.save_record()

    def invoke(self, function, *args):
        def load(name, path):
            if path == 'experiments/DGSCOPY/VERIFY.PY':
                return self.fixed
            if path == 'tools/PAN/PUBLISH.PY':
                return self.prior
            raise AssertionError('Unexpected composition dependency: ' + path)
        with mock.patch.object(M, 'ROOT', self.root), mock.patch.object(M, 'load', side_effect=load):
            return function(*args)

    def test_exact_driver_and_derived_guide_only(self):
        outputs, proof = self.invoke(M.qualified)
        after = members(outputs['CPPAN.ZIP'])
        self.assertEqual(set(after), set(self.before))
        self.assertEqual(len(after), 25)
        self.assertEqual({name for name in after if after[name] != self.before[name]}, {'PCP3216.DRV', 'INSTALL.TXT'})
        self.assertEqual(sum(after[name] == self.before[name] for name in after), 23)
        self.assertEqual(after['PCP3216.DRV'], self.driver)
        self.assertEqual(after['INSTALL.TXT'], self.expected_guide)
        self.assertEqual(outputs['INSTALL.TXT'], self.expected_guide)
        self.assertEqual(proof, self.proof)
        self.fixed.verify_profile.assert_called_once_with('colorplus32016')
        self.fixed.exact.assert_called_once_with(self.record['optimized']['profiles']['colorplus32016']['driver'])

    def test_outputs_returns_exact_composition(self):
        outputs = self.invoke(M.outputs)
        self.assertEqual(set(outputs), {'CPPAN.ZIP', 'INSTALL.TXT'})
        self.assertEqual(outputs['INSTALL.TXT'], self.expected_guide)

    def test_verify_accepts_exact_composition(self):
        outputs = self.invoke(M.outputs)
        self.assertEqual(self.invoke(M.verify, outputs['CPPAN.ZIP']), self.proof)

    def test_verify_rejects_helper_guide_driver_or_inventory_edits(self):
        files = members(self.invoke(M.outputs)['CPPAN.ZIP'])
        mutations = [('PANCFG.EXE', b'changed settings'), ('INSTALL.TXT', b'arbitrary guide'),
                     ('PCP3216.DRV', b'wrong fixed driver'), ('EXTRA.TXT', b'new member')]
        for name, data in mutations:
            with self.subTest(member=name):
                changed = dict(files)
                changed[name] = data
                with self.assertRaisesRegex(ValueError, 'driver/guide overlay'):
                    self.invoke(M.verify, archive(changed))

    def test_wrong_panning_base_identity_is_rejected(self):
        self.record['optimized']['colorplus_panning_base']['bytes'] += 1
        self.save_record()
        with self.assertRaisesRegex(ValueError, 'Accepted current panning kit differs'):
            self.invoke(M.qualified)

    def test_missing_fixed_member_is_rejected(self):
        files = dict(self.before)
        del files['PCP3216.DRV']
        self.set_base(files)
        with self.assertRaisesRegex(ValueError, 'fixed driver differs from executed qualification'):
            self.invoke(M.qualified)

    def test_wrong_native_identity_is_rejected(self):
        self.fixed.verify_profile.return_value = {'driver': identity(b'other executed driver')}
        with self.assertRaisesRegex(ValueError, 'fixed driver differs from executed qualification'):
            self.invoke(M.qualified)

    def test_wrong_payload_identity_is_rejected(self):
        self.fixed.exact.return_value = b'unqualified payload'
        with self.assertRaisesRegex(ValueError, 'fixed driver differs from executed qualification'):
            self.invoke(M.qualified)

    def test_native_qualification_failure_is_not_bypassed(self):
        self.fixed.verify_profile.side_effect = ValueError('native qualification failed')
        with self.assertRaisesRegex(ValueError, 'native qualification failed'):
            self.invoke(M.qualified)
        self.prior.products.assert_not_called()

    def test_historical_panning_failure_is_not_bypassed(self):
        self.prior.products.side_effect = ValueError('historical panning failed')
        with self.assertRaisesRegex(ValueError, 'historical panning failed'):
            self.invoke(M.qualified)

    def test_changed_or_duplicated_guide_patterns_are_rejected(self):
        old = b'Existing fixed-driver and grabber bytes remain intact.'
        marker = b'Keep the whole packet and its notices.'
        cases = [self.guide.replace(old, b'changed claim'), self.guide + old,
                 self.guide.replace(marker, b'changed insertion'), self.guide + marker]
        for guide in cases:
            with self.subTest(guide=guide):
                self.set_base(dict(self.before, **{'INSTALL.TXT': guide}))
                with self.assertRaisesRegex(ValueError, 'guide changed|insertion point changed'):
                    self.invoke(M.qualified)


if __name__ == '__main__':
    unittest.main()
