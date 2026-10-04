#ifndef TSBOOT_H
#define TSBOOT_H
#define BOOT_TIMER 2
void TandyBootBegin(HWND w);
void TandyBootTick(HWND w);
void TandyBootStop(HWND w);
void TandyExit(HWND w, int silent);
int TandyBootBusy(void);
#endif
