@echo off
PATH=C:\BIN;%PATH%
SET LIB=C:\LIB
SET INCLUDE=C:\DDK\INC;C:\DDK\286\INC
cd src\tandy16

echo Linking... > ..\..\LINK.LOG
link @tandy16.lnk >> ..\..\LINK.LOG
exit
