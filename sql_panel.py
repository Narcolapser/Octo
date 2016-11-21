from threading import Thread, Lock

from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.treeview import TreeView, TreeViewNode, TreeViewLabel
from kivy.lang import Builder
from kivy.properties import ObjectProperty, StringProperty, BooleanProperty
from kivy.clock import Clock
from kivy.core.clipboard import Clipboard
from kivy.logger import Logger

import model
import log_manager

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
        self.bind(on_touch_down=self.on_touch_down)

    def load_queries(self):
        self.logFile = model.gstore.logManager.openLog(
            '/usr/local/tomcat/logs/portal/portal.log',self.server.con)

        self.query_list_hashes = []
        self.query_list = {}
        self.query_nodes = {}
        self.updating = Lock()
        self.parents = []
        
        Clock.schedule_interval(self.thread_update,1)

    def thread_update(self,*args):
        Logger.debug("SQL Panel: Is there a running updater thread? {0}".format(self.updating.locked()))
        if self.updating.locked() == False:
            Logger.debug("SQL Panel: Preparing a new thread")
            t = Thread(target=self.update,args=args)
            t.start()
            Logger.debug("SQL Panel: Dispached thread")
        Logger.debug("SQL Panel: Done checking the updater.")
        

    def update(self, *args):
        #this makes sure only one update process is running at a time.
        Logger.debug("SQL Panel: Is an update process alread running?: {0}".format(self.updating.locked()))
        if self.updating.acquire(False) == False:
            Logger.debug("SQL Panel: Lock not acquired: {0}".format(self.updating.locked()))
            return
        Logger.debug("SQL Panel: Acquired lock:".format(self.updating.locked()))
        
        #Get the list of parents into a string form.
        p_list = ','.join([str(i) for i in self.parents])

        #query for the queries we don't already have
        parents = self.logFile.query(self.get_exclusive_parents.format(p_list))

        #save those to the raw parents list. May get ride of this later.
        self.parents_raw = parents

        #Process the new queries:
        for p in parents:
            self.parents.append(p[0])
            qhash, query = self.process_query(p[0])
            
            if qhash in self.query_list_hashes:
                #self.query_list[qhash].ids.append(p[0])
                self.query_list[qhash].add_instance(p[0])
                
            else:
                self.query_list_hashes.append(qhash)
                self.query_list[qhash] = SQL_Query(qhash,query,p[0],self)

        self.updating.release()
        Logger.debug("SQL Panel: Done updating, toggling self.update to: {0}".format(self.updating.locked()))

    def process_query(self,parent):
        '''
        Take the given number, find all the parts of the query, and then string them together into
        one piece. This also returns the hash for that query to make use in dictionaries easier.
        '''
        query_raw = self.logFile.query(self.parent_query.format(parent))
        query = ''
        query = '\n'.join([i[2] for i in query_raw[1:]])

        q_hash = hash(query)
        return (q_hash,query)

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
            elif "into" in j:
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

    def on_touch_down(self, touch):
        if touch.is_double_tap:
            try:
                Clipboard.copy(self.query_tree.selected_node.text)
            except AttributeError:
                Logger.debug("SQL Panel: Object didn't have text.")
        ScrollView.on_touch_down(self, touch)


