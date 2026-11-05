"""Replay and closed-archive negatives; only private temporary fixtures are written."""
from pathlib import Path
import copy
import importlib.machinery
import io
import json
import stat
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock
import warnings
import zipfile

HERE = Path(__file__).resolve().parent
V = importlib.machinery.SourceFileLoader('fixed_replay_negative', str(HERE / 'VERIFY.PY')).load_module()


class Replay(unittest.TestCase):
    def setUp(self):
        self.record = json.loads(V.QUAL.read_bytes())

    def verify(self, profile='colorplus32016'):
        record = SimpleNamespace(read_bytes=lambda: json.dumps(self.record).encode('ascii'))
        with mock.patch.object(V, 'QUAL', record):
            return V.verify_profile(profile)

    def test_pen_include_is_bound(self):
        self.assertIn('experiments/DGSCOPY/PEN16/DISPLAY.INC', self.record['optimized']['sources'])

    def test_current_evidence_replays(self):
        for profile in V.PROFILES:
            with self.subTest(profile=profile):
                report = self.verify(profile)
                self.assertEqual(report['driver'], self.record['optimized']['profiles'][profile]['driver']['identity'])

    def test_missing_required_source_pin_is_rejected(self):
        del self.record['optimized']['sources']['experiments/DGSCOPY/N32016/TSOFT.ASM']
        with self.assertRaisesRegex(ValueError, 'Missing required fixed-driver source'):
            self.verify()

    def test_missing_shared_source_pin_is_rejected(self):
        del self.record['optimized']['sources']['src/tandysw/PORT8086.PY']
        with self.assertRaisesRegex(ValueError, 'Missing required fixed-driver source'):
            self.verify()

    def test_wrong_source_pin_is_rejected(self):
        self.record['optimized']['sources']['experiments/DGSCOPY/N32016/TSOFT.ASM']['bytes'] += 1
        with self.assertRaisesRegex(ValueError, 'Qualified source differs'):
            self.verify()

    def test_private_reference_claim_is_rejected(self):
        self.record['optimized']['profiles']['colorplus32016']['build']['private_reference_used'] = True
        with self.assertRaisesRegex(ValueError, 'Complete source reproduction is unqualified'):
            self.verify()

    def test_cube_qualification_claim_is_rejected(self):
        self.record['optimized']['cube_execution_qualified'] = True
        with self.assertRaisesRegex(ValueError, 'Current fixed-driver qualification incomplete'):
            self.verify()

    def test_missing_native_evidence_is_rejected(self):
        row = self.record['optimized']['profiles']['colorplus32016']['ellipse']['candidate']
        del row['files']['F00.BIN']
        with self.assertRaisesRegex(ValueError, 'Native evidence closure differs|Evidence archive member inventory differs'):
            self.verify()

    def test_wrong_executed_driver_is_rejected(self):
        row = self.record['optimized']['profiles']['colorplus32016']['ellipse']['candidate']
        row['driver']['bytes'] += 1
        with self.assertRaisesRegex(ValueError, 'Stopped-image driver readback differs'):
            self.verify()

    def test_incomplete_candidate_cleanup_is_rejected(self):
        row = self.record['optimized']['profiles']['colorplus32016']['ellipse']['candidate']
        row['owned_stopped'] = False
        with self.assertRaisesRegex(ValueError, 'Native run/cleanup incomplete'):
            self.verify()

    def test_mode_baseline_must_be_accepted_control(self):
        pair = self.record['optimized']['profiles']['yamaha160-b800']['mode']
        pair['baseline'] = copy.deepcopy(pair['candidate'])
        with self.assertRaisesRegex(ValueError, 'MODE control/candidate driver binding differs'):
            self.verify('yamaha160-b800')

    def test_unrecognized_probe_bytes_are_rejected(self):
        for kind in V.PROBES:
            with self.subTest(kind=kind), mock.patch.object(Path, 'read_bytes', return_value=b'wrong executable'):
                with self.assertRaisesRegex(ValueError, 'Executed native probe differs'):
                    V.probe(HERE, kind)

    def test_ellipse_profile_header_is_checked(self):
        original = V.values
        def altered(text, key):
            return [3] if key == 'PROFILE' else original(text, key)
        with mock.patch.object(V, 'values', side_effect=altered):
            with self.assertRaisesRegex(ValueError, 'Ellipse contract: PROFILE'):
                self.verify()

    def test_exact_link_response_not_only_object_count(self):
        original = V.exact
        def altered(row):
            body = original(row)
            return body.replace(b'BITBLT.OBJ', b'WRONG.OBJ') if row['path'].endswith('/LINK.LOG') else body
        with mock.patch.object(V, 'exact', side_effect=altered):
            with self.assertRaisesRegex(ValueError, 'exact31-module source response'):
                self.verify()

    def test_recorded_assembler_summaries_are_required(self):
        original = V.exact
        def altered(row):
            body = original(row)
            return body.replace(b'Severe  Errors', b'Unrecorded    ', 1) if row['path'].endswith('/MODULES.LOG') else body
        with mock.patch.object(V, 'exact', side_effect=altered):
            with self.assertRaisesRegex(ValueError, 'Recorded assembler error totals differ'):
                self.verify()


