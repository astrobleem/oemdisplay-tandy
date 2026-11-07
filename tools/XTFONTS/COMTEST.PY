"""Verify the compatible narrow System font without writing reports."""
import argparse
import importlib.machinery
from pathlib import Path
import struct
import subprocess
import sys
import tempfile

HERE = Path(__file__).resolve().parent
C = importlib.machinery.SourceFileLoader('compat_font', str(HERE / 'COMPAT.PY')).load_module()


def rejected(data):
    try:
        C.compatible(data)
    except ValueError:
        return
    raise AssertionError('Altered or repeated input was accepted')


def check(original_path, narrow_path, compatible_path):
    original = original_path.read_bytes()
    narrow = narrow_path.read_bytes()
    result = compatible_path.read_bytes()
    assert len(original) == len(narrow) == len(result) == 4592
    assert C.N.narrow(original) == narrow, 'Historical narrow source changed'
    assert C.compatible(narrow) == result, 'Compatible asset is not reproducible'
    before, base = C.raw_font(narrow)
    after, newbase = C.raw_font(result)
    assert newbase == base and before[:118] == after[:118]
    assert C.N.I.resources(narrow) == C.N.I.resources(result)
    allowed = {base + 118 + (ord(c) - before[95]) * 4 + j
               for c, _, _ in C.SPACING for j in range(2)}
    changed = {i for i, (a, b) in enumerate(zip(narrow, result)) if a != b}
    assert len(changed) == 5 and changed <= allowed, 'Unrelated resource byte changed'
    chosen = {ord(c): (a, b) for c, a, b in C.SPACING}
    for code in range(256):
        a, b = C.glyph(before, code), C.glyph(after, code)
        if code not in chosen:
            assert a == b, code
        else:
            old_width, new_width = chosen[code]
            assert all(len(x) == old_width and len(y) == new_width and
                       x == y[:old_width] and not any(y[old_width:]) for x, y in zip(a, b))
    for char in 'MW':
        rows = C.glyph(after, ord(char))
        assert len(rows[0]) == 9 and all(row[0] == row[-1] == 0 for row in rows)
        assert [''.join('#' if p else '.' for p in row[1:8]) for row in rows] == C.N.G[char]
    assert after[90] == 0x21 and struct.unpack_from('<H', after, 86)[0] == 0
    assert struct.unpack_from('<H', after, 91)[0] == 7

    # Native Win3 USER's helper starts uppercase A only 25 bytes after a.
    # It thus samples a..y, A..Z and one unwritten byte, then truncates /52.
    # Checking every last byte avoids dependence on one observed stack value.
    sample = 'abcdefghijklmnopqrstuvwxyABCDEFGHIJKLMNOPQRSTUVWXYZ'
    known = sum(len(C.glyph(after, ord(c))[0]) for c in sample)
    units = [(known + len(C.glyph(after, code)[0])) // 52 for code in range(256)]
    assert known == 412 and set(units) == {8}
    for text, expected in [('WM', 18), ('Windows', 54), ('Font Filename:', 96),
                           ('File Edit View Help', 122), ('Window Manager', 105)]:
        assert sum(len(C.glyph(after, ord(c))[0]) for c in text) == expected
    rejected(original)
    rejected(result)
    rejected(b'')
    rejected(narrow[:-1])
    rejected(narrow + b'\0')
    for i in range(len(narrow)):
        edited = bytearray(narrow)
        edited[i] ^= 1
        rejected(edited)
    with tempfile.TemporaryDirectory() as d:
        output = Path(d) / 'XTCSYS.FON'
        cmd = [sys.executable, str(HERE / 'COMPAT.PY'), '--input', str(narrow_path.resolve()),
               '--output', str(output)]
        subprocess.run(cmd, check=True, capture_output=True)
        assert output.read_bytes() == result
        repeat = subprocess.run(cmd, capture_output=True)
        assert repeat.returncode and output.read_bytes() == result
    print('PASS: exact M/W9; five blank spacing columns; 251 other glyphs unchanged.')
    print('PASS: all bitmap/header/offset bytes preserved; all 256 sampled tails yield 8x8 units.')
    print('PASS: 4,592 single-byte alterations, old/double/truncated inputs and overwrite rejected.')


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--original', type=Path, default=HERE.parents[1] / 'distributions/WINXT/XTCSYS.FON')
    p.add_argument('--narrow', type=Path, default=HERE / 'NARROW/XTCSYS.FON')
    p.add_argument('--compatible', type=Path, default=HERE / 'COMPAT/XTCSYS.FON')
    a = p.parse_args()
    check(a.original, a.narrow, a.compatible)
