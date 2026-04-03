class Cache:
    def __init__(self):
        self._data: dict = {}

    def get(self, key: str):
        return self._data.get(key)

    def set(self, key: str, value):
        self._data[key] = value

    def clear(self):
        self._data.clear()


cache = Cache()
