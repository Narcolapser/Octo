from tkinter import *
from tkinter import ttk
import paramiko
import json
import threading
import time
import queue

class LogFile(ttk.Frame):
    def __init__(self,master,con,log,addr):
        ttk.Frame.__init__(self,master)
        log = self.preProcess(log)
        self.con = con
        self.log = log
        self.name = log[log.rfind("/")+1:]
        print(self.name)
        self.sftp = con.open_sftp()
        self.file = self.sftp.open(log)
        self.addr = addr
        self.vis = False
        self.tail = ""
        self.lines = []
        self.progress = 0.0
        self.new_lines = []

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

    def preProcess(self,val):
        if "<date>" in val:
            val = val.replace("<date>",time.strftime("%Y-%m-%d",time.gmtime()))

        print(val)
        return val

    def update(self):
        if not self.updater:
            self.updater = threading.Thread(name=self.getName()+"updater",target=self.__populate)
            self.updater.start()
        #print(self.updater.is_alive())
        if not self.updater.is_alive():
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
        while len(values) > 1000:
            values = self.tail + values
            lines = values.splitlines()

            #deal with line fragments
            self.tail = lines.pop()

            self.append_lines(lines)

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
        self.update()

    def append_lines(self,lines):
        for line in lines:
            if self.check_line(line):
                self.lines.append(line)
                self.new_lines.append(line)

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


def logLoader(val):
    val[0].disp_tree.insert('','end',text=val[1])
    

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
            logf = LogFile(frame,con,log,server_addr.get())
            log_files[logf.getName()] = logf
            tree.insert(server_addr.get(),'end',server_addr.get()+log,text=logf.name,
                        values=logf.getName(),tags=('selected'))
            tree.tag_bind('selected','<ButtonRelease-1>',logSelected)
        except Exception as e:
            print("woopies! something went wrong: ",e)
    

def itemClicked(val):
    pass

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

    topFrame.pack(side="top",fill=BOTH)

def insertFilter():
    item = tree.item(tree.focus())
    try:
        logf = log_files[item['values'][0]]
        logf.addFilter(filter_entry.get())
    except Exception as e:
        print(e)

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

def downloadFiles():
    item = tree.item(tree.focus())

    try:
        logf = log_files[item['values'][0]]
    except Exception as e:
        print(e)
        return

    logf.download("C:/development/logs/")

    

config = json.load(open("dev.config"))
root = Tk()

server_addr = StringVar(master=root, value="Enter/Select Server Address Here")#value=config['hosts'][0])
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


root.mainloop()
