ECHO OFF
IF NOT EXIST C:\WINDOWS\WIN.COM GOTO NOWIN
C:\JRPAN\JRGUARD.COM
IF ERRORLEVEL 1 GOTO GUARD
COPY /B C:\JRPAN\JRPAN.DRV C:\WINDOWS\SYSTEM\JRPAN.DRV > NUL
IF ERRORLEVEL 1 GOTO FAILED
C:
CD \WINDOWS
SETUP
GOTO END
:NOWIN
ECHO Install Windows 3.0 in C:\WINDOWS before running this installer.
GOTO END
:FAILED
ECHO File staging failed. Setup was not started.
GOTO END
:GUARD
ECHO The PCjr video page must be reserved before Setup or Windows starts.
:END
