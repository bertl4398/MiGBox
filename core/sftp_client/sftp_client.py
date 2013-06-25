# SFTP Client based on paramiko
#
# Copyright (C) 2013 Benjamin Ertl

"""
SFTP Client module based on paramiko.
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
