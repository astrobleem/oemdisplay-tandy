/* PANDLG.H - the one shared "Panning settings" window.
 *
 * Built in code from STATIC, BUTTON and EDIT children (Windows 3.0 safe, no
 * resource compiler, no Windows 3.1 control or CPL interface). One window
 * per owner process: opening it again only activates it. It owns no timer
 * and no hook; the owner's existing message loop and timer keep driving the
 * pan engine. PanDlgOpen only works inside the owner process (the engine
 * state lives there). A future Control Panel entry must therefore do what
 * PANCFG SETTINGS does: FindWindow the owner, then post PS_MSG_VERT or
 * PS_MSG_XY to it (see PanRoute in PANSET.H).
 *
 * Layout fits a 320x200 viewport. The window is placed inside the current
 * viewport on open and after Home. Apply validates, applies to the running
 * engine, reports the actual resulting mode and saves; Cancel closes and
 * leaves the engine and WIN.INI alone.
 */
#ifndef PANDLG_H
#define PANDLG_H

#include <windows.h>
#include "PANSET.H"

#ifdef __WATCOMC__
#define PAN_EXPORT __export
#else
#define PAN_EXPORT
#endif

typedef struct {
    PANHOSTOPS ops;         /* the owner's engine */
    PANSTORE store;         /* the owner's WIN.INI access */
    const char *title;      /* caption, e.g. "XTPAN panning settings" */
    const char *backend;    /* shown line, e.g. "Vertical software pan" */
} PANHOST;

/* Open or activate the settings window; host must outlive it. Returns the
 * window, or NULL if it could not be created (a driver that no longer
 * answers shows a disabled window only if it could be created). */
HWND PanDlgOpen(HINSTANCE inst, const PANHOST *host);

/* Call first in the owner's message loop: nonzero means the settings window
 * consumed the message (Tab, Enter, Esc and mnemonics) and the owner must
 * not translate or dispatch it. */
int PanDlgMessage(MSG FAR *msg);

/* Owner shutdown or driver loss: destroy the window if it exists. */
void PanDlgClose(void);

/* Window procedure of the class "PanSetDlg". MSC owners list it in the .DEF
 * EXPORTS; Watcom gets it from PAN_EXPORT. */
long FAR PASCAL PAN_EXPORT PanDlgProc(HWND hwnd, UINT msg, WPARAM wParam,
                                      LPARAM lParam);

#endif
