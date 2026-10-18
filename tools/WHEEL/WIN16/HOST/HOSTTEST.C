#define WHEEL_HOST 1
#include "../SOURCE/WXTWHL.C"
struct win {char *name;DWORD style;HWND parent;HANDLE prop;int top,total,selection,visible,enabled,iconic,width,height;};
static struct win wins[16];
static HWND hostFocus,hostActive,hostCapture,hostModal;
static DWORD hostTime;
static int posts,postCapacity=8,sends,readCount,reenter,failures;
static HWND lastReceiver;
static UINT lastMessage;
static WPARAM lastWp;
static LPARAM lastLp;
static int raw[32],rawHead,rawTail;
static int readraw(void){++readCount;return rawHead==rawTail?0:raw[rawHead++];}
#define CHECK(n,x) do{if(!(x)){printf("FAIL %s line %d\n",n,__LINE__);++failures;}else printf("PASS %s\n",n);}while(0)
static void reset(void){int i;memset(wins,0,sizeof(wins));memset(stats,0,sizeof(stats));head=tail=0;busy=blocked=0;
 hostTime=100;hostActive=hostFocus=1;lastActive=lastFocus=1;lastTick=lastDos=hostTime;hostCapture=hostModal=0;
 rawHead=rawTail=posts=sends=readCount=reenter=0;postCapacity=8;wheelRead=readraw;wheelLost=0;wheelMessage=0xc100;
 for(i=1;i<16;++i){wins[i].visible=wins[i].enabled=1;wins[i].name="BUTTON";wins[i].total=100;wins[i].width=12;wins[i].height=35;}
 wins[1].style=WS_VSCROLL;wins[1].name="Document";
}
int main(void){HWND r,b;int i,ok=1;
 reset();push(1);tick();CHECK("window_notification",posts==2&&lastReceiver==1&&lastMessage==WM_VSCROLL&&lastWp==SB_ENDSCROLL&&lastLp==0&&stats[ST_UNITS]==1);
 reset();wins[2].parent=1;wins[2].style=WS_CHILD|SBS_VERT;wins[2].name="SCROLLBAR";hostFocus=lastFocus=2;
 CHECK("child_scrollbar_route",target(2,1,&r,&b)==2&&r==1&&b==2);push(-1);tick();CHECK("win16_child_handle_highword",posts==2&&lastLp==MAKELONG(0,2));
 wins[2].style=WS_CHILD;CHECK("win30_scrollbar_cleared_style",target(2,1,&r,&b)==2);wins[2].width=35;wins[2].height=12;CHECK("horizontal_scrollbar_excluded",!target(2,1,&r,&b));wins[2].height=35;CHECK("square_scrollbar_excluded",!target(2,1,&r,&b));
 reset();wins[2].parent=3;wins[2].style=WS_CHILD;wins[3].parent=1;wins[3].style=WS_CHILD|WS_VSCROLL;
 CHECK("nearest_scrollable_ancestor",target(2,1,&r,&b)==1&&r==3);
 reset();wins[2].parent=1;wins[2].style=WS_CHILD|ES_MULTILINE;wins[2].name="EDIT";hostFocus=lastFocus=2;push(-3);tick();
 CHECK("edit_vertical_lowword",sends==1&&lastMessage==EM_LINESCROLL&&lastWp==0&&lastLp==MAKELONG(-3,0));
 reset();wins[2].parent=1;wins[2].style=WS_CHILD;wins[2].name="LISTBOX";wins[2].top=0;wins[2].selection=7;hostFocus=lastFocus=2;push(4);tick();
 CHECK("list_scroll_preserves_selection",wins[2].top==4&&wins[2].selection==7);push(-8);tick();CHECK("list_top_clamps",wins[2].top==0);
 reset();wins[2].parent=1;wins[2].style=WS_CHILD;wins[2].name="COMBOBOX";CHECK("combo_no_parent_spill",!target(2,1,&r,&b));
 reset();wins[2].parent=1;wins[2].style=WS_CHILD;wins[2].name="EDIT";CHECK("single_line_edit_excluded",!target(2,1,&r,&b));
 reset();for(i=0;i<40;++i)push(1);CHECK("ring_31_drop_newest",count()==31&&stats[ST_DROP]==9&&stats[ST_HIGH]==31);
 reset();postCapacity=0;push(1);tick();CHECK("full_application_queue_retains_input",count()==1&&posts==0);postCapacity=8;tick();CHECK("post_retry_next_turn",count()==0&&stats[ST_UNITS]==1);
 reset();push(7);hostFocus=2;wins[2].parent=1;wins[2].style=WS_CHILD;tick();CHECK("target_change_discards",count()==0&&posts==0);
 reset();push(2);hostCapture=1;tick();CHECK("capture_discards",count()==0&&posts==0);
 reset();push(2);hostModal=1;tick();CHECK("modal_discards",count()==0&&posts==0);
 reset();push(2);wins[1].iconic=1;tick();CHECK("minimized_discards",count()==0&&posts==0);
 reset();wins[8].name="WindowsXTToiletPaper";push(1);tick();CHECK("legacy_tp_no_driver_reads",readCount==0&&stats[ST_READY]==0);
 reset();wins[2].name="WindowsXTToiletPaper";wins[2].prop=BRIDGE_VERSION;hostFocus=hostActive=lastFocus=lastActive=2;push(1);push(-1);tick();
 CHECK("native_client_exclusive_order",sends==2&&posts==0&&stats[ST_UNITS]==2&&lastMessage==wheelMessage&&lastWp==(WPARAM)-1&&lastLp==1);
 reset();wins[1].prop=BRIDGE_VERSION;wins[2].parent=1;wins[2].name="EDIT";wins[2].style=WS_CHILD|ES_MULTILINE;hostFocus=lastFocus=2;push(1);tick();CHECK("opted_in_app_owns_child_focus",sends==1&&posts==0&&lastReceiver==1&&lastMessage==wheelMessage);
 reset();wins[2].parent=1;wins[2].name="EDIT";wins[2].style=WS_CHILD|ES_MULTILINE;hostFocus=lastFocus=2;push(1);reenter=1;tick();CHECK("reentrant_tick_guard",stats[ST_REENTRY]==1&&sends==1);
 reset();push(2);hostTime=1000;tick();CHECK("long_gap_discards",count()==0&&posts==0);
 reset();blocked=1;raw[0]=5;rawTail=1;push(1);tick();CHECK("new_ownership_discards_old_packets",count()==0&&rawHead==1&&posts==0&&stats[ST_READY]==0);
 reset();tick();CHECK("idle_one_read",readCount==1&&posts==0&&sends==0);
 reset();srand(7);for(i=0;i<100000;++i){
  if(rand()&1)push((rand()%16)-8);
  else {posts=0;postCapacity=(rand()%5)?8:0;hostTime+=100;tick();}
  if(count()>31||head>31||tail>31||stats[ST_HIGH]>31||posts>2){ok=0;break;}
 }CHECK("100000_bounded_queue_steps",ok);
 printf("FAILURES=%d\n",failures);return failures?1:0;
}
HWND FindWindow(char *name,char *title){int i;(void)title;for(i=1;i<16;++i)if(!strcmp(wins[i].name,name))return (HWND)i;return 0;}
HANDLE GetProp(HWND w,char *p){(void)p;return wins[w].prop;}BOOL IsWindow(HWND w){return w>0&&w<16;}BOOL IsIconic(HWND w){return wins[w].iconic;}BOOL IsWindowVisible(HWND w){return wins[w].visible;}BOOL IsWindowEnabled(HWND w){return wins[w].enabled;}
HWND GetSysModalWindow(void){return hostModal;}HWND GetCapture(void){return hostCapture;}BOOL IsChild(HWND a,HWND w){while(w&&w!=a)w=wins[w].parent;return w==a;}
HWND GetWindow(HWND w,int type){(void)w;(void)type;return 0;}HMODULE GetModuleHandle(char *n){(void)n;return 0;}
LONG GetWindowLong(HWND w,int i){(void)i;return (LONG)wins[w].style;}int GetClassName(HWND w,char *out,int n){strncpy(out,wins[w].name,(size_t)n);out[n-1]=0;return (int)strlen(out);}HWND GetParent(HWND w){return wins[w].parent;}
void GetScrollRange(HWND w,int b,int *lo,int *hi){(void)w;(void)b;*lo=0;*hi=100;}HWND GetFocus(void){return hostFocus;}HWND GetActiveWindow(void){return hostActive;}DWORD GetTickCount(void){return hostTime;}
void GetWindowRect(HWND w,RECT *r){r->left=r->top=0;r->right=wins[w].width;r->bottom=wins[w].height;}
void _dos_gettime(struct dostime_t *t){t->hour=(unsigned char)((hostTime/3600000)%24);t->minute=(unsigned char)((hostTime/60000)%60);t->second=(unsigned char)((hostTime/1000)%60);t->hsecond=(unsigned char)((hostTime%1000)/10);}
int lstrcmpi(char *a,char *b){return strcmp(a,b);}
LONG SendMessage(HWND w,UINT m,WPARAM p,LPARAM l){if(m==LB_GETTOPINDEX)return wins[w].top;if(m==LB_GETCOUNT)return wins[w].total;if(m==LB_SETTOPINDEX)wins[w].top=p;
 ++sends;lastReceiver=w;lastMessage=m;lastWp=p;lastLp=l;if(reenter){reenter=0;tick();}return 0;}
