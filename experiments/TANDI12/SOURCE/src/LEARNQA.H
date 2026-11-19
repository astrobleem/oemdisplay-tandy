/* First-party /T checks only; production handlers and file paths exercised. */
static void check11(char *key,int ok){metric(key,ok);if(!ok)errors++;}
static void fortysetup(int count){
 testprepare();while(engine.turn<count){eng_choose(&engine,&db);obs_answer(&history,&engine,&db,2);}
 questionlimit=40;nextcompute();inputready=0;
}
static void learningtest(void){
 int i,q,n,base,cells,sessions,fail;U8 row[TD_ROW];U32 id;
 metric("L11_INITIAL_SESSIONS",ln_sessions());logtext("L11_INITIAL_STATUS",(char *)ln_status());
 fail=GetProfileInt("TANDINATOR","LearnFail",0);check11("L11_DEFAULT_OFF",!learnuse&&ln_ready());
 /* 38 -> 40, 39 -> 40, never question 41; used real unique question IDs. */
 fortysetup(38);questionlimit=38;nextcompute();inputready=0;act(21);inputready=0;act(31);
 check11("Q11_38_ASK_LIMIT40",questionlimit==40&&state==1);inputready=0;act(2);inputready=0;act(2);
 check11("Q11_38_TO_40",state==2&&engine.turn==40&&history.count==40);
 check11("Q11_FORTY_CLUES",obs_explain(&history,&engine,&db,&explanation)&&explanation.count==40);
 inputready=0;act(21);check11("Q11_40_CONCEDES",state==6&&engine.turn==40);
 inputready=0;act(2);check11("Q11_NO_41",state==6&&engine.turn==40);
 capture("C:\\LOSS11.BIN");inputready=0;act(104);capture("C:\\PICK11.BIN");
 check11("Q11_PICKER_DEFAULT_SKIP",notebook==6&&ids[focus]==90);
 inputready=0;act(121);check11("Q11_NOTLISTED_SKIP",notebook==0&&reportid<0);
 sessions=ln_sessions();inputready=0;act(104);inputready=0;act(120);
 check11("Q11_LOSS_ID_NO_AUTO_SAVE",state==8&&notebook==0&&ln_sessions()==sessions);
 fortysetup(39);questionlimit=39;nextcompute();inputready=0;act(21);inputready=0;act(31);
 check11("Q11_39_ASK_LIMIT40",questionlimit==40&&state==1);inputready=0;act(2);check11("Q11_39_TO_40",state==2&&engine.turn==40&&history.count==40);
 inputready=0;act(21);inputready=0;act(10);check11("Q11_RESTART_RESET",state==1&&engine.turn==0&&questionlimit==25);
 fortysetup(25);questionlimit=25;nextcompute();inputready=0;act(21);inputready=0;act(31);
 check11("Q11_ASK_TWO_STARTS",state==1&&questionlimit==27&&engine.turn==25);
 act(2);check11("Q11_REPEATED_CLICK_GUARD",engine.turn==25);
 inputready=0;act(2);inputready=0;act(2);check11("Q11_EXACT_TWO",state==2&&engine.turn==27);
 testprepare();for(i=0;i<(int)db.nq;i++)engine.asked[i]=1;engine.turn=25;questionlimit=27;nextcompute();
 check11("Q11_EXHAUSTED_NO_LOOP",state==2&&engine.current<0&&engine.turn==25&&!pending);
 /* Explicitly reviewed base-UNKNOWN reports, not a guessed identity write. */
 testprepare();obs_reset(&history);db_row(&db,128,row);
 for(q=0;q<(int)db.nq&&history.count<3;q++)if(db_value(row,q)==2){i=history.count++;history.q[i]=(U16)q;history.a[i]=4;}
 engine.turn=history.count;reportid=128;state=3;gamesession=ln_next();n=ln_review(&db,reportid,&history);
 check11("L11_REVIEW_THREE",n==3);cells=ln_cells();sessions=ln_sessions();id=gamesession;
 inputready=0;act(100);check11("L11_REVIEW_DEFAULT_SKIP",notebook==4&&ids[focus]==90);capture("C:\\REVIEW11.BIN");
 check11("L11_REVIEW_NOT_SAVED",ln_sessions()==sessions&&ln_cells()==cells);
 inputready=0;act(117);
 if(fail){check11("L11_SAVE_FAIL_RETAINS",ln_sessions()==sessions&&ln_cells()==cells);capture("C:\\FAIL11.BIN");notebook=0;testprepare();return;}
 check11("L11_EXPLICIT_SAVE",ln_sessions()==sessions+1&&ln_cells()==3&&ln_active()==0);
 check11("L11_DEDUP",!ln_save(&db,reportid,&history,id,0)&&ln_sessions()==sessions+1);
 gamesession=ln_next();check11("L11_SECOND_REPORT",ln_save(&db,reportid,&history,gamesession,0)&&ln_active()==3);
 eng_reset(&engine,&db);engine.turn=25;learnuse=1;gamelearn=1;state=2;nextcompute();
 check11("L11_NATIVE_TIE_ONLY",engine.best==128&&engine.second==0&&learnchanged);
 for(i=0;i<(int)db.nc;i++)if(engine.score[i])break;check11("L11_BASE_SCORES_UNCHANGED",i==(int)db.nc);
 capture("C:\\TIE11.BIN");eng_reject(&engine,&db);check11("L11_REJECT_DISPLAYED",engine.rejected[128]&&engine.best==0);
 learnuse=gamelearn=0;
 gamesession=ln_next();check11("L11_NO_FEEDBACK",!ln_save(&db,reportid,&history,gamesession,1));
 history.a[0]=0;check11("L11_CONFLICT",ln_save(&db,reportid,&history,gamesession,0)&&ln_conflicts()==1&&ln_active()==2);
 sessions=ln_sessions();ln_close();check11("L11_RELAUNCH_LOAD",ln_open(&db,dbpath)&&ln_sessions()==sessions&&ln_conflicts()==1);
 notebook=1;refresh();capture("C:\\NOTES11.BIN");inputready=0;act(110);
 check11("L11_EXPERIMENT_ON",learnuse&&gamelearn);inputready=0;act(110);check11("L11_TOGGLE_OFF",!learnuse&&gamelearn);
 inputready=0;act(111);inputready=0;act(113);check11("L11_RESET_KEEPS_IDS",ln_cells()==0&&ln_sessions()==sessions&&!learnuse);
 inputready=0;notebook=1;act(112);inputready=0;act(114);check11("L11_FRESH_EMPTY",ln_cells()==0&&ln_sessions()==0&&ln_next()==1&&!learnuse);
 testprepare();obs_reset(&history);history.count=1;history.q[0]=0;history.a[0]=4;engine.turn=25;eng_rank(&engine,&db);base=engine.best;
 ln_tie(&engine,&db,&history);check11("L11_EMPTY_SAME_ENGINE",engine.best==base);
 notebook=0;testprepare();
}
