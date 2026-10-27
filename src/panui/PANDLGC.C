/* PANDLGC.C - the shared "Panning settings" window, laid out for a viewport
 * of 160x100 or less (CGAPAN).
 *
 * Same window, class, model and PANDLG.H interface as PANDLG.C: only the
 * layout differs, because PANDLG.C is sized in fixed 300x176 pixels. An owner
 * links exactly one of the two. PANDLG.C and PANSET.C stay byte-identical,
 * so the qualified XTPAN and XYCTL builds are unaffected.
 *
 * Rows come from the capability mask: Step, Dwell, Follow and Edge panning
 * plus Home, which is all CGAPAN supports. Like PANDLG.C it owns no timer,
 * no hook and no modal loop. Windows 3.0 real mode, small model, C89.
 */
#include <windows.h>
#include "PANDLG.H"

#define DLG_CLASS   "PanSetDlg"
#define DLG_TITLE   "Panning"
#define DLG_W       152
#define DLG_MAXH    96

#define ID_VIEW     201
#define ID_STEP     210
#define ID_DWELL    212
#define ID_FOLLOW   213
#define ID_EDGEON   220
#define ID_STATUS   230
#define ID_HOME     240

/* Client layout in pixels for the 3x5 fonts and six-row controls. */
#define PAN_X       4
#define PAN_W       142
#define TXT_H       7
#define ROW_H       9
#define LAY_ROW     9       /* top of the first row */
#define LAY_LABEL   86      /* width of a row label */
#define LAY_EDIT_X  92
#define LAY_EDIT_W  30
#define STATUS_H    13      /* two short lines */
#define BTN_H       10

#ifndef DM_GETDEFID
#define DM_GETDEFID (WM_USER + 0)
#endif
#ifndef DC_HASDEFID
#define DC_HASDEFID 0x534B
#endif
#ifndef EM_LIMITTEXT
#define EM_LIMITTEXT (WM_USER + 21)
#endif

static HWND hDlg;
static const PANHOST *pHost;
static PANMODEL model;
static HINSTANCE hInst;
static int bClassDone;

static void SetStatusText(const char *text)
{
    int i = 0;
    while (text[i] && i < (int)sizeof(model.status) - 1) {
        model.status[i] = text[i];
        i++;
    }
    model.status[i] = '\0';
}

static int CountRows(unsigned caps)
{
    int n = 0;
    if (caps & PS_CAP_STEP)
        n++;
    if (caps & PS_CAP_DWELL)
        n++;
    if (caps & PS_CAP_FOLLOW)
        n++;
    if (caps & PS_CAP_EDGEON)
        n++;
    return n;
}

static int ClientH(int n)
{
    return LAY_ROW + n * ROW_H + 2 + STATUS_H + 2 + BTN_H + 2;
}

static int WinHeight(int n)
{
    int h = ClientH(n) + GetSystemMetrics(SM_CYCAPTION)
            + 2 * GetSystemMetrics(SM_CYDLGFRAME);
    return h > DLG_MAXH ? DLG_MAXH : h;
}

static HWND MakeChild(HWND parent, const char *cls, const char *text,
                      DWORD style, int x, int y, int w, int h, int id)
{
    return CreateWindow((LPSTR)cls, (LPSTR)text,
                        WS_CHILD | WS_VISIBLE | style, x, y, w, h,
                        parent, (HMENU)id, hInst, NULL);
}

static void SetIntItem(HWND hwnd, int id, int v)
{
    char buf[12];
    wsprintf(buf, "%d", v);
    SetDlgItemText(hwnd, id, (LPSTR)buf);
}

static int ReadIntItem(HWND hwnd, int id, int *v)
{
    char buf[12];
    GetDlgItemText(hwnd, id, (LPSTR)buf, sizeof(buf));
    return PanParseInt(buf, v);
}

static void ShowStatus(HWND hwnd)
{
    SetDlgItemText(hwnd, ID_STATUS, (LPSTR)model.status);
}

