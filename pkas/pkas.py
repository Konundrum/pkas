from collections import defaultdict, UserDict, UserList
import json
from random import random
from os.path import join

from kivy.app import App
from kivy.event import EventDispatcher
from kivy.properties import AliasProperty, BooleanProperty, ObjectProperty, StringProperty
from kivy.lang import Builder
from kivy.uix.layout import Layout
from kivy.uix.widget import Widget
from kivy.core.window import Window

STACK_LEN = 10




class Factory(object):
    '''
    The Factory maintains an object pool of DataModels and DataWidgets.

    Items to be recycled by the factory must implement both
    .reinit(self, **kwargs) and .recycle(self), which are used by the
    Factory to setup and teardown objects. The Factory maintains a queue
    for each class, the lengths of which may be set by set_stack_length.
    '''

    _inst = None  #Singleton reference

    def __new__(cls):
        if not cls._inst:
            cls._inst = inst = super().__new__(cls)
            inst._ctors = {}
            inst._recycled = defaultdict(list)
            inst._stack_lengths = {}
        return cls._inst



    def make(self, cls, *args, **kwargs):
        '''
        Initializes objects from their respective class stacks, or if
        not available creates new ones with (args, kwargs). In order to
        to be recyclable objects must implement reinit(...).
        '''
        try:
            Ctor = self._ctors[cls]
        except KeyError:
            raise Exception('factory.make:', cls, 'not specified.')

        try:
            return self._recycled[cls].pop().reinit(*args, **kwargs)
        except IndexError:
            return Ctor(*args, **kwargs)



    def recycle(self, obj):
        '''
        Recycles obj by calling obj.recycle() and placing the object
        into its class' stack awaiting reinitialization. All other
        references to obj should be dropped by this point.
        '''
        cls = obj.__class__.__name__
        obj_stack = self._recycled[cls]

        if len(obj_stack) < self._stack_lengths[cls]:
            obj_stack.append(obj.recycle())


    def set_stack_length(self, cls, length):
        self._stack_lengths[cls] = length
        recycled = self._recycled[cls]

        if len(recycled) > length:
            self._recycled[cls] = recycled[:length]



    def specify(self, Ctor, length):
        '''Specifies a class and stack len for production by the factory.'''
        self._ctors[Ctor.__name__] = Ctor
        self._stack_lengths[Ctor.__name__] = length




factory = Factory()     # Singleton

def specify(Ctor, stack_length=STACK_LEN):
    '''Decorator to specify a class for production by the factory.'''
    factory.specify(Ctor, stack_length)
    return Ctor




class DataProperty(ObjectProperty):
    '''For DataModels to hold DataCollections. Used at file load.'''
    pass



@specify
class DataModel(EventDispatcher):
    '''
    Model that supports recycling and save / load by implementing
    recycle(), reinit(...) and to_json(), load(context) respectively.
    '''

    is_selected = BooleanProperty(False)


    def recycle(self):
        self._id = None
        for prop in self.properties():
            prop.set(self, prop.defaultvalue)
        return self


    def reinit(self, _id=None, **kwargs):
        self._id = _id
        for k, v in kwargs.items():
            setattr(self, k, v)
        return self


    def load(self, context):
        for prop in self.properties():
            if isinstance(prop, DataProperty):
                prop.get(self).load(context)


    def to_json(self):
        ''''''
        output = []
        entries = []
        output.append('{')
        append = entries.append
        append('  "class" : "{}",'.format(self.__class__.__name__))
        append('  "_id" : "{}"'.format(self._id))
        for prop in self.properties():
            value = prop.get(self)
            if isinstance(value, DataCollection):
                value = value.to_json()
            append('  "{}" : {}'.format(prop.name, value))
        output.append(',\n'.join(entries))
        output.append('}')
        return ''.join(output)


    def __init__(self, _id=None, *args, **kwargs):
        self._id = _id
        super().__init__(*args, **kwargs)

    def __eq__(self, other):
        return self is other

    def __ne__(self, other):
        return self is not other




class DataCollection(DataModel):
    '''
    Base Collection class to hold collections of DataModels. The events
    are used to keep a DataView's children in sync. DataCollection can
    be subclassed to provide a different collection event interface,
    by overriding the events list and providing the relevant methods.
    The recycle and reinit methods provided here clear and set
    collection.data. If this is undesirable you may wish to call
    DataWidget.recycle() directly in your own recycle implementation.
    '''

    events = ['on_del','on_set','on_clear','on_insert','on_update','on_swap']

    fallback = lambda *args: None
    for evt in events:
        locals()[evt] = fallback
    del locals()['fallback']

    def __init__(self, *args, **kwargs):
        for evt in self.events:
            self.register_event_type(evt)
        super().__init__(*args, **kwargs)

    def recycle(self):
        self.data.clear()
        super().recycle()

    def reinit(self, data=None, *args, **kwargs):
        self.data = data
        super().reinit(*args, **kwargs)




