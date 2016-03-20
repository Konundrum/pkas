from kivy.event import EventDispatcher
from kivy.properties import AliasProperty, NumericProperty




class ActiveProperty(AliasProperty):

  def __init__(self, prop_name, **kwargs):
    self.prop_name = '_{}'.format(prop_name)
    super().__init__(self.get, self.set, bind=[])


  def get(self, obj):
    return getattr(obj, self.prop_name)

    
  def set(self, obj, new_val):
    old_val = getattr(obj, self.prop_name)

    if new_val is old_val:
      return False
    
    if old_val:
      old_val.on_inactive(obj)
      old_val.is_active = False
    
    if new_val:
      new_val.on_active(obj)
      new_val.is_active = True
    
    setattr(obj, self.prop_name, new_val)
    return True




class SelectorProperty(AliasProperty):
  
  def get(self, obj):
    return self._selected

  # ContextTabRow, value
  def set(self, obj, value):
    if self._selected:
      self._selected.is_selected = False

    if value:
      value.is_selected = True
    
    self._selected = value
    return True


  def __init__(self, value=None):
    super().__init__(self.get, self.set, bind=[])
    self._selected = value
    if value:
      value.is_selected = True




class Walker(EventDispatcher):
  
  def _get_current(self):
    try:
      return self._list[self.index]
    except IndexError:
      self.index = len(self._list) - 1
      if self.index > -1:
        return self._list[self.index]
    return None
        

  def _set_current(self, current):
    _index = self._list.index(current)
    self.index = _index
    return True


  def _get_list(self):
    return self._list

  def _set_list(self, list):
    self.index = 0
    self._list = list
    return True


  index = NumericProperty(0)
  current = AliasProperty(_get_current, _set_current, bind=['index'])
  list = AliasProperty(_get_list, _set_list, bind=[])


  def __init__(self, **kwargs):
    self._list = []
    super().__init__(**kwargs)


  def inc(self):
    _len = len(self._list)
    if self.index < _len - 1:
      self.index += 1

    return self.current


  def dec(self):
    if self.index > 0:
      self.index -= 1
  
    return self.current


