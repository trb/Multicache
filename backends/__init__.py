import json


class Cache(object):
    def __init__(self, backend):
        self.backend = backend

    def set(self, key, data):
        if type(data) is not str:
            data = ('json', json.dumps(data))

        self.backend.store(key, data)

    def get(self, key):
        data = self.backend.retrieve(key)

        if type(data) is tuple:
            encoding, data = data

            if encoding != 'json':
                raise TypeError('No decoder found for encoding "{0}".'
                                + ' Available decoder: "json"'.format(encoding))

            return json.loads(data)

        return data

    def has(self, key):
        return self.backend.check(key)

    def delete(self, key):
        self.backend.remove(key)


def default():
    import Local
    return Cache(Local.LocalBackend())
