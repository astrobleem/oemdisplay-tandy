@echo off
PATH=C:\BIN;%PATH%
SET LIB=C:\LIB
SET INCLUDE=C:\DDK\INC;C:\DDK\286\INC
cd src\tandy16

echo Rebuilding Part 4... > ..\..\BUILD.LOG
masm -I. -v -Mx sswitch.asm,sswitch.obj; >> ..\..\BUILD.LOG
masm -I. -v -Mx TGAVID.ASM,TGAVID.OBJ; >> ..\..\BUILD.LOG
masm -I. -v -Mx cursor.asm,cursor.obj; >> ..\..\BUILD.LOG
masm -I. -v -Mx enable.asm,enable.obj; >> ..\..\BUILD.LOG

echo Linking... >> ..\..\BUILD.LOG
link4 @T16OBJS.LNK >> ..\..\BUILD.LOG
if errorlevel 1 goto fail
echo Build Successful! >> ..\..\BUILD.LOG
copy tandy16.drv ..\..\TNDY16.DRV
exit

:fail
echo Build Failed! >> ..\..\BUILD.LOG
exit
