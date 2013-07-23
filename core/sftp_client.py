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

__version__ = 0.2
__author__ = 'Benjamin Ertl'

import socket, json
import paramiko

from ConfigParser import ConfigParser
from delta import *

CMD_BLOCKCHK = 205
CMD_DELTA = 206
CMD_PATCH = 207

class SFTPClient(object):
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.host_key = None

        config = ConfigParser()
        config.read('config.cfg')
        srvkey = config.get('KeyAuth', 'srvkey')
        prvkey = config.get('KeyAuth', 'prvkey')

        # file format "ssh-rsa AAA.... user@somemachine"
        with open(srvkey, 'rb') as f:
            self.known_host = f.read()

        # get the base64 encoded known host public key
        self.known_host = self.known_host.split(' ')[1]

        self.user_key = paramiko.RSAKey.from_private_key_file(prvkey)

    def connect(self, username='', password=None):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((self.host,self.port))
        self.transport = paramiko.Transport(self.socket)
        self.transport.start_client()
        self.host_key = self.transport.get_remote_server_key()
        if not self.known_host == self.host_key.get_base64():
            raise paramiko.BadHostKeyException(self.host, self.host_key, self.known_host)
        self.transport.auth_publickey(username, self.user_key)
        self.server = paramiko.SFTP.from_transport(self.transport)

    def disconnect(self):
        self.socket.close()
        self.transport.close()

    def listdir(self, path):
        return self.server.listdir(path)

    def stat(self, path):
        return self.server.stat(path)

    def mkdir(self, path, mode=511):
        return self.server.mkdir(path, mode)

    def rmdir(self, path):
        return self.server.rmdir(path)

    def remove(self, path):
        return self.server.remove(path)

    def rename(self, src, dst):
        return self.server.rename(src, dst)

    def get(self, src, dst):
        return self.server.get(src, dst)

    def put(self, src, dst):
        return self.server.put(src, dst)

    def open(self, path, mode='rb', buffering=None):
        return self.server.open(path, mode)

    def checksums(self, path):
        path = self.server._adjust_cwd(path)
        t, msg = self.server._request(CMD_BLOCKCHK, path)
        j = msg.get_string()
        bs = json.loads(j)
        return bs

    def delta(self, path, chksums):
        path = self.server._adjust_cwd(path)
        t, msg = self.server._request(CMD_DELTA, path, json.dumps(chksums))
        j = msg.get_string()
        d = json.loads(j)
        return d

    def patch(self, path, delta):
        path = self.server._adjust_cwd(path)
        self.server._request(CMD_PATCH, path, json.dumps(delta))
