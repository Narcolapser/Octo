import paramiko
import time
import threading


class Connection():
    def __init__(self,addr,user,password,name,limit=20):
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

    def openFile(self,path):
        self.__con_lock()
        try:
            ret = ConFile(path,self)
            self.count += 1
        finally:
            self.pool_lock.release()

        return ret

    def openFileAsync(self,path):
        pass

    def getFile(self,local_path,remote_path):
        self.__con_lock()

        sftp = self.con.open_sftp()
        sftp.get(local_path,remote_path)
        sftp.close()

        self.pool_lock.release()

    def __fClose(self):
        self.pool_lock.acquire()
        self.count -= 1
        self.pool_lock.release()

    def exec_command(self,com):
        return self.con.exec_command(com)

    def __con_lock(self):
        while self.count > self.limit:
            time.sleep(1)
        self.pool_lock.acquire()

##    def __free(self):
##        self.pool_lock.release()

class ConFile():
    def __init__(self,path,parent):
        self.path = path
        self.parent = parent

        try:
            self.sftp = parent.con.open_sftp()
            self.file = self.sftp.open(path)
        except:
            print("file does not exist: {0}".format(path))

    def close(self):
        self.parent.__fClose()

    def lastEdit(self):
        try:
            lastEdit = self.sftp.stat(self.path)
            lastEdit = time.localtime(lastEdit.st_mtime)
            lastEdit = time.strftime("%Y-%m-%d",lastEdit)
            return lastEdit
        except:
            return None

    def read(self,amount):
        return self.file.read(amount)

    def write(self,content):
        self.file.write(content)

    def uread(self,amount):
        return str(self.file.read(amount),'utf-8')

    def stat(self):
        return self.file.stat()

    def tell(self):
        return self.file.tell()
