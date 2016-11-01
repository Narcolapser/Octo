from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.treeview import TreeView, TreeViewNode, TreeViewLabel
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
    get_parents = "select parent from logs where line like '%org.hibernate.SQL%'"
    get_exclusive_parents = "select parent from logs where line like '%org.hibernate.SQL%' and parent not in ({0})"
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
        self.query_nodes = {}
        self.updating = False
        self.parents = []
        
        Clock.schedule_interval(self.update,1)

    def update(self, *args):

        #this makes sure only one update process is running at a time.
        if self.updating == True:
            return
        self.updating = True

        #Get the list of parents into a string form.
        p_list = ','.join([str(i) for i in self.parents])

        #query for the queries we don't already have
        parents = self.logFile.query(self.get_exclusive_parents.format(p_list))

        #save those to the raw parents list. May get ride of this later.
        self.parents_raw = parents

        #Process the new queries:
        for p in parents:
            self.parents.append(p[0])
            self.process_query(p[0])

        self.updating = False


    def process_query(self,parent):
        query_raw = self.logFile.query(self.parent_query.format(parent))
        query = ''
        #for i in query_raw[1:]:
        #    query += '\n' + i[2]
        query = '\n'.join([i[2] for i in query_raw[1:]])

        query = self.clean_query(query)
        q_hash = hash(query)
        if q_hash not in self.query_list_hashes:
            self.query_list_hashes.append(q_hash)
            self.query_list.append(query)

            node = self.query_tree.add_node(TreeViewLabel(text=self.get_from(query)))
            self.query_nodes[q_hash] = node
            self.query_tree.add_node(TreeViewLabel(text=query),node)
        
    def clean_query(self,query):
        '''
        This method translates the portal queries into quries that can be directly run on our
        ms sql servers. Or at least it will. Right now it's just a place holder.
        '''
        return query

    def get_from(self,query):
        '''
        I mostly made this to get a snippet to make the query preview short.
        '''
        q_split = query.split('\n')
        for i,j in enumerate(q_split):
            if "from" in j:
                return q_split[0] + " " + j + " " + q_split[i+1] + "..."
            elif "update" in j:
                return j + " " + q_split[i+1] + "..."
        return q_split[1]

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
    query_tree: qt
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
        TreeView:
            id: qt
            height: self.minimum_height
            size_hint_y: None
            

<SQL_Query>:
    
    
        
'''

Builder.load_string(kv)
