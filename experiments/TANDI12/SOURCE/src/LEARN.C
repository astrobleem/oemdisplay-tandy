/* Separate experimental notebook. Never writes DAT or base engine scores.
   Two bounded far heap books keep the Win16 DGROUP below 64K. */
#include "LEARN.H"
#include "SHAPIN.H"
#ifdef WIN16
#include "FILEWIN.H"
#else
#include <stdio.h>
#endif
#include <stdlib.h>
#include <string.h>
#ifdef WIN16
#define WINVER 0x0300
#include <windows.h>
#define LF FAR
#else
#define LF
#endif
typedef struct {U16 c,q,n[4];} CELL;
typedef struct {U32 id,trace;} SESSION;
typedef struct {U32 book,next;U16 count,sessions;CELL cells[LN_CELLS];SESSION ledger[LN_SESSIONS];} BOOK;
static BOOK LF *book;static BOOK LF *scratch;
#ifdef WIN16
static HGLOBAL bh,sh;
#endif
static U8 pin[32];static U16 nc,nq;
static char primary[144],backup[144],tempfile[144],archive[144];
static U32 loaded;static int ready,frombackup,fixturemode,unusable;static const char *status="Notebook unavailable.";
#ifdef LN_HOST
static int fault;
void ln_fault(int n){fault=n;}
#define FAIL(n) (fault==(n))
#else
#define FAIL(n) 0
#endif
static U16 u16(U8 *b){return (U16)(b[0]|((U16)b[1]<<8));}
static U32 u32(U8 *b){return (U32)b[0]|((U32)b[1]<<8)|((U32)b[2]<<16)|((U32)b[3]<<24);}
static void p16(U8 *b,U16 n){b[0]=(U8)n;b[1]=(U8)(n>>8);}
static void p32(U8 *b,U32 n){int i;for(i=0;i<4;i++)b[i]=(U8)(n>>(i*8));}
static U32 crc(U32 v,U8 *p,int n){int i;while(n--){v^=*p++;for(i=0;i<8;i++)v=(v>>1)^((v&1)?0xedb88320UL:0);}return v;}
static int rd(FILE *f,U8 *b,int n,U32 *v){if((int)fread(b,1,n,f)!=n)return 0;*v=crc(*v,b,n);return 1;}
static int wr(FILE *f,U8 *b,int n,U32 *v){if((int)fwrite(b,1,n,f)!=n)return 0;*v=crc(*v,b,n);return 1;}
static void empty(BOOK LF *b,U32 id){int i;b->book=id;b->next=1;b->count=b->sessions=0;for(i=0;i<LN_CELLS;i++){b->cells[i].c=b->cells[i].q=0;}}
static int readbook(TDB *d,const char *path,BOOK LF *b,U32 *result){
 FILE *f;U8 a[64],row[TD_ROW];U32 v=0xffffffffUL,total=0,previous=0;int i,j,sum,lastc=-1,lastq=-1,ok=0;
 f=fopen(path,"rb");if(!f)return 0;
 if(fseek(f,0,SEEK_END)||ftell(f)>4164L||ftell(f)<68L||fseek(f,0,SEEK_SET))goto done;
 if(!rd(f,a,64,&v)||memcmp(a,"TDLRN011",8)||u16(a+8)!=nc||u16(a+10)!=nq||memcmp(a+24,pin,32))goto done;
 for(i=56;i<64;i++)if(a[i])goto done;
 b->count=u16(a+12);b->sessions=u16(a+14);b->book=u32(a+16);b->next=u32(a+20);
 if(b->count>LN_CELLS||b->sessions>LN_SESSIONS||!b->book||!b->next)goto done;
 for(i=0;i<(int)b->count;i++){
  CELL LF *c=&b->cells[i];if(!rd(f,a,12,&v))goto done;c->c=u16(a);c->q=u16(a+2);
  if(c->c>=nc||c->q>=nq||(int)c->c<lastc||((int)c->c==lastc&&(int)c->q<=lastq))goto done;
  if((int)c->c!=lastc&&!db_row(d,c->c,row))goto done;
  if(db_value(row,c->q)!=2)goto done;lastc=c->c;lastq=c->q;sum=0;
  for(j=0;j<4;j++){c->n[j]=u16(a+4+j*2);if(c->n[j]>b->sessions)goto done;sum+=(int)c->n[j];}
  if(!sum||sum>(int)b->sessions)goto done;total+=sum;
 }
 if(total>(U32)b->sessions*LN_ANSWERS)goto done;
 for(i=0;i<(int)b->sessions;i++){
  if(!rd(f,a,8,&v))goto done;b->ledger[i].id=u32(a);b->ledger[i].trace=u32(a+4);
  if(b->ledger[i].id<=previous||b->ledger[i].id>=b->next)goto done;previous=b->ledger[i].id;
 }
 if(b->next!=previous+1)return fclose(f),0;
 if(fread(a,1,4,f)!=4||u32(a)!=(v^0xffffffffUL)||fgetc(f)!=EOF||ferror(f))goto done;
 *result=v^0xffffffffUL;ok=1;
 done:fclose(f);return ok;
}
static int writebook(const char *path,BOOK LF *b,U32 *result){
 FILE *f;U8 a[64];U32 v=0xffffffffUL;int i,j,ok=1;
 f=fopen(path,"wb");if(!f)return 0;memset(a,0,64);memcpy(a,"TDLRN011",8);
 p16(a+8,nc);p16(a+10,nq);p16(a+12,b->count);p16(a+14,b->sessions);p32(a+16,b->book);p32(a+20,b->next);memcpy(a+24,pin,32);
 ok=wr(f,a,64,&v);
 for(i=0;i<(int)b->count&&ok;i++){
  CELL LF *c=&b->cells[i];p16(a,c->c);p16(a+2,c->q);for(j=0;j<4;j++)p16(a+4+j*2,c->n[j]);ok=wr(f,a,12,&v);
 }
 for(i=0;i<(int)b->sessions&&ok;i++){p32(a,b->ledger[i].id);p32(a+4,b->ledger[i].trace);ok=wr(f,a,8,&v);}
 p32(a,v^0xffffffffUL);if(fwrite(a,1,4,f)!=4||fflush(f)||ferror(f))ok=0;if(fclose(f))ok=0;
 *result=v^0xffffffffUL;return ok;
}
static int copyfile(const char *a,const char *b){
 FILE *in,*out;U8 buf[256];int n,ok=1;in=fopen(a,"rb");if(!in)return 0;out=fopen(b,"wb");if(!out){fclose(in);return 0;}
 while((n=(int)fread(buf,1,sizeof(buf),in))!=0)if((int)fwrite(buf,1,n,out)!=n){ok=0;break;}
 if(ferror(in)||ferror(out)||fflush(out))ok=0;if(fclose(out))ok=0;fclose(in);return ok;
}
static int present(const char *path){FILE *f=fopen(path,"rb");if(!f)return 0;fclose(f);return 1;}
/* Preserve unreadable or other-DAT bytes by rename, never overwrite them. */
static int rawarchive(const char *original){
 FILE *f;char path[144],name[13];int i;
 if(!present(original))return 1;
 for(i=1;i<=9999;i++){
  strcpy(name,fixturemode?"QOLD0000.LRN":"OLD_0000.LRN");
  name[4]=(char)('0'+i/1000);name[5]=(char)('0'+i/100%10);name[6]=(char)('0'+i/10%10);name[7]=(char)('0'+i%10);
  strcpy(path,archive);strcat(path,name);f=fopen(path,"rb");if(f){fclose(f);continue;}
  return rename(original,path)==0;
 }return 0;
}
void ln_fixture(int on){if(!ready)fixturemode=on!=0;}
static void paths(const char *dat){int i;strcpy(primary,dat);for(i=(int)strlen(primary)-1;i>=0;i--)if(primary[i]=='\\'||primary[i]=='/'||primary[i]==':')break;
 strcpy(primary+i+1,fixturemode?"QA11.LRN":"TANDI.LRN");strcpy(backup,primary);strcpy(backup+i+1,fixturemode?"QA11.BAK":"TANDI.BAK");strcpy(tempfile,primary);strcpy(tempfile+i+1,fixturemode?"QA11.TMP":"TANDI.TMP");strcpy(archive,primary);archive[i+1]=0;
}
int ln_open(TDB *d,const char *dat){
 U32 v;ln_close();if(strlen(dat)>132||d->error)return 0;
#ifdef WIN16
 bh=GlobalAlloc(GMEM_MOVEABLE|GMEM_ZEROINIT,sizeof(BOOK));sh=GlobalAlloc(GMEM_MOVEABLE|GMEM_ZEROINIT,sizeof(BOOK));
 if(bh)book=(BOOK FAR *)GlobalLock(bh);if(sh)scratch=(BOOK FAR *)GlobalLock(sh);
#else
 book=(BOOK *)calloc(1,sizeof(BOOK));scratch=(BOOK *)calloc(1,sizeof(BOOK));
#endif
 if(!book||!scratch){ln_close();status="No notebook memory; base game works.";return 0;}
 paths(dat);nc=d->nc;nq=d->nq;if(!td_sha(dat,pin)){ln_close();status="Cannot pin DAT; learning unavailable.";return 0;}
 ready=1;frombackup=0;
 if(readbook(d,primary,book,&v)){loaded=v;status="Notebook loaded. Guessing use OFF.";}
 else if(readbook(d,backup,book,&v)){loaded=v;frombackup=1;status="Recovered backup. Guessing use OFF.";}
 else {empty(book,1);loaded=0;unusable=present(primary)||present(backup);status=unusable?"Reports unreadable or other DAT. Fresh required.":"Fresh notebook. Guessing use OFF.";}
 return 1;
}
void ln_close(void){
#ifdef WIN16
 if(book&&bh)GlobalUnlock(bh);if(scratch&&sh)GlobalUnlock(sh);if(bh)GlobalFree(bh);if(sh)GlobalFree(sh);bh=sh=0;
#else
 free(book);free(scratch);
#endif
 book=scratch=0;ready=0;loaded=0;unusable=0;
}
int ln_ready(void){return ready;}
int ln_cells(void){return ready?book->count:0;}
int ln_sessions(void){return ready?book->sessions:0;}
U32 ln_next(void){return ready?book->next:0;}
const char *ln_status(void){return status;}
static int value(CELL LF *c){int i,seen=0,v=-1;for(i=0;i<4;i++)if(c->n[i]){seen++;if(c->n[i]>=2)v=i;}return seen==1&&v>=0?(v<2?v:v+1):2;}
int ln_active(void){int i,n=0;if(ready)for(i=0;i<(int)book->count;i++)if(value(&book->cells[i])!=2)n++;return n;}
int ln_conflicts(void){int i,j,k,n=0;if(ready)for(i=0;i<(int)book->count;i++){k=0;for(j=0;j<4;j++)if(book->cells[i].n[j])k++;if(k>1)n++;}return n;}
/* Preview: first report, agreeing report, or a conflict that disables use. */
int ln_preview(int c,int q,int a){int i,j,k;if(!ready||c<0||c>=(int)nc||q<0||q>=(int)nq||a<0||a>4||a==2)return -1;
 k=a<2?a:a-1;for(i=0;i<(int)book->count;i++)if((int)book->cells[i].c==c&&(int)book->cells[i].q==q){
  for(j=0;j<4;j++)if(j!=k&&book->cells[i].n[j])return 2;return 1;
 }return 0;
}
static int eligible(TDB *d,int c,const TDHISTORY *h,U8 *row){int i,j;
 if(!ready||c<0||c>=(int)nc||h->count<1||h->count>LN_ANSWERS||!db_row(d,c,row))return 0;
 for(i=0;i<h->count;i++){if(h->q[i]>=nq||h->a[i]>4)return 0;for(j=0;j<i;j++)if(h->q[j]==h->q[i])return 0;}return 1;
}
int ln_review(TDB *d,int c,const TDHISTORY *h){U8 row[TD_ROW];int i,n=0;if(!eligible(d,c,h,row))return 0;for(i=0;i<h->count;i++)if(h->a[i]!=2&&db_value(row,h->q[i])==2)n++;return n;}
int ln_detail(TDB *d,int c,const TDHISTORY *h,int index,int *q,int *a){U8 row[TD_ROW];int i,n=0;if(!eligible(d,c,h,row))return 0;
 for(i=0;i<h->count;i++)if(h->a[i]!=2&&db_value(row,h->q[i])==2){if(n++==index){*q=h->q[i];*a=h->a[i];return 1;}}return 0;
}
static int unchanged(TDB *d){U32 v=0;int ok;ok=readbook(d,primary,scratch,&v);if(!ok)ok=readbook(d,backup,scratch,&v);
 if((ok?v:0)!=loaded){status="Notebook changed. Close and reopen.";return 0;}return 1;
}
static int commit(TDB *d){U32 a,b;int had;
 if(FAIL(1)||!writebook(tempfile,book,&a)||FAIL(2)||!readbook(d,tempfile,scratch,&b)||a!=b){status="Save failed; previous file retained.";return 0;}
 /* Back up only a fully validated primary. Never replace recovery with corrupt data. */
 had=readbook(d,primary,scratch,&b);
 if(had){char stage[144];strcpy(stage,backup);stage[strlen(stage)-3]='B';stage[strlen(stage)-2]='K';stage[strlen(stage)-1]='T';
  if(FAIL(3)||!copyfile(primary,stage)||!readbook(d,stage,scratch,&b)){status="Backup failed; previous file retained.";return 0;}
  remove(backup);
  if(rename(stage,backup)){status="Cannot install backup; primary retained.";return 0;}
 }
 if(FAIL(4)){status="Save interrupted; recovery retained.";return 0;}
 /* DOS rename does not overwrite: backup is durable before removing primary. */
 if(!had&&present(primary)&&!rawarchive(primary)){status="Cannot preserve old reports; save refused.";return 0;}
 if(remove(primary)&&had){status="Cannot replace notebook; backup retained.";return 0;}
 if(FAIL(5)||rename(tempfile,primary)){status="Cannot install notebook; backup retained.";return 0;}
 if(!readbook(d,primary,scratch,&b)||b!=a){status="Saved file verification failed.";return 0;}
 loaded=a;frombackup=0;unusable=0;status="Report saved. Guessing toggle unchanged.";return 1;
}
static void recover(TDB *d){U32 v;const char *s=status;if(readbook(d,primary,book,&v)){loaded=v;frombackup=0;}else if(readbook(d,backup,book,&v)){loaded=v;frombackup=1;}else{empty(book,1);loaded=0;}status=s;}
int ln_save(TDB *d,int c,const TDHISTORY *h,U32 id,int used){
 U8 row[TD_ROW],a[4];U32 trace=0xffffffffUL;int i,j,k,at,n,extra=0;
 if(!ready||used){status="Learning-enabled or demo games cannot teach.";return 0;}
 if(unusable){status="Fresh must preserve old reports first.";return 0;}
 if(!id||id!=book->next){status="Already saved, or stale game. No duplicate.";return 0;}
 if(!eligible(d,c,h,row)){status="Confirm a completed roster game first.";return 0;}
 n=ln_review(d,c,h);if(!n){status="No new answers to report.";return 0;}
 if(book->sessions==LN_SESSIONS||book->next==0xffffffffUL){status="Notebook full. Archive a fresh notebook.";return 0;}
 if(!unchanged(d))return 0;
 for(i=0;i<h->count;i++)if(h->a[i]!=2&&db_value(row,h->q[i])==2){
  for(j=0;j<(int)book->count;j++)if((int)book->cells[j].c==c&&book->cells[j].q==h->q[i])break;
  if(j==(int)book->count)extra++;
 }
 if(book->count+extra>LN_CELLS){status="Cell limit reached. Archive a fresh notebook.";return 0;}
 for(i=0;i<h->count;i++){
  p16(a,h->q[i]);a[2]=h->a[i];a[3]=0;trace=crc(trace,a,4);
  if(h->a[i]==2||db_value(row,h->q[i])!=2)continue;
  at=0;while(at<(int)book->count&&((int)book->cells[at].c<c||((int)book->cells[at].c==c&&book->cells[at].q<h->q[i])))at++;
  if(at==(int)book->count||(int)book->cells[at].c!=c||book->cells[at].q!=h->q[i]){
   for(j=book->count;j>at;j--)book->cells[j]=book->cells[j-1];book->count++;
   book->cells[at].c=(U16)c;book->cells[at].q=h->q[i];for(k=0;k<4;k++)book->cells[at].n[k]=0;
  }
  k=h->a[i]<2?(int)h->a[i]:(int)h->a[i]-1;book->cells[at].n[k]++;
 }
 book->ledger[book->sessions].id=id;book->ledger[book->sessions].trace=trace^0xffffffffUL;book->sessions++;book->next++;
 if(commit(d))return 1;recover(d);return 0;
}
int ln_reset(TDB *d){if(!ready)return 0;if(unusable){status="Fresh must preserve old reports first.";return 0;}if(!unchanged(d))return 0;book->count=0;if(commit(d)){status="Answers reset. Session IDs retained.";return 1;}recover(d);return 0;}
int ln_fresh(TDB *d){
 FILE *f;char path[144],digits[9];U32 id,v;int i;const char *s;
 if(!ready||!unchanged(d))return 0;if(book->book==0xffffffffUL){status="Book ID exhausted; preserve files.";return 0;}
 id=book->book+1;
 if(unusable){
  if(!rawarchive(primary)||!rawarchive(backup)){status="Cannot preserve old files; fresh refused.";return 0;}
  empty(book,id);if(commit(d)){status="Fresh book. Old raw reports preserved.";return 1;}
  recover(d);unusable=1;return 0;
 }
 for(i=1;i<=9999;i++){digits[0]=(char)(fixturemode?'Q':'N');digits[1]=(char)(fixturemode?'A':'O');digits[2]=(char)(fixturemode?'1':'T');digits[3]=(char)(fixturemode?'1':'E');digits[4]=(char)('0'+i/1000);digits[5]=(char)('0'+i/100%10);digits[6]=(char)('0'+i/10%10);digits[7]=(char)('0'+i%10);digits[8]=0;strcpy(path,archive);strcat(path,digits);strcat(path,".LRN");f=fopen(path,"rb");if(f){fclose(f);continue;}break;}
 if(i>9999){status="Archive names exhausted; preserve files.";return 0;}
 if(!writebook(path,book,&v)||!readbook(d,path,scratch,&v)){status="Cannot archive; old notebook retained.";return 0;}
 empty(book,id);if(commit(d)){status="Fresh notebook. Old book archived.";return 1;}
 s=status;recover(d);status=s;return 0;
}
int ln_tie(ENGINE *e,TDB *d,const TDHISTORY *h){
 static const short delta[5][5]={{4,2,0,-4,-8},{2,2,0,-2,-4},{0,0,0,0,0},{-4,-2,0,2,2},{-8,-4,0,2,4}};
 int i,j,k,b,chosen,score,secondary=0,v;eng_rank(e,d);b=e->best;chosen=b;if(!ready||b<0||e->turn<25)return b;
 for(i=0;i<(int)d->nc;i++)if(!e->rejected[i]&&e->score[i]==e->score[b]){
  score=0;for(j=0;j<(int)book->count;j++)if((int)book->cells[j].c==i&&(v=value(&book->cells[j]))!=2)
   for(k=0;k<h->count;k++)if(h->q[k]==book->cells[j].q){score+=delta[h->a[k]][v];break;}
  if(chosen==b&&i==b)secondary=score;
  if(score>secondary||(score==secondary&&i<chosen)){chosen=i;secondary=score;}
 }
 if(chosen!=b){e->second=b;e->best=chosen;}return chosen;
}
