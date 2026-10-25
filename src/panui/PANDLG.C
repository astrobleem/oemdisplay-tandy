/* PANDLG.C - the "Panning settings" window shared by XTPAN and XYCTL.
 *
 * A passive popup built in code from STATIC, BUTTON and EDIT children: no
 * resource, no timer, no hook, no modal loop. Which rows exist depends only
 * on the capability mask in model.caps; the backend is never named here.
 * A repeat open never overwrites typed edits: it refreshes the caps, moves
 * the window and takes the focus. Windows 3.0 real mode, small model, C89.
 */
#include <windows.h>
#include "PANDLG.H"

#define DLG_CLASS   "PanSetDlg"
#define DLG_TITLE   "Panning settings"
#define DLG_W       300
#define DLG_MAXH    176

#define ID_BACKEND  200
#define ID_VIEW     201
#define ID_STEP     210
#define ID_EDGE     211
#define ID_DWELL    212
#define ID_FOLLOW   213
#define ID_EDGEON   220
#define ID_REP100   221
#define ID_REP200   222
#define ID_REP500   223
#define ID_FOLLOWD  224
#define ID_SOFT     225
#define ID_HARD     226
#define ID_STATUS   230
#define ID_HOME     240

/* Client layout in pixels: two text lines, one row per capability, then the
 * status line and the buttons at the bottom. The row pitch is 14 when there
 * is room and shrinks (down to 11) if additional rows must fit 176 px. */
#define PAN_X       7
#define PAN_W       280
#define TXT_H       12
#define STATUS_H    24      /* two lines for validation and driver messages */
#define LAY_ROW     30      /* top of the first capability row */
#define LAY_FOOT    44      /* client bottom to top of the status line */
#define LAY_BTN     16      /* client bottom to top of the buttons */
#define BTN_H       14
#define ROW_MAX     14
#define ROW_MIN     11

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

/* Bounded copy into model.status (80 bytes including the NUL). */
static void SetStatusText(const char *text)
{
    int i = 0;
    while (text[i] && i < (int)sizeof(model.status) - 1) {
        model.status[i] = text[i];
        i++;
    }
    model.status[i] = '\0';
}

/* One row per capability bit; PS_CAP_STEP..PS_CAP_MODE are bits 1..0x80. */
static int CountRows(unsigned caps)
{
    unsigned bit;
    int n = 0;
    for (bit = PS_CAP_STEP; bit <= PS_CAP_MODE; bit <<= 1)
        if (caps & bit)
            n++;
    return n;
}

static int ClientMax(void)
{
    return DLG_MAXH - GetSystemMetrics(SM_CYCAPTION)
           - 2 * GetSystemMetrics(SM_CYDLGFRAME);
}

/* Row pitch for n rows: 14 px if it fits, else the largest pitch that does,
 * but never below ROW_MIN (the window then clips at the client limit). */
static int RowStep(int n)
{
    int avail = ClientMax() - LAY_ROW - LAY_FOOT - 2;
    int step = ROW_MAX;
    if (n > 0 && n * step > avail)
        step = avail / n;
    if (step < ROW_MIN)
        step = ROW_MIN;
    return step;
}

static int ClientH(int n, int step)
{
    int h = LAY_ROW + n * step + LAY_FOOT + 2;
    if (h > ClientMax())
        h = ClientMax();
    return h;
}

static int WinHeight(int n, int step)
{
    return ClientH(n, step) + GetSystemMetrics(SM_CYCAPTION)
           + 2 * GetSystemMetrics(SM_CYDLGFRAME);
}

static HWND MakeChild(HWND parent, const char *cls, const char *text,
                      DWORD style, int x, int y, int w, int h, int id)
{
    return CreateWindow((LPSTR)cls, (LPSTR)text,
                        WS_CHILD | WS_VISIBLE | style, x, y, w, h,
                        parent, (HMENU)id, hInst, NULL);
}

