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
        obj[key] = repr(self[key])

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


  def __repr__(self):
    return '[' + ''.join('{},'.format(model._id) for model in self) + ']'


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






from random import random

class DataContext(EventDispatcher):

  is_selected = BooleanProperty(False)
  name = StringProperty('')
  store = ObjectProperty(None)


  def __init__(self):
    super().__init__()
    self.factory = factory
    self._data = {}
    self._uids = {}
    self.clear_changes()


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
    model = self.deleted[_id] = self._data[_id]
    del self._data[_id]

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
    self._data[_id] = model
    self.changed[_id] = model


  def get(self, _id):
    return self._data[_id]

  def __getitem__(self, _id):
    return self._data[_id]


