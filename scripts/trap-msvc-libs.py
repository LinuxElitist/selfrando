#!/bin/sh
#
# Copyright (c) 2014-2015, The Regents of the University of California
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# * Redistributions of source code must retain the above copyright notice, this
#   list of conditions and the following disclaimer.
#
# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
#
# * Neither the name of the University of California nor the names of its
#   contributors may be used to endorse or promote products derived from
#   this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#

# The beginning of this script is both valid shell and valid python,
# such that the script starts with the shell and is reexecuted with
# the right python.
'''which' python2.7 > /dev/null && exec python2.7 "$0" "$@" || exec python "$0" "$@"
'''

import os
import shutil
from subprocess import call

def get_platform_name():
    for key, value in os.environ.iteritems():
        if key.lower() == 'platform':
            return value.lower()
    # vcvars32.bat does not set 'Platform', but all the others do
    return "x86"

def get_files_in_dir(base_path='..', exclude_debug=False):
    files = []
    assert os.path.exists(base_path), "invalid path %s" % base_path
    to_abs_path = lambda f: os.path.abspath(os.path.join(directory, f))
    for directory, dirnames, filenames in os.walk(base_path):
        filenames = map(to_abs_path, filenames)
        files += filenames

    if exclude_debug:
        files = filter(lambda f: 'Debug' not in f, files)

    files = filter(lambda f: '.git' not in f, files)
    return files

def get_exe_path(exe_name='TrapLib.exe'):
    files = get_files_in_dir()
    traplib_exes = filter(lambda f: f.endswith(exe_name), files)
    assert len(traplib_exes), "%s not found" % exe_name
    return traplib_exes[0]


def get_path_to_link_exe():
    for base_path in os.environ['PATH'].split(os.pathsep):
        link_path = os.path.join(base_path, "link.exe")
        if os.path.exists(link_path) and os.path.isfile(link_path):
            return link_path

    assert False, "Could not find link.exe"

def set_env_vars():
    """Note: only tested on Windows 8.1 64-bit with VS 2013."""
    lines = ["#!/bin/sh","# set env. variables"]

    # MSVC_LINKER
    link_exe = get_path_to_link_exe()

    link_exe = link_exe.replace("\\", "/") # convert to posix syntax
    lines.append("export MSVC_LINKER_PATH=\"%s\"" % os.path.dirname(link_exe))

    def cygwinify(path):
        return "/" + path.replace(":", "").replace("\\", "/")

    # PATH
    scpt_path = os.path.dirname(os.path.join(os.getcwd(), __file__))
    exes_path = os.path.join(scpt_path, os.pardir, "Release")
    exes_path = os.path.abspath(exes_path)
    if os.path.exists(exes_path) and os.path.isdir(exes_path):
        lines.append("export PATH=%s:$PATH" % cygwinify(exes_path))
    else:
        exes_path = os.path.join(scpt_path, os.pardir, "Debug")
        exes_path = os.path.abspath(exes_path)
        assert os.path.exists(exes_path) and os.path.isdir(exes_path)
        lines.append("export PATH=\"%s\":$PATH" % cygwinify(exes_path))

    # LIB and LIBPATH
    platform_name = get_platform_name()
    libs_path = os.path.join(scpt_path, os.pardir, "TrappedMSVCLibs", platform_name)
    libs_path = os.path.abspath(libs_path)
    if not os.path.exists(libs_path):
        os.makedirs(libs_path)
    else:
        assert os.path.isdir(libs_path)

    platform_subdir = 'x64' if platform_name == 'x64' else ''
    randolib_path = os.path.join(scpt_path, os.pardir, platform_subdir, "Release")
    randolib_path = os.path.abspath(randolib_path)
    randolib_file_path = os.path.join(randolib_path, "RandoLib.lib")
    if not os.path.exists(randolib_file_path) or not os.path.isfile(randolib_file_path):
        randolib_path = os.path.join(scpt_path, os.pardir, platform_subdir, "Debug")
        randolib_path = os.path.abspath(randolib_path)
        randolib_file_path = os.path.join(randolib_path, "RandoLib.lib")
        assert os.path.exists(randolib_file_path) and os.path.isfile(randolib_file_path), \
               "Invalid RandoLib.lib location: %s" % randolib_path

    lines.append("export LIB=\"%s\"\\;\"%s\"\\;$LIB" % (randolib_path, libs_path))
    lines.append("export LIBPATH=\"%s\"\\;\"%s\"\\;$LIBPATH" % (randolib_path, libs_path))

    outpath = os.path.abspath(os.path.join(scpt_path, "set-buildvars-cygwin-%s.sh" % platform_name))
    with open(outpath, "w") as fh:
        fh.write("\n".join(lines))
    os.chmod(outpath, 0o755)
    print "Set build environment variables by sourcing %s" % os.path.basename(outpath)


def get_libs_from_env():
    libs = []
    assert os.environ['LIB'] is not None, r"Error, %LIB% is not set."
    dirs = filter(lambda d: d, os.environ['LIB'].split(';'))
    for d in dirs:
        if not os.path.exists(d):
            continue
        assert os.path.isdir(d)
        files = os.listdir(d)
        files = map(lambda f: os.path.join(d, f), files)
        lib_filter = lambda f: os.path.isfile(f) and f.lower().endswith(".lib")
        libs += filter(lib_filter, files)

    return libs


if __name__ == '__main__':

    # locate the files we need
    trap_lib_exe = get_exe_path()
    input_libs = get_libs_from_env()

    # make sure the output directory exists
    scpt_path = os.path.dirname(os.path.join(os.getcwd(), __file__))
    platform_name = get_platform_name()
    out_path = os.path.join(scpt_path, os.pardir, 'TrappedMSVCLibs', platform_name)
    if not os.path.isdir(out_path):
        os.makedirs(out_path)
        print 'Created output directory %s...' % out_path

    # invoke traplib.exe on each of the libraries we found
    processed = set()
    print 'Added TRaP info to: ',
    for lib in input_libs:
        lib_basename = os.path.basename(lib)
        if lib_basename in processed:  # prefer early paths in %LIB%
            continue
        print "{}, ".format(lib_basename),
        outfile = os.path.join(out_path, lib_basename)
        call([trap_lib_exe, lib, outfile])
        processed.add(lib_basename)
        # now copy the .pdb to it remains alongside the .lib
        assert lib.lower().endswith('.lib')
        pdb = lib[:-4] + ".pdb"
        pdb_copy = os.path.join(out_path, os.path.basename(pdb))
        if os.path.exists(pdb) and os.path.isfile(pdb) \
            and not os.path.exists(pdb_copy):
            shutil.copy2(pdb, out_path)
    print ""

    set_env_vars()
