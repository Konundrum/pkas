from kivy.event import EventDispatcher
from kivy.properties import BooleanProperty, ObjectProperty
from kivy.uix.widget import Widget
from .data import DataList
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



class DataView(Widget):
  data = ObjectProperty(None)
  Ctor = ObjectProperty(None)


  def __init__(self, **kwargs):
    super().__init__(**kwargs)
    self.factory = factory
    self._bound_uids = []

    # Validate data = DataDict / DataList
    # if not isinstance(data, DataList):
    #   raise TypeError('Adapter: data must be an instance of DataList')
    # if not issubclass(Ctor, DataWidget):
    #   raise TypeError('Adapter: Ctor must subclass DataWidget')

    self.bind_data()
    self.on_refresh()


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


  def on_data(self, inst, val):
    # TODO: REUSE IN PLACE
    self.on_refresh()

  def on_Ctor(self, inst, val):
    # self.on_refresh()
    pass


  def on_insert(self, i, model):
    widget = self.factory.make(self.Ctor.__name__, model=model)
    self.add_widget(widget, i)


  def on_refresh(self):
    ctor_class, data = self.Ctor.__name__, self.data
    make, recycle = self.factory.make, self.factory.recycle
    add, remove = self.add_widget, self.remove_widget

    for widget in container.children:
      remove(widget)
      recycle(widget)

    for model in data:
      add(make(ctor_class, model=model))


  def on_remove(self, i):
    widget = container.children[i]
    self.remove_widget(widget)
    self.factory.recycle(widget)



  def on_set(self, i, model):
    widget = self.factory.make(self.Ctor.__name__, model=model)
    old_widget = self.children[i]
    self.children[i] = widget
    self.factory.recycle(old_widget)


  def on_swap(self, a, b):
    children = self.children
    children[a], children[b] = children[b], children[a]

