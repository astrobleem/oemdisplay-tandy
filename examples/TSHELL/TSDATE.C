/* Compact explicit date/time editor: Windows 3.0 / 8086, 160x200 safe. */
#define WINVER 0x0300
#include <windows.h>
#include <dos.h>
#include "TNOTICE.H"
#include "TSDATE.H"
#include "DTCORE.H"

#define DATE_WIDTH 128
#define DATE_HEIGHT 164
#define DATE_EDIT 110
#define TIME_EDIT 111
#define DATE_RELOAD 112
#define DATE_APPLY 113
#define FIELD_MAX 31

static HINSTANCE dateInstance;
static HWND dateWindow;
static int dateBusy, dateApplying, dateLoaded, dateClosing;
static char loadedDate[11], loadedTime[9];

static int readClock(void *context, DTVALUE *v)
{
    struct dosdate_t before, after;
    struct dostime_t time;
    int tries;
    /* A midnight rollover must never pair yesterday's date with today's time. */
    for (tries = 0; tries < 4; ++tries) {
        _dos_getdate(&before); _dos_gettime(&time); _dos_getdate(&after);
        if (before.year == after.year && before.month == after.month &&
            before.day == after.day) {
            v->year = after.year; v->month = after.month; v->day = after.day;
            v->hour = time.hour; v->minute = time.minute; v->second = time.second;
            return DtValid(v);
        }
    }
    return 0;
}

static int setDate(void *context, const DTVALUE *v)
{
    struct dosdate_t date;
    date.year = v->year; date.month = (unsigned char)v->month;
    date.day = (unsigned char)v->day; date.dayofweek = 0;
    return _dos_setdate(&date) == 0;
}

static int setTime(void *context, const DTVALUE *v)
{
    struct dostime_t time;
    time.hour = (unsigned char)v->hour; time.minute = (unsigned char)v->minute;
    time.second = (unsigned char)v->second; time.hsecond = 0;
    return _dos_settime(&time) == 0;
}

static void loadFields(HWND w, const DTVALUE *value)
{
    DtFormat(value, loadedDate, loadedTime);
    SetDlgItemText(w, DATE_EDIT, loadedDate);
    SetDlgItemText(w, TIME_EDIT, loadedTime);
    dateLoaded = 1;
    EnableWindow(GetDlgItem(w, DATE_APPLY), TRUE);
}

static void reloadClock(HWND w)
{
    DTVALUE value;
    if (readClock(NULL, &value)) loadFields(w, &value);
    else {
        dateLoaded = 0;
        EnableWindow(GetDlgItem(w, DATE_APPLY), FALSE);
        TinyNotice(w, dateInstance, "Date/time", "Cannot read\nDOS clock.\nNothing set.");
    }
}

static void applyClock(HWND w)
{
    DTIO io;
    DTRESULT result;
    char date[FIELD_MAX + 1], time[FIELD_MAX + 1];
    char *message;
    int focus = IDCANCEL;
    if (dateApplying || !dateLoaded || dateClosing) return;
    dateApplying = 1;
    GetDlgItemText(w, DATE_EDIT, date, sizeof(date));
    GetDlgItemText(w, TIME_EDIT, time, sizeof(time));
    io.read = readClock; io.setdate = setDate; io.settime = setTime; io.context = NULL;
    DtApply(date, time, loadedDate, loadedTime, &io, &result);
    if (result.written) {
        /* Successful setters may have changed the clock even on partial failure. */
        SendMessage((HWND)0xFFFF, WM_TIMECHANGE, 0, 0L);
        if (dateClosing || !IsWindow(w)) { dateApplying = 0; return; }
    }
    if (result.code == DT_OK) {
        loadFields(w, &result.actual);
        message = "Clock changed.\nReadback OK.";
    } else if (result.code == DT_NOCHANGE) message = "No changes.\nClock not set.";
    else if (result.code == DT_BADDATE) {
        message = "Invalid date.\nYYYY-MM-DD\n1980 to 2099.\nCheck day.";
        focus = DATE_EDIT;
    } else if (result.code == DT_BADTIME) {
        message = "Invalid time.\nHH:MM:SS\n00-23 hours;\n00-59 min/sec.";
        focus = TIME_EDIT;
    } else if (result.code == DT_READFAIL) message = "Cannot read\nDOS clock.\nNothing set.";
    else if (result.code == DT_DATEFAIL) message = "Date not set.\nNothing set.";
    else if (result.code == DT_TIMEFAIL && !result.written)
        message = "Time not set.\nNothing set.";
    else {
        dateLoaded = 0;
        EnableWindow(GetDlgItem(w, DATE_APPLY), FALSE);
        if (result.code == DT_TIMEFAIL)
            message = "Date changed.\nTime failed.\nReload/check.";
        else if (result.code == DT_READBACKFAIL)
            message = "Clock changed.\nReadback failed.\nReload/check.";
        else message = "Clock changed.\nReadback differs.\nReload/check.";
    }
    TinyNotice(w, dateInstance, "Date/time", message);
    if (!dateClosing && IsWindow(w)) SetFocus(GetDlgItem(w, focus));
    dateApplying = 0;
}

static HWND makeControl(HWND w, char *cls, char *text, DWORD style,
                        int x, int y, int width, int height, int id)
{
    HWND child;
    child = CreateWindow(cls, text, WS_CHILD | WS_VISIBLE | WS_TABSTOP | style,
                         x, y, width, height, w, (HMENU)id, dateInstance, NULL);
    if (child) SendMessage(child, WM_SETFONT,
                          (WPARAM)GetStockObject(SYSTEM_FIXED_FONT), 0L);
    return child;
}

