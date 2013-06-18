#!/usr/bin/python

import sys, time
import shelve

import rsync

from fs.osfs import OSFS
from fs.sftpfs import SFTPFS
from fs.mountfs import MountFS

from fs.watch import *
from fs.errors import *


local_fs = OSFS('../tests/local')
remote_fs = OSFS('../tests/remote')
combined_fs = MountFS()
combined_fs.mountdir('local', local_fs)
combined_fs.mountdir('remote', remote_fs)

local_file_dict = shelve.open('../tests/local/.fd')

try:
    combined_fs.copy('/remote/.fd', '/local/.rfd', overwrite=True)
except ResourceNotFoundError:
    pass

remote_file_dict = shelve.open('../tests/local/.rfd')

for file_ in local_fs.walkfiles():
    if file_.find('.fd') == -1 and file_.find('.rfd') == -1:
        if not remote_fs.exists(file_):
            try:
                combined_fs.copy('/local'+file_,'/remote'+file_)
            except ParentDirectoryMissingError:
                combined_fs.makedir('/remote'+file_.rsplit('/',1)[0])
                combined_fs.copy('/local'+file_,'/remote'+file_)
            t = time.time()
            local_file_dict[str(file_)] = {'created':t}
            remote_file_dict[str(file_)] = {'created':t}
            
for dir_ in local_fs.walkdirs():
    if local_fs.isdirempty(dir_):
        combined_fs.makedir('/remote'+dir_)
