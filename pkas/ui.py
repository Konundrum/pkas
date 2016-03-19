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


  data_list = AliasProperty(_get_data, _set_data, bind=[])


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
    fbind = self.data_list.fbind
    append_uid(fbind('on_insert', self._on_insert))
    append_uid(fbind('on_refresh', self._on_refresh))
    append_uid(fbind('on_remove', self._on_remove))
    append_uid(fbind('on_set', self._on_set))
    append_uid(fbind('on_swap', self._on_swap))



  def _unbind_data(self):
    uids = self._bound_uids
    unbind_uid = self.data_list.unbind_uid
    unbind_uid('on_swap', uids.pop())
    unbind_uid('on_set', uids.pop())
    unbind_uid('on_remove', uids.pop())
    unbind_uid('on_refresh', uids.pop())
    unbind_uid('on_insert', uids.pop())



  def _on_insert(self, data, i, model):
    widget = self.factory.make(self.data_widget, model=model)
    self.add_widget(widget, i)



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
  
  def _get_widget(self):
    try:
      return self._widgets[self.index]
    except IndexError:
      return None

  def _set_widget(self, widget):
    _index = self._widgets.index(widget)
    self.index = _index
    return True


  def _get_widgets(self):
    return self._widgets

  def _set_widgets(self, widgets):
    self.index = 0
    self._widgets = widgets
    return True


  index = NumericProperty(0)
  widget = AliasProperty(_get_widget, _set_widget, bind=['index'])
  widgets = AliasProperty(_get_widgets, _set_widgets, bind=[])


  def __init__(self, **kwargs):
    super().__init__(**kwargs)
    if not self._widgets:
      self._widgets = []


  def forward(self):
    if self.index < len(self._widgets) - 1:
      self.index += 1
    return self._widgets[self.index]



  def backward(self):
    if self.index > 0:
      self.index -= 1
    return self._widgets[self.index]

