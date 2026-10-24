"""Opt-in resource-only compact160 candidates; no emulator or compiler.

Append replacements and redirect existing NE resource descriptors. Segments,
relocations, timings, framebuffer addresses, device caps and default packages
are preserved. Pinned separate inputs prevent B000/B800 substitution.
"""
import argparse
import hashlib
import json
import struct
import zipfile
from pathlib import Path
import FONT
import UI

ROOT = FONT.ROOT
PACKRES = FONT.load('compact_packres', ROOT / 'src/tandysw/PACKRES.PY')
SHA = lambda data: hashlib.sha256(data).hexdigest()
TARGETS = {
    'yamaha-b800': dict(archive='YAMAHA-B800-CANDIDATE03.ZIP', input='YAM160.DRV',
        sha256='a3d339a3f1e831bd8499fb2b0a28c683bf08f9fbeb0e96689dc3f6ef9a627c8a',
        output='C16B800.DRV', label='COMPACT160 Yamaha B800 EMULATOR ONLY', segment='B800'),
    'pc1-b000': dict(archive='PC1-B000-CANDIDATE03.ZIP', input='PC1YAMA.DRV',
        sha256='8c73d52d6811fff071dd252343c33702a1cfea0b2613ec8b20faf5a739da2a08',
        output='C16B000.DRV', label='COMPACT160 PC1 B000 UNTESTED', segment='B000'),
}


def descriptors(data):
    if len(data) < 64 or data[:2] != b'MZ':
        raise ValueError('not MZ')
    ne = struct.unpack_from('<I', data, 60)[0]
    if data[ne:ne + 2] != b'NE':
        raise ValueError('not NE')
    table = ne + struct.unpack_from('<H', data, ne + 36)[0]
    end = ne + struct.unpack_from('<H', data, ne + 38)[0]
    shift = struct.unpack_from('<H', data, table)[0]
    if shift > 15:
        raise ValueError('bad resource alignment')
    pos, records = table + 2, {}
    while pos + 2 <= end:
        typ = struct.unpack_from('<H', data, pos)[0]
        if typ == 0:
            return records, shift
        if not typ & 0x8000 or pos + 8 > end:
            raise ValueError('bad resource type')
        count = struct.unpack_from('<H', data, pos + 2)[0]
        pos += 8
        for _ in range(count):
            if pos + 12 > end:
                raise ValueError('short resource table')
            off, length, flags, rid, handle, usage = struct.unpack_from('<6H', data, pos)
            if not rid & 0x8000 or off << shift >= len(data) or (off + length) << shift > len(data):
                raise ValueError('bad resource range/name')
            key = (typ & 0x7fff, rid & 0x7fff)
            if key in records:
                raise ValueError('duplicate resource')
            records[key] = (pos, off << shift, length << shift)
            pos += 12
    raise ValueError('missing resource terminator')


def overlay(original):
    records, shift = descriptors(original)
    changes = {(2, k): v for k, v in UI.bitmaps().items()}
    for key, edit in (((0x7006, 1), UI.config), ((0x7006, 3), UI.font_requests)):
        _, off, length = records[key]
        changes[key] = edit(original[off:off + length])
    out = bytearray(original)
    unit = 1 << shift
    for key, payload in sorted(changes.items()):
        if key not in records:
            raise ValueError('missing resource ' + repr(key))
        pos = records[key][0]
        out += bytes((-len(out)) % unit)
        start = len(out)
        padded = (len(payload) + unit - 1) // unit * unit
        if start // unit > 0xffff or padded // unit > 0xffff:
            raise ValueError('resource offset overflow')
        out += payload + bytes(padded - len(payload))
        struct.pack_into('<HH', out, pos, start // unit, padded // unit)
    # All original bytes other than resource offset/length fields remain.
    allowed = {x for key in changes for x in range(records[key][0], records[key][0] + 4)}
    if any(a != b and i not in allowed for i, (a, b) in enumerate(zip(original, out))):
        raise ValueError('unexpected non-resource edit')
    actual = {(t, i): d for t, i, f, d in PACKRES.inspect_ne(out)}
    for key, payload in changes.items():
        if actual[key][:len(payload)] != payload:
            raise ValueError('resource round trip failed')
    return bytes(out), sorted(changes)


def setup(target):
    t = TARGETS[target]
    return ('; Experimental opt-in clone-only candidate. Native qualification PENDING.\n'
        '[data]\nVersion="3.0"\n[disks]\na=.,"' + t['label'] + '",OEMSETUP.INF\n'
        '[display]\nC16=a:' + t['output'] + ',"' + t['label'] +
        '","200,96,48",a:CGA.GR2,a:CGALOGO.LGO,,,,a:WXTSPL01.RLE\n'
        '[sysfonts]\na:C16SYS.FON,"XT Compact System","200,96,48"\n'
        '[fixedfonts]\na:C16FIX.FON,"XT Compact Fixed","200,96,48"\n'
        '[oemfonts]\na:C16OEM.FON,"XT Compact Terminal","200,96,48",1\n')


def build(target, out):
    t = TARGETS[target]
    if out.exists():
        raise ValueError('choose a fresh output directory')
    archive = ROOT / 'downloads/experimental/yamaha-candidate03' / t['archive']
    with zipfile.ZipFile(archive) as z:
        original = z.read(t['input'])
        # Existing first-party splash only; proprietary support stays external.
        splash = z.read('WXTSPL01.RLE')
        splash_notice = z.read('LOGOLIC.TXT')
    if SHA(original) != t['sha256']:
        raise ValueError('wrong target or modified baseline')
    driver, changes = overlay(original)
    font_record = FONT.write(out)
    (out / t['output']).write_bytes(driver)
    (out / 'WXTSPL01.RLE').write_bytes(splash)
    (out / 'LOGOLIC.TXT').write_bytes(splash_notice)
    (out / 'FONTLIC.TXT').write_bytes((ROOT / 'tools/XTFONTS/LICENSE').read_bytes())
    FONT.XT.textfile(out / 'OEMSETUP.INF', setup(target))
    record = dict(target=target, framebuffer_segment=t['segment'], baseline_sha256=SHA(original),
        driver_sha256=SHA(driver), resource_edits=changes,
        original_prefix='unchanged except existing resource offset/length fields',
        native_runtime='NOT_TESTED', hardware='NOT_TESTED', fonts=font_record,
        files={p.name: SHA(p.read_bytes()) for p in sorted(out.iterdir()) if p.is_file()})
    FONT.XT.textfile(out / 'BUILD.JSN', json.dumps(record, ensure_ascii=True, indent=2) + '\n')
    return record


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--target', required=True, choices=sorted(TARGETS))
    p.add_argument('--out', type=Path, required=True)
    a = p.parse_args()
    try:
        rec = build(a.target, a.out.resolve())
    except (ValueError, KeyError) as exc:
        p.error(str(exc))
    print(a.target, rec['driver_sha256'], 'resource build PASS; runtime NOT_TESTED')
