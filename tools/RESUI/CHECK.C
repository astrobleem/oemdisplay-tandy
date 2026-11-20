/* Original Win16 font probe; C89, MSC6 /AS /G0, real-mode Windows 3.0.
 * Run only in a private fixture. It writes C:\FONT.LOG and B800 snapshots.
 */
#define WINVER 0x0300
#include <windows.h>
#include <string.h>
static HINSTANCE instance;
static HFILE logfile;
static HFONT systemfont;
static int phase;
static int open_command;
static HWND notepad;
static HGLOBAL dialogtemplate;
static void pixelshot(char *name);

static HWND control(HWND parent, char *class, char *text, int id,
                    int x, int y, int width, int height, DWORD style)
{
    DWORD units;
    HWND child;
    units = GetDialogBaseUnits();
    child = CreateWindow(class, text, WS_CHILD | WS_VISIBLE | style,
        x * LOWORD(units) / 4, y * HIWORD(units) / 8,
        width * LOWORD(units) / 4, height * HIWORD(units) / 8,
        parent, (HMENU)id, instance, NULL);
    SendMessage(child, WM_SETFONT, (WPARAM)systemfont, 0L);
    return child;
}
static void number(char *key, long value)
{
    char text[100], digits[12];
    int n = 0, count = 0;
    unsigned long magnitude;
    while (*key) text[n++] = *key++;
    text[n++] = '=';
    if (value < 0) {
        text[n++] = '-';
        magnitude = (unsigned long)(-value);
    } else magnitude = (unsigned long)value;
    do {
        digits[count++] = (char)('0' + magnitude % 10);
        magnitude /= 10;
    } while (magnitude);
    while (count) text[n++] = digits[--count];
    text[n++] = '\r';
    text[n++] = '\n';
    _lwrite(logfile, text, n);
}
static void snapshot(char *name)
{
    HFILE f;
    f = _lcreat(name, 0);
    if (f != HFILE_ERROR) {
        number("SNAPSHOT_BYTES", _lwrite(f, (void FAR *)((DWORD)GetPrivateProfileInt("test", "vseg", 0xb800, "C:\\SPTEST.INI") << 16),
                                       32768U));
        _lclose(f);
    }
}
static void pixelshot(char *name)
{
    static COLORREF row[64];
    HDC dc; HFILE f; int x,y,w,h,left,n;
    w=GetSystemMetrics(SM_CXSCREEN);h=GetSystemMetrics(SM_CYSCREEN);
    if(w>640)return;
    dc=GetDC(NULL);f=_lcreat(name,0);
    if(f!=HFILE_ERROR){
        for(y=0;y<h;y++){
            for(left=0;left<w;left+=64){
                n=w-left;if(n>64)n=64;
                for(x=0;x<n;x++)row[x]=GetPixel(dc,left+x,y);
                _lwrite(f,(void FAR *)row,n*sizeof(COLORREF));
            }
        }
        _lclose(f);
    }
    ReleaseDC(NULL,dc);
}
static void metrics(HDC dc, int stock)
{
    TEXTMETRIC tm;
    HFONT old;
    char face[64];
    int widths[224];
    HFILE f;
    old = SelectObject(dc, GetStockObject(stock));
    number("STOCK", stock);
    if (!GetTextMetrics(dc, &tm)) number("METRICS_ERROR", 1);
    else {
        number("HEIGHT", tm.tmHeight);
        number("ISOLATED_i",LOWORD(GetTextExtent(dc,"i",1)));
        number("ISOLATED_W",LOWORD(GetTextExtent(dc,"W",1)));
        number("ASCENT", tm.tmAscent);
        number("INTERNAL", tm.tmInternalLeading);
        number("EXTERNAL", tm.tmExternalLeading);
        number("AVERAGE", tm.tmAveCharWidth);
        number("MAXIMUM", tm.tmMaxCharWidth);
        number("FIRST", (unsigned char)tm.tmFirstChar);
        number("LAST", (unsigned char)tm.tmLastChar);
        number("DEFAULT", (unsigned char)tm.tmDefaultChar);
        number("CHARSET", (unsigned char)tm.tmCharSet);
    }
    GetTextFace(dc, sizeof(face), face);
    _lwrite(logfile, face, strlen(face));
    _lwrite(logfile, "\r\n", 2);
    if (stock == SYSTEM_FONT && GetCharWidth(dc, 32, 255, widths)) {
        f = _lcreat("C:\\WIDTHS.BIN", 0);
        if (f != HFILE_ERROR) {
            _lwrite(f, (void FAR *)widths, sizeof(widths));
            _lclose(f);
        }
    }
    SelectObject(dc, old);
}
BOOL FAR PASCAL DialogProc(HWND hwnd, UINT msg, WPARAM wp, LPARAM lp)
{
    RECT rc, child;
    HDC dc;
    DWORD extent;
    if (msg == WM_INITDIALOG) {
        control(hwnd, "STATIC", "Save changes before exit?", 100,
                4, 5, 96, 12, 0L);
        control(hwnd, "BUTTON", "OK", IDOK,
                8, 28, 36, 14, BS_DEFPUSHBUTTON | WS_TABSTOP);
        control(hwnd, "BUTTON", "Cancel", 101,
                52, 28, 44, 14, BS_PUSHBUTTON | WS_TABSTOP);
        GetWindowRect(hwnd, &rc);
        number("DIALOG_LEFT", rc.left);
        number("DIALOG_RIGHT", rc.right);
        number("DIALOG_BOTTOM", rc.bottom);
        number("DIALOG_SCREEN_OVERFLOW", rc.left < 0 || rc.top < 0 ||
            rc.right > GetSystemMetrics(SM_CXSCREEN) ||
            rc.bottom > GetSystemMetrics(SM_CYSCREEN));
        GetClientRect(GetDlgItem(hwnd, 101), &child);
        dc = GetDC(GetDlgItem(hwnd, 101));
        extent = GetTextExtent(dc, "Cancel", 6);
        number("CANCEL_TEXT_WIDTH", LOWORD(extent));
        number("CANCEL_CLIENT_WIDTH", child.right);
        ReleaseDC(GetDlgItem(hwnd, 101), dc);
        SetTimer(hwnd, 1, 200, NULL);
        return TRUE;
    }
    if (msg == WM_TIMER) {
        KillTimer(hwnd, 1);
        snapshot("C:\\DIALOG.BIN");
        pixelshot("C:\\DIALOG.PXL");
        KillTimer(hwnd, 1);
        EndDialog(hwnd, 1);
        return TRUE;
    }
    if (msg == WM_COMMAND && (wp == IDOK || wp == IDCANCEL)) {
        EndDialog(hwnd, 1);
        return TRUE;
    }
    lp = lp;
    return FALSE;
}
LONG FAR PASCAL WindowProc(HWND hwnd, UINT msg, WPARAM wp, LPARAM lp)
{
    PAINTSTRUCT ps;
    HDC dc;
    RECT rc;
    char bytes[32];
    int i, row;
    HFONT old;
    FARPROC dialog;
    if (msg == WM_PAINT) {
        dc = BeginPaint(hwnd, &ps);
        GetClientRect(hwnd, &rc);
        FillRect(dc, &rc, GetStockObject(WHITE_BRUSH));
        SetTextColor(dc, RGB(0,0,0));
        SetBkColor(dc, RGB(255,255,255));
        old = SelectObject(dc, systemfont);
        TextOut(dc, 2, 2, "XT Pixels / Win3", 16);
        TextOut(dc, 2, 18, "File Edit View Help", 19);
        TextOut(dc, 2, 34, "Il1 O08 B6 rn m w", 17);
        bytes[0] = (char)0x7f;
        bytes[1] = (char)0x80;
        bytes[2] = (char)0x81;
        bytes[3] = (char)0xff;
        TextOut(dc, 2, 50, bytes, 4);
        SelectObject(dc, GetStockObject(OEM_FIXED_FONT));
        for (row = 0; row < 4; row++) {
            for (i = 0; i < 16; i++) bytes[i] = (char)(176 + row*16 + i);
            TextOut(dc, 2, 70 + row*10, bytes, 16);
        }
        SelectObject(dc, GetStockObject(SYSTEM_FIXED_FONT));
        TextOut(dc, 2, 118, "Fixed: Il1 O0 rn m", 18);
        SelectObject(dc, old);
        EndPaint(hwnd, &ps);
        return 0;
    }
    if (msg == WM_TIMER) {
        KillTimer(hwnd, 1);
        phase++;
        if (phase == 1) {
            snapshot("C:\\NORMAL.BIN");
            pixelshot("C:\\NORMAL.PXL");
            dialog = MakeProcInstance((FARPROC)DialogProc, instance);
            number("DIALOG_RESULT", DialogBoxIndirect(instance,
                dialogtemplate, hwnd, dialog));
            FreeProcInstance(dialog);
            SetTimer(hwnd, 1, 250, NULL);
        } else if (phase == 2) {
            PostMessage(hwnd, WM_SYSCOMMAND, SC_KEYMENU, (LPARAM)'f');
            SetTimer(hwnd, 1, 250, NULL);
        } else if (phase == 3) {
            int in[2], out[6], saved[2], ret;
            snapshot("C:\\MENU.BIN");
            pixelshot("C:\\MENU.PXL");
            SendMessage(hwnd, WM_CANCELMODE, 0, 0L);
            dc = GetDC(NULL); in[0] = -1; in[1] = 0;
            memset(out, 0, sizeof(out));
            ret = Escape(dc, 0x5860, 4, (LPSTR)in, (LPSTR)out);
            number("PAN_QUERY", ret);
            if (ret > 0 && out[2] > 0 && out[3] > 0) {
                saved[0] = out[0]; saved[1] = out[1];
                number("VIEW_WIDTH", out[2]); number("VIEW_HEIGHT", out[3]);
                number("DESKTOP_WIDTH", out[4]); number("DESKTOP_HEIGHT", out[5]);
                in[0] = out[4] - out[2]; in[1] = out[5] - out[3];
                number("PAN_MOVE", Escape(dc, 0x5860, 4, (LPSTR)in, (LPSTR)out));
                number("PAN_X", out[0]); number("PAN_Y", out[1]);
                snapshot("C:\\PANNED.BIN");
                number("PAN_RETURN", Escape(dc, 0x5860, 4, (LPSTR)saved, (LPSTR)out));
                number("RESTORED_X", out[0]); number("RESTORED_Y", out[1]);
                snapshot("C:\\RESTORED.BIN");
            }
            ReleaseDC(NULL, dc);
            KillTimer(hwnd, 1);

            ShowWindow(hwnd,SW_HIDE);
            number("PAINT_LAUNCH",WinExec("PBRUSH.EXE",SW_SHOW));
            SetTimer(hwnd,1,500,NULL);
        } else if(phase==4){
            HMENU menu,sub; int i,id; char text[80];
            notepad=GetWindow(GetDesktopWindow(),GW_CHILD);
            while(notepad){GetWindowText(notepad,text,sizeof(text));if(strstr(text,"Paintbrush"))break;notepad=GetWindow(notepad,GW_HWNDNEXT);}
            if(notepad){ShowWindow(notepad,SW_SHOWMAXIMIZED);UpdateWindow(notepad);GetClientRect(notepad,&rc);number("PAINT_CLIENT_WIDTH",rc.right);number("PAINT_CLIENT_HEIGHT",rc.bottom);}number("PAINT_FOUND",notepad!=NULL);
            if(notepad){
                menu=GetMenu(notepad);sub=GetSubMenu(menu,0);
                for(i=0;i<GetMenuItemCount(sub);i++){
                    GetMenuString(sub,i,text,sizeof(text),MF_BYPOSITION);
                    if(strstr(text,"Open")){id=GetMenuItemID(sub,i);number("OPEN_COMMAND",id);open_command=id;break;}
                }
            }
            SetTimer(hwnd,1,500,NULL);
        } else if(phase==5){
            if(notepad){UpdateWindow(notepad);snapshot("C:\\PAINT.BIN");pixelshot("C:\\PAINT.PXL");PostMessage(notepad,WM_COMMAND,open_command,0L);}
            SetTimer(hwnd,1,1000,NULL);
        } else if(phase==6){
            HWND dlg,child; RECT box;char cls[40],text[80];int buttons=0,fit=1;
            dlg=FindWindow("#32770",NULL);number("OPEN_DIALOG_FOUND",dlg!=NULL);
            if(dlg){
                GetWindowRect(dlg,&box);number("OPEN_TOP",box.top);number("OPEN_BOTTOM",box.bottom);number("OPEN_RIGHT",box.right);
                child=GetWindow(dlg,GW_CHILD);
                while(child){
                    GetClassName(child,cls,sizeof(cls));GetWindowText(child,text,sizeof(text));
                    if(!lstrcmpi(cls,"Button") && (GetWindowLong(child,GWL_STYLE)&15L)<2){
                        buttons++;_lwrite(logfile,text,lstrlen(text));_lwrite(logfile,"\r\n",2);
                        GetWindowRect(child,&box);number("BUTTON_TOP",box.top);number("BUTTON_BOTTOM",box.bottom);number("BUTTON_RIGHT",box.right);
                        fit=fit && box.left>=0 && box.top>=0 && box.right<=GetSystemMetrics(SM_CXSCREEN) && box.bottom<=GetSystemMetrics(SM_CYSCREEN);
                    }
                    child=GetWindow(child,GW_HWNDNEXT);
                }
                number("OPEN_BUTTONS",buttons);number("OPEN_BUTTONS_FIT",fit);
                snapshot("C:\\OPEN.BIN");pixelshot("C:\\OPEN.PXL");PostMessage(dlg,WM_CLOSE,0,0L);
            }
            if(notepad)PostMessage(notepad,WM_CLOSE,0,0L);
            SetTimer(hwnd,1,500,NULL);
        } else {
            number("DONE",1);_lclose(logfile);ExitWindows(0L,0);DestroyWindow(hwnd);
        }
        return 0;
    }
    if (msg == WM_DESTROY) {
        PostQuitMessage(0);
        return 0;
    }
    wp = wp;
    return DefWindowProc(hwnd, msg, wp, lp);
}
int PASCAL WinMain(HINSTANCE current, HINSTANCE previous,
                  LPSTR command, int show)
{
    WNDCLASS wc;
    HWND hwnd;
    HDC dc;
    MSG msg;
    HMENU menu, popup;
    unsigned char FAR *templatebytes;
    instance = current;
    command = command;
    show = show;
    logfile = _lcreat("C:\\FONT.LOG", 0);
    if (logfile == HFILE_ERROR) return 1;
    systemfont = GetStockObject(SYSTEM_FONT);
    /* Win16 packed classic template: style, BYTE count, WORD x/y/cx/cy,
     * empty menu/class strings, caption. Children are created natively.
     */
    dialogtemplate = GlobalAlloc(GMEM_MOVEABLE | GMEM_ZEROINIT, 64L);
    templatebytes = GlobalLock(dialogtemplate);
    if (!templatebytes) return 4;
    *(DWORD FAR *)templatebytes = WS_POPUP | WS_CAPTION | DS_MODALFRAME;
    templatebytes[9] = 104;
    templatebytes[11] = 52;
    lstrcpy((LPSTR)templatebytes + 15, "Save document");
    GlobalUnlock(dialogtemplate);
    number("SCREEN_WIDTH", GetSystemMetrics(SM_CXSCREEN));
    number("SCREEN_HEIGHT", GetSystemMetrics(SM_CYSCREEN));
    number("DIALOG_BASE", GetDialogBaseUnits());
    number("MENU_HEIGHT",GetSystemMetrics(SM_CYMENU));
    number("VSCROLL_WIDTH",GetSystemMetrics(SM_CXVSCROLL));
    number("HSCROLL_HEIGHT",GetSystemMetrics(SM_CYHSCROLL));
    number("VTHUMB_HEIGHT",GetSystemMetrics(SM_CYVTHUMB));
    number("HTHUMB_WIDTH",GetSystemMetrics(SM_CXHTHUMB));
    number("CAPTION_BUTTON_WIDTH",GetSystemMetrics(SM_CXSIZE));
    number("CAPTION_BUTTON_HEIGHT",GetSystemMetrics(SM_CYSIZE));
    number("CAPTION_HEIGHT",GetSystemMetrics(SM_CYCAPTION));
    number("REAL_MODE",!(GetWinFlags()&WF_PMODE));
    dc = GetDC(NULL);
    metrics(dc, SYSTEM_FONT);
    metrics(dc, SYSTEM_FIXED_FONT);
    metrics(dc, OEM_FIXED_FONT);
    ReleaseDC(NULL, dc);
    if (!previous) {
        memset(&wc, 0, sizeof(wc));
        wc.style = CS_HREDRAW | CS_VREDRAW;
        wc.lpfnWndProc = WindowProc;
        wc.hInstance = current;
        wc.hCursor = LoadCursor(NULL, IDC_ARROW);
        wc.hbrBackground = GetStockObject(WHITE_BRUSH);
        wc.lpszClassName = "XTFONTPRB";
        if (!RegisterClass(&wc)) return 2;
    }
    hwnd = CreateWindow("XTFONTPRB", "XT font test", WS_OVERLAPPEDWINDOW,
        0, 0, GetSystemMetrics(SM_CXSCREEN),
        GetSystemMetrics(SM_CYSCREEN), NULL, NULL, current, NULL);
    if (!hwnd) return 3;
    menu = CreateMenu();
    popup = CreatePopupMenu();
    AppendMenu(popup, MF_STRING, 201, "&Open...");
    AppendMenu(popup, MF_STRING, 202, "E&xit");
    AppendMenu(menu, MF_POPUP, popup, "&File");
    popup = CreatePopupMenu();
    AppendMenu(popup, MF_STRING, 203, "&Copy");
    AppendMenu(menu, MF_POPUP, popup, "&Edit");
    popup = CreatePopupMenu();
    AppendMenu(popup, MF_STRING, 204, "&Preferences...");
    AppendMenu(menu, MF_POPUP, popup, "&View");
    popup = CreatePopupMenu();
    AppendMenu(popup, MF_STRING, 205, "&About");
    AppendMenu(menu, MF_POPUP, popup, "&Help");
    SetMenu(hwnd, menu);
    ShowWindow(hwnd, SW_SHOW);
    UpdateWindow(hwnd);
    SetTimer(hwnd, 1, 250, NULL);
    while (GetMessage(&msg, NULL, 0, 0)) {
        TranslateMessage(&msg);
        DispatchMessage(&msg);
    }
    GlobalFree(dialogtemplate);
    return msg.wParam;
}
