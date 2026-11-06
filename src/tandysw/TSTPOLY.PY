#!/usr/bin/env python3
"""Host-only fail-closed and bounded-polyline geometry checks."""
from pathlib import Path
import argparse
import importlib.machinery
import random
import shutil
import tempfile

HERE = Path(__file__).resolve().parent
P = importlib.machinery.SourceFileLoader('calcpoly_tested', str(HERE / 'CALCPOLY.PY')).load_module()


def bounds(points, width):
    if not 2 <= len(points) <= 64:
        return None
    low, high, previous = 200, 0, None
    for point in points:
        x, y = point
        if not 0 <= x < width or not 0 <= y < 200 or point == previous:
            return None
        low, high, previous = min(low, y), max(high, y), point
    return low, high + 1


def run(fixtures, repo):
    for width, stage in ((640, 'current-text6404-build'), (320, 'current-text3204-build')):
        with tempfile.TemporaryDirectory(prefix='calcpoly-') as tmp:
            renderer = Path(tmp) / 'renderer'
            shutil.copytree(fixtures / stage / 'renderer', renderer)
            path = renderer / 'EGA/TSOFT.ASM'
            original = path.read_bytes()
            P.port(renderer, str(width) + 'x200x4', repo)
            candidate = path.read_bytes()
            assert candidate != original
            inverse = candidate.decode('latin1').replace('\r\n', '\n')
            for old, new in reversed(P.CHANGES):
                assert inverse.count(new) == 1
                inverse = inverse.replace(new, old)
            assert inverse.replace('\n', '\r\n').encode('latin1') == original
            print('PASS', width, 'inverse scope and unchanged validation')

            def refuse(mode=str(width) + 'x200x4'):
                before = path.read_bytes()
                try:
                    P.port(renderer, mode, repo)
                except ValueError:
                    assert path.read_bytes() == before
                else:
                    raise AssertionError('Expected rejection')

            refuse()
            path.write_bytes(original)
            refuse('800x600x16')
            for old, new in ((b'cmp count,2', b'cmp count,3'),
                             (b'cmp word ptr es:[di+4],4', b'cmp word ptr es:[di+4],5'),
                             (b'TOutput_line_ordered:', b'TOutput_line_changed:')):
                assert old in original
                path.write_bytes(original.replace(old, new))
                refuse()
            path.write_bytes(original)
            poly = renderer / 'POLYLINE.ASM'
            poly.write_bytes(poly.read_bytes() + b'\r\nnop\r\n')
            refuse()
            print('PASS', width, 'double/unsupported/changed gates/late anchor/renderer refusals without writes')
        assert bounds([(0, 0), (width-1, 199)], width) == (0, 200)
        assert bounds([(0, 5), (1, 5), (0, 5)], width) == (5, 6)
        for points in ([], [(0, 0)], [(0, 0)]*65, [(0, 0), (0, 0)],
                       [(-1, 0), (1, 1)], [(0, -1), (1, 1)],
                       [(width, 0), (1, 1)], [(0, 200), (1, 1)]):
            assert bounds(points, width) is None
        rng = random.Random(734)
        for _ in range(1000):
            points = [(rng.randrange(width), rng.randrange(200)) for _ in range(rng.randrange(2, 65))]
            result = bounds(points, width)
            if result is not None:
                assert result == (min(y for x, y in points), max(y for x, y in points)+1)
                # Every segment's enclosing Y interval lies within the copied rows.
                assert all(result[0] <= min(a[1], b[1]) <= max(a[1], b[1]) < result[1]
                           for a, b in zip(points, points[1:]))
        print('PASS', width, 'boundary/rejection cases and 1000 deterministic point-list models')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--fixtures', type=Path, required=True)
    parser.add_argument('--repo', type=Path, required=True)
    args = parser.parse_args()
    run(args.fixtures.resolve(), args.repo.resolve())
