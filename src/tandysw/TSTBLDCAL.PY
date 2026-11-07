#!/usr/bin/env python3
"""Check BUILDCALC staging without invoking a compiler or emitting reports."""
from pathlib import Path
import argparse
import ast
import importlib.machinery
import sys
import tempfile
from types import SimpleNamespace

HERE = Path(__file__).resolve().parent


class StopBeforeCompiler(Exception):
    pass


def files(root):
    return {str(p.relative_to(root)): p.read_bytes()
            for p in root.rglob('*') if p.is_file()}


def lifecycle(wrapper):
    original_load, argv = wrapper.load, sys.argv[:]
    try:
        for fail in (False, True):
            with tempfile.TemporaryDirectory(prefix='buildcalc-hooks-') as temp:
                renderer = Path(temp) / 'renderer'
                (renderer / 'EGA').mkdir(parents=True)
                source = renderer / 'EGA/TSOFT.ASM'
                source.write_bytes(b'original')
                calls, edits = [], []
                def prepare(repo, out):
                    return renderer, Path(temp) / 'resources'
                def compiler(command, env, path, timeout=180):
                    calls.append((command, env, path, timeout))
                builder = SimpleNamespace(baseline=SimpleNamespace(prepare=prepare), bounded_run=compiler)
                expected = [(['compiler', label], {'mode':'test'}, Path(temp)/label, 75)
                            for label in ('core', 'cursor', 'resources')]
                def main():
                    builder.baseline.prepare(Path(temp), Path(temp))
                    for command, env, path, timeout in expected:
                        builder.bounded_run(command, env, path, timeout)
                builder.main = main
                def live(*args):
                    edits.append('live')
                    source.write_bytes(b'partial')
                    if fail:
                        raise ValueError('deliberate unified-stage refusal')
                    source.write_bytes(b'live')
                modules = {'BUILD88':builder, 'CALCLIVE':SimpleNamespace(port=live)}
                wrapper.load = modules.__getitem__
                sys.argv = ['BUILDCALC.PY']
                try:
                    wrapper.main()
                except ValueError as error:
                    assert fail and str(error) == 'deliberate unified-stage refusal'
                else:
                    assert not fail
                assert edits == ['live']
                assert calls == ([] if fail else expected)
                assert source.read_bytes() == (b'original' if fail else b'live')
                assert builder.baseline.prepare is prepare and builder.bounded_run is compiler
                print('PASS lifecycle:', 'rollback before compiler' if fail else 'three compiler commands unchanged; apply once', '; hooks restored')
        sys.argv = ['BUILDCALC.PY', '--ui-profile', 'compact320']
        wrapper.load = lambda name: (_ for _ in ()).throw(AssertionError('Nonstock loaded builder'))
        try:
            wrapper.main()
        except ValueError as error:
            assert 'only stock UI' in str(error)
        else:
            raise AssertionError('Nonstock UI accepted without qualification')
        print('PASS nonstock UI rejected before preparation')
    finally:
        wrapper.load, sys.argv = original_load, argv


def run(repo, standalone=None):
    code = None
    if standalone is not None:
        tree = ast.parse(standalone.read_text())
        body = []
        for node in tree.body:
            body.append(node)
            if isinstance(node, ast.If) and ast.unparse(node.test) == 'not OUT.exists()':
                break
        else:
            raise AssertionError('Standalone preparation boundary missing')
        code = compile(ast.fix_missing_locations(ast.Module(body=body, type_ignores=[])), str(standalone), 'exec')
    wrapper = importlib.machinery.SourceFileLoader('tested_buildcalc', str(HERE / 'BUILDCALC.PY')).load_module()
    lifecycle(wrapper)
    load = wrapper.load
    argv = sys.argv[:]
    try:
        for mode in load('CALCFAST').MODES:
            with tempfile.TemporaryDirectory(prefix='buildcalc-') as temp:
                expected, actual = Path(temp) / 'expected', Path(temp) / 'actual'
                if code is None:
                    load('TSTLIVE').stage(repo, expected, mode, listings=True)
                else:
                    sys.argv = ['rebuild.py', '--repo', str(repo), '--source', str(HERE), '--out', str(expected),
                                '--mode', mode]
                    exec(code, {'__file__': str(standalone), '__name__': 'stage_only'})
                load('CALCLIVE').port(expected / 'renderer', mode, repo)
                state = {}

                def stop(command, env, path, timeout=180):
                    assert files(actual / 'renderer') == files(expected / 'renderer')
                    assert files(actual / 'resources') == files(expected / 'resources')
                    state['called'] = True
                    raise StopBeforeCompiler()

                def intercepted(name):
                    module = load(name)
                    if name == 'BUILD88':
                        module.bounded_run = stop
                        state['builder'] = module
                        state['prepare'] = module.baseline.prepare
                    return module

                wrapper.load = intercepted
                sys.argv = ['BUILDCALC.PY', '--repo', str(repo), '--dosbox', '/unused-no-compiler',
                            '--out', str(actual), '--mode', mode]
                try:
                    wrapper.main()
                except StopBeforeCompiler:
                    pass
                else:
                    raise AssertionError('Compiler boundary not reached')
                assert state.get('called')
                assert state['builder'].bounded_run is stop
                assert state['builder'].baseline.prepare is state['prepare']
                assert not (actual / 'RESULT.json').exists()
                print('PASS', mode, 'BUILDCALC matches independent sources/resources; hooks restored; no compiler/report')
    finally:
        wrapper.load = load
        sys.argv = argv


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, required=True)
    parser.add_argument('--standalone', type=Path, help='Optional legacy standalone staging script')
    args = parser.parse_args()
    run(args.repo.resolve(), args.standalone.resolve() if args.standalone else None)