@specify
class DataList(DataCollection, UserList):
    '''
    List implementation of DataCollection.
    Supports the base DataCollection event interface and file loading.
    '''

    def __init__(self, data=[], *args, **kwargs):
        super().__init__(data, *args, **kwargs)

    def __delitem__(self, i):
        self.data.__delitem__(i)
        self.dispatch('on_del', i)

    def __setitem__(self, i, v):
        self.data.__setitem__(i, v)
        self.dispatch('on_set', i, v)

    def append(self, x):
        self.data.append(x)
        self.dispatch('on_insert', i, x)

    def clear(self):
        self.data.clear()
        self.dispatch('on_clear')

    def extend(self, L):
        self.data.extend(L)
        self.dispatch('on_update')

    def insert(self, i, x):
        self.data.insert(i, x)
        self.dispatch('on_insert', i, x)

    def pop(self, i=None):
        self.data.pop(i)
        self.dispatch('on_del', i)

    def remove(self, x):
        i = self.data.index(x)
        del self[i]

    def reverse(self):
        self.data.reverse()
        self.dispatch('on_update')

    def sort(self, cmp=None, key=None, reverse=False):
        self.data.sort(cmp, key, reverse)
        self.dispatch('on_update')

    def swap(self, a, b):
        d = self.data
        d[a], d[b] = d[b], d[a]
        self.dispatch('on_swap', a, b)


    def load(self, context):
        '''If any data items are still _ids, load the models from context.'''
        data = self.data
        for index, item in enumerate(data):
            if type(item) is str:
                super()[index] = context[item]


    def to_json(self):
        output = []
        entries = []
        output.append('{')
        entries.append('"class":"{}"'.format(self.__class__.__name__))
        try: entries.append('"_id":"{}"'.format(self._id))
        except AttributeError: pass
        ids = []
        for item in self.data:
            ids.append(item._id)
        entries.append('"data":"[{}]"'.format(','.join(ids)))
        output.append(','.join(entries))
        output.append('}')
        return ''.join(output)




@specify
class DataDict(DataCollection, UserDict):
    '''
    Dict implementation of DataCollection.
    Supports DataCollection event interface and file loading.
    '''

    def __init__(self, data=None, *args, **kwargs):
        super().__init__(data, *args, **kwargs)
        self.keys = []
        append = self.keys.append
        for key in self.data.keys():
            append(key)

    def __delitem__(self, key):
        i = self.keys.index(key)
        del self.keys[i]
        del self.data[key]
        self.dispatch('on_del', i)

    def __setitem__(self, key, value):
        keys = self.keys
        self.data[key] = value

        try:
            i = keys.index(key)
            self.dispatch('on_set', i, value)
        except ValueError:
            keys.append(key)
            self.dispatch('on_insert', len(keys) - 1, value)

    def __iter__(self):
        return iter(self.keys)

    def clear(self):
        self.keys.clear()
        self.data.clear()
        self.dispatch('on_update')

    def fromkeys(self, *args):
        return self.data.fromkeys(*args)

    def get(self, key, default=None):
        return self.data.get(key, default)

    def items(self):
        return self.data.items()

    def keys(self):
        return self.keys

    def values(self):
        for key in self.keys:
            yield self.data[key]

    def setdefault(self, key, default=None):
        if not key in self.keys:
            self[key] = default

    def pop(self, key):
        index = self.keys.index(key)
        del self.keys[i]
        item = self.data.pop(key)
        self.dispatch('on_del', i)
        return item

    def popitem(self):
        key = self.keys.pop()
        key, item = self.data.pop(key)
        self.dispatch('on_del', len(self.keys))
        return key, item

    def swap(self, a, b):
        index = self.keys.index
        l = self.data
        a, b = index(a), index(b)
        l[a], l[b] = l[b], l[a]
        self.dispatch('on_swap', a, b)

    def update(self, *args, **kwargs):
        self.data.update(*args, **kwargs)
        self.dispatch('on_update')


    def load(self, context):
        '''If any data items are still _ids, load the models from context.'''
        data = self.data
        for key, value in data:
            if type(value) is str:
                super()[key] = context[value]


    def to_json(self):
        output = []
        entries = []
        output.append('{')
        entries.append('"class":"{}"'.format(self.__class__.__name__))
        try: entries.append('"_id":"{}"'.format(self._id))
        except AttributeError: pass
        data = []
        for key, value in self:
            data.append('"{}":"{}"'.format(key, value._id))
        entries.append('"data":{{}}'.format(','.join(entries)))
        output.append(','.join(entries))
        output.append('}')
        return ''.join(output)




