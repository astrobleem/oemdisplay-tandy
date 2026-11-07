#!/usr/bin/env python3
"""Build optimized Tandy profiles using unchanged BUILD88 arguments and audits.

Historical BUILD88 and its adapter consumers retain their accepted behavior.
Calculator changes touch only the freshly staged Tandy wrapper, immediately
before the first assembler call. A build is not native runtime acceptance.
"""
from pathlib import Path
import argparse
import importlib.machinery
import sys

HERE = Path(__file__).resolve().parent


def load(name):
    return importlib.machinery.SourceFileLoader('buildcalc_' + name, str(HERE / (name + '.PY'))).load_module()


def main():
    options = argparse.ArgumentParser(add_help=False)
    options.add_argument('--mode', default='320x200x16')
    options.add_argument('--ui-profile', default='stock')
    args, _ = options.parse_known_args()
    if args.ui_profile != 'stock':
        raise ValueError('BUILDCALC: only stock UI is validated; nonstock profiles require qualification')
    sys.path.insert(0, str(HERE))
    builder = load('BUILD88')
    live = load('CALCLIVE')
    prepare, run = builder.baseline.prepare, builder.bounded_run
    state = {}

    def capture(repo, out):
        if state:
            raise RuntimeError('BUILDCALC: unexpected repeated preparation')
        renderer, resources = prepare(repo, out)
        state.update(renderer=Path(renderer), repo=Path(repo))
        return renderer, resources

    def compile_once(command, env, path, timeout=180):
        if not state:
            raise RuntimeError('BUILDCALC: compilation before preparation')
        if 'patched' not in state:
            # Preserve exact live bounds and validate the additive guard before
            # any compiler runs; restore staged bytes if transformation fails.
            source = state['renderer'] / 'EGA/TSOFT.ASM'
            original = source.read_bytes()
            try:
                live.port(state['renderer'], args.mode, state['repo'])
            except Exception:
                source.write_bytes(original)
                raise
            state['patched'] = True
        return run(command, env, path, timeout)

    builder.baseline.prepare = capture
    builder.bounded_run = compile_once
    try:
        builder.main()
        if not state.get('patched'):
            raise RuntimeError('BUILDCALC: staged transformation did not run')
        print('BUILDCALC: live Output/text bounds plus unsupported Output copy guard applied; BUILD88 audits completed; runtime not asserted')
    finally:
        builder.baseline.prepare = prepare
        builder.bounded_run = run
        sys.path.pop(0)


if __name__ == '__main__':
    main()
