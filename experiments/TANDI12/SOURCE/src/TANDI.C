#define WINVER 0x0300
#include <windows.h>
#include <string.h>
#include "TANDI.H"
#include "OBSERVE.H"
#include "DEMO.H"
#include "ART.H"
#include "TDSOUND.H"
#include "LEARN.H"
/* Full-screen client, no standard dialogs. All calculations are outside paint. */
static TDB db;
static ENGINE engine;
static TDHISTORY history;
static TDEXPLAIN explanation;
static int explaining,explainpage;
static int notebook,learnuse,gamelearn,questionlimit=25,reportid=-1,reviewpage,pickid,learnchanged;
static U32 gamesession;
static char picktext[40];
static HWND window;
static HINSTANCE instance;
static int screenw,screenh,mono,state,focus,debug,help,busy,testmode;
static int lookx,looky,eyeupdates,sx,colors,active=1,artblits;
static HDC artdc;
static HBITMAP artbmp,oldart;
static DWORD artms;
static int animframe=-1,animticks,idleticks,pending,timerok,animredraws;
static int animcapture,animserial,tickinside,rejectphase,testreset,testwait,capoffered,soundpref=1,soundsupported,settingssaved=1;
static DWORD inputready,animcost,computepeak;
static TDDEMO demonstration;
static int demoMode,demoAuto,demoArmed,demoCues,demoQA,demoDrain,demoOwned,demoMouse,demoMouseGesture;
static int demoReturning,demoWakeCount,demoInputLeaks,demoTestStage,demoTestTicks;
static HWND demoPreviousActive,demoPreviousFocus,demoPeer;
static HCURSOR demoPreviousCursor;
static BYTE demoInitial[256],demoDown[256];
static POINT demoOrigin;
static DWORD demoStarted,demoLastInput,demoWelcome;
static void refresh(void);
static void demoPulse(void);
static void demoCleanup(int);
static void demoQATick(void);
static int demoQACase,demoQAPhases,demoQAHeldTicks,demoQASeen[8],demoQAFrames;
static int demoQASoundPref,demoQAInitialSetting,demoQAEyes,demoQAErrors;
static void animpaint(HDC dc);
static void capture(char *path);
static void animset(int frame);
static void animtick(void);
static void nextcompute(void);
static void next(void);
static int inputblocked(void){return busy||(LONG)(GetTickCount()-inputready)<0;}

static char *soundfooter(void){
    if(!soundsupported)return "F1 HELP F2 DEBUG NO SOUND";
    if(!settingssaved)return "F1 HELP F2 DEBUG SOUND UNSAVED";
    return soundpref?"F1 HELP F2 DEBUG F3 SOUND ON":"F1 HELP F2 DEBUG F3 SOUND OFF";
}
static void soundsettings(void){
    soundpref=GetProfileInt("TANDINATOR","Sound",1)!=0;
    TdSoundEnable(soundpref);
}

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
static int wrapfail,wrapmax;
static RECT buttons[6];
static int ids[6],nb;
static char labels[6][24],question[80],name[40],line[100],dbpath[144];
static char debugline[10][80];
static DWORD loadms,answerms,selectms,freespace;
static HFILE logfile=-1;
static U8 truth[TD_ROW];
static char *answers[5]={"YES","PROBABLY","DON'T KNOW",
                             "PROBABLY NOT","NO"};
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
/* Measure every line ourselves: Win3 DrawText can clip an exact-fit word
   wrapped centered line. Spaces are never included in its centering width. */
static void wrapped(HDC dc,char *s,RECT *r){
    char row[100];int n,last,take,width,y=r->top,lines=0;TEXTMETRIC tm;
    GetTextMetrics(dc,&tm);
    while(*s){
        while(*s==' ')s++;if(!*s)break;
        n=0;last=0;
        while(s[n]&&n<98){
            row[n]=s[n];row[n+1]=0;
            width=LOWORD(GetTextExtent(dc,row,n+1));
            if(width>r->right-r->left)break;
            if(s[n]==' ')last=n;n++;
        }
        take=n;
        if(s[n]&&s[n]!=' '&&last)take=last;
        if(!take)take=1;
        n=take;while(n&&s[n-1]==' ')n--;
        for(width=0;width<n;width++)row[width]=s[width];row[n]=0;
        width=LOWORD(GetTextExtent(dc,row,n));
        if(width>r->right-r->left||y+tm.tmHeight>r->bottom){
            if(testmode)wrapfail++;
        }else TextOut(dc,r->left+(r->right-r->left-width)/2,y,row,n);
        y+=tm.tmHeight;lines++;s+=take;
    }
    if(lines>wrapmax)wrapmax=lines;
}
static void ticket(HDC dc,char *s,int y,int h){
    RECT r;int left=panelleft(),width=screenw-left-4*sx;
    box(dc,left,y,width,h,colors<16?RGB(255,255,255):RGB(255,255,0));
    box(dc,left+sx,y+1,width-2*sx,h-2,RGB(255,255,255));
    r.left=left+2*sx;r.right=screenw-6*sx;r.top=y+5;r.bottom=y+h-3;
    SetTextColor(dc,RGB(0,0,0));SetBkColor(dc,RGB(255,255,255));
    wrapped(dc,s,&r);
}
/* Native 3x6 pupil/shadow shapes, restricted to two white 7x9 patches. */
static void eyes(HDC dc){
    int x=6*sx,y=43;
    if(!artdc||state>1||animframe>=0)return;
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
    if(help||debug||explaining||state>1||!active||!artdc)return;
    dc=GetDC(window);eyes(dc);ReleaseDC(window,dc);eyeupdates++;
}
static void mascot(HDC dc){
    int pose=state==2?1:(state==3?2:0);
    sprite(dc,6*sx,43,96,120,0,pose*120);artblits++;
    eyes(dc);animpaint(dc);
}
/* Exact 24x18 face crops from the supplied PARTS sheet. */
static void animpaint(HDC dc){
    if(animframe>=0&&!help&&!debug&&!explaining)
        sprite(dc,41*sx,85,24,18,(animframe%4)*32,416+(animframe/4)*20);
}
static void animset(int frame){
    HDC dc;DWORD started;int pose;char path[30],digits[12];
    if(animframe==frame)return;animframe=frame;
    if(demonstration.enabled){InvalidateRect(window,0,FALSE);return;}
    if(!active||help||debug||explaining||!artdc)return;
    started=GetTickCount();dc=GetDC(window);if(!dc)return;
    pose=state==2?1:(state==3?2:0);
    sprite(dc,41*sx,85,24,18,35,42+pose*120);
    eyes(dc);animpaint(dc);ReleaseDC(window,dc);animredraws++;
    started=GetTickCount()-started;if(started>animcost)animcost=started;
    if(testmode&&(teststep>0||testwait<40)&&animserial<120){
        lstrcpy(path,"C:\\AN");number(digits,animserial++);lstrcat(path,digits);lstrcat(path,".BIN");capture(path);
    }
}
static void addbutton(int id,char *label,int x,int y,int w,int h){
    RECT *r=&buttons[nb];r->left=x;r->top=y;r->right=x+w;r->bottom=y+h;
    ids[nb]=id;lstrcpy(labels[nb],label);nb++;
}
static char *factwords[5]={"NO","PROBABLY NOT","UNKNOWN","PROBABLY","YES"};
#include "NOTEUI.H"
static void layout(void){
    int i,left=panelleft(),width=screenw-left-4*sx;nb=0;
    if(notebook){notelayout();}
    else if(help||debug||explaining){
        if(explaining){
            if(explainpage>0)addbutton(93,"PREV",8*sx,163,76*sx,16);
            if(explainpage+1<explanation.count)addbutton(94,"NEXT",90*sx,163,76*sx,16);
        }
        if(debug==1)addbutton(91,"SHOW DEBUG",left,125,width,21);
        addbutton(90,"BACK [ESC]",explaining?174*sx:left,163,explaining?142*sx:width,16);
    }
    else if(state==0)addbutton(10,"BEGIN  [ENTER]",left,122,width,21);
    else if(state==1){
        left+=(width-164*sx)/2;width=164*sx;
        for(i=0;i<5;i++)addbutton(i,answers[i],left,86+17*i,width,16);
    }
    else if(state==2){
        addbutton(20,"YES!  [Y]",left,117,width,21);
        addbutton(21,"NO, TRY AGAIN [N]",left,144,width,21);
        addbutton(92,"HOW I KNEW [F4]",left,100,width,14);
    }else if(state==3||state==8||(state==4&&!db.error)){
        addbutton(10,"PLAY AGAIN",left,126,width,23);
        if(state==3){addbutton(92,"HOW I KNEW [F4]",left,152,width,16);
            if(!gamelearn&&ln_ready()&&ln_review(&db,reportid,&history)>0)addbutton(100,"SAVE REPORT",left,105,width,16);}
    }
    else if(state==5||state==7){
        addbutton(30,"CONTINUE GUESSING",left,115,width,16);
        if(engine.turn<40)addbutton(31,"ASK TWO MORE",left,133,width,16);
        addbutton(10,"RESTART",left,153,width,16);
    }else if(state==6){
        addbutton(104,"TELL ME WHO",left,118,width,20);
        addbutton(10,"SKIP / PLAY AGAIN",left,145,width,20);
    }
    addbutton(99,"EXIT",screenw-49,183,43,14);
    if(focus>=nb)focus=0;
}

