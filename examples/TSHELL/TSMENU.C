/* Windows 3.0 real-mode popup tracking. HMENU owns labels and command IDs. */
#define WINVER 0x0300
#include <windows.h>
#include "TSMENU.H"

#define LEVELS 16
#define LABEL 256
#define EDGE 1
#define PAD 4
#define GUTTER 8

typedef struct {
    HMENU menu;
    HWND window;
    RECT rect;
    int count, selected;
} MenuLevel;

static MenuLevel levels[LEVELS];
static int depth, running, row, screenW, screenH;
static HWND menuOwner;
static HDC menuDC;
static HINSTANCE menuInstance;
static char raw[LABEL], text[LABEL], fitted[LABEL];
static int painting, pendingPaint;
static RECT paintArea, pendingArea;
static void repair(RECT *area);

/* Native menu state packs a child count above the low-byte flags. */
static unsigned state(MenuLevel *p, int n)
{
    unsigned flags;
    flags = GetMenuState(p->menu, n, MF_BYPOSITION);
    return flags & MF_POPUP ? flags & 255 : flags;
}

static int separator(unsigned flags)
{
    return !(flags & MF_POPUP) && (flags & MF_SEPARATOR);
}

static int enabled(MenuLevel *p, int n)
{
    unsigned flags;
    if (n < 0 || n >= p->count) return 0;
    flags = state(p, n);
    return !separator(flags) && !(flags & (MF_GRAYED | MF_DISABLED));
}

static int itemheight(MenuLevel *p, int n)
{
    return separator(state(p, n)) ? row / 2 : row;
}

static int itemtop(MenuLevel *p, int n)
{
    int i, y;
    y = EDGE;
    for (i = 0; i < n; ++i) y += itemheight(p, i);
    return y;
}

/* Decode native accelerators once; doubled ampersands remain literal. */
static int label(MenuLevel *p, int n)
{
    int i, j, hot;
    GetMenuString(p->menu, n, raw, LABEL, MF_BYPOSITION);
    hot = 0;
    for (i = 0, j = 0; raw[i] && j < LABEL - 1; ++i) {
        if (raw[i] == '&') {
            if (raw[i + 1] == '&') ++i;
            else {
                if (raw[i + 1]) hot = (unsigned char)raw[i + 1];
                continue;
            }
        }
        text[j++] = raw[i];
    }
    text[j] = 0;
    if (hot >= 'a' && hot <= 'z') hot -= 'a' - 'A';
    return hot;
}

static int extent(HDC dc, char *s)
{
    return (int)LOWORD(GetTextExtent(dc, s, lstrlen(s)));
}

/* Fit only names that exceed the whole viewport. Never alter HMENU data. */
static void fit(HDC dc, int pixels)
{
    int n;
    lstrcpy(fitted, text);
    if (extent(dc, fitted) <= pixels) return;
    n = lstrlen(text);
    if (n > LABEL - 4) n = LABEL - 4;
    while (n > 0) {
        --n;
        lstrcpy(fitted, text);
        lstrcpy(fitted + n, "...");
        if (extent(dc, fitted) <= pixels) return;
    }
    lstrcpy(fitted, "...");
    while (fitted[0] && extent(dc, fitted) > pixels)
        fitted[lstrlen(fitted) - 1] = 0;
}

