#include "TDROP.H"
#define ACCEPT "Tandy.FileDrop.1"
typedef struct { WORD offset; POINT pt; BOOL nc; } TDHEAD;
/* Every query validates the entire bounded ANSI list before copying anything. */
static BOOL valid(LPSTR p,UINT n) {
 UINT i,start,count=0;
 if(n<10 || n>TD_MAX || ((TDHEAD FAR *)p)->offset!=8)return FALSE;
 i=8;
 if(!p[i])return p[i+1]==0;
 for(;;){
  start=i;
  while(i<n && p[i])i++;
  if(i==n || i-start>127 || i-start<3 || p[start+1]!=':' || p[start+2]!='\\')return FALSE;
  if(++count>16)return FALSE;
  if(++i>=n)return FALSE;
  if(!p[i])return TRUE;
 }
}
BOOL FAR PASCAL TDValid(HGLOBAL h) {
 DWORD n; LPSTR p; BOOL ok;
 n=GlobalSize(h);if(n>TD_MAX || n<10)return FALSE;
 p=GlobalLock(h);if(!p)return FALSE;
 ok=valid(p,(UINT)n);GlobalUnlock(h);return ok;
}
BOOL FAR PASCAL TDDragAcceptFiles(HWND w,BOOL yes) {
 if(!IsWindow(w))return FALSE;
 if(yes)return SetProp(w,ACCEPT,(HANDLE)1);
 RemoveProp(w,ACCEPT);return TRUE;
}
UINT FAR PASCAL TDDragQueryFile(HGLOBAL h,UINT index,LPSTR out,UINT cap) {
 LPSTR p;UINT i=8,k=0,start,len,j;DWORD n=GlobalSize(h);
 if(out && cap)out[0]=0;
 if(n>TD_MAX || n<10)return 0;
 p=GlobalLock(h);if(!p)return 0;
 if(!valid(p,(UINT)n)){GlobalUnlock(h);return 0;}
 while(p[i]){start=i;while(p[i])i++;len=i-start;
  if(k==index){if(out && cap){j=len;if(j>=cap)j=cap-1;while(j){j--;out[j]=p[start+j];}out[(len<cap)?len:cap-1]=0;}GlobalUnlock(h);return (out && cap && len>=cap)?cap-1:len;}
  k++;i++;
 }
 GlobalUnlock(h);return index==0xffff?k:0;
}
BOOL FAR PASCAL TDDragQueryPoint(HGLOBAL h,LPPOINT pt) {
 TDHEAD FAR *p;BOOL client;
 if(!pt || !TDValid(h))return FALSE;
 p=(TDHEAD FAR *)GlobalLock(h);if(!p)return FALSE;
 *pt=p->pt;client=!p->nc;GlobalUnlock(h);return client;
}
void FAR PASCAL TDDragFinish(HGLOBAL h) {GlobalFree(h);}
HWND FAR PASCAL TDTarget(POINT pt) {
 HWND w=WindowFromPoint(pt);
 while(w){if(IsWindowEnabled(w) && GetProp(w,ACCEPT))return w;w=GetParent(w);}return NULL;
}
HGLOBAL FAR PASCAL TDPack(LPCSTR list,UINT bytes,POINT pt,BOOL nc) {
 HGLOBAL h;LPSTR p;UINT i;
 if(!list || bytes<2 || bytes>TD_MAX-8)return NULL;
 h=GlobalAlloc(GMEM_MOVEABLE|GMEM_DDESHARE|GMEM_ZEROINIT,(DWORD)bytes+8);
 if(!h)return NULL;
 p=GlobalLock(h);if(!p){GlobalFree(h);return NULL;}
 ((TDHEAD FAR *)p)->offset=8;((TDHEAD FAR *)p)->pt=pt;((TDHEAD FAR *)p)->nc=nc;
 for(i=0;i<bytes;i++)p[8+i]=list[i];
 if(!valid(p,bytes+8)){GlobalUnlock(h);GlobalFree(h);return NULL;}
 GlobalUnlock(h);return h;
}
BOOL FAR PASCAL TDPost(HWND w,HGLOBAL h) {
 /* No yield between final target check and post. Failure leaves caller ownership. */
 if(!TDValid(h) || !IsWindow(w) || !GetProp(w,ACCEPT))return FALSE;
 return PostMessage(w,WM_DROPFILES,(WPARAM)h,0L);
}
