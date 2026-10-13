@ECHO OFF
REM T80OFF.BAT - undo T80ON: restores SYSTEM.INI and WIN.INI exactly as they
REM were (from SYSTEM.T80 and WIN.T80). The copied files stay in SYSTEM and
REM are unused. Run at the DOS prompt:  T80OFF [windows folder]
SET T80W=%1
IF "%T80W%"=="" SET T80W=C:\WINDOWS
T80SET OFF %T80W%
IF ERRORLEVEL 1 GOTO FAILED
ECHO TEXT80 removed: Windows starts with its previous display driver.
GOTO END
:FAILED
ECHO T80OFF: nothing to undo, or the restore failed (see above).
:END
SET T80W=
