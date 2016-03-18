from kivy.app import App
from .controller import Controller


class PKApp(App):

    
  def __init__(self, **kwargs):
    super().__init__(**kwargs)

  
  def on_start(self):
    self.controller = Controller(self)
    self.root.on_active(self)


  def on_stop(self):
    self.root.on_inactive(self)
    