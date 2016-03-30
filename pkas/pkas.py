"""
Personal Kivy Application System

This module provides a data and ui abstraction layer on top of kivy.
The module supports three primary features: Recycling of DataModels and
DataWidgets, views for displaying DataCollections, and a control system
which delegates to Interactive Widgets.

class Factory(object):
factory = Factory() # Singleton
def specify(Ctor, stack_length=STACK_LEN):

class DataModel(EventDispatcher):
class DataCollection(DataModel):
class DataList(DataCollection, MutableSequence):
class DataDeque(DataList):
class DataDict(DataCollection, MutableMapping):
class DataSet(DataCollection, MutableSet):
class FileContext(DataModel, MutableMapping):

class DataProperty(ObjectProperty):
class SelectorProperty(DataProperty):
class DataWidget(Widget):

class CollectionProperty(ObjectProperty):
class DataView(Layout):
class ListView(DataView):
class DictView(Layout):
class SetView(Layout):

class ReducerProperty(CollectionProperty):
class ListReducerView(ListView):
class DequeReducerView(ListView):
class DictReducerView(DictView):
class SetReducerView(SetView):

class Interactive(EventDispatcher):
class ActiveProperty(ObjectProperty):
class Controller(Widget):
class PKApp(App):

class Walker(EventDispatcher):
def load_kv(*args):
"""

from collections import defaultdict, deque, OrderedDict
from collections.abc import MutableSequence, MutableMapping, MutableSet
import json
from random import random
from os.path import join

from kivy.app import App
from kivy.clock import Clock
from kivy.event import EventDispatcher
from kivy.properties import (AliasProperty, BooleanProperty,
                            NumericProperty, ObjectProperty,StringProperty)
from kivy.lang import Builder
from kivy.uix.layout import Layout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.widget import Widget
from kivy.core.window import Window


STACK_LEN = 10
LOG = True
def log(*args):
    if LOG: print(*args)



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
        try: Ctor = self._ctors[cls]
        except KeyError:
            raise Exception('factory.make:', cls, 'not specified.')

        try:
            obj = self._recycled[cls].pop().reinit(*args, **kwargs)
            log('Factory:\tReused:', obj, kwargs)
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

        log('Factory:\tRecycled:', obj)


    def set_stack_length(self, cls, length):
        self._stack_lengths[cls] = length
        recycled = self._recycled[cls]

        if len(recycled) > length:
            self._recycled[cls] = recycled[:length]



    def specify(self, Ctor, length):
        '''Specifies a class and stack len for production by the factory.'''
        self._ctors[Ctor.__name__] = Ctor
        self._stack_lengths[Ctor.__name__] = length




factory = Factory() # Singleton

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
    save = []

    def __eq__(self, other): return self is other
    def __ne__(self, other): return self is not other
    def __init__(self, _id=None, *args, **kwargs):
        self._id = _id
        super().__init__(*args, **kwargs)

    def recycle(self):
        self._id = None
        for prop in self.properties().values():
            prop.set(self, prop.defaultvalue)
        return self

    def reinit(self, _id=None, **kwargs):
        self._id = _id
        for k, v in kwargs.items():
            setattr(self, k, v)
        return self

    def load(self, context):
        for prop in self.properties().values():
            if isinstance(prop, DataProperty):
                prop.get(self).load(context)

    def to_json(self):
        output = []
        entries = []
        output.append('{\n')
        append = entries.append
        append('  "__class__" : "{}"'.format(self.__class__.__name__))
        for prop_name in self.save:
            value = getattr(self, prop_name)
            if isinstance(value, DataCollection): value = value.to_json()
            elif isinstance(value, DataModel): value = value._id
            append('  "{}" : {}'.format(prop.name, value))
        output.append(',\n'.join(entries))
        output.append('  }')
        return ''.join(output)

    # def __repr__(self):
    #     return '_id:{}'.format(self._id)



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
    def __init__(self, **kwargs):
        for event in self.events: self.register_event_type(event)
        super().__init__(**kwargs)

    def _cast(self, other):
        return other.data if isinstance(other, DataCollection) else other

    def recycle(self):
        self.data.clear()
        super().recycle()

    def reinit(self, data=None, *args, **kwargs):
        self.data = data
        super().reinit(*args, **kwargs)




