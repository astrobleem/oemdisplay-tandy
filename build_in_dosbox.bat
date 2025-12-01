@echo off
echo Setting up build environment...
SET PATH=%CD%\BIN;%PATH%
SET LIB=%CD%\LIB;%LIB%
SET INCLUDE=%CD%\SRC;%INCLUDE%
SET CL=/AL

echo Running NMAKE...
NMAKE TNDY16.MAK > BUILD.LOG 2>&1

IF ERRORLEVEL 1 (
    echo Build failed >> BUILD.LOG
) ELSE (
    echo Build driver was successful. >> BUILD.LOG
)

echo Build script finished.
exit


