import connection
import logback

class Server():
    def __init__(self,config):
        self.config = config

        self.hostname = config['name']
        self.address = config['address']
        self.username = config['auth']['username']
        self.password = config['auth']['password']

        self.con = connection.Connection(self.address,self.username,self.password,self.hostname)
        
    def getHostName(self):
        return self.hostname

    def getAddress(self):
        return self.con.addr

    def getIsUp(self):
        value = self.con.simple_command('ps -aux | grep "java"')
        if "uportal" in value:
            return True
        return False

    def getUpTime(self):
        value = self.con.simple_command("uptime")
        return value

    def getMemory(self):
        value = self.con.simple_command("free -m")
        return value

class LogbackFile():
    path = '/usr/local/tomcat/webapps/uPortal/WEB-INF/classes/logback.xml'
    def __init__(self,con):
        self.con = con
        f = con.openFile(self.path)
        val = f.uread()
        f.close()
        self.lb_string = val
        self.lb = logback.Logback(val)
        
    def getLoggers(self):
        return self.lb.loggers

class LBAppender():
    pass

class LBLogger():
    pass
