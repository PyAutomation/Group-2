import argparse
import re
from logger import log
import sys
import os
import os.path
import paramiko

class Parser(object):
    """Command-line parser"""

    def __init__(self):
        self.parser = argparse.ArgumentParser(description='Parser')
        self.parser.add_argument('-P', action='store_true', help='equivalent to --partial --progress')
        self.parser.add_argument('-S', action='store_true', help='Handle sparse files efficiently')
        self.parser.add_argument('-a', action='store_true', help='Archive mode')
        self.parser.add_argument('-e', action='store', help='Specify the remote shell to use')
        self.parser.add_argument('-q', action='store_true', help='Decrease verbosity')
        self.parser.add_argument('-v', action='store_true', help='Increase verbosity')
        self.parser.add_argument('-z', action='store_true', help='Compress file data during the transfer')
        self.parser.add_argument('-pass', action='store', dest='passwd', help='Increase verbosity')
        self.parser.add_argument('-progress', action='store_true', help='Increase verbosity')
        self.parser.add_argument('paths', nargs="*")
        self.args = self.parser.parse_args()
        self.sources = []
        self.destinations = []
        self.parse_args()


    def parse_args(self):
        """Parses and then verifies sources and destinations"""

        for arg in self.args.paths:
            connection = self.check_connection(arg)
            if connection:
                self.destinations.append(connection)
            else:
                try:
                    source = os.path.expanduser(arg)
                    if os.path.exists(source):
                        self.sources.append(arg)
                    else:
                        log.logger.error("File of directory %s does not exist", source)
                        sys.exit(1)
                except:
                    log.logger.error("Incorrect path %s", arg)
                    sys.exit(1)


    def check_connection(self, host):
        """Checks whether the server connection details follow the user:port@host:directory pattern.
            Then, attempts to establish connection with the remotee host using provided credentials
            and connection settings. Exits with the error code in case of failure."""

        pattern = '([\w.]+)(:|,)([0-9]+)@([\w.]+):(/[\w./]+)'
        match = re.search(pattern, host)

        if not match:
            return

        connection = {}
        connection['username'] = match.group(1)
        connection['port'] = int(match.group(3))
        connection['host'] = match.group(4)
        connection['directory'] = match.group(5)
        connection['passwd'] = self.args.passwd
            
        try:
            t = paramiko.Transport((connection['host'], connection['port']))
            t.connect(username=connection['username'], password=connection['passwd'])
            sftp = paramiko.SFTPClient.from_transport(t)
        except:
            log.logger.error("Couldn't connets host %s:%s using username \'%s\' and password \'%s\'", 
                connection['host'], connection['port'], connection['username'], connection['passwd'])
            sys.exit(1)
        try:
            sftp.stat(connection['directory'])
            sftp.close()
            return connection
        except:
            log.logger.error("Remote directory %s does not exist", connection['directory'])
            sys.exit(1)
