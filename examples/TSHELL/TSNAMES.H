/* Read-only friendly-name display bridge. No DOS path comes from this API. */
#ifndef TSNAMES_H
#define TSNAMES_H
#define TSNAMES_LIMIT 128
#define TSNAMES_TEXT 260
#define TSNAMES_READY 2
/* Begin/Step: 1 pending, 0 aliases-only, -1 error, 2 ready to verify.
   Begin reads no sectors. Step reads at most one, never pumps messages.
   On READY the UI MUST invalidate its mapping, re-enumerate the SAME
   absolute DOS CWD and mask into the hidden list, confirm CWD, and only
   then call Commit. The bridge never changes the hidden list or DOS CWD.
   Commit compares every saved native row/count/type before display edits.
   On any error the UI rebuilds visible aliases, or disables a failed list.
   End is idempotent; call on every completion, cancel and error. */
int TSNamesBegin(LPCSTR absoluteShortCwd,HWND hiddenAliases,HWND visibleNames);
int TSNamesStep(void);
int TSNamesCommit(void);
void TSNamesEnd(void);
#endif
