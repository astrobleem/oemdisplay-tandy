#ifndef TSSVOPT_H
#define TSSVOPT_H
int SaverStarOptions(HWND owner, HINSTANCE instance, int *speed, int *stars);
BOOL FAR PASCAL StarOptProc(HWND window, UINT message, WPARAM wp, LPARAM lp);
#endif
