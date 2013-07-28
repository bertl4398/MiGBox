import unittest

import os
import zlib
import hashlib

from MiGBox.sync.delta import weakchecksum, strongchecksum, blockchecksums, delta

class DeltaTest(unittest.TestCase):

    def tearDown(self):
        os.remove('.tmp')
        os.remove('.tmp1')
        os.remove('.tmp2')

    def test_weakchecksum(self):
        data = 'hello'
        c1 = zlib.adler32(data) & 0xffffffff
        c2 = weakchecksum(data)
        self.failUnlessEqual(c1, c2)

    def test_strongchecksum(self):
        data = 'hello'
        md5 = hashlib.md5()
        md5.update(data)
        c1 = md5.hexdigest()
        c2 = strongchecksum(data)
        self.failUnlessEqual(c1, c2)

    def test_blockchecksums(self):
        data = 'hello'
        md5 = hashlib.md5()
        md5.update(data)
        c1 = zlib.adler32(data) & 0xffffffff
        c2 = md5.hexdigest()

        h1 = { unicode(c1 >> 16): [(0, c1, c2)] }

        with open('.tmp','wb') as f:
            f.write(data)

        h2 = blockchecksums('.tmp')

        self.failUnlessEqual(h1, h2)

    def test_delta_equal(self):
        data = 'hello'

        with open('.tmp', 'wb') as f:
            f.write(data)

        d = delta('.tmp', blockchecksums('.tmp'))

        self.failUnlessEqual([(0, '')], d)

    def test_delta_new(self):
        data = 'hello'

        with open('.tmp1', 'wb') as f:
            f.write(data)

        new = open('.tmp2', 'wb')
        new.close()

        d = delta('.tmp1', blockchecksums('.tmp2'))

        self.failUnlessEqual([(0, 'hello')], d)

if __name__ == '__main__':
    unittest.main()
