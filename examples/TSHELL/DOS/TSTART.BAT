@ECHO OFF
REM Configure these four DOS 8.3 paths before using this optional launcher.
SET TSDRV=C:
SET TSWIN=\WINDOWS
SET TSHOME=C:\TSTART
SET TSRSV=C:\TANDY88\RESERVE.COM
IF NOT "%1"=="" GOTO USAGE
IF NOT EXIST %TSHOME%\SHELLSEL.EXE GOTO NOHELP
REM RECOVER also rejects execution from inside Windows.
%TSHOME%\SHELLSEL.EXE RECOVER %TSDRV%%TSWIN%\SYSTEM.INI
IF ERRORLEVEL 1 GOTO FAILED
IF NOT EXIST %TSRSV% GOTO NOHELP
IF NOT EXIST %TSDRV%%TSWIN%\WIN.COM GOTO NOWIN
IF NOT EXIST %TSDRV%%TSWIN%\TSHELL.EXE GOTO NOWIN
%TSRSV%
IF ERRORLEVEL 1 GOTO FAILED
%TSDRV%
CD %TSWIN%
IF ERRORLEVEL 1 GOTO FAILED
%TSHOME%\SHELLSEL.EXE SELECT %TSDRV%%TSWIN%\SYSTEM.INI
IF ERRORLEVEL 1 GOTO SELFAIL
%TSDRV%%TSWIN%\WIN.COM /R
REM Do not skip recovery merely because WIN returned an error.
%TSHOME%\SHELLSEL.EXE RECOVER %TSDRV%%TSWIN%\SYSTEM.INI
IF ERRORLEVEL 1 GOTO RECFAIL
GOTO DONE
:SELFAIL
ECHO Shell selection failed. Windows was not started. Attempting recovery.
%TSHOME%\SHELLSEL.EXE RECOVER %TSDRV%%TSWIN%\SYSTEM.INI
IF ERRORLEVEL 1 GOTO RECFAIL
GOTO DONE
:NOHELP
ECHO SHELLSEL.EXE or RESERVE.COM is missing. Windows was not started.
GOTO DONE
:NOWIN
ECHO WIN.COM or TSHELL.EXE is missing. Windows was not started.
GOTO DONE
:FAILED
ECHO Safety check failed. Windows was not started. Keep all TSHELL sidecars.
ECHO Run SHELLSEL RECOVER with the full SYSTEM.INI path before starting Windows.
GOTO DONE
:RECFAIL
ECHO Shell recovery needs attention. Do not start Windows directly.
ECHO Keep every TSHELL sidecar and inspect the SHELLSEL error above.
GOTO DONE
:USAGE
ECHO Use TSTART without arguments, from DOS after completely exiting Windows.
:DONE
SET TSDRV=
SET TSWIN=
SET TSHOME=
SET TSRSV=
