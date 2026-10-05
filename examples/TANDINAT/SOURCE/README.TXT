TANDINATOR 0.2 - THE INCREDIBLE TANDY MIND READER
================================================
An original, offline Windows 3.0 character-guessing game for an 8088 Tandy.
A real adaptive scoring engine, not a scripted decision tree.

QUICK START
-----------
1. Copy TANDI.EXE and TANDY.DAT together into C:\TANDINAT (or another folder).
2. Start Windows with your existing guarded WindowsXT launcher
   (normally C:\WINXT\WINXT). Do not bypass reservation/recovery errors.
3. In Program Manager choose File > Run and enter C:\TANDINAT\TANDI.EXE.
4. Think of someone in ROSTER.TXT, then choose BEGIN.

The optional INSTALL.BAT copies these two files to C:\TANDINAT when YOU run
it from DOS. It does not change Windows configuration, drivers, AUTOEXEC,
CONFIG.SYS or Program Manager. No installation was performed on real CF.
This kit contains no Microsoft Windows/toolchain files or display drivers.
Use the separately supplied, already working WindowsXT/Tandy environment.

TARGET AND DISPLAY
------------------
Windows 3.0, real mode, 8088-compatible code, 640 KB conventional memory.
Tested in DOSBox-X with 320x200 16-color and 640x200 monochrome. The 640x200
4-color emulator smoke also passes using the project's existing driver;
that mode remains dependent on the driver's hardware support and caveats.
A display at least 320 pixels wide is required. 160x200 is not supported.
No network, floating point, Python or modern runtime is needed on the Tandy.
The included tests are emulator/host evidence, NOT physical Tandy validation.

PLAY
----
1 Yes; 2 Probably; 3 Don't know; 4 Probably not; 5 No.
Click a button, or Tab then Enter/Space. Y/N also confirms/rejects guesses.
F1 opens help, F2 shows candidate scores and timings, Escape or EXIT closes.
Your original pixel-art cabinet fills the left side of the full-screen game.
Questions and answer buttons stay beside it. Cabinet poses change only at
question/guess/success transitions; pupils follow the mouse within the CRT.
The sprite sheets are sliced at native size, with exact 16-color indices.
640-pixel modes double only the artwork's horizontal pixels to preserve its
apparent proportions. Mono and four-color modes use deliberate reductions.
Only changed pupils, text and focus rectangles are repainted during answers.
The normal app has no animation timer or delay, and never captures input.
Shift-Tab also moves focus backward. F1/F2 preserve the current game.
Escape, EXIT, the system close command and normal Windows switching remain
available. No display mode, desktop setting or global palette is changed.

Answer for the familiar portrayal. If unsure, choose Don't know. The game
has 128 people/characters and 128 questions, including modern characters.
A roster outside this starter set cannot be guessed reliably. The source
facts are curated and editable, not guaranteed true across every adaptation.
SOURCE/data notes explain the intended portrayals and source-verification limits.

An incorrect guess can be rejected: its candidate is removed and the game
continues. Other candidates are NOT permanently removed for contradicting
an answer. After 25 questions the best remaining guesses are offered. If
all are rejected, the oracle admits defeat. PLAY AGAIN starts a fresh game.
No answers, personal data or learning history are saved in ordinary play.

WHAT IS INCLUDED
----------------
RUN/       Just the two runtime files, installer, instructions and roster.
SOURCE/    Full rebuildable src/data/tools/tests/build project tree.
           C89 UI/core, compiler, editable data, tests and documentation.
EVIDENCE/  Final logs, numerical results and actual framebuffer screenshots.
BUILDING.TXT explains rebuilding. ENGINE.TXT explains integer scoring.
PERF.TXT distinguishes emulator numbers from unmeasured real-hardware speed.

SELF TEST
---------
Running TANDI.EXE /T starts a deterministic GUI test instead of normal play.
This explicit test writes C:\TANDI.LOG and C:\*.BIN framebuffer captures.
A private test-only WIN.INI [TANDINATOR] Test=1 switch does the same; do NOT
set it for ordinary play. The distributed kit contains no such WIN.INI.
Screenshots in the evidence were captured from emulated video RAM after
actual Win16 painting, then decoded on the host; they are not mockups.

This is an experimental native-art prototype. Natural-answer evaluation and physical
Tandy testing remain future work. Its simulated accuracy is self-consistency
against the authored database, not a claim of universal mind reading.
