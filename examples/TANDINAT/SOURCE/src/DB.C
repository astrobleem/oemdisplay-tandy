/* Disk access is the only platform-specific part of the engine. */
#include "TANDI.H"
#include <string.h>
#ifdef WIN16
#define WINVER 0x0300
#include <windows.h>
static HFILE file=-1;
#else
#include <stdio.h>
static FILE *file;
#endif
static U8 scratch[512];
static U16 word(const U8 *p){return (U16)(p[0]|((U16)p[1]<<8));}
static U32 dword(const U8 *p){return (U32)word(p)|((U32)word(p+2)<<16);}
static int readat(TDB *d,U32 pos,U8 *buf,U16 n){
    d->seeks++;d->bytes+=n;
    if(pos>d->size || (U32)n>d->size-pos){d->error=1;return 0;}
#ifdef WIN16
    if(_llseek(file,(LONG)pos,0)!=(LONG)pos ||
       _lread(file,buf,n)!=n){d->error=1;return 0;}
#else
    if(fseek(file,(long)pos,SEEK_SET) || fread(buf,1,n,file)!=n){
        d->error=1;return 0;
    }
#endif
    return 1;
}
void db_close(void){
#ifdef WIN16
    if(file!=-1)_lclose(file);
    file=-1;
#else
    if(file)fclose(file);
    file=0;
#endif
}
int db_open(TDB *d,const char *name){
    U8 head[64];U32 expected,sum=0,pos,off;U16 n,i;
    memset(d,0,sizeof(*d));db_close();
#ifdef WIN16
    file=_lopen(name,OF_READ|OF_SHARE_DENY_WRITE);
    if(file==-1){d->error=1;return 0;}
    d->size=(U32)_llseek(file,0L,2);
#else
    file=fopen(name,"rb");if(!file){d->error=1;return 0;}
    fseek(file,0,SEEK_END);d->size=(U32)ftell(file);
#endif
    if(d->size<64 || d->size>600000UL)goto bad;
    if(!readat(d,0,head,64))goto bad;
    if(memcmp(head,"TANDI01",8) || word(head+8)!=1)goto bad;
    d->nc=word(head+10);d->nq=word(head+12);
    d->rb=word(head+14);d->cb=word(head+16);
    d->qo=dword(head+20);d->co=dword(head+24);
    d->ro=dword(head+28);d->mo=dword(head+32);
    d->so=dword(head+36);expected=dword(head+44);
    if(!d->nc || d->nc>TD_MAXC || !d->nq || d->nq>TD_MAXQ ||
       d->rb!=(d->nq*3+7)/8 || d->cb!=(d->nc*3+7)/8 ||
       word(head+18) || d->qo!=64 ||
       d->co!=64+(U32)d->nq*4 ||
       d->ro!=d->co+(U32)d->nc*4 ||
       d->mo!=d->ro+(U32)d->nc*d->rb ||
       d->so!=d->mo+(U32)d->nq*d->cb ||
       d->so>=d->size || dword(head+40)!=d->size)goto bad;
    for(i=48;i<64;i++)if(head[i])goto bad;
    for(pos=64;pos<d->size;pos+=n){
        n=(U16)((d->size-pos>512)?512UL:d->size-pos);
        if(!readat(d,pos,scratch,n))goto bad;
        for(i=0;i<n;i++)sum+=scratch[i];
    }
    if(sum!=expected)goto bad;
    /* Validate every string offset with block reads, not one seek per name. */
    for(pos=d->qo;pos<d->ro;pos+=n){
        n=(U16)((d->ro-pos>512)?512UL:d->ro-pos);
        if(!readat(d,pos,scratch,n))goto bad;
        for(i=0;i<n;i+=4){
            off=dword(scratch+i);if(off<d->so||off>=d->size)goto bad;
        }
    }
    return 1;
bad: d->error=1;db_close();return 0;
}
static int stringat(TDB *d,U32 table,int index,char *out,int limit){
    U8 raw[4];U32 pos;U16 n;int i;
    out[0]=0;if(!readat(d,table+(U32)index*4,raw,4))return 0;
    pos=dword(raw);if(pos<d->so||pos>=d->size)goto bad;
    n=(U16)((d->size-pos<(U32)limit)?d->size-pos:(U32)limit);
    if(!readat(d,pos,(U8 *)out,n))return 0;
    for(i=0;i<(int)n;i++){
        if(!out[i]){if(i)return 1;goto bad;}
        if((U8)out[i]<32||(U8)out[i]>126)goto bad;
    }
bad: out[0]=0;d->error=1;return 0;
}
int db_question(TDB *d,int q,char *out){
    if(q<0||q>=(int)d->nq)return 0;
    return stringat(d,d->qo,q,out,80);
}
int db_name(TDB *d,int c,char *out){
    if(c<0||c>=(int)d->nc)return 0;
    return stringat(d,d->co,c,out,40);
}
int db_value(const U8 *buf,int index){
    unsigned bit=(unsigned)index*3;
    unsigned val=buf[bit>>3]>>(bit&7);
    if((bit&7)>5)val|=(unsigned)buf[(bit>>3)+1]<<(8-(bit&7));
    return val&7;
}
int db_row(TDB *d,int c,U8 *buf){
    int i;if(c<0||c>=(int)d->nc)return 0;
    if(!readat(d,d->ro+(U32)c*d->rb,buf,d->rb))return 0;
    for(i=0;i<(int)d->nq;i++)if(db_value(buf,i)>4){d->error=1;return 0;}
    return 1;
}
int db_column(TDB *d,int q,U8 *buf){
    int i;if(q<0||q>=(int)d->nq)return 0;
    if(!readat(d,d->mo+(U32)q*d->cb,buf,d->cb))return 0;
    for(i=0;i<(int)d->nc;i++)if(db_value(buf,i)>4){d->error=1;return 0;}
    return 1;
}
