/* Generated by gensyscalls.py. Do not edit. */

#include <private/bionic_asm.h>

ENTRY(___close)
#ifdef __NR_close
    movl    $__NR_close, %eax
    syscall
#else
    mov     $-ENOSYS, %eax
#endif
    ret
END(___close)
.hidden _TRaP_libc____close
