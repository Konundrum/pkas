#PKAS

Personal Kivy Application System


Adds additional frameworking to kivy for use with PCs.

This module provides a data and ui abstraction layer on top of kivy.
The module supports three primary features: Recycling of DataModels and
DataWidgets, views for displaying DataCollections, and a control system
which delegates to Interactive widgets.

Contents:


Data:

class Factory(object):
    def make(self, cls, *args, **kwargs):
    def recycle(self, obj):
    def set_stack_length(self, cls, length):
    def specify(self, Ctor, length):

class DataModel(EventDispatcher):
    is_selected = BooleanProperty(False)
    def recycle(self):
    def reinit(self, _id=None, **kwargs):
    def load(self, context):
    def to_json(self):


Collections:

class DataCollection(DataModel):
    events = ['on_del','on_set','on_clear','on_insert','on_update','on_swap']
    def recycle(self):
    def reinit(self, data=None, *args, **kwargs):
    def swap(self, a, b):
    def load(self, context):
    def to_json(self):

class DataList(DataCollection, UserList):
class DataDict(DataCollection, UserDict):
class DataContext(DataDict):
    name = StringProperty('default')
    filename = StringProperty('')
    def save(self):
    def load(self):


Model Properties:

class DataProperty(ObjectProperty):
class SelectorProperty(DataProperty):


Collection Properties:

class CollectionProperty(ObjectProperty):
class RecyclerProperty(CollectionProperty):


Data Widgets:

class DataWidget(Widget):
    def recycle(self):
    def reinit(self, **kwargs):

class DataView(Layout):
    data = CollectionProperty()
    cls = AliasProperty()
    def recycle(self):
    def reinit(self, **kwargs):

class RecyclerView(DataView):
    def gen_data(self):
    displayed = CollectionProperty()
    data = RecyclerProperty(displayed, gen_data)


Input related:

class Interactive(EventDispatcher):
    is_active = BooleanProperty(False)
    def on_active(self, controller):
    def on_inactive(self, controller):

class ActiveProperty(ObjectProperty):

class Controller(Widget):
    root = ActiveProperty()
    page = ActiveProperty()
    region = ActiveProperty()
    focus = ActiveProperty()

class PKApp(App):


Utils:

class Walker(EventDispatcher):
    index = AliasProperty()
    current = AliasProperty()
    data = ObjectProperty(None)
    def inc(self):
    def dec(self):


