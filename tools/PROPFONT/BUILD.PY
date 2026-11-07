"""Build optional proportional Tandy fonts, without changing System fonts.

Tandy bitmap inputs: VileR's Oldschool PC Font Pack v2.2 Windows bitmap
release, https://int10h.org/oldschool-pc-fonts/download/ . Keep SOURCE's
unmodified notice. Unavailable ANSI characters use the existing original
XT Pixels artwork. FNT/NE writing reuses the unchanged XT Pixels writer.
"""
import argparse
import importlib.machinery
from pathlib import Path
import shutil
import struct
import sys
import zipfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
KIT = ROOT / 'tools' / 'XTFONTS'
sys.path.insert(0, str(KIT))
sys.path_importer_cache[str(KIT)] = importlib.machinery.FileFinder(
    str(KIT), (importlib.machinery.SourceFileLoader, ['.py', '.PY']))
writer = importlib.machinery.SourceFileLoader('xt_pixel_writer', str(KIT/'BUILD.PY')).load_module()
fnt, fon, read_glyph, decode_code, G = writer.fnt, writer.fon, writer.read_glyph, writer.decode_code, writer.G
from INSPECT import resources, fontinfo, dword

FAMILIES = (
    ('T1P', 'XT Tandy I', 'T1SRC.FON', 700),
    ('T2P', 'XT Tandy II', 'T2SRC.FON', 700),
    ('TKP', 'XT Tandy 2K', 'TKSRC.FON', 400),
)
HEIGHTS = (8, 12)
YMAP = (None, 0, 0, 1, 2, 3, 3, 4, 5, 6, 7, 7)


def installable(raw, module, rid, label):
    # Win3 Control Panel requires uppercase FONTRES and a colon in the
    # first NE nonresident name. The unique suffix is the WIN.INI key.
    # AddFontResource alone does not enforce this consumer-install rule.
    h = fontinfo(raw)
    description = 'FONTRES %d,%d,%d : %s' % (
        h['horiz_res'] * 100 // h['vert_res'], h['horiz_res'], h['vert_res'], label)
    return fon(raw, module, rid, description)


def helv_container(data):
    module, entries = resources(data)
    fonts = [e for e in entries if e[0] == 0x8008]
    if len(fonts) != 1:
        raise ValueError('Expected one preserved Helv strike')
    raw = strike(data)
    h = fontinfo(raw)
    if h['face'] != 'Helv' or h['height'] not in (5, 6, 8):
        raise ValueError('Unexpected inherited Helv font')
    return installable(raw, module, fonts[0][1] & 0x7fff, 'Helv %d-row' % h['height'])


def strike(data):
    entries = [e for e in resources(data)[1] if e[0] == 0x8008]
    if len(entries) != 1:
        raise ValueError('Expected exactly one bitmap strike')
    offset = entries[0][3]
    raw = data[offset:offset + dword(data, offset + 2)]
    if fontinfo(raw)['version'] != 0x200:
        raise ValueError('Expected FNT 2.x')
    return raw


def trim(rows):
    columns = [x for x in range(len(rows[0])) if any(row[x] for row in rows)]
    if not columns:
        return [[] for row in rows]
    return [row[min(columns):max(columns) + 1] for row in rows]


def artwork(source):
    raw = strike(source)
    info = fontinfo(raw)
    if (info['height'], info['pix_width'], info['charset'], info['first'], info['last']) != (8, 8, 255, 0, 255):
        raise ValueError('Expected the original 8x8 CP437 Tandy resource')
    originals = {decode_code(c, 255): trim(read_glyph(raw, c)) for c in range(256)}
    rows = {}
    for code in range(32, 256):
        char = decode_code(code, 0)
        if char in originals:
            value = originals[char]
        else:
            value = trim([[int(p == '#') for p in line] for line in G.get(char, G['\u25a1'])])
        rows[char] = value
    return rows


def build_font(prefix, face, source, weight, height):
    rows = artwork(source)
    widths = [len(rows[decode_code(c, 0)][0]) + 1 if any(map(any, rows[decode_code(c, 0)])) else 4
              for c in range(32, 256)]
    alphabet = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'
    average = (sum(widths[ord(c) - 32] for c in alphabet) + 26) // 52
    contract = dict(type=0, points=11 if height == 8 else 10,
                    vert_res=48 if height == 8 else 72, horiz_res=96,
                    ascent=7 if height == 8 else 10, internal=1 if height == 8 else 2,
                    external=1, italic=0, underline=0, strikeout=0,
                    weight=weight, charset=0, pix_width=0, height=height,
                    pitch_family=0x21, avg_width=average, max_width=max(widths),
                    first=32, last=255, default=128-32, **{'break':0},
                    widths=widths, face=face)
    def glyph(char, width, cell_height, fixed=False):
        value = rows.get(char, rows[None])
        if cell_height == 12:
            value = [[0] * len(value[0]) if y is None else value[y] for y in YMAP]
        return [row + [0] * (width - len(row)) for row in value]
    old = writer.glyph
    try:
        writer.glyph = glyph
        raw, _ = fnt(contract)
    finally:
        writer.glyph = old
    # Do not mislabel third-party glyph data with the original writer's MIT tag.
    raw = bytearray(raw)
    credit = b'VileR Tandy; XT Pixels; Windows XT proportional 2026'
    raw[6:66] = credit + bytes(60 - len(credit))
    name = prefix + str(height)
    return installable(bytes(raw), name, 1, face + ' ' + str(height) + '-row')


def build(out):
    out.mkdir(parents=True, exist_ok=False)
    for prefix, face, name, weight in FAMILIES:
        for height in HEIGHTS:
            (out / (prefix + str(height) + '.FON')).write_bytes(
                build_font(prefix, face, (HERE / 'SOURCE' / name).read_bytes(), weight, height))
    # Preserve all Helv font resource bytes and names; only make their
    # container descriptions installable through Win3 Control Panel.
    with zipfile.ZipFile(ROOT / 'downloads' / 'FRESH' / 'CGA.ZIP') as archive:
        for name in ('CG1HELV.FON', 'CG2HELV.FON', 'CG6HELV.FON'):
            (out / name).write_bytes(helv_container(archive.read('CGA/' + name)))
    shutil.copyfile(HERE / 'SOURCE' / 'LICENSE.TXT', out / 'LICENSE.TXT')
    shutil.copyfile(KIT / 'LICENSE', out / 'FONTLIC.TXT')
    shutil.copyfile(HERE / 'README.TXT', out / 'README.TXT')
    return out


def package(folder, archive):
    with zipfile.ZipFile(archive, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for p in sorted(folder.iterdir()):
            if p.is_file():
                item = zipfile.ZipInfo(p.name, (2026, 11, 7, 0, 0, 0))
                item.compress_type = zipfile.ZIP_DEFLATED
                item.external_attr = 0o100644 << 16
                z.writestr(item, p.read_bytes())


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--zip', type=Path)
    args = parser.parse_args()
    build(args.out)
    if args.zip:
        package(args.out, args.zip)
    print('Built six proportional Tandy strikes and three preserved Helv strikes.')
