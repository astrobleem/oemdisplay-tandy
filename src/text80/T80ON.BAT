@ECHO OFF
REM T80ON.BAT - TEXT80 experimental 80-column text display for Windows 3.0.
REM Run from the folder holding the TEXT80 files, at the DOS prompt:
REM   T80ON [windows folder] [profile]   (defaults C:\WINDOWS and 25)
REM Profiles: 25  = TEXT80.DRV, 80x25 text, 640x200 desktop (any CGA-
REM                 compatible colour adapter: CGA, Tandy 1000, EGA, VGA)
REM           PAN = T80PAN.DRV, 80x25 text window over a 640x400 desktop;
REM                 XTPAN.EXE (copied to the Windows folder, added to
REM                 load=) pans it: Alt+PgDn / Alt+PgUp, pointer at the edge
REM           VGA = T80VGA.DRV, VGA 80x50 text, 640x400 desktop (VGA only;
REM                 Windows will not start on another adapter: run T80OFF)
REM           C25 = T80CMP.DRV, 80x25 with the compact UI profile: window
REM                 controls one text cell each; WIN.INI BorderWidth=7 and
REM                 GridGranularity=1 (restored by T80OFF)
REM Copies the driver and the 8x8 fonts into the Windows SYSTEM folder,
REM then T80SET saves SYSTEM.INI and WIN.INI as SYSTEM.T80 and WIN.T80
REM and switches the display. Nothing is deleted. Undo: T80OFF.
SET T80W=%1
SET T80P=%2
IF "%T80W%"=="" SET T80W=C:\WINDOWS
IF "%T80P%"=="" SET T80P=25
SET T80D=
IF "%T80P%"=="25" SET T80D=TEXT80.DRV
IF "%T80P%"=="PAN" SET T80D=T80PAN.DRV
IF "%T80P%"=="pan" SET T80D=T80PAN.DRV
IF "%T80P%"=="VGA" SET T80D=T80VGA.DRV
IF "%T80P%"=="vga" SET T80D=T80VGA.DRV
IF "%T80P%"=="C25" SET T80D=T80CMP.DRV
IF "%T80P%"=="c25" SET T80D=T80CMP.DRV
IF "%T80D%"=="" GOTO USAGE
IF NOT EXIST %T80W%\WIN.COM GOTO NOWIN
IF EXIST %T80W%\SYSTEM.T80 GOTO ALREADY
FOR %%F IN (%T80D% T80HELV.FON T80COUR.FON XTTSYS.FON XTCFIX.FON XTCOEM.FON) DO IF NOT EXIST %%F GOTO MISSING
IF "%T80D%"=="T80PAN.DRV" IF NOT EXIST XTPAN.EXE GOTO MISSING
FOR %%F IN (%T80D% T80HELV.FON T80COUR.FON XTTSYS.FON XTCFIX.FON XTCOEM.FON) DO COPY %%F %T80W%\SYSTEM > NUL
IF "%T80D%"=="T80PAN.DRV" GOTO PAN
IF "%T80D%"=="T80CMP.DRV" GOTO COMPACT
T80SET ON %T80W% %T80D%
IF ERRORLEVEL 1 GOTO FAILED
GOTO DONE
:COMPACT
T80SET ON %T80W% %T80D% /C
IF ERRORLEVEL 1 GOTO FAILED
GOTO DONE
:PAN
COPY XTPAN.EXE %T80W% > NUL
T80SET ON %T80W% %T80D% XTPAN.EXE
IF ERRORLEVEL 1 GOTO FAILED
:DONE
ECHO TEXT80 (%T80P%) is set up. Start Windows with WIN /R. Undo with T80OFF %T80W%
GOTO END
:USAGE
ECHO T80ON: unknown profile %T80P%. Usage: T80ON [windows folder] [25 / PAN / VGA / C25]
GOTO END
:NOWIN
ECHO T80ON: %T80W%\WIN.COM not found. Usage: T80ON [windows folder] [25 / PAN / VGA / C25]
GOTO END
:ALREADY
ECHO T80ON: already set up (%T80W%\SYSTEM.T80 exists). Run T80OFF first.
GOTO END
:MISSING
ECHO T80ON: run T80ON from the folder holding the TEXT80 files.
GOTO END
:FAILED
ECHO T80ON: T80SET failed; nothing was changed.
:END
SET T80W=
SET T80P=
SET T80D=
