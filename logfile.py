from tkinter import *
from tkinter import ttk

import paramiko
import threading
import sqlite3
import time
import tempfile

class LogFile(ttk.Frame):
    def __init__(self,master,con,log,addr,frame,filterFrame):
        ttk.Frame.__init__(self,master)
        log = self.preProcess(log)
        self.con = con
        self.log = log
        self.name = log[log.rfind("/")+1:]
        self.dbname = self.name[:self.name.find(".")]
        self.dbname = self.dbname[:self.name.find("-")]
        self.dbname = addr[:addr.find("-")] + "_" + self.dbname
        self.sftp = con.open_sftp()
        self.file = self.sftp.open(log)
        self.addr = addr
        self.vis = False
        self.tail = ""
        self.lines = []
        self.progress = 0.0
        self.new_lines = []
        self.frame = frame
        self.filterFrame = filterFrame

        self.disp_tree = ttk.Treeview(frame)
        self.s = ttk.Scrollbar(frame,orient='vertical', command=self.disp_tree.yview)
        self.disp_tree.configure(yscroll=self.s.set)
        self.disp_tree.heading('#0', text=addr, anchor='w')


        self.filters = ttk.Treeview(filterFrame)
        self.scrollFilters = ttk.Scrollbar(filterFrame,orient='vertical',
                                           command=self.filters.yview)
        self.filters.configure(yscroll=self.scrollFilters.set)
        self.filters.heading('#0', text='Filterss for: '+addr, anchor='w')
        
        self.updater = None

        self.tempdir = tempfile.TemporaryDirectory()
        self.logDB = self.getDBHandle()
        cur = self.logDB.cursor()
        com = "CREATE TABLE {0} (line text)".format(self.dbname)
        #print(com)
        cur.execute(com)
        self.logDB.commit()

        

    def getDBHandle(self):
        #self.tfile = tempfile.NamedTemporaryFile()
        tf = self.tempdir.name + self.dbname
        #print(tf)
        con = sqlite3.connect(tf)
        return con

    def preProcess(self,val):
        if "<date>" in val:
            val = val.replace("<date>",time.strftime("%Y-%m-%d",time.gmtime()))

        #print(val)
        return val

    def update(self):
        if not self.updater:
            self.updater = threading.Thread(name=self.getName()+"updater",target=self.__populate)
            self.updater.start()
        #print(self.updater.is_alive())
        if not self.updater.is_alive():
            #cur = self.logDB.cursor()
            #cur.execute("SELECT * FROM {0}".format(self.dbname))
            #self.new_lines = cur.fetchall()
            print(len(self.new_lines))
            for i in self.new_lines:
                self.disp_tree.insert('','end',text=i)
            self.new_lines = []
            self.updater = threading.Thread(name=self.getName()+"updater",target=self.__populate)
            self.updater.start()
        else:
            return False
        
    def __populate(self):
        values = str(self.file.read(65535),'utf-8')
        per = 0.1
        upDB = self.getDBHandle()
        cur = upDB.cursor()
        while len(values) > 1000:
            values = self.tail + values
            lines = values.splitlines()

            #deal with line fragments
            self.tail = lines.pop()

            self.append_lines(lines)
            #self.append_lines_db(lines,upDB,cur)

            values = str(self.file.read(65535),'utf-8')

            fstats = self.file.stat()
            size = fstats.st_size
            loc = self.file.tell()
            self.progress = loc/(size*1.0)

            if self.progress > per:
                print(self.progress*100,len(self.new_lines))
                per += 0.1

            if len(self.new_lines)> 5000: break

        self.tail += values

        print("there were {0} new lines.".format(len(self.new_lines)))

    def append_lines(self,lines):
        for line in lines:
            if self.check_line(line):
                self.lines.append(line)
                self.new_lines.append(line)

    def append_lines_db(self,lines,upDB,cur):
        for line in lines:
            inserts = 'INSERT INTO {0} VALUES (?)'.format(self.dbname)
            cur.execute(inserts,(line,))
        upDB.commit()

        cur.execute("SELECT * FROM {0}".format(self.dbname))
        self.new_lines = cur.fetchall()

    def getName(self):
        ret = self.addr + ":" + self.log
        return ret

    def __name__(self):
        return getName()

    def setVisible(self,state=True):
        if state:
            if not self.vis:
                self.s.pack(side='right',fill=BOTH)
                self.disp_tree.pack(side='top',fill=BOTH,expand=1)
                self.filters.pack(side='top',expand=1)
                self.vis=True
                
        else:
            if self.vis:
                self.s.pack_forget()
                self.disp_tree.pack_forget()
                self.filters.pack_forget()
                self.vis=False

    def addFilter(self,fstring):
        print("adding filter!")
        self.filters.insert('','end',text=fstring)
        self.refilter()

    def refilter(self):
        children = self.disp_tree.get_children()
        for child_id in children:
            child = self.disp_tree.item(child_id)
            for f in self.filters.get_children():
                fil = self.filters.item(f)
                if fil['text'] in child['text']:
                    self.disp_tree.delete(child_id)
                    break

    def check_line(self,val):
        quickToggle = True
        for f in self.filters.get_children():
            fil = self.filters.item(f)
            if fil['text'] in val:
                return False
        if "INFO" in val[:4]:
            return quickToggle
        if "DEBUG" == val[:5]:
            return quickToggle
        if "TRACE" == val[:5]:
            return quickToggle
        if "ERROR" == val[:5]:
            return quickToggle
        if "WARN" == val[:4]:
            return quickToggle
        return not quickToggle

    def download(self,path):
        sftp = self.con.open_sftp()
        sftp.get(self.log,path+self.name)
        sftp.close()

    def selected_values(self):
##      for i in tree.selection():
##            print(i)
        ret = []
        for i in self.disp_tree.selection():
            item = self.disp_tree.item(i)
            ret.append(item['text'])

        return "\n".join(ret)
