#include <stddef.h>
#include <stdint.h>
#define FAR
#define PASCAL
#define TRUE 1
#define FALSE 0
typedef int BOOL;
typedef uint16_t WORD;
typedef uint8_t BYTE;
/* Pointer-sized on host so the unmodified hook can receive EVENTMSG pointers.
   Real ABI/32-bit DWORD is verified by the actual MSC6 native build. */
typedef uintptr_t DWORD;
typedef void *HINSTANCE;
typedef void *HTASK;
typedef void *HWND;
typedef char *LPSTR;
typedef struct { int x, y; } POINT;
typedef void (*FARPROC)(void);
typedef struct { WORD message, paramL, paramH; DWORD time; } EVENTMSG;
typedef EVENTMSG *LPEVENTMSG;
#define HC_ACTION 0
#define HC_SYSMODALON 4
#define HC_SYSMODALOFF 5
#define WH_JOURNALRECORD 0
#define WM_KEYFIRST 0x100
#define WM_KEYLAST 0x108
#define WM_KEYDOWN 0x100
#define WM_KEYUP 0x101
#define WM_SYSKEYDOWN 0x104
#define WM_SYSKEYUP 0x105
#define WM_MOUSEFIRST 0x200
#define WM_MOUSELAST 0x209
#define WM_MOUSEMOVE 0x200
#define WM_LBUTTONDOWN 0x201
#define WM_LBUTTONUP 0x202
#define WM_LBUTTONDBLCLK 0x203
#define WM_RBUTTONDOWN 0x204
#define WM_RBUTTONUP 0x205
#define WM_RBUTTONDBLCLK 0x206
#define WM_MBUTTONDOWN 0x207
#define WM_MBUTTONUP 0x208
#define WM_MBUTTONDBLCLK 0x209
#define VK_LBUTTON 1
#define VK_RBUTTON 2
#define VK_MBUTTON 4
#define GW_OWNER 4
DWORD DefHookProc(int, WORD, DWORD, FARPROC *);
HTASK GetCurrentTask(void);
FARPROC GetProcAddress(HINSTANCE, LPSTR);
DWORD GetTickCount(void);
FARPROC SetWindowsHook(int, FARPROC);
BOOL UnhookWindowsHook(int, FARPROC);
HWND GetSysModalWindow(void);
HWND GetCapture(void);
HWND GetActiveWindow(void);
int GetClassName(HWND, LPSTR, int);
int GetKeyState(int);
int GetAsyncKeyState(int);
void GetCursorPos(POINT *);
HWND GetWindow(HWND, WORD);
BOOL IsWindowEnabled(HWND);
