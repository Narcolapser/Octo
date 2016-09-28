"""#!/c/Python34/python"""
"""#!/usr/bin/python"""
from tkinter import *
from tkinter import ttk
from logfile import LogFile
import logback
import connection

import paramiko
import json
import threading
import time
import queue
import os
import tempfile
import sys

def connectToAddr():
##    con = paramiko.SSHClient()
##    con.set_missing_host_key_policy(paramiko.AutoAddPolicy())
##    #print(server_addr.get())
##    con.connect(server_addr.get(),username=config['auth']['username'],
##                password=config['auth']['password'])
    
    name = server_addr.get()
    name = name[:name.find('.')]
    con = connection.Connection(server_addr.get(),config['auth']['username'],
                config['auth']['password'],name)
    connections[name]=con
    #print("name: ", name)
    tree.insert('','end',server_addr.get(),text=name,value=('',con),tags=('clicky','simple'))
    tree.tag_bind('clicky','<ButtonRelease-3>',itemClicked)
    #sftp = con.open_sftp()

    logs = []
    
    for log in config['logs']:
        logs.append(resolve_log(con,log))
    
    for log in logs:
        #print("log: ",log[0])
        try:
            logf = LogFile(frame,filterFrame,con,log[0],server_addr.get(),tempdir)
            if not logf.checkExists():
                print("Log file doesn't exist: ",log[0])
                continue
            log_files[logf.getName()] = logf
            parent = tree.insert(server_addr.get(),'end',server_addr.get()+log[0],text=logf.name,
                        values=(logf.lastEdit,logf.getName()),tags=('selected'))
            #tree.set(parent,'updated',)
            tree.tag_bind('selected','<ButtonRelease-1>',logSelected)
        except Exception as e:
            print("woopies! something went wrong with main log: ",e)
            continue

##        if len(log) > 1:
##            for sub_log in log[1]:
##                try:
##                    print(sub_log)
##                    logf = LogFile(frame,filterFrame,con,sub_log,server_addr.get(),tempdir)
##                    log_files[logf.getName()] = logf
##                    tree.insert(parent,'end',server_addr.get()+sub_log,text=logf.name,
##                            values=logf.getName(),tags=('selected'))
##                    tree.tag_bind('selected','<ButtonRelease-1>',logSelected)
##                except Exception as e:
##                    print("FAILURE!",e)

def resolve_log(con,log):
    #print(log)
    root = log['root'] + log['name']
    #print(root)
    if 'sequence' in log:
        com = "ls " + log['root'] + log['sequence'].format(date="*")
        stdin, stdout, stderr = con.exec_command(com)
        sub_logs = stdout.readlines()
        sub_logs = [i.replace('\n','') for i in sub_logs]
        #print(sub_logs)
        return (root,sub_logs)
    else:
        return (root,)
            
    
def logSelected(val):
    item = tree.item(tree.focus())
    logf = log_files[item['values'][1]]
    for i in log_files.keys():
        log_files[i].setVisible(False)

    #logf.update()

    logf.setVisible()

def itemClicked(val):
    item = tree.item(tree.identify_row(val.y))
    tree.selection_set(tree.identify_row(val.y))
    popup.tk_popup(val.x_root,val.y_root,0)

def log_config_window(val=None):
    item = tree.item(tree.selection()[0])
    #print(item)
    name = tree.selection()[0]
    name = name[:name.find('.')]
    #print(name)
    lcw = Toplevel()
    lcw.title("Logging configuration")
    #/usr/local/tomcat/webapps/uPortal/WEB-INF/classes/logback.xml
    con = connections[name]
    #print(con)

    ##sftp = con.open_sftp()
    ##config_file = sftp.open("/usr/local/tomcat/webapps/uPortal/WEB-INF/classes/logback.xml")
    config_file = con.openFile("/usr/local/tomcat/webapps/uPortal/WEB-INF/classes/logback.xml")

    conString = config_file.uread()
    config_file.close()
    #print(conString)
    #print(type(conString))
    lb = logback.Logback(str(conString))
    #print(lb)
    lcw.lb = lb
    lcw.lframes = []
    lcw.con = con

    for logger in lb.loggers:
        lframe = log_frame(lcw,logger)
        lframe.pack(side="top",fill=BOTH)
        lcw.lframes.append(lframe)

    cancel = ttk.Button(lcw,text='Close',command=lcw.destroy)
    cancel.pack(side="right",fill=BOTH)

    button = ttk.Button(lcw,text='Save',command=log_change)
    button.pack(side="right",fill=BOTH)

    root.lcw = lcw
    
