FOCUSED NATIVE TIMER DIAGNOSIS

The shipped DLL never changed during this diagnosis. Its hash is
2f244e11acf6605130928c0fdf6e280702740a057198af2221124431ed90c62d.

1. Original 500 ms caller, reduced to Cancel then empty Save on 640x200x2:
   first timer callback posted Escape successfully and returned; Cancel
   completed. Save drew normally, but no second timer callback arrived.
   Timed out at 120 seconds; 79 recorded passes are not completion.
2. Same sequence with modal-idle tracing: owner continued receiving
   WM_ENTERIDLE at about 550 native ms. KillTimer confirmed the timer was
   still registered. Repeated rearming at 500 ms did not restore delivery.
3. Same stalled dialog rearmed at 200 ms: callbacks resumed immediately,
   the original input-driving path completed Save and a real file write.
   97 checks, clean DOS return. This is a diagnostic recovery result.
4. Only the startup interval changed to 200 ms, no idle recovery handler:
   same two-case flow passed 95 checks and returned to DOS in 11.98 sec.
5. Independent queued-character caller: 320x200x4 CREATEPROMPT flow passed
   34 checks; 640x200x2 Cancel/Save passed 32. Original traced 320x200x4
   cases 16/17 also passed 97 checks.
6. Canonical expanded caller changed only its two timer constants from
   500 to 200 ms. All five full 27-case profiles passed 371 checks each,
   with second-caller isolation, zero failures and normal DOS returns.

This identifies missing automation-timer delivery as the demonstrated
mono stall, rather than an unresponsive native dialog or rejected post.
It does not establish the internal Windows/driver cause of that timing
interaction or a universal timer defect. Native GetTickCount differences
are used by idle tracing; the raw callback time field is not used as a
clock. The direct DLL callback cleanup path was also reviewed against
the owned real-mode kernel and does not free unrelated EXE thunks.

Only original source, logs, hashes and build scripts are included. The
invalid first independent diagnostic caller attempt is excluded from
accepted evidence. No OS, SDK, compiler or import-library media is here.
