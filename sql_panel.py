from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.treeview import TreeView, TreeViewNode
from kivy.lang import Builder
from kivy.properties import ObjectProperty, StringProperty, BooleanProperty

import model
import log_manager

class Query():
    pass

class ArgSet():
    pass

class SQL_Panel(ScrollView):
    '''
    The logback panel is used to turn logs on and off as well as adjust the error level of each one
    and the default error level.
    '''
    grid = ObjectProperty(None)
    active = BooleanProperty(False)
    def setServer(self,server):
        '''
        Save the local variables needed. Server specifically, but also this method spins up an
        instance of the Logback model to reference.
        '''
        self.server = server
        self.logback = model.LogbackFile(server.con)
        loggers = self.logback.getLoggers()
        self.loggers = []

        for i in loggers:
            if i.name == 'org.hibernate.SQL':
                self.ohsql = i
            if i.name == 'org.hibernate.type':
                self.ohtype = i

        self.active = not (self.ohsql.commented and self.ohtype.commented)

        self.load_queries()

    def load_queries(self):
##        self.logFile = model.LogFile(self.server.logdb,
##                     self.server.con,
##                     self.server.address,
##                     'portal.log')
        self.logFile = model.gstore.logManager.openLog(
            '/usr/local/tomcat/logs/portal/portal.log',self.server.con)

        

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
        self.active = self.ids['logback_switch'].active
        if self.active:
            self.ohsql.commented = False
            self.ohtype.commented = False
            self.logback.save()
        else:
            self.ohsql.commented = True
            self.ohtype.commented = True
            self.logback.save()
        return self.active

class SQL_Query(TreeViewNode):
    pass

#Select * from logs where parent in (select parent from logs where line like '%org.hibernate.SQL%')
kv = '''
<SQL_Panel>:
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
            cols: 1
            GridLayout:
                cols: 2
                Label:
                    text: 'Turn logging on?'
                Switch:
                    id: logback_switch
                    active: root.active
                    on_active: root.toggle_me()
            

<SQL_Query>:
    
    
        
'''

Builder.load_string(kv)
