import json
from kivy.app import App
from kivy.core.window import Window
from kivy.properties import ObjectProperty
from kivy.uix.widget import Widget
from .utils import ActiveProperty
AE = AttributeError




class Controller(Widget):
  
  binds = ObjectProperty(None)
  root = ActiveProperty('root')
  page = ActiveProperty('page')
  region = ActiveProperty('region')
  focus = ActiveProperty('focus')


  def __init__(self, **kwargs):
    self._root = self._page = self._region = self._focus = None
    super().__init__(**kwargs)
    
    keyboard = Window.request_keyboard(lambda:None, self)
    keyboard.bind(on_key_down=self._on_key_down)
    self._keyboard = keyboard



  def _on_key_down(self, keyboard, keycode, text, modifiers):
    
    _len = len(modifiers)
    if _len is 0:
      action = keycode[1]
    elif _len is 1:
      action = ''.join(['{} '.format(modifiers[0]), keycode[1]])
    else:
      action = ''.join(['ctrl shift ', keycode[1]])

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

