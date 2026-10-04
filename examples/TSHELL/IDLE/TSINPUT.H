#ifndef TSINPUT_H
#define TSINPUT_H
/* LoadLibrary("TSINPUT.DLL"), GetProcAddress with these exact names. */
typedef BOOL (FAR PASCAL *IDLEBOOLPROC)(void);
typedef DWORD (FAR PASCAL *IDLEGENPROC)(void);
BOOL FAR PASCAL IdleInstall(void);
BOOL FAR PASCAL IdleRemove(void);
DWORD FAR PASCAL IdleGeneration(void);
BOOL FAR PASCAL IdleReady(void);
#endif
