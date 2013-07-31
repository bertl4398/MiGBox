# MiGBox - Command line interface
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
MiGBox command line interface.
"""

__version__ = 0.2
__author__ = 'Benjamin Ertl'

import threading

from MiGBox.sync import syncd
from MiGBox.mount import mount, unmount

header = """
Command line interface for MiGBox - version {0}
Copyright (c) 2013 {1}

MiGBox comes with ABSOLUTELY NO WARRANTY. This is free software,
and you are welcome to redistribute it under certain conditions.

type 'start'   to start synchronizing
type 'stop'    to stop synchronizing
type 'mount'   to mount the configured sftp location
type 'unmount' to unmount the configured sftp location
type 'exit'    to exit
""".format(__version__, __author__)

def run(mode, source, destination, sftp_host, sftp_port,
        hostkey, userkey, mountpath, logfile=None, loglevel='INFO'):

    event = threading.Event()    
    thread = threading.Thread(target=syncd.run, args=(mode, source, destination,
                 sftp_host, sftp_port, hostkey, userkey, logfile, loglevel, event))

    print header
    running = True

    while running:
        in_ = raw_input("> ")
        if in_ == 'start':
            event.clear()
            thread.start()
        if in_ == 'stop':
            event.set()
            thread.join()
        if in_ == 'mount':
            p = mount(sftp_host, sftp_port, userkey, mountpath)
            if not p:
                print "SFTP mount not supported."
        if in_ == 'unmount':
            unmount(mountpath)
        if in_ == 'exit':
            event.set()
            running = False

    if thread.isAlive():
        thread.join()
