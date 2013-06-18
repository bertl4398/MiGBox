#!/usr/bin/python
#
# Rsync by Andrew Tridgell
#
# Copyright (C) 2013 Benjamin Ertl

"""
Rsync demo implementation with weak rolling checksum and sha1 strong checksum.
Based on the rsync algorithm by Andrew Tridgell.
"""

__version__ = 0.1
__author__ = 'Benjamin Ertl'

import os, sys
import hashlib

default_size = 16384
modulo = 65536

def sync(oldfile, newfile):
    chks = block_chksums(oldfile)
    d = delta(newfile, chks)

    patchedfile = open(oldfile.name + '.patch', 'w+b')
    
    patch(oldfile, patchedfile, d)

    os.rename(oldfile.name, '.' + oldfile.name + '.old')
    os.rename(patchedfile.name, oldfile.name)

    patchedfile.close()

def patch(instream, outstream, delta):
    outstream.seek(0)
    for block in delta:
        if block.data:
            outstream.write(block.data)
        else:
            instream.seek(block.offset)
            outstream.write(instream.read(block.size))

    outstream.flush()
    instream.seek(0)
    outstream.seek(0)

    #print 'old file: %s' % instream.read()
    #print 'new file: %s' % outstream.read()

def delta(stream, block_chksums, blocksize=default_size):
    blocks = []
    offset = last_match_offset = 0
    chksums = rolling_chksum(stream, offset, blocksize)
    try:
        while True:
            a, _, s, _ = next(chksums)
            match = False
            if a in block_chksums:
                for block in block_chksums[a]:
                    if block.chksum == s:
                        stream.seek(offset)
                        data = stream.read(blocksize)
                        sha1 = hashlib.sha1()
                        sha1.update(data)
                        if sha1.hexdigest() == block.sha1:
                            match = True
                            stream.seek(last_match_offset)
                            data = stream.read(offset - last_match_offset)
                            if data:
                                new_block = Block(last_match_offset, len(data), data)
                                blocks.append(new_block)
                            blocks.append(block)
                            break
            if match:
                offset += block.size
                last_match_offset = offset
                chksums = rolling_chksum(stream, offset, blocksize)
            else:
                offset += 1

    except StopIteration:
        pass

    stream.seek(last_match_offset)
    data = stream.read()
    if data:
        block = Block(last_match_offset, len(data), data)
        blocks.append(block)

    return blocks

def block_chksums(stream, offset=0, blocksize=default_size):
    table = dict()
    stream.seek(offset)
    while True:
        offset = stream.tell()
        data = stream.read(blocksize)
        if not data:
            break
        a, b, s, length = weak_chksum(data)
        sha1 = hashlib.sha1()
        sha1.update(data)
        block = Block(offset=offset,size=length)
        block.chksum = s
        block.sha1 = sha1.hexdigest()
        if a in table:
            table[a].append(block)
        else:
            table[a] = [block]
    return table

def weak_chksum(data, M=modulo):
    length = len(data)
    a = sum([ord(x) for x in data]) % M
    b = sum([(length - i) * ord(data[i]) for i in xrange(0,length)])

    return (a, b, a + (b << 16), length)

def rolling_chksum(stream, offset=0, window=default_size, M=modulo):
    stream.seek(offset)
    data = stream.read(window)
    a, b, s, length = weak_chksum(data, M=M)
    yield (a, b, s, length)
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
        yield (a, b, a + (b << 16), window)        
    offset += 1
    stream.seek(offset)
    data = stream.read()
    yield weak_chksum(data, M=M)
    
class Block(object):
    def __init__(self, offset=0, size=0, data=None):
        self.offset = offset
        self.size = size
        self.data = data

    def __str__(self):
        return """Block\n
    offset: %d\n
    size:   %d\n
    data:   %s""" % (self.offset, self.size, repr(self.data))

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
