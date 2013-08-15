# Synchronization module 
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
Synchronization methods and classes to synchronize between file system abstractions see
L{MiGBox.FileSystem}.
"""

import os
import stat
import logging
import threading

from Queue import Queue, Empty

from watchdog.events import *

sync_logger = logging.getLogger("sync")
event_logger = logging.getLogger("event")

_log = {'create': 'CREATE {0}<br />',
        'remove': 'REMOVE {0}<br />',
        'sync_to': 'SYNC {0} ==> {1}<br />',
        'sync_eq': 'SYNC {0} == {1}<br />',
        'sync_er': 'SYNC {0} !! {1}<br />',
        'sync_conf': 'SYNC {0} !CONFLICT! {1}<br />',
        'move': 'MOVE {0} ==> {1}<br />',
        'copy': 'COPY {0} ==> {1}<br />'}

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
        event_logger.info(event)

def sync_events(src, dst, eventQueue, stop, lock=threading.Lock()):
    """
    Sync events from the C{eventQueue} between C{src} and C{dst}.

    @param src: source file system abstraction.
    @type src: L{MiGBox.FileSystem}
    @param dst: destination file system abstraction.
    @type dst: L{MiGBox.FileSystem}
    @param eventQueue: event queue.
    @type eventQueue: L{MiGBox.sync.EventQueue}
    @param stop: stop event.
    @type stop: python threading event
    """

    while not stop.isSet():
        event = eventQueue.get()
        lock.acquire()
        print "sync event"
        print event
        src_path = event.src_path
        if not src_path.startswith(src.root):
            swp = src
            src = dst
            dst = swp
        dst_path = get_sync_path(src, dst, src_path)
        print src_path +  " to " + dst_path
        if isinstance(event, DirCreatedEvent):
            make_dir(dst, dst_path)
        elif isinstance(event, FileCreatedEvent):
            sync_file(src, src_path, dst, dst_path)
        elif isinstance(event, DirDeletedEvent):
            remove_dir(dst, dst_path)
            remove_dirs(dst, dst_path)
        elif isinstance(event, FileDeletedEvent):
            remove_file(dst, dst_path)
        elif isinstance(event, FileModifiedEvent):
            sync_file(src, src_path, dst, dst_path)
        elif isinstance(event, DirMovedEvent):
            new_path = get_sync_path(src, dst, event.dest_path)
            move(dst, dst_path, new_path)
            eventQueue.put(DirDeletedEvent(src_path))
        elif isinstance(event, FileMovedEvent):
            new_path = get_sync_path(src, dst, event.dest_path)
            move(dst, dst_path, new_path)
        lock.release()
        eventQueue.task_done()

def get_sync_path(src, dst, path):
    """
    Get the synchronization path for C{dst} from the C{path} on C{src}.

    @param src: source file system abstraction.
    @type src: L{MiGBox.FileSystem}
    @param dst: destination file system abstraction.
    @type dst: L{MiGBox.FileSystem}
    @param path: the path.
    @type path: str
    @return: synchronization path.
    @rtype: str
    """

    rel_path = src.get_relative_path(path)
    # windos path fix -- there might be a better solution
    sync_path = dst.join_path(dst.root, *rel_path.split("\\"))
    return sync_path
 
def sync_all_files(src, dst, path=None):
    """
    Synchronize all files from C{src} file system abstraction to C{dst}
    file system abstraction starting at C{path} and continuing recursively.

    @param src: source file system abstraction.
    @type src: L{MiGBox.FileSystem}
    @param dst: destination file system abstraction.
    @type dst: L{MiGBox.FileSystem}
    @param path: root path
    @type path: str
    """

    if not path:
        path = src.root
    dirs = [path]
    while dirs:
        dir_ = dirs.pop()
        for pathname in src.listdir(dir_):
            abs_path = src.join_path(dir_, pathname)
            sync_path = get_sync_path(src, dst, abs_path)
            try:
                if stat.S_ISDIR(src.stat(abs_path).st_mode):
                    dirs.append(abs_path)
                    try:
                        dst_mtime = dst.stat(sync_path).st_mtime
                    except (OSError, IOError):
                        make_dir(dst, sync_path)
                else:
                    sync_file(src, abs_path, dst, sync_path)
            except (IOError, OSError):
                continue

def sync_file(src, src_path, dst, dst_path):
    """
    Synchronize a file from C{src} file system abstraction to C{dst}
    file system abstraction from C{src_path} to C{dst_path}.

    If the files given by C{src_path} and C{dst_path} are equal, nothing
    is done.

    @param src: source file system abstraction.
    @type src: L{MiGBox.FileSystem}
    @param src_path: source path.
    @type src_path: str
    @param dst: destination file system abstraction.
    @type dst: L{MiGBox.FileSystem}
    @param dst_path: destination path.
    @type dst_path: str
    """

    try:
        dst_mtime = dst.stat(dst_path).st_mtime
    except (OSError, IOError):
        copy_file(src, src_path, dst, dst_path)
    else:
        try:
            src_mtime = src.stat(src_path).st_mtime
        except (OSError, IOError): # src doesnt exist?
            if src_path in src.cache:
                del src.cache[src_path]
            remove_file(dst, dst_path)
        else:
            if not dst_path in dst.cache:
                dst.cache[dst_path] = (dst_mtime, dst.blockchecksums(dst_path))
            if not src_path in src.cache:
                src.cache[src_path] = (src_mtime, src.blockchecksums(src_path))
            cached_dst_mtime, cached_dst_bs = dst.cache[dst_path]
            cached_src_mtime, cached_src_bs = src.cache[src_path]
            if dst_mtime > cached_dst_mtime: # modification has not yet been seen
                sync_logger.info(_log['sync_conf'].format(src_path,dst_path))
                dst.cache[dst_path] = (dst_mtime, dst.blockchecksums(dst_path))
                cached_dst_mtime, cached_dst_bs = dst.cache[dst_path]
            if src_mtime > cached_src_mtime: # modification has not yet been seen
                sync_logger.info(_log['sync_conf'].format(src_path,dst_path))
                src.cache[src_path] = (src_mtime, src.blockchecksums(src_path))
                cached_src_mtime, cached_src_bs = src.cache[dst_path]
            if set(cached_src_bs) - set(cached_dst_bs): # files differ
                if cached_src_mtime >= cached_dst_mtime: # src newer
                    delta = src.delta(src_path, cached_dst_bs)
                    dst.patch(dst_path, delta)
                    dst.cache[dst_path] = (dst.stat(dst_path).st_mtime, dst.blockchecksums(dst_path))
                else:
                    delta = dst.delta(dst_path, cached_src_bs)
                    src.patch(src_path, delta)
                    src.cache[src_path] = (src.stat(src_path).st_mtime, src.blockchecksums(src_path))
                sync_logger.info(_log['sync_to'].format(src_path,dst_path))
            else:
                sync_logger.debug(_log['sync_eq'].format(src_path,dst_path))

def copy_file(src, src_path, dst, dst_path):
    """
    Copy a file from C{src} C{src_path} to C{dst} C{dst_path}.

    @param src: source file system abstraction.
    @type src: L{MiGBox.FileSystem}
    @param src_path: source path.
    @type src_path: str
    @param dst: destination file system abstraction.
    @type dst: L{MiGBox.FileSystem}
    @param dst_path: destination path.
    @type dst_path: str
    """

    try:
        src.copy(src, src_path, dst, dst_path)
        sync_logger.info(_log['copy'].format(src_path,dst_path))
    except:
        sync_logger.debug(_log['copy'].format(src_path,dst_path))

def move(src, src_path, dst_path):
    """
    Move a file/directory from C{src} C{src_path} to C{dst_path}
    on the same file system.

    @param src: source file system abstraction.
    @type src: L{MiGBox.FileSystem}
    @param src_path: source path.
    @type src_path: str
    @param dst_path: destination path.
    @type dst_path: str
    """
 
    try:
        src.rename(src_path, dst_path)
        sync_logger.info(_log['move'].format(src_path,dst_path))
    except (OSError, IOError):
        sync_logger.debug(_log['move'].format(src_path,dst_path))

def remove_file(src, path):
    """
    Remove a file from C{src} given by C{path}.

    @param src: source file system abstraction.
    @type src: L{MiGBox.FileSystem}
    @param path: path.
    @type path: str
    """
 
    try:
        if path in src.cache:
            del src.cache[path]
        src.remove(path)
        sync_logger.info(_log['remove'].format(path))
    except (OSError, IOError):
        sync_logger.debug(_log['remove'].format(path))

def remove_dir(src, path):
    """
    Remove an empty directory from C{src} given by C{path}.

    @param src: source file system abstraction.
    @type src: L{MiGBox.FileSystem}
    @param path: path.
    @type path: str
    """
 
    try:
        src.rmdir(path)
        sync_logger.info(_log['remove'].format(path))
    except (OSError, IOError):
        sync_logger.debug(_log['remove'].format(path))

def remove_dirs(src, path):
    """
    Remove a directory tree of empyt directories from C{src}
    given by C{path}.

    @param src: source file system abstraction.
    @type src: L{MiGBox.FileSystem}
    @param path: path.
    @type path: str
    """ 

    try:
        src.rmdir(path)
    except (OSError, IOError):
        try:
            for pathname in src.listdir(path):
                pathname = src.join_path(path, pathname)
                if stat.S_ISDIR(src.stat(pathname).st_mode):
                    remove_dirs(src, pathname)
            src.rmdir(path)
        except (OSError, IOError):
            pass

def make_dir(src, path):
    """
    Make a new directory at C{src} given by C{path}.

    @param src: source file system abstraction.
    @type src: L{MiGBox.FileSystem}
    @param path: path.
    @type path: str
    """
 
    try:
        src.mkdir(path)
        sync_logger.info(_log['create'].format(path))
    except (OSError, IOError):
        sync_logger.debug(_log['create'].format(path))