static void paint(int index, HDC dc, RECT *damage)
{
    MenuLevel *p;
    RECT r;
    HFONT old;
    HBRUSH brush;
    int i, y, h, color, width;
    unsigned flags;
    p = &levels[index];
    GetClientRect(p->window, &r);
    brush = CreateSolidBrush(GetSysColor(COLOR_MENU));
    FillRect(dc, &r, brush); DeleteObject(brush);
    FrameRect(dc, &r, GetStockObject(BLACK_BRUSH));
    old = (HFONT)SelectObject(dc, GetStockObject(SYSTEM_FONT));
    SetBkMode(dc, TRANSPARENT);
    width = r.right;
    y = EDGE;
    for (i = 0; i < p->count; ++i) {
        flags = state(p, i); h = itemheight(p, i);
        r.left = EDGE; r.right = width - EDGE;
        r.top = y; r.bottom = y + h;
        if (r.bottom <= damage->top || r.top >= damage->bottom) {
            y += h; continue;
        }
        if (separator(flags)) {
            r.left += PAD; r.right -= PAD;
            r.top += h / 2; r.bottom = r.top + 1;
            FillRect(dc, &r, GetStockObject(GRAY_BRUSH));
        } else {
            color = COLOR_MENUTEXT;
            if (flags & (MF_GRAYED | MF_DISABLED)) color = COLOR_GRAYTEXT;
            if (p->selected == i) {
                brush = CreateSolidBrush(GetSysColor(COLOR_HIGHLIGHT));
                FillRect(dc, &r, brush); DeleteObject(brush);
                color = COLOR_HIGHLIGHTTEXT;
            }
            SetTextColor(dc, GetSysColor(color));
            label(p, i);
            fit(dc, width - 2 * (EDGE + PAD) - GUTTER);
            TextOut(dc, EDGE + PAD, y + 1, fitted, lstrlen(fitted));
            if (flags & MF_POPUP)
                TextOut(dc, width - EDGE - GUTTER, y + 1, ">", 1);
        }
        y += h;
    }
    SelectObject(dc, old);
}

/* Paint only visible pieces of real damage. Subtract newer windows with
   simple rectangles: Win3.0's complex popup clipping can leave holes on the
   compact driver. Covered parents are never drawn through a newer child. */
static void piece(int index, RECT *area)
{
    RECT local;
    local = *area;
    OffsetRect(&local, -levels[index].rect.left, -levels[index].rect.top);
    SetViewportOrg(menuDC, levels[index].rect.left, levels[index].rect.top);
    SelectClipRgn(menuDC, NULL);
    IntersectClipRect(menuDC, local.left, local.top,
                      local.right, local.bottom);
    paint(index, menuDC, &local);
}

static void visible(int index, int newer, RECT *area)
{
    RECT cover, part;
    int i;
    for (i = newer; i < depth; ++i) {
        if (!IntersectRect(&cover, area, &levels[i].rect)) continue;
        /* Four nonoverlapping rectangular leftovers, with bounded depth. */
        part = *area; part.bottom = cover.top;
        if (part.top < part.bottom) visible(index, i + 1, &part);
        part = *area; part.top = cover.bottom;
        if (part.top < part.bottom) visible(index, i + 1, &part);
        part = *area; part.top = cover.top; part.bottom = cover.bottom;
        part.right = cover.left;
        if (part.left < part.right) visible(index, i + 1, &part);
        part.left = cover.right; part.right = area->right;
        if (part.left < part.right) visible(index, i + 1, &part);
        return;
    }
    piece(index, area);
}

static void repair(RECT *area)
{
    RECT damage;
    int i;
    if (!depth || !menuDC) return;
    if (painting) {
        /* GDI can yield. Damage already inside this pass needs no new pass. */
        if (area->left >= paintArea.left && area->top >= paintArea.top &&
            area->right <= paintArea.right &&
            area->bottom <= paintArea.bottom) return;
        if (pendingPaint) UnionRect(&pendingArea, &pendingArea, area);
        else pendingArea = *area;
        pendingPaint = 1; return;
    }
    painting = 1; paintArea = *area;
    do {
        pendingPaint = 0;
        for (i = 0; i < depth; ++i)
            if (IntersectRect(&damage, &paintArea, &levels[i].rect))
                visible(i, i + 1, &damage);
        if (pendingPaint) paintArea = pendingArea;
    } while (pendingPaint);
    SetViewportOrg(menuDC, 0, 0);
    SelectClipRgn(menuDC, NULL);
    painting = 0;
}

