from kivy.event import EventDispatcher
from kivy.properties import BooleanProperty



class DataModel(EventDispatcher):
  is_selected = BooleanProperty(False)


  def __init__(self, **kwargs):
    super().__init__(self, **kwargs)



  def init(self, **kwargs):
    for k, v in kwargs.items():
      setattr(self, k, v)

    return self



  def reset(self):
    self._id = None

    props = self.properties()
    for key in props:
      setattr(self, key, props[key].defaultvalue)
      
    return self



  def __iter__(self):
    return self


  def __next__(self):
    yield '_class', self.__class__.__name__
    yield '_id', self._id  
    for key in self.properties():
      yield key, getattr(self, key)

    raise StopIteration

