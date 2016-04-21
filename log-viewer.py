import tkinter as tk
import tkinter.scrolledtext as tkst
import paramiko
import json

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
        

class Application(tk.Frame):
    def __init__(self, master=None):
        tk.Frame.__init__(self, master)
        self.pack()
        self.createWidgets()

    def createWidgets(self):
        #self.hi_there = tk.Button(self)
        #self.hi_there["text"] = "Hello World\n(click me)"
        #self.hi_there["command"] = self.say_hi
        #self.hi_there.pack(side="top")

        #self.QUIT = tk.Button(self, text="QUIT", fg="red",
        #                                    command=root.destroy)
        #self.QUIT.pack(side="bottom")

        config = getConfig()
        self.config = config
        self.servers = [Server(host,config['auth']) for host in config['hosts']]

        self.dev1 = self.servers[0]
        self.dev2 = self.servers[1]
        for s in self.servers:
            if "1" in s.address:
                self.dev1 = s
            if "2" in s.address:
                self.dev2 = s

        sftp1 = self.dev1.con.open_sftp()

        log1 = sftp1.open("/usr/local/uportal-tomcat/logs/newsreader.log")

        self.text1 = tkst.ScrolledText(master = root, wrap = tk.WORD)
        self.text1.insert(tk.INSERT,log1.read())

        self.text1.grid(column=1,row=0)

        

        
        

    def say_hi(self):
        print("hi there, everyone!")

root = tk.Tk()
app = Application(master=root)
app.mainloop()
