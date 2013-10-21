#!/usr/bin/python

import subprocess
import timeit

from MiGBox.sync import delta

def checksum_dist(filename, n, w):

    blocksize = n * 1024

    b = delta.blockchecksums(filename, blocksize)
    dist = []
    print "BLOCKSIZE {0}".format(blocksize)
    for i in xrange(1,w):
        num = len([len(x) for x in b.values() if len(x) == i])
        print "{0}: {1}".format(i, num)
        dist.append(num)

    return [float(x)/sum(dist) for x in dist]

def delta_blocksize():
    with open("blocksize", "w") as f:
        for count in [10**x for x in xrange(0,4)]:
            subprocess.call(["dd", "if=/dev/urandom", "of=1.dat", "bs=4096", "count={}".format(count)])
            subprocess.call(["dd", "if=/dev/urandom", "of=2.dat", "bs=4096", "count={}".format(count)])
            result = []
            for size in [2**x for x in xrange(3,17)]:
                r = timeit.repeat("d = delta.delta('1.dat', b, {})".format(size),
                                  setup="from MiGBox.sync import delta; b = delta.blockchecksums('2.dat', {})".format(size),
                                  number=1, repeat=5)
                result.append(min(r))
            c = timeit.repeat("subprocess.call(['bsdiff', '2.dat', '1.dat', '2.dat.patched'])", setup="import subprocess", number=1, repeat=5)
            f.write("#filesize {}\n".format(count*4096))
            f.write("y{} <- c({})\n".format(count, ", ".join([str(x) for x in result])))
            f.write("bsdiff{} <- c({})\n".format(count, str(min(c))))

def delta_stepsize():
    with open("stepsize", "w") as f:
        for count in [10**x for x in xrange(3,4)]:
            subprocess.call(["dd", "if=/dev/urandom", "of=1.dat", "bs=4096", "count={}".format(count)])
            subprocess.call(["dd", "if=/dev/urandom", "of=2.dat", "bs=4096", "count={}".format(count)])
            for size in [2**x for x in xrange(6,7)]:
                result = []
                for step in xrange(1, 51):
                    r = timeit.repeat("d = delta.delta('1.dat', b, {}, {})".format(size, step),
                                      setup="from MiGBox.sync import delta; b = delta.blockchecksums('2.dat', {})".format(size),
                                      number=1, repeat=5)
                    result.append(min(r))
                f.write("#filesize {}\n".format(count*4096))
                f.write("y <- c({})\n".format(", ".join([str(x) for x in result])))

def delta_size():
    with open("deltasize", "w") as f:
        matches = []
        misses = []
        sizes = []
        for step in xrange(1,51):
            count_mat = 0
            count_mis = 0
            size = 0
            subprocess.call(["dd", "if=/dev/urandom", "of=1.dat", "bs=4096", "count=100"])
            subprocess.call(["dd", "if=/dev/urandom", "of=2.dat", "bs=4096", "count=100"]) 
            b = delta.blockchecksums("2.dat", 64)#"linux-1.1.94.tar.gz", 64)
            d = delta.delta("1.dat", b, 64, step)#"linux-1.1.95.tar.gz", b, 64, step)
            for offset, data in d:
                if data:
                    count_mis += 1
                    size += len(data)
                else:
                    count_mat += 1
            matches.append(count_mat)
            misses.append(count_mis)
            sizes.append(size)
        f.write("mat <- c({})\n".format(", ".join([str(x) for x in matches])))
        f.write("mis <- c({})\n".format(", ".join([str(x) for x in misses])))
        f.write("size <- c({})\n".format(", ".join([str(x) for x in sizes])))
            
def delta_random():
    with open("deltarand", "w") as f:
        matches = [] 
        misses = []
        sizes = []
        for x in xrange(0,101):
            count_mat = 0
            count_mis = 0
            size = 0
            count = 100
            subprocess.call(["dd", "if=/dev/urandom", "of=1.dat", "bs=4096", "count={}".format(count)])
            subprocess.call(["dd", "if=/dev/urandom", "of=2.dat", "bs=4096", "count={}".format(count)])
            b = delta.blockchecksums("2.dat", 8)
            d = delta.delta("1.dat", b, 8)
            for offset, data in d:
                if data:
                    count_mis += 1
                    size += len(data)
                else:
                    count_mat += 1
            matches.append(count_mat)
            misses.append(count_mis)
            sizes.append(size)
        f.write("mat <- c({})\n".format(", ".join([str(x) for x in matches])))
        f.write("mis <- c({})\n".format(", ".join([str(x) for x in misses])))
        f.write("size <- c({})\n".format(", ".join([str(x) for x in sizes])))

def delta_time():
     with open("deltatime", "w") as f:
        mins = []
        for count in xrange(1,101):
            subprocess.call(["dd", "if=/dev/urandom", "of=1.dat", "bs=4096", "count={}".format(count)])
            subprocess.call(["dd", "if=/dev/urandom", "of=2.dat", "bs=4096", "count={}".format(count)])
            result = []
            for size in [2**x for x in xrange(4,7)]:
                r = timeit.repeat("d = delta.delta('1.dat', b, {})".format(size),
                                  setup="from MiGBox.sync import delta; b = delta.blockchecksums('2.dat', {})".format(size),
                                  number=1, repeat=5)
                result.append(min(r))
            f.write("#filesize {}\n".format(count*4096))
            f.write("y{} <- c({})\n".format(count, ", ".join([str(x) for x in result])))
            mins.append(min(result))
        f.write("mins <- c({})\n".format(", ".join([str(x) for x in mins])))
    
def delta_opt():
    with open("deltaopt", "w") as f:
        r = timeit.repeat("d = delta.delta('linux-1.1.95.tar.gz', b, 64)",
                          setup="from MiGBox.sync import delta; b = delta.blockchecksums('linux-1.1.94.tar.gz', 64)",
                          number=1, repeat=5)
        o = timeit.repeat("d = delta.delta('linux-1.1.95.tar.gz', b, 64, 17)",
                          setup="from MiGBox.sync import delta; b = delta.blockchecksums('linux-1.1.94.tar.gz', 64)",
                          number=1, repeat=5)
        c = timeit.repeat("subprocess.call(['bsdiff', 'linux-1.1.94.tar.gz', 'linux-1.1.95.tar.gz', 'patch'])", setup="import subprocess", number=1, repeat=5)

        f.write("delta <- c({})\n".format(", ".join([str(x) for x in r])))
        f.write("delta_opt <- c({})\n".format(", ".join([str(x) for x in o])))
        f.write("bsdiff <- c({})\n".format(", ".join([str(x) for x in c])))

def block_time():
    with open("blocktime", "w") as f:
        for count in [1, 2, 4, 6, 8, 10, 20, 40, 60, 80, 100, 200, 400, 600, 800, 1000, 2000, 4000, 6000, 8000, 10000]:
            subprocess.call(["dd", "if=/dev/urandom", "of=1.dat", "bs=4096", "count={}".format(count)])
            r = timeit.repeat("b = delta.blockchecksums('1.dat', 64)",
                              setup="from MiGBox.sync import delta",
                              number=1, repeat=5)
            f.write("block{} <- c({})\n".format(count, ", ".join([str(x) for x in r])))
 
if __name__ == "__main__":
#    delta_blocksize()
#    delta_stepsize()
#    delta_size()
#    delta_random()
#    delta_time()
#    delta_opt()
    block_time()
