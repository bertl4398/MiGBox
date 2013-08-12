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
Provides a SFTP client to use as an abstract file system.
"""

import os
import socket
import json

import paramiko

from MiGBox.sftp.common import CMD_BLOCKCHK, CMD_DELTA, CMD_PATCH, CMD_OTP

class SFTPClient(paramiko.SFTPClient):
    """
    SFTP client to connect to the MiGBox SFTP server.

    Provides methods for basic SFTP requests and extended MiGBox requests
    to compute file checksums, deltas and apply file patches. All requests
    are forwarded to the C{server} representation aquired from the C{paramiko}
    C{transport}. Therefore, the C{connect} class method can be called with
    authentication information.
    """

    @classmethod
    def connect(cls, host, port, hostkey, userkey, keypass=None, username=None, password=None):
        """
        Create a new SFTP client and connect to C{host}.

        Returns None if creation or connection fails.

        C{username} and C{password} are optional and not needed
        for the authentication, that is by default public key.

        @param host: the host name or ip address.
        @type host: str
        @param port: the host port.
        @type port: int
        @param hostkey: the path to the host's public key.
        @type hostkey: str
        @param userkey: the path to the user's private key.
        @type userkey: str
        @param keypass: password for encrypted key.
        @type keypass: str
        @param username: the user's name (optional).
        @type username: str
        @param password: the user's password (optional).
        @type password: str
        @return: L{SFTPClient} or None.
        @rtype: L{SFTPClient}
        """

        known_host = ''
        # file format "ssh-rsa AAA.... user@somemachine"
        with open(hostkey, 'rb') as f:
            known_host = f.read()
        # get the base64 encoded data of the host's public key
        known_host = known_host.split(' ')[1]

        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((host, int(port)))
        transport = paramiko.Transport(client_socket)
        transport.start_client()
        
        key_data = transport.get_remote_server_key().get_base64()
        if not known_host == key_data: 
            raise paramiko.BadHostKeyException(host, key_data, known_host)

        try:
            transport.auth_publickey(username, paramiko.RSAKey.from_private_key_file(userkey, keypass))
        except Exception:
            transport.auth_password(username, password)

        chan = transport.open_session()
        if chan is None:
            return None
        chan.invoke_subsystem('sftp')
        return cls(chan)

    def checksums(self, path):
        """
        Send a request to the server to compute block checksums of
        a given file.

        @param path: path to the file.
        @type path: str
        @return: block checksums of the file as a hashtable.
        @rtype: dict
        """

        path = self._adjust_cwd(path)
        t, msg = self._request(CMD_BLOCKCHK, path)
        j = msg.get_string()
        bs = json.loads(j)
        return bs

    def delta(self, path, checksums):
        """
        Send a request to the server to compute a delta for a
        given file, according to the block checksums.

        @param path: path to the file.
        @type path: str
        @param checksums: block checksums of old/other file.
        @type checksums: dict
        @return: delta of the given file to be applied with L{patch}.
        @rtype: list
        """

        path = self._adjust_cwd(path)
        t, msg = self._request(CMD_DELTA, path, json.dumps(checksums))
        j = msg.get_string()
        d = json.loads(j)
        return d

    def patch(self, path, delta):
        """
        Send a request to the server to patch a given file,
        according to the delta of the file to an old/other file.

        @param path: path to the file.
        @type path: str 
        @param delta: delta to an old/other file.
        @type delta: list
        """

        path = self._adjust_cwd(path)
        self._request(CMD_PATCH, path, json.dumps(delta))

    def onetimepass(self):
        """
        Request a one time password stored in a new file in the
        directory the user uses for synchronization.

        This credentials can be used to log in one time only and
        are supposed to enable sharing and collaboration with
        other users.
        """

        self._request(CMD_OTP)
