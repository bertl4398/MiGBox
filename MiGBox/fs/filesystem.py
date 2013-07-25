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

from MiGBox.sync.delta import *

class FileSystem(object):
    def __init__(self, instance=None, root='.'):
        self.instance = instance
        self.root = root
        self.cache = {}

    def listdir(self, path=None):
        if not self.instance:
            raise NotImplementedError
        if not path:
            path = self.root
        return self.instance.listdir(path)

    def walk(self, path):
        if not self.instance:
            raise NotImplementedError
        dirs = [path]
        while dirs:
            dir_ = dirs.pop()
            for name in self.instance.listdir(dir_):
                abs_path = os.path.join(dir_, name)
                if stat.S_ISDIR(self.instance.stat(abs_path).st_mode):
                    dirs.append(abs_path)
                yield abs_path

    def stat(self, path):
        if not self.instance:
            raise NotImplementedError
        return self.instance.stat(path)

    def mkdir(self, path, mode=511):
        if not self.instance:
            raise NotImplementedError
        return self.instance.mkdir(path, mode)

    def rmdir(self, path):
        if not self.instance:
            raise NotImplementedError
        return self.instance.rmdir(path)

    def remove(self, path):
        if not self.instance:
            raise NotImplementedError
        return self.instance.remove(path)

    def rename(self, src, dst):
        if not self.instance:
            raise NotImplementedError
        return self.instance.rename(src, dst)

    def copy(self, src, src_path, dst, dst_path):
        if not self.instance:
            raise NotImplementedError
        if isinstance(src, SFTPFileSystem):
            return src.get(src_path, dst_path)
        elif isinstance(dst, SFTPFileSystem):
            return dst.put(src_path, dst_path)
        return shutil.copy(src_path, dst_path)

    def relpath(self, path):
        return path.replace(self.root+os.path.sep,'')

    def open(self, path, mode='rb', buffering=None):
        raise NotImplementedError

    def cached_checksums(self, path):
        if not self.instance:
            raise NotImplementedError
        key = strongchksum(path + str(self.stat(path).st_mtime))
        if not key in self.cache:
            self.cache[key] = self.checksums(path)
        return self.cache[key]

    def checksums(self, path):
        raise NotImplementedError

    def delta(self, path, chksums):
        raise NotImplementedError

    def patch(self, path, delta):
        raise NotImplementedError

class OSFileSystem(FileSystem):
    def __init__(self, instance=os, root='.'):
        FileSystem.__init__(self, instance, root)

    def open(self, path, mode='rb', buffering=None):
        return open(path, mode)

    def checksums(self, path):
        return blockchksums(path) 

    def delta(self, path, chksums):
        return delta(path, chksums)

    def patch(self, path, delta):
        patched = patch(path, delta)
        return self.instance.rename(patched, path)
    
class SFTPFileSystem(FileSystem):
    def __init__(self, instance, root='.'):
        FileSystem.__init__(self, instance, root)

    def open(self, path, mode='rb', buffering=None):
        return self.instance.open(path, mode)

    def checksums(self, path):
        return self.instance.checksums(path)

    def delta(self, path, chksums):
        return self.instance.delta(path, chksums)

    def patch(self, path, delta):
        return self.instance.patch(path, delta)

    def get(self, src, dst):
        return self.instance.get(src, dst)

    def put(self, src, dst):
        return self.instance.put(src, dst)


