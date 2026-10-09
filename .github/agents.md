# Host checks and native build guidance

Follow root AGENTS.md and BUILDING.MD. Current Actions run host checks and
package accepted pinned runtime bytes. Native driver/application rebuilds
use explicit pinned external workspaces from tools/BUILDDEPS/README.MD and
a separately supplied DOSBox-X executable. Obtain emulator allocation before
running native builds/tests. Never silently fetch floating toolchains.

Preserve current source, tests, release pins and qualified feature assets.
Maintain CRLF, C89 and DOS 8.3 payload filenames. Do not delete EXE/DRV/COM/DLL
files merely as generated outputs: package manifests require their exact bytes.
Use docs/DEV.MD for historical source/toolchain provenance.
