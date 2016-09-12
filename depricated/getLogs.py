import paramiko
import json
import time

def getConfig():
    f = open('dev.config','r')
    config = json.load(f)
    return config

class Server:
    def __init__(self,address,auth):
        self.address = address
        self.auth = auth
        self.__connect()
        

    def __connect(self):
        self.con = self.getConnection()

    def getConnection(self):
        con = paramiko.SSHClient()
        con.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        con.connect(self.address,username=self.auth['username'],
                         password=self.auth['password'])
        return con

    def __call__(self,command):
        #self.connect()
        stdin, stdout, stderr = self.con.exec_command(command)
        results = stdout.readlines()
        #self.con.close()
        return results
        

    def uname(self):
        return self("uname -a")

    def getFile(self,remotePath,localPath):
        con = self.getConnection()
        ftp = self.con.open_sftp()
        ftp.get(remotePath,localPath)
        ftp.close()

    def getLogTar(self,logs,localPath):
        con = self.getConnection()
        con.exec_command("mkdir /tmp/logs/")
        for log in logs:
            con.exec_command("cp -rf " + log + " /tmp/logs/")
        #con.exec_command("tar -czf /tmp/logs.tar " + ''.join("%s " % log for log in logs))
        con.exec_command("tar -czf /tmp/logs.tar.gz /tmp/logs/*")
        self.getFile('/tmp/logs.tar.gz',localPath)
        con.close()

config = getConfig()
servers = [Server(host,config['auth']) for host in config['hosts']]
logs = ["/usr/local/uportal-tomcat/logs/CalendarPortlet.log",
        "/usr/local/uportal-tomcat/logs/email-preview.log",
        "/usr/local/uportal-tomcat/logs/portal/portal.log",
        "/usr/local/uportal-tomcat/logs/localhost." +
        str(time.strftime('%Y-%m-%d',time.gmtime())) + ".log"]


#print(servers)
for s in servers:
    #print(s.uname())
    #s.get("/usr/local/uportal-tomcat/logs/portal/portal.log","/development/"+s.address+".log")
    s.getLogTar(logs,s.address+".tar.gz")
    pass
