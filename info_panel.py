import connection

from kivy.uix.gridlayout import GridLayout
from kivy.lang import Builder
from kivy.properties import ObjectProperty, StringProperty

class Info_Panel(GridLayout):
    hostname = StringProperty("loading...")
    address = StringProperty("loading...")
    isup = StringProperty("loading...")
    serveruptime = StringProperty("loading...")
    memory = StringProperty("loading...")
    serviceuptime = StringProperty("loading...")
    
    def setServer(self,server):
        self.server = server
        self.refreshValues()

        self.refreshHostName()
        self.refreshAddress()

    def refreshValues(self):
        self.refreshIsUp()
        self.refreshUpTime()
        self.refreshMemory()

    def refreshHostName(self):
        self.hostname = self.server.getHostName()

    def refreshAddress(self):
        self.address = self.server.getAddress()

    def refreshIsUp(self):
        if self.server.getIsUp():
            self.isup = "Yes"
        else:
            self.isup = "No"

    def refreshUpTime(self):
        self.serveruptime = self.server.getUpTime()
        self.serviceuptime = self.server.getServiceUpTime()

    def refreshMemory(self):
        self.memory = self.server.getMemory()

#Builder.load_file('./info_panel.kv')

kv = '''
<Info_Panel>:
    canvas:
        Color:
            rgba: 0.5,0.5,0.5,0.5
        Rectangle:
            size: self.size
            pos: self.pos
        Color:
            rgba: 0.2,0.2,0.2,0.5
        Rectangle:
            size: self.size[0] - 20, self.size[1] - 20
            pos: self.pos[0] + 10, self.pos[1] + 10
    cols:2
    size_hint_y:None
    row_default_height: 50
    Label:
        size_hint_y:None
        text: 'Name'
    Label:
        size_hint_y:None
        text: root.hostname
    Label:
        size_hint_y:None
        text: 'Address'
    Label:
        text: root.address
    Label:
        size_hint_y:None
        text: 'isup'
    Label:
        text: root.isup
    Label:
        size_hint_y:None
        text: 'Server up time'
    Label:
        text: root.serveruptime
    Label:
        size_hint_y:None
        text: 'Memory'
    Label:
        text: root.memory
    Label:
        size_hint_y:None
        text: 'Service Uptime'
    Label:
        text: root.serviceuptime

'''
Builder.load_string(kv)
