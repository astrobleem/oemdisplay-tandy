# Tandy Windows 3.0 startup image

The normal ready-to-use `TANDY88.ZIP` includes `TNDYLOGO.RLE`. Users install it
through the same DOS `INSTALL` and Windows Setup **Other display** flow as the
driver. This directory is for developers reproducing or changing the artwork.

## Rebuild

```sh
python3 src/splash/tools/BUILD.PY
python3 src/splash/tools/TEST.PY
python3 src/splash/tools/VERIFY.PY src/splash/assets/TNDYLOGO.RLE
```

Python 3.8+ and its standard library are sufficient for the boot asset, PBM,
SVG and format report. If Pillow is installed, `BUILD.PY` also writes the optional
PNG previews. No external font, generative image service, or stock logo artwork
is required. The geometric wordmark and small bitmap alphabet are in `BUILD.PY`.

- `assets/TNDYLOGO.RLE`: actual 5,930-byte startup image
- `assets/TANDY.PBM`: exact 640×200 monochrome binary PBM
- `assets/TANDY.SVG`: editable vector export; canonical rebuild layout is Python
- `assets/PREVIEW.PNG`: 640×200 logical-pixel artwork preview
- `assets/ASPECT.PNG`: 640×480 preview illustrating the intended 4:3 display
- `assets/FORMAT.JSON`: dimensions, encoding statistics and accepted hash

The previews are artwork, not runtime proof. Actual unedited startup captures
and installation evidence are in [docs/SPLASH.MD](../../docs/SPLASH.MD).

To encode separately edited 640×200 binary PBM artwork:

```sh
python3 src/splash/tools/ENCODE.PY edited.pbm TNDYLOGO.RLE
```

Use hard black/white edges. The renderer and encoder do not dither or antialias.
Images too complex for the stock COM address space are rejected. A changed
image requires fresh startup acceptance and an explicit update to the pinned
hash in root `STAGE.PY`; the package builder will not silently accept new art.
Preserve CRLF when checking generated text back into this repository.

## Format and unchanged loader

The image is 640×200, one plane and two colors. Its BMP header has `biBitCount=1`,
`biCompression=2`, a two-entry black/white palette and pixel offset 62. Despite
the one-bit header, the payload uses **RLE4 nibble commands**. The stock 880-byte
`CGALOGO.LGO` ignores the palette and maps even indices to black and odd to white;
this asset uses only indices 0 and 1.

Rows are bottom-up, with every row exactly 640 pixels. Runs use count 1–254 and
byte `00` for black or `11` for white. `00 00` ends each row; `00 01` ends the
bitmap. No absolute or delta commands are emitted. The stream is 5,868 bytes,
with 2,733 runs and 200 end-of-line commands. Header sizes match actual bytes.

The untouched loader hardcodes CGA 640×200/B800 layout and reads the RLE directly
after its 880 bytes. Setup builds `WIN.COM` as:

```text
WIN.CNF (3456 bytes) + CGALOGO.LGO (880 bytes) + TNDYLOGO.RLE (5930 bytes)
```

The resulting executable is 10,266 bytes; its first 4,336 bytes are unchanged.
The source, staging and verification paths enforce a 65,280-byte COM file bound
(the 64 KiB segment less the 256-byte PSP). No loader or display-driver code
change is needed.

## Setup must own the installed executable

Windows 3.0 Setup may reuse an already-installed `CGALOGO.RLE` instead of the
same-named image on an OEM disk. Therefore the metadata names `TNDYLOGO.RLE`.
This was verified through Setup itself; there is no end-user WIN.COM patcher.
Copying an image into `WINDOWS\SYSTEM` alone does not update an installed splash.
For another artwork revision, use a new unique 8.3 filename or a fresh test
installation; do not assume a same-name reinstall refreshes Setup's cached file.

To verify a mounted installed guest on a modern host:

```sh
python3 src/splash/tools/VERIFY.PY src/splash/assets/TNDYLOGO.RLE --windows /guest/WINDOWS
```

This checks the exact component concatenation, stock loader and accepted driver.
Do not run the developer test/verification tools with Python `-O`.

## Accepted asset

SHA-256: `e7a9c043ce3b9f9c78f7ff38bc68d211a0da32462e036abb7135f0602194f083`

The image was tested using the accepted candidate05 driver, unchanged RESERVE,
normal 640 KB, `core=normal`, `cputype=8086_prefetch`, and `WIN /R`. Physical
Tandy hardware and cycle-exact timing remain unverified. This artwork does not
add a selectable 640×200 desktop mode; startup and desktop modes are separate.
