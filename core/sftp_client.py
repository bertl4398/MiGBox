# SFTP client module based on paramiko
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
SFTP client module based on paramiko.
Provides a SFTP client to use with the abstract file system access, see
L{filesystem}
"""

__version__ = 0.1
__author__ = 'Benjamin Ertl'

import socket
import paramiko

class SFTPClient(object):
    def __init__(self, host, port):
        self.host = host
        self.port = port

    def connect(self, username, password):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((self.host,self.port))
        self.transport = paramiko.Transport(self.socket)
        self.transport.connect(username=username, password=password)
        return paramiko.SFTP.from_transport(self.transport)

    def disconnect(self):
        self.socket.close()
        self.transport.close()
