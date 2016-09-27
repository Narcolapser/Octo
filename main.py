import json
import kivy
kivy.require('1.9.1')

from kivy.app import App
from kivy.config import ConfigParser

from kivy.properties import ObjectProperty

from kivy.uix.widget import Widget
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.settings import SettingsWithSidebar

from kivy.uix.gridlayout import GridLayout

from kivy.uix.tabbedpanel import TabbedPanel
from kivy.uix.tabbedpanel import TabbedPanelItem
from kivy.uix.tabbedpanel import TabbedPanelHeader


from info_panel import Info_Panel
import connection


hosts = json.load(open("hosts.ini"))

class Octo(TabbedPanel):
    serverTab = ObjectProperty(None)
    
    def addServers(self):
        self.serverTab.text = "Servers"
        self.serverTab.addServers()

    def add_connection(self,val):
        OServ = OctoServer()
        OServ.connect(val)
        OServ.text = val['name']
        OServ.load_panels()
        self.add_widget(OServ)
        self.switch_to(OServ)
        
        
class OctoServersTab(TabbedPanelItem):
    grid = ObjectProperty(None)

    def addServers(self):
        for host in hosts:
            o = OctoLauncher()
            o.text = host
            o.config = hosts[host]
            self.grid.add_widget(o)

class OctoServer(TabbedPanelItem):
    info_panel = ObjectProperty(None)

    def connect(self,configs):
        self.vals = configs
        self.hostname = configs['name']
        self.address = configs['address']
        self.username = configs['auth']['username']
        self.password = configs['auth']['password']
        self.connection = connection.Connection(self.address,self.username,self.password,self.hostname)
    
    def load_panels(self):
        i1 = Info_Panel()
        i1.setConnection(self.connection)
        self.info_panel.add_widget(i1)
        
        i2 = Info_Panel()
        i2.setConnection(self.connection)
        self.info_panel.add_widget(i2)
        
class OctoInfo(GridLayout):
    pass

class OctoLauncher(Button):
    pass

class OctoApp(App):
    def build(self):
        self.settings_cls = SettingsWithSidebar
        octo = Octo()
        octo.addServers()
        self.octo = octo
        return octo

    def open_connection(self,val):
        self.octo.add_connection(val)
        


if __name__ == '__main__':
    OctoApp().run()
