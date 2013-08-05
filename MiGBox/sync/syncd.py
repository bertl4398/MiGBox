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

    def _get_syncpath(self, path):
        rel_path = self.src.get_relative_path(path)
        return os.path.join(self.dst.root, rel_path)

    def on_created(self, event):
        sync_path = self._get_syncpath(event.src_path)
        if event.is_directory:
            sync.make_dir(self.dst, sync_path)
        else:
            sync.copy_file(self.src, event.src_path, self.dst, sync_path)

    def on_deleted(self, event):
        sync_path = self._get_syncpath(event.src_path)
        if event.is_directory:
            sync.remove_dir(self.dst, sync_path)
        else:
            sync.remove_file(self.dst, sync_path)

    def on_modified(self, event):
        sync_path = self._get_syncpath(event.src_path)
        sync.sync_file(self.src, event.src_path, self.dst, sync_path)

    def on_moved(self, event):
        sync_src = self._get_syncpath(event.src_path)
        sync_dst = self._get_syncpath(event.dest_path)
        sync.move_file(self.dst, sync_src, sync_dst)

def poll(local, remote, stop_polling):
    # get all new remote files
    sync.sync_all_files(remote, local, remote.root, modified=True)
    # delete all files deleted on remote
    sync.sync_all_files(local, remote, local.root, modified=False, deleted=True)
    if not stop_polling.isSet():
        threading.Timer(2, poll, [local, remote, stop_polling]).start()

def run(mode, source, destination, sftp_host, sftp_port, hostkey, userkey,
         username='', password='', logfile=None, loglevel='INFO',
         event=threading.Event(), **kargs):

    logger = logging.getLogger("sync")
    logger.setLevel(getattr(logging, loglevel))
    formatter = logging.Formatter('%(levelname)s: %(asctime)s %(message)s')
    ch = logging.StreamHandler()
    ch.setLevel(getattr(logging, loglevel))
    ch.setFormatter(formatter)
    if logfile:
        fh = logging.FileHandler(logfile, mode='w')
        fh.setLevel(getattr(logging, loglevel))
        fh.setFormatter(formatter)
        logger.addHandler(fh)
    else:
        logger.addHandler(ch)

    paramiko_logger = logging.getLogger("paramiko.transport")
    paramiko_logger.addHandler(logging.NullHandler())

    logger.info("Connect source and destination ...<br />")

    #logging.basicConfig(filename=logfile, filemode='w',
    #    format='%(levelname)s: %(asctime)s %(message)s',
    #    datefmt='%m/%d/%Y %I:%M:%S %p', level=getattr(logging,loglevel))

    local = OSFileSystem(root=source)

    if mode == 'local':
        remote = OSFileSystem(root=destination)
    elif mode == 'remote':
        client = SFTPClient.connect(sftp_host, sftp_port, hostkey, userkey)
        if not client:
            client = SFTPClient.connect(sftp_host, sftp_port, hostkey, userkey,
                                        username, password)
        remote = SFTPFileSystem(client)
        try:
            remote.remove(os.path.join(remote.root, username))
        except:
            pass

    # copy all new files from local to remote
    # sync all modifications from local/remote to local/remote
    # modifications are compared by modification time, the latest wins
    sync.sync_all_files(local, remote, local.root)
    # copy all new files from remote to local
    # sync no modifications, already synced
    sync.sync_all_files(remote, local, remote.root, modified=False)

    event_handler = EventHandler(local, remote)
    observer = Observer()
    observer.schedule(event_handler, path=source, recursive=True)
    observer.start()

    stop_polling = threading.Event()
    threading.Timer(2, poll, [local, remote, stop_polling]).start()
    
    while not event.isSet():
        time.sleep(1)

    stop_polling.set()

    observer.stop()
    observer.join()
