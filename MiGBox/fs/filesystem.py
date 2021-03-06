# File system abstraction module
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
File system abstraction module.
Provides a wrapper for uniform file system access with os and sftp via paramiko.
"""

import os
import stat
import shutil
import posixpath

from Queue import Empty
from watchdog.observers.polling import PollingObserver as Observer
from MiGBox.sync import EventQueue, EventHandler
from MiGBox.sync.delta import blockchecksums, delta, patch

class FileSystem(object):
    """
    This class provides uniform access to a local or remote file system
    for a number of specified methods.
    """

    def __init__(self, instance):
        """
        Create a new FileSystem object for uniform access.

        The provided methods can be overwritten and are by default passed
        to the instance that represents the file system.

        @param instance: instance representing the file system.
        @type instance: module or class
        """

        self.instance = instance
        self.cache = {}

    def join_path(self, path, *largs):
        """
        Return the joint path of the given parts.

        @param path: path.
        @type path: str
        @param largs: no or more path parts.
        @type largs: str
        @return: joint path.
        @rtype: str
        """

        raise NotImplementedError

    def get_relative_path(self, path):
        """
        Return the relative path to a given path, path - root.

        @param path: path.
        @type path: str
        @return: relative path.
        @rtype: str
        """

        raise NotImplementedError

    def listdir(self, path):
        """
        Return a list of files within a given folder.

        @param path: path to be listed.
        @type path: str
        @return: a list of the files in the given folder.
        @rtype: list
        """

        if not self.instance:
            raise NotImplementedError
        return self.instance.listdir(path)

    def stat(self, path):
        """
        Return a stat object for a path.

        @param path: path for stat infos.
        @type path: str
        """

        if not self.instance:
            raise NotImplementedError
        return self.instance.stat(path)

    def mkdir(self, path, mode=511):
        """
        Create a new directory with the given attributes.

        @param path: path to the new directory.
        @type path: str
        @param mode: requested attributes of the new folder.
        @type mode: int
        """

        if not self.instance:
            raise NotImplementedError
        return self.instance.mkdir(path, mode)

    def mkdirs(self, path, mode=511):
        """
        Create the directory tree for C{path}.

        @param path: path of the directory tree.
        @type path: str
        @param mode: requested attributes of the new folders.
        @type mode: int
        """

        raise NotImplementedError

    def rmdir(self, path):
        """
        Remove an empty directory if it exists.

        @param path: path to the directory to remove.
        @type path: str
        """

        if not self.instance:
            raise NotImplementedError
        return self.instance.rmdir(path)

    def remove(self, path):
        """
        Delete a file, if possible.

        @param path: path the file to delete.
        @type path: str
        """

        if not self.instance:
            raise NotImplementedError
        return self.instance.remove(path)

    def rename(self, src, dst):
        """
        Rename (or move) a file.

        @param src: path of the existing file.
        @type src: str
        @param dst: new path of the file.
        @type dst: str
        """

        if not self.instance:
            raise NotImplementedError
        return self.instance.rename(src, dst)

    def copy(self, src, src_path, dst, dst_path):
        """
        Copy a file from L{FileSystem} to L{FileSystem},
        from C{src_path} to C{dst_path}.

        Here implemented only for L{OSFileSystem} and
        L{SFTPFileSystem} abstractions.

        @param src: source.
        @type src: L{FileSystem}
        @param src_path: source path to copy from.
        @type src_path: str
        @param dst: destination.
        @type dst: L{FileSystem}
        @param dst_path: destination to copy to.
        @type dst_path: str
        """

        if not self.instance:
            raise NotImplementedError

        if isinstance(src, SFTPFileSystem):
            try:
                src.get(src_path, dst_path)
            except IOError:
                dst.mkdirs(os.path.dirname(dst_path))
                src.get(src_path, dst_path)
        elif isinstance(dst, SFTPFileSystem):
            try:
                dst.put(src_path, dst_path)
            except IOError:
                dst.mkdirs(posixpath.dirname(dst_path))
                dst.put(src_path, dst_path)
        else:
            try:
                shutil.copy(src_path, dst_path)
            except IOError:
                dst.mkdirs(os.path.dirname(dst_path))
                shutil.copy(src_path, dst_path)

    def open(self, path, mode='rb', buffering=None):
        """
        Open a file and create a handle for future operations
        on that file.

        @param path: path of the file to be opened.
        @type path: str
        @param mode: mode for opening the file.
        @type mode: str
        @param buffering: buffering for the file.
        @type buffering: int
        @return: a new file object.
        @rtype: file object 
        """

        raise NotImplementedError

    def blockchecksums(self, path):
        """
        Compute block checksums for a given file.

        @param path: path to the file.
        @type path: str
        @return: hashtable of block checksums, see L{MiGBox.sync.delta}
        @rtype: dict
        """

        raise NotImplementedError

    def delta(self, path, checksums):
        """
        Compute a delta for a given file, according to the block checksums.

        @param path: path to the file.
        @type path: str
        @param checksums: block checksums of old/other file.
        @type checksums: dict
        @return: delta of the given file to be applied with L{patch}.
        @rtype: list
        """

        raise NotImplementedError

    def patch(self, path, delta):
        """
        Patch a given file according to the delta of the file to an old/other file.

        @param path: path to the file.
        @type path: str 
        @param delta: delta to an old/other file.
        @type delta: list
        """

        raise NotImplementedError

    def poll(self):
        """
        Poll for changes on the file system.
        """

        raise NotImplementedError

class OSFileSystem(FileSystem):
    """
    This class represents a file system implemented by the python os module.
    """

    def __init__(self, instance=os, root='.'):
        FileSystem.__init__(self, instance)
        self.root = os.path.normpath(root)
        self.eventQueue = EventQueue()
        self.eventHandler = EventHandler(self.eventQueue)
        self.observer = Observer()
        self.observer.schedule(self.eventHandler, path=self.root, recursive=True)
        self.observer.start()

    def join_path(self, path, *largs):
        return os.path.join(path, *largs)

    def get_relative_path(self, path):
        if path.startswith(self.root):
            return path.split(self.root + os.path.sep, 1)[1]
        else:
            return path

    def open(self, path, mode='rb', buffering=None):
        return open(path, mode)

    def mkdirs(self, path, mode=511):
        return os.makedirs(path, mode)

    def blockchecksums(self, path):
        return blockchecksums(path) 

    def delta(self, path, checksums):
        return delta(path, checksums)

    def patch(self, path, delta):
        patched = patch(path, delta)
        self.instance.remove(path)
        return self.instance.rename(patched, path)

    def poll(self):
        r = []
        while True:
            try:
                r.append(self.eventQueue.get_nowait())
            except Empty:
                break
        return r 
    
class SFTPFileSystem(FileSystem):
    """
    This class represents a file system implemented by the L{MiGBox.sftp.SFTPClient}.
    """

    def __init__(self, instance, root='.'):
        FileSystem.__init__(self, instance)
        self.root = posixpath.normpath(root)

    def join_path(self, path, *largs):
        return posixpath.join(path, *largs)

    def get_relative_path(self, path):
        if path.startswith(self.root):
            return path.split(self.root + posixpath.sep, 1)[1]
        else:
            return path

    def open(self, path, mode='rb', buffering=None):
        return self.instance.open(path, mode)

    def mkdirs(self, path, mode=511):
        paths = self.get_relative_path(path).split(posixpath.sep)
        path = self.root
        for p in paths:
            path = self.join_path(path, p)
            try:
                self.mkdir(path)
            except IOError:
                continue

    def blockchecksums(self, path):
        return self.instance.checksums(path)

    def delta(self, path, chksums):
        return self.instance.delta(path, chksums)

    def patch(self, path, delta):
        return self.instance.patch(path, delta)

    def get(self, src, dst):
        return self.instance.get(src, dst)

    def put(self, src, dst):
        return self.instance.put(src, dst)

    def poll(self):
        return self.instance.poll()
