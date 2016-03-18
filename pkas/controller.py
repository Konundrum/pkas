import json
from kivy.core.window import Window
from kivy.properties import AliasProperty
from kivy.uix.widget import Widget


class Controller(Widget):

  def __init__(self, app, **kwargs):
    super().__init__(**kwargs)
    self._page = self._region = self._focus = None
    self.app = app
    self._key_binds = self._parse_keys(app.config)
    self.take_control()


  def _switch_active(self, old, new):
    if new is old:
      return False
    if old:
      old.on_inactive(self)
      old.is_active = False
    if new:
      new.on_active(self)
      new.is_active = True
    return True


  def _get_page(self):
    return self._page

  def _set_page(self, page):
    if self._switch_active(self._page, page):
      self._page = page
      return True
    

  def _get_region(self):
    return self._region

  def _set_region(self, region):
    if self._switch_active(self._region, region):
      self._region = region
      print('set region', region)
      return True


  def _get_focus(self):
    return self._focus

  def _set_focus(self, focus):
    if self._switch_active(self._focus, focus):
      self._focus = focus
      return True


  page = AliasProperty(_get_page, _set_page, bind=[])
  region = AliasProperty(_get_region, _set_region, bind=[])
  focus = AliasProperty(_get_focus, _set_focus, bind=[])
  


  def take_control(self):
    self._keyboard = Window.request_keyboard(self._keyboard_closed, self)
    self._keyboard.bind(on_key_down=self._on_keyboard_down)



  def _keyboard_closed(self):
    self._keyboard.unbind(on_key_down=self._on_keyboard_down)
    self._keyboard = None



  def _try_action(self, widget, cmd):
    try:
      cb = getattr(widget, cmd)
    except AttributeError:
      return False

    cb(self)
    return True



  def _on_keyboard_down(self, keyboard, keycode, text, modifiers):
    print(keycode[1], modifiers, 'key pressed')
    try:
      cmd = self._key_binds[keycode[1]]
    except KeyError:
      return

    cmd = 'on_{cmd}'.format(cmd=cmd)
    
    self._try_action(self._focus, cmd) or \
    self._try_action(self._region, cmd) or \
    self._try_action(self._page, cmd) or \
    self._try_action(self.app.root, cmd)    




  def _parse_keys(self, config):
    binds = {}
    if config:
      print('in parse keys')
      for cmd, key_list in config.items('keybinds'):
        for key in json.loads(key_list):
          binds[key] = cmd
          print('bound:', key, cmd)

    return binds

