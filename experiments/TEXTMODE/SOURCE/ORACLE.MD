# DIB source-crop oracle correction

The first ROUND4 screen report flagged cases 5, 7, and 9 at all four depths.
The first expected-output oracle had used a top-left API source-Y origin,
based on the observed Windows 3.0 monochrome GDI fallback when the driver
had no RC_DIBTODEV capability. That fallback is not the documented native
DIBScreenBlt contract.

## Preserved observations

- SCREEN054TOP.json retains all 12 original failure records, original case
  parameters, original expected/actual byte examples, and full comparison
  counts. It is preserved separately; no mismatches were removed from it.
- screen-first-evidence/ holds the immutable original ROUND4.LOG, every
  R4Bxx.BIN/R4Dxx.BIN before/after 32 KiB dump, the tested ROUND4.EXE, and
  the original c5844534b94ca9e4ba02d338bb1b6cb20387a413792e424a8b0f0b96d17082bd
  TANDY88.DRV. Its executable SHA256 is
  2c7f6aa17a49f98e424b4b4d74c283b1551957d5e092e62f2ab248f4edab1b66.
- SCREEN054B.json is the corrected bottom-left result over those exact dumps.
  All 56 cases pass, comparing 1,835,008 raw framebuffer bytes. SCREEN054.json
  now points to that same corrected result; SCREEN054TOP.json is the old one.

## Authoritative semantics and independent control

Bundled Windows 3 SDK reference DDK/w3sdkr1.txt, SetDIBitsToDevice Comments,
lines 33490-33497, explicitly specifies bottom-left DIB origin. The original
DDK/286/DISPLAY/4PLANE/DISCREEN.ASM lines 363-370 and 389-399 map the band as
screen bottom = ScrYorg + MapHeight - StartScan and top = bottom - NumScan.

Stock Windows 3.0 CGA.DRV independently confirms that native behavior.
Its live RASTERCAPS is 665 (including RC_DIBTODEV). The unmodified native
stock control guest is /workspace/shared/windows30/roundcg-c. ROUNDCG4B.json
records all 10 monochrome geometric cases passing with bottom-left source
coordinates. The earlier fallback-based control is ROUND05M.json; it is
kept as an observation, not the native contract.

The CGA 16 KiB framebuffer is mirrored in the upper 16 KiB of a 32 KiB B800
read. The CGA oracle explicitly mirrors expected writes too, so it compares
all 32 KiB without ignoring the aliases. Tandy mode 09 has four real banks;
its oracle compares all 32 KiB without that CGA-only mirror rule.

## Exact changed expectation

For a source DIB of height H, requested source Y sy, requested height h, and
output row oy, the prior oracle used sourceTop = sy + oy. The corrected one
uses sourceTop = H - sy - h + oy. The source scan is H - 1 - sourceTop and
must lie in [StartScan, StartScan + NumScan). The supplied lpBits starts at
the requested band, not the beginning of the full DIB. All source-X, screen
clipping, explicit DC clipping, input guards, and raw framebuffer guard
comparisons are unchanged.

For H=11, the three affected geometric cases are:
- Case 5: sx=3, sy=2, h=6. Prior sourceTop=2; corrected sourceTop=3
- Case 7: sx=2, sy=1, h=8, StartScan=3, NumScan=5. Prior sourceTop=1;
  corrected sourceTop=2, moving the visible band by one output row
- Case 9: sx=7, sy=0, h=7. Prior sourceTop=0; corrected sourceTop=4

Repeat those cases at indices +14, +28, and +42 for depths 4, 8, and 24.
No driver geometry was changed to make these pass.

## Recheck commands

python ROUND4CK.PY screen-first-evidence --source-origin top --out OLD_TOP
python ROUND4CK.PY screen-first-evidence --source-origin bottom --out NATIVE_BOTTOM
python ROUND4CK.PY /workspace/shared/windows30/roundcg-c --mode cga --source-origin bottom --out STOCK_NATIVE

ROUND4CK.PY defaults to the documented bottom-left origin; the explicit
--source-origin top switch retains the old oracle for inspection.