static void rowdamage(int index, int n)
{
    RECT r;
    if (n < 0 || n >= levels[index].count) return;
    r = levels[index].rect;
    r.left += EDGE; r.right -= EDGE;
    r.top += itemtop(&levels[index], n);
    r.bottom = r.top + itemheight(&levels[index], n);
    repair(&r);
}

LONG FAR PASCAL TSMenuProc(HWND w, UINT m, WPARAM wp, LPARAM lp)
{
    PAINTSTRUCT ps;
    RECT r;
    POINT origin;
    if (m == WM_PAINT) {
        BeginPaint(w, &ps);
        r = ps.rcPaint;
        EndPaint(w, &ps);
        origin.x = origin.y = 0; ClientToScreen(w, &origin);
        OffsetRect(&r, origin.x, origin.y);
        repair(&r); return 0;
    }
    if (m == WM_MOUSEACTIVATE) return MA_NOACTIVATE;
    return DefWindowProc(w, m, wp, lp);
}

static void trim(int count)
{
    HWND w;
    RECT exposed, more;
    if (depth <= count) return;
    exposed = levels[depth - 1].rect;
    while (depth > count) {
        more = levels[depth - 1].rect;
        UnionRect(&exposed, &exposed, &more);
        w = levels[--depth].window;
        levels[depth].window = NULL;
        DestroyWindow(w);
    }
    repair(&exposed);
}

static void selectrow(int index, int n)
{
    int previous;
    previous = levels[index].selected;
    if (previous == n) return;
    trim(index + 1);
    levels[index].selected = n;
    rowdamage(index, previous);
    rowdamage(index, n);
}

static int openmenu(HMENU menu, int x, int y)
{
    MenuLevel *p;
    HDC dc;
    HFONT old;
    int i, width, height, w;
    if (depth == LEVELS) return 0;
    SendMessage(menuOwner, WM_INITMENUPOPUP, (WPARAM)menu, 0L);
    p = &levels[depth]; p->menu = menu;
    p->count = GetMenuItemCount(menu); p->selected = -1;
    width = 0; height = 2 * EDGE;
    dc = GetDC(menuOwner);
    if (!dc) return 0;
    old = (HFONT)SelectObject(dc, GetStockObject(SYSTEM_FONT));
    for (i = 0; i < p->count; ++i) {
        label(p, i); w = extent(dc, text);
        if (w > width) width = w;
        height += itemheight(p, i);
    }
    SelectObject(dc, old); ReleaseDC(menuOwner, dc);
    width += 2 * (EDGE + PAD) + GUTTER;
    if (width > screenW) width = screenW;
    if (height > screenH) height = screenH;
    /* Width depends solely on this menu and the viewport, never depth.
       Shift left at the right edge, covering the parents as necessary. */
    if (x + width > screenW) x = screenW - width;
    if (y + height > screenH) y = screenH - height;
    if (x < 0) x = 0;
    if (y < 0) y = 0;
    p->rect.left = x; p->rect.top = y;
    p->rect.right = x + width; p->rect.bottom = y + height;
    /* Select the root before its first paint, avoiding a second row paint. */
    if (!depth)
        for (i = 0; i < p->count; ++i)
            if (enabled(p, i)) { p->selected = i; break; }
    p->window = CreateWindow("TSMenu", "", WS_POPUP | WS_CLIPSIBLINGS,
        x, y, width, height, NULL, NULL, menuInstance, NULL);
    if (!p->window) return 0;
    ++depth;
    ShowWindow(p->window, SW_SHOWNOACTIVATE);
    SetWindowPos(p->window, NULL, 0, 0, 0, 0,
                 SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE);
    UpdateWindow(p->window);
    return 1;
}

static void move(int direction)
{
    MenuLevel *p;
    int n, i;
    p = &levels[depth - 1]; n = p->selected;
    if (n < 0) n = direction > 0 ? -1 : 0;
    for (i = 0; i < p->count; ++i) {
        n += direction;
        if (n < 0) n = p->count - 1;
        if (n >= p->count) n = 0;
        if (enabled(p, n)) { selectrow(depth - 1, n); return; }
    }
}

