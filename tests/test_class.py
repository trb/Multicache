from ..cache import cache_class, cache_provider, set_storage
from ..backends.Local import LocalBackend
from ..backends import Cache
from nose.tools import with_setup


_provider_count = 0


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
    set_storage(Cache(LocalBackend()))

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
