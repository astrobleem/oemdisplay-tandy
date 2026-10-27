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

static int px,py;
static struct {BITMAPINFOHEADER h;RGBQUAD c[256];} info8;
static BYTE data8[16];
static void pan(int x,int y){int in[2],o[6];in[0]=x;in[1]=y;
 require("ESCAPE",Escape(dc,0x5860,4,(LPSTR)in,(LPSTR)o)>0);
 require("GEOMETRY",o[2]==320 && o[3]==200 && o[4]==640 && o[5]==400);
 px=o[0];py=o[1];line("LEFT",px);line("TOP",py);
}
static void shot(void){char n[]="C:\\PX000.BIN";n[5]='0'+serial/100;n[6]='0'+serial/10%10;n[7]='0'+serial%10;
 line("SHOT",serial);dump(n,(void FAR *)((DWORD)vseg<<16),32768U);serial++;}
static void fill(int x,int y,int r,int b,int c){RECT q;q.left=x;q.top=y;q.right=r;q.bottom=b;FillRect(dc,&q,brushes[c]);}
int PASCAL WinMain(HINSTANCE inst,HINSTANCE prev,LPSTR cmd,int show){int x,y,i,r,hidden=0;HDC mem;HBITMAP bm,old;DWORD before;HCURSOR cur;
 logf=_lcreat("C:\\PANXY.LOG",0);if(logf==HFILE_ERROR)return 1;dc=GetDC(0);if(!dc)return 2;
 line("HORZRES",GetDeviceCaps(dc,HORZRES));line("VERTRES",GetDeviceCaps(dc,VERTRES));line("FREE_START",GetFreeSpace(0));
 require("SIZE",GetDeviceCaps(dc,HORZRES)==640 && GetDeviceCaps(dc,VERTRES)==400);
 vseg=GetPrivateProfileInt("test","vseg",0,"C:\\SPTEST.INI");if(!vseg)vseg=(WORD)((*(BYTE FAR *)0x0040008aL & 6)<<10);line("VIDEO_SEG",vseg);
 do{r=ShowCursor(FALSE);hidden++;}while(r>=0 && hidden<32);while(r < -1){r=ShowCursor(TRUE);hidden--;}SetCursor(0);
 for(i=0;i<16;i++)brushes[i]=CreateSolidBrush(colors[i]);
 for(y=0;y<400;y+=8)for(x=0;x<640;x+=32)fill(x,y,x+32,y+8,((y>>3)+(x>>5))&15);
 pan(0,0);shot();pan(8,0);shot();pan(320,0);shot();pan(320,4);shot();pan(320,200);shot();pan(0,200);shot();pan(160,100);shot();pan(0,0);shot();
 require("CLAMP_LOW",1);pan(-2,-4);require("LOW",px==0&&py==0);pan(32767,32767);require("HIGH",px==320&&py==200);pan(319,199);require("ALIGN",px==312&&py==196);
 /* Full-width and cross-band GDI writes are followed by pixel readback. */
 fill(300,190,350,220,15);require("BAND_TOP",GetPixel(dc,320,199)==colors[15]);require("BAND_BOTTOM",GetPixel(dc,320,200)==colors[15]);
 info8.h.biSize=40;info8.h.biWidth=8;info8.h.biHeight=2;info8.h.biPlanes=1;info8.h.biBitCount=8;info8.h.biCompression=BI_RGB;info8.h.biSizeImage=16;info8.h.biClrUsed=0;
 info8.c[255].rgbRed=info8.c[255].rgbGreen=info8.c[255].rgbBlue=255;for(i=0;i<16;i++)data8[i]=255;
 require("DIB8",SetDIBitsToDevice(dc,400,199,8,2,0,0,0,2,data8,(BITMAPINFO FAR *)&info8,DIB_RGB_COLORS)==2);
 require("DIB8_TOP",GetPixel(dc,400,199)==colors[15]);require("DIB8_BOTTOM",GetPixel(dc,400,200)==colors[15]);
 require("COPY",BitBlt(dc,500,300,50,30,dc,300,190,SRCCOPY));require("COPY_READ",GetPixel(dc,520,310)==colors[15]);
 fill(0,0,640,400,0);fill(300,190,350,220,15);pan(304,192);shot();
 cur=LoadCursor(0,IDC_ARROW);require("CURSOR",cur!=0);SetCursor(cur);SetCursorPos(320,200);line("CURSOR_SHOW",ShowCursor(TRUE));shot();line("CURSOR_HIDE",ShowCursor(FALSE));shot();
 before=GetFreeSpace(0);for(i=0;i<16;i++){pan(320,200);pan(0,0);}line("FREE_PAN_DELTA",(LONG)GetFreeSpace(0)-(LONG)before);
 for(i=0;i<16;i++)DeleteObject(brushes[i]);SetCursor(0);while(hidden-->0)ShowCursor(TRUE);ReleaseDC(0,dc);line("COMPLETE",1);_lclose(logf);return 0;
}
