#!/usr/bin/python
#
# MiGBox sync daemon
#
# Copyright (C) 2013 Benjamin Ertl

"""
Sync daemon for MiGBox.
"""

__version__ = 0.1
__author__ = 'Benjamin Ertl'

import sys, time
import shelve

import rsync

import fs.utils

from fs.osfs import OSFS
from fs.sftpfs import SFTPFS

from fs.watch import *
from fs.errors import *

def sync_file(from_, to, file_):
    newerfile = from_.open(file_,'rb')
    olderfile = to.open(file_,'rb')
    patchedfile = to.open('.' + file_ + '.new','wb')

    delta = rsync.delta(newerfile, rsync.block_chksums(olderfile))

    if not rsync.equalfiles(newerfile,olderfile,delta):
        rsync.patch(newerfile,patchedfile,delta)
        to.rename(file_,'.' + file_+ '.old')
        to.rename('.' + file_ + '.new',file_)
        to.remove('.' + file_ + '.old')
    else:
        to.remove('.' + file_ + '.new')

    patchedfile.close()
    olderfile.close()
    newerfile.close()

def sync_all_files(from_, to):
    for file_ in from_.walkfiles():
        if not to.exists(file_):
            copy_file(from_,to,file_)
        else:
            from_mtime = from_.getinfo(file_)['st_mtime']
            to_mtime = to.getinfo(file_)['st_mtime']

            if from_mtime > to_mtime:
                sync_file(from_,to,file_)

def sync_empty_dirs(from_, to):            
    for dir_ in from_.walkdirs():
        if from_.isdirempty(dir_):
            if not to.exists(dir_):
                to.makedir(dir_)

def copy_file(from_, to, file_):
    try:
        fs.utils.copyfile(from_, file_, to, file_)
    except ParentDirectoryMissingError:
        to.makedir(file_.rsplit('/',1)[0])
        fs.utils.copyfile(from_, file_, to, file_)

def main():
    local_fs = OSFS('../tests/local')
    remote_fs = OSFS('../tests/remote')

    sync_empty_dirs(local_fs,remote_fs)
    sync_empty_dirs(remote_fs,local_fs)
    
    sync_all_files(local_fs,remote_fs)
    sync_all_files(remote_fs,local_fs)

    def watch(event):
        path = event.path
        if isinstance(event, CREATED):
            if local_fs.isdir(path):
                remote_fs.makedir(path)
            else:
                copy_file(local_fs,remote_fs,path)
        if isinstance(event, REMOVED):
            if local_fs.isdir(path):
                if remote_fs.exists(path):
                    remote_fs.removedir(path, recursive=True, force=True)
            else:
                if remote_fs.exists(path):
                    remote_fs.remove(path)
        if isinstance(event, MODIFIED):
            if local_fs.isdir(path):
                sync_all_files(local_fs,remote_fs)
            else:
                sync_file(local_fs,remote_fs,path)

    local_fs_watcher = local_fs.add_watcher(watch)

    wait_for_key_to_exit = raw_input('Press key to exit ...')

    local_fs.del_watcher(local_fs_watcher)

    remote_fs.close()
    local_fs.close()

if __name__ == '__main__':
    main()
