/* Tandy grabber installation shared by full Setup and guarded display entry.
 * Only our load= token is owned; unrelated startup commands survive. */
#include "TGID.H"
static int clip_token(const char *word){
 char copy[512],*p,*leaf;unsigned n=(unsigned)strlen(word);
 strcpy(copy,word);if(copy[0]=='"'){memmove(copy,copy+1,n);n--;if(n&&copy[n-1]=='"')copy[n-1]=0;}
 leaf=copy;for(p=copy;*p;p++)if(*p=='\\'||*p=='/')leaf=p+1;
 return !stricmp(leaf,"TGCLIP.EXE");
}
static void clipini(int mode){
 char n[PTH],o[PTH],j[PTH],load[512],result[512],word[512],token[PTH+4];
 unsigned i=0,k=0,w;int quoted,comma=0,h;
 if(mode==KEEP_XRSYNC)return;
 inifile="WIN.INI";ini_changed=0;loadini();sectionvalue("windows","load",load);
 while(load[i]){
  if(load[i]==' '||load[i]=='\t'||load[i]==','){if(load[i]==',')comma=1;i++;continue;}
  w=0;quoted=0;
  do{char c=load[i++];if(c=='"')quoted=!quoted;if(w+1>=sizeof(word))stop("Startup token too long","");word[w++]=c;}
  while(load[i]&&(quoted||(load[i]!=' '&&load[i]!='\t'&&load[i]!=',')));
  word[w]=0;
  if(!clip_token(word)){
   if(k){if(k+2>=sizeof(result))stop("Startup load value too long","");result[k++]=comma?',':' ';if(comma)result[k++]=' ';}
   if(k+w>=sizeof(result))stop("Startup load value too long","");memcpy(result+k,word,w);k+=w;
  }
  comma=0;
 }
 sprintf(token,"%s\\TGCLIP.EXE",win);
 if(k){if(k+1>=sizeof(result))stop("Startup load value too long","");result[k++]=' ';}
 if(k+strlen(token)>280)stop("Startup load value too long","");strcpy(result+k,token);
 if(strcmp(load,result))changeini("windows","load",result);
 if(!ini_changed){inifile="SYSTEM.INI";return;}
 if(checking)stop("TGCLIP startup token needs repair","");
 begin(win,"WIN.INI",n,o,j);h=create(n);writeall(h,(unsigned char*)oldini,(unsigned)strlen(oldini),n);closeout(h,n);commit(win,"WIN.INI",n,o,j);
 puts("WIN.INI: TGCLIP startup installed; other commands preserved.");inifile="SYSTEM.INI";
}
static int grabber_selected(void){
 char value[300],*comment;
 inifile="SYSTEM.INI";loadini();if(inivalue("display.drv",value)!=1)return 0;
 comment=strchr(value,';');if(comment)*comment=0;trim(value);
 return !stricmp(value,"HPXY.DRV")||!stricmp(value,"PANCMP2.DRV")||
  !stricmp(value,"C216N6.DRV")||!stricmp(value,"C23216.DRV")||
  !stricmp(value,"TANDY88.DRV")||!stricmp(value,"TNDY6404.DRV")||
  !stricmp(value,"TNDY160.DRV")||!stricmp(value,"TNDY3204.DRV")||
  !stricmp(value,"TNDY6402.DRV")||!stricmp(value,"TR53216.DRV")||
  !stricmp(value,"TR56404.DRV")||!stricmp(value,"TR51616.DRV")||
  !stricmp(value,"TR53204.DRV")||!stricmp(value,"TR56402.DRV");
}
static int grabber_install(const char *requested){
 char source[PTH],input[PTH],p[PTH],n[PTH],o[PTH],j[PTH];int h;
 display_route=2;not_windows();
 display_absolute(win,requested);path(sys,win,"SYSTEM");
 if(kind(sys)!=2)stop("Windows SYSTEM directory missing",sys);
 if(!grabber_selected()){puts("Another display selected; Tandy grabber unchanged.");return 0;}
 if(!getcwd(source,PTH))stop("Cannot save source directory","");
 path(input,source,"TANDYGR.GR2");if(!pinned_file(input,TG_BYTES,TG_CRC))stop("Tandy grabber source missing or damaged",input);
 path(p,source,"TGCLIP.EXE");if(!pinned_file(p,CLIP_BYTES,CLIP_CRC))stop("TGCLIP source missing or damaged",p);
 path(p,win,"TANDYGR.GR2");if(kind(p))stop("Root grabber shadows SYSTEM target",p);
 path(p,win,"SIMPLE.JRN");if(kind(p))stop("Finish pending Windows transaction first",p);
 path(p,sys,"SIMPLE.JRN");if(kind(p))stop("Finish pending SYSTEM transaction first",p);
 /* Validate SYSTEM.INI before copying. Refuse pending journals above;
  * each updated file uses the existing checked rename transaction. */
 loadini();changeini("boot","286grabber","TANDYGR.GR2");
 total=TG_BYTES+CLIP_BYTES+CAP;done=0;last=-1;space();
 path(p,sys,"TANDYGR.GR2");if(!pinned_file(p,TG_BYTES,TG_CRC))replace_file(input,sys,"TANDYGR.GR2");
 path(input,source,"TGCLIP.EXE");path(p,win,"TGCLIP.EXE");if(!pinned_file(p,CLIP_BYTES,CLIP_CRC))replace_file(input,win,"TGCLIP.EXE");
 if(ini_changed){begin(win,"SYSTEM.INI",n,o,j);h=create(n);writeall(h,(unsigned char*)oldini,(unsigned)strlen(oldini),n);closeout(h,n);commit(win,"SYSTEM.INI",n,o,j);}
 clipini(3);puts("Tandy DOS/clipboard support installed.");return 0;
}
