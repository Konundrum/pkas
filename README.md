## PKAS  
### Personal Kivy Application System  

Adds additional frameworking to kivy for use with PCs. This module provides 
a data and ui abstraction layer on top of kivy. The module supports recycling 
of DataModels and DataWidgets, file saving and loading, views for displaying 
DataCollections, and a control system which delegates to commands mapped by 
keybinds to Interactive Widgets.  
  
#### Contents:  
---
```  
class Factory(object):  
factory = Factory() # Singleton  
def specify(Ctor, stack_length=STACK_LEN):  
  
class DataModel(EventDispatcher):  
class DataCollection(DataModel):  
class DataList(DataCollection, UserList):  
class DataDict(DataCollection, UserDict):  
class FileContext(DataDict):  
  
class DataProperty(ObjectProperty):  
class SelectorProperty(DataProperty):  
class DataWidget(Widget):  
  
class CollectionProperty(ObjectProperty):  
class DataView(Layout):  
class RecyclerProperty(CollectionProperty):  
class RecyclerView(DataView):  
class ListView(DataView, BoxLayout):  
  
class Interactive(EventDispatcher):  
class ActiveProperty(ObjectProperty):  
class Controller(Widget):  
class PKApp(App):  
  
class Walker(EventDispatcher):  
def load_kv(*args):  
```  
  
  
The factory is a singleton used to make and recycle objects. Objects can 
be specified for production by decorating with @specify
Objects are recyclable by implementing methods recycle() and reinit(**kw)  
```  
factory = Factory() # Singleton  
  
@specify  
class MyDataModel(DataModel):  
  def recycle(self):  
    ...  
  def reinit(self, **kwargs):  
    ...  
```  
  
DataCollections are DataModels with an event list that defines a protocol
used to keep the DataCollection in sync with a DataView:  
```  
class DataCollection(DataModel):  
    events = ['on_evt', ...]  
```  

CollectionProperties automatically bind all events to their host:  
```  
class DataView(Layout):  
    data = CollectionProperty()  
```  
  
RecyclerProperties keep a target CollectionProperty in sync with the 
objects yielded by a generator function:  
```  
class RecyclerView(DataView):  
    def gen_data(self):  
      ...  
    displayed = CollectionProperty()  
    data = RecyclerProperty(displayed, gen_data)  
  
```  

Active Properties call active / inactive methods on InteractiveWidgets:
```  
class ActiveWidget(Interactive, Widget):  
    def on_active(self, controller):  
      ...  
    def on_inactive(self, controller):  
      ...  
```  
  
The Controller maintains 4 such properties, to which it delegates 
commands defined in {app}.ini, in addition to a file property.  
```  
class Controller(Widget):  
    file = ObjectProperty()  
    root = ActiveProperty()  
    page = ActiveProperty()  
    region = ActiveProperty()  
    focus = ActiveProperty()  
  
  
in {app}.ini:  
  
[keybinds]  
right = "right"  
down = ["s", "down"]  
close_tab = "ctrl w"  

in view.py:  
  
class MyView(RecyclerView, BoxLayout):  
    def on_right(self, controller):  
      ...  
    def on_down(self, controller):  
      ...  
    def on_close_tab(self, controller):  
      ...  
  
  
controller.focus = myview_instance  
  
  
```
  