def log_change():
    for lframe in root.lcw.lframes:
        active = lframe.logActiveVar.get()

        #this is flipped around because the GUI deals with "is active" while the file deals with
        #"is commented out".... or maybe not....
        if active == 'False':
            lframe.logger.commented = False
        else:
            lframe.logger.commented = True

        lframe.logger.level = lframe.logLevelVar.get()
    print(root.lcw.lb)
    
##    con = root.lcw.con
##    sftp = con.open_sftp()
##    #config_file = sftp.open("/usr/local/tomcat/webapps/uPortal/WEB-INF/classes/logback.xml",'w')
##    config_file = sftp.open("logback.xml",'w')
##    config_file.write(str(root.lcw.lb))
##    config_file.close()

    con = root.lcw.con
    config_file = con.openFile("logback.xml","w")
    config_file.write(str(root.lcw.lb))
    config_file.close()

    if not root.lcw.lb.generated:
        stdin, stdout, stderr = con.exec_command("sudo cp /usr/local/tomcat/webapps/uPortal/WEB-INF/classes/logback.xml /usr/local/tomcat/webapps/uPortal/WEB-INF/classes/logback.xml.bak", get_pty=True)
        stdin.write(config['auth']['password']+"\n")
        print(stdout.readlines())
        print(stderr.readlines())
    print(root.lcw.lb.generated)
    
    stdin, stdout, stderr = con.exec_command("sudo cp logback.xml /usr/local/tomcat/webapps/uPortal/WEB-INF/classes/logback.xml", get_pty=True)
    stdin.write(config['auth']['password']+"\n")
    stdin.flush()
    print(stdout.readlines())
    print(stderr.readlines())
    

def log_frame(parent,log):
    topFrame = ttk.Frame(parent)
    topFrame.logger = log

    logLabel = ttk.Label(topFrame,text=log.name)
#    if 'Sql' in log.name:
#        log.commented = True
    print(log.commented)
    topFrame.logActiveVar = StringVar(master=topFrame,value=str(log.commented))
    logActive = ttk.Checkbutton(topFrame,text="Activate.",
                                variable=topFrame.logActiveVar,
                                onvalue='False', offvalue='True')
    
    #print(logActive.selection_get())
    #print(log.level)
    topFrame.logLevelVar = StringVar(master=topFrame,value=log.level)
    logLevel = ttk.Entry(topFrame,textvariable=topFrame.logLevelVar)

    logLabel.pack(side="left",fill=BOTH)
    logLevel.pack(side="right",fill=BOTH)
    logActive.pack(side="right",fill=BOTH)

    return topFrame



def connectBar(parent):
    topFrame = ttk.Frame(parent)

    inframe = ttk.Frame(topFrame)
    conButton = ttk.Button(inframe, text="Connect",command=connectToAddr)
    namelbl = ttk.Label(inframe, text="Server Address")
    namelbl.pack(side="left",fill=BOTH)
    conButton.pack(side="right",fill=BOTH)
    inframe.pack(side="top",fill=BOTH)

    name = ttk.Combobox(topFrame,textvariable=server_addr)
    name.pack(side="top",fill=BOTH)

    hosts = []
    for host in config['hosts']:
        hosts.append(host)
    name['values'] = hosts
    server_addr.set(hosts[0])

    topFrame.pack(side="top",fill=BOTH)

