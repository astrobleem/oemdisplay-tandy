/* Uses FIXXT's checked file and INI transactions. No resident DOS helper. */
#include "PANPINS.H"
#include "PANSTART.C"
static void pan_startup(const char *key,const char *add){
 char before[512],result[512];sectionvalue("windows",key,before);
 if(!PanStartupEdit(before,add,result,sizeof(result)))stop("Malformed or oversized panning startup",key);
 /* Existing FIXXT changeini uses a 300-byte key=value/CRLF buffer. */
 if(strlen(key)+strlen(result)>296U)stop("Panning startup line too long",key);
 if(strcmp(before,result))changeini("windows",key,result);
}
static int pan_install(const char *requested,const char *source){
 char value[512],marker[512],*comment,*leaf,token[PTH+4];
 char input[PTH],dest[PTH],n[PTH],o[PTH],j[PTH];unsigned i;int h,automatic=1;
 const char *owner=0;
 /* Full repair passes global win; _fullpath cannot use it in place. */
 if(strlen(requested)>=sizeof(input))stop("Windows path too long",requested);
 strcpy(input,requested);
 display_route=3;not_windows();display_absolute(win,input);path(sys,win,"SYSTEM");
 if(kind(sys)!=2)stop("Missing Windows SYSTEM directory",sys);
 inifile="SYSTEM.INI";loadini();if(inivalue("display.drv",value)!=1)return 0;
 comment=strchr(value,';');if(comment)*comment=0;trim(value);leaf=strrchr(value,'\\');leaf=leaf?leaf+1:value;
 if(!stricmp(leaf,"HPXY.DRV"))owner="XYCTL.EXE";
 else if(!stricmp(leaf,"JRPAN.DRV")||!stricmp(leaf,"CPPAN.DRV")||!stricmp(leaf,"PANCMP2.DRV"))owner="XTPAN.EXE";
 else if(!stricmp(leaf,"CGAPAN.DRV"))owner="PANCTL.EXE";
 else if(!stricmp(leaf,"CGA100.DRV")||!stricmp(leaf,"CGA320.DRV")||!stricmp(leaf,"CGA640.DRV"))owner="CGACTL.EXE";
 else if(!stricmp(leaf,"C216N6.DRV")||!stricmp(leaf,"C23216.DRV")||
         !stricmp(leaf,"PCP3216.DRV")||!stricmp(leaf,"TNDYJR.DRV")||
         !stricmp(leaf,"TANDY88.DRV")||!stricmp(leaf,"TNDY6404.DRV")||
         !stricmp(leaf,"TNDY3204.DRV")||!stricmp(leaf,"TNDY6402.DRV")){
  owner="XTPAN.EXE";automatic=0;
 }
 if(!owner){puts("Other display selected; panning unchanged.");return 0;}
 for(i=0;i<PAN_COUNT;i++)if(!stricmp(pan_files[i].name,owner))break;
 if(i==PAN_COUNT){puts("Other display packet selected; panning unchanged.");return 0;}
 /* Verify every input before replacing any installed helper. */
 for(i=0;i<PAN_COUNT;i++){
  path(input,source,pan_files[i].name);
  if(!pinned_file(input,pan_files[i].size,pan_files[i].crc))stop("Panning input missing or damaged",input);
 }
 recover(win);recover(sys);
 total=CAP;done=0;last=-1;
 for(i=0;i<PAN_COUNT;i++)total+=pan_files[i].size;space();
 for(i=0;i<PAN_COUNT;i++){
  path(input,source,pan_files[i].name);
  path(dest,pan_files[i].system?sys:win,pan_files[i].name);
  if(!pinned_file(dest,pan_files[i].size,pan_files[i].crc)){
   if(checking)stop("Panning helper needs repair",dest);
   replace_file(input,pan_files[i].system?sys:win,pan_files[i].name);
  }
 }
 inifile="WIN.INI";loadini();ini_changed=0;
 sectionvalue("UnifiedPan","Display",marker);
 if(stricmp(marker,leaf)){
  token[0]=0;
  if(automatic){sprintf(token,"%s\\%s",win,owner);}
  pan_startup("load",token);pan_startup("run",0);
  changeini("UnifiedPan","Display",leaf);
 }
 if(ini_changed){
  if(checking)stop("Panning startup needs repair",win);
  begin(win,"WIN.INI",n,o,j);h=create(n);
  writeall(h,(unsigned char*)oldini,(unsigned)strlen(oldini),n);closeout(h,n);commit(win,"WIN.INI",n,o,j);
 }
 inifile="SYSTEM.INI";puts("Panning helpers ready; use PANCFG /SETTINGS in Windows.");return 0;
}
