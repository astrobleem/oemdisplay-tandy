#!/usr/bin/env python3
"""Audit supplied completed builds in memory; print results without report files."""
from pathlib import Path
import argparse
import importlib.machinery
import re

HERE = Path(__file__).resolve().parent


def module(name):
    return importlib.machinery.SourceFileLoader('audcalc_' + name, str(HERE / (name + '.PY'))).load_module()


def audit(build):
    build = Path(build).resolve()
    renderer = build / 'renderer'
    ega = renderer / 'EGA'
    for path in (ega / 'BUILD0.LOG', ega / 'CURSOR.LOG', ega / 'LINK.LOG',
                 build / 'resources/BUILD.LOG'):
        text = path.read_text(errors='replace')
        if any(int(n) for n in re.findall(r'(\d+)\s+Severe\s+Errors', text)) or re.search(r'error L\d+|fatal error', text, re.I):
            raise ValueError('Build error in ' + str(path))
    listings = sorted(ega.glob('*.LST'))
    if len(listings) != 28:
        raise ValueError('Expected 28 linked listings, got ' + str(len(listings)))
    isa = module('AUDIT88').audit(listings)
    rep = module('REPCOPY88').audit_listings(listings)
    link = module('PORT8086').audit_link(renderer,
        ['BMC_MAIN.OBJ', 'BMC_ETI.OBJ', 'BMC_ITE.OBJ', 'SDIB88.OBJ', 'RLE88.OBJ'])
    rle = module('RLEABITEST').audit_files(ega / 'RLE88.LST', HERE / 'RLE88.ASM')
    if (renderer / 'RLE88.ASM').read_bytes() != (HERE / 'RLE88.ASM').read_bytes():
        raise ValueError('Staged RLE source differs from audited current source')
    return {'isa': isa, 'rep': rep, 'link': link, 'rle': rle}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('builds', type=Path, nargs='+')
    args = parser.parse_args()
    for build in args.builds:
        result = audit(build)
        print('PASS', build, ': 28 listings;', result['isa']['emitted_instruction_rows_checked'],
              'ISA rows; REP safe; 28-object link closure; RLE ABI; build logs clean')
