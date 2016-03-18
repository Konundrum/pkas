from .data import factory
from kivy.event import EventDispatcher
from kivy.properties import AliasProperty, BooleanProperty, ObjectProperty
from kivy.uix.widget import Widget

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

  is_selected = BooleanProperty(False)
  model = ObjectProperty(None, rebind=True, allownone=True)


  def __init__(self, **kwargs):
    super().__init__(**kwargs)



  def reset(self):
    self.is_selected = False
    self.model = self.property('model').defaultvalue
    return self




class DataView(Widget):

  def _get_data(self):
    return self._data

  def _set_data(self, data):
    if self._data:
      self.unbind_data()
    self._data = data
    self.bind_data()
    self.on_refresh(data)


  data = AliasProperty(_get_data, _set_data, bind=[])


  def __init__(self, **kwargs):
    self._data = None
    super().__init__(**kwargs)
    self.factory = factory
    self._bound_uids = []
    self.__class__.data_widget = self.__class__.data_widget.__name__


    
  def __del__(self):
    try:
      self.unbind_data()
    except IndexError:
      pass



  def bind_data(self):
    append_uid = self._bound_uids.append
    fbind = self.data.fbind
    append_uid(fbind('on_insert', self.on_insert))
    append_uid(fbind('on_refresh', self.on_refresh))
    append_uid(fbind('on_remove', self.on_remove))
    append_uid(fbind('on_set', self.on_set))
    append_uid(fbind('on_swap', self.on_swap))



  def unbind_data(self):
    uids = self._bound_uids
    unbind_uid = self.data.unbind_uid
    unbind_uid('on_swap', uids.pop())
    unbind_uid('on_set', uids.pop())
    unbind_uid('on_remove', uids.pop())
    unbind_uid('on_refresh', uids.pop())
    unbind_uid('on_insert', uids.pop())



  def on_insert(self, data, i, model):
    widget = self.factory.make(self.data_widget, model=model)
    self.add_widget(widget, i)



  def on_refresh(self, data):
    widget_class = self.data_widget
    make, recycle = self.factory.make, self.factory.recycle
    add, remove = self.add_widget, self.remove_widget

    for widget in self.children:
      remove(widget)
      recycle(widget)

    for model in data:
      add(make(widget_class, model=model))



  def on_remove(self, data, i):
    widget = self.children[i]
    self.remove_widget(widget)
    self.factory.recycle(widget)



  def on_set(self, data, i, model):
    widget = self.factory.make(self.data_widget, model=model)
    old_widget = self.children[i]
    self.children[i] = widget
    self.factory.recycle(old_widget)



  def on_swap(self, data, a, b):
    children = self.children
    children[a], children[b] = children[b], children[a]




class Walker(EventDispatcher):
  
  def _get_position(self):
    try:
      return self._widgets[self._index]
    except IndexError:
      return None

  def _set_position(self, widget):
    index = self._widgets.index(widget)
    if index != self._index:
      self._index = index


  position = AliasProperty(_get_position, _set_position, bind=[])
  


  def __init__(self, widgets, index = 0):
    super().__init__()
    self._widgets = widgets
    self._index = index



  def increment(self):
    if self._index < len(self._widgets) - 1:
      self._index += 1
    return self._widgets[self._index]



  def decrement(self):
    if self._index > 0:
      self._index -= 1
    return self._widgets[self._index]

    