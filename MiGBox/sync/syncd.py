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

import os
import sys
import time
import threading
import logging
import paramiko
import shutil
from Queue import Queue

from MiGBox.sync import sync
from MiGBox.fs import OSFileSystem, SFTPFileSystem
from MiGBox.sftp import SFTPClient

from watchdog.events import * 
from watchdog.observers.polling import PollingObserver as Observer

events_logger = logging.getLogger("events")
events_logger.setLevel(logging.INFO)
cached_logger = logging.getLogger("cached")
cached_logger.setLevel(logging.INFO)
events_fh = logging.FileHandler("events", mode="w")
cached_fh = logging.FileHandler("cached", mode="w")
events_fh.setLevel(logging.INFO)
cached_fh.setLevel(logging.INFO)
events_logger.addHandler(events_fh)
cached_logger.addHandler(cached_fh)

class EventQueue(Queue):
    """
    This class is used to keep track of the file system
    events and is as for now the default python queue.
    """

    pass

class EventHandler(FileSystemEventHandler):
    """
    This class handles all events observed from the watchdog
    observer by putting them into an event queue, that will be 
    processed by the synchronization thread.
    """

    def __init__(self, eventQueue):
        super(EventHandler, self).__init__()
        self.eventQueue = eventQueue

    def on_any_event(self, event):
        super(EventHandler, self).on_any_event(event)
        self.eventQueue.put(event)
        events_logger.info(event)

def sync_thread(local, remote, eventQueue, stopsync):
    while not stopsync.isSet():
        event = eventQueue.get()
        local_path = event.src_path
        remote_path = sync.get_sync_path(local, remote, event.src_path)
        cached_logger.info(event)
        if isinstance(event, DirCreatedEvent):
            sync.make_dir(remote, remote_path)
        elif isinstance(event, FileCreatedEvent):
            sync.copy_file(local, local_path, remote, remote_path)
        elif isinstance(event, DirDeletedEvent):
            sync.remove_dir(remote, remote_path)
        elif isinstance(event, FileDeletedEvent):
            sync.remove_file(remote, remote_path)
        elif isinstance(event, FileModifiedEvent):
            pass
        elif isinstance(event, DirMovedEvent):
            eventQueue.put(DirCreatedEvent(event.dest_path))
            eventQueue.put(DirDeletedEvent(event.src_path))
        elif isinstance(event, FileMovedEvent):
            eventQueue.put(FileCreatedEvent(event.dest_path))
            eventQueue.put(FileDeletedEvent(event.src_path))
        eventQueue.task_done()

def sync_all_thread(local, remote, eventQueue, stopsync):
    if eventQueue.empty():
        sync.sync_all_files(local, remote, local.root)
    if not stopsync.isSet():
        threading.Timer(1, sync_all_thread, [local, remote, eventQueue, stopsync]).start()

def observer_thread(source, eventHandler):
   while True:
        try:
            print "observer start"
            observer = Observer()
            observer.schedule(eventHandler, path=source, recursive=True)
            observer.start()
            observer.join()
        except Exception:
            print "observer failed .. restart"
            continue
        
def run(mode, source, destination, sftp_host, sftp_port, hostkey, userkey,
        keypass=None, username=None, password=None, logfile=None, loglevel='INFO',
        stopsync=threading.Event(), **kargs):

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

    local = OSFileSystem(root=source)
    remote = None
    if mode == 'local':
        remote = OSFileSystem(root=destination)
    elif mode == 'remote':
        client = SFTPClient.connect(sftp_host, sftp_port, hostkey, userkey, keypass,
                                    username, password)
        remote = SFTPFileSystem(client)
    if not remote:
        logger.error("Connection failed!<br />")
        raise Exception("Connection failed.")

    eventQueue = EventQueue()
    eventHandler = EventHandler(eventQueue)

    observer = threading.Thread(target=observer_thread, args=[source, eventHandler])
    observer.name = "Observer"
    sync_all = threading.Thread(target=sync_all_thread, args=[local, remote, eventQueue, stopsync])
    sync_all.name = "SyncAll"
    sync_events = threading.Thread(target=sync_thread, args=[local, remote, eventQueue, stopsync])
    sync_events.name = "SyncEvents"

    sync_all.start()
    observer.start()
    sync_events.start()

    print threading.enumerate()
    while not stopsync.isSet():
        time.sleep(1)

    eventQueue.put(FileSystemEvent("SyncStopEvent", ""))
    sync_events.join()
