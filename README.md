# PKAS  
### Personal Kivy Application System  

Adds additional frameworking to kivy for use with PCs. This module provides a data and ui abstraction layer on top of kivy. The module supports three primary features: Recycling of DataModels and DataWidgets, views for displaying DataCollections, and a control system which delegates to Interactive widgets.  
  
### Contents:  
---
```  
class Factory(object):  
factory = Factory() # Singleton  
def specify(Ctor, stack_length=STACK_LEN):  
  
class DataModel(EventDispatcher):  
class DataCollection(DataModel):  
class DataList(DataCollection, UserList):  
class DataDict(DataCollection, UserDict):  
class DataContext(DataDict):  
  
class DataProperty(ObjectProperty):  
class SelectorProperty(DataProperty):  
class DataWidget(Widget):  
  
class CollectionProperty(ObjectProperty):  
class DataView(Layout):  
class RecyclerProperty(CollectionProperty):  
class RecyclerView(DataView):  
  
class Interactive(EventDispatcher):  
class ActiveProperty(ObjectProperty):  
class Controller(Widget):  
class PKApp(App):  
  
class Walker(EventDispatcher):  
def load_kv(*args):  
```  
  
  
Objects are recycled by implementing methods:  
```  
def recycle(self):  
def reinit(self, **kwargs):  
```  
  
DataCollections are DataModels with an event list that defines a protocol
used to keep the DataCollection in sync with a DataView.  
```  
class DataCollection(DataModel):  
  events = ['on_evt', ...]  
```  

DataViews automatically bind to all events assigned to a CollectionProperty  
```  
class DataView(Layout):  
  data = CollectionProperty()  
```  
    
  
Active Properties call active / inactive methods on InteractiveWidgets:
```
def on_active(self, controller):
def on_inactive(self, controller):
```

Selector Properties select / deleselect models:  
```  
is_selected = BooleanProperty(False)  
```  
  
