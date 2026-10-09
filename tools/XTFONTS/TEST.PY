"""Independent binary bounds/contract checks and deterministic rebuild test."""
import argparse
import hashlib
import json
import struct
import tempfile
from pathlib import Path
from BUILD import build, read_glyph, textfile
from INSPECT import resources, fontinfo, word, dword


def require(condition, message):
    if not condition:
        raise ValueError(message)


def validate_fnt(data, contract=None):
    require(len(data) >= 118, 'Truncated header')
    require(word(data, 0) == 0x200, 'Only real-mode FNT 2.x supported')
    require(dword(data, 2) == len(data), 'FNT declared size mismatch')
    info = fontinfo(data)
    require(info['type'] == 0, 'Not bitmap file data')
    require(0 < info['height'] <= 32, 'Height outside renderer bounds')
    require(0 < info['ascent'] <= info['height'], 'Ascent outside cell')
    require(info['internal'] <= info['ascent'], 'Leading outside ascent')
    require(info['first'] <= info['last'], 'Invalid character range')
    count = info['last'] - info['first'] + 2
    tableend = 118 + 4 * count
    require(tableend <= len(data), 'Truncated character table')
    bitstart, face = dword(data, 113), dword(data, 105)
    require(tableend <= bitstart < face < len(data), 'Bad offsets/order')
    require(bitstart % 2 == 0, 'Unaligned bitmap')
    require(info['width_bytes'] % 2 == 0, 'Odd combined bitmap stride')
    require(face - bitstart == info['width_bytes'] * info['height'],
            'Bitmap size/stride mismatch')
    require(dword(data, 101) == 0 and dword(data, 109) == 0,
            'Unexpected device or memory bitmap pointer')
    require(data[-1] == 0 and data[face:].count(0) == 1,
            'Invalid face name terminator')
    require(info['default'] < count - 1 and info['break'] < count - 1,
            'Default/break outside font')
    cursor = bitstart
    for i in range(count):
        width, off = struct.unpack_from('<HH', data, 118 + i * 4)
        require(0 < width <= info['max_width'], 'Glyph width out of bounds')
        require(off == cursor, 'Gap, overlap, or unordered glyph offset')
        size = (width + 7) // 8 * info['height']
        require(off + size <= face and off + size < 65536,
                'Glyph data outside bitmap/16-bit offset boundary')
        for column in range((width + 7) // 8):
            valid = min(8, width - column * 8)
            mask = (1 << (8 - valid)) - 1
            require(not any(b & mask for b in data[
                off + column * info['height']:off + (column + 1) * info['height']]),
                'Set pixels beyond advance width')
        if i == count - 1:
            require(width == 8, 'Absolute blank width contract changed')
            require(not any(data[off:off + size]), 'Nonblank absolute space')
        cursor += size
    require(not any(data[cursor:face]), 'Nonzero stride padding')
    if contract:
        for key, value in contract.items():
            if key not in ('size', 'width_bytes'):
                require(info[key] == value, 'Contract changed: ' + key)
    return info


def validate_fon(data, item):
    require(len(data) >= 64 and data[:2] == b'MZ', 'Missing DOS header')
    ne = dword(data, 60)
    require(ne >= 64 and ne + 64 <= len(data) and data[ne:ne + 2] == b'NE',
            'Missing NE header')
    require(word(data, ne + 12) == 0x8300 and data[ne + 54] == 2 and
            word(data, ne + 62) == 0x300, 'Wrong Win3 resource-only module flags')
    require(word(data, ne + 28) == word(data, ne + 30) == 0,
            'Resource-only module has segments/imported modules')
    entry, entrysize = word(data, ne + 4), word(data, ne + 6)
    require(entrysize == 2 and data[ne + entry:ne + entry + 2] == b'\0\0',
            'Nonempty entry table')
    imports = word(data, ne + 42)
    require(ne + imports < len(data) and data[ne + imports] == 0,
            'Resource-only module import-name table is not empty')
    names, namelen = dword(data, ne + 44), word(data, ne + 32)
    require(ne + entry + entrysize <= names and names + namelen <= len(data),
            'Nonresident name bounds')
    module, entries = resources(data)
    require(module == item['module'], 'Module identity changed')
    expected = next(r for r in item['resources'] if 'font' in r)
    keys = [(k, rid & 0x7fff) for k, rid, _, _, _ in entries]
    require(keys == [(0x8007, 1), (0x8008, expected['id']), (0x800f, 1)],
            'Unexpected resource types/IDs')
    spans = sorted((off, off + size) for _, _, _, off, size in entries)
    require(all(a[1] <= b[0] for a, b in zip(spans, spans[1:])),
            'Resources overlap')
    for _, _, _, off, size in entries:
        require(off % 16 == size % 16 == 0, 'Resource alignment changed')
    _, _, _, off, size = entries[1]
    raw = data[off:off + dword(data, off + 2)]
    require(len(raw) <= size, 'FNT exceeds resource')
    info = validate_fnt(raw, expected['font'])
    _, _, _, doff, dsize = entries[0]
    directory = data[doff:doff + dsize]
    require(word(directory, 0) == 1 and word(directory, 2) == expected['id'],
            'FONTDIR count/ID mismatch')
    prefix = bytearray(raw[:109])
    faceoff = dword(raw, 105)
    require(directory[:117] == struct.pack('<HH', 1, expected['id']) +
            prefix + bytes(4), 'FONTDIR metadata mismatch')
    require(directory[117:118] == b'\0' and directory[118:].startswith(raw[faceoff:]),
            'FONTDIR name mismatch')
    return info


def main(out):
    contracts = json.loads(Path(__file__).with_name('CONTRACT.JSON').read_text())
    report = {'kind': 'Host structural validation; no Win16 qualification',
              'native_qualified': False, 'fonts': {}, 'mutation_refusals': []}
    for item in contracts:
        data = (out / item['filename']).read_bytes()
        info = validate_fon(data, item)
        broken = bytearray(data)
        ne = dword(broken, 60)
        struct.pack_into('<H', broken, ne + 42, dword(broken, ne + 44) - ne)
        try:
            validate_fon(bytes(broken), item)
        except ValueError:
            report['mutation_refusals'].append(item['filename'] + ':import-table')
        else:
            raise ValueError('Nonresident description accepted as import table')
        report['fonts'][item['filename']] = {
            'sha256': hashlib.sha256(data).hexdigest(), 'bytes': len(data),
            'metrics_and_all_advances_preserved': True,
            'glyphs_in_range': info['last'] - info['first'] + 1}
        raw = (out / item['filename'].replace('.FON', '.FNT')).read_bytes()
        require(read_glyph(raw, -1) == read_glyph(raw, info['first'] + info['default']),
                'Below-range default mismatch')
        require(read_glyph(raw, 256) == read_glyph(raw, info['first'] + info['default']),
                'Above-range default mismatch')
        # Independent negative cases exercise real corruption paths.
        for name, at, value in [('height', 88, 0), ('width', 118, 0xffff),
                                ('bitmap', 113, 0xffff), ('offset', 120, 0xffff),
                                ('stride', 99, 1), ('default', 97, 255)]:
            broken = bytearray(raw)
            if name == 'default':
                broken[at] = value
            else:
                struct.pack_into('<H', broken, at, value)
            try:
                validate_fnt(bytes(broken))
            except (ValueError, IndexError, struct.error):
                report['mutation_refusals'].append(item['filename'] + ':' + name)
            else:
                raise ValueError('Corruption accepted: ' + name)
        for end in (0, 60, 117, 118, len(raw) - 1):
            try:
                validate_fnt(raw[:end])
            except (ValueError, IndexError, struct.error):
                report['mutation_refusals'].append(item['filename'] + ':truncate%d' % end)
            else:
                raise ValueError('Truncation accepted')
    with tempfile.TemporaryDirectory(prefix='xtfont-rebuild-') as temp:
        repeat = Path(temp) / 'REPEAT'
        build(repeat)
        for file in repeat.iterdir():
            require(file.read_bytes() == (out / file.name).read_bytes(),
                    'Non-reproducible output: ' + file.name)
        report['byte_identical_repeat_files'] = len(list(repeat.iterdir()))
    require((out / 'TXTSYS.FON').read_bytes() != (out / 'CGASYS.FON').read_bytes(),
            'Text-mode font accidentally proportional')
    report['total_in_range_glyphs'] = sum(v['glyphs_in_range'] for v in report['fonts'].values())
    textfile(out / 'TEST.JSON', json.dumps(report, indent=2) + '\n')
    print('PASS', report['total_in_range_glyphs'], 'glyph boundaries;',
          len(report['mutation_refusals']), 'corruptions refused;',
          report['byte_identical_repeat_files'], 'identical rebuild files')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    main(args.out)