static unsigned enterat(int index, int keyboard)
{
    MenuLevel *p;
    HMENU child;
    p = &levels[index];
    if (!enabled(p, p->selected)) return 0;
    child = GetSubMenu(p->menu, p->selected);
    if (child) {
        if (index + 1 < depth && levels[index + 1].menu == child)
            return 0;
        trim(index + 1);
        if (openmenu(child, p->rect.right - EDGE,
                     p->rect.top + itemtop(p, p->selected)) && keyboard)
            move(1);
        return 0;
    }
    return GetMenuItemID(p->menu, p->selected);
}

static unsigned enter(int keyboard)
{
    return enterat(depth - 1, keyboard);
}

/* Newest visible child wins, even when it covers an ancestor's active row. */
static int hit(POINT point, int *item)
{
    int i, n, y;
    MenuLevel *p;
    for (i = depth - 1; i >= 0; --i) {
        p = &levels[i];
        if (!PtInRect(&p->rect, point)) continue;
        y = point.y - p->rect.top - EDGE;
        for (n = 0; n < p->count && y >= 0; ++n) {
            if (y < itemheight(p, n)) {
                *item = enabled(p, n) ? n : -1; return i;
            }
            y -= itemheight(p, n);
        }
        *item = -1; return i;
    }
    return -1;
}

