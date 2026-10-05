#ifndef TSHOLD_H
#define TSHOLD_H
#define HOLD_START (WM_USER+9)
#define HOLD_CLOSE_TIMER 6
void TandyHoldBegin(HWND owner,HINSTANCE instance);
void TandyHoldRefresh(void);
void TandyHoldBlock(int enter);
void TandyHoldShutdown(int pending);
int TandyHoldRequest(HWND owner,DWORD token);
void TandyHoldMenuDone(int complete);
void TandyHoldAction(void);
int TandyHoldClose(HWND owner);
int TandyHoldCloseTick(HWND owner);
void TandyHoldStop(HWND owner);
#endif
