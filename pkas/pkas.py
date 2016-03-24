"""
Personal Kivy Application System

This module provides a data and ui abstraction layer on top of kivy.
The module supports three primary features: Recycling of DataModels and
DataWidgets, views for displaying DataCollections, and a control system
which delegates to Interactive widgets.
"""

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

    Items to be recycled by the factory must implement both reinit(kwargs)
    and recycle(), which are used by the Factory to setup and teardown
    objects. The Factory maintains a stack for each class, the lengths
    of which may be set by set_stack_length.
    '''

    _inst = None  #Singleton reference

    def __new__(cls):
        if cls._inst is None:
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
            obj = self._recycled[cls].pop().reinit(*args, **kwargs)
            print('reused:', obj)
            return obj
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

        print('Recycled:', obj)


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
    can be used to keep a DataView's children in sync. DataCollection
    can be subclassed to provide a different collection event interface,
    by overriding the events list and providing corresponding methods.
    The recycle and reinit methods provided here clear and set
    collection.data. If this is undesirable you may wish to call the
    parent DataWidget methods directly while implementing your own.
    '''

    events = ['on_del','on_set','on_clear','on_insert','on_update','on_swap']

    fallback = lambda *args: None
    for event in events:
        locals()[event] = fallback
    del locals()['fallback']

    def __init__(self, *args, **kwargs):
        for event in self.events:
            self.register_event_type(event)
        super().__init__(*args, **kwargs)

    def recycle(self):
        self.data.clear()
        super().recycle()

    def reinit(self, data=None, *args, **kwargs):
        self.data = data
        super().reinit(*args, **kwargs)

    def swap(self, a, b):
        pass
    def load(self, context):
        pass
    def to_json(self):
        pass




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
        item = self[key]
        del self.keys[i]
        del self.data[key]
        factory.recycle(item)
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




class DataProperty(ObjectProperty):

    def __init__(self,
                 default = factory.make('DataModel'),
                 allownone = True,
                 baseclass = DataModel,
                 rebind = True,
                 **kwargs):

        super().__init__(default,
                         allownone = allownone,
                         baseclass = baseclass,
                         rebind = rebind,
                         **kwargs)




class SelectorProperty(DataProperty):
    '''Manages selection / deselection of models by assignment.'''

    def set(self, obj, value):
        old_value = super().get(obj)
        super().set(obj, value)

        if old_value is not None:
            old_value.is_selected = False

        if value is not None:
            value.is_selected = True

        return True




class DataWidget(Widget):
    '''
    Widget that represents a DataModel.
    Expects a cls.defaultmodel instance as a fallback for kv bindings.
    Implements the methods reinit(**kwargs) and recycle() for recycling.
    '''

    model = DataProperty(factory.make('DataModel'))


    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


    def recycle(self):
        self.model = self.property('model').defaultvalue
        return self


    def reinit(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)
        return self




class CollectionProperty(ObjectProperty):
    '''
    Property to bind and unbind from DataCollection events.
    Uses datacollection.events and host._{prop}_uids for event binding.
    '''

    def __init__(self, **kwargs):
        super().__init__(baseclass=DataCollection, **kwargs)
        self.uid_propname = '_{}_uids'.format(self.name)


    def _bind(self, host, collection):
        uids = getattr(host, self.uid_propname, [])
        fbind = collection.fbind
        for event in collection.events:
            callback = getattr(host, event, False)
            if callback:
                uids.append(fbind(event, getattr(host, event)))
        setattr(host, self.uid_propname, uids)


    def _unbind(self, host, old_collection):
        uids = getattr(host, self.uid_propname)
        unbind_uid = old_collection.unbind_uid
        for event in reversed(old_collection.events):
            callback = getattr(host, event, False)
            if callback:
                unbind_uid(event, uids.pop())


    def set(self, host, collection):
        old_collection = self.get(host)
        if old_collection is not None:
            self._unbind(host, old_collection)

        if collection is not None:
            self._bind(host, collection)

        super().set(host, collection)
        return True





class DataView(Layout):
    '''Layout that keeps children in sync with data.'''

    data = CollectionProperty()
    cls = AliasProperty(lambda s: getattr(s, '_cls'),
                        lambda s,v: setattr(s, '_cls', v.__name__),
                        bind=[])


    def __init__(self, *args, **kwargs):
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


    def recycle(self):
        self.data.clear()
        return self


    def reinit(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)
        return self




class RecyclerProperty(CollectionProperty):
    '''
    Instead of binding to callbacks of event names on the host like the
    CollectionProperty, the RecyclerProperty accepts a target
    CollectionProperty to update with the contents yielded by generator.
    '''

    def __init__(self, target, generator, gen_update=None, **kwargs):
        super().__init__(**kwargs)
        self._factory = factory
        self.generator = generator
        self.target = target
        if gen_update is not None:
            self.gen_update = gen_update


    def _bind(self, host, collection):
        uids = getattr(host, self.uid_propname, [])
        fbind = collection.fbind

        # bind every event to update()
        for event in collection.events:
            uids.append(fbind(event, self.gen_update(host)))

        setattr(host, self.uid_propname, uids)


    def _unbind(self, host, old_collection):
        uids = getattr(host, self.uid_propname)
        unbind_uid = old_collection.unbind_uid

        for event in reversed(old_collection.events):
            unbind_uid(event, uids.pop())


    def set(self, host, collection):
        super().set(host, collection)
        if self.target.get(host) is None:
            self.target.set(host,
                self._factory.make('DataList', self.generator(host)))
        return True


    def gen_update(self, host):
        def update(collection, *args):
            '''
            Step through the current data and match in place.
            Requires target DataCollection to implement swap!
            '''
            target = getattr(host, self.target.name)
            index = -1

            for model in self.generator(host):
                index += 1
                try:
                    current = target[index]
                    if current is not model:
                        i = target.index(model)
                        target.swap(index, i)
                        print('swapped', current.name, model.name)
                    continue
                except (IndexError, ValueError):
                    pass

                target.insert(index, model)
                print('inserted', model.name)

            for i in reversed(range(index + 1, len(target))):
                del target[i]

        return update





class RecyclerView(DataView):
    '''
    Recycles widgets that are not yielded by gen_data().
    RecyclerView maintains the .displayed collection, using the models
    generated by gen_data() to update. displayed does not need to be set
    explicitly and will be destructively modified.
    '''

    def gen_data(self):
        '''Default implementation yields all of self.data.'''
        return iter(self.data)


    displayed = CollectionProperty()
    data = RecyclerProperty(displayed, gen_data)




class Interactive(EventDispatcher):
    '''Mixin for Interactive Widgets'''

    is_active = BooleanProperty(False)

    def on_active(self, controller):
        pass
    def on_inactive(self, controller):
        pass




class ActiveProperty(ObjectProperty):
    '''Activates and Deactivates Interactive Widgets'''

    def __init__(self, allownone=True, baseclass=Interactive, **kwargs):
        super().__init__(allownone=allownone, baseclass=baseclass, **kwargs)


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
    The Controller calls command methods on Interactive widgets. Key
    binds and command method names are set in {app}.ini. Up to four
    Interactive widgets are held by the following ActiveProperties:
        .root, .page, .region, .focus

    Assigning an Interactive widget to any of these properties will
    cause it to recieve commands. Command methods are of the format:
        def on_{cmd}(self, controller):

    Command methods are searched for in order; focus, region, page, root.
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

