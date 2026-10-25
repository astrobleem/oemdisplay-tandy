/* Raw DOS handles deliberately differ from host CRT descriptors. A CRT
 * write/close on one fails, reproducing the actual DOS boundary defect.
 */
#ifndef _A_NORMAL
#define _A_NORMAL 0
#endif
#define _dos_creatnew test_dos_creatnew
#define _dos_write test_dos_write
#define _dos_close test_dos_close
unsigned test_dos_creatnew(const char *,unsigned,int *);
unsigned test_dos_write(int,const void *,unsigned,unsigned *);
unsigned test_dos_close(int);
