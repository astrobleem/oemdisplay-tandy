@ECHO OFF
IF EXIST C:\TANDINAT\TANDI.EXE GOTO EXISTS
IF EXIST C:\TANDINAT\TANDY.DAT GOTO EXISTS
IF NOT EXIST C:\TANDINAT\NUL MD C:\TANDINAT
COPY TANDI.EXE C:\TANDINAT\TANDI.EXE
IF ERRORLEVEL 1 GOTO BAD
COPY TANDY.DAT C:\TANDINAT\TANDY.DAT
IF ERRORLEVEL 1 GOTO BAD
ECHO Installed. Start Windows with your guarded WindowsXT launcher.
ECHO Normally: C:\WINXT\WINXT
ECHO Do not bypass reservation/recovery errors.
ECHO Program Manager File-Run: C:\TANDINAT\TANDI.EXE
GOTO END
:EXISTS
ECHO Existing TANDINATOR files found. No files were copied.
ECHO Back up the old files and remove them before installing an update.
GOTO END
:BAD
ECHO Copy failed. Check free disk space and the target folder.
:END
