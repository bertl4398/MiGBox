# File system abstraction
#
# Copyright (C) 2013 Benjamin Ertl

"""
File system abstraction.
Based on the idea of pyfilesystem.
"""

__version__ = 0.1
__author__ = 'Benjamin Ertl'

import os, shutil, stat
import paramiko

class FileSystem(object):
    def __init__(self, instance=None, root='.'):
        self.instance = instance
        self.root = root

    def listdir(self, path='.'):
        if not self.instance:
            raise NotImplementedError
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
        if isinstance(src, paramiko.SFTPClient):
            return src.get(src_path, dst_path)
        elif isinstance(dst, paramiko.SFTPClient):
            return dst.put(src_path, dst_path)
        else:
            try:
                return shutil.copy(src_path, dst_path)
            except:
                raise NotImplementedError

    def relpath(self, path):
        return path.replace(self.root+os.path.sep,'')

    def open(self, path, mode='rb', buffering=None):
        raise NotImplementedError

    def checksums(self):
        raise NotImplementedError

class OSFileSystem(FileSystem):
    def __init__(self, instance=os, root='.'):
        FileSystem.__init__(self, instance, root)

    def open(self, path, mode='rb', buffering=None):
        return open(path, mode)

class SFTPFileSystem(FileSystem):
    def __init__(self, instance, root='.'):
        FileSystem.__init__(self, instance, root)

    def open(self, path, mode='rb', buffering=None):
        return self.instance.open(path, mode)
