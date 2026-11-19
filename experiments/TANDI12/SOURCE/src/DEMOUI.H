/* Own-window input only. No global hook, input synthesis, settings or learning. */
static void demoDraw(HDC dc){
    RECT r;int left,x,y;char nm[40],q[80];COLORREF gold;
    if(demoDrain||demonstration.phase==DEMO_DARK)return;
    gold=colors<16?RGB(255,255,255):RGB(255,255,0);
    x=demonstration.side%2?screenw-108*sx:0;
    y=(demonstration.side/2)*7;
    SetViewportOrg(dc,x,y);mascot(dc);SetViewportOrg(dc,0,0);
    left=x?6*sx:104*sx;
    r.left=left;r.right=left+210*sx;r.top=46+y;r.bottom=r.top+47;
    SetTextColor(dc,RGB(255,255,255));SetBkColor(dc,RGB(0,0,0));
    db_name(&db,demonstration.target,nm);
    if(demonstration.phase==DEMO_TITLE){
        wrapped(dc,"WATCH THE ORACLE GUESS",&r);r.top+=45;r.bottom+=45;wrapped(dc,nm,&r);
    }else if(demonstration.phase==DEMO_QUESTION||demonstration.phase==DEMO_ANSWER){
        db_question(&db,engine.current,q);wrapped(dc,q,&r);
        r.top+=50;r.bottom+=50;
        wrapped(dc,demonstration.phase==DEMO_ANSWER?factwords[demonstration.answer]:"CONSULTING...",&r);
    }else if(demonstration.phase==DEMO_GUESS){
        wrapped(dc,"I SUSPECT...",&r);r.top+=30;r.bottom+=30;
        db_name(&db,engine.best,nm);wrapped(dc,nm,&r);
    }else if(demonstration.phase==DEMO_SUCCESS){
        wrapped(dc,"THE ORACLE HAS FOUND",&r);r.top+=30;r.bottom+=30;wrapped(dc,nm,&r);
    }
    sprite(dc,demonstration.side%2?8*sx:screenw-134*sx,4+y,126,16,0,360);
    SetTextColor(dc,gold);
    text(dc,left,170-y,"DEMO - ANY INPUT STOPS");
}
static int demoKeysHeld(void){
    int i;for(i=1;i<256;i++)if(demoDown[i]||(GetAsyncKeyState(i)&0x8000))return 1;
    return demoMouse!=0;
}
static void demoBlank(void){
    HDC dc;TdSoundStop(window);dc=GetDC(window);
    if(dc){box(dc,0,0,screenw,screenh,RGB(0,0,0));ReleaseDC(window,dc);}
}
static void demoCleanup(int returnFocus){
    HWND previous=demoPreviousActive,focusBefore=demoPreviousFocus;
    HCURSOR current;int owned;
    if(demoReturning)return;demoReturning=1;
    owned=GetActiveWindow()==window&&GetCapture()==window;
    demonstration.enabled=demoDrain=0;TdSoundStop(window);animframe=-1;
    if(owned){
        /* Preserve a foreign cursor replacement even if ownership changed. */
        current=SetCursor(NULL);SetCursor(current);
        if(!current)SetCursor(demoPreviousCursor);
    }
    if(GetCapture()==window)ReleaseCapture();demoOwned=0;
    TdSoundEnable(soundpref);
    if(demoMode){
        if(returnFocus&&owned&&previous&&IsWindow(previous)){
            SetActiveWindow(previous);
            if(focusBefore&&IsWindow(focusBefore))SetFocus(focusBefore);
        }
        DestroyWindow(window);
    }else{
        eng_reset(&engine,&db);obs_reset(&history);state=0;help=debug=explaining=0;
        focus=busy=pending=capoffered=0;inputready=GetTickCount()+220;
        if(returnFocus&&owned)SetFocus(window);
        refresh();
    }
    demoReturning=0;
}
static int demoStart(void){
    int i;
    if(demonstration.enabled||demoDrain||busy||state!=0||history.count||
       help||debug||explaining||!timerok||db.error||GetCapture()||
       GetSysModalWindow()||GetActiveWindow()!=window||GetFocus()!=window)return 0;
    if(!demoMode){demoPreviousActive=window;demoPreviousFocus=window;}
    GetKeyboardState(demoInitial);
    for(i=0;i<256;i++){
        demoInitial[i]&=0x80;demoDown[i]=(BYTE)(demoInitial[i]?1:0);
    }
    demoMouse=demoMouseGesture=0;
    if(demoInitial[VK_LBUTTON])demoMouse|=MK_LBUTTON;
    if(demoInitial[VK_RBUTTON])demoMouse|=MK_RBUTTON;
    if(demoInitial[VK_MBUTTON])demoMouse|=MK_MBUTTON;
    GetCursorPos(&demoOrigin);ScreenToClient(window,&demoOrigin);
    demoStarted=demoLastInput=GetTickCount();
    if(!demo_init(&demonstration,&engine,&db,&history,(U32)demoStarted))return 0;
    SetCapture(window);demoOwned=GetCapture()==window;
    if(!demoOwned||GetActiveWindow()!=window||GetFocus()!=window){demoCleanup(0);return 0;}
    TdSoundStop(window);TdSoundEnable(demoCues&&soundpref);
    demoPreviousCursor=SetCursor(NULL);demoArmed=0;nb=0;state=0;
    lookx=looky=0;animframe=-1;animticks=idleticks=0;
    InvalidateRect(window,0,FALSE);UpdateWindow(window);return 1;
}
static void demoWake(void){
    if(!demoDrain){demoDrain=1;demoWakeCount++;demoBlank();}
    demoLastInput=GetTickCount();
}
static int demoInput(UINT m,WORD wp,LONG lp){
    int was,dx,dy;
    if(!demonstration.enabled&&!demoDrain){
        if((m>=WM_KEYFIRST&&m<=WM_KEYLAST)||
           (m>=WM_MOUSEFIRST&&m<=WM_MOUSELAST&&m!=WM_MOUSEMOVE))demoArmed=0;
        else if(m==WM_MOUSEMOVE){
            dx=(int)LOWORD(lp)-demoOrigin.x;dy=(int)HIWORD(lp)-demoOrigin.y;
            if(dx||dy)demoArmed=0;
        }
        return 0;
    }
    if(m>=WM_KEYFIRST&&m<=WM_KEYLAST){
        if(m==WM_KEYDOWN||m==WM_SYSKEYDOWN){if(wp<256)demoDown[wp]=1;demoWake();}
        else if(m==WM_KEYUP||m==WM_SYSKEYUP){
            was=wp<256?demoInitial[wp]:0;
            if(wp<256)demoDown[wp]=demoInitial[wp]=0;
            if(!was||GetTickCount()-demoStarted>=250UL||demoDrain)demoWake();
        }else demoWake();
        return 1;
    }
    if(m>=WM_MOUSEFIRST&&m<=WM_MOUSELAST){
        if(m!=WM_MOUSEMOVE)demoMouseGesture=1;
        demoMouse=wp&(MK_LBUTTON|MK_RBUTTON|MK_MBUTTON);
        if(m==WM_LBUTTONDOWN||m==WM_LBUTTONDBLCLK)demoMouse|=MK_LBUTTON;
        if(m==WM_RBUTTONDOWN||m==WM_RBUTTONDBLCLK)demoMouse|=MK_RBUTTON;
        if(m==WM_MBUTTONDOWN||m==WM_MBUTTONDBLCLK)demoMouse|=MK_MBUTTON;
        if(m==WM_LBUTTONUP)demoMouse&=~MK_LBUTTON;
        if(m==WM_RBUTTONUP)demoMouse&=~MK_RBUTTON;
        if(m==WM_MBUTTONUP)demoMouse&=~MK_MBUTTON;
        dx=(int)LOWORD(lp)-demoOrigin.x;dy=(int)HIWORD(lp)-demoOrigin.y;
        if(m!=WM_MOUSEMOVE||dx||dy)demoWake();
        return 1;
    }
    return 0;
}
static void demoDrainTick(void){
    MSG msg;DWORD quiet=demoMouseGesture?(DWORD)GetDoubleClickTime():220UL;
    if(quiet<220UL)quiet=220UL;
    if(GetActiveWindow()!=window||GetFocus()!=window||GetCapture()!=window){demoCleanup(0);return;}
    while(PeekMessage(&msg,window,WM_KEYFIRST,WM_KEYLAST,PM_REMOVE))
        demoInput(msg.message,msg.wParam,msg.lParam);
    while(PeekMessage(&msg,window,WM_MOUSEFIRST,WM_MOUSELAST,PM_REMOVE))
        demoInput(msg.message,msg.wParam,msg.lParam);
    if(demoKeysHeld()){demoLastInput=GetTickCount();return;}
    if(GetTickCount()-demoLastInput<quiet)return;
    demoCleanup(1);
}
static void demoPulse(void){
    int event;DWORD now=GetTickCount();
    if(GetActiveWindow()!=window||GetCapture()!=window||GetFocus()!=window){demoCleanup(0);return;}
    TdSoundTick(window,now);
    event=demo_step(&demonstration,&engine,&db,&history,now);
    if(event<0){demoCleanup(1);return;}
    if(event){
        state=demonstration.phase==DEMO_GUESS?2:(demonstration.phase==DEMO_SUCCESS?3:0);
        animticks=0;animframe=state==2?1:(state==3?3:-1);
        if(event&DEMO_STOPCUE)TdSoundStop(window);
        if(event&DEMO_REVEAL)TdSoundBegin(window,TD_SND_REVEAL,GetTickCount());
        if(event&DEMO_VICTORY)TdSoundBegin(window,TD_SND_VICTORY,GetTickCount());
        InvalidateRect(window,0,FALSE);UpdateWindow(window);
    }else{
        if(state==2||state==3){
            if(animticks<10){animticks++;
                if(!(animticks%2))animset(state==2?(animticks%4?1:2):(animticks%4?3:4));
            }
        }else if(demonstration.phase!=DEMO_DARK){
            idleticks++;lookx=(idleticks/4)%3-1;looky=(idleticks/12)%3-1;
            if(idleticks==36)animset(0);
            if(idleticks>=38){animset(-1);idleticks=0;}
            InvalidateRect(window,0,FALSE);
        }
    }
}
/* /J is a bounded native fixture; all messages target our own window.
   It advances demo deadlines for coverage, not production timing. */
