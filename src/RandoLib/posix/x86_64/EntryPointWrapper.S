/*
 * This file is part of selfrando.
 * Copyright (c) 2015-2017 Immunant Inc.
 * For license information, see the LICENSE file
 * included with selfrando.
 *
 */

#include <asm/unistd.h>

.section .selfrando.entry, "ax", @progbits
.globl Linux_EntryPoint_init
.hidden Linux_EntryPoint_init
.type Linux_EntryPoint_init,@function
Linux_EntryPoint_init:
        // selfrando will patch this to the correct target
        .byte 0xe9
        .long 0x00000000

        push %rdx
        push %rbp
        mov %rsp, %rbp
        and $-0x10, %rsp // need to align stack to 16 bytes

        call Linux_EntryPointImpl

        mov %rbp, %rsp
        pop %rbp
        pop %rdx

        // Try again
        jmp Linux_EntryPoint_init

.globl Linux_EntryPoint_entry
.hidden Linux_EntryPoint_entry
.type Linux_EntryPoint_entry,@function
Linux_EntryPoint_entry:
        .byte 0xe9
        .long 0x00000000

        push %rdx
        push %rbp
        mov %rsp, %rbp
        and $-0x10, %rsp // need to align stack to 16 bytes

        call Linux_EntryPointImpl

        mov %rbp, %rsp
        pop %rbp
        pop %rdx

        // Try again
        jmp Linux_EntryPoint_entry

.globl Linux_EntryPoint_return
.hidden Linux_EntryPoint_return
.type Linux_EntryPoint_return,@function
Linux_EntryPoint_return:
        ret

.globl Linux_EntryPoint_mprotect
.hidden Linux_EntryPoint_mprotect
.type Linux_EntryPoint_mprotect,@function
Linux_EntryPoint_mprotect:
        movl $__NR_mprotect, %eax
        syscall
        ret