BOOL FAR PASCAL DateProc(HWND w, UINT m, WPARAM wp, LPARAM lp)
{
    RECT r, c;
    HDC dc;
    HFONT oldfont;
    PAINTSTRUCT ps;
    HWND child;
    int ww, hh;
    if (m == WM_INITDIALOG) {
        dateWindow = w;
        GetWindowRect(w, &r); GetClientRect(w, &c);
        ww = DATE_WIDTH + r.right - r.left - c.right;
        hh = DATE_HEIGHT + r.bottom - r.top - c.bottom;
        if (ww > GetSystemMetrics(SM_CXSCREEN) || hh > GetSystemMetrics(SM_CYSCREEN)) {
            EndDialog(w, IDCANCEL); return TRUE;
        }
        SetWindowPos(w, NULL, (GetSystemMetrics(SM_CXSCREEN) - ww) / 2,
                     (GetSystemMetrics(SM_CYSCREEN) - hh) / 2, ww, hh, SWP_NOZORDER);
        if (!makeControl(w, "EDIT", "", WS_BORDER | ES_AUTOHSCROLL,
                         6, 20, 116, 18, DATE_EDIT) ||
            !makeControl(w, "EDIT", "", WS_BORDER | ES_AUTOHSCROLL,
                         6, 58, 116, 18, TIME_EDIT) ||
            !makeControl(w, "BUTTON", "&Reload current", BS_PUSHBUTTON,
                         6, 80, 116, 20, DATE_RELOAD) ||
            !makeControl(w, "BUTTON", "&Apply", BS_PUSHBUTTON,
                         6, 140, 54, 20, DATE_APPLY) ||
            !makeControl(w, "BUTTON", "&Cancel", BS_DEFPUSHBUTTON,
                         68, 140, 54, 20, IDCANCEL)) {
            EndDialog(w, IDCANCEL); return TRUE;
        }
        SendDlgItemMessage(w, DATE_EDIT, EM_LIMITTEXT, FIELD_MAX, 0L);
        SendDlgItemMessage(w, TIME_EDIT, EM_LIMITTEXT, FIELD_MAX, 0L);
        SendMessage(w, DM_SETDEFID, IDCANCEL, 0L);
        reloadClock(w);
        SetFocus(GetDlgItem(w, IDCANCEL));
        return FALSE;
    }
    if (m == WM_PAINT) {
        dc = BeginPaint(w, &ps);
        oldfont = SelectObject(dc, GetStockObject(SYSTEM_FIXED_FONT));
        SetBkMode(dc, TRANSPARENT); SetTextColor(dc, GetSysColor(COLOR_WINDOWTEXT));
        TextOut(dc, 6, 2, "YYYY-MM-DD", 10);
        TextOut(dc, 6, 40, "HH:MM:SS 24h", 12);
        TextOut(dc, 6, 104, "Apply changes", 13);
        TextOut(dc, 6, 120, "system clock.", 13);
        SelectObject(dc, oldfont); EndPaint(w, &ps); return TRUE;
    }
    if (m == WM_COMMAND) {
        if (wp == IDCANCEL) { dateClosing = 1; EndDialog(w, IDCANCEL); return TRUE; }
        /* An implicit IDOK from Enter in an edit never performs a write. */
        if (wp == IDOK) return TRUE;
        if (wp == DATE_RELOAD && !dateApplying) {
            reloadClock(w); SetFocus(GetDlgItem(w, IDCANCEL)); return TRUE;
        }
        if (wp == DATE_APPLY) {
            child = GetDlgItem(w, DATE_APPLY);
            if ((HWND)LOWORD(lp) == child && HIWORD(lp) == BN_CLICKED &&
                GetFocus() == child) applyClock(w);
            return TRUE;
        }
    }
    if (m == WM_CLOSE || (m == WM_ENDSESSION && wp)) {
        dateClosing = 1;
        EndDialog(w, IDCANCEL); return TRUE;
    }
    if (m == WM_DESTROY) dateWindow = NULL;
    return FALSE;
}

static void dateWord(BYTE FAR **p, unsigned value)
{
    *(*p)++ = (BYTE)value; *(*p)++ = (BYTE)(value >> 8);
}

void TandyDateTime(HWND owner, HINSTANCE instance)
{
    HGLOBAL memory;
    BYTE FAR *p;
    FARPROC proc;
    DWORD style, units;
    char *title = "Date/time";
    int result = -1;
    if (dateBusy) {
        if (dateWindow) SetActiveWindow(dateWindow);
        return;
    }
    dateBusy = 1; dateApplying = dateLoaded = dateClosing = 0;
    dateInstance = instance;
    memory = GlobalAlloc(GMEM_MOVEABLE | GMEM_ZEROINIT, 64);
    if (memory) {
        p = (BYTE FAR *)GlobalLock(memory);
        if (p) {
            style = WS_POPUP | WS_CAPTION | WS_SYSMENU | DS_MODALFRAME;
            dateWord(&p, LOWORD(style)); dateWord(&p, HIWORD(style)); *p++ = 0;
            units = GetDialogBaseUnits();
            dateWord(&p, 0); dateWord(&p, 0);
            dateWord(&p, DATE_WIDTH * 4 / LOWORD(units));
            dateWord(&p, DATE_HEIGHT * 8 / HIWORD(units));
            *p++ = 0; *p++ = 0;
            while (*title) *p++ = *title++;
            *p = 0; GlobalUnlock(memory);
            proc = MakeProcInstance((FARPROC)DateProc, instance);
            if (proc) {
                result = DialogBoxIndirect(instance, memory, owner, (DLGPROC)proc);
                FreeProcInstance(proc);
            }
        }
        GlobalFree(memory);
    }
    dateWindow = NULL; dateBusy = dateApplying = dateLoaded = 0;
    if (result == -1) TinyNotice(owner, instance, "Date/time", "Cannot open\ndate/time.");
}
