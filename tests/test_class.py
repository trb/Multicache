from ..cache import cache_class, cache_provider, set_storage, do_updates
from ..backends.Local import LocalBackend
from ..backends import Cache
from nose.tools import with_setup


_provider_count = 0


class MockBackend(Cache):
    def __init__(self, Backend):
        super(MockBackend, self).__init__(Backend)

    def get_storage(self):
        return self.backend._storage


storage = MockBackend(LocalBackend())
set_storage(storage)


@cache_class(id_attribute='user_id')
class C(object):
    def __init__(self, id_):
        self.user_id = id_

    @cache_provider
    def _provider(self):
        global _provider_count
        _provider_count += 1
        return {
                'name': 'User name ' + str(self.user_id),
                'id': self.user_id}


def setup():
    global storage
    storage = MockBackend(LocalBackend())
    set_storage(storage)


def teardown():
    global _provider_count
    _provider_count = 0


@with_setup(setup, teardown)
def test_class():
    """Test basic usage, setting attributes, instantiating a class, etc."""
    c1 = C(1)
    assert c1.name == 'User name 1'

    c1.name = 'Example user'
    assert c1.name == 'Example user'

    c1.new_field = 'new value'
    assert c1.new_field == 'new value'


@with_setup(setup, teardown)
def test_classes():
    """Make sure multiple instances don't overwrite each others values"""
    c1 = C(1)
    c2 = C(2)

    assert c1.name == 'User name 1'
    assert c2.name == 'User name 2'

    c2.name = 'Example user'
    assert c1.name == 'User name 1'
    assert c2.name == 'Example user'

    c2.new_field = 'new value'
    assert hasattr(c1, 'new_field') != True
    assert c2.new_field == 'new value'


@with_setup(setup, teardown)
def test_provider():
    """Provider should not be called when class is instantiated"""
    c1 = C(1)
    assert _provider_count == 0, 'Instantiating a class should not retrieve data'
    c2 = C(2)
    assert _provider_count == 0, 'Instantiating a second class should not retrieve data'

    c1.name # Access data, execute pipeline
    assert _provider_count == 2, 'Two objects from pipeline should be loaded'


@with_setup(setup, teardown)
def test_write():
    """Make sure that cache gets updated after cachable attributes are set"""
    import json

    c1 = C(1)

    c1.name = 'Testname'
    do_updates()
    s = storage.get_storage()['class:C1'][1]
    s = json.loads(s)
    assert s['name'] == 'Testname'


@with_setup(setup, teardown)
def test_has():
    """Check that hasattr works with auto-load attributes"""
    c1 = C(1)
    assert hasattr(c1, 'name'), 'This should be autoloaded when checking existence'
    assert _provider_count == 1, 'Provider should have been called'


@with_setup(setup, teardown)
def test_multi_write():
    """Make sure that writes into multiple classes don't interfere with
    each other"""
    import json

    c1 = C(1)
    c2 = C(2)

    c1.name = 'Testname one'
    c2.name = 'Testname two'

    do_updates()

    s = storage.get_storage()['class:C1'][1]
    s = json.loads(s)
    assert s['name'] == 'Testname one', 'Wrong name stored for first class'

    s = storage.get_storage()['class:C2'][1]
    s = json.loads(s)
    assert s['name'] == 'Testname two', 'Wrong name stored for second class'


@with_setup(setup, teardown)
def test_cache_read():
    """Make sure that provider isn't called if there's a cache hit, and the
    changed value in cache is respected"""
    c1 = C(1)

    c1.name = 'Some name'
    do_updates()

    c_test = C(1)
    assert c_test.name == 'Some name', 'Name is wrong in second instance'
    assert _provider_count == 1, 'Provider should only have been called once (second instance should be a cache hit)'