static void EditItem(HWND hwnd, int id, int y, int h)
{
    HWND e = MakeChild(hwnd, "EDIT", "", WS_BORDER | ES_AUTOHSCROLL |
                       WS_TABSTOP, 190, y, 44, h, id);
    SendMessage(e, EM_LIMITTEXT, 5, 0L);
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
    wsprintf(buf, "View %dx%d of %dx%d at %d,%d", c->viewW, c->viewH,
             c->workW, c->workH, c->viewX, c->viewY);
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

/* Shows model.work in the controls that exist. */
static void FillControls(HWND hwnd)
{
    unsigned caps = model.caps.caps;
    const PANSET *w = &model.work;

    SetViewLine(hwnd);
    ShowStatus(hwnd);
    if (caps & PS_CAP_STEP)
        SetIntItem(hwnd, ID_STEP, w->step);
    if (caps & PS_CAP_EDGE)
        SetIntItem(hwnd, ID_EDGE, w->edge);
    if (caps & PS_CAP_DWELL)
        SetIntItem(hwnd, ID_DWELL, w->dwell);
    if (caps & PS_CAP_FOLLOW)
        CheckDlgButton(hwnd, ID_FOLLOW, w->follow != 0);
    if (caps & PS_CAP_EDGEON)
        CheckDlgButton(hwnd, ID_EDGEON, w->edgeOn != 0);
    if (caps & PS_CAP_REPEAT)
        CheckRadioButton(hwnd, ID_REP100, ID_REP500,
                         w->repeat == 500 ? ID_REP500 :
                         w->repeat == 200 ? ID_REP200 : ID_REP100);
    if (caps & PS_CAP_FOLLOWD)
        CheckDlgButton(hwnd, ID_FOLLOWD, w->followDlg != 0);
    if (caps & PS_CAP_MODE)
        CheckRadioButton(hwnd, ID_SOFT, ID_HARD,
                         w->mode == PS_MODE_HARD ? ID_HARD : ID_SOFT);
}

/* Reads only the controls that were created. PS_E_TEXT leaves the rest of
 * model.work changed but the caller does not apply it. */
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
    if (caps & PS_CAP_EDGE) {
        if (ReadIntItem(hwnd, ID_EDGE, &v) != PS_OK)
            return PS_E_TEXT;
        w->edge = v;
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
    if (caps & PS_CAP_REPEAT) {
        if (IsDlgButtonChecked(hwnd, ID_REP500))
            w->repeat = 500;
        else if (IsDlgButtonChecked(hwnd, ID_REP200))
            w->repeat = 200;
        else
            w->repeat = 100;
    }
    if (caps & PS_CAP_FOLLOWD)
        w->followDlg = IsDlgButtonChecked(hwnd, ID_FOLLOWD) ? 1 : 0;
    if (caps & PS_CAP_MODE)
        w->mode = IsDlgButtonChecked(hwnd, ID_HARD) ? PS_MODE_HARD
                                                    : PS_MODE_SOFT;
    return PS_OK;
}

/* Creates the children for model.caps. Called from WM_CREATE, so every
 * control exists before FillControls touches it. */
static void BuildControls(HWND hwnd)
{
    unsigned caps = model.caps.caps;
    int n = CountRows(caps);
    int step = RowStep(n);
    int h = ClientH(n, step);
    int y = LAY_ROW;
    const char *bk = pHost->backend ? pHost->backend : "";

    MakeChild(hwnd, "STATIC", bk, SS_LEFT, PAN_X, 3, PAN_W, TXT_H, ID_BACKEND);
    MakeChild(hwnd, "STATIC", "", SS_LEFT, PAN_X, 16, PAN_W, TXT_H, ID_VIEW);

    if (caps & PS_CAP_STEP) {
        MakeChild(hwnd, "STATIC", "Step (rows)", SS_LEFT, PAN_X, y, 180,
                  step, 0);
        EditItem(hwnd, ID_STEP, y, step);
        y += step;
    }
    if (caps & PS_CAP_EDGE) {
        MakeChild(hwnd, "STATIC", "Edge band width (rows)", SS_LEFT, PAN_X,
                  y, 180, step, 0);
        EditItem(hwnd, ID_EDGE, y, step);
        y += step;
    }
    if (caps & PS_CAP_DWELL) {
        MakeChild(hwnd, "STATIC", "Dwell before pan (ms)", SS_LEFT, PAN_X,
                  y, 180, step, 0);
        EditItem(hwnd, ID_DWELL, y, step);
        y += step;
    }
    if (caps & PS_CAP_FOLLOW) {
        MakeChild(hwnd, "BUTTON", "Follow any newly activated window",
                  BS_AUTOCHECKBOX | WS_TABSTOP, PAN_X, y, PAN_W, step,
                  ID_FOLLOW);
        y += step;
    }
    if (caps & PS_CAP_EDGEON) {
        MakeChild(hwnd, "BUTTON", "Pan at screen edge",
                  BS_AUTOCHECKBOX | WS_TABSTOP, PAN_X, y, PAN_W, step,
                  ID_EDGEON);
        y += step;
    }
    if (caps & PS_CAP_REPEAT) {
        /* one group: WS_GROUP and WS_TABSTOP on the first radio only */
        MakeChild(hwnd, "BUTTON", "Repeat 100 ms",
                  BS_AUTORADIOBUTTON | WS_GROUP | WS_TABSTOP, PAN_X, y, 120,
                  step, ID_REP100);
        MakeChild(hwnd, "BUTTON", "200 ms", BS_AUTORADIOBUTTON, 130, y, 70,
                  step, ID_REP200);
        MakeChild(hwnd, "BUTTON", "500 ms", BS_AUTORADIOBUTTON, 204, y, 70,
                  step, ID_REP500);
        y += step;
    }
    if (caps & PS_CAP_FOLLOWD) {
        MakeChild(hwnd, "BUTTON", "Follow dialog boxes only",
                  BS_AUTOCHECKBOX | WS_TABSTOP, PAN_X, y, PAN_W, step,
                  ID_FOLLOWD);
        y += step;
    }
    if (caps & PS_CAP_MODE) {
        MakeChild(hwnd, "BUTTON", "Software",
                  BS_AUTORADIOBUTTON | WS_GROUP | WS_TABSTOP, PAN_X, y, 90,
                  step, ID_SOFT);
        MakeChild(hwnd, "BUTTON", "Hardware", BS_AUTORADIOBUTTON, 100, y, 90,
                  step, ID_HARD);
        y += step;
    }

    MakeChild(hwnd, "STATIC", "", SS_LEFT, PAN_X, h - LAY_FOOT, PAN_W,
              STATUS_H, ID_STATUS);
    if (caps & PS_CAP_HOME)
        MakeChild(hwnd, "BUTTON", "Home", BS_PUSHBUTTON | WS_TABSTOP, PAN_X,
                  h - LAY_BTN, 60, BTN_H, ID_HOME);
    MakeChild(hwnd, "BUTTON", "Apply", BS_DEFPUSHBUTTON | WS_TABSTOP, 160,
              h - LAY_BTN, 60, BTN_H, IDOK);
    MakeChild(hwnd, "BUTTON", "Cancel", BS_PUSHBUTTON | WS_TABSTOP, 226,
              h - LAY_BTN, 60, BTN_H, IDCANCEL);

    FillControls(hwnd);
    UpdateButtons(hwnd);
}

/* Moves the window to the viewport origin; the size is never changed. */
static void Reposition(HWND hwnd)
{
    SetWindowPos(hwnd, NULL, model.caps.viewX + 4, model.caps.viewY + 2,
                 0, 0, SWP_NOSIZE | SWP_NOZORDER | SWP_NOACTIVATE);
}

/* Repeat open: query the driver but keep the typed edits. The controls were
 * built for the old caps, so a changed capability set only disables the
 * buttons and asks the user to reopen. */
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
        SetStatusText(ok ? "Driver changed: reopen this window"
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
    /* model.work is the actual result, so a refused mode shows here */
    FillControls(hwnd);
    UpdateButtons(hwnd);
    /* Apply never pans: the origin in model.caps may be stale, so the
     * window stays where the user sees it. Only open and Home move it. */
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

/* The first control that was created, so focus lands on a real edit or
 * checkbox rather than on the window itself. */
static HWND FirstTabStop(HWND hwnd)
{
    int ids[9];
    int i;
    HWND h;

    ids[0] = ID_STEP;
    ids[1] = ID_EDGE;
    ids[2] = ID_DWELL;
    ids[3] = ID_FOLLOW;
    ids[4] = ID_EDGEON;
    ids[5] = ID_REP100;
    ids[6] = ID_FOLLOWD;
    ids[7] = ID_SOFT;
    ids[8] = ID_HOME;
    for (i = 0; i < 9; i++) {
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
    int n, step, h;

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
    n = CountRows(model.caps.caps);
    step = RowStep(n);
    h = WinHeight(n, step);
    hDlg = CreateWindow((LPSTR)DLG_CLASS, (LPSTR)title,
                        WS_POPUP | WS_CAPTION | WS_SYSMENU,
                        model.caps.viewX + 4, model.caps.viewY + 2,
                        DLG_W, h, NULL, NULL, inst, NULL);
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
        /* IsDialogMessage asks for the default button; without this answer
         * Enter would not reach Apply. */
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
