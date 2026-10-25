#ifndef SNDSTUB_H
#define SNDSTUB_H
#include <stddef.h>
#undef NULL
#define NULL 0
#define FAR
#define PASCAL
typedef unsigned WORD;
typedef unsigned long DWORD;
typedef int HWND;
typedef int HINSTANCE;
typedef int HMODULE;
typedef long LONG;
typedef void (*FARPROC)(void);
typedef struct {int style;LONG (*lpfnWndProc)(void);int cbClsExtra,cbWndExtra;HINSTANCE hInstance;int hIcon,hCursor,hbrBackground;char *lpszMenuName,*lpszClassName;} WNDCLASS;
#define WF_PMODE 1
#define GWW_HINSTANCE -6
#define GW_HWNDFIRST 0
#define GW_HWNDNEXT 2
#define WS_POPUP 0
unsigned GetWinFlags(void);
unsigned TpSoundTestRom(void);
int IsWindow(HWND);
unsigned GetWindowWord(HWND,int);
int GetClassName(HWND,char *,int);
int lstrcmp(char *,char *);
HWND FindWindow(char *,char *);
HMODULE GetModuleHandle(char *);
FARPROC GetProcAddress(HMODULE,char *);
HWND GetWindow(HWND,int);
int outp(unsigned,unsigned);
int DestroyWindow(HWND);
int UnregisterClass(char *,HINSTANCE);
HWND GetActiveWindow(void);
int IsWindowEnabled(HWND);
int IsIconic(HWND);
LONG DefWindowProc(void);
int RegisterClass(WNDCLASS *);
HWND CreateWindow(char *,char *,unsigned,int,int,int,int,HWND,void *,HINSTANCE,void *);
int OpenSound(void);
void CloseSound(void);
#endif
