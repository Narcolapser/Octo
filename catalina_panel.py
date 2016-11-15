from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.lang import Builder
from kivy.properties import ObjectProperty, StringProperty, NumericProperty
from kivy.clock import Clock

import model

#Todo: When the content is first loaded, I don't think all the data get's pulled, something is a
#bit off there. So this needs to be updated yet to get the log up to the end on the first pass.

class Catalina_Panel(ScrollView):
    '''
    This is a simple panel that just displays the catalina output. Quick and handy to see what is
    going on for each server.
    '''
    text = StringProperty("")
    g_width = NumericProperty(750)
    def setServer(self,server):
        '''
        Set the server object for this catalina object.
        '''
        self.server = server
        self.cat = model.Catalina(self.server.con)
        self.text = self.cat.content
        self.lines = []
        self.cl = []

        #check for new content once a second.
        Clock.schedule_interval(self.update,1)

    def update(self, *args):
        '''
        See if there is new text. If the user left the panel at the bottom of the log, then
        automatically scroll the window to keep it at the bottom. If the user has scrolled else
        where, then don't automatically scroll them down.
        '''
        at_bottom = self.scroll_y < 0.01
        self.g_width = self.ids['content_grid'].size[0]
        if at_bottom:
            self.scroll_y = 0
            self.update_from_scroll()
        
        self.text = self.cat.update()
        for line in self.text.split('\n')[:-1]:
            if hash(line) in self.lines:
                continue
            l = ContentLabel(text=line)
            l.g_width = self.g_width
            
            self.ids['content_grid'].add_widget(l)
            self.cl.append(l)
            self.lines.append(hash(line))

        for l in self.cl:
            l.g_width = self.ids['content_grid'].size[0]


class ContentLabel(Label):
    g_width = NumericProperty(750)

#height: self.texture_size[1]
kv = '''
<Catalina_Panel>:
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
        cols: 1
        id: content_grid
        pos: 10,10
        size_hint_y: None
        height: self.minimum_height

<ContentLabel>:
    text_size: self.g_width,None
    halign: 'left'
    size_hint_y: None
    
'''

Builder.load_string(kv)

