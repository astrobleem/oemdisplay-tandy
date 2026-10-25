/* Automated Win3.0 /G0 /Gw /AS viewport regression; emulator fixture only. */
#define WINVER 0x0300
#include <windows.h>
#include <dos.h>
#define XP 0x5850
static HDC dc;
static HFILE logf;
static int hidden, serial;
static WORD vseg;
static HBRUSH brushes[16];
static COLORREF colors[16]={
 RGB(0,0,0),RGB(128,0,0),RGB(0,128,0),RGB(128,128,0),
 RGB(0,0,128),RGB(128,0,128),RGB(0,128,128),RGB(128,128,128),
 RGB(64,64,64),RGB(255,0,0),RGB(0,255,0),RGB(255,255,0),
 RGB(0,0,255),RGB(255,0,255),RGB(0,255,255),RGB(255,255,255)};
static BYTE raw[4096];
static struct {BITMAPINFOHEADER h;RGBQUAD c[16];} info;
static BYTE dib[220];
static void line(char *k,LONG v){char b[100];int n=wsprintf(b,"%s=%ld\r\n",(LPSTR)k,v);_lwrite(logf,b,n);}
static void require(char *k,int v){line(k,v);if(!v){line("FAILED",1);}}
static void dump(char *n,void FAR *p,UINT bytes){HFILE f=_lcreat(n,0);UINT got=0;if(f!=HFILE_ERROR){got=_lwrite(f,p,bytes);_lclose(f);}require("DUMP_OK",got==bytes);}
static int pan(int want){int o[3]={-2,0,0};int r=Escape(dc,XP,2,(LPSTR)&want,(LPSTR)o);require("ESCAPE_OK",r>0 && o[1]==200 && o[2]==400);return o[0];}
static void shot(int visible){char n[]="C:\\SP000.BIN";POINT p;int top=pan(-1);GetCursorPos(&p);line("SHOT",serial);line("TOP",top);line("VISIBLE",visible);line("X",p.x);line("Y",p.y);n[5]=(char)('0'+serial/100);n[6]=(char)('0'+serial/10%10);n[7]=(char)('0'+serial%10);dump(n,(void FAR *)((DWORD)vseg<<16),32768U);serial++;_lclose(logf);logf=_lopen("C:\\SPTEST.LOG",OF_WRITE);_llseek(logf,0L,2);}
static void fill(HDC d,int x,int y,int r,int b,int c){RECT q;q.left=x;q.top=y;q.right=r;q.bottom=b;FillRect(d,&q,brushes[c]);}
static void pattern(void){int x,y,c;for(y=0;y<400;y+=8)for(x=0;x<320;x+=32){c=x>=288?12+((y>>7)&3):((y>>3)+(x>>5))&15;fill(dc,x,y,x+32,y+8,c);}}
static void fixtures(void){HDC mem;HBITMAP bm,old;HFONT font,of;int x,y,c;HPEN pen,op;
 fill(dc,17,95,83,108,9);
 SaveDC(dc);IntersectClipRect(dc,40,102,100,205);fill(dc,25,98,120,211,12);RestoreDC(dc,-1);
 mem=CreateCompatibleDC(dc);bm=CreateCompatibleBitmap(dc,128,32);require("TEXT_BITMAP",mem && bm);
 if(mem && bm){old=SelectObject(mem,bm);font=(HFONT)GetStockObject(SYSTEM_FIXED_FONT);of=SelectObject(mem,font);fill(mem,0,0,128,32,15);SetTextColor(mem,colors[11]);SetBkMode(mem,TRANSPARENT);require("MEM_TEXT",TextOut(mem,2,2,"Ag09 Win30",10));line("TEXT_BYTES",GetBitmapBits(bm,4096L,raw));dump("C:\\TEXT.BIN",raw,2048);
 SelectObject(dc,font);SetTextColor(dc,colors[11]);SetBkMode(dc,TRANSPARENT);fill(dc,150,94,278,126,15);require("SCREEN_TEXT_TOP",TextOut(dc,152,96,"Ag09 Win30",10));fill(dc,150,294,278,326,15);require("SCREEN_TEXT_BOTTOM",TextOut(dc,152,296,"Ag09 Win30",10));SelectObject(mem,of);SelectObject(mem,old);DeleteObject(bm);DeleteDC(mem);}
 mem=CreateCompatibleDC(dc);bm=CreateCompatibleBitmap(dc,32,16);require("DDB_BITMAP",mem && bm);
 if(mem && bm){old=SelectObject(mem,bm);for(y=0;y<16;y+=4)for(x=0;x<32;x+=4)fill(mem,x,y,x+4,y+4,((x>>2)+3*(y>>2))&15);require("DDB_TOP",BitBlt(dc,5,94,32,16,mem,0,0,SRCCOPY));require("DDB_BOTTOM",BitBlt(dc,5,294,32,16,mem,0,0,SRCCOPY));SelectObject(mem,old);DeleteObject(bm);DeleteDC(mem);}
 info.h.biSize=40;info.h.biWidth=37;info.h.biHeight=11;info.h.biPlanes=1;info.h.biBitCount=4;info.h.biCompression=BI_RGB;info.h.biSizeImage=220;info.h.biClrUsed=16;
 for(c=0;c<16;c++){info.c[c].rgbRed=GetRValue(colors[c]);info.c[c].rgbGreen=GetGValue(colors[c]);info.c[c].rgbBlue=GetBValue(colors[c]);}
 for(y=0;y<11;y++)for(x=0;x<37;x++){c=(x+3*y)&15;if(x&1)dib[(10-y)*20+(x>>1)]|=c;else dib[(10-y)*20+(x>>1)]=(BYTE)(c<<4);}
 line("DIB_MIDDLE",SetDIBitsToDevice(dc,270,193,37,11,0,0,0,11,dib,(BITMAPINFO FAR *)&info,DIB_RGB_COLORS));
 line("DIB_LOGICAL_EDGE",SetDIBitsToDevice(dc,270,393,37,11,0,0,0,11,dib,(BITMAPINFO FAR *)&info,DIB_RGB_COLORS));
 pen=CreatePen(PS_SOLID,1,colors[15]);op=SelectObject(dc,pen);MoveTo(dc,0,200);require("LINE",LineTo(dc,320,200));SelectObject(dc,op);DeleteObject(pen);
 require("SCREEN_COPY",BitBlt(dc,100,220,96,60,dc,0,180,SRCCOPY));
}
static void pump(void){MSG msg;DWORD end=GetCurrentTime()+1200;while(GetCurrentTime()<end){while(PeekMessage(&msg,NULL,0,0,PM_REMOVE)){TranslateMessage(&msg);DispatchMessage(&msg);}Yield();}}
static void helper(void){char b[256];
 WriteProfileString("XTPan","Enabled","0");
 WriteProfileString("XTPan","FollowActive","0");
 WriteProfileString("windows","load","EXISTING.EXE");
 require("CONFIG_LAUNCH",WinExec("C:\\JRPAN\\PANCFG.EXE",SW_SHOWMINIMIZED)>=32);pump();
 GetProfileString("windows","load","",b,sizeof(b));require("CONFIG_PRESERVED",lstrcmp(b,"EXISTING.EXE C:\\JRPAN\\XTPAN.EXE")==0);
 require("HELPER_RUNNING",FindWindow("XTPan",NULL)!=NULL);
 require("CONFIG_REENABLED",GetProfileInt("XTPan","Enabled",0)==1);
 SetCursorPos(150,350);pump();require("HELPER_DOWN",pan(-1)==200);
 pan(0);pump();require("HELPER_RESET_SYNC",pan(-1)==200);
 SetCursorPos(150,75);pump();require("HELPER_UP",pan(-1)==50);
 require("CONFIG_OFF_LAUNCH",WinExec("C:\\JRPAN\\PANCFG.EXE OFF",SW_SHOWMINIMIZED)>=32);pump();
 GetProfileString("windows","load","",b,sizeof(b));require("CONFIG_REMOVED",lstrcmp(b,"EXISTING.EXE")==0);
 require("HELPER_STOPPED",FindWindow("XTPan",NULL)==NULL);WriteProfileString("windows","load","");
}
int PASCAL WinMain(HINSTANCE inst,HINSTANCE prev,LPSTR cmd,int show){int i,r;RECT rect;HCURSOR cur;POINT p;DWORD free0;
 logf=_lcreat("C:\\SPTEST.LOG",0);if(logf==HFILE_ERROR)return 1;
 dc=GetDC(NULL);if(!dc)return 2;
 if(!lstrcmpi(cmd,"MEM")){line("HORZRES",GetDeviceCaps(dc,HORZRES));line("VERTRES",GetDeviceCaps(dc,VERTRES));line("FREE_START",GetFreeSpace(0));line("COMPLETE",1);ReleaseDC(NULL,dc);_lclose(logf);return 0;}
 vseg=GetPrivateProfileInt("test","vseg",0,"C:\\SPTEST.INI");
 if(!vseg){vseg=(WORD)((*(BYTE FAR *)0x0040008aL & 6)<<10);}
 line("VIDEO_SEG",vseg);line("HORZRES",GetDeviceCaps(dc,HORZRES));line("VERTRES",GetDeviceCaps(dc,VERTRES));line("NUMCOLORS",GetDeviceCaps(dc,NUMCOLORS));line("START_TOP",pan(-1));
 if(GetDeviceCaps(dc,HORZRES)!=320 || GetDeviceCaps(dc,VERTRES)!=400 || pan(-1)!=0){line("WRONG_DISPLAY",1);_lclose(logf);return 3;}
 free0=GetFreeSpace(0);line("FREE_START",free0);
 hidden=0;do{r=ShowCursor(FALSE);hidden++;}while(r>=0 && hidden<32);
 /* A mouse-free guest can start below -1. Normalize the fixture's hidden
    count so every visible capture actually requests count zero. */
 while(r < -1){r=ShowCursor(TRUE);hidden--;}SetCursor(NULL);
 for(i=0;i<16;i++)brushes[i]=CreateSolidBrush(colors[i]);
 pattern();shot(0);
 {int tops[8]={1,99,100,199,200,-2,32767,-1};for(i=0;i<8;i++){line("PAN_REQUEST",tops[i]);line("PAN_RETURN",pan(tops[i]));shot(0);}}
 pan(100);fixtures();shot(0);pan(0);shot(0);pan(200);shot(0);
 rect.left=0;rect.top=0;rect.right=320;rect.bottom=400;
 require("SCROLL",ScrollDC(dc,0,-17,&rect,&rect,NULL,NULL));fill(dc,0,383,320,400,6);shot(0);pan(0);shot(0);pan(100);shot(0);
 cur=LoadCursor(NULL,IDC_ARROW);require("CURSOR_LOADED",cur!=NULL);SetCursor(cur);
 for(i=0;i<6;i++){p.x=(i&1)?319:0;p.y=(i<2)?99:(i<4)?100:299;SetCursorPos(p.x,p.y);line("CURSOR_SHOW",ShowCursor(TRUE));shot(1);line("CURSOR_HIDE",ShowCursor(FALSE));shot(0);}
 SetCursorPos(80,198);ShowCursor(TRUE);fill(dc,75,196,110,210,10);shot(1);pan(199);shot(1);pan(200);shot(1);ShowCursor(FALSE);shot(0);
 SetCursor(NULL);pan(0);shot(0);
 line("FREE_BEFORE_PANS",GetFreeSpace(0));for(i=0;i<40;i++)pan((i&1)?0:200);line("FREE_AFTER",GetFreeSpace(0));line("FREE_DELTA",(LONG)GetFreeSpace(0)-(LONG)free0);
 for(i=0;i<16;i++)DeleteObject(brushes[i]);line("FREE_CLEAN",GetFreeSpace(0));helper();ReleaseDC(NULL,dc);while(hidden-->0)ShowCursor(TRUE);
 line("COMPLETE",1);_lclose(logf);return 0;
}
