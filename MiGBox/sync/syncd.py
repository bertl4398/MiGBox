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

from MiGBox.sync import EventQueue, EventHandler, sync_events, sync_all_files
from MiGBox.fs import OSFileSystem, SFTPFileSystem
from MiGBox.sftp import SFTPClient

from watchdog.events import FileSystemEvent

sync_all_thread = None
poll_thread = None

def poll_events(local, remote, stop):
    print "poll"
    events = remote.poll()
    for event in events:
        print event
        local.eventQueue.put(event)
    if not stop.isSet():
        poll_thread = threading.Timer(3, poll_events, [local, remote, stop])
        poll_thread.start()
 
def sync_all(local, remote, stop):
    logger = logging.getLogger("sync")
    logger.debug("Sync all files.<br />")
    print "sync all"
    sync_all_files(local, remote, local.root)
    if not stop.isSet():
        sync_all_thread = threading.Timer(5, sync_all, [local, remote, stop])
        sync_all_thread.start()

def run(mode, source, destination, sftp_host, sftp_port, hostkey, userkey,
        keypass=None, username=None, password=None, logfile=None, loglevel='INFO',
        stopsync=threading.Event(), **kargs):

    sync_logger = logging.getLogger("sync")
    event_logger = logging.getLogger("event")
    sync_logger.setLevel(getattr(logging, loglevel))
    event_logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(levelname)s: %(asctime)s %(message)s')
    ch = logging.StreamHandler()
    ch.setLevel(getattr(logging, loglevel))
    ch.setFormatter(formatter)
    if logfile:
        fh = logging.FileHandler(logfile, mode='w')
        fh.setLevel(getattr(logging, loglevel))
        fh.setFormatter(formatter)
        sync_logger.addHandler(fh)
    else:
        sync_logger.addHandler(ch)
    event_logger.addHandler(logging.FileHandler("events", mode="w"))
    paramiko_logger = logging.getLogger("paramiko.transport")
    paramiko_logger.addHandler(logging.NullHandler())

    sync_logger.info("Connect source and destination ...<br />")

    local = OSFileSystem(root=source)
    remote = None
    if mode == 'local':
        remote = OSFileSystem(root=destination)
    elif mode == 'remote':
        try:
            client = SFTPClient.connect(sftp_host, sftp_port, hostkey, userkey, keypass,
                                        username, password)
        except:
            sync_logger.error("Connection failed!<br />")
            local.observer.stop()
            local.observer.join()
            raise
        remote = SFTPFileSystem(client)
    if not remote:
        sync_logger.error("Connection failed!<br />")
        raise Exception("Connection failed.")

    sync_events_thread = threading.Thread(target=sync_events,
                                          args=[local, remote, local.eventQueue, stopsync])
    sync_events_thread.name = "SyncEvents"

    once = threading.Event()
    once.set()

    sync_all(local, remote, stopsync)
    sync_all(remote, local, once)

    time.sleep(10)

    poll_events(local, remote, stopsync)

    sync_events_thread.start()

    print threading.enumerate()
    while not stopsync.isSet():
        time.sleep(1)

    remote.observer.stop()
    local.observer.stop()
    local.eventQueue.put(FileSystemEvent("SyncStopEvent", ""))
    sync_events_thread.join()
    if sync_all_thread:
        sync_all_thread.cancel()
        sync_all_thread.join()
    if poll_thread:
        poll_thread.cancel()
        poll_thread.join()
