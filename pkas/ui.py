from .data import factory
from kivy.event import EventDispatcher
from kivy.properties import AliasProperty, BooleanProperty, ObjectProperty
from kivy.uix.widget import Widget
from kivy.uix.layout import Layout

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




class DataView(Layout):

  def _get_data(self):
    return self._data

  def _set_data(self, data):
    if self._data:
      self._unbind_data()
    self._data = data
    self._bind_data()
    self._on_refresh(data)


  def _get_cls(self):
    return self._cls.__name__

  def _set_cls(self, cls):
    self._cls = cls


  cls = AliasProperty(_get_cls, _set_cls, bind=[])
  data = AliasProperty(_get_data, _set_data, bind=[])


  def __init__(self, **kwargs):
    self._bound_uids = []
    self._data = None
    self._factory = factory
    super().__init__(**kwargs)


    
  def __del__(self):
    try:
      self._unbind_data()
    except IndexError:
      pass



  def _bind_data(self):
    append_uid = self._bound_uids.append
    fbind = self.data.fbind
    append_uid(fbind('on_insert', self._on_insert))
    append_uid(fbind('on_refresh', self._on_refresh))
    append_uid(fbind('on_remove', self._on_remove))
    append_uid(fbind('on_set', self._on_set))
    append_uid(fbind('on_swap', self._on_swap))



  def _unbind_data(self):
    uids = self._bound_uids
    unbind_uid = self.data.unbind_uid
    unbind_uid('on_swap', uids.pop())
    unbind_uid('on_set', uids.pop())
    unbind_uid('on_remove', uids.pop())
    unbind_uid('on_refresh', uids.pop())
    unbind_uid('on_insert', uids.pop())



  def _on_insert(self, data, i, model):
    widget = self._factory.make(self.cls, model=model)
    self.add_widget(widget, i)



  def _on_refresh(self, data):
    cls = self.cls
    make, recycle = self._factory.make, self._factory.recycle
    add, remove = self.add_widget, self.remove_widget

    for widget in self.children:
      remove(widget)
      recycle(widget)

    for model in data:
      add(make(cls, model=model))



  def _on_remove(self, data, i):
    widget = self.children[i]
    self.remove_widget(widget)
    self._factory.recycle(widget)



  # set only overwrites.
  def _on_set(self, data, i, model):
    factory = self._factory
    old_widget = self.children[i]
    self.remove_widget(old_widget)
    factory.recycle(old_widget)
    widget = factory.make(self.cls, model=model)
    self.add_widget(widget, i)



  def _on_swap(self, data, a, b):
    children = self.children
    children[a], children[b] = children[b], children[a]




class RecycleView(DataView):
  
  def __init__(self, data=None, **kwargs):
    super().__init__(**kwargs)
    self.collection = data
    self.update()


  def gen_data(self):
    pass


  def update(self):
    collection = self.collection
    data = self.data
    index = -1

    for model in self.gen_data():
      index += 1
      current = data[index]

      if current is not model:
        try:
          i = data.index(model)
          del data[i]
        except ValueError:
          pass

        data.insert(model, index)


