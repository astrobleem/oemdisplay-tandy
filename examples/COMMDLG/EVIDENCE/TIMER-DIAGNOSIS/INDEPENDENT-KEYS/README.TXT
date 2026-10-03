Focused COMMDLG keyboard-message diagnosis

Exact final DLL SHA-256:
2f244e11acf6605130928c0fdf6e280702740a057198af2221124431ed90c62d
Corrected independent caller SHA-256:
7b8ef615e97abf43640a5249ec93ac158abbb2bdb0d32e4e0aaeda0ee32a37e1

Accepted focused runs:
- cdlg-focused-key-3204-r2: original expanded case17 semantics
  (FILEMUSTEXIST | CREATEPROMPT new Open). 34 checks, 0 failures,
  18.02 seconds, clean DOS return. NEWOPEN.TXT typed through queued
  WM_CHAR; queued Return opened CREATEPROMPT initially focused No;
  queued focus-to-Yes was verified before queued Return accepted.
  Returned C:\CDCASE\NEWOPEN.TXT, error0, without creating the file.
- cdlg-focused-key-6402: original expanded case0 then case1 semantics.
  32 checks, 0 failures, 12.54 seconds, clean DOS return. Escape canceled
  Open; an initially empty Save accepted queued ROUND and Return,
  returned C:\CDCASE\ROUND.TXT, and caller created/wrote the output.
- Both: preserved SP/DS, output capacity and surrounding canaries,
  file title/offset consistency, caller cwd; zero leftover CD*.TMP.

All runtime DLL copies and original final DLL hash-check identically.
No DLL source or binary was modified. See RESULTS.JSON for exact paths.

Environment: DOSBox-X, native Windows3.0 real mode (GetWinFlags=64),
8086_prefetch CPU,640KB conventional, no XMS/EMS/UMB,100000 cycles.
Cycles are expedited QA, not physical8088 speed. Input is synthetic
queued keyboard messages, not physical keyboard input. Caller is
compiled /G0 /Gw /AS /Od and linked historical Microsoft COMMDLG.LIB.
Message queue capacity requested32, character input one per timer tick;
150-tick native watchdog plus120-second host timeout.

The passing isolated flows show these individual behaviors work on the
exact corrected DLL. They do not establish full expanded-harness or
all-mode acceptance. Original timer/queue stress remains separate.

Excluded attempt: cdlg-focused-key-3204 used initial diagnostic caller
c2b9afca with incorrect near %s varargs to Win16 wsprintf, causing trace
corruption. It was allowed to expire under its host timeout. Every %s
argument was corrected to LPSTR; numeric queue logging was also fixed,
and log buffers enlarged. cdlg-focused-key-build02 is the valid caller.
