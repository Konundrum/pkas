import json
from kivy.app import App
from kivy.core.window import Window
from kivy.uix.widget import Widget

from .ui import ActiveProperty



class Controller(Widget):
    '''The Controller manages inputs and command delegation.

    The Controller manages inputs by calling command methods on Interactive
    widgets. Key binds and command names are set in {app_name}.ini. Up to four
    Interactive widgets are held by the following ActiveProperties:
        .root, .page, .region, .focus
    Setting an Interactive widget to any of these properties will cause it to
    recieve commands. Command methods are of the format:
        def on_cmd(self, controller):
    Commands do not bubble and are searched for from focus to root.
    '''

    root = ActiveProperty()
    page = ActiveProperty()
    region = ActiveProperty()
    focus = ActiveProperty()


    def __init__(self, binds=None, **kwargs):
        self.binds = binds
        super().__init__(**kwargs)
        keyboard = Window.request_keyboard(lambda:None, self)
        keyboard.bind(on_key_down=self._on_key_down)
        self._keyboard = keyboard


    def _on_key_down(self, keyboard, keycode, text, modifiers):
        num_modifiers = len(modifiers)

        if num_modifiers is 0:
            input_keys = keycode[1]
        elif num_modifiers is 1:
            input_keys = ''.join(['{} '.format(modifiers[0]), keycode[1]])
        else:
            input_keys = ''.join(['ctrl shift ', keycode[1]])

        try:
            cmd = self.binds[input_keys]
        except KeyError:
            return False

        print(input_keys, cmd)

        try:
            cb = getattr(self.focus, cmd)
        except AttributeError:
            try:
                cb = getattr(self.region, cmd)
            except AttributeError:
                try:
                    cb = getattr(self.page, cmd)
                except AttributeError:
                    try:
                        cb = getattr(self.root, cmd)
                    except AttributeError:
                        return False

        cb(self)
        return True


    def release_keyboard(self):
        self._keyboard.unbind(on_key_down=self._on_key_down)
        self._keyboard = None



class PKApp(App):
    '''PKApp is the base application class.

    On instantiation it parses the config file and instantiates the controller.
     If on_start is overrided, super().onstart() must be called.
    '''

    def __init__(self, **kwargs):
        super().__init__(**kwargs)


    def on_start(self):
        binds = {}
        for cmd, key_list in self.config.items('keybinds'):
            for key in json.loads(key_list):
                binds[key] = 'on_{}'.format(cmd)

        self.controller = Controller(binds=binds, root=self.root)

