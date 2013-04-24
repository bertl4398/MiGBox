#!/usr/bin/python

import sys
import zlib
import logging
import traceback

from fs.osfs import OSFS
from fs.sftpfs import SFTPFS
from fs.mountfs import MountFS

from fs.watch import *
from fs.errors import *


local_fs = OSFS('~/testdir/1')
remote_fs = OSFS('~/testdir/2')
combined_fs = MountFS()
combined_fs.mountdir('local', local_fs)
combined_fs.mountdir('remote', remote_fs)

def checksums(file_, blocksize=4096):
    """Generate checksums for all blocks of the input file.

    Args:
        file_: input file object.
        blocksize: number of bytes per block.
    Returns:
        A list of checksums.
    """
    file_.seek(0)
    chck_sums = []
    read = file_.read(blocksize)
    while read:
        # Use adler32 week checksums.
        chck_sums.append(zlib.adler32(read))
        read = file_.read(blocksize)
    return chck_sums

def sync(from_file, to_file, blocksize=4096):
    """Synchronize a file from local to remote filesystem.

    Args:
        from_file: file to synchronize from.
        to_file: file to synchronize to.
    """
    try:
        from_checksums = checksums(from_file)
        to_checksums = checksums(to_file)

        for i in xrange(0,len(from_checksums)):
            if i < len(to_checksums):
                if from_checksums[i] != to_checksums[i]:
                    from_file.seek(i*blocksize)
                    to_file.seek(i*blocksize)
                    to_file.write(from_file.read(blocksize))
            else:
                from_file.seek(i*blocksize)
                to_file.seek(0, 2)
                to_file.write(from_file.read(blocksize))

        to_file.seek(from_file.seek(0, 2))
        to_file.truncate()
    except Exception, e:
        logging.error(e)
        traceback.print_exc()
    finally:
        if from_file:
            from_file.close()
        if to_file:
            to_file.close()

def watch(event):
    """Callback for local filesystem watcher.

    Args:
        event: The callback event.
    """
    path = event.path
    if isinstance(event, CREATED):
        if local_fs.isdir(path):
            combined_fs.makedir('/remote'+path)
        else:
            sync(local_fs.open(path,'rb'),
                 remote_fs.open(path,'w+b'))
    if isinstance(event, REMOVED):
        if local_fs.isdir(path):
            combined_fs.removedir('/remote'+path, recursive=True, force=True)
        combined_fs.remove('/remote'+path)
    if isinstance(event, MODIFIED):
        if local_fs.isdir(path):
            raise NotImplementedError
        sync(local_fs.open(path,'rb'),
             remote_fs.open(path,'w+b'))

def init():
    """Initial synchronization.

    Walks through the remote and local filesystem and creates/recreates
    folders and synchronizes all files in each directory according to their
    last modification time.
    """
    for dir_, files in remote_fs.walk():
        combined_fs.makedir('/local'+dir_, allow_recreate=True)
        for file_ in files:
            sync(remote_fs.open(dir_+'/'+file_,'rb'),
                 local_fs.open(dir_+'/'+file_,'w+b'))
    for dir_, files in local_fs.walk():
        combined_fs.makedir('/remote'+dir_, allow_recreate=True)
        for file_ in files:
            sync(local_fs.open(dir_+'/'+file_,'rb'),
                 remote_fs.open(dir_+'/'+file_,'w+b'))
def main():
    """Main entry point."""
    try:
        init()

        local_fs_watcher = local_fs.add_watcher(watch)

        wait_for_key_to_exit = raw_input('Press key to exit ...')
   
    except Exception, e:
        traceback.print_exc()
        sys.exit(1)

    finally:
        local_fs.del_watcher(local_fs_watcher)
        combined_fs.close()
        remote_fs.close()
        local_fs.close()

if __name__ == '__main__':
    main()
