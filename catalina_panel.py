from kivy.uix.scrollview import ScrollView
from kivy.lang import Builder
from kivy.properties import ObjectProperty, StringProperty
from kivy.clock import Clock

import model

class Catalina_Panel(ScrollView):
    text = StringProperty("w00t!")
    def setServer(self,server):
        self.server = server
        self.cat = model.Catalina(self.server.con)
        #print(type(self.cat.start))
        #self.text = str(self.cat.start)
        self.text = self.cat.content
        Clock.schedule_interval(self.update,1)

    def update(self, *args):
        at_bottom = self.scroll_y < 0.01
        self.text = self.cat.update()
        if at_bottom:
            self.scroll_y = 0
            self.update_from_scroll()

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
    Label:
        text: root.text
        pos: 10,10
        text_size: self.width-20, None
        size_hint_y: None
        height: self.texture_size[1]
        
'''

Builder.load_string(kv)

