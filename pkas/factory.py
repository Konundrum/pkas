from collections import defaultdict
QUEUE_LEN = 0


class Factory(object):

  def __init__(self):
    super().__init__()
    self._ctors = {}
    self._recycled = defaultdict(list)
    self._queue_lengths = {}



  def make(self, name, **kwargs):
    try:
      Ctor = self._ctors[name]
    except KeyError:
      Exception('factory.make: Invalid ctor name.')
    
    class_name = Ctor.__name__

    try:
      return self._recycled[class_name].pop().init(**kwargs)
    except IndexError:
      return Ctor(**kwargs)



  def recycle(self, obj):
    class_name = obj.__class__.__name__
    obj_queue = self._recycled[class_name]
    max_queue = self._queue_lengths[class_name]

    if len(obj_queue) < max_queue:
      obj_queue.append(obj.reset())
      


  def set_queue_length(self, name, length):
    class_name = self._ctors[name].__name__
    self._queue_lengths[class_name] = length


    
  def specify(self, name, Ctor, length=QUEUE_LEN):
    self._ctors[name] = Ctor
    self._queue_lengths[Ctor.__name__] = length


