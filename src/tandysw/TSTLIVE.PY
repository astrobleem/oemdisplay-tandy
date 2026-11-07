#!/usr/bin/env python3
"""Check exact live-bound preservation and only the unsupported Output guard."""
from pathlib import Path
import argparse
import importlib.machinery
import shutil
import re
import tempfile

HERE = Path(__file__).resolve().parent


def load(name):
    return importlib.machinery.SourceFileLoader('tstlive_' + name, str(HERE / (name + ('.py' if name == 'build' else '.PY')))).load_module()


def stage(repo, out, mode, listings=False):
    """Independently prepare accepted TR5 sources using the external view inputs."""
    baseline = load('build')
    renderer, resources = baseline.prepare(repo, out)
    load('PORT8086').port(renderer, repo)
    load('PORTDIB').port(renderer, repo)
    load('MODEPROF').port(renderer, resources, repo, mode)
    load('REPCOPY88').port(renderer, mode)
    load('BYTECOL').port(renderer, mode)
    load('CURKEEP').port(renderer, mode, combined=True)
    load('OUTROWS').port(renderer, mode)
    load('WIDESCAN').port(renderer, mode)
    if listings:
        for filename in ('BLDCOR.BAT', 'BLDCUR.BAT'):
            path = renderer / filename
            text = baseline.normalized(path).replace('SET INCLUDE=', 'SET INCLUDE=R:\\INC;')
            text = text.replace('MASM -I', 'MASM -LA -I')
            if filename == 'BLDCOR.BAT':
                text = re.sub(r',([a-z0-9]+)\.obj;', r',\1.obj,\1.lst;', text)
            baseline.write_dos(path, text)
    return renderer, resources


def run(fixtures, repo):
    output, text, fast, unified = (load(n) for n in ('OUTPUTBOUNDS', 'TEXTBOUNDS', 'CALCFAST', 'CALCLIVE'))
    for mode in output.EXPECTED:
        name = {'640x200x4':'current-base6404-build', '320x200x4':'current-base3204-build'}.get(mode, 'current-base-' + mode + '-build')
        with tempfile.TemporaryDirectory(prefix='tstlive-') as temp:
            if fixtures is None:
                renderer, _ = stage(repo, Path(temp), mode)
            else:
                renderer = Path(temp)/'renderer'
                shutil.copytree(fixtures/name/'renderer', renderer)
            path = renderer/'EGA/TSOFT.ASM'
            original = path.read_bytes()
            other = {p:p.read_bytes() for p in renderer.rglob('*') if p.is_file() and p != path}
            bounded_output = output.transform(original, mode)
            live = text.transform(bounded_output, mode)
            text.selftest(bounded_output, mode)
            unified.port(renderer, mode, repo)
            candidate = path.read_bytes()
            old, new, count = fast.CHANGES[0]
            old, new = (v.replace('\n','\r\n').encode('latin1') for v in (old,new))
            assert candidate.count(new) == count == 1
            assert candidate.replace(new,old) == live
            assert all(p.read_bytes()==data for p,data in other.items())
            assert b'    cmp count,1024\r\n' in candidate
            # Live text and every non-Output byte stay exact, including FLAGS behavior.
            start = live.index(b'cProc TOutput,')
            end = live.index(b'cProc TPixel,',start)
            delta = len(new)-len(old)
            assert candidate[:start] == live[:start] and candidate[end+delta:] == live[end:]
            assert candidate.count(b'    call FlushRetainColumns\r\n') == live.count(b'    call FlushRetainColumns\r\n')
            for bad, badmode in ((candidate,mode),(original+b';change\r\n',mode),(original,'unsupported')):
                try:unified.transform(bad,badmode)
                except ValueError:pass
                else:raise AssertionError('Invalid source/mode accepted')
            # A changed dispatcher must be refused before even the pinned stage is written.
            path.write_bytes(original)
            dispatch=renderer/'OUTPUT.ASM'
            dispatch.write_bytes(dispatch.read_bytes()+b'\r\nnop\r\n')
            try:unified.port(renderer,mode,repo)
            except ValueError:assert path.read_bytes()==original
            else:raise AssertionError('Changed dispatcher accepted')
            print('PASS',mode,'exact live inverse; text/column/count1024/RLE preserved; malformed/double/dispatcher refusal')
    # All16-bit style values: only actual dispatch styles retain the original copy path.
    assert [style for style in range(65536) if style == 18 or style == 4] == [4,18]
    print('PASS complete16-bit style partition: only4 and18 remain eligible for post-render copy')


if __name__ == '__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--fixtures',type=Path,help='Optional existing native baseline fixtures; otherwise stage from --repo')
    p.add_argument('--repo',type=Path,required=True)
    a=p.parse_args();run(a.fixtures.resolve() if a.fixtures else None,a.repo.resolve())