static void SetViewLine(HWND hwnd)
{
    const PANCAPS *c = &model.caps;
    char buf[48];
    wsprintf(buf, "View %d,%d of %dx%d", c->viewX, c->viewY, c->workW,
             c->workH);
    SetDlgItemText(hwnd, ID_VIEW, (LPSTR)buf);
}

/* With the driver lost, Apply and Home stay disabled; Cancel always works. */
static void UpdateButtons(HWND hwnd)
{
    int live = model.caps.backend != PS_BACK_NONE;
    EnableWindow(GetDlgItem(hwnd, IDOK), live);
    if (GetDlgItem(hwnd, ID_HOME))
        EnableWindow(GetDlgItem(hwnd, ID_HOME), live);
}

static void FillControls(HWND hwnd)
{
    unsigned caps = model.caps.caps;
    const PANSET *w = &model.work;

    SetViewLine(hwnd);
    ShowStatus(hwnd);
    if (caps & PS_CAP_STEP)
        SetIntItem(hwnd, ID_STEP, w->step);
    if (caps & PS_CAP_DWELL)
        SetIntItem(hwnd, ID_DWELL, w->dwell);
    if (caps & PS_CAP_FOLLOW)
        CheckDlgButton(hwnd, ID_FOLLOW, w->follow != 0);
    if (caps & PS_CAP_EDGEON)
        CheckDlgButton(hwnd, ID_EDGEON, w->edgeOn != 0);
}

/* PS_E_TEXT leaves the rest of model.work changed; the caller then does
 * not apply it. */
static int ReadControls(HWND hwnd)
{
    unsigned caps = model.caps.caps;
    PANSET *w = &model.work;
    int v;

    if (caps & PS_CAP_STEP) {
        if (ReadIntItem(hwnd, ID_STEP, &v) != PS_OK)
            return PS_E_TEXT;
        w->step = v;
    }
    if (caps & PS_CAP_DWELL) {
        if (ReadIntItem(hwnd, ID_DWELL, &v) != PS_OK)
            return PS_E_TEXT;
        w->dwell = v;
    }
    if (caps & PS_CAP_FOLLOW)
        w->follow = IsDlgButtonChecked(hwnd, ID_FOLLOW) ? 1 : 0;
    if (caps & PS_CAP_EDGEON)
        w->edgeOn = IsDlgButtonChecked(hwnd, ID_EDGEON) ? 1 : 0;
    return PS_OK;
}

static void EditRow(HWND hwnd, const char *label, int id, int y)
{
    HWND e;
    MakeChild(hwnd, "STATIC", label, SS_LEFT, PAN_X, y + 1, LAY_LABEL,
              TXT_H, 0);
    e = MakeChild(hwnd, "EDIT", "", WS_BORDER | ES_AUTOHSCROLL | WS_TABSTOP,
                  LAY_EDIT_X, y, LAY_EDIT_W, ROW_H - 1, id);
    SendMessage(e, EM_LIMITTEXT, 5, 0L);
}

static void BuildControls(HWND hwnd)
{
    unsigned caps = model.caps.caps;
    int n = CountRows(caps);
    int h = ClientH(n);
    int y = LAY_ROW;

    MakeChild(hwnd, "STATIC", "", SS_LEFT, PAN_X, 1, PAN_W, TXT_H, ID_VIEW);
    if (caps & PS_CAP_STEP) {
        EditRow(hwnd, "Step (pixels)", ID_STEP, y);
        y += ROW_H;
    }
    if (caps & PS_CAP_DWELL) {
        EditRow(hwnd, "Dwell before pan (ms)", ID_DWELL, y);
        y += ROW_H;
    }
    if (caps & PS_CAP_FOLLOW) {
        MakeChild(hwnd, "BUTTON", "Follow active window",
                  BS_AUTOCHECKBOX | WS_TABSTOP, PAN_X, y, PAN_W, ROW_H - 1,
                  ID_FOLLOW);
        y += ROW_H;
    }
    if (caps & PS_CAP_EDGEON) {
        MakeChild(hwnd, "BUTTON", "Pan at screen edge",
                  BS_AUTOCHECKBOX | WS_TABSTOP, PAN_X, y, PAN_W, ROW_H - 1,
                  ID_EDGEON);
        y += ROW_H;
    }
    MakeChild(hwnd, "STATIC", "", SS_LEFT, PAN_X, h - BTN_H - 4 - STATUS_H,
              PAN_W, STATUS_H, ID_STATUS);
    if (caps & PS_CAP_HOME)
        MakeChild(hwnd, "BUTTON", "Home", BS_PUSHBUTTON | WS_TABSTOP, PAN_X,
                  h - BTN_H - 2, 34, BTN_H, ID_HOME);
    MakeChild(hwnd, "BUTTON", "Apply", BS_DEFPUSHBUTTON | WS_TABSTOP, 62,
              h - BTN_H - 2, 40, BTN_H, IDOK);
    MakeChild(hwnd, "BUTTON", "Cancel", BS_PUSHBUTTON | WS_TABSTOP, 106,
              h - BTN_H - 2, 40, BTN_H, IDCANCEL);

    FillControls(hwnd);
    UpdateButtons(hwnd);
}

