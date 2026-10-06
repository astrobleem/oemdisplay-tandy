TANDY FILE DROP - WINDOWS 3.0 REAL-MODE PROOF

A bounded, independent file-path drag/drop extension for Windows 3.0 on
8086/8088-class machines. Includes two small native applications and TDROP.LIB.
No stock File Manager patch, replacement SHELL.DLL, OLE, COMMDLG or Win32 port.

INSTALL / TRY
Copy DROPRX.EXE and DROPTX.EXE into C:\. Create C:\DROP.TXT and optionally
C:\SECOND.TXT (the supplied text fixtures may be used). Start DROPRX.EXE from
Program Manager's Run command. It launches the sender in a separate task.
Drag from the sender's client area onto the receiver. Hold Shift on release
to transfer both fixture names. Escape cancels. Closing either application
is safe. This demo only displays paths; it never opens, copies, moves,
renames or deletes dropped files. /D opts into C:\DROPRX.LOG and C:\DROPTX.LOG;
normal runs create neither. /A keeps automated diagnostic logging.
The demo deliberately uses fixed fixture paths, not a directory browser.
Delete these demo files to uninstall. No SYSTEM.INI or stock files are changed.

STATUS AND COMPATIBILITY
This is an explicitly named Win3.0 extension, not transparent Windows 3.1
shell compatibility. Win3.0 retained extended-style bit 0x10 in our native
probe. Retention alone does not supply the later shell APIs or file manager
behavior. The owned stock Win3.0 installation contains no SHELL.DLL, and the
running test had no SHELL module. TDROP acceptance therefore uses the window
property Tandy.FileDrop.1; unmodified Windows File Manager does not use it.

TDROP.LIB implements independently named counterparts:
 TDDragAcceptFiles(window, BOOL) registers/removes acceptance.
 TDDragQueryFile(handle, index, buffer, size) copies a path. Index 0xffff
 counts files; NULL buffer queries its length. Size includes the final NUL.
 A short nonzero buffer is terminated and returns the copied length.
 TDDragQueryPoint(handle, POINT FAR *) copies receiver-client coordinates
 and returns TRUE for a client-area drop, FALSE for nonclient/invalid data.
 TDDragFinish(handle) frees the packet exactly once.

TDValid validates before any query. TDPack creates packets. TDTarget resolves
WindowFromPoint then walks parents to an explicitly accepting window. TDPost
rechecks the target and posts WM_DROPFILES (0x0233), passing the movable global
handle in wParam. These are static-library APIs, not exported SHELL ordinals.
Programs must include TDROP.H and link TDROP.LIB and their normal Win16 SDK libs.

PACKET / OWNERSHIP
The historical Win16 layout is eight bytes: WORD offset (8), signed 16-bit
POINT x/y, 16-bit BOOL nonclient, followed by ANSI full DOS paths, each NUL
terminated, with an additional final NUL. This is NOT the Win32 DROPFILES
structure and has no fWide member. Packet size is capped at 4096 bytes, paths
at 127 bytes each, and count at 16. The demo uses single-byte DOS/ANSI names;
Unicode, long filenames, network paths, DBCS and huge packets are out of scope.

Allocation is GMEM_MOVEABLE | GMEM_DDESHARE | GMEM_ZEROINIT. Far pointers exist
only during a GlobalLock. The sender unlocks before PostMessage. Allocation,
lock, invalid-packet, target and queue failures leave the sender responsible
for freeing. Successful post transfers ownership; sender must never free or
query it afterward. Receiver validates bounds, header, drive-root prefix and
terminators before displaying/logging paths, then calls TDDragFinish once.
WM_DESTROY revokes acceptance and drains queued WM_DROPFILES handles.
Cooperative Win16 scheduling permits final target check and PostMessage
without an intervening yield. Forced task termination/crash recovery is not
guaranteed; arbitrary hostile handles are not a security boundary.

Receiver-client coordinates are computed with ScreenToClient at release;
nonclient is classified against GetClientRect. Both client and nonclient
paths are supported. Cancelling only releases capture if this window still
owns it, avoiding interference with a different window's new capture.

BUILD
Use the existing licensed Microsoft C6/Windows SDK repository toolchain:
 python3 BUILD.PY --repo <repository> --dosbox <DOSBox-X> --out <new-directory>
Native flags: /G0 /Gw /AS /W3 /Od, Microsoft segmented linker, Windows 3.0
resource-free NE header marking equivalent to RC /30. TDROP.LIB is created
with the existing librarian. No 186/286/386 instructions are requested.
The compiler emits two benign unreferenced-variable warnings in the receiver
variant because its shared source excludes sender-only branches.

TEST
 python3 RUNTEST.PY --guest <installed-mode-guest> --build <build-directory>
  --dosbox <DOSBox-X> --out <new-test-directory>
The cloned guest uses 640KB, 8086_prefetch, no EMS/XMS/UMB, Windows /R.
The receiver /A starts the independent sender /A, checks queries and packets,
receives two file paths, then exits Windows normally. Tests use programmatic
messages for cancel/error coverage. They do not substitute for real-mouse QA.
AUDIT.PY verifies the emitted NE flags and every imported ordinal against
owned Windows 3.0 KERNEL/USER/GDI binaries. No shell import is present.
See ../../EVIDENCE for this trial; historical TESTS.TXT remains in the
unchanged examples/FILEDROP package.

BACKGROUND
Historical packet reference: Microsoft Systems Journal, 'Drop Everything',
1992, https://jacobfilipp.com/MSJ/1992-dropeverything.pdf . Implementation is
independent C source. The NT microsoft/winfile project targets Win32 and was
not ported or incorporated. No OS/compiler binaries are distributed here.
Physical Tandy hardware remains untested.
