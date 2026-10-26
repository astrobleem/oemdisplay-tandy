/* Original read-only Win3 metrics probe; C89, MSC6 /G0 /Gw /AS.
 * Scoped Windows 3.0 API qualification is recorded in API.JSN.
 * This helper does not qualify Yamaha scanout or application interaction.
 * No VRAM, ports, driver hooks, timings, disk images or physical hardware.
 * Only writes C:\C16MET.TXT in the licensed private guest fixture.
 */
#define WINVER 0x0300
#include <windows.h>
#include <string.h>
static HFILE output;

static void value(char *key, int number)
{
    char line[100];
    int length;
    length = wsprintf(line, "%s=%d\r\n", (LPSTR)key, number);
    _lwrite(output, line, length);
}

int PASCAL WinMain(HINSTANCE instance, HINSTANCE previous, LPSTR command, int show)
{
    HDC dc;
    HFONT old;
    TEXTMETRIC tm;
    DWORD units, extent;
    int i, stock;
    char key[32], face[64];
    char *sample = "File Options Window Help";
    output = _lcreat("C:\\C16MET.TXT", 0);
    if (output == HFILE_ERROR) return 1;
    value("WindowsVersion", (int)LOWORD(GetVersion()));
    value("WindowsFlags", (int)LOWORD(GetWinFlags()));
    for (i = 0; i < 43; ++i) {
        wsprintf(key, "SM_%d", i);
        value(key, GetSystemMetrics(i));
    }
    units = GetDialogBaseUnits();
    value("DialogBaseX", LOWORD(units));
    value("DialogBaseY", HIWORD(units));
    dc = GetDC(NULL);
    if (!dc) { _lclose(output); return 2; }
    for (stock = OEM_FIXED_FONT; stock <= SYSTEM_FONT; ++stock) {
        old = SelectObject(dc, GetStockObject(stock));
        value("StockFont", stock);
        if (GetTextMetrics(dc, &tm)) {
            value("Height", tm.tmHeight);
            value("Ascent", tm.tmAscent);
            value("Internal", tm.tmInternalLeading);
            value("External", tm.tmExternalLeading);
            value("Average", tm.tmAveCharWidth);
            value("Maximum", tm.tmMaxCharWidth);
            value("Weight", tm.tmWeight);
            value("Charset", (unsigned char)tm.tmCharSet);
        }
        GetTextFace(dc, sizeof(face), face);
        _lwrite(output, face, strlen(face));
        _lwrite(output, "\r\n", 2);
        extent = GetTextExtent(dc, sample, strlen(sample));
        value("MenuTextWidth", LOWORD(extent));
        value("MenuTextHeight", HIWORD(extent));
        SelectObject(dc, old);
    }
    ReleaseDC(NULL, dc);
    _lclose(output);
    /* Explicit opt-in for unattended disposable-fixture tests only. */
    if (lstrcmp(command, "/EXIT") == 0) ExitWindows(0L, 0);
    return 0;
}
