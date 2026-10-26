# RLE source provenance

The RLE4/RLE8 parser and DIB bridge in `RLE88.ASM`, `PORTDIB.PY`, and
`SDIB88.ASM` are project source for the 8086/8088 Tandy display-driver path.
The Windows 3.1 DDK `WINVBE` source file `SRC/DRV/DIB.C` was consulted for
Windows GDI DIB-entrypoint/control-flow behavior. Official Windows DIB format
material was used for BI_RLE4/BI_RLE8 escape, run, padding, delta, EOL, and EOB
semantics. The source is not copied wholesale from WINVBE.

The driver is already a Microsoft-DDK-derived adaptation. Existing Microsoft
notices and rights stay in force, and this change does not assert a new license
grant. The canonical accepted HPXY provenance remains the record in
`tools/XR1PACK/PROVENANCE.JSN`; the accepted payload remains at its existing
hash until separately reviewed and authorized.
