/* Own-window 320x200 notebook controls; no standard dialogs. */
static void notelayout(void){
 addbutton(90,"BACK / SKIP [ESC]",8*sx,163,304*sx,16);
 if(notebook==1){
  if(ln_ready()){
   addbutton(110,learnuse?"USE NOTES: ON":"USE NOTES: OFF",8*sx,115,304*sx,16);
   addbutton(111,"RESET ANSWERS",8*sx,137,148*sx,16);
   addbutton(112,"FRESH NOTEBOOK",164*sx,137,148*sx,16);
  }
 }else if(notebook==2||notebook==3){
  addbutton(notebook==2?113:114,notebook==2?"CONFIRM RESET":"ARCHIVE / FRESH",8*sx,136,148*sx,20);
 }else if(notebook==4){
  int n=ln_review(&db,reportid,&history);
  if(reviewpage>0)addbutton(115,"PREV",8*sx,137,72*sx,16);
  if(reviewpage+1<n)addbutton(116,"NEXT",86*sx,137,72*sx,16);
  addbutton(117,"SAVE REPORT",164*sx,137,148*sx,16);
 }else if(notebook==6){
  addbutton(118,"PREV",8*sx,115,72*sx,16);
  addbutton(119,"NEXT",86*sx,115,72*sx,16);
  addbutton(120,"CONFIRM IDENTITY",164*sx,115,148*sx,16);
  addbutton(121,"NOT LISTED / SKIP",8*sx,137,148*sx,16);
 }
}
static void noteparagraph(HDC dc,char *s,int y,int bottom){RECT r;r.left=8*sx;r.right=312*sx;r.top=y;r.bottom=bottom;DrawText(dc,s,-1,&r,DT_WORDBREAK|DT_NOPREFIX);}
static void notedraw(HDC dc){
 char num[20],nm[40],qtext[80];int q,a,n,preview;
 if(notebook==1){
  text(dc,8*sx,43,"Experimental: wrong reports can hurt.");
  text(dc,8*sx,55,"Use only for score ties after Q25.");
  lstrcpy(line,"Cells ");number(num,ln_cells());lstrcat(line,num);lstrcat(line,"/256. Games ");number(num,ln_sessions());lstrcat(line,num);lstrcat(line,"/128.");text(dc,8*sx,68,line);
  lstrcpy(line,"Agreed ");number(num,ln_active());lstrcat(line,num);lstrcat(line,". Conflicts ");number(num,ln_conflicts());lstrcat(line,num);lstrcat(line," (inactive).");text(dc,8*sx,80,line);
  noteparagraph(dc,(char *)ln_status(),92,114);
 }else if(notebook==2){
  noteparagraph(dc,"Reset all reported answers? Saved game IDs remain to prevent duplicates. A full game ledger stays full. Fresh notebook archives it.",48,126);
 }else if(notebook==3){
  noteparagraph(dc,"Preserve reports in free archive files, then start fresh? Compatible books use NOTE names; unreadable or other-DAT files use OLD_ names. Guessing use turns OFF.",48,126);
 }else if(notebook==4){
  db_name(&db,reportid,nm);noteparagraph(dc,nm,43,70);
  text(dc,8*sx,70,"Confirmed identity. Save is optional.");
  n=ln_review(&db,reportid,&history);
  if(ln_detail(&db,reportid,&history,reviewpage,&q,&a)){
   db_question(&db,q,qtext);noteparagraph(dc,qtext,84,113);
   lstrcpy(line,"Your answer: ");lstrcat(line,factwords[a]);text(dc,8*sx,115,line);
  }
  preview=ln_preview(reportid,q,a);number(num,reviewpage+1);lstrcpy(line,num);lstrcat(line,"/");number(num,n);lstrcat(line,num);
  lstrcat(line,preview==2?": CONFLICT - DISABLES NOTE":preview==1?": AGREES WITH REPORTS":": FIRST REPORT");text(dc,8*sx,125,line);
 }else if(notebook==5){noteparagraph(dc,(char *)ln_status(),48,96);text(dc,8*sx,108,"F5 manages the notebook.");}
 else if(notebook==6){
  text(dc,8*sx,43,"Who were you thinking of? Optional.");text(dc,8*sx,55,"Type a name prefix, or Prev / Next.");
  lstrcpy(line,"Find: ");lstrcat(line,picktext);text(dc,8*sx,68,line);
  db_name(&db,pickid,nm);noteparagraph(dc,nm,82,111);
  text(dc,8*sx,156,"Unlisted names cannot be learned yet.");
 }
}
static int noteact(int id){
 if(id==90){notebook=0;focus=0;refresh();inputready=GetTickCount()+220;return 1;}
 if(notebook==1&&id==110&&ln_ready()){learnuse=!learnuse;if(learnuse&&history.count>0)gamelearn=1;}
 else if(notebook==1&&id==111)notebook=2;
 else if(notebook==1&&id==112)notebook=3;
 else if(notebook==2&&id==113){ln_reset(&db);learnuse=0;notebook=5;}
 else if(notebook==3&&id==114){if(ln_fresh(&db)){learnuse=0;gamesession=0;reportid=-1;}notebook=5;}
 else if(notebook==4&&id==115){if(reviewpage>0)reviewpage--;}
 else if(notebook==4&&id==116){if(reviewpage+1<ln_review(&db,reportid,&history))reviewpage++;}
 else if(notebook==4&&id==117){ln_save(&db,reportid,&history,gamesession,gamelearn||demonstration.enabled||demoMode);notebook=5;}
 else if(notebook==6&&id==118){pickid=(pickid+db.nc-1)%db.nc;picktext[0]=0;}
 else if(notebook==6&&id==119){pickid=(pickid+1)%db.nc;picktext[0]=0;}
 else if(notebook==6&&id==120){
  reportid=pickid;state=8;db_name(&db,reportid,name);
  if(!gamelearn&&ln_ready()&&ln_review(&db,reportid,&history)>0){notebook=4;reviewpage=0;}
  else {notebook=0;} /* confirmed named edition, no automatic report */
 }else if(notebook==6&&id==121){notebook=0;reportid=-1;}
 else return 0;
 focus=0;refresh();inputready=GetTickCount()+220;return 1;
}
static void notetype(WORD key){
 char nm[40];int i,j,n;char c;if(inputblocked())return;n=lstrlen(picktext);
 if(key==8){if(n)picktext[--n]=0;}
 else if(key>=32&&key<=126&&n<30){picktext[n++]=(char)key;picktext[n]=0;}else return;
 for(i=0;i<(int)db.nc;i++){
  db_name(&db,i,nm);for(j=0;j<n;j++){c=nm[j];if(c>='a'&&c<='z')c=(char)(c-32);if((int)c!=((picktext[j]>='a'&&picktext[j]<='z')?picktext[j]-32:picktext[j]))break;}
  if(j==n){pickid=i;break;}
 }
 refresh();
}