def filterEntry(parent):
    topFrame = ttk.Frame(parent)

    inframe = ttk.Frame(topFrame)
    addButton = ttk.Button(inframe, text="Add",command=insertFilter)
    delButton = ttk.Button(inframe, text="Remove",command=removeFilter)
    refButton = ttk.Button(inframe, text="Refresh",command=refreshFilters)
    namelbl = ttk.Label(inframe, text="Filter Entry")
    namelbl.pack(side="left",fill=BOTH)
    addButton.pack(side="right",fill=BOTH)
    delButton.pack(side="right",fill=BOTH)
    refButton.pack(side="right",fill=BOTH)
    inframe.pack(side="top",fill=BOTH)

    name = ttk.Entry(topFrame,textvariable=filter_entry)
    name.pack(side="top",fill=BOTH)

    topFrame.pack(side="top",fill=BOTH)

def insertFilter():
    item = tree.item(tree.focus())
    try:
        logf = log_files[item['values'][1]]
        logf.addFilter(filter_entry.get())
    except Exception as e:
        print(e)

def removeFilter():
    item = tree.item(tree.focus())
    try:
        logf = log_files[item['values'][1]]
        logf.removeFilter()
    except Exception as e:
        print(e)

def refreshFilters():
    item = tree.item(tree.focus())
    try:
        logf = log_files[item['values'][1]]
        logf.refilter()
    except Exception as e:
        print(e)

def downloadFiles():
    logs = []
    sel = tree.selection()

    for i in sel:
        try:
            item = tree.item(i)
            logs.append(log_files[item['values'][1]])
        except Exception as e:
            print(e)

    for logf in logs:
        print(logf.name)
        log_dir = "c:/development/logs/{0}/".format(logf.addr)
        if not os.path.isdir(log_dir):
            os.mkdir(log_dir)
        logf.download("c:/development/logs/{0}/".format(logf.addr))
        


def clipboard_copy(val):
    item = tree.item(tree.focus())

    try:
        logf = log_files[item['values'][1]]
        clip = logf.selected_values()
        root.clipboard_clear()
        root.clipboard_append(clip)
        print(clip)
    except Exception as e:
        print(e)
        return


def update_logs():
    #print("I'm idle!")

    for l in log_files.keys():
        #print(l)
        log_files[l].update()
    
    root.after(100,update_logs)

config = json.load(open("dev.config"))
root = Tk()
root.title("Octo")
r_click_selection = None
usefulbits = {}
memoryleak = []


popup = Menu(root,tearoff=0)
popup.add_command(label="Configure Logs",command=log_config_window)

server_addr = StringVar(master=root)
filter_entry = StringVar(master=root, value="enter new filters here")
connections = {}
log_files = {}
log_back = {}
tempdir = tempfile.TemporaryDirectory()


content = ttk.Frame(root, padding=(3,3,12,12))
frame = ttk.Frame(content, width=600, height=600)
content.pack(side='top',fill=BOTH,expand=1)

frameLeft = ttk.Frame(content, width=200, height=600)
filterFrame = ttk.Frame(frameLeft, width=200, height=400)
connectBar(frameLeft)

tree = ttk.Treeview(frameLeft)
tree.pack(side="top",fill=BOTH, expand=1)
tree['columns'] = ('updated',)#'fnames',
#tree.column('fnames',width=200,anchor='e')
#tree.column('con',width=0)
tree.column('updated',width=100,anchor='center')
#tree.heading('fnames', text='Server and file list')
tree.heading('updated', text='Last updated')

dlbutton = ttk.Button(frameLeft, text="Download!", command=downloadFiles)
dlbutton.pack(side="top",fill=X)


frameLeft.pack(side='left',fill=Y)
frame.pack(side='top',fill=BOTH, expand=1)

filterFrame.pack(side='right',expand=1,fill=Y)
filterEntry(filterFrame)

root.bind_all('<Control-Key-c>',clipboard_copy)

root.after(100,update_logs)

if "idlelib" in sys.modules:
    print("And we are in Idle")
else:
    print("not debugging, real program! woohoo!")

root.mainloop()
