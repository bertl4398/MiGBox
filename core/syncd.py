#!/usr/bin/python
#
# MiGBox sync daemon
#
# Copyright (C) 2013 Benjamin Ertl

"""
Sync daemon for MiGBox.
"""

__version__ = 0.2
__author__ = 'Benjamin Ertl'

import os, sys, time
import logging, traceback
import paramiko, watchdog
import ConfigParser

import sync

from filesystem import *
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

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

def main():
    config = ConfigParser.ConfigParser()
    config.read('config.cfg')

    log_file = config.get('Logging', 'file')
    log_level = config.get('Logging', 'level')

    src_path = config.get('Sync', 'src')
    dst_path = config.get('Sync', 'dst')

    logging.basicConfig(filename=log_file, filemode='w',\
                        format='%(levelname)s: %(asctime)s %(message)s',\
                        datefmt='%m/%d/%Y %I:%M:%S %p', level=getattr(logging,log_level))

    local = OSFileSystem(root=src_path)
    remote = OSFileSystem(root=dst_path)

    sync.sync_all_files(local, remote, local.root)
    sync.sync_all_files(remote, local, remote.root, modified=False)

    event_handler = EventHandler(local, remote)
    observer = Observer()
    observer.schedule(event_handler, path=src_path, recursive=True)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass

    observer.stop()
    observer.join()

    sys.exit(0)

if __name__ == '__main__':
    main()