@specify
class DataContext(DataDict):
    '''
    DataDict for saving to and loading from files.

    Objects are stored by a unique key that is added as an attribute when
    the model is added to the context. This key remains with the object
    through saving.
    '''

    name = StringProperty('default')
    filename = StringProperty('')


    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.register_event_type('on_save')
        self.register_event_type('on_load')

    def on_save(self):
        pass

    def on_load(self):
        pass

    def __repr__(self):
        return 'Context {}: {}'.format(self.name, self.data)

    def __delitem__(self, key):
        item = self[key]
        super().__delitem__(key)
        factory.recycle(item)

    def _get_id(self):
        for i in range(3):
            _id = str(random())
            try:
                self[_id]
            except KeyError:
                return _id

        raise Exception('Did not create unique _id after 3 tries!')


    def save(self):
        '''Iterate over keys, items.to_json() and write to self.filename'''
        with open(self.filename, 'w') as f:
            f.write('{\n')
            f.write('"name" : "{}",\n'.format(self.name))
            for _id, model in self:
                f.write('"{}" : {}'.format(_id, model.to_json()))
            f.write('}\n')


    def load(self):
        '''Parse filename as json, update self and call load() on items.'''
        make = self.factory.make
        with open(self.filename, 'r') as f:
            data = json.load(file = f, object_hook = lambda dct:
                    make(dct.pop('class'), dct) if 'class' in dct else dct )

        self.name = data.pop('name')
        self.update(data)

        for model in data.values():
            model.load(self)




class SelectorProperty(ObjectProperty):
    '''Manages selection / deselection of models by assignment.'''

    def set(self, obj, value):
        old_value = super().get(obj)

        if old_value is not None:
            old_value.is_selected = False

        if value is not None:
            value.is_selected = True

        super().set(obj, value)
        return True





class DataWidget(Widget):
    '''
    Widget that represents a DataModel.
    Expects a cls.defaultmodel instance as a fallback for kv bindings.
    Implements the recycler init(**kwargs) and recycle() interface.
    '''

    model = ObjectProperty(None, rebind=True, allownone=True)
    defaultmodel = factory.make('DataModel')


    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


    def reinit(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)
        return self


    def recycle(self):
        self.model = self.defaultmodel
        return self



class CollectionProperty(ObjectProperty):
    '''
    Property to bind and unbind from DataCollection events.
    Uses datacollection.events and host._bound_uids for event binding.
    '''

    def __init__(self, **kwargs):
        super().__init__(baseclass=DataCollection, **kwargs)


    def set(self, host, collection):
        uids = host._bound_uids
        old_collection = self.get(host)
        if old_collection:
            unbind_uid = old_collection.unbind_uid
            for evt in reversed(old_collection.events):
                unbind_uid(evt, uids.pop())

        if collection is not None:
            append_uid = uids.append
            fbind = collection.fbind
            for evt in collection.events:
                append_uid(fbind(evt, getattr(host, evt)))

        super().set(host, collection)
        host.on_update(collection)
        return True




class DataView(Layout):
    '''Layout that keeps children in sync with data.'''

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
        '''Returns the child widget index for use in DataCollections.'''
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
    '''
    Binds and unbinds Collections to target DataList.
    The host object must implement gen_data().
    '''

    def __init__(self, target, **kwargs):
        self.target = target
        self._factory = factory
        super().__init__(**kwargs)


    def set(self, host, collection):
        super().set(host, collection)
        setattr(host, self.target,
                self._factory.make('DataList', host.gen_data()))
        return True




class RecyclerView(DataView):
    '''
    Recyles widgets that are not yielded by gen_data().
    RecyclerView maintains the .displayed collection, using the models
    generated by gen_data() to update. displayed does not need to be set
    explicitly and will be destructively modified.
    '''

    displayed = CollectionProperty()
    data = RecyclerProperty('displayed')


    def gen_data(self):
        '''Default implementation iterates over self.data entirely.'''
        return iter(self.data)


    def update(self, collection):
        '''Step through the current data and match in place.'''
        displayed = self.displayed
        index = -1

        for model in self.gen_data():
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



class Controller(Widget):
    '''
    Manages inputs and delegates commands.
    The Controller calls command methods on Interactive widgets. Key binds and
    command method names are set in {app}.ini. Up to four Interactive widgets
    are held by the following ActiveProperties:
    .root, .page, .region, .focus
    Assigning an Interactive widget to any of these properties will cause it
    to recieve commands. Command methods are of the format:
    def on_{cmd}(self, controller):
    Commands dont bubble and are searched in order; focus, region, page, root.
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
    '''
    PKApp is the base application class.

    On instantiation it parses the config file and instantiates the with the
    keybinds. If on_start is overrided, super().onstart() should be called.
    '''

    def __init__(self, **kwargs):
        super().__init__(**kwargs)


    def on_start(self):
        binds = {}
        for cmd, key_list in self.config.items('keybinds'):
            for key in json.loads(key_list):
                binds[key] = 'on_{}'.format(cmd)

        self.controller = Controller(binds=binds, root=self.root)




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


    index = AliasProperty(_get_index, _set_index)
    current = AliasProperty(_get_current, _set_current, bind=['index','data'])
    data = ObjectProperty(None)


    def __init__(self, index=0, **kwargs):
        self._index = index
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



def load_kv(*args):
    Builder.load_file(join(*args))

