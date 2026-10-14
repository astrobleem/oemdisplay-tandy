@ECHO OFF
REM T80OFF.BAT - undo T80ON: T80SET OFF puts back exactly the lines T80ON
REM changed in SYSTEM.INI and WIN.INI (recorded in T80SET.STA); every other
REM setting, including ones changed since, stays. (T80SET RESTORE instead
REM copies back the whole files saved by T80ON, SYSTEM.T80 and WIN.T80.)
REM The copied files stay in SYSTEM and are unused.
REM Run at the DOS prompt:  T80OFF [windows folder]
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
