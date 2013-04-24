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


local_fs = OSFS('/home/dev/testdir/1')
remote_fs = OSFS('/home/dev/testdir/2')
combined_fs = MountFS()
combined_fs.mountdir('local', local_fs)
combined_fs.mountdir('remote', remote_fs)

def checksums(infile, blocksize=4096):
    """Generate checksums for all blocks of the input file.

    Args:
        infile: input file object.
        blocksize: number of bytes per block.
    Returns:
        A list of checksums.
    """
    infile.seek(0)
    chck_sums = []
    read = infile.read(blocksize)
    while read:
        # Use adler32 week checksums.
        chck_sums.append(zlib.adler32(read))
        read = infile.read(blocksize)
    return chck_sums

def sync(path, blocksize=4096):
    """Synchronize a file from local to remote filesystem.

    Args:
        path: string, Path of the file to synchronize.
    Returns:
        True if the file was synchronized to the remote filesystem.
    """
    local_file = None
    remote_file = None
    try:
        remote_file = remote_fs.open(path, 'w+b')
        local_file = local_fs.open(path, 'rb')
        local_checksums = checksums(local_file)
        remote_checksums = checksums(remote_file)

        for i in xrange(0,len(local_checksums)):
            if i < len(remote_checksums):
                if local_checksums[i] != remote_checksums[i]:
                    local_file.seek(i*blocksize)
                    remote_file.seek(i*blocksize)
                    remote_file.write(local_file.read(blocksize))
            else:
                local_file.seek(i*blocksize)
                remote_file.seek(0, 2)
                remote_file.write(local_file.read(blocksize))

        remote_file.seek(local_file.seek(0, 2))
        remote_file.truncate()
        local_file.close()
        remote_file.close()
    except Exception, e:
        logging.error(e)
    finally:
        if remote_file:
            remote_file.close()
        if local_file:
            local_file.close()

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
            sync(path)
    if isinstance(event, REMOVED):
        if local_fs.isdir(path):
            combined_fs.removedir('/remote'+path, recursive=True, force=True)
        combined_fs.remove('/remote'+path)
    if isinstance(event, MODIFIED):
        if local_fs.isdir(path):
            raise NotImplementedError
        sync(path)

def init():
    """Initialize the remote filesystem.

    Walks through the local filesystem and creates/recreates folders
    and synchronize all files in each directory.
    """
    for dir_, files in local_fs.walk():
        combined_fs.makedir('/remote'+dir_, allow_recreate=True)
        for file_ in files:
            sync(dir_+'/'+file_)

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
