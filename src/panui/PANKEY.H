/* Shared queued commands; a hook records only, owners execute at timer time. */
#ifndef PANKEY_H
#define PANKEY_H
#include <windows.h>
#include "PANCMD.H"
typedef struct {WORD key,command,mods,flags;} PANBIND;
/* Legacy exports keep the published CGAPAN ABI. */
int FAR PASCAL PanKeyNext(void);
BOOL FAR PASCAL PanKeyInstall(HWND,WORD);
BOOL FAR PASCAL PanKeyInstallEx(HWND,WORD,const PANBIND FAR *,int);
BOOL FAR PASCAL PanKeyRemove(void);
/* Small static client, linked into each owner; one DLL is loaded per session. */
int PanInputDefaults(PANBIND *,int);
int PanInputStart(HWND,WORD,const PANBIND *,int);
int PanInputNext(void);
int PanInputActive(void);
int PanInputStop(void);
#endif
