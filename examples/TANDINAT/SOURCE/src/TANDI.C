#define WINVER 0x0300
#include <windows.h>
#include <string.h>
#include "TANDI.H"
#include "ART.H"
/* Full-screen client, no standard dialogs. All calculations are outside paint. */
static TDB db;
static ENGINE engine;
static HWND window;
static HINSTANCE instance;
static int screenw,screenh,mono,state,focus,debug,help,busy,testmode;
static int lookx,looky,eyeupdates,sx,colors,active=1,artblits;
static HDC artdc;
static HBITMAP artbmp,oldart;
static DWORD artms;
static struct { BITMAPINFOHEADER h; RGBQUAD c[16]; } artinfo;
/* Driver logical RGB entries intentionally differ from RGBI display values.
   This preserves the source sheet's exact 0..15 hardware color indices. */
static unsigned char rgb[16][3]={{0,0,0},{0,0,128},{0,128,0},{0,128,128},
 {128,0,0},{128,0,128},{128,128,0},{128,128,128},{64,64,64},
 {0,0,255},{0,255,0},{0,255,255},{255,0,0},{255,0,255},
 {255,255,0},{255,255,255}};
static unsigned char monomap[16]={0,0,0,15,0,0,0,15,0,0,15,15,15,15,15,15};
static unsigned char lowmap[16]={0,0,10,10,12,12,12,15,0,0,10,10,12,12,15,15};
static int errors,teststep,wrongguess,finished,testtarget,verified,testinside;
static RECT buttons[6];
static int ids[6],nb;
static char labels[6][24],question[80],name[40],line[100],dbpath[144];
static char debugline[10][80];
static DWORD loadms,answerms,selectms,freespace;
static HFILE logfile=-1;
static U8 truth[TD_ROW];
static char *answers[5]={"1  YES","2  PROBABLY","3  DON'T KNOW",
                             "4  PROBABLY NOT","5  NO"};
