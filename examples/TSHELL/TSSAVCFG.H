#ifndef TSSAVCFG_H
#define TSSAVCFG_H
#include "SCFGCORE.H"
int SaverConfigRead(SCCONFIG *config);
int SaverConfigProgram(HWND owner, HINSTANCE instance,
                       const SCCONFIG *config, int choice, char *command);
BOOL FAR PASCAL SaverCfgProc(HWND window, UINT message, WPARAM wp, LPARAM lp);
#endif