/* Moves the window to the viewport origin; the size is never changed. */
static void Reposition(HWND hwnd)
{
    SetWindowPos(hwnd, NULL, model.caps.viewX + 3, model.caps.viewY + 1,
                 0, 0, SWP_NOSIZE | SWP_NOZORDER | SWP_NOACTIVATE);
}

/* Repeat open: query the driver but keep the typed edits. */
static void RefreshCaps(void)
{
    PANCAPS fresh;
    PANSET live;
    int ok;

    fresh.backend = PS_BACK_NONE;
    fresh.caps = 0;
    ok = pHost->ops.query(pHost->ops.ctx, &fresh, &live);
    if (!ok || fresh.backend != model.caps.backend ||
        fresh.caps != model.caps.caps) {
        model.caps.backend = PS_BACK_NONE;
        SetStatusText(ok ? "Driver changed: reopen"
                         : PanSetErrorText(PS_E_LOST));
        return;
    }
    model.caps = fresh;
    model.live = live;
}

void PanDlgTrack(void)
{
    int x, y, backend;
    RECT r;
    if (!hDlg || !IsWindow(hDlg))
        return;
    x = model.caps.viewX;
    y = model.caps.viewY;
    backend = model.caps.backend;
    RefreshCaps();
    if (backend != model.caps.backend) {
        ShowStatus(hDlg);
        UpdateButtons(hDlg);
    }
    if (x != model.caps.viewX || y != model.caps.viewY) {
        SetViewLine(hDlg);
        GetWindowRect(hDlg, &r);
        if (r.left < model.caps.viewX || r.top < model.caps.viewY ||
            r.right > model.caps.viewX + model.caps.viewW ||
            r.bottom > model.caps.viewY + model.caps.viewH)
            Reposition(hDlg);
    }
}

static void DoApply(HWND hwnd)
{
    int rc;
    if (model.caps.backend == PS_BACK_NONE)
        return;
    rc = ReadControls(hwnd);
    if (rc != PS_OK) {
        SetStatusText(PanSetErrorText(rc));
        ShowStatus(hwnd);
        return;
    }
    PanModelApply(&model, &pHost->ops, &pHost->store);
    /* model.work is the engine's actual result, so a rounded step shows. */
    FillControls(hwnd);
    UpdateButtons(hwnd);
}

static void DoCancel(HWND hwnd)
{
    PanModelCancel(&model);
    DestroyWindow(hwnd);
}

/* Home changes only the viewport: typed edits are left as they are. */
static void DoHome(HWND hwnd)
{
    if (model.caps.backend == PS_BACK_NONE ||
        !(model.caps.caps & PS_CAP_HOME))
        return;
    PanModelHome(&model, &pHost->ops);
    ShowStatus(hwnd);
    SetViewLine(hwnd);
    UpdateButtons(hwnd);
    Reposition(hwnd);
}

