# Preserved development snapshot

The exact pre-cleanup snapshot is `96ce6971a1757f3c77094322ed82741791c79646`, preserved by DEV.
All original source paths, bundled tools and notices remain at that commit.
Existing release tags/assets and local originals are unchanged.

[Browse the immutable snapshot](https://github.com/astrobleem/oemdisplay-tandy/tree/96ce6971a1757f3c77094322ed82741791c79646/).

Main retains current driver/application source, tests, runtime assets,
current optional experiment packets and accepted release ZIPs. Historical
TNDY16 source/builders, generic tandy4 source, win2 analysis, tanvidasm and
old disk1 scaffolding belong to the preserved snapshot. The old uppercase
TSHELL idle-only tests are archived there; main retains the unchanged
lowercase Hold-capable successor and runs both its idle and Hold checks.

Bundled DDK, compiler/linker/header/library trees and emulator binaries are
kept only in the snapshot. [Pinned build-input instructions](../tools/BUILDDEPS/README.MD)
prepare an external workspace with exact source and dependency identities.
Only an explicit fetch command accesses the network. Supply DOSBox-X
separately; package CI does not compile legacy native source.

Historical packets/evidence are immutable records. Their references to
old repository paths identify the preserved pre-cleanup tree, not missing
current package inputs. Old relative paths inside accepted ZIPs remain
unchanged to retain their release hashes.
