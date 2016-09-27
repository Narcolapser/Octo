import kivy
kivy.require('1.9.1')

from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.label import Label
from kivy.config import ConfigParser
from kivy.uix.tabbedpanel import TabbedPanel
from kivy.uix.button import Button
from kivy.uix.tabbedpanel import TabbedPanelItem
from kivy.uix.tabbedpanel import TabbedPanelHeader

#config = json.load(open("dev.config"))

#config = ConfigParser()
#config.read('dev.config')

#s = Settings()


class Octo(TabbedPanel):
    pass
        
class OctoServerTab(TabbedPanelItem):
    pass

class OctoLauncher(Button):
    pass

class OctoApp(App):
    def build(self):
        octo = Octo()
        return octo


if __name__ == '__main__':
    OctoApp().run()