@specify
class DataList(DataCollection, MutableSequence):
    '''
    List implementation of DataCollection.
    '''
    events = 'on_del','on_set','on_clear','on_insert','on_update','on_swap'
    def on_insert(self,i,x): pass
    def on_clear(self): pass
    def on_del(self,i): pass
    def on_set(self,i,x): pass
    def on_update(self): pass
    def on_swap(self,a,b): pass

    def __init__(self, data=None, **kwargs):
        super().__init__(**kwargs)
        if data is not None:
            if not isinstance(data, MutableSequence):
                raise TypeError('DataList passed non MutableSequence.', data)
            self.data = data
        else: self.data = []
    def __iter__(self): return iter(self.data)
    def __lt__(self, other): return self.data <  self._cast(other)
    def __le__(self, other): return self.data <= self._cast(other)
    def __eq__(self, other): return self.data == self._cast(other)
    def __ne__(self, other): return self.data != self._cast(other)
    def __gt__(self, other): return self.data >  self._cast(other)
    def __ge__(self, other): return self.data >= self._cast(other)
    def __contains__(self, item): return item in self.data
    def __len__(self): return len(self.data)
    def __reversed__(self): return reversed(self.data)
    def __getitem__(self, index): return self.data[index]
    def __setitem__(self, index, item):
        self.data.__setitem__(index, item)
        self.dispatch('on_set', index, item)
    def __delitem__(self, index):
        del self.data[index]
        self.dispatch('on_del', index)
    def __add__(self, other):
        if isinstance(other, DataList):
            return self.__class__(self.data + other.data)
        elif isinstance(other, type(self.data)):
            return self.__class__(self.data + other)
        return self.__class__(self.data + list(other))
    def __radd__(self, other):
        if isinstance(other, DataList):
            return self.__class__(other.data + self.data)
        elif isinstance(other, type(self.data)):
            return self.__class__(other + self.data)
        return self.__class__(list(other) + self.data)
    def __iadd__(self, other):
        if isinstance(other, DataList):
            self.data += other.data
        elif isinstance(other, type(self.data)):
            self.data += other
        else:
            self.data += list(other)
        self.dispatch('on_update')
        return self
    def __mul__(self, n):
        return self.__class__(self.data*n)
    def __imul__(self, n):
        self.data *= n
        self.dispatch('on_update')
        return self
    __rmul__ = __mul__
    def append(self, item):
        self.data.append(item)
        self.dispatch('on_insert', len(self)-1, item)
    def clear(self):
        self.data.clear()
        self.dispatch('on_clear')
    def copy(self): return self.__class__(self.data.copy())
    def count(self, item): return self.data.count(item)
    def extend(self, L):
        self.data.extend(L)
        self.dispatch('on_update')
    def index(self, item):
        return self.data.index(item)
    def insert(self, index, item):
        self.data.insert(index, item)
        self.dispatch('on_insert', index, item)
    def pop(self, index=None):
        self.data.pop(index)
        self.dispatch('on_del', index)
    def remove(self, item):
        index = self.data.index(item)
        del self[index]
        self.dispatch('on_del', index)
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
                self.data[index] = context[item]

    def to_json(self):
        ent = []
        out = []
        out.append('{')
        ent.append('"__class__":"{}"'.format(self.__class__.__name__))
        ent.append('"data":"[{}]"'.format(','.join(i._id for i in self.data)))
        out.append(','.join(ent))
        out.append('}')
        return ''.join(out)



@specify
class DataDeque(DataList):

    def __init__(self, data=None, **kwargs):
        if data is not None: data = deque(data)
        else: data = deque()
        super().__init__(data)

    def appendleft(self, x):
        self.data.appendleft(x)
        self.dispatch('on_insert', 0, x)

    def popleft(self):
        self.data.popleft()
        self.dispatch('on_del', 0)



