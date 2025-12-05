@echo off
PATH=C:\BIN;%PATH%
echo. > C:\INPUT.TXT
echo Checking LIBW.LIB... > C:\LIBS.LOG
lib C:\LIB\LIBW.LIB,C:\LIBW.LST < C:\INPUT.TXT >> C:\LIBS.LOG
echo. >> C:\LIBS.LOG
echo Checking KERNEL.LIB... >> C:\LIBS.LOG
lib C:\LIB\KERNEL.LIB,C:\KERNEL.LST < C:\INPUT.TXT >> C:\LIBS.LOG
echo Done. >> C:\LIBS.LOG
exit
