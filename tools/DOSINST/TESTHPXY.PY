"""Current HPXY qualification rejects stale bytes and incomplete native proof."""
from pathlib import Path
import copy
import importlib.machinery
import json
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
M = importlib.machinery.SourceFileLoader('test_hpxy_gate', str(HERE / 'HPXY.PY')).load_module()
P = importlib.machinery.SourceFileLoader('test_hpxy_publisher', str(HERE / 'RCPUB.PY')).load_module()


class CurrentHPXY(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.entries = P.expanded_entries()
        cls.archive = P.pub.zip_bytes(cls.entries)
        cls.inherited = json.loads((M.ROOT / 'docs/QUAL/WDESK/PACKAGE.JSN').read_bytes())
        cls.expanded = json.loads((M.ROOT / 'docs/QUAL/DOSINST/EXPAND.JSN').read_bytes())
        cls.receipt = M.QUAL / 'PACKAGE.JSN'
        cls.q = json.loads(cls.receipt.read_bytes())

    def qualify(self, q=None, entries=None, archive=None):
        read = Path.read_bytes
        def patched(path):
            if path == self.receipt and q is not None:
                return json.dumps(q).encode('ascii')
            return read(path)
        with patch.object(Path, 'read_bytes', patched):
            return M.qualify(entries or self.entries,
                             archive or self.archive, self.inherited, self.expanded)

    def test_exact_normal_package(self):
        self.assertEqual(self.qualify()['status'], 'PASS_CANONICAL_HPXY_PACKAGE')

    def test_incomplete_native_or_wrong_installed_bytes(self):
        for name in ('fresh', 'update', 'drivers_only'):
            for field in ('complete', 'owned_stopped', 'lease_released'):
                q = copy.deepcopy(self.q)
                q['native'][name][field] = False
                with self.assertRaises(ValueError):
                    self.qualify(q)
        for field in ('installed_driver', 'installed_helper'):
            q = copy.deepcopy(self.q)
            q['native']['update'][field]['sha256'] = '0' * 64
            with self.assertRaises(ValueError):
                self.qualify(q)

    def test_preparation_alone_cannot_qualify_full_finisher(self):
        q = copy.deepcopy(self.q)
        q['native']['update']['full_finisher_complete'] = False
        with self.assertRaisesRegex(ValueError, 'full finisher'):
            self.qualify(q)

    def test_native_input_identity_cannot_be_restamped(self):
        q = copy.deepcopy(self.q)
        q['native']['fresh']['tested_inputs']['SETUP.EXE']['sha256'] = '0' * 64
        with self.assertRaisesRegex(ValueError, 'native inputs'):
            self.qualify(q)

    def test_application_repaint_and_return_required(self):
        for field in ('paintbrush_repaint_and_pan', 'normal_dos_return'):
            q = copy.deepcopy(self.q)
            q['native']['drivers_only'][field] = False
            with self.assertRaisesRegex(ValueError, 'Windows acceptance'):
                self.qualify(q)

    def test_installed_helper_steps_required(self):
        q = copy.deepcopy(self.q)
        q['native']['drivers_only']['helper_check']['installed_helper_steps_verified'] = False
        with self.assertRaisesRegex(ValueError, 'XYCTL step acceptance'):
            self.qualify(q)

    def test_unrelated_member_change_even_with_restamped_archive_is_refused(self):
        entries = dict(self.entries)
        entries['WINXT/SOUND.DRV'] += b'changed'
        archive = P.pub.zip_bytes(entries)
        q = copy.deepcopy(self.q)
        q['archive'] = M.identity(archive)
        q['files'] = {n: M.identity(b) for n, b in sorted(entries.items())}
        with self.assertRaisesRegex(ValueError, 'Unexpected canonical'):
            self.qualify(q, entries, archive)

    def test_stale_source_binding_and_raw_receipt_are_refused(self):
        q = copy.deepcopy(self.q)
        next(iter(q['sources'].values()))['sha256'] = '0' * 64
        with self.assertRaisesRegex(ValueError, 'source differs'):
            self.qualify(q)
        q = copy.deepcopy(self.q)
        q['native']['drivers_only']['extra_unverified_claim'] = True
        with self.assertRaisesRegex(ValueError, 'raw result differs'):
            self.qualify(q)


if __name__ == '__main__':
    unittest.main()