@specify
class DataDict(DataCollection, MutableMapping):
    '''
    Dict implementation of DataCollection.
    Supports DataCollection event interface and file loading.
    '''
    events = 'on_del','on_set','on_clear','on_update'
    def on_del(self,k,v): pass
    def on_set(self,k,v): pass
    def on_clear(self): pass
    def on_update(self): pass

    def __init__(self, data=None, **kwargs):
        if data is not None:
            if not isinstance(data, MutableMapping):
                raise TypeError('DataDict passed non MutableMapping.', data)
        else:
            data = dict()
            props = self.properties()
            for kw in kwargs:
                if kw not in props: data[kw] = kwargs.pop(kw)

        super().__init__(**kwargs)
        self.data = data

    def __eq__(self, other): return self.data == self._cast(other)
    def __ne__(self, other): return self.data != self._cast(other)
    def __getitem__(self, key): return self.data[key]
    def __setitem__(self, key, value):
        self.data[key] = value
        self.dispatch('on_set', key, value)
    def __delitem__(self, key):
        del self.data[key]
        self.dispatch('on_del', key)
    def __iter__(self): return iter(self.data)
    def __len__(self): return len(self.data)
    def __contains__(self, key): return key in self.data
    def copy(self): return self.__class__(self.data.copy())

    def clear(self):
        self.data.clear()
        self.dispatch('on_clear')

    @classmethod
    def fromkeys(cls, iterable, value=None):
        d = cls()
        for key in iterable:
            d[key] = value
        return d

    def get(self, key, default=None): return self.data.get(key, default)
    def items(self): return self.data.items()
    def keys(self): return self.data.keys()
    def values(self): return self.data.values()
    def setdefault(self, key, default=None):
        self.data.setdefault(key, default)

    def pop(self, key):
        item = self.data.pop(key)
        self.dispatch('on_del', key)
        return item

    def popitem(self):
        key, item = self.data.pop(key)
        self.dispatch('on_del', key)
        return key, item

    def update(self, *args, **kwargs):
        self.data.update(*args, **kwargs)
        self.dispatch('on_update')

    def load(self, context):
        '''If any data items are still _ids, load the models from context.'''
        data = self.data
        for key, value in data:
            if type(value) is str:
                self.data[key] = context[value]

    def to_json(self):
        output = []
        entries = []
        output.append('{')
        entries.append('"__class__":"{}"'.format(self.__class__.__name__))
        data = []
        for key, value in self.data:
            data.append('"{}":"{}"'.format(key, value._id))
        entries.append('"data":{{}}'.format(','.join(entries)))
        output.append(','.join(entries))
        output.append('}')
        return ''.join(output)



class DataSet(DataCollection, MutableSet):
    events = 'on_discard','on_add','on_clear','on_update'
    def on_discard(self,x): pass
    def on_add(self,x): pass
    def on_clear(self): pass
    def on_update(self): pass

    def __init__(self, data=None, **kwargs):
        if data is not None:
            if not isinstance(data, MutableSet):
                raise TypeError('DataSet passed non MutableSet.', data)
        else:
            data = set()

        super().__init__(**kwargs)
        self.data = data

    def __contains__(self, item): return self.data.contains(item)
    def __iter__(self): return iter(self.data)
    def __len__(self): return len(self.data)
    def __le__(self, other): return self.data <= self._cast(other)
    def __lt__(self, other): return self.data < self._cast(other)
    def __eq__(self, other): return self.data == self._cast(other)
    def __ne__(self, other): return self.data != self._cast(other)
    def __gt__(self, other): return self.data > self._cast(other)
    def __ge__(self, other): return self.data >= self._cast(other)
    def __and__(self, other): return self.data & self._cast(other)
    def __or__(self, other): return self.data | self._cast(other)
    def __sub__(self, other): return self.data - self._cast(other)
    def __xor__(self, other): return self.data ^ self._cast(other)
    def __ior__(self, other):
        self.data |= self._cast(other)
        self.dispatch('on_update')
    def __iand__(self, other):
        self.data &= self._cast(other)
        self.dispatch('on_update')
    def __ixor__(self, other):
        self.data ^= self._cast(other)
        self.dispatch('on_update')
    def __isub__(self, other):
        self.data -= self._cast(other)
        self.dispatch('on_update')
    def add(self, item):
        self.data.add(item)
        self.dispatch('on_add', item)
    def discard(self, item):
        self.data.discard(item)
        self.dispatch('on_discard', item)
    def clear(self):
        self.data.clear()
        self.dispatch('on_clear')
    def copy(self): return self.__class__(self.data.copy())
    def isdisjoint(self): return isdisjoint(self.data)
    def pop(self):
        item = self.data.pop()
        self.dispatch('on_discard', item)
        return item
    def remove(self, item):
        self.data.remove(item)
        self.dispatch('on_discard', item)

    def load(self, context):
        '''If any data items are still _ids, load the models from context.'''
        data = self.data
        for item in data:
            if type(item) is str:
                data.remove(item)
                data.add(context[item])

    def to_json(self):
        ent = []
        out = []
        out.append('{')
        ent.append('"__class__":"{}"'.format(self.__class__.__name__))
        ent.append('"data":"{{}}"'.format(','.join(i._id for i in self.data)))
        out.append(','.join(ent))
        out.append('}')
        return ''.join(out)



