#! /usr/bin/env python
# encoding: utf-8
#
# Copyright (C) 2011 Serge Monkewitz
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# Authors:
#     - Serge Monkewitz, IPAC/Caltech
#
# Work on this project has been sponsored by LSST and SLAC/DOE.
#

from __future__ import with_statement
import getpass
import operator
import os
import stat

from waflib import Configure, Logs, Task, TaskGen

__ver = {
    'atleast_version': operator.ge,
    'exact_version': operator.eq,
    'max_version': operator.le,
}

def __parse_version(version):
    return tuple(map(int, version.split('.')))


def options(ctx):
    ctx.add_option('--mysql-dir', type='string', dest='mysql_dir',
                   help='''Path to the mysql install directory.
                           Defaults to ${PREFIX}.''')
    ctx.add_option('--mysql-config', type='string', dest='mysql_config',
                   help='''Path to the mysql_config script (e.g. /usr/local/bin/mysql_config).
                           Used to obtain the location of MySQL header files and plugins.''')
    ctx.add_option('--mysql-includes', type='string', dest='mysql_includes',
                   help='''Path to the directory where the MySQL header files are located.
                           Defaults to ${mysql-dir}/include/mysql; ignored if --mysql-config is used.''')

@Configure.conf
def check_mysql(self, **kw):
    self.start_msg('Checking for mysql install')
    mysql_dir = self.options.mysql_dir
    if mysql_dir:
        if not os.path.isdir(mysql_dir) or not os.access(mysql_dir, os.X_OK):
            self.fatal('--mysql-dir does not identify an accessible directory')
        self.end_msg(mysql_dir)
        self.env.MYSQL_DIR = mysql_dir
    else:
        self.env.MYSQL_DIR = self.env.PREFIX

    # Check for the MySQL config script
    config = self.options.mysql_config
    if config:
        if not os.path.isfile(config) or not os.access(config, os.X_OK):
            self.fatal('--mysql-config does not identify an executable')
        includes = self.cmd_and_log([config, '--include'])
    else:
        includes = self.options.mysql_includes or os.path.join(self.env.MYSQL_DIR, 'include', 'mysql')

    # Get include directory
    self.start_msg('Checking for mysql include directory')
    if not includes or not os.path.isdir(includes):
        self.fatal('Invalid/missing mysql header directory')
    else:
        self.end_msg(includes)
    self.env.INCLUDES_MYSQL = [includes]

    # Get the server version
    version = self.check_cc(fragment='''#include "mysql.h"
                                        int main() {
                                            printf(MYSQL_SERVER_VERSION);
                                            return 0;
                                        }''',
                            execute=True,
                            define_ret=True,
                            use='MYSQL',
                            msg='Checking for mysql.h')
    if any(vc in kw for vc in __ver.keys()):
        # Make sure version constraints are satsified
        self.start_msg('Checking MySQL version')
        try:
            mv = __parse_version(version)
        except:
            self.fatal('Invalid MYSQL_SERVER_VERSION %s' % version)
        for constraint in __ver.keys():
            if constraint in kw:
                try:
                    dv = __parse_version(kw[constraint])
                except:
                    self.fatal('Invalid %s value %s' % (constraint, kw[constraint]))
                if not __ver[constraint](mv, dv):
                    self.fatal('MySQL server version %s violates %s=%s' % (version, constraint, kw[constraint]))
        self.end_msg(version)

