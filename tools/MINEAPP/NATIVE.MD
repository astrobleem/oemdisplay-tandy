# Bounded native app acceptance

Run only after the parent/current coordinator grants an emulator slot. Use a
private existing DOS/Windows 3.0 real-mode fixture, not user storage. Keep the
accepted WINMINE/WMABT/Cookie bytes unchanged. Record the exact BUILD.JSN and
candidate SFX hashes used. No hypothetical older-version migration matrix.

1. From another current drive, run the complete MINESET.EXE into a new private
   DOS directory. Run COOKSET.EXE into a second directory. Compare every output
   with its packet; run each setup again to confirm a matching retry succeeds.
   Confirm a differing destination app file is refused without changes.
2. With no WMABT in Windows or SYSTEM, start the fixture's normal guarded
   Windows desktop. From an unrelated current directory, use File / Run (or
   Tandy Start / Run) with the full MINERUN path. Verify game play, Help / About,
   normal close, then launch/About/close a second time. Confirm no global DLL,
   INI, display, shell or boot bytes changed.
3. Run COOKIE.EXE directly from the same normal desktop. Verify click/buy,
   Save/Load and exit. Rerun its DOS setup and verify COOKIE.SAV is preserved.
   No TANDY88 directory, launcher or legacy display installation is present.
4. With the private shim temporarily missing, verify MINERUN's bounded error
   and no child launch. Rerun MINESET to restore the missing packet member,
   then repeat normal launch/About/exit. Do not remove a real user's file.
5. Verify the same app launch under the actual current FullXT sound profile.
   Unchanged WINMINE imports SOUND in addition to KERNEL/GDI/USER/WMABT; report
   an actual failure to the sound owner rather than editing its clients here.

The host mock covers foreign-loaded-module and LoadLibrary/WinExec failure
cleanup. Native loader behavior and the absent-global-DLL path still require
the real Windows checks above. Stop/release owned processes and the lease
under the coordinator's normal rules; retain a concise execution receipt.