class SQL_Query():
    parent_query = "Select * from logs where parent is {0}"
    args = "SELECT * FROM logs WHERE ID = {0}"
    def __init__(self,qhash,query,qid,parent):
        self.qhash = qhash
        self.query = query
        self.ids = [qid]
        self.parent = parent
        
        node = parent.query_tree.add_node(TreeViewLabel(text=parent.get_from(query)))
        parent.query_nodes[qhash] = node
        parent.query_tree.add_node(TreeViewLabel(text=query),node)
        self.instances = {}

    def add_instance(self,qid):
        '''
        Adds an instance of a particular query. This way we can see not only the queries but also
        the values and results they run with. Doing this in a tree view keeps it compact.
        '''
        #Save the query id.
        self.ids.append(qid)
        #set a session id, this will be used to find parameters and results.
        sid = qid + 1
        #Get past the query.
        res = self.parent.logFile.query(self.args.format(sid))

        try:
            while res[0][3] != 0: #when res[0][3] = 0 we will be at log entries that are "TRACE"
                sid += 1
                res = self.parent.logFile.query(self.args.format(sid))
        except IndexError:
            Logger.debug("SQL Panel: List didn't contain appropriate number of entries: {0}".format(res))
            return

        #necessary temp bits
        rows = []
        parameters = []
        results = {}

        #these time stamps that show up along side parameters and results. 
        time_stamps = ('TIME_ID1_21_','TD_FIVE_2_21_','TD_HOUR3_21_','TD_MINUT4_21_','TD_TIME5_21_')
        while len(res) > 0 and res[0][3] == 0:
            sid += 1
            #in order to ignore those time stamps we must check to see if this entry is one.
            is_time_stamp = False
            for ts in time_stamps:
                #this establishes whether or not it is a time stamp
                is_time_stamp |= ts in res[0][2]
            if is_time_stamp:
                #if it is a time stamp, get the next query and continue.
                res = self.parent.logFile.query(self.args.format(sid))
                #I might be able to make thie a break in the future. I'm pretty sure time stamps
                # won't happen until after the parameters and results are past.
                continue

            #potentially un-needed now.
            rows.append(res)

            #Find the paramaters for this query
            if "BasicBinder" in res[0][2]:
                #get the paramater number
                pnum = 0
                start = res[0][2].find("binding parameter [") + len('binding parameter [')
                end = res[0][2].find('] as [',start)
                pnum = int(res[0][2][start:end])

                #get paramater value:
                pval = ''
                start = res[0][2].find('] - ') + len('] - ')
                pval = res[0][2][start:]
                parameters.append((pnum,pval))

            #Find the results of this query
            if "BasicExtractor" in res[0][2]:
                #Get the value:
                rval = ''
                start = res[0][2].find("Found [") + len('Found [')
                end = res[0][2].find('] as column [')
                rval = res[0][2][start:end]

                #Get the Column:
                rcol = ''
                start = res[0][2].find('] as column [') + len('] as column [')
                rcol = res[0][2][start:-1]

                if rcol in results.keys():
                    results[rcol].append(rval)
                else:
                    results[rcol] = [rval]
                
            #get the next entry.
            res = self.parent.logFile.query(self.args.format(sid))

            #end while loop.
        #save the query in a convenient class wrapper.
        self.instances[qid] = Query(parameters,results)
        #insert the new instance into the treeview.
        self.parent.query_tree.add_node(TreeViewLabel(
            text=str(self.instances[qid])),
            self.parent.query_nodes[self.qhash])

class Query():
    def __init__(self,parameters,results):
        self.parameters = parameters
        self.results = results

    def __str__(self):
        ret = ''
        #format the paramaters
        ret += 'Quried with paramaters:\n'
        for p in self.parameters:
            ret += p[1] + '\n'


        #format the results
        ret += 'Returned the values:\n'

        #This is basically a translation. The data is currently a list under a column name. This
        # for loop translates it into a list of rows, each with it's own list of column names.
        rows = []
        for i in self.results.keys():
            for n,j in enumerate(self.results[i]):
                if len(rows) < n + 1:
                    rows.append({i:j})
                else:
                    rows[n][i] = j

        #print out the column heads.
        for i in self.results.keys():
            ret += i + '        '
        ret += '\n'

        #print out the row values. Hopefully these match the column heads...
        for i in self.results.keys():
            for j in rows:
                try:
                    ret += j[i] + '        '
                except KeyError:
                    Logger.debug("SQL Panel: Didn't find: {0} in {1}".format(i,j))

        #for good measure
        ret += '\n'
        
        return ret
        
        
     


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
