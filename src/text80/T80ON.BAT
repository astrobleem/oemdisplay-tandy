@ECHO OFF
REM T80ON.BAT - TEXT80 experimental 80-column text display for Windows 3.0.
REM Run from the folder holding the TEXT80 files, at the DOS prompt:
REM   T80ON [windows folder]        (default C:\WINDOWS)
REM Copies TEXT80.DRV and the 8x8 fonts into the Windows SYSTEM folder,
REM then T80SET saves SYSTEM.INI and WIN.INI as SYSTEM.T80 and WIN.T80
REM and switches the display. Nothing is deleted. Undo: T80OFF.
SET T80W=%1
IF "%T80W%"=="" SET T80W=C:\WINDOWS
IF NOT EXIST %T80W%\WIN.COM GOTO NOWIN
IF EXIST %T80W%\SYSTEM.T80 GOTO ALREADY
FOR %%F IN (TEXT80.DRV T80HELV.FON T80COUR.FON XTTSYS.FON XTCFIX.FON XTCOEM.FON) DO IF NOT EXIST %%F GOTO MISSING
FOR %%F IN (TEXT80.DRV T80HELV.FON T80COUR.FON XTTSYS.FON XTCFIX.FON XTCOEM.FON) DO COPY %%F %T80W%\SYSTEM > NUL
T80SET ON %T80W% TEXT80.DRV
IF ERRORLEVEL 1 GOTO FAILED
ECHO TEXT80 is set up. Start Windows with WIN /R. Undo with T80OFF %T80W%
GOTO END
:NOWIN
ECHO T80ON: %T80W%\WIN.COM not found. Usage: T80ON [windows folder]
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
