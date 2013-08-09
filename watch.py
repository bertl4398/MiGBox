import os
import stat
import time
import copy
import threading
import logging
import shutil

from Queue import Queue

from watchdog.events import *
from watchdog.observers import Observer

#logging.basicConfig(filename="synclog", filemode="w", level=logging.DEBUG)

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
        try:
            if isinstance(event, DirCreatedEvent):
                path = sync_path(src, dst, event.src_path)
                if not os.path.exists(path):
                    os.mkdir(path)
            elif isinstance(event, FileCreatedEvent):
                path = sync_path(src, dst, event.src_path)
                shutil.copy(event.src_path, path)
            elif isinstance(event, DirDeletedEvent):
                path = sync_path(src, dst, event.src_path)
                os.rmdir(path)
            elif isinstance(event, FileDeletedEvent):
                path = sync_path(src, dst, event.src_path)
                os.remove(path)
            elif isinstance(event, FileModifiedEvent):
                path = sync_path(src, dst, event.src_path)
            elif isinstance(event, DirMovedEvent) or isinstance(event, FileMovedEvent):
                srcpath = sync_path(src, dst, event.src_path)
                dstpath = sync_path(src, dst, event.dest_path)
                shutil.move(srcpath, dstpath)
            else:
                sync_all(src, dst)
        except(shutil.Error, OSError, IOError):
            queue.add(FileSystemEvent("SyncAllEvent", event.src_path))

        cached_logger.info(event)
        queue.task_done()

def sync_all(src, dst):
        for root, dirs, files in os.walk(src):
            for dir_ in dirs:
                 path = os.path.join(root, dir_)
                 syncpath = sync_path(src, dst, path)
                 if not os.path.exists(syncpath):
                     os.mkdir(syncpath)
            for file_ in files:
                path = os.path.join(root, file_)
                shutil.copyfile(path, sync_path(src, dst, path))

class EventQueue(Queue):

    def add(self, item, block=True, timeout=None):
        tmp = copy.copy(self.queue)
        if not item in tmp:
            self.put(item, block, timeout)

class EventHandler(FileSystemEventHandler):

    def __init__(self, eventQueue):
        super(EventHandler, self).__init__()
        self.eventQueue = eventQueue

    def on_any_event(self, event):
        super(EventHandler, self).on_any_event(event)
        events_logger.info(event)
        eventQueue.add(event)

eventQueue = EventQueue()
stop_sync = threading.Event()
observer = Observer()

source = "/home/benjamin/migsync/MiGBox/tests/local"
destination = "/home/benjamin/migsync/MiGBox/tests/remote"

event_handler = EventHandler(eventQueue)
observer.schedule(event_handler, path=source, recursive=True)

observer_thread = threading.Thread(target=observer.start, args=[])
sync_thread = threading.Thread(target=sync, args=[source, destination, eventQueue, stop_sync])

observer_thread.start()
sync_thread.start()

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    pass

stop_sync.set()
eventQueue.add(FileSystemEvent("SyncStopEvent", ""))
sync_thread.join()
