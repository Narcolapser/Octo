from kivy.uix.gridlayout import GridLayout
from kivy.lang import Builder
from kivy.properties import ObjectProperty, StringProperty

import model

class Logback_Panel(GridLayout):
    
    def setServer(self,server):
        self.server = server
        self.logback = model.LogbackFile(server.con)
        self.load()

    def load(self):
        loggers = self.logback.getLoggers()
        for i in loggers:
            l = Logback_Logger()
            l.load_logger(i)
            self.add_widget(l)

class Logback_Logger(GridLayout):
    name = StringProperty('Loading...')
    active = StringProperty('Loading...')
    level = StringProperty('Loading...')

    def load_logger(self,logger):
        self.logger = logger
        self.name = logger.name
        if logger.commented:
            self.active = 'inactive'
        else:
            self.active = 'active'
        self.level = logger.level
        

#Builder.load_file('./logback_panel.kv')

kv = '''
<Logback_Panel>:
    canvas:
        Color:
            rgba: 0.5,0.5,0.5,0.7
        Rectangle:
            size: self.size
            pos: self.pos
        Color:
            rgba: 0.2,0.2,0.2,0.7
        Rectangle:
            size: self.size[0] - 20, self.size[1] - 20
            pos: self.pos[0] + 10, self.pos[1] + 10
    cols:1
    size_hint_y:None
    row_default_height: 50
    Logback_Logger:

<Logback_Logger>:
    cols:3
    Label:
        text: root.name
    Label:
        text: root.active
    Label:
        text: root.level
        
'''

Builder.load_string(kv)

