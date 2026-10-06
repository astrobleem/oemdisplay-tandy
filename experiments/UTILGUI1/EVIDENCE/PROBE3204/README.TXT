320x200x4 FORCED-PAINT OBSERVER LIMITATION

FORCED retains the original RAM dumps and decoded PNGs from the main normal
flow. Some EXJOY readings/notice and FileDrop path rows are missing there.
The same run's VIDEO frames show the complete stable paused and path states.
The frames were extracted losslessly at the times recorded in RECORD.JSN.
The original 25-second recording remains in the local native QA capture set;
its hash is recorded here. No exact RAW-to-AVI timestamp was recorded, so the
frame times identify surrounding observed states, not cycle-exact simultaneity.

QUEUED is a separate successful run of the EXACT SAME production executables.
The only observer changes remove cross-task UpdateWindow and defer each RAM
sample until the next observer timer, before performing the next UI action.
That leaves the applications time to process queued paint themselves. These
RAM samples contain all expected text and agree with the observed display.
All normal-flow checks, no-default-log checks, CPU sentinels and unchanged
original-fixture checks passed. The modified observer source/build are here.

BASELINE is an explicit comparison using historical EXJOY and FileDrop
executables in the same fixture, with the final CDTEST held constant. Those
sampled baseline dumps did not reproduce the missing text. This therefore
establishes neither a general driver defect nor a proven historical app bug.

SUPPORTED CONCLUSION
The synchronous cross-task forced-paint/immediate-RAM-sampling observer path
is not a reliable visual oracle for these trial apps in this fixture. Normal
queued presentation is verified by both the video and the delayed sampling
run. The exact low-level cause was not established. No production application
or display-driver change was made in response to this observation.
The main 3204 screenshot set uses the successful QUEUED run's RAM samples.

PORTABLE REPRODUCTION
Build SOURCE/UIQA.C with its BUILD.PY using your owned C6/SDK tree. From the
kit root, run QA/UIRUN.PY with --observer-source
EVIDENCE/PROBE3204/SOURCE/UIQA.C and --harness pointing to that new UIQA.EXE.
Also supply --bin BIN, --guest YOUR_OWNED_3204_GUEST, --dosbox DOSBOX_X and
--out NEW_OUTPUT. The runner clones the guest and checks exact source pins.

The bundled portable runner was repeated successfully with the explicit
observer source option. PORTABLE.JSN and PORTABLE.LOG retain that check.
