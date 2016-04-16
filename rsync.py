#!/usr/bin/python

import paramiko
import os
import os.path
import subprocess
import shlex
import re


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
    sftp.put(source, os.path.join(dest, file))


def copy_dir(sftp, source, dest, *options):
    """Copies directory *source* to remote *dest* directory
        It *r* option is provided, performs recursive copy
        Otherwise, creates an empty directory with the same name as *source*"""

    dir = os.path.basename(source)
    if 'r' in options:
        sftp.mkdir(os.path.join(dest, dir))
        for filename in os.listdir(source):
            file = os.path.join(source, filename)
            if os.path.isfile(file):
                copy_file(sftp, file, os.path.join(dest, dir))
            elif os.path.isdir(file):
                copy_dir(sftp, file, os.path.join(dest, dir), 'r')
    else:
        sftp.mkdir(os.path.join(dest, dir))


def get_hash(path):
    """Gets hash of local *path* file"""

    cmd = shlex.split("md5sum " + path)
    ps = subprocess.Popen(cmd, shell=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return ps.stdout.read().split()[0]


def check_connection(host):
    """Checks whether the server connection details follow the user:port@host:directory pattern"""

    pattern = '([\w.]+)(:|,)([0-9]+)@([\w.]+):/([\w./]+)'
    connection = {}
    match = re.search(pattern, host)
    if match:
        connection['username'] = match.group(1)
        connection['port'] = int(match.group(3))
        connection['host'] = match.group(4)
        connection['directory'] = match.group(5)
    return connection


def main():
    """Some trash to test routines implemented so far"""
    
    hostname = "ubuntu-server"
    port = 22
    t = paramiko.Transport((hostname, port))
    username = "ed"
    password = "qwerty"
    t.connect(username=username, password=password)
    sftp = paramiko.SFTPClient.from_transport(t)

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect('ubuntu-server', username=username, password=password)
    
    rsync(sftp, ssh, '/home/ed/Python/hw7', '/home/ed/tmp')    


if __name__ == "__main__":    
    #main()
    str = "root:22@host.com:/dir/sde"
    d = check_connection(str)
    if d:
        print d
    else:
        print "Wrong connection details"

