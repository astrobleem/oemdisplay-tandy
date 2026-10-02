#define WINVER 0x0300
#include <windows.h>
#define W 64
#define H 16
struct INFO16 { BITMAPINFOHEADER h; RGBQUAD c[16]; };
static struct INFO16 info, query, synth;
static BYTE bits[4096], raw[4096], sbits[512];
static HFILE logFile;
static COLORREF colors[16]={
 RGB(0,0,0), RGB(0,0,128), RGB(0,128,0), RGB(0,128,128),
 RGB(128,0,0), RGB(128,0,128), RGB(128,128,0), RGB(128,128,128),
 RGB(64,64,64), RGB(0,0,255), RGB(0,255,0), RGB(0,255,255),
 RGB(255,0,0), RGB(255,0,255), RGB(255,255,0), RGB(255,255,255)
};
static void line(char *key, LONG value)
{
 char out[100],digits[12]; int n=0,d=0; DWORD v;
 while(*key)out[n++]=*key++;out[n++]='=';
 if(value<0){out[n++]='-';v=(DWORD)(-value);}else v=(DWORD)value;
 do{digits[d++]=(char)('0'+v%10);v/=10;}while(v);
 while(d)out[n++]=digits[--d];out[n++]='\r';out[n++]='\n';
 _lwrite(logFile,out,n);
}
static void dump(char *name,void FAR *p,UINT n)
{
 HFILE f;f=_lcreat(name,0);if(f!=HFILE_ERROR){_lwrite(f,p,n);_lclose(f);}
}
static void fill(HDC dc,int l,int t,int r,int b,COLORREF c)
{
 HBRUSH br;RECT rc;rc.left=l;rc.top=t;rc.right=r;rc.bottom=b;
 br=CreateSolidBrush(c);FillRect(dc,&rc,br);DeleteObject(br);
}
static void init(struct INFO16 *p,int bpp)
{
 int i;BYTE *v=(BYTE *)p;
 for(i=0;i<sizeof(struct INFO16);i++)v[i]=0;
 p->h.biSize=40L;p->h.biWidth=W;p->h.biHeight=H;
 p->h.biPlanes=1;p->h.biBitCount=bpp;p->h.biCompression=BI_RGB;
 if(bpp) {p->h.biSizeImage=512L;p->h.biClrUsed=16L;}
 for(i=0;i<16;i++){
 p->c[i].rgbRed=GetRValue(colors[i]);
 p->c[i].rgbGreen=GetGValue(colors[i]);
 p->c[i].rgbBlue=GetBValue(colors[i]);}
}
static void savebmp(char *name,struct INFO16 *p,BYTE *b)
{
 BITMAPFILEHEADER fh;HFILE f;
 fh.bfType=0x4d42;fh.bfSize=630L;fh.bfReserved1=0;fh.bfReserved2=0;fh.bfOffBits=118L;
 f=_lcreat(name,0);if(f==HFILE_ERROR)return;
 _lwrite(f,&fh,sizeof(fh));_lwrite(f,p,104);_lwrite(f,b,512);_lclose(f);
}
int PASCAL WinMain(HINSTANCE inst,HINSTANCE prev,LPSTR cmd,int show)
{
 HDC dc,mem,mem2;HBITMAP bm,bm2,bm3,old,old2;BITMAP obj;int i,x,y,r,hidden;
 logFile=_lcreat("C:\\ROUND.LOG",0);if(logFile==HFILE_ERROR)return 1;
 line("VERSION",1);dc=GetDC(NULL);
 line("HORZRES",GetDeviceCaps(dc,HORZRES));line("VERTRES",GetDeviceCaps(dc,VERTRES));
 line("BITSPIXEL",GetDeviceCaps(dc,BITSPIXEL));line("PLANES",GetDeviceCaps(dc,PLANES));line("NUMCOLORS",GetDeviceCaps(dc,NUMCOLORS));
 mem=CreateCompatibleDC(dc);bm=CreateCompatibleBitmap(dc,W,H);
 line("CCDC",mem!=NULL);line("CCBM",bm!=NULL);
 line("GETOBJECT",GetObject(bm,sizeof(obj),&obj));
 line("BM_TYPE",obj.bmType);line("BM_WIDTH",obj.bmWidth);line("BM_HEIGHT",obj.bmHeight);
 line("BM_WIDTHBYTES",obj.bmWidthBytes);line("BM_PLANES",obj.bmPlanes);line("BM_BITSPIXEL",obj.bmBitsPixel);
 old=SelectObject(mem,bm);line("SELECT",old!=NULL);
 for(i=0;i<16;i++)fill(mem,i*4,0,i*4+4,H,colors[i]);
 for(i=0;i<16;i++){line("SOURCE_INDEX",i);line("SOURCE_PIXEL",GetPixel(mem,i*4+1,8));}
 for(i=0;i<4096;i++){bits[i]=0xa5;raw[i]=0xa5;}
 line("GETBITS_START",1);line("GETBITS",GetBitmapBits(bm,4096L,raw));dump("C:\\ROUNDDDB.BIN",raw,4096);
 SelectObject(mem,old);
 init(&query,0);line("QUERY_START",1);r=GetDIBits(dc,bm,0,H,NULL,(LPBITMAPINFO)&query,DIB_RGB_COLORS);
 line("QUERY_RETURN",r);line("Q_BITS",query.h.biBitCount);line("Q_PLANES",query.h.biPlanes);line("Q_SIZE",query.h.biSizeImage);line("Q_COLORS",query.h.biClrUsed);dump("C:\\ROUNDQ.BIN",&query,sizeof(query));
 init(&info,4);line("GETDIB_START",1);r=GetDIBits(dc,bm,0,H,bits,(LPBITMAPINFO)&info,DIB_RGB_COLORS);
 line("GETDIB_RETURN",r);line("DIB_BITS",info.h.biBitCount);line("DIB_PLANES",info.h.biPlanes);line("DIB_SIZE",info.h.biSizeImage);line("DIB_COLORS",info.h.biClrUsed);
 dump("C:\\ROUNDDIB.BIN",bits,4096);dump("C:\\ROUNDINF.BIN",&info,sizeof(info));savebmp("C:\\ROUND.BMP",&info,bits);
 init(&synth,4);for(y=0;y<H;y++)for(x=0;x<W/2;x++)sbits[y*32+x]=(BYTE)((x/2)*17);
 savebmp("C:\\ROUNDSYN.BMP",&synth,sbits);
 hidden=0;do{r=ShowCursor(FALSE);hidden++;}while(r>=0 && hidden<32);SetCursor(NULL);
 fill(dc,0,0,GetDeviceCaps(dc,HORZRES),GetDeviceCaps(dc,VERTRES),RGB(64,64,64));
 old=SelectObject(mem,bm);line("SOURCE_BLT",BitBlt(dc,16,8,W,H,mem,0,0,SRCCOPY));
 line("DIB_TO_DC_START",1);line("DIB_TO_DC",SetDIBitsToDevice(dc,16,40,W,H,0,0,0,H,bits,(LPBITMAPINFO)&info,DIB_RGB_COLORS));
 line("SYN_TO_DC",SetDIBitsToDevice(dc,16,72,W,H,0,0,0,H,sbits,(LPBITMAPINFO)&synth,DIB_RGB_COLORS));
 bm2=CreateCompatibleBitmap(dc,W,H);mem2=CreateCompatibleDC(dc);
 line("SETDIB_START",1);line("SETDIB",SetDIBits(dc,bm2,0,H,sbits,(LPBITMAPINFO)&synth,DIB_RGB_COLORS));
 old2=SelectObject(mem2,bm2);line("SETDIB_BLT",BitBlt(dc,16,104,W,H,mem2,0,0,SRCCOPY));
 for(i=0;i<16;i++){line("RESTORED_INDEX",i);line("RESTORED_PIXEL",GetPixel(mem2,i*4+1,8));}
 bm3=CreateDIBitmap(dc,&synth.h,CBM_INIT,sbits,(LPBITMAPINFO)&synth,DIB_RGB_COLORS);
 line("CREATEDIB",bm3!=NULL);if(bm3){
 line("DIBOBJECT",GetObject(bm3,sizeof(obj),&obj));
 line("DBM_WIDTHBYTES",obj.bmWidthBytes);line("DBM_PLANES",obj.bmPlanes);line("DBM_BITSPIXEL",obj.bmBitsPixel);
 SelectObject(mem2,bm3);line("CREATEDIB_BLT",BitBlt(dc,16,136,W,H,mem2,0,0,SRCCOPY));
 SelectObject(mem2,bm2);DeleteObject(bm3);}
 dump("C:\\ROUNDVRM.BIN",(void FAR *)0xb8000000L,32768U);
 line("COMPLETE",1);_lclose(logFile);
 MessageBox(NULL,"Bitmap probe complete","ROUND",MB_OK);
 SelectObject(mem2,old2);DeleteObject(bm2);DeleteDC(mem2);
 SelectObject(mem,old);DeleteObject(bm);DeleteDC(mem);ReleaseDC(NULL,dc);
 while(hidden>0){ShowCursor(TRUE);hidden--;}
 return 0;
}
