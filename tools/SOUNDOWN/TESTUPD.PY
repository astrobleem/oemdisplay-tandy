"""Synthetic updater input-selection regressions; no emulator or kit writes."""
from pathlib import Path
import argparse
import copy
import importlib.util
from importlib.machinery import SourceFileLoader
import json
import subprocess
import sys
import tempfile
import unittest
import zlib

SCRIPT = Path(__file__).with_name('UPDATE.PY')
spec = importlib.util.spec_from_loader('sound_update_tests',
    SourceFileLoader('sound_update_tests', str(SCRIPT)))
update = importlib.util.module_from_spec(spec)
spec.loader.exec_module(update)


def put(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def record(path, value):
    put(path, json.dumps(value).encode('ascii'))


class SelectionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='sound-update-select-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.display, self.sound, self.native = [self.root/name for name in
                                               ('display', 'sound', 'native')]
        self.old_here, self.old_repo = update.HERE, update.REPO
        self.addCleanup(self.restore_module)
        update.REPO = self.display
        update.HERE = self.display/'tools/SOUNDOWN'
        self.clean = {'return': 0, 'owned_child_stopped': True,
                      'lease_released': True}
        self.current = {}
        for name, folder in update.NAMES.items():
            relative = 'client/'+name+'.C'
            source = ('current source '+name).encode()
            put(self.display/relative, source)
            for suffix, text in (('9', source), ('3', b'stale client source')):
                build = self.native/(folder+suffix)
                binary = ('binary '+name+suffix).encode()
                put(build/name, binary)
                put(build/Path(relative).name, text)
                record(build/'BUILD.JSON', {
                    'source_pins': {'unified/oemdisplay-tandy/'+relative:
                                    update.identity(text)},
                    'runtime': {name: update.identity(binary)}})
                record(build/'PROCESS.JSON', self.clean)
                if suffix == '9':
                    self.current[name] = binary
        self.fixxt = self.native/'fixxt-current'
        source, binary = b'current finisher source', b'current finisher binary'
        put(update.HERE/'FIXXT.C', source)
        put(self.fixxt/'FIXXT.C', source)
        put(self.fixxt/'FIXXT.EXE', binary)
        record(self.fixxt/'BUILD.JSON', {'sources': {'FIXXT.C': update.identity(source)},
                                       'runtime': update.identity(binary)})
        record(self.fixxt/'PROCESS.JSON', self.clean)
        self.current['FIXXT.EXE'] = binary
        source = b'current sound source'
        put(self.sound/'src/win30/DRIVER/TSOUND.C', source)
        for folder, text in (('driver8', source), ('driver2', b'stale sound source')):
            build = self.native/folder
            binary = ('sound binary '+folder).encode()
            put(build/'TSOUND.C', text)
            put(build/'SOUND.DRV', binary)
            record(build/'BUILD.JSON', {'sources': {'TSOUND.C': update.identity(text)},
                                       'runtime': update.identity(binary)})
            record(build/'PROCESS.JSON', self.clean)
            if folder == 'driver8':
                self.current['SOUND.DRV'] = binary
        sound = self.current['SOUND.DRV']
        record(self.sound/'src/win30/DRIVER/SOUNDID.JSON', {
            'file': 'SOUND.DRV', **update.identity(sound),
            'crc32': '%08x' % zlib.crc32(sound)})
        for path in (update.HERE/'SOUNDID.H',
                     self.sound/'src/win30/DRIVER/SOUNDID.H'):
            put(path, b'identical generated sound expectations')
        self.acceptance = {'runtime_claim': 'completed production-driver native observer',
            'client_binaries': {name: update.identity(self.current[name]) for name in
                               ('TCHIME.EXE', 'XPCHIME.EXE', 'TEXIT.EXE', 'TP.EXE')},
            'driver': update.identity(sound),
            'logs': {'UNIFYQA.LOG': {'checks': ['AllPass']}}}
        self.acceptance['client_binaries']['WINDOWS/TSHELL.EXE'] = update.identity(
            self.current['TSHELL.EXE'])
        self.receipt = self.root/'ACCEPT.JSN'
        record(self.receipt, self.acceptance)
        self.args = argparse.Namespace(native=self.native, client_suffix='9',
            driver=self.native/'driver8', fixxt=self.fixxt, sound_repo=self.sound,
            acceptance=self.receipt, apply=False, report=None, tshell_build=None)

    def restore_module(self):
        update.HERE, update.REPO = self.old_here, self.old_repo

    def test_explicit_current_set_ignores_stale_default_directories(self):
        binaries, records = update.native_inputs(self.args)
        self.assertEqual(binaries, self.current)
        self.assertEqual(records['SOUND.DRV']['runtime'],
                         update.identity(self.current['SOUND.DRV']))
        self.assertFalse((self.display/'tools/XR1PACK').exists())

    def test_stale_client_selection_refuses_current_source_mismatch(self):
        self.args.client_suffix = '3'
        with self.assertRaisesRegex(ValueError, 'Stale source:'):
            update.native_inputs(self.args)
        self.assertFalse((self.display/'tools/XR1PACK').exists())

    def shell_override(self, source=None):
        build = self.native/'tshell12'
        relative = 'client/TSHELL.EXE.C'
        text = (self.display/relative).read_bytes() if source is None else source
        binary = b'separately qualified primary shell binary'
        put(build/'TSHELL.EXE', binary)
        put(build/Path(relative).name, text)
        record(build/'BUILD.JSON', {
            'source_pins': {'unified/oemdisplay-tandy/'+relative: update.identity(text)},
            'runtime': {'TSHELL.EXE': update.identity(binary)}})
        record(build/'PROCESS.JSON', self.clean)
        self.args.tshell_build = build
        return binary

    def test_shell_override_keeps_four_unchanged_suffix_clients(self):
        shell = self.shell_override()
        binaries, records = update.native_inputs(self.args)
        expected = dict(self.current)
        expected['TSHELL.EXE'] = shell
        self.assertEqual(binaries, expected)
        self.assertEqual(records['TSHELL.EXE']['runtime'], update.identity(shell))
        self.assertFalse((self.display/'tools/XR1PACK').exists())

    def test_shell_override_source_mismatch_refuses(self):
        self.shell_override(b'stale command-tail source')
        with self.assertRaisesRegex(ValueError, 'Stale source:'):
            update.native_inputs(self.args)

    def test_shell_override_retains_cleanup_gate(self):
        self.shell_override()
        record(self.args.tshell_build/'PROCESS.JSON', {**self.clean, 'return': 1})
        with self.assertRaisesRegex(ValueError, 'did not complete/clean up: TSHELL.EXE'):
            update.native_inputs(self.args)

    def test_shell_override_needs_matching_installed_shell_acceptance(self):
        self.shell_override()
        with self.assertRaisesRegex(ValueError, 'another installed TSHELL'):
            update.integrate(self.args)
        self.assertFalse((self.display/'tools/XR1PACK').exists())

    def test_stale_explicit_driver_refuses_current_source_mismatch(self):
        self.args.driver = self.native/'driver2'
        with self.assertRaisesRegex(ValueError, 'Stale finisher source: TSOUND.C'):
            update.native_inputs(self.args)

    def test_current_client_source_change_refuses(self):
        put(self.display/'client/TSHELL.EXE.C', b'changed after native build')
        with self.assertRaisesRegex(ValueError, 'Stale source:'):
            update.native_inputs(self.args)

    def test_selection_retains_installed_shell_acceptance_gate(self):
        bad = copy.deepcopy(self.acceptance)
        bad['client_binaries']['WINDOWS/TSHELL.EXE'] = update.identity(b'other shell')
        record(self.receipt, bad)
        with self.assertRaisesRegex(ValueError, 'another installed TSHELL'):
            update.integrate(self.args)
        self.assertFalse((self.display/'tools/XR1PACK').exists())

    def test_selection_retains_driver_acceptance_gate(self):
        bad = copy.deepcopy(self.acceptance)
        bad['driver'] = update.identity(b'other driver')
        record(self.receipt, bad)
        with self.assertRaisesRegex(ValueError, 'another sound driver'):
            update.integrate(self.args)
        self.assertFalse((self.display/'tools/XR1PACK').exists())

    def test_cli_requires_both_explicit_selection_arguments(self):
        base = [sys.executable, str(SCRIPT), '--native', str(self.native),
                '--fixxt', str(self.fixxt), '--sound-repo', str(self.sound),
                '--acceptance', str(self.receipt)]
        for extra, missing in ((['--driver', str(self.args.driver)], '--client-suffix'),
                               (['--client-suffix', '9'], '--driver')):
            result = subprocess.run(base+extra, capture_output=True, text=True,
                                    timeout=10)
            self.assertEqual(result.returncode, 2)
            self.assertIn(missing, result.stderr)
        self.assertFalse((self.display/'tools/XR1PACK').exists())


if __name__ == '__main__':
    unittest.main(verbosity=2)