static HWND FirstTabStop(HWND hwnd)
{
    int ids[5];
    int i;
    HWND h;

    ids[0] = ID_STEP;
    ids[1] = ID_DWELL;
    ids[2] = ID_FOLLOW;
    ids[3] = ID_EDGEON;
    ids[4] = ID_HOME;
    for (i = 0; i < 5; i++) {
        h = GetDlgItem(hwnd, ids[i]);
        if (h)
            return h;
    }
    return GetDlgItem(hwnd, IDOK);
}

static int RegisterPanClass(HINSTANCE inst)
{
    WNDCLASS wc;

    wc.style = 0;
    wc.lpfnWndProc = (WNDPROC)PanDlgProc;   /* class proc: no thunk */
    wc.cbClsExtra = 0;
    wc.cbWndExtra = 0;
    wc.hInstance = inst;
    wc.hIcon = NULL;
    wc.hCursor = LoadCursor(NULL, IDC_ARROW);
    wc.hbrBackground = (HBRUSH)(COLOR_WINDOW + 1);
    wc.lpszMenuName = NULL;
    wc.lpszClassName = (LPSTR)DLG_CLASS;
    if (!RegisterClass(&wc))
        return 0;
    bClassDone = 1;
    return 1;
}

HWND PanDlgOpen(HINSTANCE inst, const PANHOST *host)
{
    const char *title = host->title ? host->title : DLG_TITLE;

    if (hDlg && IsWindow(hDlg)) {
        pHost = host;
        if (IsIconic(hDlg))
            ShowWindow(hDlg, SW_RESTORE);
        RefreshCaps();
        SetViewLine(hDlg);
        UpdateButtons(hDlg);
        Reposition(hDlg);
        BringWindowToTop(hDlg);
        SetFocus(hDlg);
        return hDlg;
    }
    if (!bClassDone && !RegisterPanClass(inst))
        return NULL;

    hInst = inst;
    pHost = host;
    PanModelOpen(&model, &host->ops);
    hDlg = CreateWindow((LPSTR)DLG_CLASS, (LPSTR)title,
                        WS_POPUP | WS_CAPTION | WS_SYSMENU,
                        model.caps.viewX + 3, model.caps.viewY + 1,
                        DLG_W, WinHeight(CountRows(model.caps.caps)),
                        NULL, NULL, inst, NULL);
    if (!hDlg)
        return NULL;
    ShowWindow(hDlg, SW_SHOWNORMAL);
    SetFocus(hDlg);
    return hDlg;
}

int PanDlgMessage(MSG FAR *msg)
{
    return hDlg && IsWindow(hDlg) && IsDialogMessage(hDlg, msg);
}

void PanDlgClose(void)
{
    if (hDlg && IsWindow(hDlg))
        DestroyWindow(hDlg);
    hDlg = NULL;
}

long FAR PASCAL PAN_EXPORT PanDlgProc(HWND hwnd, UINT msg, WPARAM wParam,
                                      LPARAM lParam)
{
    switch (msg) {
    case WM_CREATE:
        BuildControls(hwnd);
        return 0L;
    case WM_SETFOCUS:
        if (FirstTabStop(hwnd))
            SetFocus(FirstTabStop(hwnd));
        return 0L;
    case DM_GETDEFID:
        return MAKELONG(IDOK, DC_HASDEFID);
    case WM_NEXTDLGCTL: {
        HWND next;
        next = lParam ? (HWND)wParam :
               GetNextDlgTabItem(hwnd, GetFocus(), wParam != 0);
        if (next) {
            SetFocus(next);
            if (SendMessage(next, WM_GETDLGCODE, 0, 0L) & DLGC_HASSETSEL)
                SendMessage(next, EM_SETSEL, 0, MAKELONG(0, -1));
        }
        return 0L;
    }
    case WM_COMMAND:
        if (wParam == IDOK)
            DoApply(hwnd);
        else if (wParam == IDCANCEL)
            DoCancel(hwnd);
        else if (wParam == ID_HOME)
            DoHome(hwnd);
        return 0L;
    case WM_CLOSE:
        DoCancel(hwnd);
        return 0L;
    case WM_DESTROY:
        hDlg = NULL;
        break;
    }
    return DefWindowProc(hwnd, msg, wParam, lParam);
}
