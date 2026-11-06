#!/usr/bin/env python3
"""Host-only current-source staging and Calculator transforms for all profiles."""
from pathlib import Path
import argparse
import importlib.machinery
import sys
import tempfile

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import build


def module(name):
    return importlib.machinery.SourceFileLoader('allcalc_' + name, str(HERE / (name + '.PY'))).load_module()


def run(repo, fixtures):
    fast, poly = module('CALCFAST'), module('CALCPOLY')
    profiles = module('MODEPROF').PROFILES
    assert set(fast.MODES) == set(poly.MODES) == set(profiles)
    for mode, profile in profiles.items():
        with tempfile.TemporaryDirectory(prefix='allcalc-') as temp:
            renderer, resources = build.prepare(repo, Path(temp))
            module('PORT8086').port(renderer, repo)
            module('PORTDIB').port(renderer, repo)
            module('MODEPROF').port(renderer, resources, repo, mode)
            module('REPCOPY88').port(renderer, mode)
            module('BYTECOL').port(renderer, mode)
            module('CURKEEP').port(renderer, mode, combined=True)
            module('OUTROWS').port(renderer, mode)
            module('WIDESCAN').port(renderer, mode)
            path = renderer / 'EGA/TSOFT.ASM'
            old = path.read_bytes()
            protected = {p: p.read_bytes() for p in renderer.rglob('*') if p.is_file() and p != path}
            fast.port(renderer, mode, repo)
            poly.port(renderer, mode, repo)
            candidate = path.read_bytes()
            assert all(p.read_bytes() == data for p, data in protected.items())
            inverse = candidate.decode('latin1').replace('\r\n', '\n')
            for a, b in reversed(poly.CHANGES):
                assert inverse.count(b) == 1
                inverse = inverse.replace(b, a)
            for a, b, count in reversed(fast.CHANGES):
                assert inverse.count(b) == count
                inverse = inverse.replace(b, a)
            assert inverse.replace('\n', '\r\n').encode('latin1') == old
            for transform in (fast, poly):
                try:
                    transform.port(renderer, mode, repo)
                except ValueError:
                    assert path.read_bytes() == candidate
                else:
                    raise AssertionError('Double application accepted')
            if profile['colors'] == 4:
                name = 'poly6404-build' if profile['width'] == 640 else 'poly3204-build'
                assert candidate == (fixtures / name / 'renderer/EGA/TSOFT.ASM').read_bytes()
            # Pixel-to-logical-byte rounding remains independent of color depth.
            width = profile['width']
            factor = module('BYTECOL').PHYSICAL_BYTES[mode]
            for left in range(width):
                for right in range(left + 1, width + 1):
                    first, last = left // 8, (right + 7) // 8
                    assert 0 <= first < last <= width // 8
                    assert first*8 <= left < right <= last*8
                    assert last*factor <= width*{16:4,4:2,2:1}[profile['colors']]//8
            # The bounded polyline proof uses only in-screen geometry, unchanged
            # by shadow-to-VRAM encoding. Check new width160 explicitly too.
            bounds = module('TSTPOLY').bounds
            assert bounds([(0,0), (width-1,199)], width) == (0,200)
            assert bounds([(width,0), (0,1)], width) is None
            assert bounds([(0,0), (0,0)], width) is None
            print('PASS', mode, 'full pinned staging, reversible edits, source/RLE preservation, double rejection, column bounds')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, required=True)
    parser.add_argument('--fixtures', type=Path, required=True)
    args = parser.parse_args()
    run(args.repo.resolve(), args.fixtures.resolve())
