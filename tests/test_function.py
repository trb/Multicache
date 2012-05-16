from ..cache import cache_function, set_storage
from ..backends.Local import LocalBackend
from ..backends import Cache

from nose.tools import with_setup


__call_counter = 0


def __clear_cache():
    set_storage(Cache(LocalBackend()))


def __reset_call_counter():
    global __call_counter
    __call_counter = 0


@cache_function
def unique_key(a, b):
    global __call_counter
    __call_counter += 1
    return str(a) + ':' + str(b)


@cache_function('example_key')
def manual_key(a, b):
    global __call_counter
    __call_counter += 1
    return str(a) + ':' + str(b)


@cache_function
def complex_return_value(to_extend):
    global __call_counter
    __call_counter += 1

    l = ['one', 'two']
    l.extend(to_extend)
    dict = {
            'value': l
            }
    return dict


@with_setup(__clear_cache, __reset_call_counter)
def test_cache():
    """Make sure that a function called with the same parameters
    twice only executes once"""

    assert unique_key('one', 'two') == 'one:two'
    assert unique_key('one', 'two') == 'one:two'

    assert __call_counter == 1, 'Function was not cached'


@with_setup(__clear_cache, __reset_call_counter)
def test_multiple_args():
    """The same function called with varying arguments should
    be cached for each argument permutation"""

    assert unique_key('one', 'two') == 'one:two'
    assert unique_key('two', 'three') == 'two:three', 'Manually specified key was not used, different arguments give different results'

    assert __call_counter == 2, 'Function was not called for each permutation of arguments'


@with_setup(__clear_cache, __reset_call_counter)
def test_manual_key():
    """Specifying a manual key should return the value of the first
    function call for all subsequent calls"""

    assert manual_key('one', 'two') == 'one:two'
    assert manual_key('two', 'three') == 'one:two', 'Different arguments did not return the same value as the first call'

    assert __call_counter == 1


@with_setup(__clear_cache, __reset_call_counter)
def test_complex():
    assert complex_return_value(['three', 'four']) == {'value': ['one', 'two', 'three', 'four']}
    assert complex_return_value(['ten']) == {'value': ['one', 'two', 'ten']}

    assert __call_counter == 2, 'Function was not called for each permutation of arguments'
