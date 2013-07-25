# MiGBox common module
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
MiGBox common module.
Provides common functions and constants for all MiGBox modules.
"""

import os

# get MiGBox path
if "MIGBOXPATH" in os.environ:
    # the MIGBOXPATH environment variable
    # should point to the MiGBox main directory.
    migbox_path = os.environ["MIGBOXPATH"]
else:
    # if environment variable not set assume
    # parent dir as valid path to config/, log/, etc.
    migbox_path = os.path.abspath(os.pardir)

config_path = os.path.join(migbox_path, "config")
icons_path = os.path.join(migbox_path, "icons")
log_path = os.path.join(migbox_path, "log")
keys_path = os.path.join(migbox_path, "keys")

# string to show short version of the license in gui, cli and server
ABOUT ="""
MiGBox - File Synchronization for the Minimum Intrusion Grid (MiG)

Copyright (c) 2013 Benjamin Ertl

This program is free software; you can redistribute it and/or
modify it under the terms of the GNU General Public License
as published by the Free Software Foundation; either version
2 of the License, or (at your option) any later version.

This program is distributed in the hope that it will be
useful, but WITHOUT ANY WARRANTY; without even the
implied warranty of MERCHANTABILITY or FITNESS FOR A
PARTICULAR PURPOSE. See the GNU General Public License
for more details.

You should have received a copy of the GNU General Public
License along with this program; if not, write to the Free
Software Foundation, Inc., 51 Franklin Street, Fifth Floor,
Boston, MA 02110-1301 USA.
"""


