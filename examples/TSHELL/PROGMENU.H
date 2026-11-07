#ifndef PROGMENU_H
#define PROGMENU_H

/* Include windows.h first. Add PmDialogProc to the application's DEF exports. */
HMENU PmMenuCreate(HINSTANCE instance);
void PmMenuInit(HMENU menu);
/* After root destruction retain IDs for the Win3.0 posted WM_COMMAND. */
void PmMenuDone(void);
int PmMenuCommand(unsigned command);
int PmMenuChoose(HWND owner, unsigned command);
void PmPrograms(HWND owner, HINSTANCE instance);
BOOL FAR PASCAL PmDialogProc(HWND window, UINT message,
                            WPARAM wparam, LPARAM lparam);
/* Returns 1 on launch success, 0 on refusal/failure; displays a short reason. */
int PmLaunch(HWND owner, const char *command);
/* Raw WinExec status, or 0 for a local refusal/CWD error. */
UINT PmLaunchShow(HWND owner, char *command, int show);

#endif
