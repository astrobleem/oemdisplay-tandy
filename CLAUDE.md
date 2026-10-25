# Contributor build guidance

Follow [AGENTS.md](AGENTS.md) and [BUILDING.MD](BUILDING.MD). Current core
packaging is `tools/DOSINST/RCPUB.PY`; download curation is
`tools/CURRENT/BUNDLE.PY` with `PRODUCTS.JSN` and `CHECK.PY`. Current Actions
verify/package accepted bytes and upload artifacts; they do not compile native
DDK source or automatically publish new milestone releases.

The current consumer ZIP contains root SETUP.EXE, README.TXT and the expanded
WINXT folder. Full setup runs in DOS; drivers only use ordinary Windows Setup
with that same folder. Python is for developer tooling, never consumer
preparation. Original XTC/XTE/XTTSYS fonts, the grabber and startup artwork are
bundled as specified by the packet manifests. DOS/Windows itself remains required.
Do not reintroduce historical support-file gathering or manual INI installation.

`src/tandysw/BUILD88.PY` exists for the five-profile TR5 developer base;
`src/pc1512/BUILD15.PY` uses it. Neither command means the current HPXY/desktop
product was rebuilt. Use explicit commit-pinned external source/toolchain
views from [BUILDDEPS](tools/BUILDDEPS/README.MD), supply DOSBox-X separately,
and retain source/native evidence and exact accepted runtime pins. A build or
oracle is not runtime acceptance. Do not silently fetch or substitute inputs.

Preserve CRLF, DOS 8.3 payload names, 8086/8088 MASM conventions and native C89.
Open Watcom builds the expanded SETUP/wrapper; the accepted FIXXT uses external
MSC6/LINK4 through `tools/SOUNDOWN/FINBUILD.PY`. Host Windows GCC must use the managed launcher
specified in AGENTS.md; it is not a native DOS compiler.

Obtain an explicit emulator slot and shared lease; use a private image/config,
owned watchdog, headless controls and verified stop/release. Older builders do
not acquire the lease for you. Never stop another task's process or use CF hardware.
Keep current lowercase TSHELL idle/Hold tests; do not recreate the case collision.

Historical TNDY16 sources are preserved at the [exact DEV snapshot](https://github.com/astrobleem/oemdisplay-tandy/tree/96ce6971a1757f3c77094322ed82741791c79646/).
The moved `oemdisk/MAKEDISK.PY` and `oemdisk/MAKEDISK.BAT` reproduce older
packets, not current downloads.
Preserve historical evidence, notices and all existing release tags/assets.
Follow the current publication authorization; a local build is not publication approval.
