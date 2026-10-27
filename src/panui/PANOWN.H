/* Shared owner routing. Queries never select a driver mode or move a view. */
#ifndef PANOWN_H
#define PANOWN_H
#include <windows.h>
#define PN_NONE 0
#define PN_VERT 1
#define PN_XY 2
#define PN_CGA 3
#define PN_FIXED 4
HWND PanOwnerFind(int *);
int PanOwnerRoute(int);
WORD PanOwnerMessage(int);
const char *PanOwnerExe(int);
int PanOwnerDetect(int *);
int PanOwnerPath(HINSTANCE,int,char *,int);
#endif
