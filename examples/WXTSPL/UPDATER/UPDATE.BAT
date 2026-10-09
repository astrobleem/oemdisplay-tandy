@ECHO OFF
REM For the combined candidate: modern-side package validation precedes DOS use.
IF NOT "%1"=="" GOTO USAGE
IF NOT EXIST FASTSET.EXE GOTO FAIL
IF NOT EXIST WAVEXT.EXE GOTO FAIL
ECHO Updating wave startup. Default checks compare bytes; no SHA.
FASTSET UPDATE C:\WINDOWS C:\WINXT WAVEXT.EXE
IF ERRORLEVEL 1 GOTO FAIL
ECHO Startup update complete. Backups remain in HELP02 and FAST01.
GOTO END
:USAGE
ECHO Run UPDATE with no arguments from the qualified candidate folder.
GOTO END
:FAIL
ECHO Refused or incomplete. Preserve HELP02, FAST01, WAVE01 and sidecars.
ECHO Do not start Windows until the recorded operation completes or is restored.
:END
