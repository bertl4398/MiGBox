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
L{MiGBox.fs}.
"""

import os, stat
import logging

_log = {'create': 'CREATE {0}<br />',
        'remove': 'REMOVE {0}<br />',
        'sync_to': 'SYNC {0} ==> {1}<br />',
        'sync_eq': 'SYNC {0} == {1}<br />',
        'sync_er': 'SYNC {0} !! {1}<br />',
        'move': 'MOVE {0} ==> {1}<br />',
        'copy': 'COPY {0} ==> {1}<br />'}

def sync_all_files(src, dst, path, modified=True):
    """
    Synchronize all files from src filesystem abstraction to dst
    filesystem abstraction starting at path and continuing recursively.

    @param src: source filesystem abstraction.
    @type src: FileSystem
    @param dst: destination filesystem abstraction.
    @type dst: FileSystem
    @param path: root path
    @type path: str
    @param modified: two-way synchronize modified files.
    @type modified: bool
    """
    for pathname in src.walk(path):
        rel_path = src.relpath(pathname)
        sync_path = os.path.join(dst.root,rel_path)
        if stat.S_ISDIR(src.stat(pathname).st_mode):
            try:
                mtime = dst.stat(sync_path).st_mtime
            except (OSError, IOError):
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
                copy_file(src, pathname, dst, sync_path)

def sync_file(src, src_path, dst, dst_path):
    """
    Synchronize a file from src filesystem abstraction to dst
    filesystem abstraction from src path to dst path using rsync.

    If the files given by src path and dst path are equal, nothing
    is done.

    @param src: source filesystem abstraction.
    @type src: FileSystem
    @param src_path: source path.
    @type src_path: str
    @param dst: destination filesystem abstraction.
    @type dst: FileSystem
    @param dst_path: destination path.
    @type dst_path: str
    """
    try:
        dst_bs = dst.checksums(dst_path)
        src_bs = src.checksums(src_path)
        if set(src_bs) - set(dst_bs):
            delta = src.delta(src_path, dst_bs)
            dst.patch(dst_path, delta)
            logging.info(_log['sync_to'].format(src_path,dst_path))
        else:
            logging.info(_log['sync_eq'].format(src_path,dst_path))
    except:
        logging.error(_log['sync_er'].format(src_path,dst_path))

def copy_file(src, src_path, dst, dst_path):
    try:
        src.copy(src, src_path, dst, dst_path)
        logging.info(_log['copy'].format(src_path,dst_path))
    except (OSError, IOError):
        logging.error(_log['copy'].format(src_path,dst_path))

def move_file(src, src_path, dst_path):
    try:
        src.rename(src_path, dst_path)
        logging.info(_log['move'].format(src_path,dst_path))
    except (OSError, IOError):
        logging.error(_log['move'].format(src_path,dst_path))

def remove_file(src, path):
    try:
        src.remove(path)
        logging.info(_log['remove'].format(path))
    except (OSError, IOError):
        logging.error(_log['remove'].format(path))

def remove_dir(src, path):
    try:
        src.rmdir(path)
        logging.info(_log['remove'].format(path))
    except (OSError, IOError):
        logging.error(_log['remove'].format(path))

def make_dir(src, path):
    try:
        src.mkdir(path)
        logging.info(_log['create'].format(path))
    except (OSError, IOError):
        logging.error(_log['create'].format(path))
