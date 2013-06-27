# Synchronization module 
#
# Copyright (C) 2013 Benjamin Ertl

"""
Synchronization module providing functions for synchronization from
FileSystem abstraction to FileSystem abstraction.
"""

__version__ = 0.2
__author__ = 'Benjamin Ertl'

import os, stat
import filecmp
import logging, traceback
import rsync

log = {'create': 'CREATE {0}',
       'remove': 'REMOVE {0}',
       'sync_to': 'SYNC {0} ==> {1}',
       'sync_eq': 'SYNC {0} == {1}',
       'sync_er': 'SYNC {0} !! {1}',
       'move': 'MOVE {0} ==> {1}',
       'copy': 'COPY {0} ==> {1}'}

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
    dirs = []
    for pathname in src.listdir(path):
        abs_path = os.path.join(path,pathname)
        rel_path = src.relpath(abs_path)
        sync_path = os.path.join(dst.root,rel_path)
        if stat.S_ISDIR(src.stat(abs_path).st_mode):
            dirs.append(abs_path)
            try:
               mtime = dst.stat(sync_path).st_mtime
            except (OSError, IOError):
               make_dir(dst, sync_path)
        else:
            try:
                remote_mtime = dst.stat(sync_path).st_mtime
                local_mtime = src.stat(abs_path).st_mtime
                if remote_mtime > local_mtime and modified:
                    sync_file(dst, sync_path, src, abs_path)
                elif remote_mtime < local_mtime and modified:
                    sync_file(src, abs_path, dst, sync_path)
            except (OSError, IOError):
                copy_file(src, abs_path, dst, sync_path)
    for dir_ in dirs:
        sync_all_files(src, dst, dir_, True)

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
        if not filecmp.cmp(src_path,dst_path,shallow=False):
            newfile = src.open(src_path,'rb')
            oldfile = dst.open(dst_path,'rb')
            tmpfile = dst.open(dst_path+'.tmp','wb')
            delta = rsync.delta(newfile,rsync.block_chksums(oldfile))
            rsync.patch(oldfile,tmpfile,delta)
            tmpfile.close(); oldfile.close(); newfile.close()
            dst.remove(dst_path); dst.rename(dst_path+'.tmp',dst_path)
            logging.info(log['sync_to'].format(src_path,dst_path))
        else:
            logging.info(log['sync_eq'].format(src_path,dst_path))
    except:
        logging.error(log['sync_er'].format(src_path,dst_path))
        traceback.print_exc()

def copy_file(src, src_path, dst, dst_path):
    try:
        src.copy(src, src_path, dst, dst_path)
        logging.info(log['copy'].format(src_path,dst_path))
    except (OSError, IOError):
        logging.error(log['copy'].format(src_path,dst_path))

def move_file(src, src_path, dst_path):
    try:
        src.rename(src_path, dst_path)
        logging.info(log['move'].format(src_path,dst_path))
    except (OSError, IOError):
        logging.error(log['move'].format(src_path,dst_path))

def remove_file(src, path):
    try:
        src.remove(path)
        logging.info(log['remove'].format(path))
    except (OSError, IOError):
        logging.error(log['remove'].format(path))

def remove_dir(src, path):
    try:
        src.rmdir(path)
        logging.info(log['remove'].format(path))
    except (OSError, IOError):
        logging.error(log['remove'].format(path))

def make_dir(src, path):
    try:
        src.mkdir(path)
        logging.info(log['create'].format(path))
    except (OSError, IOError):
        logging.error(log['create'].format(path))
