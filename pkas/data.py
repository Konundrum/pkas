from collections import defaultdict
from kivy.event import EventDispatcher
from kivy.properties import BooleanProperty, ObjectProperty, StringProperty


QUEUE_LEN = 10




class Factory(object):


  # Singleton reference
  _inst = None

  def __new__(cls):
    if not cls._inst:
      cls._inst = inst = super().__new__(cls)
      inst._ctors = {}
      inst._recycled = defaultdict(list)
      inst._queue_lengths = {}

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
    self.dispatch('on_change', self)
    super().__setattr__(k, v)



  def __repr__(self):
    return self._id if self._id else self.__class__.__name__



  def init(self, **kwargs):
    for k, v in kwargs.items():
      setattr(self, k, v)
    return self


  def to_obj(self):
    obj = {}
    obj['_class'] = self.__class__.__name__
    obj['_id'] = str(self._id)
    for key in self.properties():
        obj[key] = repr(self[key])
    return obj



  def on_change(self, v):
    pass



  def reset(self):
    self._id = None

    props = self.properties()
    for key in props:
      setattr(self, key, props[key].defaultvalue)
      
    return self




class DataCollection(DataModel):
  
  def __init__(self, **kwargs):
    self.register_event_type('on_insert')
    self.register_event_type('on_refresh')
    self.register_event_type('on_remove')
    self.register_event_type('on_set')
    self.register_event_type('on_swap')
    super().__init__(**kwargs)


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




@specify
class DataList(DataCollection):

  def __init__(self, *args, **kwargs):
    super().__init__(**kwargs)
    self.item_list = list(*args)


  def __delitem__(self, i):
    del self.item_list[i]
    i =  len(self.item_list) - i
    self.dispatch('on_remove', i)


  def __getitem__(self, i):
    return self.item_list[i]


  def __setitem__(self, i, v):
    self.item_list.__setitem__(i, v)
    i =  len(self.item_list) - 1 - i
    self.dispatch('on_set', i, v)


  def __iter__(self):
    return iter(self.item_list)


  def __len__(self):
    return len(self.item_list)


  def __repr__(self):
    return repr(self.item_list)


  def append(self, x):
    self.item_list.append(x)
    self.dispatch('on_insert', 0, x)



  def clear(self):
    self.item_list.clear()
    self.dispatch('on_refresh')


  
  def extend(self, L):
    for x in L:
      self.append(x)


  def index(self, v):
    return self.item_list.index(v)


  def insert(self, i, x):
    _list = self.item_list
    _list.insert(i, x)
    self.dispatch('on_insert', len(_list) - 1 - i, x)



  def pop(self, i=None):
    self.item_list.pop(i)
    i =  len(self.item_list) - i
    self.dispatch('on_remove', i)



  def refresh(self):
    self.dispatch('on_refresh')



  def remove(self, x):
    _list = self.item_list
    i =  len(_list) - 1 - _list.index(x)
    _list.remove(x)
    self.dispatch('on_remove', i)



  def reverse(self):
    self.item_list.reverse()
    self.dispatch('on_refresh')



  def sort(self, cmp=None, key=None, reverse=False):
    self.item_list.sort(cmp, key, reverse)
    self.dispatch('on_refresh')



  def swap(self, a, b):
    l = self.item_list
    l[a], l[b] = l[b], l[a]
    _len =  len(l) - 1
    a, b = (_len - a), (_len - b)
    self.dispatch('on_swap', a, b)




@specify
class DataDict(DataCollection):


  def __init__(self, dictionary={}, **kwargs):
    super().__init__(**kwargs)
    self.item_list = _list = []
    self._keys = _keys = []

    append = _list.append
    for key, model in dictionary:
      _keys.append(key)
      append(model)

    self.refresh()


  def __contains__(self, value):
    return value in self.item_list


  def __delitem__(self, key):
    i = self._keys.index(key)
    del self._keys[i]
    del self.item_list[i]
    i =  len(self.item_list) - i
    self.dispatch('on_remove', i)


  def __getitem__(self, key):
    return self.item_list[self._keys.index(key)]


  def __iter__(self):
    return iter(self.item_list)


  def __len__(self):
    return len(self.item_list)


  def __setitem__(self, key, v):
    _list = self.item_list
    _keys = self._keys
    try:
      i = _keys.index(key)
      _list[i] = v
      i = len(_list) - 1 - i
      self.dispatch('on_set', i, v)
    except ValueError:
      _keys.append(key)
      _list.append(v)
      self.dispatch('on_insert', 0, v)

    
  def __repr__(self):
    repr(self.item_list)


  def clear(self):
    self._keys.clear()
    self.item_list.clear()
    self.dispatch('on_refresh')

  def copy(self):
    raise Exception('Copy not implemented!')

  def fromkeys(self):
    return iter(self._keys)

  def get(self, key):
    return self.item_list[self._keys.index(key)]

  def items(self):
    return iter(self.item_list)

  def keys(self):
    return iter(self._keys)

  def values(self):
    return iter(self.item_list)

  def refresh(self):
    self.dispatch('on_refresh')

  def swap(self, a, b):
    index = self._keys.index
    l = self.item_list
    _len =  len(l) - 1
    
    a, b = index(a), index(b)
    l[a], l[b] = l[b], l[a]
    a, b = (_len - a), (_len - b)    
    self.dispatch('swap', a, b)



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
    self._clear_changes()


  def __contains__(self, _id):
    return _id in self._data


  def __getitem__(self, _id):
    return self._data[_id]


  def __repr__(self):
    return 'DataContext: {}'.format(self.name)


  def _get_id(self):
    for i in range(3):
      _id = str(random())
      try:
        self[_id]
      except KeyError:
        return _id
    
    raise Exception('Did not create unique _id after 3 tries!')



  def _clear_changes(self):
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



  def _load_object(self, store, key, result):
    class_name = result.pop['_class']
    self.put(self.factory.make(class_name, **store_obj))
    
    print('filemanager: loaded object', result)
    


  def load(self):
    factory = self.factory
    store = self.store

    for key in store:
      store_obj = store.async_get(self._load_object, key)
    
    print('filemanager: loaded file')



  def put(self, model):
    try:
      _id = model._id    
      if _id in self._data:
        return

    except AttributeError:
      model._id = _id = self._get_id()

    self._uids[_id] = model.fbind('on_change', self._register_change)
    self._data[_id] = model
    self.changed[_id] = model



  def _register_change(self, model):
    self.changed[model._id]



  def save(self):
    delete = self.store.delete
    put = self.store.put
    recycle = self.factory.recycle

    for _id, obj in self.deleted.items():
      delete(_id)
      recycle(obj)

    for _id, model in self.changed.items():
      for prop in model:
        put(_id, **model.to_obj())

    self._clear_changes()

