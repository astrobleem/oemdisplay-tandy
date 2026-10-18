#include <stdint.h>
#include <string.h>
#include <stdlib.h>
#include <stdio.h>
#undef NULL
#define NULL 0
#define FAR
#define PASCAL
typedef uint16_t WORD,HWND,HANDLE,HINSTANCE,HMODULE,UINT;
typedef int16_t WPARAM;
typedef uint32_t DWORD;
typedef int32_t LONG,LPARAM;
typedef int BOOL;
typedef struct {int left,top,right,bottom;} RECT;
typedef char *LPSTR;
typedef void (*FARPROC)(void);
typedef LONG (*WNDPROC)(HWND,UINT,WPARAM,LPARAM);
typedef struct {int dummy;} MSG;
typedef struct {int style;WNDPROC lpfnWndProc;int cbClsExtra,cbWndExtra;HINSTANCE hInstance;HANDLE hIcon,hCursor,hbrBackground;char *lpszMenuName,*lpszClassName;} WNDCLASS;
struct dostime_t {unsigned char hour,minute,second,hsecond;};
#define TRUE 1
#define FALSE 0
#define WS_CHILD 0x40000000UL
#define WS_VSCROLL 0x00200000UL
#define WS_OVERLAPPED 0
#define ES_MULTILINE 4
#define LBS_MULTICOLUMN 512
#define LBS_OWNERDRAWVARIABLE 32
#define SBS_VERT 1
#define GWL_STYLE -16
#define GW_OWNER 4
#define SB_VERT 1
#define SB_LINEUP 0
#define SB_LINEDOWN 1
#define SB_ENDSCROLL 8
#define WM_VSCROLL 0x115
#define EM_LINESCROLL 0x406
#define LB_GETTOPINDEX 0x40f
#define LB_GETCOUNT 0x40c
#define LB_SETTOPINDEX 0x418
#define WM_TIMER 0x113
#define WM_QUERYENDSESSION 0x11
#define WM_ENDSESSION 0x16
#define WM_CLOSE 0x10
#define WM_DESTROY 2
#define MB_OK 0
#define MB_ICONEXCLAMATION 0x30
#define MAKELONG(a,b) ((LPARAM)((uint16_t)(a)|((DWORD)(uint16_t)(b)<<16)))
HWND FindWindow(char *,char *);HANDLE GetProp(HWND,char *);BOOL IsWindow(HWND);BOOL IsIconic(HWND);BOOL IsWindowVisible(HWND);BOOL IsWindowEnabled(HWND);
HWND GetSysModalWindow(void);HWND GetCapture(void);BOOL IsChild(HWND,HWND);HWND GetWindow(HWND,int);HMODULE GetModuleHandle(char *);
LONG GetWindowLong(HWND,int);int GetClassName(HWND,char *,int);HWND GetParent(HWND);void GetScrollRange(HWND,int,int *,int *);
void GetWindowRect(HWND,RECT *);
HWND GetFocus(void);HWND GetActiveWindow(void);DWORD GetTickCount(void);void _dos_gettime(struct dostime_t *);
int lstrcmpi(char *,char *);LONG SendMessage(HWND,UINT,WPARAM,LPARAM);BOOL PostMessage(HWND,UINT,WPARAM,LPARAM);
void DestroyWindow(HWND);void KillTimer(HWND,UINT);void RemoveProp(HWND,char *);void PostQuitMessage(int);LONG DefWindowProc(HWND,UINT,WPARAM,LPARAM);
int MessageBox(HWND,char *,char *,UINT);
FARPROC GetProcAddress(HMODULE,char *);WORD RegisterWindowMessage(char *);FARPROC MakeProcInstance(FARPROC,HINSTANCE);
BOOL RegisterClass(WNDCLASS *);HWND CreateWindow(char *,char *,DWORD,int,int,int,int,HWND,HANDLE,HINSTANCE,void *);
WORD SetTimer(HWND,UINT,UINT,void *);BOOL SetProp(HWND,char *,HANDLE);BOOL GetMessage(MSG *,HWND,UINT,UINT);void TranslateMessage(MSG *);void DispatchMessage(MSG *);void FreeProcInstance(FARPROC);
