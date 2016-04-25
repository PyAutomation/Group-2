#!/usr/bin/python

import subprocess
import shlex
from parser import Parser
from logger import log
import paramiko
import os
import os.path
import sys

# I do not see rsync utility ever used here, but this is my favourite one :( 

def syncronize(sftp, ssh, localPath, remoteDir):
    """Helper function"""

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
                syncronize(sftp, ssh, file, os.path.join(remoteDir, filename))
            except:
                copy_dir(sftp, file, remoteDir, 'r')


def sync_file(sftp, ssh, localPath, remoteDir):
    """
    Syncronizes file available locally at localPath and
    file with the same name available in remote remoteDir derectory
    """

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


def rsync():
    parser = Parser()

    for source in parser.sources:
        for destination in parser.destinations:
            username = destination['username']
            password = destination['passwd']
            host = destination['host']
            port = destination['port']
            dest = destination['directory']

            t = paramiko.Transport((host, port))
            log.logger.info('Establishing sFTP connection with %s:%s', host, port)
            t.connect(username=username, password=password)
            log.logger.info('sFTP Connection with %s established', host)
            sftp = paramiko.SFTPClient.from_transport(t)

            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            log.logger.info('Establishing SSH connection with %s', host)
            ssh.connect(hostname=host, port=port, username=username, password=password)
            log.logger.info('SSH connection with %s established', host)
            
            syncronize(sftp, ssh, source, dest)
            sftp.close()
            ssh.close()   


if __name__ == "__main__":
    rsync()
