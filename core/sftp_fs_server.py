import logging

from fs.expose.sftp import * 

import paramiko

class SecureServerInterface(BaseServerInterface):
    def check_auth_none(self, username):
        return paramiko.AUTH_FAILED
    def check_auth_password(self, username, password):
        if username == 'test':
            return paramiko.AUTH_SUCCESSFUL
        return paramiko.AUTH_FAILED
    def check_auth_publickey(self, username, key):
        if username == 'test':
            return paramiko.AUTH_SUCCESSFUL
        return paramiko.AUTH_FAILED
    def get_allowed_auths(self, username):
        return "password,publickey"

class SecureSFTPRequestHandler(SFTPRequestHandler):
    def handle(self):
        self.transport.start_server(server=SecureServerInterface())

class SFTPServer(object):
    def __init__(self, filesystem, port):
        self.fs = filesystem
        self.port = port

    def serve_forever(self):
        self.server = BaseSFTPServer(('',self.port), self.fs,
                      RequestHandlerClass=SecureSFTPRequestHandler)
        self.server.serve_forever()

    def server_close(self):
        self.server.server_close()

if __name__ == "__main__":
    from fs.osfs import OSFS
    fs = OSFS('.')
    port = 49152
    server = SFTPServer(fs, port)

    try:
        server.serve_forever()

    except SystemExit, KeyboardInterrupt:
        server.server_close()
