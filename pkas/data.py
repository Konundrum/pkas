from collections import defaultdict
from kivy.event import EventDispatcher
from kivy.properties import BooleanProperty, ObjectProperty, StringProperty


QUEUE_LEN = 10




class Factory(object):

  # Singleton reference
  _inst = None



  def __init__(self):
    super().__init__()
    self._ctors = {}
    self._recycled = defaultdict(list)
    self._queue_lengths = {}



  def __new__(cls):
    if not cls._inst:
      cls._inst = super().__new__(cls)

    return cls._inst



  def make(self, class_name, *args, **kwargs):
    try:
      Ctor = self._ctors[class_name]
    except KeyError:
      raise Exception('factory.make:', name,'not specified.')

    try:
      return self._recycled[class_name].pop().init(*args, **kwargs)
    except IndexError:
      pass

    return Ctor(*args, **kwargs)



  def recycle(self, obj):
    class_name = obj.__class__.__name__
    obj_queue = self._recycled[class_name]
    max_queue = self._queue_lengths[class_name]

    if len(obj_queue) < max_queue:
      obj_queue.append(obj.reset())
      


  def set_queue_length(self, class_name, length):
    self._queue_lengths[class_name] = length
    recycled = self._recycled[class_name]
    if len(recycled) > length:
      self._recycled[class_name] = recycled[:length]


    
  def specify(self, Ctor, length):
    self._ctors[Ctor.__name__] = Ctor
    self._queue_lengths[Ctor.__name__] = length




factory = Factory()


def specify(Ctor, length=QUEUE_LEN):
  factory.specify(Ctor, length)
  return Ctor




@specify
class DataModel(EventDispatcher):

  is_selected = BooleanProperty(False)


  def __init__(self, **kwargs):
    self.register_event_type('on_change')
    self._id = None
    super().__init__(**kwargs)



  def __setattr__(self, k, v):
    # if self[k] != v:
    self.dispatch('on_change', self)
    super().__setattr__(k, v)



  def __repr__(self):
    return self._id if self._id else self.__class__.__name__



  def to_obj(self):
    obj = {}
    obj['_class'] = self.__class__.__name__
    obj['_id'] = self._id
    for key in self.properties():
        obj[key] = repr(self[key])
    return obj



  def on_change(self, v):
    return



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




@specify
class DataList(DataModel):

  
  def __init__(self, *args, **kwargs):
    super().__init__(**kwargs)
    self._list = list(*args)
    self.register_event_type('on_insert')
    self.register_event_type('on_refresh')
    self.register_event_type('on_remove')
    self.register_event_type('on_set')
    self.register_event_type('on_swap')


  def __delitem__(self, i):
    self._list.__delitem__(i)
    i =  len(self._list) - i
    self.dispatch('on_remove', i)
   

  def __iter__(self):
    return iter(self._list)


  def __len__(self):
    return len(self._list)


  def __setitem__(self, i, v):
    self._list.__setitem__(i, v)
    i =  len(self._list) - 1 - i
    self.dispatch('on_set', i, v)


  def __repr__(self):
    return '[' + ''.join('{}, '.format(repr(model)) for model in self) + ']'



  def append(self, x):
    self._list.append(x)
    self.dispatch('on_insert', len(self._list) - 2, x)



  def clear(self):
    self._list.clear()
    self.dispatch('on_refresh')


  
  def extend(self, L):
    for x in L:
      self.append(x)



  def insert(self, i, x):
    self._list.insert(i, x)
    self.dispatch('on_insert', i, x)



  def pop(self, i=None):
    self._list.pop(i)
    i =  len(self._list) - i
    self.dispatch('on_remove', i)



  def refresh(self):
    self.dispatch('on_refresh')



  def remove(self, x):
    _list = self._list
    i =  len(_list) - 1 - _list.index(x)
    _list.remove(x)
    self.dispatch('on_remove', i)



  def reverse(self):
    self._list.reverse()
    self.dispatch('on_refresh')



  def sort(self, cmp=None, key=None, reverse=False):
    self._list.sort(cmp, key, reverse)
    self.dispatch('on_refresh')



  def swap(self, a, b):
    self[a], self[b] = self[b], self[a]
    _len =  len(self._list) - 1
    a, b = (_len - a), (_len - b)
    self.dispatch('on_swap', a, b)



  def on_insert(self, i, x):
    pass
  
  def on_refresh(self):
    pass
  
  def on_remove(self, i):
    pass
  
  def on_set(self, i, v):
    pass
  
  def on_swap(self, a, b):
    pass




from random import random


@specify
class DataContext(DataModel):

  name = StringProperty('')
  store = ObjectProperty(None, allownone=True)


  def __init__(self, **kwargs):
    super().__init__(**kwargs)
    self.factory = factory
    self._data = {}
    self._uids = {}
    self.clear_changes()


  def __getitem__(self, _id):
    return self._data[_id]



  def _get_id(self):
    for i in range(2):
      _id = str(random())
      try:
        self[_id]
      except KeyError:
        return _id
    
    raise Exception('couldnt create _id after 2 tries.')



  def clear_changes(self):
    self.changed = {}
    self.deleted = {}



  def delete(self, _id):
    model = self.deleted[_id] = self._data[_id]
    del self._data[_id]

    model.unbind_uid('on_change', self._uids[_id])
    del self._uids[_id]

    try:
      del self.changed[_id]
    except KeyError:
      pass



  def get(self, _id):
    return self._data[_id]



  def load(self):
    factory = self.factory
    store = self.store
    
    my_callback = lambda store, key, result: print('filemanager: loaded object', store, key, result)

    for key in store:
      store_obj = store.get(key, callback=my_callback)
      class_name = store_obj.pop['_class']
      self.put(factory.make(class_name, **store_obj))
      
    print('filemanager: loaded file')



  def put(self, model):
    try:
      _id = model._id
    except AttributeError:
      model._id = _id = self._get_id()

    self._uids[_id] = model.fbind('on_change', self.register_change)
    self._data[_id] = model
    self.changed[_id] = model



  def register_change(self, model):
    self.changed[model._id]



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

