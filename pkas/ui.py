from os.path import join
from kivy.event import EventDispatcher
from kivy.lang import Builder
from kivy.properties import *
from kivy.uix.widget import Widget
from kivy.uix.layout import Layout

from .data import factory, DataCollection


def load_kv(*args):
    Builder.load_file(join(*args))


class DataWidget(Widget):
    '''Widget that represents a DataModel.
    Expects a cls.defaultmodel instance as a fallback for kv bindings.
    Implements the recycler init(**kwargs) and recycle() interface.
    '''

    model = ObjectProperty(None, rebind=True, allownone=True)
    defaultmodel = factory.make('DataModel')


    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


    def init(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)
        return self


    def recycle(self):
        self.model = self.defaultmodel
        return self



class CollectionProperty(ObjectProperty):
    '''View property to bind and unbind from DataCollection events.
    Uses datacollection.events and view._bound_uids for event binding.
    '''

    def __init__(self, **kwargs):
        super().__init__(baseclass=DataCollection, **kwargs)


    def set(self, view, data):
        uids = view._bound_uids
        old_data = self.get(view)
        if old_data:
            unbind_uid = old_data.unbind_uid
            for evt in reversed(old_data.events):
                unbind_uid(evt, uids.pop())

        if data is not None:
            append_uid = uids.append
            fbind = data.fbind
            for evt in data.events:
                append_uid(fbind(evt, getattr(view, evt)))

        super().set(view, data)
        view.on_update(data)
        return True




class DataView(Layout):
    '''Layout that keeps children in sync with data.
    Complexity comes from the fact that children are kept in reverse order.
    '''

    data = CollectionProperty()
    cls = AliasProperty(lambda s: getattr(s, '_cls'),
                        lambda s,v: setattr(s, '_cls', v.__name__),
                        bind=[])


    def __init__(self, *args, **kwargs):
        self._bound_uids = []
        self._factory = factory
        super().__init__(**kwargs)


    def __del__(self):
        try:
            self._unbind_data()
        except IndexError:
            pass


    def get_child_index(self, child):
        '''Returns the reversed index for use in DataCollections.'''
        c = self.children
        return len(c) - 1 - c.index(child)


    def on_del(self, data, i):
        i = len(self.children) - 1 - i
        widget = self.children[i]
        self.remove_widget(widget)
        self._factory.recycle(widget)


    def on_set(self, data, i, model):
        i = len(self.children) - 1 - i
        factory = self._factory
        old_widget = self.children[i]

        self.remove_widget(old_widget)
        factory.recycle(old_widget)
        widget = factory.make(self.cls, model=model)
        self.add_widget(widget, i)


    def on_clear(self):
        recycle = self._factory.recycle
        for widget in self.children:
            recycle(widget)
        self.clear_widgets()


    def on_insert(self, data, i, model):
        widget = self._factory.make(self.cls, model=model)
        i = len(self.children) - i
        self.add_widget(widget, i)


    def on_swap(self, data, a, b):
        children = self.children
        l =  len(children) - 1
        a, b = (l - a), (l - b)
        children[a], children[b] = children[b], children[a]


    def on_update(self, data):
        recycle = self._factory.recycle
        for widget in self.children:
            recycle(widget)

        self.clear_widgets()

        if data:
            add_widget = self.add_widget
            cls = self.cls
            make = self._factory.make
            for model in data:
                add_widget(make(cls, model=model))



class RecyclerProperty(CollectionProperty):
    '''Binds and unbinds Collections.'''

    def __init__(self, display_prop, **kwargs):
        self.display_prop = display_prop
        super().__init__(**kwargs)


    def set(self, view, collection):
        super().set(view, collection)
        displayed = view._factory.make('DataList', view.gen_displayed())
        setattr(view, self.display_prop, displayed)
        return True



class RecyclerView(DataView):
    '''Recyles widgets that are not in view.

    RecyclerView maintains the .displayed list, matching the data models
    yielded by gen_displayed() on changes to data. This means that data does not
    need to be set explicitly and will be destructively modified if set.
    '''

    displayed = CollectionProperty()
    data = RecyclerProperty('displayed')


    def gen_displayed(self):
        '''Default implementation simply copies self.data'''
        return iter(self.data)


    def update(self, collection):
        '''Step through the current data and match in place.'''
        displayed = self.displayed
        index = -1

        for model in self.gen_displayed():
            index += 1
            try:
                current = displayed[index]
                if current is not model:
                    i = displayed.index(model)
                    displayed.swap(index, i)
                continue
            except (IndexError, ValueError):
                pass

            displayed.insert(index, model)

        for i in reversed(range(index + 1, len(displayed))):
            del displayed[i]



    def get_child_index(self, child):
        '''Returns the reversed index for use in DataCollections.'''
        data = self.data
        return len(data) - 1 - data.index(child)



class Interactive(EventDispatcher):
    '''Mixin for Interactive Widgets'''

    is_active = BooleanProperty(False)

    def on_active(self, controller):
        pass
    def on_inactive(self, controller):
        pass



class ActiveProperty(ObjectProperty):
    '''Activates and Deactivates Interactive Widgets'''

    def __init__(self, allownone=True, **kwargs):
        super().__init__(allownone=allownone, **kwargs)


    def set(self, obj, value):
        old_value = super().get(obj)

        if value is old_value:
            return False

        if old_value:
            old_value.is_active = False
            old_value.on_inactive(obj)

        if value:
            value.is_active = True
            value.on_active(obj)

        super().set(obj, value)
        return True



class Walker(EventDispatcher):
    '''Convenience class for walking lists.'''

    def _get_index(self):
        return self._index

    def _set_index(self, i):
        if i == self._index:
            return False
        self._index = i
        return True

    def _get_current(self):
        _index = self._index
        try: return self.data[_index]
        except IndexError: pass

        _max = len(self.data) - 1
        if _max == -1: return None

        self.index = _max
        return self.data[_max]

    def _set_current(self, current):
        index = self.data.index(current)
        self.index = index
        return True


    index = AliasProperty(_get_index, _set_index, bind=[])
    current = AliasProperty(_get_current, _set_current, bind=['index', 'data'])
    data = ObjectProperty(None)


    def __init__(self, **kwargs):
        self._index = 0
        super().__init__(**kwargs)


    def inc(self):
        length = len(self.data)
        if self.index < length - 1:
            self.index = self.index + 1
        return self.current


    def dec(self):
        if self.index > 0:
            self.index -= 1
        return self.current
