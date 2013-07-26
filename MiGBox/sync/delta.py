# Module for delta computation
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
Module for delta computation.
Provides methods for checksum and delta computation and application. 
"""

import zlib, hashlib
import base64

BLOCKSIZE = 65536

def weakchecksum(data):
    """
    Compute weak checksum.

    @param data: data for checksum computation.
    @type data: str
    @return adler32 checksum.
    """
    return zlib.adler32(data) & 0xffffffff

def strongchecksum(data):
    """
    Compute strong checksum.

    @param data: data for checksum computation.
    @type data: str
    @return md5 hexdigest.
    """
    md5 = hashlib.md5()
    md5.update(data)
    return md5.hexdigest()

def blockchecksums(filename, size=BLOCKSIZE):
    """
    Compute block checksums for file filename with size size.
    Chechsums are L{zlib.adler32} checksums as weak checksums
    and L{hashlib.md5} checksums as strong checksums.

    @param filename: filename.
    @type filename: str
    @param size: block size, default 65536.
    @type size: int
    @return dict as hashtable of tuples as
            (block offset, weak checksum, strong checksum).
    """
    with open(filename, "rb") as f:
        results = {}; offset = 0
        data = f.read(size)
        while data:
            hmd5 = strongchecksum(data)
            h = weakchecksum(data)
            # unicode keys for compatibility with json over sftp
            k = unicode(h >> 16)
            if k in results:
                results[k].append((offset, h, hmd5))
            else:
                results[k] = [(offset, h, hmd5)]
            offset += size
            data = f.read(size)
    return results

def delta(filename, checksums, size=BLOCKSIZE):
    """
    Compute delta for file filename with size size.
        
    @param filename: filename.
    @type filename: str
    @param checksums: checksums from L{blockchecksums}
    @type checksums: dict
    @param size: block size, default 65536.
    @type size: int
    @return list of tuples as (offset, data).
    """
    diff = []
    if not checksums:
        return diff
    with open(filename, "rb") as f:
        offset = last = 0; match = False
        data = f.read(size)
        while data:
            h = weakchecksum(data)
            k = unicode(h >> 16)
            if k in checksums:
                for off, weak, strong in checksums[k]:
                    if h == weak:
                        if strong == strongchecksum(data):
                            # match
                            match = True
                            with open(filename, "rb") as tmp:
                                tmp.seek(last)
                                new_data = tmp.read(offset - last)
                                # base64 encoding for json/sftp compatibility
                                new_data = base64.b64encode(new_data)
                                if new_data:
                                    diff.append((last, new_data))
                                diff.append((off, ''))
                            offset += size
                            last = offset
            if not match:
                # no match
                offset += 1
                f.seek(offset)
            match = False
            data = f.read(size)
        if not diff:
            f.seek(0)
            diff.append((0, f.read()))
    return diff

def patch(filename, delta, size=BLOCKSIZE):
    """
    Patch file filename.
    Write patched file to filename + .patched.

    @param filename: filename.
    @type filename: str
    @param delta: list of tuples from L{delta}.
    @type delta: list of tuples
    @param size: block size, default 65536.
    @type size: int
    @return name of patched file.
    """
    with open(filename, "rb") as old:
        with open(filename + ".patched", "wb") as new:
            for offset, data in delta:
                if data:
                    d = base64.b64decode(data)
                    new.write(d)
                else:
                    old.seek(int(offset))
                    d = old.read(size)
                    new.write(d)
    return filename + ".patched"
