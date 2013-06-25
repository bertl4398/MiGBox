#!/usr/bin/python
#
# SFTP server based on paramiko
#
# Copyright (C) 2013 Benjamin Ertl

"""
SFTP server implementation based on paramiko.
"""

__version__ = 0.1
__author__ = 'Benjamin Ertl'

import time, threading, socket

import paramiko

from stub_sftp import StubServer, StubSFTPServer

host = ''
port = 50007

paramiko.common.logging.basicConfig(level=getattr(paramiko.common,'INFO'))

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind((host,port))
s.listen(1)

conn, addr = s.accept()

t= paramiko.Transport(conn)
t.add_server_key(paramiko.RSAKey.from_private_key_file('test_rsa'))

event = threading.Event()
server = StubServer()

t.set_subsystem_handler('sftp', paramiko.SFTPServer, StubSFTPServer)

t.start_server(event, server)

while t.is_active():
    time.sleep(1)

s.close()
t.close()

print 'Done ...'
