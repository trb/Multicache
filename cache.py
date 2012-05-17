from types import FunctionType

import backends


__storage = backends.default()
def set_storage(BackendInstance):
    global __storage
    __storage = BackendInstance


def make_cached(make_key, f):
        def cached(*args, **kwargs):
            cache_key = make_key(args=args, kwargs=kwargs)
            if __storage.has(cache_key):
                return __storage.get(cache_key)

            value = f(*args, **kwargs)
            __storage.set(cache_key, value)
            return value

        return cached


def cache_function(function_or_key):
    key = 'function:'
    if type(function_or_key) is FunctionType:
        """No args to decorator makes the first arg the
        function to be decorated"""
        f = function_or_key
        key = key + f.__name__
        def make_key(args=None, kwargs=None):
            return key + f.__name__ + str(args) + str(kwargs)

        return make_cached(make_key, f)
    else:
        """Arguments have been passed to the decorator.
        The user wants to override automatic key creation and always
        use the same, so do that here"""
        key += function_or_key
        def make_decorator(f):
            def make_key(args=None, kwargs=None):
                return key + ':' + f.__name__

            return make_cached(make_key, f)
        return make_decorator


__register = []
__open_queue = False
__in_init = False
__cache = {}
__next_provider = None
__update = []


def __register_update(id_, values):
    __update.append((id_, values))


def do_updates():
    global __update
    for id_, values in __update:
        __storage.set(id_, values)

    __update = []


def __do_queue():
    global __register
    global __cache
    global __open_queue

    __open_queue = False

    for id_, self, provider in __register:
        if not __storage.has(id_):
            __storage.set(id_, provider(self))

        self.__cached__ = __storage.get(id_)

    __register = []


def __register_class(id_, self, provider):
    global __open_queue

    __register.append((id_, self, provider))
    __open_queue = True


def __make_id(cls, self, id_attribute):
    return 'class:' + cls.__name__ + str(self.__dict__[id_attribute])


def __should_do_queue(self):
    if not __open_queue:
        return False

    if '__in_init' in self.__dict__:
        if self.__dict__['__in_init']:
            return False
    else:
        return False

    return True


def cache_class(id_attribute):
    """Cachable attributes don't have to be specified since
    self.__cached__.keys() will provide all attributes that were
    retrieved from cache (and could subsequently be updated).
    """
    def make_class(cls):
        global __next_provider
        if __next_provider is None:
            raise LookupError("No provider function declared. Put"
                              + " the 'cache_provider' decorator on the"
                              + " function that returns data for the"
                              + " instance")
        provider_function = __next_provider
        __next_provider = None

        old_init = cls.__init__
        def new_init(self, *args, **kwargs):
            self.__in_init = True
            old_init(self, *args, **kwargs)
            self.__in_init = False

            __register_class(__make_id(cls, self, id_attribute),
                             self, provider_function)
        cls.__init__ = new_init

        old_getattribute = cls.__getattribute__
        def new_getattribute(self, key):
            if key != '__dict__' and key != '__cached__':
                if __should_do_queue(self):
                    __do_queue()

                if hasattr(self, '__cached__') and key in self.__cached__:
                    return self.__cached__[key]

            return old_getattribute(self, key)
        cls.__getattribute__ = new_getattribute

        old_setattr = cls.__setattr__
        def new_setattr(self, key, value):
            if key != '__cache__':
                if __should_do_queue(self):
                    __do_queue()

            if hasattr(self, '__cached__'):
                """Only check for updatable cache values
                when a cache dict exists"""
                if not hasattr(self, '__cachable_attrs'):
                    self.__dict__['__cachable_attrs'] = \
                                        self.__dict__['__cached__'].keys()

                if key in self.__dict__['__cachable_attrs']:
                    if key != self.__dict__['__cached__'][key]:
                        self.__dict__['__cached__'][key] = value
                        __register_update(
                              __make_id(cls, self, id_attribute),
                              self.__cached__)
                        return

            old_setattr(self, key, value)
        cls.__setattr__ = new_setattr

        def hasattr(self, key):
            if __should_do_queue(self):
                __do_queue()

            if '__cache__' in self.__dict__:
                if key in self.__dict__['__cache__']:
                    return True

            if key in self.__dict__:
                return True

            return False
        cls.__hasattr__ = hasattr

        return cls
    return make_class


def cache_provider(f):
    global __next_provider
    __next_provider = f
    return f
