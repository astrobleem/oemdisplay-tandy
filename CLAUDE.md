# Contributor build guidance

Follow AGENTS.md and BUILDING.MD. Current native display source is
src/tandysw; current shell/app source is under examples. Preserve current
tests, current optional feature packets, runtime manifests and exact
accepted release hashes. A rebuild is not runtime acceptance.

Use tools/BUILDDEPS/README.MD to prepare explicit commit-pinned external
DDK/toolchain/source views. Supply DOSBox-X separately and obtain a test
allocation before running it. Do not silently fetch or substitute floating
inputs. Keep CRLF and DOS 8.3 payload filenames; use 8086/8088-compatible
MASM syntax and C89 for native C code.

Current release Actions execute host tests and package pinned binaries;
they do not compile native MASM/DDK source. Use the current lowercase
TSHELL idle/Hold test suite; do not recreate the historical case collision.

The earlier TNDY16 source/build instructions and all original tools are
preserved in [the exact DEV snapshot](https://github.com/astrobleem/oemdisplay-tandy/tree/96ce6971a1757f3c77094322ed82741791c79646/).
Never rewrite history or delete existing release tags/assets.
