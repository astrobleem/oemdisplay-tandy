#ifndef TD_FILEWIN_H
#define TD_FILEWIN_H
/* Unbuffered Win3 file APIs avoid CRT stdio buffers in the near data segment. */
#define WINVER 0x0300
#include <windows.h>
#include <stddef.h>
#include <string.h>
#define EOF (-1)
#define SEEK_SET 0
#define SEEK_CUR 1
#define SEEK_END 2
typedef struct {HFILE h;int error;} TD_FILE;
#define FILE TD_FILE
static TD_FILE td_files[3];
static FILE *td_fopen(const char *p,const char *mode){int i;HFILE h;for(i=0;i<3;i++)if(!td_files[i].h)break;if(i==3)return NULL;
 h=mode[0]=='w'?_lcreat(p,0):_lopen(p,OF_READ|OF_SHARE_DENY_WRITE);if(h==-1)return NULL;
 td_files[i].h=h+1;td_files[i].error=0;return &td_files[i];}
static size_t td_fread(void *p,size_t size,size_t n,FILE *f){UINT got;if(!size)return 0;got=_lread(f->h-1,p,(UINT)(size*n));if(got==(UINT)-1){f->error=1;return 0;}return got/size;}
static size_t td_fwrite(const void *p,size_t size,size_t n,FILE *f){UINT got;if(!size)return 0;got=_lwrite(f->h-1,p,(UINT)(size*n));if(got!=(UINT)(size*n))f->error=1;return got==(UINT)-1?0:got/size;}
static int td_fclose(FILE *f){int r=_lclose(f->h-1);f->h=0;return r;}
static int td_fseek(FILE *f,long n,int kind){if(_llseek(f->h-1,n,kind)==-1L){f->error=1;return -1;}return 0;}
static long td_ftell(FILE *f){return _llseek(f->h-1,0L,SEEK_CUR);}
static int td_fgetc(FILE *f){U8 c;return td_fread(&c,1,1,f)==1?c:EOF;}
int remove(const char *);
int rename(const char *,const char *);
#define fopen td_fopen
#define fread td_fread
#define fwrite td_fwrite
#define fclose td_fclose
#define fseek td_fseek
#define ftell td_ftell
#define fgetc td_fgetc
#define fflush(f) 0
#define ferror(f) ((f)->error)
#endif
