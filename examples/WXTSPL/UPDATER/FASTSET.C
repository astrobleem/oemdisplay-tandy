/* Guarded migration of recognized wave launchers; C89 / 8086 / DOS 3.3+.
 * Reuses bounded transaction and byte-comparison checks. Never writes Windows resources or CF itself.
 * Public source only; rebuilt helpers require separate native qualification. */
#define main wave_main
#include "WAVEXT.C"
#undef main
/* Default helper identity uses kit reference bytes, never a digest. */
#define MAXFAST 5
struct fastfile { char rel[32],oldh[65],newh[65];long oldsize,newsize; };
static struct fastfile ff[MAXFAST];
static int nf;
static char fdir[PTH],a[PTH],b[PTH],c[PTH];
static const char active_mark[]="Windows XT fast launch 01 complete\r\n";
static const char restored_mark[]="Windows XT fast launch 01 restored\r\n";
static void filemap(int shell){nf=shell?5:3;strcpy(ff[0].rel,"WINXT.BAT");strcpy(ff[1].rel,"WAVE01" SEP "WINXT.NEW");if(shell){strcpy(ff[2].rel,"TSTART.BAT");strcpy(ff[3].rel,"WAVE01" SEP "TSTART.NEW");}strcpy(ff[nf-1].rel,"WAVE01" SEP "META.TXT");}
static void slot(char *out,int i,int newer){char name[16];sprintf(name,"F%d.%s",i,newer?"NEW":"BAK");join(out,fdir,name);}
static void side(char *out,int i,int newer){char *dot;join(out,home,ff[i].rel);dot=strrchr(out,'.');if(!dot)fail("Bad migration target");strcpy(dot,newer?".FNE":".FOL");}
static int hexhash(const char *h){unsigned n=64;if(strlen(h)!=n)return 0;while(n--)if(!isxdigit((unsigned char)h[n]))return 0;return 1;}
static long smallsize(char *s){char *end;long n=strtol(s,&end,10);if(!*s||*end||n<1||n>=MAXBAT)fail("Bad migration size");return n;}
static void marker_exact(const char *name,const char *text){join(a,fdir,name);if(kind(a)){textread(a,metadata);if(strcmp(metadata,text))fail("Changed migration marker");}}
static void mark_remove(const char *name,const char *text){marker_exact(name,text);join(a,fdir,name);if(kind(a)&&remove(a))fail("Cannot remove recognized migration marker");}
static void mark_write(const char *name,const char *text){marker_exact(name,text);join(a,fdir,name);if(!kind(a))write_new(a,(const unsigned char *)text,(unsigned)strlen(text));}
static void record(void){int i;char *at=metadata;
 at+=sprintf(at,"FASTSET02\r\n%s\r\n%s\r\n%d\r\n",win,home,nf);
 for(i=0;i<nf;i++)at+=sprintf(at,"-\r\n-\r\n%ld\r\n%ld\r\n",ff[i].oldsize,ff[i].newsize);
 join(a,fdir,"META.TXT");write_new(a,(const unsigned char *)metadata,(unsigned)strlen(metadata));if(!text_equal(a,metadata))fail("Journal readback mismatch");checkpoint("fast-recorded");
}
static void meta_format(const char *name){FILE *f;char line[PTH];int v,i;unsigned n;
 f=fopen(name,"rb");if(kind(name)!=1||!f)fail("Missing migration metadata snapshot");read_line(f,line,PTH);v=!strcmp(line,"WAVEXT01")?1:!strcmp(line,"WAVEXT02")?2:0;if(!v)fail("Unknown wave metadata snapshot");read_line(f,line,PTH);if(strcmp(line,win))fail("Snapshot Windows path mismatch");read_line(f,line,PTH);if(strcmp(line,home))fail("Snapshot support path mismatch");read_line(f,line,PTH);if(strcmp(line,have_shell?"1":"0"))fail("Snapshot shell mismatch");
 for(i=0;i<4;i++){read_line(f,line,PTH);if(v==2||(i>=2&&!have_shell)){if(strcmp(line,"-"))fail("Invalid snapshot byte journal");}else{n=(unsigned)strlen(line);if(n!=64)fail("Invalid snapshot digest syntax");while(n--)if(!isxdigit(line[n]))fail("Invalid snapshot digest syntax");}}
 if(fgetc(f)!=EOF||ferror(f)||fclose(f))fail("Snapshot metadata read error/trailing data");
}
static void snapshots(void){int i,j;char path[PTH];
 /* Reconstruct known launcher transformations, rather than trusting journal hashes. */
 have_shell=nf==5;for(j=0;j<1+have_shell;j++){join(path,txn,saved[j]);textread(path,original[j]);}
 for(i=0;i<nf-1;i++){j=i/2;slot(a,i,0);patch_mode(j,0);if(!text_equal(a,replacement[j])){patch_mode(j,1);if(!text_equal(a,replacement[j]))fail("Unknown migration backup launcher");}slot(a,i,1);patch_mode(j,1);if(!text_equal(a,replacement[j]))fail("Changed migration stage launcher");}
 slot(a,nf-1,0);meta_format(a);slot(a,nf-1,1);meta_format(a);
}
static int slot_equal(const char *live,int i,int newer){char ref[PTH];slot(ref,i,newer);return bytes_equal(live,ref);}
static void load_record(void){FILE *f;char line[PTH];int i,number,version;
 join(a,fdir,"META.TXT");textread(a,metadata);f=fopen(a,"rb");if(!f)fail("Incomplete migration journal; keep FAST01");
 read_line(f,line,PTH);version=!strcmp(line,"FASTSET01")?1:!strcmp(line,"FASTSET02")?2:0;if(!version)fail("Unknown migration journal");read_line(f,line,PTH);if(strcmp(line,win))fail("Migration Windows path mismatch");read_line(f,line,PTH);if(strcmp(line,home))fail("Migration support path mismatch");read_line(f,line,PTH);number=atoi(line);if((number!=3&&number!=5)||strlen(line)!=1)fail("Bad migration file count");filemap(number==5);
 for(i=0;i<nf;i++){read_line(f,ff[i].oldh,65);read_line(f,ff[i].newh,65);if(version==1){if(!hexhash(ff[i].oldh)||!hexhash(ff[i].newh))fail("Bad migration digest syntax");}else if(strcmp(ff[i].oldh,"-")||strcmp(ff[i].newh,"-"))fail("Bad migration byte journal");read_line(f,line,PTH);ff[i].oldsize=smallsize(line);read_line(f,line,PTH);ff[i].newsize=smallsize(line);}
 if(fgetc(f)!=EOF||ferror(f)||fclose(f))fail("Migration journal trailing data/read error");
 snapshots();
 marker_exact("DONE.TAG",active_mark);marker_exact("RESTORED.TAG",restored_mark);join(a,fdir,"DONE.TAG");join(b,fdir,"RESTORED.TAG");if(kind(a)&&kind(b))fail("Conflicting migration markers");
}
/* Fixed targets only. Inspect every live and sidecar name before any mutation. */
static int stateof(int i){int live,old,next;join(a,home,ff[i].rel);side(b,i,0);side(c,i,1);writable(a);writable(b);writable(c);
 live=!kind(a)?0:slot_equal(a,i,0)?1:slot_equal(a,i,1)?2:-1;
 old=!kind(b)?0:slot_equal(b,i,0)?1:-1;next=!kind(c)?0:slot_equal(c,i,1)?1:-1;
 if(live==1&&old==0&&(next==0||next==1))return 1;if(live==2&&old==1&&next==0)return 2;if(live==0&&old==1&&next==1)return 3;
 fail("Unknown migration target/sidecar; no unsafe fallback");return 0;
}
static void allstates(void){int i,s,active,restored;join(a,fdir,"DONE.TAG");active=kind(a)!=0;join(a,fdir,"RESTORED.TAG");restored=kind(a)!=0;for(i=0;i<nf;i++){s=stateof(i);if((active&&s!=2)||(restored&&s!=1))fail("Migration marker conflicts with target state");}}
static void deep_binaries(void){if(!stage_checked)load_txn();if(nf&&((nf==5)!=have_shell))fail("Migration/wave shell count mismatch");binaries_preflight(1);}
static void create_record(void){int i,j;char input[PTH];struct stat st;
 /* Main already checked the complete active wave before any helper write. */
 filemap(have_shell);for(i=0;i<nf;i++){side(a,i,0);side(b,i,1);if(kind(a)||kind(b))fail("Existing migration sidecar");join(a,home,ff[i].rel);if(kind(a)!=1||stat(a,&st)||st.st_size<1||st.st_size>=MAXBAT)fail("Bad migration input size");ff[i].oldsize=st.st_size;}
 space_check();
#if defined(HOST_TEST) && !defined(HOST_WIN)
 if(mkdir(fdir,0700))fail("Cannot exclusively create FAST01");
#else
 if(mkdir(fdir))fail("Cannot exclusively create FAST01");
#endif
 progress("Saving launcher backups and stages...");
 for(i=0;i<nf;i++){join(input,home,ff[i].rel);slot(b,i,0);copy_new(input,b);slot(b,i,1);
  if(i==nf-1){sprintf(metadata,"WAVEXT02\r\n%s\r\n%s\r\n%d\r\n-\r\n-\r\n-\r\n-\r\n",win,home,have_shell);ff[i].newsize=(long)strlen(metadata);write_new(b,(const unsigned char *)metadata,(unsigned)ff[i].newsize);if(!text_equal(b,metadata))fail("Metadata stage readback failed");}
  else{j=i/2;patch_mode(j,1);ff[i].newsize=(long)strlen(replacement[j]);write_new(b,(const unsigned char *)replacement[j],(unsigned)ff[i].newsize);if(!text_equal(b,replacement[j]))fail("Launcher stage readback failed");}
 }
 snapshots();record();
}
static void apply_fast(void){int i,s;progress("Committing recognized launcher transaction...");load_record();deep_binaries();allstates();mark_remove("RESTORED.TAG",restored_mark);mark_remove("DONE.TAG",active_mark);
 for(i=0;i<nf;i++){s=stateof(i);if(s==2)continue;if(s==1){slot(a,i,1);side(b,i,1);if(!kind(b))copy_new(a,b);join(a,home,ff[i].rel);side(b,i,0);move_new(a,b);checkpoint("fast-gap");}side(a,i,1);join(b,home,ff[i].rel);move_new(a,b);checkpoint("fast-live");if(stateof(i)!=2)fail("Migration commit readback failed");}
 load_txn();marker_preflight();for(i=0;i<1+have_shell;i++)if(starter_state(i)!=2)fail("Migrated starter did not verify");deep_binaries();mark_write("DONE.TAG",active_mark);puts("APPLIED: recognized launchers use START. Deep VERIFY remains available. Roll back with FASTSET RESTORE Windows-dir support-dir.");
}
static void restore_fast(void){int i,s;progress("Committing recognized launcher transaction...");load_record();deep_binaries();allstates();mark_remove("DONE.TAG",active_mark);mark_remove("RESTORED.TAG",restored_mark);
 for(i=nf-1;i>=0;i--){s=stateof(i);if(s==1)continue;if(s==2){join(a,home,ff[i].rel);side(b,i,1);move_new(a,b);checkpoint("fast-restore-gap");}side(a,i,0);join(b,home,ff[i].rel);move_new(a,b);checkpoint("fast-restore-live");if(stateof(i)!=1)fail("Migration rollback readback failed");}
 load_txn();marker_preflight();for(i=0;i<1+have_shell;i++)if(starter_state(i)!=2)fail("Restored launcher did not verify");mark_write("RESTORED.TAG",restored_mark);puts("RESTORED: exact prior wave launchers, staged starters and metadata. Wave and Windows unchanged; FAST01 retained.");
}

