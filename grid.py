from tkinter import *
from tkinter import ttk
from logfile import LogFile

import paramiko
import json
import threading
import time
import queue
import os

#def logLoader(val):
#    val[0].disp_tree.insert('','end',text=val[1])

def itemClicked(val):
    pass    

def connectToAddr():
    con = paramiko.SSHClient()
    con.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    print(server_addr.get())
    con.connect(server_addr.get(),username=config['auth']['username'],
                password=config['auth']['password'])
    
    name = server_addr.get()
    name = name[:name.find('.')]
    connections[name]=con
    tree.insert('','end',server_addr.get(),text=name,value=con,tags=('clicky','simple'))
    tree.tag_bind('clicky','<ButtonRelease-1>',itemClicked)
    for log in config['logs']:
        try:
            logf = LogFile(frame,con,log,server_addr.get(),frame,filterFrame)
            log_files[logf.getName()] = logf
            tree.insert(server_addr.get(),'end',server_addr.get()+log,text=logf.name,
                        values=logf.getName(),tags=('selected'))
            tree.tag_bind('selected','<ButtonRelease-1>',logSelected)
        except Exception as e:
            print("woopies! something went wrong: ",e)
    
def logSelected(val):
    item = tree.item(tree.focus())

    logf = log_files[item['values'][0]]
    for i in log_files.keys():
        log_files[i].setVisible(False)
    logf.update()
    logf.setVisible()

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
    delButton = ttk.Button(inframe, text="Remove",command=insertFilter)
    namelbl = ttk.Label(inframe, text="Filter Entry")
    namelbl.pack(side="left",fill=BOTH)
    addButton.pack(side="right",fill=BOTH)
    delButton.pack(side="right",fill=BOTH)
    inframe.pack(side="top",fill=BOTH)

    name = ttk.Entry(topFrame,textvariable=filter_entry)
    name.pack(side="top",fill=BOTH)

    topFrame.pack(side="top",fill=BOTH)

def insertFilter():
    item = tree.item(tree.focus())
    try:
        logf = log_files[item['values'][0]]
        logf.addFilter(filter_entry.get())
    except Exception as e:
        print(e)

def downloadFiles():
    logs = []
    sel = tree.selection()
    

    for i in sel:
        try:
            item = tree.item(i)
            logs.append(log_files[item['values'][0]])
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
        logf = log_files[item['values'][0]]
        clip = logf.selected_values()
        root.clipboard_clear()
        root.clipboard_append(clip)
        print(clip)
    except Exception as e:
        print(e)
        return

    

config = json.load(open("dev.config"))
root = Tk()

server_addr = StringVar(master=root)#value=config['hosts'][0])
filter_entry = StringVar(master=root, value="enter new filters here")
connections = {}
log_files = {}

content = ttk.Frame(root, padding=(3,3,12,12))
frame = ttk.Frame(content, width=600, height=600)
content.pack(side='top',fill=BOTH,expand=1)

frameLeft = ttk.Frame(content, width=200, height=600)
filterFrame = ttk.Frame(frameLeft, width=200, height=400)
connectBar(frameLeft)

tree = ttk.Treeview(frameLeft)
tree.pack(side="top",fill=BOTH, expand=1)

dlbutton = ttk.Button(frameLeft, text="Download!", command=downloadFiles)
dlbutton.pack(side="top",fill=X)


frameLeft.pack(side='left',fill=Y)
frame.pack(side='top',fill=BOTH, expand=1)

filterFrame.pack(side='right',expand=1,fill=Y)
filterEntry(filterFrame)

root.bind_all('<Control-Key-c>',clipboard_copy)


root.mainloop()
