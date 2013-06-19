#!/usr/bin/python
#
# Rsync by Andrew Tridgell
#
# Copyright (C) 2013 Benjamin Ertl

"""
Rsync demo implementation with weak rolling checksum and sha1 strong checksum.
Based on the rsync algorithm by Andrew Tridgell.
"""

__version__ = 0.2
__author__ = 'Benjamin Ertl'

import os, sys
import hashlib

from collections import namedtuple

default_size = 16384
modulo = 65536

Weakchksum = namedtuple('Weakchksum',['a','b','s','length'])

def sync(oldfile, newfile):
    patchedfile = open('.' + oldfile.name + '.patch', 'wb')
    
    patch(oldfile, patchedfile, delta(newfile, block_chksums(oldfile)))

    os.rename(oldfile.name, '.' + oldfile.name + '.old')
    os.rename(patchedfile.name, oldfile.name)

    patchedfile.close()

def patch(instream, outstream, delta):
    outstream.seek(0)
    for block in delta:
        if type(block) == str:
            outstream.write(block)
        else:
            instream.seek(block[0])
            outstream.write(instream.read(block[1]))

    outstream.flush()
    instream.seek(0)
    outstream.seek(0)

def equalfiles(f1, f2, delta):
    f1.seek(0); f2.seek(0)
    if not f1.read(1) and not f2.read(1):
        return True
    offset = 0; equal = False
    for d in delta:
        if type(d) == str:
            return False
        else:
            blockoffset, size = d
            if offset == blockoffset:
                offset += size
                equal = True
            else:
                return False
    return equal

def delta(stream, blockchksums, blocksize=default_size):
    blocks = []
    offset = last_match_offset = 0
    rollingchksum = rolling_chksum(stream, offset, blocksize)
    try:
        while True:
            chksum = next(rollingchksum)
            match = False
            if chksum.a in blockchksums:
                for block in blockchksums[chksum.a]:
                    if chksum.s == block['weak']:
                        stream.seek(offset)
                        data = stream.read(blocksize)
                        if strong_chksum(data) == block['strong']:
                            match = True
                            stream.seek(last_match_offset)
                            data = stream.read(offset - last_match_offset)
                            if data:
                                blocks.append(data)
                            blocks.append((block['offset'], block['size']))
                            break
            if match:
                offset += block['size']
                last_match_offset = offset
                rollingchksum = rolling_chksum(stream, offset, blocksize)
            else:
                offset += 1

    except StopIteration:
        pass

    stream.seek(last_match_offset)
    data = stream.read()
    if data:
        blocks.append(data)
    return blocks

def block_chksums(stream, offset=0, blocksize=default_size):
    table = dict()
    stream.seek(offset)
    while True:
        data = stream.read(blocksize)
        if not data:
            break
        weakchksum = weak_chksum(data)
        strongchksum = strong_chksum(data)
        if weakchksum.a in table:
            table[weakchksum.a].append({'weak':weakchksum.s,
                                        'strong':strongchksum,
                                        'offset':offset,
                                        'size':weakchksum.length})
        else:
            table[weakchksum.a] = [{'weak':weakchksum.s,
                                    'strong':strongchksum,
                                    'offset':offset,
                                    'size':weakchksum.length}]
        offset += blocksize
    return table

def strong_chksum(data):
    sha1 = hashlib.sha1()
    sha1.update(data)
    return sha1.hexdigest()

def weak_chksum(data, M=modulo):
    length = len(data)
    a = sum([ord(x) for x in data]) % M
    b = sum([(length - i) * ord(data[i]) for i in xrange(0,length)])

    return Weakchksum(a, b, a + (b << 16), length)

def rolling_chksum(stream, offset=0, window=default_size, M=modulo):
    stream.seek(offset)
    data = stream.read(window)
    weakchksum = weak_chksum(data, M=M)
    a, b, _, _ = weakchksum
    yield weakchksum
    while True:
        stream.seek(offset)
        x0 = stream.read(1)
        stream.seek(offset+window)
        x1 = stream.read(1)
        if not x1:
            break
        a = (a - ord(x0) + ord(x1)) % M
        b = (b - window * ord(x0) + a) % M
        offset += 1
        yield Weakchksum(a, b, a + (b << 16), window)        
    offset += 1
    stream.seek(offset)
    data = stream.read()
    yield weak_chksum(data, M=M)
    
def main():
    try:
        oldfilename = sys.argv[1]
        newfilename = sys.argv[2]
    except:
        print "Usage: ", sys.argv[0], "oldfile newfile"; sys.exit(1)

    oldfile = open(oldfilename, 'rb')
    newfile = open(newfilename, 'rb')

    sync(oldfile, newfile)

    oldfile.close()
    newfile.close()

    sys.exit(0)

if __name__ == '__main__':
    main()
