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

IF EXIST disk1 RD /S /Q disk1
MD disk1
COPY TNDY16.DRV disk1\TNDY16.DRV
COPY OEMSETUP.INF disk1\OEMSETUP.INF
COPY FILE_ID.DIZ disk1\FILE_ID.DIZ
COPY README.TXT disk1\README.TXT

ECHO Converting text files to DOS format...
powershell -Command "(Get-Content disk1\OEMSETUP.INF) | Set-Content disk1\OEMSETUP.INF -Encoding Ascii"
powershell -Command "(Get-Content disk1\FILE_ID.DIZ) | Set-Content disk1\FILE_ID.DIZ -Encoding Ascii"
powershell -Command "(Get-Content disk1\README.TXT) | Set-Content disk1\README.TXT -Encoding Ascii"

IF EXIST TNDY16.ZIP DEL TNDY16.ZIP
ECHO Zipping files...
powershell -Command "Compress-Archive -Path disk1 -DestinationPath TNDY16.ZIP"

ECHO Package created: TNDY16.ZIP (contains disk1 directory)
DIR TNDY16.ZIP

:END