@specify
class FileContext(DataModel, MutableMapping):
    '''
    DataModel for saving to and loading from files.

    Objects are stored by a unique key that is added as an attribute when
    the model is added to the context. This key remains with the object
    through saving.
    '''

    name = StringProperty('default')
    filename = StringProperty('')
    data = ObjectProperty(None, baseclass=dict)


    def __init__(self, mode='json', **kwargs):
        super().__init__(**kwargs)
        self.mode = mode

    # def __repr__(self):
    #     return 'Cotnext {}: {}'.format(self.name, self.data)
    def __len__(self): return len(self.data)
    def __iter__(self): return iter(self.data)
    def __contains__(self, key): return key in self.data
    def __delitem__(self, key): del self.data[key]
    def __setitem__(self, key, value): self.data[key] = value
    def __getitem__(self, key): return self.data[key]
    def get(self, key): return self.data[key]
    def delete(self, key): del self.data[key]
    def put(self, value):
        try: _id = value._id
        except AttributeError: _id = value._id = self._get_id()
        else:
            if _id in self.data: raise ValueError('ID already in File')
        self.data[_id] = value


    def _get_id(self):
        for i in range(3):
            _id = random()
            try: self[_id]
            except KeyError:
                return _id

        raise Exception('Did not create unique _id after 3 tries!')


    def save(self):
        '''Iterate over keys, items.to_{mode}() and write to self.filename'''
        log('Saving:', self)

        with open(self.filename, 'w') as f:
            f.write('pkas:mode={}\n'.format(self.mode))
            for output in getattr(self, 'to_{}'.format(self.mode))():
                f.write(output)


    def to_json(self):
        yield ('{\n')
        for _id, model in self.data.items():
            yield ('"{}" : {},\n'.format(_id, getattr(model, 'to_json')()))
        yield ('"name" : "{}"\n'.format(self.name))
        yield ('}\n')


    def load(self):
        '''Parse filename as json, update self and call load() on items.'''
        make = self.factory.make
        with open(self.filename, 'r') as f:
            data = json.load(file = f, object_hook = lambda d:
                make(d.pop('__class__'), **d) if '__class__' in d else d)

        self.name = data.pop('name')
        self.data = data
        for model in data.values():
            model.load(self)



class DataProperty(ObjectProperty):
    '''For models to hold other models.'''

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

    def __init__(self, allownone=True, **kwargs):
        super().__init__(allownone=allownone, **kwargs)

    def set(self, obj, new_value):
        old_value = super().get(obj)
        super().set(obj, new_value)
        if old_value is not None: old_value.is_selected = False
        if new_value is not None: new_value.is_selected = True
        return True



class DataWidget(Widget):
    '''
    Widget that represents a DataModel.
    Expects a cls.defaultmodel instance as a fallback for kv bindings.
    Implements the methods reinit(**kwargs) and recycle() for recycling.
    '''

    model = DataProperty(factory.make('DataModel'))

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

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

    def __init__(self, baseclass=DataCollection, **kwargs):
        super().__init__(None, allownone=True, baseclass=baseclass, **kwargs)


    def _bind(self, host, collection):
        uid_propname = '_uids_{}'.format(self.name)
        uids = getattr(host, uid_propname, [])
        fbind = collection.fbind

        for event in collection.events:
            callback = getattr(host, event, None)
            if callback is not None: uids.append(fbind(event, callback))
        setattr(host, uid_propname, uids)

        log('Bound collection', host, uid_propname, collection)


    def _unbind(self, host, old_collection):
        uids = getattr(host, '_uids_{}'.format(self.name))
        unbind_uid = old_collection.unbind_uid

        for event in reversed(old_collection.events):
            callback = getattr(host, event, False)
            if callback:
                unbind_uid(event, uids.pop())

        log('Unbound collection', host, old_collection)


    def set(self, host, collection):
        old_collection = self.get(host)
        if old_collection is not None:
            self._unbind(host, old_collection)

        if collection is not None:
            self._bind(host, collection)

        super().set(host, collection)
        return True



