/* PANSET.H - shared panning settings model for the existing helpers.
 *
 * Pure C89: no Windows calls, so HOSTUI.PY compiles and tests it on the
 * host. XTPAN.EXE (vertical software panning, escape 0x5850) and XYCTL.EXE
 * (Tandy XY panning, escape 0x5860) each own their pan engine and timer and
 * describe themselves to this module; neither engine is changed by it.
 *
 * Settings are NOT merged by name. Each backend exposes only what its own
 * engine does:
 *   vertical: Step (rows), Edge band width (rows), Dwell (ms before an edge
 *             pan, repeated while the pointer stays), FollowActive (a newly
 *             activated window of ANY class is brought into view).
 *   XY:       Edge panning on/off, edge Repeat interval (100/200/500 ms),
 *             Follow dialogs (class #32770 only, continuous while active),
 *             and the Software/Hardware mode (session only, never saved).
 * Mode 2 of the HPXY mode escape is fault injection: it does not exist here
 * and is never accepted. Mode 3 selects a linked window workspace locally;
 * only 0 (software) or 1 (hardware) may reach a driver mode escape.
 */
#ifndef PANSET_H
#define PANSET_H

#define PS_BACK_NONE 0
#define PS_BACK_VERT 1
#define PS_BACK_XY   2

#define PS_CAP_STEP    0x0001u  /* vertical: Step rows */
#define PS_CAP_EDGE    0x0002u  /* vertical: edge band width, rows */
#define PS_CAP_DWELL   0x0004u  /* vertical: dwell/repeat delay, ms */
#define PS_CAP_FOLLOW  0x0008u  /* vertical: follow any activated window */
#define PS_CAP_EDGEON  0x0010u  /* XY: edge panning enabled */
#define PS_CAP_REPEAT  0x0020u  /* XY: edge repeat interval */
#define PS_CAP_FOLLOWD 0x0040u  /* XY: follow active dialogs only */
#define PS_CAP_MODE    0x0080u  /* XY: Software/Hardware, with read-back */
#define PS_CAP_HOME    0x0100u  /* viewport can be sent Home */
#define PS_CAP_DESK    0x0200u  /* caller linked the window-moving alternative */
#define PS_CAP_HARD    0x0400u  /* a readable hardware mode is available */
#define PS_CAP_SOFT    0x0800u  /* an existing framebuffer software pan exists */

#define PS_MODE_SOFT 0
#define PS_MODE_HARD 1
#define PS_MODE_DESK 3          /* owner-local choice; never a driver escape */

#define PS_OK        0
#define PS_E_BACKEND 1   /* no usable backend */
#define PS_E_STEP    2
#define PS_E_EDGE    3
#define PS_E_DWELL   4
#define PS_E_FOLLOW  5
#define PS_E_EDGEON  6
#define PS_E_REPEAT  7
#define PS_E_FOLLOWD 8
#define PS_E_MODE    9
#define PS_E_TEXT    10  /* field is not a plain number */
#define PS_E_STORE   11  /* WIN.INI write failed */
#define PS_E_APPLY   12  /* the engine refused the settings */
#define PS_E_LOST    13  /* the driver no longer answers */

/* WIN.INI layout. [XTPan] keeps its existing keys and defaults; XYCTL
 * persists to its own section. Only exposed keys are ever written. */
#define PS_SEC_VERT "XTPan"
#define PS_KEY_STEP "Step"
#define PS_KEY_DWELL "Dwell"
#define PS_KEY_EDGE "Edge"
#define PS_KEY_FOLLOW "FollowActive"
#define PS_SEC_XY "XYPan"
#define PS_KEY_EDGEON "EdgeOn"
#define PS_KEY_REPEAT "RepeatMs"
#define PS_KEY_FOLLOWD "FollowDialogs"

/* Registered window messages that make the running owner open (or just
 * activate) its settings window. The owner never starts a second engine. */
#define PS_MSG_VERT "XTPanSettings"
#define PS_MSG_XY   "XYPanSettings"
#define PS_ARG_SETTINGS "/SETTINGS"

typedef struct {
    int backend;            /* PS_BACK_* */
    unsigned caps;          /* PS_CAP_* the detected backend supports */
    int viewX, viewY;       /* viewport origin in the workspace */
    int viewW, viewH;       /* viewport size */
    int workW, workH;       /* workspace (logical desktop) size */
} PANCAPS;

typedef struct {
    int step, dwell, edge, follow;               /* vertical */
    int edgeOn, repeat, followDlg, mode;         /* XY */
} PANSET;

/* WIN.INI access is injected: the owners wrap GetProfileInt and
 * WriteProfileString, HOSTUI.PY supplies a fake. put returns nonzero when
 * the value was written. */
typedef struct {
    void *ctx;
    int (*get)(void *ctx, const char *section, const char *key, int def);
    int (*put)(void *ctx, const char *section, const char *key, int value);
} PANSTORE;

