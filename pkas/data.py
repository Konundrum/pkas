import json
from collections import defaultdict, UserDict, UserList
from kivy.event import EventDispatcher
from kivy.properties import BooleanProperty, ObjectProperty, StringProperty



STACK_LEN = 10



class Factory(object):
    '''The Facotry maintains an object pool of DataModels and DataWidgets.

    Items to be recycled by the factory must implement both
    .init(self, **kwargs) and .recycle(self), which will be used by the
    Factory to setup and teardown objects. The Factory maintains a queue
    for each class, the lengths of which may be set dynamically.
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
        try:
            Ctor = self._ctors[cls]
        except KeyError:
            raise Exception('factory.make:', cls, 'not specified.')

        try:
            return self._recycled[cls].pop().init(*args, **kwargs)
        except IndexError:
            return Ctor(*args, **kwargs)


    def recycle(self, obj):
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
        self._ctors[Ctor.__name__] = Ctor
        self._stack_lengths[Ctor.__name__] = length



factory = Factory()



def specify(Ctor, stack_length=STACK_LEN):
    factory.specify(Ctor, stack_length)
    return Ctor



class DataProperty(ObjectProperty):
    '''For DataModels to hold DataCollections. Used for load detection.'''
    pass



@specify
class DataModel(EventDispatcher):
    '''Model that supports object recycling and file loading.'''

    is_selected = BooleanProperty(False)


    def init(self, _id=None, **kwargs):
        self._id = _id
        for k, v in kwargs.items():
            setattr(self, k, v)
        return self


    def recycle(self):
        self._id = None
        for prop in self.properties():
            prop.set(self, prop.defaultvalue)
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
    '''Base Collection class to hold collections of DataModels. The events
    are used keep a DataView's children in sync. DataCollection may be
    subclassed and provide a different collection->view event interface by
    overriding the events list and providing the relevant methods.
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



@specify
class DataList(DataCollection, UserList):
    '''List implementation of DataCollection.
    Supports the DataCollection event interface and file loading.
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
    '''Dict implementation of DataCollection.
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



from random import random

@specify
class DataContext(DataDict):
    '''DataDict for saving to and loading from files.

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


    def load(self):
        '''Parse filename as json, update the dict and call load() on each.'''
        make = self.factory.make
        with open(self.filename, 'r') as f:
            data = json.load(file = f, object_hook = lambda dct:
                    make(dct.pop('class'), dct) if 'class' in dct else dct )

        self.name = data.pop('name')
        self.update(data)

        for model in data.values():
            model.load(self)


    def save(self):
        '''Iterate over items.to_json() and write to self.filename'''
        with open(self.filename, 'w') as f:
            for string in self.to_json():
                f.write(string)


    def to_json(self):
        '''Generator used by save() to write each object as json.'''
        yield '{\n'
        yield '"name" : "{}",\n'.format(self.name)
        for _id, model in self:
            yield '"{}" : {}'.format(_id, model.to_json())
        yield '}\n'
        raise StopIteration


    def on_save(self):
        pass
    def on_load(self):
        pass



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

