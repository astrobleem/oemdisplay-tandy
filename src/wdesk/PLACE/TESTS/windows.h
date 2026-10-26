#ifndef WTP_MOCK_WINDOWS_H
#define WTP_MOCK_WINDOWS_H
#define FAR
#define PASCAL
typedef unsigned short WORD;
typedef unsigned short HWND;
typedef unsigned short HTASK;
typedef unsigned short HDWP;
typedef unsigned UINT;
typedef int BOOL;
typedef long LONG;
typedef unsigned long DWORD;
typedef const char *LPCSTR;
typedef struct {short left,top,right,bottom;} RECT;
typedef struct {short x,y;} POINT;
typedef RECT *LPRECT;
typedef POINT *LPPOINT;
typedef WORD HMODULE;
typedef void (*FARPROC)(void);
#define GWW_HINSTANCE (-6)
#define GW_HWNDPREV 3
#define GW_HWNDNEXT 2
#define GW_OWNER 4
#define GW_CHILD 5
#define GWL_STYLE (-16)
#define WS_CHILD 0x40000000L
#define WS_CAPTION 0x00c00000L
#define SM_CXSCREEN 0
#define SM_CYSCREEN 1
#define SM_CYCAPTION 4
#define SW_SHOWNOACTIVATE 4
#define SW_HIDE 0
#define SW_SHOWNORMAL 1
#define SW_SHOWMINIMIZED 2
#define SW_SHOWMAXIMIZED 3
#define SW_SHOWNA 8
#define SWP_NOSIZE 1u
#define SWP_NOMOVE 2u
#define SWP_NOZORDER 4u
#define SWP_NOACTIVATE 16u
BOOL IsWindow(HWND window);
HTASK GetWindowTask(HWND window);
WORD GetWindowWord(HWND window,int index);
BOOL IsIconic(HWND window);
BOOL IsZoomed(HWND window);
void GetWindowRect(HWND window,RECT *rect);
HWND GetWindow(HWND window,int command);
BOOL ShowWindow(HWND window,int command);
void SetWindowPos(HWND window,HWND after,int x,int y,int width,int height,UINT flags);
HWND GetDesktopWindow(void);
BOOL IsWindowVisible(HWND window);
LONG GetWindowLong(HWND window,int index);
HTASK GetCurrentTask(void);
int GetClassName(HWND window,char *name,int size);
int GetSystemMetrics(int index);
HDWP BeginDeferWindowPos(int count);
HDWP DeferWindowPos(HDWP batch,HWND window,HWND after,int x,int y,int width,int height,UINT flags);
void EndDeferWindowPos(HDWP batch);
HMODULE GetModuleHandle(LPCSTR name);
FARPROC GetProcAddress(HMODULE module,LPCSTR name);
HWND GetActiveWindow(void);
#endif
