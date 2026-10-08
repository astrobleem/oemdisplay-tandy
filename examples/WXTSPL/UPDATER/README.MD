# Guarded DOS startup updater

`WAVEXT` is original 8086/C89 code for DOS 3.3+. The installer calls it after
creating its numbered backup and before committing the guarded launchers.
It expands the exact qualified original logo and privately joins it with your
matching `SYSTEM\WIN.CNF`. It never patches installed `WIN.COM` or settings.

At plain DOS, use `WAVEXT CHECK|APPLY|RESTORE|VERIFY C:\WINDOWS C:\WINXT`.
`CHECK` reads the transaction without changing files. `RESTORE` disables the
wave and restores exact original starters; private stages remain inactive.
`APPLY` re-enables a recognized transaction. Changed loaders, starters,
wrappers, incomplete transactions and insufficient space refuse safely.
Preserve `WAVE01` and sidecars after a refusal; do not bypass the launcher.

`VERIFY` returns 0 for qualified TR53216/TANDY88 Color, 1 for a valid static
profile, or 2 for an unsafe state. Native tests covered repeated apply,
starter/loader/wrapper refusals, normal Color and static Windows exits, and
full 35-file installer rollback. [Exact qualification](../../../docs/QUAL/WAVEINS.JSON).

`SETTEST.PY /path/to/guest` checks an actual generated starter's existing
Windows working directory and absolute OEM source path. CI additionally
binds this installer source and public payload to the native qualification.
Build with an existing owned Microsoft C 6 toolchain using `BUILD.BAT`;
changed executable bytes require new qualification. No compiler or Windows
loader bytes are distributed here. Do not redistribute completed private
loaders or staged owned fonts.
