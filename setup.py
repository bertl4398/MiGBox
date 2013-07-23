#!/usr/bin/python
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

import sys

description = """
MiGBox - File synchronization for the Minimum Intrusion Grid (MiG)
This package provides an application with gui and cli for file
synchronization to be used with the Minimum Intrusion Grid.

With modifications, this application can als be deployed and used with
any other client/server architecture supporting python.

Required packages:
    paramiko
    watchdog
"""

try:
    from setuptools import setup
    d = { 'install_requires': ['paramiko', 'watchdog'] }
except ImportError:
    from distutils.core import setup
    d = {}

setup(name='MiGBox',
      version='0.1',
      description='MiGBox file synchronization',
      author='Benjamin Ertl',
      author_email='bertl4398@gmail.com',
      license = 'GPL',
      url='https://github.com/bertl4398/MiGBox',
      platforms = 'Posix; MacOS X; Windows',
      package_dir={'MiGBox': ''},
      packages=['MiGBox', 'MiGBox.core'],
      long_description = description,
      **d
     )
