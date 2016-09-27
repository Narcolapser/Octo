import kivy
kivy.require('1.9.1')

from kivy.app import App
from kivy.config import ConfigParser

from kivy.properties import ObjectProperty

from kivy.uix.widget import Widget
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.settings import SettingsWithSidebar

from kivy.uix.floatlayout import FloatLayout

from kivy.uix.tabbedpanel import TabbedPanel
from kivy.uix.tabbedpanel import TabbedPanelItem
from kivy.uix.tabbedpanel import TabbedPanelHeader

import json

#config = json.load(open("dev.config"))
hosts = json.load(open("hosts.ini"))

#config = Config()
#config.read('octo.ini')
#Config.set('graphics', 'width', '1000')
#Config.set('graphics', 'height', '600')

#s = Settings()


class Octo(TabbedPanel):
    serverTab = ObjectProperty(None)
    
    def addServers(self):
        self.serverTab.text = "Servers"
        self.serverTab.addServers()

    def add_connection(self,val):
        tp = OctoServer()
        tp.text = val['name']
        tp.load_panels()
        self.add_widget(tp)
        self.switch_to(tp)
        
        
class OctoServerTab(TabbedPanelItem):
    grid = ObjectProperty(None)

    def addServers(self):
        for host in hosts:
            o = OctoLauncher()
            o.text = host
            o.config = hosts[host]
            self.grid.add_widget(o)

class OctoServer(TabbedPanelItem):
    option_panel = ObjectProperty(None)
    info_panel = ObjectProperty(None)
    cur_panel = ObjectProperty(None)
    panels = []
    
    def load_panels(self):
        o = OctoDisplay()
        self.option_panel.add_widget(o.get_button(self))
        self.panels.append(o)

    def swap_info(self,new_panel):
        if self.cur_panel == new_panel: return
        try:
            self.info_panel.remove_widget(self.cur_panel)
        except:
            pass
        self.info_panel.add_widget(new_panel)
        self.cur_panel = new_panel

class OctoDisplay():
    def get_button(self,main):
        self.main = main
        if not hasattr(self,'button'):
            self.button = Button()
            self.button.text = 'Info'
            self.button.height = 50
            self.button.width = 100
            self.button.size_hint_y = None
            self.button.bind(on_release=self.callback)
        return self.button

    def callback(self,val):
        self.main.swap_info(self)

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
