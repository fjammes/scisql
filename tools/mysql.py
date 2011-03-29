#! /usr/bin/env python
# encoding: utf-8
import operator
import os, os.path

from waflib import Configure, Logs, Task, TaskGen

__ver = {
    'atleast_version': operator.ge,
    'exact_version': operator.eq,
    'max_version': operator.le,
}

def __parse_version(version):
    return tuple(map(int, version.split('.')))


def options(ctx):
    ctx.add_option('--mysql', type='string', dest='mysql',
                   help='''Path to the mysql command line client (e.g. /usr/local/bin/mysql).
                           Used to CREATE and DROP the scisql UDFs after installation.
                           Defaults to ${PREFIX}/bin/mysql.''')
    ctx.add_option('--mysql-config', type='string', dest='mysql_config',
                   help='''Path to the mysql_config script (e.g. /usr/local/bin/mysql_config).
                           Used to obtain the location of MySQL header files and plugins.''')
    ctx.add_option('--mysql-includes', type='string', dest='mysql_includes',
                   help='''Path to the directory where the MySQL header files are located.
                           Defaults to ${PREFIX}/include/mysql; ignored if --mysql-config is used.''')
    ctx.add_option('--mysql-plugins', type='string', dest='mysql_plugins',
                   help='''Path to the MySQL server plugin directory (UDF installation directory).
                           Defaults to ${PREFIX}/lib/mysql/plugin/; ignored if --mysql-config is used.''')
    ctx.add_option('--mysql-user', type='string', dest='mysql_user', default='root',
                   help='MySQL user name with admin priviledges')
    ctx.add_option('--mysql-socket', type='string', dest='mysql_socket', default='/tmp/mysql.sock',
                   help='UNIX socket file for connecting to MySQL')

@Configure.conf
def check_mysql(self, **kw):
    # Check for the MySQL command line client
    self.start_msg('Checking for mysql command line client')
    mysql = self.options.mysql
    if mysql:
        if not os.path.isfile(mysql) or not os.access(mysql, os.X_OK):
            self.fatal('--mysql does not identify an executable')
        self.end_msg(mysql)
    else:
        mysql = os.path.join(self.env.PREFIX, 'bin', 'mysql')
        if not os.path.isfile(mysql) or not os.access(mysql, os.X_OK):
            self.fatal('${PREFIX}/bin/mysql does not identify an executable')
    self.env.MYSQL = mysql
    self.end_msg(mysql)
    self.env.MYSQL_USER = self.options.mysql_user
    self.env.MYSQL_SOCKET = self.options.mysql_socket

    # Check for the MySQL config script
    config = self.options.mysql_config
    if config:
        if not os.path.isfile(config) or not os.access(config, os.X_OK):
            self.fatal('--mysql-config does not identify an executable')
        includes = self.cmd_and_log([config, '--includes'])
        plugins = self.cmd_and_log([config, '--plugindir'])
    else:
        includes = self.options.mysql_includes or os.path.join(self.env.PREFIX, 'include', 'mysql')
        plugins = self.options.mysql_plugins or os.path.join(self.env.PREFIX, 'lib', 'mysql', 'plugin')

    # Get include directory
    self.start_msg('Checking for mysql include directory')
    if not includes or not os.path.isdir(includes):
        self.fatal('Invalid/missing mysql header directory')
    else:
        self.end_msg(includes)
    self.env.INCLUDES_MYSQL = [includes]

    # Get plugin directory (for UDF installation)
    self.start_msg('Checking for mysql plugins directory')
    if not plugins or not os.path.isdir(plugins):
        self.fatal('Invalid/missing MySQL plugin directory.')
    else:
        self.end_msg(plugins)
    self.env.MYSQL_PLUGIN_DIR = plugins

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


# Task generator for running .mysql script files

@TaskGen.extension('.mysql')
def process_mysql(self, node): 
    self.create_task('MySqlScript', node, []) 

@Task.always_run
class MySqlScript(Task.Task):
    run_str = '${MYSQL} -vvv -S ${MYSQL_SOCKET} -u ${MYSQL_USER} -p < ${SRC}'
    color = 'PINK'
    shell = True
    ext_in = '.mysql'
    reentrant = False
    install_path = False
