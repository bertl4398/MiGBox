MiGBox
======

File synchronization for the Minimum Intrusion Grid.

Copyright (C) 2013  Benjamin Ertl

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License along
with this program; if not, write to the Free Software Foundation, Inc.,
51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

Getting started
---------------

MiGBox was build with pyinstaller 2.0 for Linux and MacOS X and
cx_Freeze 4.3.1 for Windows, so you dont have to install it as a python
package.

You can just download the packed standalone version for your OS,
unpack it and run migbox(.exe).

If you want to run/install/build it from source, e.g. the standalone version
does not work for you, you need to have the required python libraries installed first.

You can also run MiGBox from the console, see the `--help` option for additional arguments.

  `migbox`         runs the graphical user interface, same as
  `migbox gui`,
  `migbox cli`     runs the command line interface
  `migbox server`  runs the MiGBox SFTP server.

Requirements
------------

  - python 2.7          <http://www.python.org/>
  - pycrypto >= 2.6     <https://www.dlitz.net/software/pycrypto/>
  - paramiko >= 1.11.0  <https://github.com/paramiko/paramiko>
  - watchdog >= 0.6.0   <https://pypi.python.org/pypi/watchdog>

For the graphical user interface

  - PyQt4 >= 4.8.4      <http://pyqt.sourceforge.net/Docs/PyQt4/installation.html>

Installation
------------

If you have all required packages installed, you dont have to install MiGBox as a
python package and can just run following command in the MiGBox directory:

 `python migbox.py`

To actually build and install MiGBox, e.g. with easy_install, run following command
in the MiGBox directory (as root):

  `easy_install .`
