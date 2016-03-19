import json
from kivy.app import App
from kivy.core.window import Window
from kivy.properties import AliasProperty, ObjectProperty
from kivy.uix.widget import Widget
AE = AttributeError



class Controller(Widget):


  def _gen_get(prop):
    prop = '_{}'.format(prop)
    
    def getter(self):
      return getattr(self, prop)

    return getter


  def _gen_set(prop):
    prop = '_{}'.format(prop)
    
    def switcher(self, new_val):
      old_val = getattr(self, prop)

      if new_val is old_val:
        return False
      
      if old_val:
        old_val.on_inactive(self)
        old_val.is_active = False
      
      if new_val:
        new_val.on_active(self)
        new_val.is_active = True
      
      setattr(self, prop, new_val)
      return True

    return switcher


  def _get_context(self):
    return self._context

  def _set_context(self, context):
    if context is self._context:
      return False
    if self._context:
      self._context.is_selected = False
    
    self._context = context
    context.is_selected = True
    return True



  binds = ObjectProperty(None)
  context = AliasProperty(_get_context, _set_context, bind=[])
  root = AliasProperty(_gen_get('root'), _gen_set('root'), bind=[])
  page = AliasProperty(_gen_get('page'), _gen_set('page'), bind=[])
  region = AliasProperty(_gen_get('region'), _gen_set('region'), bind=[])
  focus = AliasProperty(_gen_get('focus'), _gen_set('focus'), bind=[])  


  def __init__(self, **kwargs):
    self._context = self._root = self._page = self._region = self._focus = None
    super().__init__(**kwargs)
    
    keyboard = Window.request_keyboard(lambda:None, self)
    keyboard.bind(on_key_down=self._on_key_down)
    self._keyboard = keyboard



  def _on_key_down(self, keyboard, keycode, text, modifiers):
    action = ''.join([*('{} '.format(m) for m in modifiers), keycode[1]])
    print(action, 'pressed')

    try:
      cmd = self.binds[action]
    except KeyError:
      return False

    try:
      cb = getattr(self._focus, cmd)
    except AE:
      try:
        cb = getattr(self._region, cmd)
      except AE:
        try:
          cb = getattr(self._page, cmd)
        except AE:
          try:
            cb = getattr(self._root, cmd)
          except AE:
            return False

    cb(self)
    return True



  def release_keyboard(self):
    self._keyboard.unbind(on_key_down=self._on_key_down)
    self._keyboard = None




class PKApp(App):

    
  def __init__(self, **kwargs):
    super().__init__(**kwargs)


  
  def on_start(self):
    binds = {}
    for cmd, key_list in self.config.items('keybinds'):
      for key in json.loads(key_list):
        binds[key] = 'on_{}'.format(cmd)

    self.controller = Controller(binds=binds, root=self.root)

