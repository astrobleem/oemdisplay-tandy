# Windows XT native installer tooling

For installation use the prebuilt WINXT.EXE and the [current guide](../../docs/DESKTOP.MD)
on the DOS computer. The packet supplies display support, including the grabber,
fonts, artwork and helpers. Windows itself comes from its installed directory
or original Setup disks; the native helper gathers required OS files automatically.

Developer source is in [DOSINST](../DOSINST/). BUILD.PY targets the 8088 DOS
preparer or finisher using the recorded toolchain flags. PUBLISH.PY delegates
to the closed native publisher; release creation requires matching native
fresh/update/cold receipts and exact packet hashes.

PREPARE.PY remains a developer oracle for the accepted preparation recipe.
It is excluded from the consumer download and is not an installation step.
TESTPREP.PY checks that recipe, while DOSINST/TESTPUB.PY checks native archive
closure and qualification guards. DOSINST/TESTCRC.PY checks actual C CRC code
against zlib; Windows GCC builds use the shared preflighted launcher.
