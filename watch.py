import os
import stat
import time
import copy
import threading
import logging
import shutil
import filecmp

from Queue import Queue

from watchdog.events import *
from watchdog.observers import Observer

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

def sync_path(src, dst, path):
    relpath = path.replace(src, "").lstrip(os.sep)
    return os.path.join(dst, relpath)

def sync(src, dst, queue, stop):
    while not stop.isSet():
        event = queue.get()
        path = sync_path(src, dst, event.src_path)
        if isinstance(event, DirCreatedEvent):
            try:
                os.mkdir(path)
            except OSError:
                pass
        elif isinstance(event, FileCreatedEvent):
            try:
                shutil.copy(event.src_path, path)
            except (OSError, IOError):
                pass
        elif isinstance(event, DirDeletedEvent):
            try:
                os.rmdir(path)
            except OSError:
                pass
        elif isinstance(event, FileDeletedEvent):
            try:
                os.remove(path)
            except OSError:
                pass
        elif isinstance(event, FileModifiedEvent):
            try:
                shutil.copy(event.src_path, path)
            except (OSError, IOError):
                pass
        elif isinstance(event, DirMovedEvent):
            dstpath = sync_path(src, dst, event.dest_path)
            try:
                os.rename(path, dstpath)
            except OSError:
                pass
        elif isinstance(event, FileMovedEvent):
            dstpath = sync_path(src, dst, event.dest_path)
            try:
                os.rename(path, dstpath)
            except OSError:
                pass

        cached_logger.info(event)
        queue.task_done()

def sync_all(src, dst, eventQueue, stop):
    if eventQueue.empty():
        for root, dirs, files in os.walk(src):
            for dir_ in dirs:
                path = os.path.join(root, dir_)
                syncpath = sync_path(src, dst, path)
                if not os.path.exists(syncpath):
                    os.mkdir(syncpath)
            for file_ in files:
                path = os.path.join(root, file_)
                syncpath =  sync_path(src, dst, path)
                if not os.path.exists(syncpath):
                    try:
                        shutil.copyfile(path, syncpath)
                    except (OSError, IOError):
                        pass
                elif not filecmp.cmp(path, syncpath, True):
                    try:
                        shutil.copyfile(path, syncpath)
                    except (OSError, IOError):
                        pass
    if not stop.isSet():
        threading.Timer(3, sync_all, [src, dst, eventQueue, stop]).start()
 
class EventQueue(Queue):
    pass

class EventHandler(FileSystemEventHandler):

    def __init__(self, eventQueue):
        super(EventHandler, self).__init__()
        self.eventQueue = eventQueue

    def on_any_event(self, event):
        super(EventHandler, self).on_any_event(event)
        events_logger.info(event)
        eventQueue.put(event)

eventQueue = EventQueue()
stop_sync = threading.Event()
observer = Observer()

source = "/home/benjamin/MiGBox/tests/local"
destination = "/home/benjamin/MiGBox/tests/remote"

event_handler = EventHandler(eventQueue)
observer.schedule(event_handler, path=source, recursive=True)

observer_thread = threading.Thread(target=observer.start, args=[])
sync_thread = threading.Thread(target=sync, args=[source, destination, eventQueue, stop_sync])
sync_all_thread = threading.Timer(3, sync_all, [source, destination, eventQueue, stop_sync])

observer_thread.start()
sync_thread.start()
sync_all_thread.start()

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    pass

observer.stop()
stop_sync.set()
eventQueue.put(FileSystemEvent("SyncStopEvent", ""))
sync_thread.join()
