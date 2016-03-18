from collections import defaultdict
QUEUE_LEN = 10


class Factory(object):
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



  def make(self, name, **kwargs):
    try:
      Ctor = self._ctors[name]
    except KeyError:
      Exception('factory.make:', name,'not specified.')

    try:
      return self._recycled[name].pop().init(**kwargs)
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


    
    # Adapter accepts Ctors... 
    
  def specify(self, Ctor, length):
    self._ctors[Ctor.__name__] = Ctor
    self._queue_lengths[Ctor.__name__] = length



factory = Factory()



def specify(Ctor, length=QUEUE_LEN):
  factory.specify(Ctor, length)
  return Ctor
