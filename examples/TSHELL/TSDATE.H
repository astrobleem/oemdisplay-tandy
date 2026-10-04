#ifndef TSDATE_H
#define TSDATE_H

/* Include windows.h first. Export DateProc from the application's DEF. */
void TandyDateTime(HWND owner, HINSTANCE instance);
BOOL FAR PASCAL DateProc(HWND window, UINT message,
                        WPARAM wparam, LPARAM lparam);

#endif
