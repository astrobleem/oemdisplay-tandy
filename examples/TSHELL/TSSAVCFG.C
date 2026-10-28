/* Explicit, compact saver settings. Windows 3.0 / 8086, 160x200 safe. */
#define WINVER 0x0300
#include <windows.h>
#include <dos.h>
#include "TNOTICE.H"
#include "TSSAVER.H"
#include "TSSAVCFG.H"
#include "TSSVOPT.H"
#include "PROGMENU.H"
#define CFG_WIDTH 128
#define CFG_HEIGHT 164
#define CFG_MATRIX 120
#define CFG_STARFIELD 119
#define CFG_MAZE 121
#define CFG_NONE 122
#define CFG_SECONDS 123
#define CFG_PREVIEW 124
#define CFG_APPLY 125
#define CFG_OPTIONS 126
#define CFG_CUBE 127
#define CFG_CHOICE 128
#define CFG_STARTPREVIEW (WM_USER + 71)
#define CFG_RELEASE_TIMER 4
static HINSTANCE cfgInstance;
static HWND cfgWindow;
static int cfgBusy, cfgApplying, cfgLoaded, cfgClosing, cfgPreviewPending;
static int cfgCompact;
static int stagedSpeed, stagedStars, optionsDirty;
static SCCONFIG loaded;
static char iniPath[144];
static char *keys[SC_KEYS] = { "Enabled", "IdleSeconds", "Choice", "Program", "MazeProgram",
                             "StarProgram", "Speed", "Stars", "CubeProgram" };
static char *section(int key)
{ return key == SC_SPEED || key == SC_STARS ? "Starfield" : "ScreenSaver"; }

