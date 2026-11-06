#!/usr/bin/env python3
"""Host-only regression checks against the existing tested assembly fixtures."""
from pathlib import Path
import argparse
import importlib.machinery
import shutil
import tempfile

HERE = Path(__file__).resolve().parent
C = importlib.machinery.SourceFileLoader('calcfast', str(HERE / 'CALCFAST.PY')).load_module()


def run(fixtures, donor):
    checks = []
    for mode, base, tested in (
        ('640x200x4', 'base-build', 'text-build'),
        ('320x200x4', 'base3204-build', 'text3204-build'),
    ):
        with tempfile.TemporaryDirectory(prefix='calcfast-') as tmp:
            root = Path(tmp)
            renderer = root / 'renderer'
            (renderer / 'EGA').mkdir(parents=True)
            defs = root / 'DDK/286/INC/GDIDEFS.INC'
            defs.parent.mkdir(parents=True)
            shutil.copyfile(donor / 'DDK/286/INC/GDIDEFS.INC', defs)
            output = renderer / 'OUTPUT.ASM'
            target = renderer / 'EGA/TSOFT.ASM'
            original = (fixtures / base / 'renderer/EGA/TSOFT.ASM').read_bytes()
            original_output = (fixtures / base / 'renderer/OUTPUT.ASM').read_bytes()
            original_defs = defs.read_bytes()

            def reset():
                target.write_bytes(original)
                output.write_bytes(original_output)
                defs.write_bytes(original_defs)

            def refused(mode_arg=mode):
                before = target.read_bytes()
                try:
                    C.port(renderer, mode_arg, root)
                except ValueError:
                    assert target.read_bytes() == before, 'Rejection wrote staged wrapper'
                else:
                    raise AssertionError('Expected rejection')

            reset()
            C.port(renderer, mode, root)
            expected = (fixtures / tested / 'renderer/EGA/TSOFT.ASM').read_bytes()
            # The tested 640 fixture predates one explanatory comment edit in
            # the shared transform. Normalize only that exact comment, not code.
            expected = expected.replace(
                b'; Bounds are nonnegative and <=640, so ceil(right/8) cannot overflow.',
                b'; Bounds are nonnegative and <=SCREEN_WIDTH (at most 640 pixels).')
            assert target.read_bytes() == expected
            assert output.read_bytes() == original_output
            assert defs.read_bytes() == original_defs
            checks.append(mode + ': tested candidate bytes match (one historical comment normalized); inputs unchanged')
            refused()
            checks.append(mode + ': double application rejected without writes')
            reset()
            refused('800x600x16')
            checks.append(mode + ': unsupported mode rejected without writes')
            reset()
            output.write_bytes(original_output.replace(b'\tdec\tax', b'\tinc\tax'))
            refused()
            checks.append(mode + ': changed fallback rejected without writes')
            reset()
            output.write_bytes(original_output.replace(b'dispatch_scanlines:', b'\tmov ax,123\r\ndispatch_scanlines:'))
            refused()
            checks.append(mode + ': added dispatcher instruction rejected without writes')
            reset()
            defs.write_bytes(original_defs.replace(b'OS_POLYLINE\tequ\t18', b'OS_POLYLINE\tequ\t19'))
            assert defs.read_bytes() != original_defs
            refused()
            checks.append(mode + ': changed numeric style rejected without writes')
            reset()
            target.write_bytes(original.replace(b'text_rectangle clip,restore', b'text_rectangle clip,altered'))
            refused()
            checks.append(mode + ': late text anchor failure rejected without partial writes')
    return checks


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--fixtures', type=Path, required=True)
    parser.add_argument('--repo', type=Path, required=True)
    args = parser.parse_args()
    for check in run(args.fixtures.resolve(), args.repo.resolve()):
        print('PASS ' + check)
