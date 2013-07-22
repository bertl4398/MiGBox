#!/usr/bin/python
#
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

__version__ = 0.3
__author__ = 'Benjamin Ertl'

import os, sys, time
import threading
import logging, traceback
import paramiko, watchdog

import sync

from filesystem import *
from sftp_client import SFTPClient

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer
from ConfigParser import ConfigParser

class EventHandler(watchdog.events.FileSystemEventHandler):
    def __init__(self, src, dst):
        watchdog.events.FileSystemEventHandler.__init__(self)
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

def main(sftp=True, event=threading.Event()):
    config = ConfigParser()
    config.read('config.cfg')

    log_file = config.get('Logging', 'log_file')
    log_level = config.get('Logging', 'log_level')

    src_path = config.get('Sync', 'sync_src')
    dst_path = config.get('Sync', 'sync_dst')

    sftp_host = config.get('Connection', 'sftp_host')
    sftp_port = config.getint('Connection', 'sftp_port')

    logging.basicConfig(filename=log_file, filemode='w',\
                        format='%(levelname)s: %(asctime)s %(message)s',\
                        datefmt='%m/%d/%Y %I:%M:%S %p', level=getattr(logging,log_level))

    local = OSFileSystem(root=src_path)
    remote = None

    if sftp == 'False':
        remote = OSFileSystem(root=dst_path)
    else:
        client = SFTPClient(sftp_host, sftp_port)
        try:
            client.connect('test','test')
            remote = SFTPFileSystem(client)
        except Exception as e:
            print e

    if remote:
        sync.sync_all_files(local, remote, local.root)
        sync.sync_all_files(remote, local, remote.root, modified=False)

        event_handler = EventHandler(local, remote)
        observer = Observer()
        observer.schedule(event_handler, path=src_path, recursive=True)
        observer.start()

        try:
            while not event.isSet():
                time.sleep(1)
        except KeyboardInterrupt:
            pass

        observer.stop()
        observer.join()

if __name__ == '__main__':
    try:
        sftp = sys.argv[1]
        print 'Local sync ...'
    except IndexError:
        print 'SFTP sync ...'

    if sftp == 'False':
        main(sftp)
    else:
        main()
