FILE-DROP PROOF - READ BEFORE RUNNING
====================================
The sealed receiver automatically attempts C:\DROPTX.EXE when it starts.
Before testing, use DOS/File Manager to check that path. If it already
exists, determine what it is first: the receiver would launch that file.
Do not overwrite, rename or remove another program just to run this demo.
If uncertain, skip the drop test until that path is understood.

When C:\DROPTX.EXE is absent, leave all files here. In Program Manager:
1. Run the full path to this folder's DROPRX.EXE, with NO arguments.
2. Run this folder's DROPTX.EXE manually, also with NO arguments.
The failed automatic lookup is harmless in that case. No root copy is needed.

Drag the sender client area onto the receiver. Shift at release sends two
names; Escape cancels. The displayed strings are deliberately fixed:
C:\DROP.TXT and C:\SECOND.TXT. The files do not have to exist. The included
text fixtures are examples only. No dropped file is opened/copied/moved.
TDROP is statically linked; no DLL or system extension is required.

The apps create/append C:\DROPRX.LOG and C:\DROPTX.LOG. Preserve any old logs
before testing. C: remains hardcoded even if TANDYLAB is on another drive.
Use no command-line switches: leading / or - starts automated diagnostics
and the receiver's diagnostic mode can exit Windows. Close both windows
normally when finished. Real-mouse and hardware behavior needs this test.
