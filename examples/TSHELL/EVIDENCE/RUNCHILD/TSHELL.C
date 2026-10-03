#define WINVER 0x0300
#include <windows.h>
#include <direct.h>
int PASCAL WinMain(HINSTANCE a,HINSTANCE b,LPSTR cmd,int show){HFILE f;char cwd[144];f=_lcreat("C:\\CHILD.LOG",0);_lwrite(f,cmd,lstrlen(cmd));_lwrite(f,"\r\n",2);if(getcwd(cwd,sizeof(cwd)))_lwrite(f,cwd,lstrlen(cwd));_lclose(f);return 0;}
