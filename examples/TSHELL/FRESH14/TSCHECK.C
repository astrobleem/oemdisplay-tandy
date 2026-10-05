/* Read-only byte comparison for the DOS fresh installer. 8086, MSC6. */
#include <dos.h>
#include <fcntl.h>
#include <string.h>
static unsigned char left[1024], right[1024];
int main(int argc, char **argv)
{
    unsigned a, b, na, nb, status = 0;
    if (argc != 3) return 3;
    if (_dos_open(argv[1], O_RDONLY, &a)) return 2;
    if (_dos_open(argv[2], O_RDONLY, &b)) {
        _dos_close(a); return 2;
    }
    for (;;) {
        if (_dos_read(a, left, sizeof(left), &na) ||
            _dos_read(b, right, sizeof(right), &nb)) {
            status = 2; break;
        }
        if (na != nb || memcmp(left, right, na)) { status = 1; break; }
        if (!na) break;
    }
    if (_dos_close(a)) status = 2;
    if (_dos_close(b)) status = 2;
    return (int)status;
}
