@ECHO OFF
REM Build and package TNDY16 driver (Windows Compatible)

IF NOT EXIST TNDY16.DRV (
    ECHO TNDY16.DRV not found. Creating build...
    CALL build_driver.bat
)

IF NOT EXIST TNDY16.DRV (
    ECHO Build failed or TNDY16.DRV still missing.
    GOTO END
)

IF EXIST TNDY16 RD /S /Q TNDY16
MD TNDY16
COPY TNDY16.DRV TNDY16\TNDY16.DRV
COPY OEMSETUP.INF TNDY16\OEMSETUP.INF
COPY FILE_ID.DIZ TNDY16\FILE_ID.DIZ
COPY README.TXT TNDY16\README.TXT

ECHO Converting text files to DOS format...
powershell -Command "(Get-Content TNDY16\OEMSETUP.INF) | Set-Content TNDY16\OEMSETUP.INF -Encoding Ascii"
powershell -Command "(Get-Content TNDY16\FILE_ID.DIZ) | Set-Content TNDY16\FILE_ID.DIZ -Encoding Ascii"
powershell -Command "(Get-Content TNDY16\README.TXT) | Set-Content TNDY16\README.TXT -Encoding Ascii"

IF EXIST TNDY16.ZIP DEL TNDY16.ZIP
ECHO Zipping files...
powershell -Command "Compress-Archive -Path TNDY16\* -DestinationPath TNDY16.ZIP"

ECHO Package created: TNDY16.ZIP
DIR TNDY16.ZIP

:END
