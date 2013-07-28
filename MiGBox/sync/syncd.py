# MiGBox sync daemon
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
Sync daemon for MiGBox.
"""

import os, sys, time
import threading
import logging
import paramiko

from MiGBox.sync import sync
from MiGBox.fs import OSFileSystem, SFTPFileSystem
from MiGBox.sftp import SFTPClient

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

class EventHandler(FileSystemEventHandler):
    def __init__(self, src, dst):
        FileSystemEventHandler.__init__(self)
        self.src = src
        self.dst = dst

    def get_syncpath(self, path):
        rel_path = self.src.relpath(path)
        return os.path.join(self.dst.root, rel_path)

    def on_created(self, event):
        sync_path = self.get_syncpath(event.src_path)
        if event.is_directory:
            sync.make_dir(self.dst, sync_path)
        else:
            sync.copy_file(self.src, event.src_path, self.dst, sync_path)

    def on_deleted(self, event):
        sync_path = self.get_syncpath(event.src_path)
        if event.is_directory:
            sync.remove_dir(self.dst, sync_path)
        else:
            sync.remove_file(self.dst, sync_path)

    def on_modified(self, event):
        sync_path = self.get_syncpath(event.src_path)
        sync.sync_file(self.src, event.src_path, self.dst, sync_path)

    def on_moved(self, event):
        sync_src = self.get_syncpath(event.src_path)
        sync_dst = self.get_syncpath(event.dest_path)
        sync.move_file(self.dst, sync_src, sync_dst)

def run(src_path, dst_path, sftp_host, sftp_port, host_key, user_key,
         log_file, log_level, event=threading.Event()):

    logging.basicConfig(filename=log_file, filemode='w',\
                        format='%(levelname)s: %(asctime)s %(message)s',\
                        datefmt='%m/%d/%Y %I:%M:%S %p', level=getattr(logging,log_level))

    local = OSFileSystem(root=src_path)
    remote = OSFileSystem(root=dst_path)

#   client = SFTPClient()
#   client.connect(sftp_host, sftp_port, host_key, user_key)
#   remote = SFTPFileSystem(client)

    # copy all new files from local to remote
    # sync all modifications from local/remote to local/remote
    # modifications are compared by modification time, the latest wins
    sync.sync_all_files(local, remote, local.root)
    # copy all new files from remote to local
    # sync no modifications, already synced
    sync.sync_all_files(remote, local, remote.root, modified=False)

    event_handler = EventHandler(local, remote)
    observer = Observer()
    observer.schedule(event_handler, path=src_path, recursive=True)
    observer.start()

    while not event.isSet():
        time.sleep(1)

    observer.stop()
    observer.join()

if __name__ == '__main__':

    log_file = '/home/benjamin/MiGBox/log/sync.log'
    log_level = 'INFO'

    src_path = '/home/benjamin/MiGBox/tests/local'
    dst_path = '/home/benjamin/MiGBox/tests/remote'

    sftp_host = ''
    sftp_port = 50007 

    host_key = '/home/benjamin/MiGBox/keys/server_rsa_key.pub'
    user_key = '/home/benjamin/MiGBox/keys/user_rsa_key'

    run(src_path, dst_path, sftp_host, sftp_port, host_key, user_key,
         log_file, log_level)
