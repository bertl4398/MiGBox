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

import io

from ConfigParser import SafeConfigParser

about ="""
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

# default migbox.cfg configuration file
default_migbox = """
[Sync]
source =
destination =
[Connection]
sftp_host =
sftp_port =
[Logging]
logfile =
loglevel =
[KeyAuth]
userkey =
hostkey =
[Mount]
mountpath =
"""

# default server.cfg configuration file
default_server = """
[ROOT]
rootpath =
[Connection]
host =
port =
backlog =
[Logging]
logfile =
loglevel =
[KeyAuth]
hostkey =
userkey =
"""

def write_config(configfile, values, server=False):
    """
    Write the given values to the given configfile.

    Values are expected to be in the form of

    C{{'section': {'option': value}}}

    Writes always the default structure.

    @param configfile: path to the config file.
    @type configfile: str
    @param values: configuration values.
    @type values: dict
    """

    config = SafeConfigParser()
    if server:
        config.readfp(io.BytesIO(default_server))
    else:
        config.readfp(io.BytesIO(default_migbox))
    config.read(configfile)
    for section, options in values.items():
        for option, value in options.items():
            config.set(section, option, value)
    with open(configfile, 'wb') as f:
        config.write(f)

def read_config(configfile, server=False):
    """
    Read the given configfile and return a dictionary
    with all sections, options and values in the form of

    C{{'section': {'option': value}}}

    A default configuration file is read first to
    set the right structure.

    @param configfile: path to the config file.
    @type configfile: str
    @return: dictionary of all values.
    @rtype: dict
    """

    values = {}
    config = SafeConfigParser()
    if server:
        config.readfp(io.BytesIO(default_server))
    else:
        config.readfp(io.BytesIO(default_migbox))
    config.read(configfile)
    for section in config.sections():
        values[section] = {}
        for option, value in config.items(section):
            values[section][option] = value
    return values

def print_vars(vars_):
    """
    Print the given variables in the form of
    C{{'section': {'option': value}}}. 

    @param vars_: dictionary of dictionaries.
    @type vars_: dict
    """

    for section, options in vars_.items():
        print section
        for option, value in options.items():
            print "    {0}: {1}".format(option,value)

def get_vars(vars_):
    """
    Return the given variables in the from of
    C{{'section': {'option': value}}} as a dictionary
    of C{{'option': value}}.

    @param vars_: dictionary of dictionaries.
    @type vars_: dict
    @return: dictionary of named values.
    @rtype: dict
    """

    var_dict = {}
    for section, options in vars_.items():
        for option, value in options.items():
            var_dict[option] = value
    return var_dict
