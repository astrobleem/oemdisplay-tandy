"""Original 160x200 graphics controls, independent of text-cell alignment.

Win3 OBM_CHECKBOXES is four columns by three rows. Preserve that state
layout; each tile is 6x8. Caption glyphs have seven rows and USER supplies
their frame. Native USER hit-testing/metric selection still needs testing.
"""
import struct


def dib(rows):
    """1bpp BITMAPCOREHEADER, black ink/white paper, DWORD-padded rows."""
    width, height = len(rows[0]), len(rows)
    if not width or any(len(r) != width for r in rows):
        raise ValueError('nonrectangular bitmap')
    stride = (width + 31) // 32 * 4
    bits = bytearray()
    for row in reversed(rows):
        line = bytearray(stride)
        for x, ink in enumerate(row):
            if not ink:
                line[x // 8] |= 0x80 >> (x % 8)
        bits += line
    return struct.pack('<IHHHH', 12, width, height, 1, 1) + bytes((0, 0, 0, 255, 255, 255)) + bits


def grid(drawing):
    return [[int(c == '#') for c in row] for row in drawing.split('/')]


def inverse(rows):
    return [[1 - x for x in row] for row in rows]


def join(a, b):
    return [x + y for x, y in zip(a, b)]


UP = grid('....../....../..#.../.###../#####./....../....../......')
DOWN = list(reversed(UP))
LEFT = grid('....../..#.../.##.../###.../.##.../..#.../....../......')
RIGHT = [list(reversed(r)) for r in LEFT]
RESTORE = grid('....../..#.../.###../....../.###../..#.../......')
SYSTEM = grid('....../....../.####./....../.####./....../......')
CHECK = grid('....../....../....#./...#../#.#.../.#..../....../......')
BLANK = [[0] * 6 for _ in range(8)]


def checkbox(row, checked, pressed):
    pixels = [[0] * 6 for _ in range(8)]
    if row == 1:  # radio circle: 5x6 ink outline plus spacing column
        outline = {(1, 1), (2, 1), (3, 1), (0, 2), (4, 2),
                   (0, 3), (4, 3), (0, 4), (4, 4), (0, 5), (4, 5),
                   (1, 6), (2, 6), (3, 6)}
        inside = {(x, y) for y in range(2, 6) for x in range(1, 4)}
        mark = {(2, 3), (2, 4)}
    else:
        outline = {(x, y) for y in range(1, 7) for x in range(5)
                   if x in (0, 4) or y in (1, 6)}
        inside = {(x, y) for y in range(2, 6) for x in range(1, 4)}
        mark = {(1, 4), (2, 5), (3, 3), (3, 4)}
        if row == 2:  # original stipple for the inherited three-state row
            mark = {(x, y) for x, y in inside if (x + y) % 2 == 0 and (checked or x == 2)}
    for x, y in outline:
        pixels[y][x] = 1
    for x, y in inside:
        pixels[y][x] = int(pressed) ^ int((checked or row == 2) and (x, y) in mark)
    return pixels


def bitmaps():
    capup, capdown = UP[:7], DOWN[:7]
    entries = {
        32747: RESTORE, 32749: capdown, 32748: capup,
        32746: inverse(capdown), 32745: inverse(capup), 32744: inverse(RESTORE),
        32754: join(SYSTEM, SYSTEM),
        32753: UP, 32752: DOWN, 32750: LEFT, 32751: RIGHT,
        32743: inverse(UP), 32742: inverse(DOWN),
        32740: inverse(LEFT), 32741: inverse(RIGHT),
        32760: CHECK, 32761: BLANK, 32766: BLANK,
        32738: DOWN, 32739: RIGHT,
        # Legacy USER aliases use the same compact dimensions.
        32755: RESTORE, 32757: capdown, 32756: capup,
        32763: RIGHT, 32762: LEFT, 32765: UP, 32764: DOWN,
        32767: join(SYSTEM, SYSTEM),
    }
    atlas = []
    for row in range(3):
        tiles = [checkbox(row, checked, pressed) for pressed, checked in
                 ((False, False), (False, True), (True, False), (True, True))]
        atlas += [sum((tile[y] for tile in tiles), []) for y in range(8)]
    entries[32759] = atlas
    return {key: dib(rows) for key, rows in entries.items()}


def config(data):
    """Change only documented OEM machine words; leave colors/padding alone."""
    words = list(struct.unpack_from('<9H', data))
    if words != [11, 23, 2, 4, 1, 2, 0, 1, 1]:
        raise ValueError('unexpected 160 OEMCONFIG words: ' + repr(words))
    result = bytearray(data)
    # Thumb H/W, icon X/Y compression, cursor X/Y compression, Kanji,
    # vertical/horizontal border thickness. Retain inherited icon X=2/Y=4
    # and cursor values; actual icon dimensions/rendering need native checks.
    struct.pack_into('<9H', result, 0, 8, 6, 2, 4, 1, 2, 0, 1, 1)
    return bytes(result)


def font_requests(data):
    """Three packed LOGFONTs: retain faces/charset, request four-pixel width."""
    result = bytearray(data)
    pos = 0
    for expected in (b'Terminal', b'Courier', b'Helv'):
        end = data.index(0, pos + 18)
        if data[pos + 18:end] != expected or struct.unpack_from('<H', data, pos)[0] != 8:
            raise ValueError('unexpected OEM LOGFONT')
        struct.pack_into('<H', result, pos + 2, 4)
        pos = end + 1
    if any(data[pos:]):
        raise ValueError('unexpected OEM LOGFONT tail')
    return bytes(result)