static void explaindraw(HDC dc){
    TDCLUE *c;char a[40],b[40],num[20],q[80];RECT r;
    if(!explanation.valid){
        text(dc,8*sx,72,"No complete comparison is available.");
        text(dc,8*sx,90,"A guess is not proof of identity.");return;
    }
    db_name(&db,explanation.leader,a);db_name(&db,explanation.other,b);
    lstrcpy(line,a);lstrcat(line," vs ");lstrcat(line,b);
    r.left=8*sx;r.right=screenw-8*sx;r.top=43;r.bottom=68;
    DrawText(dc,line,-1,&r,DT_WORDBREAK|DT_NOPREFIX);
    if(explanation.count==0){text(dc,8*sx,80,"No answers yet. A score tie, not proof.");return;}
    c=&explanation.clue[explainpage];db_question(&db,c->q,q);
    r.top=71;r.bottom=100;DrawText(dc,q,-1,&r,DT_WORDBREAK|DT_NOPREFIX);
    lstrcpy(line,"You: ");lstrcat(line,c->answer==2?"DON'T KNOW":factwords[c->answer]);text(dc,8*sx,102,line);
    lstrcpy(line,"Guess DAT: ");lstrcat(line,factwords[c->leaderFact]);
    lstrcat(line," (");number(num,c->leaderDelta);lstrcat(line,num);lstrcat(line,")");text(dc,8*sx,114,line);
    lstrcpy(line,"Other DAT: ");lstrcat(line,factwords[c->otherFact]);
    lstrcat(line," (");number(num,c->otherDelta);lstrcat(line,num);lstrcat(line,")");text(dc,8*sx,126,line);
    lstrcpy(line,"Score difference: ");number(num,c->difference);lstrcat(line,num);
    lstrcat(line,c->difference>0?" for guess":(c->difference<0?" against guess":" neutral"));text(dc,8*sx,138,line);
    number(num,explanation.sum);lstrcpy(line,"Margin ");lstrcat(line,num);
    lstrcat(line,". Clue ");number(num,explainpage+1);lstrcat(line,num);lstrcat(line,"/");
    number(num,explanation.count);lstrcat(line,num);lstrcat(line,". Not proof.");text(dc,8*sx,150,line);
}
#include "DEMOUI.H"
static void draw(HWND w){
    PAINTSTRUCT ps;HDC dc;int i;RECT r;char temp[24];COLORREF gold;
    dc=BeginPaint(w,&ps);SetBkMode(dc,OPAQUE);
    SelectObject(dc,GetStockObject(SYSTEM_FIXED_FONT));
    box(dc,0,0,screenw,screenh,RGB(0,0,0));
    if(demonstration.enabled||demoDrain){
        demoDraw(dc);EndPaint(w,&ps);return;
    }
    gold=colors<16?RGB(255,255,255):RGB(255,255,0);
    SetTextColor(dc,gold);SetBkColor(dc,RGB(0,0,0));
    if(artdc)sprite(dc,(screenw-126*sx)/2,4,126,16,0,360);
    else centered(dc,5,"TANDINATOR");
    centered(dc,22,notebook?"EXPERIMENTAL NOTEBOOK":explaining?"HOW I KNEW - SCORE CLUES":help?"HOW TO CONSULT THE ORACLE":(debug?"DIAGNOSTICS - SPOILERS":"THE INCREDIBLE TANDY MIND READER"));
    box(dc,6*sx,35,screenw-12*sx,1,gold);
    box(dc,6*sx,179,screenw-12*sx,1,gold);
    SetTextColor(dc,RGB(255,255,255));
    if(notebook){notedraw(dc);}
    else if(debug||help||explaining){
        if(!explaining)sprite(dc,screenw-55*sx,40,48,40,debug?48:0,376);
        if(explaining)explaindraw(dc);
        else if(debug==2){for(i=0;i<10;i++)text(dc,8*sx,43+i*11,debugline[i]);}
        else if(debug==1){
            text(dc,8*sx,87,"This shows likely names and scores.");
            text(dc,8*sx,103,"It may spoil the guessing game.");
        }
        else{
            text(dc,8*sx,45,"Think of someone in the roster.");
            text(dc,8*sx,61,"1 Yes  2 Probably  3 Don't know");
            text(dc,8*sx,74,"4 Probably not  5 No");
            text(dc,8*sx,90,"Tab changes focus. Enter chooses.");
            text(dc,8*sx,103,"Leading = within 24 score points.");
            text(dc,8*sx,119,"Count may rise. Other names can win.");
            text(dc,8*sx,132,"F4 on a guess: clues, not proof.");
            text(dc,8*sx,145,"App 0.3.9 local; 384 characters. F5 notes.");
        }
    }else{
        r.left=6*sx;r.right=102*sx;r.top=43;r.bottom=163;
        if(RectVisible(dc,&r))mascot(dc);
        if(state==0){
            ticket(dc,"Think of a roster character. Use its named edition.",45,64);
        }else if(state==1){
            ticket(dc,question,42,42);
            number(temp,engine.turn+1);lstrcpy(line,"Q ");lstrcat(line,temp);
            SetTextColor(dc,gold);SetBkColor(dc,RGB(0,0,0));text(dc,34*sx,168,line);
            {TDPOOL pool;obs_pool(&engine,&db,&pool);
                lstrcpy(line,"Leading: ");number(temp,pool.leading);lstrcat(line,temp);
                lstrcat(line,"/");number(temp,pool.eligible);lstrcat(line,temp);
                text(dc,panelleft(),170,line);}
        }else if(state==2){
            ticket(dc,learnchanged?"NOTES TIE-BREAK...":!eng_confident(&engine,&db)?"TENTATIVE GUESS...":"I SUSPECT...",46,20);ticket(dc,name,70,38);
        }else if(state==3){
            ticket(dc,"THANKS! A MATCH.",48,32);
            number(temp,engine.turn);lstrcpy(line,"Questions asked: ");lstrcat(line,temp);ticket(dc,line,84,27);
        }else if(state==4){
            ticket(dc,db.error?"Cannot read TANDY.DAT. Exit, replace it beside this EXE, then restart.":
                  "You have stumped the silicon oracle! Try another character.",45,65);
        }else if(state==5||state==7){
            ticket(dc,state==5?"25 questions used. Continue guessing, or ask two more?":"That guess missed. Continue, or ask two more?",45,65);
        }else if(state==8){
            ticket(dc,"Thanks for telling me. You beat this round!",45,65);
        }else if(state==6){
            ticket(dc,engine.evidence<7?"Not enough clues. Who were you thinking of? You can skip.":"No reliable match. Who were you thinking of? You can skip.",45,65);
        }
        if(!artdc){SetTextColor(dc,RGB(255,255,255));text(dc,8,85,"THE ORACLE");text(dc,8,100,"IS LISTENING");}
    }
    for(i=0;i<nb;i++){
        r=buttons[i];if(!RectVisible(dc,&r))continue;
        box(dc,r.left,r.top,r.right-r.left,r.bottom-r.top,gold);
        box(dc,r.left+sx,r.top+1,r.right-r.left-2*sx,r.bottom-r.top-2,RGB(255,255,255));
        SetTextColor(dc,RGB(0,0,0));SetBkColor(dc,RGB(255,255,255));
        r.top+=3;
        if(state==1&&!debug&&!help&&ids[i]>=0&&ids[i]<5){
            number(temp,ids[i]+1);text(dc,r.left+8*sx,r.top,temp);
            r.left+=24*sx;r.right-=8*sx;
        }
        DrawText(dc,labels[i],-1,&r,DT_CENTER|DT_SINGLELINE|DT_NOPREFIX);
        if(i==focus){r=buttons[i];InflateRect(&r,-2,-2);DrawFocusRect(dc,&r);}
    }
    SetTextColor(dc,RGB(255,255,255));SetBkColor(dc,RGB(0,0,0));
    text(dc,8,186,busy?"CONSULTING...":soundfooter());EndPaint(w,&ps);
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
    r.left=6*sx;r.right=screenw-4*sx;r.top=164;r.bottom=178;
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
static void nextcompute(void){
    DWORD start;int previous=state,previousfocus=focus;TdSoundStop(window);busy=1;busyfooter();start=GetTickCount();
    learnchanged=0;
    /* Stop rather than turn absent/contradictory clues into a named guess. */
    if(engine.turn>=questionlimit&&
       (engine.best<0||engine.evidence<7||engine.score[engine.best]<engine.evidence*2)){state=6;reportid=-1;}
    else if((engine.turn<25||engine.turn>=questionlimit)&&
            (engine.turn>=questionlimit||eng_confident(&engine,&db))){state=2;db_name(&db,engine.best,name);}
    else if(eng_choose(&engine,&db)<0){
        state=db.error?4:(engine.best<0||!eng_confident(&engine,&db)?6:2);
        if(state==2)db_name(&db,engine.best,name);
    }else {state=1;db_question(&db,engine.current,question);}
    if(state==2&&learnuse){int base=engine.best;ln_tie(&engine,&db,&history);learnchanged=base!=engine.best;db_name(&db,engine.best,name);}
    selectms=GetTickCount()-start;metric("SELECT_MS",selectms);
    if(selectms>computepeak)computepeak=selectms;
    metric("SAMPLE",engine.count);metric("ROWS",engine.examined);
    if(db.error)state=4;busy=0;explaining=0;focus=0;pending=0;
    animset(-1);animticks=0;idleticks=0;
    inputready=GetTickCount()+220;
    if(state==2)animframe=1;
    if(state==4)TdSoundBegin(window,TD_SND_WRONG,GetTickCount());
    if(previous==1&&state==1&&engine.turn>0){
        previous=artblits;questionrefresh(previousfocus);
        metric("QUESTION_CABINET_UNTOUCHED",previous==artblits);
    }else refresh();
    inputready=GetTickCount()+220;
    if(state==2)TdSoundBegin(window,TD_SND_REVEAL,GetTickCount());
    else if(state==1&&rejectphase)TdSoundBegin(window,TD_SND_WRONG,GetTickCount());
}
/* Paint the thinking expression before synchronous engine work.
   No decorative timer delay; the post-compute input guard stays intact. */
static void next(void){
    busy=1;pending=0;animticks=0;idleticks=0;busyfooter();
    animset(rejectphase?7:6);
    nextcompute();rejectphase=0;
}
static void animtick(void){
    static int reveal[5]={1,2,1,4,-1};
    static int victory[5]={3,4,3,4,3};
    if(demoDrain){demoDrainTick();return;}
    if(demonstration.enabled){demoPulse();return;}
    if(demoAuto&&demoArmed&&state==0&&history.count==0&&!help&&!debug&&!explaining&&
       GetTickCount()-demoWelcome>=DEMO_IDLE_MS)demoStart();
    if(!active||help||debug||explaining||notebook)return;
    TdSoundTick(window,GetTickCount());
    if(state==2||state==3){
        if(animticks<10){animticks++;if(!(animticks%2))
            animset(state==2?reveal[animticks/2-1]:victory[animticks/2-1]);}
    }else if(state<=1){
        idleticks++;
        if(idleticks==36)animset(0);
        if(idleticks>=38){animset(-1);idleticks=0;}
    }
}
static void act(int id){
    DWORD start;
    if(id==99){SendMessage(window,WM_CLOSE,0,0);return;}
    if(inputblocked())return;
    if(notebook&&noteact(id))return;
    if(id==90){debug=help=explaining=notebook=0;refresh();return;}
    if(id==100&&state==3&&!gamelearn){notebook=4;reviewpage=0;focus=0;refresh();inputready=GetTickCount()+220;return;}
    if(id==104&&state==6){notebook=6;pickid=0;picktext[0]=0;focus=0;refresh();inputready=GetTickCount()+220;return;}
    if(id==92&&(state==2||state==3)&&!help&&!debug){
        TdSoundStop(window);explaining=1;explainpage=0;
        obs_explain(&history,&engine,&db,&explanation);
        focus=0;refresh();inputready=GetTickCount()+220;return;
    }
    if(explaining&&(id==93||id==94)){
        if(id==93&&explainpage>0)explainpage--;
        if(id==94&&explainpage+1<explanation.count)explainpage++;
        focus=0;refresh();inputready=GetTickCount()+220;return;
    }
    if(id==91&&debug==1){debug=2;debugupdate();focus=0;refresh();inputready=GetTickCount()+220;return;}
    if(id==30&&(state==5||state==7)){next();return;}
    if(id==31&&(state==5||state==7)&&engine.turn<40){questionlimit=engine.turn+2;if(questionlimit>40)questionlimit=40;next();return;}
    if(id==10){
        if(db.error){state=4;refresh();return;}
        TdSoundStop(window);eng_reset(&engine,&db);obs_reset(&history);capoffered=0;questionlimit=25;gamesession=ln_next();gamelearn=learnuse;reportid=-1;state=1;next();return;
    }
    if(id>=0&&id<5&&state==1){
        if(engine.turn>=40)return;
        TdSoundStop(window);start=GetTickCount();
        if(!obs_answer(&history,&engine,&db,4-id))state=4;
        answerms=GetTickCount()-start;metric("ANSWER_MS",answerms);
        if(state!=4)next();else refresh();return;
    }
    if(state==2&&id==20){reportid=engine.best;state=3;animticks=0;animframe=3;
        refresh();inputready=GetTickCount()+220;TdSoundBegin(window,TD_SND_VICTORY,GetTickCount());return;}
    if(state==2&&id==21){
        TdSoundStop(window);eng_reject(&engine,&db);
        if(engine.turn>=25){
            if(engine.turn>=40){state=6;reportid=-1;}
            else if(engine.best<0)state=6;
            else {state=capoffered?7:5;capoffered=1;}
            busy=pending=0;animticks=0;animframe=-1;
            focus=0;refresh();inputready=GetTickCount()+220;
            TdSoundBegin(window,TD_SND_WRONG,GetTickCount());return;
        }
        rejectphase=1;next();
    }
}
/* Deterministic fixture setup; inputs under test still use production handlers. */
static void testprepare(void){
    busy=pending=0;inputready=0;capoffered=0;questionlimit=25;notebook=0;learnuse=gamelearn=0;gamesession=ln_next();eng_reset(&engine,&db);obs_reset(&history);state=1;
    nextcompute();inputready=0;
}
#include "LEARNQA.H"
static void soundtest(void){
    WNDCLASS c;HWND peer;TDSNDSTAT before,after;int result;
    TdSoundStop(window);TdSoundEnable(1);TdSoundGetStats(&before);
    c.style=0;c.lpfnWndProc=DefWindowProc;c.cbClsExtra=c.cbWndExtra=0;
    c.hInstance=instance;c.hIcon=0;c.hCursor=0;c.hbrBackground=0;
    c.lpszMenuName=0;c.lpszClassName="TandyStartupChime";
    if(RegisterClass(&c)){
        peer=CreateWindow(c.lpszClassName,"Busy test",WS_POPUP,0,0,0,0,0,0,instance,0);
        if(peer){result=TdSoundBegin(window,TD_SND_REVEAL,GetTickCount());
            TdSoundTick(window,GetTickCount());TdSoundGetStats(&after);
            metric("SOUND_BUSY_SILENT",result==TD_SND_BUSY&&after.portWrites==before.portWrites);
            DestroyWindow(peer);}
        UnregisterClass(c.lpszClassName,instance);
    }
    TdSoundEnable(0);TdSoundGetStats(&before);
    result=TdSoundBegin(window,TD_SND_VICTORY,GetTickCount());
    TdSoundTick(window,GetTickCount());TdSoundGetStats(&after);
    metric("SOUND_OFF_SILENT",result==TD_SND_DISABLED&&before.portWrites==after.portWrites);
    TdSoundEnable(1);
    result=TdSoundBegin(window,TD_SND_REVEAL,GetTickCount());TdSoundTick(window,GetTickCount());
    SendMessage(window,WM_ACTIVATEAPP,0,0);TdSoundGetStats(&after);
    metric("SOUND_FOCUS_RELEASE",result==TD_SND_STARTED&&!after.playing&&!FindWindow("TandyPSGTest",0));
    SendMessage(window,WM_ACTIVATEAPP,1,0);TdSoundEnable(soundpref);inputready=0;
}
static void layouttest(void){
    int i,j,bestq=0,bestn=0,maxq=0,maxn=0,turn,ok=1,fit=1;char q[80],nm[40];
    HDC dc;RECT r;
    dc=GetDC(window);SelectObject(dc,GetStockObject(SYSTEM_FIXED_FONT));
    /* Same rectangles as tickets, but an empty clip avoids transient screens. */
    IntersectClipRect(dc,0,0,0,0);
    r.left=panelleft()+2*sx;r.right=screenw-6*sx;r.top=47;r.bottom=81;
    for(i=0;i<(int)db.nq;i++){
        db_question(&db,i,q);wrapped(dc,q,&r);
        if(lstrlen(q)>maxq){maxq=lstrlen(q);bestq=i;}
    }
    r.top=75;r.bottom=105;
    for(i=0;i<(int)db.nc;i++){
        db_name(&db,i,nm);wrapped(dc,nm,&r);
        if(lstrlen(nm)>maxn){maxn=lstrlen(nm);bestn=i;}
    }
    for(i=0;i<(int)db.nq;i++){
        db_question(&db,i,q);r.left=8*sx;r.right=screenw-8*sx;r.top=71;r.bottom=100;
        DrawText(dc,q,-1,&r,DT_WORDBREAK|DT_NOPREFIX|DT_CALCRECT);
        if(r.bottom>100)fit=0;
    }
    metric("EXPLAIN_QUESTION_LAYOUT",fit);
    db_name(&db,bestn,nm);lstrcpy(line,nm);lstrcat(line," vs ");lstrcat(line,nm);
    r.left=8*sx;r.right=screenw-8*sx;r.top=43;r.bottom=68;
    DrawText(dc,line,-1,&r,DT_WORDBREAK|DT_NOPREFIX|DT_CALCRECT);
    metric("EXPLAIN_NAME_LAYOUT",r.bottom<=68);
    ReleaseDC(window,dc);
    metric("ALL_QUESTIONS_CHECKED",db.nq);metric("ALL_NAMES_CHECKED",db.nc);
    metric("WRAP_FAILURES",wrapfail);metric("MAX_TEXT_LINES",wrapmax);
    state=1;lstrcpy(question,"Is your character strongly associated with movies?");
    refresh();capture("C:\\CLIPFIX.BIN");
    db_question(&db,bestq,question);refresh();capture("C:\\LONGQ.BIN");
    state=2;db_name(&db,bestn,name);refresh();capture("C:\\LONGNAME.BIN");
    for(i=0;i<5;i++){
        testprepare();turn=engine.turn;SendMessage(window,WM_KEYDOWN,'1'+i,0);
        if(engine.turn!=turn+1)ok=0;
        for(j=0;j<2;j++){
            testprepare();turn=engine.turn;
            SendMessage(window,WM_LBUTTONDOWN,0,MAKELONG(
                j?buttons[i].right-1:buttons[i].left,
                j?buttons[i].bottom-1:buttons[i].top));
            if(engine.turn!=turn+1)ok=0;
        }
    }
    testprepare();turn=engine.turn;
    SendMessage(window,WM_LBUTTONDOWN,0,MAKELONG(buttons[0].left-1,buttons[0].top+5));
    if(engine.turn!=turn)ok=0;
    metric("FIVE_KEYS_TEN_CORNERS_OUTSIDE",ok);
    testprepare();turn=engine.turn;
    SendMessage(window,WM_KEYDOWN,VK_RETURN,0x40000000L);
    metric("HELD_KEY_IGNORED",engine.turn==turn);
    SendMessage(window,WM_KEYDOWN,VK_RETURN,0);
    turn=engine.turn;SendMessage(window,WM_KEYDOWN,VK_RETURN,0);
    SendMessage(window,WM_LBUTTONDOWN,0,MAKELONG(buttons[0].left+2,buttons[0].top+2));
    metric("BUSY_INPUT_IGNORED",engine.turn==turn&&!pending&&inputblocked());
    busy=pending=0;state=2;focus=0;animticks=10;inputready=0;refresh();
    SendMessage(window,WM_LBUTTONDOWN,0,MAKELONG(210*sx,130));
    SendMessage(window,WM_LBUTTONDOWN,0,MAKELONG(210*sx,130));
    SendMessage(window,WM_LBUTTONDBLCLK,0,MAKELONG(210*sx,130));
    metric("DOUBLE_CLICK_STAYS_SUCCESS",state==3);
    if(!ok||wrapfail)errors++;
    testprepare();
}
static void usabilitytest(void){
    int turn,leader,i,gates,savedpref;
    testprepare();turn=engine.turn;
    SendMessage(window,WM_KEYDOWN,VK_F1,0);
    SendMessage(window,WM_KEYDOWN,VK_ESCAPE,0);
    metric("ESC_HELP_PRESERVED",!help&&!debug&&!explaining&&engine.turn==turn&&IsWindow(window));
    inputready=0;SendMessage(window,WM_KEYDOWN,VK_F2,0);
    metric("DEBUG_WARNING_FIRST",debug==1&&ids[0]==91);capture("C:\\WARN.BIN");
    SendMessage(window,WM_KEYDOWN,VK_ESCAPE,0);metric("ESC_DEBUG_PRESERVED",!debug&&engine.turn==turn);
    inputready=0;SendMessage(window,WM_KEYDOWN,VK_F2,0);act(91);
    metric("DEBUG_EXPLICIT_REVEAL",debug==2);SendMessage(window,WM_KEYDOWN,VK_ESCAPE,0);
    testprepare();while(engine.turn<25){eng_choose(&engine,&db);obs_answer(&history,&engine,&db,2);}
    nextcompute();inputready=0;leader=engine.best;act(21);
    metric("LIMIT_REJECTION_GATE",state==5&&!pending&&engine.rejected[leader]);capture("C:\\CONTINUE.BIN");
    leader=engine.best;turn=engine.turn;
    for(i=0;i<6;i++)animtick();
    metric("GATE_NO_AUTO_GUESS",state==5&&!pending&&engine.best==leader&&engine.turn==turn);
    inputready=0;act(30);
    metric("EXPLICIT_CONTINUE",state==2&&engine.turn==25&&engine.best==leader);
    inputready=0;act(21);metric("SECOND_REJECTION_NO_GATE",state==7&&capoffered);
    inputready=0;act(10);
    metric("GATE_RESTART",state==1&&engine.turn==0&&!capoffered);
    savedpref=soundpref;SendMessage(window,WM_KEYDOWN,VK_F3,0);
    metric("SOUND_PREF_SAVED",settingssaved&&(int)GetProfileInt("TANDINATOR","Sound",savedpref)==soundpref);
    SendMessage(window,WM_KEYDOWN,VK_F3,0x40000000L);
    metric("SOUND_HELD_KEY_IGNORED",soundpref!=savedpref);
    SendMessage(window,WM_KEYDOWN,VK_F3,0);
    testprepare();while(engine.turn<25){eng_choose(&engine,&db);obs_answer(&history,&engine,&db,2);}
    nextcompute();i=0;gates=0;
    while(state==2){inputready=0;act(21);i++;if(state==5||state==7){if(state==5)gates++;inputready=0;act(30);}}
    metric("CAP_ALL_CANDIDATES_REACHABLE",state==6&&i==(int)db.nc&&gates==1);
    metric("CAP_GATE_COUNT",gates);
    busy=pending=0;TdSoundStop(window);db.error=1;state=4;refresh();
    metric("BAD_DAT_EXIT_ONLY",nb==1&&ids[0]==99);capture("C:\\BADDB.BIN");
    db.error=0;testprepare();
}
static void observetest(void){
    int q,a,k,known,i,negative,oldturn;TDPOOL pool;U8 obsrow[TD_ROW];
    testprepare();db_row(&db,0,obsrow);
    while(!eng_confident(&engine,&db)){
        q=eng_choose(&engine,&db);if(q<0)break;
        obs_answer(&history,&engine,&db,db_value(obsrow,q));
    }
    nextcompute();inputready=0;act(92);
    metric("EXPLAIN_ACTUAL_RUNNER_UP",explaining&&explanation.valid&&
           explanation.leader==engine.best&&explanation.other==engine.second&&
           explanation.count==engine.turn);
    capture("C:\\EXPLAIN.BIN");oldturn=engine.turn;
    inputready=0;SendMessage(window,WM_KEYDOWN,'Y',0);
    metric("EXPLAIN_GAME_INPUT_BLOCKED",explaining&&engine.turn==oldturn&&state==2);
    SendMessage(window,WM_KEYDOWN,VK_ESCAPE,0);
    metric("EXPLAIN_ESCAPE_PRESERVES",!explaining&&engine.turn==oldturn&&state==2);
    testprepare();db_row(&db,1,obsrow);known=0;
    while(!eng_confident(&engine,&db)){
        q=eng_choose(&engine,&db);if(q<0)break;a=db_value(obsrow,q);
        if(a!=2){known++;if(known==1||known==4)a=4-a;}
        obs_answer(&history,&engine,&db,a);
    }
    nextcompute();inputready=0;SendMessage(window,WM_KEYDOWN,VK_F4,0);
    metric("EXPLAIN_F4_OPENS",explaining&&explanation.valid);
    negative=-1;for(i=0;i<explanation.count;i++)if(explanation.clue[i].difference<0){negative=i;break;}
    metric("EXPLAIN_CONFLICT_RETAINED",negative>=0);
    if(negative>=0){
        for(k=0;k<negative;k++){inputready=0;act(94);}
        capture("C:\\CONFLICT.BIN");
    }
    i=explainpage;SendMessage(window,WM_KEYDOWN,VK_F4,0x40000000L);
    metric("EXPLAIN_HELD_KEY_IGNORED",explaining&&explainpage==i);
    SendMessage(window,WM_KEYDOWN,VK_ESCAPE,0);testprepare();
    for(i=0;i<(int)db.nq;i++){engine.current=i;obs_answer(&history,&engine,&db,2);}
    nextcompute();inputready=0;act(92);
    metric("EXPLAIN_FULL_HISTORY",explanation.valid&&explanation.count==(int)db.nq&&history.count>25);
    for(i=1;i<explanation.count;i++){inputready=0;act(94);}
    metric("EXPLAIN_LAST_PAGE",explainpage+1==explanation.count);
    capture("C:\\EXPLAST.BIN");inputready=0;act(94);
    metric("EXPLAIN_PAGE_BOUND",explainpage+1==explanation.count);
    SendMessage(window,WM_KEYDOWN,VK_ESCAPE,0);testprepare();obs_pool(&engine,&db,&pool);
    metric("LEADING_ALL_AT_START",pool.leading==(int)db.nc&&pool.eligible==(int)db.nc);
    inputready=0;act(0);capture("C:\\COUNTINC.BIN");refresh();capture("C:\\COUNTFUL.BIN");
    testprepare();
}
/* Bounded local regression fixture; Test=2, real production handlers. */
static void quicktest(void){
    int i,q,first;U8 row[TD_ROW];
    testprepare();
    for(i=0;i<25;i++){q=eng_choose(&engine,&db);if(q<0)break;obs_answer(&history,&engine,&db,2);}
    nextcompute();metric("UNKNOWN_ABSTAINS",state==6&&!eng_confident(&engine,&db)&&engine.evidence==0);
    capture("C:\\UNKNOWN.BIN");
    testprepare();engine.turn=25;engine.evidence=7;
    nextcompute();metric("CONTRADICTION_ABSTAINS",state==6);
    testprepare();engine.turn=25;engine.evidence=7;
    for(i=0;i<(int)db.nc;i++)engine.score[i]=14;
    nextcompute();metric("TIE_IS_TENTATIVE",state==2&&!eng_confident(&engine,&db));
    capture("C:\\TENTATIVE.BIN");first=engine.best;inputready=0;act(21);
    metric("REJECTION_GATE",state==5&&engine.rejected[first]);
    inputready=0;act(31);nextcompute();metric("ASK_TWO_RETAINED",questionlimit==27&&state==1);
    testprepare();db_row(&db,0,row);
    while(engine.turn<25&&!eng_confident(&engine,&db)){
        q=eng_choose(&engine,&db);if(q<0)break;obs_answer(&history,&engine,&db,db_value(row,q));
    }
    nextcompute();metric("MARIO_FIRST_MATCH",state==2&&engine.best==0);
    capture("C:\\MATCH.BIN");inputready=0;act(20);metric("CONFIRM_MATCH",state==3);
    metric("QUICK_COMPLETE",1);KillTimer(window,1);SendMessage(window,WM_CLOSE,0,0);
}
static void testtick(void){
    int answer,i,turnsaved,statesaved,lx,ly;char nm[40],target[40];RECT damage;HWND peer;HDC testdc;
    if(inputblocked())return;
    if(testmode==2&&!db.error){quicktest();return;}
    if(db.error){
        metric("BAD_DAT_EXIT_ONLY",state==4&&nb==1&&ids[0]==99);
        capture("C:\\BADDB.BIN");metric("APP_ERROR",db.error);metric("ERRORS",1);metric("COMPLETE",1);
        KillTimer(window,1);SendMessage(window,WM_CLOSE,0,0);return;
    }
    if(testreset){testreset=0;act(10);return;}
    if((state==2||state==3)&&animticks<10)return;
    if(teststep==0&&testwait++<40)return;
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
        GetProfileString("TANDINATOR","TestTarget","Mario",target,sizeof(target));
        for(i=0;i<(int)db.nc;i++){db_name(&db,i,nm);if(!lstrcmp(nm,target)){testtarget=i;break;}}
        metric("TARGET_FOUND",i<(int)db.nc);
        db_name(&db,testtarget,nm);logtext("TARGET_NAME",nm);
        db_row(&db,testtarget,truth);
        soundtest();inputready=0;SendMessage(window,WM_KEYDOWN,VK_F1,0);capture("C:\\HELP.BIN");
        SendMessage(window,WM_KEYDOWN,VK_F1,0);
        SendMessage(window,WM_KEYDOWN,VK_F2,0);
        SendMessage(window,WM_KEYDOWN,VK_F2,0);
        metric("OVERLAYS_PRESERVE_STATE",state==0&&engine.turn==0);
        SendMessage(window,WM_KEYDOWN,VK_TAB,0);
        metric("TAB_FOCUS_MOVED",focus==1);
        SendMessage(window,WM_KEYDOWN,VK_TAB,0);
        SendMessage(window,WM_KEYDOWN,VK_RETURN,0);layouttest();usabilitytest();observetest();learningtest();teststep++;return;
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
                wrongguess=1;testreset=1;return;
            }
            SendMessage(window,WM_KEYDOWN,'Y',0);capture("C:\\SUCCESS.BIN");
            metric("TARGET_SUCCESS",state==3);finished=1;
        }else {act(21);if(++errors>10)finished=1;}
    }
    if(state==5){metric("TEST_CONTINUE_GATE",1);act(30);return;}
    if(state==4){metric("APP_ERROR",db.error);errors++;finished=1;}
    if(finished){
        TDSNDSTAT soundstats;
        if(inputblocked())return;
        TdSoundGetStats(&soundstats);
        metric("SOUND_STARTS_REVEAL",soundstats.starts[0]);
        metric("SOUND_STARTS_VICTORY",soundstats.starts[1]);
        metric("SOUND_STARTS_WRONG",soundstats.starts[2]);
        metric("SOUND_COMPLETE_REVEAL",soundstats.completions[0]);
        metric("SOUND_COMPLETE_VICTORY",soundstats.completions[1]);
        metric("SOUND_COMPLETE_WRONG",soundstats.completions[2]);
        metric("SOUND_BUSY_SKIPS",soundstats.busySkips);
        metric("SOUND_WRITES",soundstats.portWrites);
        metric("SOUND_LATE_ABORTS",soundstats.lateAborts);
        metric("SOUND_FAILURES",soundstats.failures);
        debug=2;debugupdate();refresh();capture("C:\\DEBUG.BIN");debug=0;
        if(state==3){
            refresh();
            SendMessage(window,WM_LBUTTONDOWN,0,
                MAKELONG((buttons[0].left+buttons[0].right)/2,
                         (buttons[0].top+buttons[0].bottom)/2));
            metric("MOUSE_REPLAY_STARTED",state==1&&engine.turn==0);
        }
        metric("ANIM_CAPTURES",animserial);metric("ANIM_REDRAWS",animredraws);metric("ANIM_MAX_MS",animcost);
        metric("COMPUTE_MAX_MS",computepeak);
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
    if(msg==WM_ACTIVATEAPP)active=wp!=0;
    if(msg==WM_SETCURSOR&&demoReturning)return 1;
    if(demoInput(msg,wp,lp))return 0;
    if((demonstration.enabled||demoDrain)&&
       (msg==WM_KILLFOCUS||(msg==WM_ACTIVATE&&wp==WA_INACTIVE)||
        (msg==WM_ACTIVATEAPP&&!wp)||msg==WM_CANCELMODE)){
        demoCleanup(0);return 0;
    }
    if(msg==WM_SETCURSOR&&(demonstration.enabled||demoDrain)&&
       GetActiveWindow()==w&&GetCapture()==w){SetCursor(NULL);return 1;}
    if(msg==WM_TIMER&&wp==3&&demoQA){demoQATick();return 0;}
    if(msg==WM_QUERYENDSESSION||msg==WM_CLOSE||(msg==WM_ENDSESSION&&wp)){
        if(demonstration.enabled||demoDrain)demoCleanup(0);
        if(!IsWindow(w))return msg==WM_QUERYENDSESSION?1:0;
    }
    if(msg==WM_KILLFOCUS||(msg==WM_ACTIVATE&&wp==0))TdSoundStop(window);
    if(msg==WM_QUERYENDSESSION){TdSoundStop(window);return 1;}
    if(msg==WM_ENDSESSION&&wp){TdSoundStop(window);return 0;}
    if(msg==WM_CLOSE)TdSoundStop(window);
    if(msg==WM_PAINT){draw(w);return 0;}
    if(msg==WM_TIMER){
        if(wp==2&&!tickinside){tickinside=1;animtick();tickinside=0;}
        if(wp==1&&testmode&&!testinside){testinside=1;testtick();testinside=0;}
        return 0;
    }
    if(msg==WM_ACTIVATEAPP){active=wp!=0;
        if(!active)TdSoundStop(window);else {inputready=GetTickCount()+220;refresh();}return 0;}
    if(msg==WM_MOUSEMOVE){look(LOWORD(lp),HIWORD(lp));return 0;}
    if(msg==WM_LBUTTONDOWN){
        x=LOWORD(lp);y=HIWORD(lp);
        if(x>=screenw-49&&x<screenw-6&&y>=183&&y<197){act(99);return 0;}
        if(inputblocked())return 0;
        for(i=0;i<nb;i++)if(x>=buttons[i].left&&x<buttons[i].right&&
           y>=buttons[i].top&&y<buttons[i].bottom){
            if(focus>=0&&focus<nb)InvalidateRect(w,&buttons[focus],FALSE);
            focus=i;act(ids[i]);break;
        }
        return 0;
    }
    if(msg==WM_CHAR&&notebook==6){notetype(wp);return 0;}
    if(msg==WM_KEYDOWN){
        if(lp&0x40000000L)return 0;
        if(wp==VK_F3){
            soundpref=!soundpref;TdSoundEnable(soundpref);
            settingssaved=WriteProfileString("TANDINATOR","Sound",soundpref?"1":"0");
            refresh();return 0;
        }
        if(wp==VK_ESCAPE){
            if(help||debug||explaining||notebook){help=debug=explaining=notebook=0;focus=0;refresh();inputready=GetTickCount()+220;return 0;}
            SendMessage(w,WM_CLOSE,0,0);return 0;
        }
        if(inputblocked())return 0;
        if(wp==VK_F5&&!db.error){TdSoundStop(window);notebook=notebook?0:1;help=debug=explaining=0;focus=0;refresh();inputready=GetTickCount()+220;return 0;}
        if(notebook){
            if(wp==VK_TAB){focus=(focus+1)%nb;refresh();return 0;}
            if(wp==VK_RETURN||wp==VK_SPACE){act(ids[focus]);return 0;}
            return 0;
        }
        if(wp==VK_F1){TdSoundStop(window);help=!help;debug=explaining=0;focus=0;refresh();return 0;}
        if(wp==VK_F2){TdSoundStop(window);debug=debug?0:1;help=explaining=0;focus=0;refresh();return 0;}
        if(wp==VK_F4&&!explaining&&(state==2||state==3)){act(92);return 0;}
        if(wp==VK_TAB){if(nb){
            InvalidateRect(w,&buttons[focus],FALSE);
            focus=(focus+(GetKeyState(VK_SHIFT)<0?nb-1:1))%nb;
            InvalidateRect(w,&buttons[focus],FALSE);UpdateWindow(w);
        }return 0;}
        if(wp==VK_RETURN||wp==VK_SPACE){if(nb)act(ids[focus]);return 0;}
        if(!debug&&!help&&!explaining&&state==1&&wp>='1'&&wp<='5'){act(wp-'1');return 0;}
        if(!debug&&!help&&!explaining&&state==2&&(wp=='Y'||wp=='N'))act(wp=='Y'?20:21);
        return 0;
    }
    if(msg==WM_DESTROY){
        KillTimer(window,2);KillTimer(window,3);TdSoundStop(window);
        if(GetCapture()==window)ReleaseCapture();
        if(demoPeer&&IsWindow(demoPeer))DestroyWindow(demoPeer);
        artfree();ln_close();db_close();if(logfile!=-1)_lclose(logfile);PostQuitMessage(0);return 0;
    }
    return DefWindowProc(w,msg,wp,lp);
}
int PASCAL WinMain(HANDLE inst,HANDLE prev,LPSTR cmd,int show){
    WNDCLASS c;MSG msg;HDC dc;DWORD start;int i,len;HANDLE displaymodule;char modulepath[144];
    instance=inst;
    while(*cmd==' ')cmd++;
    for(i=0;cmd[i];i++)if(cmd[i]=='/'&&cmd[i+1]){
        len=cmd[i+1];if(len>='a'&&len<='z')len-='a'-'A';
        if(len=='D'||len=='S')demoMode=1;
        if(len=='A')demoAuto=demoArmed=1;
        if(len=='C')demoCues=1;
        if(len=='J')demoQA=demoAuto=demoArmed=1;
    }
    if(demoMode&&(prev||FindWindow("TandyTandinatorSaver",NULL)||GetCapture()||GetSysModalWindow()))return 8;
    demoPreviousActive=GetActiveWindow();demoPreviousFocus=GetFocus();
    GetCursorPos(&demoOrigin);
    testmode=!demoMode&&!demoAuto&&!demoQA&&((*cmd=='/'&&cmd[1]=='T')||GetProfileInt("TANDINATOR","Test",0));
    if(testmode&&GetProfileInt("TANDINATOR","Test",0)==2)testmode=2;
    GetModuleFileName(inst,dbpath,sizeof(dbpath));len=lstrlen(dbpath);
    for(i=len-1;i>=0;i--)if(dbpath[i]=='\\'||dbpath[i]==':')break;
    lstrcpy(dbpath+i+1,"TANDY.DAT");
    freespace=GetFreeSpace(0);start=GetTickCount();db_open(&db,dbpath);
    loadms=GetTickCount()-start;if(db.error)state=4;
    else if(!demoMode&&!demoQA){ln_fixture(testmode);ln_open(&db,dbpath);}
    if(testmode||demoQA)logfile=_lcreat("C:\\TANDI.LOG",0);
    metric("WINFLAGS",GetWinFlags());metric("LOAD_MS",loadms);
    metric("ENGINE_BYTES",sizeof(engine));metric("DB_STRUCT_BYTES",sizeof(db));
    metric("FREE_SPACE_BEFORE",freespace);metric("CHARACTERS",db.nc);
    metric("QUESTIONS_AVAILABLE",db.nq);
    screenw=GetSystemMetrics(SM_CXSCREEN);screenh=GetSystemMetrics(SM_CYSCREEN);
    metric("WIDTH",screenw);metric("HEIGHT",screenh);
    displaymodule=GetModuleHandle("DISPLAY");modulepath[0]=0;
    if(displaymodule)GetModuleFileName(displaymodule,modulepath,sizeof(modulepath));
    metric("DISPLAY_MODULE_PRESENT",displaymodule!=0);logtext("DISPLAY_MODULE_PATH",modulepath);
    c.style=CS_DBLCLKS;c.lpfnWndProc=WndProc;c.cbClsExtra=c.cbWndExtra=0;
    c.hInstance=inst;c.hIcon=0;c.hCursor=demoMode?NULL:LoadCursor(0,IDC_ARROW);
    c.hbrBackground=GetStockObject(BLACK_BRUSH);c.lpszMenuName=0;
    c.lpszClassName=demoMode?"TandyTandinatorSaver":"Tandinator02";if(!RegisterClass(&c)){ln_close();db_close();return 1;}
    window=CreateWindow(c.lpszClassName,"TANDINATOR",WS_POPUP,0,0,
                        screenw,screenh,0,0,inst,0);
    if(!window){ln_close();db_close();return 1;}
    sx=screenw>=640?2:1;
    dc=GetDC(window);colors=GetDeviceCaps(dc,NUMCOLORS);mono=colors==2;
    metric("ART_READY",artinit(dc));ReleaseDC(window,dc);
    metric("ART_INIT_MS",artms);metric("ART_DIB_BYTES",sizeof(artbits));
    metric("FREE_SPACE_ART",GetFreeSpace(0));
    layout();
    if(demoMode&&(GetCapture()||GetSysModalWindow()||GetActiveWindow()!=demoPreviousActive)){
        DestroyWindow(window);return 8;
    }
    ShowWindow(window,show);SetActiveWindow(window);SetFocus(window);UpdateWindow(window);
    timerok=SetTimer(window,2,100,0)!=0;
    metric("ANIM_TIMER_READY",timerok);
    soundsupported=TdSoundInit(window,inst,timerok);
    soundsettings();metric("SOUND_READY",soundsupported);metric("SOUND_PREF_LOADED",soundpref);refresh();
    demoWelcome=GetTickCount();
    if(demoMode&&!demoStart()){DestroyWindow(window);return 8;}
    if(demoQA)SetTimer(window,3,100,0);
    if(testmode)SetTimer(window,1,100,0);
    while(GetMessage(&msg,0,0,0)){
        if(!demonstration.enabled&&!demoDrain)TranslateMessage(&msg);
        DispatchMessage(&msg);
    }
    TdSoundStop(window);KillTimer(window,2);return msg.wParam;
}
