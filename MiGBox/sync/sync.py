# Synchronization module 
#
# Copyright (C) 2013 Benjamin Ertl
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

"""
Synchronization methods to synchronize between file system abstractions see
L{MiGBox.FileSystem}.
"""

import os, stat
import logging

logger = logging.getLogger("sync")

_log = {'create': 'CREATE {0}<br />',
        'remove': 'REMOVE {0}<br />',
        'sync_to': 'SYNC {0} ==> {1}<br />',
        'sync_eq': 'SYNC {0} == {1}<br />',
        'sync_er': 'SYNC {0} !! {1}<br />',
        'sync_conf': 'SYNC {0} !CONFLICT! {1}<br />',
        'move': 'MOVE {0} ==> {1}<br />',
        'copy': 'COPY {0} ==> {1}<br />'}

def sync_all_files(src, dst, path, modified=True, deleted=False):
    """
    Synchronize all files from C{src} file system abstraction to C{dst}
    file system abstraction starting at C{path} and continuing recursively.

    @param src: source file system abstraction.
    @type src: L{MiGBox.FileSystem}
    @param dst: destination file system abstraction.
    @type dst: L{MiGBox.FileSystem}
    @param path: root path
    @type path: str
    @param modified: two-way synchronize modified files.
    @type modified: bool
    """

    for pathname in src.walk(path):
        rel_path = src.get_relative_path(pathname)
        sync_path = os.path.join(dst.root,rel_path)
        if stat.S_ISDIR(src.stat(pathname).st_mode):
            try:
                mtime = dst.stat(sync_path).st_mtime
            except (OSError, IOError):
                if deleted:
                    remove_dir(src, pathname)
                else:
                    make_dir(dst, sync_path)
        else:
            try:
               remote_mtime = dst.stat(sync_path).st_mtime
               local_mtime = src.stat(pathname).st_mtime
               if remote_mtime > local_mtime and modified:
                   sync_file(dst, sync_path, src, pathname)
               elif remote_mtime < local_mtime and modified:
                   sync_file(src, pathname, dst, sync_path)
            except (OSError, IOError):
                if deleted:
                    remove_file(src, pathname)
                else:
                    copy_file(src, pathname, dst, sync_path)

def sync_file(src, src_path, dst, dst_path):
    """
    Synchronize a file from C{src} file system abstraction to C{dst}
    file system abstraction from C{src_path} to C{dst_path}.

    If the files given by C{src_path} and C{dst_path} are equal, nothing
    is done.

    @param src: source file system abstraction.
    @type src: L{MiGBox.FileSystem}
    @param src_path: source path.
    @type src_path: str
    @param dst: destination file system abstraction.
    @type dst: L{MiGBox.FileSystem}
    @param dst_path: destination path.
    @type dst_path: str
    """

    try:
        dst_mod, dst_bs = dst.cached_checksums(dst_path)
        src_mod, src_bs = src.cached_checksums(src_path)
        if dst_mod:
            logger.info(_log['sync_conf'].format(src_path,dst_path))
        if set(src_bs) - set(dst_bs):
            delta = src.delta(src_path, dst_bs)
            dst.patch(dst_path, delta)
            dst.cached_checksums(dst_path)
            logger.info(_log['sync_to'].format(src_path,dst_path))
        else:
            logger.info(_log['sync_eq'].format(src_path,dst_path))
    except:
        logger.error(_log['sync_er'].format(src_path,dst_path))

def copy_file(src, src_path, dst, dst_path):
    """
    Copy a file from C{src} C{src_path} to C{dst} C{dst_path}.

    @param src: source file system abstraction.
    @type src: L{MiGBox.FileSystem}
    @param src_path: source path.
    @type src_path: str
    @param dst: destination file system abstraction.
    @type dst: L{MiGBox.FileSystem}
    @param dst_path: destination path.
    @type dst_path: str
    """

    try:
        src.copy(src, src_path, dst, dst_path)
        logger.info(_log['copy'].format(src_path,dst_path))
    except (OSError, IOError):
        logger.error(_log['copy'].format(src_path,dst_path))

def move_file(src, src_path, dst_path):
    """
    Move a file from C{src} C{src_path} to C{dst_path} on the same
    file system.

    @param src: source file system abstraction.
    @type src: L{MiGBox.FileSystem}
    @param src_path: source path.
    @type src_path: str
    @param dst_path: destination path.
    @type dst_path: str
    """
 
    try:
        src.rename(src_path, dst_path)
        logger.info(_log['move'].format(src_path,dst_path))
    except (OSError, IOError):
        logger.error(_log['move'].format(src_path,dst_path))

def remove_file(src, path):
    """
    Remove a file from C{src} given by C{path}.

    @param src: source file system abstraction.
    @type src: L{MiGBox.FileSystem}
    @param path: path.
    @type path: str
    """
 
    try:
        src.remove(path)
        logger.info(_log['remove'].format(path))
    except (OSError, IOError):
        logger.error(_log['remove'].format(path))

def remove_dir(src, path):
    """
    Remove a directory from C{src} given by C{path}.

    @param src: source file system abstraction.
    @type src: L{MiGBox.FileSystem}
    @param path: path.
    @type path: str
    """
 
    try:
        src.rmdir(path)
        logger.info(_log['remove'].format(path))
    except (OSError, IOError):
        logger.error(_log['remove'].format(path))

def make_dir(src, path):
    """
    Make a new directory at C{src} given by C{path}.

    @param src: source file system abstraction.
    @type src: L{MiGBox.FileSystem}
    @param path: path.
    @type path: str
    """
 
    try:
        src.mkdir(path)
        logger.info(_log['create'].format(path))
    except (OSError, IOError):
        logger.error(_log['create'].format(path))
