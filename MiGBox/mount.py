# Mount module to mount remote SFTP locations to the local file system. 
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
This module provides methods to mount a SFTP location to the local file system.

Uses 'sshfs' on Unix systems.

MacOS X and Windows not yet supported.
"""

import os
import sys

from subprocess import call

def mount(host, port, userkey, mountpath):
    """
    Mount the given sftp location to C{mountpath}.

    Try to use an OS appropriate external program like 'sshfs'.

    @param host: sftp host name/ip.
    @type host: str
    @param port: sftp port.
    @type port: int
    @param userkey: path to the user's private key for authentication.
    @type userkey: str
    @param mountpath: path to mount the local location, create if not exists.
    @type mountpath: str
    @return: mountpath on success, else None.
    @rtype: str
    """

    host = host if host != '' else 'localhost'

    if not os.path.exists(mountpath):
        os.mkdir(mountpath)

    config_str = "Host sshfsserver\n    HostName {0}\n    Port {1}\n    IdentityFile {2}".format(
        host, port, userkey)

    with open('.sshfs_config', 'w') as f:
        f.write(config_str)

    sshfs_config = os.path.abspath('.sshfs_config')

    if sys.platform.startswith('linux'):
        try:
            call(['sshfs', '-F', sshfs_config, 'sshfsserver:', mountpath])
            return mountpath
        except Exception as e:
            print e
    return None

def unmount(mountpath):
    """
    Unmount the given sftp location under C{mountpath}.

    @param mountpath: path where the local sftp location is mounted.
    @type mountpath: str
    """

    if sys.platform.startswith('linux'):
        try:
            call(['fusermount', '-u', mountpath])
        except Exception as e:
            print e
