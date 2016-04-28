from tkinter import *
from tkinter import ttk

import paramiko
import threading
import sqlite3
import time
import os
import random

class LogFile(ttk.Frame):
    def __init__(self,master,filterFrame,con,log,addr,tempdir):
        ttk.Frame.__init__(self,master)
        self.master = master
        self.filterFrame = filterFrame
        self.con = con
        self.log = self.preProcess(log)
        self.addr = addr
        self.tempdir = tempdir.name
        
        self.vis = False
        self.lines = []
        self.tail = ""
        self.progress = 0.0
        self.new_lines = []
        self.numRows = 0
        self.lastAdded = 0
        self.updater = None
        self.alive = True
        self.has_new = False
        self.command = "SELECT * FROM lines WHERE ID > {0}"
        
        self.__makeConnection()
        self.__makeGUI()
        self.__makeName()
        self.__makeDB()

    def __makeConnection(self):
        self.sftp = self.con.open_sftp()
        self.file = self.sftp.open(self.log)

    def __makeGUI(self):
        self.disp_tree = ttk.Treeview(self.master)
        self.s = ttk.Scrollbar(self.master,orient='vertical', command=self.disp_tree.yview)
        self.disp_tree.configure(yscroll=self.s.set)
        self.disp_tree.heading('#0', text=self.addr, anchor='w')

        self.filters = ttk.Treeview(self.filterFrame)
        self.scrollFilters = ttk.Scrollbar(self.filterFrame,orient='vertical',
                                           command=self.filters.yview)
        self.filters.configure(yscroll=self.scrollFilters.set)
        self.filters.heading('#0', text='Filterss for: '+self.addr, anchor='w')

    def __makeName(self):
        self.name = self.log[self.log.rfind("/")+1:]
        self.dbname = self.name[:self.name.find(".")]
        self.dbname = self.dbname.replace("-","_")
        self.dbname = self.addr[:self.addr.find("-")] + "_" + self.dbname + str(random.randint(0,1000))


    def __makeDB(self):
        self.logDB = self.getDBHandle()
        cur = self.logDB.cursor()
        com = "CREATE TABLE lines (ID integer, line text)"
        cur.execute(com)
        self.logDB.commit()

        #self.update_cur = cur
        self.update_cur = None
        self.db_lock = threading.Lock()

    def getDBHandle(self):
        tf = self.tempdir + "\\" + self.addr + " - " + self.log[self.log.rfind("/")+1:]
        print(tf)
        con = sqlite3.connect(tf)
        return con

    def preProcess(self,val):
        if "{date}" in val:
            val = val.format(date=time.strftime("%Y-%m-%d",time.gmtime()))
        return val

    def update(self,update_num=1000):
        i = update_num
        if self.has_new:
            if self.db_lock.acquire(timeout=0.01):
                self.update_cur = self.logDB.cursor()
                com = self.command.format(self.lastAdded)
                self.update_cur.execute(com)

                row = self.update_cur.fetchone()
                while i > 0 and row:
                    self.lastAdded = row[0]
                    self.disp_tree.insert('','end',text=row[1])
                    i -= 1
                    row = self.update_cur.fetchone()

                if not row:
                    self.has_new = False

                self.update_cur.close()
                self.db_lock.release()
        
    def __populate(self):
        values = str(self.file.read(65535),'utf-8')
        per = 0.1
        upDB = self.getDBHandle()
        cur = upDB.cursor()
        while self.alive:
            while len(values) > 100:
                values = self.tail + values
                lines = values.splitlines()

                #deal with line fragments
                self.tail = lines.pop()
                
                self.append_lines_db(lines,upDB,cur)
                
                values = str(self.file.read(65535),'utf-8')

                fstats = self.file.stat()
                size = fstats.st_size
                loc = self.file.tell()
                self.progress = loc/(size*1.0)

                #print("we are {0}% through {1}.".format(self.progress*100,self.log))

            self.tail += values
            time.sleep(60)

    def append_lines(self,lines):
        for line in lines:
            if self.check_line(line):
                self.lines.append(line)
                self.new_lines.append(line)

    def append_lines_db(self,lines,upDB,cur):
        if len(lines):
            for line in lines:
                self.numRows += 1
                inserts = 'INSERT INTO lines VALUES (?,?)'.format(self.dbname)
                cur.execute(inserts,(self.numRows,line))
            for i in range(10):
                try:
                    self.db_lock.acquire(timeout=5)
                    upDB.commit()
                    self.has_new = True
                    self.db_lock.release()
                    break
                except Exception as e:
                    print("failed to commit to {1} on try {0}: ".format(i,self.dbname),e)
                    print(len(lines))
            

    def getName(self):
        ret = self.addr + ":" + self.log
        return ret

    def __name__(self):
        return getName()

    def setVisible(self,state=True):
        if not self.updater:
            self.updater = threading.Thread(name=self.getName()+"updater",target=self.__populate)
            self.updater.start()
            
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
        #self.refilter()

    def removeFilter(self,fstring):
        print("removing filter!")
        self.filters.insert('','end',text=fstring)
        #self.refilter()

    def refilter(self):
        filters = []
        for f in self.filters.get_children():
            filters.append(self.filters.item(f)['text'])

        if len(filters):
            wheres = " AND ".join(filters)
            self.command = "SELECT * FROM lines WHERE ID > {0} AND " + wheres

        else:
            self.command = "SELECT * FROM lines WHERE ID > {0}"


        self.s.pack_forget()
        self.disp_tree.pack_forget()
        del self.s
        del self.disp_tree
        
        self.disp_tree = ttk.Treeview(self.master)
        self.s = ttk.Scrollbar(self.master,orient='vertical', command=self.disp_tree.yview)
        self.disp_tree.configure(yscroll=self.s.set)
        self.disp_tree.heading('#0', text=self.addr, anchor='w')

        self.db_lock.acquire()
        self.lastAdded = 0
        self.db_lock.release()

        print(self.command)


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
        ret = []
        for i in self.disp_tree.selection():
            item = self.disp_tree.item(i)
            ret.append(item['text'])

        return "\n".join(ret)
