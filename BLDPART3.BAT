@echo off
PATH=C:\BIN;%PATH%
SET LIB=C:\LIB
SET INCLUDE=C:\DDK\INC;C:\DDK\286\INC
cd src\tandy16
echo Starting Build Part 3... >> ..\..\BUILD.LOG
echo Assembling Part 3... >> ..\..\BUILD.LOG
masm -I. -v -Mx -DHIRES dither.asm,hidither.obj; >> ..\..\BUILD.LOG
masm -I. -v -Mx sswitch.asm,sswitch.obj; >> ..\..\BUILD.LOG
masm -I. -v -Mx stubs.asm,stubs.obj; >> ..\..\BUILD.LOG
masm -I. -v -Mx enable.asm,enable.obj; >> ..\..\BUILD.LOG
echo Linking... >> ..\..\BUILD.LOG
link @tandy16.lnk >> ..\..\BUILD.LOG
if errorlevel 1 goto fail
:success
echo Build Successful! >> ..\..\BUILD.LOG
copy tandy16.drv ..\..\TNDY16.DRV
cd ..\..
exit

:fail
echo Build Failed! >> ..\..\BUILD.LOG
cd ..\..
exit
