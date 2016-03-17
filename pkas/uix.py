from kivy.lang import Builder
from kivy.event import EventDispatcher
from kivy.properties import AliasProperty, BooleanProperty
from os.path import join


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





class Selector(EventDispatcher):

  def _get_selected(self):
    try:
      return self._widgets[self._index]
    except IndexError:
      return None


  def _set_selected(self, widget):
    index = self._widgets.index(widget)
    if index != self._index:
      self._index = index
      return True

  selected = AliasProperty(_get_selected, _set_selected, bind=[])
  

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

