"""Check exact stage reproduction and exhaustive COPY/XOR span behavior."""
from pathlib import Path
import argparse
import os
import runpy
import subprocess

HERE = Path(__file__).resolve().parent
stage = runpy.run_path(str(HERE/'COPYFAST.PY'))
repair = runpy.run_path(str(HERE/'OMFFIX.PY'))['repair']


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--closure', type=Path, help='Optional historical closure for extra OMF comparison')
    p.add_argument('--out', type=Path, required=True)
    p.add_argument('--cc', default=os.environ.get('CC', 'cc'))
    a = p.parse_args()
    a.out.mkdir(parents=True, exist_ok=False)
    for profile, width in [('colorplus32016', 320), ('yamaha160-b800', 160)]:
        name = stage['PROFILES'][profile][0]
        pair = 'CPLS/N32016' if width == 320 else 'YAMAHA/N16016'
        if a.closure is not None:
            tested = (a.closure/'MATCHED'/pair/'CAND'/'DGSCDRW.OBJ').read_bytes()
            raw = bytearray()
            at = 0
            while at < len(tested):
                kind = tested[at]
                end = at+3+int.from_bytes(tested[at+1:at+3], 'little')
                if kind == 0x9a:
                    payload = b'\x02\xff\x03\xff\x04\xff\x02'
                    record = bytearray([kind])+bytearray((len(payload)+1).to_bytes(2, 'little'))+payload
                    record.append((-sum(record)) & 255)
                    raw.extend(record)
                else:
                    raw.extend(tested[at:end])
                at = end
            assert repair(bytes(raw)) == tested
            bad = bytearray(raw)
            bad[3] ^= 1
            try:
                repair(bytes(bad))
            except ValueError:
                pass
            else:
                raise AssertionError('OMF repair accepted a bad checksum')
        before = ((a.closure/'SOURCES'/profile/'GENDRAW.C') if a.closure is not None else
                  HERE/('N320BASE.C' if width == 320 else 'N160BASE.C')).resolve()
        expected = HERE/name/'GENDRAW.C'
        assert stage['transform'](before.read_bytes(), profile) == expected.read_bytes()
        for invalid in [expected.read_bytes(), before.read_bytes()+b'\r\n']:
            try:
                stage['transform'](invalid, profile)
            except ValueError:
                pass
            else:
                raise AssertionError('Stage accepted an already optimized or changed input')
        exe = (a.out/('span'+str(width))).resolve()
        subprocess.run([a.cc, '-std=c99', '-O1', '-g', '-fsanitize=address,undefined',
                        '-fno-omit-frame-pointer', '-x', 'c', '-I'+str(HERE), '-DWIDTH='+str(width),
                        '-DBASE_SOURCE="'+str(before)+'"',
                        '-DCAND_SOURCE="'+str(expected)+'"', str(HERE/'SPAN.C'), '-o', str(exe)],
                       check=True)
        subprocess.run([str(exe)], env=dict(os.environ, ASAN_OPTIONS='detect_leaks=0'), check=True)
    print('Exact source stage and both exhaustive span suites passed')


if __name__ == '__main__':
    main()
