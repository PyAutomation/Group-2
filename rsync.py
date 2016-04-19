#!/usr/bin/python

import paramiko
import os
import os.path
import subprocess
import shlex
import re
import logging
import argparse
import sys

class Logger(object):
    def __init__(self, level):
        self.logger = logging.getLogger(__name__)
        if not len(self.logger.handlers):
            self.logger.setLevel(level)
            self.fh = logging.FileHandler('trace.log')
            self.fh.setLevel(level)
            self.ch = logging.StreamHandler()
            self.ch.setLevel(level)
            self.formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            self.fh.setFormatter(self.formatter)
            self.ch.setFormatter(self.formatter)
            self.logger.addHandler(self.fh)
            self.logger.addHandler(self.ch)

log = Logger(logging.INFO)

def rsync(sftp, ssh, localPath, remoteDir):
    """The rsync function"""

    if os.path.isfile(localPath):
        sync_file(sftp, ssh, localPath, remoteDir)
    elif os.path.isdir(localPath):
        sync_dir(sftp, ssh, localPath, remoteDir)
    elif os.path.islink(localPath):
        pass


def sync_dir(sftp, ssh, localPath, remoteDir):
    """Syncronizes two directories"""

    for filename in os.listdir(localPath):
        file = os.path.join(localPath, filename)
        if os.path.isfile(file):
            sync_file(sftp, ssh, file, remoteDir)
        elif os.path.isdir(file):
            try:
                sftp.stat(os.path.join(remoteDir, filename))
                rsync(sftp, ssh, file, os.path.join(remoteDir, filename))
            except:
                copy_dir(sftp, file, remoteDir, 'r')


def sync_file(sftp, ssh, localPath, remoteDir):
    """Syncronizes file available locally at localPath and
        file with the same name available in remote remoteDir derectory"""

    if not check(sftp, ssh, localPath, remoteDir):
        copy_file(sftp, localPath, remoteDir)


def check(sftp, ssh, localPath, remoteDir):
    """Compares hashes of localPath file and file with the same
        name in remote remoteDir directory"""

    file = os.path.basename(localPath)
    if file in sftp.listdir(remoteDir):
        stdin, stdout, stderr = ssh.exec_command("md5sum " + os.path.join(remoteDir, file))
        remote_hash = stdout.read().split()[0]
        local_hash = get_hash(localPath)
        return local_hash == remote_hash
    else:
        return False
 

def copy_file(sftp, source, dest):
    """Copies local file *source* to remote *dest* folder"""

    file = os.path.basename(source)
    log.logger.info('Copying %s to %s', source, dest)
    sftp.put(source, os.path.join(dest, file))


def copy_dir(sftp, source, dest, *options):
    """Copies directory *source* to remote *dest* directory
        It *r* option is provided, performs recursive copy
        Otherwise, creates an empty directory with the same name as *source*"""

    dir = os.path.basename(source)
    if 'r' in options:
        log.logger.info('Creating directory %s', os.path.join(dest, dir))
        sftp.mkdir(os.path.join(dest, dir))
        for filename in os.listdir(source):
            file = os.path.join(source, filename)
            if os.path.isfile(file):
                copy_file(sftp, file, os.path.join(dest, dir))
            elif os.path.isdir(file):
                copy_dir(sftp, file, os.path.join(dest, dir), 'r')
    else:
        log.logger.info('Creating directory %s', os.path.join(dest, dir))
        sftp.mkdir(os.path.join(dest, dir))


def get_hash(path):
    """Gets hash of local *path* file"""

    cmd = shlex.split("md5sum " + path)
    ps = subprocess.Popen(cmd, shell=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return ps.stdout.read().split()[0]


def check_connection(host):
    """Checks whether the server connection details follow the user:port@host:directory pattern"""

    pattern = '([\w.]+)(:|,)([0-9]+)@([\w.]+):(/[\w./]+)'
    connection = {}
    match = re.search(pattern, host)
    if match:
        connection['username'] = match.group(1)
        connection['port'] = int(match.group(3))
        connection['host'] = match.group(4)
        connection['directory'] = match.group(5)
    return connection


def parser():
    "Parses command-line"
    parser = argparse.ArgumentParser(description='Parser')
    parser.add_argument('-P', action='store_true', help='equivalent to --partial --progress')
    parser.add_argument('-S', action='store_true', help='Handle sparse files efficiently')
    parser.add_argument('-a', action='store_true', help='Archive mode')
    parser.add_argument('-e', action='store', help='Specify the remote shell to use')
    parser.add_argument('-q', action='store_true', help='Decrease verbosity')
    parser.add_argument('-v', action='store_true', help='Increase verbosity')
    parser.add_argument('-z', action='store_true', help='Compress file data during the transfer')
    parser.add_argument('-pass', action='store', dest='passwd', help='Increase verbosity')
    parser.add_argument('-progress', action='store_true', help='Increase verbosity')
    parser.add_argument('source')
    parser.add_argument('dest')
    args = parser.parse_args()
    d = {}
    d["passwd"] = args.passwd
    d["source"] = args.source
    d["dest"] = args.dest
    return d


def main(hostname, port, username, password, source, dest):
    """Some trash to test existing routines"""
    
    t = paramiko.Transport((hostname, port))
    log.logger.info('Establishing sFTP connection with %s...', hostname)
    t.connect(username=username, password=password)
    log.logger.info('sFTP Connection with %s established', hostname)
    sftp = paramiko.SFTPClient.from_transport(t)

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    log.logger.info('Establishing SSH connection with %s', hostname)
    ssh.connect('ubuntu-server', username=username, password=password)
    log.logger.info('SSH connection with %s established', hostname)
    
    rsync(sftp, ssh, source, dest)   


if __name__ == "__main__":    
    cmd_args = parser()
    connection = check_connection(cmd_args["dest"])
    if not connection:
        log.logger.error('Wrong connection details. Exiting the program...')
        sys.exit(1)
    else:
        hostname = connection['host']
        port = connection['port']
        username = connection['username']
        dest = connection['directory']
    source = os.path.expanduser(cmd_args["source"])
    if not os.path.exists(source):
        log.logger.error("Source file or directory %s does not exist. Exiting the program...", source)
        sys.exit(1)
    dest = os.path.expanduser(dest)
    if not os.path.exists(dest):
        log.logger.error("Destination directory %s does not exist. Exiting the program...", dest)
        sys.exit(1)
    if not cmd_args["passwd"]:
        log.logger.error("No password provided. Exiting the program...")
        sys.exit(1)
    else:
        password = cmd_args["passwd"]

    main(hostname, port, username, password, source, dest)
