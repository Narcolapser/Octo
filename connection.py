# -*- coding: utf-8 -*-
'''
Module for managing connections to remote servers for Octo.

This module's purpose is to provide a wrapper for Paramiko for Octo to connect through. Originally
Octo worked directly with Paramiko and everything was grand. But then Octo started wanting to have
dozens of connections open. Paramiko, being sensible (and constrained by the remote hosts) wouldn't
allow this. So this module came in like a marriage counselor to tend to the broken relationship.

The Connection class is the sole point of access to the remote host. It monitors how many
connections are currently open and won't open any unless the number is under the threshold amount.

The ConFile class represents a file on the remote server. It does not garuntee however that the
connection to that file is open. Which is the entire point. This class with abstract away opening
and closing the file, and thusly freeing connections, from the logfile class. This makes logfile
a less complicated class and the whole system runs just a little bit smoother. Note: as of
writing, this is not currently how ConFile works, but rather a future aspiration.

Programer: Toben "Narcolapser" Archer
Date: 2016-09-25

'''

import paramiko
import time
import threading
import sys


class Connection():
    def __init__(self,addr,user,password,name,limit=20):
        '''
        Single class for managing connections to remote servers.

        Arguments:
        addr - The IP address of remote host.
        user - The user name used to login to remote host.
        password - The password used to login to remote host.
        name - Name of connection, mostly a vanity value.
        limit - The maximum permissable connections, default = 20
        '''
        self.addr = addr
        self.user = user
        self.password = password
        self.name = name
        self.limit = limit

        self.con = paramiko.SSHClient()
        self.con.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.con.connect(addr,username=user,password=password)
        self.count = 0
        self.pool_lock = threading.Lock()

        self.version = sys.version_info[0]

    def openFile(self,path,mode=None):
        '''
        Standard file opening method. 

        Arguments:
        path - remote path.
        '''
        if not mode:
            mode = 'r'
        self.__con_lock()
        try:
            ret = ConFile(path,self,mode)
            self.count += 1
        finally:
            self.pool_lock.release()

        return ret

    def getFile(self,local_path,remote_path):
        '''
        Downloads a remote file.

        Arguments:
        local_path - the location on your local machine where the file is to be saved to.
        remote_path - the location on the remote machine where the file is to be read from.
        '''
        self.__con_lock()

        sftp = self.con.open_sftp()
        sftp.get(local_path,remote_path)
        sftp.close()

        self.pool_lock.release()

    def __conClose(self):
        '''
        Hidden method for decrementing the number of connections.
        '''        
        self.pool_lock.acquire()
        self.count -= 1
        self.pool_lock.release()

    def __conOpen(self):
        '''
        Hidden method for aquiring a reservered connection
        '''
        self.__con_lock()
        self.count += 1
        self.pool_lock.release()

    def exec_command(self,com,get_pty=False):
        '''
        A pass through method for paramiko's exec_command.

        Arguments:
        com - the command to be executed.
        '''
        return self.con.exec_command(com,get_pty=get_pty)

    def simple_command(self,com):
        '''
        This method is designed to make simple calling methods like "uptime" or "ls" which have
        no need for interaction, but are just to fetch info.

        Arguments:
        com - the command to be executed.
        '''
        stdin, stdout, stderr = self.con.exec_command(com)
        if self.version == 2:
            ret = str(stdout.read()).encode('utf-8')
        else:
            ret = str(stdout.read(),'utf-8')

        return ret

    def simple_sudo(self,com):
        '''
        Simple sudo is here to simplify the process of using a command that needs sudo. It will
        only work if the user you are logged in as has sudo privilages.

        Arguments:
        com - The command to be executed. Sudo will be added. so if you need to run:
            sudo cp here there
        just pass
            cp here there
        and this command will take care of the rest.
        '''
        stdin, stdout, stderr = self.con.exec_command("sudo " + com, get_pty=True)
        stdin.write(self.password+"\n")
        print(stdout.readlines())
        print(stdout.readlines())

    def __con_lock(self):
        '''
        Hidden convenience method for acquiring when safe. 
        '''
        while self.count > self.limit:
            time.sleep(1)
        self.pool_lock.acquire()

##    def __free(self):
##        self.pool_lock.release()

class ConFile():
    def __init__(self,path,parent,mode=None):
        '''
        An interface for remote files. This class will tend to opening and closing connections with
        the remote server and keeping track of the current location in the remote file. This way
        logfile can believe it still is connecting straight to the remote file, but in reality the
        connection will frequently be closed and passed to a different log. This allows for dozens
        and hundreds of logs to be open with out running into problems with maximum number of ssh
        connections on a given server.

        Note: This fancy stuff isn't implemented yet, so currently this is mostly a wrapper.

        Arguments:
        path - the location of the file on the remote server.
        parent - the connection class that this confile belongs to. 
        '''
        self.mode = mode
        if not mode:
            self.mode = 'r'
        self.path = path
        self.parent = parent

        self.version = sys.version_info[0]

        try:
            self.sftp = parent.con.open_sftp()
            self.file = self.sftp.open(path,self.mode)
        except FileNotFoundError as e:
            print("file does not exist: {0}".format(path))
        except Exception as e:
            print("Something has gone wrong retriving file")

    def close(self):
        self.file.close()
        #self.parent.__fClose()

    def lastEdit(self):
        try:
            lastEdit = self.sftp.stat(self.path)
            lastEdit = time.localtime(lastEdit.st_mtime)
            lastEdit = time.strftime("%Y-%m-%d",lastEdit)
            return lastEdit
        except FileNotFoundError as e:
            print("Cannot see last edit as file does not exist: {0}".format(self.path))
            return None

    def checkExists(self):
        try:
            stats = self.sftp.stat(self.path)
        except FileNotFoundError as e:
            return False
        return True

    def read(self,amount):
        return self.file.read(amount)

    def write(self,content):
        self.file.write(content)

    def uread(self,amount=None):
        if not amount:
            amount = 65535
        ret = ''
        if self.version == 2:
            fetch = str(self.file.read(amount)).encode('utf-8')
        else:
            fetch = str(self.file.read(amount),'utf-8')
        while len(fetch) and len(ret) < amount:
            ret += fetch
            if self.version == 2:
                fetch = str(self.file.read(amount)).encode('utf-8')
            else:
                fetch = str(self.file.read(amount),'utf-8')
        return ret

    def stat(self):
        return self.file.stat()

    def tell(self):
        return self.file.tell()

    def seek(self,val):
        self.file.seek(val)
