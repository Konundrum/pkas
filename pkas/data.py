from kivy.event import EventDispatcher
from kivy.properties import BooleanProperty, ObjectProperty, StringProperty
from .factory import factory


class DataModel(EventDispatcher):
  is_selected = BooleanProperty(False)


  def __init__(self, **kwargs):
    super().__init__(self, **kwargs)
    self.register_event_type('on_change')


  def __setattr__(self, k, v):
    # if self[k] != v:
    self.dispatch('on_change', self)
    super().__setattr__(k, v)


  def to_obj(self):
    obj = {}
    obj['_class'] = self.__class__.__name__
    obj['_id'] = self._id
    for key in self.properties():
        obj[key] = self[key]

    return obj


  def on_change(self, v):
    pass


  def apply(self, **kwargs):
    for k, v in kwargs.items():
      setattr(self, k, v)

    return self



  def reset(self):
    self._id = None

    props = self.properties()
    for key in props:
      setattr(self, key, props[key].defaultvalue)
      
    return self





from random import random


# Shouldn't be a dict, should own a dict..?
class DataContext(EventDispatcher, dict):

  is_selected = BooleanProperty(False)
  name = StringProperty('')
  store = ObjectProperty(None)


  def __init__(self):
    super().__init__()
    self.factory = factory
    self.clear_changes()
    self._uids = {}


  def clear_changes(self):
    self.changed = {}
    self.deleted = {}



  def load(self):
    factory = self.factory
    store = self.store
    
    my_callback = lambda store, key, result: print('filemanager: loaded object', store, key, result)

    for key in store:
      store_obj = store.get(key, callback=my_callback)
      class_name = store_obj.pop['_class']
      self.put(factory.make(class_name, **store_obj))
      
    print('filemanager: loaded file')




  def save(self):
    delete = self.store.delete
    put = self.store.put
    recycle = self.factory.recycle

    for _id, obj in self.deleted:
      delete(_id)
      recycle(obj)

    for _id, model in self.changed:
      for prop in model:
        put(_id, **model.to_obj())

    self.clear_changes()



  def delete(self, _id):
    model = self.deleted[_id] = self[_id]
    del self[_id]

    model.unbind_uid('on_change', self._uids[_id])
    del self._uids[_id]

    try:
      del self.changed[_id]
    except KeyError:
      pass




  def _get_id(self):
    for i in range(2):
      _id = str(random())
      try:
        self[_id]
      except KeyError:
        return _id
    
    raise Exception('couldnt create _id after 2 tries.')



  def register_change(self, model):
    self.changed[model._id]


  def put(self, model):
    try:
      _id = model._id
    except AttributeError:
      model._id = _id = self._get_id()

    self._uids[_id] = model.fbind('on_change', self.register_change)
    super().__setitem__(_id, model)
    self.changed[_id] = model



