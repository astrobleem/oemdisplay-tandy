@echo off
echo Building Tandy 16-color Display Driver...
echo.

REM Delete any existing driver and log
if exist TNDY16.DRV del TNDY16.DRV
if exist BUILD.LOG del BUILD.LOG

echo Starting DOSBox to run the build...
echo DOSBox will automatically run BUILD.BAT.
echo Close the DOSBox window when the build is complete.
echo.

REM Run DOSBox - it will automatically run BUILD.BAT
start "" "DOSBOX\DOSBox-0.74-3\DOSBox.exe" -conf dosbox-x.conf

echo Waiting for build to complete...
echo Press any key when you've closed DOSBox...
REM pause >nul

echo.
echo Checking build results...
echo Reading BUILD.LOG:
echo ================================================
if exist BUILD.LOG (
    type BUILD.LOG
) else (
    echo BUILD.LOG not found!
)
echo ================================================

echo.
echo Checking for TNDY16.DRV...
if exist TNDY16.DRV (
    echo ✓ Driver file TNDY16.DRV found!
    for %%A in (TNDY16.DRV) do echo   Size: %%~zA bytes
) else (
    echo ✗ Driver file TNDY16.DRV not found!
)

echo.
echo Build process complete!