class DataView(Layout):

    data = CollectionProperty(baseclass=DataCollection)
    cls = AliasProperty(lambda s: getattr(s, '_cls'),
                        lambda s,v: setattr(s, '_cls', v.__name__),
                        bind=[])


    def __init__(self, **kwargs):
        self.factory = factory
        super().__init__(**kwargs)

    def recycle(self):
        self.data = None
        return self

    def reinit(self, **kwargs):
        for k, v in kwargs.items(): setattr(self, k, v)
        return self

    def update(self):
        self.on_update(self.data)



class ListView(DataView):
    '''Layout that keeps a list collection in sync with data.'''

    data = CollectionProperty(baseclass=DataList)
    def detach(self): self.data = None

    def get_child_index(self, child):
        '''Returns the child widget index's position in the DataList.'''
        return len(self.children) - 1 - self.children.index(child)

    def on_del(self, data, i):
        i = len(self.children) - 1 - i
        widget = self.children[i]
        self.remove_widget(widget)
        self.factory.recycle(widget)

    def on_set(self, data, i, model):
        i = len(self.children) - 1 - i
        factory = self.factory
        old_widget = self.children[i]

        self.remove_widget(old_widget)
        factory.recycle(old_widget)
        widget = factory.make(self.cls, model=model)
        self.add_widget(widget, i)

    def on_clear(self, data):
        recycle = self.factory.recycle
        for widget in self.children:
            recycle(widget)
        self.clear_widgets()

    def on_insert(self, data, i, model):
        widget = self.factory.make(self.cls, model=model)
        i = len(self.children) - i
        self.add_widget(widget, i)

    def on_swap(self, data, a, b):
        children = self.children
        l =  len(children) - 1
        a, b = (l - a), (l - b)
        children[a], children[b] = children[b], children[a]

    def on_update(self, data):
        recycle = self.factory.recycle
        for widget in self.children: recycle(widget)
        self.clear_widgets()

        if data:
            add_widget = self.add_widget
            cls = self.cls
            make = self.factory.make
            for model in data: add_widget(make(cls, model=model))




class DictView(Layout):
    '''Layout that keeps children in sync with data.'''

    data = CollectionProperty(baseclass=DataDict)
    def detach(self): self.data = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.widgets = {}

    def on_del(self, data, key):
        widget = self.widgets.pop(key)
        self.remove_widget(widget)
        self.factory.recycle(widget)

    def on_set(self, data, key, model):
        factory = self.factory
        try: old_widget = self.widgets[key]
        except KeyError: pass
        else:
            self.remove_widget(old_widget)
            factory.recycle(old_widget)

        widget = factory.make(self.cls, model=model)
        self.widgets[key] = widget
        self.add_widget(widget)

    def on_clear(self, data):
        recycle = self.factory.recycle
        for widget in self.children:
            recycle(widget)
        self.widgets.clear()
        self.clear_widgets()


    def on_update(self, data):
        widgets = self.widgets
        recycle = self.factory.recycle
        for widget in self.children: recycle(widget)
        self.clear_widgets()
        self.widgets.clear()

        if data:
            add_widget = self.add_widget
            cls = self.cls
            make = self.factory.make
            for key, model in data:
                widget = make(cls, model=model)
                add_widget(widget)
                widgets[key] = widget




class SetView(Layout):
    '''Layout that keeps children in sync with data.'''

    data = CollectionProperty(baseclass=DataSet)
    def detach(self): self.data = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.widgets = {}

    def on_discard(self, data, item):
        widget = self.widgets.pop(id(item))
        self.remove_widget(widget)
        self.factory.recycle(widget)

    def on_add(self, data, model):
        _id = id(model)
        try: self.widgets[_id]
        except KeyError: pass
        else: return

        widget = self.factory.make(self.cls, model=model)
        self.widgets[_id] = widget
        self.add_widget(widget)

    def on_clear(self, data):
        recycle = self.factory.recycle
        for widget in self.children:
            recycle(widget)
        self.widgets.clear()
        self.clear_widgets()

    def on_update(self, data):
        widgets = self.widgets
        recycle = self.factory.recycle
        for widget in self.children: recycle(widget)
        self.clear_widgets()
        self.widgets.clear()

        if data:
            add_widget = self.add_widget
            cls = self.cls
            make = self.factory.make
            for model in data:
                widget = make(cls, model=model)
                add_widget(widget)
                widgets[id(model)] = widget




