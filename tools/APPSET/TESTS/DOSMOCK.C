#include <io.h>
#include <fcntl.h>
#include <sys/types.h>
#include <sys/stat.h>
#include "DOSMOCK.H"
#define RAW_BASE 10000
unsigned test_dos_creatnew(const char *name,unsigned attributes,int *handle)
{
 int fd;attributes=attributes;
 fd=open(name,O_WRONLY|O_CREAT|O_EXCL|O_BINARY,S_IREAD|S_IWRITE);
 if(fd<0)return 5;*handle=fd+RAW_BASE;return 0;
}
unsigned test_dos_write(int handle,const void *data,unsigned count,unsigned *written)
{
 int n;if(handle<RAW_BASE)return 6;
 n=write(handle-RAW_BASE,data,count);if(n<0)return 5;*written=(unsigned)n;return 0;
}
unsigned test_dos_close(int handle)
{if(handle<RAW_BASE)return 6;return close(handle-RAW_BASE)?6:0;}
