# SFTP server interface based on paramiko
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
SFTP server interface implementation based on paramiko.
Provides a SFTP server interface for the MiG SFTP server.
"""

import os
import base64

import paramiko

from Crypto import Random
from Crypto.Hash import MD5

class SFTPHandle(paramiko.SFTPHandle):
    """
    This class inherits from L{paramiko.SFTPHandle}.

    It provides an abstract object representing a handle to an open file/directory.
    """

    def stat(self):
        """
        Return an L{paramiko.SFTPAttributes} object for this open file.

        @return: an attribute object for the given file.
        @rtype: L{paramiko.SFTPAttributes}
        """

        try:
            return paramiko.SFTPAttributes.from_stat(os.fstat(self.readfile.fileno()))
        except OSError as e:
            return paramiko.SFTPServer.convert_errno(e.errno)

    def chattr(self, attr):
        """
        Change the attributes of this file.

        @param attr: attributes to change.
        @type attr: L{paramiko.SFTPAttributes}
        @return: return code
        @rtype: int
        """

        try:            
            paramiko.SFTPServer.set_file_attr(self.filename, attr)
            return paramiko.SFTP_OK
        except OSError as e:
            return paramiko.SFTPServer.convert_errno(e.errno)

class SFTPServerInterface(paramiko.SFTPServerInterface):
    """
    This class inherits from L{paramiko.SFTPServerInterface}.

    It defines an interface for the SFTP server.
    """

    def __init__(self, server, *largs, **kwargs):
        """
        Create a new SFTP server interface that handles SFTP operations.

        @param server: SFTP server associated with this interface.
        @type server: ServerInterface
        @param root: local root path for SFTP operations on this interface.
        @type root: str
        """
        super(paramiko.SFTPServerInterface, self).__init__(*largs, **kwargs)
        self.root = os.path.normpath(server.root)
        self.salt = server.salt

    def session_started(self):
        """
        The SFTP server session has just started.  This method is meant to be
        overridden to perform any necessary setup before handling callbacks
        from SFTP operations.
        """
        # TODO implement necessary setup?
        pass

    def session_ended(self):
        """
        The SFTP server session has just ended, either cleanly or via an
        exception.  This method is meant to be overridden to perform any
        necessary cleanup before this C{paramiko.SFTPServerInterface} object is
        destroyed.
        """
        # TODO implement clean up?
        pass

    def _get_path(self, path):
        return self.root + self.canonicalize(path)

    def open(self, path, flags, attr):
        """
        Open a file on the server and create a handle for future operations
        on that file.

        @param path: path of the file to be opened.
        @type path: str
        @param flags: flags or'd together from the C{os} module.
        @type flags: int
        @param attr: requested attributes of the file if it is newly created.
        @type attr: L{paramiko.SFTPAttributes}
        @return: a new L{paramiko.SFTPHandle} I{or error code}.
        @rtype L{paramiko.SFTPHandle}
        """

        path = self._get_path(path)
        try:
            binary_flag = getattr(os, 'O_BINARY',  0)
            flags |= binary_flag
            mode = getattr(attr, 'st_mode', None)
            if mode is not None:
                fd = os.open(path, flags, mode)
            else:
                fd = os.open(path, flags, 0666)
        except OSError, e:
            return paramiko.SFTPServer.convert_errno(e.errno)
        if (flags & os.O_CREAT) and (attr is not None):
            attr._flags &= ~attr.FLAG_PERMISSIONS
            paramiko.SFTPServer.set_file_attr(path, attr)
        if flags & os.O_WRONLY:
            if flags & os.O_APPEND:
                fstr = 'ab'
            else:
                fstr = 'wb'
        elif flags & os.O_RDWR:
            if flags & os.O_APPEND:
                fstr = 'a+b'
            else:
                fstr = 'r+b'
        else:
            fstr = 'rb'
        try:
            f = os.fdopen(fd, fstr)
        except OSError, e:
            return paramiko.SFTPServer.convert_errno(e.errno)
        fobj = SFTPHandle(flags)
        fobj.filename = path
        fobj.readfile = f
        fobj.writefile = f
        return fobj

    def list_folder(self, path):
        """
        Return a list of files within a given folder.

        @param path: path to be listed.
        @type path: str
        @return: a list of the files in the given folder, using
            L{paramiko.SFTPAttributes} objects.
        @rtype: list of L{paramiko.SFTPAttributes} I{or error code}
        """

        path = self._get_path(path)
        attr_list = []
        try:
            files = os.listdir(path)
            for file_ in files:
                stat = os.stat(os.path.join(path, file_))
                attr = paramiko.SFTPAttributes.from_stat(stat)
                attr.filename = file_
                attr_list.append(attr)
            return attr_list
        except OSError as e:
            return paramiko.SFTPServer.convert_errno(e.errno)

    def stat(self, path):
        """
        Return an L{paramiko.SFTPAttributes} object for a path on the server,
        or an error code.

        @param path: path for stat infos.
        @type path: str
        @return: an attributes object for the given path, or error code.
        @rtype: L{paramiko.SFTPAttributes} I{or error code}
        """

        path = self._get_path(path)
        try:
            return paramiko.SFTPAttributes.from_stat(os.stat(path))
        except OSError as e:
            return paramiko.SFTPServer.convert_errno(e.errno)

    def lstat(self, path):
        """
        Return an L{paramiko.SFTPAttributes} object for a path on the server,
        or an error code.

        @param path: path for stat infos.
        @type path: str
        @return: an attributes object for the given file, or an error code.
        @rtype: L{SFTPAttributes} I{or error code}
        """

        path = self._get_path(path)
        try:
            return paramiko.SFTPAttributes.from_stat(os.lstat(path))
        except OSError as e:
            return paramiko.SFTPServer.convert_errno(e.errno)

    def remove(self, path):
        """
        Delete a file, if possible.

        @param path: path the file to delete.
        @type path: str
        @return: return code.
        @rtype: int
        """

        path = self._get_path(path)
        try:
            os.remove(path)
            return paramiko.SFTP_OK
        except OSError as e:
            return paramiko.SFTPServer.convert_errno(e.errno)

    def rename(self, oldpath, newpath):
        """
        Rename (or move) a file.

        @param oldpath: path of the existing file.
        @type oldpath: str
        @param newpath: new path of the file.
        @type newpath: str
        @return: return code.
        @rtype: int
        """

        oldpath = self._get_path(oldpath)
        newpath = self._get_path(newpath)
        try:
            os.rename(oldpath, newpath)
            return paramiko.SFTP_OK
        except OSError as e:
            return paramiko.SFTPServer.convert_errno(e.errno)

    def mkdir(self, path, attr):
        """
        Create a new directory with the given attributes.

        @param path: path to the new directory.
        @type path: str
        @param attr: requested attributes of the new folder.
        @type attr: L{paramiko.SFTPAttributes}
        @return: return code
        @rtype: int
        """

        path = self._get_path(path)
        try:
            os.mkdir(path)
            if attr:
                paramiko.SFTPServer.set_file_attr(path, attr)
            return paramiko.SFTP_OK
        except OSError as e:
            return paramiko.SFTPServer.convert_errno(e.errno)

    def rmdir(self, path):
        """
        Remove an empty directory if it exists.

        @param path: path to the directory to remove.
        @type path: str
        @return: return code.
        @rtype: int
        """

        path = self._get_path(path)
        try:
            os.rmdir(path)
            return paramiko.SFTP_OK
        except OSError as e:
            return paramiko.SFTPServer.convert_errno(e.errno)

    def chattr(self, path, attr):
        """
        Change the attributes of a file.

        @param path: path of the file to change.
        @type path: str
        @param attr: attributes to change on the file.
        @type attr: L{paramiko.SFTPAttributes}
        @return: return code.
        @rtype: int
        """

        path = self._get_path(path)
        try:
            paramiko.SFTPServer.set_file_attr(path, attr)
            return paramiko.SFTP_OK
        except OSError as e:
            return paramiko.SFTPServer.convert_errno(e.errno)

    def readlink(self, path):
        """
        Return the target of a symbolic link (or shortcut) on the server.
        
        @param path: path of the symbolic link.
        @type path: str
        @return: the target path of the symbolic link, or an error code.
        @rtype: str I{or error code}
        """

        path = self._get_path(path)
        try:
            symlink = os.readlink(path)
            if os.path.isabs(symlink):
                head, tail = os.path.split(symlink)
                head = head.replace(self.root + os.path.sep, '')
                symlink = os.path.join(head, tail)
            return symlink                
        except OSError as e:
            return paramiko.SFTPServer.convert_errno(e.errno)
    
    def symlink(self, target_path, path):
        """
        Create a symbolic link on the server, as new pathname C{path},
        with C{target_path} as the target of the link.
        
        @param target_path: path of the target for this new symbolic link.
        @type target_path: str
        @param path: path of the symbolic link to create.
        @type path: str
        @return: return code.
        @rtype: int
        """

        path = self._get_path(path)
        target_path = self._get_path(target_path)
        try:
            os.symlink(target_path, path)
            return paramiko.SFTP_OK
        except OSError as e:
            return paramiko.SFTPServer.convert_errno(e.errno)

    def onetimepass(self):
        """
        Create a one time password stored in a new file on the
        root path the user uses for synchronization.

        This credentials can be used to log in one time only and
        are supposed to enable sharing and collaboration with
        other users.
        """

        rnd = Random.OSRNG.new().read(1024)
        pas = base64.b64encode(rnd)
        usr = MD5.new(self.salt)
        usr.update(pas)
        path = self._get_path(usr.hexdigest())
        try:
            fd = os.open(path, os.O_CREAT|os.O_WRONLY, 0644)
            os.write(fd, pas)
            return paramiko.SFTP_OK
        except OSError as e:
            return paramiko.SFTPServer.convert_errno(e.errno)