/* HELP02 preserves helper snapshots separately from the accepted FAST01 evidence.
 * No COPY over a live EXE. Recorded old/new/gap rename states are resumable. */
static int known_helper(const char *name,const char *source){char ref[PTH],*end;int i;const char *names[2]={"WVOLD.EXE","WVFAST.EXE"};
 if(bytes_equal(name,source))return 1;
 for(i=0;i<2;i++){if(strlen(source)>=PTH-12)fail("Helper reference path too long");strcpy(ref,source);end=strrchr(ref,'\\');
#if defined(HOST_TEST) && !defined(HOST_WIN)
 end=strrchr(ref,'/');
#endif
 if(end)strcpy(end+1,names[i]);else strcpy(ref,names[i]);if(bytes_equal(name,ref))return i+2;}
 return 0;
}
static void helper_update(const char *source){char dir[PTH],old[PTH],fresh[PTH],live[PTH],prev[PTH],nextpath[PTH],rec[PTH];int l,o,n,prepared=0,known;struct stat st;unsigned char mz[2]={0x4d,0x5a};
 join(dir,home,"HELP02");join(old,dir,"OLD.EXE");join(fresh,dir,"NEW.EXE");join(rec,dir,"META.TXT");join(live,home,"WAVEXT.EXE");join(prev,home,"WAVEXT.ZOL");join(nextpath,home,"WAVEXT.ZNE");
 if(!kind(dir)){
  if(kind(prev)||kind(nextpath)||kind(source)!=1||kind(live)!=1)fail("Helper input/sidecar conflict");known=known_helper(live,source);if(!known)fail("Installed helper differs from kit reference bytes; preserve it");if(stat(source,&st)||st.st_size<1000||st.st_size>
#ifdef HOST_TEST
1048576L
#else
65535L
#endif
)fail("Bad new helper size");size_header(source,st.st_size,mz,2);if(stat(live,&st)||st.st_size<1000||st.st_size>
#ifdef HOST_TEST
1048576L
#else
65535L
#endif
)fail("Bad installed helper size");size_header(live,st.st_size,mz,2);space_check();
#if defined(HOST_TEST) && !defined(HOST_WIN)
  if(mkdir(dir,0700))fail("Cannot exclusively create HELP02");
#else
  if(mkdir(dir))fail("Cannot exclusively create HELP02");
#endif
  progress("Saving installed and replacement helper bytes...");copy_new(live,old);copy_new(source,fresh);sprintf(metadata,"HELPER02\r\n%s\r\n%s\r\n",win,home);write_new(rec,(const unsigned char *)metadata,(unsigned)strlen(metadata));if(!text_equal(rec,metadata))fail("Helper record readback failed");prepared=1;checkpoint("helper-recorded");
 }
 if(kind(dir)!=2)fail("HELP02 is not a directory");sprintf(metadata,"HELPER02\r\n%s\r\n%s\r\n",win,home);if(!prepared&&(!text_equal(rec,metadata)||!bytes_equal(source,fresh)||!known_helper(old,source)))fail("Helper record or kit bytes differ; keep HELP02");
 if(prepared){if(known==1)return;l=1;o=0;n=0;}else{
 if(bytes_equal(live,fresh)&&!kind(prev)&&!kind(nextpath)&&bytes_equal(old,fresh))return;
 l=!kind(live)?0:bytes_equal(live,fresh)?2:bytes_equal(live,old)?1:-1;o=!kind(prev)?0:bytes_equal(prev,old)?1:-1;n=!kind(nextpath)?0:bytes_equal(nextpath,fresh)?1:-1;}
 if(!((l==1&&o==0&&(n==0||n==1))||(l==0&&o==1&&n==1)||(l==2&&o==1&&n==0)))fail("Unknown helper recovery state; preserve all evidence");
 if(l==2)return;progress("Installing helper by recorded renames...");if(l==1){if(!n)copy_new(fresh,nextpath);move_new(live,prev);checkpoint("helper-gap");}move_new(nextpath,live);if(!bytes_equal(live,fresh))fail("Helper commit readback failed");checkpoint("helper-live");
}
int main(int argc,char **argv){int update,i;
 update=argc==5&&!stricmp(argv[1],"UPDATE");if(argc!=4&&!update){puts("FASTSET UPDATE Windows-dir support-dir new-WAVEXT-file\nFASTSET CHECK|APPLY|RESTORE Windows-dir support-dir\nDefaults compare bytes; deep diagnostics: WAVEXT VERIFY.");return 2;}
 paths(argv[2],argv[3]);not_windows();join(fdir,home,"FAST01");
 if(!update&&stricmp(argv[1],"APPLY")&&stricmp(argv[1],"CHECK")&&stricmp(argv[1],"RESTORE"))return 2;
 /* Read-only validation precedes helper or launcher mutation. */
 if(kind(fdir)){if(kind(fdir)!=2)fail("FAST01 not a directory");load_record();deep_binaries();allstates();}
 else{load_txn();marker_preflight();deep_binaries();for(i=0;i<1+have_shell;i++)if(starter_state(i)!=2)fail("Complete active wave required before helper update");join(a,home,"WAVE.RDY");if(!text_equal(a,marker))fail("Active wave required");}
 if(update)helper_update(argv[4]);
 if(update||!stricmp(argv[1],"APPLY")){if(!kind(fdir))create_record();apply_fast();return 0;}
 if(kind(fdir)!=2)fail("Recognized migration record required");if(!stricmp(argv[1],"RESTORE")){restore_fast();return 0;}puts("CHECK PASS: recognized byte snapshots and transaction states; no changes.");return 0;
}
