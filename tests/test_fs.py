import unittest

import os
import shutil

from MiGBox.fs import FileSystem, OSFileSystem, SFTPFileSystem

class FileSystemTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        try:
            os.mkdir(".testdir")
        except:
            pass
        finally:
            cls.fs = OSFileSystem(root=".testdir")

    @classmethod
    def tearDownClass(cls):
        cls.fs.observer.stop()
        cls.fs.observer.join()

        shutil.rmtree(".testdir")

    def test_join_path(self):
        fs = self.fs

        self.assertEqual(fs.join_path(".","new"),os.path.join(".","new"))

    def test_get_relative_path(self):
        fs = self.fs

        self.assertEqual(fs.get_relative_path(".testdir/new"),"new")
        self.assertEqual(fs.get_relative_path("new"),"new") 

    def test_listdir(self):
        fs = self.fs

        self.assertEqual(fs.listdir(".testdir"),os.listdir(".testdir"))

    def test_stat(self):
        fs = self.fs

        self.assertEqual(fs.stat(".testdir"),os.stat(".testdir")) 

    def test_mkdir(self):
        fs = self.fs

        fs.mkdir(".testdir/newdir")

        self.assertTrue(os.path.exists(".testdir/newdir"))

    def test_mkdirs(self):
        fs = self.fs

        fs.mkdirs(".testdir/newdir/newdir")

        self.assertTrue(os.path.exists(".testdir/newdir/newdir"))

    def test_rmdir(self):
        fs = self.fs

        os.mkdir(".testdir/removedir")
        fs.rmdir(".testdir/removedir")

        self.assertFalse(os.path.exists(".testdir/removedir"))

    def test_remove(self):
        fs = self.fs

        f = open(".testdir/removefile","w")
        f.close()

        fs.remove(".testdir/removefile")

        self.assertFalse(os.path.exists(".testdir/removefile"))

    def test_rename(self):
        fs = self.fs

        f = open(".testdir/oldfile","w")
        f.close()

        fs.rename(".testdir/oldfile", ".testdir/newfile")

        self.assertFalse(os.path.exists(".testdir/oldfile"))
        self.assertTrue(os.path.exists(".testdir/newfile"))

    def test_copy(self):
        fs = self.fs

        f = open(".testdir/copyfile","w")
        f.close()

        fs.copy(fs,".testdir/copyfile",fs,".testdir/file")

        self.assertTrue(os.path.exists(".testdir/copyfile"))
        self.assertTrue(os.path.exists(".testdir/file"))

    def test_open(self):
        fs = self.fs

        f = open(".testdir/openfile","w")
        f.close()

        f1 = fs.open(".testdir/openfile")
        f2 = open(".testdir/openfile","rb")

        self.assertEqual(type(f1), type(f2))

if __name__ == '__main__':
    unittest.main()
