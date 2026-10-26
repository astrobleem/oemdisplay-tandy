#ifndef APPSET_TEST_WINDOWS_H
#define APPSET_TEST_WINDOWS_H
#include <stddef.h>
typedef unsigned int UINT;
typedef unsigned int HINSTANCE;
typedef char *LPSTR;
typedef int HFILE;
#define PASCAL
#define HFILE_ERROR (-1)
#define OF_READ 0
#define OF_SHARE_DENY_WRITE 32
#define WF_STANDARD 16
#define WF_ENHANCED 32
#define MB_OK 0
#define MB_ICONEXCLAMATION 48
#define SW_SHOWNORMAL 1
HFILE _lopen(char *,int);
UINT _lread(HFILE,void *,UINT);
int _lclose(HFILE);
int MessageBox(void *,char *,char *,int);
UINT GetWinFlags(void);
UINT GetModuleFileName(HINSTANCE,char *,int);
HINSTANCE GetModuleHandle(char *);
HINSTANCE LoadLibrary(char *);
void FreeLibrary(HINSTANCE);
UINT WinExec(char *,int);
char *lstrcpy(char *,char *);
char *lstrcat(char *,char *);
#endif
