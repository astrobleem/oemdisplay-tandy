#ifndef TSINPUT_H
#define TSINPUT_H
/* LoadLibrary("TSINPUT.DLL"), GetProcAddress with these exact names. */
typedef BOOL (FAR PASCAL *IDLEBOOLPROC)(void);
typedef DWORD (FAR PASCAL *IDLEGENPROC)(void);
BOOL FAR PASCAL IdleInstall(void);
BOOL FAR PASCAL IdleRemove(void);
DWORD FAR PASCAL IdleGeneration(void);
BOOL FAR PASCAL IdleReady(void);
/* A separate LoadLibrary reference must remain until HoldRemove succeeds. */
typedef BOOL (FAR PASCAL *HOLDINSTALLPROC)(HWND, WORD, BOOL);
typedef BOOL (FAR PASCAL *HOLDPOLICYPROC)(HWND, BOOL);
typedef BOOL (FAR PASCAL *HOLDTAKEPROC)(HWND, DWORD);
BOOL FAR PASCAL HoldInstall(HWND target, WORD message, BOOL allowed);
BOOL FAR PASCAL HoldRemove(void);
BOOL FAR PASCAL HoldPolicy(HWND target, BOOL allowed);
BOOL FAR PASCAL HoldTake(HWND target, DWORD token);
#endif
