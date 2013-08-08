import unittest

import os
import zlib
import hashlib

from MiGBox.fs import FileSystem, OSFileSystem, SFTPFileSystem

class FileSystemTest(unittest.TestCase):

    def tearDown(self):
        pass

    def test_walkOS(self):
        print "walk os"
        fs = OSFileSystem()
        for pathname in fs.walk(fs.root):
            print "path " + pathname
            rel_path = fs.get_relative_path(pathname)
            print "rel_path " + rel_path
            sync_path = fs.join_path(fs.root, rel_path)
            print "sync_path " + sync_path
        pass

    def test_walkSFTP(self):
        print "walk sftp"
        fs = SFTPFileSystem(os)
        for pathname in fs.walk(fs.root):
            print "path " + pathname
            rel_path = fs.get_relative_path(pathname)
            print "rel_path " + rel_path
            sync_path = fs.join_path(fs.root, rel_path)
            print "sync_path " + sync_path
        pass

if __name__ == '__main__':
    unittest.main()
