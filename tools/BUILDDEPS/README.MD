# Pinned external legacy build inputs

This local cleanup candidate supplies dependency adapters without changing
program source, binaries, package pins or existing build scripts. It does not
run an emulator or installer. Current release Actions package accepted bytes;
they do not require these legacy source-build inputs.

`LOCK.JSON` identifies exact Git objects, SHA-256 hashes and byte lengths for
BIN, DDK, INCLUDE and LIB. Its current commit is the installer-settled main
`96ce6971a1757f3c77094322ed82741791c79646`. Remote DEV preserves this exact final pre-cleanup snapshot. Its commit and
tree identity have been verified against final main. The lock is settled-dev
and records refs/remotes/origin/DEV. Existing release tags/assets are intact.
Retrieve the complete locked SHA, never a floating branch head.

Before removing dependency directories, preserve the exact settled pre-cleanup
main as DEV. Regenerate the lock with `lock --status settled-dev`; that command
requires the locally fetched DEV ref to equal the specified complete commit
SHA. Never resolve build inputs from floating DEV, main, a shortened SHA or a
latest download. Preserve existing release tags/assets and provenance notices.

## Obtain inputs explicitly

Python 3.8+ and Git are required. Use your authorized original dependency bytes.
An emulator is supplied separately through the existing `--dosbox` argument.
The adapter does not include or download DOSBox-X.

An existing local clone containing the locked commit needs no network access:

```sh
python tools/BUILDDEPS/DEPS.PY materialize --lock tools/BUILDDEPS/LOCK.JSON \
  --repo /local/preserved-clone --out /scratch/legacy-inputs
python tools/BUILDDEPS/DEPS.PY verify --lock tools/BUILDDEPS/LOCK.JSON \
  --deps /scratch/legacy-inputs
```

Alternatively, request retrieval explicitly. Only `fetch` accesses the network:

```sh
python tools/BUILDDEPS/DEPS.PY fetch --lock tools/BUILDDEPS/LOCK.JSON \
  --out /scratch/dependency-git
python tools/BUILDDEPS/DEPS.PY materialize --lock tools/BUILDDEPS/LOCK.JSON \
  --repo /scratch/dependency-git --out /scratch/legacy-inputs
```

The repository URL and full SHA are fixed by the checked-in lock. Fetching
objects alone is not file validation; materialization checks locked membership,
Git blob identities, SHA-256 and sizes. Verification rejects missing, extra,
changed or linked files. Local Git reads disable replacement objects and all
transport protocols, so a partial clone cannot silently fetch missing inputs.
Existing outputs are refused, never replaced. Failed
I/O may leave a partial fresh directory; it cannot pass verification. No error
handler removes source directories or retries deletion.

## Build with current source and archived inputs

Create a new external workspace using an explicit source commit. `view` reads
source bytes from Git objects, preserving exact CRLF/LF and distinct tracked
paths. Uncommitted source edits are deliberately excluded: commit a reviewable
source snapshot before reproducing it.

```sh
python tools/BUILDDEPS/DEPS.PY view --lock tools/BUILDDEPS/LOCK.JSON \
  --deps /scratch/legacy-inputs --source-repo /local/current-clone \
  --source-commit FULL_40_CHARACTER_COMMIT --profile display \
  --out /scratch/display-source
python /scratch/display-source/src/tandysw/BUILD88.PY \
  --repo /scratch/display-source --dosbox /external/dosbox-x \
  --out /scratch/new-display-build --mode 640x200x4
```

The second command is a separately allocated native build, not part of adapter
verification. Follow existing CPU/runtime qualification gates before accepting
its output. A successful source build does not promote package pins.

Profiles: `display` retains current driver source and docs; `keyboard` retains
current keyboard source; `textmode` includes its separate renderer source;
`shell` retains TSHELL; `examples` retains all app sources; `experiments`
retains optional packets and their source; `tools` retains packaging/helper
source, current installer source and runtime fixtures; `release` retains the current package/test
closure. ZIP-contained experimental source still requires its documented
explicit extraction into a fresh directory. Scripts run from the selected workspace and
receive that same workspace via their existing `--repo` parameter. Root BIN,
DDK, INCLUDE and LIB retain their expected DOS paths, so existing mounts and
linker/include contracts remain unchanged. PREPXT's build batch uses drive T;
mount the workspace as T for that separately allocated build.

This compatibility approach copies about 88 MB of dependency bytes into each
fresh external workspace. It avoids duplicating toolchains on main and avoids
editing every historical builder. The initial lock retains the full four
dependency trees, including their notices; narrowing them requires separately
verified native include/link closure. No automatic invocation hooks or silent
fetches are added to ordinary packaging/tests.

The preserved snapshot has distinct TSHELL `IDLE/TESTS` and `IDLE/tests`
paths, and Windows correctly refuses views of that original tree. Direct blob
inspection identifies uppercase TESTS as the earlier idle-only suite and
lowercase tests as its Hold-capable successor. The cleanup retains the current
lowercase suite unchanged, routes the host runner to it, and preserves all
three historical uppercase blobs at the exact DEV snapshot. It does not merge
or case-normalize their contents. Cleaned source commits can therefore use
shell/examples/release views on Windows. The source's existing TST5SRC path-key
check still has a Windows separator limitation; TESTSRC.PY uses canonical keys.

## Review stages

1. Review adapters, settled lock and host integrity/refusal tests while all
   original files remain. `python -B tools/BUILDDEPS/TESTDEPS.PY` runs no network
   or guest programs.
2. Confirm DEV remains at the exact authorized pre-cleanup main, publish that
   preservation ref before cleanup merge, and repeat dependency/static validation
   in the allocated environments. Use a separate source snapshot identity for
   each external workspace.
3. Remove obsolete source/builders as a separate normal commit after archive
   links and historical documentation are updated. Preserve current sources,
   tests, current feature assets and release assets.
4. Remove DDK/BIN/INCLUDE/LIB and bundled emulator trees in another commit only
   after source-build reproduction and documentation gates pass. Current
   package CI remains independent of these dependency retrieval commands.

Generate the file-level removal proposal outside the source checkout:

```sh
python tools/BUILDDEPS/PLAN.PY --repo /local/current-clone \
  --commit FULL_40_CHARACTER_COMMIT --out /scratch/cleanup-proposal.json
```

It records exact blobs, SHA-256, sizes and separate gates for obsolete source
and external build inputs. It conservatively preserves experiment packets,
root release ZIPs and the entire current feature/test closure. The orphan
gitlink and stale instruction rewrites remain explicit manual followups.
No command applies the proposal.

For host-only five-mode TR5 staging validation of a display view, use:

```sh
python -B tools/BUILDDEPS/TESTSRC.PY --view /scratch/display-source
```

That verifier checks existing baseline/source pins and exact final staged
assembly with canonical path keys; it does not alter existing pinned source
tests, compile native binaries or run an emulator.

The adapter never deletes source trees, rewrites history or changes remote
refs. Cleanup is a separate reviewed commit against the preserved snapshot.

The installer-settled source profiles also retain src/tandysw/TINST.C,
examples/WXTSPL/UPDATER and docs/QUAL/WAVEINS.JSON where current package
tests require them. The new wave installer runtime/source pins are
preserved unchanged by cleanup.
