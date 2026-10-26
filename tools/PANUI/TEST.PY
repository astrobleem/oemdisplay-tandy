"""Regression checks for current native settings/package receipt bindings."""
from pathlib import Path
import copy
import importlib.machinery
import io
import json
import re
import shutil
import tempfile
import unittest
from unittest.mock import patch
import zipfile

ROOT = Path(__file__).resolve().parents[2]
U = importlib.machinery.SourceFileLoader('ui_receipts', str(ROOT / 'src/panui/VERIFY.PY')).load_module()
P = importlib.machinery.SourceFileLoader('ui_installer', str(ROOT / 'tools/DOSINST/PANUI.PY')).load_module()
S = importlib.machinery.SourceFileLoader('ui_softpan', str(ROOT / 'tools/SPPACK/PACKAGE.PY')).load_module()
C = importlib.machinery.SourceFileLoader('ui_core', str(ROOT / 'tools/DOSINST/RCPUB.PY')).load_module()


class Bindings(unittest.TestCase):
    def test_finisher_runtime_size_matches_current_xy_helper(self):
        text = (ROOT / 'tools/DOSINST/FIXXT.C').read_text()
        names = re.findall(r'"([^"]+)"', re.search(
            r'static const char \*names\[\]=\{([^}]+)\}', text)[1])
        sizes = re.search(r'static unsigned long sizes\[\]=\{([^}]+)\}', text)[1].split(',')
        self.assertEqual(len(names), len(sizes))
        _, binaries = U.verify()
        self.assertEqual(int(sizes[names.index('XYCTL.EXE')].replace('UL', '')),
                         len(binaries['XYCTL.EXE']))

    def test_actual_native_helpers_and_source_closure(self):
        q, binaries = U.verify()
        self.assertEqual(set(q['cases']), {'PCJR', 'COLORPLUS', 'TANDYXY'})
        self.assertEqual(set(binaries), {'XTPAN.EXE', 'PANCFG.EXE', 'XYCTL.EXE'})

    def test_omitted_compiled_source_refused(self):
        q = json.loads(U.QUAL.read_bytes())
        q['sources'].pop('src/panui/PANDLG.C')
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / 'NATIVE.JSN'
            p.write_text(json.dumps(q))
            with patch.object(U, 'QUAL', p):
                with self.assertRaisesRegex(ValueError, 'source inventory'):
                    U.verify()

    def test_window_run_cannot_be_rebound_to_different_helpers(self):
        q = json.loads(U.QUAL.read_bytes())
        row = q['window_backend']
        with zipfile.ZipFile(io.BytesIO((ROOT / row['path']).read_bytes())) as z:
            members = {n: z.read(n) for n in z.namelist()}
        name = 'EVIDENCE/PCJR/RESULT.JSON'
        result = json.loads(members[name])
        result['binaries']['XTPAN.EXE']['sha256'] = '0' * 64
        members[name] = json.dumps(result).encode('ascii')
        stream = io.BytesIO()
        with zipfile.ZipFile(stream, 'w') as z:
            for name, data in members.items():
                z.writestr(name, data)
        data = stream.getvalue()
        row['identity'] = U.identity(data)
        row['members'] = {n: U.identity(b) for n, b in members.items()}
        original_exact = U.exact
        def exact(name, pin):
            return data if name == row['path'] else original_exact(name, pin)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'NATIVE.JSN'
            path.write_text(json.dumps(q))
            with patch.object(U, 'QUAL', path), patch.object(U, 'exact', exact):
                with self.assertRaisesRegex(ValueError, 'Window run used different helper'):
                    U.verify()

    def test_declared_ui_manifest_must_match_native_receipt(self):
        spec = json.loads((ROOT / 'tools/SPPACK/PUBLIC.JSN').read_bytes())
        spec['qualification']['ui_update']['manifest']['sha256'] = '0' * 64
        with self.assertRaisesRegex(ValueError, 'qualification manifest'):
            S.payload('JRPAN', spec)

    def test_each_native_case_binds_packet_and_executables(self):
        entries = C.expanded_entries()
        archive = C.pub.zip_bytes(entries)
        baseline = json.loads((ROOT / 'docs/QUAL/DOSINST/EXPAND.JSN').read_bytes())
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for folder in ('docs/QUAL/DOSINST', 'tools/XROEM'):
                shutil.copytree(ROOT / folder, root / folder)
            qdir = root / 'docs/QUAL/WDESK'
            qdir.mkdir()
            shutil.copyfile(U.QUAL, qdir / 'NATIVE.JSN')
            files = {n: P.identity(b) for n, b in entries.items()}
            q = {'status': 'PASS_NATIVE_PACKAGE', 'physical_qualification': False,
                 'baseline_expanded': P.identity((root / 'docs/QUAL/DOSINST/EXPAND.JSN').read_bytes()),
                 'helper_qualification': P.identity(U.QUAL.read_bytes()),
                 'archive': P.identity(archive), 'files': files, 'native': {}}
            for name in ('fresh', 'update', 'finisher'):
                row = {'complete': True, 'owned_stopped': True, 'lease_released': True,
                       'archive': copy.deepcopy(q['archive']),
                       'helper': copy.deepcopy(files['SETUP.EXE'])}
                if name != 'finisher':
                    row['prepared_comparison'] = {'count': 370 if name == 'fresh' else 83, 'different': []}
                else:
                    row.update(finisher=copy.deepcopy(files['WINXT/FIXXT.EXE']),
                               input_runtime=copy.deepcopy(files['WINXT/XYCTL.EXE']),
                               installed_helper=copy.deepcopy(files['WINXT/XYCTL.EXE']),
                               guarded_windows_return=True)
                q['native'][name] = row

            def run(record):
                raw = io.BytesIO()
                with zipfile.ZipFile(raw, 'w') as z:
                    z.writestr('RESULT.JSN', json.dumps(record['native']))
                data = raw.getvalue()
                (qdir / 'INSTALL.ZIP').write_bytes(data)
                record['evidence'] = {'docs/QUAL/WDESK/INSTALL.ZIP': P.identity(data)}
                (qdir / 'PACKAGE.JSN').write_text(json.dumps(record))
                with patch.object(P, 'ROOT', root), patch.object(P, 'helpers'), patch.object(P, 'runtimes',
                        return_value={n: entries['WINXT/' + n] for n in ('FIXXT.EXE', 'XYCTL.EXE')}):
                    return P.qualify(entries, archive, baseline)

            run(copy.deepcopy(q))
            for name in q['native']:
                for key in ('archive', 'helper'):
                    bad = copy.deepcopy(q)
                    bad['native'][name][key]['sha256'] = '0' * 64
                    with self.assertRaisesRegex(ValueError, 'Different packet/Setup'):
                        run(bad)
            for key in ('finisher', 'input_runtime', 'installed_helper'):
                bad = copy.deepcopy(q)
                bad['native']['finisher'][key]['sha256'] = '0' * 64
                with self.assertRaisesRegex(ValueError, 'Installed helper/Windows'):
                    run(bad)


if __name__ == '__main__':
    unittest.main()