static void number(char *s,long n){
    char reverse[16];int i=0,j=0;unsigned long u;
    if(n<0){s[j++]='-';u=(unsigned long)(-n);}else u=n;
    do{reverse[i++]=(char)('0'+u%10);u/=10;}while(u);
    while(i)s[j++]=reverse[--i];s[j]=0;
}
static void metric(char *key,long n){
    char s[120],v[20];if(logfile==-1)return;
    number(v,n);lstrcpy(s,key);lstrcat(s,"=");lstrcat(s,v);
    lstrcat(s,"\r\n");_lwrite(logfile,s,lstrlen(s));
}
static void logtext(char *key,char *s){
    if(logfile==-1)return;_lwrite(logfile,key,lstrlen(key));
    _lwrite(logfile,"=",1);_lwrite(logfile,s,lstrlen(s));
    _lwrite(logfile,"\r\n",2);
}
static void text(HDC dc,int x,int y,char *s){TextOut(dc,x,y,s,lstrlen(s));}
static void box(HDC dc,int x,int y,int w,int h,COLORREF color){
    RECT r;HBRUSH b;r.left=x;r.top=y;r.right=x+w;r.bottom=y+h;
    b=CreateSolidBrush(color);FillRect(dc,&r,b);DeleteObject(b);
}
static void frame(HDC dc,int x,int y,int w,int h){
    HBRUSH old;old=SelectObject(dc,GetStockObject(NULL_BRUSH));
    Rectangle(dc,x,y,x+w,y+h);SelectObject(dc,old);
}
static void centered(HDC dc,int y,char *s){
    RECT r;r.left=4;r.right=screenw-4;r.top=y;r.bottom=y+14;
    DrawText(dc,s,-1,&r,DT_CENTER|DT_SINGLELINE|DT_NOPREFIX);
}
static int panelleft(void){return 104*sx;}
static void artfree(void){
    if(artdc){SelectObject(artdc,oldart);DeleteDC(artdc);artdc=0;}
    if(artbmp){DeleteObject(artbmp);artbmp=0;}
}
static int artinit(HDC dc){
    HBITMAP native,old,scaled;HDC source;int i,j;DWORD start;
    start=GetTickCount(); /* Static DIB header begins zeroed; initialized once. */
    artinfo.h.biSize=sizeof(BITMAPINFOHEADER);artinfo.h.biWidth=ART_W;
    artinfo.h.biHeight=ART_H;artinfo.h.biPlanes=1;
    artinfo.h.biBitCount=4;artinfo.h.biSizeImage=sizeof(artbits);
    artinfo.h.biClrUsed=16;
    for(i=0;i<16;i++){
        j=i;
        if(colors==2)j=monomap[i];
        if(colors==4)j=lowmap[i];
        artinfo.c[i].rgbRed=rgb[j][0];artinfo.c[i].rgbGreen=rgb[j][1];
        artinfo.c[i].rgbBlue=rgb[j][2];
    }
    native=CreateDIBitmap(dc,&artinfo.h,CBM_INIT,artbits,(BITMAPINFO FAR *)&artinfo,DIB_RGB_COLORS);
    if(!native)return 0;
    artdc=CreateCompatibleDC(dc);if(!artdc){DeleteObject(native);return 0;}
    artbmp=native;oldart=SelectObject(artdc,artbmp);
    if(sx==2){
        source=CreateCompatibleDC(dc);scaled=CreateCompatibleBitmap(dc,ART_W*2,ART_H);
        if(!source||!scaled){if(source)DeleteDC(source);if(scaled)DeleteObject(scaled);artfree();return 0;}
        old=SelectObject(source,scaled);SetStretchBltMode(source,COLORONCOLOR);
        if(!StretchBlt(source,0,0,ART_W*2,ART_H,artdc,0,0,ART_W,ART_H,SRCCOPY)){
            SelectObject(source,old);DeleteDC(source);DeleteObject(scaled);artfree();return 0;}
        SelectObject(source,old);DeleteDC(source);SelectObject(artdc,oldart);
        DeleteObject(native);artbmp=scaled;SelectObject(artdc,artbmp);
    }
    artms=GetTickCount()-start;return 1;
}
static void sprite(HDC dc,int x,int y,int w,int h,int ax,int ay){
    if(artdc)BitBlt(dc,x,y,w*sx,h,artdc,ax*sx,ay,SRCCOPY);
}
static void ticket(HDC dc,char *s,int y,int h){
    RECT r;int left=panelleft(),width=screenw-left-4*sx;
    box(dc,left,y,width,h,colors<16?RGB(255,255,255):RGB(255,255,0));
    box(dc,left+sx,y+1,width-2*sx,h-2,RGB(255,255,255));
    r.left=left+2*sx;r.right=screenw-6*sx;r.top=y+5;r.bottom=y+h-3;
    SetTextColor(dc,RGB(0,0,0));SetBkColor(dc,RGB(255,255,255));
    DrawText(dc,s,-1,&r,DT_CENTER|DT_WORDBREAK|DT_NOPREFIX);
}
/* Native 3x6 pupil/shadow shapes, restricted to two white 7x9 patches. */
static void eyes(HDC dc){
    int x=6*sx,y=43;
    if(!artdc||state>1)return;
    box(dc,x+39*sx,y+42,7*sx,9,RGB(255,255,255));
    box(dc,x+47*sx,y+42,7*sx,9,RGB(255,255,255));
    sprite(dc,x+(42+lookx)*sx,y+44+looky,3,6,42,44);
    sprite(dc,x+(49+lookx)*sx,y+44+looky,3,6,49,44);
}
static void look(int x,int y){
    int nx,ny,cx=52*sx;HDC dc;
    nx=(x-cx)/(40*sx);ny=(y-90)/35;
    if(nx>1)nx=1;if(nx<-1)nx=-1;
    if(ny>1)ny=1;if(ny<-1)ny=-1;
    if(nx==lookx&&ny==looky)return;
    lookx=nx;looky=ny;
    if(help||debug||state>1||!active||!artdc)return;
    dc=GetDC(window);eyes(dc);ReleaseDC(window,dc);eyeupdates++;
}
static void mascot(HDC dc){
    int pose=state==2?1:(state==3?2:0);
    sprite(dc,6*sx,43,96,120,0,pose*120);artblits++;
    eyes(dc);
}
static void addbutton(int id,char *label,int x,int y,int w,int h){
    RECT *r=&buttons[nb];r->left=x;r->top=y;r->right=x+w;r->bottom=y+h;
    ids[nb]=id;lstrcpy(labels[nb],label);nb++;
}
static void layout(void){
    int i,left=panelleft(),width=screenw-left-4*sx;nb=0;
    if(help||debug){addbutton(90,"BACK (F1/F2)",left,163,width,16);}
    else if(state==0)addbutton(10,"BEGIN  [ENTER]",left,122,width,21);
    else if(state==1)for(i=0;i<5;i++)addbutton(i,answers[i],left,88+18*i,width,16);
    else if(state==2){
        addbutton(20,"YES!  [Y]",left,117,width,21);
        addbutton(21,"NO, TRY AGAIN [N]",left,144,width,21);
    }else if(state==3||state==4)addbutton(10,"PLAY AGAIN",left,126,width,23);
    addbutton(99,"EXIT",screenw-49,183,43,14);
    if(focus>=nb)focus=0;
}
static void draw(HWND w){
    PAINTSTRUCT ps;HDC dc;int i;RECT r;char temp[24];COLORREF gold;
    dc=BeginPaint(w,&ps);SetBkMode(dc,OPAQUE);
    SelectObject(dc,GetStockObject(SYSTEM_FIXED_FONT));
    box(dc,0,0,screenw,screenh,RGB(0,0,0));
    gold=colors<16?RGB(255,255,255):RGB(255,255,0);
    SetTextColor(dc,gold);SetBkColor(dc,RGB(0,0,0));
    if(artdc)sprite(dc,(screenw-126*sx)/2,4,126,16,0,360);
    else centered(dc,5,"TANDINATOR");
    centered(dc,22,help?"HOW TO CONSULT THE ORACLE":(debug?"THE ORACLE'S NOTES":"THE INCREDIBLE TANDY MIND READER"));
    box(dc,6*sx,35,screenw-12*sx,1,gold);
    box(dc,6*sx,179,screenw-12*sx,1,gold);
    SetTextColor(dc,RGB(255,255,255));
    if(debug||help){
        sprite(dc,screenw-55*sx,40,48,40,debug?48:0,376);
        if(debug){for(i=0;i<10;i++)text(dc,8*sx,43+i*11,debugline[i]);}
        else{
            text(dc,8*sx,45,"Think of someone in the roster.");
            text(dc,8*sx,61,"1 Yes  2 Probably  3 Don't know");
            text(dc,8*sx,74,"4 Probably not  5 No");
            text(dc,8*sx,90,"Tab changes focus. Enter chooses.");
            text(dc,8*sx,103,"F2 shows scores. Esc exits.");
            text(dc,8*sx,119,"Use common portrayals, not disguises.");
            text(dc,8*sx,132,"Unsure? Don't know is always fine.");
            text(dc,8*sx,145,"Offline. Answers are never saved.");
        }
    }else{
        r.left=6*sx;r.right=102*sx;r.top=43;r.bottom=163;
        if(RectVisible(dc,&r))mascot(dc);
        if(state==0){
            ticket(dc,"Think of a person or character. The silicon oracle awaits.",45,64);
        }else if(state==1){
            ticket(dc,question,42,42);
            number(temp,engine.turn+1);lstrcpy(line,"Q ");lstrcat(line,temp);
            SetTextColor(dc,gold);SetBkColor(dc,RGB(0,0,0));text(dc,34*sx,168,line);
        }else if(state==2){
            ticket(dc,"I SUSPECT...",46,20);ticket(dc,name,70,38);
        }else if(state==3){
            ticket(dc,"THE TANDINATOR KNOWS ALL!",48,32);
            number(temp,engine.turn);lstrcpy(line,"Questions asked: ");lstrcat(line,temp);ticket(dc,line,84,27);
        }else if(state==4){
            ticket(dc,db.error?"The crystal disk is clouded. Check TANDY.DAT beside this EXE.":
                  "You have stumped the silicon oracle! Try another character.",45,65);
        }
        if(!artdc){SetTextColor(dc,RGB(255,255,255));text(dc,8,85,"THE ORACLE");text(dc,8,100,"IS LISTENING");}
    }
    for(i=0;i<nb;i++){
        r=buttons[i];if(!RectVisible(dc,&r))continue;
        box(dc,r.left,r.top,r.right-r.left,r.bottom-r.top,gold);
        box(dc,r.left+sx,r.top+1,r.right-r.left-2*sx,r.bottom-r.top-2,RGB(255,255,255));
        SetTextColor(dc,RGB(0,0,0));SetBkColor(dc,RGB(255,255,255));
        r.top+=3;DrawText(dc,labels[i],-1,&r,DT_CENTER|DT_SINGLELINE|DT_NOPREFIX);
        if(i==focus){r=buttons[i];InflateRect(&r,-2,-2);DrawFocusRect(dc,&r);}
    }
    SetTextColor(dc,RGB(255,255,255));SetBkColor(dc,RGB(0,0,0));
    text(dc,8,186,busy?"CONSULTING...":"F1 HELP  F2 SCORES");EndPaint(w,&ps);
}
static void refresh(void){layout();InvalidateRect(window,0,FALSE);UpdateWindow(window);}
static void busyfooter(void){
    HDC dc;dc=GetDC(window);
    SelectObject(dc,GetStockObject(SYSTEM_FIXED_FONT));
    SetTextColor(dc,RGB(255,255,255));SetBkColor(dc,RGB(0,0,0));
    box(dc,8,182,screenw-61,16,RGB(0,0,0));
    text(dc,8,186,"CONSULTING...");ReleaseDC(window,dc);
}
static void questionrefresh(int previousfocus){
    RECT r;layout();
    if(previousfocus>=0&&previousfocus<nb)InvalidateRect(window,&buttons[previousfocus],FALSE);
    InvalidateRect(window,&buttons[0],FALSE);
    r.left=panelleft();r.right=screenw-4*sx;r.top=42;r.bottom=84;
    InvalidateRect(window,&r,FALSE);
    r.left=6*sx;r.right=102*sx;r.top=164;r.bottom=177;
    InvalidateRect(window,&r,FALSE);
    r.left=8;r.right=screenw-53;r.top=182;r.bottom=199;
    InvalidateRect(window,&r,FALSE);UpdateWindow(window);
}
static void capture(char *path){
    HFILE f;f=_lcreat(path,0);if(f!=-1){
        _lwrite(f,(const void FAR *)0xb8000000L,32768U);_lclose(f);
    }
}
static void debugupdate(void){
    int i,j,b,used[5];char nm[40],num[20];
    for(i=0;i<5;i++){
        b=-1;for(j=0;j<(int)db.nc;j++){
            int k,skip=engine.rejected[j];for(k=0;k<i;k++)if(used[k]==j)skip=1;
            if(!skip&&(b<0||engine.score[j]>engine.score[b]))b=j;
        }
        used[i]=b;debugline[i][0]=0;
        if(b>=0){db_name(&db,b,nm);number(num,engine.score[b]);
            lstrcpy(debugline[i],nm);lstrcat(debugline[i],"  ");lstrcat(debugline[i],num);}
    }
    lstrcpy(debugline[5],"Split Y/N/U: ");number(num,engine.yesw);
    lstrcat(debugline[5],num);lstrcat(debugline[5],"/");number(num,engine.now);
    lstrcat(debugline[5],num);lstrcat(debugline[5],"/");number(num,engine.unknownw);
    lstrcat(debugline[5],num);
    lstrcpy(debugline[6],"Utility: ");number(num,engine.utility);lstrcat(debugline[6],num);
    lstrcpy(debugline[7],"Load/answer/select ms: ");number(num,loadms);
    lstrcat(debugline[7],num);lstrcat(debugline[7],"/");number(num,answerms);
    lstrcat(debugline[7],num);lstrcat(debugline[7],"/");number(num,selectms);
    lstrcat(debugline[7],num);
    lstrcpy(debugline[8],"Rows examined: ");number(num,engine.examined);lstrcat(debugline[8],num);
    lstrcpy(debugline[9],"Emulator timing; not physical 8088.");
}
static void next(void){
    DWORD start;int previous=state,previousfocus=focus;busy=1;busyfooter();start=GetTickCount();
    if(eng_confident(&engine,&db)){state=2;db_name(&db,engine.best,name);}
    else if(eng_choose(&engine,&db)<0){
        state=(engine.best<0||db.error)?4:2;
        if(state==2)db_name(&db,engine.best,name);
    }else {state=1;db_question(&db,engine.current,question);}
    selectms=GetTickCount()-start;metric("SELECT_MS",selectms);
    metric("SAMPLE",engine.count);metric("ROWS",engine.examined);
    if(db.error)state=4;busy=0;focus=0;
    if(previous==1&&state==1&&engine.turn>0){
        previous=artblits;questionrefresh(previousfocus);
        metric("QUESTION_CABINET_UNTOUCHED",previous==artblits);
    }else refresh();
}
static void act(int id){
    DWORD start;if(busy)return;
    if(id==99){SendMessage(window,WM_CLOSE,0,0);return;}
    if(id==90){debug=help=0;refresh();return;}
    if(id==10){
        if(db.error){state=4;refresh();return;}
        eng_reset(&engine,&db);state=1;next();return;
    }
    if(id>=0&&id<5&&state==1){
        start=GetTickCount();
        if(!eng_answer(&engine,&db,4-id))state=4;
        answerms=GetTickCount()-start;metric("ANSWER_MS",answerms);
        if(state!=4)next();else refresh();return;
    }
    if(state==2&&id==20){state=3;refresh();return;}
    if(state==2&&id==21){eng_reject(&engine,&db);next();}
}
static void testtick(void){
    int answer,i,turnsaved,statesaved,lx,ly;char nm[40];RECT damage;HWND peer;HDC testdc;
    if(teststep==0){
        lx=lookx;ly=looky;lookx=looky=0;testdc=GetDC(window);eyes(testdc);
        capture("C:\\NATIVE.BIN");lookx=lx;looky=ly;eyes(testdc);ReleaseDC(window,testdc);
        capture("C:\\WELCOME.BIN");
        peer=CreateWindow("STATIC","TANDI focus check",WS_OVERLAPPEDWINDOW,
                          20,50,140,70,0,0,instance,0);
        if(peer){
            statesaved=state;turnsaved=engine.turn;ShowWindow(peer,SW_SHOW);UpdateWindow(peer);
            metric("FOCUS_OTHER_WINDOW",GetActiveWindow()==peer);
            SetActiveWindow(window);BringWindowToTop(window);UpdateWindow(window);
            SetActiveWindow(window);BringWindowToTop(window);DestroyWindow(peer);UpdateWindow(window);
            metric("FOCUS_RETURNED",GetActiveWindow()==window);
            metric("FOCUS_STATE_PRESERVED",state==statesaved&&engine.turn==turnsaved);
            capture("C:\\FOCUS.BIN");
        }
        damage.left=screenw-6;damage.top=100;
        damage.right=screenw-2;damage.bottom=120;
        InvalidateRect(window,&damage,FALSE);UpdateWindow(window);
        damage.left=100;damage.top=174;damage.right=125;damage.bottom=180;
        InvalidateRect(window,&damage,FALSE);UpdateWindow(window);
        capture("C:\\EXPOSE.BIN");
        look(0,0);capture("C:\\EYELEFT.BIN");
        look(screenw-1,screenh-1);capture("C:\\EYERIGHT.BIN");
        i=eyeupdates;look(screenw-1,screenh-1);
        metric("UNCHANGED_MOUSE_NO_REDRAW",i==eyeupdates);
        metric("EYE_REDRAWS",eyeupdates);
        for(i=0;i<(int)db.nc;i++){db_name(&db,i,nm);if(!lstrcmp(nm,"Mario")){testtarget=i;break;}}
        db_name(&db,testtarget,nm);logtext("TARGET_NAME",nm);
        db_row(&db,testtarget,truth);
        SendMessage(window,WM_KEYDOWN,VK_F1,0);capture("C:\\HELP.BIN");
        SendMessage(window,WM_KEYDOWN,VK_F1,0);
        SendMessage(window,WM_KEYDOWN,VK_F2,0);
        SendMessage(window,WM_KEYDOWN,VK_F2,0);
        metric("OVERLAYS_PRESERVE_STATE",state==0&&engine.turn==0);
        SendMessage(window,WM_KEYDOWN,VK_TAB,0);
        metric("TAB_FOCUS_MOVED",focus==1);
        SendMessage(window,WM_KEYDOWN,VK_TAB,0);
        SendMessage(window,WM_KEYDOWN,VK_RETURN,0);teststep++;return;
    }
    if(state==1){
        if(!verified){capture("C:\\QUESTION.BIN");verified=1;}
        else if(verified==1&&engine.turn>0){
            capture("C:\\PARTIAL.BIN");refresh();
            capture("C:\\FULLDRAW.BIN");verified=2;
        }
        answer=db_value(truth,engine.current);
        if(engine.turn==0){
            SendMessage(window,WM_KEYDOWN,VK_TAB,0);
            SendMessage(window,WM_KEYDOWN,VK_TAB,0);
            i=4-answer;
            SendMessage(window,WM_LBUTTONDOWN,0,
                MAKELONG((buttons[i].left+buttons[i].right)/2,
                         (buttons[i].top+buttons[i].bottom)/2));
        }else SendMessage(window,WM_KEYDOWN,(WORD)('1'+4-answer),0);
        return;
    }
    if(state==2){
        logtext("GUESS",name);metric("QUESTIONS",engine.turn);
        capture("C:\\GUESS.BIN");
        if(engine.best==testtarget){
            if(!wrongguess){
                /* Exercise explicit rejection and prove another guess/question. */
                SendMessage(window,WM_KEYDOWN,'N',0);metric("REJECTION_CONTINUED",state==1||state==2);
                wrongguess=1;act(10);return;
            }
            SendMessage(window,WM_KEYDOWN,'Y',0);capture("C:\\SUCCESS.BIN");
            metric("TARGET_SUCCESS",state==3);finished=1;
        }else {act(21);if(++errors>10)finished=1;}
    }
    if(state==4){metric("APP_ERROR",db.error);errors++;finished=1;}
    if(finished){
        debug=1;debugupdate();refresh();capture("C:\\DEBUG.BIN");debug=0;
        if(state==3){
            refresh();
            SendMessage(window,WM_LBUTTONDOWN,0,
                MAKELONG((buttons[0].left+buttons[0].right)/2,
                         (buttons[0].top+buttons[0].bottom)/2));
            metric("MOUSE_REPLAY_STARTED",state==1&&engine.turn==0);
        }
        metric("DB_BYTES",db.bytes);metric("DB_SEEKS",db.seeks);
        metric("FREE_SPACE_AFTER",GetFreeSpace(0));
        metric("ERRORS",errors);metric("COMPLETE",1);
        KillTimer(window,1);
        i=GetProfileInt("TANDINATOR","TestExit",0);metric("EXIT_METHOD",i);
        if(i==1)SendMessage(window,WM_KEYDOWN,VK_ESCAPE,0);
        else if(i==2)SendMessage(window,WM_SYSCOMMAND,SC_CLOSE,0);
        else if(i==3)SendMessage(window,WM_LBUTTONDOWN,0,
            MAKELONG((buttons[nb-1].left+buttons[nb-1].right)/2,
                     (buttons[nb-1].top+buttons[nb-1].bottom)/2));
        else SendMessage(window,WM_CLOSE,0,0);
    }
}
LONG FAR PASCAL WndProc(HWND w,UINT msg,WORD wp,LONG lp){
    int i,x,y;
    if(msg==WM_PAINT){draw(w);return 0;}
    if(msg==WM_TIMER){if(testmode&&!testinside){testinside=1;testtick();testinside=0;}return 0;}
    if(msg==WM_ACTIVATEAPP){active=wp!=0;if(active)refresh();return 0;}
    if(msg==WM_MOUSEMOVE){look(LOWORD(lp),HIWORD(lp));return 0;}
    if(msg==WM_LBUTTONDOWN){
        x=LOWORD(lp);y=HIWORD(lp);
        for(i=0;i<nb;i++)if(x>=buttons[i].left&&x<buttons[i].right&&
           y>=buttons[i].top&&y<buttons[i].bottom){
            if(focus>=0&&focus<nb)InvalidateRect(w,&buttons[focus],FALSE);
            focus=i;act(ids[i]);break;
        }
        return 0;
    }
    if(msg==WM_KEYDOWN){
        if(wp==VK_ESCAPE){SendMessage(w,WM_CLOSE,0,0);return 0;}
        if(wp==VK_F1){help=!help;debug=0;focus=0;refresh();return 0;}
        if(wp==VK_F2){debug=!debug;help=0;focus=0;debugupdate();refresh();return 0;}
        if(wp==VK_TAB){if(nb){
            InvalidateRect(w,&buttons[focus],FALSE);
            focus=(focus+(GetKeyState(VK_SHIFT)<0?nb-1:1))%nb;
            InvalidateRect(w,&buttons[focus],FALSE);UpdateWindow(w);
        }return 0;}
        if(wp==VK_RETURN||wp==VK_SPACE){if(nb)act(ids[focus]);return 0;}
        if(!debug&&!help&&state==1&&wp>='1'&&wp<='5'){act(wp-'1');return 0;}
        if(!debug&&!help&&state==2&&(wp=='Y'||wp=='N'))act(wp=='Y'?20:21);
        return 0;
    }
    if(msg==WM_DESTROY){artfree();db_close();if(logfile!=-1)_lclose(logfile);PostQuitMessage(0);return 0;}
    return DefWindowProc(w,msg,wp,lp);
}
int PASCAL WinMain(HANDLE inst,HANDLE prev,LPSTR cmd,int show){
    WNDCLASS c;MSG msg;HDC dc;DWORD start;int i,len;
    instance=inst;(void)prev;
    while(*cmd==' ')cmd++;
    testmode=(*cmd=='/'&&cmd[1]=='T')||GetProfileInt("TANDINATOR","Test",0);
    GetModuleFileName(inst,dbpath,sizeof(dbpath));len=lstrlen(dbpath);
    for(i=len-1;i>=0;i--)if(dbpath[i]=='\\'||dbpath[i]==':')break;
    lstrcpy(dbpath+i+1,"TANDY.DAT");
    freespace=GetFreeSpace(0);start=GetTickCount();db_open(&db,dbpath);
    loadms=GetTickCount()-start;if(db.error)state=4;
    if(testmode)logfile=_lcreat("C:\\TANDI.LOG",0);
    metric("WINFLAGS",GetWinFlags());metric("LOAD_MS",loadms);
    metric("ENGINE_BYTES",sizeof(engine));metric("DB_STRUCT_BYTES",sizeof(db));
    metric("FREE_SPACE_BEFORE",freespace);metric("CHARACTERS",db.nc);
    metric("QUESTIONS_AVAILABLE",db.nq);
    screenw=GetSystemMetrics(SM_CXSCREEN);screenh=GetSystemMetrics(SM_CYSCREEN);
    metric("WIDTH",screenw);metric("HEIGHT",screenh);
    c.style=0;c.lpfnWndProc=WndProc;c.cbClsExtra=c.cbWndExtra=0;
    c.hInstance=inst;c.hIcon=0;c.hCursor=LoadCursor(0,IDC_ARROW);
    c.hbrBackground=GetStockObject(BLACK_BRUSH);c.lpszMenuName=0;
    c.lpszClassName="Tandinator02";if(!RegisterClass(&c))return 1;
    window=CreateWindow(c.lpszClassName,"TANDINATOR",WS_POPUP,0,0,
                        screenw,screenh,0,0,inst,0);
    sx=screenw>=640?2:1;
    dc=GetDC(window);colors=GetDeviceCaps(dc,NUMCOLORS);mono=colors==2;
    metric("ART_READY",artinit(dc));ReleaseDC(window,dc);
    metric("ART_INIT_MS",artms);metric("ART_DIB_BYTES",sizeof(artbits));
    metric("FREE_SPACE_ART",GetFreeSpace(0));
    layout();ShowWindow(window,show);UpdateWindow(window);
    if(testmode)SetTimer(window,1,100,0);
    while(GetMessage(&msg,0,0,0)){TranslateMessage(&msg);DispatchMessage(&msg);}
    return msg.wParam;
}