BOOL PostMessage(HWND w,UINT m,WPARAM p,LPARAM l){if(posts>=postCapacity)return 0;++posts;lastReceiver=w;lastMessage=m;lastWp=p;lastLp=l;return 1;}
void DestroyWindow(HWND w){(void)w;}void KillTimer(HWND w,UINT n){(void)w;(void)n;}void RemoveProp(HWND w,char *p){(void)w;(void)p;}void PostQuitMessage(int i){(void)i;}LONG DefWindowProc(HWND w,UINT m,WPARAM p,LPARAM l){(void)w;(void)m;(void)p;(void)l;return 0;}
int MessageBox(HWND w,char *text,char *title,UINT flags){(void)w;(void)text;(void)title;(void)flags;return 1;}
FARPROC GetProcAddress(HMODULE m,char *n){(void)m;(void)n;return 0;}WORD RegisterWindowMessage(char *n){(void)n;return 0xc100;}FARPROC MakeProcInstance(FARPROC p,HINSTANCE i){(void)i;return p;}
BOOL RegisterClass(WNDCLASS *w){(void)w;return 1;}HWND CreateWindow(char *a,char *b,DWORD c,int d,int e,int f,int g,HWND h,HANDLE i,HINSTANCE j,void *k){(void)a;(void)b;(void)c;(void)d;(void)e;(void)f;(void)g;(void)h;(void)i;(void)j;(void)k;return 1;}
WORD SetTimer(HWND w,UINT a,UINT b,void *p){(void)w;(void)a;(void)b;(void)p;return 1;}BOOL SetProp(HWND w,char *p,HANDLE v){(void)p;wins[w].prop=v;return 1;}BOOL GetMessage(MSG *m,HWND w,UINT a,UINT b){(void)m;(void)w;(void)a;(void)b;return 0;}
void TranslateMessage(MSG *m){(void)m;}void DispatchMessage(MSG *m){(void)m;}void FreeProcInstance(FARPROC p){(void)p;}