class ReducerProperty(CollectionProperty):
    '''
    Instead of binding to callbacks of event names on the host like the
    CollectionProperty, the RecyclerProperty accepts a target
    CollectionProperty to update with the contents yielded by generator.
    '''

    def __init__(self, target_name, **kwargs):
        super().__init__(**kwargs)
        self.factory = factory
        self.target_name = target_name


    def _bind(self, host, collection):
        fbind = collection.fbind
        uid_propname = '_uids_{}'.format(self.name)
        uids = getattr(host, uid_propname, [])
        update = getattr(host, 'update_{}'.format(self.target_name))

        # # bind every event to update()
        for event in collection.events:
            uids.append(fbind(event, update))

        setattr(host, uid_propname, uids)
        log('Bound collection', host, uid_propname, collection)

        update(collection)


    def _unbind(self, host, old_collection):
        uids = getattr(host, '_uids_{}'.format(self.name))
        unbind_uid = old_collection.unbind_uid

        for event in reversed(old_collection.events):
            unbind_uid(event, uids.pop())


    def set(self, host, collection):
        super().set(host, collection)
        return True



class ListReducerView(ListView):

    displayed = CollectionProperty(baseclass=DataList)
    data = ReducerProperty('displayed')
    def detach(self): self.displayed = None; self.data = None

    def __init__(self, displayed=None, **kwargs):
        if displayed is None: self.displayed = factory.make('DataList')
        else: self.displayed = displayed
        super().__init__(**kwargs)


    def update_displayed(self, *evt_args):
        '''
        Step through the current list and match in place.
        Requires target DataCollection to implement swap!
        (i.e. this should go in the ListReducer)
        '''
        displayed = self.displayed
        index = -1

        for model in self.gen_displayed():
            index += 1
            try:
                current = displayed[index]
                if current is not model:
                    i = displayed.index(model)
                    displayed.swap(index, i)
                    log('update: swapped', current.name, model.name)
                continue
            except (IndexError, ValueError): pass

            displayed.insert(index, model)
            log('update: inserted', model.name)

        for i in reversed(range(index + 1, len(displayed))):
            del displayed[i]


    def gen_displayed(self): return iter(self.data)



class DequeReducerView(ListView):

    displayed = CollectionProperty(baseclass=DataDeque)
    data = ReducerProperty('displayed')
    displayed_index = NumericProperty(0)
    displayed_total = NumericProperty(10)

    def detach(self): self.displayed = None; self.data = None
    def on_displayed_index(self, _, index): self.update_displayed()
    def on_displayed_total(self, _, index): self.update_displayed()

    def __init__(self, displayed=None, **kwargs):
        if displayed is None: self.displayed = factory.make('DataDeque')
        else: self.displayed = displayed
        super().__init__(**kwargs)


    def update_displayed(self, *evt_args):
        '''
        Like list but with special case first entry
        '''
        data = self.data
        displayed = self.displayed
        index = 0

        try: model = data[self.displayed_index]
        except: displayed.clear(); return
        try: current = displayed[index]
        except: displayed.append(model)
        else:
            if current is not model:
                try: i = displayed.index(model)
                except ValueError: displayed.appendleft(model)
                else: displayed.swap(index, i)

        for index in range(1, self.displayed_total):
            try: model = data[self.displayed_index + index]
            except: break
            try: current = displayed[index]
            except: pass
            else:
                try:
                    if current is not model:
                        i = displayed.index(model)
                        displayed.swap(index, i)
                    continue
                except ValueError: pass
            displayed.insert(index, model)
        else: index += 1

        for i in reversed(range(index, len(displayed))):
            del displayed[i]



    def scroll_up(self, amt=1):
        if self.displayed_index > 0:
            self.displayed_index -= 1
            self.update_displayed()


    def scroll_down(self, amt=1):
        if self.displayed_index < len(self.data) - 1:
            self.displayed.popleft()
            self.displayed_index += 1
            self.update_displayed()





class DictReducerView(DictView):

    displayed = CollectionProperty(baseclass=DataDict)
    data = ReducerProperty('displayed')
    def detach(self): self.displayed = None; self.data = None

    def __init__(self, displayed=None, **kwargs):
        if displayed is None: self.displayed = factory.make('DataDict')
        else: self.displayed = displayed
        super().__init__(**kwargs)


    def update_displayed(self, *evt_args):
        current_keys = set()
        displayed = self.displayed

        for key, model in self.gen_displayed():
            current_keys.add(key)
            try: displayed[key]
            except: displayed[key] = model

        for key in current_keys.symmetric_difference(displayed):
            del displayed[key]



