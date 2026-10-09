#ifndef CP_WIN_STUB
#define CP_WIN_STUB
#include <stddef.h>
typedef unsigned int UINT;
typedef unsigned short WORD;
typedef int HANDLE;
typedef int (*FARPROC)(int);
typedef int HWND;
typedef int HMENU;
typedef int HINSTANCE;
typedef int BOOL;
typedef UINT WPARAM;
typedef long LPARAM;
typedef struct {char szPathName[144];} OFSTRUCT;
#define FALSE 0
#define TRUE 1
#define FAR
#define PASCAL
#define MF_STRING 0
#define MF_SEPARATOR 0x800
#define MF_BYCOMMAND 0
#define MF_BYPOSITION 0x400
#define MF_POPUP 0x10
#define MF_GRAYED 1
#define MF_DISABLED 2
#define HFILE_ERROR (-1)
#define OF_EXIST 0x4000
#define SW_SHOWNORMAL 1
#define SW_RESTORE 9
#define WM_COMMAND 0x111
HANDLE GetModuleHandle(const char *);
FARPROC GetProcAddress(HANDLE,const char *);
int AppendMenu(HMENU,UINT,UINT,const char *);
HWND FindWindow(const char *,const char *);
UINT GetWindowsDirectory(char *,int);
char *lstrcat(char *,const char *);
int OpenFile(char *,OFSTRUCT *,UINT);
UINT WinExec(char *,int);
int wsprintf(char *,const char *,...);
BOOL IsWindowEnabled(HWND);
HWND GetLastActivePopup(HWND);
int BringWindowToTop(HWND);
HWND SetActiveWindow(HWND);
int ShowWindow(HWND,int);
HMENU GetMenu(HWND);
HMENU GetSubMenu(HMENU,int);
UINT GetMenuState(HMENU,UINT,UINT);
int GetMenuItemCount(HMENU);
UINT GetMenuItemID(HMENU,int);
int GetMenuString(HMENU,UINT,char *,int,UINT);
int lstrcmpi(const char *,const char *);
BOOL PostMessage(HWND,UINT,WPARAM,LPARAM);
#endif
