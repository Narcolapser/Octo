import connection
import logback

class Server():
    '''
    Wrapper class for a server connection. Meant to be passed around to the info panels. There are
    a couple of default server information methods available. 
    '''
    def __init__(self,config):
        '''
        Arguments:
        The configuration.
        '''
        self.config = config

        self.hostname = config['name']
        self.address = config['address']
        self.username = config['auth']['username']
        self.password = config['auth']['password']

        self.con = connection.Connection(self.address,self.username,self.password,self.hostname)

        self.PID = None
        
    def getHostName(self):
        return self.hostname

    def getAddress(self):
        return self.con.addr

    def getIsUp(self):
        self.getPID()
        if self.PID:
            return True
        return False

    def getPID(self):
        self.PID = self.con.simple_command(' ps -ef | grep "dynatrace" | grep -v grep |awk \'{print $2}\'')
        print([self.PID])
        return self.PID

    def getServiceUpTime(self):
        com = "ps -p {0} -o etime=".format(self.getPID().replace('\n',''))
        value = self.con.simple_command(com)
        print(com,value)
        return value

    def getUpTime(self):
        value = self.con.simple_command("uptime")
        return value

    def getMemory(self):
        value = self.con.simple_command("free -m")
        return value

class LogbackFile():
    '''
    Model for the logback info panel. contains the necessary methods for reading and writing
    logback files. Also, currently the default location of the logback file as well. Seeing as
    there are multiple logback files on the server, this may have to change in the future.
    '''
    path = '/usr/local/tomcat/webapps/uPortal/WEB-INF/classes/logback.xml'
    def __init__(self,con):
        '''
        pass the connection object.
        '''
        self.con = con
        f = con.openFile(self.path)
        val = f.uread()
        f.close()
        self.lb_string = val
        self.lb = logback.Logback(val)
        
    def getLoggers(self):
        '''
        Pass through method that returns a list of loggers from the logback.py file.
        '''
        return self.lb.loggers

    def save(self):
        '''
        This method will save the logback file as you have it currently edited. It handles all the
        interaction and precautions of writing the logback.xml file.
        '''
        
        #Create and save the file to the user's home directory. This is done to simplify the
        #process of putting the new logback.xml in place, but also provides a crumb trail.
        config_file = self.con.openFile("logback.xml",'w')
        config_file.write(str(self.lb))
        config_file.close()

        if not self.lb.generated: #if the last logback wasn't generated, we need to make a backup.
            self.con.simple_sudo("cp {0} {0}.bak".format(self.path))

        #Now that the file is on the server and we know there is a backup. Let's copy the
        #logback.xml file from the home directory to the actual directory.
        self.con.simple_sudo("cp logback.xml {0}".format(self.path))
            

class LBAppender():
    pass

class LBLogger():
    pass

class Catalina():
    '''
    The model class for the catalina.out info panel. Takes care of fetching and holding all the
    information that is coming out of the catalina.out file. 
    '''
    def __init__(self,con):
        self.con = con
        self.file = con.openFile('/usr/local/tomcat/logs/catalina.out')
        self.start = self.file.stat().st_size
        self.start -= 10000
        if self.start < 1:
            self.start = 0
        self.content = ''

        self.file.seek(self.start)
        self.content += self.file.uread(1000)

    def update(self):
        '''
        Get the current content available. Note that this is basically from when you first
        connected to now.
        '''
        self.content += self.file.uread(1000)
        return self.content