static int iniName(void)
{
    int n = GetWindowsDirectory(iniPath, sizeof(iniPath));
    if (!n || n >= sizeof(iniPath) - 12) return 0;
    lstrcat(iniPath, "\\TSHELL.INI"); return 1;
}
static int readKey(void *context, int key, char *value, int size)
{
    unsigned attr, error;
    HFILE file;
    int n;
    error = _dos_getfileattr(iniPath, &attr);
    if (error == 2) return 0;
    if (error || (attr & 0x10)) return -1;
    file = _lopen(iniPath, OF_READ | OF_SHARE_DENY_NONE);
    if (file == HFILE_ERROR) return -1;
    _lclose(file);
    /* Win3 strips control characters from default strings: use printable text. */
    n = GetPrivateProfileString(section(key), keys[key], "{TSHELL-ABSENT-A}", value, size, iniPath);
    if (n >= size - 1) return -1;
    if (lstrcmp(value, "{TSHELL-ABSENT-A}")) return 1;
    /* A literal value equal to a sentinel must still count as present. */
    n = GetPrivateProfileString(section(key), keys[key], "{TSHELL-ABSENT-B}", value, size, iniPath);
    if (n >= size - 1) return -1;
    return lstrcmp(value, "{TSHELL-ABSENT-B}") != 0;
}
static int writeKey(void *context, int key, const char *value)
{
    unsigned attr, error;
    error = _dos_getfileattr(iniPath, &attr);
    /* Win3 creates a new private INI only with its Windows-relative name. */
    if (error == 2) return !value ||
        WritePrivateProfileString(section(key), keys[key], (LPSTR)value, "TSHELL.INI") != 0;
    if (error || (attr & 0x11)) return 0;
    return WritePrivateProfileString(section(key), keys[key],
        value ? (LPSTR)value : (LPSTR)NULL, iniPath) != 0;
}
static void configIO(SCIO *io)
{ io->read = readKey; io->write = writeKey; io->context = NULL; }
int SaverConfigRead(SCCONFIG *config)
{
    SCIO io;
    if (!iniName()) return SC_READFAIL;
    configIO(&io); return ScRead(&io, config);
}
int SaverConfigProgram(HWND w, HINSTANCE instance,
                       const SCCONFIG *config, int choice, char *command)
{
    const char *path;
    OFSTRUCT of;
    if (choice != SC_MATRIX && choice != SC_MAZE && choice != SC_STARFIELD && choice != SC_CUBE) {
        TinyNotice(w, instance, "Saver", "Choose a saver."); return 0;
    }
    path = ScProgram(config, choice);
    if (!ScAbsolute(path)) {
        TinyNotice(w, instance, "Saver", "Bad app path.\nSee TSHELL.INI."); return 0;
    }
    if (OpenFile((LPSTR)path, &of, OF_EXIST) == HFILE_ERROR) {
        TinyNotice(w, instance, "Saver", choice == SC_CUBE ? "Cube missing.\nRun CUBESET." : choice == SC_STARFIELD ?
                   "Starfield\nmissing. Check\nStarProgram." : choice == SC_MAZE ?
                   "Maze missing.\nNothing saved." : "Matrix missing.\nNothing saved.");
        return 0;
    }
    return ScCommand(path, 0, 0, command, 128);
}
static int selection(HWND w)
{
    int n;
    if (cfgCompact) {
        n = (int)SendDlgItemMessage(w, CFG_CHOICE, CB_GETCURSEL, 0, 0L);
        return n == 0 ? SC_MATRIX : n == 1 ? SC_MAZE : n == 2 ? SC_STARFIELD :
               n == 3 ? SC_CUBE : n == 4 ? SC_NONE : -1;
    }
    if (IsDlgButtonChecked(w, CFG_MATRIX)) return SC_MATRIX;
    if (IsDlgButtonChecked(w, CFG_MAZE)) return SC_MAZE;
    if (IsDlgButtonChecked(w, CFG_STARFIELD)) return SC_STARFIELD;
    if (IsDlgButtonChecked(w, CFG_NONE)) return SC_NONE;
    if (IsDlgButtonChecked(w, CFG_CUBE)) return SC_CUBE;
    return -1;
}
static void choose(HWND w, int id)
{
    if (cfgCompact) {
        SendDlgItemMessage(w, CFG_CHOICE, CB_SETCURSEL, id == CFG_MATRIX ? 0 :
            id == CFG_MAZE ? 1 : id == CFG_STARFIELD ? 2 : id == CFG_CUBE ? 3 : 4, 0L);
        return;
    }
    CheckDlgButton(w, CFG_MATRIX, id == CFG_MATRIX);
    CheckDlgButton(w, CFG_MAZE, id == CFG_MAZE);
    CheckDlgButton(w, CFG_STARFIELD, id == CFG_STARFIELD);
    CheckDlgButton(w, CFG_NONE, id == CFG_NONE);
    CheckDlgButton(w, CFG_CUBE, id == CFG_CUBE);
}
static void updatePreview(HWND w)
{
    EnableWindow(GetDlgItem(w, CFG_PREVIEW), cfgLoaded && selection(w) > SC_NONE);
    EnableWindow(GetDlgItem(w, CFG_OPTIONS), cfgLoaded &&
        (selection(w) == SC_STARFIELD || selection(w) == SC_CUBE));
}
static int inputHeld(void)
{
    int key;
    for (key = 1; key < 256; ++key)
        if (GetAsyncKeyState(key) & 0x8000) return 1;
    return GetCapture() != NULL;
}
static void applyConfig(HWND w)
{
    SCIO io;
    SCCONFIG after;
    char seconds[12], command[128], speed[4], stars[4];
    int result, choice, applied;
    char *message;
    if (cfgApplying || !cfgLoaded || cfgClosing) return;
    cfgApplying = 1;
    GetDlgItemText(w, CFG_SECONDS, seconds, sizeof(seconds));
    choice = selection(w);
    if (!ScSeconds(seconds)) {
        TinyNotice(w, cfgInstance, "Saver", "Idle seconds:\n10 to 3600.\nWhole numbers.");
        SetFocus(GetDlgItem(w, CFG_SECONDS)); cfgApplying = 0; return;
    }
    if (choice < SC_NONE) {
        TinyNotice(w, cfgInstance, "Saver", "Choose a saver\nor None.");
        cfgApplying = 0; return;
    }
    if (choice != SC_NONE && !SaverConfigProgram(w, cfgInstance, &loaded, choice, command)) {
        cfgApplying = 0; return;
    }
    if (cfgClosing || !IsWindow(w)) { cfgApplying = 0; return; }
    configIO(&io);
    wsprintf(speed, "%d", stagedSpeed); wsprintf(stars, "%d", stagedStars);
    result = ScSaveOptions(&io, &loaded, seconds, choice,
        optionsDirty ? speed : NULL, optionsDirty ? stars : NULL, &after);
    if (result == SC_OK) {
        loaded = after;
        optionsDirty = 0;
        applied = TSSaverReconfigure();
        if (applied > 0) message = "Saved.\nApplies now.";
        else if (!applied) message = "Saved for next\nshell startup.";
        else message = NULL; /* Policy already explained the safe failure. */
    } else if (result == SC_READFAIL) message = "Cannot read\nTSHELL.INI.\nNothing saved.";
    else if (result == SC_CONFLICT) {
        cfgLoaded = 0;
        message = "Setup changed.\nReopen/check.\nNothing saved.";
    } else if (result == SC_WRITEFAIL) message = "Save failed.\nOld values\nrestored.";
    else {
        cfgLoaded = 0;
        message = "Save uncertain.\nReopen/check\nTSHELL.INI.";
    }
    if (!cfgClosing && IsWindow(w)) {
        EnableWindow(GetDlgItem(w, CFG_APPLY), cfgLoaded);
        updatePreview(w);
        if (message) TinyNotice(w, cfgInstance, "Saver", message);
        if (!cfgClosing && IsWindow(w)) SetFocus(GetDlgItem(w, IDCANCEL));
    }
    cfgApplying = 0;
}
static HWND makeControl(HWND w, char *cls, char *text, DWORD style,
                        int x, int y, int width, int height, int id)
{
    HWND child = CreateWindow(cls, text, WS_CHILD | WS_VISIBLE | WS_TABSTOP | style,
                              x, y, width, height, w, (HMENU)id, cfgInstance, NULL);
    if (child) SendMessage(child, WM_SETFONT,
                          (WPARAM)GetStockObject(SYSTEM_FIXED_FONT), 0L);
    return child;
}
BOOL FAR PASCAL SaverCfgProc(HWND w, UINT m, WPARAM wp, LPARAM lp)
{
    RECT r, c;
    PAINTSTRUCT ps;
    HDC dc;
    HFONT oldfont;
    HWND child;
    char command[128];
    int ww, hh, choice;
    if (m == WM_INITDIALOG) {
        cfgWindow = w;
        GetWindowRect(w, &r); GetClientRect(w, &c);
        ww = CFG_WIDTH + r.right - r.left - c.right;
        hh = (cfgCompact ? 88 : CFG_HEIGHT) + r.bottom - r.top - c.bottom;
        if (ww > GetSystemMetrics(SM_CXSCREEN) || hh > GetSystemMetrics(SM_CYSCREEN)) {
            EndDialog(w, IDCANCEL); return TRUE;
        }
        SetWindowPos(w, NULL, (GetSystemMetrics(SM_CXSCREEN) - ww) / 2,
                     (GetSystemMetrics(SM_CYSCREEN) - hh) / 2, ww, hh, SWP_NOZORDER);
        if (cfgCompact) {
            if (!makeControl(w, "COMBOBOX", "", CBS_DROPDOWNLIST | WS_VSCROLL | WS_GROUP,
                             6, 14, 116, 72, CFG_CHOICE) ||
                !makeControl(w, "EDIT", "", WS_BORDER | ES_AUTOHSCROLL | WS_GROUP,
                             38, 32, 84, 16, CFG_SECONDS) ||
                !makeControl(w, "BUTTON", "&Options", BS_PUSHBUTTON, 6, 50, 54, 16, CFG_OPTIONS) ||
                !makeControl(w, "BUTTON", "&Preview", BS_PUSHBUTTON, 68, 50, 54, 16, CFG_PREVIEW) ||
                !makeControl(w, "BUTTON", "&Apply", BS_PUSHBUTTON, 6, 70, 54, 16, CFG_APPLY) ||
                !makeControl(w, "BUTTON", "&Cancel", BS_DEFPUSHBUTTON, 68, 70, 54, 16, IDCANCEL)) {
                EndDialog(w, IDCANCEL); return TRUE;
            }
            SendDlgItemMessage(w, CFG_CHOICE, CB_ADDSTRING, 0, (LPARAM)(LPSTR)"Matrix");
            SendDlgItemMessage(w, CFG_CHOICE, CB_ADDSTRING, 0, (LPARAM)(LPSTR)"Maze");
            SendDlgItemMessage(w, CFG_CHOICE, CB_ADDSTRING, 0, (LPARAM)(LPSTR)"Starfield");
            SendDlgItemMessage(w, CFG_CHOICE, CB_ADDSTRING, 0, (LPARAM)(LPSTR)"Cube");
            SendDlgItemMessage(w, CFG_CHOICE, CB_ADDSTRING, 0, (LPARAM)(LPSTR)"None");
        } else if (!makeControl(w, "BUTTON", "&Matrix", BS_RADIOBUTTON | WS_GROUP,
                         6, 0, 116, 16, CFG_MATRIX) ||
            !makeControl(w, "BUTTON", "Ma&ze", BS_RADIOBUTTON,
                         6, 16, 116, 16, CFG_MAZE) ||
            !makeControl(w, "BUTTON", "&Starfield", BS_RADIOBUTTON,
                         6, 32, 116, 16, CFG_STARFIELD) ||
            !makeControl(w, "BUTTON", "&None", BS_RADIOBUTTON,
                         6, 48, 54, 16, CFG_NONE) ||
            !makeControl(w, "BUTTON", "&Cube", BS_RADIOBUTTON,
                         68, 48, 54, 16, CFG_CUBE) ||
            !makeControl(w, "EDIT", "", WS_BORDER | ES_AUTOHSCROLL | WS_GROUP,
                         6, 80, 116, 18, CFG_SECONDS) ||
            !makeControl(w, "BUTTON", "&Options...", BS_PUSHBUTTON,
                         6, 100, 116, 18, CFG_OPTIONS) ||
            !makeControl(w, "BUTTON", "&Preview", BS_PUSHBUTTON,
                         6, 120, 116, 20, CFG_PREVIEW) ||
            !makeControl(w, "BUTTON", "&Apply", BS_PUSHBUTTON,
                         6, 142, 54, 20, CFG_APPLY) ||
            !makeControl(w, "BUTTON", "&Cancel", BS_DEFPUSHBUTTON,
                         68, 142, 54, 20, IDCANCEL)) {
            EndDialog(w, IDCANCEL); return TRUE;
        }
        SendDlgItemMessage(w, CFG_SECONDS, EM_LIMITTEXT, 11, 0L);
        SendMessage(w, DM_SETDEFID, IDCANCEL, 0L);
        cfgLoaded = SaverConfigRead(&loaded) == SC_OK;
        if (cfgLoaded) {
            SetDlgItemText(w, CFG_SECONDS, ScValue(&loaded, SC_SECONDS));
            choice = ScEnabled(&loaded) ? ScChoice(&loaded) : SC_NONE;
            if (choice >= SC_NONE) choose(w,
                choice == SC_MATRIX ? CFG_MATRIX : choice == SC_MAZE ? CFG_MAZE :
                choice == SC_STARFIELD ? CFG_STARFIELD : choice == SC_CUBE ? CFG_CUBE : CFG_NONE);
            stagedSpeed = ScSpeed(ScValue(&loaded, SC_SPEED));
            stagedStars = ScStars(ScValue(&loaded, SC_STARS));
            if (!stagedSpeed) stagedSpeed = 2;
            if (!stagedStars) stagedStars = 32;
        } else TinyNotice(w, cfgInstance, "Saver", "Cannot read\nTSHELL.INI.");
        EnableWindow(GetDlgItem(w, CFG_APPLY), cfgLoaded); updatePreview(w);
        SetFocus(GetDlgItem(w, IDCANCEL)); return FALSE;
    }
    if (m == WM_PAINT) {
        dc = BeginPaint(w, &ps);
        oldfont = SelectObject(dc, GetStockObject(SYSTEM_FIXED_FONT));
        SetBkMode(dc, TRANSPARENT); SetTextColor(dc, GetSysColor(COLOR_WINDOWTEXT));
        if (cfgCompact) {
            TextOut(dc, 6, 0, "Screen saver", 12);
            TextOut(dc, 6, 34, "Sec:", 4);
        } else {
            TextOut(dc, 6, 64, "10-3600 sec:", 12);
        }
        SelectObject(dc, oldfont); EndPaint(w, &ps); return TRUE;
    }
    if (m == WM_COMMAND) {
        if (wp == CFG_CHOICE && HIWORD(lp) == CBN_SELCHANGE) { updatePreview(w); return TRUE; }
        if (wp == IDCANCEL) { cfgClosing = 1; EndDialog(w, IDCANCEL); return TRUE; }
        /* Win3 may send IDOK/zero LPARAM for Enter on the focused button. */
        if (wp == IDOK) {
            child = GetFocus();
            if (child == GetDlgItem(w, CFG_APPLY)) wp = CFG_APPLY;
            else if (child == GetDlgItem(w, CFG_PREVIEW)) wp = CFG_PREVIEW;
            else if (child == GetDlgItem(w, CFG_OPTIONS)) wp = CFG_OPTIONS;
            else return TRUE; /* Enter in the edit never writes or previews. */
        }
        if ((wp >= CFG_STARFIELD && wp <= CFG_NONE) || wp == CFG_CUBE) {
            if (HIWORD(lp) == BN_CLICKED && (HWND)LOWORD(lp) == GetDlgItem(w, wp)) {
                choose(w, wp); updatePreview(w);
            }
            return TRUE;
        }
        if (wp == CFG_APPLY || wp == CFG_PREVIEW || wp == CFG_OPTIONS) {
            child = GetDlgItem(w, wp);
            if ((!lp || ((HWND)LOWORD(lp) == child && HIWORD(lp) == BN_CLICKED)) &&
                GetFocus() == child && !cfgApplying && !cfgClosing) {
                if (wp == CFG_APPLY) applyConfig(w);
                else if (wp == CFG_OPTIONS) {
                    if (cfgLoaded && selection(w) == SC_STARFIELD &&
                        SaverStarOptions(w, cfgInstance, &stagedSpeed, &stagedStars)) optionsDirty = 1;
                    if (cfgLoaded && selection(w) == SC_CUBE &&
                        SaverConfigProgram(w, cfgInstance, &loaded, SC_CUBE, command)) {
                        command[lstrlen(command)-1] = 'C';
                        PmLaunchShow(w, command, SW_SHOWNORMAL);
                    }
                }
                else if (!cfgPreviewPending && cfgLoaded) {
                    cfgPreviewPending = 1; PostMessage(w, CFG_STARTPREVIEW, 0, 0L);
                }
            }
            return TRUE;
        }
    }
    if (m == CFG_STARTPREVIEW) {
        if (!cfgPreviewPending) return TRUE;
        if (!cfgApplying && cfgLoaded && !cfgClosing && GetActiveWindow() == w &&
            GetFocus() == GetDlgItem(w, CFG_PREVIEW) && inputHeld()) {
            if (!SetTimer(w, CFG_RELEASE_TIMER, 50, NULL)) cfgPreviewPending = 0;
            return TRUE;
        }
        KillTimer(w, CFG_RELEASE_TIMER);
        cfgPreviewPending = 0;
        if (!cfgApplying && cfgLoaded && !cfgClosing && GetActiveWindow() == w &&
            GetFocus() == GetDlgItem(w, CFG_PREVIEW) &&
            SaverConfigProgram(w, cfgInstance, &loaded, selection(w), command)) {
            if (selection(w) == SC_STARFIELD &&
                !ScCommand(ScProgram(&loaded, SC_STARFIELD), stagedSpeed, stagedStars, command, sizeof(command)))
                TinyNotice(w, cfgInstance, "Saver", "Preview path\ntoo long. See\nStarProgram.");
            else TSSaverPreview(w, cfgInstance, command);
        }
        return TRUE;
    }
    if (m == WM_TIMER && wp == CFG_RELEASE_TIMER) {
        PostMessage(w, CFG_STARTPREVIEW, 0, 0L); return TRUE;
    }
    if (m == WM_TIMER && wp == SAVER_PREVIEW_TIMER) {
        TSSaverPreviewTick(w); return TRUE;
    }
    if (m == WM_CLOSE || (m == WM_ENDSESSION && wp)) {
        cfgClosing = 1; EndDialog(w, IDCANCEL); return TRUE;
    }
    if (m == WM_DESTROY) {
        KillTimer(w, CFG_RELEASE_TIMER); TSSaverPreviewEnd(w); cfgWindow = NULL;
    }
    return FALSE;
}
static void cfgWord(BYTE FAR **p, unsigned value)
{ *(*p)++ = (BYTE)value; *(*p)++ = (BYTE)(value >> 8); }
void TSSaverSettings(HWND owner, HINSTANCE instance)
{
    HGLOBAL memory;
    BYTE FAR *p;
    FARPROC proc;
    DWORD style, units;
    char *title = "Screen saver";
    int result = -1;
    if (cfgBusy) { if (cfgWindow) SetActiveWindow(cfgWindow); return; }
    cfgBusy = 1; cfgApplying = cfgLoaded = cfgClosing = cfgPreviewPending = 0;
    optionsDirty = 0; stagedSpeed = 2; stagedStars = 32;
    cfgInstance = instance;
    cfgCompact = GetSystemMetrics(SM_CYSCREEN) < 180;
    /* Also safe for callers that omit the customary outer shell hold. */
    TSSaverHold(1);
    memory = GlobalAlloc(GMEM_MOVEABLE | GMEM_ZEROINIT, 64);
    if (memory) {
        p = (BYTE FAR *)GlobalLock(memory);
        if (p) {
            style = cfgCompact ? WS_POPUP | WS_BORDER : WS_POPUP | WS_CAPTION | WS_SYSMENU | DS_MODALFRAME;
            cfgWord(&p, LOWORD(style)); cfgWord(&p, HIWORD(style)); *p++ = 0;
            units = GetDialogBaseUnits(); cfgWord(&p, 0); cfgWord(&p, 0);
            cfgWord(&p, CFG_WIDTH * 4 / LOWORD(units));
            cfgWord(&p, (cfgCompact ? 88 : CFG_HEIGHT) * 8 / HIWORD(units));
            *p++ = 0; *p++ = 0;
            while (*title) *p++ = *title++;
            *p = 0; GlobalUnlock(memory);
            proc = MakeProcInstance((FARPROC)SaverCfgProc, instance);
            if (proc) {
                result = DialogBoxIndirect(instance, memory, owner, (DLGPROC)proc);
                FreeProcInstance(proc);
            }
        }
        GlobalFree(memory);
    }
    cfgWindow = NULL; cfgBusy = cfgApplying = cfgLoaded = cfgPreviewPending = 0;
    TSSaverHold(0);
    if (result == -1) TinyNotice(owner, instance, "Saver", "Cannot open\nsaver settings.");
}