class EvidenceArchive(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.payloads = {}
        self.q = {'profiles': {}}
        for profile, label in [('colorplus32016', 'CPL'), ('yamaha160-b800', 'YAM')]:
            def run(name):
                folder = label + '/' + name
                files = {'EXECUTED.DRV': (folder + ' driver').encode(), 'F00.BIN': (folder + ' frame').encode()}
                self.payloads.update({folder + '/' + n: b for n, b in files.items()})
                return {'folder': V.EVIDENCE_PREFIX + folder,
                        'files': {n: V.identity(b) for n, b in files.items()},
                        'driver': V.identity(files['EXECUTED.DRV'])}
            p = {kind: {role: run(kind.upper() + '/' + role.upper()) for role in ('baseline', 'candidate')}
                 for kind in ('ellipse', 'rounded') + (('mode',) if profile == 'yamaha160-b800' else ())}
            p['setup'] = run('SETUP')
            control, log = label + '/CONTROL.DRV', label + '/BUILD/C6.LOG'
            self.payloads[control], self.payloads[log] = (label + ' control').encode(), b'build fixture'
            p['control_driver'] = {'path': V.EVIDENCE_PREFIX + control, 'identity': V.identity(self.payloads[control])}
            p['build'] = {'logs': [{'path': V.EVIDENCE_PREFIX + log, 'identity': V.identity(self.payloads[log])}]}
            self.q['profiles'][profile] = p
        self.archive_path = self.root / 'docs/pcp/OUTPUT/OPTIMIZED.ZIP'
        self.archive_path.parent.mkdir(parents=True)
        self.set_archive(self.payloads)
        self.cache = {}
        self.addCleanup(lambda: [temp.cleanup() for temp in self.cache.values()])
        for patch in (mock.patch.object(V, 'ROOT', self.root),
                      mock.patch.object(V, 'QUAL', SimpleNamespace(read_bytes=lambda: json.dumps({'optimized': self.q}).encode())),
                      mock.patch.object(V, '_evidence_cache', self.cache)):
            patch.start()
            self.addCleanup(patch.stop)

    def set_archive(self, files):
        stream = io.BytesIO()
        rows = files.items() if isinstance(files, dict) else files
        with warnings.catch_warnings():
            warnings.simplefilter('ignore', UserWarning)
            with zipfile.ZipFile(stream, 'w', zipfile.ZIP_STORED) as zipped:
                for name, data in rows:
                    zipped.writestr(name, data)
        data = stream.getvalue()
        self.archive_path.write_bytes(data)
        self.q['evidence_archive'] = {'path': 'docs/pcp/OUTPUT/OPTIMIZED.ZIP', 'identity': V.identity(data)}

    def test_exact_inventory_and_prefix_only_redirect(self):
        root = V.evidence_root()
        actual = {p.relative_to(root).as_posix(): p.read_bytes() for p in root.rglob('*') if p.is_file()}
        self.assertEqual(actual, self.payloads)
        name = next(iter(self.payloads))
        self.assertEqual(V.local(V.EVIDENCE_PREFIX + name), root / name)
        self.assertEqual(V.local('tools/CPPACK/PAYLOAD/CPFAST.DRV'), self.root / 'tools/CPPACK/PAYLOAD/CPFAST.DRV')
        self.assertEqual(V.local('docs/pcp/OUTPUT/OPTIMIZED-other/file'), self.root / 'docs/pcp/OUTPUT/OPTIMIZED-other/file')
        self.assertEqual(V.evidence_root(), root)
        self.assertEqual(len(self.cache), 1)

    def test_no_raw_folder_fallback(self):
        name = next(iter(self.payloads))
        raw = self.root / V.EVIDENCE_PREFIX / name
        raw.parent.mkdir(parents=True)
        raw.write_bytes(self.payloads[name])
        self.q['evidence_archive']['path'] = 'missing.zip'
        with self.assertRaisesRegex(ValueError, 'no raw-folder fallback'):
            V.local(V.EVIDENCE_PREFIX + name)

    def test_missing_archive_binding_is_rejected(self):
        del self.q['evidence_archive']
        with self.assertRaisesRegex(ValueError, 'Missing bound optimized evidence archive'):
            V.evidence_root()

    def test_corrupt_archive_identity_is_rejected(self):
        self.archive_path.write_bytes(self.archive_path.read_bytes() + b'changed')
        with self.assertRaisesRegex(ValueError, 'Evidence archive identity differs'):
            V.evidence_root()

    def test_cached_extraction_still_checks_transport_identity(self):
        V.evidence_root()
        self.archive_path.write_bytes(self.archive_path.read_bytes() + b'changed')
        with self.assertRaisesRegex(ValueError, 'Evidence archive identity differs'):
            V.evidence_root()

    def test_invalid_zip_with_matching_identity_is_rejected(self):
        self.archive_path.write_bytes(b'not a ZIP')
        self.q['evidence_archive']['identity'] = V.identity(b'not a ZIP')
        with self.assertRaisesRegex(ValueError, 'Unreadable bound evidence archive'):
            V.evidence_root()

    def test_extra_member_is_rejected(self):
        self.set_archive(dict(self.payloads, **{'UNBOUND.DRV': b'not qualified'}))
        with self.assertRaisesRegex(ValueError, 'member inventory differs'):
            V.evidence_root()

    def test_missing_member_is_rejected(self):
        files = dict(self.payloads)
        del files[next(iter(files))]
        self.set_archive(files)
        with self.assertRaisesRegex(ValueError, 'member inventory differs'):
            V.evidence_root()

    def test_duplicate_member_is_rejected(self):
        rows = list(self.payloads.items())
        self.set_archive(rows + [rows[0]])
        with self.assertRaisesRegex(ValueError, 'Duplicate evidence archive member'):
            V.evidence_root()

    def test_unsafe_member_names_are_rejected(self):
        for name in ('../escape', '/absolute', 'C:/drive', 'CPL\\escape', 'CPL/./alias'):
            with self.subTest(name=name):
                self.set_archive(dict(self.payloads, **{name: b'unsafe'}))
                with self.assertRaisesRegex(ValueError, 'Unsafe qualification path'):
                    V.evidence_root()

    def test_symlink_member_is_rejected(self):
        rows = list(self.payloads.items())
        info = zipfile.ZipInfo(rows[0][0])
        info.create_system = 3
        info.external_attr = (stat.S_IFLNK | 0o777) << 16
        rows[0] = (info, rows[0][1])
        self.set_archive(rows)
        with self.assertRaisesRegex(ValueError, 'Nonregular or encrypted'):
            V.evidence_root()

    def test_wrong_member_bytes_fail_before_any_extraction(self):
        files = dict(self.payloads)
        name = next(iter(files))
        files[name] = b'x' * len(files[name])
        self.set_archive(files)
        with mock.patch.object(V.tempfile, 'TemporaryDirectory') as temporary:
            with self.assertRaisesRegex(ValueError, 'member identity differs'):
                V.evidence_root()
            temporary.assert_not_called()

    def test_changed_member_size_is_rejected(self):
        files = dict(self.payloads)
        files[next(iter(files))] += b'extra'
        self.set_archive(files)
        with self.assertRaisesRegex(ValueError, 'member size differs'):
            V.evidence_root()

    def test_unbound_executed_driver_is_rejected(self):
        row = self.q['profiles']['colorplus32016']['ellipse']['candidate']
        del row['files']['EXECUTED.DRV']
        with self.assertRaisesRegex(ValueError, 'driver readback differs: unbound evidence'):
            V.evidence_root()

    def test_control_driver_must_be_bound_inside_archive(self):
        self.q['profiles']['colorplus32016']['control_driver']['path'] = 'unbound/CONTROL.DRV'
        with self.assertRaisesRegex(ValueError, 'outside optimized prefix'):
            V.evidence_root()

    def test_changed_bindings_do_not_reuse_cached_extraction(self):
        V.evidence_root()
        self.q['profiles']['colorplus32016']['ellipse']['candidate']['files']['F00.BIN']['bytes'] += 1
        with self.assertRaisesRegex(ValueError, 'member size differs'):
            V.evidence_root()


if __name__ == '__main__':
    unittest.main()
