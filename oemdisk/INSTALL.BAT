@ECHO OFF
REM Run from the completed OEM disk, at a real DOS prompt.
REM The Windows path is selected by the host STAGE.PY tool.
IF NOT EXIST RESERVE.COM GOTO SOURCE
IF NOT EXIST TANDY88.BAT GOTO SOURCE
IF NOT EXIST LOCAL.TXT GOTO FONTS
IF NOT EXIST C:\WINDOWS\WIN.COM GOTO NOWIN
IF NOT EXIST C:\WINDOWS\SETUP.EXE GOTO NOWIN
IF EXIST C:\TANDY88\NUL GOTO EXISTS
REM Reserve before any install work; an error must never start Windows.
RESERVE.COM
IF ERRORLEVEL 1 GOTO FAILED
MD C:\TANDY88
IF NOT EXIST C:\TANDY88\NUL GOTO COPYFAIL
COPY /B RESERVE.COM C:\TANDY88\RESERVE.COM > NUL
IF ERRORLEVEL 1 GOTO COPYFAIL
IF NOT EXIST C:\TANDY88\RESERVE.COM GOTO COPYFAIL
COPY /B TANDY88.BAT C:\TANDY88\TANDY88.BAT > NUL
IF ERRORLEVEL 1 GOTO COPYFAIL
IF NOT EXIST C:\TANDY88\TANDY88.BAT GOTO COPYFAIL
ECHO Helper installed in C:\TANDY88. Windows files were not changed.
ECHO Next: C:\TANDY88\TANDY88 SETUP
ECHO Select Other display and supply this completed OEM disk's path.
ECHO Afterwards always start Windows with C:\TANDY88\TANDY88
GOTO DONE
:SOURCE
ECHO Required source files missing. Run INSTALL from the OEM disk.
GOTO DONE
:FONTS
ECHO Incomplete disk. Run STAGE.PY with your own Windows 3.0 media first.
GOTO DONE
:NOWIN
ECHO Windows 3.0 WIN.COM or SETUP.EXE missing in C:\WINDOWS.
ECHO Use STAGE.PY --windows-dir to select the correct DOS directory.
GOTO DONE
:EXISTS
ECHO C:\TANDY88 already exists. No files were changed.
ECHO Use the existing launcher, or reboot and review that directory
ECHO before removing it yourself and installing this package again.
GOTO DONE
:FAILED
ECHO Video reservation failed. Nothing installed. Windows not started.
GOTO DONE
:COPYFAIL
ECHO Helper copy failed. Do not use the incomplete C:\TANDY88 directory.
ECHO Correct the disk problem and review the directory before retrying.
:DONE
