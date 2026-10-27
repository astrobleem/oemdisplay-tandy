/* Native DIB-only checks; inserted into the existing SCENE probe. */
#include <dos.h>
struct DIBINFO16 { BITMAPINFOHEADER h; RGBQUAD c[16]; };
static struct DIBINFO16 dinfo,dout;
static BYTE din[2048],dgot[2048];
static COLORREF dcolors[16]={RGB(0,0,0),RGB(0,0,128),RGB(0,128,0),
 RGB(0,128,128),RGB(128,0,0),RGB(128,0,128),RGB(128,128,0),
 RGB(128,128,128),RGB(64,64,64),RGB(0,0,255),RGB(0,255,0),
 RGB(0,255,255),RGB(255,0,0),RGB(255,0,255),RGB(255,255,0),RGB(255,255,255)};
static int DIndex(int x,int y,int h,int pattern) {
 if(pattern==0)return ((x/8)+y)&15;
 if(pattern==1)return ((x+y)&1)?10:3;
 if(pattern==3)return (x&1)?(((h-1-y)*3+2)&15):((h-1-y+5)&15);
 return (x*3+y*5)&15;
}
static COLORREF DColor(int x,int y,int h,int pattern) {
 int v;v=DIndex(x,y,h,pattern);
 return RGB(dinfo.c[v].rgbRed,dinfo.c[v].rgbGreen,dinfo.c[v].rgbBlue);
}
static void DInfo(struct DIBINFO16 *p,int w,int h,int perm) {
 int i,v;memset(p,0,sizeof(*p));p->h.biSize=40L;p->h.biWidth=w;
 p->h.biHeight=h;p->h.biPlanes=1;p->h.biBitCount=4;
 p->h.biSizeImage=(DWORD)(((w*4+31)/32)*4)*h;p->h.biClrUsed=16;
 for(i=0;i<16;i++){v=perm?((i*5+3)&15):i;
  p->c[i].rgbRed=GetRValue(dcolors[v]);p->c[i].rgbGreen=GetGValue(dcolors[v]);
  p->c[i].rgbBlue=GetBValue(dcolors[v]);}
}
static void DCase(HDC dc,HDC mem,int w,int h,int pattern,int perm,int crossing,int bench) {
 HBITMAP bm,old;HGLOBAL big;BYTE __huge *hp;LPSTR source,target;void FAR *locked;
 int x,y,row,pitch,n,i,v,r,badset,badget,badguard;DWORD begin,end;unsigned seg,off;
 bm=0;big=0;hp=0;old=0;badset=badget=badguard=0;
 pitch=((w*4+31)/32)*4;n=pitch*h;DInfo(&dinfo,w,h,perm);
 memset(din,0xa5,sizeof(din));memset(dgot,0xa5,sizeof(dgot));
 for(y=0;y<h;y++)for(x=0;x<w;x++){
  row=h-1-y;i=row*pitch+x/2;v=DIndex(x,y,h,pattern);
  if(x&1)din[i]=(BYTE)((din[i]&0xf0)|v);else din[i]=(BYTE)((din[i]&15)|(v<<4));
 }
 if(pattern==3){n=0;for(row=0;row<h;row++){
  din[n++]=(BYTE)w;din[n++]=(BYTE)(((row+5)&15)*16+((row*3+2)&15));
  din[n++]=0;din[n++]=0;}din[n++]=0;din[n++]=1;
  dinfo.h.biCompression=BI_RLE4;dinfo.h.biSizeImage=n;
 }
 source=(LPSTR)din;target=(LPSTR)dgot;
 if(crossing){
  Check("DIB_HUGE_CAP",n+32<=528);if(n+32>528)goto cleanup;
  big=GlobalAlloc(GMEM_MOVEABLE,66048L);Check("DIB_HUGE_ALLOC",big!=0);if(!big)goto cleanup;
  locked=GlobalLock(big);Check("DIB_HUGE_LOCK",locked!=0);if(!locked)goto cleanup;
  hp=(BYTE __huge *)locked;seg=FP_SEG(locked)+(FP_OFF(locked)>>4);
  off=(unsigned)(0xfff0U+(FP_OFF(locked)&15));source=(LPSTR)MAKELONG(off,seg);target=source;
  for(i=0;i<n+32;i++)hp[65520L+i]=din[i];
 }
 bm=CreateCompatibleBitmap(dc,w,h);Check("DIB_BITMAP",bm!=0);if(!bm)goto cleanup;
 r=SetDIBits(dc,bm,0,h,source,(LPBITMAPINFO)&dinfo,DIB_RGB_COLORS);
 Check("DIB_SET_ROWS",r==h);old=SelectObject(mem,bm);
 for(y=0;y<h;y++)for(x=0;x<w;x++)if(GetPixel(mem,x,y)!=DColor(x,y,h,pattern))badset++;
 SelectObject(mem,old);old=0;
 if(crossing)for(i=0;i<pitch*h+32;i++)hp[65520L+i]=0xa5;
 DInfo(&dout,w,h,0);r=GetDIBits(dc,bm,0,h,target,(LPBITMAPINFO)&dout,DIB_RGB_COLORS);
 Check("DIB_GET_ROWS",r==h);
 if(crossing)for(i=0;i<pitch*h+32;i++)dgot[i]=hp[65520L+i];
 for(y=0;y<h;y++)for(x=0;x<w;x++){
  i=(h-1-y)*pitch+x/2;v=(x&1)?(dgot[i]&15):(dgot[i]>>4);
  if(RGB(dout.c[v].rgbRed,dout.c[v].rgbGreen,dout.c[v].rgbBlue)!=DColor(x,y,h,pattern))badget++;
 }
 for(i=pitch*h;i<pitch*h+32;i++)if(dgot[i]!=0xa5)badguard++;
 wsprintf(line,"DIB w=%d h=%d pattern=%d perm=%d cross=%d setbad=%d getbad=%d guardbad=%d\r\n",w,h,pattern,perm,crossing,badset,badget,badguard);Log(line);
 Check("DIB_SET_PIXELS",badset==0);Check("DIB_GET_PIXELS",badget==0);Check("DIB_GUARD",badguard==0);
 if(bench){
  begin=GetTickCount();for(i=0;i<64;i++)if(SetDIBits(dc,bm,0,h,source,(LPBITMAPINFO)&dinfo,DIB_RGB_COLORS)!=h)badset++;end=GetTickCount();
  wsprintf(line,"DIBBENCH dir=SET calls=64 ms=%lu\r\n",end-begin);Log(line);
  begin=GetTickCount();for(i=0;i<64;i++)if(GetDIBits(dc,bm,0,h,target,(LPBITMAPINFO)&dout,DIB_RGB_COLORS)!=h)badget++;end=GetTickCount();
  wsprintf(line,"DIBBENCH dir=GET calls=64 ms=%lu\r\n",end-begin);Log(line);
  Check("DIB_BENCH_RETURNS",badset==0 && badget==0);
 }
cleanup:
 if(old)SelectObject(mem,old);if(bm)DeleteObject(bm);
 if(big){if(hp)GlobalUnlock(big);GlobalFree(big);}
}
static void DibTests(void) {
 HDC dc,mem;int i;static int widths[8]={1,7,8,9,15,16,17,37};
 dc=GetDC(mainWnd);mem=CreateCompatibleDC(dc);Check("DIB_DC",mem!=0);
 if(mem){for(i=0;i<8;i++)DCase(dc,mem,widths[i],3,i%3,i&1,0,0);
  DCase(dc,mem,37,11,2,1,1,0);DCase(dc,mem,37,11,3,1,0,0);
  DCase(dc,mem,80,32,0,1,0,1);DeleteDC(mem);}
 ReleaseDC(mainWnd,dc);
}
