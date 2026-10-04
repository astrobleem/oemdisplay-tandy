@ECHO OFF
REM Edit these paths to match TSTART.BAT. This never starts Windows.
SET TSHOME=C:\TSTART
SET TSINI=C:\WINDOWS\SYSTEM.INI
IF NOT "%1"=="" GOTO USAGE
IF NOT EXIST %TSHOME%\SHELLSEL.EXE GOTO MISSING
%TSHOME%\SHELLSEL.EXE RECOVER %TSINI%
IF ERRORLEVEL 1 GOTO FAILED
GOTO DONE
:MISSING
ECHO SHELLSEL.EXE missing from %TSHOME%. Nothing changed.
GOTO DONE
:FAILED
ECHO Recovery failed. Keep every TSHELL sidecar and do not start Windows.
GOTO DONE
:USAGE
ECHO Use RECOVER without arguments, from DOS after exiting Windows.
:DONE
SET TSHOME=
SET TSINI=