class SetReducerView(SetView):

    displayed = CollectionProperty(baseclass=DataSet)
    data = ReducerProperty('displayed')
    def detach(self): self.displayed = None; self.data = None

    def __init__(self, displayed=None, **kwargs):
        if displayed is None: self.displayed = factory.make('DataSet')
        else: self.displayed = displayed
        super().__init__(displayed=displayed, **kwargs)

    def update_displayed(self, *evt_args):
        # add each value to set; delete symmetric difference
        current_models = set()
        displayed = self.displayed

        for model in self.gen_displayed():
            current_models.add(model)
            if model not in displayed:
                displayed.add(model)

        for model in current_models.symmetric_difference(displayed):
            displayed.remove(model)




class Interactive(EventDispatcher):
    '''Mixin for Interactive Widgets'''
    is_active = BooleanProperty(False)
    stop_propogation = BooleanProperty(False)
    def on_active(self, controller): pass
    def on_inactive(self, controller): pass




class ActiveProperty(ObjectProperty):
    '''Activates and Deactivates Interactive Widgets'''

    def __init__(self, allownone=True, baseclass=Interactive, **kwargs):
        super().__init__(allownone=allownone, baseclass=baseclass, **kwargs)


    def set(self, obj, value):
        old_value = super().get(obj)
        if value is old_value: return False

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

    file = ObjectProperty(None, allownone=True)
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
        self.factory = factory


    # Modal control locking?
    def _on_key_down(self, keyboard, keycode, text, modifiers):
        num_modifiers = len(modifiers)

        if num_modifiers is 0:
            input_keys = keycode[1]
        elif num_modifiers is 1:
            input_keys = ''.join(['{} '.format(modifiers[0]), keycode[1]])
        else:
            input_keys = ''.join(['ctrl shift ', keycode[1]])

        try: cmd = self.binds[input_keys]
        except KeyError: return False

        print('focus:', self.focus)
        if self.focus is not None:
            try:
                cb = getattr(self.focus, cmd)
            except AttributeError:
                if self.focus.stop_propogation: return
            else:
                if not cb(self): return

        print('region:', self.region)
        if self.region is not None:
            try:
                cb = getattr(self.region, cmd)
            except AttributeError:
                if self.region.stop_propogation: return
            else:
                if not cb(self): return

        if self.page is not None:
            try:
                cb = getattr(self.page, cmd)
            except AttributeError:
                if self.page.stop_propogation: return
            else:
                if not cb(self): return

        if self.root is not None:
            try:
                cb = getattr(self.root, cmd)
            except AttributeError:
                if self.root.stop_propogation: return
            else:
                if not cb(self): return


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
        for cmd, data in self.config.items('keybinds'):
            data = json.loads(data)
            if type(data) is str:
                binds[data] = 'on_{}'.format(cmd)
            else:
                for key in data:
                    binds[key] = 'on_{}'.format(cmd)

        self.controller = Controller(binds=binds, root=self.root)




class Walker(EventDispatcher):
    '''Convenience class for walking lists.'''

    def _get_index(self):
        return self._index

    def _set_index(self, i):
        self._index = i
        return True

    def _get_current(self):
        _index = self._index
        try: return self.data[_index]
        except TypeError: return None
        except IndexError: pass

        _max = len(self.data) - 1
        if _max == -1: return None

        self.index = _max
        return self.data[_max]

    def _set_current(self, current):
        try: index = self.data.index(current)
        except ValueError: return False
        else: self.index = index
        return True


    index = AliasProperty(_get_index, _set_index)
    current = AliasProperty(_get_current, _set_current, bind=['index','data'])
    data = ObjectProperty(None, allownone=True)


    def __init__(self, index=0, **kwargs):
        self._index = index
        super().__init__(**kwargs)


    def inc(self):
        length = len(self.data)
        if self.index < length - 1: self.index += 1
        else: self.index = self.index # Dispatch regardless

    def dec(self):
        if self.index > 0: self.index -= 1
        else: self.index = self.index


    def update(self): self.index = self.index


def load_kv(*args):
    Builder.load_file(join(*args))

