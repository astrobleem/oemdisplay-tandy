"""Process-private modern Windows GDI font check, NOT native Win3 proof."""
import argparse
import ctypes as C
import json
import tempfile
from pathlib import Path
from PIL import Image
import FONT
import TEST


class TM(C.Structure):
    _fields_ = [(s, C.c_long) for s in ('height', 'ascent', 'descent', 'internal', 'external',
        'avg', 'maximum', 'weight', 'overhang', 'aspect_x', 'aspect_y')] + [(s, C.c_ubyte) for s in
        ('first', 'last', 'default', 'break_char', 'italic', 'underline', 'strikeout', 'pitch', 'charset')]


class BI(C.Structure):
    _fields_ = [('size', C.c_uint), ('width', C.c_long), ('height', C.c_long),
        ('planes', C.c_ushort), ('bits', C.c_ushort), ('compression', C.c_uint),
        ('image_size', C.c_uint), ('xres', C.c_long), ('yres', C.c_long),
        ('used', C.c_uint), ('important', C.c_uint)]


def run(out):
    out.mkdir(parents=True, exist_ok=False)
    g = C.WinDLL('gdi32', use_last_error=True)
    sig = {
        'AddFontResourceExW': ([C.c_wchar_p, C.c_uint, C.c_void_p], C.c_int),
        'RemoveFontResourceExW': ([C.c_wchar_p, C.c_uint, C.c_void_p], C.c_int),
        'CreateCompatibleDC': ([C.c_void_p], C.c_void_p),
        'CreateDIBSection': ([C.c_void_p, C.c_void_p, C.c_uint, C.POINTER(C.c_void_p), C.c_void_p, C.c_uint], C.c_void_p),
        'CreateFontW': ([C.c_int] * 5 + [C.c_uint] * 8 + [C.c_wchar_p], C.c_void_p),
        'SelectObject': ([C.c_void_p, C.c_void_p], C.c_void_p),
        'GetTextMetricsA': ([C.c_void_p, C.POINTER(TM)], C.c_int),
        'GetTextFaceW': ([C.c_void_p, C.c_int, C.c_wchar_p], C.c_int),
        'TextOutA': ([C.c_void_p, C.c_int, C.c_int, C.c_char_p, C.c_int], C.c_int),
        'SetTextColor': ([C.c_void_p, C.c_uint], C.c_uint),
        'SetBkColor': ([C.c_void_p, C.c_uint], C.c_uint),
        'GdiFlush': ([], C.c_int), 'DeleteObject': ([C.c_void_p], C.c_int),
        'DeleteDC': ([C.c_void_p], C.c_int),
    }
    for name, (args, result) in sig.items():
        function = getattr(g, name)
        function.argtypes, function.restype = args, result
    records = []
    with tempfile.TemporaryDirectory(prefix='compactgdi-') as scratch:
        for index, (name, values) in enumerate(FONT.FACES.items()):
            face, module, rid, charset, fixed, weight, family, internal, external = values
            alias = 'XT Compact Audit ' + str(index)
            font, coverage = FONT.fnt(alias, charset, fixed, weight, family, internal, external)
            path = Path(scratch) / name
            path.write_bytes(FONT.XT.fon(font, 'C16AUDIT', rid))
            loaded = g.AddFontResourceExW(str(path), 16, None)
            assert loaded == 1, (name, 'font load', C.get_last_error())
            dc = dib = handle = oldfont = oldbitmap = None
            try:
                dc = g.CreateCompatibleDC(None)
                bi = BI(C.sizeof(BI), 320, -100, 1, 32, 0, 320 * 100 * 4, 0, 0, 0, 0)
                pointer = C.c_void_p()
                dib = g.CreateDIBSection(dc, C.byref(bi), 0, C.byref(pointer), None, 0)
                assert dc and dib
                oldbitmap = g.SelectObject(dc, dib)
                handle = g.CreateFontW(8, 0, 0, 0, weight, 0, 0, 0, charset, 0, 0, 3, family, alias)
                assert handle
                oldfont = g.SelectObject(dc, handle)
                actualface = C.create_unicode_buffer(64)
                assert g.GetTextFaceW(dc, 64, actualface) and actualface.value == alias
                tm = TM()
                assert g.GetTextMetricsA(dc, C.byref(tm))
                expected = TEST.INSPECT.fontinfo(font)
                assert (tm.height, tm.ascent, tm.internal, tm.external, tm.avg, tm.maximum, tm.weight) == (
                    8, 7, internal, external, 4, expected['max_width'], weight), name
                C.memset(pointer, 255, bi.image_size)
                g.SetTextColor(dc, 0)
                g.SetBkColor(dc, 0xffffff)
                expectedimage = Image.new('RGB', (320, 100), 'white')
                for i, code in enumerate(range(32, 127)):
                    x, y = 2 + i % 24 * 13, 2 + i // 24 * 12
                    assert g.TextOutA(dc, x, y, bytes([code]), 1)
                    for gy, row in enumerate(TEST.pixels(font, code)):
                        for gx, ink in enumerate(row):
                            if ink:
                                expectedimage.putpixel((x + gx, y + gy), (0, 0, 0))
                g.GdiFlush()
                actual = Image.frombytes('RGB', (320, 100), C.string_at(pointer, bi.image_size), 'raw', 'BGRX')
                assert actual.tobytes() == expectedimage.tobytes(), (name, 'ASCII raster mismatch')
                actual.save(out / ('GDI' + str(index) + '.PNG'))
                records.append(dict(font=name, loaded_process_private=True, ascii_pixel_checks=95,
                    height=tm.height, ascent=tm.ascent, average=tm.avg, maximum=tm.maximum,
                    weight=tm.weight, match='EXACT', native_win3='NOT_TESTED'))
            finally:
                if dc and oldfont:
                    g.SelectObject(dc, oldfont)
                if handle:
                    g.DeleteObject(handle)
                if dc and oldbitmap:
                    g.SelectObject(dc, oldbitmap)
                if dib:
                    g.DeleteObject(dib)
                if dc:
                    g.DeleteDC(dc)
                assert g.RemoveFontResourceExW(str(path), 16, None), 'temporary font cleanup failed'
    result = dict(status='PASS', scope='MODERN HOST GDI ONLY', fonts=records, native_win3='NOT_TESTED')
    FONT.XT.textfile(out / 'HOSTGDI.JSN', json.dumps(result, indent=2) + '\n')
    print(json.dumps(result))


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--out', type=Path, required=True)
    a = p.parse_args()
    run(a.out.resolve())
