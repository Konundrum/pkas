from kivy.event import EventDispatcher
from kivy.properties import BooleanProperty, ObjectProperty
from .factory import factory


class DataWidget(EventDispatcher):
  is_selected = BooleanProperty(False)
  model = ObjectProperty(None, rebind=True)

  def __init__(self, **kwargs):
    super().__init__(**kwargs)


  def reset(self):
    self.is_selected = False
    self.model = self.property(model).defaultvalue
    return self




class DataList(EventDispatcher, list):
  
  def __init__(self, **kwargs):
    super().__init__(**kwargs)
    self.register_event_type('on_insert')
    self.register_event_type('on_refresh')
    self.register_event_type('on_remove')
    self.register_event_type('on_set')
    self.register_event_type('on_swap')
  

  def on_insert(self, i, x):
    pass
  def on_refresh(self):
    pass
  def on_remove(self, x):
    pass
  def on_set(self, i, v):
    pass
  def on_swap(self, a, b):
    pass


  def __delitem__(self, i):
    super().__delitem__(i)
    self.dispatch('remove', i)
    

  def __setitem__(self, i, v):
    super().__setitem__(i, v)
    self.dispatch('set', i, v)


  def clear(self):
    super().clear()
    self.dispatch('refresh', self)

  def pop(self, i=None):
    super().pop(i)
    self.dispatch('remove', i)


  def refresh(self):
    self.dispatch('refresh', self)


  def swap(self, a, b):
    self[a], self[b] = self[b], self[a]
    self.dispatch('swap', a, b)

  def append(self, x):
    super().append(x)
    self.dispatch('insert', len(self) - 2, x)

  
  def extend(self, L):
    for x in L:
      self.append(x)


  def insert(self, i, x):
    super().insert(i, x)
    self.dispatch('insert', i, x)


  def remove(self, x):
    i = self.index(x)
    super().remove(x)
    self.dispatch('remove', i)


  def sort(self, cmp=None, key=None, reverse=False):
    super().sort(cmp, key, reverse)
    self.dispatch('refresh', self)


  def reverse(self):
    super().reverse()
    self.dispatch('refresh', self)





class DataAdapter(EventDispatcher):
  container = ObjectProperty(None)
  data = ObjectProperty(None)
  Ctor = ObjectProperty(None)


  def __init__(self, **kwargs):
    super().__init__(**kwargs)
    self.factory = factory
    self._binds = []

    # Validate data = DataDict / DataList
    if not isinstance(data, DataList):
      raise TypeError('Adapter: data must be an instance of DataList')

    if not issubclass(Ctor, DataWidget):
      raise TypeError('Adapter: Ctor must subclass DataWidget')

    self.bind()
    self.on_refresh()


  def bind(self):
    append = self._binds.append
    fbind = self.data.fbind
    append(fbind('on_insert', self.on_insert))
    append(fbind('on_refresh', self.on_refresh))
    append(fbind('on_remove', self.on_remove))
    append(fbind('on_set', self.on_set))
    append(fbind('on_swap', self.on_swap))


  def unbind(self):
    binds = self._binds
    unbind = self.data.unbind_uid
    unbind('on_swap', binds.pop())
    unbind('on_set', binds.pop())
    unbind('on_remove', binds.pop())
    unbind('on_refresh', binds.pop())
    unbind('on_insert', binds.pop())


  def on_container(self, inst, val):
    self.on_refresh()

  def on_data(self, inst, val):
    # TODO: REUSE IN PLACE
    self.on_refresh()

  def on_Ctor(self, inst, val):
    self.on_refresh()


  def on_insert(self, i, model):
    widget = self.factory.make(self.Ctor.__name__, model=model)
    self.container.add_widget(widget, i)


  def on_refresh(self):
    ctor_class = self.Ctor.__name__
    data = self.data
    container = self.container
    factory = self.factory

    for widget in container.children:
      container.remove_widget(widget)
      factory.recycle(widget)

    for model in data:
      container.add_widget(factory.make(ctor_class, model=model))


  def on_remove(self, i):
    container = self.container
    widget = container.children[i]
    container.remove_widget(widget)
    self.factory.recycle(widget)



  def on_set(self, i, model):
    widget = self.factory.make(self.Ctor.__name__, model=model)
    old_widget = self.container.children[i]
    self.container.children[i] = widget
    self.factory.recycle(old_widget)


  def on_swap(self, a, b):
    children = self.container.children
    children[a], children[b] = children[b], children[a]