LONG FAR PASCAL DemoPeerProc(HWND w,UINT m,WORD wp,LONG lp){
    if((m>=WM_KEYFIRST&&m<=WM_KEYLAST)||(m>=WM_MOUSEFIRST&&m<=WM_MOUSELAST)){
        if(m!=WM_MOUSEMOVE)demoInputLeaks++;return 0;
    }
    return DefWindowProc(w,m,wp,lp);
}
static void demoQACheck(char *key,int ok){metric(key,ok);if(!ok)demoQAErrors++;}
static void demoQANew(void){
    BringWindowToTop(window);SetActiveWindow(window);SetFocus(window);state=0;eng_reset(&engine,&db);obs_reset(&history);
    demoQACheck("DEMO_START",demoStart());demoTestTicks=0;
}
static void demoQATick(void){
    int i,old;char path[30],n[12];TDSNDSTAT stats;
    if(++demoTestTicks>1400){metric("DEMO_TIMEOUT",1);SendMessage(window,WM_CLOSE,0,0);return;}
    if(!demoTestStage){
        WNDCLASS c;
        c.style=0;c.lpfnWndProc=DemoPeerProc;c.cbClsExtra=c.cbWndExtra=0;
        c.hInstance=instance;c.hIcon=0;c.hCursor=LoadCursor(NULL,IDC_CROSS);
        c.hbrBackground=GetStockObject(WHITE_BRUSH);c.lpszMenuName=0;c.lpszClassName="TandiDemoPeer";
        RegisterClass(&c);demoPeer=CreateWindow(c.lpszClassName,"DEMO QA",WS_POPUP,
                            0,0,screenw,screenh,0,0,instance,0);
        ShowWindow(demoPeer,SW_SHOWNOACTIVATE);
        BringWindowToTop(window);
        SetActiveWindow(window);SetFocus(window);
        demoQASoundPref=soundpref;demoQAInitialSetting=GetProfileInt("TANDINATOR","Sound",-1);
        demoQACheck("DEMO_TEST_PROFILE_SUPPRESSED",!testmode);
        /* Opt-in idle arm never starts on an active game. */
        state=1;history.count=1;demoWelcome=GetTickCount()-DEMO_IDLE_MS;
        animtick();demoQACheck("DEMO_NO_MIDGAME_ACTIVATION",!demonstration.enabled);
        state=0;history.count=0;demoArmed=0;animtick();
        demoQACheck("DEMO_DISARMED_STAYS_OFF",!demonstration.enabled);
        demoArmed=1;animtick();demoQACheck("DEMO_IDLE_ACTIVATES",demonstration.enabled);
        demoQACheck("DEMO_CUES_OPTIN",TdSoundEnabled()==(demoCues&&soundpref));
        demoTestStage=1;demoTestTicks=0;return;
    }
    if(demoTestStage==1){
        if(!demonstration.enabled){demoQACheck("DEMO_CYCLE_ALIVE",0);demoTestStage=99;return;}
        if(++demoQAPhases%3==0){
            demonstration.due=GetTickCount();demoPulse();
            if(demonstration.phase==DEMO_SUCCESS){
                for(i=0;i<8;i++)if(demonstration.target==(int)demonstration.roster[i])demoQASeen[i]++;
            }
            if(demoQAFrames<36){
                lstrcpy(path,"C:\\D");number(n,demoQAFrames++);lstrcat(path,n);lstrcat(path,".BIN");capture(path);
                metric("DEMO_FRAME_PHASE",demonstration.phase);metric("DEMO_FRAME_SIDE",demonstration.side);
            }
        }else if(demonstration.phase==DEMO_QUESTION&&demoQAEyes<6){
            lookx=demoQAEyes%3-1;looky=demoQAEyes/3;animframe=-1;
            InvalidateRect(window,0,FALSE);UpdateWindow(window);
            lstrcpy(path,"C:\\DEYE");number(n,demoQAEyes++);lstrcat(path,n);lstrcat(path,".BIN");capture(path);
            metric("DEMO_EYE_SIDE",demonstration.side);
        }
        if(demonstration.games<8)return;
        old=1;for(i=0;i<8;i++)if(demoQASeen[i]!=1)old=0;
        demoQACheck("DEMO_EIGHT_TARGETS",old);
        TdSoundGetStats(&stats);metric("DEMO_SOUND_WRITES",stats.portWrites);
        demoQACheck("DEMO_SOUND_OFF_QUIET",(demoCues&&soundpref)||!stats.portWrites);
        demoQACheck("DEMO_DEFAULT_QUIET",demoCues||!stats.portWrites);
        demoCleanup(1);demoTestStage=2;demoQACase=0;return;
    }
    if(demoTestStage==2){
        demoQANew();
        if(demoQACase==0){
            SendMessage(window,WM_MOUSEMOVE,0,MAKELONG(demoOrigin.x,demoOrigin.y));
            demoQACheck("DEMO_IDENTICAL_MOVE_IGNORED",demonstration.enabled&&!demoDrain);
            demoInitial[VK_F1]=demoDown[VK_F1]=1;demoStarted=GetTickCount();
            SendMessage(window,WM_KEYUP,VK_F1,0);
            demoQACheck("DEMO_INITIAL_RELEASE_IGNORED",!demoDrain);
            SendMessage(window,WM_KEYDOWN,VK_F3,0);
            SendMessage(window,WM_KEYDOWN,VK_F3,0x40000000L);
            SendMessage(window,WM_CHAR,'x',0);
            PostMessage(window,WM_KEYDOWN,VK_RETURN,0);
            PostMessage(window,WM_CHAR,13,0);
            PostMessage(window,WM_KEYUP,VK_RETURN,0);
            demoQACheck("DEMO_FIRST_KEY_BLANKS",demoDrain);
            capture("C:\\DWAKE.BIN");
            demoQACheck("DEMO_F3_NO_WRITE",soundpref==demoQASoundPref&&
                (int)GetProfileInt("TANDINATOR","Sound",-1)==demoQAInitialSetting);
            TdSoundGetStats(&stats);demoQACheck("DEMO_WAKE_STOPS_SOUND",!stats.playing);
            demoQAHeldTicks=0;demoTestStage=3;return;
        }
        if(demoQACase==1){
            SendMessage(window,WM_LBUTTONDOWN,MK_LBUTTON,MAKELONG(210*sx,130));
            SendMessage(window,WM_LBUTTONDBLCLK,MK_LBUTTON,MAKELONG(210*sx,130));
            demoQAHeldTicks=0;demoTestStage=3;return;
        }
        if(demoQACase==2){
            SendMessage(window,WM_MOUSEMOVE,0,MAKELONG(demoOrigin.x+1,demoOrigin.y));
            demoQACheck("DEMO_REAL_MOVE_WAKES",demoDrain);demoTestStage=4;return;
        }
        if(demoQACase==3){
            SetCapture(demoPeer);demoPulse();
            demoQACheck("DEMO_FOREIGN_CAPTURE_PRESERVED",!demonstration.enabled&&GetCapture()==demoPeer);
            ReleaseCapture();demoTestStage=5;return;
        }
        if(demoQACase==4){
            SetCursor(LoadCursor(NULL,IDC_CROSS));SetFocus(demoPeer);
            demoQACheck("DEMO_FOCUS_LOSS_STOPS",!demonstration.enabled&&GetFocus()==demoPeer);
            {HCURSOR cursor=SetCursor(NULL);SetCursor(cursor);
                demoQACheck("DEMO_FOREIGN_CURSOR_PRESERVED",cursor==LoadCursor(NULL,IDC_CROSS));}
            demoTestStage=5;return;
        }
        if(demoQACase==5){
            SendMessage(window,WM_CANCELMODE,0,0);
            demoQACheck("DEMO_CANCEL_STOPS",!demonstration.enabled&&GetCapture()!=window);
            demoTestStage=5;return;
        }
        if(demoQACase==6){
            SendMessage(window,WM_SYSKEYDOWN,VK_MENU,0);
            SendMessage(window,WM_SYSCHAR,'x',0);
            SendMessage(window,WM_SYSKEYUP,VK_MENU,0);
            demoQACheck("DEMO_SYSTEM_KEY_CONSUMED",demoDrain);demoTestStage=4;return;
        }
        if(demoQACase==7){
            SendMessage(window,WM_ACTIVATEAPP,0,0);
            demoQACheck("DEMO_TASK_SWITCH_STOPS",!demonstration.enabled&&GetCapture()!=window);
            demoQACheck("DEMO_INACTIVE_ANIMATION_STOPS",!active);
            SendMessage(window,WM_ACTIVATEAPP,1,0);demoTestStage=5;return;
        }
        /* Dedicated /S restoration shares this exact close path. */
        demoMode=1;demoPreviousActive=demoPreviousFocus=demoPeer;
        SendMessage(window,WM_KEYDOWN,VK_RETURN,0);
        SendMessage(window,WM_KEYUP,VK_RETURN,0);
        demoQACheck("DEMO_SETTING_UNCHANGED",soundpref==demoQASoundPref&&
            (int)GetProfileInt("TANDINATOR","Sound",-1)==demoQAInitialSetting);
        demoQACheck("DEMO_NO_INPUT_LEAKS",!demoInputLeaks);
        demoQACheck("DEMO_NATIVE_ALL_CHECKS",!demoQAErrors);
        metric("ERRORS",demoQAErrors);metric("COMPLETE",1);demoTestStage=6;return;
    }
    if(demoTestStage==3){
        if(++demoQAHeldTicks<5)return;
        demoQACheck("DEMO_HELD_DRAIN",demoDrain&&GetCapture()==window);
        if(!demoQACase)SendMessage(window,WM_KEYUP,VK_F3,0);
        else SendMessage(window,WM_LBUTTONUP,0,0);
        demoTestStage=4;return;
    }
    if(demoTestStage==4){
        if(demoQACase==1&&demoQAHeldTicks<10){
            if(++demoQAHeldTicks<9)return;
            demoQACheck("DEMO_DELAYED_DOUBLE_CLICK_DRAIN",demoDrain&&GetCapture()==window);
            SendMessage(window,WM_LBUTTONDBLCLK,MK_LBUTTON,0);
            SendMessage(window,WM_LBUTTONUP,0,0);demoQAHeldTicks=10;
        }
        if(demoDrain)return;
        demoQACheck("DEMO_WAKE_NO_GAME_ACTION",state==0&&engine.turn==0&&history.count==0&&!help&&!debug&&!explaining);
        demoQACheck("DEMO_DRAIN_RELEASED",GetCapture()!=window);
        demoQACheck("DEMO_IDLE_NOT_REARMED",!demoArmed);demoTestStage=5;
    }
    if(demoTestStage==5){demoQACase++;demoTestStage=2;return;}
    if(demoTestStage==99){metric("ERRORS",demoQAErrors+1);metric("COMPLETE",1);SendMessage(window,WM_CLOSE,0,0);}
}
