About This Tandy native Win16 white-box checks

ABOUTUT.C includes the byte-identical production SUBJECT.C snapshot, renaming only its WinMain during preprocessing. Production source is not modified. All tests run in disposable clones of accepted Setup-produced installations. Build uses existing Microsoft C /G0 /Gw /AS /W3 /Od and LINK4. Runtime uses DOSBox-X 8086_prefetch, 640 KB conventional RAM, XMS/EMS/UMB disabled, and the shared RESERVE launcher before Windows /r.

138 assertions per mode cover real Windows APIs, actual physical color counts, four logical DDB planes, app controls/geometry, native font extents on every page, reported memory, CPU labels, page commands, keyboard helpers including Shift-Tab, refresh, Escape, and ordinary WM_CLOSE. Host checks compare the logged screen tuple against all five expected profiles. Synthetic keyboard state is restored.

Limits: this is native Windows emulation, not physical hardware. Included production code executes against Windows APIs and controls, with synthetic messages for deterministic checks. Actual end-user message-loop and visual screenshot checks are separate.

Evidence: RESULTS.JSON; per-mode ABOUTUT.LOG, RUN.CNF, HOST.LOG and RESULT.JSON; exact SUBJECT.C and harness; build logs/configuration and executable/map. Guest OS installations and compiler tools are deliberately excluded from EVIDENCE.ZIP.
