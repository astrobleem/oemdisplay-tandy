#define WinMain OriginalWinMain
#include "SUBJECT.C"
#undef WinMain
static HFILE logf;static int passn,failn;
static void line(char *s){_lwrite(logf,(LPSTR)s,lstrlen(s));_lwrite(logf,"\r\n",2);}
static void check(char *s,int ok){if(ok){passn++;_lwrite(logf,"PASS=",5);}else{failn++;_lwrite(logf,"FAIL=",5);}line(s);}
static void val(char *s,DWORD v){char b[12];_lwrite(logf,(LPSTR)s,lstrlen(s));num(b,v);line(b);}
int PASCAL WinMain(HINSTANCE inst,HINSTANCE prev,LPSTR cmd,int show){
 WNDCLASS wc;HWND w;RECT r,br;POINT pt;HDC dc;TEXTMETRIC tm;DWORD ext,before,after;int i,j,x,ew,ec;char name[80],b[24];BYTE kb[256],savedkb[256];MSG msg;
 instance=inst;logf=_lcreat("C:\\ABOUTUT.LOG",0);if(logf==HFILE_ERROR)return 9;
 line("HARNESS=ABOUT_NATIVE_WIN16");ew=GetSystemMetrics(SM_CXSCREEN);ec=cmd[0]=='1'?16:cmd[0]=='b'?16:cmd[0]=='2'?2:4;
 val("SCREEN_WIDTH=",ew);val("SCREEN_HEIGHT=",GetSystemMetrics(SM_CYSCREEN));val("WIN_FLAGS=",GetWinFlags());
 check("windows-real-mode",!(GetWinFlags()&WF_PMODE));check("windows-8086-flag",(GetWinFlags()&WF_CPU086)!=0);
 wc.style=CS_HREDRAW|CS_VREDRAW;wc.lpfnWndProc=WndProc;wc.cbClsExtra=0;wc.cbWndExtra=0;wc.hInstance=inst;wc.hIcon=NULL;wc.hCursor=LoadCursor(NULL,IDC_ARROW);wc.hbrBackground=GetStockObject(WHITE_BRUSH);wc.lpszMenuName=NULL;wc.lpszClassName="AboutUT";
 check("register",RegisterClass(&wc)!=0);w=CreateWindow("AboutUT","About Tandy",WS_OVERLAPPEDWINDOW|WS_CLIPCHILDREN,0,0,160,200,NULL,NULL,inst,NULL);check("window",w!=NULL);if(!w)goto done;
 ShowWindow(w,SW_SHOWMAXIMIZED);UpdateWindow(w);GetClientRect(w,&r);x=(r.right-148)/2;if(x<0)x=0;
 val("CLIENT_WIDTH=",r.right);val("CLIENT_HEIGHT=",r.bottom);val("COLORS=",colors);val("PLANES=",planes);val("BITS=",bits);val("VERSION=",version);val("FREE_BYTES=",freebytes);
 check("sample-version",version==GetVersion());check("sample-flags",flags==GetWinFlags());check("sample-width",width==ew);check("sample-height",height==200);check("actual-mode-colors",colors==ec);check("four-logical-planes",planes==4);check("one-bit-per-plane",bits==1);
 before=GetFreeSpace(0);sample(w);after=GetFreeSpace(0);check("sample-free-memory-api",freebytes<=before&&freebytes>=after);check("free-memory-plausible",freebytes>0&&freebytes<655360L);
 for(i=0;i<4;i++){num(b,i);lstrcpy(name,"control-created-");lstrcat(name,b);check(name,buttons[i]!=NULL&&IsWindow(buttons[i]));GetWindowText(buttons[i],name,80);check("control-label",!lstrcmp(name,i==0?"Sys":i==1?"Disp":i==2?"Mem":"Refresh"));GetWindowRect(buttons[i],&br);pt.x=br.left;pt.y=br.top;ScreenToClient(w,&pt);check("control-geometry",pt.x==(i<3?x+i*50:x)&&pt.y==(i<3?2:130)&&br.right-br.left==(i<3?48:148)&&br.bottom-br.top==20);check("control-in-client",pt.x>=0&&pt.y>=0&&pt.x+br.right-br.left<=r.right&&pt.y+br.bottom-br.top<=r.bottom);}
 dc=GetDC(w);SelectObject(dc,GetStockObject(SYSTEM_FIXED_FONT));GetTextMetrics(dc,&tm);val("FONT_HEIGHT=",tm.tmHeight);val("FONT_WIDTH=",tm.tmAveCharWidth);check("row-height",tm.tmHeight<=12);
 for(j=0;j<3;j++){SendMessage(w,WM_COMMAND,SYS+j,0L);check("page-command",page==j);for(i=0;i<8;i++){ext=GetTextExtent(dc,lines[i],lstrlen(lines[i]));check("text-width-in-client",x+2+LOWORD(ext)<=r.right);check("text-no-buffer-overflow",lstrlen(lines[i])<24);if(lines[i][0])check("text-above-refresh",28+i*12+HIWORD(ext)<=130);}UpdateWindow(w);}
 ext=GetTextExtent(dc,"S D M R / Esc",13);check("footer-bounds",x+2+LOWORD(ext)<=r.right&&154+HIWORD(ext)<=r.bottom);ReleaseDC(w,dc);
 page=0;compose();check("system-title",!lstrcmp(lines[0],"About This Tandy"));check("system-version",!lstrcmp(lines[1],"Windows 3.00"));check("system-mode",!lstrcmp(lines[2],"Real mode"));check("system-cpu",!lstrcmp(lines[4],"8086/8088"));check("model-honesty",!lstrcmp(lines[5],"Model: unknown"));
 page=1;compose();num(b,width);lstrcpy(name,"Width: ");lstrcat(name,b);check("display-width",!lstrcmp(lines[1],name));num(b,colors);lstrcpy(name,"Colors: ");lstrcat(name,b);check("display-actual-colors",!lstrcmp(lines[3],name));check("display-logical-planes",!lstrcmp(lines[4],"DDB planes: 4"));
 page=2;compose();num(b,freebytes/1024L);lstrcat(b," KiB");check("memory-kib",!lstrcmp(lines[2],b));check("memory-honesty",!lstrcmp(lines[4],"Not installed RAM"));
 check("cpu-unknown",!lstrcmp(cpu(0),"Unknown family"));check("cpu-186",!lstrcmp(cpu(WF_CPU186),"80186/80188"));check("cpu-286",!lstrcmp(cpu(WF_CPU286),"80286 family"));check("cpu-386",!lstrcmp(cpu(WF_CPU386),"80386 family"));check("cpu-486",!lstrcmp(cpu(WF_CPU486),"80486 family"));
 check("key-s",key(w,'S')&&page==0);check("key-d",key(w,'D')&&page==1);check("key-m",key(w,'M')&&page==2);check("right-wrap",key(w,VK_RIGHT)&&page==0);check("left-wrap",key(w,VK_LEFT)&&page==2);check("unknown-key",!key(w,'Z'));SetFocus(w);check("tab-from-parent-selects-sys",key(w,VK_TAB)&&GetFocus()==buttons[0]);SetFocus(buttons[0]);check("tab-focus",key(w,VK_TAB)&&GetFocus()==buttons[1]);SetFocus(buttons[3]);check("tab-wrap",key(w,VK_TAB)&&GetFocus()==buttons[0]);
 GetKeyboardState(savedkb);for(i=0;i<256;i++)kb[i]=savedkb[i];kb[VK_SHIFT]=0x80;SetKeyboardState(kb);SetFocus(w);check("shift-tab-parent-refresh",key(w,VK_TAB)&&GetFocus()==buttons[3]);SetFocus(buttons[0]);check("shift-tab-wrap-refresh",key(w,VK_TAB)&&GetFocus()==buttons[3]);check("shift-tab-backwards",key(w,VK_TAB)&&GetFocus()==buttons[2]);SetKeyboardState(savedkb);
 version=flags=freebytes=0;width=height=colors=planes=bits=0;check("refresh-key",key(w,'R'));check("refresh-values",version==GetVersion()&&flags==GetWinFlags()&&freebytes>0&&width==ew&&height==200&&colors==ec&&planes==4&&bits==1);check("refresh-keeps-page",page==2);
 check("escape-handled",key(w,VK_ESCAPE));check("escape-destroys",!IsWindow(w));check("destroy-posts-quit",PeekMessage(&msg,NULL,WM_QUIT,WM_QUIT,PM_REMOVE)&&msg.message==WM_QUIT);
 w=CreateWindow("AboutUT","Close test",WS_OVERLAPPEDWINDOW,0,0,160,200,NULL,NULL,inst,NULL);check("close-window-created",w!=NULL);if(w){SendMessage(w,WM_CLOSE,0,0L);check("wm-close-destroys",!IsWindow(w));}
 done:val("PASS_COUNT=",passn);val("FAIL_COUNT=",failn);line("COMPLETE=1");_lclose(logf);return failn?1:0;
}
