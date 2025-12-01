@echo off
PATH=C:\BIN;%PATH%
SET LIB=C:\LIB
SET INCLUDE=C:\DDK\INC;C:\DDK\286\INC
cd src\tandy16
echo Starting Build... > ..\...\BUILD.LOG
del *.obj
del *.map
del *.sym
del tandy16.drv
dir *.asm >> ..\..\BUILD.LOG
nmake /a tandy16.drv >> ..\..\BUILD.LOG
if exist tandy16.drv goto success
echo Linking... >> ..\..\BUILD.LOG
link @tandy16.lnk >> ..\..\BUILD.LOG
if errorlevel 1 goto fail
:success
echo Build Successful! >> ..\..\BUILD.LOG
copy tandy16.drv ..\...\TNDY16.DRV
cd ..\..
exit

:fail
echo Build Failed! >> ..\..\BUILD.LOG
cd ..\..
exit
