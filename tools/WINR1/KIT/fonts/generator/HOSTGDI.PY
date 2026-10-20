"""Temporary process-private Win32 GDI loading/rendering check.

This is host GDI, NOT a Windows 3.0 / DOSBox / Tandy test.
The compatibility System/Terminal names are given unique audit aliases.
"""
import ctypes as C
import json
import struct
from pathlib import Path
from BUILD import fnt, fon, read_glyph, textfile


class TM(C.Structure):
    _fields_ = [(s, C.c_long) for s in ('height', 'ascent', 'descent',
        'internal', 'external', 'avg', 'maximum', 'weight', 'overhang',
        'aspect_x', 'aspect_y')] + [(s, C.c_ubyte) for s in (
        'first', 'last', 'default', 'break_char', 'italic', 'underline',
        'strikeout', 'pitch', 'charset')]


class BI(C.Structure):
    _fields_ = [('size', C.c_uint), ('width', C.c_long),
                ('height', C.c_long), ('planes', C.c_ushort),
                ('bits', C.c_ushort), ('compression', C.c_uint),
                ('image_size', C.c_uint), ('xres', C.c_long),
                ('yres', C.c_long), ('used', C.c_uint), ('important', C.c_uint)]


def check(out):
    from PIL import Image
    g = C.WinDLL('gdi32', use_last_error=True)
    signatures = {
        'AddFontResourceExW': ([C.c_wchar_p, C.c_uint, C.c_void_p], C.c_int),
        'RemoveFontResourceExW': ([C.c_wchar_p, C.c_uint, C.c_void_p], C.c_int),
        'CreateCompatibleDC': ([C.c_void_p], C.c_void_p),
        'CreateDIBSection': ([C.c_void_p, C.c_void_p, C.c_uint,
            C.POINTER(C.c_void_p), C.c_void_p, C.c_uint], C.c_void_p),
        'CreateFontW': ([C.c_int] * 5 + [C.c_uint] * 8 + [C.c_wchar_p], C.c_void_p),
        'SelectObject': ([C.c_void_p, C.c_void_p], C.c_void_p),
        'GetTextMetricsA': ([C.c_void_p, C.POINTER(TM)], C.c_int),
        'GetTextFaceW': ([C.c_void_p, C.c_int, C.c_wchar_p], C.c_int),
        'TextOutA': ([C.c_void_p, C.c_int, C.c_int, C.c_char_p, C.c_int], C.c_int),
        'SetTextColor': ([C.c_void_p, C.c_uint], C.c_uint),
        'SetBkColor': ([C.c_void_p, C.c_uint], C.c_uint),
        'GdiFlush': ([], C.c_int),
        'DeleteObject': ([C.c_void_p], C.c_int),
        'DeleteDC': ([C.c_void_p], C.c_int)}
    for name, (args, rest) in signatures.items():
        function = getattr(g, name)
        function.argtypes, function.restype = args, rest
    contracts = json.loads(Path(__file__).with_name('CONTRACT.JSON').read_text())
    result = []
    for i, item in enumerate(contracts):
        h = next(r['font'] for r in item['resources'] if 'font' in r)
        face = 'XT Audit %d' % i
        font, _ = fnt(h, face)
        path = out / ('AUDIT%d.FON' % i)
        path.write_bytes(fon(font, 'AUDIT%d' % i, 27))
        loaded = g.AddFontResourceExW(str(path.resolve()), 16, None)
        assert loaded == 1, ('font failed to load', item['filename'])
        dc = bitmap = handle = oldbitmap = oldfont = None
        try:
            dc = g.CreateCompatibleDC(None)
            bi = BI(C.sizeof(BI), 640, -200, 1, 32, 0, 640 * 200 * 4, 0, 0, 0, 0)
            pointer = C.c_void_p()
            bitmap = g.CreateDIBSection(dc, C.byref(bi), 0, C.byref(pointer), None, 0)
            assert dc and bitmap
            oldbitmap = g.SelectObject(dc, bitmap)
            handle = g.CreateFontW(h['height'], 0, 0, 0, h['weight'], 0, 0, 0,
                h['charset'], 0, 0, 3, h['pitch_family'], face)
            assert handle
            oldfont = g.SelectObject(dc, handle)
            actualface = C.create_unicode_buffer(64)
            assert g.GetTextFaceW(dc, 64, actualface)
            assert actualface.value == face, (face, actualface.value)
            tm = TM()
            assert g.GetTextMetricsA(dc, C.byref(tm))
            expected = (h['height'], h['ascent'], h['internal'],
                        h['external'], h['avg_width'], h['max_width'])
            actual = (tm.height, tm.ascent, tm.internal, tm.external, tm.avg, tm.maximum)
            assert actual == expected, (item['filename'], actual, expected)
            # Four rows cover the whole encoded strike, including fallback.
            C.memset(pointer, 255, bi.image_size)
            g.SetBkColor(dc, 0xffffff)
            g.SetTextColor(dc, 0)
            expected_pixels = bytearray([255] * (640 * 200 * 3))
            checked = 0
            positions = []
            for code in range(h['first'], h['last'] + 1):
                y = 2 + (code - h['first']) // 32 * (h['height'] + 2)
                x = 2 + (code - h['first']) % 32 * 18
                assert g.TextOutA(dc, x, y, bytes([code]), 1)
                rows = read_glyph(font, code)
                positions.append((code, x, y, len(rows[0])))
                for gy, row in enumerate(rows):
                    for gx, ink in enumerate(row):
                        if ink:
                            p = ((y + gy) * 640 + x + gx) * 3
                            expected_pixels[p:p + 3] = bytes(3)
                checked += 1
            g.GdiFlush()
            data = C.string_at(pointer, bi.image_size)
            actualimage = Image.frombytes('RGB', (640, 200), data, 'raw', 'BGRX')
            actualimage.save(out / ('GDI%d.PNG' % i))
            expectedimage = Image.frombytes('RGB', (640, 200), bytes(expected_pixels))
            # Report modern mapper behavior separately from Win16.
            mismatch = sum(a != b for a, b in zip(actualimage.tobytes(), expectedimage.tobytes()))
            mismatched_codes = [code for code, x, y, width in positions
                if actualimage.crop((x, y, x + width, y + h['height'])).tobytes() !=
                   expectedimage.crop((x, y, x + width, y + h['height'])).tobytes()]
            if h['charset'] == 0:
                assert set(mismatched_codes) <= {0x81, 0x8d, 0x8f, 0x90, 0x9d}, (
                    item['filename'], mismatched_codes)
            else:
                assert mismatch == 0, (item['filename'], mismatched_codes)
            result.append({'font': item['filename'], 'loaded': loaded,
                'face': actualface.value, 'metrics': actual,
                'codes_rendered': checked, 'different_rgb_components': mismatch,
                'modern_mapper_different_codes': mismatched_codes,
                'extended_oem_direct_bytes_qualified': False,
                'normal_text_pixel_match_required': True})
        finally:
            if oldfont:
                g.SelectObject(dc, oldfont)
            if oldbitmap:
                g.SelectObject(dc, oldbitmap)
            if handle:
                g.DeleteObject(handle)
            if bitmap:
                g.DeleteObject(bitmap)
            if dc:
                g.DeleteDC(dc)
            assert g.RemoveFontResourceExW(str(path.resolve()), 16, None)
    textfile(out / 'HOSTGDI.JSON', json.dumps({'kind': 'Win32 host GDI, not Win16',
                                             'results': result}, indent=2) + '\n')
    return result


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(check(args.out), indent=2))
