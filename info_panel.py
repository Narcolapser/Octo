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

    def refreshMemory(self):
        self.memory = self.server.getMemory()

Builder.load_file('./info_panel.kv')

