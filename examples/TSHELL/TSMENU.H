#ifndef TSMENU_H
#define TSMENU_H

/* Track a bounded HMENU tree, with children above overlapping parents. */
void FAR TSMenuTrack(HMENU menu, int x, int y, HWND owner);
LONG FAR PASCAL TSMenuProc(HWND w, UINT m, WPARAM wp, LPARAM lp);

#endif
