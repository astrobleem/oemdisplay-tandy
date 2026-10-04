#ifndef TSSAVER_H
#define TSSAVER_H
#define SAVER_TIMER 3
void TSSaverBegin(HWND owner, HINSTANCE instance);
void TSSaverTick(HWND owner);
void TSSaverHold(int enter);
void TSSaverShutdown(int pending);
void TSSaverStop(HWND owner);
#endif
