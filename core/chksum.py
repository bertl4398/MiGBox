# Module for checksum computation
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
Module for checksum computation.
Provides methods for checksum and delta computation and application. 
"""
__version__ = 0.1
__author__ = 'Benjamin Ertl'

import zlib

BLOCKSIZE = (64 * 1024)

def blockchksums(filename, size=BLOCKSIZE):
    """
    Compute block checksums for file filename with size size.
    Chechsums are L{zlib.adler32} checksums.

    @param filename: filename.
    @type filename: str
    @param size: block size, default 65536.
    @type size: int
    @return dict as hashtable of tuples as (block offset, block checksum)
    """
    with open(filename, "rb") as f:
        results = {}; offset = 0
        data = f.read(size)
        while data:
            h = zlib.adler32(data) % 2**32
            k = h >> 16
            if k in results:
                results[k].append((offset, h))
            else:
                results[k] = [(offset, h)]
            offset += size
            data = f.read(size)
    return results

def delta(filename, chksums, size=BLOCKSIZE):
    """
    Compute delta for file filename with size size.
        
    @param filename: filename.
    @type filename: str
    @param chksums: checksums from L{blockchksums}
    @type chksums: dict
    @param size: block size, default 65536.
    @type size: int
    @return list of tuples as (block offset, data)
    """
    diff = []
    with open(filename, "rb") as f:
        offset = last = 0; match = False
        data = f.read(size)
        while data:
            h = zlib.adler32(data) % 2**32
            k = h >> 16
            if k in chksums:
                for o, c in chksums[k]:
                    if h == c:
                        # match
                        match = True
                        if offset != last:
                            # append diff data
                            with open(filename, "rb") as tmp:
                                diff.append((last, tmp.read(offset - last)))
                        # append matching block offset
                        diff.append((o, ''))
            if match:
                offset += size
                last = offset
            else:
                offset += 1
                f.seek(offset)
            match = False
            data = f.read(size)
    return diff

def patch(filename, delta, size=BLOCKSIZE):
    """
    Patch file filename.

    @param filename: filename.
    @type filename: str
    @param delta: list of tuples from L{delta}.
    @type delta: list of tuples
    @param size: block size, default 65536.
    @type size: int
    """
    written = []
    with open(filename, "rb") as old:
        with open(filename + ".patched", "wb") as new:
            for offset, data in delta:
                if data:
                    new.write(data)
                    written.append(len(data))
                else:
                    old.seek(offset)
                    d = old.read(size)
                    new.write(d)
                    written.append(len(d))
    return written 