/* Operations the owner provides for its own engine. */
typedef struct {
    void *ctx;
    /* Re-read the driver. Nonzero: caps and live are current. Zero: the
     * driver no longer answers (caps->backend is set to PS_BACK_NONE). */
    int (*query)(void *ctx, PANCAPS *caps, PANSET *live);
    /* Apply already validated settings to the running engine. actual gets
     * what is really in effect afterwards (for the mode, read back from the
     * driver, not assumed from the request). note may receive a short
     * explanation when actual differs from want. Returns PS_OK, PS_E_APPLY
     * or PS_E_LOST. */
    int (*apply)(void *ctx, const PANSET *want, PANSET *actual,
                 char *note, int noteCap);
    /* Send the viewport to the workspace origin. Nonzero on success. */
    int (*home)(void *ctx);
} PANHOSTOPS;

typedef struct {
    PANCAPS caps;
    PANSET live;            /* what the engine runs now */
    PANSET work;            /* what the dialog is editing */
    int differs;            /* last Apply: actual result != request */
    char status[80];        /* one line for the dialog */
} PANMODEL;

/* Defaults. vertical: Step 50, Dwell 400, Edge 3, FollowActive 1 (as
 * XTPAN.C reads them today). XY: EdgeOn 0, Repeat 100, FollowDlg 0, mode
 * software: what XYCTL starts with today. */
void PanSetDefaults(int backend, PANSET *s);

/* Capability mask a backend offers. modeReadback is nonzero only when the
 * owner can read the real mode back (otherwise PS_CAP_MODE is withheld). */
unsigned PanCapsFor(int backend, int modeReadback);

/* Validate only the fields caps exposes; ignores the rest. Vertical
 * bounds: Step 8..workH, Edge 1..viewH/2, Dwell 0..10000, Follow 0/1: no
 * 8/4 alignment is imposed. XY: EdgeOn 0/1, Repeat 100/200/500,
 * FollowDlg 0/1, mode 0/1 and only when PS_CAP_MODE is present. Returns
 * PS_OK or the PS_E_* code of the first bad field. */
int PanSetValidate(const PANCAPS *c, const PANSET *s);

const char *PanSetErrorText(int code);

/* Plain decimal only: optional blanks, 1..5 digits, no sign. PS_OK or
 * PS_E_TEXT. */
int PanParseInt(const char *text, int *value);

/* Read persisted settings. Starts from defaults; vertical mirrors the
 * startup clamps of XTPAN.C (Step >= 8, Edge >= 1, Follow nonzero is 1); XY
 * falls back to the default for any value outside what the engine accepts.
 * The mode is never loaded. */
void PanSetLoad(const PANCAPS *c, PANSET *s, const PANSTORE *st);

/* Validate, then write ONLY the keys caps exposes (never Enabled, KeyMods,
 * KeyDown/KeyUp/KeyTop, LogKeys, LogFile, and never the mode). PS_OK, a
 * validation code (nothing written) or PS_E_STORE. */
int PanSetSave(const PANCAPS *c, const PANSET *s, const PANSTORE *st);

/* Dialog model. Open queries the driver and copies live to work. Cancel
 * discards work and touches neither the engine nor the store. Apply
 * validates work, applies it, takes the engine's actual result as live and
 * only then saves; any earlier failure leaves live and the store alone.
 * Home asks the engine to go Home and re-reads the viewport origin. All
 * set model->status. */
int PanModelOpen(PANMODEL *m, const PANHOSTOPS *ops);
void PanModelCancel(PANMODEL *m);
int PanModelApply(PANMODEL *m, const PANHOSTOPS *ops, const PANSTORE *st);
int PanModelHome(PANMODEL *m, const PANHOSTOPS *ops);

/* Command line of PANCFG.EXE. Exactly like today: "OFF" (any case) turns
 * the helper off; anything else, including nothing, turns it on. New:
 * "SETTINGS" or "/SETTINGS" (any case, nothing else on the line) opens the
 * settings of the running helper. */
#define PS_CMD_ENABLE   0
#define PS_CMD_OFF      1
#define PS_CMD_SETTINGS 2
int PanCmdParse(const char *cmd);

/* What PANCFG SETTINGS does. A running owner is only told to open its
 * dialog; a stopped but enabled one is started with /SETTINGS; a disabled
 * one is left alone and the user is told. Never edits load= or Enabled. */
#define PS_ROUTE_POST  0
#define PS_ROUTE_START 1
#define PS_ROUTE_OFF   2
int PanRoute(int ownerRunning, int enabled);

/* What an owner EXE does at startup when another instance may exist:
 * PS_OWN_RUN: become the owner; PS_OWN_FORWARD: post the open message to
 * the existing owner and exit; PS_OWN_EXIT: exit (or just activate it). */
#define PS_OWN_RUN     0
#define PS_OWN_FORWARD 1
#define PS_OWN_EXIT    2
int PanOwnerStart(int otherRunning, int settingsRequested);

#endif
