/* Generated by gensyscalls.py. Do not edit. */

#include <private/bionic_asm.h>

ENTRY(mremap)
    movq    %rcx, %r10
#ifdef __NR_mremap
    movl    $__NR_mremap, %eax
    syscall
#else
    mov     $-ENOSYS, %eax
#endif
    ret
END(mremap)
