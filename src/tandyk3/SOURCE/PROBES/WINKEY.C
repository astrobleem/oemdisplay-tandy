/* First-party Windows 3.0 real-mode/8086 keyboard message observer. */
#define WINVER 0x0300
#include <windows.h>
static HFILE logFile = -1;
static char rows[20][160];
static int rowCount, failed;
static unsigned long sequence;
static void SaveLine(LPSTR text)
{
    UINT len;
    if (logFile == -1 || failed) return;
    len = lstrlen(text);
    if (_lwrite(logFile,text,len) != len) failed = 1;
}
static void ApiProbe(void)
{
    char line[160], src[4], oem[4], back[4];
    static BYTE states[256];
    static unsigned int glyph[4]={92,124,126,96};
    unsigned int i,j,vk,scan,round;
    DWORD recipe,chars;
    int n;
    wsprintf(line,"# API GetKeyboardType: type=%d subtype=%d functions=%d\r\n",
        GetKeyboardType(0),GetKeyboardType(1),GetKeyboardType(2)); SaveLine(line);
    for(i=0;i<4;i++) {
        scan=0x60+i; vk=MapVirtualKey(scan,1); round=MapVirtualKey(vk,0);
        wsprintf(line,"# API MapVirtualKey scan=%02X vk=%04X round=%02X char=%04X\r\n",
            scan,vk,round,MapVirtualKey(vk,2)); SaveLine(line);
        vk=VkKeyScan(glyph[i]); recipe=OemKeyScan(glyph[i]);
        wsprintf(line,"# API glyph=%02X VkKeyScan=%04X OemKeyScan=%08lX\r\n",
            glyph[i],vk,recipe); SaveLine(line);
        for(j=0;j<256;j++) states[j]=0;
        if(vk&0x100) states[VK_SHIFT]=0x80;
        if(vk&0x200) states[VK_CONTROL]=0x80;
        if(vk&0x400) states[VK_MENU]=0x80;
        chars=0; n=ToAscii(vk&255,scan,states,&chars,0);
        wsprintf(line,"# API ToAscii glyph=%02X result=%d chars=%08lX\r\n",
            glyph[i],n,chars); SaveLine(line);
    }
    src[0]='A';src[1]=0;src[2]=(char)0xe9;src[3]=92;
    for(i=0;i<4;i++) oem[i]=back[i]=(char)0xcc;
    AnsiToOemBuff(src,oem,4); OemToAnsiBuff(oem,back,4);
    wsprintf(line,"# API Buff src=4100E95C oem=%02X%02X%02X%02X back=%02X%02X%02X%02X\r\n",
        (BYTE)oem[0],(BYTE)oem[1],(BYTE)oem[2],(BYTE)oem[3],
        (BYTE)back[0],(BYTE)back[1],(BYTE)back[2],(BYTE)back[3]); SaveLine(line);
}
long FAR PASCAL WndProc(HWND w, UINT m, WORD wp, LONG lp)
{
    PAINTSTRUCT ps;
    HDC dc;
    char s[160];
    char *name;
    unsigned int hi;
    int i, first, visible, lineHeight;
    TEXTMETRIC tm;
    RECT client;
    switch (m) {
    case WM_KEYDOWN: case WM_KEYUP: case WM_SYSKEYDOWN:
    case WM_SYSKEYUP: case WM_CHAR: case WM_SYSCHAR:
    case WM_DEADCHAR: case WM_SYSDEADCHAR:
        name="KEYDOWN";
        if(m==WM_KEYUP) name="KEYUP";
        if(m==WM_SYSKEYDOWN) name="SYSKEYDOWN";
        if(m==WM_SYSKEYUP) name="SYSKEYUP";
        if(m==WM_CHAR) name="CHAR";
        if(m==WM_SYSCHAR) name="SYSCHAR";
        if(m==WM_DEADCHAR) name="DEADCHAR";
        if(m==WM_SYSDEADCHAR) name="SYSDEADCHAR";
        hi=HIWORD(lp);
        wsprintf(s,"%lu %s value=%04X scan=%02X repeat=%u ext=%u alt=%u prev=%u up=%u num=%u shift=%u ctrl=%u\r\n",
            ++sequence,(LPSTR)name,wp,hi&255,LOWORD(lp),
            (hi>>8)&1,(hi>>13)&1,(hi>>14)&1,(hi>>15)&1,
            GetKeyState(VK_NUMLOCK)&1,(GetKeyState(VK_SHIFT)&0x8000)!=0,
            (GetKeyState(VK_CONTROL)&0x8000)!=0);
        SaveLine(s);
        if(rowCount==20) {
            for(i=0;i<19;i++) lstrcpy(rows[i],rows[i+1]);
            rowCount=19;
        }
        lstrcpy(rows[rowCount++],s);
        InvalidateRect(w,NULL,TRUE);
        /* Preserve ordinary Windows system-key behavior, including Alt-F4. */
        return DefWindowProc(w,m,wp,lp);
    case WM_TIMER:
        if(wp==1) { KillTimer(w,1); DestroyWindow(w); return 0; }
        break;
    case WM_PAINT:
        dc=BeginPaint(w,&ps);
        TextOut(dc,4,4,"WINKEY.LOG: OS message scan fields, NOT raw hardware bytes.",59);
        TextOut(dc,4,22,"Click this window, test keys; close window or Alt-F4 to finish.",63);
        GetTextMetrics(dc,&tm); lineHeight=tm.tmHeight+2;
        GetClientRect(w,&client); visible=(client.bottom-44)/lineHeight;
        if(visible<0) visible=0;
        first=rowCount-visible; if(first<0) first=0;
        for(i=first;i<rowCount;i++)
            TextOut(dc,4,44+(i-first)*lineHeight,rows[i],lstrlen(rows[i])-2);
        if(failed) TextOut(dc,4,370,"LOG WRITE FAILED. Close and check disk space.",45);
        EndPaint(w,&ps);
        return 0;
    case WM_DESTROY:
        SaveLine("# Window closed normally.\r\n");
        if(logFile!=-1) { if(_lclose(logFile)!=0) failed=1; logFile=-1; }
        if(failed) MessageBox(NULL,"WINKEY.LOG write or close failed.","WINKEY",MB_OK|MB_ICONEXCLAMATION);
        PostQuitMessage(failed ? 1 : 0);
        return 0;
    }
    return DefWindowProc(w,m,wp,lp);
}
int PASCAL WinMain(HANDLE inst,HANDLE prev,LPSTR cmd,int show)
{
    WNDCLASS wc;
    HWND w;
    MSG msg;
    if(prev) { MessageBox(NULL,"Close the existing WINKEY first.","WINKEY",MB_OK); return 1; }
    logFile=_lcreat("WINKEY.LOG",0);
    if(logFile==-1) { MessageBox(NULL,"Cannot create WINKEY.LOG in current directory.","WINKEY",MB_OK); return 1; }
    SaveLine("WINKEY Windows 3.0: virtual/character values and OS message scan fields.\r\n");
    SaveLine("NOT raw port 60h bytes. CHAR values use the Windows character encoding.\r\n");
    SaveLine("ext=bit24 alt=bit29 prev=bit30 up=bit31; repeat=low16; scan=bits16..23.\r\n");
    if(lstrcmp(cmd,"/api")==0 || lstrcmp(cmd,"/smoke")==0 || lstrcmp(cmd,"/matrix")==0) ApiProbe();
    wc.style=CS_HREDRAW|CS_VREDRAW;
    wc.lpfnWndProc=WndProc;
    wc.cbClsExtra=wc.cbWndExtra=0;
    wc.hInstance=inst;
    wc.hIcon=LoadIcon(NULL,IDI_APPLICATION);
    wc.hCursor=LoadCursor(NULL,IDC_ARROW);
    wc.hbrBackground=GetStockObject(WHITE_BRUSH);
    wc.lpszMenuName=NULL;
    wc.lpszClassName="WINKEY30";
    if(!RegisterClass(&wc)) { _lclose(logFile); return 1; }
    w=CreateWindow("WINKEY30","Windows 3.0 Keyboard Probe",WS_OVERLAPPEDWINDOW,
        CW_USEDEFAULT,CW_USEDEFAULT,620,440,NULL,NULL,inst,NULL);
    if(!w) { _lclose(logFile); return 1; }
    ShowWindow(w,show); UpdateWindow(w);
    if(lstrcmp(cmd,"/smoke")==0) SetTimer(w,1,20000,NULL);
    if(lstrcmp(cmd,"/matrix")==0) SetTimer(w,1,60000,NULL);
    while(GetMessage(&msg,NULL,0,0)) { TranslateMessage(&msg); DispatchMessage(&msg); }
    return msg.wParam;
}
