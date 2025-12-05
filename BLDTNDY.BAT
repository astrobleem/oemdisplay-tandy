@echo off
PATH=C:\BIN;%PATH%
SET LIB=C:\LIB
SET INCLUDE=C:\DDK\INC;C:\DDK\286\INC
cd src\tandy16

if "%1"=="1" goto part1
if "%1"=="2" goto part2
if "%1"=="3" goto part3
if "%1"=="4" goto part4
if "%1"=="5" goto part5

echo Usage: BLDTNDY.BAT [1-5]
exit

:part1
echo Starting Build Part 1... > ..\..\BUILD.LOG
del *.obj
del *.map
del *.sym
del tandy16.drv
dir *.asm >> ..\..\BUILD.LOG
echo Assembling Part 1... >> ..\..\BUILD.LOG
masm -I. -v -Mx tandy.asm,tandy.obj; >> ..\..\BUILD.LOG
masm -I. -v -Mx cursors.asm,cursors.obj; >> ..\..\BUILD.LOG
masm -I. -v -Mx inquire.asm,inquire.obj; >> ..\..\BUILD.LOG
masm -I. -v -Mx setmode.asm,setmode.obj; >> ..\..\BUILD.LOG
exit

:part2
echo Starting Build Part 2... >> ..\..\BUILD.LOG
echo Assembling Part 2... >> ..\..\BUILD.LOG
masm -I. -v -Mx disable.asm,disable.obj; >> ..\..\BUILD.LOG
masm -I. -v -Mx color.asm,color.obj; >> ..\..\BUILD.LOG
masm -I. -v -Mx blkwhite.asm,blkwhite.obj; >> ..\..\BUILD.LOG
masm -I. -v -Mx chkstk.asm,chkstk.obj; >> ..\..\BUILD.LOG
masm -I. -v -Mx colorinf.asm,colorinf.obj; >> ..\..\BUILD.LOG
exit

:part3
echo Starting Build Part 3... >> ..\..\BUILD.LOG
echo Assembling Part 3... >> ..\..\BUILD.LOG
masm -I. -v -Mx control.asm,control.obj; >> ..\..\BUILD.LOG
masm -I. -v -Mx fb.asm,fb.obj; >> ..\..\BUILD.LOG
masm -I. -v -Mx charwdth.asm,charwdth.obj; >> ..\..\BUILD.LOG
masm -I. -v -Mx -DLORES dither.asm,lodither.obj; >> ..\..\BUILD.LOG
exit

:part4
echo Starting Build Part 4... >> ..\..\BUILD.LOG
echo Assembling Part 4... >> ..\..\BUILD.LOG
masm -I. -v -Mx -DHIRES dither.asm,hidither.obj; >> ..\..\BUILD.LOG
masm -I. -v -Mx sswitch.asm,sswitch.obj; >> ..\..\BUILD.LOG
masm -I. -v -Mx TGAVID.ASM,TGAVID.OBJ; >> ..\..\BUILD.LOG
masm -I. -v -Mx cursor.asm,cursor.obj; >> ..\..\BUILD.LOG
masm -I. -v -Mx enable.asm,enable.obj; >> ..\..\BUILD.LOG
masm -I. -v -Mx stubs.asm,stubs.obj; >> ..\..\BUILD.LOG
exit

:part5
echo Starting Build Part 5 (Linking)... >> ..\..\BUILD.LOG
echo Linking... >> ..\..\BUILD.LOG
link4 /NOE @tandy16.lnk >> ..\..\BUILD.LOG
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
