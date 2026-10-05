#ifndef TSSAVER_H
#define TSSAVER_H
#define SAVER_TIMER 3
#define SAVER_PREVIEW_TIMER 5
void TSSaverBegin(HWND owner, HINSTANCE instance);
void TSSaverTick(HWND owner);
void TSSaverHold(int enter);
void TSSaverShutdown(int pending);
void TSSaverStop(HWND owner);
void TSSaverSettings(HWND owner, HINSTANCE instance);
/* Internal settings bridge; only Begin marks this process as primary. */
int TSSaverPrimary(void);
int TSSaverShortcutBusy(void);
int TSSaverReconfigure(void);
void TSSaverPreview(HWND owner, HINSTANCE instance, char *command);
void TSSaverPreviewTick(HWND owner);
void TSSaverPreviewEnd(HWND owner);
#endif
