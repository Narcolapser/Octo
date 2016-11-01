from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.treeview import TreeView, TreeViewNode
from kivy.lang import Builder
from kivy.properties import ObjectProperty, StringProperty, BooleanProperty
from kivy.clock import Clock

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
    query = "Select * from logs where parent in (select parent from logs where line like '%org.hibernate.SQL%') ORDER BY parent"
    get_parents = "(select parent from logs where line like '%org.hibernate.SQL%')"
    parent_query = "Select * from logs where parent is {0}"
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
        self.logFile = model.gstore.logManager.openLog(
            '/usr/local/tomcat/logs/portal/portal.log',self.server.con)

        self.query_list_hashes = []
        self.query_list = []
        self.updating = False
        Clock.schedule_interval(self.update,1)

    def update(self, *args):
        if self.updating == True:
            return
        self.updating = True
        a = self.logFile.query(self.query)
        try:
            current = a[0][4]
            print(a[0])
            query = ''
            for i in a:
                if i[4] in self.query_list:
                    continue
                if i[4] == current:
                    query += '\n' + i[2]
                else:
                    q_hash = hash(query)
                    if q_hash not in self.query_list_hashes:
                        l = Label(text=query)
                        l.size_hint_y = None
                        l.height = 400
                        self.grid.add_widget(l)
                        self.query_list.append(i[4])
                        print(self.query_list)
                    else:
                        self.query_list_hashes.append(q_hash)
                    current = i[4]
                    query = i[2]
                    
##                if hash(i[2]) not in self.query_list:
##                    print(hash(i[2]))
##                    l = Label(text=i[2])
##                    l.size_hint_y = None
##                    l.height = 20
##                    self.grid.add_widget(l)
##                    self.query_list.append(hash(i[2]))
            #print(self.query_list)
        except:
            pass
        self.updating = False

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
