from .data import factory
from kivy.event import EventDispatcher
from kivy.properties import AliasProperty, BooleanProperty, NumericProperty, ObjectProperty
from kivy.uix.widget import Widget
from kivy.uix.textinput import TextInput

from os.path import join
from kivy.lang import Builder


def load_kv(*args):
  Builder.load_file(join(*args))




class Interactive(EventDispatcher):

  is_active = BooleanProperty(False)
  
  
  def __init__(self, **kwargs):
    super().__init__(**kwargs)


  def on_active(self, app):
    pass

  def on_inactive(self, app):
    pass




class DataWidget(Widget):

  model = ObjectProperty(None, rebind=True, allownone=True)


  def __init__(self, **kwargs):
    super().__init__(**kwargs)


  def init(self, **kwargs):
    for k, v in kwargs.items():
      setattr(self, k, v)
    return self


  def reset(self):
    self.is_selected = False
    self.model = self.property('model').defaultvalue
    return self




class DataView(Widget):

  def _get_data(self):
    return self._data

  def _set_data(self, data):
    if self._data:
      self._unbind_data()
    self._data = data
    self._bind_data()
    self._on_refresh(data)


  collection = AliasProperty(_get_data, _set_data, bind=[])
  data_widget = ObjectProperty(None)


  def __init__(self, **kwargs):
    self._data = None
    super().__init__(**kwargs)
    self.factory = factory
    self._bound_uids = []
    self.__class__.data_widget = self.__class__.data_widget.__name__


    
  def __del__(self):
    try:
      self._unbind_data()
    except IndexError:
      pass



  def _bind_data(self):
    append_uid = self._bound_uids.append
    fbind = self.collection.fbind
    append_uid(fbind('on_insert', self._on_insert))
    append_uid(fbind('on_refresh', self._on_refresh))
    append_uid(fbind('on_remove', self._on_remove))
    append_uid(fbind('on_set', self._on_set))
    append_uid(fbind('on_swap', self._on_swap))



  def _unbind_data(self):
    uids = self._bound_uids
    unbind_uid = self.collection.unbind_uid
    unbind_uid('on_swap', uids.pop())
    unbind_uid('on_set', uids.pop())
    unbind_uid('on_remove', uids.pop())
    unbind_uid('on_refresh', uids.pop())
    unbind_uid('on_insert', uids.pop())



  def _on_insert(self, data, i, model):
    widget = self.factory.make(self.data_widget, model=model)
    self.add_widget(widget, i)
    # print('insert:', i)
    # self.add_widget(widget)



  def _on_refresh(self, data):
    widget_class = self.data_widget
    make, recycle = self.factory.make, self.factory.recycle
    add, remove = self.add_widget, self.remove_widget

    for widget in self.children:
      remove(widget)
      recycle(widget)

    for model in data:
      add(make(widget_class, model=model))



  def _on_remove(self, data, i):
    widget = self.children[i]
    self.remove_widget(widget)
    self.factory.recycle(widget)



  def _on_set(self, data, i, model):
    widget = self.factory.make(self.data_widget, model=model)
    old_widget = self.children[i]
    self.children[i] = widget
    self.factory.recycle(old_widget)



  def _on_swap(self, data, a, b):
    children = self.children
    children[a], children[b] = children[b], children[a]




class Walker(EventDispatcher):
  
  def _get_current(self):
    try:
      return self._list[self.index]
    except IndexError:
      self.index = len(self._list) - 1
      if self.index > -1:
        return self._list[self.index]
    return None
        

  def _set_current(self, current):
    _index = self._list.index(current)
    self.index = _index
    return True


  def _get_list(self):
    return self._list

  def _set_list(self, list):
    self.index = 0
    self._list = list
    return True


  index = NumericProperty(0)
  current = AliasProperty(_get_current, _set_current, bind=['index'])
  list = AliasProperty(_get_list, _set_list, bind=[])


  def __init__(self, **kwargs):
    self._list = []
    super().__init__(**kwargs)


  def inc(self):
    _len = len(self._list)
    if self.index < _len - 1:
      self.index += 1

    return self.current


  def dec(self):
    if self.index > 0:
      self.index -= 1
  
    return self.current




class SelectorProperty(AliasProperty):
  
  def _get_selected(self, p):
    return self._selected

  def _set_selected(self, p, v):
    if self._selected:
      self._selected.is_selected = False

    if v:
      v.is_selected = True
    
    self._selected = v
    return True


  def __init__(self, v=None):
    super().__init__(self._get_selected, self._set_selected, bind=[])
    self._selected = v
    if v:
      v.is_selected = True




class Selection():

  def filter(self, fn):
    models = self.models
    self.models = {}

    for _id, model in models.items():
      if fn(model):
        self.models[model._id] = model

