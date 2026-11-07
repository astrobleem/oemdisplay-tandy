"""Independent bitmap/width checks and optional decoded-font contact sheet."""
import argparse
import importlib.machinery
from pathlib import Path
import re
import struct
import sys
import tempfile
import zipfile

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path_importer_cache[str(HERE)] = importlib.machinery.FileFinder(
    str(HERE), (importlib.machinery.SourceFileLoader, ['.py', '.PY']))
import BUILD as B


def container(data):
    # Decode independently of the producer/INSPECT helper. Verify both the
    # actual Control Panel description contract and the NE resource bounds.
    assert data[:2] == b'MZ'
    ne = struct.unpack_from('<I', data, 60)[0]
    assert data[ne:ne + 2] == b'NE'
    start = struct.unpack_from('<I', data, ne + 44)[0]
    size = struct.unpack_from('<H', data, ne + 32)[0]
    length = data[start]
    assert size == length + 4 and start + size <= len(data)
    assert data[start + 1 + length:start + size] == b'\0\0\0'
    description = data[start + 1:start + 1 + length].decode('ascii')
    assert description[:7] == 'FONTRES' and ':' in description[8:]
    label = description[8:].split(':', 1)[1].strip(' ')
    assert label and label == description.split(':', 1)[1].strip(' ')
    p = ne + struct.unpack_from('<H', data, ne + 36)[0]
    shift = struct.unpack_from('<H', data, p)[0]
    assert shift == 4
    p += 2
    payloads = {}
    spans = []
    while struct.unpack_from('<H', data, p)[0]:
        kind, count, reserved = struct.unpack_from('<HHI', data, p)
        assert count == 1 and reserved == 0 and kind not in payloads
        p += 8
        off, length, flags, rid, handle, usage = struct.unpack_from('<HHHHHH', data, p)
        p += 12
        off, length = off << shift, length << shift
        assert off >= start + size and off + length <= len(data)
        assert handle == usage == 0
        spans.append((off, off + length))
        payloads[kind] = (rid, flags, data[off:off + length])
    assert sorted(payloads) == [0x8007, 0x8008, 0x800f]
    assert all(a[1] <= b[0] for a, b in zip(sorted(spans), sorted(spans)[1:]))
    raw = payloads[0x8008][2]
    fsize = struct.unpack_from('<I', raw, 2)[0]
    assert not any(raw[fsize:])
    raw = raw[:fsize]
    font_id = payloads[0x8008][0] & 0x7fff
    directory = payloads[0x8007][2]
    assert struct.unpack_from('<HH', directory) == (1, font_id)
    assert directory[4:113] == raw[:109]
    assert directory[113:118] == b'\0' * 5
    face_at = struct.unpack_from('<I', raw, 105)[0]
    face = raw[face_at:].split(b'\0', 1)[0]
    assert directory[118:].split(b'\0', 1)[0] == face
    height = struct.unpack_from('<H', raw, 88)[0]
    vdpi, hdpi = struct.unpack_from('<HH', raw, 70)
    expected = 'FONTRES %d,%d,%d : %s %d-row' % (hdpi * 100 // vdpi, hdpi, vdpi, face.decode('ascii'), height)
    assert description == expected
    return label, payloads


def pixels(raw, code):
    first, last, fallback = raw[95], raw[96], raw[97]
    if not first <= code <= last:
        code = first + fallback
    width, offset = struct.unpack_from('<HH', raw, 118 + (code-first)*4)
    height = struct.unpack_from('<H', raw, 88)[0]
    return [[(raw[offset + (x//8)*height + y] >> (7-x%8)) & 1
             for x in range(width)] for y in range(height)]


def run(folder):
    count = 0
    allrows = {}
    labels = set()
    for path in sorted(folder.glob('*.FON')):
        label, _ = container(path.read_bytes())
        assert label not in labels, 'Duplicate Control Panel registration key'
        labels.add(label)
        # Native CONTROL's prefix test is case-sensitive, and ':' is required.
        data = bytearray(path.read_bytes())
        ne = struct.unpack_from('<I', data, 60)[0]
        start = struct.unpack_from('<I', data, ne + 44)[0]
        for where in (start + 1, data.index(ord(':'), start + 1, start + 1 + data[start])):
            bad = bytearray(data)
            bad[where] = ord('x')
            try:
                container(bytes(bad))
            except AssertionError:
                pass
            else:
                raise AssertionError('Invalid Control Panel container accepted')
    assert len(labels) == 9
    with tempfile.TemporaryDirectory() as temp:
        repeat = B.build(Path(temp) / 'fonts')
        for path in sorted(folder.iterdir()):
            assert path.read_bytes() == (repeat / path.name).read_bytes(), path.name
    for prefix, face, source, weight in B.FAMILIES:
        old = B.strike((HERE / 'SOURCE' / source).read_bytes())
        for height in B.HEIGHTS:
            name = prefix + str(height) + '.FON'
            assert re.fullmatch(r'[A-Z0-9]{1,8}\.FON', name)
            data = (folder / name).read_bytes()
            ne = struct.unpack_from('<I', data, 60)[0]
            assert data[ne:ne+2] == b'NE'
            assert struct.unpack_from('<H', data, ne+28)[0] == 0  # no code/data segments
            assert struct.unpack_from('<H', data, ne+62)[0] == 0x300
            entries = B.resources(data)[1]
            assert [e[0] for e in entries] == [0x8007,0x8008,0x800f]
            raw = B.strike(data)
            h = B.fontinfo(raw)
            assert h['face'] == face and h['height'] == height
            assert h['pix_width'] == 0 and h['pitch_family'] & 1
            assert h['charset'] == 0 and h['weight'] == weight
            assert len(raw) < 65536 and h['max_width'] == max(h['widths'])
            widths = h['widths']
            assert min(widths) < max(widths)
            assert widths[ord('i')-32] < widths[ord('W')-32]
            assert widths[ord('.')-32] < widths[ord('M')-32]
            glyphs = [pixels(raw, c) for c in range(256)]
            allrows[name] = glyphs
            for code in range(256):
                rows = glyphs[code]
                assert len(rows) == height and len(set(map(len,rows))) == 1
                assert all(row[-1] == 0 for row in rows), (name, code, 'spacing')
                if code < 32:
                    assert rows == glyphs[128]
                count += 1
            # Compare every CP437-mappable ANSI glyph to an independent direct
            # bit-table decode of the input, allowing only removed blank sides,
            # a final spacing column and the documented vertical row map.
            for code in range(32,256):
                char = B.decode_code(code,0)
                try:
                    cp = char.encode('cp437')[0]
                except (UnicodeEncodeError, AttributeError):
                    continue
                if B.decode_code(cp,255) != char:
                    continue
                source_rows = pixels(old,cp)
                cols = [x for x in range(8) if any(r[x] for r in source_rows)]
                cut = [r[min(cols):max(cols)+1] for r in source_rows] if cols else [[] for r in source_rows]
                if height == 12:
                    cut = [[0]*len(cut[0]) if y is None else cut[y] for y in B.YMAP]
                actual = glyphs[code]
                expected = [r + [0]*(len(actual[0])-len(r)) for r in cut]
                assert actual == expected, (name,code,'source ink changed')
            for text in ('File Edit View Help','OK   Cancel','Save As...'):
                assert sum(widths[ord(c)-32] for c in text) <= 144, (name,text)
            print('%s: %s, %d rows, widths %d..%d, %d bytes' %
                  (name,face,height,min(widths),max(widths),len(data)))
    for height in B.HEIGHTS:
        for a,b in [('T1P','T2P'),('T1P','TKP'),('T2P','TKP')]:
            left,right=allrows[a+str(height)+'.FON'],allrows[b+str(height)+'.FON']
            differences=sum(left[c] != right[c] for c in range(32,127))
            assert differences >= 4, (a,b,'merely renamed face')
            print('%s/%s at %d px: %d ASCII glyphs differ' % (a,b,height,differences))
    with zipfile.ZipFile(B.ROOT/'downloads/FRESH/CGA.ZIP') as z:
        for name in ('CG1HELV.FON','CG2HELV.FON','CG6HELV.FON'):
            original = z.read('CGA/'+name)
            current = (folder/name).read_bytes()
            assert current == B.helv_container(original)
            assert B.strike(current) == B.strike(original)
            old_resources = {e[0]: (e[1], e[2], original[e[3]:e[3]+e[4]]) for e in B.resources(original)[1]}
            assert container(current)[1] == old_resources
    print('PASS: nine Control Panel containers and unique keys; complete Helv resources preserved.')
    print('PASS: %d all-byte glyph/advance checks; exact reproduction, original ink, distinct faces and fitting.' % count)


def specimen(folder, out):
    from PIL import Image, ImageDraw
    files = ['CG1HELV.FON','CG2HELV.FON'] + [p+str(h)+'.FON' for p,_,_,_ in B.FAMILIES for h in B.HEIGHTS]
    samples = ['Windows XT   File Edit View Help',
               'The quick brown fox jumps.  Il1 O0 MWmw',
               '0123456789   Save As...  [ OK ] [ Cancel ]']
    im=Image.new('RGB',(1000,970),'#f6f2e8')
    draw=ImageDraw.Draw(im)
    for row,name in enumerate(files):
        raw=B.strike((folder/name).read_bytes());h=B.fontinfo(raw)
        top=18+row*118
        draw.text((20,top),name+'  |  '+h['face']+'  |  '+str(h['height'])+' bitmap rows',fill='#445044')
        for j,text in enumerate(samples):
            x=20;y=top+20+j*30
            for ch in text:
                glyph=pixels(raw,ord(ch))
                for gy,line in enumerate(glyph):
                    for gx,ink in enumerate(line):
                        if ink:draw.rectangle((x+gx*2,y+gy*2,x+gx*2+1,y+gy*2+1),fill='#182b23')
                x+=len(glyph[0])*2
    im.save(out)


if __name__ == '__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--fonts',type=Path,default=HERE/'BIN')
    p.add_argument('--specimen',type=Path)
    a=p.parse_args();run(a.fonts)
    if a.specimen:specimen(a.fonts,a.specimen)
