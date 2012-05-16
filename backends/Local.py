class LocalBackend(object):
    def __init__(self):
        self._storage = {}

    def store(self, key, data):
        self._storage[key] = data

    def retrieve(self, key):
        return self._storage[key]

    def check(self, key):
        return key in self._storage

    def remove(self, key):
        del self._storage[key]
