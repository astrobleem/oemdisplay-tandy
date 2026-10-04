#ifndef WINDOWS_H
#define WINDOWS_H
#include <stddef.h>
typedef unsigned UINT; typedef unsigned WPARAM; typedef long LPARAM; typedef unsigned long DWORD; typedef int HWND; typedef int HMODULE; typedef int HINSTANCE; typedef void *FARPROC; typedef struct {char szPathName[144];} OFSTRUCT;
#define FAR
#define PASCAL
typedef int BOOL;
#define MB_OK 0
#define MB_ICONEXCLAMATION 48
#define HFILE_ERROR -1
#define GWW_HINSTANCE (-6)
unsigned GetWindowWord(HWND,int);
#define OF_EXIST 0x4000
#define SW_HIDE 0
#define SW_SHOWNORMAL 1
#define SW_SHOWMINNOACTIVE 7
int lstrcmpi(const char*,const char*); int lstrlen(const char*); char*lstrcpy(char*,const char*);char*lstrcat(char*,const char*);
UINT GetWindowsDirectory(char*,UINT);int GetPrivateProfileString(const char*,const char*,const char*,char*,int,const char*);int GetPrivateProfileInt(const char*,const char*,int,const char*);int GetProfileString(const char*,const char*,const char*,char*,int);
int OpenFile(const char*,OFSTRUCT*,UINT);int FindWindow(const char*,const char*);HMODULE GetModuleHandle(const char*);FARPROC GetProcAddress(HMODULE,const char*);int SetTimer(HWND,int,int,void*);int KillTimer(HWND,int);UINT WinExec(const char*,UINT);int ExitWindows(DWORD,unsigned);int MessageBox(HWND,const char*,const char*,UINT);
#endif
