from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.lang import Builder
from kivy.properties import ObjectProperty, StringProperty, BooleanProperty

import model

class Logback_Panel(ScrollView):
    grid = ObjectProperty(None)
    
    def setServer(self,server):
        self.server = server
        self.logback = model.LogbackFile(server.con)
        self.load()

    def load(self):
        loggers = self.logback.getLoggers()
        for i in loggers:
            l = Logback_Logger()
            l.load_logger(i)
            self.grid.add_widget(l)

class Logback_Logger(GridLayout):
    name = StringProperty('Loading...')
    active = BooleanProperty(False)
    level = StringProperty('Loading...')

    def load_logger(self,logger):
        self.logger = logger
        self.name = logger.name
        if logger.commented:
            self.active = False
        else:
            self.active = True
        self.level = logger.level

    def deactivate(self,val):
        pass
        

#Builder.load_file('./logback_panel.kv')

kv = '''
<Logback_Panel>:
    grid: log_grid
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

    GridLayout:
        id: log_grid
        cols: 1
        size_hint_y:None
        height: self.minimum_height

<Logback_Logger>:
    
    cols:3
    height: 50
    size_hint_y: None
    Label:
        text_size: self.width, None
        text: root.name
    Switch:
        id: activity_switch
        active: root.active
    Label:
        text: root.level
        
'''

Builder.load_string(kv)