void FAR TSMenuTrack(HMENU menu, int x, int y, HWND owner)
{
    WNDCLASS wc;
    MSG msg;
    HDC dc;
    HFONT old;
    TEXTMETRIC tm;
    POINT point, lastMouse, openedAt, origin;
    RECT damage;
    int damaged;
    HWND previous;
    int level, item, key, i, quit, suppressUp;
    unsigned command;
    if (running) return;
    menuOwner = owner;
    menuInstance = (HINSTANCE)GetWindowWord(owner, GWW_HINSTANCE);
    if (!GetClassInfo(menuInstance, "TSMenu", &wc)) {
        wc.style = 0; wc.lpfnWndProc = TSMenuProc;
        wc.cbClsExtra = wc.cbWndExtra = 0;
        wc.hInstance = menuInstance; wc.hIcon = NULL;
        wc.hCursor = LoadCursor(NULL, IDC_ARROW); wc.hbrBackground = NULL;
        wc.lpszMenuName = NULL; wc.lpszClassName = "TSMenu";
        if (!RegisterClass(&wc)) return;
    }
    dc = GetDC(owner); if (!dc) return;
    old = (HFONT)SelectObject(dc, GetStockObject(SYSTEM_FONT));
    i = GetTextMetrics(dc, &tm);
    SelectObject(dc, old); ReleaseDC(owner, dc);
    if (!i || tm.tmHeight < 1) return;
    row = tm.tmHeight + 1;
    screenW = GetSystemMetrics(SM_CXSCREEN);
    screenH = GetSystemMetrics(SM_CYSCREEN);
    if (screenH > 200) screenH = 200;
    menuDC = CreateDC("DISPLAY", NULL, NULL, NULL);
    if (!menuDC) return;
    depth = 0; command = 0; quit = 0; suppressUp = 0; running = 1;
    if (!openmenu(menu, x, y)) {
        DeleteDC(menuDC); menuDC = NULL; running = 0; return;
    }
    GetCursorPos(&lastMouse);
    previous = SetCapture(owner);
    while (running && IsWindow(owner)) {
        i = GetMessage(&msg, NULL, 0, 0);
        if (i <= 0) { quit = i == 0; break; }
        if (msg.message == WM_KEYDOWN || msg.message == WM_SYSKEYDOWN) {
            GetCursorPos(&lastMouse);
            key = msg.wParam;
            if (key == VK_ESCAPE || key == VK_LEFT) {
                if (depth > 1) trim(depth - 1);
                else if (key == VK_ESCAPE) running = 0;
            } else if (key == VK_DOWN) move(1);
            else if (key == VK_UP) move(-1);
            else if (key == VK_HOME || key == VK_END) {
                selectrow(depth - 1, -1); move(key == VK_HOME ? 1 : -1);
            } else if (key == VK_RETURN || key == VK_RIGHT) {
                if (key == VK_RETURN || GetSubMenu(
                    levels[depth - 1].menu, levels[depth - 1].selected))
                    command = enter(1);
            } else if (key == VK_MENU || key == VK_TAB) running = 0;
            else {
                for (i = 0; i < levels[depth - 1].count; ++i)
                    if (enabled(&levels[depth - 1], i) &&
                        label(&levels[depth - 1], i) == key) {
                        selectrow(depth - 1, i); command = enter(1); break;
                    }
            }
            if (command) running = 0;
            continue;
        }
        if (msg.message == WM_LBUTTONDOWN || msg.message == WM_LBUTTONUP ||
            msg.message == WM_MOUSEMOVE || msg.message == WM_RBUTTONDOWN) {
            point.x = (int)LOWORD(msg.lParam);
            point.y = (int)HIWORD(msg.lParam);
            if (msg.message == WM_MOUSEMOVE) GetCursorPos(&point);
            else ClientToScreen(msg.hwnd, &point);
            /* Showing a child can synthesize WM_MOUSEMOVE at the unchanged
               cursor position. It must not undo keyboard navigation. */
            if (msg.message == WM_MOUSEMOVE && point.x == lastMouse.x &&
                point.y == lastMouse.y) continue;
            lastMouse = point;
            if (msg.message == WM_LBUTTONUP && suppressUp) {
                suppressUp = 0;
                if (point.x == openedAt.x && point.y == openedAt.y)
                    continue;
            }
            if (msg.message == WM_LBUTTONDOWN && suppressUp &&
                (point.x != openedAt.x || point.y != openedAt.y))
                suppressUp = 0;
            level = hit(point, &item);
            if (level < 0) {
                if (msg.message != WM_MOUSEMOVE) running = 0;
            } else if (item >= 0) {
                selectrow(level, item);
                if (state(&levels[level], item) & MF_POPUP) {
                    if (level == depth - 1) {
                        enter(0);
                        /* Opening a child must not also activate the
                           newly covered row on the same button release. */
                        if (depth > level + 1) {
                            suppressUp = 1; openedAt = point;
                        }
                    }
                } else if (msg.message == WM_LBUTTONUP) {
                    trim(level + 1); command = enter(0);
                    if (command) running = 0;
                }
            }
            continue;
        }
        /* Popup WM_PAINT handles its own actual damage once. A clock or
           button paint can expose part of an overlapping menu, so repair
           only that invalid rectangle after the normal window paints. */
        damaged = 0;
        if (msg.message == WM_PAINT) {
            for (i = 0; i < depth; ++i)
                if (levels[i].window == msg.hwnd) break;
            if (i == depth && GetUpdateRect(msg.hwnd, &damage, FALSE)) {
                origin.x = origin.y = 0;
                ClientToScreen(msg.hwnd, &origin);
                OffsetRect(&damage, origin.x, origin.y); damaged = 1;
            }
        }
        TranslateMessage(&msg); DispatchMessage(&msg);
        if (damaged) repair(&damage);
        if (GetCapture() != owner || GetActiveWindow() != owner) running = 0;
    }
    trim(0);
    DeleteDC(menuDC); menuDC = NULL;
    if (GetCapture() == owner) ReleaseCapture();
    if (previous && IsWindow(previous)) SetCapture(previous);
    running = 0;
    if (IsWindow(owner)) UpdateWindow(owner);
    if (command && IsWindow(owner))
        PostMessage(owner, WM_COMMAND, command, 0L);
    if (quit) PostQuitMessage(msg.wParam);
}
