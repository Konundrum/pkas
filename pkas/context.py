from random import random


class DataContext(dict):
  def __init__(self, factory, store, name):
    super().__init__()
    self.factory = factory
    self.name = name
    self.store = store
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

    for _id, obj in self.deleted:
      delete(_id)
      self.factory.recycle(obj)

    for _id, model in self.changed:
      put(_id, model)

    self.clear_changes()



  def delete(self, _id):
    self.deleted[_id] = self[_id]
    del self[_id]

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



  def put(self, model):
    try:
      _id = model['_id']
    except KeyError:
      model['_id'] = _id = self._get_id()

    # Subscribe to model changes
    # uids = []
    # for prop in model.properties():
    #   uids.append(prop.fbind() )

    # Better to just append context and replace setattr?
    # model.context = self

    super().__setitem__(_id, model)





class ContextManager(dict):
  def __init__(self, factory):
    self.factory = factory

  
  def close(self, name):
    del self[name]


  def __setitem__(self, name, store):
    super().__setitem__(name, DataContext(self.factory, store, name))

