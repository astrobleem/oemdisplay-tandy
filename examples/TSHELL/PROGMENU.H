#ifndef PROGMENU_H
#define PROGMENU_H

/* Include windows.h first. Add PmDialogProc to the application's DEF exports. */
void PmPrograms(HWND owner, HINSTANCE instance);
BOOL FAR PASCAL PmDialogProc(HWND window, UINT message,
                            WPARAM wparam, LPARAM lparam);
/* Returns 1 on launch success, 0 on refusal/failure; displays a short reason. */
int PmLaunch(HWND owner, const char *command);
/* Raw WinExec status, or 0 for a local refusal/CWD error. */
UINT PmLaunchShow(HWND owner, char *command, int show);

#endif
