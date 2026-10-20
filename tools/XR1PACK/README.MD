# Current XR1 own-media package

`README.TXT` is the end-user preparation and installation guide. This package
starts from ordinary owned Windows 3.0 media; it does not require the earlier
private DOS-CROOT. The supplied 47 payload inputs include the selected adapted
drivers, authored shell/helpers, wheel driver, original fonts and artwork.
Their component identities and notices are separate from owned-media inputs.

`PREPARE.PY` validates all inputs before creating a new output folder. It
accepts expanded or SZDD files from the pinned English media set and generates
the owned loader-containing files and Setup metadata locally. Fresh preparation
creates 367 files; update preparation creates 80 and has no W30 Setup tree.
The prepared output stays private. The public download contains no original
Windows installation media or assembled loader.

The current package is XR1-only. Legacy custom display rows and prompts have
been removed. The unchanged CPSET/FIXXT binaries have a 49,840-byte Setup data
contract, so the local transformation fills the removed rows with inert authored
comments before the final language row and all seven DOS EOF markers. The resulting file has its own exact hash;
the input hash, copy ranges and new project metadata are recorded in INPUTS.JSN.
No executable pin or check is relaxed to accommodate this transformation.

Host boundary checks use synthetic media:

```text
python tools/XR1PACK/TESTPREP.PY
```

New preparation/installation qualification is recorded in QUALIFY.JSN. Earlier
R1 integration evidence remains separate; packaging does not turn emulator
results into hardware qualification. The Minesweeper packet preserves the
existing converted executable and shim with its own notices and exact scope.

Publication uses PUBLISH.PY and TESTPUB.PY with an explicit commit and closed
asset inventory. Existing rc.6/rc.7 releases and assets remain unchanged.
