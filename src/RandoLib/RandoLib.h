/*
 * Copyright (c) 2014-2015, The Regents of the University of California
 * Copyright (c) 2015-2017 Immunant Inc.
 * All rights reserved.
 *
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions are met:
 *
 * * Redistributions of source code must retain the above copyright notice, this
 *   list of conditions and the following disclaimer.
 *
 * * Redistributions in binary form must reproduce the above copyright notice,
 *   this list of conditions and the following disclaimer in the documentation
 *   and/or other materials provided with the distribution.
 *
 * * Neither the name of the University of California nor the names of its
 *   contributors may be used to endorse or promote products derived from
 *   this software without specific prior written permission.
 *
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
 * AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
 * IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
 * DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
 * FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
 * DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
 * SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
 * CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
 * OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
 * OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
 */

#ifndef __RANDOLIB_H
#define __RANDOLIB_H
#pragma once

#include <OS.h>

#pragma pack(1) // TODO: MSVC-only; use gcc equivalent on Linux
struct RANDO_SECTION Function {
    os::BytePointer undiv_start, div_start;
    size_t size;
    size_t undiv_alignment;
    size_t alignment_padding;

    // Boolean flags
    bool skip_copy  : 1;
    bool from_trap  : 1;
    bool is_padding : 1;
    bool is_gap     : 1;
    bool has_size   : 1;

    ptrdiff_t div_delta() const {
        return skip_copy ? 0 : (div_start - undiv_start);
    }

    os::BytePointer inline undiv_end() const {
        return undiv_start + size;
    }

    os::BytePointer inline div_end() const {
        return div_start + size;
    }

    bool undiv_contains(os::BytePointer addr) const {
        return addr >= undiv_start && addr < undiv_end();
    }

    bool div_contains(os::BytePointer addr) const {
        return addr >= div_start && addr < div_end();
    }

    os::BytePointer post_div_address(os::BytePointer addr) const {
        RANDO_ASSERT(undiv_contains(addr));
        return (addr + div_delta());
    }

    // Tiebreaker rank for elems with the same undiv_addr
    int sort_rank() const {
        // TRaP elems should come before their padding and gaps
        if (from_trap)
            return 1;
        if (is_padding)
            return 2;
        if (is_gap)
            return 3;
        return 4;
    }
};

template<typename T>
struct RANDO_SECTION Vector {
    T *elems;
    size_t num_elems;

    Vector() : elems(nullptr), num_elems(0) { }
    Vector(const Vector&) = delete;
    Vector(const Vector&&) = delete;
    Vector &operator=(const Vector&) = delete;
    Vector &operator=(const Vector&&) = delete;

    void allocate() {
        if (elems != nullptr)
            os::API::MemFree(elems);
        elems = reinterpret_cast<T*>(os::API::MemAlloc(num_elems * sizeof(T), true));
    }

    void free() {
        if (elems != nullptr)
            os::API::MemFree(elems);
        elems = nullptr;
    }

    void extend(size_t num_extra) {
        if (num_extra == 0)
            return;
        if (elems == nullptr) {
            num_elems = num_extra;
            allocate();
            return;
        }

        T *old_elems = elems;
        num_elems += num_extra;
        elems = reinterpret_cast<T*>(os::API::MemAlloc(num_elems * sizeof(T), true));
        os::API::MemCpy(elems, old_elems, (num_elems - num_extra) * sizeof(T));
        os::API::MemFree(old_elems);
    }

    T &operator[](size_t idx) {
        return elems[idx];
    }

    const T &operator[](size_t idx) const {
        return elems[idx];
    }

    template<typename Func>
    void sort(Func compare) {
        os::API::QuickSort(elems, num_elems, sizeof(T), compare);
    }

    template<typename Func>
    void remove_if(Func remove_index) {
        size_t out = 0;
        for (size_t in = 0; in < num_elems; in++) {
            if (remove_index(in))
                continue;
            if (out < in)
                elems[out] = elems[in];
            out++;
        }
        num_elems = out;
        // TODO: shrink the memory region to save space???
    }
};

struct RANDO_SECTION FunctionList : public Vector<Function> {
    Function *FindFunction(os::BytePointer) const;

    // It's unfortunare that we have to use a template here,
    // but it seems we cannot forward-declare os::Module::Relocation
    template<class Reloc>
    void AdjustRelocation(Reloc*) const;
};

#endif // __RANDOLIB_H
