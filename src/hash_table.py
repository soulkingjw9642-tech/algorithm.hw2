"""A string-keyed hash table using separate chaining."""


class _Node:
    __slots__ = ("key", "value", "next")

    def __init__(self, key, value, next_node=None):
        self.key = key
        self.value = value
        self.next = next_node


class HashTable:
    """A hash table with Horner hashing and a 0.75 maximum load factor."""

    _INITIAL_CAPACITY = 8
    _MAX_LOAD_FACTOR = 0.75

    def __init__(self):
        self._buckets = [None] * self._INITIAL_CAPACITY
        self.size = 0

    def _index(self, key):
        value = 0
        for character in key:
            value = (value * 31 + ord(character)) % len(self._buckets)
        return value

    def put(self, key, value):
        """Insert or replace a string key and return its value."""
        if not isinstance(key, str):
            raise TypeError("key must be a string")

        index = self._index(key)
        node = self._buckets[index]
        while node is not None:
            if node.key == key:
                node.value = value
                return value
            node = node.next

        self._buckets[index] = _Node(key, value, self._buckets[index])
        self.size += 1
        if self.size / len(self._buckets) > self._MAX_LOAD_FACTOR:
            self._resize()
        return value

    def get(self, key):
        """Return the value for a key, or None when it is absent."""
        if not isinstance(key, str):
            raise TypeError("key must be a string")

        node = self._buckets[self._index(key)]
        while node is not None:
            if node.key == key:
                return node.value
            node = node.next
        return None

    def _resize(self):
        old_buckets = self._buckets
        self._buckets = [None] * (len(old_buckets) * 2)

        for head in old_buckets:
            node = head
            while node is not None:
                next_node = node.next
                index = self._index(node.key)
                node.next = self._buckets[index]
                self._buckets[index] = node
                node = next_node
