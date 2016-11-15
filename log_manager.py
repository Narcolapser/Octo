# -*- coding: utf-8 -*-

from kivy.clock import Clock

import connection
import model

import sqlite3
import time
import os
import random
import threading
import hashlib

log_levels = ["TRACE","DEBUG","INFO","WARNING","WARN","ERROR","SEVERE"]

class LogManager():
    def __init__(self):
        try:
            os.remove(os.path.join(model.gstore.data_dir,"log.db"))
        except Exception as e:
            print('Error: {0}'.format(e))
            #print("no database, skipping deleting")

        self.lock = threading.Lock()

        self.db = sqlite3.connect(os.path.join(model.gstore.data_dir,"log.db"))
        c = self.db.cursor()
        c.execute("CREATE TABLE logs (ID integer, logID integer, line text, type integer, parent integer)")

        self.logs = {}

    def openLog(self,path,connection):
        key = hash(path+connection.addr)
        if key in self.logs.keys():
            return self.logs[key]

        self.logs[key] = LogFile(self,connection,key,path)

        return self.logs[key]

    def getCursor(self):
        self.lock.acquire()
        return self.db.cursor()

    def closeCursor(self,cur):
        cur.close()
        self.db.commit()
        self.lock.release()


class LogFile():
    def __init__(self,db,connection,logID,path):
        self.db = db
        self.connection = connection
        self.logID = logID
        self.path = path
        
        self.row_count = 0

        self.populate()

    def query(self,query):
        c = self.db.getCursor()

        c.execute(query)

        val = c.fetchall()

        self.db.closeCursor(c)

        return val

    def populate(self):
        self.file = self.connection.openFile(self.path)

        val = self.file.uread().split('\n')

        self.last = val[-1]

        val = val[:-1]

        c = self.db.getCursor()
        
        tracer = 0
        for i in val:
            #this was to elegant to totally remove. I'll leave it for at least one commit.
            #but i'm afraid of how much time it will take when it has to be run across several
            #thousand rows.
            #if True in [j in i[:10] for j in log_levels]:
            
            tip = i[:i.find(' ')]
            try:
                log_type = log_levels.index(tip)
            except ValueError:
                log_type = -1
            if log_type != -1:
                tracer = self.row_count
            
            
                
            c.execute("INSERT INTO logs values (?,?,?,?,?)",
                      (self.row_count,self.logID,i,log_type,tracer))
            self.row_count += 1

        self.db.closeCursor(c)
        
        Clock.schedule_interval(self.update,1)

    def update(self, *args):
        val = (self.last+self.file.uread()).split('\n')
        self.last = val[-1]
        val = val[:-1]
        c = self.db.getCursor()
        
        tracer = 0
        for i in val:
            tip = i[:i.find(' ')]
            try:
                log_type = log_levels.index(tip)
            except ValueError:
                log_type = -1
            if log_type != -1:
                tracer = self.row_count
            c.execute("INSERT INTO logs values (?,?,?,?,?)",
                      (self.row_count,self.logID,i,log_type,tracer))
            self.row_count += 1

        #print(self.row_count)
        self.db.closeCursor(c)
