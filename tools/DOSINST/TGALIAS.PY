"""Expanded Tandy install recipe; retained archive recipes stay frozen."""
from pathlib import Path
import hashlib
import re
import zlib

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def aliases(pins, files, crcs):
    for name in ('TANDYGR.GR2', 'TGCLIP.EXE'):
        data = (ROOT / 'distributions/WINXT' / name).read_bytes()
        row = ('{"%s","%s",%dUL,0,0x%08xUL},\r\n' %
               (name, hashlib.sha256(data).hexdigest(), len(data),
                zlib.crc32(data))).encode('ascii')
        pins = pins.replace(b'};', row + b'};')
        targets = ['WINXT\\\\' + name, 'WINXT\\\\FILES\\\\' + name]
        if name.endswith('.GR2'):
            targets.insert(0, 'W30\\\\' + name)
        for target in targets:
            row = ('{"%s","%s",%dUL,0},\r\n' %
                   (target, name, len(data))).encode('ascii')
            files = files.replace(b'};\r\n#define NFILES',
                                  row + b'};\r\n#define NFILES')
            row = ('0x00000000UL, /* %s */\r\n};' % target).encode('ascii')
            crcs = crcs.replace(b'};', row)
    files = files.replace(b'a:CGA.GR2', b'a:TANDYGR.GR2')
    files = files.replace(b'"SETUP.INF",49840UL,2}',
                          b'"SETUP.INF",49848UL,2}')
    ident = (HERE / 'TGSETID.H').read_bytes()
    sha = re.search(rb'TG_SETUP_SHA "([0-9a-f]{64})"', ident)[1]
    crc = re.search(rb'TG_SETUP_CRC (0x[0-9a-f]{8}UL)', ident)[1]
    files = re.sub(rb'(#define SETUP_OUTPUT_SHA ")[0-9a-f]{64}',
                   lambda m: m[1] + sha, files)
    files = re.sub(rb'(#define SETUP_OUTPUT_CRC )0x[0-9a-f]+UL',
                   lambda m: m[1] + crc, files)
    return pins, files, crcs
