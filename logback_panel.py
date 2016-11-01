from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.lang import Builder
from kivy.properties import ObjectProperty, StringProperty, BooleanProperty

import model

class Logback_Panel(ScrollView):
    '''
    The logback panel is used to turn logs on and off as well as adjust the error level of each one
    and the default error level.
    '''
    grid = ObjectProperty(None)
    def setServer(self,server):
        '''
        Save the local variables needed. Server specifically, but also this method spins up an
        instance of the Logback model to reference.
        '''
        self.server = server
        self.logback = model.LogbackFile(server.con)

        if self.logback.loaded:
            loggers = self.logback.getLoggers()
            self.loggers = []
            for i in loggers:
                l = Logback_Logger()
                l.load_logger(i)
                self.loggers.append(l)
                self.grid.add_widget(l)
        else:
            l = Label(text='Failed to load logback')
            self.grid.add_widget(l)

    def save_logback(self):
        '''
        Save the logback now that you've updated what you want.
        '''
        print("Saving log back.")
        self.logback.save()

class Logback_Logger(GridLayout):
    '''
    View class for the individual loggers. 
    '''

    name = StringProperty('Loading...')
    active = BooleanProperty(False)
    level = StringProperty('Loading...')

    def load_logger(self,logger):
        '''
        Load the logger and create it's view.
        '''
        self.logger = logger
        self.name = logger.name
        if logger.commented:
            self.active = False
        else:
            self.active = True
        self.level = logger.level

    def toggle_me(self):
        '''
        called whenever the status of the activity toggle changes. This method makes sure that the
        underlying logger get's the memo.
        '''
        self.active = self.ids['activity_switch'].active
        if self.active:
            self.logger.commented = False
        else:
            self.logger.commented = True
        return self.active
        

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
        GridLayout:
            height: 50
            size_hint_y: None
            cols: 3
            Label:
                text: 'name of logger'
            Label:
                text: 'Is logger active?'
            Label:
                text: 'Logging Level'
        Button:
            height: 50
            size_hint_y: None
            text: 'Save'
            on_press: root.save_logback()

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
        on_active: root.toggle_me()
    Label:
        text: root.level
        
'''

Builder.load_string(kv)
